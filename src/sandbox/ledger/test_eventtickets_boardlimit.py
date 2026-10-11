"""Acceptance suite for the event-ticket audit-board read-cap
parameterization (BigDomain R1840 tech-queue row; seed =
eventtickets.py event_audit_board window R1826 + monthcross
probe R1834). Asserts the pre-registered criteria AC-ETL1..
AC-ETL7 from the R1840 tech.md claim line (criteria were
registered before this code existed; honesty law).

Family law = the R1729 usage_log / R1804 journal_board
read-cap line: the default limit=0 keeps the full board
byte-identical (no extra key); a positive limit keeps the
last N sessions in session_key ascending order - the tail
window, the same rows the mirror clause (ORDER BY
session_key DESC LIMIT N, reversed back) yields; window
filtering runs before the cap (orthogonal), the overflow
block reports the in-window full count under "total" (never
the post-truncation count - a capped read never lies about
what it left out); a malformed limit fails closed
E_ET_BAD_LIMIT before the window gate (the double-bad
gate-order law; the sole sentinel is 0).

Design verdict from the claim line (registered before the
code): the overflow block is FOUR keys {limit, total,
returned, truncated} - the R1729 usage_log same-type shape -
because the default event_audit_board envelope carries no
"total" key (unlike journal_board whose default already had
one), and an honest truncation read must carry the full
count. The seed line's "three keys" is corrected in the
claim line per the R1704 precedent.

One history row is injected straight into ticket_purchases by
this fixture (test-side direct write, the R1730 family
precedent, noted here) so windowed reads carry distinct cell
values; the board's row axis stays the registry-driven dense
session axis in every window (the AC-EAW3 law), so the
orthogonality face asserts row sets, not cell arithmetic
(covered by the boardwin suite).

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_eventtickets_boardlimit.py
"""

import datetime
import hashlib
import inspect
import json
import os
import sqlite3
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

CAP_KEYS = {"limit", "total", "returned", "truncated"}

