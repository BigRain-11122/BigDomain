"""Acceptance suite for the studio onboarding annual-fee face
(BigDomain R625; canon = BLUEPRINT sec-4 B-side price rows B1/B2,
joint delivery per the explore-lane same-structure note).
Asserts the pre-registered criteria AC-SB1..AC-SB7 from the R625
backlog row (criteria were registered before this code existed;
honesty law). Each criterion prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL.

Usage: python test_studio.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L      # noqa: E402  (P-47-2b core)
import venue as V       # noqa: E402  (R605 occupancy engine)
import studio as S      # noqa: E402  (R625 studio onboarding face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_st_error(fn, *codes):
    try:
        fn()
    except S.StudioError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="studio-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    ven = V.VenueFace(led)
    stf = S.StudioFace(led, ven)

    led.mint_to_pool("pool:reserve", 200000, "SETTLE-ST-A", "settlement")
    for who, av in (("usr:alice", "alice"), ("usr:bob", "bob"),
                    ("usr:carol", "carol")):
        led.ensure_account(who, census_avatar_id=av)
        led.adjust([("pool:reserve", "debit", 50000), (who, "credit", 50000)],
                   "manual:fund-%s" % av, "suite funding %s" % av)
    bal = lambda who: led.balance(who)["balance"]  # noqa: E731

    # -- AC-SB1 reference law: one registry table, writes via the engine --
    reg_g = stf.register_studio("studio:pixelforge", "game_studio")
    reg_idem = stf.register_studio("studio:pixelforge", "game_studio")
    ok_km, code_km = expect_st_error(
        lambda: stf.register_studio("studio:pixelforge", "quant_studio"),
        S.E_ST_KIND_MISMATCH)
    ok_badk, code_bk = expect_st_error(
        lambda: stf.register_studio("studio:x", "film_studio"),
        S.E_ST_BAD_ARGS)
    reg_q = stf.register_studio("studio:quantworks", "quant_studio")
    conn = sqlite3.connect(db_path)
    my_tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
        " AND name LIKE 'studio%'").fetchall()]
    conn.close()
    with open(os.path.join(BASE, "studio.py"), encoding="utf-8") as h:
        src = h.read()
    ok1 = (reg_g["idempotent"] is False and reg_idem["idempotent"] is True
           and reg_q["idempotent"] is False
           and ok_km and code_km == S.E_ST_KIND_MISMATCH
           and ok_badk and code_bk == S.E_ST_BAD_ARGS
           and my_tables == ["studio_products"]
           and "INSERT INTO venue_occupancy" not in src
           and "UPDATE" not in src)
    record("AC-SB1", ok1, "registry = studio_products only (%s);"
          " re-register idempotent; kind-drift %s; bad kind %s;"
          " module source has zero direct INSERT INTO venue_occupancy and"
          " zero row-mutation verb surface"
          % (my_tables, code_km, code_bk))

    # -- AC-SB2 annual window: one spend, gates before the spend ----------
    b0 = bal("usr:alice")
    r1 = stf.onboard_studio("usr:alice", "studio:pixelforge", 26, 9800,
                            "order:sb2a")
    b1 = bal("usr:alice")
    occ = ven.occupancy_ledger("studio:pixelforge")
    ok_dup, code_dp = expect_st_error(
        lambda: stf.onboard_studio("usr:alice", "studio:pixelforge", 26,
                                   9800, "order:sb2b"),
        S.E_ST_DUP)
    b2 = bal("usr:alice")
    ok_taken, code_tk = expect_st_error(
        lambda: stf.onboard_studio("usr:bob", "studio:pixelforge", 26,
                                   9800, "order:sb2c"),
        S.E_ST_TAKEN)
    b_bob = bal("usr:bob")
    r2 = stf.onboard_studio("usr:alice", "studio:pixelforge", 27, 9800,
                            "order:sb2d")
    b3 = bal("usr:alice")
    ok2 = (b0 - b1 == 9800 and r1["fee"] == 9800
           and r1["window"] == [26, 26]
           and len(occ) == 1 and occ[0]["bound_spend_tx"] == r1["spend_tx"]
           and ok_dup and code_dp == S.E_ST_DUP and b2 == b1
           and ok_taken and code_tk == S.E_ST_TAKEN and b_bob == 50000
           and b1 - b3 == 9800 and r2["window"] == [27, 27]
           and stf.studio_tenant("studio:pixelforge", 26) == "usr:alice"
           and stf.studio_tenant("studio:pixelforge", 27) == "usr:alice"
           and stf.studio_tenant("studio:pixelforge", 28) is None)
    record("AC-SB2", ok2, "year window [26,26] one spend 9800 (bal delta"
          " %d); replay %s zero charge; other-account %s zero charge;"
          " renewal year 27 legal (window %s, delta %d); tenant 26/27"
          " = alice, 28 = None"
          % (b0 - b1, code_dp, code_tk, r2["window"], b1 - b3))

    # -- AC-SB3 two kinds + parallel studios are independent ---------------
    b_pre = bal("usr:alice")
    rq = stf.onboard_studio("usr:alice", "studio:quantworks", 26, 19800,
                            "order:sb3a")
    b_mid = bal("usr:alice")
    stf.register_studio("studio:indienest", "game_studio")
    rc = stf.onboard_studio("usr:carol", "studio:indienest", 26, 9800,
                            "order:sb3b")
    b_carol = bal("usr:carol")
    ok3 = (b_pre - b_mid == 19800 and rq["st_kind"] == "quant_studio"
           and 50000 - b_carol == 9800 and rc["st_kind"] == "game_studio"
           and stf.studio_tenant("studio:quantworks", 26) == "usr:alice"
           and stf.studio_tenant("studio:indienest", 26) == "usr:carol")
    record("AC-SB3", ok3, "same account holds game (pixelforge) + quant"
          " (quantworks) seats in year 26 legally (delta %d); parallel"
          " same-kind studio indienest onboarded by carol legally (delta"
          " %d); each onboarding exactly one spend"
          % (b_pre - b_mid, 50000 - b_carol))

    # -- AC-SB4 registry gate + bad args, all zero side effects -----------
    ok_unk, code_uk = expect_st_error(
        lambda: stf.onboard_studio("usr:bob", "studio:ghostworks", 26, 9800,
                                   "order:sb4a"),
        S.E_ST_UNKNOWN)
    ok_acct, code_ac = expect_st_error(
        lambda: stf.onboard_studio("corp:acme", "studio:pixelforge", 26,
                                   9800, "order:sb4b"),
        S.E_ST_BAD_ARGS)
    ok_price, code_pr = expect_st_error(
        lambda: stf.onboard_studio("usr:bob", "studio:pixelforge", 26, 0,
                                   "order:sb4c"),
        S.E_ST_BAD_ARGS)
    ok_year, code_yr = expect_st_error(
        lambda: stf.onboard_studio("usr:bob", "studio:pixelforge", -1,
                                   9800, "order:sb4d"),
        S.E_ST_BAD_ARGS)
    ok_ref, code_rf = expect_st_error(
        lambda: stf.onboard_studio("usr:bob", "studio:pixelforge", 26, 9800,
                                   "  "),
        S.E_ST_BAD_ARGS)
    ok_unk_ben, code_ub = expect_st_error(
        lambda: stf.studio_benefits("studio:ghostworks"),
        S.E_ST_UNKNOWN)
    b_bob_after = bal("usr:bob")
    ok4 = (ok_unk and code_uk == S.E_ST_UNKNOWN
           and ok_acct and code_ac == S.E_ST_BAD_ARGS
           and ok_price and code_pr == S.E_ST_BAD_ARGS
           and ok_year and code_yr == S.E_ST_BAD_ARGS
           and ok_ref and code_rf == S.E_ST_BAD_ARGS
           and ok_unk_ben and code_ub == S.E_ST_UNKNOWN
           and b_bob_after == 50000)
    record("AC-SB4", ok4, "unknown studio %s; bad account %s; bad price"
          " %s; bad year %s; empty ref %s; benefits-on-unknown %s;"
          " bob balance flat at %d (all rejects zero charge)"
          % (code_uk, code_ac, code_pr, code_yr, code_rf, code_ub,
             b_bob_after))

    # -- AC-SB5 benefit bundles + derived profile read faces ---------------
    ben_g = stf.studio_benefits("studio:pixelforge")
    ben_q = stf.studio_benefits("studio:quantworks")
    b_pre_read = bal("usr:alice")
    prof = stf.studio_profile("usr:alice", 26)
    b_post_read = bal("usr:alice")
    prof_bob = stf.studio_profile("usr:bob", 26)
    alice_ids = sorted(item["studio_id"] for item in prof["subscriptions"])
    ok5 = (ben_g["benefits"] == ["idea_pool_access", "player_traffic_boost",
                                 "studio_floor"]
           and ben_q["benefits"] == ["stock_inspiration_feed",
                                     "co_create_observation_entry",
                                     "quant_screen_spotlight"]
           and alice_ids == ["studio:pixelforge", "studio:quantworks"]
           and all(item["spend_tx"] for item in prof["subscriptions"])
           and all(item["year"] == 26 for item in prof["subscriptions"])
           and b_post_read == b_pre_read
           and prof_bob["subscriptions"] == []
           and stf.studio_profile("usr:alice", 28)["subscriptions"] == [])
    record("AC-SB5", ok5, "canon bundles B1 %s / B2 %s; alice profile at"
          " 26 = %s (all rows carry spend tx, year 26); reads move zero"
          " tokens; empty profile for bob; year-28 profile empty"
          % (ben_g["benefits"], ben_q["benefits"], alice_ids))

    # -- AC-SB6 isolation law: spends are the only token touches -----------
    spent_alice = 50000 - bal("usr:alice")
    spent_bob = 50000 - bal("usr:bob")
    spent_carol = 50000 - bal("usr:carol")
    fees = r1["fee"] + r2["fee"] + rq["fee"] + rc["fee"]
    conn = sqlite3.connect(db_path)
    studio_rows = conn.execute(
        "SELECT COUNT(*) FROM studio_products").fetchone()[0]
    venue_studio_rows = conn.execute(
        "SELECT COUNT(*) FROM venue_occupancy WHERE unit_id IN"
        " ('studio:pixelforge','studio:quantworks','studio:indienest')"
    ).fetchone()[0]
    conn.close()
    pool_left = led.balance("pool:reserve")["balance"]
    ok6 = (spent_alice == r1["fee"] + r2["fee"] + rq["fee"]
           and spent_bob == 0 and spent_carol == rc["fee"]
           and fees == 9800 * 2 + 19800 + 9800
           and pool_left == 200000 - 150000 + fees
           and studio_rows == 3 and venue_studio_rows == 4
           and "refund" not in src and "withdraw" not in src
           and "convert" not in src and "transfer" not in src)
    record("AC-SB6", ok6, "spends alice %d = 9800+9800+19800, bob %d = 0,"
          " carol %d = 9800; total fees %d; pool:reserve %d = 50,000"
          " seeded + fees recirculated (conservation); 3 registry rows"
          " immutable, 4 venue occupancy rows; zero banned verbs in"
          " module source" % (spent_alice, spent_bob, spent_carol, fees,
                             pool_left))

    # -- AC-SB7 hard laws: ASCII, config bytes, caller-supplied prices -----
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    non_ascii = sum(1 for byte in
                     open(os.path.join(BASE, "studio.py"), "rb").read()
                     if byte > 127)
    ok7 = (cfg_after == cfg_bytes and non_ascii == 0
           and cfg == json.loads(cfg_bytes.decode("utf-8")))
    record("AC-SB7", ok7, "config.json byte-identical before/after"
          " (zero new keys, prices arrive only as caller arguments,"
          " production anchors 9800/19800 CNY stay [needs-CEO] P1"
          " approval-only); studio.py pure ASCII (%d non-ascii bytes)"
          % non_ascii)

    led.close()
    ven.close()
    stf.close()
    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s (%d/%d criteria green)%s"
          % ("PASS" if not fails else "FAIL",
             len(RESULTS) - len(fails), len(RESULTS),
             "" if not fails else " - failed: " + ",".join(fails)),
          flush=True)
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())
