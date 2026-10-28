"""Acceptance suite for the apimarket market-wide monthly supply
timeline (BigDomain R2214; canon = the R2214 explore-queue claim row,
criteria AC-MSM1..AC-MSM8 registered in that row BEFORE this code).

Face under proof: APIMarketFace.api_market_supply_months. The family
already answered asking price by month, per-category shelves by month
and per-listing supply snapshots, but no face answered the WHOLE
MARKET's shelf position month over month together with its gross flow.
This suite pins:

  - the seventeen-key envelope and thirteen-key month rows, honest
    empty first, the market scope label;
  - the booking law: a cycle opens at publish and at each re-listing,
    a cycle closes at its own delisting, units_added is the finite base
    supply declared by a publish plus the restock units of that month,
    and units_sold is purchases net of refunds of that month, so a
    refund-only month is honestly negative;
  - the contiguous grid over supply-and-movement events only, where a
    month with no event at all is an honest zero row;
  - the month-end sampling law through _alive_at_instant and
    _supply_at_instant (a delisting inside the month removes the shelf
    from that month end, a re-listing inside the month puts it back, a
    refund hands its unit back to the shelf);
  - conservation three ways, including the running opened-minus-closed
    identity with the live shelf count;
  - both peak laws with the earlier-month tie-break;
  - the honest empty envelope and the absence of any account key on a
    market-scope face;
  - the pure-read law (frozen table digests, constant ledger_tx,
    byte-identical repeats), cross-instance and cross-restart byte
    identity, the wiring and the ASCII/LF source hygiene.

Usage: python test_apimarket_marketsupplymonths.py
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
    "scope", "month_count", "first_month", "last_month", "listing_count",
    "seller_count", "peak_month", "peak_live_listing_count",
    "month_over_month_change", "busiest_open_month", "busiest_open_count",
    "opened_total", "closed_total", "units_added_total",
    "units_sold_total", "disclaimer", "months"}

ROW_KEYS = {
    "month", "as_of", "opened_count", "closed_count", "net_shop_change",
    "live_listing_count", "seller_count", "in_stock_listing_count",
    "sold_out_listing_count", "unlimited_listing_count", "remaining_units",
    "units_added", "units_sold"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions", "apimarket_supply_revisions")


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set
    before each write so the month buckets are reproducible."""

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


def month_row(env, month):
    for row in env["months"]:
        if row["month"] == month:
            return row
    raise AssertionError("month %r missing from months" % (month,))


