"""Acceptance suite for the apimarket buyer-side spend concentration
face (BigDomain R2185; canon = the R2178 explore claim row, criteria
AC-BC1..AC-BC8 registered in that row BEFORE this code existed -
honesty law; the AC-BC prefix, api_buyer_concentration,
buyer_herfindahl, test_apimarket_buyerconcentration and
ledger-apimarket-buyerconcentration were all git-grep zero-occupancy
anchored against HEAD 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_buyer_concentration. The buyer
spend face lists sellers and categories with their shares but carries
no index, so "is this resident's spend all on one counterparty, or on
one category" had no face. This suite pins:

  - the twenty-key envelope and eleven-key rows on BOTH axes, honest
    empty first;
  - the purchase-side row authority, the total order
    (-net_spend, -gross_spend, key) with rank 1..n and a
    cumulative_share landing on exactly 1.0 per axis;
  - conservation on both axes and the refund law (a fully refunded
    seller stays on the roll at zero weight);
  - the share law (each axis sums to 1.0 inside 1e-9, None when the
    net total is not positive - never a fake zero), top1 and an
    honest top3;
  - the herfindahl law (monopoly 10000.0, n equal buckets 10000/n)
    computed independently on each axis;
  - the pareto law on integers, including a bucket landing exactly
    on 80%;
  - the gate (eight forms), the bare prefix, strict buyer isolation
    and cross-face identity with api_buyer_seller_spend;
  - the pure-read law, cross-restart byte identity and the wiring.

Usage: python test_apimarket_buyerconcentration.py
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
    "buyer_id", "purchase_count", "refund_count", "seller_count",
    "category_count", "refunded_sellers", "gross_spend",
    "refunded_tokens", "net_spend", "top1_seller_share",
    "top3_seller_share", "seller_herfindahl",
    "pareto_seller_count", "top1_category_share",
    "top3_category_share", "category_herfindahl",
    "pareto_category_count", "disclaimer", "sellers", "categories"}

SELLER_ROW_KEYS = {
    "dev_account", "rank", "purchase_count", "refund_count",
    "net_purchase_count", "gross_spend", "refunded_tokens",
    "net_spend", "listing_count", "share", "cumulative_share"}

CATEGORY_ROW_KEYS = {
    "category", "rank", "purchase_count", "refund_count",
    "net_purchase_count", "gross_spend", "refunded_tokens",
    "net_spend", "listing_count", "share", "cumulative_share"}

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


def fund(led, who):
    led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:" + who, "credit", 400)],
               "manual:fund-" + who, "suite funding " + who)


def seller_row(env, dev):
    for row in env["sellers"]:
        if row["dev_account"] == dev:
            return row
    raise AssertionError("seller %r missing from rows" % (dev,))


def category_row(env, category):
    for row in env["categories"]:
        if row["category"] == category:
            return row
    raise AssertionError("category %r missing from rows" % (category,))


def seed_world(led, dk, am):
    """dana sells bob two units and erin one (fully refunded); frank
    sells bob one big unit and kate one small one; gina sells bob in
    the data category and jade one unit; hana sells jade one unit of
    the SAME weight as gina (the 10000/n law); ivan's only sale to
    nate is fully refunded (the zero-net law). Bob's seller axis lands
    exactly on 80% after two buckets (the pareto boundary) while his
    category axis reaches 80% on the first bucket."""
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-BC-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-BC-S",
                     "settlement")
    for who in ("bob", "erin", "jade", "kate", "nate"):
        fund(led, who)
    for dev in ("dana", "frank", "gina", "hana", "ivan"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    a1 = am.publish_api("usr:dana", "a1", "Alpha API",
                        "alpha payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    a2 = am.publish_api("usr:dana", "a2", "Beta API",
                        "beta payloads", PAYLOAD, 20, False,
                        category="tools")["listing_id"]
    a3 = am.publish_api("usr:dana", "a3", "Gamma API",
                        "gamma payloads", PAYLOAD, 30, False,
                        category="tools")["listing_id"]
    f1 = am.publish_api("usr:frank", "f1", "Frank One API",
                        "frank payloads", PAYLOAD, 50, False,
                        category="tools")["listing_id"]
    f2 = am.publish_api("usr:frank", "f2", "Frank Two API",
                        "frank payloads two", PAYLOAD, 8, False,
                        category="tools")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina One API",
                        "gina payloads", PAYLOAD, 20, False,
                        category="data")["listing_id"]
    g2 = am.publish_api("usr:gina", "g2", "Gina Two API",
                        "gina payloads two", PAYLOAD, 5, False,
                        category="data")["listing_id"]
    h1 = am.publish_api("usr:hana", "h1", "Hana One API",
                        "hana payloads", PAYLOAD, 5, False,
                        category="data")["listing_id"]
    i1 = am.publish_api("usr:ivan", "i1", "Ivan One API",
                        "ivan payloads", PAYLOAD, 9, False,
                        category="tools")["listing_id"]

    am.purchase_api("usr:bob", a1, "ref-bob-a1")
    am.purchase_api("usr:bob", a2, "ref-bob-a2")
    am.purchase_api("usr:bob", f1, "ref-bob-f1")
    am.purchase_api("usr:bob", g1, "ref-bob-g1")
    p_erin = am.purchase_api("usr:erin", a3, "ref-erin-a3")
    am.purchase_api("usr:jade", g2, "ref-jade-g2")
    am.purchase_api("usr:jade", h1, "ref-jade-h1")
    am.purchase_api("usr:kate", f2, "ref-kate-f2")
    p_nate = am.purchase_api("usr:nate", i1, "ref-nate-i1")

    am.refund_api("usr:erin", p_erin["purchase_id"],
                  "listing did not match description")
    am.refund_api("usr:nate", p_nate["purchase_id"],
                  "listing did not match description")


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerconcentration-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    seed_world(led, dk, am)

    # -- AC-BC1 the contract, honest empty first ----------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-bc-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_concentration("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    bob = am.api_buyer_concentration("usr:bob")
    seller_keys_ok = all(set(row.keys()) == SELLER_ROW_KEYS
                         for row in bob["sellers"])
    cat_keys_ok = all(set(row.keys()) == CATEGORY_ROW_KEYS
                      for row in bob["categories"])
    ok1 = (set(bob.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and seller_keys_ok
           and cat_keys_ok
           and bob["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["buyer_id"] == "usr:nobody"
           and empty["purchase_count"] == 0
           and empty["refund_count"] == 0
           and empty["seller_count"] == 0
           and empty["category_count"] == 0
           and empty["refunded_sellers"] == 0
           and empty["gross_spend"] == 0
           and empty["refunded_tokens"] == 0
           and empty["net_spend"] == 0
           and empty["top1_seller_share"] is None
           and empty["top3_seller_share"] is None
           and empty["seller_herfindahl"] is None
           and empty["pareto_seller_count"] is None
           and empty["top1_category_share"] is None
           and empty["top3_category_share"] is None
           and empty["category_herfindahl"] is None
           and empty["pareto_category_count"] is None
           and empty["sellers"] == []
           and empty["categories"] == [])
    record("AC-BC1", ok1,
           "env_keys=%d exact=%r seller_keys=%r cat_keys=%r"
           " empty_rows=%r"
           % (len(bob), set(bob.keys()) == ENVELOPE_KEYS,
              seller_keys_ok, cat_keys_ok,
              (len(empty["sellers"]), len(empty["categories"]))))

    # -- AC-BC2 purchase-side authority, order and cumulative ---------
    seller_order = [row["dev_account"] for row in bob["sellers"]]
    cat_order = [row["category"] for row in bob["categories"]]
    seller_ranks = [row["rank"] for row in bob["sellers"]]
    cat_ranks = [row["rank"] for row in bob["categories"]]
    cum_s = [row["cumulative_share"] for row in bob["sellers"]]
    cum_c = [row["cumulative_share"] for row in bob["categories"]]
    ok2 = (seller_order == ["usr:frank", "usr:dana", "usr:gina"]
           and cat_order == ["tools", "data"]
           and seller_ranks == [1, 2, 3]
           and cat_ranks == [1, 2]
           and cum_s[-1] == 1.0
           and cum_c[-1] == 1.0
           and all(row["dev_account"] not in ("usr:hana", "usr:ivan")
                   for row in bob["sellers"])
           and all(row["category"] != "none"
                   for row in bob["categories"]))
    record("AC-BC2", ok2,
           "sellers=%r cats=%r ranks=%r cum_s=%r cum_c=%r"
           % (seller_order, cat_order, (seller_ranks, cat_ranks),
              cum_s, cum_c))

    # -- AC-BC3 conservation on both axes and the refund law ----------
    erin = am.api_buyer_concentration("usr:erin")
    erin_seller = seller_row(erin, "usr:dana")
    erin_cat = category_row(erin, "tools")
    ok3 = (sum(row["net_spend"] for row in bob["sellers"])
           == bob["net_spend"] == 100
           and sum(row["gross_spend"] for row in bob["sellers"])
           == bob["gross_spend"] == 100
           and sum(row["net_spend"] for row in bob["categories"])
           == bob["net_spend"]
           and sum(row["gross_spend"] for row in bob["categories"])
           == bob["gross_spend"]
           and bob["net_spend"] + bob["refunded_tokens"]
           == bob["gross_spend"]
           and bob["purchase_count"] == 4
           and bob["refund_count"] == 0
           and bob["seller_count"] == 3
           and bob["category_count"] == 2
           and bob["refunded_sellers"] == 0
           and erin["net_spend"] == 0
           and erin["gross_spend"] == 30
           and erin["refunded_tokens"] == 30
           and erin["seller_count"] == 1
           and erin["refunded_sellers"] == 1
           and erin["purchase_count"] == 1
           and erin["refund_count"] == 1
           and erin_seller["net_purchase_count"] == 0
           and erin_seller["net_spend"] == 0
           and erin_seller["share"] is None
           and erin_cat["net_spend"] == 0
           and erin_cat["share"] is None)
    record("AC-BC3", ok3,
           "bob_net=%r bob_gross=%r erin=%r erin_seller=%r"
           % (bob["net_spend"], bob["gross_spend"],
              (erin["purchase_count"], erin["refund_count"],
               erin["net_spend"], erin["refunded_tokens"]),
              (erin_seller["net_purchase_count"],
               erin_seller["net_spend"], erin_seller["share"])))

    # -- AC-BC4 share law and the zero-net scope ----------------------
    seller_shares = [row["share"] for row in bob["sellers"]]
    cat_shares = [row["share"] for row in bob["categories"]]
    ok4 = (seller_shares == [0.5, 0.3, 0.2]
           and cat_shares == [0.8, 0.2]
           and abs(sum(seller_shares) - 1.0) <= 1e-9
           and abs(sum(cat_shares) - 1.0) <= 1e-9
           and bob["top1_seller_share"] == 0.5
           and bob["top3_seller_share"] == 1.0
           and bob["top1_category_share"] == 0.8
           and bob["top3_category_share"] == 1.0
           and erin["top1_seller_share"] is None
           and erin["top3_seller_share"] is None
           and erin["seller_herfindahl"] is None
           and erin["pareto_seller_count"] is None
           and erin["top1_category_share"] is None
           and erin["category_herfindahl"] is None
           and erin["pareto_category_count"] is None
           and all(row["cumulative_share"] is None
                   for row in erin["sellers"])
           and all(row["cumulative_share"] is None
                   for row in erin["categories"]))
    record("AC-BC4", ok4,
           "seller_shares=%r cats=%r top1s=%r top1c=%r erin=%r"
           % (seller_shares, cat_shares, bob["top1_seller_share"],
              bob["top1_category_share"],
              (erin["top1_seller_share"], erin["seller_herfindahl"],
               erin["pareto_seller_count"])))

    # -- AC-BC5 herfindahl law on both axes ---------------------------
    jade = am.api_buyer_concentration("usr:jade")
    kate = am.api_buyer_concentration("usr:kate")
    exact_s = sum((float(row["net_spend"]) / bob["net_spend"]) ** 2
                  for row in bob["sellers"])
    exact_c = sum((float(row["net_spend"]) / bob["net_spend"]) ** 2
                  for row in bob["categories"])
    ok5 = (bob["seller_herfindahl"] == 3800.0
           and bob["seller_herfindahl"] == round(exact_s * 10000, 2)
           and bob["category_herfindahl"] == 6800.0
           and bob["category_herfindahl"] == round(exact_c * 10000, 2)
           and jade["seller_herfindahl"] == 5000.0
           and jade["top1_seller_share"] == 0.5
           and jade["top3_seller_share"] == 1.0
           and jade["category_herfindahl"] == 10000.0
           and jade["top1_category_share"] == 1.0
           and kate["seller_herfindahl"] == 10000.0
           and kate["top1_seller_share"] == 1.0
           and kate["category_herfindahl"] == 10000.0)
    record("AC-BC5", ok5,
           "bob_s=%r exact_s=%r bob_c=%r exact_c=%r jade=%r kate=%r"
           % (bob["seller_herfindahl"], round(exact_s * 10000, 2),
              bob["category_herfindahl"], round(exact_c * 10000, 2),
              (jade["seller_herfindahl"],
               jade["category_herfindahl"]),
              kate["seller_herfindahl"]))

    # -- AC-BC6 pareto law and the exact-80% boundary -----------------
    ok6 = (bob["pareto_seller_count"] == 2
           and bob["pareto_category_count"] == 1
           and jade["pareto_seller_count"] == 2
           and jade["pareto_category_count"] == 1
           and kate["pareto_seller_count"] == 1
           and isinstance(bob["pareto_seller_count"], int)
           and not isinstance(bob["pareto_seller_count"], bool)
           and isinstance(bob["pareto_category_count"], int))
    record("AC-BC6", ok6,
           "bob=%r jade=%r kate=%r"
           % ((bob["pareto_seller_count"],
               bob["pareto_category_count"]),
              (jade["pareto_seller_count"],
               jade["pareto_category_count"]),
              kate["pareto_seller_count"]))

    # -- AC-BC7 gate, isolation and cross-face identity ---------------
    gate_codes = []
    for bad in (None, "", "u", "usr", 123, [], {"usr:x": 1}, False):
        try:
            am.api_buyer_concentration(bad)
            gate_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            gate_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_buyer_concentration("usr:")
    spend = am.api_buyer_seller_spend("usr:bob")
    spend_by_dev = {row["dev_account"]: row for row in spend["sellers"]}
    cross_rows = all(
        spend_by_dev[row["dev_account"]]["net_spent"]
        == row["net_spend"]
        and spend_by_dev[row["dev_account"]]["gross_spent"]
        == row["gross_spend"]
        for row in bob["sellers"])
    ok7 = (gate_codes == ["E_AM_BAD_ACCOUNT"] * 8
           and prefix["buyer_id"] == "usr:"
           and prefix["seller_count"] == 0
           and prefix["category_count"] == 0
           and prefix["net_spend"] == 0
           and prefix["sellers"] == []
           and prefix["categories"] == []
           and bob["net_spend"] == spend["net_spent"]
           and bob["gross_spend"] == spend["gross_spent"]
           and bob["purchase_count"] == spend["purchase_count"]
           and bob["refund_count"] == spend["refund_count"]
           and bob["seller_count"] == spend["seller_count"]
           and cross_rows
           and all(row["dev_account"] not in ("usr:gina", "usr:hana")
                   for row in kate["sellers"])
           and jade["net_spend"] == 10
           and all(row["dev_account"] != "usr:dana"
                   for row in jade["sellers"]))
    record("AC-BC7", ok7,
           "gate=%r prefix=%r cross=%r spend=%r kate_rows=%r"
           % (gate_codes, (prefix["seller_count"],
                           prefix["net_spend"]), cross_rows,
              (spend["net_spent"], spend["gross_spent"]),
              [row["dev_account"] for row in kate["sellers"]]))

    # -- AC-BC8 pure read, cross-restart identity and the wiring ------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    again = dumps(am.api_buyer_concentration("usr:bob"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    final_bob = dumps(am.api_buyer_concentration("usr:bob"))
    final_jade = dumps(am.api_buyer_concentration("usr:jade"))
    final_erin = dumps(am.api_buyer_concentration("usr:erin"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_bob = dumps(am.api_buyer_concentration("usr:bob"))
    second_jade = dumps(am.api_buyer_concentration("usr:jade"))
    second_erin = dumps(am.api_buyer_concentration("usr:erin"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_bob = dumps(am.api_buyer_concentration("usr:bob"))
    third_jade = dumps(am.api_buyer_concentration("usr:jade"))
    third_erin = dumps(am.api_buyer_concentration("usr:erin"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_buyer_concentration("usr:bob")
        am.api_buyer_concentration("usr:jade")
        am.api_buyer_concentration("usr:erin")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (again == final_bob
           and final_bob == second_bob == third_bob
           and final_jade == second_jade == third_jade
           and final_erin == second_erin == third_erin
           and digests_before == digests_after
           and tx_before == tx_after
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-buyerconcentration" in runner_text)
    record("AC-BC8", ok8,
           "sha16=%s stable=%r identical=%r frozen=%r tx_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final_bob.encode("utf-8"))
              .hexdigest()[:16], again == final_bob,
              final_bob == second_bob == third_bob,
              digests_before == digests_after, tx_b == tx_a,
              shas_before == shas_after,
              "ledger-apimarket-buyerconcentration" in runner_text))

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