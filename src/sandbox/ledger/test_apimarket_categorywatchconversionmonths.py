"""Acceptance suite for the apimarket per-category monthly
watch-to-purchase conversion (BigDomain R2237; canon = the R2230
explore seed row 5/6, criteria AC-CWC1..AC-CWC8 registered in that row
BEFORE this code existed).

Face under proof: APIMarketFace.api_category_watch_conversion_months.
The market face answers the whole market on a month axis, the listing
funnel face answers one listing over its lifetime and the category
watch face answers volume only - so whether a category's attention
actually converted had no reading. This suite pins:

  - the sixteen-key envelope, fourteen-key month rows, twelve-key
    category cells and the honest empty world;
  - the cohort law on the watch month (an unwatch is not an event, a
    purchase never re-dates the watch month);
  - the three conversion legs: converted, pre_owned excluded from the
    funnel, and pending that also absorbs a refunded purchase so a
    cancellation lowers that month's rate in place;
  - the contiguous grid with a zero month carrying a None rate and
    None latencies rather than fabricated zeros;
  - the category seam through the watch instant: a revision lands in
    later buckets only;
  - the true-market benchmark column that survives the trimmed view,
    plus identity against api_category_watch_months and
    api_market_conversion_months;
  - the include_uncategorized gate: bool-only fail-closed before any
    read, False dropping the bucket AND recomputing every aggregate;
  - the pure-read law (frozen table digests, constant ledger_tx,
    byte-identical repeats and three instances across restarts), the
    wiring and the ASCII/LF source hygiene.

Usage: python test_apimarket_categorywatchconversionmonths.py
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
    "month_count", "first_month", "last_month", "watch_count",
    "pre_owned_count", "funnel_count", "converted_count",
    "pending_count", "conversion_rate", "avg_convert_seconds",
    "median_convert_seconds", "fastest_convert_seconds",
    "slowest_convert_seconds", "category_count", "disclaimer",
    "months"}

ROW_KEYS = {
    "month", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate",
    "avg_convert_seconds", "median_convert_seconds",
    "fastest_convert_seconds", "slowest_convert_seconds",
    "market_conversion_rate", "category_count", "categories"}

CELL_KEYS = {
    "category", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate",
    "avg_convert_seconds", "median_convert_seconds",
    "fastest_convert_seconds", "slowest_convert_seconds",
    "market_conversion_rate"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set
    before each write so the month buckets are reproducible."""

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


def cell_row(row, category):
    for cell in row["categories"]:
        if cell["category"] == category:
            return cell
    raise AssertionError("category %r missing from row %r"
                         % (category, row["month"]))


