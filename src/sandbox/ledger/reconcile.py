"""Reconcile script for the token ledger sandbox (BigDomain P-47-2b).

Spec section 3: the honesty-law self-check machine core. Eight checks, one
PASS/FAIL line each, every adjust line named, final verdict last. Output
discipline: conclusion lines only (token economy, script output rule).

Exit codes: 0 = PASS, 2 = FAIL. Doubles as the independent re-run entry for
the lab second-window review (ledger P-2026-09-24-53 item 2).

Usage: python reconcile.py <db_path> [config_path]
"""

import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(HERE, "ledger.db")
DEFAULT_CFG = os.path.join(HERE, "config.json")


def check_lines(conn, cfg):
    fails = 0

    def report(idx, name, bad, detail=""):
        nonlocal fails
        if bad:
            fails += 1
        print("%d %s %s%s" % (idx, name, "FAIL" if bad else "PASS",
                              (" n=%d %s" % (bad, detail)) if bad else ""))

    # 1 per-tx double-entry balance: >= 2 entries, debit sum = credit sum (AC-L1)
    bad1 = conn.execute("""
        SELECT COUNT(*) FROM (
          SELECT t.tx_id FROM ledger_tx t
          LEFT JOIN ledger_entries e ON e.tx_id = t.tx_id
          GROUP BY t.tx_id
          HAVING COUNT(e.entry_id) < 2
             OR COALESCE(SUM(CASE WHEN e.direction = 'debit' THEN e.amount
                                 ELSE -e.amount END), 0) <> 0)""").fetchone()[0]
    report(1, "double-entry-balance", bad1)

    # 2 sign law: usr/pool >= 0, equity <= 0 (AC-L2)
    bad2 = conn.execute("""
        SELECT COUNT(*) FROM ledger_accounts
         WHERE (account_id LIKE 'equity:%' AND balance > 0)
            OR (account_id NOT LIKE 'equity:%' AND balance < 0)""").fetchone()[0]
    report(2, "balance-sign-law", bad2)

    # 3 materialized balance vs entries-derived balance, per account (AC-L5)
    bad3 = conn.execute(
        "SELECT COUNT(*) FROM v_derived_balance WHERE materialized <> derived").fetchone()[0]
    report(3, "materialized-vs-derived", bad3)

    # 4 identities: sum of all balances = 0 and issued = -equity (AC-L6)
    row = conn.execute("""
        SELECT COALESCE(SUM(balance), 0),
               COALESCE(SUM(CASE WHEN account_id NOT LIKE 'equity:%'
                                 THEN balance ELSE 0 END), 0),
               COALESCE(SUM(CASE WHEN account_id LIKE 'equity:%'
                                 THEN balance ELSE 0 END), 0)
          FROM ledger_accounts""").fetchone()
    bad4 = 0 if (row[0] == 0 and row[1] == -row[2]) else 1
    report(4, "zero-sum-and-mint-identity", bad4,
           "sum=%d issued=%d equity=%d" % (row[0], row[1], row[2]))

    # 5 ref idempotence: no (ref, ref_type) pair used twice (AC-L4)
    bad5 = conn.execute("""
        SELECT COUNT(*) FROM (
          SELECT ref, ref_type FROM ledger_tx
           GROUP BY ref, ref_type HAVING COUNT(*) > 1)""").fetchone()[0]
    report(5, "ref-idempotence", bad5)

    # 6 content rewards reference gate-passed events only (AC-L8)
    content_actions = [a for a, spec in sorted((cfg.get("actions") or {}).items())
                      if isinstance(spec, dict) and spec.get("content_gate")]
    bad6 = 0
    if content_actions:
        marks = ",".join("?" * len(content_actions))
        bad6 = conn.execute(
            "SELECT COUNT(*) FROM ledger_tx WHERE action IN (%s) AND ref_type = 'event'"
            " AND NOT EXISTS (SELECT 1 FROM gate_events g"
            " WHERE g.evt_id = ledger_tx.ref AND g.gate = 'pass')" % marks,
            content_actions).fetchone()[0]
    report(6, "content-gate-refs", bad6)

    # 7 orphan entries (tx missing or account missing)
    bad7 = conn.execute("""
        SELECT (SELECT COUNT(*) FROM ledger_entries e
                 WHERE NOT EXISTS (SELECT 1 FROM ledger_tx t WHERE t.tx_id = e.tx_id))
             + (SELECT COUNT(*) FROM ledger_entries e
                 WHERE NOT EXISTS (SELECT 1 FROM ledger_accounts a
                                    WHERE a.account_id = e.account_id))""").fetchone()[0]
    report(7, "orphan-entries", bad7)

    # 8 over-cap scan (AC-L7) + adjust lines named (spec section 3)
    bad8 = 0
    for action, spec in sorted((cfg.get("actions") or {}).items()):
        if not isinstance(spec, dict):
            continue
        cap = int(spec.get("daily_cap", 0) or 0)
        if cap <= 0:
            continue
        rows = conn.execute(
            "SELECT e.account_id, substr(t.ts_utc, 1, 10) AS day, SUM(e.amount) AS used"
            " FROM ledger_entries e JOIN ledger_tx t ON t.tx_id = e.tx_id"
            " WHERE e.direction = 'credit' AND t.action = ?"
            " GROUP BY e.account_id, day HAVING used > ?", (action, cap)).fetchall()
        bad8 += len(rows)
        for r in rows:
            print("  over-cap: account=%s action=%s day=%s used=%d cap=%d"
                  % (r[0], action, r[1], r[2], cap))
    for a in conn.execute(
            "SELECT tx_id, ref, memo FROM ledger_tx WHERE type = 'adjust'"
            " ORDER BY ts_utc").fetchall():
        if not (a[2] and str(a[2]).strip()):
            bad8 += 1
        print("  adjust: tx_id=%s ref=%s memo=%s" % (a[0], a[1], a[2]))
    report(8, "cap-scan-and-adjust-lines", bad8)
    return fails


def main(argv):
    db_path = argv[1] if len(argv) > 1 else DEFAULT_DB
    cfg_path = argv[2] if len(argv) > 2 else DEFAULT_CFG
    with open(cfg_path, encoding="utf-8") as handle:
        cfg = json.load(handle)
    conn = sqlite3.connect(db_path)
    try:
        fails = check_lines(conn, cfg)
    finally:
        conn.close()
    if fails:
        print("RECONCILE FAIL (%d/8 checks failed)" % fails)
        return 2
    print("RECONCILE PASS (8/8 checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
