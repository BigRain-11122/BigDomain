"""Acceptance suite for the member banner_board month-roll
fidelity example (BigDomain R1861 tech-queue claim row; seed =
the R1851 limit tail param + R1856 window tail param already
shipped on ReminderFace.banner_board - the R1730/R1738/R1739/
R1839/R1845/R1854/R1858/R1859 month-roll family symmetric gap:
member banner_board was the window-parameter family member
without a roll pin).

Asserts the pre-registered criteria AC-MB1..AC-MB7 from the
R1861 tech.md claim line (criteria were registered before
this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any
FAIL.

Carrier verdict (the R1845 devboard_roll / R1858 callroll /
R1859 sec_batch banner_queue dedicated-suite precedent): the
existing test_banner_board.py world reaches past months via
direct fixture injection - this suite instead builds a fresh
isolated face instance in its own temp world and drives the
TRUE product write path end to end: every journal row lands
via attempt()/on_accept() with an explicit ts, so record-time
(ts_utc) is exactly the passed stamp and the month roll rides
the product path itself, zero fixture injection.

World (cap=2 in-memory cfg variant, shipped config.json
untouched): October day - AV-A attempts renewal_due with no
budget (skip_budget), AV-B accepts first_service with no
budget (skip_budget), AV-C/AV-D hold grants and send (cap
exhausted at 2), AV-E attempts with a grant (skip_daily_cap),
AV-F accepts first_service (skip_daily_cap). November day -
AV-G attempts with no budget (skip_budget), AV-A retries the
same reason on the new day (skip_budget - one avatar living in
both month windows), AV-I/AV-K send on the fresh day (daily
cap window resets), AV-J accepts first_service once the cap
is hit (skip_daily_cap). The window param narrows the world
by record-time month; the default read aggregates across
months; the cap slices only the returned list. Immutable rows
never disappear and the totals telescope.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_banner_board_roll.py
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


def dumps(env):
    return json.dumps(env, sort_keys=True)


def strip_window(env):
    """Pop the additive window key for default-vs-explicit
    byte comparison (R1856 additive-envelope law)."""
    env = dict(env)
    env.pop("window", None)
    return env


def load_cfg(cap):
    with open(CFG_PATH, encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg = json.loads(json.dumps(cfg))
    cfg["reminder"]["daily_send_cap_default"] = cap
    return cfg


def main():
    tmp = tempfile.mkdtemp(prefix="banner-roll-")
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    rm_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "reminder.py"), "rb").read()
    ).hexdigest()

    cfg = load_cfg(2)
    db = os.path.join(tmp, "roll.db")
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
    oct_status = dict((r[0], r[1]) for r in q(
        db, "SELECT status, COUNT(*) FROM member_reminder_log"
        " GROUP BY status"))
    oct_skip_ids = [r[0] for r in q(
        db, "SELECT send_id FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%' ORDER BY send_id")]
    default_oct = face.banner_board()
    explicit_oct = face.banner_board(window=OCT_W)
    same_oct = (dumps(strip_window(explicit_oct))
               == dumps(default_oct))
    s_oct = dumps(explicit_oct)
    board_ids = [r["census_avatar_id"] for r in
                 explicit_oct["banner_board"]]
    ok1 = (r_a["status"] == RM.ST_SKIP_BUDGET
           and r_b["status"] == RM.ST_SKIP_BUDGET
           and r_c["status"] == "sent" and r_d["status"] == "sent"
           and r_e["status"] == RM.ST_SKIP_CAP
           and r_f["status"] == RM.ST_SKIP_CAP
           and oct_status.get("skipped_no_budget") == 2
           and oct_status.get("skipped_daily_cap") == 2
           and oct_status.get("sent") == 2
           and len(oct_skip_ids) == 4 and same_oct
           and board_ids == ["AV-A", "AV-B", "AV-E", "AV-F"]
           and explicit_oct["total"] == 4
           and explicit_oct["by_status"] == {
               "skipped_no_budget": 2, "skipped_daily_cap": 2}
           and explicit_oct["by_reason"] == {
               "first_service": 2, "renewal_due": 2})
    record("AC-MB1", ok1,
           "oct_status=%s rows_default==explicit_oct=%s"
           " board=%s total=%d oct_skip_ids=%d"
           % (sorted(oct_status.items()), same_oct, board_ids,
              explicit_oct["total"], len(oct_skip_ids)))

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
    nov_rows = q(
        db, "SELECT COUNT(*) FROM member_reminder_log"
        " WHERE substr(ts_utc,1,7)=?", (NOV_W,))
    nov_skipped = int(q(
        db, "SELECT COUNT(*) FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%' AND substr(ts_utc,1,7)=?",
        (NOV_W,))[0][0])
    explicit_nov = face.banner_board(window=NOV_W)
    nov_ids = [r["census_avatar_id"] for r in
               explicit_nov["banner_board"]]
    default_all = face.banner_board()
    all_ids = [r["census_avatar_id"] for r in
               default_all["banner_board"]]
    row_a = [r for r in default_all["banner_board"]
             if r["census_avatar_id"] == "AV-A"][0]
    ok2 = (n_g["status"] == RM.ST_SKIP_BUDGET
           and n_a["status"] == RM.ST_SKIP_BUDGET
           and n_i["status"] == "sent" and n_k["status"] == "sent"
           and n_j["status"] == RM.ST_SKIP_CAP
           and nov_rows[0][0] == 5 and nov_skipped == 3
           and nov_ids == ["AV-A", "AV-G", "AV-J"]
           and explicit_nov["total"] == 3
           and explicit_nov["window"] == NOV_W
           and all_ids == ["AV-A", "AV-B", "AV-E", "AV-F",
                           "AV-G", "AV-J"]
           and row_a["skipped"] == 2)
    record("AC-MB2", ok2,
           "nov_rows=%d nov_skipped=%d nov_board=%s nov_total=%d"
           " default_board=%d avatars av-A-merged=%s"
           % (nov_rows[0][0], nov_skipped, nov_ids,
              explicit_nov["total"], len(all_ids), row_a))

    # ---- October window preservation after the roll -----------
    oct_after = face.banner_board(window=OCT_W)
    byte_same = dumps(oct_after) == s_oct
    a_oct = [r for r in oct_after["banner_board"]
             if r["census_avatar_id"] == "AV-A"][0]
    a_nov = [r for r in explicit_nov["banner_board"]
             if r["census_avatar_id"] == "AV-A"][0]
    no_leak_both_ways = (
        a_oct["skipped"] == 1 and a_nov["skipped"] == 1
        and not (set(nov_ids) & {"AV-B", "AV-E", "AV-F"})
        and not (set([r["census_avatar_id"] for r in
                      oct_after["banner_board"]])
                 & {"AV-G", "AV-J"}))
    ok3 = byte_same and no_leak_both_ways
    record("AC-MB3", ok3,
           "oct_window_byte_identical_after_roll=%s"
           " av-A-oct=%d av-A-nov=%s leak-free=%s"
           % (byte_same, a_oct["skipped"], a_nov, no_leak_both_ways))

    # ---- Immutable rows never lost + totals telescope ----------
    total_all = int(q(db, "SELECT COUNT(*) FROM"
                      " member_reminder_log")[0][0])
    oct_ids_now = [r[0] for r in q(
        db, "SELECT send_id FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%' AND"
        " substr(ts_utc,1,7)=? ORDER BY send_id", (OCT_W,))]
    oct_total = face.banner_board(window=OCT_W)["total"]
    nov_total = face.banner_board(window=NOV_W)["total"]
    tele = (default_all["total"] == oct_total + nov_total == 7)
    ok4 = (total_all == 11 and oct_ids_now == oct_skip_ids
           and tele)
    record("AC-MB4", ok4,
           "full_count=%d oct_ids_preserved=%s telescoping=%s"
           " (%d==%d+%d)"
           % (total_all, oct_ids_now == oct_skip_ids, tele,
              default_all["total"], oct_total, nov_total))

    # ---- Window x cap x cross-month orthogonality --------------
    cap_nov = face.banner_board(limit=2, window=NOV_W)
    cap_oct = face.banner_board(limit=1, window=OCT_W)
    nov_full = explicit_nov["banner_board"]
    ok5 = (set(cap_nov) == {"banner_board", "total", "by_status",
                            "by_reason", "ai_generated",
                            "disclaimer", "persistent", "window",
                            "limit", "banner_board_total",
                            "returned", "truncated"}
           and cap_nov["window"] == NOV_W
           and cap_nov["limit"] == 2
           and cap_nov["banner_board_total"] == 3
           and cap_nov["returned"] == 2
           and cap_nov["truncated"] is True
           and cap_nov["banner_board"] == nov_full[-2:]
           and cap_oct["banner_board_total"] == 4
           and cap_oct["returned"] == 1
           and cap_oct["truncated"] is True
           and cap_oct["banner_board"] == json.loads(s_oct)
           ["banner_board"][-1:]
           and cap_oct["total"] == 4)
    record("AC-MB5", ok5,
           "nov-cap env 12 keys + total==%d returned==%d"
           " truncated==%s oct-cap total==%d returned==%d"
           % (cap_nov["banner_board_total"], cap_nov["returned"],
              cap_nov["truncated"], cap_oct["banner_board_total"],
              cap_oct["returned"]))

    # ---- Pure-read law ----------------------------------------
    src = inspect.getsource(RM.ReminderFace.banner_board)
    writes = [kw for kw in WRITE_KW if kw in src]
    before = int(q(db, "SELECT COUNT(*) FROM"
                   " member_reminder_log")[0][0])
    face.banner_board(window=OCT_W)
    face.banner_board(limit=1, window=NOV_W)
    face.banner_board()
    after = int(q(db, "SELECT COUNT(*) FROM"
                  " member_reminder_log")[0][0])
    ok6 = (not writes and before == after == 11)
    record("AC-MB6", ok6,
           "write_keywords=%s count_stable=%s (%d==%d)"
           % (writes, before == after, before, after))
    face.close()

    # ---- Hygiene: ASCII, imports, shipped bytes, temp world ---
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
    ok7 = (ascii_ok and not net_hits
           and cfg_sha_in == cfg_sha_out
           and rm_sha_in == rm_sha_out and world_outside_repo)
    record("AC-MB7", ok7,
           "ascii=%s net_imports=%s cfg_unchanged=%s"
           " reminder_unchanged=%s world_outside_repo=%s"
           % (ascii_ok, net_hits, cfg_sha_in == cfg_sha_out,
              rm_sha_in == rm_sha_out, world_outside_repo))

    shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE PASS %d/%d" % (passed, EXPECTED), flush=True)
    if passed != EXPECTED or len(RESULTS) != EXPECTED:
        sys.exit(1)


if __name__ == "__main__":
    main()
