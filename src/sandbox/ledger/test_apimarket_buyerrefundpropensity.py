"""Acceptance suite for the apimarket buyer refund-propensity face
(BigDomain R2167; canon = the R2166 explore-queue seed row claimed in
this round, criteria AC-RFP1..AC-RFP8 registered in that claim row
BEFORE this suite existed - honesty law; the AC-RFP prefix,
test_apimarket_buyerrefundpropensity, ledger-apimarket-refundpropensity,
market_refund_rate, smoothed_refund_rate and _RFP_SMOOTH were all
git-grep -F zero-occupancy anchored against HEAD 2026-10-27 rc=1, while
the api_buyer_refund_propensity / refund_propensity text occupancy is
the seed row and the reseed script themselves - the code face was
untouched).

Face under proof: APIMarketFace.api_buyer_refund_propensity. The buyer
profile answers lifetime refunded amount and refund count, the refund
register lists rows and the refund exposure is the seller-side
shortfall, so a resident with one refund out of three purchases and one
with one out of thirty read identically, and there is no market
benchmark. This suite pins:

  - the sixteen-key envelope and the honest empty resident first;
  - the denominator law (every purchase counts, refunds are one per
    purchase, so the rate lives in [0,1] and never divides by zero);
  - the amount axis as a separate quantity from the count axis;
  - the market benchmark and its None edges;
  - the low-sample shrinkage: the smoothed rate is the market-centred
    form whose deviation is scaled by exactly n/(n+K), so a one-purchase
    history cannot read as more dangerous than a long one;
  - refund authority (append-only rows), the lifecycle no-ops and the
    cross-face identity with api_buyer_profile;
  - the seven-form account gate, the pure-read law and cross-restart
    byte identity.

Usage: python test_apimarket_buyerrefundpropensity.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402 (P-47-2b core)
import metered as M                   # noqa: E402 (R626 product)
import apidev as D                    # noqa: E402 (R1700 registry)
import apimarket as A                 # noqa: E402 (R1763 face)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

ENVELOPE_KEYS = {
    "buyer_id", "purchase_count", "refund_count",
    "non_refunded_purchase_count", "gross_spent", "refunded_tokens",
    "net_spent", "refund_rate", "refund_amount_rate",
    "market_purchase_count", "market_refund_count",
    "market_refund_rate", "refund_rate_delta", "smoothing_strength",
    "smoothed_refund_rate", "disclaimer"}

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apidev.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions",
          "apimarket_rating_revisions")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def dumps(env):
    return json.dumps(env, sort_keys=True)


def table_digest(conn, table):
    rows = conn.execute(
        "SELECT * FROM " + table + " ORDER BY rowid").fetchall()
    blob = repr(rows).encode("utf-8")
    return len(rows), hashlib.sha256(blob).hexdigest()


def market_digests(am):
    conn = sqlite3.connect(am.db_path)
    out = {t: table_digest(conn, t) for t in TABLES}
    conn.close()
    return out


def ledger_tx_ids(led):
    conn = sqlite3.connect(led.db_path)
    ids = set(str(r[0]) for r in conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall())
    conn.close()
    return ids


def build_stack(db_path, cfg, lobby_cfg):
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    gate = SecGate.from_config(lobby_cfg)
    am = A.APIMarketFace(led, dk, gate, DISCLAIMER)
    return led, metered, dk, gate, am


def close_stack(am, dk, metered, led):
    am.close()
    dk.close()
    metered.close()
    led.close()


def seed_world(led, dk, am):
    """dana owns twenty premium listings (10 tokens) and four cheap ones
    (3 tokens). dave buys all twenty premium and refunds eight; frank
    buys the same twenty and refunds none; bob buys two cheap and two
    premium and refunds one cheap; carol buys one cheap and refunds it;
    erin never buys. Market: 45 purchases and 10 refunds, so the market
    count rate is 10/45 - low enough that the shrinkage ordering between
    a one-purchase history and a twenty-purchase one is observable."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-RFP-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-RFP-S",
                     "settlement")
    for who, amount in (("dave", 400), ("frank", 400), ("bob", 60),
                        ("carol", 20), ("erin", 20)):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    prem = []
    for idx in range(1, 21):
        prem.append(am.publish_api(
            "usr:dana", "prem-%02d" % idx, "Premium API %02d" % idx,
            "premium service payload", PAYLOAD, 10, False,
            category="data")["listing_id"])
    cheap = []
    for idx in range(1, 5):
        cheap.append(am.publish_api(
            "usr:dana", "cheap-%02d" % idx, "Cheap API %02d" % idx,
            "cheap service payload", PAYLOAD, 3, False,
            category="tools")["listing_id"])
    dave_purchases = [am.purchase_api("usr:dave", lid,
                                      "rfp-dave-%02d" % i)
                      for i, lid in enumerate(prem)]
    frank_purchases = [am.purchase_api("usr:frank", lid,
                                       "rfp-frank-%02d" % i)
                       for i, lid in enumerate(prem)]
    for purchase in dave_purchases[:8]:
        am.refund_api("usr:dave", purchase["purchase_id"],
                      "service did not match the listing")
    bob_cheap0 = am.purchase_api("usr:bob", cheap[0], "rfp-bob-c0")
    am.purchase_api("usr:bob", cheap[1], "rfp-bob-c1")
    am.purchase_api("usr:bob", prem[0], "rfp-bob-p0")
    am.purchase_api("usr:bob", prem[1], "rfp-bob-p1")
    am.refund_api("usr:bob", bob_cheap0["purchase_id"],
                  "endpoint retired after purchase")
    carol_cheap = am.purchase_api("usr:carol", cheap[2], "rfp-carol-c2")
    am.refund_api("usr:carol", carol_cheap["purchase_id"],
                  "wrong tier for my use case")
    return {"prem": prem, "cheap": cheap,
            "dave_purchases": dave_purchases,
            "frank_purchases": frank_purchases}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerrefundpropensity-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    ids = seed_world(led, dk, am)

    # -- AC-RFP1 the contract and the honest empty resident ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-rfp-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_refund_propensity("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    bob = am.api_buyer_refund_propensity("usr:bob")
    ok1 = (set(bob.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and bob["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["buyer_id"] == "usr:nobody"
           and empty["purchase_count"] == 0
           and empty["refund_count"] == 0
           and empty["non_refunded_purchase_count"] == 0
           and empty["gross_spent"] == 0
           and empty["refunded_tokens"] == 0
           and empty["net_spent"] == 0
           and empty["refund_rate"] is None
           and empty["refund_amount_rate"] is None
           and empty["market_purchase_count"] == 0
           and empty["market_refund_count"] == 0
           and empty["market_refund_rate"] is None
           and empty["refund_rate_delta"] is None
           and empty["smoothing_strength"] == 10
           and empty["smoothed_refund_rate"] is None)
    record("AC-RFP1", ok1,
           "env_keys=%d exact=%r empty=%r bob_keys=%d"
           % (len(bob), set(bob.keys()) == ENVELOPE_KEYS,
              (empty["purchase_count"], empty["refund_rate"],
               empty["smoothed_refund_rate"]), len(bob)))

    # -- AC-RFP2 the denominator law -----------------------------------
    carol = am.api_buyer_refund_propensity("usr:carol")
    dave = am.api_buyer_refund_propensity("usr:dave")
    frank = am.api_buyer_refund_propensity("usr:frank")
    erin = am.api_buyer_refund_propensity("usr:erin")
    ok2 = True
    for env in (bob, carol, dave, frank, erin):
        purchases = env["purchase_count"]
        refunds = env["refund_count"]
        ok2 = (ok2
               and refunds <= purchases
               and env["non_refunded_purchase_count"]
               == purchases - refunds
               and env["net_spent"]
               == env["gross_spent"] - env["refunded_tokens"]
               and (env["refund_rate"] is None
                    if purchases == 0
                    else env["refund_rate"]
                    == float(refunds) / purchases)
               and (0.0 <= env["refund_rate"] <= 1.0
                    if env["refund_rate"] is not None else True))
    ok2 = (ok2
           and bob["purchase_count"] == 4
           and bob["refund_count"] == 1
           and bob["non_refunded_purchase_count"] == 3
           and bob["gross_spent"] == 26
           and bob["refunded_tokens"] == 3
           and bob["net_spent"] == 23
           and bob["refund_rate"] == 0.25
           and carol["purchase_count"] == 1
           and carol["refund_count"] == 1
           and carol["non_refunded_purchase_count"] == 0
           and carol["refund_rate"] == 1.0
           and carol["net_spent"] == 0
           and dave["purchase_count"] == 20
           and dave["refund_count"] == 8
           and dave["refund_rate"] == 0.4
           and dave["gross_spent"] == 200
           and dave["refunded_tokens"] == 80
           and dave["net_spent"] == 120
           and frank["purchase_count"] == 20
           and frank["refund_count"] == 0
           and frank["refund_rate"] == 0.0
           and erin["purchase_count"] == 0
           and erin["refund_rate"] is None)
    record("AC-RFP2", ok2,
           "bob=%r carol=%r dave=%r frank=%r erin=%r"
           % ((bob["purchase_count"], bob["refund_count"],
               bob["refund_rate"]),
              (carol["purchase_count"], carol["refund_rate"]),
              (dave["purchase_count"], dave["refund_count"],
               dave["refund_rate"]),
              (frank["purchase_count"], frank["refund_rate"]),
              (erin["purchase_count"], erin["refund_rate"])))

    # -- AC-RFP3 the amount axis is a separate quantity ----------------
    ok3 = (abs(bob["refund_amount_rate"] - 3.0 / 26) < 1e-12
           and bob["refund_amount_rate"] != bob["refund_rate"]
           and carol["refund_amount_rate"] == 1.0
           and dave["refund_amount_rate"] == 0.4
           and frank["refund_amount_rate"] == 0.0
           and erin["refund_amount_rate"] is None
           and bob["refund_amount_rate"] < bob["refund_rate"])
    record("AC-RFP3", ok3,
           "bob amount=%r count=%r carol=%r dave=%r frank=%r"
           % (bob["refund_amount_rate"], bob["refund_rate"],
              carol["refund_amount_rate"],
              dave["refund_amount_rate"],
              frank["refund_amount_rate"]))

    # -- AC-RFP4 the market benchmark and its None edges ---------------
    market_rate = 10.0 / 45.0
    ok4 = (bob["market_purchase_count"] == 45
           and bob["market_refund_count"] == 10
           and bob["market_refund_rate"] == market_rate
           and carol["market_refund_rate"] == market_rate
           and dave["market_refund_rate"] == market_rate
           and frank["market_refund_rate"] == market_rate
           and abs(bob["refund_rate_delta"] - (0.25 - market_rate))
           < 1e-12
           and abs(carol["refund_rate_delta"] - (1.0 - market_rate))
           < 1e-12
           and abs(dave["refund_rate_delta"] - (0.4 - market_rate))
           < 1e-12
           and abs(frank["refund_rate_delta"] + market_rate) < 1e-12
           and erin["market_refund_rate"] == market_rate
           and erin["refund_rate_delta"] is None
           and empty["market_refund_rate"] is None
           and empty["refund_rate_delta"] is None)
    record("AC-RFP4", ok4,
           "market=%r deltas=%r erin_delta=%r"
           % (market_rate,
              (bob["refund_rate_delta"], carol["refund_rate_delta"],
               dave["refund_rate_delta"], frank["refund_rate_delta"]),
              erin["refund_rate_delta"]))

    # -- AC-RFP5 the low-sample shrinkage ------------------------------
    k = 10
    ok5 = True
    for env in (bob, carol, dave, frank):
        n = env["purchase_count"]
        expected = ((env["refund_count"] + k * market_rate)
                    / (n + k))
        shrink_lhs = abs(env["smoothed_refund_rate"] - market_rate)
        shrink_rhs = (abs(env["refund_rate"] - market_rate)
                      * n / float(n + k))
        ok5 = (ok5
               and env["smoothing_strength"] == k
               and abs(env["smoothed_refund_rate"] - expected) < 1e-12
               and abs(shrink_lhs - shrink_rhs) < 1e-12
               and 0.0 <= env["smoothed_refund_rate"] <= 1.0)
    ok5 = (ok5
           and erin["smoothed_refund_rate"] is None
           and empty["smoothed_refund_rate"] is None
           and carol["refund_rate"] > dave["refund_rate"]
           and carol["smoothed_refund_rate"] < dave["smoothed_refund_rate"]
           and carol["smoothed_refund_rate"] < carol["refund_rate"]
           and frank["smoothed_refund_rate"] > frank["refund_rate"])
    record("AC-RFP5", ok5,
           "carol raw=%r smooth=%r dave raw=%r smooth=%r frank=%r"
           % (carol["refund_rate"], carol["smoothed_refund_rate"],
              dave["refund_rate"], dave["smoothed_refund_rate"],
              frank["smoothed_refund_rate"]))

    # -- AC-RFP6 refund authority, lifecycle and the profile identity --
    frank_before = am.api_buyer_refund_propensity("usr:frank")
    profile_before = am.api_buyer_profile("usr:frank")
    am.refund_api("usr:frank", ids["frank_purchases"][0]["purchase_id"],
                  "duplicate charge on the first call")
    frank_after = am.api_buyer_refund_propensity("usr:frank")
    profile_after = am.api_buyer_profile("usr:frank")
    dave_before_delist = dumps(am.api_buyer_refund_propensity("usr:dave"))
    am.delist_api("usr:dana", ids["prem"][0])
    dave_after_delist = dumps(am.api_buyer_refund_propensity("usr:dave"))
    am.relist_api("usr:dana", ids["prem"][0])
    dave_after_relist = dumps(am.api_buyer_refund_propensity("usr:dave"))
    ok6 = (frank_before["refund_count"] == 0
           and frank_after["refund_count"] == 1
           and frank_after["refund_rate"] == 0.05
           and frank_after["refunded_tokens"] == 10
           and frank_after["net_spent"] == 190
           and frank_after["purchase_count"] == 20
           and profile_before["refund_count"] == 0
           and profile_after["refund_count"] == 1
           and profile_after["refunded_total"] == 10
           and dave_after_delist == dave_before_delist
           and dave_after_relist == dave_before_delist
           and bob["purchase_count"]
           == am.api_buyer_profile("usr:bob")["purchase_count"]
           and bob["refund_count"]
           == am.api_buyer_profile("usr:bob")["refund_count"]
           and bob["gross_spent"]
           == am.api_buyer_profile("usr:bob")["gross_spent"]
           and bob["refunded_tokens"]
           == am.api_buyer_profile("usr:bob")["refunded_total"]
           and carol["refunded_tokens"]
           == am.api_buyer_profile("usr:carol")["refunded_total"]
           and dave["purchase_count"]
           == am.api_buyer_profile("usr:dave")["purchase_count"])
    record("AC-RFP6", ok6,
           "frank before=%r after=%r profile=%r delist_same=%r"
           " cross_face=%r"
           % ((frank_before["refund_count"],
               frank_before["refund_rate"]),
              (frank_after["refund_count"], frank_after["refund_rate"],
               frank_after["refunded_tokens"]),
              (profile_after["refund_count"],
               profile_after["refunded_total"]),
              dave_after_delist == dave_before_delist
              and dave_after_relist == dave_before_delist,
              bob["gross_spent"]
              == am.api_buyer_profile("usr:bob")["gross_spent"]))

    # -- AC-RFP7 the gate family and the pure-read law -----------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    acct_codes = []
    for bad in (None, "", "  ", 123, [], {"usr:x": 1}, "bob"):
        try:
            am.api_buyer_refund_propensity(bad)
            acct_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            acct_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_buyer_refund_propensity("usr:")
    first = dumps(am.api_buyer_refund_propensity("usr:bob"))
    second = dumps(am.api_buyer_refund_propensity("usr:bob"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (acct_codes == ["E_AM_BAD_ACCOUNT"] * 7
           and prefix["purchase_count"] == 0
           and prefix["refund_rate"] is None
           and prefix["market_refund_rate"] is not None
           and prefix["smoothed_refund_rate"] is None
           and first == second
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-RFP7", ok7,
           "acct=%r prefix=%r repeat=%r frozen=%r tx=%r"
           % (acct_codes, (prefix["purchase_count"],
                           prefix["smoothed_refund_rate"]),
              first == second, digests_before == digests_after,
              tx_before == tx_after))

    # -- AC-RFP8 cross-restart identity and the wiring ------------------
    final_bob = dumps(am.api_buyer_refund_propensity("usr:bob"))
    final_carol = dumps(am.api_buyer_refund_propensity("usr:carol"))
    final_erin = dumps(am.api_buyer_refund_propensity("usr:erin"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_bob = dumps(am.api_buyer_refund_propensity("usr:bob"))
    second_carol = dumps(am.api_buyer_refund_propensity("usr:carol"))
    second_erin = dumps(am.api_buyer_refund_propensity("usr:erin"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_bob = dumps(am.api_buyer_refund_propensity("usr:bob"))
    third_carol = dumps(am.api_buyer_refund_propensity("usr:carol"))
    third_erin = dumps(am.api_buyer_refund_propensity("usr:erin"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_buyer_refund_propensity("usr:bob")
        am.api_buyer_refund_propensity("usr:carol")
        am.api_buyer_refund_propensity("usr:erin")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (final_bob == second_bob == third_bob
           and final_carol == second_carol == third_carol
           and final_erin == second_erin == third_erin
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-refundpropensity" in runner_text)
    record("AC-RFP8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final_bob.encode("utf-8"))
              .hexdigest()[:16],
              final_bob == second_bob == third_bob and
              final_carol == second_carol == third_carol and
              final_erin == second_erin == third_erin,
              tx_b == tx_a, dig_b == dig_a,
              shas_before == shas_after,
              "ledger-apimarket-refundpropensity" in runner_text))

    close_stack(am, dk, metered, led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    verdict = "SUITE PASS %d/%d" % (passed, total)
    if passed != total:
        verdict = "SUITE FAIL %d/%d" % (passed, total)
    print(verdict, flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())