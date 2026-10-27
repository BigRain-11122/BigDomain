"""Acceptance suite for the apimarket asking-price percentile face
(BigDomain R2160; canon = the explore-queue row seeded in R2149 and
claimed in R2160, criteria AC-MPP1..AC-MPP8 registered in that claim
note BEFORE this code existed - honesty law; the AC-MPP prefix, the
api_market_price_percentiles name, price_percentiles and _percentile
were git-grep zero-occupancy on the src face against HEAD 2026-10-27,
rc=1, and test_apimarket_pricepercentiles /
ledger-apimarket-pricepercentiles / p90_price were zero-occupancy
across the whole tree).

Face under proof: APIMarketFace.api_market_price_percentiles. The
catalog face answers the per-bucket min/max band, the position face
answers one listing's rank inside its own bucket, and the market stats
face carries a single avg_live_price; the distribution itself - the
quartiles, the median, the ninetieth percentile and the spread - had
no face, so a seller could not tell which band its asking price lands
in and an operator had no pricing benchmark. This suite pins:

  - the fourteen-key envelope and the eight-key rows, honest empty
    world first;
  - the scope law (live only by default, retired on request) with
    partition conservation and the global/row aggregation identity;
  - the linear-interpolation percentile law on the exact sample
    [1..10] and the small-sample edges;
  - one row per effective category bucket, the uncategorized bucket
    last, and revise_category moving counts and quantiles in one step
    that restores byte-identically on the way back;
  - the price seam (revise_price moves the distribution) and the
    asking-price nature of the face (purchases, refunds and ratings
    never move it);
  - the bool-only gate family, the pure-read law and cross-restart
    byte identity plus the runner wiring.

Usage: python test_apimarket_pricepercentiles.py
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
    "listing_count", "live_listing_count", "retired_listing_count",
    "min_price", "max_price", "p25_price", "p50_price", "p75_price",
    "p90_price", "mean_price", "spread", "category_count",
    "categories", "disclaimer"}

ROW_KEYS = {
    "category", "listing_count", "live_listing_count",
    "retired_listing_count", "min_price", "max_price", "mean_price",
    "p50_price"}

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


def seed_devs(led, dk, devs):
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-MPP-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-MPP-S",
                     "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    for who in devs:
        dk.issue_key("usr:" + who, who + "-key", 10, ["backtest"],
                     False)


def seed_world(led, dk, am):
    """dana owns two 'data' listings (10 and 3) and one uncategorized
    listing (5); frank one 'tools' listing (7); gina one 'media'
    listing (6) plus a second 'media' listing (9) that is retired, so
    its price leaves the default distribution and returns when
    include_delisted is requested."""
    seed_devs(led, dk, ("dana", "frank", "gina"))
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
    g2 = am.publish_api("usr:gina", "media-archive", "Media Archive API",
                        "archived media pipeline pack", PAYLOAD, 9,
                        False, category="media")["listing_id"]
    am.delist_api("usr:gina", g2)
    return d1, d2, d3, f1, g1, g2


def price_world(prices, categories=None):
    """Build a throwaway world whose live asking prices are exactly
    `prices` (one listing each) and return the face for it."""
    tmp = tempfile.mkdtemp(prefix="apimarket-mpp-price-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    led, metered, dk, _gate, am = build_stack(
        os.path.join(tmp, "ledger.db"), cfg, lobby_cfg)
    seed_devs(led, dk, ("dana",))
    for idx, price in enumerate(prices):
        cat = None
        if categories is not None:
            cat = categories[idx]
        am.publish_api("usr:dana", "p%02d" % idx,
                       "Listing %02d" % idx,
                       "deterministic price sample", PAYLOAD,
                       int(price), False, category=cat)
    return led, metered, dk, am


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-pricepercentiles-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d3, f1, g1, g2 = seed_world(led, dk, am)

    # -- AC-MPP1 the contract, honest empty first ----------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-mpp-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_price_percentiles()
    close_stack(e_am, e_dk, e_metered, e_led)
    base = am.api_market_price_percentiles()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in base["categories"])
    ok1 = (set(base.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and row_keys_ok
           and base["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["listing_count"] == 0
           and empty["live_listing_count"] == 0
           and empty["retired_listing_count"] == 0
           and empty["min_price"] is None
           and empty["max_price"] is None
           and empty["p25_price"] is None
           and empty["p50_price"] is None
           and empty["p75_price"] is None
           and empty["p90_price"] is None
           and empty["mean_price"] is None
           and empty["spread"] is None
           and empty["category_count"] == 0
           and empty["categories"] == [])
    record("AC-MPP1", ok1,
           "env_keys=%d exact=%r row_keys=%r rows=%d empty_rows=%d"
           % (len(base), set(base.keys()) == ENVELOPE_KEYS,
              row_keys_ok, len(base["categories"]),
              len(empty["categories"])))

    # -- AC-MPP2 scope law, partition conservation, aggregation -------
    with_retired = am.api_market_price_percentiles(include_delisted=True)
    base_cats = [row["category"] for row in base["categories"]]
    full_cats = [row["category"] for row in with_retired["categories"]]
    ok2 = (base["listing_count"] == 5
           and base["live_listing_count"] == 5
           and base["retired_listing_count"] == 0
           and base["min_price"] == 3
           and base["max_price"] == 10
           and with_retired["listing_count"] == 6
           and with_retired["live_listing_count"] == 5
           and with_retired["retired_listing_count"] == 1
           and with_retired["max_price"] == 10
           and [int(x) for x in [3, 5, 6, 7, 10]]
           == sorted([3, 5, 6, 7, 10])
           # partition conservation across both scopes
           and base["listing_count"]
           == base["live_listing_count"] + base["retired_listing_count"]
           and with_retired["listing_count"]
           == (with_retired["live_listing_count"]
               + with_retired["retired_listing_count"])
           # row set: category ascending, the uncategorized bucket last
           and base_cats == ["data", "media", "tools", None]
           and full_cats == ["data", "media", "tools", None]
           # the envelope is exactly the aggregate of its rows
           and base["listing_count"]
           == sum(row["listing_count"] for row in base["categories"])
           and with_retired["listing_count"]
           == sum(row["listing_count"]
                  for row in with_retired["categories"])
           and base["min_price"]
           == min(row["min_price"] for row in base["categories"])
           and base["max_price"]
           == max(row["max_price"] for row in base["categories"]))
    record("AC-MPP2", ok2,
           "base=%r full=%r cats=%r full_cats=%r"
           % ((base["listing_count"], base["live_listing_count"],
               base["retired_listing_count"]),
              (with_retired["listing_count"],
               with_retired["live_listing_count"],
               with_retired["retired_listing_count"]),
              base_cats, full_cats))

    # -- AC-MPP3 percentile law on the exact sample [1..10] -----------
    p_led, p_metered, p_dk, p_am = price_world(list(range(1, 11)))
    exact = p_am.api_market_price_percentiles()
    close_stack(p_am, p_dk, p_metered, p_led)
    ok3 = (exact["listing_count"] == 10
           and exact["min_price"] == 1
           and exact["max_price"] == 10
           and exact["p25_price"] == 3.25
           and exact["p50_price"] == 5.5
           and exact["p75_price"] == 7.75
           and exact["p90_price"] == 9.1
           and exact["mean_price"] == 5.5
           and exact["spread"] == 9
           and exact["min_price"] <= exact["p25_price"]
           <= exact["p50_price"] <= exact["p75_price"]
           <= exact["p90_price"] <= exact["max_price"])
    record("AC-MPP3", ok3,
           "p25=%r p50=%r p75=%r p90=%r mean=%r spread=%r"
           % (exact["p25_price"], exact["p50_price"],
              exact["p75_price"], exact["p90_price"],
              exact["mean_price"], exact["spread"]))

    # -- AC-MPP4 small-sample edges ------------------------------------
    one_led, one_metered, one_dk, one_am = price_world([7])
    one = one_am.api_market_price_percentiles()
    close_stack(one_am, one_dk, one_metered, one_led)
    two_led, two_metered, two_dk, two_am = price_world([3, 5])
    two = two_am.api_market_price_percentiles()
    close_stack(two_am, two_dk, two_metered, two_led)
    three_led, three_metered, three_dk, three_am = price_world(
        [1, 2, 3])
    three = three_am.api_market_price_percentiles()
    close_stack(three_am, three_dk, three_metered, three_led)
    ok4 = (one["p25_price"] == 7.0 and one["p50_price"] == 7.0
           and one["p75_price"] == 7.0 and one["p90_price"] == 7.0
           and one["spread"] == 0 and one["min_price"] == 7
           and one["max_price"] == 7
           and two["p50_price"] == 4.0
           and two["spread"] == 2
           and three["p50_price"] == 2.0
           and three["p25_price"] == 1.5
           and three["p75_price"] == 2.5)
    record("AC-MPP4", ok4,
           "one=(%r,%r,%r,%r) two_p50=%r three_p50=%r"
           % (one["p25_price"], one["p50_price"], one["p75_price"],
              one["p90_price"], two["p50_price"],
              three["p50_price"]))

    # -- AC-MPP5 category rows and the single effective-bucket seam ----
    cats_face = am.api_categories()
    cat_buckets = [row["category"] for row in cats_face["categories"]]
    if cats_face["uncategorized_count"]:
        cat_buckets = cat_buckets + [None]
    rows_ok = all(
        row["listing_count"] == (row["live_listing_count"]
                                + row["retired_listing_count"])
        and row["min_price"] <= row["max_price"]
        and row["mean_price"] == float(row["min_price"]
                                       + row["max_price"]) / 2
        for row in base["categories"] if row["listing_count"] == 2)
    before_move = dumps(am.api_market_price_percentiles())
    am.revise_category("usr:dana", d3, "tools")
    moved = am.api_market_price_percentiles()
    moved_cats = {row["category"]: row for row in moved["categories"]}
    am.revise_category("usr:dana", d3, None)
    back = dumps(am.api_market_price_percentiles())
    ok5 = (set(cat_buckets) == set(base_cats)
           and rows_ok
           and all(row["listing_count"]
                   == row["live_listing_count"]
                   + row["retired_listing_count"]
                   for row in base["categories"])
           and moved_cats["tools"]["listing_count"] == 2
           and moved_cats["tools"]["min_price"] == 5
           and moved_cats["tools"]["max_price"] == 7
           and moved_cats["tools"]["p50_price"] == 6.0
           and None not in moved_cats
           and moved["category_count"] == 3
           and moved["listing_count"] == base["listing_count"]
           and back == before_move)
    record("AC-MPP5", ok5,
           "cat_buckets=%r base=%r moved_tools=%r restored=%r"
           % (cat_buckets, base_cats,
              (moved_cats["tools"]["listing_count"],
               moved_cats["tools"]["min_price"],
               moved_cats["tools"]["max_price"],
               moved_cats["tools"]["p50_price"]),
              back == before_move))

    # -- AC-MPP6 the price seam and the asking-price nature -----------
    pre_price = am.api_market_price_percentiles()
    am.revise_price("usr:dana", d2, 1)
    priced = am.api_market_price_percentiles()
    buy = am.purchase_api("usr:bob", d1, "ref-bob-d1")
    am.refund_api("usr:bob", buy["purchase_id"], "changed my mind")
    am.rate_api("usr:bob", d1, 5)
    traded = am.api_market_price_percentiles()
    retired_only = am.api_market_price_percentiles(include_delisted=True)
    ok6 = (pre_price["min_price"] == 3
           and priced["min_price"] == 1
           and priced["max_price"] == 10
           and priced["p25_price"] == 5.0
           and priced["p50_price"] == 6.0
           and priced["spread"] == 9
           and "media" in [row["category"]
                           for row in priced["categories"]]
           # trades never move an asking-price distribution
           and dumps(traded) == dumps(priced)
           # the retired listing enters only on request, with its
           # own delist-time price
           and retired_only["listing_count"] == priced["listing_count"]
           + 1
           and {row["category"]: row for row in
                retired_only["categories"]}["media"]["listing_count"]
           == 2
           and {row["category"]: row for row in
                retired_only["categories"]}["media"]["max_price"] == 9)
    record("AC-MPP6", ok6,
           "pre_min=%r post=%r trade_equal=%r retired_media=%r"
           % (pre_price["min_price"],
              (priced["min_price"], priced["p25_price"],
               priced["p50_price"]), dumps(traded) == dumps(priced),
              {row["category"]: row for row in
               retired_only["categories"]}["media"]))

    # -- AC-MPP7 the gate family and the pure read --------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    gate_codes = []
    for bad in (0, 1, "", "yes", None):
        try:
            am.api_market_price_percentiles(bad)
            gate_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            gate_codes.append(getattr(exc, "code", "?"))
    first = dumps(am.api_market_price_percentiles())
    second = dumps(am.api_market_price_percentiles())
    for _ in range(3):
        am.api_market_price_percentiles()
        am.api_market_price_percentiles(include_delisted=True)
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (gate_codes == ["E_AM_BAD_ARGS"] * 5
           and first == second
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-MPP7", ok7,
           "gate=%r repeat=%r frozen=%r tx=%r"
           % (gate_codes, first == second,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-MPP8 cross-restart identity and the wiring ----------------
    final = dumps(am.api_market_price_percentiles())
    final_full = dumps(am.api_market_price_percentiles(True))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_run = dumps(am.api_market_price_percentiles())
    second_full = dumps(am.api_market_price_percentiles(True))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_run = dumps(am.api_market_price_percentiles())
    third_full = dumps(am.api_market_price_percentiles(True))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_market_price_percentiles()
        am.api_market_price_percentiles(True)
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (final == second_run == third_run
           and final_full == second_full == third_full
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-pricepercentiles" in runner_text)
    record("AC-MPP8", ok8,
           "sha16=%s identical=%r retired_identical=%r tx_equal=%r"
           " digests_equal=%r files_equal=%r registered=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_run == third_run,
              final_full == second_full == third_full, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-pricepercentiles" in runner_text))

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