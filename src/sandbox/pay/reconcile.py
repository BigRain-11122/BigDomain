"""Reconciliation for the pay sandbox (BigDomain P-47-4b, AC-Y12).

Six checks (docs/spec/payment-integration-spec.md section 3), same
discipline as the ledger reconcile: exit 0 = PASS, exit 2 = FAIL, the
one-line conclusion prints first (token-economy output discipline).
Standalone by design: it re-derives everything from the pay config and
both SQLite files, so it doubles as the independent-recheck entry
(P-53 defense line two, dual-window acceptance paradigm).

Checks:
  1 status_scan   every order status is a legal state-machine value
  2 receipt_match paid/granted orders carry a sig_ok=1 receipt;
                 orphan receipts named
  3 grant_match   granted orders carry exactly one grant row; grant
                 rows on non-granted orders and dangling paid orders
                 (paid without grant = the no-grant window) FAIL
  4 amount_match  every sig_ok=1 receipt amount equals its order amount
                 (price-injection detection)
  5 conversion    every share tx with ref_type='order' references a
                 really-granted order, credits the order's usr account
                 with exactly the price-table token count, and every
                 granted order with tokens>0 carries one
  6 fiat_scan     the ledger schema carries zero fiat-named columns
                 (cross-domain isolation assertion)

Usage:
    python reconcile.py <pay_db> <pay_config.json> <ledger_db>
"""

import json
import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

_LEGAL_STATUS = ("created", "pending", "paid", "granted", "closed")
_FIAT_COLUMNS = {"amount_cent", "price_cent", "fiat_cent", "fiat_amount",
                 "amount_fiat", "cny", "cny_cent", "yuan", "yuan_cent",
                 "amount_yuan", "amount_cny"}
_LEDGER_TABLES = ("ledger_accounts", "gate_events", "ledger_tx", "ledger_entries")


def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def check_status_scan(pay_conn, config):
    rows = pay_conn.execute("SELECT status, COUNT(*) FROM pay_orders"
                            " GROUP BY status").fetchall()
    bad = [(s, n) for s, n in rows if s not in _LEGAL_STATUS]
    counts = dict(rows)
    if bad:
        return False, "illegal status values: %s" % bad
    return True, "orders by status: %s" % json.dumps(counts, sort_keys=True)


def check_receipt_match(pay_conn, config):
    missing = pay_conn.execute(
        "SELECT o.order_id FROM pay_orders o WHERE o.status IN ('paid','granted')"
        " AND NOT EXISTS (SELECT 1 FROM pay_receipts r WHERE r.order_id = o.order_id"
        " AND r.sig_ok = 1)").fetchall()
    orphans = pay_conn.execute(
        "SELECT r.receipt_id FROM pay_receipts r LEFT JOIN pay_orders o"
        " ON o.order_id = r.order_id WHERE o.order_id IS NULL").fetchall()
    if missing or orphans:
        return False, "orders without valid receipt: %s; orphan receipts: %s" % (
            [r[0] for r in missing], [r[0] for r in orphans])
    return True, "receipt coverage ok"


def check_grant_match(pay_conn, config):
    dangling = pay_conn.execute(
        "SELECT order_id FROM pay_orders WHERE status = 'paid'").fetchall()
    ungranted_rows = pay_conn.execute(
        "SELECT g.order_id FROM pay_grants g JOIN pay_orders o"
        " ON o.order_id = g.order_id WHERE o.status <> 'granted'").fetchall()
    missing_grant = pay_conn.execute(
        "SELECT o.order_id FROM pay_orders o WHERE o.status = 'granted'"
        " AND NOT EXISTS (SELECT 1 FROM pay_grants g WHERE g.order_id = o.order_id)"
        ).fetchall()
    if dangling or ungranted_rows or missing_grant:
        return False, ("dangling paid (no-grant window): %s; grants on non-granted:"
                       " %s; granted without grant row: %s"
                       % ([r[0] for r in dangling], [r[0] for r in ungranted_rows],
                          [r[0] for r in missing_grant]))
    return True, "grant coverage ok, no dangling paid"


