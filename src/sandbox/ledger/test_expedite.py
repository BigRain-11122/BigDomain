"""Acceptance suite for the trading-hall expedite-privilege face
(BigDomain R620; canon = BLUEPRINT sec-4 C3/C7 hall value-added
line). Asserts the pre-registered criteria AC-XP1..AC-XP7 from the
R620 backlog row (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Usage: python test_expedite.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L   # noqa: E402  (P-47-2b core)
import expedite as X  # noqa: E402  (R620 extension face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_x_error(fn, *codes):
    try:
        fn()
    except X.ExpediteError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="expedite-ac-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    ef = X.ExpediteFace(led)

    led.mint_to_pool("pool:reserve", 1000, "SETTLE-XP-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.adjust([("pool:reserve", "debit", 300), ("usr:alice", "credit", 300)],
               "manual:fund-a", "suite funding alice")
    led.adjust([("pool:reserve", "debit", 100), ("usr:bob", "credit", 100)],
               "manual:fund-b", "suite funding bob")
    bal = lambda who: led.balance(who)["balance"]  # noqa: E731

    # -- AC-XP1 idempotent purchase: one spend per ref, replay free ---
    b0 = bal("usr:alice")
    p1 = ef.purchase("usr:alice", "demo_queuejump", 50, "order:xp1")
    b1 = bal("usr:alice")
    p2 = ef.purchase("usr:alice", "demo_queuejump", 50, "order:xp1")
    b2 = bal("usr:alice")
    ok1 = (b1 == b0 - 50 and b2 == b1 and p2["idempotent"]
           and p1["credit_id"] == p2["credit_id"] and not p1["idempotent"]
           and bool(p1["spend_tx"]) and p1["spend_tx"] == p2["spend_tx"])
    record("AC-XP1", ok1, "fresh ref charged once (%d->%d->%d); replay of"
          " order:xp1 returned the same credit #%d with spend tx %s and no"
          " second charge" % (b0, b1, b2, p2["credit_id"],
                              p1["spend_tx"][:10]))

    # -- AC-XP2 purchase provenance: all four kinds bind a real spend --
    kinds = (("submit_expedite", "order:xp2a"),
             ("backtest_expedite", "order:xp2b"),
             ("demo_queuejump", "order:xp2c"),
             ("resident_dialogue", "order:xp2d"))
    for kind, ref in kinds:
        ef.purchase("usr:alice", kind, 10, ref)
    b3 = bal("usr:alice")
    conn = sqlite3.connect(db_path)
    creds = conn.execute(
        "SELECT credit_id, kind, bound_spend_tx FROM expedite_credits"
        " WHERE account_id = 'usr:alice' ORDER BY credit_id").fetchall()
    prov = []
    ok2 = (len(creds) == 5 and b3 == b0 - 50 - 40)
    for credit_id, kind, tx in creds:
        head = conn.execute(
            "SELECT type FROM ledger_tx WHERE tx_id = ?", (tx,)).fetchone()
        leg = conn.execute(
            "SELECT direction FROM ledger_entries WHERE tx_id = ?"
            " AND account_id = 'usr:alice'", (tx,)).fetchone()
        good = (head is not None and head[0] == "spend" and leg is not None
                and leg[0] == "debit")
        prov.append("%s->%s" % (kind, head[0] if head else "MISSING"))
        ok2 = ok2 and good
    conn.close()
    record("AC-XP2", ok2, "five credits, four kinds, every row bound to a"
          " real spend (type=spend, debit leg): %s; total charge 90 of 300"
          " (%d left)" % ("; ".join(prov), b3))

    # -- AC-XP3 consumption gate: no credit -> reject, normal ungated --
    b_bob = bal("usr:bob")
    ok_gate, code_gate = expect_x_error(
        lambda: ef.submit("usr:bob", "demo:build-9",
                          expedite_kind="demo_queuejump"),
        X.E_EXP_NO_CREDIT)
    snap0 = ef.queue_snapshot()["jobs"]
    r_norm_bob = ef.submit("usr:bob", "demo:build-9")
    snap1 = ef.queue_snapshot()["jobs"]
    ok3 = (ok_gate and code_gate == X.E_EXP_NO_CREDIT
           and len(snap0) == 0 and not r_norm_bob["expedited"]
           and r_norm_bob["position"] == 1 and bal("usr:bob") == b_bob
           and len(snap1) == 1 and snap1[0]["expedited"] is False)
    record("AC-XP3", ok3, "bob with zero credits: expedited submit rejected"
          " %s leaving zero rows and zero charge (%d==%d); plain submit"
          " ungated, job #%d normal at position 1" %
          (code_gate, b_bob, bal("usr:bob"), r_norm_bob["job_id"]))

    # -- AC-XP4 kind-domain mismatch: reject, nothing consumed -------
    jobs_before = len(ef.queue_snapshot()["jobs"])
    ok_mm, code_mm = expect_x_error(
        lambda: ef.submit("usr:alice", "demo:build-3",
                          expedite_kind="submit_expedite"),
        X.E_EXP_KIND_MISMATCH)
    cr = ef.credits_view("usr:alice")["credits"]
    sub_credits = [c for c in cr if c["kind"] == "submit_expedite"]
    jobs_after = len(ef.queue_snapshot()["jobs"])
    ok4 = (ok_mm and code_mm == X.E_EXP_KIND_MISMATCH
           and len(sub_credits) == 1 and not sub_credits[0]["consumed"]
           and jobs_after == jobs_before)
    record("AC-XP4", ok4, "submit_expedite credit cannot jump a demo:* job"
          " (%s); credit stayed unconsumed and job count unchanged"
          " (%d==%d)" % (code_mm, jobs_before, jobs_after))

    # -- AC-XP5 two-tier ordering: later expedited outranks all normal -
    r_n1 = ef.submit("usr:alice", "idea:tower-mk2")
    r_e1 = ef.submit("usr:alice", "demo:build-3",
                     expedite_kind="demo_queuejump")
    r_n2 = ef.submit("usr:alice", "idea:tower-mk3")
    r_e2 = ef.submit("usr:alice", "demo:build-4",
                     expedite_kind="demo_queuejump")
    snap = ef.queue_snapshot()["jobs"]
    order = [(j["subject"], j["expedited"]) for j in snap]
    want = [("demo:build-3", True), ("demo:build-4", True),
            ("demo:build-9", False), ("idea:tower-mk2", False),
            ("idea:tower-mk3", False)]
    ok5 = (order == want
           and [j["position"] for j in snap] == [1, 2, 3, 4, 5]
           and r_n1["position"] == 2 and r_n2["position"] == 4
           and r_e1["position"] == 1 and r_e2["position"] == 2
           and r_e1["expedited"] and r_e2["expedited"]
           and not r_n1["expedited"] and not r_n2["expedited"])
    record("AC-XP5", ok5, "expedited jobs (seq %d, %d) submitted after normal"
          " jobs still rank 1-2 ahead of all three normal jobs; within-tier"
          " FIFO holds (build-3 before build-4, tower-mk2 before"
          " tower-mk3); submit receipts returned live positions 2/1/4/2"
          % (r_e1["base_seq"], r_e2["base_seq"]))

    # -- AC-XP6 one credit = one job, consumed once, job provenance ----
    ok_used, code_used = expect_x_error(
        lambda: ef.submit("usr:alice", "demo:build-5",
                          expedite_kind="demo_queuejump"),
        X.E_EXP_NO_CREDIT)
    cr6 = ef.credits_view("usr:alice")["credits"]
    demo = [c for c in cr6 if c["kind"] == "demo_queuejump"]
    e1 = [j for j in ef.queue_snapshot()["jobs"]
          if j["subject"] == "demo:build-3"][0]
    e2 = [j for j in ef.queue_snapshot()["jobs"]
          if j["subject"] == "demo:build-4"][0]
    used_ids = sorted(c["credit_id"] for c in demo if c["consumed"])
    job_by_credit = {c["credit_id"]: c["consumed_job"] for c in demo}
    ok6 = (ok_used and len(demo) == 2 and used_ids == sorted(
               [p1["credit_id"], [c for c in cr if c["kind"] ==
                "demo_queuejump" and c["purchase_ref"] == "order:xp2c"][0]
                ["credit_id"]])
           and all(c["consumed"] for c in demo)
           and job_by_credit.get(p1["credit_id"]) == e1["job_id"]
           and all(c["consumed_job"] in (e1["job_id"], e2["job_id"])
                   for c in demo))
    record("AC-XP6", ok6, "third demo jump rejected %s after both credits"
          " were consumed; each consumed credit row binds the exact job it"
          " jumped (credits %s -> jobs %s/%s), one credit = one job"
          % (code_used, used_ids, e1["job_id"], e2["job_id"]))

    # -- AC-XP7 bad args: zero side effects + hard-law source scan -----
    b7 = bal("usr:alice")
    jobs7 = len(ef.queue_snapshot()["jobs"])
    creds7 = len(ef.credits_view("usr:alice")["credits"])
    bad = []
    raised_all = True
    for label, fn, code in (
            ("bad account", lambda: ef.submit("svc:x", "idea:y"),
             X.E_EXP_BAD_ACCOUNT),
            ("empty subject", lambda: ef.submit("usr:alice", "  "),
             X.E_EXP_BAD_SUBJECT),
            ("bad kind", lambda: ef.submit("usr:alice", "idea:y",
                                           expedite_kind="magic"),
             X.E_EXP_BAD_KIND),
            ("zero price", lambda: ef.purchase("usr:alice",
                                              "submit_expedite", 0,
                                              "order:xp7a"),
             X.E_EXP_BAD_AMOUNT),
            ("empty ref", lambda: ef.purchase("usr:alice",
                                             "submit_expedite", 10, "  "),
             X.E_EXP_BAD_REF)):
        ok_one, got = expect_x_error(fn, code)
        if ok_one:
            bad.append("%s=%s" % (label, got))
        else:
            bad.append("%s NOT-RAISED(%s)" % (label, got))
            raised_all = False
    with open(os.path.join(BASE, "expedite.py"), encoding="utf-8") as h:
        src = h.read()
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    owner_rewrite = ("UPDATE expedite_credits SET account_id" in src
                     or "UPDATE expedite_credits SET kind" in src)
    ok7 = (b7 == bal("usr:alice") and jobs7 == len(ef.queue_snapshot()
                                                   ["jobs"])
           and creds7 == len(ef.credits_view("usr:alice")["credits"])
           and raised_all and non_ascii == 0
           and not owner_rewrite)
    record("AC-XP7", ok7, "all bad args rejected (%s); zero side effects"
          " (balance %d==%d, jobs %d, credits %d); module pure ASCII (%d"
          " non-ascii), no ownership-column UPDATE surface" %
          ("; ".join(bad), b7, bal("usr:alice"), jobs7, creds7, non_ascii))

    ef.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
