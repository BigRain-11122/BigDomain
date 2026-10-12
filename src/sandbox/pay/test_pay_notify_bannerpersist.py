"""Acceptance suite for the pay notify banner_queue capped-window
read cross-restart persistence example (BigDomain R1884 tech-queue
claim row; seed = the R1883 reseed line - the window suite
AC-PN16..22, the cap suite AC-PN8..15 and the month-roll suite
AC-PN23..29 all proved their faces inside ONE process lifetime;
this closes the family gap they left open: close -> brand-new
instance -> same-db reopen must reproduce every derived read face
byte-identically (zero in-memory drift), and the contrast pair
must survive restart AND new data: the default (windowless) faces
drift to the new rows while the explicit-window October reads stay
frozen to the pre-restart snapshot).

Asserts the pre-registered criteria AC-PN30..AC-PN36 from the
R1884 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Carrier verdict (R1718 wiring law, R1883 same family): a fresh
isolated face instance in its own temp world drives the TRUE
product write path end to end - every skipped row lands via
notify_payment_success() on a granted order with an explicit ts
(the R1869 explicit-ts precedent), zero fixture injection into
pay_notify_log.

World (no W15 grants -> every attempt lands skipped_no_budget):
October anchor day - AV-A/AV-B/AV-C/AV-D each hold one granted
pack_compute_19_9 order; four payment_success attempts share one
stamp (same-second tie world) -> 4 skipped rows in window 2026-10,
snapshotted on instance #1. Instance #2 reopens the same db,
proves the five read faces byte-identical, then drives the
November roll (AV-E pack + AV-A birthright_entry second product,
one avatar living in both month windows + AV-F pack, one shared
stamp) -> 3 more skipped rows in window 2026-11; default faces
drift to 7, October windowed faces stay frozen. Instance #3
reopens once more and reproduces the whole post-roll state.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_pay_notify_bannerpersist.py
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
NOV_TS = "2026-11-02T09:30:00Z"         # November roll day (post-restart)
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


def log_set(db):
    return q(db, "SELECT send_id, census_avatar_id, order_id,"
                 " reason, status, ts_utc FROM pay_notify_log"
                 " ORDER BY send_id")


def five_faces(face):
    """The five derived read faces of the persistence example."""
    return {
        "oct_bare": face.banner_queue(window=OCT_W),
        "oct_cap2": face.banner_queue(limit=2, window=OCT_W),
        "oct_cap50": face.banner_queue(limit=50, window=OCT_W),
        "def_cap2": face.banner_queue(limit=2),
        "def_bare": face.banner_queue(),
    }


def snap(faces):
    return {k: dumps(v) for k, v in faces.items()}


def main():
    tmp = tempfile.mkdtemp(prefix="paynotify-bannerpersist-")
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    face_sha_in = hashlib.sha256(
        open(FACE_PATH, "rb").read()).hexdigest()

    world = TP.build(mint=True)
    pay_db = os.path.join(world["tmp"], "pay.db")

    oct_oids = []
    for name in ("AV-A", "AV-B", "AV-C", "AV-D"):
        oid, _ = TP.happy(world, "pack_compute_19_9", name,
                          nonce="persist-oct-" + name)
        oct_oids.append(oid)
    nov_oids = []
    oid, _ = TP.happy(world, "pack_compute_19_9", "AV-E",
                      nonce="persist-nov-e")
    nov_oids.append(oid)
    oid, _ = TP.happy(world, "birthright_entry", "AV-A",
                      nonce="persist-nov-a2")
    nov_oids.append(oid)
    oid, _ = TP.happy(world, "pack_compute_19_9", "AV-F",
                      nonce="persist-nov-f")
    nov_oids.append(oid)

    db = os.path.join(tmp, "bannerpersist.db")
    cfg = TN.notify_cfg(TP.load_pay_config(), cap=1000)

    # ---- instance #1: October anchor + pre-restart snapshot -------
    f1 = N.PayNotifyFace(cfg, db, pay_db=pay_db)   # no grants -> skips
    oct_res = [f1.notify_payment_success(o, now=OCT_TS)
               for o in oct_oids]

    pre_log = log_set(db)                    # pure-read anchor (PN34)
    faces1 = five_faces(f1)
    s1 = snap(faces1)
    post_read_log = log_set(db)

    ok30 = (all(r["status"] == N.ST_SKIP_BUDGET for r in oct_res)
            and len(pre_log) == 4 and len(post_read_log) == 4
            and isinstance(faces1["oct_bare"], list)
            and len(faces1["oct_bare"]) == 4
            and [r[1] for r in faces1["oct_bare"]]
            == ["AV-A", "AV-B", "AV-C", "AV-D"]
            and all(r[5] == OCT_TS for r in faces1["oct_bare"])
            and set(faces1["oct_cap2"].keys()) == CAP_SIX
            and faces1["oct_cap2"]["limit"] == 2
            and faces1["oct_cap2"]["total"] == 4
            and faces1["oct_cap2"]["returned"] == 2
            and faces1["oct_cap2"]["truncated"] is True
            and faces1["oct_cap2"]["window"] == OCT_W
            and [r[1] for r in faces1["oct_cap2"]["rows"]]
            == ["AV-C", "AV-D"]
            and set(faces1["oct_cap50"].keys()) == CAP_SIX
            and faces1["oct_cap50"]["total"] == 4
            and faces1["oct_cap50"]["returned"] == 4
            and faces1["oct_cap50"]["truncated"] is False
            and dumps(faces1["oct_cap50"]["rows"])
            == dumps(faces1["oct_bare"])
            and set(faces1["def_cap2"].keys()) == CAP_FIVE
            and faces1["def_cap2"]["total"] == 4
            and [r[1] for r in faces1["def_cap2"]["rows"]]
            == ["AV-C", "AV-D"]
            and isinstance(faces1["def_bare"], list)
            and len(faces1["def_bare"]) == 4)
    record("AC-PN30", ok30,
           "oct statuses=%s skip_rows=%d faces: bare=%d cap2_tail=%s "
           "cap50_eq_bare=%s def_cap2_keys=%s def_bare=%d"
           % ([r["status"] for r in oct_res], len(pre_log),
              len(faces1["oct_bare"]),
              [r[1] for r in faces1["oct_cap2"]["rows"]],
              dumps(faces1["oct_cap50"]["rows"])
              == dumps(faces1["oct_bare"]),
              sorted(faces1["def_cap2"].keys()),
              len(faces1["def_bare"])))

    # ---- instance #2: same-db reopen, byte-identity ---------------
    f1.close()
    f2 = N.PayNotifyFace(cfg, db, pay_db=pay_db)
    faces2 = five_faces(f2)
    s2 = snap(faces2)
    ok31 = (s2 == s1
            and set(faces2["oct_cap2"].keys()) == CAP_SIX
            and set(faces2["def_cap2"].keys()) == CAP_FIVE
            and [r[1] for r in faces2["oct_cap2"]["rows"]]
            == ["AV-C", "AV-D"])
    record("AC-PN31", ok31,
           "all_five_byte_identical=%s oct_cap2_tail_frozen=%s "
           "key_sets_stable=%s"
           % (s2 == s1,
              [r[1] for r in faces2["oct_cap2"]["rows"]]
              == ["AV-C", "AV-D"],
              set(faces2["oct_cap2"].keys()) == CAP_SIX
              and set(faces2["def_cap2"].keys()) == CAP_FIVE))

    # ---- post-restart November roll: drift vs freeze --------------
    nov_res = [f2.notify_payment_success(o, now=NOV_TS)
               for o in nov_oids]

    pre_nov_log = log_set(db)                # pure-read anchor (PN34)
    faces2n = five_faces(f2)
    s2n = snap(faces2n)
    post_nov_log = log_set(db)

    ok32 = (all(r["status"] == N.ST_SKIP_BUDGET for r in nov_res)
            and len(pre_nov_log) == 7
            and s2n["oct_bare"] == s1["oct_bare"]
            and s2n["oct_cap2"] == s1["oct_cap2"]
            and s2n["oct_cap50"] == s1["oct_cap50"]
            and faces2n["def_cap2"]["total"] == 7
            and [r[1] for r in faces2n["def_cap2"]["rows"]]
            == ["AV-A", "AV-F"]
            and s2n["def_cap2"] != s1["def_cap2"]
            and len(faces2n["def_bare"]) == 7
            and s2n["def_bare"] != s1["def_bare"]
            and int(q(db, "SELECT COUNT(*) FROM pay_notify_log"
                        " WHERE census_avatar_id='AV-A'"
                        " AND status LIKE 'skipped_%'")[0][0]) == 2)
    record("AC-PN32", ok32,
           "oct_frozen(bare=%s cap2=%s cap50=%s) def_drift("
           "total=%d tail=%s bare=%d) ava_both_windows=%d"
           % (s2n["oct_bare"] == s1["oct_bare"],
              s2n["oct_cap2"] == s1["oct_cap2"],
              s2n["oct_cap50"] == s1["oct_cap50"],
              faces2n["def_cap2"]["total"],
              [r[1] for r in faces2n["def_cap2"]["rows"]],
              len(faces2n["def_bare"]),
              int(q(db, "SELECT COUNT(*) FROM pay_notify_log"
                        " WHERE census_avatar_id='AV-A'"
                        " AND status LIKE 'skipped_%'")[0][0])))

    # ---- window totals semantics across restart --------------------
    nov_cap = f2.banner_queue(limit=5, window=NOV_W)
    empty_cap = f2.banner_queue(limit=3, window=EMPTY_W)
    ok33 = (faces2n["oct_cap2"]["total"] == 4
            and int(q(db, "SELECT COUNT(*) FROM pay_notify_log"
                        " WHERE status LIKE 'skipped_%'"
                        " AND substr(ts_utc,1,7)=?",
                        (OCT_W,))[0][0]) == 4
            and set(nov_cap.keys()) == CAP_SIX
            and nov_cap["total"] == 3
            and nov_cap["returned"] == 3
            and nov_cap["truncated"] is False
            and all(r[5][:7] == NOV_W for r in nov_cap["rows"])
            and set(empty_cap.keys()) == CAP_SIX
            and empty_cap["rows"] == []
            and empty_cap["total"] == 0
            and empty_cap["returned"] == 0
            and empty_cap["truncated"] is False
            and empty_cap["window"] == EMPTY_W)
    record("AC-PN33", ok33,
           "oct_total=%d nov_total=%d nov_returned=%d "
           "empty_total=%d empty_keys=%s"
           % (faces2n["oct_cap2"]["total"], nov_cap["total"],
              nov_cap["returned"], empty_cap["total"],
              sorted(empty_cap.keys())))

    # ---- pure-read law across restart (zero side effects) ---------
    ok34 = (pre_log == post_read_log            # instance #1 batch
            and pre_nov_log == post_nov_log     # instance #2 batch
            and dumps(sorted(faces2n["def_bare"]))
            == dumps(sorted(f2.banner_queue()))
            and int(q(db, "SELECT COUNT(*) FROM pay_notify_log")
                    [0][0]) == 7
            and int(q(db, "SELECT COUNT(*) FROM pay_notify_grants")
                    [0][0]) == 0)
    record("AC-PN34", ok34,
           "i1_batch_clean=%s i2_batch_clean=%s bare_reread_eq=%s "
           "log_rows=%d grant_rows=%d"
           % (pre_log == post_read_log,
              pre_nov_log == post_nov_log,
              dumps(sorted(faces2n["def_bare"]))
              == dumps(sorted(f2.banner_queue())),
              7, 0))

    # ---- instance #3: double-restart stability ---------------------
    f2.close()
    f3 = N.PayNotifyFace(cfg, db, pay_db=pay_db)
    faces3 = five_faces(f3)
    s3 = snap(faces3)
    ok35 = (s3 == s2n
            and s3["oct_bare"] == s1["oct_bare"]
            and s3["oct_cap2"] == s1["oct_cap2"]
            and s3["oct_cap50"] == s1["oct_cap50"]
            and faces3["def_cap2"]["total"] == 7
            and [r[1] for r in faces3["def_cap2"]["rows"]]
            == ["AV-A", "AV-F"])
    record("AC-PN35", ok35,
           "i3_eq_i2_postroll=%s oct_still_eq_original_snapshot=%s "
           "def_tail=%s"
           % (s3 == s2n,
              s3["oct_bare"] == s1["oct_bare"]
              and s3["oct_cap2"] == s1["oct_cap2"]
              and s3["oct_cap50"] == s1["oct_cap50"],
              [r[1] for r in faces3["def_cap2"]["rows"]]))

    # ---- hygiene ----------------------------------------------------
    cfg_sha_out = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    face_sha_out = hashlib.sha256(
        open(FACE_PATH, "rb").read()).hexdigest()
    ascii_ok = all(ord(c) < 128 for c in
                   open(os.path.abspath(__file__),
                        encoding="utf-8").read())
    ok36 = (cfg_sha_out == cfg_sha_in
            and face_sha_out == face_sha_in
            and not os.path.abspath(db).startswith(
                os.path.abspath(BASE))
            and ascii_ok)
    record("AC-PN36", ok36,
           "cfg_stable=%s face_stable=%s world_outside=%s ascii=%s"
           % (cfg_sha_out == cfg_sha_in,
              face_sha_out == face_sha_in,
              not os.path.abspath(db).startswith(
                  os.path.abspath(BASE)),
              ascii_ok))

    f3.close()
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