def seed_world(led, dk, am, clock):
    """Four listings: t1 at dana (tools), d1 at lia (data, later
    analytics), u1 at lia (the honest uncategorized bucket) and g1 at
    gina (data).

    JAN: erin buys d1 on 01-05 and only watches it on 01-10 (pre_owned);
         bob and kit watch t1 on 01-10 and bob buys t1 on 01-12
         (converted, 172800s); sol watches u1 on 01-25 (pending).
    FEB: no event at all (the zero row).
    MAR: bob watches d1 on 03-05 and buys it on 03-08 (converted,
         259200s, booked under data); lia re-files d1 to analytics on
         03-20, after the watch.
    APR: bob watches g1 on 04-02, buys it on 04-05 and refunds it on
         04-20, so the cancellation leg turns that watch pending.
    MAY: kit watches d1 on 05-07, now booked under analytics, pending.

    Per category: tools 2 watches / 1 converted / 1 pending; data 3 /
    1 pre_owned / 1 converted / 1 pending; analytics 1 / 0 / 1;
    uncategorized 1 / 0 / 1. Market 7 watches / 1 pre_owned / funnel 6
    / 2 converted / 4 pending.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-CWC-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-CWC-S",
                     "settlement")
    for who in ("bob", "kit", "erin", "sol"):
        fund(led, who)
    for dev in ("dana", "lia", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    d1 = am.publish_api("usr:lia", "d1", "Lia Data API",
                        "lia data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    u1 = am.publish_api("usr:lia", "u1", "Lia Unsorted API",
                        "lia unsorted payloads", PAYLOAD, 10,
                        False)["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    clock.value = "2026-01-05T00:00:00Z"
    am.purchase_api("usr:erin", d1, "BUY-CWC-1")

    clock.value = "2026-01-10T00:00:00Z"
    am.watch_api("usr:bob", t1)
    am.watch_api("usr:kit", t1)
    am.watch_api("usr:erin", d1)

    clock.value = "2026-01-12T00:00:00Z"
    am.purchase_api("usr:bob", t1, "BUY-CWC-2")

    clock.value = "2026-01-25T00:00:00Z"
    am.watch_api("usr:sol", u1)

    clock.value = "2026-03-05T00:00:00Z"
    am.watch_api("usr:bob", d1)
    clock.value = "2026-03-08T00:00:00Z"
    am.purchase_api("usr:bob", d1, "BUY-CWC-3")
    clock.value = "2026-03-20T00:00:00Z"
    am.revise_category("usr:lia", d1, "analytics")

    clock.value = "2026-04-02T00:00:00Z"
    am.watch_api("usr:bob", g1)
    clock.value = "2026-04-05T00:00:00Z"
    purchase = am.purchase_api("usr:bob", g1, "BUY-CWC-4")
    clock.value = "2026-04-20T00:00:00Z"
    am.refund_api("usr:bob", purchase["purchase_id"], "cancelled")

    clock.value = "2026-05-07T00:00:00Z"
    am.watch_api("usr:kit", d1)

    return {"t1": t1, "d1": d1, "u1": u1, "g1": g1}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-categorycwc-")
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

    env = am.api_category_watch_conversion_months()
    trimmed = am.api_category_watch_conversion_months(False)
    watch_vol = am.api_category_watch_months()
    market_conv = am.api_market_conversion_months()

    # -- AC-CWC1 contract shape and the honest empty world -----------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-cwc-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_category_watch_conversion_months()
    empty_trimmed = e_am.api_category_watch_conversion_months(False)
    close_stack(e_am, e_dk, e_metered, e_led)
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    cells_ok = all(set(cell.keys()) == CELL_KEYS
                   for row in env["months"]
                   for cell in row["categories"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(trimmed.keys()) == ENVELOPE_KEYS
           and rows_ok and cells_ok
           and env["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["watch_count"] == 0
           and empty["funnel_count"] == 0
           and empty["conversion_rate"] is None
           and empty["avg_convert_seconds"] is None
           and empty["median_convert_seconds"] is None
           and empty["category_count"] == 0
           and empty_trimmed["month_count"] == 0)
    record("AC-CWC1", ok1,
           "env_keys=%d exact=%r row_keys=%r cell_keys=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              cells_ok,
              (empty["month_count"], empty["conversion_rate"],
               empty["category_count"])))

    # -- AC-CWC2 cohort law on the watch month -----------------------
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    may = month_row(env, "2026-05")
    ok2 = (jan["watch_count"] == 4
           and jan["pre_owned_count"] == 1
           and jan["funnel_count"] == 3
           and jan["converted_count"] == 1
           and jan["pending_count"] == 2
           and mar["watch_count"] == 1
           and mar["converted_count"] == 1
           and may["watch_count"] == 1
           and [row["month"] for row in env["months"]] == [
               "2026-01", "2026-02", "2026-03", "2026-04",
               "2026-05"]
           and env["watch_count"] == 7)
    record("AC-CWC2", ok2,
           "jan=%r mar=%r may=%r grid=%r"
           % ((jan["watch_count"], jan["pre_owned_count"],
               jan["funnel_count"], jan["converted_count"],
               jan["pending_count"]),
              (mar["watch_count"], mar["converted_count"]),
              (may["watch_count"], may["converted_count"]),
              [row["month"] for row in env["months"]]))

    # -- AC-CWC3 conversion and cancellation legs --------------------
    jan_tools = cell_row(jan, "tools")
    jan_data = cell_row(jan, "data")
    mar_data = cell_row(mar, "data")
    apr = month_row(env, "2026-04")
    apr_data = cell_row(apr, "data")
    ok3 = (jan_tools["converted_count"] == 1
           and jan_tools["pending_count"] == 1
           and jan_data["pre_owned_count"] == 1
           and jan_data["funnel_count"] == 0
           and jan_data["converted_count"] == 0
           and jan_data["conversion_rate"] is None
           and mar_data["converted_count"] == 1
           and mar_data["conversion_rate"] == 1.0
           and apr_data["watch_count"] == 1
           and apr_data["funnel_count"] == 1
           and apr_data["converted_count"] == 0
           and apr_data["pending_count"] == 1
           and apr_data["conversion_rate"] == 0.0
           and env["converted_count"] == 2
           and env["pending_count"] == 4
           and env["avg_convert_seconds"] == 216000.0
           and env["median_convert_seconds"] == 216000.0
           and env["fastest_convert_seconds"] == 172800
           and env["slowest_convert_seconds"] == 259200)
    record("AC-CWC3", ok3,
           "jan_tools=%r jan_data=%r mar_data=%r apr_data=%r lat=%r"
           % ((jan_tools["converted_count"],
               jan_tools["pending_count"]),
              (jan_data["pre_owned_count"], jan_data["funnel_count"],
               jan_data["conversion_rate"]),
              (mar_data["converted_count"],
               mar_data["conversion_rate"]),
              (apr_data["converted_count"], apr_data["pending_count"],
               apr_data["conversion_rate"]),
              (env["avg_convert_seconds"],
               env["fastest_convert_seconds"],
               env["slowest_convert_seconds"])))

    # -- AC-CWC4 contiguous grid and the honest zero month -----------
    feb = month_row(env, "2026-02")
    ok4 = (feb["watch_count"] == 0
           and feb["pre_owned_count"] == 0
           and feb["funnel_count"] == 0
           and feb["converted_count"] == 0
           and feb["pending_count"] == 0
           and feb["conversion_rate"] is None
           and feb["market_conversion_rate"] is None
           and feb["avg_convert_seconds"] is None
           and feb["median_convert_seconds"] is None
           and feb["fastest_convert_seconds"] is None
           and feb["slowest_convert_seconds"] is None
           and feb["category_count"] == 0
           and feb["categories"] == []
           and env["month_count"] == 5
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-05")
    record("AC-CWC4", ok4,
           "feb=%r months=%r"
           % ((feb["watch_count"], feb["funnel_count"],
               feb["conversion_rate"], feb["categories"]),
              env["month_count"]))

    # -- AC-CWC5 category seam through the watch instant -------------
    jan_cats = [cell["category"] for cell in jan["categories"]]
    mar_cats = [cell["category"] for cell in mar["categories"]]
    may_cats = [cell["category"] for cell in may["categories"]]
    may_analytics = cell_row(may, "analytics")
    ok5 = (jan_cats == ["data", "tools", None]
           and jan["categories"][-1]["category"] is None
           and mar_cats == ["data"]
           and may_cats == ["analytics"]
           and may_analytics["watch_count"] == 1
           and may_analytics["pending_count"] == 1
           and env["category_count"] == 4
           and trimmed["category_count"] == 3)
    record("AC-CWC5", ok5,
           "jan_cats=%r mar_cats=%r may_cats=%r may_analytics=%r"
           % (jan_cats, mar_cats, may_cats,
              (may_analytics["watch_count"],
               may_analytics["pending_count"])))

    # -- AC-CWC6 conservation, benchmark column and identity ---------
    def sums(view):
        w = sum(r["watch_count"] for r in view["months"])
        p = sum(r["pre_owned_count"] for r in view["months"])
        f = sum(r["funnel_count"] for r in view["months"])
        c = sum(r["converted_count"] for r in view["months"])
        n = sum(r["pending_count"] for r in view["months"])
        return w, p, f, c, n

    cell_sums_ok = True
    for row in env["months"]:
        for field in ("watch_count", "pre_owned_count",
                      "funnel_count", "converted_count",
                      "pending_count"):
            if sum(c[field] for c in row["categories"]) \
                    != row[field]:
                cell_sums_ok = False
        if row["category_count"] != len(row["categories"]):
            cell_sums_ok = False
        if row["funnel_count"] != (row["watch_count"]
                                   - row["pre_owned_count"]):
            cell_sums_ok = False
        if row["pending_count"] != (row["funnel_count"]
                                    - row["converted_count"]):
            cell_sums_ok = False
    env_sums = sums(env)
    trim_sums = sums(trimmed)
    vol_months = {row["month"]: row["watch_count"]
                  for row in watch_vol["months"]}
    conv_months = {row["month"]: row["watch_count"]
                   for row in market_conv["months"]}
    grid_identity = all(
        row["watch_count"] == vol_months.get(row["month"])
        == conv_months.get(row["month"])
        for row in env["months"])
    trim_jan = month_row(trimmed, "2026-01")
    trim_jan_tools = cell_row(trim_jan, "tools")
    ok6 = (cell_sums_ok
           and env_sums == (7, 1, 6, 2, 4)
           and env_sums == (env["watch_count"], env["pre_owned_count"],
                            env["funnel_count"],
                            env["converted_count"],
                            env["pending_count"])
           and abs(env["conversion_rate"] - 2.0 / 6.0) < 1e-12
           and trim_sums == (6, 1, 5, 2, 3)
           and abs(trimmed["conversion_rate"] - 0.4) < 1e-12
           and grid_identity
           and watch_vol["watch_count"] == 7
           and market_conv["converted_count"] == 2
           and market_conv["pre_owned_count"] == 1
           and market_conv["pending_count"] == 4
           and jan["market_conversion_rate"] == jan_tools[
               "market_conversion_rate"]
           and abs(jan_tools["market_conversion_rate"]
                   - 1.0 / 3.0) < 1e-12
           and trim_jan["conversion_rate"] == 0.5
           and abs(trim_jan["market_conversion_rate"]
                   - 1.0 / 3.0) < 1e-12
           and trim_jan_tools["market_conversion_rate"] \
           == trim_jan["market_conversion_rate"])
    record("AC-CWC6", ok6,
           "cells=%r sums=%r/%r identity=%r benchmark=%r/%r"
           % (cell_sums_ok, env_sums, trim_sums, grid_identity,
              jan_tools["market_conversion_rate"],
              trim_jan["market_conversion_rate"]))

    # -- AC-CWC7 the include_uncategorized gate ----------------------
    trimmed_cats = set()
    for row in trimmed["months"]:
        for cell in row["categories"]:
            trimmed_cats.add(cell["category"])
    trim_total_cells = sum(len(row["categories"])
                           for row in trimmed["months"])
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_codes = []
    for bad in (1, 0, "yes", [], {}, None, 1.0):
        try:
            am.api_category_watch_conversion_months(bad)
        except A.ApiMarketError as exc:
            bad_codes.append(exc.code)
        else:
            bad_codes.append("ACCEPTED")
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (None not in trimmed_cats
           and trim_total_cells == 5
           and trim_jan["category_count"] == 2
           and trimmed["watch_count"] == 6
           and trimmed["pending_count"] == 3
           and bad_codes == [A.E_AM_BAD_ARGS] * 7
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-CWC7", ok7,
           "trim_cats=%r cells=%r trim=%r gates=%r frozen=%r"
           % (sorted(str(c) for c in trimmed_cats), trim_total_cells,
              (trimmed["watch_count"], trimmed["pending_count"]),
              bad_codes, digests_before == digests_after))

    # -- AC-CWC8 pure read, determinism and hygiene ------------------
    call_a = dumps(am.api_category_watch_conversion_months())
    call_b = dumps(am.api_category_watch_conversion_months())
    call_t = dumps(am.api_category_watch_conversion_months(False))
    led2, metered2, dk2, _gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    call_c = dumps(am2.api_category_watch_conversion_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, _gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    call_d = dumps(am3.api_category_watch_conversion_months())
    call_dt = dumps(am3.api_category_watch_conversion_months(False))
    close_stack(am3, dk3, metered3, led3)
    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (call_a == call_b == call_c == call_d == dumps(env)
           and call_t == call_dt == dumps(trimmed)
           and b'"ledger-apimarket-categorywatchconversionmonths"' \
           in recon
           and b"test_apimarket_categorywatchconversionmonths.py" \
           in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-CWC8", ok8,
           "bytes_same=%r wired=%r ascii_lf=%r"
           % (call_a == call_d,
              b'"ledger-apimarket-categorywatchconversionmonths"'
              in recon,
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