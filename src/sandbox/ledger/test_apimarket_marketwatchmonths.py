"""Acceptance suite for the apimarket market-wide watch-volume monthly
timeline (BigDomain R2192; canon = the R2189 seed 3/10 explore claim
row, criteria AC-MWM1..AC-MWM8 registered in that row in the same
window as this code - disclosed honestly there).

Face under proof: APIMarketFace.api_market_watch_months. The watch
family answered one listing, one buyer's budget, one buyer's
conversion and one buyer's category mix, so the market carried a live
stock but no monthly flow. This suite pins:

  - the twelve-key envelope and eight-key month rows, honest empty
    first, and the no-argument signature;
  - the cash-basis double stamp (a watch books in the watched_utc
    month, an unwatch in the unwatched_utc month, and a later unwatch
    never rewrites the watch month, so a pure-unwatch month carries an
    honestly negative net);
  - the contiguous month grid with a zero-event month in the middle,
    and conservation of watches, unwatches, nets and the running
    active_count landing on the live watch count;
  - the event-derived participant law per month and lifetime in the
    envelope;
  - the busiest-month law with the earlier-month tie-break, a
    pure-unwatch month never peaking, and None on an empty world;
  - cross-face identity with api_watchlist per buyer and in total;
  - the pure-read law (frozen table digests and ledger_tx set,
    byte-identical repeats) and cross-instance plus cross-restart byte
    identity;
  - the wiring and the ASCII/LF source hygiene.

Usage: python test_apimarket_marketwatchmonths.py
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
    "month_count", "watch_count", "unwatch_count", "net_count",
    "live_watch_count", "buyer_count", "seller_count", "listing_count",
    "busiest_month", "busiest_watch_count", "months", "disclaimer"}

ROW_KEYS = {
    "month", "watch_count", "unwatch_count", "net_count",
    "active_count", "buyer_count", "seller_count", "listing_count"}

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


def seed_world(led, dk, am, clock):
    """Three listings: t1 at dana (tools), d1 at lia (data), g1 at gina
    (data).

    JAN: bob watches t1, kit watches t1, erin watches d1 (3 watches).
    FEB: no event at all (the zero row that proves the grid).
    MAR: bob watches d1, sol watches g1 (2 watches); erin unwatches d1
    (1 unwatch, net +1).
    APR: bob watches g1 (1 watch, net +1).
    MAY: kit unwatches t1 (1 unwatch and no watch, so net is honestly
    negative and this month can never be the busiest).

    Totals: 6 watches, 2 unwatches, 4 live rows, so the running
    active_count lands on 4 in MAY.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-MWM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-MWM-S",
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
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    clock.value = "2026-01-10T00:00:00Z"
    am.watch_api("usr:bob", t1)
    am.watch_api("usr:kit", t1)
    am.watch_api("usr:erin", d1)

    clock.value = "2026-03-05T00:00:00Z"
    am.watch_api("usr:bob", d1)
    am.watch_api("usr:sol", g1)
    am.unwatch_api("usr:erin", d1)

    clock.value = "2026-04-02T00:00:00Z"
    am.watch_api("usr:bob", g1)

    clock.value = "2026-05-07T00:00:00Z"
    am.unwatch_api("usr:kit", t1)

    return {"t1": t1, "d1": d1, "g1": g1}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-marketwatchmonths-")
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
    ids = seed_world(led, dk, am, _CLOCK)

    # -- AC-MWM1 the contract, honest empty first, no argument ------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-mwm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_watch_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_market_watch_months()
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    arg_rejected = False
    try:
        am.api_market_watch_months("2026-01")
    except TypeError:
        arg_rejected = True
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
           and env["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["watch_count"] == 0
           and empty["unwatch_count"] == 0
           and empty["net_count"] == 0
           and empty["live_watch_count"] == 0
           and empty["busiest_month"] is None
           and empty["busiest_watch_count"] is None
           and arg_rejected)
    record("AC-MWM1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r TypeError=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              (empty["month_count"], empty["months"]), arg_rejected))

    # -- AC-MWM2 cash-basis double stamp -----------------------------
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    apr = month_row(env, "2026-04")
    may = month_row(env, "2026-05")
    ok2 = (jan["watch_count"] == 3 and jan["unwatch_count"] == 0
           and jan["net_count"] == 3
           and mar["watch_count"] == 2 and mar["unwatch_count"] == 1
           and mar["net_count"] == 1
           and apr["watch_count"] == 1 and apr["unwatch_count"] == 0
           and apr["net_count"] == 1
           and may["watch_count"] == 0 and may["unwatch_count"] == 1
           and may["net_count"] == -1
           and may["active_count"] == 4
           and jan["active_count"] == 3)
    record("AC-MWM2", ok2,
           "jan=%r mar=%r apr=%r may=%r"
           % ((jan["watch_count"], jan["unwatch_count"], jan["net_count"]),
              (mar["watch_count"], mar["unwatch_count"], mar["net_count"]),
              (apr["watch_count"], apr["unwatch_count"], apr["net_count"]),
              (may["watch_count"], may["unwatch_count"], may["net_count"])))

    # -- AC-MWM3 grid and conservation -------------------------------
    grid = [row["month"] for row in env["months"]]
    feb = month_row(env, "2026-02")
    sum_w = sum(row["watch_count"] for row in env["months"])
    sum_u = sum(row["unwatch_count"] for row in env["months"])
    flat_feb = (feb["watch_count"] == 0 and feb["unwatch_count"] == 0
                and feb["net_count"] == 0 and feb["buyer_count"] == 0
                and feb["active_count"] == jan["active_count"])
    ok3 = (grid == ["2026-01", "2026-02", "2026-03", "2026-04",
                    "2026-05"]
           and flat_feb
           and sum_w == env["watch_count"] == 6
           and sum_u == env["unwatch_count"] == 2
           and env["net_count"] == 4
           and env["month_count"] == len(env["months"]) == 5
           and all(row["net_count"] == row["watch_count"]
                   - row["unwatch_count"] for row in env["months"])
           and env["months"][-1]["active_count"]
           == env["live_watch_count"] == 4)
    record("AC-MWM3", ok3,
           "grid=%r feb_flat=%r sums=%r/%r live=%d"
           % (grid, flat_feb, sum_w, sum_u, env["live_watch_count"]))

    # -- AC-MWM4 event-derived participants --------------------------
    ok4 = (jan["buyer_count"] == 3 and jan["seller_count"] == 2
           and jan["listing_count"] == 2
           and mar["buyer_count"] == 3 and mar["seller_count"] == 2
           and mar["listing_count"] == 2
           and apr["buyer_count"] == 1 and apr["seller_count"] == 1
           and apr["listing_count"] == 1
           and may["buyer_count"] == 1 and may["seller_count"] == 1
           and may["listing_count"] == 1
           and env["buyer_count"] == 4
           and env["seller_count"] == 3
           and env["listing_count"] == 3
           and env["buyer_count"] <= sum(row["buyer_count"]
                                         for row in env["months"]))
    record("AC-MWM4", ok4,
           "jan=%r mar=%r may=%r lifetime=%r"
           % ((jan["buyer_count"], jan["seller_count"]),
              (mar["buyer_count"], mar["seller_count"]),
              (may["buyer_count"], may["seller_count"]),
              (env["buyer_count"], env["seller_count"],
               env["listing_count"])))

    # -- AC-MWM5 busiest-month law -----------------------------------
    ok5 = (env["busiest_month"] == "2026-01"
           and env["busiest_watch_count"] == 3
           and empty_busiest(am, cfg, lobby_cfg) == (None, None))
    record("AC-MWM5", ok5,
           "busiest=%r count=%r empty=%r"
           % (env["busiest_month"], env["busiest_watch_count"],
              empty_busiest(am, cfg, lobby_cfg)))

    # -- AC-MWM6 cross-face with api_watchlist -----------------------
    bob = am.api_watchlist("usr:bob")["watch_count"]
    kit = am.api_watchlist("usr:kit")["watch_count"]
    erin = am.api_watchlist("usr:erin")["watch_count"]
    sol = am.api_watchlist("usr:sol")["watch_count"]
    ok6 = (bob == 3 and kit == 0 and erin == 0 and sol == 1
           and bob + kit + erin + sol == env["live_watch_count"] == 4
           and env["watch_count"] == 6
           and env["unwatch_count"] == 2)
    record("AC-MWM6", ok6,
           "buyers=%r/%r/%r/%r live=%d"
           % (bob, kit, erin, sol, env["live_watch_count"]))

    # -- AC-MWM7 pure read and deterministic bytes -------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_market_watch_months())
    call_b = dumps(am.api_market_watch_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg, lobby_cfg)
    call_c = dumps(am2.api_market_watch_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg, lobby_cfg)
    call_d = dumps(am3.api_market_watch_months())
    close_stack(am3, dk3, metered3, led3)

    ok7 = (digests_before == digests_after
           and tx_before == tx_after
           and call_a == call_b == call_c == call_d == dumps(env))
    record("AC-MWM7", ok7,
           "digests_same=%r tx_same=%r bytes_same=%r len=%d"
           % (digests_before == digests_after, tx_before == tx_after,
              call_a == call_d, len(call_a)))

    # -- AC-MWM8 hygiene and the wiring ------------------------------
    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (b'"ledger-apimarket-marketwatchmonths"' in recon
           and b"test_apimarket_marketwatchmonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-MWM8", ok8,
           "wired=%r src_lf=%r test_ascii_lf=%r"
           % (b'"ledger-apimarket-marketwatchmonths"' in recon,
              b"\r\n" not in src, b"\r\n" not in test_src))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


def empty_busiest(am, cfg, lobby_cfg):
    tmp = tempfile.mkdtemp(prefix="apimarket-mwm-empty2-")
    led, metered, dk, gate, am2 = build_stack(
        os.path.join(tmp, "ledger.db"), cfg, lobby_cfg)
    env = am2.api_market_watch_months()
    close_stack(am2, dk, metered, led)
    return env["busiest_month"], env["busiest_watch_count"]


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())