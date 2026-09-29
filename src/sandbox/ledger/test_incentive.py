"""Acceptance suite for the UGC creator incentive gradient allocator
(BigDomain explore queue #3, round R600). Asserts the pre-registered
criteria AC-IG1..AC-IG7 from the R600 backlog row (criteria were
registered before this code existed; honesty law). Each criterion
prints PASS/FAIL with evidence; the process exits non-zero on any
FAIL.

Usage: python test_incentive.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L       # noqa: E402  (P-47-2b core)
import incentive as IN  # noqa: E402  (R600 allocation-layer face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_incentive_error(fn, *codes):
    try:
        fn()
    except IN.IncentiveError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="incentive-ac-")
    cfg_path = os.path.join(BASE, "config.json")
    with open(cfg_path, encoding="utf-8") as handle:
        cfg = json.load(handle)
    with open(cfg_path, "rb") as handle:
        cfg_sha_before = hashlib.sha256(handle.read()).hexdigest()

    db_path = os.path.join(tmp, "ledger.db")
    led = L.Ledger(db_path, cfg)
    face = IN.IncentiveFace(led)

    # ---------- AC-IG1: gradient law (pure function) ----------
    seq = [IN.payout_for(u) for u in (0, 1, 3, 5, 6, 15, 16, 40, 100)]
    ok_zero = seq[0] == 0
    ok_mono = all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1))
    marg = [IN.payout_for(u + 1) - IN.payout_for(u) for u in (2, 6, 20)]
    ok_marg = marg[0] == 10 and marg[1] == 5 and marg[2] == 2
    ok_det = IN.payout_for(37) == IN.payout_for(37) and seq == [
        0, 10, 30, 50, 55, 100, 102, 150, 270]
    record("AC-IG1", ok_zero and ok_mono and ok_marg and ok_det,
           "payout(0)=%d mono=%s marg=%s det=%s seq=%s"
           % (seq[0], ok_mono, marg, ok_det, seq))

    # ---------- settlement windows ----------
    led.mint_to_pool("pool:share", 2000, "SETTLE-IG-A", "settlement")
    for name in ("alice", "bob", "carol", "dave"):
        led.ensure_account("usr:" + name, census_avatar_id=name)
    pool_before = led.balance("pool:share")["balance"]
    bal_before = {name: led.balance("usr:" + name)["balance"]
                  for name in ("alice", "bob", "carol", "dave")}

    # W1: budget-binding window. raw capped = 150 + 130 + 130 = 410
    # > budget 400 -> floor 146/126/126 (sum 398), remainder 2 lands on
    # the first two creators in input order -> 147/127/126, total 400.
    paid_w1 = face.settle_window("W1", [
        ("usr:alice", 100),  # raw 270 -> collar 150
        ("usr:bob", 30),     # raw 50 + 50 + 30 = 130
        ("usr:carol", 30),
    ])
    # W2: collar-binding window (huge units, budget not binding).
    paid_w2 = face.settle_window("W2", [("usr:dave", 10 ** 6)])

    # ---------- AC-IG2: per-creator collar ----------
    ok_w2 = paid_w2 == [("usr:dave", IN.SANDBOX_PARAMS["collar"])]
    ok_w1_cap = all(a <= IN.SANDBOX_PARAMS["collar"] for _, a in paid_w1)
    record("AC-IG2", ok_w2 and ok_w1_cap,
           "dave 1,000,000 units -> %s (collar %d); W1 payouts %s all <= collar"
           % (paid_w2, IN.SANDBOX_PARAMS["collar"], paid_w1))

    # ---------- AC-IG3: window budget cap, exact landing ----------
    total_w1 = sum(a for _, a in paid_w1)
    ok_budget = total_w1 == IN.SANDBOX_PARAMS["budget"]
    ok_exact = paid_w1 == [("usr:alice", 147), ("usr:bob", 127),
                           ("usr:carol", 126)]
    total_w2 = sum(a for _, a in paid_w2)
    ok_w2_le = total_w2 <= IN.SANDBOX_PARAMS["budget"]
    record("AC-IG3", ok_budget and ok_exact and ok_w2_le,
           "W1 raw 410 > budget 400 -> pro-rata lands exactly %d (%s); W2 %d <= budget"
           % (total_w1, paid_w1, total_w2))

    # ---------- AC-IG4: ledger booking join ----------
    total_all = total_w1 + total_w2
    ok_pool = (pool_before
               - led.balance("pool:share")["balance"]) == total_all
    ok_bal = (led.balance("usr:alice")["balance"] == bal_before["alice"] + 147
              and led.balance("usr:bob")["balance"] == bal_before["bob"] + 127
              and led.balance("usr:carol")["balance"] == bal_before["carol"] + 126
              and led.balance("usr:dave")["balance"] == bal_before["dave"] + 150)
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT e.account_id, e.amount, t.ref FROM ledger_entries e"
        " JOIN ledger_tx t ON t.tx_id = e.tx_id"
        " WHERE t.ref LIKE 'incentive:%' AND e.direction = 'credit'"
        " ORDER BY t.ref").fetchall()
    conn.close()
    ok_join = (len(rows) == 4
               and all(r[2] == "incentive:%s:%s" % (r[2].split(":")[1],
                                                     r[0]) for r in rows)
               and sum(r[1] for r in rows) == total_all)
    record("AC-IG4", ok_pool and ok_bal and ok_join,
           "pool:share -%d == total paid %d; balances exact; join rows %d refs %s"
           % (total_all, total_all, len(rows), [r[2] for r in rows]))

    # ---------- AC-IG5: window idempotence ----------
    snap = {name: led.balance("usr:" + name)["balance"] for name in
            ("alice", "bob", "carol", "dave")}
    snap_pool = led.balance("pool:share")["balance"]
    got, code = expect_incentive_error(
        lambda: face.settle_window("W1", [("usr:alice", 100)]),
        IN.E_INC_WINDOW_DUP)
    ok_idem = (got and code == IN.E_INC_WINDOW_DUP
               and all(led.balance("usr:" + n)["balance"] == snap[n]
                       for n in ("alice", "bob", "carol", "dave"))
               and led.balance("pool:share")["balance"] == snap_pool)
    record("AC-IG5", ok_idem,
           "re-settle W1 -> %s; balances unchanged pool=%s usr=%s"
           % (code, led.balance("pool:share")["balance"] == snap_pool, snap))

    # ---------- AC-IG6: red-line source face ----------
    with open(os.path.join(BASE, "incentive.py"), "rb") as handle:
        src_bytes = handle.read()
    src = src_bytes.decode("ascii", errors="strict")
    banned = ("sell", "refund", "exchange", "withdraw", "transfer",
              "mint")
    hits = [w for w in banned if w in src.lower()]
    ok_ascii = all(b < 128 for b in src_bytes)
    ok_norng = "import random" not in src
    record("AC-IG6", not hits and ok_ascii and ok_norng,
           "banned-verb hits=%s ascii=%s no-rng=%s"
           % (hits, ok_ascii, ok_norng))

    # ---------- AC-IG7: adoption face stays approval-only ----------
    with open(cfg_path, "rb") as handle:
        cfg_sha_after = hashlib.sha256(handle.read()).hexdigest()
    ok_cfg = cfg_sha_before == cfg_sha_after
    ok_nokey = ("incentive" not in cfg
                and not any("incentive" in str(k).lower() for k in cfg))
    record("AC-IG7", ok_cfg and ok_nokey,
           "config.json sha unchanged=%s; no incentive param key in shipped config=%s"
           % (ok_cfg, ok_nokey))

    led.close()
    face.close()
    bad = [ac for ac, ok in RESULTS if not ok]
    if bad:
        print("SUITE FAIL (%d/%d): %s" % (len(bad), len(RESULTS), bad),
              flush=True)
        return 1
    print("SUITE PASS (%d/%d)" % (len(RESULTS) - len(bad), len(RESULTS)),
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
