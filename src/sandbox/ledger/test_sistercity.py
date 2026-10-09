"""Acceptance suite for the sister-city cross-city visit face
(BigDomain R1696; canon = explore-queue sister-city cross-city
visit line: visit passes + cross-city commercial-district
exposure, settlement protocol = settlement.py referenced through
its public API, never rebuilt). Asserts the pre-registered
criteria AC-SC1..AC-SC7 from the R1696 explore-queue row
(criteria were registered before this code existed; honesty law).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

The settlement protocol face is the real product held by reference
(no copy); the sister-city module reaches it only through its
public API (build_manifest / verify_manifest). This test source
stays pure ASCII per the encoding discipline.

Usage: python test_sistercity.py
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
import settlement as ST                 # noqa: E402 (R601 product)
import sistercity as SC                 # noqa: E402 (R1696 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: sister-city visit passes"
             " are city keepsakes, not investment advice")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_sc_error(fn, *codes):
    try:
        fn()
    except SC.SisterCityError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="sistercity-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    sc = SC.SisterCityFace(led, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 2000, "SETTLE-SC-A", "settlement")
    folks = (("alice", 100, "a"), ("bob", 100, "b"), ("carol", 100, "c"),
             ("dave", 100, "d"), ("erin", 50, "e"),
             ("merch1", 100, "m1"), ("merch2", 100, "m2"),
             ("merch3", 100, "m3"))
    for who, amount, tag in folks:
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag, "suite funding " + who)
    bal = lambda who: led.balance("usr:" + who)["balance"]  # noqa: E731
    conn = sqlite3.connect(db_path)

    # -- AC-SC1 sister-city pairing registry face ---------------------------
    t1 = sc.register_twin("tpe-kyoto-2026", "Taipei", "Kyoto",
                          10, 20, 5, 8, 2, False)
    n_t0 = _count(conn, "twin_registry")
    ok_dup, code_dup = expect_sc_error(
        lambda: sc.register_twin("tpe-kyoto-2026", "Taipei", "Kyoto",
                                10, 20, 5, 8, 2, False),
        SC.E_SC_DUP_TWIN)
    n_t1 = _count(conn, "twin_registry")
    t2 = sc.register_twin("shanghai-sapporo", "Shanghai", "Sapporo",
                          5, 9, 3, 4, 1, True)
    n_t2 = _count(conn, "twin_registry")
    bad1 = []
    raised1 = True
    for label, fn, code in (
            ("empty key", lambda: sc.register_twin(
                " ", "A", "B", 0, 5, 5, 5, 1, False), SC.E_SC_BAD_TWIN),
            ("empty home", lambda: sc.register_twin(
                "k", " ", "B", 0, 5, 5, 5, 1, False), SC.E_SC_BAD_TWIN),
            ("empty sister", lambda: sc.register_twin(
                "k", "A", " ", 0, 5, 5, 5, 1, False), SC.E_SC_BAD_TWIN),
            ("same city", lambda: sc.register_twin(
                "k", "A", "A", 0, 5, 5, 5, 1, False), SC.E_SC_BAD_TWIN),
            ("negative start", lambda: sc.register_twin(
                "k", "A", "B", -1, 5, 5, 5, 1, False), SC.E_SC_BAD_TWIN),
            ("end==start", lambda: sc.register_twin(
                "k", "A", "B", 5, 5, 5, 5, 1, False), SC.E_SC_BAD_TWIN),
            ("end<start", lambda: sc.register_twin(
                "k", "A", "B", 6, 5, 5, 5, 1, False), SC.E_SC_BAD_TWIN),
            ("zero pass price", lambda: sc.register_twin(
                "k", "A", "B", 0, 5, 0, 5, 1, False), SC.E_SC_BAD_PRICE),
            ("bool pass price", lambda: sc.register_twin(
                "k", "A", "B", 0, 5, True, 5, 1, False),
             SC.E_SC_BAD_PRICE),
            ("zero exposure price", lambda: sc.register_twin(
                "k", "A", "B", 0, 5, 5, 0, 1, False), SC.E_SC_BAD_PRICE),
            ("slots 0", lambda: sc.register_twin(
                "k", "A", "B", 0, 5, 5, 5, 0, False), SC.E_SC_BAD_TWIN),
            ("non-bool ai flag", lambda: sc.register_twin(
                "k", "A", "B", 0, 5, 5, 5, 1, "yes"),
             SC.E_SC_BAD_TWIN)):
        ok_one, got = expect_sc_error(fn, code)
        if ok_one:
            bad1.append("%s=%s" % (label, got))
        else:
            bad1.append("%s NOT-RAISED(%s)" % (label, got))
            raised1 = False
    n_t3 = _count(conn, "twin_registry")
    ok1 = (t1["ai_label"] == 0 and t2["ai_label"] == 1
           and t1["pair_id"] != t2["pair_id"]
           and ok_dup and code_dup == SC.E_SC_DUP_TWIN
           and n_t0 == 1 and n_t1 == 1 and n_t2 == 2
           and n_t3 == 2 and raised1
           and t1["start_window"] == 10 and t1["end_window"] == 20
           and t1["exposure_slots"] == 2 and t2["exposure_slots"] == 1)
    record("AC-SC1", ok1, "one row per pair_key: %d rows after 2"
          " legal registrations; same-key re-registration rejected"
          " %s with zero rows (%d==%d); declared labels persist"
          " (t1=%d t2=%d); all %d bad params rejected (%s)"
          % (n_t2, code_dup, n_t1, n_t2, t1["ai_label"],
             t2["ai_label"], len(bad1), "; ".join(bad1)))

    # -- AC-SC2 visit-pass purchase + window gate ---------------------------
    b_bob0, b_carol0, b_alice0, b_dave0 = (bal("bob"), bal("carol"),
                                           bal("alice"), bal("dave"))
    p1 = sc.buy_visit_pass("usr:bob", t1["pair_id"], 10, "order:sc2a")
    p2 = sc.buy_visit_pass("usr:carol", t1["pair_id"], 20, "order:sc2b")
    p3 = sc.buy_visit_pass("usr:dave", t1["pair_id"], 12, "order:sc2c")
    ok_before, code_bf = expect_sc_error(
        lambda: sc.buy_visit_pass("usr:alice", t1["pair_id"], 9,
                                  "order:sc2d"),
        SC.E_SC_WINDOW)
    ok_after, code_af = expect_sc_error(
        lambda: sc.buy_visit_pass("usr:alice", t1["pair_id"], 21,
                                  "order:sc2e"),
        SC.E_SC_WINDOW)
    ok_replay, code_rp = expect_sc_error(
        lambda: sc.buy_visit_pass("usr:carol", t1["pair_id"], 15,
                                  "order:sc2b"),
        SC.E_SC_DUP_PASS)
    ok_second, code_2nd = expect_sc_error(
        lambda: sc.buy_visit_pass("usr:dave", t1["pair_id"], 15,
                                  "order:sc2f"),
        SC.E_SC_PASS_EXISTS)
    n_pass = _count(conn, "twin_passes")
    tx_head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                           (p1["spend_tx"],)).fetchone()
    tx_leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = 'usr:bob'", (p1["spend_tx"],)).fetchone()
    ok2 = (p1["pass_window"] == 10 and p2["pass_window"] == 20
           and p3["pass_window"] == 12
           and bal("bob") == b_bob0 - 5
           and bal("carol") == b_carol0 - 5
           and bal("dave") == b_dave0 - 5
           and ok_before and code_bf == SC.E_SC_WINDOW
           and ok_after and code_af == SC.E_SC_WINDOW
           and bal("alice") == b_alice0
           and ok_replay and code_rp == SC.E_SC_DUP_PASS
           and ok_second and code_2nd == SC.E_SC_PASS_EXISTS
           and n_pass == 3 and p1["price_paid"] == 5
           and p2["price_paid"] == 5 and p3["price_paid"] == 5
           and p1["spend_tx"] != p2["spend_tx"]
           and p1["spend_tx"] != p3["spend_tx"]
           and tx_head is not None and tx_head[0] == "spend"
           and tx_leg is not None and tx_leg[0] == "debit")
    record("AC-SC2", ok2, "both window edges inclusive: bob bought"
          " at tick 10, carol at tick 20, dave at tick 12 (three"
          " distinct spend txs, each type=spend with a debit leg,"
          " price_paid=%d immutable copy of the registered pass"
          " price); one tick outside refuses fail-closed %s (tick"
          " 9) and %s (tick 21) with zero charge (%d==%d);"
          " same-(buyer,ref) replay rejected %s and second pass per"
          " (account,pair) rejected %s, both BEFORE the spend"
          " (balances untouched); one pass per resident per pairing"
          " holds: %d pass rows for 3 residents"
          % (p1["price_paid"], code_bf, code_af, b_alice0,
             bal("alice"), code_rp, code_2nd, n_pass))

    # -- AC-SC3 cross-city commercial-district exposure face -----------------
    b_m1_0, b_m2_0, b_m3_0 = (bal("merch1"), bal("merch2"),
                               bal("merch3"))
    x1 = sc.book_exposure("usr:merch1", t1["pair_id"], 11, "expo:sc3a")
    ok_x_replay, code_xr = expect_sc_error(
        lambda: sc.book_exposure("usr:merch1", t1["pair_id"], 12,
                                 "expo:sc3a"),
        SC.E_SC_DUP_EXPOSURE)
    x2 = sc.book_exposure("usr:merch2", t1["pair_id"], 12, "expo:sc3b")
    ok_x_full, code_xf = expect_sc_error(
        lambda: sc.book_exposure("usr:merch3", t1["pair_id"], 13,
                                 "expo:sc3c"),
        SC.E_SC_EXPOSURE_FULL)
    ok_x_out, code_xo = expect_sc_error(
        lambda: sc.book_exposure("usr:merch3", t1["pair_id"], 21,
                                 "expo:sc3d"),
        SC.E_SC_WINDOW)
    n_exp = _count(conn, "twin_exposures")
    tx_x = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = 'usr:merch1'",
        (x1["spend_tx"],)).fetchone()
    ok3 = (x1["exposure_window"] == 11 and x2["exposure_window"] == 12
           and bal("merch1") == b_m1_0 - 8
           and bal("merch2") == b_m2_0 - 8
           and ok_x_replay and code_xr == SC.E_SC_DUP_EXPOSURE
           and ok_x_full and code_xf == SC.E_SC_EXPOSURE_FULL
           and ok_x_out and code_xo == SC.E_SC_WINDOW
           and bal("merch3") == b_m3_0 and n_exp == 2
           and x1["price_paid"] == 8 and x2["price_paid"] == 8
           and x1["spend_tx"] != x2["spend_tx"]
           and tx_x is not None and tx_x[0] == "debit")
    record("AC-SC3", ok3, "merch1 booked at tick 11 and merch2 at"
          " tick 12 (two distinct spend txs with debit legs,"
          " price_paid=%d); same-(merchant,ref) replay rejected %s"
          " BEFORE the spend; the pair-wide slot cap (slots=2)"
          " rejected merch3 %s with zero charge (%d==%d); one tick"
          " outside the window rejected %s with zero charge;"
          " exposure rows=%d"
          % (x1["price_paid"], code_xr, code_xf, b_m3_0,
             bal("merch3"), code_xo, n_exp))

    # -- AC-SC4 cross-city settlement protocol reference face -----------------
    settle1 = sc.settle_twin_window(
        t1["pair_id"], "2026-W42", ["home", "sister", "platform"],
        {"home": 40, "sister": 35, "platform": 25})
    ok_again, code_ag = expect_sc_error(
        lambda: sc.settle_twin_window(
            t1["pair_id"], "2026-W42", ["home", "sister", "platform"],
            {"home": 40, "sister": 35, "platform": 25}),
        SC.E_SC_SETTLED)
    settle2 = sc.settle_twin_window(
        t1["pair_id"], "2026-W43", ["home", "sister", "platform"],
        {"home": 40, "sister": 35, "platform": 25})
    total = settle1["sales_total_cent"]
    apportion = settle1["apportioned_cent"]
    rows = conn.execute(
        "SELECT period, manifest_id FROM twin_settlements"
        " WHERE pair_id = ? ORDER BY settle_id",
        (t1["pair_id"],)).fetchall()
    sales_rows = [{"amount_cent": 5}, {"amount_cent": 5},
                  {"amount_cent": 5}, {"amount_cent": 8},
                  {"amount_cent": 8}]
    reverified = sc.settlement.verify_manifest(
        {k: v for k, v in settle1.items()
         if k not in ("pair_id", "pair_key", "window_period",
                      "sales_rows", "disclaimer", "ai_label")},
        sales_rows, [])
    ok_empty_p, code_ep = expect_sc_error(
        lambda: sc.settle_twin_window(t1["pair_id"], "  ",
                                      ["home"], {"home": 1}),
        SC.E_SC_BAD_ARGS)
    ok_dup_parties, code_dp = expect_sc_error(
        lambda: sc.settle_twin_window(t1["pair_id"], "x",
                                      ["home", "home"],
                                      {"home": 1}),
        SC.E_SC_BAD_PARTIES)
    ok_no_parties, code_np = expect_sc_error(
        lambda: sc.settle_twin_window(t1["pair_id"], "x", [],
                                      {"home": 1}),
        SC.E_SC_BAD_PARTIES)
    ok_no_weights, code_nw = expect_sc_error(
        lambda: sc.settle_twin_window(t1["pair_id"], "x",
                                      ["home"], {}),
        SC.E_SC_BAD_PARTIES)
    ok_unknown_settle, code_us = expect_sc_error(
        lambda: sc.settle_twin_window(999, "x", ["home"],
                                      {"home": 1}),
        SC.E_SC_UNKNOWN_TWIN)
    with open(os.path.join(BASE, "sistercity.py"), encoding="utf-8") as h:
        src4 = h.read()
    ok4 = (total == 31 and sum(apportion.values()) == total
           and set(apportion) == {"home", "sister", "platform"}
           and settle1["window_period"] == "2026-W42"
           and settle1["period"].startswith("twin:%d/" % t1["pair_id"])
           and settle1["sales_rows"] == 5
           and settle1["prev_id"] is None
           and settle2["prev_id"] == settle1["id"]
           and settle1["id"] != settle2["id"]
           and ok_again and code_ag == SC.E_SC_SETTLED
           and reverified is True
           and isinstance(sc.settlement, ST.SettlementFace)
           and "import settlement" in src4
           and "hashlib" not in src4 and "sha256" not in src4
           and len(rows) == 2
           and rows[0][0] == "2026-W42" and rows[1][0] == "2026-W43"
           and rows[0][1] == settle1["id"]
           and ok_empty_p and ok_dup_parties and ok_no_parties
           and ok_no_weights and ok_unknown_settle)
    record("AC-SC4", ok4, "twin window revenue (3 passes x 5 + 2"
          " exposures x 8 = %d cent) settled through the referenced"
          " SettlementFace public API (isinstance proof, module"
          " source imports settlement and builds zero second"
          " engine: no hashlib/sha256 in source); integer split"
          " zero loss (apportioned sum %d == total %d across %s);"
          " manifest re-verified through verify_manifest (%s);"
          " repeat settle rejected %s; second period legal with"
          " hash chain (settle2.prev_id == settle1.id); %d"
          " settlement rows persisted with matching manifest ids;"
          " bad settle inputs rejected (%s/%s/%s/%s/%s)"
          % (total, sum(apportion.values()), total,
             sorted(apportion), reverified, code_ag, len(rows),
             code_ep, code_dp, code_np, code_nw, code_us))

    # -- AC-SC5 AIGC label + resident disclaimer ------------------------------
    ok_no_dis, code_nd = expect_sc_error(
        lambda: SC.SisterCityFace(led, "  "), SC.E_SC_NO_DISCLAIMER)
    view1 = sc.twin_view(t1["pair_id"])
    view2 = sc.twin_view(t2["pair_id"])
    act6 = sc.active_twins(6)
    act15 = sc.active_twins(15)
    board1 = sc.twin_board(t1["pair_id"])
    label_rejected = False
    try:
        conn.execute(
            "INSERT INTO twin_registry (pair_key, home_city,"
            " sister_city, start_window, end_window, pass_price,"
            " exposure_price, exposure_slots, ai_label,"
            " registered_utc) VALUES ('x-key','A','B',0,1,1,1,1,2,'t')")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        label_rejected = True
    b5 = {who: bal(who) for who in
          ("alice", "bob", "carol", "dave", "erin",
           "merch1", "merch2", "merch3")}
    sc.twin_view(t1["pair_id"])
    sc.twin_view(t2["pair_id"])
    sc.active_twins(8)
    sc.twin_board(t1["pair_id"])
    sc.active_twins(12)
    b5b = {who: bal(who) for who in
           ("alice", "bob", "carol", "dave", "erin",
            "merch1", "merch2", "merch3")}
    ok5 = (ok_no_dis and code_nd == SC.E_SC_NO_DISCLAIMER
           and view1["ai_label"] == 0 and view2["ai_label"] == 1
           and view1["disclaimer"] == DISCLAIMER
           and view2["disclaimer"] == DISCLAIMER
           and act6["disclaimer"] == DISCLAIMER
           and act15["disclaimer"] == DISCLAIMER
           and board1["disclaimer"] == DISCLAIMER
           and p1["ai_label"] == 0 and x1["ai_label"] == 0
           and settle1["ai_label"] == 0
           and settle1["disclaimer"] == DISCLAIMER
           and all(r["ai_label"] in (0, 1) for r in act6["twins"])
           and all(r["ai_label"] in (0, 1) for r in act15["twins"])
           and label_rejected and b5 == b5b)
    record("AC-SC5", ok5, "empty disclaimer refuses construction"
          " %s; every presentation face carries the declared label"
          " (twin_view %d/%d, buy %d, exposure %d, settle %d,"
          " active_twins rows labeled); direct SQL ai_label=2"
          " refused by the CHECK (%s); all four view envelopes"
          " (twin_view / active_twins / twin_board / settle"
          " return) carry the resident disclaimer; pure reads move"
          " zero tokens (all eight balances unchanged)"
          % (code_nd, view1["ai_label"], view2["ai_label"],
             p1["ai_label"], x1["ai_label"], settle1["ai_label"],
             label_rejected))

    # -- AC-SC6 read faces ------------------------------------------------------
    ok_bad_tick, code_bt = expect_sc_error(
        lambda: sc.active_twins("x"), SC.E_SC_BAD_ARGS)
    ok_unknown_view, code_uv = expect_sc_error(
        lambda: sc.twin_view(999), SC.E_SC_UNKNOWN_TWIN)
    ok_unknown_board, code_ub = expect_sc_error(
        lambda: sc.twin_board(999), SC.E_SC_UNKNOWN_TWIN)
    act6_keys = [r["pair_key"] for r in act6["twins"]]
    act15_keys = [r["pair_key"] for r in act15["twins"]]
    pass_rows = [(r["buyer_id"], r["price_paid"], r["pass_window"])
                 for r in board1["passes"]]
    expo_rows = [(r["merchant_id"], r["price_paid"])
                 for r in board1["exposures"]]
    b6 = {who: bal(who) for who in
          ("alice", "bob", "carol", "dave", "erin",
           "merch1", "merch2", "merch3")}
    sc.twin_view(t1["pair_id"])
    sc.active_twins(15)
    sc.twin_board(t1["pair_id"])
    b6b = {who: bal(who) for who in
           ("alice", "bob", "carol", "dave", "erin",
            "merch1", "merch2", "merch3")}
    ok6 = (view1["pass_count"] == 3 and view1["pass_holder_count"] == 3
           and view1["exposure_count"] == 2
           and view1["merchant_count"] == 2
           and view1["start_window"] == 10
           and view1["end_window"] == 20
           and view1["pass_price"] == 5
           and view1["exposure_price"] == 8
           and view1["exposure_slots"] == 2
           and act6_keys == ["shanghai-sapporo"]
           and act15_keys == ["tpe-kyoto-2026"]
           and sorted(pass_rows) == [("usr:bob", 5, 10),
                                     ("usr:carol", 5, 20),
                                     ("usr:dave", 5, 12)]
           and sorted(expo_rows) == [("usr:merch1", 8),
                                      ("usr:merch2", 8)]
           and all(r["spend_tx"] for r in board1["passes"])
           and all(r["spend_tx"] for r in board1["exposures"])
           and ok_bad_tick and ok_unknown_view and ok_unknown_board
           and b6 == b6b)
    record("AC-SC6", ok6, "twin_view carries window, prices and"
          " derived counts (passes=%d holders=%d exposures=%d"
          " merchants=%d); active_twins lists only the covering"
          " pairing (tick 6 -> %s, tick 15 -> %s); twin_board is"
          " the audit trail (3 pass rows + 2 exposure rows, every"
          " row bound to its spend tx, immutable price copies);"
          " bad tick %s / unknown pair %s / %s rejected; all reads"
          " pure (balances unchanged)"
          % (view1["pass_count"], view1["pass_holder_count"],
             view1["exposure_count"], view1["merchant_count"],
             act6_keys, act15_keys, code_bt, code_uv, code_ub))

    # -- AC-SC7 hard law: bad args, hygiene, byte-stable config ---------------
    b7 = {who: bal(who) for who in
          ("alice", "bob", "carol", "dave", "erin",
           "merch1", "merch2", "merch3")}
    counts0 = (_count(conn, "twin_registry"),
               _count(conn, "twin_passes"),
               _count(conn, "twin_exposures"),
               _count(conn, "twin_settlements"))
    bad7 = []
    raised7 = True
    for label, fn, code in (
            ("pool buyer pass", lambda: sc.buy_visit_pass(
                "pool:reserve", t1["pair_id"], 15, "order:sc7a"),
             SC.E_SC_BAD_ACCOUNT),
            ("empty ref pass", lambda: sc.buy_visit_pass(
                "usr:erin", t1["pair_id"], 15, "  "),
             SC.E_SC_BAD_ARGS),
            ("bool window pass", lambda: sc.buy_visit_pass(
                "usr:erin", t1["pair_id"], True, "order:sc7b"),
             SC.E_SC_BAD_ARGS),
            ("negative window pass", lambda: sc.buy_visit_pass(
                "usr:erin", t1["pair_id"], -1, "order:sc7c"),
             SC.E_SC_BAD_ARGS),
            ("str pair id pass", lambda: sc.buy_visit_pass(
                "usr:erin", "x", 15, "order:sc7d"), SC.E_SC_BAD_ARGS),
            ("bool pair id pass", lambda: sc.buy_visit_pass(
                "usr:erin", True, 15, "order:sc7e"), SC.E_SC_BAD_ARGS),
            ("unknown pair pass", lambda: sc.buy_visit_pass(
                "usr:erin", 999, 15, "order:sc7f"),
             SC.E_SC_UNKNOWN_TWIN),
            ("pool merchant exposure", lambda: sc.book_exposure(
                "pool:reserve", t1["pair_id"], 15, "expo:sc7a"),
             SC.E_SC_BAD_ACCOUNT),
            ("empty ref exposure", lambda: sc.book_exposure(
                "usr:merch3", t1["pair_id"], 15, "  "),
             SC.E_SC_BAD_ARGS),
            ("unknown pair exposure", lambda: sc.book_exposure(
                "usr:merch3", 999, 15, "expo:sc7b"),
             SC.E_SC_UNKNOWN_TWIN),
            ("bool window exposure", lambda: sc.book_exposure(
                "usr:merch3", t1["pair_id"], True, "expo:sc7c"),
             SC.E_SC_BAD_ARGS),
            ("settle non-list parties", lambda: sc.settle_twin_window(
                t1["pair_id"], "y", "home", {"home": 1}),
             SC.E_SC_BAD_PARTIES),
            ("settle non-dict weights", lambda: sc.settle_twin_window(
                t1["pair_id"], "y", ["home"], ["home"]),
             SC.E_SC_BAD_PARTIES)):
        ok_one, got = expect_sc_error(fn, code)
        if ok_one:
            bad7.append("%s=%s" % (label, got))
        else:
            bad7.append("%s NOT-RAISED(%s)" % (label, got))
            raised7 = False
    counts1 = (_count(conn, "twin_registry"),
               _count(conn, "twin_passes"),
               _count(conn, "twin_exposures"),
               _count(conn, "twin_settlements"))
    with open(os.path.join(BASE, "sistercity.py"), encoding="utf-8") as h:
        src7 = h.read()
    non_ascii = sum(1 for ch in src7 if ord(ch) > 127)
    net_imports = [ln for ln in src7.splitlines()
                   if (ln.startswith("import ") or ln.startswith("from "))
                   and any(w in ln for w in
                           ("urllib", "requests", "socket", "http"))]
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_after = h.read()
    bal7 = {who: bal(who) for who in
            ("alice", "bob", "carol", "dave", "erin",
             "merch1", "merch2", "merch3")}
    ok7 = (raised7 and counts0 == counts1 and b7 == bal7
           and non_ascii == 0 and not net_imports
           and "UPDATE twin_" not in src7
           and "random" not in src7
           and cfg_after == cfg_bytes)
    record("AC-SC7", ok7, "all %d bad args rejected (%s); zero side"
          " effects (four tables' rows %s unchanged, all eight"
          " balances unchanged); module pure ASCII (%d non-ascii);"
          " zero network imports (%d); zero UPDATE surface; zero"
          " RNG (no random in source); config.json byte-stable"
          % (len(bad7), "; ".join(bad7), counts0, non_ascii,
             len(net_imports)))

    conn.close()
    sc.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
