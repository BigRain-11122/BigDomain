"""Acceptance suite for the apimarket seller repricing-discipline face
(BigDomain R2171; canon = the R2171 explore claim row, criteria
AC-PVC1..AC-PVC8 registered in that row BEFORE this code existed -
honesty law; the AC-PVC prefix, api_price_volatility,
test_apimarket_pricevolatility, ledger-apimarket-pricevolatility,
avg_reprice_pct and repricing_sellers were all git-grep zero-occupancy
anchored against HEAD 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_price_volatility. Every existing
price face is a snapshot cross-section (api_price_history per listing,
api_listing_position inside a category, api_market_price_percentiles
across live asking prices, api_listing_velocity on shelf life). None of
them answers how often a seller reprices, by how much, up or down, and
whether that magnitude is sane next to the market. This suite pins:

  - the fifteen-key envelope and nine-key rows, honest empty first;
  - the repricing-side row authority (a listing with live stock but no
    revision does not appear) and the total order
    (-revision_count, -abs(total_pct), listing_id ascending);
  - the magnitude law (each step and the row total derived only from
    two stored prices) and the per-row conservation
    revision_count == up_count + down_count;
  - the pooled aggregation law (mean of steps, median odd-middle or
    even-midpoint, max by absolute value keeping the sign, signed sum)
    with None instead of a fabricated 0.0;
  - the scope law (market scope carries no self-benchmark, a seller
    scope carries the market-wide pooled average, strict isolation,
    a never-repricing seller reads honestly empty);
  - cross-face same source (api_price_history agrees per row) and the
    invariances (purchase, delist/relist and a foreign repricing do not
    move other rows);
  - the seven-form account gate, the pure-read law and cross-restart
    byte identity.

Usage: python test_apimarket_pricevolatility.py
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
    "dev_account", "scope", "listing_count", "repriced_listing_count",
    "revision_count", "up_count", "down_count", "net_direction_pct",
    "avg_reprice_pct", "median_reprice_pct", "max_reprice_pct",
    "market_avg_reprice_pct", "most_repriced_listing", "disclaimer",
    "rows"}

ROW_KEYS = {
    "listing_id", "listing_key", "title", "revision_count",
    "up_count", "down_count", "base_price", "current_price",
    "total_pct"}

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


def row_of(env, listing_id):
    for row in env["rows"]:
        if row["listing_id"] == listing_id:
            return row
    raise AssertionError("listing %r missing from rows" % (listing_id,))


def seed_world(led, dk, am):
    """dana reprices a1 twice (one up, one down) and a2 once (up);
    frank publishes but never reprices, so f1 must stay absent; gina
    makes three steps (up, down, up) so the six pooled steps give an
    even count and exercise the median midpoint."""
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-PVC-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-PVC-S",
                     "settlement")
    for who in ("bob", "carol"):
        fund(led, who)
    for dev in ("dana", "frank", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    a1 = am.publish_api("usr:dana", "a1", "Alpha API",
                        "alpha payloads", PAYLOAD, 10,
                        False)["listing_id"]
    a2 = am.publish_api("usr:dana", "a2", "Beta API",
                        "beta payloads", PAYLOAD, 20,
                        False)["listing_id"]
    f1 = am.publish_api("usr:frank", "f1", "Frank One API",
                        "frank payloads", PAYLOAD, 50,
                        False)["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina One API",
                        "gina payloads", PAYLOAD, 4,
                        False)["listing_id"]

    am.revise_price("usr:dana", a1, 12)
    am.revise_price("usr:dana", a1, 9)
    am.revise_price("usr:dana", a2, 30)
    am.revise_price("usr:gina", g1, 5)
    am.revise_price("usr:gina", g1, 3)
    am.revise_price("usr:gina", g1, 6)
    return {"a1": a1, "a2": a2, "f1": f1, "g1": g1}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-pricevolatility-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    ids = seed_world(led, dk, am)

    # -- AC-PVC1 the contract, honest empty first ---------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-pvc-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_price_volatility()
    empty_seller = e_am.api_price_volatility("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_price_volatility()
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
           and empty["repriced_listing_count"] == 0
           and empty["revision_count"] == 0
           and empty["up_count"] == 0
           and empty["down_count"] == 0
           and empty["rows"] == []
           and empty["net_direction_pct"] is None
           and empty["avg_reprice_pct"] is None
           and empty["median_reprice_pct"] is None
           and empty["max_reprice_pct"] is None
           and empty["market_avg_reprice_pct"] is None
           and empty["most_repriced_listing"] is None
           and empty_seller["rows"] == []
           and empty_seller["avg_reprice_pct"] is None)
    record("AC-PVC1", ok1,
           "keys=%d rowkeys=%r empty=%r empty_seller_rows=%r"
           % (len(market), row_keys_ok,
              (empty["revision_count"], empty["rows"],
               empty["avg_reprice_pct"]),
              empty_seller["rows"]))

    # -- AC-PVC2 row authority and the total order --------------------
    order_ids = [row["listing_id"] for row in market["rows"]]
    ok2 = (ids["f1"] not in order_ids
           and order_ids == [ids["g1"], ids["a1"], ids["a2"]]
           and market["listing_count"] == 4
           and market["repriced_listing_count"] == 3
           and market["repriced_listing_count"] == len(market["rows"])
           and market["most_repriced_listing"] == ids["g1"]
           and row_of(market, ids["g1"])["revision_count"] == 3
           and row_of(market, ids["a1"])["revision_count"] == 2
           and row_of(market, ids["a2"])["revision_count"] == 1)
    record("AC-PVC2", ok2,
           "order=%r f1_absent=%r listing_count=%d most=%r"
           % (order_ids, ids["f1"] not in order_ids,
              market["listing_count"], market["most_repriced_listing"]))

    # -- AC-PVC3 the magnitude law -----------------------------------
    r_a1 = row_of(market, ids["a1"])
    r_a2 = row_of(market, ids["a2"])
    r_g1 = row_of(market, ids["g1"])
    ok3 = (r_a1["base_price"] == 10 and r_a1["current_price"] == 9
           and r_a1["total_pct"] == -10.0
           and r_a1["up_count"] == 1 and r_a1["down_count"] == 1
           and r_a2["base_price"] == 20 and r_a2["current_price"] == 30
           and r_a2["total_pct"] == 50.0
           and r_a2["up_count"] == 1 and r_a2["down_count"] == 0
           and r_g1["base_price"] == 4 and r_g1["current_price"] == 6
           and r_g1["total_pct"] == 50.0
           and r_g1["up_count"] == 2 and r_g1["down_count"] == 1
           and r_g1["listing_key"] == "g1"
           and r_g1["title"] == "Gina One API")
    record("AC-PVC3", ok3,
           "a1=%r a2=%r g1=%r"
           % ((r_a1["base_price"], r_a1["current_price"],
               r_a1["total_pct"]), (r_a2["total_pct"],),
              (r_g1["total_pct"], r_g1["up_count"],
               r_g1["down_count"])))

    # -- AC-PVC4 conservation and the pooled aggregation law ----------
    per_row_ok = all(row["revision_count"]
                     == row["up_count"] + row["down_count"]
                     for row in market["rows"])
    ok4 = (per_row_ok
           and market["revision_count"] == 6
           and market["revision_count"] == sum(
               row["revision_count"] for row in market["rows"])
           and market["up_count"] == 4
           and market["down_count"] == 2
           and market["up_count"] + market["down_count"] == 6
           and market["net_direction_pct"] == 130.0
           and market["avg_reprice_pct"] == 21.67
           and market["median_reprice_pct"] == 22.5
           and market["max_reprice_pct"] == 100.0)
    record("AC-PVC4", ok4,
           "per_row=%r rev=%d up=%d down=%d net=%r avg=%r med=%r"
           " max=%r"
           % (per_row_ok, market["revision_count"],
              market["up_count"], market["down_count"],
              market["net_direction_pct"], market["avg_reprice_pct"],
              market["median_reprice_pct"],
              market["max_reprice_pct"]))

    # -- AC-PVC5 the scope law and the benchmark ----------------------
    dana = am.api_price_volatility("usr:dana")
    frank = am.api_price_volatility("usr:frank")
    dana_ids = [row["listing_id"] for row in dana["rows"]]
    frank_rows = frank["rows"]
    ok5 = (market["scope"] == "market"
           and market["market_avg_reprice_pct"] is None
           and dana["scope"] == "seller"
           and dana["market_avg_reprice_pct"]
           == market["avg_reprice_pct"] == 21.67
           and dana["listing_count"] == 2
           and dana["repriced_listing_count"] == 2
           and dana_ids == [ids["a1"], ids["a2"]]
           and dana["revision_count"] == 3
           and dana["up_count"] == 2
           and dana["down_count"] == 1
           and dana["net_direction_pct"] == 45.0
           and dana["avg_reprice_pct"] == 15.0
           and dana["median_reprice_pct"] == 20.0
           and dana["max_reprice_pct"] == 50.0
           and dana["most_repriced_listing"] == ids["a1"]
           and frank["rows"] == frank_rows == []
           and frank["listing_count"] == 1
           and frank["repriced_listing_count"] == 0
           and frank["revision_count"] == 0
           and frank["avg_reprice_pct"] is None
           and frank["market_avg_reprice_pct"] == 21.67)
    record("AC-PVC5", ok5,
           "market_scope=%r dana=%r benchmark=%r frank=%r"
           % (market["scope"], (dana["revision_count"],
                               dana["avg_reprice_pct"],
                               dana["median_reprice_pct"]),
              dana["market_avg_reprice_pct"], frank_rows))

    # -- AC-PVC6 cross-face same source and the invariances -----------
    history_ok = True
    for row in market["rows"]:
        hist = am.api_price_history(row["listing_id"])
        if (hist["revision_count"] != row["revision_count"]
                or hist["current_price"] != row["current_price"]
                or hist["base_price"] != row["base_price"]):
            history_ok = False
    snapshot = dumps(market)
    am.purchase_api("usr:bob", ids["g1"], "ref-pvc-bob-g1")
    after_buy = dumps(am.api_price_volatility())
    am.delist_api("usr:frank", ids["f1"])
    after_delist = dumps(am.api_price_volatility())
    am.relist_api("usr:frank", ids["f1"])
    after_relist = dumps(am.api_price_volatility())
    before_move = am.api_price_volatility()
    am.revise_price("usr:dana", ids["a2"], 33)
    after_move = am.api_price_volatility()
    untouched = all(
        row_of(after_move, lid) == row_of(before_move, lid)
        for lid in (ids["a1"], ids["g1"]))
    ok6 = (history_ok
           and after_buy == snapshot
           and after_delist == snapshot
           and after_relist == snapshot
           and untouched
           and row_of(after_move, ids["a2"])["total_pct"] == 65.0
           and after_move["revision_count"] == 7)
    record("AC-PVC6", ok6,
           "history=%r buy=%r delist=%r relist=%r untouched=%r"
           " moved_total=%r"
           % (history_ok, after_buy == snapshot,
              after_delist == snapshot, after_relist == snapshot,
              untouched, row_of(after_move, ids["a2"])["total_pct"]))

    # -- AC-PVC7 the gate family and the pure read -------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    acct_codes = []
    for bad in ("", "u", "usr", 123, [], {"usr:x": 1}, False):
        try:
            am.api_price_volatility(bad)
            acct_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            acct_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_price_volatility("usr:")
    fresh = am.api_price_volatility()
    twice = am.api_price_volatility()
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (acct_codes == ["E_AM_BAD_ACCOUNT"] * 7
           and prefix["revision_count"] == 0
           and prefix["rows"] == []
           and prefix["avg_reprice_pct"] is None
           and fresh == twice
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-PVC7", ok7,
           "acct=%r prefix=%r idem=%r frozen=%r tx=%r"
           % (acct_codes, prefix["revision_count"], fresh == twice,
              digests_before == digests_after,
              tx_before == tx_after))

    # -- AC-PVC8 cross-restart identity and the wiring ---------------
    final_market = dumps(am.api_price_volatility())
    final_dana = dumps(am.api_price_volatility("usr:dana"))
    final_frank = dumps(am.api_price_volatility("usr:frank"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_price_volatility())
    second_dana = dumps(am.api_price_volatility("usr:dana"))
    second_frank = dumps(am.api_price_volatility("usr:frank"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_price_volatility())
    third_dana = dumps(am.api_price_volatility("usr:dana"))
    third_frank = dumps(am.api_price_volatility("usr:frank"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_price_volatility()
        am.api_price_volatility("usr:dana")
        am.api_price_volatility("usr:frank")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    with open(os.path.abspath(__file__), "rb") as handle:
        suite_text = handle.read().decode("utf-8")
    # the needle is assembled so this very assertion line is not a
    # self-referential hit (R1678 lesson).
    net_needle = "import " + "socket"
    ok8 = (final_market == second_market == third_market
           and final_dana == second_dana == third_dana
           and final_frank == second_frank == third_frank
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-pricevolatility" in runner_text
           and all(ord(ch) < 128 for ch in suite_text)
           and net_needle not in suite_text)
    record("AC-PVC8", ok8,
           "sha16=%s identical=%r frozen=%r files_equal=%r"
           " registered=%r ascii=%r"
           % (hashlib.sha256(final_market.encode("utf-8"))
              .hexdigest()[:16],
              final_market == second_market == third_market,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-pricevolatility" in runner_text,
              all(ord(ch) < 128 for ch in suite_text)))

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