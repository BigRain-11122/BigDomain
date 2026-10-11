"""Acceptance suite for the event-ticket audit-board window
parameterization (BigDomain R1826 tech-queue row; seed =
eventtickets.py event_audit_board R1771/R1788). Asserts the
pre-registered criteria AC-EAW1..AC-EAW7 from the R1826
tech.md claim line (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Family law = the R1730/R1793 window-parameterization line:
default None keeps the full-window behavior byte-stable; an
explicit YYYY-MM month window filters sold/revenue by
purchased_utc and admitted by checked_utc (record-time
columns, each row family on its own provenance stamp - the
seed verdict); no_show in a windowed read is the
end-of-window snapshot (purchases month<=W minus check-ins
month<=W, structurally non-negative because every check-in
row pairs with a purchase that precedes it in the product
flow - the same per-pair law the full board pairs by); the
in-window net flow is deliberately NOT surfaced under the
no_show field name; the admission rate stays the
window-filtered ratio under the zero-sold guard; a
malformed window fails closed E_ET_BAD_ARGS before any
read.

History rows are injected straight into the ticket tables by
this fixture (test-side direct writes, the R1730 family
precedent, noted here): the product gates are bypassed on
purpose so two synthetic past months can be pinned
deterministically. Injected rows respect the temporal order
the product flow enforces (a check-in row only exists with
its purchase month at or before it).

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_eventtickets_boardwin.py
"""

import datetime
import inspect
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                      # noqa: E402 (P-47-2b core)
import eventtickets as T                # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7

DISCLAIMER = ("sandbox stand-in disclaimer: virtual event tickets"
             " grant admission only, not investment advice")

ROW_KEYS = {"session_key", "title", "ai_label", "sold",
            "admitted", "no_show", "revenue", "admission_rate"}

BAD_FORMS = ["2026-13", "2026-00", "2026-1", "2026/10", "2026",
             "202610", "abcd", "", 2026, True, 2.5,
             "2026-10\n", "2026-10 ", "2026-10\r"]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def _month_now():
    return datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m")


def _prev_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    m -= 1
    if m == 0:
        y, m = y - 1, 12
    return "%04d-%02d" % (y, m)


def _next_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    m += 1
    if m == 13:
        y, m = y + 1, 1
    return "%04d-%02d" % (y, m)


def _stamp(ym, day):
    return "%s-%02dT12:00:00Z" % (ym, day)