def seed_world(led, dk, am, clock):
    """Three listings, six months, one honest zero month.

    JAN: dana publishes t1 (finite 5) and t2 (finite 3); lia publishes
         d1 with no declared supply (unlimited).
    FEB: bob buys t1 (one unit leaves the shelf).
    MAR: dana restocks t1 by 4; lia delists d1 (that shelf is gone from
         the MAR month end).
    APR: no event at all (the honest zero row).
    MAY: bob buys t2.
    JUN: bob refunds the FEB t1 purchase (the unit returns, so the month
         is honestly negative on units_sold) and lia re-lists d1.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-MSM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-MSM-S",
                     "settlement")
    for who in ("bob", "kit"):
        fund(led, who)
    for dev in ("dana", "lia"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    clock.value = "2026-01-05T00:00:00Z"
    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        supply=5, category="tools")["listing_id"]
    clock.value = "2026-01-20T00:00:00Z"
    t2 = am.publish_api("usr:dana", "t2", "Dana Tools Pro",
                        "dana tools pro payloads", PAYLOAD, 10, False,
                        supply=3, category="tools")["listing_id"]
    clock.value = "2026-01-25T00:00:00Z"
    d1 = am.publish_api("usr:lia", "d1", "Lia Data API",
                        "lia data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    clock.value = "2026-02-10T00:00:00Z"
    am.purchase_api("usr:bob", t1, "MSM-BOB-T1")

    clock.value = "2026-03-02T00:00:00Z"
    am.restock_api("usr:dana", t1, 4)
    clock.value = "2026-03-15T00:00:00Z"
    am.delist_api("usr:lia", d1)

    clock.value = "2026-05-03T00:00:00Z"
    am.purchase_api("usr:bob", t2, "MSM-BOB-T2")

    clock.value = "2026-06-07T00:00:00Z"
    bought = am.api_library("usr:bob")["purchases"]
    t1_purchase = [p for p in bought
                   if int(p["listing_id"]) == int(t1)][0]["purchase_id"]
    am.refund_api("usr:bob", t1_purchase, "not as described")

    clock.value = "2026-06-20T00:00:00Z"
    am.relist_api("usr:lia", d1)

    return {"t1": t1, "t2": t2, "d1": d1}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-marketsupplymonths-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    clock = Clock()
    _CLOCK = clock
    orig_now = A._now_utc
    A._now_utc = clock.now_utc
    try:
        return run(db_path, cfg, lobby_cfg, shas_before)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, shas_before):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    seed_world(led, dk, am, _CLOCK)

    env = am.api_market_supply_months()

    # -- AC-MSM1 contract, honest empty first, scope label -----------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-msm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_supply_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and rows_ok
           and env["scope"] == "market"
           and env["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["listing_count"] == 0
           and empty["seller_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_live_listing_count"] is None
           and empty["month_over_month_change"] is None
           and empty["busiest_open_month"] is None
           and empty["busiest_open_count"] is None
           and empty["opened_total"] == 0
           and empty["closed_total"] == 0
           and empty["units_added_total"] == 0
           and empty["units_sold_total"] == 0)
    record("AC-MSM1", ok1,
           "env_keys=%d exact=%r row_keys=%r scope=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              env["scope"], (empty["month_count"], empty["months"])))

    # -- AC-MSM2 booking law and the honestly negative month --------
    jan = month_row(env, "2026-01")
    feb = month_row(env, "2026-02")
    mar = month_row(env, "2026-03")
    may = month_row(env, "2026-05")
    jun = month_row(env, "2026-06")
    ok2 = (jan["opened_count"] == 3 and jan["closed_count"] == 0
           and jan["net_shop_change"] == 3
           and jan["units_added"] == 8 and jan["units_sold"] == 0
           and feb["opened_count"] == 0 and feb["units_sold"] == 1
           and mar["units_added"] == 4 and mar["units_sold"] == 0
           and may["units_sold"] == 1
           and jun["units_sold"] == -1 and jun["units_added"] == 0
           and jun["opened_count"] == 1 and jun["closed_count"] == 0
           and env["opened_total"] == 4
           and env["closed_total"] == 1
           and env["units_added_total"] == 12
           and env["units_sold_total"] == 1)
    record("AC-MSM2", ok2,
           "jan=%r feb=%r mar=%r may=%r jun=%r totals=%r"
           % (jan["units_added"], feb["units_sold"], mar["units_added"],
              may["units_sold"], jun["units_sold"],
              (env["opened_total"], env["closed_total"],
               env["units_added_total"], env["units_sold_total"])))

    # -- AC-MSM3 contiguous grid and the honest zero month ----------
    grid = [row["month"] for row in env["months"]]
    apr = month_row(env, "2026-04")
    ok3 = (grid == ["2026-01", "2026-02", "2026-03", "2026-04",
                    "2026-05", "2026-06"]
           and env["month_count"] == 6
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-06"
           and apr["opened_count"] == 0 and apr["closed_count"] == 0
           and apr["net_shop_change"] == 0 and apr["units_added"] == 0
           and apr["units_sold"] == 0
           and apr["live_listing_count"] == 2)
    record("AC-MSM3", ok3,
           "grid=%r apr=%r" % (grid,
                               (apr["opened_count"], apr["units_added"],
                                apr["units_sold"],
                                apr["live_listing_count"])))

    # -- AC-MSM4 month-end sampling law -----------------------------
    ok4 = (jan["live_listing_count"] == 3
           and jan["seller_count"] == 2
           and jan["in_stock_listing_count"] == 2
           and jan["unlimited_listing_count"] == 1
           and jan["remaining_units"] == 8
           and feb["remaining_units"] == 7
           and mar["live_listing_count"] == 2
           and mar["seller_count"] == 1
           and mar["unlimited_listing_count"] == 0
           and mar["remaining_units"] == 11
           and jun["live_listing_count"] == 3
           and jun["seller_count"] == 2
           and jun["unlimited_listing_count"] == 1
           and jun["remaining_units"] == 11)
    record("AC-MSM4", ok4,
           "jan=%r feb_rem=%r mar=%r jun=%r"
           % ((jan["live_listing_count"], jan["seller_count"],
               jan["remaining_units"]), feb["remaining_units"],
              (mar["live_listing_count"], mar["unlimited_listing_count"],
               mar["remaining_units"]),
              (jun["live_listing_count"], jun["remaining_units"])))

    # -- AC-MSM5 conservation, three ways ---------------------------
    cells_ok = True
    running_ok = True
    opened_running = 0
    closed_running = 0
    for row in env["months"]:
        opened_running += row["opened_count"]
        closed_running += row["closed_count"]
        if row["live_listing_count"] != (
                row["in_stock_listing_count"]
                + row["sold_out_listing_count"]
                + row["unlimited_listing_count"]):
            cells_ok = False
        if row["live_listing_count"] != opened_running - closed_running:
            running_ok = False
        if row["net_shop_change"] != (
                row["opened_count"] - row["closed_count"]):
            cells_ok = False
    ok5 = cells_ok and running_ok and env["listing_count"] == 3
    record("AC-MSM5", ok5,
           "cells=%r running=%r listing_count=%r"
           % (cells_ok, running_ok, env["listing_count"]))

    # -- AC-MSM6 peak laws with the earlier-month tie-break ---------
    ok6 = (env["peak_month"] == "2026-01"
           and env["peak_live_listing_count"] == 3
           and env["busiest_open_month"] == "2026-01"
           and env["busiest_open_count"] == 3
           and env["month_over_month_change"] == 1)
    record("AC-MSM6", ok6,
           "peak=%r open=%r mom=%r"
           % ((env["peak_month"], env["peak_live_listing_count"]),
              (env["busiest_open_month"], env["busiest_open_count"]),
              env["month_over_month_change"]))

    # -- AC-MSM7 honest empty and no account surface ----------------
    blobs = [dumps(env)]
    blobs.extend(dumps(row) for row in env["months"])
    ok7 = (empty["months"] == [] and empty["scope"] == "market"
           and all("buyer_id" not in blob and "dev_account" not in blob
                   for blob in blobs)
           and env["months"]
           and not any("buyer_id" in row or "dev_account" in row
                       for row in env["months"]))
    record("AC-MSM7", ok7,
           "empty_rows=%r account_keys=%r rows=%d"
           % (empty["months"],
              any("buyer_id" in blob or "dev_account" in blob
                  for blob in blobs), len(env["months"])))

    # -- AC-MSM8 pure read, determinism and the wiring --------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_market_supply_months())
    call_b = dumps(am.api_market_supply_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    close_stack(am, dk, metered, led)

    led2, metered2, dk2, _gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    call_c = dumps(am2.api_market_supply_months())
    close_stack(am2, dk2, metered2, led2)

    led3, metered3, dk3, _gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    call_d = dumps(am3.api_market_supply_months())
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (digests_before == digests_after
           and tx_before == tx_after
           and call_a == call_b == call_c == call_d == dumps(env)
           and b'"ledger-apimarket-marketsupplymonths"' in recon
           and b"test_apimarket_marketsupplymonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-MSM8", ok8,
           "digests_same=%r tx_same=%r bytes_same=%r wired=%r ascii_lf=%r"
           % (digests_before == digests_after, tx_before == tx_after,
              call_a == call_d,
              b'"ledger-apimarket-marketsupplymonths"' in recon,
              (b"\r\n" not in test_src
               and all(b < 128 for b in test_src))))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("%s PRODUCT_SHA_STABLE %r"
          % ("PASS" if shas_before == shas_after else "FAIL",
             shas_before == shas_after), flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())