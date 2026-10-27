"""Acceptance suite for the apimarket watch-to-purchase conversion
funnel (BigDomain R2162; canon = the R2149 explore seed claimed in
R2162, criteria AC-WCV1..AC-WCV8 registered in that claim row BEFORE
this code existed - honesty law; the suite name, the runner label,
pre_owned_count and avg_convert_seconds were git-grep zero-occupancy
anchored against HEAD 2026-10-27, rc=1, while the AC-WCV and
api_watch_conversion occupancy comes from the seed row text itself).

Face under proof: APIMarketFace.api_watch_conversion. api_listing_demand
counts watchers and conversions per listing but publishes no rate, no
latency and no market or seller aggregate - and its conversion
predicate ignores ORDER, so a purchase stamped BEFORE the watch is
counted as a conversion. This suite pins the new face:

  - the fifteen-key envelope and the twelve-key rows, honest empty
    world first;
  - the DIRECTIONAL conversion law: a live watch converts only when
    the buyer's unrefunded purchase stamp is at or after the watch
    stamp, a purchase that predates the watch is pre_owned and leaves
    the funnel denominator, and a refund returns the watch to pending;
  - latency derived only from the two stored stamps (pooled average,
    median with the even-count midpoint, extremes, all None when
    nothing converted);
  - watch-side category rows on the one effective-category seam,
    uncategorized last, counters conserving the envelope, and the
    pinned non-additivity of the rate and of the pooled average;
  - scope: market-wide by default, one seller on request, strict
    seller isolation, an honest empty envelope for a seller with no
    watched listing, and additive counters across sellers;
  - retirement neither clearing a watch nor a conversion;
  - the bool-only include_uncategorized gate, the seven-form account
    gate, the pure-read law and cross-restart byte identity.

Usage: python test_apimarket_watchconversion.py
"""

import datetime
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
    "dev_account", "include_uncategorized", "watch_count",
    "pre_owned_count", "funnel_count", "converted_count",
    "pending_count", "conversion_rate", "avg_convert_seconds",
    "median_convert_seconds", "fastest_convert_seconds",
    "slowest_convert_seconds", "oldest_pending_watch_utc",
    "categories", "disclaimer"}

ROW_KEYS = {
    "category", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate",
    "avg_convert_seconds", "median_convert_seconds",
    "fastest_convert_seconds", "slowest_convert_seconds",
    "oldest_pending_watch_utc"}

COUNTERS = ("watch_count", "pre_owned_count", "funnel_count",
            "converted_count", "pending_count")

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")

T0 = datetime.datetime(2026, 11, 1, 0, 0, 0)


