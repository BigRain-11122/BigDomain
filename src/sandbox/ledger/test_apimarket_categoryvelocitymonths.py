"""Acceptance suite for the apimarket per-category monthly velocity face
(BigDomain R2186; criteria AC-CVMT1..AC-CVMT8 were registered in the
R2186 explore-queue row BEFORE this code existed - honesty law; the
proposed AC-CVM prefix turned out to be occupied by the civicpoints
AC-CVM1..CVM7 family, 194 hits, so the prefix is AC-CVMT with zero
occupancy, and ledger-apimarket-categoryvelocitymonths,
peak_sale_count and sale_month_count were zero-occupancy as well).

Face under proof: APIMarketFace.api_category_velocity_months. The
existing faces answer a shelf once over its whole life
(api_listing_velocity), the asking price per month
(api_category_price_months) and the units left on the shelf
(api_category_supply_months) - none of them puts a sale on a calendar
month, so "is this category harder to sell this month than last month"
had no reading. This suite pins the new face:

  - the thirteen-key envelope, the thirteen-key month rows, the
    five-key category cells, the honest empty world and the bool gate;
  - the UTC month bucketing of each sale, the contiguous window over
    SALE months (a month with no sale is an honest zero row, which is
    deliberately not the catalog-event window of the price and supply
    faces) and the month-end second boundary;
  - the net authority: a refunded purchase leaves every count and
    aggregate and is never moved into the refund month;
  - the cycle-opening law: a sale inside a later cycle is measured
    from that cycle's re-listing stamp, never from the original one,
    and a re-listing after the sale cannot move the figure;
  - the per-month aggregates, the fastest/slowest tie-breaks, the
    conservation of sale counts across cells, rows and the envelope,
    and the honest None on a zero month;
  - the sale-instant category seam (a later revision never re-files
    history), the uncategorized filter and the bucket ordering;
  - the pure-read law with frozen table digests and a constant
    ledger_tx set;
  - cross-restart byte identity over three instances plus product-file
    and runner wiring.

Usage: python test_apimarket_categoryvelocitymonths.py
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
    "month_count", "first_month", "last_month", "sale_count",
    "listing_count", "category_count", "peak_month", "peak_sale_count",
    "month_over_month_change", "market_avg_seconds",
    "market_median_seconds", "disclaimer", "months"}

ROW_KEYS = {
    "month", "as_of", "sale_count", "listing_count", "category_count",
    "avg_seconds", "median_seconds", "fastest_seconds",
    "slowest_seconds", "fastest_listing_id", "slowest_listing_id",
    "market_avg_seconds", "categories"}

CELL_KEYS = {
    "category", "sale_count", "listing_count", "avg_seconds",
    "median_seconds"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions",
          "apimarket_supply_revisions")

FMT = "%Y-%m-%dT%H:%M:%SZ"


class Clock(object):
    """Deterministic stamp holder: the suite sets one explicit UTC
    string before each write so the month buckets are reproducible
    (module clock patched, restored in main's finally block)."""

    def __init__(self):
        self.value = "2026-01-05T00:00:00Z"

    def now_utc(self):
        return self.value


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def dumps(env):
    return json.dumps(env, sort_keys=True)


def secs(earlier, later):
    start = datetime.datetime.strptime(earlier, FMT)
    end = datetime.datetime.strptime(later, FMT)
    return int((end - start).total_seconds())


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


def by_month(env):
    return {row["month"]: row for row in env["months"]}


def cells_by_category(row):
    return {cell["category"]: cell for cell in row["categories"]}


def seed_world(led, dk, am, clock):
    """dana publishes three shelves in January: d1 (price 10, data),
    f1 (price 4, tools) and u1 (price 6, uncategorized). Sales land in
    February (d1 by bob, f1 by carol), April (u1 by dave, f1 by hal),
    June (f1 by erin and by faye at the month's last second) and July
    (f1 by bob
    at the month's first second, d1 by gus). Bob's February d1
    purchase is refunded on 2026-04-25, so February must keep carol's
    sale only and never grow a data cell. f1 is retired on 2026-05-02
    and re-listed on 2026-05-20, so the June and July f1 sales are
    measured from that re-listing. d1 is re-filed from data to data2 on
    2026-06-01, so gus in July is a data2 sale while the February d1
    sale (already refunded anyway) never appears under data2. An August
    price revision must NOT extend the window, which ends on the last
    sale month."""
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-CVMT-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-CVMT-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin", "faye", "gus", "hal"):
        fund(led, who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    clock.value = "2026-01-05T00:00:00Z"
    d1 = am.publish_api("usr:dana", "scan-api", "Scan API",
                        "portfolio scan endpoint", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    f1 = am.publish_api("usr:dana", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 4,
                        False, category="tools")["listing_id"]
    u1 = am.publish_api("usr:dana", "loose-pack", "Loose Pack API",
                        "uncategorized payload pack", PAYLOAD, 6,
                        False)["listing_id"]
    clock.value = "2026-02-10T12:00:00Z"
    refund_me = am.purchase_api("usr:bob", d1, "ref-bob-d1")
    clock.value = "2026-02-20T12:00:00Z"
    am.purchase_api("usr:carol", f1, "ref-carol-f1")
    clock.value = "2026-04-10T12:00:00Z"
    am.purchase_api("usr:dave", u1, "ref-dave-u1")
    clock.value = "2026-04-15T12:00:00Z"
    am.purchase_api("usr:hal", f1, "ref-hal-f1")
    clock.value = "2026-04-25T12:00:00Z"
    am.refund_api("usr:bob", refund_me["purchase_id"],
                  "listing did not match description")
    clock.value = "2026-05-02T12:00:00Z"
    am.delist_api("usr:dana", f1)
    clock.value = "2026-05-20T12:00:00Z"
    am.relist_api("usr:dana", f1)
    clock.value = "2026-06-01T12:00:00Z"
    am.revise_category("usr:dana", d1, "data2")
    clock.value = "2026-06-20T12:00:00Z"
    am.purchase_api("usr:erin", f1, "ref-erin-f1")
    clock.value = "2026-06-30T23:59:59Z"
    am.purchase_api("usr:faye", f1, "ref-faye-f1")
    clock.value = "2026-07-01T00:00:00Z"
    am.purchase_api("usr:bob", f1, "ref-bob-f1")
    clock.value = "2026-07-02T12:00:00Z"
    am.purchase_api("usr:gus", d1, "ref-gus-d1")
    clock.value = "2026-08-03T12:00:00Z"
    am.revise_price("usr:dana", d1, 11)
    return d1, f1, u1


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-cvmt-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    clock = Clock()
    orig_now = A._now_utc
    A._now_utc = clock.now_utc
    try:
        return run(db_path, cfg, lobby_cfg, shas_before, clock)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, shas_before, clock):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, f1, u1 = seed_world(led, dk, am, clock)

    # -- AC-CVMT1 the contract, the honest empty world, the bool gate
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-cvmt-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_category_velocity_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_category_velocity_months()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in market["months"])
    cell_keys_ok = all(set(cell.keys()) == CELL_KEYS
                       for row in market["months"]
                       for cell in row["categories"])
    gate_forms = []
    for bad in (0, 1, "", "yes", None, [], {}, 1.0):
        try:
            am.api_category_velocity_months(bad)
            gate_forms.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            gate_forms.append(str(exc).split(":")[0].strip())
    ok1 = (set(market.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and row_keys_ok and cell_keys_ok
           and market["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["sale_count"] == 0
           and empty["listing_count"] == 0
           and empty["category_count"] == 0
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["peak_month"] is None
           and empty["peak_sale_count"] is None
           and empty["month_over_month_change"] is None
           and empty["market_avg_seconds"] is None
           and empty["market_median_seconds"] is None
           and empty["months"] == []
           and gate_forms == ["E_AM_BAD_ARGS"] * 8)
    record("AC-CVMT1", ok1,
           "env_keys=%d exact=%r row_keys=%r cell_keys=%r empty=%r"
           " gate=%r"
           % (len(market), set(market.keys()) == ENVELOPE_KEYS,
              row_keys_ok, cell_keys_ok, empty["months"], gate_forms))

    # -- AC-CVMT2 the sale-month window, the boundary, the catalog----
    # window runs over SALE months only: February through July is
    # contiguous (March and May sell nothing and stay as honest zero
    # rows), while the August price revision must not extend it.
    bm = by_month(market)
    as_of_ok = all(
        bm[m]["as_of"] == as_of for m, as_of in (
            ("2026-02", "2026-02-28T23:59:59Z"),
            ("2026-03", "2026-03-31T23:59:59Z"),
            ("2026-04", "2026-04-30T23:59:59Z"),
            ("2026-05", "2026-05-31T23:59:59Z"),
            ("2026-06", "2026-06-30T23:59:59Z"),
            ("2026-07", "2026-07-31T23:59:59Z")))
    ok2 = (market["month_count"] == 6
           and [row["month"] for row in market["months"]]
           == ["2026-02", "2026-03", "2026-04", "2026-05",
               "2026-06", "2026-07"]
           and market["first_month"] == "2026-02"
           and market["last_month"] == "2026-07"
           and as_of_ok
           and bm["2026-03"]["sale_count"] == 0
           and bm["2026-05"]["sale_count"] == 0
           and bm["2026-03"]["avg_seconds"] is None
           and bm["2026-05"]["median_seconds"] is None
           and bm["2026-03"]["categories"] == []
           and bm["2026-06"]["sale_count"] == 2
           and bm["2026-07"]["sale_count"] == 2)
    record("AC-CVMT2", ok2,
           "months=%r zero_months=%r price_rev_excluded=%r"
           % ([row["month"] for row in market["months"]],
              [m for m in bm if bm[m]["sale_count"] == 0],
              market["last_month"] == "2026-07"))

    # -- AC-CVMT3 the net authority --------------------------------
    # bob's February d1 purchase is refunded, so it leaves every count
    # and aggregate, and it is never moved into the refund month: April
    # carries only dave's u1 sale, and February keeps carol's tools
    # sale with no data cell at all.
    feb_cells = cells_by_category(bm["2026-02"])
    apr_cells = cells_by_category(bm["2026-04"])
    ok3 = (bm["2026-02"]["sale_count"] == 1
           and feb_cells.get("data") is None
           and feb_cells["tools"]["sale_count"] == 1
           and bm["2026-04"]["sale_count"] == 2
           and apr_cells[None]["sale_count"] == 1
           and apr_cells["tools"]["sale_count"] == 1
           and "data" not in apr_cells
           and bm["2026-02"]["listing_count"] == 1
           and bm["2026-04"]["listing_count"] == 2
           and market["sale_count"] == 7)
    record("AC-CVMT3", ok3,
           "feb=%r apr_cells=%r total=%r"
           % (sorted(feb_cells, key=str), sorted(apr_cells, key=str),
              market["sale_count"]))

    # -- AC-CVMT4 the cycle-opening law ----------------------------
    # carol's February f1 sale opens at the January publish stamp;
    # erin, faye and bob all sell on f1's SECOND cycle, so they are
    # measured from the 2026-05-20 re-listing and never from January.
    carol_expected = secs("2026-01-05T00:00:00Z", "2026-02-20T12:00:00Z")
    erin_expected = secs("2026-05-20T12:00:00Z", "2026-06-20T12:00:00Z")
    faye_expected = secs("2026-05-20T12:00:00Z",
                         "2026-06-30T23:59:59Z")
    bob_expected = secs("2026-05-20T12:00:00Z",
                        "2026-07-01T00:00:00Z")
    gus_expected = secs("2026-01-05T00:00:00Z", "2026-07-02T12:00:00Z")
    ok4 = (cells_by_category(bm["2026-02"])["tools"]["avg_seconds"]
           == float(carol_expected)
           and bm["2026-06"]["slowest_seconds"] == faye_expected
           and bm["2026-06"]["fastest_seconds"] == erin_expected
           and bm["2026-07"]["fastest_seconds"] == bob_expected
           and cells_by_category(bm["2026-07"])["data2"]["avg_seconds"]
           == float(gus_expected)
           and erin_expected < carol_expected
           and bob_expected - faye_expected == 1)
    record("AC-CVMT4", ok4,
           "carol=%r erin=%r faye=%r bob=%r gus=%r"
           % (carol_expected, erin_expected, faye_expected,
              bob_expected, gus_expected))

    # -- AC-CVMT5 aggregates, tie-breaks and conservation ----------
    jun = bm["2026-06"]
    jun_durations = sorted([erin_expected, faye_expected])
    jun_avg = float(sum(jun_durations)) / 2.0
    jun_median = (jun_durations[0] + jun_durations[1]) / 2.0

    ok5 = (jun["avg_seconds"] == jun_avg
           and jun["median_seconds"] == jun_median
           and jun["sale_count"]
           == sum(c["sale_count"] for c in jun["categories"])
           and all(row["sale_count"]
                   == sum(c["sale_count"] for c in row["categories"])
                   for row in market["months"])
           and market["sale_count"]
           == sum(row["sale_count"] for row in market["months"])
           and market["market_avg_seconds"]
           == float(sum([carol_expected, secs(
               "2026-01-05T00:00:00Z", "2026-04-10T12:00:00Z"),
               secs("2026-01-05T00:00:00Z", "2026-04-15T12:00:00Z"),
               erin_expected, faye_expected, bob_expected,
               gus_expected])) / 7.0
           and market["peak_month"] == "2026-04"
           and market["peak_sale_count"] == 2
           and market["month_over_month_change"] == 0
           and all(row["market_avg_seconds"]
                   == market["market_avg_seconds"]
                   for row in market["months"])
           and bm["2026-03"]["fastest_seconds"] is None
           and bm["2026-03"]["fastest_listing_id"] is None)
    record("AC-CVMT5", ok5,
           "jun_avg=%r jun_median=%r peak=%r mom=%r market_avg=%r"
           % (jun["avg_seconds"], jun["median_seconds"],
              market["peak_month"], market["month_over_month_change"],
              market["market_avg_seconds"]))

    # -- AC-CVMT6 the sale-instant bucket, the filter, the order ---
    july_cells = cells_by_category(bm["2026-07"])
    filtered = am.api_category_velocity_months(False)
    fbm = by_month(filtered)
    ok6 = ("data" not in july_cells
           and "data2" in july_cells
           and sorted(july_cells) == ["data2", "tools"]
           and [c["category"] for c in bm["2026-07"]["categories"]]
           == ["data2", "tools"]
           and [c["category"] for c in bm["2026-04"]["categories"]]
           == ["tools", None]
           and filtered["sale_count"] == 6
           and filtered["listing_count"] == 2
           and filtered["category_count"] == 2
           and filtered["market_avg_seconds"] == float(sum(
               [carol_expected,
                secs("2026-01-05T00:00:00Z", "2026-04-15T12:00:00Z"),
                erin_expected, faye_expected,
                bob_expected, gus_expected])) / 6.0
           and fbm["2026-04"]["sale_count"] == 1
           and fbm["2026-03"]["sale_count"] == 0
           and fbm["2026-03"]["categories"] == []
           and all(c["category"] is not None
                   for row in filtered["months"]
                   for c in row["categories"]))
    record("AC-CVMT6", ok6,
           "july_buckets=%r filtered_sale=%r filtered_cat=%r"
           % ([c["category"] for c in bm["2026-07"]["categories"]],
              filtered["sale_count"], filtered["category_count"]))

    # -- AC-CVMT7 the pure-read law -------------------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    first = dumps(am.api_category_velocity_months())
    second = dumps(am.api_category_velocity_months())
    third = dumps(am.api_category_velocity_months(True))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (first == second == third
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-CVMT7", ok7,
           "identical=%r frozen=%r tx=%r sha16=%s"
           % (first == second == third, digests_before == digests_after,
              tx_before == tx_after,
              hashlib.sha256(first.encode("utf-8")).hexdigest()[:16]))

    # -- AC-CVMT8 cross-restart identity and the wiring ------------
    final = dumps(am.api_category_velocity_months())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_category_velocity_months())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_category_velocity_months())
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_category_velocity_months()
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (final == second_market == third_market
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-categoryvelocitymonths" in runner_text)
    record("AC-CVMT8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_market == third_market, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-categoryvelocitymonths" in runner_text))

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