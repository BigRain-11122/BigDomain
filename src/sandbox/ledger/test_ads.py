"""Acceptance suite for the virtual-exhibition ad-slot schedule face
(BigDomain R622; canon = BLUEPRINT sec-4 B3 ad-slot price row).
Asserts the pre-registered criteria AC-AD1..AC-AD7 from the R622
backlog row (criteria were registered before this code existed;
honesty law). Each criterion prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL.

Usage: python test_ads.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L   # noqa: E402  (P-47-2b core)
import venue as V   # noqa: E402  (R605 occupancy engine, referenced)
import ads as A     # noqa: E402  (R622 schedule face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_ad_error(fn, *codes):
    try:
        fn()
    except A.AdsError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="ads-ac-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    ven = V.VenueFace(led)
    af = A.AdsFace(led, ven)

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_sha_before = hashlib.sha256(handle.read()).hexdigest()

    led.mint_to_pool("pool:reserve", 1000, "SETTLE-AD-A", "settlement")
    for name, amount in (("alice", 300), ("bob", 200), ("carol", 200),
                        ("dave", 100)):
        led.ensure_account("usr:" + name, census_avatar_id=name)
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + name, "credit", amount)],
                   "manual:fund-" + name, "suite funding " + name)
    bal = lambda who: led.balance(who)["balance"]  # noqa: E731

    # -- AC-AD1 venue-reference law: one registry table, venue rows ---
    af.register_ad_unit("screen:quant-main", "quant_screen_carousel",
                        rotation_slots=3)
    af.register_ad_unit("naming:harbor-gate", "building_naming")
    af.register_ad_unit("naming:metro-l4", "building_naming")
    af.register_ad_unit("splash:lobby", "lobby_splash")
    b_alice, b_bob, b_carol = bal("usr:alice"), bal("usr:bob"), bal("usr:carol")
    r_nam = af.book("usr:alice", "naming:harbor-gate", 0, 2, 30, "order:ad1a")
    r_spl = af.book("usr:bob", "splash:lobby", 0, 1, 50, "order:ad1b")
    r_scr = af.book("usr:carol", "screen:quant-main", 0, 4, 10, "order:ad1c")
    conn = sqlite3.connect(db_path)
    ad_tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
        " AND name LIKE 'ad_%'").fetchall()]
    prov = []
    ok1 = (ad_tables == ["ad_units"] and r_nam["fee"] == 60
           and r_spl["fee"] == 50 and r_scr["fee"] == 40
           and bal("usr:alice") == b_alice - 60
           and bal("usr:bob") == b_bob - 50
           and bal("usr:carol") == b_carol - 40)
    for res, want_kind in ((r_nam, "storefront"), (r_spl, "storefront"),
                           (r_scr, "venue")):
        occ = conn.execute(
            "SELECT kind, account_id FROM venue_occupancy"
            " WHERE bound_spend_tx = ?", (res["spend_tx"],)).fetchone()
        head = conn.execute(
            "SELECT type FROM ledger_tx WHERE tx_id = ?",
            (res["spend_tx"],)).fetchone()
        good = (occ is not None and occ[0] == want_kind
                and head is not None and head[0] == "spend")
        prov.append("%s/%s" % (res["ad_kind"], want_kind))
        ok1 = ok1 and good and res["occ_id"] > 0
    conn.close()
    record("AC-AD1", ok1, "ads-owned tables %s (single registry table); all"
          " three products booked through the venue API as occupancy rows"
          " (%s), each bound to a real spend tx; fees 60/50/40 moved"
          " balances exactly (%d/%d/%d left)"
          % (ad_tables, "; ".join(prov), bal("usr:alice"), bal("usr:bob"),
             bal("usr:carol")))

    # -- AC-AD2 schedule-window booking: future window, one spend ------
    b2 = bal("usr:carol")
    r_adv = af.book("usr:carol", "naming:metro-l4", 100, 1, 70, "order:ad2")
    h99 = af.naming_holder("naming:metro-l4", 99)
    h100 = af.naming_holder("naming:metro-l4", 100)
    h101 = af.naming_holder("naming:metro-l4", 101)
    ok2 = (bal("usr:carol") == b2 - 70 and r_adv["fee"] == 70
           and r_adv["start_window"] == 100 and r_adv["end_window"] == 100
           and bool(r_adv["spend_tx"]) and r_adv["occ_id"] > 0
           and h99 is None and h100 == "usr:carol" and h101 is None)
    record("AC-AD2", ok2, "advance booking at window 100 charged exactly"
          " one spend 70 (%d->%d), receipt span 100..100 with occ row #%d"
          " and tx %s; holder None/holder/None at windows 99/100/101"
          % (b2, bal("usr:carol"), r_adv["occ_id"], r_adv["spend_tx"][:10]))

    # -- AC-AD3 carousel rotation: capacity gate + lineup order -------
    ba, bb, bc, bd = (bal("usr:alice"), bal("usr:bob"), bal("usr:carol"),
                      bal("usr:dave"))
    r3a = af.book("usr:alice", "screen:quant-main", 10, 4, 5, "order:ad3a")
    r3b = af.book("usr:bob", "screen:quant-main", 10, 4, 5, "order:ad3b")
    r3c = af.book("usr:carol", "screen:quant-main", 10, 4, 5, "order:ad3c")
    ok_full, code_full = expect_ad_error(
        lambda: af.book("usr:dave", "screen:quant-main", 10, 4, 5,
                        "order:ad3d"), A.E_AD_FULL)
    line10 = af.carousel_lineup("screen:quant-main", 10)
    line4 = af.carousel_lineup("screen:quant-main", 4)
    line13 = af.carousel_lineup("screen:quant-main", 13)
    order = [x["account_id"] for x in line10["advertisers"]]
    positions = [x["position"] for x in line10["advertisers"]]
    occ_seq = [x["occ_id"] for x in line10["advertisers"]]
    ok3 = (bal("usr:alice") == ba - 20 and bal("usr:bob") == bb - 20
           and bal("usr:carol") == bc - 20 and bal("usr:dave") == bd
           and ok_full and code_full == A.E_AD_FULL
           and line10["rotation_slots"] == 3 and order ==
           ["usr:alice", "usr:bob", "usr:carol"]
           and positions == [1, 2, 3]
           and occ_seq == sorted(occ_seq)
           and line4["advertisers"] == [] and len(line13["advertisers"]) == 3)
    record("AC-AD3", ok3, "3-slot screen took 3 overlapping advertisers"
          " (fees 20 each, %d/%d/%d left), 4th rejected %s with zero"
          " charge (%d==%d); lineup at w10 = %s positions %s in booking"
          " order (occ ids ascending %s); w4 empty, w13 still 3"
          % (bal("usr:alice"), bal("usr:bob"), bal("usr:carol"),
             code_full, bd, bal("usr:dave"), order, positions, occ_seq))

    # -- AC-AD4 exclusivity gate: overlap rejected, adjacency allowed --
    bc4 = bal("usr:carol")
    ok_splash, code_splash = expect_ad_error(
        lambda: af.book("usr:carol", "splash:lobby", 0, 1, 50, "order:ad4a"),
        A.E_AD_TAKEN)
    ok_nam, code_nam = expect_ad_error(
        lambda: af.book("usr:carol", "naming:harbor-gate", 1, 2, 30,
                        "order:ad4b"), A.E_AD_TAKEN)
    b4_rejects = bal("usr:carol")
    own0 = af.splash_owner("splash:lobby", 0)
    own1 = af.splash_owner("splash:lobby", 1)
    h1 = af.naming_holder("naming:harbor-gate", 1)
    h2a = af.naming_holder("naming:harbor-gate", 2)
    r_adj = af.book("usr:carol", "naming:harbor-gate", 2, 1, 30, "order:ad4c")
    h2b = af.naming_holder("naming:harbor-gate", 2)
    ok4 = (ok_splash and code_splash == A.E_AD_TAKEN
           and ok_nam and code_nam == A.E_AD_TAKEN
           and b4_rejects == bc4
           and own0 == "usr:bob"
           and own1 is None and h1 == "usr:alice" and h2a is None
           and r_adj["fee"] == 30 and bal("usr:carol") == bc4 - 30
           and h2b == "usr:carol")
    record("AC-AD4", ok4, "second overlapping booking rejected %s on both"
          " exclusive kinds with zero charge (%d==%d); splash owner"
          " bob@w0 / None@w1, naming holder alice@w1 / None@w2; adjacent"
          " non-overlap window 2..2 booked fine (holder carol@w2, fee 30)"
          % (code_splash, bc4, b4_rejects))

    # -- AC-AD5 registry gates: unknown / kind change / exclusive slots -
    bd5 = bal("usr:dave")
    ok_unk, code_unk = expect_ad_error(
        lambda: af.book("usr:dave", "screen:ghost", 0, 1, 10, "order:ad5a"),
        A.E_AD_UNKNOWN)
    ok_kind, code_kind = expect_ad_error(
        lambda: af.register_ad_unit("naming:harbor-gate",
                                    "quant_screen_carousel",
                                    rotation_slots=2),
        A.E_AD_KIND_MISMATCH)
    ok_slots, code_slots = expect_ad_error(
        lambda: af.register_ad_unit("naming:metro-l5", "building_naming",
                                    rotation_slots=3), A.E_AD_BAD_ARGS)
    re_reg = af.register_ad_unit("screen:quant-main", "quant_screen_carousel",
                                 rotation_slots=3)
    conn = sqlite3.connect(db_path)
    unit_count = conn.execute("SELECT COUNT(*) FROM ad_units").fetchone()[0]
    conn.close()
    ok5 = (ok_unk and code_unk == A.E_AD_UNKNOWN
           and bd5 == bal("usr:dave")
           and ok_kind and code_kind == A.E_AD_KIND_MISMATCH
           and ok_slots and code_slots == A.E_AD_BAD_ARGS
           and re_reg["idempotent"] and unit_count == 4)
    record("AC-AD5", ok5, "unregistered unit booking rejected %s zero"
          " charge (%d==%d); kind change on a registered unit rejected"
          " %s; exclusive kind with rotation_slots=3 rejected %s;"
          " same-params re-register idempotent (ad_units rows %d)"
          % (code_unk, bd5, bal("usr:dave"), code_kind, code_slots,
             unit_count))

    # -- AC-AD6 duplicate replay + schedule board read view ------------
    ba6 = bal("usr:alice")
    ok_dup, code_dup = expect_ad_error(
        lambda: af.book("usr:alice", "screen:quant-main", 10, 4, 5,
                        "order:ad6-dup"), A.E_AD_DUP)
    board_scr = af.schedule_board("screen:quant-main")
    board_nam = af.schedule_board("naming:harbor-gate")
    scr_spans = [(b["start_window"], b["end_window"])
                for b in board_scr["bookings"]]
    scr_accounts = [b["account_id"] for b in board_scr["bookings"]]
    nam_spans = [(b["start_window"], b["end_window"])
                 for b in board_nam["bookings"]]
    nam_accounts = [b["account_id"] for b in board_nam["bookings"]]
    ok6 = (ok_dup and code_dup == A.E_AD_DUP and ba6 == bal("usr:alice")
           and board_scr["ad_kind"] == "quant_screen_carousel"
           and scr_spans == [(0, 3), (10, 13), (10, 13), (10, 13)]
           and scr_accounts == ["usr:carol", "usr:alice", "usr:bob",
                               "usr:carol"]
           and all(b["spend_tx"] for b in board_scr["bookings"])
           and board_nam["ad_kind"] == "building_naming"
           and nam_spans == [(0, 1), (2, 2)]
           and nam_accounts == ["usr:alice", "usr:carol"]
           and all(b["spend_tx"] for b in board_nam["bookings"]))
    record("AC-AD6", ok6, "identical replay (alice, screen, 10..13)"
          " rejected %s with zero second charge (%d==%d); schedule board"
          " screen = 4 bookings %s owners %s every row tx-proven; naming"
          " board = %s owners %s"
          % (code_dup, ba6, bal("usr:alice"), scr_spans, scr_accounts,
             nam_spans, nam_accounts))

    # -- AC-AD7 hard laws: bad args, purity, immutability, config -------
    b7 = {w: bal("usr:" + w) for w in ("alice", "bob", "carol", "dave")}
    conn = sqlite3.connect(db_path)
    occ7 = conn.execute("SELECT COUNT(*) FROM venue_occupancy").fetchone()[0]
    conn.close()
    bad = []
    raised_all = True
    for label, fn, code in (
            ("bad account", lambda: af.book("svc:x", "splash:lobby",
                                           0, 1, 50, "order:ad7a"),
             A.E_AD_BAD_ARGS),
            ("zero windows", lambda: af.book("usr:dave", "splash:lobby",
                                            0, 0, 50, "order:ad7b"),
             A.E_AD_BAD_ARGS),
            ("negative start", lambda: af.book("usr:dave", "splash:lobby",
                                               -1, 1, 50, "order:ad7c"),
             A.E_AD_BAD_ARGS),
            ("zero price", lambda: af.book("usr:dave", "splash:lobby",
                                           0, 1, 0, "order:ad7d"),
             A.E_AD_BAD_ARGS),
            ("empty ref", lambda: af.book("usr:dave", "splash:lobby",
                                          0, 1, 50, "  "),
             A.E_AD_BAD_ARGS),
            ("bad lineup window", lambda: af.carousel_lineup(
                "screen:quant-main", -1), A.E_AD_BAD_ARGS)):
        ok_one, got = expect_ad_error(fn, code)
        if ok_one:
            bad.append("%s=%s" % (label, got))
        else:
            bad.append("%s NOT-RAISED(%s)" % (label, got))
            raised_all = False
    conn = sqlite3.connect(db_path)
    occ7b = conn.execute("SELECT COUNT(*) FROM venue_occupancy").fetchone()[0]
    conn.close()
    with open(os.path.join(BASE, "ads.py"), encoding="utf-8") as handle:
        src = handle.read()
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    update_face = ("UPDATE ad_units" in src
                   or "UPDATE venue_occupancy" in src)
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_sha_after = hashlib.sha256(handle.read()).hexdigest()
    ok7 = (raised_all
           and all(bal("usr:" + w) == b7[w] for w in b7)
           and occ7 == occ7b
           and non_ascii == 0 and not update_face
           and cfg_sha_before == cfg_sha_after)
    record("AC-AD7", ok7, "all bad args rejected (%s); zero side effects"
          " (balances %s unchanged, occupancy rows %d==%d); module pure"
          " ASCII (%d non-ascii), zero UPDATE surface on registry or"
          " occupancy rows, config.json byte-unchanged"
          % ("; ".join(bad), [b7[w] for w in sorted(b7)], occ7, occ7b,
             non_ascii))

    af.close()
    ven.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