def check_amount_match(pay_conn, config):
    bad = pay_conn.execute(
        "SELECT r.order_id FROM pay_receipts r JOIN pay_orders o"
        " ON o.order_id = r.order_id WHERE r.sig_ok = 1"
        " AND r.amount_cent <> o.amount_cent").fetchall()
    if bad:
        return False, "receipt/order amount mismatch: %s" % [r[0] for r in bad]
    return True, "amounts consistent (receipt = locked order price)"


def check_conversion(pay_conn, config, ledger_conn):
    products = (config or {}).get("products") or {}
    conv_txs = ledger_conn.execute(
        "SELECT tx_id, ref FROM ledger_tx WHERE ref_type = 'order'"
        " AND type = 'share'").fetchall()
    problems = []
    seen_refs = set()
    for tx_id, ref in conv_txs:
        seen_refs.add(str(ref))
        order = pay_conn.execute(
            "SELECT census_avatar_id, product_id, status FROM pay_orders"
            " WHERE order_id = ?", (str(ref),)).fetchone()
        if order is None or order[2] != "granted":
            problems.append("phantom conversion ref=%s tx=%s" % (ref, tx_id))
            continue
        spec = products.get(str(order[1])) or {}
        want = int(spec.get("share_tokens", 0))
        credits = ledger_conn.execute(
            "SELECT account_id, amount FROM ledger_entries WHERE tx_id = ?"
            " AND direction = 'credit'", (tx_id,)).fetchall()
        want_account = "usr:" + str(order[0])
        if (len(credits) != 1 or credits[0][0] != want_account
                or int(credits[0][1]) != want):
            problems.append("conversion amount/account mismatch ref=%s tx=%s"
                            % (ref, tx_id))
    for row in pay_conn.execute(
            "SELECT order_id, product_id FROM pay_orders WHERE status = 'granted'"
            ).fetchall():
        spec = products.get(str(row[1])) or {}
        if int(spec.get("share_tokens", 0)) > 0 and row[0] not in seen_refs:
            problems.append("granted order missing conversion: %s" % row[0])
    if problems:
        return False, "; ".join(problems[:5])
    return True, "conversion entries consistent (%d checked)" % len(conv_txs)


def check_fiat_scan(pay_conn, config, ledger_conn):
    hits = []
    for table in _LEDGER_TABLES:
        cols = [r[1] for r in ledger_conn.execute(
            "PRAGMA table_info(%s)" % table).fetchall()]
        for col in cols:
            if col.lower() in _FIAT_COLUMNS:
                hits.append("%s.%s" % (table, col))
    if hits:
        return False, "fiat-named columns in ledger: %s" % hits
    return True, "ledger schema carries zero fiat fields"


def run_checks(pay_db, config, ledger_db):
    """Returns (ok, [(name, ok, detail)])."""
    pay_conn = _connect(pay_db)
    ledger_conn = _connect(ledger_db)
    try:
        results = []
        for name, fn in (
                ("status_scan", lambda: check_status_scan(pay_conn, config)),
                ("receipt_match", lambda: check_receipt_match(pay_conn, config)),
                ("grant_match", lambda: check_grant_match(pay_conn, config)),
                ("amount_match", lambda: check_amount_match(pay_conn, config)),
                ("conversion", lambda: check_conversion(pay_conn, config, ledger_conn)),
                ("fiat_scan", lambda: check_fiat_scan(pay_conn, config, ledger_conn))):
            try:
                ok, detail = fn()
            except sqlite3.Error as exc:
                ok, detail = False, "query error: %s" % exc
            results.append((name, bool(ok), detail))
        return all(ok for _, ok, _ in results), results
    finally:
        pay_conn.close()
        ledger_conn.close()


def main(argv):
    if len(argv) != 4:
        print("usage: reconcile.py <pay_db> <pay_config.json> <ledger_db>",
              file=sys.stderr)
        return 2
    pay_db, cfg_path, ledger_db = argv[1], argv[2], argv[3]
    try:
        with open(cfg_path, encoding="utf-8") as handle:
            config = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print("reconcile: FAIL config unreadable: %s" % exc)
        return 2
    ok, results = run_checks(pay_db, config, ledger_db)
    verdict = "PASS" if ok else "FAIL"
    print("reconcile: %s checks=%d/6" % (verdict, sum(1 for _, o, _ in results if o)))
    for name, o, detail in results:
        print("  [%s] %s: %s" % ("ok" if o else "FAIL", name, detail))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
