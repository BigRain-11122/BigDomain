"""Acceptance suite for the pay notify banner_queue monthly-roll
fidelity example (BigDomain R1883 tech-queue claim row; seed =
the R1878 window suite AC-PN16..22 + the R1871 cap suite
AC-PN8..15 - this closes the family gap those two left open:
AC-PN16..22 proved the window/cap faces only in a static
single-month world; the monthly-roll fidelity example needs the
pre-roll snapshot -> post-roll explicit old-month read
byte-identity, the family law with R1730/R1845/R1854/R1858/
R1868/R1869/R1876/R1879 precedents).

Asserts the pre-registered criteria AC-PN23..AC-PN29 from the
R1883 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Carrier verdict (R1718 wiring law): a fresh isolated face
instance in its own temp world drives the TRUE product write
path end to end - every skipped row lands via
notify_payment_success() on a granted order with an explicit ts
(the R1869 explicit-ts precedent), so record time (ts_utc) is
exactly the passed stamp and the month roll rides the product
path itself, zero fixture injection into pay_notify_log.

World (no W15 grants -> every attempt lands skipped_no_budget):
October anchor day - AV-A/AV-B/AV-C/AV-D each hold one granted
pack_compute_19_9 order; four payment_success attempts share
one stamp (same-second tie world) -> 4 skipped rows in window
2026-10. November roll day - AV-E (pack) + AV-A (second product
birthright_entry: one avatar living in both month windows) +
AV-F (pack) hold granted orders; three attempts share a second
stamp -> 3 skipped rows in window 2026-11. 7 skipped total, 0
sent rows, 0 grant rows.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_pay_notify_bannerroll.py
"""

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import test_pay as TP                    # noqa: E402 (fixture reuse)
import test_pay_notify as TN             # noqa: E402 (scaffold reuse)
import notify as N                       # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7

OCT_TS = "2026-10-15T10:00:00Z"         # October anchor day
NOV_TS = "2026-11-02T09:30:00Z"         # November roll day
OCT_W = OCT_TS[:7]                      # "2026-10"
NOV_W = NOV_TS[:7]                      # "2026-11"
EMPTY_W = "2026-12"                     # honest-empty month

CAP_SIX = {"rows", "limit", "total", "returned", "truncated",
           "window"}
CAP_FIVE = {"rows", "limit", "total", "returned", "truncated"}

CFG_PATH = os.path.join(BASE, "config.json")
FACE_PATH = os.path.join(BASE, "notify.py")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def q(db, sql, args=()):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def dumps(obj):
    return json.dumps(obj, sort_keys=True, default=str)


def skip_rows(db):
    return q(db, "SELECT send_id, status FROM pay_notify_log"
                 " WHERE status LIKE 'skipped_%'")


