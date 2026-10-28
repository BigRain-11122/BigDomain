"""Acceptance suite for the apimarket category supply trend face
(BigDomain R2182; criteria AC-CSM1..AC-CSM8 were registered in the
R2182 explore-queue row BEFORE this code existed - honesty law; the
AC-CSM prefix, api_category_supply_months,
test_apimarket_categorysupplymonths, ledger-apimarket-categorysupply
months, peak_live_listing_count and _supply_at_instant were all
git-grep zero-occupancy anchored against HEAD 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_category_supply_months. Every
other catalog face is a snapshot (api_categories reports the current
live/retired split and price band), and api_category_price_months
answers how the ASKING PRICE moved rather than how much of the
category was still on sale. This suite pins the new face, the
point-in-time rebuild of each category's supply at every UTC month end:

  - the ten-key envelope, the nine-key month rows, the six-key bucket
    cells, the honest empty world and the bool gate;
  - the month-end sampling law (as_of = the month's last second) and
    the contiguous window, including the disclosed asymmetry that a
    price revision is not a supply event;
  - the cycle law on the time axis (retired listings honestly absent,
    re-listed ones present again);
  - the supply arithmetic at an instant: a purchase counts from its
    own stamp, a restock adds from its own stamp, a refund hands its
    unit back, and an unlimited shelf never reports units or sold out;
  - three-way conservation, bucket ordering, the uncategorized filter,
    the honest zero month and the trend extremes;
  - the pure-read law with frozen table digests and a constant
    ledger_tx set;
  - cross-restart byte identity over three instances plus product-file
    and runner wiring.

Usage: python test_apimarket_categorysupplymonths.py
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
    "month_count", "first_month", "last_month", "listing_count",
    "category_count", "peak_month", "peak_live_listing_count",
    "month_over_month_change", "disclaimer", "months"}

ROW_KEYS = {
    "month", "as_of", "live_listing_count", "category_count",
    "in_stock_listing_count", "sold_out_listing_count",
    "unlimited_listing_count", "remaining_units", "categories"}

CELL_KEYS = {
    "category", "live_listing_count", "in_stock_listing_count",
    "sold_out_listing_count", "unlimited_listing_count",
    "remaining_units"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions",
          "apimarket_supply_revisions")


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
    """dana publishes three shelves in January: d1 (price 10, supply 2,
    data), f1 (price 4, unlimited, tools) and u1 (price 6, supply 1,
    uncategorized). February bob buys one d1 unit. March dana restocks
    d1 by three and bob is refunded. April carol buys the single u1
    unit, so that shelf is honestly sold out from April's month end.
    May dana retires f1; June she re-lists it and re-files d1 from data
    to data2. A July price revision is planted to prove a price move is
    NOT a supply event, so the window must still end in June."""
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-CSM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-CSM-S",
                     "settlement")
    for who in ("bob", "carol"):
        fund(led, who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    clock.value = "2026-01-05T00:00:00Z"
    d1 = am.publish_api("usr:dana", "scan-api", "Scan API",
                        "portfolio scan endpoint", PAYLOAD, 10,
                        False, supply=2, category="data")["listing_id"]
    f1 = am.publish_api("usr:dana", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 4,
                        False, category="tools")["listing_id"]
    u1 = am.publish_api("usr:dana", "loose-pack", "Loose Pack API",
                        "uncategorized payload pack", PAYLOAD, 6,
                        False, supply=1)["listing_id"]
    clock.value = "2026-02-10T00:00:00Z"
    purchase = am.purchase_api("usr:bob", d1, "ref-bob-d1")
    clock.value = "2026-03-05T00:00:00Z"
    am.restock_api("usr:dana", d1, 3)
    clock.value = "2026-03-20T00:00:00Z"
    am.refund_api("usr:bob", purchase["purchase_id"],
                  "listing did not match description")
    clock.value = "2026-04-10T00:00:00Z"
    am.purchase_api("usr:carol", u1, "ref-carol-u1")
    clock.value = "2026-05-02T00:00:00Z"
    am.delist_api("usr:dana", f1)
    clock.value = "2026-06-01T00:00:00Z"
    am.relist_api("usr:dana", f1)
    clock.value = "2026-06-15T00:00:00Z"
    am.revise_category("usr:dana", d1, "data2")
    clock.value = "2026-07-10T00:00:00Z"
    am.revise_price("usr:dana", d1, 11)
    return d1, f1, u1


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-csm-")
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

    # -- AC-CSM1 the contract, honest empty, the bool gate -----------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-csm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_category_supply_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_category_supply_months()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in market["months"])
    cell_keys_ok = all(set(cell.keys()) == CELL_KEYS
                       for row in market["months"]
                       for cell in row["categories"])
    gate_forms = []
    for bad in (0, 1, "", "yes", None, [], {}, 1.0):
        try:
            am.api_category_supply_months(bad)
            gate_forms.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            gate_forms.append(str(exc).split(":")[0].strip())
    ok1 = (set(market.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and row_keys_ok and cell_keys_ok
           and market["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["listing_count"] == 0
           and empty["category_count"] == 0
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["peak_month"] is None
           and empty["peak_live_listing_count"] is None
           and empty["month_over_month_change"] is None
           and empty["months"] == []
           and gate_forms == ["E_AM_BAD_ARGS"] * 8)
    record("AC-CSM1", ok1,
           "env_keys=%d exact=%r row_keys=%r cell_keys=%r empty=%r"
           " gate=%r"
           % (len(market), set(market.keys()) == ENVELOPE_KEYS,
              row_keys_ok, cell_keys_ok, empty["months"], gate_forms))

    # -- AC-CSM2 the month-end sampling law and the window -----------
    bm = by_month(market)
    as_of_ok = all(
        bm[m]["as_of"] == as_of for m, as_of in (
            ("2026-01", "2026-01-31T23:59:59Z"),
            ("2026-02", "2026-02-28T23:59:59Z"),
            ("2026-03", "2026-03-31T23:59:59Z"),
            ("2026-04", "2026-04-30T23:59:59Z"),
            ("2026-05", "2026-05-31T23:59:59Z"),
            ("2026-06", "2026-06-30T23:59:59Z")))
    ok2 = (market["month_count"] == 6
           and [row["month"] for row in market["months"]]
           == ["2026-01", "2026-02", "2026-03", "2026-04",
               "2026-05", "2026-06"]
           and market["first_month"] == "2026-01"
           and market["last_month"] == "2026-06"
           and as_of_ok)
    record("AC-CSM2", ok2,
           "months=%r as_of_ok=%r price_revision_excluded=%r"
           % ([row["month"] for row in market["months"]], as_of_ok,
              market["last_month"] == "2026-06"))

    # -- AC-CSM3 three-way conservation ------------------------------
    def conserve_row(row):
        return (row["live_listing_count"]
                == (row["in_stock_listing_count"]
                    + row["sold_out_listing_count"]
                    + row["unlimited_listing_count"])
                and row["live_listing_count"]
                == sum(c["live_listing_count"]
                       for c in row["categories"])
                and row["in_stock_listing_count"]
                == sum(c["in_stock_listing_count"]
                       for c in row["categories"])
                and row["sold_out_listing_count"]
                == sum(c["sold_out_listing_count"]
                       for c in row["categories"])
                and row["unlimited_listing_count"]
                == sum(c["unlimited_listing_count"]
                       for c in row["categories"])
                and row["remaining_units"]
                == sum(c["remaining_units"]
                       for c in row["categories"])
                and row["category_count"] == len(row["categories"])
                and all(c["live_listing_count"]
                        == (c["in_stock_listing_count"]
                            + c["sold_out_listing_count"]
                            + c["unlimited_listing_count"])
                        for c in row["categories"]))

    ok3 = (all(conserve_row(row) for row in market["months"])
           and market["listing_count"] == 3
           and market["category_count"] == 4)
    record("AC-CSM3", ok3,
           "conserved=%r listing_count=%r category_count=%r"
           % (all(conserve_row(row) for row in market["months"]),
              market["listing_count"], market["category_count"]))

    # -- AC-CSM4 the supply arithmetic at an instant ----------------
    # d1 keeps its full 2 units in January (the February purchase is
    # not yet visible), drops to 1 in February, jumps to 5 in March
    # (restock +3 on the 5th, refund on the 20th hands the unit back),
    # and u1 is honestly sold out from April on. f1 is unlimited, so it
    # never reports units and never sells out.
    def cell(month, category):
        return cells_by_category(bm[month]).get(category)

    d1_rem = [cell(m, "data")["remaining_units"]
              for m in ("2026-01", "2026-02", "2026-03", "2026-04",
                        "2026-05")]
    u1_rem = [cell(m, None)["remaining_units"]
              for m in ("2026-01", "2026-02", "2026-03", "2026-04",
                        "2026-05")]
    u1_out = [cell(m, None)["sold_out_listing_count"]
              for m in ("2026-01", "2026-02", "2026-03", "2026-04",
                        "2026-05")]
    ok4 = (d1_rem == [2, 1, 5, 5, 5]
           and u1_rem == [1, 1, 1, 0, 0]
           and u1_out == [0, 0, 0, 1, 1]
           and cell("2026-01", "tools")["unlimited_listing_count"] == 1
           and cell("2026-01", "tools")["remaining_units"] == 0
           and cell("2026-01", "tools")["sold_out_listing_count"] == 0
           and cell("2026-02", "tools")["sold_out_listing_count"] == 0)
    record("AC-CSM4", ok4,
           "d1_remaining=%r u1_remaining=%r u1_sold_out=%r"
           % (d1_rem, u1_rem, u1_out))

    # -- AC-CSM5 the cycle law on the time axis ---------------------
    # f1 publishes in January, is retired on 2026-05-02 and re-listed
    # on 2026-06-01, so the May month end honestly misses it.
    ok5a = (bm["2026-01"]["live_listing_count"] == 3
            and bm["2026-04"]["live_listing_count"] == 3
            and bm["2026-05"]["live_listing_count"] == 2
            and bm["2026-05"]["unlimited_listing_count"] == 0
            and bm["2026-06"]["live_listing_count"] == 3
            and bm["2026-06"]["unlimited_listing_count"] == 1)

    # a listing retired inside its own month is absent at that month end
    zero_tmp = tempfile.mkdtemp(prefix="apimarket-csm-zero-")
    z_led, z_metered, z_dk, _z_gate, z_am = build_stack(
        os.path.join(zero_tmp, "ledger.db"), cfg, lobby_cfg)
    z_dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    clock.value = "2026-01-05T00:00:00Z"
    z1 = z_am.publish_api("usr:dana", "flash-api", "Flash API",
                          "short lived endpoint", PAYLOAD, 9,
                          False, supply=5, category="data")["listing_id"]
    clock.value = "2026-01-20T00:00:00Z"
    z_am.delist_api("usr:dana", z1)
    clock.value = "2026-04-10T00:00:00Z"
    z_am.publish_api("usr:dana", "calm-api", "Calm API",
                     "later endpoint", PAYLOAD, 3, False, supply=2,
                     category="tools")
    zero = z_am.api_category_supply_months()
    close_stack(z_am, z_dk, z_metered, z_led)
    zm = by_month(zero)
    ok5b = (zero["month_count"] == 4
            and [row["month"] for row in zero["months"]]
            == ["2026-01", "2026-02", "2026-03", "2026-04"]
            and [row["live_listing_count"] for row in zero["months"]]
            == [0, 0, 0, 1]
            and zm["2026-02"]["categories"] == []
            and zm["2026-02"]["remaining_units"] == 0
            and zm["2026-02"]["category_count"] == 0
            and zm["2026-04"]["remaining_units"] == 2)
    record("AC-CSM5", ok5a and ok5b,
           "live=%r may_unlimited=%r zero_live=%r zero_feb_cells=%r"
           % ([row["live_listing_count"] for row in market["months"]],
              bm["2026-05"]["unlimited_listing_count"],
              [row["live_listing_count"] for row in zero["months"]],
              zm["2026-02"]["categories"]))

    # -- AC-CSM6 the trend extremes, the month delta and ordering ---
    jun_cells = bm["2026-06"]["categories"]
    order_ok = ([c["category"] for c in jun_cells]
                == ["data2", "tools", None])
    ordered_all = all(
        [c["category"] for c in row["categories"]]
        == sorted([c["category"] for c in row["categories"]
                   if c["category"] is not None])
        + ([None] if any(c["category"] is None
                         for c in row["categories"]) else [])
        for row in market["months"])
    filtered = am.api_category_supply_months(include_uncategorized=False)
    fjun = by_month(filtered)["2026-06"]
    ok6 = (market["peak_month"] == "2026-01"
           and market["peak_live_listing_count"] == 3
           and market["month_over_month_change"] == 1
           and order_ok and ordered_all
           and fjun["live_listing_count"] == 2
           and fjun["category_count"] == 2
           and fjun["remaining_units"] == 5
           and all(c["category"] is not None
                   for c in fjun["categories"])
           and filtered["category_count"] == 3
           # the filter removes the uncategorized shelf from every
           # sampled month of the view, so it also leaves the counted
           # listing set: the honest reading of "distinct listings
           # appearing in any sampled month".
           and filtered["listing_count"] == 2)
    record("AC-CSM6", ok6,
           "peak=%r/%r delta=%r jun_cells=%r filtered_jun=%r"
           % (market["peak_month"], market["peak_live_listing_count"],
              market["month_over_month_change"],
              [str(c["category"]) for c in jun_cells],
              (fjun["live_listing_count"], fjun["remaining_units"])))

    # -- AC-CSM7 the pure-read law and determinism ------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    first = dumps(am.api_category_supply_months())
    second = dumps(am.api_category_supply_months())
    third = dumps(am.api_category_supply_months(True))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (first == second == third
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-CSM7", ok7,
           "identical=%r frozen=%r tx=%r sha16=%s"
           % (first == second == third,
              digests_before == digests_after, tx_before == tx_after,
              hashlib.sha256(first.encode("utf-8")).hexdigest()[:16]))

    # -- AC-CSM8 cross-restart identity and the wiring --------------
    final = dumps(am.api_category_supply_months())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_category_supply_months())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_category_supply_months())
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_category_supply_months()
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
           and "ledger-apimarket-categorysupplymonths"
           in runner_text)
    record("AC-CSM8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_market == third_market, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-categorysupplymonths" in runner_text))

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