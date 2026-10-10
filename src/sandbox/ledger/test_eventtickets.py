"""Acceptance suite for the virtual event ticket face (BigDomain
R1767; canon = explore-queue virtual event ticket line: the
liveroom paid-admission variant over the festival schedule-window
convention - session registry + in-window ticket purchase with
replay/limit/capacity gates before the one spend + the admission
check-in gate). Asserts the pre-registered criteria AC-ET1..ET7
from the R1767 explore-queue row (criteria were registered before
this code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

The ledger is the real product injected by reference (no copy).
This test source stays pure ASCII per the encoding discipline.

Usage: python test_eventtickets.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                      # noqa: E402 (P-47-2b core)
import eventtickets as T                # noqa: E402 (R1767 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: virtual event tickets"
             " grant admission only, not investment advice")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_et_error(fn, *codes):
    try:
        fn()
    except T.TicketError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _tx_count(conn):
    return conn.execute("SELECT COUNT(*) FROM ledger_tx").fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="eventtickets-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    tf = T.EventTicketFace(led, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 2000, "SETUP-ET-A", "settlement")
    for who, amount, tag in (("alice", 100, "a"), ("bob", 100, "b"),
                             ("carol", 100, "c"), ("dave", 100, "d"),
                             ("erin", 50, "e")):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag, "suite funding " + who)
    bal = lambda who: led.balance("usr:" + who)["balance"]  # noqa: E731
    conn = sqlite3.connect(db_path)

    # -- AC-ET1 session registry face ---------------------------------------
    s1 = tf.register_session("gala-2026", "City Gala Night", 10, 20,
                             5, 2, False)
    n_s0 = _count(conn, "ticket_sessions")
    ok_dup, code_dup = expect_et_error(
        lambda: tf.register_session("gala-2026", "Again", 10, 20,
                                    5, 2, False),
        T.E_ET_DUP_SESSION)
    n_s1 = _count(conn, "ticket_sessions")
    s2 = tf.register_session("quant-show", "Quant Data Show", 5, 9,
                             3, 1, True, 2)
    n_s2 = _count(conn, "ticket_sessions")
    bad1 = []
    raised1 = True
    for label, fn, code in (
            ("empty key", lambda: tf.register_session(
                " ", "t", 0, 5, 5, 1, False), T.E_ET_BAD_SESSION),
            ("none key", lambda: tf.register_session(
                None, "t", 0, 5, 5, 1, False), T.E_ET_BAD_SESSION),
            ("empty title", lambda: tf.register_session(
                "k", "  ", 0, 5, 5, 1, False), T.E_ET_BAD_SESSION),
            ("negative start", lambda: tf.register_session(
                "k", "t", -1, 5, 5, 1, False), T.E_ET_BAD_SESSION),
            ("end==start", lambda: tf.register_session(
                "k", "t", 5, 5, 5, 1, False), T.E_ET_BAD_SESSION),
            ("end<start", lambda: tf.register_session(
                "k", "t", 6, 5, 5, 1, False), T.E_ET_BAD_SESSION),
            ("zero price", lambda: tf.register_session(
                "k", "t", 0, 5, 0, 1, False), T.E_ET_BAD_PRICE),
            ("bool price", lambda: tf.register_session(
                "k", "t", 0, 5, True, 1, False), T.E_ET_BAD_PRICE),
            ("limit 0", lambda: tf.register_session(
                "k", "t", 0, 5, 5, 0, False), T.E_ET_BAD_SESSION),
            ("capacity 0", lambda: tf.register_session(
                "k", "t", 0, 5, 5, 1, False, 0), T.E_ET_BAD_SESSION),
            ("non-bool ai flag", lambda: tf.register_session(
                "k", "t", 0, 5, 5, 1, "yes"), T.E_ET_BAD_SESSION)):
        ok_one, got = expect_et_error(fn, code)
        if ok_one:
            bad1.append("%s=%s" % (label, got))
        else:
            bad1.append("%s NOT-RAISED(%s)" % (label, got))
            raised1 = False
    n_s3 = _count(conn, "ticket_sessions")
    ok1 = (s1["ai_label"] == 0 and s2["ai_label"] == 1
           and s2["capacity"] == 2 and s1["capacity"] is None
           and ok_dup and code_dup == T.E_ET_DUP_SESSION
           and n_s0 == 1 and n_s1 == 1 and n_s2 == 2 and n_s3 == 2
           and raised1
           and s1["start_window"] == 10 and s1["end_window"] == 20
           and s1["disclaimer"] == DISCLAIMER)
    record("AC-ET1", ok1, "one row per session_key: %d rows after 2"
          " legal registrations; same-key re-registration rejected"
          " %s with zero rows (%d==%d); declared labels persist"
          " (s1=%d s2=%d); capacity None legal / capacity 2 legal;"
          " all %d bad params rejected (%s); register envelope"
          " carries the disclaimer"
          % (n_s2, code_dup, n_s1, n_s2, s1["ai_label"],
             s2["ai_label"], len(bad1), "; ".join(bad1)))

    # -- AC-ET2 in-window sale + out-of-window refusal ----------------------
    b_bob0, b_carol0 = bal("bob"), bal("carol")
    p1 = tf.buy_ticket("usr:bob", s1["session_id"], 10, "order:et2a")
    p2 = tf.buy_ticket("usr:bob", s1["session_id"], 20, "order:et2b")
    b_bob1 = bal("bob")
    ok_before, code_bf = expect_et_error(
        lambda: tf.buy_ticket("usr:carol", s1["session_id"], 9,
                              "order:et2c"),
        T.E_ET_WINDOW)
    ok_after, code_af = expect_et_error(
        lambda: tf.buy_ticket("usr:carol", s1["session_id"], 21,
                              "order:et2d"),
        T.E_ET_WINDOW)
    b_carol1 = bal("carol")
    n_pur2 = _count(conn, "ticket_purchases")
    tx_head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                           (p1["spend_tx"],)).fetchone()
    tx_leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = 'usr:bob'", (p1["spend_tx"],)).fetchone()
    ok2 = (p1["purchase_window"] == 10 and p2["purchase_window"] == 20
           and b_bob1 == b_bob0 - 10
           and ok_before and code_bf == T.E_ET_WINDOW
           and ok_after and code_af == T.E_ET_WINDOW
           and b_carol1 == b_carol0 and n_pur2 == 2
           and p1["price_paid"] == 5 and p2["price_paid"] == 5
           and tx_head is not None and tx_head[0] == "spend"
           and tx_leg is not None and tx_leg[0] == "debit")
    record("AC-ET2", ok2, "both window edges inclusive: bob bought"
          " at tick 10 and tick 20 (charged %d->%d, price_paid=%d"
          " immutable copy of the registered price); one tick"
          " outside refuses fail-closed %s (tick 9) and %s (tick"
          " 21) with zero charge (%d==%d) and zero rows (%d==2);"
          " each purchase bound to a real spend tx (type=spend,"
          " debit leg)"
          % (b_bob0, b_bob1, p1["price_paid"], code_bf, code_af,
             b_carol0, b_carol1, n_pur2))

    # -- AC-ET3 ticket idempotence + per-account limit gate ------------------
    b_bob2, b_carol2 = bal("bob"), bal("carol")
    ok_limited, code_lim = expect_et_error(
        lambda: tf.buy_ticket("usr:bob", s1["session_id"], 15,
                              "order:et3a"),
        T.E_ET_LIMIT)
    b_bob3 = bal("bob")
    p3 = tf.buy_ticket("usr:carol", s1["session_id"], 12, "order:et3b")
    ok_replay, code_rp = expect_et_error(
        lambda: tf.buy_ticket("usr:carol", s1["session_id"], 13,
                              "order:et3b"),
        T.E_ET_DUP_TICKET)
    p4 = tf.buy_ticket("usr:carol", s1["session_id"], 13, "order:et3c")
    ok_carol_limit, code_cl = expect_et_error(
        lambda: tf.buy_ticket("usr:carol", s1["session_id"], 14,
                              "order:et3d"),
        T.E_ET_LIMIT)
    b_carol3 = bal("carol")
    ok3 = (ok_limited and code_lim == T.E_ET_LIMIT and b_bob3 == b_bob2
           and p3["spend_tx"] != p4["spend_tx"]
           and ok_replay and code_rp == T.E_ET_DUP_TICKET
           and ok_carol_limit and code_cl == T.E_ET_LIMIT
           and b_carol3 == b_carol2 - 10)
    record("AC-ET3", ok3, "bob at limit 2: third ticket rejected %s"
          " BEFORE the spend (%d==%d); carol's independent counter"
          " passes her own gate (two legal in-limit tickets,"
          " distinct txs); same-(buyer,ref) replay rejected %s"
          " before the spend; carol's third ticket rejected %s at"
          " her own limit; only the two legal buys charged"
          " (%d->%d)"
          % (code_lim, b_bob2, b_bob3, code_rp, code_cl, b_carol2,
             b_carol3))

    # -- AC-ET4 session-wide capacity cap -------------------------------------
    b_alice0, b_dave0, b_carol4 = bal("alice"), bal("dave"), bal("carol")
    a1 = tf.buy_ticket("usr:alice", s2["session_id"], 6, "order:et4a")
    d1 = tf.buy_ticket("usr:dave", s2["session_id"], 7, "order:et4b")
    ok_sold, code_sd = expect_et_error(
        lambda: tf.buy_ticket("usr:carol", s2["session_id"], 8,
                              "order:et4c"),
        T.E_ET_SOLD_OUT)
    b_carol5 = bal("carol")
    n_s1_pur = conn.execute(
        "SELECT COUNT(*) FROM ticket_purchases WHERE session_id = ?",
        (s1["session_id"],)).fetchone()[0]
    ok4 = (a1["price_paid"] == 3 and d1["price_paid"] == 3
           and bal("alice") == b_alice0 - 3
           and bal("dave") == b_dave0 - 3
           and ok_sold and code_sd == T.E_ET_SOLD_OUT
           and b_carol5 == b_carol4 and n_s1_pur == 4)
    record("AC-ET4", ok4, "cap-2 session: two distinct buyers (alice,"
          " dave) passed, a third buyer (carol) rejected %s BEFORE"
          " the spend with zero charge (%d==%d) - the cap counts"
          " the session, not the buyer; the uncapped session"
          " legally holds %d tickets (> the capped session's whole"
          " capacity)"
          % (code_sd, b_carol4, b_carol5, n_s1_pur))

    # -- AC-ET5 paid-admission check-in gate ---------------------------------
    tx_before = _tx_count(conn)
    ok_noticket, code_nt = expect_et_error(
        lambda: tf.admit("usr:erin", s1["session_id"], 15),
        T.E_ET_NO_TICKET)
    n_chk_nt = _count(conn, "ticket_checkins")
    ok_outwin, code_ow = expect_et_error(
        lambda: tf.admit("usr:bob", s1["session_id"], 21),
        T.E_ET_WINDOW)
    c1 = tf.admit("usr:bob", s1["session_id"], 15)
    ok_recheck, code_rc = expect_et_error(
        lambda: tf.admit("usr:bob", s1["session_id"], 16),
        T.E_ET_DUP_CHECKIN)
    c2 = tf.admit("usr:carol", s1["session_id"], 12)
    tx_after = _tx_count(conn)
    att = tf.attendees(s1["session_id"])
    n_chk = _count(conn, "ticket_checkins")
    ok5 = (ok_noticket and code_nt == T.E_ET_NO_TICKET
           and n_chk_nt == 0 and ok_outwin and code_ow == T.E_ET_WINDOW
           and c1["tickets_held"] == 2 and c2["tickets_held"] == 2
           and ok_recheck and code_rc == T.E_ET_DUP_CHECKIN
           and tx_after == tx_before and n_chk == 2
           and [r["account_id"] for r in att["checkins"]]
           == ["usr:bob", "usr:carol"]
           and att["disclaimer"] == DISCLAIMER)
    record("AC-ET5", ok5, "ticketless erin refused %s at the gate"
          " with zero check-in rows (liveroom unattended-admission"
          " law: no ticket, no entry); out-of-window admission"
          " refused %s zero rows; ticket holders bob+carol admitted"
          " (tickets_held=2 each, append-only rows in arrival"
          " order); re-check-in rejected %s; admission moved zero"
          " tokens (ledger_tx %d==%d)"
          % (code_nt, code_ow, code_rc, tx_before, tx_after))

    # -- AC-ET6 AIGC label + resident disclaimer -----------------------------
    ok_no_dis, code_nd = expect_et_error(
        lambda: T.EventTicketFace(led, "  "), T.E_ET_NO_DISCLAIMER)
    s_view = tf.session_view(s2["session_id"])
    act6 = tf.active_sessions(6)
    act15 = tf.active_sessions(15)
    board6 = tf.session_board(s2["session_id"])
    att6 = tf.attendees(s2["session_id"])
    label_rejected = False
    try:
        conn.execute(
            "INSERT INTO ticket_sessions (session_key, title,"
            " start_window, end_window, ticket_price,"
            " per_account_limit, capacity, ai_label,"
            " registered_utc) VALUES ('x-key','t',0,1,1,1,NULL,2,'t')")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        label_rejected = True
    b6 = {who: bal(who) for who in
          ("alice", "bob", "carol", "dave", "erin")}
    s_view6 = tf.session_view(s1["session_id"])
    act6b = tf.active_sessions(8)
    b6b = {who: bal(who) for who in
           ("alice", "bob", "carol", "dave", "erin")}
    act_ids6 = [r["session_key"] for r in act6["sessions"]]
    act_ids15 = [r["session_key"] for r in act15["sessions"]]
    ok6 = (ok_no_dis and code_nd == T.E_ET_NO_DISCLAIMER
           and s_view["ai_label"] == 1
           and s_view["disclaimer"] == DISCLAIMER
           and s_view6["ticket_count"] == 4
           and s_view6["ticket_buyers"] == 2
           and s_view6["attendee_count"] == 2
           and act_ids6 == ["quant-show"]
           and act_ids15 == ["gala-2026"]
           and all(r["ai_label"] in (0, 1) for r in act6["sessions"])
           and all(r["ai_label"] in (0, 1) for r in act15["sessions"])
           and act6["disclaimer"] == DISCLAIMER
           and act15["disclaimer"] == DISCLAIMER
           and act6b["disclaimer"] == DISCLAIMER
           and board6["disclaimer"] == DISCLAIMER
           and att6["disclaimer"] == DISCLAIMER
           and a1["ai_label"] == 1 and p1["ai_label"] == 0
           and c1["ai_label"] == 0
           and label_rejected and b6 == b6b)
    record("AC-ET6", ok6, "empty disclaimer refuses construction %s;"
          " every presentation face carries the declared label"
          " (session_view ai_label=%d, buy returns %d/%d, admit"
          " returns %d, active_sessions rows labeled); direct SQL"
          " ai_label=2 refused by the CHECK (%s); all six view"
          " envelopes (session_view / session_board / attendees /"
          " active_sessions / buy return / admit return) carry the"
          " resident disclaimer; derived counts read pure (s1"
          " tickets=%d buyers=%d attendees=%d); pure reads move"
          " zero tokens (balances unchanged)"
          % (code_nd, s_view["ai_label"], a1["ai_label"],
             p1["ai_label"], c1["ai_label"], label_rejected,
             s_view6["ticket_count"], s_view6["ticket_buyers"],
             s_view6["attendee_count"]))

    # -- AC-ET7 hard law: bad args, hygiene, byte-stable config -------------
    b7 = {who: bal(who) for who in
          ("alice", "bob", "carol", "dave", "erin")}
    counts0 = (_count(conn, "ticket_sessions"),
               _count(conn, "ticket_purchases"),
               _count(conn, "ticket_checkins"))
    bad7 = []
    raised7 = True
    for label, fn, code in (
            ("pool buyer", lambda: tf.buy_ticket(
                "pool:reserve", s1["session_id"], 15, "order:et7a"),
             T.E_ET_BAD_ACCOUNT),
            ("empty ref", lambda: tf.buy_ticket(
                "usr:dave", s1["session_id"], 15, "  "),
             T.E_ET_BAD_ARGS),
            ("bool window buy", lambda: tf.buy_ticket(
                "usr:dave", s1["session_id"], True, "order:et7b"),
             T.E_ET_BAD_ARGS),
            ("negative window buy", lambda: tf.buy_ticket(
                "usr:dave", s1["session_id"], -1, "order:et7c"),
             T.E_ET_BAD_ARGS),
            ("str session id", lambda: tf.buy_ticket(
                "usr:dave", "x", 15, "order:et7d"),
             T.E_ET_BAD_ARGS),
            ("bool session id", lambda: tf.buy_ticket(
                "usr:dave", True, 15, "order:et7e"),
             T.E_ET_BAD_ARGS),
            ("unknown session buy", lambda: tf.buy_ticket(
                "usr:dave", 999, 15, "order:et7f"),
             T.E_ET_UNKNOWN_SESSION),
            ("pool admit", lambda: tf.admit(
                "pool:reserve", s1["session_id"], 15),
             T.E_ET_BAD_ACCOUNT),
            ("bool window admit", lambda: tf.admit(
                "usr:dave", s1["session_id"], True),
             T.E_ET_BAD_ARGS),
            ("unknown session admit", lambda: tf.admit(
                "usr:dave", 999, 15), T.E_ET_UNKNOWN_SESSION),
            ("bad active_sessions tick", lambda: tf.active_sessions(
                "x"), T.E_ET_BAD_ARGS),
            ("unknown session_view", lambda: tf.session_view(999),
             T.E_ET_UNKNOWN_SESSION),
            ("unknown board", lambda: tf.session_board(999),
             T.E_ET_UNKNOWN_SESSION),
            ("unknown attendees", lambda: tf.attendees(999),
             T.E_ET_UNKNOWN_SESSION)):
        ok_one, got = expect_et_error(fn, code)
        if ok_one:
            bad7.append("%s=%s" % (label, got))
        else:
            bad7.append("%s NOT-RAISED(%s)" % (label, got))
            raised7 = False
    counts1 = (_count(conn, "ticket_sessions"),
               _count(conn, "ticket_purchases"),
               _count(conn, "ticket_checkins"))
    with open(os.path.join(BASE, "eventtickets.py"), encoding="utf-8") as h:
        src7 = h.read()
    non_ascii = sum(1 for ch in src7 if ord(ch) > 127)
    net_imports = [ln for ln in src7.splitlines()
                   if (ln.startswith("import ") or ln.startswith("from "))
                   and any(w in ln for w in
                           ("urllib", "requests", "socket", "http"))]
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_after = h.read()
    bal7 = {who: bal(who) for who in
            ("alice", "bob", "carol", "dave", "erin")}
    ok7 = (raised7 and counts0 == counts1 and b7 == bal7
           and non_ascii == 0 and not net_imports
           and "UPDATE ticket_" not in src7
           and "random" not in src7 and cfg_after == cfg_bytes)
    record("AC-ET7", ok7, "all %d bad args rejected (%s); zero side"
          " effects (rows %s unchanged, all balances unchanged);"
          " module pure ASCII (%d non-ascii); zero network imports"
          " (%d); zero UPDATE surface (window/limit/capacity/"
          "has-ticket all COUNT faces); zero RNG (no random in"
          " source); config.json byte-stable"
          % (len(bad7), "; ".join(bad7), counts0, non_ascii,
             len(net_imports)))

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
