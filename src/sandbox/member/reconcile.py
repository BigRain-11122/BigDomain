"""Entitlement-domain reconciliation (BigDomain P-47-5b, AC-M14).

Six checks over the member db, with the pay db as the grant-source
oracle and the ledger db as the token-domain cross-schema witness:

  check1  period <-> grant: every period's source_grant_id resolves to
           a real pay_grants row owned by the same census avatar, and
           every tier key is a catalog tier
  check2  credit conservation: zero orphan journal rows; per period
           balance == grants - consumed - expired, never negative;
           refunds never exceed what the period actually consumed
  check3  privilege legality: vouchers only on tiers that carry the
           mapped privilege; journal reason/ref_type discipline holds
  check4  two-domain schema isolation: member tables carry zero
           fiat-named and zero token-named columns (AC-M10/M11), the
           ledger tables carry zero quota-named columns
  check5  audit integrity: every domain change keeps its audit row
           (period open / period expire / every credit event / voucher
           open-use-expire); a deleted audit row is a FAIL
  check6  sweep coverage: zero past-due periods still active

Discipline: one conclusion line first; exit 0 = PASS, exit 2 = FAIL
(same as the ledger eight-check and the pay six-check). Stdlib only.

Usage:
    python reconcile.py [--member-db data/member.db] [--pay-db ...]
                        [--ledger-db ...] [--config config.json]
"""

import argparse
import json
import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
_LOBBY = os.path.normpath(os.path.join(BASE, "..", "lobby"))
_PAY = os.path.normpath(os.path.join(BASE, "..", "pay"))
_LEDGER = os.path.normpath(os.path.join(BASE, "..", "ledger"))
for _p in (_LOBBY, _PAY, _LEDGER, BASE):
    # deterministic order: BASE first - reconcile/member/catalog resolve
    # here, sec_gate to the lobby product (same contract as member.py)
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

from sec_gate import GateOfflineError  # noqa: E402 (lobby product)
import catalog                         # noqa: E402 (this package)
from member import _h, add_days, now_utc  # noqa: E402 (this package)

# banned column-name substrings (lowercase): the fiat/token vocabulary
# must never appear in the entitlement schema, and the quota vocabulary
# must never appear in the token ledger schema (AC-M10/M11 cross law)
FIAT_SUBSTRINGS = ("price", "amount", "cent", "fee", "yuan", "rmb", "cny")
TOKEN_SUBSTRINGS = ("token", "coin")
QUOTA_SUBSTRINGS = ("credit", "quota", "voucher")


def _tables(conn):
    return [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
        " AND name NOT LIKE 'sqlite_%'")]


def _columns(conn, table):
    return [r[1] for r in conn.execute("PRAGMA table_info(%s)" % table)]


