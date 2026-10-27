"""Acceptance suite for the apimarket category price trend face
(BigDomain R2176; criteria AC-CPM1..AC-CPM8 were registered in the
R2176 explore-queue row BEFORE this code existed - honesty law; the
AC-CPM prefix, api_category_price_months, p50_change,
_category_at_instant and _alive_at were all git-grep zero-occupancy
anchored against HEAD 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_category_price_months. Every other
price face is a snapshot of the current state (price percentiles, the
per-category min/max band), and every time axis the market had answers
turnover. This suite pins the new face, the point-in-time rebuild of
each category's asking price at every UTC month end:

  - the seven-key envelope, the twelve-key month rows, the five-key
    bucket cells, the honest empty world and the bool gate;
  - the month-end sampling law (as_of = the month's last second) and
    the contiguous window, including the honest zero month;
  - the price timing law (a revision in the month's last second counts
    there, one at the next month's first second does not);
  - the category timing law (a revision moves the bucket from its own
    month end on, and previous_category is preserved);
  - the cycle law on the time axis (retired between, present again);
  - conservation, the median trend series, bucket ordering, the
    uncategorized filter and the cross-face identity against the
    current-state percentile face;
  - the pure-read law with frozen table digests and a constant
    ledger_tx set;
  - cross-restart byte identity over three instances plus product-file
    and runner wiring.

Usage: python test_apimarket_categorypricemonths.py
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
    "category_count", "disclaimer", "months"}

ROW_KEYS = {
    "month", "as_of", "live_listing_count", "category_count",
    "min_price", "max_price", "p25_price", "p50_price", "p75_price",
    "mean_price", "p50_change", "categories"}

CELL_KEYS = {
    "category", "live_listing_count", "min_price", "max_price",
    "p50_price"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


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


def by_month(env):
    return {row["month"]: row for row in env["months"]}


def cells_by_category(row):
    return {cell["category"]: cell for cell in row["categories"]}


def seed_world(dk, am, clock):
    """dana owns d1 (10, data) and f1 (4, tools); both publish in
    January. February reprices d1 to 20 and retires f1; March re-lists
    f1 at the 31st's last second d1 becomes 30; April first second d1
    becomes 40 and mid-April d1 is re-filed under data2; June adds g1
    (2, tools) and f2 (6, uncategorized)."""
    clock.value = "2026-01-05T00:00:00Z"
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    f1 = am.publish_api("usr:dana", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 4,
                        False, category="tools")["listing_id"]
    clock.value = "2026-02-10T00:00:00Z"
    am.revise_price("usr:dana", d1, 20)
    clock.value = "2026-02-20T00:00:00Z"
    am.delist_api("usr:dana", f1)
    clock.value = "2026-03-01T00:00:00Z"
    am.relist_api("usr:dana", f1)
    clock.value = "2026-03-31T23:59:59Z"
    am.revise_price("usr:dana", d1, 30)
    clock.value = "2026-04-01T00:00:00Z"
    am.revise_price("usr:dana", d1, 40)
    clock.value = "2026-04-15T00:00:00Z"
    am.revise_category("usr:dana", d1, "data2")
    clock.value = "2026-06-02T00:00:00Z"
    g1 = am.publish_api("usr:dana", "tiny-kit", "Tiny Kit API",
                        "small deterministic payload", PAYLOAD, 2,
                        False, category="tools")["listing_id"]
    f2 = am.publish_api("usr:dana", "loose-pack", "Loose Pack API",
                        "uncategorized payload pack", PAYLOAD, 6,
                        False)["listing_id"]
    return d1, f1, g1, f2


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-cpm-")
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
    d1, f1, g1, f2 = seed_world(dk, am, clock)

    # -- AC-CPM1 the contract, honest empty, the bool gate ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-cpm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_category_price_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_category_price_months()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in market["months"])
    cell_keys_ok = all(set(cell.keys()) == CELL_KEYS
                       for row in market["months"]
                       for cell in row["categories"])
    gate_forms = []
    for bad in ("yes", 1, None, [], 0, 1.0):
        try:
            am.api_category_price_months(bad)
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
           and empty["months"] == []
           and gate_forms == ["E_AM_BAD_ARGS"] * 6)
    record("AC-CPM1", ok1,
           "env_keys=%d exact=%r row_keys=%r cell_keys=%r empty=%r"
           " gate=%r"
           % (len(market), set(market.keys()) == ENVELOPE_KEYS,
              row_keys_ok, cell_keys_ok, empty["months"], gate_forms))

    # -- AC-CPM2 the month-end sampling law and the window ------------
    base = am.api_category_price_months()
    bm = by_month(base)
    as_of_ok = (bm["2026-01"]["as_of"] == "2026-01-31T23:59:59Z"
                and bm["2026-02"]["as_of"] == "2026-02-28T23:59:59Z"
                and bm["2026-03"]["as_of"] == "2026-03-31T23:59:59Z"
                and bm["2026-04"]["as_of"] == "2026-04-30T23:59:59Z"
                and bm["2026-05"]["as_of"] == "2026-05-31T23:59:59Z"
                and bm["2026-06"]["as_of"] == "2026-06-30T23:59:59Z")
    # a June publication is absent from every earlier month end
    jan_cells = cells_by_category(bm["2026-01"])
    earlier_clean = (list(jan_cells) == ["data", "tools"]
                     and bm["2026-01"]["live_listing_count"] == 2
                     and json.dumps(bm["2026-01"]).count("tiny-kit") == 0)
    ok2 = (base["month_count"] == 6
           and [row["month"] for row in base["months"]]
           == ["2026-01", "2026-02", "2026-03", "2026-04",
               "2026-05", "2026-06"]
           and base["first_month"] == "2026-01"
           and base["last_month"] == "2026-06"
           and as_of_ok and earlier_clean)
    record("AC-CPM2", ok2,
           "months=%r as_of=%r jan_cells=%r"
           % ([row["month"] for row in base["months"]], as_of_ok,
              sorted(str(c) for c in jan_cells)))

    # -- AC-CPM3 the price timing law --------------------------------
    # January keeps the base 10, February reads 20, March reads 30
    # because the revision landed at 23:59:59, and April reads 40
    # because the 00:00:00 revision did not leak back into March.
    def single_price(month, category):
        cell = cells_by_category(bm[month]).get(category)
        return None if cell is None else cell["min_price"]

    ok3 = (single_price("2026-01", "data") == 10
           and single_price("2026-02", "data") == 20
           and single_price("2026-03", "data") == 30
           and single_price("2026-04", "data2") == 40
           and bm["2026-03"]["p50_price"] == 17.0
           and bm["2026-04"]["p50_price"] == 22.0)
    record("AC-CPM3", ok3,
           "prices=%r mar_p50=%r apr_p50=%r"
           % ([single_price("2026-01", "data"),
               single_price("2026-02", "data"),
               single_price("2026-03", "data"),
               single_price("2026-04", "data2")],
              bm["2026-03"]["p50_price"], bm["2026-04"]["p50_price"]))

    # -- AC-CPM4 the category timing law -----------------------------
    history = am.api_category_history(d1)
    ok4 = ("data2" not in cells_by_category(bm["2026-01"])
           and "data" in cells_by_category(bm["2026-01"])
           and "data2" not in cells_by_category(bm["2026-03"])
           and "data2" in cells_by_category(bm["2026-04"])
           and "data" not in cells_by_category(bm["2026-04"])
           and history["revision_count"] == 1
           and history["revisions"][0]["previous_category"] == "data"
           and history["revisions"][0]["category"] == "data2")
    record("AC-CPM4", ok4,
           "jan=%r mar=%r apr=%r history=%r"
           % (sorted(str(c) for c in cells_by_category(bm["2026-01"])),
              sorted(str(c) for c in cells_by_category(bm["2026-03"])),
              sorted(str(c) for c in cells_by_category(bm["2026-04"])),
              history["revision_count"]))

    # -- AC-CPM5 the cycle law on the time axis ----------------------
    # f1 publishes in January, is retired on 2026-02-20 and re-listed
    # on 2026-03-01, so the February month end honestly misses it.
    ok5 = (bm["2026-01"]["live_listing_count"] == 2
           and bm["2026-02"]["live_listing_count"] == 1
           and bm["2026-02"]["category_count"] == 1
           and bm["2026-03"]["live_listing_count"] == 2
           and single_price("2026-03", "tools") == 4)
    record("AC-CPM5", ok5,
           "live=%r feb_cats=%r mar_tools=%r"
           % ([row["live_listing_count"] for row in base["months"]],
              sorted(str(c) for c in cells_by_category(bm["2026-02"])),
              single_price("2026-03", "tools")))

    # -- AC-CPM6 conservation, the trend series and the filter -------
    jun = bm["2026-06"]
    june_cells = cells_by_category(jun)
    percentiles = am.api_market_price_percentiles()
    ordered_ok = all(
        [c["category"] for c in row["categories"]]
        == sorted([c["category"] for c in row["categories"]
                   if c["category"] is not None],
                  key=lambda s: s)
        + ([None] if any(c["category"] is None
                         for c in row["categories"]) else [])
        for row in base["months"])
    filtered = am.api_category_price_months(include_uncategorized=False)
    fjun = by_month(filtered)["2026-06"]
    ok6 = (all(row["live_listing_count"]
               == sum(cell["live_listing_count"]
                      for cell in row["categories"])
               for row in base["months"])
           and all(row["category_count"] == len(row["categories"])
                   for row in base["months"])
           and [row["live_listing_count"] for row in base["months"]]
           == [2, 1, 2, 2, 2, 4]
           and [row["p50_price"] for row in base["months"]]
           == [7.0, 20.0, 17.0, 22.0, 22.0, 5.0]
           and [row["p50_change"] for row in base["months"]]
           == [None, 13.0, -3.0, 5.0, 0.0, -17.0]
           and jun["min_price"] == percentiles["min_price"] == 2
           and jun["max_price"] == percentiles["max_price"] == 40
           and jun["p25_price"] == percentiles["p25_price"]
           and jun["p50_price"] == percentiles["p50_price"]
           and jun["p75_price"] == percentiles["p75_price"]
           and jun["mean_price"] == percentiles["mean_price"]
           and base["listing_count"] == percentiles["listing_count"] == 4
           and base["category_count"] == 4
           and ordered_ok
           and june_cells[None]["min_price"] == 6
           and filtered["category_count"] == 3
           and fjun["live_listing_count"] == 3
           and fjun["p50_price"] == 4.0
           and all(cell["category"] is not None
                   for cell in fjun["categories"]))
    record("AC-CPM6", ok6,
           "live=%r p50=%r change=%r percentiles=(%r,%r,%r,%r)"
           " listing_count=%r filtered_jun=%r"
           % ([row["live_listing_count"] for row in base["months"]],
              [row["p50_price"] for row in base["months"]],
              [row["p50_change"] for row in base["months"]],
              percentiles["min_price"], percentiles["p25_price"],
              percentiles["p50_price"], percentiles["p75_price"],
              base["listing_count"],
              (fjun["live_listing_count"], fjun["p50_price"])))

    # -- AC-CPM7 the pure-read law and determinism -------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    first = dumps(am.api_category_price_months())
    second = dumps(am.api_category_price_months())
    third = dumps(am.api_category_price_months(True))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (first == second == third
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-CPM7", ok7,
           "identical=%r frozen=%r tx=%r sha16=%s"
           % (first == second == third,
              digests_before == digests_after, tx_before == tx_after,
              hashlib.sha256(first.encode("utf-8")).hexdigest()[:16]))

    # -- AC-CPM8 the honest zero month (the contiguous window) -------
    zero_tmp = tempfile.mkdtemp(prefix="apimarket-cpm-zero-")
    z_led, z_metered, z_dk, _z_gate, z_am = build_stack(
        os.path.join(zero_tmp, "ledger.db"), cfg, lobby_cfg)
    z_dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    clock.value = "2026-01-05T00:00:00Z"
    z1 = z_am.publish_api("usr:dana", "flash-api", "Flash API",
                          "short lived endpoint", PAYLOAD, 9, False,
                          category="data")["listing_id"]
    clock.value = "2026-01-20T00:00:00Z"
    z_am.delist_api("usr:dana", z1)
    clock.value = "2026-04-10T00:00:00Z"
    z_am.publish_api("usr:dana", "calm-api", "Calm API",
                     "later endpoint", PAYLOAD, 3, False,
                     category="tools")
    zero = z_am.api_category_price_months()
    close_stack(z_am, z_dk, z_metered, z_led)
    zm = by_month(zero)
    ok8a = (zero["month_count"] == 4
            and [row["month"] for row in zero["months"]]
            == ["2026-01", "2026-02", "2026-03", "2026-04"]
            and [row["live_listing_count"] for row in zero["months"]]
            == [0, 0, 0, 1]
            and zm["2026-01"]["p50_price"] is None
            and zm["2026-02"]["p50_price"] is None
            and zm["2026-03"]["p50_price"] is None
            and zm["2026-02"]["p50_change"] is None
            and zm["2026-02"]["categories"] == []
            and zm["2026-04"]["p50_price"] == 3.0
            and zm["2026-04"]["p50_change"] is None)
    zero_note = ("zero_live=%r zero_p50=%r"
                 % ([row["live_listing_count"] for row in zero["months"]],
                    [row["p50_price"] for row in zero["months"]]))

    # -- AC-CPM8b cross-restart identity and the wiring --------------
    final = dumps(am.api_category_price_months())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_category_price_months())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_category_price_months())
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_category_price_months()
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (ok8a
           and final == second_market == third_market
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-categorypricemonths"
           in runner_text)
    record("AC-CPM8", ok8,
           "sha16=%s %s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              zero_note,
              final == second_market == third_market, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-categorypricemonths" in runner_text))

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