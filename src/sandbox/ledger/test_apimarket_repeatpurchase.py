"""Acceptance suite for the apimarket repeat-purchase face
(BigDomain R2161; canon = the R2149 explore seed claimed in R2161,
criteria AC-RPT1..AC-RPT8 registered in that claim note BEFORE this
code existed - honesty law; the AC-RPT prefix, api_repeat_purchase,
this suite name, the ledger-apimarket-repeatpurchase runner label,
repeat_buyer_count and top_repeat_buyer were all git-grep
zero-occupancy anchored against HEAD 2026-10-27, rc=1).

Face under proof: APIMarketFace.api_repeat_purchase. The library gives
rows, the buyer profile gives lifetime aggregates, the seller profile
gives gross totals and the category demand face gives volumes - none of
them answers whether the same resident comes back. This suite pins the
new face:

  - the twelve-key envelope and the eight-key rows, honest empty world
    first;
  - the NET-purchase counting authority (a refunded purchase counts
    neither in the numerator nor in the denominator, so a buyer whose
    only purchase was refunded disappears instead of being misread as a
    one-time buyer) and the repeat laws built on it;
  - scope: market-wide by default, one seller on request, with strict
    seller isolation and the honest difference between the two readings
    (one purchase each from two sellers is a repeat for the market and
    not a repeat for either seller);
  - purchase-side category rows on the one effective-category seam,
    uncategorized last, with the row sums conserving the envelope;
  - max / average / top-repeat-buyer extremes;
  - revise_category moving purchases between buckets without moving the
    envelope;
  - the seven-form account gate, the bare usr: prefix reading honestly
    empty, the pure-read law and cross-restart byte identity.

Usage: python test_apimarket_repeatpurchase.py
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
    "dev_account", "buyer_count", "repeat_buyer_count",
    "one_time_buyer_count", "repeat_rate", "purchase_count",
    "repeat_purchase_count", "avg_purchases_per_buyer",
    "max_purchases", "top_repeat_buyer", "categories", "disclaimer"}

ROW_KEYS = {
    "category", "buyer_count", "repeat_buyer_count",
    "one_time_buyer_count", "repeat_rate", "purchase_count",
    "repeat_purchase_count", "avg_purchases_per_buyer"}

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


def by_cat(env):
    return {row["category"]: row for row in env["categories"]}


def seed_world(led, dk, am):
    """dana owns d1/d2 in 'data' and d3 in the uncategorized bucket,
    frank owns two 'tools' listings, gina owns one 'media' listing that
    never sells. bob buys d1, d2 and f1 (a repeat buyer for dana, a
    one-time buyer for frank). carol buys d1 and refunds it, so she
    vanishes from the net counting entirely. dave buys f1 and f2 (a
    repeat buyer for frank). erin buys d3 and f1 - a repeat for the
    market and a one-time buyer for each seller."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-RPT-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-RPT-S",
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
    f2 = am.publish_api("usr:frank", "grid-kit", "Grid Kit API",
                        "deterministic grid payloads", PAYLOAD, 4,
                        False, category="tools")["listing_id"]
    am.publish_api("usr:gina", "media-pack", "Media Pack API",
                   "media pipeline pack", PAYLOAD, 6, False,
                   category="media")
    for lid, ref in ((d1, "ref-bob-d1"), (d2, "ref-bob-d2"),
                     (f1, "ref-bob-f1")):
        am.purchase_api("usr:bob", lid, ref)
    carol_d1 = am.purchase_api("usr:carol", d1, "ref-carol-d1")
    for lid, ref in ((f1, "ref-dave-f1"), (f2, "ref-dave-f2")):
        am.purchase_api("usr:dave", lid, ref)
    am.purchase_api("usr:erin", d3, "ref-erin-d3")
    am.purchase_api("usr:erin", f1, "ref-erin-f1")
    am.refund_api("usr:carol", carol_d1["purchase_id"],
                  "listing did not match description")
    return d1, d2, d3, f1, f2


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-repeatpurchase-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d3, f1, f2 = seed_world(led, dk, am)

    # -- AC-RPT1 the contract, honest empty first ----------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-rpt-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_repeat_purchase()
    empty_seller = e_am.api_repeat_purchase("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_repeat_purchase()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in market["categories"])
    ok1 = (set(market.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and set(empty_seller.keys()) == ENVELOPE_KEYS
           and row_keys_ok
           and market["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["dev_account"] is None
           and empty["buyer_count"] == 0
           and empty["repeat_buyer_count"] == 0
           and empty["one_time_buyer_count"] == 0
           and empty["repeat_rate"] is None
           and empty["purchase_count"] == 0
           and empty["repeat_purchase_count"] == 0
           and empty["avg_purchases_per_buyer"] is None
           and empty["max_purchases"] == 0
           and empty["top_repeat_buyer"] is None
           and empty["categories"] == []
           and empty_seller["dev_account"] == "usr:nobody"
           and empty_seller["buyer_count"] == 0
           and empty_seller["categories"] == [])
    record("AC-RPT1", ok1,
           "env_keys=%d exact=%r row_keys=%r cats=%d empty_cats=%d"
           % (len(market), set(market.keys()) == ENVELOPE_KEYS,
              row_keys_ok, len(market["categories"]),
              len(empty["categories"])))

    # -- AC-RPT2 net counting, the repeat laws and the refund law ------
    dana = am.api_repeat_purchase("usr:dana")
    ok2 = (market["purchase_count"] == 7
           and market["buyer_count"] == 3
           and market["repeat_buyer_count"] == 3
           and market["one_time_buyer_count"] == 0
           and market["repeat_purchase_count"] == 4
           and market["repeat_purchase_count"]
           == market["purchase_count"] - market["buyer_count"]
           and market["repeat_rate"] == 1.0
           and market["avg_purchases_per_buyer"] == 7.0 / 3.0
           and dana["purchase_count"] == 3
           and dana["buyer_count"] == 2
           and dana["repeat_buyer_count"] == 1
           and dana["one_time_buyer_count"] == 1
           and dana["repeat_rate"] == 0.5
           and dana["repeat_purchase_count"] == 1
           and dana["avg_purchases_per_buyer"] == 1.5
           and "usr:carol" not in json.dumps(dana))
    record("AC-RPT2", ok2,
           "market=%r dana=%r"
           % ({k: market[k] for k in ("purchase_count", "buyer_count",
                                      "repeat_buyer_count",
                                      "repeat_purchase_count")},
              {k: dana[k] for k in ("purchase_count", "buyer_count",
                                    "repeat_buyer_count",
                                    "repeat_rate")}))

    # -- AC-RPT3 scope: seller isolation and the honest difference -----
    frank = am.api_repeat_purchase("usr:frank")
    gina = am.api_repeat_purchase("usr:gina")
    positions = am.api_repeat_purchase("usr:dana")
    ok3 = (frank["purchase_count"] == 4
           and frank["buyer_count"] == 3
           and frank["repeat_buyer_count"] == 1
           and frank["top_repeat_buyer"] == "usr:dave"
           and frank["repeat_rate"] == 1.0 / 3.0
           and gina["purchase_count"] == 0
           and gina["buyer_count"] == 0
           and gina["repeat_rate"] is None
           and gina["categories"] == []
           and gina["top_repeat_buyer"] is None
           and market["repeat_buyer_count"] == 3
           and positions["repeat_buyer_count"] == 1)
    record("AC-RPT3", ok3,
           "frank=%r gina=%r market_repeat=%d dana_repeat=%d"
           % ({k: frank[k] for k in ("buyer_count",
                                     "repeat_buyer_count",
                                     "repeat_rate")},
              {k: gina[k] for k in ("buyer_count", "purchase_count")},
              market["repeat_buyer_count"],
              positions["repeat_buyer_count"]))

    # -- AC-RPT4 category rows and conservation ------------------------
    cats = by_cat(market)
    data_row = cats["data"]
    tools_row = cats["tools"]
    unc_row = cats[None]
    order = [row["category"] for row in market["categories"]]
    ok4 = (order == ["data", "tools", None]
           and data_row["purchase_count"] == 2
           and data_row["buyer_count"] == 1
           and data_row["repeat_buyer_count"] == 1
           and data_row["repeat_purchase_count"] == 1
           and tools_row["purchase_count"] == 4
           and tools_row["buyer_count"] == 3
           and tools_row["repeat_buyer_count"] == 1
           and tools_row["repeat_purchase_count"] == 1
           and tools_row["repeat_rate"] == 1.0 / 3.0
           and unc_row["purchase_count"] == 1
           and unc_row["buyer_count"] == 1
           and unc_row["repeat_buyer_count"] == 0
           and unc_row["repeat_purchase_count"] == 0
           and sum(row["purchase_count"]
                   for row in market["categories"])
           == market["purchase_count"]
           and all(row["repeat_purchase_count"]
                   == row["purchase_count"] - row["buyer_count"]
                   for row in market["categories"])
           and sum(row["repeat_purchase_count"]
                   for row in market["categories"]) == 2
           and market["repeat_purchase_count"] == 4
           and market["repeat_purchase_count"]
           >= sum(row["repeat_purchase_count"]
                  for row in market["categories"])
           and "media" not in cats)
    record("AC-RPT4", ok4,
           "order=%r rows=%r sum=%d envelope=%d"
           % (order,
              [(row["category"], row["purchase_count"],
                row["repeat_buyer_count"])
               for row in market["categories"]],
              sum(row["purchase_count"]
                  for row in market["categories"]),
              market["purchase_count"]))

    # -- AC-RPT5 the extremes and the top repeat buyer -----------------
    ok5 = (market["max_purchases"] == 3
           and market["top_repeat_buyer"] == "usr:bob"
           and dana["max_purchases"] == 2
           and dana["top_repeat_buyer"] == "usr:bob"
           and frank["max_purchases"] == 2
           and frank["top_repeat_buyer"] == "usr:dave"
           and gina["max_purchases"] == 0)
    record("AC-RPT5", ok5,
           "market_max=%d top=%r dana_top=%r frank_top=%r"
           % (market["max_purchases"], market["top_repeat_buyer"],
              dana["top_repeat_buyer"], frank["top_repeat_buyer"]))

    # -- AC-RPT6 the effective-category seam ---------------------------
    before = dumps(market)
    am.revise_category("usr:dana", d3, "data")
    moved = am.api_repeat_purchase()
    moved_cats = by_cat(moved)
    ok6 = (moved_cats["data"]["purchase_count"] == 3
           and moved_cats["data"]["buyer_count"] == 2
           and moved_cats["data"]["repeat_buyer_count"] == 1
           and moved_cats["data"]["repeat_purchase_count"] == 1
           and None not in moved_cats
           and moved["purchase_count"] == market["purchase_count"]
           and moved["buyer_count"] == market["buyer_count"]
           and moved["repeat_buyer_count"]
           == market["repeat_buyer_count"])
    am.revise_category("usr:dana", d3, None)
    restored = am.api_repeat_purchase()
    ok6 = ok6 and dumps(restored) == before
    record("AC-RPT6", ok6,
           "data_purchases=%d->%d unc_present=%r roundtrip=%r"
           % (data_row["purchase_count"],
              moved_cats["data"]["purchase_count"],
              None in moved_cats, dumps(restored) == before))

    # -- AC-RPT7 the gate family and the pure-read law -----------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    acct_codes = []
    for bad in ("", "u", "usr", 123, [], {"usr:x": 1}, False):
        try:
            am.api_repeat_purchase(bad)
            acct_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            acct_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_repeat_purchase("usr:")
    first = dumps(am.api_repeat_purchase("usr:frank"))
    second = dumps(am.api_repeat_purchase("usr:frank"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (acct_codes == ["E_AM_BAD_ACCOUNT"] * 7
           and prefix["buyer_count"] == 0
           and prefix["purchase_count"] == 0
           and prefix["categories"] == []
           and prefix["repeat_rate"] is None
           and first == second
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-RPT7", ok7,
           "acct=%r prefix_rows=%d repeat=%r frozen=%r tx=%r"
           % (acct_codes, prefix["buyer_count"], first == second,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-RPT8 cross-restart identity and the wiring ------------------
    final = dumps(am.api_repeat_purchase())
    final_dana = dumps(am.api_repeat_purchase("usr:dana"))
    final_gina = dumps(am.api_repeat_purchase("usr:gina"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_repeat_purchase())
    second_dana = dumps(am.api_repeat_purchase("usr:dana"))
    second_gina = dumps(am.api_repeat_purchase("usr:gina"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_repeat_purchase())
    third_dana = dumps(am.api_repeat_purchase("usr:dana"))
    third_gina = dumps(am.api_repeat_purchase("usr:gina"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_repeat_purchase()
        am.api_repeat_purchase("usr:dana")
        am.api_repeat_purchase("usr:gina")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (final == second_market == third_market
           and final_dana == second_dana == third_dana
           and final_gina == second_gina == third_gina
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-repeatpurchase" in runner_text)
    record("AC-RPT8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_market == third_market, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-repeatpurchase" in runner_text))

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