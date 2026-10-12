"""Acceptance suite for the member banner_queue capped+windowed
monthly-roll fidelity example (BigDomain R1879 tech-queue claim
row; seed = the R1866 window suite AC-MB8..14 + the R1872 cap
suite AC-MB15..22 - this closes the family gap those two left
open: AC-MB12 proved only the BARE window face survives the
roll (a single post-roll comparison); the capped+windowed face
needs the pre-roll snapshot -> post-roll explicit old-month
cap-window read byte-identity, the monthly-roll example family
law with R1730/R1845/R1854/R1858/R1868/R1869/R1876 precedents).

Asserts the pre-registered criteria AC-MB23..AC-MB29 from the
R1879 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Carrier verdict (the R1866/R1872 sister law): a fresh isolated
face instance in its own temp world drives the TRUE product
write path end to end - every journal row lands via
attempt()/on_accept() with an explicit ts (no frozen clock, the
R1869 explicit-ts precedent), so record-time (ts_utc) is
exactly the passed stamp and the month roll rides the product
path itself, zero fixture injection.

World (cap=2 in-memory cfg variant, shipped config.json
untouched): October day - AV-A attempts renewal_due with no
budget (skip_budget), AV-B accepts first_service with no budget
(skip_budget), AV-C/AV-D hold grants and send (cap exhausted at
2), AV-E attempts with a grant (skip_daily_cap), AV-F accepts
first_service (skip_daily_cap) = 4 skipped rows sharing one
stamp (tie world). November day - AV-G attempts with no budget
(skip_budget), AV-A retries the same reason on the new day
(skip_budget - one avatar living in both month windows), AV-I/
AV-K send on the fresh day (daily cap window resets), AV-J
accepts first_service once the cap is hit (skip_daily_cap) =
3 skipped rows sharing a second stamp. 7 skipped total, 11
journal rows, 5 grant rows.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_banner_queue_caproll.py
"""

import hashlib
import inspect
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import reminder as RM                   # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7

OCT_TS = "2026-10-15T10:00:00Z"         # October anchor day
NOV_TS = "2026-11-02T09:30:00Z"         # November roll day
OCT_W = OCT_TS[:7]                      # "2026-10"
NOV_W = NOV_TS[:7]                      # "2026-11"
CFG_PATH = os.path.join(BASE, "config.json")

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")
WRITE_KW = ("INSERT", "UPDATE ", "DELETE", "REPLACE", "CREATE",
            "DROP ")

CAP_SIX = {"rows", "limit", "total", "returned", "truncated",
           "window"}
CAP_FIVE = {"rows", "limit", "total", "returned", "truncated"}


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
    return json.dumps(obj, sort_keys=True)