def run_checks(member_db, pay_db, ledger_db, config, now=None):
    """Return a list of 'checkN: detail' finding strings; empty = clean."""
    fails = []

    def fail(tag, detail):
        fails.append("%s: %s" % (tag, detail))

    cat = catalog.Catalog.from_config(config)  # validates the catalog too
    ts = str(now or now_utc())
    mconn = sqlite3.connect(member_db)
    pconn = sqlite3.connect(pay_db)
    lconn = sqlite3.connect(ledger_db)
    try:
        periods = mconn.execute(
            "SELECT period_id, census_avatar_id, tier, source_grant_id,"
            " status, end_utc FROM member_periods").fetchall()
        # ---- check1: every period traces to a real grant -------------
        for pid, avatar, tier_key, grant_id, status, end_utc in periods:
            row = pconn.execute(
                "SELECT census_avatar_id FROM pay_grants WHERE grant_id = ?",
                (grant_id,)).fetchone()
            if row is None:
                fail("check1", "period %s: grant %s absent from pay_grants"
                     % (pid, grant_id))
            elif row[0] != avatar:
                fail("check1", "period %s: grant %s owned by %s not %s"
                     % (pid, grant_id, row[0], avatar))
            if str(tier_key) not in cat.tiers:
                fail("check1", "period %s: unknown tier %s" % (pid, tier_key))
        # ---- check2: credit conservation ------------------------------
        orphan = mconn.execute(
            "SELECT COUNT(*) FROM member_credit_events e WHERE NOT EXISTS"
            " (SELECT 1 FROM member_periods p WHERE p.period_id ="
            " e.period_id)").fetchone()[0]
        if orphan:
            fail("check2", "orphan credit journal rows: %d" % orphan)
        for pid, avatar, tier_key, grant_id, status, end_utc in periods:
            row = mconn.execute(
                "SELECT COALESCE(SUM(delta), 0),"
                " COALESCE(SUM(CASE WHEN reason = 'grant' AND"
                " ref_type = 'activation' THEN delta END), 0),"
                " -COALESCE(SUM(CASE WHEN reason = 'consume'"
                " THEN delta END), 0),"
                " -COALESCE(SUM(CASE WHEN reason = 'expire'"
                " THEN delta END), 0),"
                " COALESCE(SUM(CASE WHEN reason = 'grant' AND"
                " ref_type = 'service_refund' THEN delta END), 0)"
                " FROM member_credit_events WHERE period_id = ?",
                (pid,)).fetchone()
            balance, granted, consumed, expired, refunded = \
                (int(v) for v in row)
            # identity: balance == activation grants + refunds
            #           - consumed - expired (refunds are grant-reason
            # rows too; conservation stays machine-checkable)
            if balance != granted + refunded - consumed - expired:
                fail("check2", "period %s identity broken: balance=%d"
                     " grant=%d consume=%d expire=%d"
                     % (pid, balance, granted, consumed, expired))
            if balance < 0:
                fail("check2", "period %s negative balance %d" % (pid, balance))
            if refunded > consumed:
                fail("check2", "period %s refunds %d exceed consumed %d"
                     % (pid, refunded, consumed))
        # ---- check3: privilege legality + journal discipline ----------
        for vid, pid, vtype in mconn.execute(
                "SELECT voucher_id, period_id, voucher_type"
                " FROM member_vouchers"):
            prow = mconn.execute(
                "SELECT tier FROM member_periods WHERE period_id = ?",
                (pid,)).fetchone()
            priv = cat.vouchers.get(str(vtype))
            if priv is None:
                fail("check3", "voucher %s: unknown type %s" % (vid, vtype))
                continue
            if prow is None:
                fail("check3", "voucher %s: orphan period %s" % (vid, pid))
                continue
            tier = cat.tiers.get(str(prow[0]))
            if tier is None or priv not in tier.privileges:
                fail("check3", "voucher %s: privilege %s not granted by"
                     " tier %s" % (vid, priv, prow[0]))
        for eid, reason, ref_type in mconn.execute(
                "SELECT event_id, reason, ref_type FROM"
                " member_credit_events"):
            if reason == "grant" and ref_type not in ("activation",
                                                      "service_refund"):
                fail("check3", "credit event %s: grant ref_type %s"
                     % (eid, ref_type))
            elif reason == "consume" and ref_type not in (None,
                                                          "service_ticket"):
                fail("check3", "credit event %s: consume ref_type %s"
                     % (eid, ref_type))
            elif reason == "expire" and ref_type is not None:
                fail("check3", "credit event %s: expire ref_type %s"
                     % (eid, ref_type))
        # ---- check4: two-domain schema isolation ----------------------
        for table in _tables(mconn):
            for col in _columns(mconn, table):
                low = col.lower()
                hit = next((s for s in FIAT_SUBSTRINGS + TOKEN_SUBSTRINGS
                            if s in low), None)
                if hit is not None:
                    fail("check4", "member %s.%s carries a %s-named column"
                         % (table, col, hit))
        for table in _tables(lconn):
            for col in _columns(lconn, table):
                low = col.lower()
                hit = next((s for s in QUOTA_SUBSTRINGS if s in low), None)
                if hit is not None:
                    fail("check4", "ledger %s.%s carries a quota-named"
                         " column" % (table, col))
        # ---- check5: audit integrity ----------------------------------
        for pid, status in mconn.execute(
                "SELECT period_id, status FROM member_periods"):
            if not mconn.execute(
                    "SELECT 1 FROM member_audit WHERE audit_id = ?",
                    (_h("audit", "period", pid),)).fetchone():
                fail("check5", "period %s: open audit row missing" % pid)
            if status == "expired" and not mconn.execute(
                    "SELECT 1 FROM member_audit WHERE audit_id = ?",
                    (_h("audit", "expire", pid),)).fetchone():
                fail("check5", "period %s: expire audit row missing" % pid)
        for eid, in mconn.execute(
                "SELECT event_id FROM member_credit_events"):
            if not mconn.execute(
                    "SELECT 1 FROM member_audit WHERE audit_id = ?",
                    (_h("audit", "credits", eid),)).fetchone():
                fail("check5", "credit event %s: audit row missing" % eid)
        for vid, status in mconn.execute(
                "SELECT voucher_id, status FROM member_vouchers"):
            if not mconn.execute(
                    "SELECT 1 FROM member_audit WHERE audit_id = ?",
                    (_h("audit", "voucher-open", vid),)).fetchone():
                fail("check5", "voucher %s: open audit row missing" % vid)
            if status == "used" and not mconn.execute(
                    "SELECT 1 FROM member_audit WHERE audit_id = ?",
                    (_h("audit", "voucher-used", vid),)).fetchone():
                fail("check5", "voucher %s: used audit row missing" % vid)
            if status == "expired" and not mconn.execute(
                    "SELECT 1 FROM member_audit WHERE audit_id = ?",
                    (_h("audit", "voucher-expire", vid),)).fetchone():
                fail("check5", "voucher %s: expire audit row missing" % vid)
        # ---- check6: sweep coverage -----------------------------------
        for pid, tier_key, end_utc in mconn.execute(
                "SELECT period_id, tier, end_utc FROM member_periods"
                " WHERE status = 'active'"):
            tier = cat.tiers.get(str(tier_key))
            grace = tier.grace_days if tier is not None else 0
            if add_days(end_utc, grace) <= ts:
                fail("check6", "past-due active period residue: %s" % pid)
    finally:
        mconn.close()
        pconn.close()
        lconn.close()
    return fails


