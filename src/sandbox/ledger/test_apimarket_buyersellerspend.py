"""Acceptance suite for the apimarket buyer-side seller spend face
(BigDomain R2158; canon = the explore-queue row seeded in R2149 and
claimed in R2158, criteria AC-BSS1..AC-BSS8 registered in that claim
note BEFORE this code existed - honesty law; the AC-BSS prefix, the
api_buyer_seller_spend name, this suite name, the
ledger-apimarket-buyersellerspend runner label, avg_net_spend as a row
key on this face and dev_paid_share were all git-grep zero-occupancy
anchored against HEAD 2026-10-27, rc=1).

Face under proof: APIMarketFace.api_buyer_seller_spend. The category
axis answers "where did my money go"; inside one category the seller
composition stayed unanswered - how many sellers this resident actually
paid, which one took the largest share, and whether the resident is
bound to a single counterparty. This suite pins the new face:

  - the fifteen-key envelope and the sixteen-key rows, honest empty
    world first;
  - row authority on the PURCHASE side (a seller with stock but zero
    purchases of this buyer stays absent) and a TOTAL order whose rank
    is a position, never a dense rank;
  - trade conservation per row plus envelope sums, and the six cash
    figures identical to api_buyer_category_spend on the same world;
  - net_share = net_spent / total net spend, and None for every row
    when the total is not positive;
  - a refund lowering only the net side (purchase, listing and the
    seller's presence all survive a full refund);
  - the effective-category seam: revise_category moves the seller row's
    category_count in one step and the buyer face agrees;
  - strict buyer isolation, the seven-form account gate, the pure-read
    law and cross-restart byte identity.

Usage: python test_apimarket_buyersellerspend.py
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

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apidev.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

ENVELOPE_KEYS = {
    "buyer_id", "seller_count", "purchase_count", "refund_count",
    "net_purchase_count", "gross_spent", "refunded_tokens",
    "net_spent", "dev_paid", "platform_paid", "dev_paid_net",
    "platform_paid_net", "listing_count", "sellers", "disclaimer"}

ROW_KEYS = {
    "dev_account", "rank", "purchase_count", "refund_count",
    "net_purchase_count", "gross_spent", "refunded_tokens",
    "net_spent", "dev_paid", "platform_paid", "dev_paid_net",
    "platform_paid_net", "listing_count", "category_count",
    "avg_net_spend", "net_share"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


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


def by_seller(env):
    return {row["dev_account"]: row for row in env["sellers"]}


def seed_world(led, dk, am):
    """dana owns two 'data' listings and one uncategorized listing,
    frank one 'tools' listing, gina one 'media' listing that never
    sells. bob buys d1/d2/f1/d3 (dana 18 over three listings, frank 7).
    carol buys d1 then refunds it and buys f1 (dana gross 10 refunded
    10, frank 7). dave buys only g1 (gina 6). erin buys d1 and refunds
    it, so her total net spend is zero."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-BSS-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-BSS-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    dk.issue_key("usr:gina", "gina-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True,
                        category="data")["listing_id"]
    d3 = am.publish_api("usr:dana", "chart-raw", "Raw Chart API",
                        "uncategorized chart payloads", PAYLOAD, 5,
                        False)["listing_id"]
    f1 = am.publish_api("usr:frank", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 7,
                        False, category="tools")["listing_id"]
    g1 = am.publish_api("usr:gina", "media-pack", "Media Pack API",
                        "media pipeline pack", PAYLOAD, 6, False,
                        category="media")["listing_id"]
    for lid, ref in ((d1, "ref-bob-d1"), (d2, "ref-bob-d2"),
                     (f1, "ref-bob-f1"), (d3, "ref-bob-d3")):
        am.purchase_api("usr:bob", lid, ref)
    carol_d1 = am.purchase_api("usr:carol", d1, "ref-carol-d1")
    am.purchase_api("usr:carol", f1, "ref-carol-f1")
    am.purchase_api("usr:dave", g1, "ref-dave-g1")
    erin_d1 = am.purchase_api("usr:erin", d1, "ref-erin-d1")
    am.refund_api("usr:carol", carol_d1["purchase_id"],
                  "listing did not match description")
    am.refund_api("usr:erin", erin_d1["purchase_id"],
                  "changed my mind")
    return d1, d2, d3, f1, g1


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyersellerspend-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d3, f1, g1 = seed_world(led, dk, am)

    # -- AC-BSS1 the contract, honest empty first ----------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-bss-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_seller_spend("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    bob = am.api_buyer_seller_spend("usr:bob")
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in bob["sellers"])
    ok1 = (set(bob.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and row_keys_ok
           and bob["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["buyer_id"] == "usr:nobody"
           and empty["seller_count"] == 0
           and empty["purchase_count"] == 0
           and empty["refund_count"] == 0
           and empty["net_purchase_count"] == 0
           and empty["gross_spent"] == 0
           and empty["refunded_tokens"] == 0
           and empty["net_spent"] == 0
           and empty["dev_paid"] == 0
           and empty["platform_paid"] == 0
           and empty["dev_paid_net"] == 0
           and empty["platform_paid_net"] == 0
           and empty["listing_count"] == 0
           and empty["sellers"] == [])
    record("AC-BSS1", ok1,
           "env_keys=%d exact=%r row_keys=%r rows=%d empty_rows=%d"
           % (len(bob), set(bob.keys()) == ENVELOPE_KEYS,
              row_keys_ok, len(bob["sellers"]),
              len(empty["sellers"])))

    # -- AC-BSS2 purchase-side row authority, order and rank ------------
    carol = am.api_buyer_seller_spend("usr:carol")
    dave = am.api_buyer_seller_spend("usr:dave")
    b_view = by_seller(bob)
    ok2 = ([row["dev_account"] for row in bob["sellers"]]
           == ["usr:dana", "usr:frank"]
           and [row["rank"] for row in bob["sellers"]] == [1, 2]
           and [row["dev_account"] for row in carol["sellers"]]
           == ["usr:frank", "usr:dana"]
           and [row["rank"] for row in carol["sellers"]] == [1, 2]
           and [row["dev_account"] for row in dave["sellers"]]
           == ["usr:gina"]
           and [row["rank"] for row in dave["sellers"]] == [1]
           and dave["seller_count"] == 1
           and "usr:gina" not in b_view
           and "usr:gina" not in by_seller(carol)
           and "usr:frank" not in by_seller(dave)
           and bob["seller_count"] == 2
           and carol["seller_count"] == 2
           and bob["purchase_count"] == 4
           and bob["gross_spent"] == 25
           and carol["gross_spent"] == 17
           and bob["listing_count"] == 4
           and carol["listing_count"] == 2)
    record("AC-BSS2", ok2,
           "bob=%r carol_net=%r dave=%r"
           % ([row["dev_account"] for row in bob["sellers"]],
              [(row["dev_account"], row["net_spent"])
               for row in carol["sellers"]],
              [row["dev_account"] for row in dave["sellers"]]))

    # -- AC-BSS3 conservation, envelope sums, cross-face identity ------
    b_dana = b_view["usr:dana"]
    b_frank = b_view["usr:frank"]
    bcs = am.api_buyer_category_spend("usr:bob")
    c_bcs = am.api_buyer_category_spend("usr:carol")
    d_bcs = am.api_buyer_category_spend("usr:dave")
    ok3 = (all(row["gross_spent"]
               == row["net_spent"] + row["refunded_tokens"]
               for row in bob["sellers"])
           and all(row["net_purchase_count"]
                   == row["purchase_count"] - row["refund_count"]
                   for row in bob["sellers"])
           and all(row["dev_paid"] + row["platform_paid"]
                   == row["gross_spent"]
                   for row in bob["sellers"])
           and all(row["dev_paid_net"] + row["platform_paid_net"]
                   == row["net_spent"]
                   for row in bob["sellers"])
           and bob["seller_count"] == len(bob["sellers"])
           and bob["purchase_count"]
           == sum(row["purchase_count"] for row in bob["sellers"])
           and bob["refund_count"]
           == sum(row["refund_count"] for row in bob["sellers"])
           and bob["net_purchase_count"]
           == sum(row["net_purchase_count"] for row in bob["sellers"])
           and bob["gross_spent"]
           == sum(row["gross_spent"] for row in bob["sellers"])
           and bob["refunded_tokens"]
           == sum(row["refunded_tokens"] for row in bob["sellers"])
           and bob["net_spent"]
           == sum(row["net_spent"] for row in bob["sellers"])
           and bob["dev_paid"]
           == sum(row["dev_paid"] for row in bob["sellers"])
           and bob["platform_paid"]
           == sum(row["platform_paid"] for row in bob["sellers"])
           and bob["dev_paid_net"]
           == sum(row["dev_paid_net"] for row in bob["sellers"])
           and bob["platform_paid_net"]
           == sum(row["platform_paid_net"]
                  for row in bob["sellers"])
           and bob["listing_count"]
           == len(set([d1, d2, d3, f1]))
           and b_dana["purchase_count"] == 3
           and b_dana["gross_spent"] == 18
           and b_frank["gross_spent"] == 7
           and [(bob[k], bcs[k]) for k in
                ("purchase_count", "refund_count",
                 "net_purchase_count", "gross_spent",
                 "refunded_tokens", "net_spent")]
           == [(bcs[k], bcs[k]) for k in
               ("purchase_count", "refund_count",
                "net_purchase_count", "gross_spent",
                "refunded_tokens", "net_spent")]
           and [(carol[k], c_bcs[k]) for k in
                ("purchase_count", "refund_count",
                 "net_purchase_count", "gross_spent",
                 "refunded_tokens", "net_spent")]
           == [(c_bcs[k], c_bcs[k]) for k in
               ("purchase_count", "refund_count",
                "net_purchase_count", "gross_spent",
                "refunded_tokens", "net_spent")]
           and [(dave[k], d_bcs[k]) for k in
                ("purchase_count", "refund_count",
                 "net_purchase_count", "gross_spent",
                 "refunded_tokens", "net_spent")]
           == [(d_bcs[k], d_bcs[k]) for k in
               ("purchase_count", "refund_count",
                "net_purchase_count", "gross_spent",
                "refunded_tokens", "net_spent")]
           and bob["dev_paid_net"] == bcs["dev_paid_net"]
           and bob["platform_paid_net"] == bcs["platform_paid_net"])
    record("AC-BSS3", ok3,
           "dana=%d frank=%d total=%d bcs_total=%d frozen=%r"
           % (b_dana["gross_spent"], b_frank["gross_spent"],
              bob["gross_spent"], bcs["gross_spent"],
              carol["net_spent"] == c_bcs["net_spent"]))

    # -- AC-BSS4 the share law -----------------------------------------
    erin = am.api_buyer_seller_spend("usr:erin")
    total = bob["net_spent"]
    shares = [row["net_share"] for row in bob["sellers"]]
    c_shares = [row["net_share"] for row in carol["sellers"]]
    e_shares = [row["net_share"] for row in erin["sellers"]]
    ok4 = (total == 25
           and shares[0] == float(18) / total
           and shares[1] == float(7) / total
           and abs(sum(shares) - 1.0) < 1e-9
           and carol["net_spent"] == 7
           and c_shares[0] == 1.0
           and c_shares[1] == 0.0
           and erin["net_spent"] == 0
           and erin["seller_count"] == 1
           and erin["sellers"][0]["net_spent"] == 0
           and erin["sellers"][0]["gross_spent"] == 10
           and erin["sellers"][0]["refunded_tokens"] == 10
           and e_shares == [None])
    record("AC-BSS4", ok4,
           "shares=%r sum=%.17g carol=%r erin=%r"
           % (shares, sum(shares), c_shares, e_shares))

    # -- AC-BSS5 the refund law ----------------------------------------
    c_view = by_seller(carol)
    c_dana = c_view["usr:dana"]
    c_frank = c_view["usr:frank"]
    ok5 = (c_dana["purchase_count"] == 1
           and c_dana["refund_count"] == 1
           and c_dana["net_purchase_count"] == 0
           and c_dana["gross_spent"] == 10
           and c_dana["refunded_tokens"] == 10
           and c_dana["net_spent"] == 0
           and c_dana["dev_paid_net"] == 0
           and c_dana["platform_paid_net"] == 0
           and c_dana["dev_paid"] == 7
           and c_dana["listing_count"] == 1
           and c_dana["avg_net_spend"] is None
           and c_frank["purchase_count"] == 1
           and c_frank["refund_count"] == 0
           and c_frank["net_spent"] == 7
           and c_frank["avg_net_spend"] == 7.0
           and carol["net_purchase_count"] == 1
           and carol["net_spent"] == 7
           and carol["refunded_tokens"] == 10
           and b_dana["refund_count"] == 0
           and b_dana["net_spent"] == 18
           and b_dana["avg_net_spend"] == 6.0
           and erin["sellers"][0]["listing_count"] == 1
           and erin["sellers"][0]["avg_net_spend"] is None)
    record("AC-BSS5", ok5,
           "carol_dana net=%d listings=%d avg=%r frank_avg=%r"
           % (c_dana["net_spent"], c_dana["listing_count"],
              c_dana["avg_net_spend"], c_frank["avg_net_spend"]))

    # -- AC-BSS6 the effective-category seam ---------------------------
    before = dumps(bob)
    ok6 = (b_dana["category_count"] == 2
           and b_frank["category_count"] == 1
           and bcs["category_count"] == 3)
    am.revise_category("usr:dana", d3, "data")
    moved = am.api_buyer_seller_spend("usr:bob")
    moved_bcs = am.api_buyer_category_spend("usr:bob")
    moved_view = by_seller(moved)
    ok6 = (ok6
           and moved_view["usr:dana"]["category_count"] == 1
           and moved_view["usr:frank"]["category_count"] == 1
           and moved_bcs["category_count"] == 2
           and moved_bcs["gross_spent"] == bcs["gross_spent"]
           and moved["gross_spent"] == bob["gross_spent"]
           and moved["net_spent"] == bob["net_spent"])
    am.revise_category("usr:dana", d3, None)
    restored = am.api_buyer_seller_spend("usr:bob")
    ok6 = ok6 and dumps(restored) == before
    record("AC-BSS6", ok6,
           "dana_cats=%d->%d bcs_cats=%d->%d roundtrip=%r"
           % (b_dana["category_count"],
              by_seller(moved)["usr:dana"]["category_count"],
              bcs["category_count"],
              moved_bcs["category_count"],
              dumps(restored) == before))

    # -- AC-BSS7 the gate family and the pure-read law -----------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    acct_codes = []
    for bad in (None, "", "u", "usr", 123, [], {"usr:x": 1}):
        try:
            am.api_buyer_seller_spend(bad)
            acct_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            acct_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_buyer_seller_spend("usr:")
    first = dumps(am.api_buyer_seller_spend("usr:carol"))
    second = dumps(am.api_buyer_seller_spend("usr:carol"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (acct_codes == ["E_AM_BAD_ACCOUNT"] * 7
           and prefix["seller_count"] == 0
           and prefix["sellers"] == []
           and prefix["purchase_count"] == 0
           and prefix["net_spent"] == 0
           and first == second
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-BSS7", ok7,
           "acct=%r prefix_rows=%d repeat=%r frozen=%r tx=%r"
           % (acct_codes, prefix["seller_count"], first == second,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-BSS8 cross-restart identity and the wiring ------------------
    final = dumps(am.api_buyer_seller_spend("usr:bob"))
    final_carol = dumps(am.api_buyer_seller_spend("usr:carol"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_bob = dumps(am.api_buyer_seller_spend("usr:bob"))
    second_carol = dumps(am.api_buyer_seller_spend("usr:carol"))
    second_erin = dumps(am.api_buyer_seller_spend("usr:erin"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_bob = dumps(am.api_buyer_seller_spend("usr:bob"))
    third_carol = dumps(am.api_buyer_seller_spend("usr:carol"))
    third_erin = dumps(am.api_buyer_seller_spend("usr:erin"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_buyer_seller_spend("usr:bob")
        am.api_buyer_seller_spend("usr:carol")
        am.api_buyer_seller_spend("usr:erin")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (final == second_bob == third_bob
           and final_carol == second_carol == third_carol
           and second_erin == third_erin
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-buyersellerspend" in runner_text)
    record("AC-BSS8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_bob == third_bob, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-buyersellerspend" in runner_text))

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