def load_cfg(cap):
    with open(CFG_PATH, encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg = json.loads(json.dumps(cfg))
    cfg["reminder"]["daily_send_cap_default"] = cap
    return cfg


def main():
    tmp = tempfile.mkdtemp(prefix="banner-caproll-")
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    rm_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "reminder.py"), "rb").read()
    ).hexdigest()

    cfg = load_cfg(2)
    db = os.path.join(tmp, "caproll.db")
    face = RM.ReminderFace(cfg, db)

    # ---- October anchor: 6 true-path calls, explicit ts -------
    for avatar in ("AV-C", "AV-D", "AV-E"):
        face.grant_authorization(avatar, "renewal_notice", "longterm")
    r_a = face.attempt("AV-A", "renewal_notice", "renewal_due",
                       now=OCT_TS, period_key="PK-A")
    r_b = face.on_accept("AV-B", now=OCT_TS, auto_renewal=True)
    r_c = face.attempt("AV-C", "renewal_notice", "renewal_due",
                       now=OCT_TS, period_key="PK-C")
    r_d = face.attempt("AV-D", "renewal_notice", "renewal_due",
                       now=OCT_TS, period_key="PK-D")
    r_e = face.attempt("AV-E", "renewal_notice", "renewal_due",
                       now=OCT_TS, period_key="PK-E")
    r_f = face.on_accept("AV-F", now=OCT_TS, auto_renewal=True)

    # pre-roll snapshot quartet (the AC-MB23 evidence base)
    pre_oct_bare = face.banner_queue(window=OCT_W)
    pre_oct_cap2 = face.banner_queue(window=OCT_W, limit=2)
    pre_oct_cap50 = face.banner_queue(window=OCT_W, limit=50)
    pre_def_cap2 = face.banner_queue(limit=2)
    s_pre_bare = dumps(pre_oct_bare)
    s_pre_cap2 = dumps(pre_oct_cap2)
    s_pre_cap50 = dumps(pre_oct_cap50)
    s_pre_def = dumps(pre_def_cap2)

    oct_skipped = int(q(
        db, "SELECT COUNT(*) FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%'")[0][0])
    oct_rows_total = int(q(
        db, "SELECT COUNT(*) FROM member_reminder_log")[0][0])
    grants_total = int(q(
        db, "SELECT COUNT(*) FROM"
        " member_subscribe_grants")[0][0])

    ok23 = (r_a["status"] == RM.ST_SKIP_BUDGET
            and r_b["status"] == RM.ST_SKIP_BUDGET
            and r_c["status"] == "sent" and r_d["status"] == "sent"
            and r_e["status"] == RM.ST_SKIP_CAP
            and r_f["status"] == RM.ST_SKIP_CAP
            and oct_skipped == 4 and oct_rows_total == 6
            and grants_total == 3
            and isinstance(pre_oct_bare, list)
            and len(pre_oct_bare) == 4
            and [r[1] for r in pre_oct_bare]
            == ["AV-A", "AV-B", "AV-E", "AV-F"]
            and set(pre_oct_cap2.keys()) == CAP_SIX
            and pre_oct_cap2["limit"] == 2
            and pre_oct_cap2["total"] == 4
            and pre_oct_cap2["returned"] == 2
            and pre_oct_cap2["truncated"] is True
            and pre_oct_cap2["window"] == OCT_W
            and [r[1] for r in pre_oct_cap2["rows"]]
            == ["AV-E", "AV-F"]
            and set(pre_oct_cap50.keys()) == CAP_SIX
            and pre_oct_cap50["total"] == 4
            and pre_oct_cap50["returned"] == 4
            and pre_oct_cap50["truncated"] is False
            and dumps(pre_oct_cap50["rows"]) == s_pre_bare
            and set(pre_def_cap2.keys()) == CAP_FIVE
            and pre_def_cap2["total"] == 4
            and [r[1] for r in pre_def_cap2["rows"]]
            == ["AV-E", "AV-F"])
    record("AC-MB23", ok23,
           "oct statuses=%s,%s,%s,%s,%s,%s skipped=%d rows=%d "
           "grants=%d bare_order=%s cap2_keys=%s cap2_tail=%s "
           "cap50==bare=%s def_cap2_tail=%s"
           % (r_a["status"], r_b["status"], r_c["status"],
              r_d["status"], r_e["status"], r_f["status"],
              oct_skipped, oct_rows_total, grants_total,
              [r[1] for r in pre_oct_bare],
              sorted(pre_oct_cap2.keys()),
              [r[1] for r in pre_oct_cap2["rows"]],
              dumps(pre_oct_cap50["rows"]) == s_pre_bare,
              [r[1] for r in pre_def_cap2["rows"]]))

    # ---- November roll: 5 true-path calls on the new day -------
    for avatar in ("AV-I", "AV-K"):
        face.grant_authorization(avatar, "renewal_notice", "longterm")
    n_g = face.attempt("AV-G", "renewal_notice", "renewal_due",
                       now=NOV_TS, period_key="PK-G")
    n_a = face.attempt("AV-A", "renewal_notice", "renewal_due",
                       now=NOV_TS, period_key="PK-A")
    n_i = face.attempt("AV-I", "renewal_notice", "renewal_due",
                       now=NOV_TS, period_key="PK-I")
    n_k = face.attempt("AV-K", "renewal_notice", "renewal_due",
                       now=NOV_TS, period_key="PK-K")
    n_j = face.on_accept("AV-J", now=NOV_TS, auto_renewal=True)

    full_skipped = int(q(
        db, "SELECT COUNT(*) FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%'")[0][0])
    full_rows = int(q(
        db, "SELECT COUNT(*) FROM member_reminder_log")[0][0])
    post_oct_bare = face.banner_queue(window=OCT_W)
    nov_bare = face.banner_queue(window=NOV_W)
    oct_avatars = set(r[1] for r in post_oct_bare)
    nov_avatars = set(r[1] for r in nov_bare)
    no_leak = (not (nov_avatars & {"AV-B", "AV-E", "AV-F"})
               and not (oct_avatars & {"AV-G", "AV-J"}))

    ok24 = (n_g["status"] == RM.ST_SKIP_BUDGET
            and n_a["status"] == RM.ST_SKIP_BUDGET
            and n_i["status"] == "sent" and n_k["status"] == "sent"
            and n_j["status"] == RM.ST_SKIP_CAP
            and full_skipped == 7 and full_rows == 11
            and dumps(post_oct_bare) == s_pre_bare
            and len(nov_bare) == 3
            and [r[1] for r in nov_bare]
            == ["AV-G", "AV-A", "AV-J"]
            and no_leak)
    record("AC-MB24", ok24,
           "nov statuses=%s,%s,%s,%s,%s full_skipped=%d rows=%d "
           "oct_bare==pre_bare=%s nov_rows=%d nov_order=%s "
           "leak_free=%s"
           % (n_g["status"], n_a["status"], n_i["status"],
              n_k["status"], n_j["status"], full_skipped,
              full_rows, dumps(post_oct_bare) == s_pre_bare,
              len(nov_bare), [r[1] for r in nov_bare], no_leak))

    # ---- AC-MB25: capped old-month projection fidelity --------
    post_oct_cap2 = face.banner_queue(window=OCT_W, limit=2)
    post_oct_cap2_again = face.banner_queue(window=OCT_W, limit=2)
    post_oct_cap50 = face.banner_queue(window=OCT_W, limit=50)
    ok25 = (dumps(post_oct_cap2) == s_pre_cap2
            and dumps(post_oct_cap2) == dumps(post_oct_cap2_again)
            and dumps(post_oct_cap50["rows"]) == s_pre_bare
            and post_oct_cap50["total"] == 4
            and post_oct_cap50["truncated"] is False
            and [r[1] for r in post_oct_cap2["rows"]]
            == ["AV-E", "AV-F"])
    record("AC-MB25", ok25,
           "oct_cap2==pre_snapshot=%s double_call_identical=%s "
           "oct_cap50_rows==pre_bare=%s cap50_total=%d "
           "tie_tail_frozen=%s"
           % (dumps(post_oct_cap2) == s_pre_cap2,
              dumps(post_oct_cap2) == dumps(post_oct_cap2_again),
              dumps(post_oct_cap50["rows"]) == s_pre_bare,
              post_oct_cap50["total"],
              [r[1] for r in post_oct_cap2["rows"]]))

    # ---- AC-MB26: default cap face follows the new window ----
    post_def_cap2 = face.banner_queue(limit=2)
    full_bare = face.banner_queue()
    def_tail_avatars = [r[1] for r in post_def_cap2["rows"]]
    full_tail_avatars = [r[1] for r in full_bare[-2:]]
    ok26 = (dumps(post_def_cap2["rows"]) == dumps(full_bare[-2:])
            and def_tail_avatars == ["AV-A", "AV-J"]
            and full_tail_avatars == ["AV-A", "AV-J"]
            and dumps(post_def_cap2) != s_pre_def
            and post_def_cap2["total"] == 7
            and set(post_def_cap2.keys()) == CAP_FIVE)
    record("AC-MB26", ok26,
           "def_tail==full_tail=%s tail=%s total=%d "
           "drifted_from_pre=%s keys_five=%s"
           % (dumps(post_def_cap2["rows"])
              == dumps(full_bare[-2:]),
              def_tail_avatars, post_def_cap2["total"],
              dumps(post_def_cap2) != s_pre_def,
              set(post_def_cap2.keys()) == CAP_FIVE))

    # ---- AC-MB27: window-total semantics across the roll ------
    nov_cap2 = face.banner_queue(window=NOV_W, limit=2)
    post_oct_total = post_oct_cap2["total"]
    pre_oct_total = pre_oct_cap2["total"]
    ok27 = (pre_oct_total == 4 and post_oct_total == 4
            and post_oct_cap50["total"] == 4
            and nov_cap2["total"] == 3
            and post_def_cap2["total"] == 7
            and nov_cap2["returned"] == 2
            and nov_cap2["truncated"] is True)
    record("AC-MB27", ok27,
           "oct_window_total pre=%d post=%d cap50=%d "
           "nov_window_total=%d default_total=%d "
           "window_before_count_and_limit=%s"
           % (pre_oct_total, post_oct_total,
              post_oct_cap50["total"], nov_cap2["total"],
              post_def_cap2["total"],
              pre_oct_total == post_oct_total == 4
              and post_def_cap2["total"] == 7))

    # ---- AC-MB28: orthogonality + reverse assertion -----------
    oct_months = set(r[4][:7] for r in post_oct_cap2["rows"])
    def_months = set(r[4][:7]
                     for r in post_def_cap2["rows"])
    rows_diverge = (dumps(post_oct_cap2["rows"])
                    != dumps(post_def_cap2["rows"]))
    empty_combo = face.banner_queue(window="2026-09", limit=2)
    ok28 = (oct_months == {"2026-10"}
            and def_months == {"2026-11"}
            and rows_diverge
            and set(post_oct_cap2.keys()) == CAP_SIX
            and set(post_def_cap2.keys()) == CAP_FIVE
            and post_oct_cap2["window"] == OCT_W
            and "window" not in post_def_cap2
            and empty_combo["rows"] == []
            and empty_combo["total"] == 0
            and empty_combo["returned"] == 0
            and empty_combo["truncated"] is False
            and empty_combo["window"] == "2026-09"
            and empty_combo["limit"] == 2)
    record("AC-MB28", ok28,
           "oct_cap2_months=%s def_cap2_months=%s rows_diverge=%s "
           "oct_keys_six=%s def_keys_five=%s empty_combo=%s"
           % (sorted(oct_months), sorted(def_months),
              rows_diverge,
              set(post_oct_cap2.keys()) == CAP_SIX,
              set(post_def_cap2.keys()) == CAP_FIVE,
              empty_combo["rows"] == []
              and empty_combo["total"] == 0))

    # ---- AC-MB29: pure-read law + hygiene ---------------------
    src = inspect.getsource(RM.ReminderFace.banner_queue)
    writes = [kw for kw in WRITE_KW if kw in src]
    before29 = (q(db, "SELECT COUNT(*) FROM"
                  " member_reminder_log")[0][0],
                q(db, "SELECT COUNT(*) FROM"
                  " member_subscribe_grants")[0][0])
    face.banner_queue()
    face.banner_queue(limit=2)
    face.banner_queue(window=OCT_W)
    face.banner_queue(window=OCT_W, limit=2)
    face.banner_queue(window=NOV_W, limit=2)
    face.banner_queue(window="2026-09", limit=2)
    after29 = (q(db, "SELECT COUNT(*) FROM"
                 " member_reminder_log")[0][0],
               q(db, "SELECT COUNT(*) FROM"
                 " member_subscribe_grants")[0][0])
    face.close()
    with open(os.path.abspath(__file__), "rb") as fh:
        own = fh.read()
    ascii_ok = True
    try:
        own.decode("ascii")
    except UnicodeDecodeError:
        ascii_ok = False
    import_lines = [ln.strip() for ln in own.decode("utf-8")
                    .splitlines() if ln.strip().startswith("import ")]
    net_hits = [ln for ln in import_lines
                for lib in NET_LIBS if lib in ln]
    cfg_sha_out = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    rm_sha_out = hashlib.sha256(
        open(os.path.join(BASE, "reminder.py"), "rb").read()
    ).hexdigest()
    world_outside_repo = not os.path.abspath(db).startswith(
        os.path.abspath(BASE) + os.sep)
    ok29 = (not writes and before29 == after29
            and before29[0] == 11 and before29[1] == 5
            and ascii_ok and not net_hits
            and cfg_sha_in == cfg_sha_out
            and rm_sha_in == rm_sha_out and world_outside_repo)
    record("AC-MB29", ok29,
           "write_keywords=%s counts_stable=%s (log %d==%d "
           "grants %d==%d) ascii=%s net_imports=%s "
           "cfg_unchanged=%s reminder_unchanged=%s "
           "world_outside_repo=%s"
           % (writes, before29 == after29, before29[0],
              after29[0], before29[1], after29[1], ascii_ok,
              net_hits, cfg_sha_in == cfg_sha_out,
              rm_sha_in == rm_sha_out, world_outside_repo))

    shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE PASS %d/%d" % (passed, EXPECTED), flush=True)
    if passed != EXPECTED or len(RESULTS) != EXPECTED:
        sys.exit(1)


if __name__ == "__main__":
    main()