def ts(seconds):
    return (T0 + datetime.timedelta(seconds=seconds)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


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
    """dana owns d1/d2 in data and d3 uncategorized, frank owns f1/f2
    in tools, gina owns g1 in media. Watches and purchases are made
    through the public doors, then every stamp is rewritten to the
    deterministic T0 lattice so the latency figures are exact:

      data: bob watches d1 then buys it (+100s, converted), bob
            watches d2 and never buys (pending), carol buys d1 first
            and watches it later (+50s, pre_owned);
      tools: carol watches f1 then buys (+300s), erin watches f1 then
            buys (+601s after a +600 watch, converted in 1s), dave
            buys f2 first and watches later (+100s, pre_owned), bob
            watches f2 and never buys (pending);
      uncategorized: erin watches d3, buys it and refunds it, so the
            watch sits pending under the net law;
      media: gina's g1 is never watched at all.
    """
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-WCV-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-WCV-S",
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
    g1 = am.publish_api("usr:gina", "media-pack", "Media Pack API",
                        "media pipeline pack", PAYLOAD, 6, False,
                        category="media")["listing_id"]

    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    am.watch_api("usr:carol", d1)
    am.watch_api("usr:bob", d1)
    am.purchase_api("usr:bob", d1, "ref-bob-d1")
    am.watch_api("usr:bob", d2)
    am.watch_api("usr:carol", f1)
    am.purchase_api("usr:carol", f1, "ref-carol-f1")
    am.watch_api("usr:erin", f1)
    am.purchase_api("usr:erin", f1, "ref-erin-f1")
    am.purchase_api("usr:dave", f2, "ref-dave-f2")
    am.watch_api("usr:dave", f2)
    am.watch_api("usr:bob", f2)
    am.watch_api("usr:erin", d3)
    erin_d3 = am.purchase_api("usr:erin", d3, "ref-erin-d3")
    am.refund_api("usr:erin", erin_d3["purchase_id"],
                  "listing did not match description")

    conn = sqlite3.connect(am.db_path)
    lattice = [
        ("usr:bob", d1, 0, 100),
        ("usr:carol", d1, 50, 0),
        ("usr:bob", d2, 200, None),
        ("usr:carol", f1, 0, 300),
        ("usr:erin", f1, 600, 601),
        ("usr:dave", f2, 500, 400),
        ("usr:bob", f2, 700, None),
        ("usr:erin", d3, 0, 500),
    ]
    for buyer, listing_id, watch_s, buy_s in lattice:
        conn.execute("UPDATE apimarket_watchlist SET watched_utc = ?"
                     " WHERE buyer_id = ? AND listing_id = ?",
                     (ts(watch_s), buyer, listing_id))
        if buy_s is not None:
            conn.execute("UPDATE apimarket_purchases"
                         " SET purchased_utc = ?"
                         " WHERE buyer_id = ? AND listing_id = ?",
                         (ts(buy_s), buyer, listing_id))
    conn.commit()
    conn.close()
    return d1, d2, d3, f1, f2, g1


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-watchconversion-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d3, f1, f2, g1 = seed_world(led, dk, am)

    # -- AC-WCV1 the contract, honest empty first ----------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-wcv-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_watch_conversion()
    empty_seller = e_am.api_watch_conversion("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_watch_conversion()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in market["categories"])
    ok1 = (set(market.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and set(empty_seller.keys()) == ENVELOPE_KEYS
           and row_keys_ok
           and market["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["dev_account"] is None
           and empty["include_uncategorized"] is True
           and empty["watch_count"] == 0
           and empty["pre_owned_count"] == 0
           and empty["funnel_count"] == 0
           and empty["converted_count"] == 0
           and empty["pending_count"] == 0
           and empty["conversion_rate"] is None
           and empty["avg_convert_seconds"] is None
           and empty["median_convert_seconds"] is None
           and empty["fastest_convert_seconds"] is None
           and empty["slowest_convert_seconds"] is None
           and empty["oldest_pending_watch_utc"] is None
           and empty["categories"] == []
           and empty_seller["dev_account"] == "usr:nobody"
           and empty_seller["watch_count"] == 0
           and empty_seller["categories"] == [])
    record("AC-WCV1", ok1,
           "env_keys=%d exact=%r row_keys=%r cats=%d empty_cats=%d"
           % (len(market), set(market.keys()) == ENVELOPE_KEYS,
              row_keys_ok, len(market["categories"]),
              len(empty["categories"])))

    # -- AC-WCV2 the directional conversion law ------------------------
    ok2 = (market["watch_count"] == 8
           and market["pre_owned_count"] == 2
           and market["funnel_count"] == 6
           and market["converted_count"] == 3
           and market["pending_count"] == 3
           and market["watch_count"]
           == market["pre_owned_count"] + market["funnel_count"]
           and market["funnel_count"]
           == market["converted_count"] + market["pending_count"])
    demand = am.api_listing_demand("usr:dana")
    d1_demand = [r for r in demand["rows"]
                 if r["listing_id"] == d1][0]
    ok2 = ok2 and (d1_demand["converted_count"] == 2
                   and d1_demand["watcher_count"] == 2)
    record("AC-WCV2", ok2,
           "watch=%d pre=%d funnel=%d conv=%d pend=%d"
           " demand_d1_conv=%d"
           % (market["watch_count"], market["pre_owned_count"],
              market["funnel_count"], market["converted_count"],
              market["pending_count"], d1_demand["converted_count"]))

    # -- AC-WCV3 the latency readings ----------------------------------
    cats = by_cat(market)
    tools = cats["tools"]
    data_row = cats["data"]
    ok3 = (market["fastest_convert_seconds"] == 1
           and market["slowest_convert_seconds"] == 300
           and market["avg_convert_seconds"] == (100 + 300 + 1) / 3.0
           and market["median_convert_seconds"] == 100
           and tools["fastest_convert_seconds"] == 1
           and tools["slowest_convert_seconds"] == 300
           and tools["avg_convert_seconds"] == 150.5
           and tools["median_convert_seconds"] == 150.5
           and data_row["converted_count"] == 1
           and data_row["avg_convert_seconds"] == 100.0
           and data_row["median_convert_seconds"] == 100.0
           and data_row["fastest_convert_seconds"] == 100
           and data_row["slowest_convert_seconds"] == 100)
    record("AC-WCV3", ok3,
           "fast=%r slow=%r avg=%r median=%r tools=%r"
           % (market["fastest_convert_seconds"],
              market["slowest_convert_seconds"],
              market["avg_convert_seconds"],
              market["median_convert_seconds"],
              (tools["avg_convert_seconds"],
               tools["median_convert_seconds"])))

    # -- AC-WCV4 watch-side rows, conservation, non-additivity ---------
    order = [row["category"] for row in market["categories"]]
    unc = cats[None]
    row_rate_mean = sum(row["conversion_rate"]
                        for row in market["categories"]) / 3.0
    converted_rows = [row["avg_convert_seconds"]
                      for row in market["categories"]
                      if row["avg_convert_seconds"] is not None]
    row_avg_mean = sum(converted_rows) / len(converted_rows)
    ok4 = (order == ["data", "tools", None]
           and unc["watch_count"] == 1
           and unc["converted_count"] == 0
           and unc["pending_count"] == 1
           and unc["conversion_rate"] == 0.0
           and unc["avg_convert_seconds"] is None
           and unc["oldest_pending_watch_utc"] == ts(0)
           and all(sum(row[k] for row in market["categories"])
                   == market[k] for k in COUNTERS)
           and market["conversion_rate"] == 0.5
           and abs(row_rate_mean - market["conversion_rate"]) > 1e-9
           and abs(row_avg_mean
                   - market["avg_convert_seconds"]) > 1e-9
           and "media" not in cats)
    record("AC-WCV4", ok4,
           "order=%r sum_ok=%r rate=%r row_rate_mean=%r pool=%r"
           " row_avg_mean=%r"
           % (order,
              all(sum(row[k] for row in market["categories"])
                  == market[k] for k in COUNTERS),
              market["conversion_rate"], row_rate_mean,
              market["avg_convert_seconds"], row_avg_mean))

    # -- AC-WCV5 scope and strict seller isolation ---------------------
    dana = am.api_watch_conversion("usr:dana")
    frank = am.api_watch_conversion("usr:frank")
    gina = am.api_watch_conversion("usr:gina")
    ok5 = (dana["watch_count"] == 4
           and dana["pre_owned_count"] == 1
           and dana["funnel_count"] == 3
           and dana["converted_count"] == 1
           and dana["pending_count"] == 2
           and dana["conversion_rate"] == 1.0 / 3.0
           and dana["oldest_pending_watch_utc"] == ts(0)
           and frank["watch_count"] == 4
           and frank["pre_owned_count"] == 1
           and frank["converted_count"] == 2
           and frank["conversion_rate"] == 2.0 / 3.0
           and frank["oldest_pending_watch_utc"] == ts(700)
           and gina["watch_count"] == 0
           and gina["categories"] == []
           and gina["conversion_rate"] is None
           and all(dana[k] + frank[k] == market[k]
                   for k in COUNTERS))
    record("AC-WCV5", ok5,
           "dana=%r frank=%r gina=%d add_ok=%r"
           % ({k: dana[k] for k in COUNTERS},
              {k: frank[k] for k in COUNTERS},
              gina["watch_count"],
              all(dana[k] + frank[k] == market[k]
                  for k in COUNTERS)))

    # -- AC-WCV6 the effective-category seam ---------------------------
    before = dumps(market)
    am.revise_category("usr:dana", d3, "data")
    moved = am.api_watch_conversion()
    moved_cats = by_cat(moved)
    ok6 = (None not in moved_cats
           and moved_cats["data"]["watch_count"] == 4
           and moved_cats["data"]["pending_count"] == 2
           and moved_cats["data"]["oldest_pending_watch_utc"] == ts(0)
           and moved["watch_count"] == market["watch_count"]
           and moved["converted_count"] == market["converted_count"])
    am.revise_category("usr:dana", d3, None)
    restored = am.api_watch_conversion()
    ok6 = ok6 and dumps(restored) == before
    am.delist_api("usr:dana", d2)
    retired = dumps(am.api_watch_conversion())
    am.relist_api("usr:dana", d2)
    relisted = dumps(am.api_watch_conversion())
    ok6 = ok6 and retired == before and relisted == before
    record("AC-WCV6", ok6,
           "moved_data=%d unc_gone=%r roundtrip=%r"
           " retire_silent=%r relist_silent=%r"
           % (moved_cats["data"]["watch_count"], None not in moved_cats,
              dumps(restored) == before, retired == before,
              relisted == before))

    # -- AC-WCV7 the gate family and the pure-read law -----------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    acct_codes = []
    for bad in ("", "u", "usr", 123, [], {"usr:x": 1}, False):
        try:
            am.api_watch_conversion(bad)
            acct_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            acct_codes.append(getattr(exc, "code", "?"))
    args_codes = []
    for bad in (0, 1, None, "yes", []):
        try:
            am.api_watch_conversion(None, bad)
            args_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            args_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_watch_conversion("usr:")
    excluded = am.api_watch_conversion(None, False)
    first = dumps(am.api_watch_conversion("usr:frank"))
    second = dumps(am.api_watch_conversion("usr:frank"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (acct_codes == ["E_AM_BAD_ACCOUNT"] * 7
           and args_codes == ["E_AM_BAD_ARGS"] * 5
           and prefix["watch_count"] == 0
           and prefix["categories"] == []
           and excluded["include_uncategorized"] is False
           and excluded["watch_count"] == 7
           and excluded["pending_count"] == 2
           and None not in by_cat(excluded)
           and first == second
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-WCV7", ok7,
           "acct=%r args=%r prefix=%d excluded=%d frozen=%r tx=%r"
           % (acct_codes, args_codes, prefix["watch_count"],
              excluded["watch_count"],
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-WCV8 cross-restart identity and the wiring ------------------
    final = dumps(am.api_watch_conversion())
    final_dana = dumps(am.api_watch_conversion("usr:dana"))
    final_gina = dumps(am.api_watch_conversion("usr:gina"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_watch_conversion())
    second_dana = dumps(am.api_watch_conversion("usr:dana"))
    second_gina = dumps(am.api_watch_conversion("usr:gina"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_watch_conversion())
    third_dana = dumps(am.api_watch_conversion("usr:dana"))
    third_gina = dumps(am.api_watch_conversion("usr:gina"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_watch_conversion()
        am.api_watch_conversion("usr:dana")
        am.api_watch_conversion("usr:gina")
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
           and "ledger-apimarket-watchconversion" in runner_text)
    record("AC-WCV8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_market == third_market, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-watchconversion" in runner_text))

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