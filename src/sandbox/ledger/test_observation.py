"""Acceptance suite for the strategy paid-observation face
(BigDomain R623; canon = BLUEPRINT sec-4 strategy co-creation
observation line). Asserts the pre-registered criteria
AC-OB1..AC-OB7 from the R623 backlog row (criteria were registered
before this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Usage: python test_observation.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L   # noqa: E402  (P-47-2b core)
import observation as O  # noqa: E402  (R623 extension face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_o_error(fn, *codes):
    try:
        fn()
    except O.ObservationError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


ALPHA = {"sharpe": 1.9, "cagr_pct": 24.0, "max_dd_pct": -12.5,
         "trades": 311}
BETA = {"sharpe": 1.2, "cagr_pct": 9.0, "max_dd_pct": -6.5, "trades": 88}


def main():
    tmp = tempfile.mkdtemp(prefix="observation-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    of = O.ObservationFace(led)

    led.mint_to_pool("pool:reserve", 1000, "SETTLE-OB-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    led.adjust([("pool:reserve", "debit", 300), ("usr:alice", "credit", 300)],
               "manual:fund-a", "suite funding alice")
    led.adjust([("pool:reserve", "debit", 500), ("usr:bob", "credit", 500)],
               "manual:fund-b", "suite funding bob")
    led.adjust([("pool:reserve", "debit", 200), ("usr:carol", "credit", 200)],
               "manual:fund-c", "suite funding carol")
    bal = lambda who: led.balance(who)["balance"]  # noqa: E731

    # -- AC-OB1 registry gate + results-only registration ---------------
    b_bob0 = bal("usr:bob")
    ok_unk_buy, code_ub = expect_o_error(
        lambda: of.buy_single("usr:bob", "strat:ghost", 99, "order:ob1a"),
        O.E_OBS_UNKNOWN)
    ok_unk_obs, code_uo = expect_o_error(
        lambda: of.observe("usr:bob", "strat:ghost", "2099-01"),
        O.E_OBS_UNKNOWN)
    reg1 = of.register_strategy("strat:alpha", "usr:maker", ALPHA)
    ok_re, code_re = expect_o_error(
        lambda: of.register_strategy("strat:alpha", "usr:maker", ALPHA),
        O.E_OBS_EXISTS)
    ok_bad_sum, code_bs = expect_o_error(
        lambda: of.register_strategy("strat:empty", "usr:maker", {}),
        O.E_OBS_BAD_ARGS)
    conn = sqlite3.connect(db_path)
    n_reg = conn.execute("SELECT COUNT(*) FROM obs_strategies").fetchone()[0]
    n_grant = conn.execute("SELECT COUNT(*) FROM obs_grants").fetchone()[0]
    conn.close()
    ok1 = (ok_unk_buy and code_ub == O.E_OBS_UNKNOWN
           and ok_unk_obs and code_uo == O.E_OBS_UNKNOWN
           and ok_re and code_re == O.E_OBS_EXISTS
           and ok_bad_sum and code_bs == O.E_OBS_BAD_ARGS
           and reg1["registered"] and n_reg == 1 and n_grant == 0
           and bal("usr:bob") == b_bob0)
    record("AC-OB1", ok1, "unknown strategy buy/observe rejected (%s/%s)"
          " zero charge (%d==%d) zero grant rows; re-register %s; empty"
          " summary %s; registry holds exactly 1 row (results summary"
          " only - no source parameter on the face)"
          % (code_ub, code_uo, b_bob0, bal("usr:bob"), code_re, code_bs))

    # -- AC-OB2 single purchase: exactly one spend bound to its tx ------
    b_al0 = bal("usr:alice")
    g1 = of.buy_single("usr:alice", "strat:alpha", 99, "order:ob2a")
    b_al1 = bal("usr:alice")
    conn = sqlite3.connect(db_path)
    tx_head = conn.execute(
        "SELECT type FROM ledger_tx WHERE tx_id = ?",
        (g1["spend_tx"],)).fetchone()
    tx_leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = 'usr:alice'", (g1["spend_tx"],)).fetchone()
    conn.close()
    view = of.entitlements_view("usr:alice")["grants"]
    ok2 = (b_al1 == b_al0 - 99 and len(view) == 1
           and view[0]["kind"] == "single"
           and view[0]["strategy_id"] == "strat:alpha"
           and view[0]["spend_tx"] == g1["spend_tx"]
           and tx_head is not None and tx_head[0] == "spend"
           and tx_leg is not None and tx_leg[0] == "debit")
    record("AC-OB2", ok2, "single grant #%d charged once (%d->%d); grant"
          " row binds real spend tx %s (type=spend, debit leg);"
          " entitlements_view carries tx provenance"
          % (g1["grant_id"], b_al0, b_al1, g1["spend_tx"][:10]))

    # -- AC-OB3 duplicate single: rejected BEFORE the spend --------------
    g_al_count = len(of.entitlements_view("usr:alice")["grants"])
    ok_dup, code_dup = expect_o_error(
        lambda: of.buy_single("usr:alice", "strat:alpha", 99, "order:ob3a"),
        O.E_OBS_DUP)
    ok3 = (ok_dup and code_dup == O.E_OBS_DUP
           and bal("usr:alice") == b_al1
           and len(of.entitlements_view("usr:alice")["grants"])
           == g_al_count)
    record("AC-OB3", ok3, "same (account, strategy) repurchase rejected %s"
          " with the balance untouched (%d==%d) and grant rows"
          " unchanged (%d) - refusal happens before the spend"
          % (code_dup, b_al1, bal("usr:alice"), g_al_count))

    # -- AC-OB4 monthly pass: one spend per month, window idempotent -----
    of.register_strategy("strat:beta", "usr:maker", BETA)
    of.register_strategy("strat:gamma", "usr:maker",
                         {"sharpe": 0.8, "cagr_pct": 5.0})
    b_bob1 = bal("usr:bob")
    p1 = of.buy_pass("usr:bob", "2099-01", 199, "order:ob4a")
    b_bob2 = bal("usr:bob")
    ok_pdup, code_pd = expect_o_error(
        lambda: of.buy_pass("usr:bob", "2099-01", 199, "order:ob4b"),
        O.E_OBS_PASS_DUP)
    b_after_dup = bal("usr:bob")
    p2 = of.buy_pass("usr:bob", "2099-02", 199, "order:ob4c")
    b_bob3 = bal("usr:bob")
    gates = [of.can_observe("usr:bob", s, "2099-01")["allowed"]
             for s in ("strat:alpha", "strat:beta", "strat:gamma")]
    ok4 = (b_bob2 == b_bob1 - 199 and ok_pdup
           and code_pd == O.E_OBS_PASS_DUP and b_after_dup == b_bob2
           and b_bob3 == b_bob2 - 199
           and p1["spend_tx"] != p2["spend_tx"]
           and gates == [True, True, True])
    record("AC-OB4", ok4, "pass month 2099-01 charged once (%d->%d);"
          " same-month repurchase rejected %s before the spend (balance"
          " still %d); another month 2099-02 is a separate legal spend"
          " (%d); distinct txs %s/%s; one pass opens all three"
          " strategies inside its window (%s)"
          % (b_bob1, b_bob2, code_pd, b_after_dup, b_bob3,
             p1["spend_tx"][:8], p2["spend_tx"][:8], gates))

    # -- AC-OB5 fail-closed gate, permanence, window expiry -------------
    b_carol0 = bal("usr:carol")
    ok_denied, code_dn = expect_o_error(
        lambda: of.observe("usr:carol", "strat:alpha", "2099-01"),
        O.E_OBS_DENIED)
    v_perm = of.observe("usr:alice", "strat:alpha", "2099-03")
    v_pass_in = of.observe("usr:bob", "strat:beta", "2099-01")
    ok_exp, code_exp = expect_o_error(
        lambda: of.observe("usr:bob", "strat:beta", "2099-03"),
        O.E_OBS_DENIED)
    ok5 = (ok_denied and code_dn == O.E_OBS_DENIED
           and bal("usr:carol") == b_carol0
           and v_perm["kind"] == "single" and v_pass_in["kind"] == "pass"
           and ok_exp and code_exp == O.E_OBS_DENIED)
    record("AC-OB5", ok5, "carol with no entitlement rejected %s zero"
          " charge (%d==%d); alice's single grant still works in a later"
          " month 2099-03 (kind=single); bob's pass works inside 2099-01"
          " (kind=pass) but is denied %s outside its window"
          % (code_dn, b_carol0, bal("usr:carol"), code_exp))

    # -- AC-OB6 results-only view: exact key set, no source column ------
    v = of.observe("usr:alice", "strat:alpha", "2099-03")
    conn = sqlite3.connect(db_path)
    cols = [r[1] for r in conn.execute(
        "PRAGMA table_info(obs_strategies)").fetchall()]
    conn.close()
    bal_before = bal("usr:alice")
    of.can_observe("usr:alice", "strat:alpha", "2099-03")
    of.strategy_view("strat:alpha")
    bal_after = bal("usr:alice")
    round_trip = of.strategy_view("strat:alpha")["summary"] == ALPHA
    with open(os.path.join(BASE, "observation.py"), encoding="utf-8") as h:
        src = h.read()
    no_source_api = ("source_code" not in src and '"source"' not in src
                     and "'source'" not in src)
    ok6 = (sorted(v.keys()) == ["kind", "strategy_id", "summary", "tx"]
           and "source" not in cols and cols == ["strategy_id",
                                                 "creator_account",
                                                 "summary_json",
                                                 "registered_utc"]
           and bal_before == bal_after and round_trip and no_source_api
           and v["summary"] == ALPHA)
    record("AC-OB6", ok6, "observe view keys exactly {strategy_id, "
          "summary, kind, tx}; registry columns %s (no source column);"
          " observe/can_observe/strategy_view are pure reads (balance"
          " %d==%d); summary round-trips byte-equal; module has no"
          " source-code accessor" % (cols, bal_before, bal_after))

    # -- AC-OB7 bad args zero side effects + hard-law source scan -------
    b7a, b7b, b7c = bal("usr:alice"), bal("usr:bob"), bal("usr:carol")
    g7 = (len(of.entitlements_view("usr:alice")["grants"]),
          len(of.entitlements_view("usr:bob")["grants"]),
          len(of.entitlements_view("usr:carol")["grants"]))
    bad = []
    raised_all = True
    for label, fn, code in (
            ("bad buyer", lambda: of.buy_single("svc:x", "strat:alpha",
                                                99, "order:ob7a"),
             O.E_OBS_BAD_ACCOUNT),
            ("zero price", lambda: of.buy_single("usr:carol",
                                                "strat:alpha", 0,
                                                "order:ob7b"),
             O.E_OBS_BAD_PRICE),
            ("bool price", lambda: of.buy_single("usr:carol",
                                                "strat:alpha", True,
                                                "order:ob7c"),
             O.E_OBS_BAD_PRICE),
            ("empty ref", lambda: of.buy_single("usr:carol",
                                                "strat:alpha", 99, "  "),
             O.E_OBS_BAD_ARGS),
            ("bad month fmt", lambda: of.buy_pass("usr:carol", "209901",
                                                  199, "order:ob7d"),
             O.E_OBS_BAD_MONTH),
            ("month 13", lambda: of.buy_pass("usr:carol", "2099-13",
                                             199, "order:ob7e"),
             O.E_OBS_BAD_MONTH),
            ("empty strategy id", lambda: of.observe("usr:carol", "  ",
                                                     "2099-01"),
             O.E_OBS_BAD_ARGS),
            ("bad creator", lambda: of.register_strategy("strat:delta",
                                                         "svc:x", ALPHA),
             O.E_OBS_BAD_ACCOUNT)):
        ok_one, got = expect_o_error(fn, code)
        if ok_one:
            bad.append("%s=%s" % (label, got))
        else:
            bad.append("%s NOT-RAISED(%s)" % (label, got))
            raised_all = False
    with open(os.path.join(BASE, "observation.py"), encoding="utf-8") as h:
        src = h.read()
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    no_update = ("UPDATE obs_grants" not in src
                 and "UPDATE obs_strategies" not in src)
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_after = h.read()
    ok7 = (b7a == bal("usr:alice") and b7b == bal("usr:bob")
           and b7c == bal("usr:carol")
           and g7 == (len(of.entitlements_view("usr:alice")["grants"]),
                      len(of.entitlements_view("usr:bob")["grants"]),
                      len(of.entitlements_view("usr:carol")["grants"]))
           and raised_all and non_ascii == 0 and no_update
           and cfg_after == cfg_bytes)
    record("AC-OB7", ok7, "all bad args rejected (%s); zero side effects"
          " (balances %d/%d/%d unchanged, grant rows unchanged %s); module"
          " pure ASCII (%d non-ascii); zero UPDATE surface; config.json"
          " byte-stable" % ("; ".join(bad), b7a, b7b, b7c, g7, non_ascii))

    of.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