BAD_LIMITS = [-1, True, "2", 2.5, None]


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
    m1 = _prev_month(_prev_month(cur_m))   # the older history month
    fut = _next_month(cur_m)              # the future month

    tmp = tempfile.mkdtemp(prefix="eventtickets-boardlimit-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    tf = T.EventTicketFace(led, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 2000, "SETUP-ETL-A",
                     "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.adjust([("pool:reserve", "debit", 100),
                ("usr:alice", "credit", 100)],
               "manual:fund-alice",
               "suite funding alice")

    # real-API world: four registered sessions (ascending keys)
    s_a = tf.register_session("alpha-gala", "Alpha Gala Night",
                              10, 20, 5, 2, False)
    tf.register_session("m-bravo", "Bravo Session", 0, 5, 3, 1,
                        True)
    tf.register_session("m-charlie", "Charlie Session", 0, 5,
                       4, 1, False)
    tf.register_session("zulu-empty",
                        "Zulu Registered No Sales", 0, 5, 1, 1,
                        True)
    tf.buy_ticket("usr:alice", s_a["session_id"], 10,
                  "order:etl1")
    tf.admit("usr:alice", s_a["session_id"], 12)

    # independent read-only connection (the R1814 mirror-SQL
    # law): used for the mirror clause, the counts and the
    # session-id resolve; the one history injection below is
    # the sole test-side write and goes through its own
    # short-lived writable connection.
    probe = sqlite3.connect(
        "file:" + db_path.replace("\\", "/") + "?mode=ro",
        uri=True)

    def _counts():
        return tuple(
            probe.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
            for t in ("ticket_sessions", "ticket_purchases",
                      "ticket_checkins"))

    sid_b = probe.execute(
        "SELECT session_id FROM ticket_sessions"
        " WHERE session_key = ?", ("m-bravo",)).fetchone()[0]
    wconn = sqlite3.connect(db_path)
    wconn.execute(
        "INSERT INTO ticket_purchases (session_id, buyer_id,"
        " purchase_ref, price_paid, spend_tx, purchase_window,"
        " purchased_utc) VALUES (?,?,?,?,?,?,?)",
        (sid_b, "usr:hx", "inject:hx1", 3, "inject:spend-hx", 1,
         _stamp(m1, 5)))
    wconn.commit()
    wconn.close()

    # -- AC-ETL1 contract, default zero drift, additive keys ------
    full1 = tf.event_audit_board()
    full2 = tf.event_audit_board()
    ok1_def_keys = (set(full1.keys()) ==
                    {"event_audit_board", "disclaimer"}
                    and full1["disclaimer"] == DISCLAIMER)
    ok1_det = (json.dumps(full1, sort_keys=True)
               == json.dumps(full2, sort_keys=True))
    rows_full = full1["event_audit_board"]
    ok1_rows = (len(rows_full) == 4
                and [r["session_key"] for r in rows_full] ==
                ["alpha-gala", "m-bravo", "m-charlie",
                 "zulu-empty"]
                and all(set(r.keys()) == ROW_KEYS
                        for r in rows_full))
    cap2 = tf.event_audit_board(limit=2)
    ok1_add = (set(cap2.keys()) ==
               {"event_audit_board", "disclaimer"} | CAP_KEYS
               and cap2["limit"] == 2)
    wl = tf.event_audit_board(cur_m, 2)
    ok1_coexist = (set(wl.keys()) ==
                   {"event_audit_board", "disclaimer", "window"}
                   | CAP_KEYS
                   and wl["window"] == cur_m)
    record("AC-ETL1", ok1_def_keys and ok1_det and ok1_rows
           and ok1_add and ok1_coexist,
           "default limit=0 envelope keys exact=%s;"
           " double-call byte-identical=%s; 4 sessions"
           " ascending with the 8-key row shape=%s; limit>0"
           " adds exactly four keys"
           " {limit,total,returned,truncated}=%s; window+limit"
           " keys coexist=%s"
           % (ok1_def_keys, ok1_det, ok1_rows, ok1_add,
              ok1_coexist))

    # -- AC-ETL2 malformed limit fail-closed + gate order ---------
    before = _counts()
    rejects = 0
    for bad in BAD_LIMITS:
        try:
            tf.event_audit_board(limit=bad)
        except T.TicketError as exc:
            if exc.code == T.E_ET_BAD_LIMIT:
                rejects += 1
    after = _counts()
    ok2_forms = (rejects == len(BAD_LIMITS)
                 and before == after)
    ok2_order = False
    try:
        tf.event_audit_board("2026-13", -1)
    except T.TicketError as exc:
        ok2_order = (exc.code == T.E_ET_BAD_LIMIT)
    ok2_win = False
    try:
        tf.event_audit_board("2026-13")
    except T.TicketError as exc:
        ok2_win = (exc.code == T.E_ET_BAD_ARGS)
    record("AC-ETL2", ok2_forms and ok2_order and ok2_win,
           "%d/%d malformed limits rejected E_ET_BAD_LIMIT"
           " (-1 / True / \"2\" / 2.5 / None; the sole sentinel"
           " is 0); three-table counts flat %s -> %s;"
           " double-bad (bad window + bad limit) fires"
           " E_ET_BAD_LIMIT first=%s; bad window alone still"
           " E_ET_BAD_ARGS=%s"
           % (rejects, len(BAD_LIMITS), before, after,
              ok2_order, ok2_win))

    # -- AC-ETL3 tail-window truncation semantics ------------------
    tail = tf.event_audit_board(limit=2)
    rows_tail = tail["event_audit_board"]
    ok3_cap = (tail["returned"] == 2
               and tail["truncated"] is True
               and tail["total"] == 4
               and len(rows_tail) == 2)
    ok3_tail_eq = (rows_tail == rows_full[-2:]
                   and [r["session_key"] for r in rows_tail] ==
                   ["m-charlie", "zulu-empty"]
                   and all(set(r.keys()) == ROW_KEYS
                           for r in rows_tail))
    mirror = [r[0] for r in probe.execute(
        "SELECT session_key FROM ticket_sessions"
        " ORDER BY session_key DESC LIMIT 2").fetchall()]
    mirror.reverse()
    ok3_mirror = (mirror ==
                  [r["session_key"] for r in rows_tail])
    record("AC-ETL3", ok3_cap and ok3_tail_eq and ok3_mirror,
           "limit=2: returned=2 truncated=True total=4=%s;"
           " rows == full-read tail slice byte-equal=%s;"
           " mirror SQL (DESC LIMIT 2 reversed) == product"
           " session_key order %s=%s"
           % (ok3_cap, ok3_tail_eq, mirror, ok3_mirror))

    # -- AC-ETL4 boundary states ------------------------------------
    b_eq = tf.event_audit_board(limit=4)
    ok4_eq = (b_eq["truncated"] is False
              and b_eq["returned"] == 4
              and b_eq["event_audit_board"] == rows_full)
    b_over = tf.event_audit_board(limit=50)
    ok4_over = (b_over["truncated"] is False
                and b_over["returned"] == 4
                and b_over["total"] == 4)
    b_one = tf.event_audit_board(limit=1)
    ok4_one = (b_one["returned"] == 1
               and b_one["truncated"] is True
               and [r["session_key"] for r in
                    b_one["event_audit_board"]] == ["zulu-empty"])
    db2 = os.path.join(tmp, "ledger2.db")
    led2 = L.Ledger(db2, cfg)
    tf2 = T.EventTicketFace(led2, DISCLAIMER)
    b0 = tf2.event_audit_board(limit=3)
    ok4_zero = (b0["event_audit_board"] == []
                and b0["returned"] == 0
                and b0["total"] == 0
                and b0["truncated"] is False
                and set(b0.keys()) ==
                {"event_audit_board", "disclaimer"} | CAP_KEYS)
    tf2.close()
    led2.close()
    record("AC-ETL4", ok4_eq and ok4_over and ok4_one
           and ok4_zero,
           "limit==total (4/4): truncated=False all rows=%s;"
           " limit>total (50 over 4)=%s; limit=1 single tail"
           " row=%s; zero-session world limit=3: empty board,"
           " returned=0 total=0 truncated=False with the four"
           " cap keys present=%s"
           % (ok4_eq, ok4_over, ok4_one, ok4_zero))

    # -- AC-ETL5 window x cap orthogonal combination ----------------
    ok5 = True
    trace5 = []
    for w in (m1, cur_m, fut):
        bwf = tf.event_audit_board(w)
        bwl = tf.event_audit_board(w, 2)
        eq = (bwl["event_audit_board"] ==
              bwf["event_audit_board"][-2:])
        ok5 = ok5 and eq and (
            bwl["total"] == len(bwf["event_audit_board"])
            and bwl["returned"] == 2
            and bwl["truncated"] is True
            and bwl["window"] == w)
        trace5.append("%s rows=%d cap-tail-eq=%s"
                      % (w, len(bwf["event_audit_board"]), eq))
    record("AC-ETL5", ok5,
           "window filter before LIMIT, each window"
           " [%s]: capped rows == windowed-full tail slice;"
           " total == in-window full count (registry-driven"
           " dense axis, window-invariant); returned/truncated"
           " computed against the in-window count=%s"
           % ("; ".join(trace5), ok5))

    # -- AC-ETL6 pure-read law + determinism -------------------------
    counts0 = _counts()
    tf.event_audit_board()
    tf.event_audit_board(limit=2)
    tf.event_audit_board(cur_m)
    tf.event_audit_board(cur_m, 2)
    tf.event_audit_board(m1, 3)
    tf.event_audit_board(fut, 1)
    tf.event_audit_board(limit=50)
    counts1 = _counts()
    method_src = inspect.getsource(
        T.EventTicketFace.event_audit_board)
    ok6_pure = (counts0 == counts1
                and "INSERT" not in method_src
                and "UPDATE" not in method_src
                and "DELETE" not in method_src)
    d1 = json.dumps(tf.event_audit_board(m1, 2), sort_keys=True)
    d2 = json.dumps(tf.event_audit_board(m1, 2), sort_keys=True)
    ok6_det = d1 == d2
    record("AC-ETL6", ok6_pure and ok6_det,
           "three-table counts flat across every limit form"
           " %s -> %s; method source carries zero data-changing"
           " statements (inspect)=%s; capped windowed"
           " double-call byte-identical=%s"
           % (counts0, counts1, ok6_pure, ok6_det))

    # -- AC-ETL7 hygiene + delivery -----------------------------------
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
           and "ledger-eventtickets-boardlimit" in runner_src
           and len(RESULTS) + 1 == EXPECTED)
    record("AC-ETL7", ok7,
           "module pure ASCII (%d non-ascii); zero network"
           " imports (%d); zero mutation surface for own"
           " tables; zero dice; config.json byte-stable"
           " (sha16 %s); reconcile_all SUITES row"
           " 'ledger-eventtickets-boardlimit' registered;"
           " criteria drift self-check %d/%d"
           % (non_ascii, len(net_imports),
              hashlib.sha256(cfg_after).hexdigest()[:16],
              len(RESULTS), EXPECTED))

    probe.close()
    tf.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
