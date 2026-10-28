"""Acceptance suite for the apimarket per-category monthly watch flow
(BigDomain R2210; canon = the R2210 explore-queue claim row, criteria
AC-CWM1..AC-CWM8 registered in that row BEFORE this code).

Face under proof: APIMarketFace.api_category_watch_months. The market
watch face answers the whole market on a month axis and the seller face
one seller's stock, while the buyer category mix is one buyer's live
snapshot and api_categories a supply snapshot - so which categories gain
attention month over month had no face. This suite pins:

  - the fifteen-key envelope, seven-key month rows and seven-key
    category cells, plus the honest empty world;
  - the cash-basis double stamp: a watch books in the watched_utc month,
    an unwatch in the unwatched_utc month, and a later unwatch never
    rewrites the watch month, so a pure-unwatch month is honestly
    negative;
  - the contiguous grid with a zero-event month whose active counts and
    level stay flat;
  - the category-at-the-event-instant law: a category revision lands in
    the later month only and never moves an earlier month's bucket;
  - conservation three ways (month == cell sums, envelope == month sums,
    last-month cell actives == live count) plus cross-face identity with
    api_market_watch_months;
  - participant distinctness per cell versus lifetime distinct counts in
    the envelope, the peak law with the earlier-month tie-break and the
    None month-over-month change;
  - the include_uncategorized gate: bool-only fail-closed before any
    read, False dropping the bucket AND recomputing every aggregate,
    True keeping it last;
  - the pure-read law (frozen table digests, constant ledger_tx,
    byte-identical repeats and three instances across restarts), the
    wiring and the ASCII/LF source hygiene.

Usage: python test_apimarket_categorywatchmonths.py
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
    "unwatch_count", "net_count", "live_watch_count", "category_count",
    "buyer_count", "listing_count", "peak_month", "peak_watch_count",
    "month_over_month_change", "disclaimer", "months"}

ROW_KEYS = {
    "month", "watch_count", "unwatch_count", "net_count",
    "active_count", "category_count", "categories"}

CELL_KEYS = {
    "category", "watch_count", "unwatch_count", "net_count",
    "active_count", "buyer_count", "listing_count"}

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
    """Four listings: t1 at dana (tools), d1 and u1 at lia (data and the
    honest uncategorized bucket), g1 at gina (data).

    JAN: bob and kit watch t1, erin watches d1, sol watches u1.
    FEB: no event at all (the zero row that proves the grid).
    MAR: bob watches d1, erin unwatches d1, then lia re-files d1 to
         analytics on 03-20 - after both March events.
    APR: bob watches g1, kit watches d1 (now analytics).
    MAY: kit unwatches t1 (pure-unwatch month, honestly negative net).

    Per category: tools 2 watches / 1 unwatch / live 1; data 3 / 1 /
    live 2 (d1 book plus g1); analytics 1 / 0 / live 1; uncategorized
    1 / 0 / live 1. Market 7 / 2 / live 5.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-CWM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-CWM-S",
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

    clock.value = "2026-01-10T00:00:00Z"
    am.watch_api("usr:bob", t1)
    am.watch_api("usr:kit", t1)
    am.watch_api("usr:erin", d1)
    am.watch_api("usr:sol", u1)

    clock.value = "2026-03-05T00:00:00Z"
    am.watch_api("usr:bob", d1)
    clock.value = "2026-03-06T00:00:00Z"
    am.unwatch_api("usr:erin", d1)
    clock.value = "2026-03-20T00:00:00Z"
    am.revise_category("usr:lia", d1, "analytics")

    clock.value = "2026-04-02T00:00:00Z"
    am.watch_api("usr:bob", g1)
    clock.value = "2026-04-10T00:00:00Z"
    am.watch_api("usr:kit", d1)

    clock.value = "2026-05-07T00:00:00Z"
    am.unwatch_api("usr:kit", t1)

    return {"t1": t1, "d1": d1, "u1": u1, "g1": g1}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-categorywatchmonths-")
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

    env = am.api_category_watch_months()
    trimmed = am.api_category_watch_months(False)
    market = am.api_market_watch_months()

    # -- AC-CWM1 contract shape and the honest empty world -----------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-cwm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_category_watch_months()
    empty_trimmed = e_am.api_category_watch_months(False)
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
           and empty["live_watch_count"] == 0
           and empty["category_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_watch_count"] is None
           and empty["month_over_month_change"] is None
           and empty_trimmed["month_count"] == 0)
    record("AC-CWM1", ok1,
           "env_keys=%d exact=%r row_keys=%r cell_keys=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              cells_ok,
              (empty["month_count"], empty["months"],
               empty["peak_month"])))

    # -- AC-CWM2 cash-basis double stamp -----------------------------
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    may = month_row(env, "2026-05")
    jan_tools = cell_row(jan, "tools")
    mar_data = cell_row(mar, "data")
    may_tools = cell_row(may, "tools")
    ok2 = (jan["watch_count"] == 4 and jan["unwatch_count"] == 0
           and jan_tools["watch_count"] == 2
           and mar["watch_count"] == 1 and mar["unwatch_count"] == 1
           and mar["net_count"] == 0
           and mar_data["watch_count"] == 1
           and mar_data["unwatch_count"] == 1
           and mar_data["net_count"] == 0
           and may["watch_count"] == 0
           and may["unwatch_count"] == 1
           and may["net_count"] == -1
           and may_tools["net_count"] == -1
           and may_tools["active_count"] == 1)
    record("AC-CWM2", ok2,
           "jan=%r mar=%r mar_data=%r may=%r may_tools=%r"
           % ((jan["watch_count"], jan["unwatch_count"]),
              (mar["watch_count"], mar["unwatch_count"],
               mar["net_count"]),
              (mar_data["watch_count"], mar_data["unwatch_count"],
               mar_data["net_count"]),
              (may["watch_count"], may["unwatch_count"],
               may["net_count"]),
              (may_tools["active_count"],)))

    # -- AC-CWM3 contiguous grid and the honest zero month -----------
    grid = [row["month"] for row in env["months"]]
    feb = month_row(env, "2026-02")
    ok3 = (grid == ["2026-01", "2026-02", "2026-03", "2026-04",
                    "2026-05"]
           and feb["watch_count"] == 0
           and feb["unwatch_count"] == 0
           and feb["net_count"] == 0
           and feb["category_count"] == 0
           and feb["categories"] == []
           and feb["active_count"] == jan["active_count"] == 4
           and env["month_count"] == 5
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-05")
    record("AC-CWM3", ok3,
           "grid=%r feb=%r"
           % (grid, (feb["watch_count"], feb["active_count"],
                     feb["category_count"])))

    # -- AC-CWM4 category attribution at the event instant -----------
    apr = month_row(env, "2026-04")
    apr_cats = [cell["category"] for cell in apr["categories"]]
    apr_analytics = cell_row(apr, "analytics")
    apr_data = cell_row(apr, "data")
    jan_cats = [cell["category"] for cell in jan["categories"]]
    ok4 = (apr_cats == ["analytics", "data"]
           and apr_analytics["watch_count"] == 1
           and apr_data["watch_count"] == 1
           and "analytics" not in [c["category"]
                                   for c in mar["categories"]]
           and jan_cats == ["data", "tools", None]
           and jan["categories"][-1]["category"] is None
           and env["category_count"] == 4)
    record("AC-CWM4", ok4,
           "apr_cats=%r analytics=%r jan_cats=%r"
           % (apr_cats, apr_analytics["watch_count"], jan_cats))

    # -- AC-CWM5 conservation three ways ----------------------------
    def sums(env_view):
        w = sum(r["watch_count"] for r in env_view["months"])
        u = sum(r["unwatch_count"] for r in env_view["months"])
        n = sum(r["net_count"] for r in env_view["months"])
        return w, u, n

    cell_sums_ok = True
    for row in env["months"]:
        if sum(c["watch_count"] for c in row["categories"]) \
                != row["watch_count"]:
            cell_sums_ok = False
        if sum(c["unwatch_count"] for c in row["categories"]) \
                != row["unwatch_count"]:
            cell_sums_ok = False
        if sum(c["net_count"] for c in row["categories"]) \
                != row["net_count"]:
            cell_sums_ok = False
        if row["category_count"] != len(row["categories"]):
            cell_sums_ok = False
    w, u, n = sums(env)
    tw, tu, tn = sums(trimmed)
    ok5 = (cell_sums_ok
           and (w, u, n) == (env["watch_count"],
                             env["unwatch_count"],
                             env["net_count"])
           and (w, u, n) == (7, 2, 5)
           and env["months"][-1]["active_count"] \
           == env["live_watch_count"] == 5
           and (tw, tu, tn) == (trimmed["watch_count"],
                                trimmed["unwatch_count"],
                                trimmed["net_count"])
           and (tw, tu, tn) == (6, 2, 4)
           and trimmed["months"][-1]["active_count"] \
           == trimmed["live_watch_count"] == 4
           and market["watch_count"] == env["watch_count"] == 7
           and market["unwatch_count"] == env["unwatch_count"] == 2
           and market["live_watch_count"] == env["live_watch_count"] == 5)
    record("AC-CWM5", ok5,
           "cells=%r sums=%r/%r last_row_active=%r market=%r"
           % (cell_sums_ok, (w, u, n), (tw, tu, tn),
              env["months"][-1]["active_count"],
              (market["watch_count"], market["unwatch_count"],
               market["live_watch_count"])))

    # -- AC-CWM6 participant distinctness, peak, monthly change ------
    jan_none = cell_row(jan, None)
    feb_active = feb["active_count"]
    row_sums_buyers = sum(c["buyer_count"]
                          for r in env["months"]
                          for c in r["categories"])
    row_sums_listings = sum(c["listing_count"]
                            for r in env["months"]
                            for c in r["categories"])
    ok6 = (jan_tools["buyer_count"] == 2
           and jan_tools["listing_count"] == 1
           and jan_none["buyer_count"] == 1
           and mar_data["buyer_count"] == 2
           and mar_data["listing_count"] == 1
           and env["buyer_count"] == 4
           and env["listing_count"] == 4
           and env["buyer_count"] <= row_sums_buyers
           and env["listing_count"] <= row_sums_listings
           and env["peak_month"] == "2026-01"
           and env["peak_watch_count"] == 4
           and env["month_over_month_change"] == -2
           and trimmed["peak_month"] == "2026-01"
           and trimmed["peak_watch_count"] == 3
           and trimmed["month_over_month_change"] == -2
           and feb_active == 4)
    record("AC-CWM6", ok6,
           "buyers=%r/%r peak=%r mom=%r trimmed=%r"
           % (env["buyer_count"], row_sums_buyers,
              (env["peak_month"], env["peak_watch_count"]),
              env["month_over_month_change"],
              (trimmed["peak_watch_count"],
               trimmed["month_over_month_change"])))

    # -- AC-CWM7 the include_uncategorized gate ----------------------
    trimmed_cats = set()
    for row in trimmed["months"]:
        for cell in row["categories"]:
            trimmed_cats.add(cell["category"])
    trim_jan = month_row(trimmed, "2026-01")
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_codes = []
    for bad in (1, 0, "yes", [], {}, None, 1.0):
        try:
            am.api_category_watch_months(bad)
        except A.ApiMarketError as exc:
            bad_codes.append(exc.code)
        else:
            bad_codes.append("ACCEPTED")
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (None not in trimmed_cats
           and trim_jan["watch_count"] == 3
           and trim_jan["category_count"] == 2
           and trimmed["category_count"] == 3
           and bad_codes == [A.E_AM_BAD_ARGS] * 7
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-CWM7", ok7,
           "trim_cats=%r trim_jan=%r gates=%r frozen=%r"
           % (sorted(str(c) for c in trimmed_cats),
              (trim_jan["watch_count"], trim_jan["category_count"]),
              bad_codes, digests_before == digests_after))

    # -- AC-CWM8 pure read, determinism and hygiene ------------------
    call_a = dumps(am.api_category_watch_months())
    call_b = dumps(am.api_category_watch_months())
    call_t = dumps(am.api_category_watch_months(False))
    led2, metered2, dk2, _gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    call_c = dumps(am2.api_category_watch_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, _gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    call_d = dumps(am3.api_category_watch_months())
    call_dt = dumps(am3.api_category_watch_months(False))
    close_stack(am3, dk3, metered3, led3)
    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (call_a == call_b == call_c == call_d == dumps(env)
           and call_t == call_dt == dumps(trimmed)
           and b'"ledger-apimarket-categorywatchmonths"' in recon
           and b"test_apimarket_categorywatchmonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-CWM8", ok8,
           "bytes_same=%r wired=%r ascii_lf=%r"
           % (call_a == call_d,
              b'"ledger-apimarket-categorywatchmonths"' in recon,
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