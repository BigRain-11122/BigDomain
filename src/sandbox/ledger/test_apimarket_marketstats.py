"""Acceptance suite for the apimarket market-wide overview face
(BigDomain R2090; canon = the explore-queue row seeded and claimed
in R2090, criteria AC-AMMS1..AC-AMMS8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMMS prefix, the
api_market_stats name, this suite name and the
ledger-apimarket-marketstats runner label were all git-grep
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.api_market_stats. The ten existing
read faces each answer one narrow question - one listing
(api_view), one listing's ratings, price history and metadata
history, one seller's trust face (dev_profile), the seller board
(dev_sales_board), one buyer's library (api_library), the whole
board (api_board), one search page (api_search), one listing's
supply (api_supply) and its lifecycle. None answers "how big is
this market". This window pins that face:

  - the fifteen-key envelope on an honest empty market (zeros,
    avg_live_price None, disclaimer present) and on the loaded
    world;
  - partition conservation: listing_count == live + retired, and
    dev_count == the distinct seller count;
  - trade conservation: gross == net + refunded, net == dev net +
    platform net exactly (integer split), net_purchase_count ==
    purchase_count - refund_count;
  - retirement and re-listing only move the partition counters -
    every historical aggregate stays byte-frozen;
  - a refund lowers net gross and both net pools by exactly the
    refunded amounts while purchase_count and buyer_count keep
    counting the trades that did happen;
  - cross-face agreement with dev_sales_board (per-developer
    sums equal the market totals);
  - cross-restart byte identity across three instances;
  - the pure-read law: zero row mutations, zero token movement,
    product files byte-identical.

Usage: python test_apimarket_marketstats.py
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
    "listing_count", "live_listing_count",
    "retired_listing_count", "dev_count", "buyer_count",
    "purchase_count", "refund_count", "net_purchase_count",
    "gross_tokens", "refunded_tokens", "net_gross_tokens",
    "dev_revenue", "platform_revenue", "avg_live_price",
    "disclaimer"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings",
          "apimarket_price_revisions",
          "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_refunds")


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
    """dana owns two listings (10 and 3), frank one (7), gina is
    prefix-valid with zero listings. bob/carol/dave buy from dana;
    u1..u7 buy frank's listing. 11 purchases, gross 75 tokens,
    10 distinct buyers, 2 distinct sellers."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-AMMS-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-AMMS-S",
                     "settlement")
    for who in ("bob", "carol", "dave") + tuple(
            "u%d" % i for i in range(1, 8)):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3,
                        True)["listing_id"]
    f1 = am.publish_api("usr:frank", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 7,
                        False)["listing_id"]
    am.purchase_api("usr:bob", d1, "ref-bob-d1")
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    am.purchase_api("usr:bob", d2, "ref-bob-d2")
    am.purchase_api("usr:dave", d2, "ref-dave-d2")
    u1_purchase = None
    for i in range(1, 8):
        buyer = "usr:u%d" % i
        res = am.purchase_api(buyer, f1, "ref-u%d-f1" % i)
        if i == 1:
            u1_purchase = res["purchase_id"]
    return d1, d2, f1, u1_purchase


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-marketstats-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, f1, u1_purchase = seed_world(led, dk, am)

    # -- AC-AMMS1 envelope contract, honest empty market first ----------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-marketstats-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_stats()
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_market_stats()
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and env["disclaimer"] == DISCLAIMER
           and empty["listing_count"] == 0
           and empty["live_listing_count"] == 0
           and empty["retired_listing_count"] == 0
           and empty["dev_count"] == 0
           and empty["buyer_count"] == 0
           and empty["purchase_count"] == 0
           and empty["refund_count"] == 0
           and empty["net_purchase_count"] == 0
           and empty["gross_tokens"] == 0
           and empty["refunded_tokens"] == 0
           and empty["net_gross_tokens"] == 0
           and empty["dev_revenue"] == 0
           and empty["platform_revenue"] == 0
           and empty["avg_live_price"] is None)
    record("AC-AMMS1", ok1,
           "keys=%d exact=%r loaded=%d empty=%r avg=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS,
              env["listing_count"], empty["listing_count"],
              empty["avg_live_price"]))

    # -- AC-AMMS2 partition conservation and participant counts ---------
    ok2 = (env["listing_count"] == 3
           and env["live_listing_count"] == 3
           and env["retired_listing_count"] == 0
           and env["listing_count"]
           == env["live_listing_count"]
           + env["retired_listing_count"]
           and env["dev_count"] == 2
           and env["buyer_count"] == 10
           and abs(env["avg_live_price"]
                   - (10 + 3 + 7) / 3.0) < 1e-12)
    conn = sqlite3.connect(am.db_path)
    distinct_buyers = conn.execute(
        "SELECT COUNT(DISTINCT buyer_id) FROM apimarket_purchases"
    ).fetchone()[0]
    distinct_devs = conn.execute(
        "SELECT COUNT(DISTINCT dev_account) FROM apimarket_listings"
    ).fetchone()[0]
    conn.close()
    ok2 = (ok2 and env["buyer_count"] == int(distinct_buyers)
           and env["dev_count"] == int(distinct_devs))
    record("AC-AMMS2", ok2,
           "listing=%d/%d/%d dev=%d buyers=%d distinct=%d/%d avg=%r"
           % (env["listing_count"], env["live_listing_count"],
              env["retired_listing_count"], env["dev_count"],
              env["buyer_count"], int(distinct_devs),
              int(distinct_buyers), env["avg_live_price"]))

    # -- AC-AMMS3 trade conservation ------------------------------------
    ok3 = (env["purchase_count"] == 11
           and env["refund_count"] == 0
           and env["net_purchase_count"] == 11
           and env["gross_tokens"] == 75
           and env["refunded_tokens"] == 0
           and env["net_gross_tokens"] == 75
           and env["gross_tokens"]
           == env["net_gross_tokens"] + env["refunded_tokens"]
           and env["net_gross_tokens"]
           == env["dev_revenue"] + env["platform_revenue"]
           and env["net_purchase_count"]
           == env["purchase_count"] - env["refund_count"])
    conn = sqlite3.connect(am.db_path)
    paid = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(price_paid), 0)"
        " FROM apimarket_purchases").fetchone()
    conn.close()
    ok3 = ok3 and env["purchase_count"] == int(paid[0]) \
        and env["gross_tokens"] == int(paid[1])
    record("AC-AMMS3", ok3,
           "purchases=%d refunds=%d net_purchases=%d gross=%d net=%d"
           " dev+plat=%d/%d paid=%d/%d"
           % (env["purchase_count"], env["refund_count"],
              env["net_purchase_count"], env["gross_tokens"],
              env["net_gross_tokens"], env["dev_revenue"],
              env["platform_revenue"], int(paid[0]), int(paid[1])))

    # -- AC-AMMS4 delist and relist only move the partition counters -----
    frozen_keys = [k for k in ENVELOPE_KEYS
                   if k not in ("live_listing_count",
                                "retired_listing_count",
                                "avg_live_price", "disclaimer")]
    before = am.api_market_stats()
    am.delist_api("usr:dana", d2)
    after_delist = am.api_market_stats()
    am.relist_api("usr:dana", d2)
    after_relist = am.api_market_stats()
    ok4 = (after_delist["live_listing_count"] == 2
           and after_delist["retired_listing_count"] == 1
           and after_delist["listing_count"] == 3
           and after_delist["avg_live_price"]
           == (10 + 7) / 2.0
           and all(after_delist[k] == before[k] for k in frozen_keys)
           and after_relist == before)
    record("AC-AMMS4", ok4,
           "delist=%d/%d relist_back=%r frozen=%r avg=%r"
           % (after_delist["live_listing_count"],
              after_delist["retired_listing_count"],
              after_relist == before,
              all(after_delist[k] == before[k]
                  for k in frozen_keys),
              after_delist["avg_live_price"]))

    # -- AC-AMMS5 refund lowers the net side only ------------------------
    refund = am.refund_api("usr:u1", u1_purchase, "suite refund")
    after_refund = am.api_market_stats()
    ok5 = (after_refund["refund_count"] == 1
           and after_refund["purchase_count"] == 11
           and after_refund["buyer_count"] == 10
           and after_refund["net_purchase_count"] == 10
           and after_refund["refunded_tokens"] == refund["amount"]
           and after_refund["net_gross_tokens"]
           == before["net_gross_tokens"] - refund["amount"]
           and after_refund["gross_tokens"] == before["gross_tokens"]
           and after_refund["dev_revenue"]
           == before["dev_revenue"] - refund["dev_share"]
           and after_refund["platform_revenue"]
           == before["platform_revenue"] - refund["platform_share"]
           and after_refund["net_gross_tokens"]
           == after_refund["dev_revenue"]
           + after_refund["platform_revenue"]
           and after_refund["gross_tokens"]
           == after_refund["net_gross_tokens"]
           + after_refund["refunded_tokens"])
    record("AC-AMMS5", ok5,
           "refund=%r/%r/%r purchases=%d buyers=%d net=%d/%d"
           % (refund["amount"], refund["dev_share"],
              refund["platform_share"], after_refund["purchase_count"],
              after_refund["buyer_count"],
              after_refund["net_gross_tokens"],
              after_refund["gross_tokens"]))

    # -- AC-AMMS6 cross-face agreement with dev_sales_board --------------
    board = am.dev_sales_board()
    gross_sum = sum(int(r["gross_revenue"]) for r in board["board"])
    purchase_sum = sum(int(r["purchase_count"])
                       for r in board["board"])
    ok6 = (gross_sum == after_refund["gross_tokens"]
           and purchase_sum == after_refund["purchase_count"]
           and len(board["board"]) == after_refund["dev_count"])
    record("AC-AMMS6", ok6,
           "board_rows=%d gross_sum=%d market_gross=%d"
           " purchase_sum=%d market_purchases=%d"
           % (len(board["board"]), gross_sum,
              after_refund["gross_tokens"], purchase_sum,
              after_refund["purchase_count"]))

    # -- AC-AMMS7 cross-restart byte identity ----------------------------
    first = dumps(after_refund)
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second = dumps(am.api_market_stats())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third = dumps(am.api_market_stats())
    ok7 = (first == second == third)
    record("AC-AMMS7", ok7,
           "sha16=%s identical=%r"
           % (hashlib.sha256(first.encode("utf-8")).hexdigest()[:16],
              first == second == third))

    # -- AC-AMMS8 pure read ---------------------------------------------
    tx_before = ledger_tx_ids(led)
    digests_before = market_digests(am)
    for _ in range(3):
        am.api_market_stats()
    tx_after = ledger_tx_ids(led)
    digests_after = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    ok8 = (tx_before == tx_after
           and digests_before == digests_after
           and shas_before == shas_after)
    record("AC-AMMS8", ok8,
           "tx_equal=%r digests_equal=%r files_equal=%r tx=%d"
           % (tx_before == tx_after, digests_before == digests_after,
              shas_before == shas_after, len(tx_after)))

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