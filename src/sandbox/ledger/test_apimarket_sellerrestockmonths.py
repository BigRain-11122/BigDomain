"""Acceptance suite for the seller monthly replenishment cadence
(BigDomain R2222; canon = the R2213 explore-queue seed row claimed in
R2222, criteria AC-RSM1..AC-RSM9 registered in that row in the same
window as this code, disclosed - the R2137/R2141/R2144 precedent).

Face under proof: APIMarketFace.api_seller_restock_months.
api_supply_history answers ONE listing's revision chain and
api_seller_supply answers a live snapshot rollup, so "how often does
this shop replenish, and is the replenishment growing or shrinking"
had no time axis. This suite pins:

  - the envelope keys, the ten-key month rows and the honest empty
    world;
  - the booking law: a restock books in the month of its own
    restocked_utc, a later restock never rewrites an earlier month,
    and a month inside the range with no restock is an honest zero
    row;
  - the cadence law: gaps measured between a scope's own
    consecutive revisions in revision_id order, an integer floor
    mean, and None gaps with fewer than two revisions;
  - the direction law: thickening / thinning / flat over the last
    two active months, None with fewer than two;
  - conservation of the row counts and units against the envelope,
    the integer floor row average, and the monotone accumulators;
  - the peak law with the earlier-month tie-break and no zero peak;
  - the scope law (market scope without a self-benchmark, seller
    scope with the market pooled mean, strict isolation), the
    unlimited-shelf exclusion and the cross-face identity against
    api_seller_supply;
  - the account gate and the pure-read law (frozen table digests,
    constant ledger_tx set);
  - cross-instance byte identity over two full-stack restarts,
    wiring and ASCII/LF hygiene.

Usage: python test_apimarket_sellerrestockmonths.py
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
import apimarket_report as RPT        # noqa: E402 (config loader)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apimarket_report.py"),
    os.path.join(BASE, "apidev.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

ENVELOPE_KEYS = {
    "scope", "dev_account", "restock_count", "units_added",
    "listing_count", "owned_listing_count", "month_count",
    "active_month_count", "first_month", "last_month", "peak_month",
    "peak_units_added", "latest_month_units_added",
    "avg_units_per_restock", "largest_restock_units",
    "smallest_restock_units", "mean_gap_seconds", "max_gap_seconds",
    "trend", "market_mean_units_per_restock", "disclaimer", "months"}

ROW_KEYS = {
    "month", "restock_count", "units_added", "listing_count",
    "avg_units_per_restock", "largest_restock_units",
    "first_restock_utc", "last_restock_utc", "running_restock_count",
    "running_units_added"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_questions", "apimarket_answers",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_rating_replies", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions",
          "apimarket_supply_revisions")

BAD_ACCOUNTS = ("", "u", "usrX:dana", 123, False, [],
                {}, {"usr:x": 1})

DANA_JAN_UNITS = 12          # 5 + 7
DANA_MAR_UNITS = 7           # 3 + 4
GAP_10D = 864000
GAP_45D = 3888000
GAP_9D = 777600
HANA_GAP_59D = 5097600
MARKET_MEAN_GAP = 1296000
MARKET_MAX_GAP = 2246400
DANA_MEAN_GAP = 1843200


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set
    before each write so the month buckets are reproducible."""

    def __init__(self):
        self.value = "2026-01-01T00:00:00Z"

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


def error_code(fn, *args):
    try:
        fn(*args)
    except A.ApiMarketError as exc:
        return exc.code
    return None


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


def month_row(env, month):
    for row in env["months"]:
        if row["month"] == month:
            return row
    raise AssertionError("month %r missing from months" % (month,))