def main():
    cur_m = _month_now()
    m2 = _prev_month(cur_m)          # the recent history month
    m1 = _prev_month(m2)             # the older history month
    fut = _next_month(cur_m)         # the future month

    tmp = tempfile.mkdtemp(prefix="eventtickets-boardwin-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    tf = T.EventTicketFace(led, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 2000, "SETUP-EAW-A",
                     "settlement")
    for who, amount, tag in (("alice", 100, "a"), ("bob", 100, "b"),
                             ("dave", 100, "d")):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag,
                   "suite funding " + who)

    import sqlite3
    conn = sqlite3.connect(db_path)

    def _counts():
        return tuple(
            conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
            for t in ("ticket_sessions", "ticket_purchases",
                      "ticket_checkins"))

    def _manual_flow(sid, w):
        s = conn.execute(
            "SELECT COUNT(*) FROM ticket_purchases"
            " WHERE session_id = ?"
            " AND substr(purchased_utc, 1, 7) = ?",
            (sid, w)).fetchone()[0]
        a = conn.execute(
            "SELECT COUNT(*) FROM ticket_checkins"
            " WHERE session_id = ?"
            " AND substr(checked_utc, 1, 7) = ?",
            (sid, w)).fetchone()[0]
        rev = conn.execute(
            "SELECT COALESCE(SUM(price_paid), 0) FROM"
            " ticket_purchases WHERE session_id = ?"
            " AND substr(purchased_utc, 1, 7) = ?",
            (sid, w)).fetchone()[0]
        return int(s), int(a), int(rev)

    def _manual_snapshot_noshow(sid, w):
        p = conn.execute(
            "SELECT COUNT(*) FROM ticket_purchases"
            " WHERE session_id = ?"
            " AND substr(purchased_utc, 1, 7) <= ?",
            (sid, w)).fetchone()[0]
        c = conn.execute(
            "SELECT COUNT(*) FROM ticket_checkins"
            " WHERE session_id = ?"
            " AND substr(checked_utc, 1, 7) <= ?",
            (sid, w)).fetchone()[0]
        return int(p) - int(c)

    # -- real-API world (all rows stamped in the current month) --
    s_gala = tf.register_session("alpha-gala", "Alpha Gala Night",
                                 10, 20, 5, 2, False)
    s_zulu = tf.register_session("zulu-empty",
                                 "Zulu Registered No Sales",
                                 0, 5, 1, 1, True)
    tf.buy_ticket("usr:alice", s_gala["session_id"], 10,
                  "order:eaw1")
    tf.buy_ticket("usr:alice", s_gala["session_id"], 15,
                  "order:eaw2")
    tf.buy_ticket("usr:bob", s_gala["session_id"], 12,
                  "order:eaw3")
    tf.admit("usr:alice", s_gala["session_id"], 12)

    # -- AC-EAW1 contract, default zero drift, additive window ----
    full1 = tf.event_audit_board()
    full2 = tf.event_audit_board()
    ok1_keys = (set(full1.keys()) ==
                {"event_audit_board", "disclaimer"}
                and full1["disclaimer"] == DISCLAIMER)
    ok1_det = (json.dumps(full1, sort_keys=True)
               == json.dumps(full2, sort_keys=True))
    rows_full = full1["event_audit_board"]
    ok1_rows = (len(rows_full) == 2
                and all(set(r.keys()) == ROW_KEYS
                        for r in rows_full)
                and [r["session_key"] for r in rows_full] ==
                ["alpha-gala", "zulu-empty"])
    ok1_manual = True
    for r in rows_full:
        # session_key is unique; resolve id by key for manual SQL
        sid = conn.execute(
            "SELECT session_id FROM ticket_sessions"
            " WHERE session_key = ?",
            (r["session_key"],)).fetchone()[0]
        g = conn.execute(
            "SELECT COUNT(*) FROM ticket_purchases"
            " WHERE session_id = ?", (sid,)).fetchone()[0]
        c = conn.execute(
            "SELECT COUNT(*) FROM ticket_checkins"
            " WHERE session_id = ?", (sid,)).fetchone()[0]
        rev = conn.execute(
            "SELECT COALESCE(SUM(price_paid), 0) FROM"
            " ticket_purchases WHERE session_id = ?",
            (sid,)).fetchone()[0]
        ok1_manual = ok1_manual and (
            r["sold"] == int(g) and r["admitted"] == int(c)
            and r["no_show"] == int(g) - int(c)
            and r["revenue"] == int(rev)
            and r["admission_rate"] == (round(int(c) / int(g), 4)
                                        if int(g) else 0.0))
    win_read = tf.event_audit_board(cur_m)
    ok1_add = (set(win_read.keys()) ==
               {"event_audit_board", "window", "disclaimer"}
               and win_read["window"] == cur_m)
    ok1_cur = (win_read["event_audit_board"] == rows_full)
    record("AC-EAW1", ok1_keys and ok1_det and ok1_rows
           and ok1_manual and ok1_add and ok1_cur,
           "default envelope keys exact=%s; double-call"
           " byte-identical=%s; rows manual-SQL equal=%s;"
           " explicit window adds key window=%s additive;"
           " cur-month window == full board for the"
           " all-current-month world=%s"
           % (ok1_keys, ok1_det, ok1_manual, ok1_add, ok1_cur))

    # -- AC-EAW2 malformed window fail-closed ----------------------
    before = _counts()
    rejects = 0
    for bad in BAD_FORMS:
        try:
            tf.event_audit_board(bad)
        except T.TicketError as exc:
            if exc.code == T.E_ET_BAD_ARGS:
                rejects += 1
    after = _counts()
    ok2 = (rejects == len(BAD_FORMS) and before == after)
    record("AC-EAW2", ok2,
           "%d/%d malformed forms rejected E_ET_BAD_ARGS"
           " (11 base + 3 trailing R1748 forms); default"
           " sentinel is None only (empty string rejected);"
           " three-table counts flat %s -> %s"
           % (rejects, len(BAD_FORMS), before, after))

    # -- history injection (test-side direct writes, noted) -------
    s_x = tf.register_session("xmonth-cross",
                              "Cross Month Case", 0, 5, 3, 1, False)
    s_i = tf.register_session("inmonth-full",
                             "In Month Full Funnel", 0, 5, 4, 1,
                             False)
    conn.execute(
        "INSERT INTO ticket_purchases (session_id, buyer_id,"
        " purchase_ref, price_paid, spend_tx, purchase_window,"
        " purchased_utc) VALUES (?,?,?,?,?,?,?)",
        (s_x["session_id"], "usr:fx", "inject:fx1", 3,
         "inject:spend-x", 1, _stamp(m1, 5)))
    conn.execute(
        "INSERT INTO ticket_checkins (session_id, account_id,"
        " at_window, checked_utc) VALUES (?,?,?,?)",
        (s_x["session_id"], "usr:fx", 2, _stamp(m2, 7)))
    conn.execute(
        "INSERT INTO ticket_purchases (session_id, buyer_id,"
        " purchase_ref, price_paid, spend_tx, purchase_window,"
        " purchased_utc) VALUES (?,?,?,?,?,?,?)",
        (s_i["session_id"], "usr:fi", "inject:fi1", 4,
         "inject:spend-i", 1, _stamp(m2, 9)))
    conn.execute(
        "INSERT INTO ticket_checkins (session_id, account_id,"
        " at_window, checked_utc) VALUES (?,?,?,?)",
        (s_i["session_id"], "usr:fi", 2, _stamp(m2, 21)))
    conn.commit()

    def _board(w):
        return {r["session_key"]: r for r in
                tf.event_audit_board(w)["event_audit_board"]}

    def _sid(key):
        return conn.execute(
            "SELECT session_id FROM ticket_sessions"
            " WHERE session_key = ?", (key,)).fetchone()[0]

    # -- AC-EAW3 record-time window filter semantics ---------------
    r_m2 = _board(m2)
    ok3_dense = len(r_m2) == 4      # registry-driven axis, dense
    ok3_hist = True
    trace3 = []
    for key in ("xmonth-cross", "inmonth-full", "alpha-gala",
                "zulu-empty"):
        s, a, rev = _manual_flow(_sid(key), m2)
        ok3_hist = ok3_hist and (
            r_m2[key]["sold"] == s
            and r_m2[key]["admitted"] == a
            and r_m2[key]["revenue"] == rev)
        trace3.append("%s s=%d a=%d rev=%d" % (key, s, a, rev))
    ok3_no_leak = (r_m2["alpha-gala"]["sold"] == 0
                   and r_m2["alpha-gala"]["admitted"] == 0)
    r_cur = _board(cur_m)
    ok3_cur_leak = (r_cur["xmonth-cross"]["sold"] == 0
                    and r_cur["xmonth-cross"]["admitted"] == 0
                    and r_cur["alpha-gala"]["sold"] == 3)
    r_m1 = _board(m1)
    ok3_m1 = (r_m1["xmonth-cross"]["sold"] == 1
              and r_m1["xmonth-cross"]["admitted"] == 0
              and r_m1["inmonth-full"]["sold"] == 0)
    r_fut = tf.event_audit_board(fut)
    ok3_fut = (all(r["sold"] == 0 and r["admitted"] == 0
                   and r["revenue"] == 0
                   for r in r_fut["event_audit_board"])
               and len(r_fut["event_audit_board"]) == 4
               and r_fut["window"] == fut)
    full_now = tf.event_audit_board()
    ok3_full_contains = (
        {r["session_key"] for r in
         full_now["event_audit_board"]}
        == {"alpha-gala", "zulu-empty", "xmonth-cross",
            "inmonth-full"})
    record("AC-EAW3", ok3_dense and ok3_hist and ok3_no_leak
           and ok3_cur_leak and ok3_m1 and ok3_fut
           and ok3_full_contains,
           "windowed cells == manual SQL per record-time"
           " column [%s]; history window carries zero"
           " current-month rows=%s; current-month window"
           " carries zero history rows=%s; older month read"
           " exact=%s; future window honest zeros dense=%s;"
           " default full-window still shows every session=%s"
           % ("; ".join(trace3), ok3_no_leak, ok3_cur_leak,
              ok3_m1, ok3_fut, ok3_full_contains))

    # -- AC-EAW4 no_show end-of-window snapshot --------------
    ok4_cross = (r_m2["xmonth-cross"]["sold"] == 0
                 and r_m2["xmonth-cross"]["admitted"] == 1
                 and r_m2["xmonth-cross"]["no_show"] == 0)
    ok4_m1_snap = (r_m1["xmonth-cross"]["no_show"] == 1)
    ok4_manual = all(
        r["no_show"] == _manual_snapshot_noshow(
            _sid(r["session_key"]), w)
        for w in (m1, m2, cur_m, fut)
        for r in tf.event_audit_board(w)
        ["event_audit_board"])
    ok4_nonneg = all(
        r["no_show"] >= 0
        for w in (m1, m2, cur_m, fut)
        for r in tf.event_audit_board(w)
        ["event_audit_board"])
    record("AC-EAW4", ok4_cross and ok4_m1_snap
           and ok4_manual and ok4_nonneg,
           "cross-month case (purchase %s + check-in %s):"
           " window %s sold_w=0 admitted_w=1"
           " no_show=0 (net-flow -1 never surfaced under the"
           " field name)=%s; older-month snapshot no_show=1=%s;"
           " every windowed no_show == manual cumulative"
           " SQL=%s; no_show >= 0 across all windows=%s"
           % (m1, m2, m2, ok4_cross, ok4_m1_snap,
              ok4_manual, ok4_nonneg))

    # -- AC-EAW5 admission_rate window path ------------------------
    ok5_cross = (r_m2["xmonth-cross"]["admission_rate"] == 0.0)
    ok5_full = (r_m2["inmonth-full"]["admission_rate"] == 1.0)
    ok5_manual = all(
        r["admission_rate"] == (round(r["admitted"]
                                      / r["sold"], 4)
                                if r["sold"] > 0 else 0.0)
        for r in tf.event_audit_board(m2)
        ["event_audit_board"])
    record("AC-EAW5", ok5_cross and ok5_full and ok5_manual,
           "zero-sold guard in window (sold_w=0,"
           " admitted_w=1 -> rate 0.0)=%s; in-month full"
           " funnel rate 1.0=%s; every windowed rate =="
           " windowed ratio arithmetic=%s"
           % (ok5_cross, ok5_full, ok5_manual))

    # -- AC-EAW6 revenue window face -------------------------------
    ok6_m1 = (r_m1["xmonth-cross"]["revenue"] == 3
              and r_m2["xmonth-cross"]["revenue"] == 0)
    ok6_m2 = (r_m2["inmonth-full"]["revenue"] == 4)
    ok6_manual = all(
        r["revenue"] == _manual_flow(_sid(r["session_key"]),
                                     w)[2]
        for w in (m1, m2, cur_m, fut)
        for r in tf.event_audit_board(w)
        ["event_audit_board"])
    sum_all = conn.execute(
        "SELECT COALESCE(SUM(price_paid), 0) FROM"
        " ticket_purchases").fetchone()[0]
    ok6_full = (sum(int(r["revenue"]) for r in
                    full_now["event_audit_board"])
                == int(sum_all))
    record("AC-EAW6", ok6_m1 and ok6_m2 and ok6_manual
           and ok6_full,
           "cross-month revenue lands in the purchase month"
           " (m1 rev=3, m2 rev=0)=%s; in-month rev=4=%s;"
           " every windowed revenue == manual SQL=%s;"
           " full-board revenue sum == SUM(price_paid) over"
           " all purchases (%d)=%s"
           % (ok6_m1, ok6_m2, ok6_manual, int(sum_all),
              ok6_full))

    # -- AC-EAW7 pure-read law + liveness + determinism ------------
    counts0 = _counts()
    for w in (None, m1, m2, cur_m, fut):
        tf.event_audit_board(w)
    counts1 = _counts()
    method_src = inspect.getsource(
        T.EventTicketFace.event_audit_board)
    ok7_pure = (counts0 == counts1
                and "INSERT" not in method_src
                and "UPDATE" not in method_src
                and "DELETE" not in method_src)
    w1 = json.dumps(tf.event_audit_board(m2), sort_keys=True)
    w2 = json.dumps(tf.event_audit_board(m2), sort_keys=True)
    ok7_det = w1 == w2
    # liveness: a fresh current-month purchase moves the
    # current-month window on re-read; the history window
    # stays unchanged (zero cached state).
    tf.buy_ticket("usr:dave", s_zulu["session_id"], 3,
                  "order:eaw-live")
    cur_after = _board(cur_m)
    hist_after = _board(m2)
    ok7_live = (cur_after["zulu-empty"]["sold"] == 1
                and hist_after["zulu-empty"]["sold"] == 0)
    with open(os.path.join(BASE, "eventtickets.py"),
              encoding="utf-8") as handle:
        src = handle.read()
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [ln for ln in src.splitlines()
                    if (ln.startswith("import ")
                        or ln.startswith("from "))]
    net_imports = [ln for ln in import_lines
                   if any(w in ln for w in
                          ("urllib", "requests", "socket", "http"))]
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    with open(os.path.join(
            os.path.dirname(BASE), "reconcile_all.py"),
            encoding="utf-8") as handle:
        runner_src = handle.read()
    ok7 = (non_ascii == 0 and not net_imports
           and "UPDATE ticket_" not in src
           and "random" not in src
           and cfg_after == cfg_bytes
           and 'ledger-eventtickets-boardwin' in runner_src
           and len(RESULTS) + 1 == EXPECTED)
    record("AC-EAW7", ok7,
           "three-table counts flat %s; method source carries"
           " zero data-changing statements (inspect)=%s;"
           " windowed double-call byte-identical=%s; fresh"
           " purchase moves cur-month window 0->1 while history"
           " window stays 0=%s; module pure ASCII (%d"
           " non-ascii); zero network imports (%d); zero"
           " mutation surface for own tables; zero dice;"
           " config.json byte-stable; reconcile_all SUITES"
           " row 'ledger-eventtickets-boardwin' registered;"
           " criteria drift self-check %d/%d"
           % (counts0 == counts1, ok7_pure, ok7_det, ok7_live,
              non_ascii, len(net_imports), len(RESULTS),
              EXPECTED))

    conn.close()
    tf.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
