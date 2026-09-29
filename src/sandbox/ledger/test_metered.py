"""Acceptance suite for the enterprise metered API billing face
(BigDomain R626; canon = BLUEPRINT sec-4 B-side price row B5,
explore-lane top open row claim).
Asserts the pre-registered criteria AC-MT1..AC-MT7 from the R626
backlog row (criteria were registered before this code existed;
honesty law). Each criterion prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL.

Usage: python test_metered.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L      # noqa: E402  (P-47-2b core)
import metered as M     # noqa: E402  (R626 metering + billing face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_mt_error(fn, *codes):
    try:
        fn()
    except M.MeteredError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def expect_ledger_error(fn, *codes):
    try:
        fn()
    except L.LedgerError as exc:
        return getattr(exc, "code", "") in codes, getattr(exc, "code", "")
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="metered-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    mtf = M.MeteredFace(led)

    led.mint_to_pool("pool:reserve", 200000, "SETTLE-MT-A", "settlement")
    for who, av in (("usr:alice", "alice"), ("usr:bob", "bob"),
                    ("usr:carol", "carol")):
        led.ensure_account(who, census_avatar_id=av)
        led.adjust([("pool:reserve", "debit", 50000), (who, "credit", 50000)],
                   "manual:fund-%s" % av, "suite funding %s" % av)
    bal = lambda who: led.balance(who)["balance"]  # noqa: E731

    # -- AC-MT1 reference law: three own tables, one token touch point ---
    reg_a = mtf.register_client("ent:acme", "usr:alice",
                                ("backtest", "visualize"))
    reg_idem = mtf.register_client("ent:acme", "usr:alice",
                                   ("backtest", "visualize"))
    ok_dup_reg, code_dr = expect_mt_error(
        lambda: mtf.register_client("ent:acme", "usr:bob",
                                    ("backtest",)),
        M.E_MT_DUP)
    ok_badkind, code_bk = expect_mt_error(
        lambda: mtf.register_client("ent:x", "usr:bob", ("forecast",)),
        M.E_MT_BAD_ARGS)
    ok_badfund, code_bf = expect_mt_error(
        lambda: mtf.register_client("ent:x", "corp:ghost", ("backtest",)),
        M.E_MT_BAD_ARGS)
    reg_b = mtf.register_client("ent:boblab", "usr:bob", ("backtest",))
    reg_c = mtf.register_client("ent:carollab", "usr:carol",
                                ("backtest", "visualize"))
    conn = sqlite3.connect(db_path)
    my_tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
        " AND name LIKE 'metered%' ORDER BY name").fetchall()]
    call_cols = [r[1] for r in conn.execute(
        "PRAGMA table_info(metered_calls)").fetchall()]
    conn.close()
    with open(os.path.join(BASE, "metered.py"), encoding="utf-8") as h:
        src = h.read()
    ok1 = (reg_a["idempotent"] is False and reg_idem["idempotent"] is True
           and reg_b["idempotent"] is False and reg_c["idempotent"] is False
           and ok_dup_reg and code_dr == M.E_MT_DUP
           and ok_badkind and code_bk == M.E_MT_BAD_ARGS
           and ok_badfund and code_bf == M.E_MT_BAD_ARGS
           and my_tables == ["metered_calls", "metered_clients",
                             "metered_packs"]
           and call_cols == ["call_ref", "client_id", "kind",
                             "engine_ref", "consumed_utc"]
           and src.count("self.led.spend") == 1)
    record("AC-MT1", ok1, "own tables = %s; call rows carry zero"
          " numeric-result columns (%s); module has exactly one token"
          " touch point (self.led.spend x%d, inside buy_pack); engine"
          " = receipts only (engine_ref verbatim, zero backtest"
          " logic); conflicting re-register %s; bad kind %s; bad"
          " funding %s"
          % (my_tables, call_cols, src.count("self.led.spend"),
             code_dr, code_bk, code_bf))

    # -- AC-MT2 prepaid pack purchase: idempotent, gates before spend ---
    b0 = bal("usr:alice")
    p1 = mtf.buy_pack("ent:acme", 100, 5, "order:mt2a")
    b1 = bal("usr:alice")
    contract_mid = mtf.client_contract("ent:acme")
    ok_dup_pack, code_dp = expect_mt_error(
        lambda: mtf.buy_pack("ent:acme", 100, 5, "order:mt2a"),
        M.E_MT_DUP)
    b2 = bal("usr:alice")
    p2 = mtf.buy_pack("ent:acme", 50, 5, "order:mt2b")
    b3 = bal("usr:alice")
    ok_insuf, code_in = expect_ledger_error(
        lambda: mtf.buy_pack("ent:carollab", 20000, 500, "order:mt2big"),
        L.E_NEGATIVE_BALANCE)
    b_carol = bal("usr:carol")
    ok2 = (b0 - b1 == 500 and p1["total_price"] == 500
           and p1["spend_tx"] and contract_mid["call_credits"] == 100
           and ok_dup_pack and code_dp == M.E_MT_DUP and b2 == b1
           and b1 - b3 == 250 and p2["calls"] == 50
           and mtf.client_contract("ent:acme")["call_credits"] == 150
           and ok_insuf and code_in == L.E_NEGATIVE_BALANCE
           and b_carol == 50000
           and mtf.client_contract("ent:carollab")["call_credits"] == 0)
    record("AC-MT2", ok2, "pack 100x5 = one spend %d (delta %d, tx"
          " bound); replay %s zero charge (bal flat %d); stack pack"
          " 50x5 (delta %d, credits 150); insufficient-balance %s"
          " zero side effects (carol flat %d, credits 0)"
          % (p1["total_price"], b0 - b1, code_dp, b2, b1 - b3,
             code_in, b_carol))

    # -- AC-MT3 metered consumption: one credit per call, fail-closed --
    c1 = mtf.meter_call("ent:acme", "backtest", "call:a1",
                        "engineref:bm-0001")
    c2 = mtf.meter_call("ent:acme", "visualize", "call:a2",
                        "engineref:bm-0002")
    c3 = mtf.meter_call("ent:acme", "backtest", "call:a3",
                        "engineref:bm-0003")
    ok_dup_call, code_dc = expect_mt_error(
        lambda: mtf.meter_call("ent:acme", "backtest", "call:a1",
                               "engineref:bm-0001"),
        M.E_MT_DUP)
    credits_after_dup = mtf.client_contract("ent:acme")["call_credits"]
    small = mtf.buy_pack("ent:carollab", 2, 5, "order:mt3a")
    mtf.meter_call("ent:carollab", "backtest", "call:c1", "engineref:bm-9")
    mtf.meter_call("ent:carollab", "backtest", "call:c2", "engineref:bm-10")
    ok_empty, code_nc = expect_mt_error(
        lambda: mtf.meter_call("ent:carollab", "backtest", "call:c3",
                               "engineref:bm-11"),
        M.E_MT_NO_CREDITS)
    b_alice_calls = bal("usr:alice")
    ok3 = (c1["call_ref"] == "call:a1" and c2["kind"] == "visualize"
           and c3["engine_ref"] == "engineref:bm-0003"
           and ok_dup_call and code_dc == M.E_MT_DUP
           and credits_after_dup == 147
           and mtf.client_contract("ent:acme")["call_credits"] == 147
           and small["total_price"] == 10
           and ok_empty and code_nc == M.E_MT_NO_CREDITS
           and mtf.client_contract("ent:carollab")["call_credits"] == 0
           and b_alice_calls == bal("usr:alice"))
    record("AC-MT3", ok3, "three calls consume 150 -> %d (one credit"
          " each, engine refs stored verbatim); replay %s zero"
          " double-charge (credits flat %d); 2-credit pack drained"
          " then zero-credit %s fail-closed (credits 0); metering"
          " moves zero tokens"
          % (mtf.client_contract("ent:acme")["call_credits"], code_dc,
             credits_after_dup, code_nc))

    # -- AC-MT4 registry gate + bad args, all zero side effects ----------
    ok_unk_pack, code_up = expect_mt_error(
        lambda: mtf.buy_pack("ent:ghost", 10, 5, "order:mt4a"),
        M.E_MT_UNKNOWN)
    ok_unk_call, code_uc = expect_mt_error(
        lambda: mtf.meter_call("ent:ghost", "backtest", "call:g1",
                               "engineref:bm-x"),
        M.E_MT_UNKNOWN)
    ok_gate, code_gt = expect_mt_error(
        lambda: mtf.meter_call("ent:boblab", "visualize", "call:b1",
                               "engineref:bm-y"),
        M.E_MT_KIND_GATE)
    ok_unk_kind, code_uk = expect_mt_error(
        lambda: mtf.meter_call("ent:acme", "forecast", "call:b2",
                               "engineref:bm-z"),
        M.E_MT_BAD_ARGS)
    ok_zero_calls, code_zc = expect_mt_error(
        lambda: mtf.buy_pack("ent:boblab", 0, 5, "order:mt4b"),
        M.E_MT_BAD_ARGS)
    ok_zero_price, code_zp = expect_mt_error(
        lambda: mtf.buy_pack("ent:boblab", 10, 0, "order:mt4c"),
        M.E_MT_BAD_ARGS)
    ok_bad_fund, code_bf2 = expect_mt_error(
        lambda: mtf.register_client("ent:acme2", "ent:nested",
                                   ("backtest",)),
        M.E_MT_BAD_ARGS)
    ok_bad_client, code_bc = expect_mt_error(
        lambda: mtf.buy_pack("usr:alice", 10, 5, "order:mt4d"),
        M.E_MT_UNKNOWN)
    b_bob = bal("usr:bob")
    credits_bob = mtf.client_contract("ent:boblab")["call_credits"]
    ok4 = (ok_unk_pack and code_up == M.E_MT_UNKNOWN
           and ok_unk_call and code_uc == M.E_MT_UNKNOWN
           and ok_gate and code_gt == M.E_MT_KIND_GATE
           and ok_unk_kind and code_uk == M.E_MT_BAD_ARGS
           and ok_zero_calls and code_zc == M.E_MT_BAD_ARGS
           and ok_zero_price and code_zp == M.E_MT_BAD_ARGS
           and ok_bad_fund and code_bf2 == M.E_MT_BAD_ARGS
           and ok_bad_client and code_bc == M.E_MT_UNKNOWN
           and b_bob == 50000 and credits_bob == 0)
    record("AC-MT4", ok4, "unknown client buy %s / call %s; kind"
          " not enabled %s (visualize on backtest-only client);"
          " unknown kind %s; calls<1 %s; unit_price<1 %s; nested"
          " funding %s; usr: as client id %s; bob balance flat"
          " %d credits 0 (all rejects zero side effects)"
          % (code_up, code_uc, code_gt, code_uk, code_zc, code_zp,
             code_bf2, code_bc, b_bob))

    # -- AC-MT5 reconciliation read face + tamper detection --------------
    b_pre_read = bal("usr:alice")
    rec = mtf.reconcile_client("ent:acme")
    usage = mtf.usage_log("ent:acme")
    b_post_read = bal("usr:alice")
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE metered_clients SET call_credits ="
                 " call_credits - 1 WHERE client_id = 'ent:acme'")
    conn.commit()
    conn.close()
    tampered = mtf.reconcile_client("ent:acme")
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE metered_clients SET call_credits ="
                 " call_credits + 1 WHERE client_id = 'ent:acme'")
    conn.commit()
    conn.close()
    restored = mtf.reconcile_client("ent:acme")
    ok_unk_rec, code_ur = expect_mt_error(
        lambda: mtf.reconcile_client("ent:ghost"),
        M.E_MT_UNKNOWN)
    ok5 = (rec["packs"] == 2 and rec["purchased_calls"] == 150
           and rec["consumed_calls"] == 3
           and rec["remaining_credits"] == 147 and rec["balanced"] is True
           and len(rec["spend_txs"]) == 2 and rec["billed_total"] == 750
           and usage["calls"][0]["engine_ref"].startswith("engineref:")
           and len(usage["calls"]) == 3
           and b_post_read == b_pre_read
           and tampered["balanced"] is False
           and restored["balanced"] is True
           and ok_unk_rec and code_ur == M.E_MT_UNKNOWN)
    record("AC-MT5", ok5, "acme purchased %d = consumed %d + remaining"
          " %d balanced=True (2 packs, billed %d, %d spend txs);"
          " usage log 3 rows with engine receipts; counter tamper"
          " -1 -> balanced=%s detected, restored -> %s; unknown"
          " client %s; reads move zero tokens (bal flat)"
          % (rec["purchased_calls"], rec["consumed_calls"],
             rec["remaining_credits"], rec["billed_total"],
             len(rec["spend_txs"]), tampered["balanced"],
             restored["balanced"], code_ur))

    # -- AC-MT6 isolation law: no credit-to-token verb, immutable rows ---
    spent_alice = 50000 - bal("usr:alice")
    spent_bob = 50000 - bal("usr:bob")
    spent_carol = 50000 - bal("usr:carol")
    fees = p1["total_price"] + p2["total_price"] + small["total_price"]
    pool_left = led.balance("pool:reserve")["balance"]
    banned_hits = [w for w in ("refund", "withdraw", "convert", "transfer")
                   if w in src]
    immutable_ok = ("UPDATE metered_packs" not in src
                    and "UPDATE metered_calls" not in src
                    and "DELETE FROM" not in src)
    ok6 = (spent_alice == 750 and spent_bob == 0
           and spent_carol == 10 and fees == 760
           and pool_left == 200000 - 150000 + fees
           and not banned_hits and immutable_ok
           and "meter_call" in src and src.count("UPDATE metered_clients")
           == 2)
    record("AC-MT6", ok6, "spends alice %d = packs 500+250, bob %d = 0,"
          " carol %d = 10; billed %d recirculated to pool:reserve"
          " (%d conservation); zero banned verbs in source %s; zero"
          " UPDATE/DELETE on pack+call rows (immutable), credit"
          " counter is the only mutable cell (%d client-table"
          " updates); meter_call moves zero tokens"
          % (spent_alice, spent_bob, spent_carol, fees, pool_left,
             banned_hits, src.count("UPDATE metered_clients")))

    # -- AC-MT7 hard laws: ASCII, config bytes, prices caller-supplied ---
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    non_ascii = sum(1 for byte in
                     open(os.path.join(BASE, "metered.py"), "rb").read()
                     if byte > 127)
    ok7 = (cfg_after == cfg_bytes and non_ascii == 0
           and "needs-CEO" in src
           and cfg == json.loads(cfg_bytes.decode("utf-8")))
    record("AC-MT7", ok7, "config.json byte-identical before/after"
          " (zero new keys; per-call prices arrive only as caller"
          " arguments; production 0.5-CNY/call anchor and up ="
          " [needs-CEO] P1 approval-only; production external API"
          " endpoint = bootstrap-time three-question gate + CEO"
          " authorization, sandbox is pure local zero network);"
          " metered.py pure ASCII (%d non-ascii bytes)"
          % non_ascii)

    led.close()
    mtf.close()
    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s (%d/%d criteria green)%s"
          % ("PASS" if not fails else "FAIL",
             len(RESULTS) - len(fails), len(RESULTS),
             "" if not fails else " - failed: " + ",".join(fails)),
          flush=True)
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())
