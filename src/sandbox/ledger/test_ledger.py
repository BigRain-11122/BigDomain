"""Acceptance suite for the token ledger sandbox (BigDomain P-47-2b).

Asserts the pre-registered criteria AC-L1..AC-L11 from
docs/spec/token-ledger-spec.md section 1. Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Usage: python test_ledger.py
"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L  # noqa: E402
from sec_gate import E_GATE_OFFLINE, GateOfflineError  # noqa: E402  (lobby pipeline product)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_error(fn, *codes):
    try:
        fn()
    except L.LedgerError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def db_query(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def run_reconcile(db_path, cfg_path):
    proc = subprocess.run(
        [sys.executable, os.path.join(BASE, "reconcile.py"), db_path, cfg_path],
        capture_output=True, text=True, encoding="utf-8", timeout=60)
    return proc.returncode, (proc.stdout or "").strip()


def main():
    tmp = tempfile.mkdtemp(prefix="ledger-ac-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    cfg["actions"] = dict(cfg.get("actions") or {})
    cfg["actions"]["login"] = dict(cfg["actions"]["login"], daily_cap=20)  # suite headroom
    cfg["actions"]["boundary_a"] = {"score": 5, "daily_cap": 11, "pool": "pool:reward"}
    cfg["actions"]["boundary_c"] = {"score": 1, "daily_cap": 11, "pool": "pool:reward"}
    cfg_path = os.path.join(tmp, "merged-config.json")
    with open(cfg_path, "w", encoding="utf-8") as handle:
        json.dump(cfg, handle, ensure_ascii=False, indent=2)
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    led.mint_to_pool("pool:reward", 200, "SETTLE-R1", "settlement")
    led.mint_to_pool("pool:share", 100, "SETTLE-R2", "settlement")

    # AC-L11: no census avatar binding = no account, no payout
    ok_create, code_create = expect_error(
        lambda: led.ensure_account("usr:ghost"), L.E_NO_BINDING)
    led.ensure_account("usr:a1", "AV-001")
    ok_payout, code_payout = expect_error(
        lambda: led.grant_reward("usr:neverbound", "login", "EVT-NOBIND"), L.E_NO_BINDING)
    record("AC-L11", ok_create and ok_payout,
           "unbound-create=%s(%s) unbound-payout=%s(%s)"
           % (ok_create, code_create, ok_payout, code_payout))

    # AC-L7: daily cap boundary (-1 below / 0 at / +1 over); cap is per
    # user, per action, per UTC day (config-driven)
    led.ensure_account("usr:b1", "AV-002")
    for i in range(10):
        led.grant_reward("usr:b1", "boundary_c", "EVT-B%02d" % i)  # used 1..10 (below)
    led.grant_reward("usr:b1", "boundary_c", "EVT-B10")           # used 11 (exactly at cap)
    ok_cap, code_cap = expect_error(
        lambda: led.grant_reward("usr:b1", "boundary_c", "EVT-B11"), L.E_TOKEN_CAP)
    bal_b1 = led.balance("usr:b1")["balance"]
    record("AC-L7", ok_cap and bal_b1 == 11,
           "score=1 cap=11: below/at-cap booked, +1-over rejected=%s(%s) balance=%d=cap"
           % (ok_cap, code_cap, bal_b1))

    # AC-L9: AI-adjudicated grants carry the server-set source_ai + bill label;
    # client-supplied source_ai is ignored
    led.record_gate_pass("EVT-AI-1")
    led.grant_reward("usr:a1", "chat_mining", "EVT-AI-1")
    row = db_query(db_path, "SELECT source_ai FROM ledger_tx WHERE ref = 'EVT-AI-1'")[0]
    bill = led.bill("usr:a1")
    ai_items = [i for i in bill["items"] if i.get("ai_label")]
    ok_server_ai = row[0] == 1 and len(ai_items) >= 1
    led.grant_sandbox({"op": "reward", "account_id": "usr:b1", "action": "login",
                       "ref": "EVT-SPOOF-1", "ref_type": "event", "source_ai": True})
    spoof = db_query(db_path, "SELECT source_ai FROM ledger_tx WHERE ref = 'EVT-SPOOF-1'")[0]
    record("AC-L9", ok_server_ai and spoof[0] == 0,
           "ai-action source_ai=%s ai_label=%s; client-spoof stored source_ai=%s"
           % (row[0], [i.get("ai_label") for i in ai_items[:1]], spoof[0]))

    # AC-L8: content rewards need a gate-passed event ref; unwired gate = no serve
    ok_gate_rej, code_gate = expect_error(
        lambda: led.grant_reward("usr:a1", "cocreate", "EVT-RAW-1"), L.E_GATE_REF)
    led.record_gate_pass("EVT-RAW-1")
    led.grant_reward("usr:a1", "cocreate", "EVT-RAW-1")
    ok_after = led.balance("usr:a1")["balance"] >= 20
    offline_cases = []
    for label, mutate in (("empty-wordlist", lambda c: c["gate"].__setitem__("forbidden_words", [])),
                          ("no-gate-section", lambda c: c.__setitem__("gate", None))):
        cfg_off = json.loads(json.dumps(cfg))
        mutate(cfg_off)
        led_off = L.Ledger(os.path.join(tmp, "nogate-%s.db" % label), cfg_off)
        ok_off, detail = False, ""
        try:
            led_off.serve_check()
        except GateOfflineError as exc:
            ok_off, detail = E_GATE_OFFLINE in str(exc), str(exc)
        led_off.close()
        offline_cases.append("%s=%s" % (label, ok_off))
    ok_offline = all(c.endswith("=True") for c in offline_cases)
    record("AC-L8", ok_gate_rej and ok_after and ok_offline,
           "unpassed-ref-rejected=%s(%s) payout-after-pass=%s; serve-refusal %s (%s)"
           % (ok_gate_rej, code_gate, ok_after, offline_cases, detail))

    # AC-L4: same (ref, ref_type) source can never be paid twice
    led.grant_reward("usr:a1", "login", "EVT-L1")
    ok_dup_share, code_dup_share = expect_error(
        lambda: led.grant_reward("usr:a1", "login", "EVT-L1"), L.E_REF_DUPLICATE)
    ok_dup_mint, code_dup_mint = expect_error(
        lambda: led.mint_to_pool("pool:reward", 50, "SETTLE-R1", "settlement"),
        L.E_REF_DUPLICATE)
    record("AC-L4", ok_dup_share and ok_dup_mint,
           "re-grant-same-source=%s(%s) re-mint-same-ref=%s(%s)"
           % (ok_dup_share, code_dup_share, ok_dup_mint, code_dup_mint))

    # AC-L3: identical replay of one tx = rejected, content-addressed id
    led3 = L.Ledger(os.path.join(tmp, "dedup.db"), cfg)
    led3.ensure_account(L.AUTH_ACCOUNT)
    led3.ensure_account("pool:reward")
    entries = [(L.AUTH_ACCOUNT, "debit", 10), ("pool:reward", "credit", 10)]
    args = ("mint", "mint", "SETTLE-D1", "settlement", False, entries)
    kw = {"memo": None, "ts_utc": "2026-09-24T00:00:00Z"}
    led3._write_tx(*args, **kw)
    ok_replay, code_replay = expect_error(lambda: led3._write_tx(*args, **kw),
                                          L.E_TX_DUPLICATE, L.E_REF_DUPLICATE)
    kept = db_query(led3.db_path,
                    "SELECT COUNT(*) FROM ledger_tx WHERE ref = 'SETTLE-D1'")[0][0]
    led3.close()
    record("AC-L3", ok_replay and kept == 1,
           "identical-replay rejected=%s(%s) rows-kept=%d (content-addressed tx_id)"
           % (ok_replay, code_replay, kept))

    # AC-L2: overdraft refused whole-tx, balances untouched; equity stays <= 0
    bal_a1 = led.balance("usr:a1")["balance"]
    ok_over, code_over = expect_error(
        lambda: led.spend("usr:a1", bal_a1 + 7, "ORDER-OVER", "order"),
        L.E_NEGATIVE_BALANCE)
    bal_after = led.balance("usr:a1")["balance"]
    equity = led.balance(L.AUTH_ACCOUNT)["balance"]
    record("AC-L2", ok_over and bal_after == bal_a1 and equity <= 0,
           "overspend rejected=%s(%s) balance-unchanged=%s equity=%d(<=0)"
           % (ok_over, code_over, bal_after == bal_a1, equity))

    # AC-L1: app validation + DB trigger fallback refuse bad books
    ok_app, code_app = expect_error(
        lambda: led._write_tx("mint", "mint", "SETTLE-BAD1", "settlement", False,
                              [(L.AUTH_ACCOUNT, "debit", 10), ("pool:reward", "credit", 9)]),
        L.E_TX_IMBALANCE)
    ok_min, code_min = expect_error(
        lambda: led._write_tx("mint", "mint", "SETTLE-BAD2", "settlement", False,
                              [(L.AUTH_ACCOUNT, "debit", 10)]),
        L.E_TX_MIN_ENTRIES)
    raw = sqlite3.connect(db_path, timeout=10, isolation_level=None)
    db_refused, db_code = False, ""
    try:
        raw.execute("BEGIN IMMEDIATE")
        raw.execute(
            "INSERT INTO ledger_tx (tx_id, type, action, ref, ref_type, source_ai, memo,"
            " ts_utc) VALUES ('rawimbtx1','mint','mint','RAW-IMB-1','settlement',0,NULL,"
            "'2026-09-24T00:00:00Z')")
        raw.execute(
            "INSERT INTO ledger_entries (tx_id, account_id, direction, amount, ts_utc)"
            " VALUES ('rawimbtx1', ?, 'debit', 10, '2026-09-24T00:00:00Z')", (L.AUTH_ACCOUNT,))
        raw.execute(
            "INSERT INTO ledger_entries (tx_id, account_id, direction, amount, ts_utc)"
            " VALUES ('rawimbtx1','pool:reward','credit',9,'2026-09-24T00:00:00Z')")
        raw.execute("UPDATE ledger_tx SET closed = 1 WHERE tx_id = 'rawimbtx1'")
    except sqlite3.IntegrityError as exc:
        db_refused, db_code = L.E_TX_IMBALANCE in str(exc), str(exc)
        raw.execute("ROLLBACK")
    else:
        raw.execute("ROLLBACK")
    raw.close()
    kept_raw = db_query(db_path,
                        "SELECT COUNT(*) FROM ledger_tx WHERE ref = 'RAW-IMB-1'")[0][0]
    record("AC-L1", ok_app and ok_min and db_refused and kept_raw == 0,
           "app-imbalance=%s(%s) min-entries=%s(%s) db-close-refused=%s rolled-back-rows=%d"
           % (ok_app, code_app, ok_min, code_min, db_refused, kept_raw))

    # one clean spend + one adjust so reserve activity and adjust naming exist
    led.spend("usr:a1", 10, "ORDER-1", "order")
    led.adjust([("pool:reward", "debit", 1), ("pool:share", "credit", 1)],
               "MANUAL-001", "sandbox reconciliation drill")

    # AC-L5: reconcile PASS clean, FAIL + exit 2 after a balance tamper
    rc_pass, out_pass = run_reconcile(db_path, cfg_path)
    ok_pass = rc_pass == 0 and "RECONCILE PASS" in out_pass
    sums = db_query(db_path, """
        SELECT COALESCE(SUM(balance), 0),
               COALESCE(SUM(CASE WHEN account_id NOT LIKE 'equity:%'
                                 THEN balance ELSE 0 END), 0),
               COALESCE(SUM(CASE WHEN account_id LIKE 'equity:%'
                                 THEN balance ELSE 0 END), 0)
          FROM ledger_accounts""")[0]
    tam = sqlite3.connect(db_path, isolation_level=None)
    tam.execute("UPDATE ledger_accounts SET balance = balance + 7"
                " WHERE account_id = 'pool:reserve'")
    tam.execute("DELETE FROM gate_events WHERE evt_id = 'EVT-RAW-1'")
    tam.close()
    rc_fail, out_fail = run_reconcile(db_path, cfg_path)
    ok_fail = rc_fail == 2 and "RECONCILE FAIL" in out_fail
    lines_fail = out_fail.splitlines()
    check3_fail = any(l.startswith("3 materialized-vs-derived FAIL") for l in lines_fail)
    record("AC-L5", ok_pass and ok_fail and check3_fail,
           "clean rc=%d; tampered rc=%d check3-fail=%s last=%s"
           % (rc_pass, rc_fail, check3_fail, lines_fail[-1] if lines_fail else ""))

    # AC-L6: zero-sum + mint identity hold clean, break under tamper
    ok_ids = sums[0] == 0 and sums[1] == -sums[2]
    check4_clean = any(l.startswith("4 zero-sum-and-mint-identity PASS")
                       for l in out_pass.splitlines())
    check4_fail = any(l.startswith("4 zero-sum-and-mint-identity FAIL")
                      for l in lines_fail)
    check6_fail = any(l.startswith("6 content-gate-refs FAIL") for l in lines_fail)
    record("AC-L6", ok_ids and check4_clean and check4_fail,
           "sum-all=%d issued=%d equity=%d identity=%s; check4 clean=%s tampered=%s gate-check6-fail=%s"
           % (sums[0], sums[1], sums[2], ok_ids, check4_clean, check4_fail, check6_fail))

    # AC-L10: balance/bill responses carry the persistent non-advisory disclaimer
    bal = led.balance("usr:a1")
    bill10 = led.bill("usr:a1")
    disc = cfg["token"]["disclaimer"]
    ok10 = (bal.get("disclaimer") == disc and bill10.get("disclaimer") == disc
            and bal.get("persistent") is True and bool(disc))
    record("AC-L10", ok10,
           "balance.disclaimer=%s bill.disclaimer=%s persistent=%s len=%d"
           % (bal.get("disclaimer") == disc, bill10.get("disclaimer") == disc,
              bal.get("persistent"), len(disc)))

    led.close()
    fails = [ac for ac, ok in RESULTS if not ok]
    total = len(RESULTS)
    print("SUITE %s (%d/%d criteria pass)" % ("PASS" if not fails else "FAIL",
                                              total - len(fails), total), flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
