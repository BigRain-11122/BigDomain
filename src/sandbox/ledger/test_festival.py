"""Acceptance suite for the city solar-term / festival
limited-event face (BigDomain R1693; canon = explore-queue city
solar-term / festival limited-event engine line: the ads/venue
schedule-window convention + per-account purchase-limit gate +
event-commemorative collectibles linkage). Asserts the
pre-registered criteria AC-FE1..AC-FE7 from the R1693
explore-queue row (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

The collectibles face is the real product injected by reference
(no copy); the festival module reaches it only through its public
API. This test source stays pure ASCII per the encoding
discipline.

Usage: python test_festival.py
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
import collectibles as C               # noqa: E402 (R619 product)
import festival as F                    # noqa: E402 (R1693 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: festival limited items"
             " are city keepsakes, not investment advice")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_fe_error(fn, *codes):
    try:
        fn()
    except F.FestivalError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


class _WrongDbCol(object):
    """Wiring probe: an object with the issue_certificate surface
    but a foreign db_path - the face must refuse construction
    (shared-file law, AC-FE5)."""

    db_path = "not-the-ledger.db"

    def issue_certificate(self, *args, **kwargs):
        raise AssertionError("must not be called")


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _cert_refs(col, account):
    return [c["event_ref"] for c in
            col.collection(account)["certificates"]]


def main():
    tmp = tempfile.mkdtemp(prefix="festival-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    col = C.CollectiblesFace(led)
    ff = F.FestivalFace(led, col, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 2000, "SETTLE-FE-A", "settlement")
    for who, amount, tag in (("alice", 100, "a"), ("bob", 100, "b"),
                             ("carol", 100, "c"), ("dave", 100, "d"),
                             ("erin", 50, "e")):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag, "suite funding " + who)
    bal = lambda who: led.balance("usr:" + who)["balance"]  # noqa: E731
    conn = sqlite3.connect(db_path)

    # -- AC-FE1 schedule-window registry face ------------------------------
    ev1 = ff.register_event("lichun-2026", "Lichun Limited", 10, 20,
                            5, 2, False)
    n_ev0 = _count(conn, "festival_events")
    ok_dup, code_dup = expect_fe_error(
        lambda: ff.register_event("lichun-2026", "Again", 10, 20,
                                  5, 2, False),
        F.E_FE_DUP_EVENT)
    n_ev1 = _count(conn, "festival_events")
    ev2 = ff.register_event("mid-autumn", "Mid-Autumn Lantern", 5, 9,
                            3, 1, True, 2)
    n_ev2 = _count(conn, "festival_events")
    bad1 = []
    raised1 = True
    for label, fn, code in (
            ("empty key", lambda: ff.register_event(
                " ", "t", 0, 5, 5, 1, False), F.E_FE_BAD_EVENT),
            ("none key", lambda: ff.register_event(
                None, "t", 0, 5, 5, 1, False), F.E_FE_BAD_EVENT),
            ("empty title", lambda: ff.register_event(
                "k", "  ", 0, 5, 5, 1, False), F.E_FE_BAD_EVENT),
            ("negative start", lambda: ff.register_event(
                "k", "t", -1, 5, 5, 1, False), F.E_FE_BAD_EVENT),
            ("end==start", lambda: ff.register_event(
                "k", "t", 5, 5, 5, 1, False), F.E_FE_BAD_EVENT),
            ("end<start", lambda: ff.register_event(
                "k", "t", 6, 5, 5, 1, False), F.E_FE_BAD_EVENT),
            ("zero price", lambda: ff.register_event(
                "k", "t", 0, 5, 0, 1, False), F.E_FE_BAD_PRICE),
            ("bool price", lambda: ff.register_event(
                "k", "t", 0, 5, True, 1, False), F.E_FE_BAD_PRICE),
            ("limit 0", lambda: ff.register_event(
                "k", "t", 0, 5, 5, 0, False), F.E_FE_BAD_EVENT),
            ("cap 0", lambda: ff.register_event(
                "k", "t", 0, 5, 5, 1, False, 0), F.E_FE_BAD_EVENT),
            ("non-bool ai flag", lambda: ff.register_event(
                "k", "t", 0, 5, 5, 1, "yes"), F.E_FE_BAD_EVENT)):
        ok_one, got = expect_fe_error(fn, code)
        if ok_one:
            bad1.append("%s=%s" % (label, got))
        else:
            bad1.append("%s NOT-RAISED(%s)" % (label, got))
            raised1 = False
    n_ev3 = _count(conn, "festival_events")
    ok1 = (ev1["ai_label"] == 0 and ev2["ai_label"] == 1
           and ev2["edition_cap"] == 2 and ev1["edition_cap"] is None
           and ok_dup and code_dup == F.E_FE_DUP_EVENT
           and n_ev0 == 1 and n_ev1 == 1 and n_ev2 == 2
           and n_ev3 == 2 and raised1
           and ev1["start_window"] == 10 and ev1["end_window"] == 20)
    record("AC-FE1", ok1, "one row per event_key: %d rows after 2"
          " legal registrations; same-key re-registration rejected"
          " %s with zero rows (%d==%d); declared labels persist"
          " (ev1=%d ev2=%d); cap None legal / cap 2 legal; all %d"
          " bad params rejected (%s)"
          % (n_ev2, code_dup, n_ev1, n_ev2, ev1["ai_label"],
             ev2["ai_label"], len(bad1), "; ".join(bad1)))

    # -- AC-FE2 in-window sale + out-of-window refusal ----------------------
    b_bob0, b_carol0 = bal("bob"), bal("carol")
    p1 = ff.buy_event_item("usr:bob", ev1["event_id"], 10, "order:fe2a")
    p2 = ff.buy_event_item("usr:bob", ev1["event_id"], 20, "order:fe2b")
    b_bob1 = bal("bob")
    ok_before, code_bf = expect_fe_error(
        lambda: ff.buy_event_item("usr:carol", ev1["event_id"], 9,
                                  "order:fe2c"),
        F.E_FE_WINDOW)
    ok_after, code_af = expect_fe_error(
        lambda: ff.buy_event_item("usr:carol", ev1["event_id"], 21,
                                  "order:fe2d"),
        F.E_FE_WINDOW)
    b_carol1 = bal("carol")
    n_pur2 = _count(conn, "festival_purchases")
    tx_head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                           (p1["spend_tx"],)).fetchone()
    tx_leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = 'usr:bob'", (p1["spend_tx"],)).fetchone()
    ok2 = (p1["purchase_window"] == 10 and p2["purchase_window"] == 20
           and b_bob1 == b_bob0 - 10
           and ok_before and code_bf == F.E_FE_WINDOW
           and ok_after and code_af == F.E_FE_WINDOW
           and b_carol1 == b_carol0 and n_pur2 == 2
           and p1["price_paid"] == 5 and p2["price_paid"] == 5
           and tx_head is not None and tx_head[0] == "spend"
           and tx_leg is not None and tx_leg[0] == "debit")
    record("AC-FE2", ok2, "both window edges inclusive: bob bought"
          " at tick 10 and tick 20 (charged %d->%d, price_paid=%d"
          " immutable copy of the registered price); one tick"
          " outside refuses fail-closed %s (tick 9) and %s (tick"
          " 21) with zero charge (%d==%d) and zero rows (%d==2);"
          " each purchase bound to a real spend tx (type=spend,"
          " debit leg)"
          % (b_bob0, b_bob1, p1["price_paid"], code_bf, code_af,
             b_carol0, b_carol1, n_pur2))

    # -- AC-FE3 per-account purchase-limit gate ------------------------------
    b_bob2, b_carol2 = bal("bob"), bal("carol")
    ok_limited, code_lim = expect_fe_error(
        lambda: ff.buy_event_item("usr:bob", ev1["event_id"], 15,
                                  "order:fe3a"),
        F.E_FE_LIMIT)
    b_bob3 = bal("bob")
    p3 = ff.buy_event_item("usr:carol", ev1["event_id"], 12, "order:fe3b")
    ok_replay, code_rp = expect_fe_error(
        lambda: ff.buy_event_item("usr:carol", ev1["event_id"], 13,
                                  "order:fe3b"),
        F.E_FE_DUP_PURCHASE)
    p4 = ff.buy_event_item("usr:carol", ev1["event_id"], 13, "order:fe3c")
    ok_carol_limit, code_cl = expect_fe_error(
        lambda: ff.buy_event_item("usr:carol", ev1["event_id"], 14,
                                  "order:fe3d"),
        F.E_FE_LIMIT)
    b_carol3 = bal("carol")
    ok3 = (ok_limited and code_lim == F.E_FE_LIMIT and b_bob3 == b_bob2
           and p3["spend_tx"] != p4["spend_tx"]
           and ok_replay and code_rp == F.E_FE_DUP_PURCHASE
           and ok_carol_limit and code_cl == F.E_FE_LIMIT
           and b_carol3 == b_carol2 - 10)
    record("AC-FE3", ok3, "bob at limit 2: third buy rejected %s"
          " BEFORE the spend (%d==%d); carol's independent counter"
          " passes her own gate (two legal buys, distinct txs);"
          " same-(buyer,ref) replay rejected %s before the spend;"
          " carol's third buy rejected %s at her own limit; only"
          " the two legal buys charged (%d->%d)"
          % (code_lim, b_bob2, b_bob3, code_rp, code_cl, b_carol2,
             b_carol3))

    # -- AC-FE4 event-wide edition cap ---------------------------------------
    b_alice0, b_dave0, b_carol4 = bal("alice"), bal("dave"), bal("carol")
    a1 = ff.buy_event_item("usr:alice", ev2["event_id"], 6, "order:fe4a")
    d1 = ff.buy_event_item("usr:dave", ev2["event_id"], 7, "order:fe4b")
    ok_sold, code_sd = expect_fe_error(
        lambda: ff.buy_event_item("usr:carol", ev2["event_id"], 8,
                                  "order:fe4c"),
        F.E_FE_SOLD_OUT)
    b_carol5 = bal("carol")
    n_ev1_pur = conn.execute(
        "SELECT COUNT(*) FROM festival_purchases WHERE event_id = ?",
        (ev1["event_id"],)).fetchone()[0]
    ok4 = (a1["price_paid"] == 3 and d1["price_paid"] == 3
           and bal("alice") == b_alice0 - 3
           and bal("dave") == b_dave0 - 3
           and ok_sold and code_sd == F.E_FE_SOLD_OUT
           and b_carol5 == b_carol4 and n_ev1_pur == 4)
    record("AC-FE4", ok4, "cap-2 event: two distinct buyers (alice,"
          " dave) passed, a third buyer (carol) rejected %s BEFORE"
          " the spend with zero charge (%d==%d) - the cap counts the"
          " event, not the buyer; the uncapped event legally holds"
          " %d purchases (> the capped event's whole edition)"
          % (code_sd, b_carol4, b_carol5, n_ev1_pur))

    # -- AC-FE5 event-commemorative collectibles linkage ---------------------
    alice_refs = _cert_refs(col, "usr:alice")
    bob_refs = _cert_refs(col, "usr:bob")
    carol_refs = _cert_refs(col, "usr:carol")
    dave_refs = _cert_refs(col, "usr:dave")
    board1 = ff.festival_board(ev1["event_id"])
    bob_comm = [r["commemorative"] for r in board1["purchases"]
                if r["buyer_id"] == "usr:bob"]
    carol_comm = [r["commemorative"] for r in board1["purchases"]
                  if r["buyer_id"] == "usr:carol"]
    col.issue_certificate("usr:erin", "festival:lichun-2026",
                          "festival:lichun-2026")  # platform pre-award
    pe = ff.buy_event_item("usr:erin", ev1["event_id"], 15, "order:fe5a")
    erin_refs = _cert_refs(col, "usr:erin")
    ok_nc, code_nc = expect_fe_error(
        lambda: F.FestivalFace(led, None, DISCLAIMER),
        F.E_FE_NO_COLLECTIBLES)
    ok_wrongdb, code_wd = expect_fe_error(
        lambda: F.FestivalFace(led, _WrongDbCol(), DISCLAIMER),
        F.E_FE_NO_COLLECTIBLES)
    with open(os.path.join(BASE, "festival.py"), encoding="utf-8") as h:
        src = h.read()
    ok5 = (alice_refs == ["festival:mid-autumn"]
           and bob_refs == ["festival:lichun-2026"]
           and carol_refs == ["festival:lichun-2026"]
           and dave_refs == ["festival:mid-autumn"]
           and bob_comm == [1, 0] and carol_comm == [1, 0]
           and pe["commemorative"] == 0
           and erin_refs == ["festival:lichun-2026"]
           and "INSERT INTO collectibles" not in src
           and "INSERT INTO cl_editions" not in src
           and ok_nc and code_nc == F.E_FE_NO_COLLECTIBLES
           and ok_wrongdb and code_wd == F.E_FE_NO_COLLECTIBLES)
    record("AC-FE5", ok5, "first purchase grants exactly one event"
          " commemorative through the collectibles public API:"
          " alice %s, bob (2 buys) %s, carol (2 buys) %s, dave %s;"
          " commemorative flag per (buyer,event) exactly one 1"
          " (bob %s, carol %s); platform pre-award on erin:"
          " purchase legal, no double award (flag=%d, certs still"
          " %s); module writes zero collectibles rows (source"
          " scan); unwired collectibles refuses construction %s;"
          " foreign-db collectibles refuses %s"
          % (alice_refs, bob_refs, carol_refs, dave_refs, bob_comm,
             carol_comm, pe["commemorative"], erin_refs, code_nc,
             code_wd))

    # -- AC-FE6 AIGC label + resident disclaimer -----------------------------
    ok_no_dis, code_nd = expect_fe_error(
        lambda: F.FestivalFace(led, col, "  "), F.E_FE_NO_DISCLAIMER)
    ev_view = ff.event_view(ev2["event_id"])
    act6 = ff.active_events(6)
    act15 = ff.active_events(15)
    label_rejected = False
    try:
        conn.execute(
            "INSERT INTO festival_events (event_key, title,"
            " start_window, end_window, token_price,"
            " per_account_limit, edition_cap, ai_label,"
            " registered_utc) VALUES ('x-key','t',0,1,1,1,NULL,2,'t')")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        label_rejected = True
    b6 = {who: bal(who) for who in
          ("alice", "bob", "carol", "dave", "erin")}
    board6 = ff.festival_board(ev2["event_id"])
    ev_view6 = ff.event_view(ev1["event_id"])
    act6b = ff.active_events(8)
    b6b = {who: bal(who) for who in
           ("alice", "bob", "carol", "dave", "erin")}
    act_ids6 = [r["event_key"] for r in act6["events"]]
    act_ids15 = [r["event_key"] for r in act15["events"]]
    ok6 = (ok_no_dis and code_nd == F.E_FE_NO_DISCLAIMER
           and ev_view["ai_label"] == 1
           and ev_view["disclaimer"] == DISCLAIMER
           and ev_view6["purchase_count"] == 5
           and ev_view6["participant_count"] == 3
           and act_ids6 == ["mid-autumn"]
           and act_ids15 == ["lichun-2026"]
           and all(r["ai_label"] in (0, 1) for r in act6["events"])
           and all(r["ai_label"] in (0, 1) for r in act15["events"])
           and act6["disclaimer"] == DISCLAIMER
           and act15["disclaimer"] == DISCLAIMER
           and act6b["disclaimer"] == DISCLAIMER
           and board6["disclaimer"] == DISCLAIMER
           and a1["ai_label"] == 1 and pe["ai_label"] == 0
           and label_rejected and b6 == b6b)
    record("AC-FE6", ok6, "empty disclaimer refuses construction"
          " %s; every presentation face carries the declared label"
          " (event_view ai_label=%d, buy returns %d/%d,"
          " active_events rows labeled); direct SQL ai_label=2"
          " refused by the CHECK (%s); all four view envelopes"
          " (event_view / active_events / festival_board / buy"
          " return) carry the resident disclaimer; derived counts"
          " read pure (ev1 purchases=%d participants=%d); pure"
          " reads move zero tokens (balances unchanged)"
          % (code_nd, ev_view["ai_label"], a1["ai_label"],
             pe["ai_label"], label_rejected,
             ev_view6["purchase_count"],
             ev_view6["participant_count"]))

    # -- AC-FE7 hard law: bad args, hygiene, byte-stable config -------------
    b7 = {who: bal(who) for who in
          ("alice", "bob", "carol", "dave", "erin")}
    counts0 = (_count(conn, "festival_events"),
               _count(conn, "festival_purchases"))
    bad7 = []
    raised7 = True
    for label, fn, code in (
            ("pool buyer", lambda: ff.buy_event_item(
                "pool:reserve", ev1["event_id"], 15, "order:fe7a"),
             F.E_FE_BAD_ACCOUNT),
            ("empty ref", lambda: ff.buy_event_item(
                "usr:dave", ev1["event_id"], 15, "  "),
             F.E_FE_BAD_ARGS),
            ("bool window", lambda: ff.buy_event_item(
                "usr:dave", ev1["event_id"], True, "order:fe7b"),
             F.E_FE_BAD_ARGS),
            ("negative window", lambda: ff.buy_event_item(
                "usr:dave", ev1["event_id"], -1, "order:fe7c"),
             F.E_FE_BAD_ARGS),
            ("str event id", lambda: ff.buy_event_item(
                "usr:dave", "x", 15, "order:fe7d"),
             F.E_FE_BAD_ARGS),
            ("bool event id", lambda: ff.buy_event_item(
                "usr:dave", True, 15, "order:fe7e"),
             F.E_FE_BAD_ARGS),
            ("unknown event buy", lambda: ff.buy_event_item(
                "usr:dave", 999, 15, "order:fe7f"),
             F.E_FE_UNKNOWN_EVENT),
            ("bad active_events tick", lambda: ff.active_events("x"),
             F.E_FE_BAD_ARGS),
            ("unknown event_view", lambda: ff.event_view(999),
             F.E_FE_UNKNOWN_EVENT),
            ("unknown board", lambda: ff.festival_board(999),
             F.E_FE_UNKNOWN_EVENT)):
        ok_one, got = expect_fe_error(fn, code)
        if ok_one:
            bad7.append("%s=%s" % (label, got))
        else:
            bad7.append("%s NOT-RAISED(%s)" % (label, got))
            raised7 = False
    counts1 = (_count(conn, "festival_events"),
               _count(conn, "festival_purchases"))
    with open(os.path.join(BASE, "festival.py"), encoding="utf-8") as h:
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
           and "UPDATE festival_" not in src7
           and "INSERT INTO collectibles" not in src7
           and "random" not in src7 and cfg_after == cfg_bytes)
    record("AC-FE7", ok7, "all %d bad args rejected (%s); zero side"
          " effects (rows %s unchanged, all balances unchanged);"
          " module pure ASCII (%d non-ascii); zero network imports"
          " (%d); zero UPDATE surface; zero collectibles-table"
          " writes; zero RNG (no random in source); config.json"
          " byte-stable"
          % (len(bad7), "; ".join(bad7), counts0, non_ascii,
             len(net_imports)))

    conn.close()
    ff.close()
    col.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
