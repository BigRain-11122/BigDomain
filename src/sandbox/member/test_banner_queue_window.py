"""Acceptance suite for the member banner_queue window param
(BigDomain R1866 tech-queue claim row; seed = the R1856
banner_board window law + the R1860 rows_by_status raw-row
window caliber - banner_queue was the window-parameter family
member whose raw row face carried no window param).

Asserts the pre-registered criteria AC-MB8..AC-MB14 from the
R1866 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Carrier verdict (the R1861 banner_board_roll sister-precedent):
a fresh isolated face instance in its own temp world drives the
TRUE product write path end to end - every journal row lands via
attempt()/on_accept() with an explicit ts, so record-time
(ts_utc) is exactly the passed stamp and the month roll rides
the product path itself, zero fixture injection. The row face
never gets an envelope: window cuts the row set, it never
reorders and never reshapes (raw LIST caliber, R1860 law).

World (cap=2 in-memory cfg variant, shipped config.json
untouched): October day - AV-A attempts renewal_due with no
budget (skip_budget), AV-B accepts first_service with no budget
(skip_budget), AV-C/AV-D hold grants and send (cap exhausted at
2), AV-E attempts with a grant (skip_daily_cap), AV-F accepts
first_service (skip_daily_cap) = 4 skipped rows. November day -
AV-G attempts with no budget (skip_budget), AV-A retries the
same reason on the new day (skip_budget - one avatar living in
both month windows), AV-I/AV-K send on the fresh day (daily cap
window resets), AV-J accepts first_service once the cap is hit
(skip_daily_cap) = 3 skipped rows. 7 skipped total, 11 rows.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_banner_queue_window.py
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

# R1856 bads14 tuple, reused verbatim (family law).
BADS14 = ("2026-13", "2026-00", "2026-1", "2026/10", "2026",
          "202610", "abcd", "", 2026, True, 2.5,
          "2026-10\n", "2026-10 ", "2026-10\r")


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


def dumps(rows):
    return json.dumps(rows, sort_keys=True)


def load_cfg(cap):
    with open(CFG_PATH, encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg = json.loads(json.dumps(cfg))
    cfg["reminder"]["daily_send_cap_default"] = cap
    return cfg


def main():
    tmp = tempfile.mkdtemp(prefix="banner-qwin-")
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    rm_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "reminder.py"), "rb").read()
    ).hexdigest()

    cfg = load_cfg(2)
    db = os.path.join(tmp, "qwin.db")
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
    oct_skipped = int(q(
        db, "SELECT COUNT(*) FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%'")[0][0])
    default_read = face.banner_queue()
    none_read = face.banner_queue(window=None)
    oct_read = face.banner_queue(window=OCT_W)
    mirror_oct = q(
        db, "SELECT send_id, census_avatar_id, reason, status,"
        " ts_utc FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%' ORDER BY ts_utc")
    s_oct = dumps(oct_read)
    ok8 = (r_a["status"] == RM.ST_SKIP_BUDGET
           and r_b["status"] == RM.ST_SKIP_BUDGET
           and r_c["status"] == "sent" and r_d["status"] == "sent"
           and r_e["status"] == RM.ST_SKIP_CAP
           and r_f["status"] == RM.ST_SKIP_CAP
           and oct_skipped == 4
           and len(default_read) == 4 and len(none_read) == 4
           and len(oct_read) == 4
           and dumps(default_read) == dumps(mirror_oct)
           and dumps(none_read) == dumps(default_read)
           and dumps(oct_read) == dumps(default_read)
           and default_read[0][1] == "AV-A"
           and default_read[3][1] == "AV-F")
    record("AC-MB8", ok8,
           "oct_skipped=%d default==mirror=%s none==default=%s"
           " window==default_oct_only=%s rows=%d"
           % (oct_skipped,
              dumps(default_read) == dumps(mirror_oct),
              dumps(none_read) == dumps(default_read),
              dumps(oct_read) == dumps(default_read),
              len(default_read)))

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
    nov_read = face.banner_queue(window=NOV_W)
    mirror_nov = q(
        db, "SELECT send_id, census_avatar_id, reason, status,"
        " ts_utc FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%' AND substr(ts_utc,1,7)=?"
        " ORDER BY ts_utc", (NOV_W,))
    full_read = face.banner_queue()
    nov_in_full = [r for r in full_read
                   if r[4][:7] == NOV_W]
    ts_sorted = all(nov_read[i][4] <= nov_read[i + 1][4]
                    for i in range(len(nov_read) - 1))
    ok9 = (n_g["status"] == RM.ST_SKIP_BUDGET
           and n_a["status"] == RM.ST_SKIP_BUDGET
           and n_i["status"] == "sent" and n_k["status"] == "sent"
           and n_j["status"] == RM.ST_SKIP_CAP
           and len(nov_read) == 3
           and dumps(nov_read) == dumps(mirror_nov)
           and dumps(nov_read) == dumps(nov_in_full)
           and ts_sorted
           and [r[1] for r in nov_read] == ["AV-G", "AV-A", "AV-J"]
           and len(full_read) == 7)
    record("AC-MB9", ok9,
           "nov_rows=%d window==mirror=%s window==default_subset=%s"
           " ts_nondecreasing=%s order=%s full=%d"
           % (len(nov_read),
              dumps(nov_read) == dumps(mirror_nov),
              dumps(nov_read) == dumps(nov_in_full),
              ts_sorted, [r[1] for r in nov_read], len(full_read)))

    # ---- 14 bad-window forms fail closed ----------------------
    before10 = (q(db, "SELECT COUNT(*) FROM"
                  " member_reminder_log")[0][0],
                q(db, "SELECT COUNT(*) FROM"
                  " member_subscribe_grants")[0][0])
    rejects = []
    for bad in BADS14:
        try:
            face.banner_queue(window=bad)
            rejects.append((bad, "no-refusal"))
        except ValueError as exc:
            rejects.append((bad, RM.E_REM_BAD_WINDOW in str(exc)))
    after10 = (q(db, "SELECT COUNT(*) FROM"
                 " member_reminder_log")[0][0],
               q(db, "SELECT COUNT(*) FROM"
                 " member_subscribe_grants")[0][0])
    ok10 = (all(r[1] is True for r in rejects)
            and before10 == after10)
    record("AC-MB10", ok10,
           "rejects=%d/%d counts_stable=%s"
           % (sum(1 for r in rejects if r[1] is True),
              len(rejects), before10 == after10))

    # ---- Honest empty window (a month with zero rows) --------
    empty_read = face.banner_queue(window="2026-09")
    ok11 = (empty_read == [])
    record("AC-MB11", ok11,
           "empty_window_rows=%d honest_empty_list=%s"
           % (len(empty_read), empty_read == []))

    # ---- October window preservation after the roll -----------
    oct_after = face.banner_queue(window=OCT_W)
    byte_same = dumps(oct_after) == s_oct
    oct_avatars = set(r[1] for r in oct_after)
    nov_avatars = set(r[1] for r in nov_read)
    no_leak_both_ways = (
        not (nov_avatars & {"AV-B", "AV-E", "AV-F"})
        and not (oct_avatars & {"AV-G", "AV-J"})
        and len(full_read) == 7)
    ok12 = (byte_same and no_leak_both_ways)
    record("AC-MB12", ok12,
           "oct_window_byte_identical_after_roll=%s"
           " oct_avatars=%s nov_avatars=%s leak_free=%s"
           % (byte_same, sorted(oct_avatars),
              sorted(nov_avatars), no_leak_both_ways))

    # ---- Telescoping + board-total interlock -------------------
    full_ids = set(r[0] for r in full_read)
    oct_ids = set(r[0] for r in oct_after)
    nov_ids = set(r[0] for r in nov_read)
    tele = (oct_ids | nov_ids == full_ids
            and not (oct_ids & nov_ids)
            and len(oct_ids) + len(nov_ids) == len(full_ids))
    board_oct = face.banner_board(window=OCT_W)["total"]
    board_nov = face.banner_board(window=NOV_W)["total"]
    board_all = face.banner_board()["total"]
    interlock = (len(oct_after) == board_oct
                 and len(nov_read) == board_nov
                 and len(full_read) == board_all
                 and board_oct + board_nov == board_all == 7)
    ok13 = (tele and interlock)
    record("AC-MB13", ok13,
           "partition_union=%s disjoint=%s interlock_queue_len=="
           "board_total: oct %d==%d nov %d==%d full %d==%d"
           % (oct_ids | nov_ids == full_ids,
              not (oct_ids & nov_ids),
              len(oct_after), board_oct,
              len(nov_read), board_nov,
              len(full_read), board_all))

    # ---- Pure-read law ----------------------------------------
    src = inspect.getsource(RM.ReminderFace.banner_queue)
    writes = [kw for kw in WRITE_KW if kw in src]
    before14 = int(q(db, "SELECT COUNT(*) FROM"
                    " member_reminder_log")[0][0])
    face.banner_queue()
    face.banner_queue(window=OCT_W)
    face.banner_queue(window=NOV_W)
    face.banner_queue(window="2026-09")
    after14 = int(q(db, "SELECT COUNT(*) FROM"
                   " member_reminder_log")[0][0])
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
    ok14 = (not writes and before14 == after14 == 11
            and ascii_ok and not net_hits
            and cfg_sha_in == cfg_sha_out
            and rm_sha_in == rm_sha_out and world_outside_repo)
    record("AC-MB14", ok14,
           "write_keywords=%s count_stable=%s (%d==%d)"
           " ascii=%s net_imports=%s cfg_unchanged=%s"
           " reminder_unchanged=%s world_outside_repo=%s"
           % (writes, before14 == after14, before14, after14,
              ascii_ok, net_hits, cfg_sha_in == cfg_sha_out,
              rm_sha_in == rm_sha_out, world_outside_repo))

    shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE PASS %d/%d" % (passed, EXPECTED), flush=True)
    if passed != EXPECTED or len(RESULTS) != EXPECTED:
        sys.exit(1)


if __name__ == "__main__":
    main()