def main():
    parser = argparse.ArgumentParser(
        description="BigDomain member entitlement reconcile (AC-M14 six checks)")
    parser.add_argument("--member-db",
                        default=os.path.join(BASE, "data", "member.db"))
    parser.add_argument("--pay-db",
                        default=os.path.join(_PAY, "data", "pay.db"))
    parser.add_argument("--ledger-db",
                        default=os.path.join(_LEDGER, "data", "ledger.db"))
    parser.add_argument("--config", default=os.path.join(BASE, "config.json"))
    parser.add_argument("--now", default=None,
                        help="override the coverage clock (ISO 8601 Z)")
    args = parser.parse_args()
    try:
        with open(args.config, encoding="utf-8") as handle:
            cfg = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print("FAIL: config unreadable: %s" % exc, flush=True)
        return 2
    try:
        fails = run_checks(args.member_db, args.pay_db, args.ledger_db,
                           cfg, now=args.now)
    except GateOfflineError as exc:
        print("FAIL: catalog refused: %s" % exc, flush=True)
        return 2
    if fails:
        print("FAIL: %d finding(s); first: %s" % (len(fails), fails[0]),
              flush=True)
        for line in fails:
            print("  - " + line)
        return 2
    print("PASS: 6 checks clean (member=%s pay=%s ledger=%s)"
          % (args.member_db, args.pay_db, args.ledger_db), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
