"""Acceptance suite for the apimarket shelf-to-sale velocity face
(BigDomain R2169; canon = the R2166 explore seed claimed in R2169,
criteria AC-LV1..AC-LV8 registered in that claim row BEFORE this code
existed - honesty law; the AC-LV prefix, test_apimarket_listingvelocity,
ledger-apimarket-listingvelocity, first_sale_utc, category_avg_seconds,
shelf_opened_utc, sold_count, unsold_count and market_avg_seconds were
all git-grep zero-occupancy anchored against HEAD 2026-10-28, rc=1; the
face-name occupancy is the seed row text, and opened_utc was already
taken by the claim chain, hence shelf_opened_utc).

Face under proof: APIMarketFace.api_listing_velocity. The market answers
event rows, one trade end to end, the cash month and the repricing
history - none of them answers how long a shelf sat before it sold.
This suite pins:

  - the thirteen-key envelope and eleven-key rows, honest empty first;
  - the cycle-opening start law (a sale inside a re-listed cycle is
    measured from that cycle's opening, a later re-listing never moves
    the measured elapsed time);
  - the net sale authority (a refunded-only purchase is UNSOLD, never a
    zero-second sale) and the sold + unsold partition;
  - elapsed seconds derived only from stored stamps, integer, clamped at
    zero for the disclosed out-of-order boundary;
  - the pooled average, the median (odd middle / even midpoint) and the
    fastest / slowest extremes with the listing_id tie-break;
  - the MARKET-scoped category and market benchmarks that stay
    comparable under a seller scope, and the one effective-category
    seam (revise_category moves a row and its bucket average together,
    and the round trip restores the bytes);
  - retirement after the sale, the seven-form account gate, the bare
    usr: prefix reading honestly empty, the pure-read law and
    cross-restart byte identity.

Usage: python test_apimarket_listingvelocity.py
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
    "dev_account", "listing_count", "sold_count", "unsold_count",
    "avg_seconds", "median_seconds", "fastest_seconds",
    "slowest_seconds", "fastest_listing_id", "slowest_listing_id",
    "market_avg_seconds", "rows", "disclaimer"}

ROW_KEYS = {
    "listing_id", "listing_key", "title", "category", "delisted",
    "current_price", "shelf_opened_utc", "first_sale_utc",
    "elapsed_seconds", "category_avg_seconds", "unsold"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")

LISTED = "2026-05-01T00:00:00Z"
D1_SALE = "2026-05-03T00:00:00Z"
D2_SALE = "2026-05-02T00:00:00Z"
D2_REFUND = "2026-05-04T00:00:00Z"
D3_SALE = "2026-05-05T00:00:00Z"
F1_DELIST = "2026-05-02T00:00:00Z"
F1_RELIST = "2026-06-01T00:00:00Z"
F1_SALE = "2026-06-03T00:00:00Z"
F2_SALE = "2026-05-11T00:00:00Z"
F4_LISTED = "2026-07-01T00:00:00Z"
F4_SALE = "2026-06-01T00:00:00Z"


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


def set_stamp(am, table, column, key_column, key, stamp):
    """Fixture setup only: every write door stamps the wall clock, and
    this face reads what the append-only tables store, so a
    deterministic duration grid needs fixed instants."""
    conn = sqlite3.connect(am.db_path)
    conn.execute("UPDATE " + table + " SET " + column + " = ?"
                 " WHERE " + key_column + " = ?", (stamp, key))
    conn.commit()
    conn.close()


def fund(led, who):
    led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:" + who, "credit", 400)],
               "manual:fund-" + who, "suite funding " + who)


def row_of(env, listing_id):
    for row in env["rows"]:
        if row["listing_id"] == listing_id:
            return row
    raise AssertionError("listing %r missing from rows" % (listing_id,))


def seed_world(led, dk, am):
    """dana owns d1 (data, sells in 2 days), d2 (data, the only
    purchase is refunded -> honestly unsold) and d3 (uncategorized,
    sells in 4 days). frank owns f1 (tools, sold only after a
    re-listing cycle so the start law is visible), f2 (tools, the
    slowest sale) and f4 (tools, a purchase backdated before the
    listing stamp, the clamp boundary). gina owns g1 (media, never
    sells)."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-LV-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-LV-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        fund(led, who)
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
    f4 = am.publish_api("usr:frank", "slow-kit", "Slow Kit API",
                        "late shelf payloads", PAYLOAD, 9, False,
                        category="tools")["listing_id"]

    for lid in (d1, d2, d3, f1, f2, g1):
        set_stamp(am, "apimarket_listings", "listed_utc",
                  "listing_id", lid, LISTED)
    set_stamp(am, "apimarket_listings", "listed_utc",
              "listing_id", f4, F4_LISTED)

    # f1 is retired before it ever sells, then re-listed: its sale
    # belongs to cycle 2 and must be measured from that opening.
    am.delist_api("usr:frank", f1)
    set_stamp(am, "apimarket_delistings", "delisted_utc",
              "listing_id", f1, F1_DELIST)
    am.relist_api("usr:frank", f1)
    set_stamp(am, "apimarket_relistings", "relisted_utc",
              "listing_id", f1, F1_RELIST)

    p_d1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")
    p_d2 = am.purchase_api("usr:bob", d2, "ref-bob-d2")
    p_d3 = am.purchase_api("usr:carol", d3, "ref-carol-d3")
    p_f1 = am.purchase_api("usr:dave", f1, "ref-dave-f1")
    p_f2 = am.purchase_api("usr:erin", f2, "ref-erin-f2")
    p_f4 = am.purchase_api("usr:dave", f4, "ref-dave-f4")

    for purchase, stamp in ((p_d1, D1_SALE), (p_d2, D2_SALE),
                            (p_d3, D3_SALE), (p_f1, F1_SALE),
                            (p_f2, F2_SALE), (p_f4, F4_SALE)):
        set_stamp(am, "apimarket_purchases", "purchased_utc",
                  "purchase_id", purchase["purchase_id"], stamp)

    am.refund_api("usr:bob", p_d2["purchase_id"],
                  "listing did not match description")
    set_stamp(am, "apimarket_refunds", "refunded_utc",
              "purchase_id", p_d2["purchase_id"], D2_REFUND)
    return d1, d2, d3, f1, f2, g1, f4


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-listingvelocity-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d3, f1, f2, g1, f4 = seed_world(led, dk, am)

    # -- AC-LV1 the contract, honest empty first ----------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-lv-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_listing_velocity()
    empty_seller = e_am.api_listing_velocity("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_listing_velocity()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in market["rows"])
    ok1 = (set(market.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and set(empty_seller.keys()) == ENVELOPE_KEYS
           and row_keys_ok
           and market["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["dev_account"] is None
           and empty["listing_count"] == 0
           and empty["sold_count"] == 0
           and empty["unsold_count"] == 0
           and empty["avg_seconds"] is None
           and empty["median_seconds"] is None
           and empty["fastest_seconds"] is None
           and empty["slowest_seconds"] is None
           and empty["fastest_listing_id"] is None
           and empty["slowest_listing_id"] is None
           and empty["market_avg_seconds"] is None
           and empty["rows"] == []
           and empty_seller["dev_account"] == "usr:nobody"
           and empty_seller["listing_count"] == 0
           and empty_seller["rows"] == [])
    record("AC-LV1", ok1,
           "env_keys=%d exact=%r row_keys=%r rows=%d empty_rows=%d"
           % (len(market), set(market.keys()) == ENVELOPE_KEYS,
              row_keys_ok, len(market["rows"]),
              len(empty["rows"])))

    # -- AC-LV2 the cycle-opening start law ----------------------------
    f1_row = row_of(market, f1)
    d1_row = row_of(market, d1)
    ok2 = (f1_row["shelf_opened_utc"] == F1_RELIST
           and f1_row["first_sale_utc"] == F1_SALE
           and f1_row["elapsed_seconds"] == 172800
           and d1_row["shelf_opened_utc"] == LISTED
           and d1_row["elapsed_seconds"] == 172800)
    record("AC-LV2", ok2,
           "f1_opened=%r f1_elapsed=%r d1_opened=%r d1_elapsed=%r"
           % (f1_row["shelf_opened_utc"], f1_row["elapsed_seconds"],
              d1_row["shelf_opened_utc"], d1_row["elapsed_seconds"]))

    # -- AC-LV3 net authority and the unsold partition -----------------
    d2_row = row_of(market, d2)
    dana = am.api_listing_velocity("usr:dana")
    ok3 = (d2_row["unsold"] is True
           and d2_row["first_sale_utc"] is None
           and d2_row["elapsed_seconds"] is None
           and d2_row["shelf_opened_utc"] is None
           and market["listing_count"] == 7
           and market["sold_count"] == 5
           and market["unsold_count"] == 2
           and market["sold_count"] + market["unsold_count"]
           == market["listing_count"]
           and dana["listing_count"] == 3
           and dana["sold_count"] == 2
           and dana["unsold_count"] == 1)
    record("AC-LV3", ok3,
           "d2_unsold=%r counts=%r dana=%r"
           % (d2_row["unsold"],
              (market["listing_count"], market["sold_count"],
               market["unsold_count"]),
              (dana["listing_count"], dana["sold_count"],
               dana["unsold_count"])))

    # -- AC-LV4 derivation and the clamp boundary ----------------------
    f4_row = row_of(market, f4)
    all_int = all(isinstance(r["elapsed_seconds"], int)
                  and not isinstance(r["elapsed_seconds"], bool)
                  and r["elapsed_seconds"] >= 0
                  for r in market["rows"]
                  if not r["unsold"])
    ok4 = (f4_row["elapsed_seconds"] == 0
           and f4_row["shelf_opened_utc"] == F4_LISTED
           and f4_row["first_sale_utc"] == F4_SALE
           and all_int)
    record("AC-LV4", ok4,
           "f4_elapsed=%r f4_opened=%r ints_non_negative=%r"
           % (f4_row["elapsed_seconds"], f4_row["shelf_opened_utc"],
              all_int))

    # -- AC-LV5 aggregates and extremes --------------------------------
    ok5 = (market["avg_seconds"] == 311040.0
           and market["median_seconds"] == 172800.0
           and market["fastest_seconds"] == 0
           and market["slowest_seconds"] == 864000
           and market["fastest_listing_id"] == f4
           and market["slowest_listing_id"] == f2
           and dana["avg_seconds"] == 259200.0
           and dana["median_seconds"] == 259200.0
           and dana["fastest_seconds"] == 172800
           and dana["fastest_listing_id"] == d1
           and dana["slowest_seconds"] == 345600
           and dana["slowest_listing_id"] == d3)
    record("AC-LV5", ok5,
           "market=%r dana=%r"
           % ({k: market[k] for k in ("avg_seconds",
                                      "median_seconds",
                                      "fastest_seconds",
                                      "slowest_seconds")},
              {k: dana[k] for k in ("avg_seconds", "median_seconds",
                                    "fastest_seconds",
                                    "slowest_seconds")}))

    # -- AC-LV6 market-scoped benchmarks and the category seam ---------
    gina = am.api_listing_velocity("usr:gina")
    tools_avg = (345600.0)
    pre = dumps(dana)
    ok6a = (d1_row["category_avg_seconds"] == 172800.0
            and row_of(market, d3)["category_avg_seconds"]
            == 345600.0
            and row_of(market, f2)["category_avg_seconds"] == tools_avg
            and row_of(gina, g1)["category_avg_seconds"] is None
            and dana["market_avg_seconds"] == market["avg_seconds"]
            == 311040.0)
    am.revise_category("usr:dana", d1, category="media")
    moved = am.api_listing_velocity("usr:dana")
    m_row = row_of(moved, d1)
    # media held only an unsold shelf, so after the move its sold pool
    # is exactly d1 (172800s) - a real bucket average, not a carried
    # value - while data keeps only an unsold shelf and honestly has
    # no average left.
    moved_ok = (m_row["category"] == "media"
                and m_row["category_avg_seconds"] == 172800.0
                and row_of(moved, d2)["category_avg_seconds"] is None)
    am.revise_category("usr:dana", d1, category="data")
    back = dumps(am.api_listing_velocity("usr:dana"))
    ok6 = ok6a and moved_ok and back == pre
    record("AC-LV6", ok6,
           "bench=%r moved=%r roundtrip=%r"
           % (ok6a, moved_ok, back == pre))

    # -- AC-LV7 lifecycle, gates, pure read ----------------------------
    before_rel = dumps(am.api_listing_velocity())
    am.delist_api("usr:frank", f2)
    set_stamp(am, "apimarket_delistings", "delisted_utc",
              "listing_id", f2, "2026-08-01T00:00:00Z")
    am.relist_api("usr:frank", f2)
    set_stamp(am, "apimarket_relistings", "relisted_utc",
              "listing_id", f2, "2026-09-01T00:00:00Z")
    after_rel = dumps(am.api_listing_velocity())
    f2_row = row_of(am.api_listing_velocity(), f2)
    relist_law = (before_rel == after_rel
                  and f2_row["elapsed_seconds"] == 864000
                  and f2_row["shelf_opened_utc"] == LISTED)
    am.delist_api("usr:dana", d1)
    set_stamp(am, "apimarket_delistings", "delisted_utc",
              "listing_id", d1, "2026-10-01T00:00:00Z")
    retired = am.api_listing_velocity("usr:dana")
    r_row = row_of(retired, d1)
    life_ok = (r_row["delisted"] is True
               and r_row["elapsed_seconds"] == 172800
               and retired["avg_seconds"] == 259200.0)

    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    acct_codes = []
    for bad in ("", "u", "usr", 123, [], {"usr:x": 1}, False):
        try:
            am.api_listing_velocity(bad)
            acct_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            acct_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_listing_velocity("usr:")
    first = dumps(am.api_listing_velocity("usr:frank"))
    second = dumps(am.api_listing_velocity("usr:frank"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (relist_law and life_ok
           and acct_codes == ["E_AM_BAD_ACCOUNT"] * 7
           and prefix["listing_count"] == 0
           and prefix["sold_count"] == 0
           and prefix["rows"] == []
           and prefix["avg_seconds"] is None
           and first == second
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-LV7", ok7,
           "relist_law=%r life=%r acct=%r prefix=%r frozen=%r tx=%r"
           % (relist_law, life_ok, acct_codes,
              prefix["listing_count"], digests_before == digests_after,
              tx_before == tx_after))

    # -- AC-LV8 cross-restart identity and the wiring ------------------
    final = dumps(am.api_listing_velocity())
    final_dana = dumps(am.api_listing_velocity("usr:dana"))
    final_gina = dumps(am.api_listing_velocity("usr:gina"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_listing_velocity())
    second_dana = dumps(am.api_listing_velocity("usr:dana"))
    second_gina = dumps(am.api_listing_velocity("usr:gina"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_listing_velocity())
    third_dana = dumps(am.api_listing_velocity("usr:dana"))
    third_gina = dumps(am.api_listing_velocity("usr:gina"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_listing_velocity()
        am.api_listing_velocity("usr:dana")
        am.api_listing_velocity("usr:gina")
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
           and "ledger-apimarket-listingvelocity" in runner_text)
    record("AC-LV8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_market == third_market, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-listingvelocity" in runner_text))

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