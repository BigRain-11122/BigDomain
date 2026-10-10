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
  7 revoke_ref    every pay_notify_revokes row references a grant
                 history for its (avatar, template) - the face only
                 writes a revoke when live budget exists, so a revoke
                 with zero grants is a dangling reference (R1740
                 follow-up, R1746 wiring)
  8 revoke_dead   revocation dead-account discipline: for each (avatar,
                 template) with revoke history, cutoff = latest revoke
                 ts and live grants must sit strictly after it (the
                 same-second grant-after-revoke lands dead, R1740
                 ruling 2); a dead account (zero live grants) must
                 show zero 'sent' rows after the cutoff (AC-VR3 send
                 side, independent SQL re-derivation - the control
                 plane never imports the writer face)

The revoke checks need the notify db (pay_notify.db). Resolution is
three-state: an explicit fourth positional argument wins; else a
sibling pay_notify.db next to the pay db auto-binds; else the run is
six-check mode with an explicit [skip] line. An explicitly named db
that is missing FAILs both revoke checks (fail-closed: no silent
downgrade). The header's checks=N/N denominator is the number of
checks actually run.

Usage:
    python reconcile.py <pay_db> <pay_config.json> <ledger_db> [notify_db]
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


def _resolve_notify_db(pay_db, notify_db):
    """Three-state notify-db resolution (R1746): explicit argument
    wins; else a sibling pay_notify.db next to the pay db (the face's
    canonical file name) auto-binds; (None, None) means the revoke
    checks cannot run (six-check mode)."""
    if notify_db:
        return notify_db, "explicit"
    sibling = os.path.join(os.path.dirname(os.path.abspath(pay_db)),
                           "pay_notify.db")
    if os.path.exists(sibling):
        return sibling, "auto"
    return None, None


def check_revoke_ref(notify_conn, config):
    """Check 7: revoke dangling references - every pay_notify_revokes
    row must reference an authorization history (the face appends a
    revoke only when live budget exists, which requires grant rows);
    a (avatar, template) pair with a revoke but zero grants is a
    dangling reference (tamper posture)."""
    dangling = notify_conn.execute(
        "SELECT r.revoke_id FROM pay_notify_revokes r WHERE NOT EXISTS ("
        " SELECT 1 FROM pay_notify_grants g"
        " WHERE g.census_avatar_id = r.census_avatar_id"
        " AND g.template_id = r.template_id)").fetchall()
    if dangling:
        return False, "revoke rows without grant history: %s" % (
            [r[0] for r in dangling],)
    total = notify_conn.execute(
        "SELECT COUNT(*) FROM pay_notify_revokes").fetchone()[0]
    return True, "revoke rows reference grant history (%d checked)" % total


def check_revoke_dead(notify_conn, config):
    """Check 8: revocation dead-account discipline - for each (avatar,
    template) with revoke history, cutoff = latest revoke ts and the
    live account = grants strictly after the cutoff (same-second
    grant-after-revoke lands dead, R1740 ruling 2). A dead account
    (zero live grants) must show zero 'sent' rows after the cutoff:
    the face never sends on a revoked subscription (AC-VR3), so a
    post-cutoff sent row on a dead account is the tamper posture this
    check names. Re-granted pairs (live grants after the cutoff,
    AC-VR4) may legally send and are skipped."""
    pairs = notify_conn.execute(
        "SELECT DISTINCT census_avatar_id, template_id"
        " FROM pay_notify_revokes").fetchall()
    problems = []
    for avatar, template in pairs:
        cutoff = notify_conn.execute(
            "SELECT MAX(ts_utc) FROM pay_notify_revokes"
            " WHERE census_avatar_id=? AND template_id=?",
            (avatar, template)).fetchone()[0]
        live = notify_conn.execute(
            "SELECT COUNT(*) FROM pay_notify_grants"
            " WHERE census_avatar_id=? AND template_id=? AND ts_utc>?",
            (avatar, template, cutoff)).fetchone()[0]
        if live:
            continue
        sent = notify_conn.execute(
            "SELECT send_id FROM pay_notify_log"
            " WHERE census_avatar_id=? AND template_id=?"
            " AND status='sent' AND ts_utc>?",
            (avatar, template, cutoff)).fetchall()
        if sent:
            problems.append("dead account %s/%s sent after cutoff: %s"
                            % (avatar, template, [s[0] for s in sent]))
    if problems:
        return False, "; ".join(problems[:5])
    return True, ("revocation dead-account discipline ok"
                  " (%d pairs checked)" % len(pairs))


def run_checks(pay_db, config, ledger_db, notify_db=None):
    """Returns (ok, [(name, ok, detail)], notify_path, notify_mode)."""
    notify_path, notify_mode = _resolve_notify_db(pay_db, notify_db)
    pay_conn = _connect(pay_db)
    ledger_conn = _connect(ledger_db)
    notify_conn = None
    try:
        checks = [
            ("status_scan", lambda: check_status_scan(pay_conn, config)),
            ("receipt_match", lambda: check_receipt_match(pay_conn, config)),
            ("grant_match", lambda: check_grant_match(pay_conn, config)),
            ("amount_match", lambda: check_amount_match(pay_conn, config)),
            ("conversion", lambda: check_conversion(pay_conn, config, ledger_conn)),
            ("fiat_scan", lambda: check_fiat_scan(pay_conn, config, ledger_conn)),
        ]
        if notify_mode == "explicit" and not os.path.exists(notify_path):
            # fail-closed: an explicitly named db that is missing must
            # never silently downgrade to six-check mode
            missing = "notify db not found: %s" % notify_path
            checks += [
                ("revoke_ref", lambda: (False, missing)),
                ("revoke_dead", lambda: (False, missing)),
            ]
        elif notify_path is not None:
            notify_conn = _connect(notify_path)
            checks += [
                ("revoke_ref",
                 lambda: check_revoke_ref(notify_conn, config)),
                ("revoke_dead",
                 lambda: check_revoke_dead(notify_conn, config)),
            ]
        results = []
        for name, fn in checks:
            try:
                ok, detail = fn()
            except sqlite3.Error as exc:
                ok, detail = False, "query error: %s" % exc
            results.append((name, bool(ok), detail))
        return (all(ok for _, ok, _ in results), results,
                notify_path, notify_mode)
    finally:
        pay_conn.close()
        ledger_conn.close()
        if notify_conn is not None:
            notify_conn.close()


def main(argv):
    if len(argv) not in (4, 5):
        print("usage: reconcile.py <pay_db> <pay_config.json> <ledger_db>"
              " [notify_db]", file=sys.stderr)
        return 2
    pay_db, cfg_path, ledger_db = argv[1], argv[2], argv[3]
    notify_db = argv[4] if len(argv) == 5 else None
    try:
        with open(cfg_path, encoding="utf-8") as handle:
            config = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print("reconcile: FAIL config unreadable: %s" % exc)
        return 2
    ok, results, notify_path, notify_mode = run_checks(
        pay_db, config, ledger_db, notify_db)
    verdict = "PASS" if ok else "FAIL"
    print("reconcile: %s checks=%d/%d" % (
        verdict, sum(1 for _, o, _ in results if o), len(results)))
    if notify_mode:
        print("  [mode] notify db: %s (%s)" % (notify_path, notify_mode))
    else:
        print("  [skip] revoke_ref/revoke_dead: no notify db resolved"
              " (six-check mode)")
    for name, o, detail in results:
        print("  [%s] %s: %s" % ("ok" if o else "FAIL", name, detail))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
