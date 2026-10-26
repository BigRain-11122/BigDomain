"""Acceptance suite for the apimarket per-category demand face
(BigDomain R2141; canon = the explore-queue row seeded and claimed in
R2141, criteria AC-AMCD1..AC-AMCD8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMCD prefix, the
api_category_demand name, include_uncategorized, avg_net_price, this
suite name and the ledger-apimarket-categorydemand runner label were
all git-grep zero-occupancy anchored 2026-10-26, rc=1).

Face under proof: APIMarketFace.api_category_demand. api_categories
answers the supply side of one category; nothing answered which
categories actually SELL (api_market_stats aggregates the whole
market, api_listing_demand one listing, dev_sales_board one seller,
api_market_months one month). This window pins the new face:

  - the thirteen-key envelope and the twelve-key rows on an honest
    empty market and on the loaded world;
  - partition conservation per row and globally, with the honest
    uncategorized bucket last;
  - trade conservation per row and cross-face identity with
    api_market_stats on the default call;
  - the buyer_count law: a distinct count WITHIN a category, the
    envelope counting distinct buyers over the included rows;
  - retirement and re-listing only move the partition counters;
  - a refund lowers the net side of the refunded listing's category
    only, keeping purchase_count and buyer_count intact;
  - the include_uncategorized switch and its bool gate;
  - cross-restart byte identity and the pure-read law.

Usage: python test_apimarket_categorydemand.py
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
    "category_count", "listing_count", "live_listing_count",
    "retired_listing_count", "purchase_count", "buyer_count",
    "refund_count", "net_purchase_count", "gross_tokens",
    "refunded_tokens", "net_gross_tokens", "categories",
    "disclaimer"}

ROW_KEYS = {
    "category", "listing_count", "live_listing_count",
    "retired_listing_count", "purchase_count", "buyer_count",
    "refund_count", "net_purchase_count", "gross_tokens",
    "refunded_tokens", "net_gross_tokens", "avg_net_price"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds")


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


def by_category(env):
    return {row["category"]: row for row in env["categories"]}


def seed_world(led, dk, am):
    """dana owns two 'data' listings and one uncategorized listing,
    frank one 'tools' listing, gina one 'tools' listing that never
    sells. Seven purchases: data 3 / tools 3 / uncategorized 1,
    gross 23 / 21 / 5 = 49. Distinct buyers: bob, carol (data),
    u1..u3 (tools), u1 again on the uncategorized row."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-AMCD-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-AMCD-S",
                     "settlement")
    for who in ("bob", "carol") + tuple("u%d" % i for i in range(1, 4)):
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
    g1 = am.publish_api("usr:gina", "docs-kit", "Docs Kit API",
                        "document pipeline kit", PAYLOAD, 4, False,
                        category="tools")["listing_id"]
    bob_d1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    am.purchase_api("usr:bob", d2, "ref-bob-d2")
    for i in range(1, 4):
        am.purchase_api("usr:u%d" % i, f1, "ref-u%d-f1" % i)
    am.purchase_api("usr:u1", d3, "ref-u1-d3")
    return d1, d2, d3, f1, g1, bob_d1


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-categorydemand-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d3, f1, g1, bob_d1 = seed_world(led, dk, am)

    # -- AC-AMCD1 envelope and row contract, honest empty market first --
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-categorydemand-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_category_demand()
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_category_demand()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in env["categories"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and row_keys_ok
           and env["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["category_count"] == 0
           and empty["listing_count"] == 0
           and empty["purchase_count"] == 0
           and empty["buyer_count"] == 0
           and empty["refund_count"] == 0
           and empty["net_purchase_count"] == 0
           and empty["gross_tokens"] == 0
           and empty["refunded_tokens"] == 0
           and empty["net_gross_tokens"] == 0
           and empty["categories"] == [])
    record("AC-AMCD1", ok1,
           "env_keys=%d exact=%r row_keys=%r rows=%d empty_rows=%d"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS,
              row_keys_ok, len(env["categories"]),
              len(empty["categories"])))

    # -- AC-AMCD2 partition conservation and bucket position ------------
    rows = env["categories"]
    cats = [row["category"] for row in rows]
    ok2 = (env["category_count"] == len(rows) == 3
           and cats == ["data", "tools", None]
           and env["listing_count"] == 5
           and env["listing_count"]
           == sum(row["listing_count"] for row in rows)
           and env["live_listing_count"] == 5
           and env["retired_listing_count"] == 0
           and all(row["listing_count"]
                   == row["live_listing_count"]
                   + row["retired_listing_count"] for row in rows)
           and env["listing_count"] == env["live_listing_count"]
           + env["retired_listing_count"])
    record("AC-AMCD2", ok2,
           "cats=%r count=%d listings=%d/%d/%d"
           % (cats, env["category_count"], env["listing_count"],
              env["live_listing_count"],
              env["retired_listing_count"]))

    # -- AC-AMCD3 trade conservation and cross-face identity ------------
    ok3 = (env["purchase_count"] == 7
           and env["gross_tokens"] == 49
           and env["refund_count"] == 0
           and env["net_purchase_count"] == 7
           and env["net_gross_tokens"] == 49
           and all(row["gross_tokens"]
                   == row["net_gross_tokens"] + row["refunded_tokens"]
                   for row in rows)
           and all(row["net_purchase_count"]
                   == row["purchase_count"] - row["refund_count"]
                   for row in rows))
    stats = am.api_market_stats()
    ok3 = (ok3
           and env["purchase_count"] == stats["purchase_count"]
           and env["refund_count"] == stats["refund_count"]
           and env["gross_tokens"] == stats["gross_tokens"]
           and env["refunded_tokens"] == stats["refunded_tokens"]
           and env["net_gross_tokens"] == stats["net_gross_tokens"]
           and env["listing_count"] == stats["listing_count"])
    record("AC-AMCD3", ok3,
           "purchases=%d gross=%d net=%d stats=%d/%d/%d"
           % (env["purchase_count"], env["gross_tokens"],
              env["net_gross_tokens"], stats["purchase_count"],
              stats["gross_tokens"], stats["net_gross_tokens"]))

    # -- AC-AMCD4 buyer_count is a within-category distinct count -------
    view = by_category(env)
    ok4 = (view["data"]["buyer_count"] == 2
           and view["data"]["purchase_count"] == 3
           and view["tools"]["buyer_count"] == 3
           and view["tools"]["purchase_count"] == 3
           and view[None]["buyer_count"] == 1
           and view[None]["purchase_count"] == 1
           and env["buyer_count"] == 5
           and env["buyer_count"] < sum(row["buyer_count"]
                                        for row in rows))
    conn = sqlite3.connect(am.db_path)
    data_buyers = conn.execute(
        "SELECT COUNT(DISTINCT p.buyer_id)"
        " FROM apimarket_purchases p"
        " JOIN apimarket_listings l ON l.listing_id = p.listing_id"
        " WHERE l.category = 'data'").fetchone()[0]
    conn.close()
    ok4 = ok4 and view["data"]["buyer_count"] == int(data_buyers)
    record("AC-AMCD4", ok4,
           "data=%d tools=%d uncat=%d envelope=%d row_sum=%d distinct=%d"
           % (view["data"]["buyer_count"],
              view["tools"]["buyer_count"],
              view[None]["buyer_count"], env["buyer_count"],
              sum(row["buyer_count"] for row in rows),
              int(data_buyers)))

    # -- AC-AMCD5 delist and relist only move the partition counters ----
    frozen = [k for k in ROW_KEYS
              if k not in ("live_listing_count",
                           "retired_listing_count")]
    before = am.api_category_demand()
    am.delist_api("usr:dana", d2)
    after_delist = am.api_category_demand()
    am.relist_api("usr:dana", d2)
    after_relist = am.api_category_demand()
    b_data = by_category(before)["data"]
    d_data = by_category(after_delist)["data"]
    ok5 = (d_data["live_listing_count"] == b_data["live_listing_count"] - 1
           and d_data["retired_listing_count"] == 1
           and all(d_data[k] == b_data[k] for k in frozen)
           and after_delist["retired_listing_count"] == 1
           and after_delist["live_listing_count"] == 4
           and after_relist == before)
    record("AC-AMCD5", ok5,
           "live=%d->%d retired=%d frozen=%r relist_back=%r"
           % (b_data["live_listing_count"],
              d_data["live_listing_count"],
              after_delist["retired_listing_count"],
              all(d_data[k] == b_data[k] for k in frozen),
              after_relist == before))

    # -- AC-AMCD6 a refund lowers the net side of one category only -----
    refund = am.refund_api("usr:bob", bob_d1["purchase_id"],
                           "suite refund")
    after_refund = am.api_category_demand()
    r_view = by_category(after_refund)
    r_data = r_view["data"]
    ok6 = (after_refund["refund_count"] == 1
           and after_refund["refunded_tokens"] == refund["amount"]
           and after_refund["gross_tokens"] == before["gross_tokens"]
           and after_refund["purchase_count"]
           == before["purchase_count"]
           and after_refund["buyer_count"] == before["buyer_count"]
           and r_data["purchase_count"] == b_data["purchase_count"]
           and r_data["buyer_count"] == b_data["buyer_count"]
           and r_data["gross_tokens"] == b_data["gross_tokens"]
           and r_data["refunded_tokens"] == refund["amount"]
           and r_data["net_gross_tokens"]
           == b_data["net_gross_tokens"] - refund["amount"]
           and r_data["net_purchase_count"]
           == b_data["purchase_count"] - 1
           and r_data["avg_net_price"]
           == float(r_data["net_gross_tokens"])
           / r_data["net_purchase_count"]
           and r_view["tools"] == view["tools"]
           and r_view[None] == view[None])
    record("AC-AMCD6", ok6,
           "refund=%d data_net=%d->%d avg=%r tools_frozen=%r"
           % (refund["amount"], b_data["net_gross_tokens"],
              r_data["net_gross_tokens"], r_data["avg_net_price"],
              r_view["tools"] == view["tools"]))

    # -- AC-AMCD7 the uncategorized switch and its bool gate ------------
    switched = am.api_category_demand(include_uncategorized=False)
    s_view = by_category(switched)
    gate_codes = []
    for bad in (None, 1, 0, "yes", [], {}):
        try:
            am.api_category_demand(include_uncategorized=bad)
            gate_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            gate_codes.append(getattr(exc, "code", "?"))
    ok7 = (switched["category_count"] == 2
           and [row["category"] for row in switched["categories"]]
           == ["data", "tools"]
           and None not in s_view
           and switched["listing_count"]
           == after_refund["listing_count"] - 1
           and switched["purchase_count"]
           == after_refund["purchase_count"] - 1
           and switched["gross_tokens"]
           == after_refund["gross_tokens"]
           - view[None]["gross_tokens"]
           and switched["buyer_count"] == 5
           and gate_codes == ["E_AM_BAD_ARGS"] * 6)
    record("AC-AMCD7", ok7,
           "rows=%d listing_drop=%d purchase_drop=%d buyer=%d gates=%r"
           % (switched["category_count"],
              after_refund["listing_count"]
              - switched["listing_count"],
              after_refund["purchase_count"]
              - switched["purchase_count"],
              switched["buyer_count"], gate_codes))

    # -- AC-AMCD8 cross-restart byte identity and the pure-read law -----
    first = dumps(after_refund)
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second = dumps(am.api_category_demand())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third = dumps(am.api_category_demand())
    tx_before = ledger_tx_ids(led)
    digests_before = market_digests(am)
    for _ in range(3):
        am.api_category_demand()
    tx_after = ledger_tx_ids(led)
    digests_after = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (first == second == third
           and tx_before == tx_after
           and digests_before == digests_after
           and shas_before == shas_after
           and "ledger-apimarket-categorydemand" in runner_text)
    record("AC-AMCD8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(first.encode("utf-8")).hexdigest()[:16],
              first == second == third, tx_before == tx_after,
              digests_before == digests_after,
              shas_before == shas_after,
              "ledger-apimarket-categorydemand" in runner_text))

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