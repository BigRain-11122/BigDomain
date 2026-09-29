"""Acceptance suite for the city prop/cosmetic inventory face (BigDomain
explore queue #6, round R599). Asserts the pre-registered criteria
AC-PR1..AC-PR7 from the R599 backlog row (criteria were registered
before this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Usage: python test_props.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L  # noqa: E402  (P-47-2b core)
import props as P    # noqa: E402  (R599 extension face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_prop_error(fn, *codes):
    try:
        fn()
    except P.PropError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def expect_ledger_error(fn, *codes):
    try:
        fn()
    except L.LedgerError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="props-ac-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    pf = P.PropsFace(led)

    led.mint_to_pool("pool:reserve", 1000, "SETTLE-PR-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.adjust([("pool:reserve", "debit", 300), ("usr:alice", "credit", 300)],
               "manual:fund-a", "suite funding alice")
    led.adjust([("pool:reserve", "debit", 100), ("usr:bob", "credit", 100)],
               "manual:fund-b", "suite funding bob")

    # -- AC-PR1 counts-vs-tokens isolation ---------------------------------
    bal0 = led.balance("usr:alice")["balance"]
    r1 = pf.buy_prop("usr:alice", "jetpack", "prop", 20, "order:pr1", count=3)
    bal1 = led.balance("usr:alice")["balance"]
    inv1 = pf.inventory("usr:alice")
    ok1 = (bal1 == bal0 - 20 and r1["count_credits"] == 3
           and inv1["props"] == [{"item_id": "jetpack", "count_credits": 3}]
           and bool(r1["spend_tx_id"]))
    c1 = pf.consume_prop("usr:alice", "jetpack", 1)
    bal2 = led.balance("usr:alice")["balance"]
    ok1 = ok1 and c1["count_credits"] == 2 and bal2 == bal1
    record("AC-PR1", ok1, "buy moved tokens by price only (%d->%d), consume "
          "moved 0 (%d->%d); credits 3->2" % (bal0, bal1, bal1, bal2))

    # -- AC-PR2 cosmetic entitlement is permanent --------------------------
    r2 = pf.buy_prop("usr:alice", "hat_gold", "cosmetic", 15, "order:pr2")
    inv2 = pf.inventory("usr:alice")
    bal_pre = led.balance("usr:alice")["balance"]
    ok_dup, code_dup = expect_prop_error(
        lambda: pf.buy_prop("usr:alice", "hat_gold", "cosmetic", 15,
                            "order:pr2b"), P.E_PROP_DUP)
    bal_post = led.balance("usr:alice")["balance"]
    ok_cons, code_cons = expect_prop_error(
        lambda: pf.consume_prop("usr:alice", "hat_gold", 1), P.E_PROP_BAD_KIND)
    ok2 = ("hat_gold" in inv2["cosmetics"] and r2["count_credits"] == 0
           and ok_dup and bal_post == bal_pre and ok_cons)
    record("AC-PR2", ok2, "cosmetic granted; duplicate buy rejected %s with "
          "zero charge (%d==%d); consume path rejected %s"
          % (code_dup, bal_pre, bal_post, code_cons))

    # -- AC-PR3 consumable credit flow -------------------------------------
    pf.consume_prop("usr:alice", "jetpack", 2)  # credits 2 -> 0
    ok_ins, code_ins = expect_prop_error(
        lambda: pf.consume_prop("usr:alice", "jetpack", 1),
        P.E_PROP_INSUFFICIENT)
    r3b = pf.buy_prop("usr:alice", "jetpack", "prop", 20, "order:pr3", count=2)
    inv3 = pf.inventory("usr:alice")
    ok3 = (ok_ins and r3b["count_credits"] == 2
           and inv3["props"] == [{"item_id": "jetpack", "count_credits": 2}])
    record("AC-PR3", ok3, "3->2->0 then over-consume rejected %s; re-purchase "
          "stacks credits back to %d" % (code_ins, r3b["count_credits"]))

    # -- AC-PR4 no reverse-conversion verb ---------------------------------
    with open(os.path.join(BASE, "props.py"), encoding="utf-8") as handle:
        src = handle.read()
    banned = ("sell", "refund", "exchange", "withdraw", "transfer", "mint")
    hits = [b for b in banned if b in src]
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    bal_now = led.balance("usr:alice")["balance"]
    ok4 = (not hits and non_ascii == 0 and bal_now == 300 - 20 - 15 - 20)
    record("AC-PR4", ok4, "source scan banned-hits=%s non-ascii=%d; lifecycle "
          "token delta = purchases only, bal=%d" % (hits, non_ascii, bal_now))

    # -- AC-PR5 purchase provenance binding --------------------------------
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT item_id, bound_spend_tx FROM props_inventory"
        " WHERE account_id = 'usr:alice'").fetchall()
    ok5 = len(rows) == 2
    ev5 = []
    for item_id, tx in rows:
        head = conn.execute(
            "SELECT type FROM ledger_tx WHERE tx_id = ?", (tx,)).fetchone()
        leg = conn.execute(
            "SELECT direction FROM ledger_entries"
            " WHERE tx_id = ? AND account_id = 'usr:alice'", (tx,)).fetchone()
        good = (head is not None and head[0] == "spend"
                and leg is not None and leg[0] == "debit")
        ok5 = ok5 and good
        ev5.append("%s->%s:%s" % (item_id, tx[:10],
                                  head[0] if head else "MISSING"))
    conn.close()
    record("AC-PR5", ok5, "every grant bound to a real spend tx: %s"
          % "; ".join(ev5))

    # -- AC-PR6 cross-account isolation ------------------------------------
    inv_b0 = pf.inventory("usr:bob")
    ok6 = (inv_b0["cosmetics"] == [] and inv_b0["props"] == [])
    pf.buy_prop("usr:bob", "hat_gold", "cosmetic", 15, "order:pr6")
    inv_b1 = pf.inventory("usr:bob")
    inv_a = pf.inventory("usr:alice")
    alice_jet = [p for p in inv_a["props"] if p["item_id"] == "jetpack"]
    ok6 = (ok6 and inv_b1["cosmetics"] == ["hat_gold"]
           and len(inv_a["cosmetics"]) == 1 and alice_jet
           and alice_jet[0]["count_credits"] == 2)
    record("AC-PR6", ok6, "bob started empty, bought his own hat_gold; alice "
          "inventory unaffected (cosmetics=%d, jetpack credits=%d)"
          % (len(inv_a["cosmetics"]),
             alice_jet[0]["count_credits"] if alice_jet else -1))

    # -- AC-PR7 atomicity on insufficient funds / bad kind ------------------
    bal_b0 = led.balance("usr:bob")["balance"]
    ok_neg, code_neg = expect_ledger_error(
        lambda: pf.buy_prop("usr:bob", "spaceship", "cosmetic", 999,
                            "order:pr7"), L.E_NEGATIVE_BALANCE)
    inv_b2 = pf.inventory("usr:bob")
    bal_b1 = led.balance("usr:bob")["balance"]
    ok_kind, code_kind = expect_prop_error(
        lambda: pf.buy_prop("usr:bob", "vehicle_x", "vehicle", 10,
                            "order:pr7b"), P.E_PROP_BAD_KIND)
    ok7 = (ok_neg and bal_b1 == bal_b0
           and "spaceship" not in inv_b2["cosmetics"] and ok_kind)
    record("AC-PR7", ok7, "insufficient funds rejected %s with zero charge "
          "(%d==%d) and zero grant; unknown kind rejected %s"
          % (code_neg, bal_b0, bal_b1, code_kind))

    pf.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
