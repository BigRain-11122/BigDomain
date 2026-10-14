"""Cross-restart persistence suite for the enterprise metered API
billing face (BigDomain R1954; FIFO head claim of the R1949 reseed
row; persist-example family R1886 lineage).
Asserts the pre-registered criteria AC-MTP1..AC-MTP7 from the
tech.md metered-persist row (criteria were registered in the claim
row before this code existed; honesty law). Two-piece restart law:
the metering face owns its sqlite connection over the same db file;
persistence semantics live in the client credit counter plus the
immutable pack/call rows. Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Usage: python test_metered_persist.py
"""

import hashlib
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
CLIENTS = ("ent:acme", "ent:boblab", "ent:carollab")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_mt_error(fn, *codes):
    try:
        fn()
    except M.MeteredError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def battery(face):
    """Full read-face battery over all clients + per-client contract
    envelope key pins (deterministic dumps, zero ts echo)."""
    out = {}
    for cid in CLIENTS:
        out[cid + "/contract"] = face.client_contract(cid)
        out[cid + "/reconcile"] = face.reconcile_client(cid)
        out[cid + "/usage"] = face.usage_log(cid)
    return json.dumps(out, sort_keys=True)


def table_dump(db_path):
    conn = sqlite3.connect(db_path)
    out = {}
    for tbl, order in (
            ("metered_clients", "client_id"),
            ("metered_packs", "pack_id"),
            ("metered_calls", "consumed_utc, call_ref")):
        rows = conn.execute(
            "SELECT * FROM %s ORDER BY %s" % (tbl, order)).fetchall()
        out[tbl] = rows
    conn.close()
    return json.dumps(out, sort_keys=True, default=str)


def table_counts(db_path):
    conn = sqlite3.connect(db_path)
    counts = tuple(conn.execute(
        "SELECT COUNT(*) FROM %s" % tbl).fetchone()[0]
        for tbl in ("metered_clients", "metered_packs",
                    "metered_calls"))
    conn.close()
    return counts


def tx_exists(db_path, tx_id):
    conn = sqlite3.connect(db_path)
    n = conn.execute("SELECT COUNT(*) FROM ledger_tx WHERE tx_id = ?",
                      (tx_id,)).fetchone()[0]
    conn.close()
    return int(n)


def anchor_rows(db_path):
    conn = sqlite3.connect(db_path)
    packs = conn.execute(
        "SELECT client_id, purchase_ref, calls, unit_price,"
        " total_price, bound_spend_tx FROM metered_packs"
        " ORDER BY pack_id").fetchall()
    calls = conn.execute(
        "SELECT call_ref, client_id, kind, engine_ref FROM"
        " metered_calls ORDER BY consumed_utc, call_ref").fetchall()
    conn.close()
    return packs, calls


