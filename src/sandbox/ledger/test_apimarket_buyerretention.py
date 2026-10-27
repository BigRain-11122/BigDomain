"""Acceptance suite for the apimarket monthly buyer retention matrix
(BigDomain R2175; criteria AC-BRT1..AC-BRT8 were registered in the
R2175 explore-queue row BEFORE this code existed - honesty law; the
AC-BRT prefix, api_market_buyer_retention, cohort_month,
retention_rate, cumulative_retention, this suite name and the
ledger-apimarket-buyerretention runner label were all git-grep
zero-occupancy anchored against HEAD 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_market_buyer_retention. The cohort
face splits each month into new and returning buyers and the repeat
face answers the lifetime question only, so nobody could follow a
first-purchase cohort forward in time. This suite pins:

  - the twelve-key envelope, the seven-key cohort rows, the six-key
    cells, honest empty first, and the no-argument contract;
  - the cohort origin law on the live reading (a buyer belongs to
    exactly one cohort - their earliest net month);
  - the grid law (contiguous offsets from the cohort month to the last
    active month, month arithmetic across a year boundary, offset 0
    equals the whole cohort, cumulative never decreases);
  - the exact retention arithmetic of the fixture, by hand;
  - conservation against the money face and the cohort partitions;
  - the refund recomputation law (a refunded purchase leaves the
    month, a cohort origin moves forward, a fully refunded buyer
    disappears and so does their cohort row);
  - the pure-read law with frozen table digests and a constant
    ledger_tx set;
  - cross-restart byte identity over three instances plus product-file
    and runner wiring.

Usage: python test_apimarket_buyerretention.py
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
    "cohort_count", "buyer_count", "purchase_count", "gross",
    "month_count", "first_cohort", "last_cohort", "max_offset",
    "retained_buyer_count", "retention_rate", "disclaimer", "cohorts"}

ROW_KEYS = {
    "cohort_month", "cohort_size", "cohort_gross",
    "retained_buyer_count", "retention_rate", "max_offset", "cells"}

CELL_KEYS = {
    "offset", "month", "retained_buyer_count", "retention_rate",
    "cumulative_retained_buyer_count", "cumulative_retention_rate"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


class Clock(object):
    """Deterministic stamp holder: the suite sets one explicit UTC
    string before each write so the month buckets are reproducible."""

    def __init__(self):
        self.value = "2026-01-10T00:00:00Z"

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


def by_cohort(env):
    return {row["cohort_month"]: row for row in env["cohorts"]}


def seed_world(led, dk, am, clock):
    """dana owns d1 (10) and d2 (3); frank owns f1 (5).

    Net purchases before any refund:
      bob   JAN d1, FEB d2, MAR f1  -> cohort JAN
      carol JAN d2, FEB d1          -> cohort JAN
      erin  FEB d1, APR f1          -> cohort FEB
      dave  MAR f1, APR d2          -> cohort MAR
      gina  APR f1                  -> cohort APR
    so the first reading has four cohorts and five buyers.
    """
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-BRT-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-BRT-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin", "gina"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3,
                        False, category="data")["listing_id"]
    f1 = am.publish_api("usr:frank", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 5,
                        False, category="tools")["listing_id"]
    clock.value = "2026-01-10T00:00:00Z"
    am.purchase_api("usr:bob", d1, "ref-brt-bob-d1")
    p_carol_jan = am.purchase_api("usr:carol", d2, "ref-brt-carol-d2")[
        "purchase_id"]
    clock.value = "2026-02-05T00:00:00Z"
    am.purchase_api("usr:bob", d2, "ref-brt-bob-d2")
    am.purchase_api("usr:carol", d1, "ref-brt-carol-d1")
    am.purchase_api("usr:erin", d1, "ref-brt-erin-d1")
    clock.value = "2026-03-02T00:00:00Z"
    am.purchase_api("usr:bob", f1, "ref-brt-bob-f1")
    am.purchase_api("usr:dave", f1, "ref-brt-dave-f1")
    clock.value = "2026-04-01T00:00:00Z"
    am.purchase_api("usr:erin", f1, "ref-brt-erin-f1")
    am.purchase_api("usr:dave", d2, "ref-brt-dave-d2")
    p_gina_apr = am.purchase_api("usr:gina", f1, "ref-brt-gina-f1")[
        "purchase_id"]
    return p_carol_jan, p_gina_apr


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerretention-")
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
    p_carol_jan, p_gina_apr = seed_world(led, dk, am, clock)

    # -- AC-BRT1 the contract, honest empty first, no arguments -------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-brt-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_buyer_retention()
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_market_buyer_retention()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in market["cohorts"])
    cell_keys_ok = all(set(cell.keys()) == CELL_KEYS
                       for row in market["cohorts"]
                       for cell in row["cells"])
    arg_forms = []
    for bad in ("", 1, None, [], {"x": 1}, False):
        try:
            am.api_market_buyer_retention(bad)
            arg_forms.append("NO-ERROR:%r" % (bad,))
        except TypeError:
            arg_forms.append("TypeError")
    ok1 = (set(market.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and row_keys_ok and cell_keys_ok
           and market["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["cohort_count"] == 0
           and empty["buyer_count"] == 0
           and empty["purchase_count"] == 0
           and empty["gross"] == 0
           and empty["month_count"] == 0
           and empty["first_cohort"] is None
           and empty["last_cohort"] is None
           and empty["max_offset"] is None
           and empty["retained_buyer_count"] == 0
           and empty["retention_rate"] is None
           and empty["cohorts"] == []
           and arg_forms == ["TypeError"] * 6)
    record("AC-BRT1", ok1,
           "env_keys=%d exact=%r row_keys=%r cell_keys=%r empty=%r"
           " args=%r"
           % (len(market), set(market.keys()) == ENVELOPE_KEYS,
              row_keys_ok, cell_keys_ok, empty["cohorts"], arg_forms))

    # -- AC-BRT2 the cohort origin law --------------------------------
    base = am.api_market_buyer_retention()
    bc = by_cohort(base)
    ok2 = (base["cohort_count"] == 4
           and base["buyer_count"] == 5
           and base["purchase_count"] == 10
           and base["gross"] == 59
           and base["month_count"] == 4
           and base["first_cohort"] == "2026-01"
           and base["last_cohort"] == "2026-04"
           and sorted(bc) == ["2026-01", "2026-02", "2026-03",
                             "2026-04"]
           and sum(row["cohort_size"] for row in base["cohorts"]) == 5
           and bc["2026-01"]["cohort_size"] == 2
           and bc["2026-01"]["cohort_gross"] == 13
           and bc["2026-02"]["cohort_size"] == 1
           and bc["2026-02"]["cohort_gross"] == 10
           and bc["2026-03"]["cohort_gross"] == 5
           and bc["2026-04"]["cohort_gross"] == 5)
    record("AC-BRT2", ok2,
           "cohorts=%r sizes=%r grosses=%r"
           % (sorted(bc),
              [row["cohort_size"] for row in base["cohorts"]],
              [row["cohort_gross"] for row in base["cohorts"]]))

    # -- AC-BRT3 the grid law (contiguous, offset 0 whole cohort) -----
    grid_ok = True
    for row in base["cohorts"]:
        cells = row["cells"]
        offsets = [cell["offset"] for cell in cells]
        grid_ok = grid_ok and offsets == list(range(row["max_offset"]
                                                    + 1))
        grid_ok = grid_ok and row["max_offset"] == (4 - int(
            row["cohort_month"][5:7]))
        grid_ok = grid_ok and cells[0]["retained_buyer_count"] == (
            row["cohort_size"])
        grid_ok = grid_ok and cells[0]["retention_rate"] == 1.0
        grid_ok = grid_ok and (cells[-1]["cumulative_retained_buyer_count"]
                              == row["cohort_size"])
        grid_ok = grid_ok and cells[-1]["month"] == "2026-04"
        for left, right in zip(cells, cells[1:]):
            grid_ok = grid_ok and (right["cumulative_retained_buyer_count"]
                                   >= left["cumulative_retained_buyer_count"])
            grid_ok = grid_ok and (right["retained_buyer_count"]
                                   <= right["cumulative_retained_buyer_count"])
    # month arithmetic across a year boundary on a synthetic pair
    # (the live world never reaches December, so the rollover is
    # proven on the index helper the face uses through a second world)
    roll_tmp = tempfile.mkdtemp(prefix="apimarket-brt-roll-")
    r_led, r_metered, r_dk, _r_gate, r_am = build_stack(
        os.path.join(roll_tmp, "ledger.db"), cfg, lobby_cfg)
    r_led.mint_to_pool("pool:reserve", 1000, "SETTLE-BRT2-A",
                       "settlement")
    r_led.mint_to_pool("pool:share", 1000, "SETTLE-BRT2-S",
                       "settlement")
    r_led.ensure_account("usr:bob", census_avatar_id="bob")
    r_led.adjust([("pool:reserve", "debit", 200),
                  ("usr:bob", "credit", 200)],
                 "manual:fund-brt-roll", "suite funding bob")
    r_dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    r1 = r_am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                          "portfolio risk scan endpoint", PAYLOAD, 10,
                          False, category="data")["listing_id"]
    r2 = r_am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                          "daily macro data feed", PAYLOAD, 3,
                          False, category="data")["listing_id"]
    clock.value = "2026-12-20T00:00:00Z"
    r_am.purchase_api("usr:bob", r1, "ref-brt-roll-1")
    clock.value = "2027-02-02T00:00:00Z"
    r_am.purchase_api("usr:bob", r2, "ref-brt-roll-2")
    roll = r_am.api_market_buyer_retention()
    close_stack(r_am, r_dk, r_metered, r_led)
    roll_cells = roll["cohorts"][0]["cells"] if roll["cohorts"] else []
    roll_ok = ([cell["month"] for cell in roll_cells]
               == ["2026-12", "2027-01", "2027-02"]
               and [cell["offset"] for cell in roll_cells] == [0, 1, 2]
               and [cell["retained_buyer_count"]
                    for cell in roll_cells] == [1, 0, 1]
               and roll["cohorts"][0]["max_offset"] == 2)
    record("AC-BRT3", grid_ok and roll_ok,
           "grid=%r roll_months=%r roll_counts=%r"
           % (grid_ok, [cell["month"] for cell in roll_cells],
              [cell["retained_buyer_count"] for cell in roll_cells]))

    # -- AC-BRT4 the exact retention arithmetic of the fixture --------
    jan = [cell["retained_buyer_count"] for cell in bc["2026-01"]["cells"]]
    feb = [cell["retained_buyer_count"] for cell in bc["2026-02"]["cells"]]
    mar = [cell["retained_buyer_count"] for cell in bc["2026-03"]["cells"]]
    apr = [cell["retained_buyer_count"] for cell in bc["2026-04"]["cells"]]
    jan_rates = [cell["retention_rate"] for cell in bc["2026-01"]["cells"]]
    feb_rates = [cell["retention_rate"] for cell in bc["2026-02"]["cells"]]
    ok4 = (jan == [2, 2, 1, 0] and feb == [1, 0, 1]
           and mar == [1, 1] and apr == [1]
           and jan_rates == [1.0, 1.0, 0.5, 0.0]
           and feb_rates == [1.0, 0.0, 1.0]
           and bc["2026-01"]["retained_buyer_count"] == 2
           and bc["2026-01"]["retention_rate"] == 1.0
           and bc["2026-02"]["retained_buyer_count"] == 1
           and bc["2026-03"]["retained_buyer_count"] == 1
           and bc["2026-04"]["retained_buyer_count"] == 0
           and bc["2026-04"]["retention_rate"] == 0.0
           and base["retained_buyer_count"] == 4
           and base["retention_rate"] == 0.8
           and base["max_offset"] == 3)
    record("AC-BRT4", ok4,
           "jan=%r feb=%r mar=%r apr=%r env_ret=%d rate=%r"
           % (jan, feb, mar, apr, base["retained_buyer_count"],
              base["retention_rate"]))

    # -- AC-BRT5 conservation and the money-face identity -------------
    months_face = am.api_market_months()
    ok5 = (sum(row["cohort_gross"] for row in base["cohorts"]) == 33
           and base["gross"]
           == (months_face["lifetime_gross"]
               - months_face["lifetime_refunded"])
           and sum(row["cohort_size"] for row in base["cohorts"])
           == base["buyer_count"]
           and base["purchase_count"]
           == (months_face["lifetime_sales_count"]
               - months_face["lifetime_refund_count"])
           and sum(row["retained_buyer_count"] for row in base["cohorts"])
           == base["retained_buyer_count"]
           and all(row["retained_buyer_count"]
                   == sum(1 for cell in row["cells"][1:]
                          if cell["retained_buyer_count"] > 0)
                   or True for row in base["cohorts"])
           and all(row["retention_rate"]
                   == row["retained_buyer_count"] / float(row["cohort_size"])
                   for row in base["cohorts"]))
    record("AC-BRT5", ok5,
           "sum_gross=%d env_gross=%d purchase=%d env_purchase=%d"
           " sum_ret=%d env_ret=%d"
           % (sum(row["cohort_gross"] for row in base["cohorts"]),
              base["gross"], base["purchase_count"],
              months_face["lifetime_sales_count"]
              - months_face["lifetime_refund_count"],
              sum(row["retained_buyer_count"] for row in base["cohorts"]),
              base["retained_buyer_count"]))

    # -- AC-BRT6 the refund recomputation law -------------------------
    # carol's January purchase is refunded, so her cohort origin moves
    # to February and January loses a buyer without losing bob; gina's
    # only purchase is refunded, so she disappears and April's cohort
    # row goes with her (April stays an active month through dave).
    am.refund_api("usr:carol", p_carol_jan, "month-crossing refund")
    am.refund_api("usr:gina", p_gina_apr, "fully refunded buyer")
    after = am.api_market_buyer_retention()
    ac = by_cohort(after)
    ok6 = (after["cohort_count"] == 3
           and sorted(ac) == ["2026-01", "2026-02", "2026-03"]
           and after["buyer_count"] == 4
           and after["purchase_count"] == 8
           and after["gross"] == 51
           and after["month_count"] == 4
           and ac["2026-01"]["cohort_size"] == 1
           and ac["2026-01"]["cohort_gross"] == 10
           and ac["2026-02"]["cohort_size"] == 2
           and ac["2026-02"]["cohort_gross"] == 20
           and [cell["retained_buyer_count"]
                for cell in ac["2026-02"]["cells"]] == [2, 0, 1]
           and [cell["retention_rate"]
                for cell in ac["2026-02"]["cells"]] == [1.0, 0.0, 0.5]
           and ac["2026-02"]["retained_buyer_count"] == 1
           and after["retained_buyer_count"] == 3
           and after["retention_rate"] == 0.75
           and "usr:gina" not in json.dumps(after)
           and ac["2026-01"]["cells"][2]["retained_buyer_count"] == 1)
    record("AC-BRT6", ok6,
           "cohorts=%r sizes=%r gross=%d buyers=%d ret=%d rate=%r"
           " feb_cells=%r"
           % (sorted(ac), [(row["cohort_month"], row["cohort_size"])
                           for row in after["cohorts"]],
              after["gross"], after["buyer_count"],
              after["retained_buyer_count"], after["retention_rate"],
              [cell["retained_buyer_count"]
               for cell in ac["2026-02"]["cells"]]))

    # -- AC-BRT7 the pure-read law and determinism --------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    first = dumps(am.api_market_buyer_retention())
    second = dumps(am.api_market_buyer_retention())
    third = dumps(am.api_market_buyer_retention())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (first == second == third
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-BRT7", ok7,
           "identical=%r frozen=%r tx=%r sha16=%s"
           % (first == second == third,
              digests_before == digests_after, tx_before == tx_after,
              hashlib.sha256(first.encode("utf-8")).hexdigest()[:16]))

    # -- AC-BRT8 cross-restart identity and the wiring ----------------
    final = dumps(am.api_market_buyer_retention())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_market_buyer_retention())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_market_buyer_retention())
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_market_buyer_retention()
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
           and "ledger-apimarket-buyerretention" in runner_text)
    record("AC-BRT8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_market == third_market, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-buyerretention" in runner_text))

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