def seed_world(led, dk, am, clock):
    """Three sellers, four finite shelves and one unlimited shelf.

    dana: t1 (base 10) restocked +5 on Jan 05 and +7 on Jan 15, then
    d1 (base 5) restocked +3 on Mar 01 and +4 on Mar 10 - a silent
    February, a thinning trend and a 45-day gap between the January
    and March work. u1 is published WITHOUT a supply, so it can never
    carry a revision.
    gina: g1 (base 8) restocked once in January - the isolation leg
    with honest None gaps.
    hana: h1 (base 5) restocked +2 on Feb 05 and +2 on Apr 05 - the
    flat leg that also stretches the market grid to April.
    """
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-RSM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-RSM-S",
                     "settlement")
    for dev in ("dana", "gina", "hana"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    clock.value = "2026-01-01T00:00:00Z"
    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        supply=10, category="tools")["listing_id"]
    d1 = am.publish_api("usr:dana", "d1", "Dana Data API",
                        "dana data payloads", PAYLOAD, 10, False,
                        supply=5, category="data")["listing_id"]
    u1 = am.publish_api("usr:dana", "u1", "Dana Unlimited API",
                        "a shelf with no declared stock", PAYLOAD, 10,
                        False)["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        supply=8, category="data")["listing_id"]
    h1 = am.publish_api("usr:hana", "h1", "Hana Media API",
                        "hana media payloads", PAYLOAD, 10, False,
                        supply=5, category="media")["listing_id"]

    clock.value = "2026-01-05T00:00:00Z"
    am.restock_api("usr:dana", t1, 5)
    clock.value = "2026-01-15T00:00:00Z"
    am.restock_api("usr:dana", t1, 7)
    clock.value = "2026-01-20T00:00:00Z"
    am.restock_api("usr:gina", g1, 4)
    clock.value = "2026-02-05T00:00:00Z"
    am.restock_api("usr:hana", h1, 2)
    clock.value = "2026-03-01T00:00:00Z"
    am.restock_api("usr:dana", d1, 3)
    clock.value = "2026-03-10T00:00:00Z"
    am.restock_api("usr:dana", d1, 4)
    clock.value = "2026-04-05T00:00:00Z"
    am.restock_api("usr:hana", h1, 2)

    return {"t1": t1, "d1": d1, "u1": u1, "g1": g1, "h1": h1}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerrestockmonths-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}
    cfg, lobby_cfg = RPT.load_configs()

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
    shelves = seed_world(led, dk, am, _CLOCK)

    # -- AC-RSM1 the contract and the honest empty world ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-rsm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_restock_months("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_seller_restock_months("usr:dana")
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
           and env["disclaimer"] == DISCLAIMER
           and env["scope"] == "seller"
           and env["dev_account"] == "usr:dana"
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["restock_count"] == 0
           and empty["units_added"] == 0
           and empty["listing_count"] == 0
           and empty["owned_listing_count"] == 0
           and empty["active_month_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_units_added"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_units_added"] == 0
           and empty["avg_units_per_restock"] is None
           and empty["largest_restock_units"] is None
           and empty["smallest_restock_units"] is None
           and empty["mean_gap_seconds"] is None
           and empty["max_gap_seconds"] is None
           and empty["trend"] is None
           and empty["market_mean_units_per_restock"] is None)
    record("AC-RSM1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              (empty["month_count"], empty["months"],
               empty["avg_units_per_restock"])))

    # -- AC-RSM2 booking law: the revision books on its own month ---
    jan = month_row(env, "2026-01")
    feb = month_row(env, "2026-02")
    mar = month_row(env, "2026-03")
    grid = [row["month"] for row in env["months"]]
    unlimited_code = error_code(am.restock_api, "usr:dana",
                                shelves["u1"], 5)
    after_refusal = am.api_seller_restock_months("usr:dana")
    ok2 = (grid == ["2026-01", "2026-02", "2026-03"]
           and jan["restock_count"] == 2
           and jan["units_added"] == DANA_JAN_UNITS
           and mar["restock_count"] == 2
           and mar["units_added"] == DANA_MAR_UNITS
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-03"
           and env["restock_count"] == 4
           and env["units_added"] == DANA_JAN_UNITS + DANA_MAR_UNITS
           and unlimited_code == "E_AM_SUPPLY_UNLIMITED"
           and after_refusal["restock_count"] == env["restock_count"])
    record("AC-RSM2", ok2,
           "grid=%r jan=%r mar=%r totals=%r unlimited=%r"
           % (grid, (jan["restock_count"], jan["units_added"]),
              (mar["restock_count"], mar["units_added"]),
              (env["restock_count"], env["units_added"]),
              (unlimited_code, after_refusal["restock_count"])))

    # -- AC-RSM3 cadence law over consecutive revisions ------------
    gina = am.api_seller_restock_months("usr:gina")
    hana = am.api_seller_restock_months("usr:hana")
    market = am.api_seller_restock_months()
    ok3 = (env["mean_gap_seconds"] == DANA_MEAN_GAP
           and env["max_gap_seconds"] == GAP_45D
           and (GAP_10D + GAP_45D + GAP_9D) // 3 == DANA_MEAN_GAP
           and gina["restock_count"] == 1
           and gina["mean_gap_seconds"] is None
           and gina["max_gap_seconds"] is None
           and hana["mean_gap_seconds"] == HANA_GAP_59D
           and hana["max_gap_seconds"] == HANA_GAP_59D
           and market["mean_gap_seconds"] == MARKET_MEAN_GAP
           and market["max_gap_seconds"] == MARKET_MAX_GAP)
    record("AC-RSM3", ok3,
           "dana=%r gina=%r hana=%r market=%r"
           % ((env["mean_gap_seconds"], env["max_gap_seconds"]),
              (gina["mean_gap_seconds"], gina["max_gap_seconds"]),
              hana["mean_gap_seconds"],
              (market["mean_gap_seconds"], market["max_gap_seconds"])))

    # -- AC-RSM4 direction law: thinning, flat, None ---------------
    hana_grid = [row["month"] for row in hana["months"]]
    ok4 = (env["trend"] == "thinning"
           and hana["trend"] == "flat"
           and gina["trend"] is None
           and market["trend"] == "thinning"
           and hana_grid == ["2026-02", "2026-03", "2026-04"]
           and month_row(hana, "2026-02")["units_added"] == 2
           and month_row(hana, "2026-04")["units_added"] == 2
           and month_row(hana, "2026-03")["units_added"] == 0
           and month_row(hana, "2026-03")["restock_count"] == 0)
    record("AC-RSM4", ok4,
           "dana=%r hana=%r gina=%r market=%r hana_grid=%r"
           % (env["trend"], hana["trend"], gina["trend"],
              market["trend"], hana_grid))

    # -- AC-RSM5 conservation and the integer floor average --------
    ok5 = (sum(row["restock_count"] for row in env["months"])
           == env["restock_count"] == 4
           and sum(row["units_added"] for row in env["months"])
           == env["units_added"] == 19
           and env["avg_units_per_restock"] == 19 // 4
           and jan["avg_units_per_restock"] == DANA_JAN_UNITS // 2
           and mar["avg_units_per_restock"] == DANA_MAR_UNITS // 2
           and all(row["avg_units_per_restock"]
                   == row["units_added"] // row["restock_count"]
                   for row in env["months"]
                   if row["restock_count"] > 0)
           and env["months"][-1]["running_restock_count"]
           == env["restock_count"]
           and env["months"][-1]["running_units_added"]
           == env["units_added"]
           and [row["running_units_added"] for row in env["months"]]
           == [DANA_JAN_UNITS, DANA_JAN_UNITS,
               DANA_JAN_UNITS + DANA_MAR_UNITS]
           and env["avg_units_per_restock"] == 4
           and env["largest_restock_units"] == 7
           and env["smallest_restock_units"] == 3)
    record("AC-RSM5", ok5,
           "counts=%r units=%r avg=%r running=%r extremes=%r"
           % ([row["restock_count"] for row in env["months"]],
              [row["units_added"] for row in env["months"]],
              (env["avg_units_per_restock"],
               jan["avg_units_per_restock"],
               mar["avg_units_per_restock"]),
              [row["running_units_added"] for row in env["months"]],
              (env["largest_restock_units"],
               env["smallest_restock_units"])))

    # -- AC-RSM6 peak law, tie-break and no zero peak --------------
    ok6 = (env["peak_month"] == "2026-01"
           and env["peak_units_added"] == DANA_JAN_UNITS
           and env["latest_month_units_added"] == DANA_MAR_UNITS
           and env["month_count"] == 3
           and env["active_month_count"] == 2
           and feb["units_added"] == 0
           and feb["restock_count"] == 0
           and feb["avg_units_per_restock"] is None
           and feb["largest_restock_units"] is None
           and feb["first_restock_utc"] is None
           and feb["last_restock_utc"] is None
           and feb["running_units_added"] == DANA_JAN_UNITS
           and hana["peak_month"] == "2026-02"
           and hana["peak_units_added"] == 2
           and gina["peak_month"] == "2026-01"
           and gina["peak_units_added"] == 4)
    record("AC-RSM6", ok6,
           "peak=%r feb=%r hana=%r gina=%r"
           % ((env["peak_month"], env["peak_units_added"]),
              (feb["restock_count"], feb["avg_units_per_restock"],
               feb["running_units_added"]),
              (hana["peak_month"], hana["peak_units_added"]),
              (gina["peak_month"], gina["peak_units_added"])))

    # -- AC-RSM7 scope law, isolation and cross-face identity ------
    supply = am.api_seller_supply("usr:dana")
    market_supply_ids = am.api_seller_restock_months()
    ok7 = (env["market_mean_units_per_restock"]
           == market["avg_units_per_restock"] == 3
           and market["scope"] == "market"
           and market["dev_account"] is None
           and market["market_mean_units_per_restock"] is None
           and market["restock_count"] == 7
           and market["units_added"] == 27
           and market["listing_count"] == 4
           and market["owned_listing_count"] == 5
           and market["month_count"] == 4
           and market["active_month_count"] == 4
           and market["peak_month"] == "2026-01"
           and market["peak_units_added"] == 16
           and market["latest_month_units_added"] == 2
           and market_supply_ids["restock_count"]
           == market["restock_count"]
           and supply["total_restock_count"] == env["restock_count"]
           == 4
           and supply["total_restocked_units"] == env["units_added"]
           == 19
           and supply["listing_count"] == 3
           and env["owned_listing_count"] == 3
           and env["listing_count"] == 2
           and gina["restock_count"] == 1
           and gina["units_added"] == 4
           and gina["month_count"] == 1
           and gina["months"][0]["month"] == "2026-01"
           and gina["owned_listing_count"] == 1
           and gina["market_mean_units_per_restock"]
           == market["avg_units_per_restock"] == 3
           and hana["units_added"] == 4
           and hana["month_count"] == 3
           and hana["market_mean_units_per_restock"] == 3)
    record("AC-RSM7", ok7,
           "supply=%r face=%r market=%r gina=%r hana=%r"
           % ((supply["total_restock_count"],
               supply["total_restocked_units"],
               supply["listing_count"]),
              (env["restock_count"], env["units_added"],
               env["owned_listing_count"], env["market_mean_units_per_restock"]),
              (market["restock_count"], market["units_added"],
               market["listing_count"], market["owned_listing_count"],
               market["avg_units_per_restock"]),
              (gina["units_added"], gina["owned_listing_count"]),
              (hana["units_added"], hana["month_count"])))

    # -- AC-RSM8 account gate and the pure read --------------------
    codes = [error_code(am.api_seller_restock_months, form)
             for form in BAD_ACCOUNTS]
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_seller_restock_months("usr:dana"))
    call_b = dumps(am.api_seller_restock_months("usr:dana"))
    market_a = dumps(am.api_seller_restock_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok8 = (codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and call_a == call_b == dumps(env)
           and market_a == dumps(market)
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-RSM8", ok8,
           "gate=%r deterministic=%r digests_same=%r tx_same=%r"
           % (codes, call_a == call_b,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-RSM9 restarts, wiring and hygiene ----------------------
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_seller_restock_months("usr:dana"))
    market_c = dumps(am2.api_seller_restock_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_seller_restock_months("usr:dana"))
    market_d = dumps(am3.api_seller_restock_months())
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok9 = (call_a == call_c == call_d == dumps(env)
           and market_a == market_c == market_d == dumps(market)
           and b'"ledger-apimarket-sellerrestockmonths"' in recon
           and b"test_apimarket_sellerrestockmonths.py" in recon
           and b"def api_seller_restock_months" in src
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-RSM9", ok9,
           "bytes_same=%r wired=%r ascii=%r crlf_clean=%r"
           % (call_a == call_d,
              b'"ledger-apimarket-sellerrestockmonths"' in recon,
              all(b < 128 for b in test_src),
              b"\r\n" not in test_src))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())