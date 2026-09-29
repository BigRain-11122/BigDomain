"""Acceptance suite for the city digital collectibles face (BigDomain
R619; canon = BLUEPRINT sec-4 C-end item 6). Asserts the
pre-registered criteria AC-CL1..AC-CL7 from the R619 backlog row
(criteria were registered before this code existed; honesty law).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Usage: python test_collectibles.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L        # noqa: E402  (P-47-2b core)
import collectibles as C  # noqa: E402  (R619 extension face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_cl_error(fn, *codes):
    try:
        fn()
    except C.CollectiblesError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="collectibles-ac-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    cf = C.CollectiblesFace(led)

    led.mint_to_pool("pool:reserve", 1000, "SETTLE-CL-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.adjust([("pool:reserve", "debit", 300), ("usr:alice", "credit", 300)],
               "manual:fund-a", "suite funding alice")
    led.adjust([("pool:reserve", "debit", 100), ("usr:bob", "credit", 100)],
               "manual:fund-b", "suite funding bob")

    # -- AC-CL1 award face: zero token, event provenance, dup reject --
    bal0 = led.balance("usr:alice")["balance"]
    r1 = cf.issue_certificate("usr:alice", "bld:harbor-gate:complete",
                              "cert_harbor_gate")
    bal1 = led.balance("usr:alice")["balance"]
    col1 = cf.collection("usr:alice")
    ok_dup, code_dup = expect_cl_error(
        lambda: cf.issue_certificate("usr:alice", "bld:harbor-gate:complete",
                                     "cert_harbor_gate"), C.E_CL_DUP)
    col1b = cf.collection("usr:alice")
    ok1 = (bal1 == bal0 and r1["kind"] == "certificate"
           and col1["certificates"] == [
               {"item_id": "cert_harbor_gate",
                "event_ref": "bld:harbor-gate:complete"}]
           and ok_dup and len(col1b["certificates"]) == 1)
    record("AC-CL1", ok1, "award moved 0 tokens (%d==%d); certificate bound "
          "to event bld:harbor-gate:complete; duplicate award rejected %s "
          "with rows still %d" % (bal0, bal1, code_dup,
                                  len(col1b["certificates"])))

    # -- AC-CL2 replay right: one spend, permanent, dup pre-check ------
    r2 = cf.buy_replay_right("usr:alice", "chrono:2026-q1-parade", 25,
                             "order:cl2")
    bal2 = led.balance("usr:alice")["balance"]
    col2 = cf.collection("usr:alice")
    ok_dup2, code_dup2 = expect_cl_error(
        lambda: cf.buy_replay_right("usr:alice", "chrono:2026-q1-parade",
                                    25, "order:cl2b"), C.E_CL_DUP)
    bal2b = led.balance("usr:alice")["balance"]
    ok2 = (bal2 == bal0 - 25 and len(col2["replays"]) == 1
           and col2["replays"][0]["event_ref"] == "chrono:2026-q1-parade"
           and bool(col2["replays"][0]["spend_tx"]) and ok_dup2
           and bal2b == bal2)
    record("AC-CL2", ok2, "replay purchase = exactly one spend (%d->%d); "
          "right permanent in collection; duplicate rejected %s with zero "
          "charge (%d==%d)" % (bal0, bal2, code_dup2, bal2, bal2b))

    # -- AC-CL3 limited card: proof gate, numbering, cap, idempotency --
    ok_gate, code_gate = expect_cl_error(
        lambda: cf.claim_card("usr:bob", "card_2026", "resident_card", 3, ""),
        C.E_CL_MEMBERSHIP_REQUIRED)
    colb0 = cf.collection("usr:bob")
    c1 = cf.claim_card("usr:alice", "card_2026", "resident_card", 3, "per-1")
    c2 = cf.claim_card("usr:bob", "card_2026", "resident_card", 3, "per-2")
    c3 = cf.claim_card("usr:alice", "card_2027", "resident_card", 2, "per-3")
    c4 = cf.claim_card("usr:bob", "card_2027", "resident_card", 2, "per-4")
    ok_full, code_full = expect_cl_error(
        lambda: cf.claim_card("usr:carol", "card_2027", "resident_card", 2,
                              "per-5"), C.E_CL_SOLD_OUT)
    st27 = cf.edition_status("card_2027")
    ok_dup3, code_dup3 = expect_cl_error(
        lambda: cf.claim_card("usr:alice", "card_2026", "resident_card", 3,
                              "per-6"), C.E_CL_DUP)
    ok3 = (ok_gate and colb0["cards"] == [] and c1["card_no"] == 1
           and c2["card_no"] == 2 and c1["cap"] == 3 and c2["cap"] == 3
           and c3["card_no"] == 1 and c4["card_no"] == 2 and c3["cap"] == 2
           and ok_full and st27["issued"] == 2 and st27["cap"] == 2
           and ok_dup3)
    record("AC-CL3", ok3, "empty member proof rejected %s with zero issuance; "
          "deterministic numbering 2026: alice=#1 bob=#2 cap locked 3; 2027 "
          "cap 2: alice=#1 bob=#2 then third claimant sold out %s with "
          "counter still %d/%d; per-account per-edition duplicate rejected "
          "%s" % (code_gate, code_full, st27["issued"], st27["cap"],
                  code_dup3))

    # -- AC-CL4 never-changes-hands hard law ----------------------------
    with open(os.path.join(BASE, "collectibles.py"), encoding="utf-8") as h:
        src = h.read()
    banned = ("sell", "refund", "exchange", "withdraw", "transfer", "mint",
              "resell", "auction", "trade")
    hits = [b for b in banned if b in src]
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    mutates_owner = "UPDATE collectibles" in src
    ok4 = (not hits and non_ascii == 0 and not mutates_owner)
    record("AC-CL4", ok4, "banned-verb source scan hits=%s; non-ascii=%d; "
          "owner-row UPDATE present=%s (only counter table may UPDATE)"
          % (hits, non_ascii, mutates_owner))

    # -- AC-CL5 provenance binding --------------------------------------
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT kind, event_ref, bound_spend_tx FROM collectibles"
        " WHERE account_id = 'usr:alice'").fetchall()
    ok5 = len(rows) == 4
    ev5 = []
    for kind, event_ref, tx in rows:
        if kind == "replay":
            head = conn.execute(
                "SELECT type FROM ledger_tx WHERE tx_id = ?", (tx,)).fetchone()
            leg = conn.execute(
                "SELECT direction FROM ledger_entries"
                " WHERE tx_id = ? AND account_id = 'usr:alice'",
                (tx,)).fetchone()
            good = (head is not None and head[0] == "spend"
                    and leg is not None and leg[0] == "debit")
            ev5.append("replay->%s:%s" % (tx[:10],
                                          head[0] if head else "MISSING"))
        else:
            good = (tx == "" and bool(str(event_ref).strip()))
            ev5.append("%s->event:%s" % (kind, event_ref[:18]))
        ok5 = ok5 and good
    conn.close()
    record("AC-CL5", ok5, "purchase row bound to a real spend tx, award and "
          "claim rows carry event provenance with no spend: %s"
          % "; ".join(ev5))

    # -- AC-CL6 cross-account isolation ---------------------------------
    cola = cf.collection("usr:alice")
    colb = cf.collection("usr:bob")
    ok6 = (len(cola["certificates"]) == 1 and len(cola["replays"]) == 1
           and sorted(c["card_no"] for c in cola["cards"]) == [1, 1]
           and len(colb["certificates"]) == 0 and len(colb["replays"]) == 0
           and [c["card_no"] for c in colb["cards"]] == [2, 2])
    record("AC-CL6", ok6, "alice holds cert+replay+cards[#1,#1], bob holds "
          "only his cards[#2,#2]; zero cross-account leak in either view")

    # -- AC-CL7 bad-arg rejects with zero side effects -------------------
    bal_pre = led.balance("usr:bob")["balance"]
    ok_ref, code_ref = expect_cl_error(
        lambda: cf.buy_replay_right("usr:bob", "  ", 10, "order:cl7"),
        C.E_CL_BAD_REF)
    ok_amt, code_amt = expect_cl_error(
        lambda: cf.buy_replay_right("usr:bob", "chrono:x", 0, "order:cl7b"),
        C.E_CL_BAD_AMOUNT)
    ok_ed, code_ed = expect_cl_error(
        lambda: cf.claim_card("usr:bob", "card_bad", "resident_card", 0,
                              "per-7"), C.E_CL_BAD_EDITION)
    ok_out, code_out = expect_cl_error(
        lambda: cf.claim_card("usr:carol", "card_2027", "resident_card", 2,
                              "per-8"), C.E_CL_SOLD_OUT)
    bal_post = led.balance("usr:bob")["balance"]
    colb2 = cf.collection("usr:bob")
    st27b = cf.edition_status("card_2027")
    ok7 = (ok_ref and ok_amt and ok_ed and ok_out and bal_post == bal_pre
           and len(colb2["replays"]) == 0 and len(colb2["cards"]) == 2
           and st27b["issued"] == 2)
    record("AC-CL7", ok7, "empty event ref rejected %s, zero price rejected "
          "%s, zero cap rejected %s, post-sold-out claim rejected %s; all "
          "zero-charge (%d==%d) zero-grant (bob cards still %d) and counter "
          "still %d/%d" % (code_ref, code_amt, code_ed, code_out, bal_pre,
                           bal_post, len(colb2["cards"]), st27b["issued"],
                           st27b["cap"]))

    cf.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
