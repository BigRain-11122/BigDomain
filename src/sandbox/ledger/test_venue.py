"""Acceptance suite for the city venue rental + storefront tenancy face
(BigDomain explore queue #2, round R605). Asserts the pre-registered
criteria AC-VN1..AC-VN7 from the R605 backlog row (criteria were
registered before this code existed; honesty law). Each criterion
prints PASS/FAIL with evidence; the process exits non-zero on any
FAIL.

Usage: python test_venue.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L  # noqa: E402  (P-47-2b core)
import venue as V   # noqa: E402  (R605 extension face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_venue_error(fn, *codes):
    try:
        fn()
    except V.VenueError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def expect_ledger_error(fn, *codes):
    try:
        fn()
    except L.LedgerError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="venue-ac-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    vf = V.VenueFace(led)

    led.mint_to_pool("pool:reserve", 1000, "SETTLE-VN-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.adjust([("pool:reserve", "debit", 300), ("usr:alice", "credit", 300)],
               "manual:fund-a", "suite funding alice")
    led.adjust([("pool:reserve", "debit", 100), ("usr:bob", "credit", 100)],
               "manual:fund-b", "suite funding bob")

    # -- AC-VN1 whole-window fee is one spend, the only token touch -----
    vf.register_venue("plaza", 2)
    bal0 = led.balance("usr:alice")["balance"]
    r1 = vf.rent_venue("usr:alice", "plaza", 100, 10, 5, "order:vn1")
    bal1 = led.balance("usr:alice")["balance"]
    ok1 = (r1["fee"] == 50 and r1["start_tick"] == 100
           and r1["end_tick"] == 109 and bal1 == bal0 - 50
           and bool(r1["spend_tx_id"])
           and vf.is_rented("plaza", "usr:alice", 100)
           and vf.is_rented("plaza", "usr:alice", 109))
    record("AC-VN1", ok1, "term 10 x price 5 = fee 50 via one spend "
          "(%d->%d); occupancy active inside [100,109]"
          % (bal0, bal1))

    # -- AC-VN2 capacity gate rejects with zero charge -------------------
    r2a = vf.rent_venue("usr:alice", "plaza", 200, 10, 5, "order:vn2a")
    r2b = vf.rent_venue("usr:bob", "plaza", 205, 10, 5, "order:vn2b")
    bal_a0 = led.balance("usr:alice")["balance"]
    ok_full, code_full = expect_venue_error(
        lambda: vf.rent_venue("usr:alice", "plaza", 206, 10, 5,
                             "order:vn2c"), V.E_VN_FULL)
    bal_a1 = led.balance("usr:alice")["balance"]
    ok2 = (r2a["fee"] == 50 and r2b["fee"] == 50 and ok_full
           and bal_a1 == bal_a0)
    record("AC-VN2", ok2, "capacity 2 filled by [200,209]+[205,214]; third "
          "overlapping rental rejected %s with zero charge (%d==%d)"
          % (code_full, bal_a0, bal_a1))

    # -- AC-VN3 window expiry frees the slot, audit row survives ---------
    expired = vf.is_rented("plaza", "usr:alice", 110)
    r3 = vf.rent_venue("usr:bob", "plaza", 110, 5, 4, "order:vn3")
    hist = vf.occupancy_ledger("plaza")
    alice_rows = [h for h in hist if h["account_id"] == "usr:alice"]
    ok3 = (not expired and r3["fee"] == 20
           and len(alice_rows) == 2
           and all(h["bound_spend_tx"] for h in alice_rows))
    record("AC-VN3", ok3, "is_rented(110)=False after end 109; bob re-rents "
          "the freed slot [110,114] fee 20; alice audit rows=%d with tx "
          "provenance" % len(alice_rows))

    # -- AC-VN4 identical rental is idempotent-rejected ------------------
    bal_b0 = led.balance("usr:bob")["balance"]
    ok_dup, code_dup = expect_venue_error(
        lambda: vf.rent_venue("usr:bob", "plaza", 110, 5, 4, "order:vn3b"),
        V.E_VN_DUP)
    bal_b1 = led.balance("usr:bob")["balance"]
    ok4 = ok_dup and bal_b1 == bal_b0
    record("AC-VN4", ok4, "identical re-rent [110,114] rejected %s with zero "
          "charge (%d==%d)" % (code_dup, bal_b0, bal_b1))

    # -- AC-VN5 storefront exclusivity inside the lease window -----------
    ls1 = vf.lease_storefront("usr:alice", "booth-1", 300, 10, 3,
                              "order:vn5")
    bal_b2 = led.balance("usr:bob")["balance"]
    ok_active, code_active = expect_venue_error(
        lambda: vf.lease_storefront("usr:bob", "booth-1", 305, 5, 3,
                                    "order:vn5b"), V.E_VN_LEASE_ACTIVE)
    bal_b3 = led.balance("usr:bob")["balance"]
    ls2 = vf.lease_storefront("usr:bob", "booth-1", 310, 5, 3, "order:vn5c")
    ok5 = (ls1["fee"] == 30 and ok_active and bal_b3 == bal_b2
           and ls2["fee"] == 15
           and vf.tenant_of("booth-1", 309) == "usr:alice"
           and vf.tenant_of("booth-1", 310) == "usr:bob")
    record("AC-VN5", ok5, "alice leases [300,309] fee 30; bob's overlapping "
          "lease rejected %s zero charge (%d==%d); bob leases the next "
          "window [310,314] fee 15; tenant flip at 309->310"
          % (code_active, bal_b2, bal_b3))

    # -- AC-VN6 early termination moves zero tokens ---------------------
    bal_t0 = led.balance("usr:alice")["balance"]
    conn6 = sqlite3.connect(db_path)
    tx_count0 = conn6.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'").fetchone()[0]
    conn6.close()
    t1 = vf.terminate_lease("booth-1", 305)
    bal_t1 = led.balance("usr:alice")["balance"]
    conn6 = sqlite3.connect(db_path)
    tx_count1 = conn6.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'").fetchone()[0]
    conn6.close()
    ok6 = (t1["terminated_for"] == "usr:alice" and t1["terminated_at"] == 305
           and vf.tenant_of("booth-1", 305) == "usr:alice"
           and vf.tenant_of("booth-1", 306) is None
           and bal_t1 == bal_t0 and tx_count1 == tx_count0)
    record("AC-VN6", ok6, "termination at 305: effective through 305, free "
          "from 306; alice balance unchanged (%d==%d); spend-tx count "
          "unchanged (%d==%d) - no refund face exists in the mechanism"
          % (bal_t0, bal_t1, tx_count0, tx_count1))

    # -- AC-VN7 provenance binding + isolation source law ---------------
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT kind, unit_id, account_id, bound_spend_tx"
        " FROM venue_occupancy").fetchall()
    ok7 = len(rows) > 0
    ev7 = []
    for kind, unit_id, account_id, tx in rows:
        head = conn.execute(
            "SELECT type FROM ledger_tx WHERE tx_id = ?", (tx,)).fetchone()
        leg = conn.execute(
            "SELECT direction FROM ledger_entries"
            " WHERE tx_id = ? AND account_id = ?", (tx, account_id)
            ).fetchone()
        good = (head is not None and head[0] == "spend"
                and leg is not None and leg[0] == "debit")
        ok7 = ok7 and good
        ev7.append("%s/%s@%s" % (kind, unit_id, tx[:10]))
    conn.close()
    with open(os.path.join(BASE, "venue.py"), encoding="utf-8") as handle:
        src = handle.read()
    banned = ("sell", "refund", "exchange", "withdraw", "transfer", "mint")
    hits = [b for b in banned if b in src]
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    ok7 = ok7 and not hits and non_ascii == 0
    record("AC-VN7", ok7, "all %d occupancy rows bind a real spend tx for "
          "their own account: %s; source scan banned-hits=%s non-ascii=%d"
          % (len(rows), "; ".join(ev7[:4]) + (";..." if len(ev7) > 4 else ""),
             hits, non_ascii))

    vf.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
