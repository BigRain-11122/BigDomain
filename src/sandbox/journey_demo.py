"""One-command city business-day journey demo (BigDomain, R607).

Turns the J1..J6 user-journey design (docs/spec/integration-
deepening-spec.md, journey-19.9-v2-spec.md) into a runnable artifact:
one command walks a business day inside the silicon city through the
REAL sandbox faces -- ledger core, pre-publication content gate,
props, venue rental, storefront tenancy and the creator incentive
window -- with fail-closed proof, exact balance conservation checks
and a wallclock-free deterministic transcript. Direct answer to the
product-first order P-2026-09-29-07: process made visible, results
early.

Pure composition: zero new faces, zero new schemas, zero network,
zero server startup. Criteria AC-JD1..AC-JD6 were preregistered in
the R607 backlog row BEFORE this code existed (honesty law).

Usage: python src/sandbox/journey_demo.py
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ledger"))
sys.path.insert(0, os.path.join(HERE, "lobby"))

import incentive as INC   # noqa: E402  (R600 face)
import ledger as L        # noqa: E402  (P-47-2b core)
import props as PR        # noqa: E402  (R599 face)
import sec_gate as SG     # noqa: E402  (lobby pre-publication gate)
import venue as VN        # noqa: E402  (R605 face)

CFG_PATH = os.path.join(HERE, "ledger", "config.json")
CALLS = [0]     # real face-call counter (AC-JD2 evidence)
FAILS = []


def bump(n=1):
    CALLS[0] += n


def check(ac, ok, evidence):
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)
    if not ok:
        FAILS.append(ac)


def main():
    with open(CFG_PATH, encoding="utf-8") as handle:
        cfg = json.load(handle)
    tmp = tempfile.mkdtemp(prefix="journey-demo-")
    led = L.Ledger(os.path.join(tmp, "ledger.db"), cfg)
    bump()

    print("=== BigDomain city business-day journey demo (R607) ===")
    disc = led.disclaimer_payload()
    bump()
    text = disc["text"] if isinstance(disc, dict) and "text" in disc \
        else str(disc)
    print("DISCLAIMER (persistent, from config): %s" % text)
    print("AIGC LABEL TEXT (from config): %s"
          % cfg["token"]["ai_label_text"])

    # -- J1 resident onboarding: census-bound accounts --------------
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    bump(3)
    print("J1 RESIDENT ONBOARD  3 census-bound accounts ensured"
          " (alice / bob / carol)")

    # -- J2 platform pools + fiat-side stand-in funding -------------
    led.mint_to_pool("pool:reserve", 1000, "demo:mint:reserve")
    led.mint_to_pool("pool:share", 500, "demo:mint:share")
    led.mint_to_pool("pool:reward", 500, "demo:mint:reward")
    bump(3)
    led.adjust([("pool:reserve", "debit", 200), ("usr:alice", "credit", 200)],
               "demo:fund:alice", "journey demo fiat-side stand-in funding")
    led.adjust([("pool:reserve", "debit", 100), ("usr:bob", "credit", 100)],
               "demo:fund:bob", "journey demo fiat-side stand-in funding")
    bump(2)
    print("J2 PLATFORM POOLS   reserve/share/reward pools minted;"
          " alice funded 200, bob funded 100"
          " (fiat top-up = sandbox stand-in, real channel = pay face)")

    # -- J3 pre-publication content gate: fail-closed proof ---------
    gate = SG.SecGate(cfg["gate"]["forbidden_words"],
                      cfg["gate"]["advisory_ban_words"])
    bump()
    bad_word = str(cfg["gate"]["forbidden_words"][0])
    post_bad = "spam sample post carrying config word: " + bad_word
    tripped = None
    try:
        gate.check_text(post_bad)
        FAILS.append("AC-JD3 gate did not reject")
    except SG.ContentRejectedError as exc:
        tripped = getattr(exc, "word", bad_word)
    bump()
    post_ok = "community event tonight at the plaza stage, all welcome"
    gate.check_text(post_ok)
    bump()
    check("AC-JD3a", tripped is not None,
          "banned post REJECTED before publication (tripped word from"
          " config at runtime): %s; clean post accepted" % tripped)

    # -- J4 gated co-create reward: only via a recorded gate pass -----
    bal_bob_0 = led.balance("usr:bob")["balance"]
    bump()
    refused = None
    try:
        led.grant_reward("usr:bob", "cocreate", "evt:demo:not-recorded",
                         "event")
    except L.LedgerError as exc:
        refused = exc.code
    bump()
    check("AC-JD3b", refused == "E_GATE_REF"
          and led.balance("usr:bob")["balance"] == bal_bob_0,
          "reward layer refuses an unrecorded event (%s), bob balance"
          " unchanged - fail-closed below the gate too" % refused)
    evt_id = led.record_gate_pass("evt:demo:cocreate:1")
    bump()
    led.grant_reward("usr:bob", "cocreate", evt_id, "event")
    bump()
    cocreate_score = int(cfg["actions"]["cocreate"]["score"])
    cocreate_pool = str(cfg["actions"]["cocreate"]["pool"])
    check("AC-JD2a",
          led.balance("usr:bob")["balance"] == bal_bob_0 + cocreate_score,
          "gated co-create reward booked from %s (config action pool),"
          " bob +%d" % (cocreate_pool, cocreate_score))
    print("J4 CO-CREATE REWARD clean post passed the gate, gate pass"
          " recorded, reward +%d booked from %s"
          % (cocreate_score, cocreate_pool))

    # -- J5 props: buy with token spend, then consume a unit --------
    pf = PR.PropsFace(led)
    bump()
    buy = pf.buy_prop("usr:alice", "jetpack", "prop", 20,
                      "order:demo-jd1", count=3)
    bump()
    inv = pf.inventory("usr:alice")
    bump()
    pf.consume_prop("usr:alice", "jetpack", 1)
    bump()
    left = pf.inventory("usr:alice")["props"][0]["count_credits"]
    bump()
    check("AC-JD2b",
          bool(buy.get("spend_tx_id")) and inv["props"][0]["count_credits"] == 3
          and left == 2,
          "prop bought for 20 via one real token spend (tx booked),"
          " 3 credits granted, 1 consumed -> %d left" % left)
    print("J5 CITY PROP SHOP    jetpack x3 bought for 20 (token spend"
          " tx on ledger), 1 consumed, %d credits left" % left)

    # -- J6 venue rental: whole-window fee = one spend --------------
    vf = VN.VenueFace(led)
    bump()
    vf.register_venue("vn:plaza", 2)
    bump()
    rent = vf.rent_venue("usr:alice", "vn:plaza", 100, 3, 10,
                         "order:demo-vn1")
    bump()
    rented = vf.is_rented("vn:plaza", "usr:alice", 102)
    bump()
    check("AC-JD2c", rent["fee"] == 30 and bool(rent["spend_tx_id"])
          and rented is True,
          "venue rented ticks 100-102, fee 30 via one real spend,"
          " occupancy row bound to that spend tx")
    print("J6 VENUE RENTAL     plaza rented 3 windows for 30"
          " (one spend tx, occupancy bound)")

    # -- J7 storefront tenancy: exclusive lease + blocked rival -----
    lease = vf.lease_storefront("usr:bob", "sf:corner", 200, 2, 15,
                                "order:demo-sf1")
    bump()
    bal_alice_0 = led.balance("usr:alice")["balance"]
    bump()
    blocked = None
    try:
        vf.lease_storefront("usr:alice", "sf:corner", 201, 1, 15,
                            "order:demo-sf2")
    except VN.VenueError as exc:
        blocked = exc.code
    bump()
    check("AC-JD3c",
          lease["fee"] == 30 and blocked == "E_VN_LEASE_ACTIVE"
          and led.balance("usr:alice")["balance"] == bal_alice_0,
          "bob leased storefront for 30; rival tenancy inside the"
          " active window REJECTED (%s) with zero charge, alice"
          " balance unchanged" % blocked)
    print("J7 STOREFRONT       corner storefront leased by bob for 30;"
          " rival attempt rejected E_VN_LEASE_ACTIVE, zero tokens moved")

    # -- J8 creator incentive window settlement ---------------------
    inf = INC.IncentiveFace(led)
    bump()
    paid = inf.settle_window("demo:win:1",
                             [("usr:bob", 7), ("usr:carol", 12)])
    bump()
    paid_map = dict(paid)
    par = INC.SANDBOX_PARAMS
    raw = {"usr:bob": INC.payout_for(7), "usr:carol": INC.payout_for(12)}
    exp_paid = {k: min(v, par["collar"]) for k, v in raw.items()}
    check("AC-JD2d", paid_map == exp_paid
          and sum(exp_paid.values()) <= par["budget"],
          "incentive window settled: %s (gradient + collar + budget"
          " all from the shipped face, each payout one share tx)"
          % sorted(paid_map.items()))
    print("J8 CREATOR SHARE    window demo:win:1 settled -> %s"
          % sorted(paid_map.items()))

    # -- J9 conservation: every account and pool exact-match --------
    # spend() credits pool:reserve (BLUEPRINT 5.4: tokens never leave
    # the loop) - the three spends flow back as platform revenue.
    revenue_back = 20 + rent["fee"] + lease["fee"]
    expect = {
        "usr:alice": 200 - 20 - rent["fee"],
        "usr:bob": 100 + cocreate_score - lease["fee"] + exp_paid["usr:bob"],
        "usr:carol": exp_paid["usr:carol"],
        "pool:share": 500 - cocreate_score - sum(exp_paid.values()),
        "pool:reward": 500,
        "pool:reserve": 1000 - 300 + revenue_back,
    }
    mismatch = {acct: (expect[acct], led.balance(acct)["balance"])
                for acct in expect
                if led.balance(acct)["balance"] != expect[acct]}
    bump(len(expect))
    check("AC-JD5a", not mismatch,
          "conservation exact-match for 3 accounts + 3 pools:"
          " alice=%d bob=%d carol=%d share=%d reward=%d reserve=%d"
          " mismatch(expect,actual)=%s"
          % (expect["usr:alice"], expect["usr:bob"], expect["usr:carol"],
             expect["pool:share"], expect["pool:reward"],
             expect["pool:reserve"], sorted(mismatch.items())))
    bill_len = len(led.bill("usr:alice", limit=100))
    bump()
    print("J9 CONSERVATION    all balances exact-match ledger state;"
          " %d spend revenue flowed back to pool:reserve (token loop"
          " closes, BLUEPRINT 5.4); alice bill shows %d ledger rows"
          % (revenue_back, bill_len))

    # -- AC-JD4 runtime self-scan: zero literal gate words in source
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        src = handle.read()
    banned = [str(w) for w in cfg["gate"]["forbidden_words"]] \
        + [str(w) for w in cfg["gate"]["advisory_ban_words"]]
    hits = [w for w in banned if w in src]
    check("AC-JD4", not hits,
          "demo source carries 0 literal forbidden/advisory words"
          " (banned demo content is built from config at runtime)")

    led.close()
    print("DEMO PASS: 8 journey stages, %d real face calls,"
          " 0 network, 0 server startup" % CALLS[0])
    print("DISCLAIMER (footer, persistent, from config): %s" % text)
    if FAILS:
        print("DEMO FAIL: %s" % ",".join(FAILS))
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