def main():
    tmp = tempfile.mkdtemp(prefix="paynotify-bannerroll-")
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    face_sha_in = hashlib.sha256(
        open(FACE_PATH, "rb").read()).hexdigest()

    world = TP.build(mint=True)
    pay_db = os.path.join(world["tmp"], "pay.db")

    oct_oids = []
    for name in ("AV-A", "AV-B", "AV-C", "AV-D"):
        oid, _ = TP.happy(world, "pack_compute_19_9", name,
                          nonce="roll-oct-" + name)
        oct_oids.append(oid)
    nov_oids = []
    oid, _ = TP.happy(world, "pack_compute_19_9", "AV-E",
                      nonce="roll-nov-e")
    nov_oids.append(oid)
    oid, _ = TP.happy(world, "birthright_entry", "AV-A",
                      nonce="roll-nov-a2")
    nov_oids.append(oid)
    oid, _ = TP.happy(world, "pack_compute_19_9", "AV-F",
                      nonce="roll-nov-f")
    nov_oids.append(oid)

    db = os.path.join(tmp, "bannerroll.db")
    cfg = TN.notify_cfg(TP.load_pay_config(), cap=1000)
    f = N.PayNotifyFace(cfg, db, pay_db=pay_db)   # no grants -> skips

    # ---- October anchor: 4 true-path attempts, one shared stamp --
    oct_res = [f.notify_payment_success(o, now=OCT_TS)
               for o in oct_oids]

    pre_rows = skip_rows(db)
    pre_oct_bare = f.banner_queue(window=OCT_W)
    pre_oct_cap2 = f.banner_queue(limit=2, window=OCT_W)
    pre_oct_cap50 = f.banner_queue(limit=50, window=OCT_W)
    pre_def_cap2 = f.banner_queue(limit=2)
    s_pre_bare = dumps(pre_oct_bare)
    s_pre_cap2 = dumps(pre_oct_cap2)
    s_pre_cap50 = dumps(pre_oct_cap50)
    s_pre_def = dumps(pre_def_cap2)

    oct_sent = int(q(db, "SELECT COUNT(*) FROM pay_notify_log"
                        " WHERE status='sent'")[0][0])
    oct_total_rows = int(q(
        db, "SELECT COUNT(*) FROM pay_notify_log")[0][0])

    ok23 = (all(r["status"] == N.ST_SKIP_BUDGET for r in oct_res)
            and len(pre_rows) == 4 and oct_sent == 0
            and oct_total_rows == 4
            and isinstance(pre_oct_bare, list)
            and len(pre_oct_bare) == 4
            and [r[1] for r in pre_oct_bare]
            == ["AV-A", "AV-B", "AV-C", "AV-D"]
            and all(r[5] == OCT_TS for r in pre_oct_bare)
            and set(pre_oct_cap2.keys()) == CAP_SIX
            and pre_oct_cap2["limit"] == 2
            and pre_oct_cap2["total"] == 4
            and pre_oct_cap2["returned"] == 2
            and pre_oct_cap2["truncated"] is True
            and pre_oct_cap2["window"] == OCT_W
            and [r[1] for r in pre_oct_cap2["rows"]]
            == ["AV-C", "AV-D"]
            and set(pre_oct_cap50.keys()) == CAP_SIX
            and pre_oct_cap50["total"] == 4
            and pre_oct_cap50["returned"] == 4
            and pre_oct_cap50["truncated"] is False
            and dumps(pre_oct_cap50["rows"]) == s_pre_bare
            and set(pre_def_cap2.keys()) == CAP_FIVE
            and pre_def_cap2["total"] == 4
            and [r[1] for r in pre_def_cap2["rows"]]
            == ["AV-C", "AV-D"])
    record("AC-PN23", ok23,
           "oct statuses=%s skip_rows=%d sent=%d all_rows=%d "
           "bare=%s cap2_keys=%s cap2_tail=%s cap50_eq_bare=%s "
           "def_tail=%s"
           % ([r["status"] for r in oct_res], len(pre_rows),
              oct_sent, oct_total_rows,
              [r[1] for r in pre_oct_bare],
              sorted(pre_oct_cap2.keys()),
              [r[1] for r in pre_oct_cap2["rows"]],
              dumps(pre_oct_cap50["rows"]) == s_pre_bare,
              [r[1] for r in pre_def_cap2["rows"]]))

    # ---- November roll: 3 true-path attempts on the new day -------
    nov_res = [f.notify_payment_success(o, now=NOV_TS)
               for o in nov_oids]

    ok24 = (all(r["status"] == N.ST_SKIP_BUDGET for r in nov_res)
            and int(q(db, "SELECT COUNT(*) FROM pay_notify_log"
                         " WHERE status LIKE 'skipped_%'"
                         " AND substr(ts_utc,1,7)=?",
                         (NOV_W,))[0][0]) == 3
            and int(q(db, "SELECT COUNT(*) FROM pay_notify_log"
                         " WHERE status LIKE 'skipped_%'")[0][0]) == 7
            and int(q(db, "SELECT COUNT(*) FROM pay_notify_log"
                         " WHERE census_avatar_id='AV-A'"
                         " AND status LIKE 'skipped_%'")[0][0]) == 2
            and int(q(db, "SELECT COUNT(*) FROM pay_notify_log"
                         " WHERE status='sent'")[0][0]) == 0)
    record("AC-PN24", ok24,
           "nov statuses=%s nov_rows=%d total_skip=%d "
           "ava_both_windows=%d"
           % ([r["status"] for r in nov_res], 3, 7, 2))

    # ---- post-roll fidelity reads ----------------------------------
    post_oct_cap2 = f.banner_queue(limit=2, window=OCT_W)
    post_oct_cap50 = f.banner_queue(limit=50, window=OCT_W)
    post_def_cap2 = f.banner_queue(limit=2)
    post_nov_cap = f.banner_queue(limit=5, window=NOV_W)
    empty_cap = f.banner_queue(limit=3, window=EMPTY_W)
    post_rows = skip_rows(db)

    ok25 = (dumps(post_oct_cap2) == s_pre_cap2
            and [r[1] for r in post_oct_cap2["rows"]]
            == ["AV-C", "AV-D"])
    record("AC-PN25", ok25,
           "post_oct_cap2==pre byte-identity=%s tail=%s"
           % (dumps(post_oct_cap2) == s_pre_cap2,
              [r[1] for r in post_oct_cap2["rows"]]))

    ok26 = (dumps(post_oct_cap50["rows"]) == s_pre_bare
            and len(post_oct_cap50["rows"]) == 4)
    record("AC-PN26", ok26,
           "post_oct_cap50_rows==pre_bare=%s len=%d"
           % (dumps(post_oct_cap50["rows"]) == s_pre_bare,
              len(post_oct_cap50["rows"])))

    ok27 = (post_def_cap2["total"] == 7
            and [r[1] for r in post_def_cap2["rows"]]
            == ["AV-A", "AV-F"]
            and dumps(post_def_cap2) != s_pre_def)
    record("AC-PN27", ok27,
           "def_cap total=%d tail=%s drift_from_pre=%s"
           % (post_def_cap2["total"],
              [r[1] for r in post_def_cap2["rows"]],
              dumps(post_def_cap2) != s_pre_def))

    oct_ts_ok = all(r[5][:7] == OCT_W
                    for r in post_oct_cap2["rows"])
    def_ts_ok = all(r[5][:7] == NOV_W
                    for r in post_def_cap2["rows"])
    ok28 = (post_oct_cap2["total"] == 4
            and post_nov_cap["total"] == 3
            and post_def_cap2["total"] == 7
            and post_nov_cap["returned"] == 3
            and post_nov_cap["truncated"] is False
            and oct_ts_ok and def_ts_ok
            and dumps(post_oct_cap2["rows"])
            != dumps(post_def_cap2["rows"]))
    record("AC-PN28", ok28,
           "oct_total=%d nov_total=%d def_total=%d "
           "oct_rows_all_oct=%s def_tail_all_nov=%s "
           "reads_differ=%s"
           % (post_oct_cap2["total"], post_nov_cap["total"],
              post_def_cap2["total"], oct_ts_ok, def_ts_ok,
              dumps(post_oct_cap2["rows"])
              != dumps(post_def_cap2["rows"])))

    cfg_sha_out = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    face_sha_out = hashlib.sha256(
        open(FACE_PATH, "rb").read()).hexdigest()
    empty_ok = (set(empty_cap.keys()) == CAP_SIX
                and empty_cap["rows"] == []
                and empty_cap["total"] == 0
                and empty_cap["returned"] == 0
                and empty_cap["truncated"] is False
                and empty_cap["window"] == EMPTY_W)
    pure_read_ok = (sorted(pre_rows + q(
        db, "SELECT send_id, status FROM pay_notify_log"
        " WHERE status LIKE 'skipped_%' AND substr(ts_utc,1,7)=?",
        (NOV_W,))) == sorted(post_rows)
        and len(post_rows) == 7)
    hygiene_ok = (cfg_sha_out == cfg_sha_in
                  and face_sha_out == face_sha_in
                  and not os.path.abspath(db).startswith(
                      os.path.abspath(BASE))
                  and all(ord(c) < 128 for c in
                          open(os.path.abspath(__file__),
                               encoding="utf-8").read()))
    ok29 = empty_ok and pure_read_ok and hygiene_ok
    record("AC-PN29", ok29,
           "empty_keys=%s empty_total=%d pure_read=%s "
           "cfg_stable=%s face_stable=%s world_outside=%s "
           "ascii=%s"
           % (sorted(empty_cap.keys()), empty_cap["total"],
              pure_read_ok, cfg_sha_out == cfg_sha_in,
              face_sha_out == face_sha_in,
              not os.path.abspath(db).startswith(
                  os.path.abspath(BASE)),
              all(ord(c) < 128 for c in
                  open(os.path.abspath(__file__),
                       encoding="utf-8").read())))

    f.close()
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(world["tmp"], ignore_errors=True)

    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s: %d/%d pass-lines"
          % ("PASS" if not fails else "FAIL",
             len(RESULTS) - len(fails), EXPECTED))
    if len(RESULTS) != EXPECTED or fails:
        print("SUITE FAIL: %s" % fails)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