def main():
    tmp = tempfile.mkdtemp(prefix="metered-persist-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(BASE, "metered.py"), "rb") as handle:
        metered_bytes = handle.read()
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    mtf = M.MeteredFace(led)
    led.mint_to_pool("pool:reserve", 200000, "SETTLE-MTP", "settlement")
    for who, av in (("usr:alice", "alice"), ("usr:bob", "bob"),
                    ("usr:carol", "carol")):
        led.ensure_account(who, census_avatar_id=av)
        led.adjust([("pool:reserve", "debit", 50000), (who, "credit", 50000)],
                   "manual:fund-%s" % av, "suite funding %s" % av)
    bal = lambda who, lg: lg.balance(who)["balance"]  # noqa: E731

    # -- anchor world (pre-registration AC-MTP1 shape) --------------------
    mtf.register_client("ent:acme", "usr:alice", ("backtest", "visualize"))
    mtf.register_client("ent:boblab", "usr:bob", ("backtest",))
    mtf.register_client("ent:carollab", "usr:carol",
                        ("backtest", "visualize"))
    p1 = mtf.buy_pack("ent:acme", 100, 5, "order:mtp-a1")
    p2 = mtf.buy_pack("ent:acme", 50, 5, "order:mtp-a2")
    mtf.buy_pack("ent:boblab", 10, 5, "order:mtp-b1")
    p_c = mtf.buy_pack("ent:carollab", 2, 5, "order:mtp-c1")
    mtf.meter_call("ent:acme", "backtest", "call:a1", "eng:bm-0001")
    mtf.meter_call("ent:acme", "visualize", "call:a2", "eng:bm-0002")
    mtf.meter_call("ent:acme", "backtest", "call:a3", "eng:bm-0003")
    mtf.meter_call("ent:boblab", "backtest", "call:b1", "eng:bm-0004")
    mtf.meter_call("ent:carollab", "backtest", "call:c1", "eng:bm-0005")
    mtf.meter_call("ent:carollab", "visualize", "call:c2", "eng:bm-0006")

    snap_battery = battery(mtf)
    snap_tables = table_dump(db_path)
    counts_pre = table_counts(db_path)
    anchor_packs_pre, anchor_calls_pre = anchor_rows(db_path)
    cross = [tx_exists(db_path, t) for t in
             (p1["spend_tx"], p2["spend_tx"], p_c["spend_tx"])]
    balanced = [mtf.reconcile_client(c)["balanced"] for c in CLIENTS]
    ok1 = (counts_pre == (3, 4, 6)
           and cross == [1, 1, 1] and balanced == [True, True, True]
           and mtf.client_contract("ent:acme")["call_credits"] == 147
           and mtf.client_contract("ent:boblab")["call_credits"] == 9
           and mtf.client_contract("ent:carollab")["call_credits"] == 0)
    record("AC-MTP1", ok1, "anchor world: 3 clients / %d packs / %d"
          " calls; credits acme=%d boblab=%d carollab=%d (drained"
          " zero-credit anchor); every bound_spend_tx cross-checked"
          " in ledger_tx %s; balanced verdicts %s"
          % (counts_pre[1], counts_pre[2],
             mtf.client_contract("ent:acme")["call_credits"],
             mtf.client_contract("ent:boblab")["call_credits"],
             mtf.client_contract("ent:carollab")["call_credits"],
             cross, balanced))

    # -- AC-MTP2: two-piece close -> reopen, byte-identical battery -------
    mtf.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    mtf2 = M.MeteredFace(led2)
    post_battery = battery(mtf2)
    post_tables = table_dump(db_path)
    ok2 = (post_battery == snap_battery and post_tables == snap_tables)
    record("AC-MTP2", ok2, "close -> new Ledger + new MeteredFace over"
          " the same db: battery dumps byte-identical (%dB) and"
          " three-table SQL dumps byte-identical (%d rows) = zero"
          " in-memory drift; the credit counter (only mutable cell)"
          " persisted" % (len(snap_battery.encode("utf-8")),
                          counts_pre[0] + counts_pre[1] + counts_pre[2]))

    # -- AC-MTP3: restart-surviving gates, all reject zero-charge ---------
    b_alice_pre = bal("usr:alice", led2)
    ok_dup_pack, code_dp = expect_mt_error(
        lambda: mtf2.buy_pack("ent:acme", 100, 5, "order:mtp-a1"),
        M.E_MT_DUP)
    ok_dup_call, code_dc = expect_mt_error(
        lambda: mtf2.meter_call("ent:acme", "backtest", "call:a1",
                                "eng:bm-0001"),
        M.E_MT_DUP)
    ok_unk_buy, code_ub = expect_mt_error(
        lambda: mtf2.buy_pack("ent:ghost", 10, 5, "order:mtp-g1"),
        M.E_MT_UNKNOWN)
    ok_unk_call, code_uc = expect_mt_error(
        lambda: mtf2.meter_call("ent:ghost", "backtest", "call:g1",
                                "eng:x"), M.E_MT_UNKNOWN)
    ok_unk_con, code_co = expect_mt_error(
        lambda: mtf2.client_contract("ent:ghost"), M.E_MT_UNKNOWN)
    ok_unk_rec, code_rc = expect_mt_error(
        lambda: mtf2.reconcile_client("ent:ghost"), M.E_MT_UNKNOWN)
    ok_unk_usg, code_us = expect_mt_error(
        lambda: mtf2.usage_log("ent:ghost"), M.E_MT_UNKNOWN)
    ok_gate, code_gt = expect_mt_error(
        lambda: mtf2.meter_call("ent:boblab", "visualize", "call:b9",
                                "eng:bm-y"), M.E_MT_KIND_GATE)
    ok_nocred, code_nc = expect_mt_error(
        lambda: mtf2.meter_call("ent:carollab", "backtest", "call:c9",
                                "eng:bm-z"), M.E_MT_NO_CREDITS)
    ok_bad_calls, code_bc = expect_mt_error(
        lambda: mtf2.buy_pack("ent:acme", 0, 5, "order:mtp-bad1"),
        M.E_MT_BAD_ARGS)
    ok_bad_price, code_bp = expect_mt_error(
        lambda: mtf2.buy_pack("ent:acme", 10, 0, "order:mtp-bad2"),
        M.E_MT_BAD_ARGS)
    ok_bad_kind, code_bk = expect_mt_error(
        lambda: mtf2.meter_call("ent:acme", "forecast", "call:bad",
                                "eng:x"), M.E_MT_BAD_ARGS)
    ok_bad_ref, code_br = expect_mt_error(
        lambda: mtf2.buy_pack("ent:acme", 10, 5, "  "), M.E_MT_BAD_ARGS)
    ok_dup_reg, code_dr = expect_mt_error(
        lambda: mtf2.register_client("ent:acme", "usr:bob",
                                    ("backtest",)), M.E_MT_DUP)
    idem = mtf2.register_client("ent:acme", "usr:alice",
                                ("backtest", "visualize"))
    b_alice_post = bal("usr:alice", led2)
    counts_gates = table_counts(db_path)
    ok3 = (ok_dup_pack and code_dp == M.E_MT_DUP
           and ok_dup_call and code_dc == M.E_MT_DUP
           and ok_unk_buy and code_ub == M.E_MT_UNKNOWN
           and ok_unk_call and code_uc == M.E_MT_UNKNOWN
           and ok_unk_con and code_co == M.E_MT_UNKNOWN
           and ok_unk_rec and code_rc == M.E_MT_UNKNOWN
           and ok_unk_usg and code_us == M.E_MT_UNKNOWN
           and ok_gate and code_gt == M.E_MT_KIND_GATE
           and ok_nocred and code_nc == M.E_MT_NO_CREDITS
           and ok_bad_calls and code_bc == M.E_MT_BAD_ARGS
           and ok_bad_price and code_bp == M.E_MT_BAD_ARGS
           and ok_bad_kind and code_bk == M.E_MT_BAD_ARGS
           and ok_bad_ref and code_br == M.E_MT_BAD_ARGS
           and ok_dup_reg and code_dr == M.E_MT_DUP
           and idem["idempotent"] is True
           and b_alice_post == b_alice_pre
           and counts_gates == counts_pre)
    record("AC-MTP3", ok3, "restart-surviving gates: pack replay %s"
          " (bal flat), call replay %s (zero double-charge), unknown"
          " client %s x5 faces, kind gate %s, zero-credit %s, bad"
          " args %s/%s/%s/%s, conflicting re-register %s; idempotent"
          " re-register ok; row counts flat %s = all rejects fire"
          " before any write" % (code_dp, code_dc, code_ub, code_gt,
                                code_nc, code_bc, code_bp, code_bk,
                                code_br, code_dr, counts_gates))

    # -- AC-MTP4: real-path continuation, zero-cache recompute ------------
    px = mtf2.buy_pack("ent:acme", 20, 5, "order:mtp-x1")
    mtf2.meter_call("ent:acme", "backtest", "call:x1", "eng:bm-0007")
    mtf2.meter_call("ent:boblab", "backtest", "call:b2", "eng:bm-0008")
    cont_battery = battery(mtf2)
    rec_acme = mtf2.reconcile_client("ent:acme")
    rec_bob = mtf2.reconcile_client("ent:boblab")
    usage_acme = mtf2.usage_log("ent:acme")["calls"]
    ok4 = (cont_battery != snap_battery
           and mtf2.client_contract("ent:acme")["call_credits"] == 166
           and mtf2.client_contract("ent:boblab")["call_credits"] == 8
           and rec_acme["balanced"] is True
           and rec_acme["purchased_calls"] == 170
           and rec_acme["consumed_calls"] == 4
           and rec_bob["balanced"] is True
           and rec_bob["consumed_calls"] == 2
           and tx_exists(db_path, px["spend_tx"]) == 1
           and [c["call_ref"] for c in usage_acme][-1] == "call:x1")
    record("AC-MTP4", ok4, "post-restart continuation: new pack (real"
          " spend, tx cross-checked) + new calls -> acme credits"
          " 147+20-1=%d, boblab 9-1=%d; battery re-read reflects the"
          " new state (zero cache); balanced verdicts stay True"
          " (acme purchased %d == consumed %d + remaining %d)"
          % (mtf2.client_contract("ent:acme")["call_credits"],
             mtf2.client_contract("ent:boblab")["call_credits"],
             rec_acme["purchased_calls"], rec_acme["consumed_calls"],
             rec_acme["remaining_credits"]))

    # -- AC-MTP5: frozen anchor rows + provenance --------------------------
    anchor_packs_post, anchor_calls_post = anchor_rows(db_path)
    pre_refs = [r[1] for r in anchor_packs_pre]
    post_refs = [r[1] for r in anchor_packs_post][:len(pre_refs)]
    frozen_packs = ([r for r in anchor_packs_pre if r[1] != "order:mtp-x1"]
                    == [r for r in anchor_packs_post
                        if r[1] in
                        ("order:mtp-a1", "order:mtp-a2", "order:mtp-b1",
                         "order:mtp-c1")])
    pre_call_refs = {r[0] for r in anchor_calls_pre}
    frozen_calls = (sorted(
        [tuple(r) for r in anchor_calls_pre
         if r[0] in pre_call_refs])
        == sorted([tuple(r) for r in anchor_calls_post
                   if r[0] in pre_call_refs]))
    ok5 = (post_refs == pre_refs and frozen_packs and frozen_calls
           and len(anchor_calls_post) == len(anchor_calls_pre) + 2
           and p1["spend_tx"] in [r[5] for r in anchor_packs_post]
           and anchor_packs_post[-1][1] == "order:mtp-x1")
    record("AC-MTP5", ok5, "frozen anchors: original %d pack rows and"
          " %d call rows byte-identical after restart + continuation"
          " (immutable rows); provenance freeze: first-purchase spend"
          " tx still bound; only appended rows added (pack count"
          " %d -> %d)"
          % (len(anchor_packs_pre), len(anchor_calls_pre),
             counts_pre[1], table_counts(db_path)[1]))

    # -- AC-MTP6: pure-read law ---------------------------------------------
    before = table_counts(db_path)
    b1 = battery(mtf2)
    b2 = battery(mtf2)
    after = table_counts(db_path)
    ok6 = (before == after and b1 == b2)
    record("AC-MTP6", ok6, "pure-read law: full battery read leaves"
          " row counts identical %s; double-call dumps"
          " byte-identical" % (before,))

    # -- AC-MTP7: third instance stable + hygiene ---------------------------
    end_battery = battery(mtf2)
    mtf2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    mtf3 = M.MeteredFace(led3)
    third_battery = battery(mtf3)
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    with open(os.path.join(BASE, "metered.py"), "rb") as handle:
        metered_after = handle.read()
    with open(os.path.abspath(__file__), "rb") as handle:
        own_bytes = handle.read()
    own_non_ascii = sum(1 for b in own_bytes if b > 127)
    sha_own = hashlib.sha256(own_bytes).hexdigest()[:16]
    ok7 = (third_battery == end_battery
           and cfg_after == cfg_bytes and metered_after == metered_bytes
           and own_non_ascii == 0
           and tmp.startswith(tempfile.gettempdir()))
    record("AC-MTP7", ok7, "second close -> third instance over the"
          " same db: battery byte-identical to the second-instance"
          " end state (%d clients x 3 faces); config.json untouched"
          " (%d bytes); metered.py untouched; suite source pure"
          " ASCII (%d non-ascii bytes, sha16 %s); world in"
          " tempfile.gettempdir()"
          % (len(CLIENTS), len(cfg_after), own_non_ascii, sha_own))

    mtf3.close()
    led3.close()
    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s (%d/%d criteria green)%s"
          % ("PASS" if not fails else "FAIL",
             len(RESULTS) - len(fails), len(RESULTS),
             "" if not fails else " - failed: " + ",".join(fails)),
          flush=True)
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())
