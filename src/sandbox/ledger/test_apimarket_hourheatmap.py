"""Acceptance suite for the apimarket market activity heatmap face
(BigDomain R2165; canon = the R2149 reseed row claimed in R2165,
criteria AC-MHH1..AC-MHH8 registered in that claim row BEFORE this
code existed - honesty law; the AC-MHH prefix and the
api_market_hour_heatmap name occupy only that seed row text, while
test_apimarket_hourheatmap, ledger-apimarket-hourheatmap,
busiest_hour, busiest_weekday and hour_of_day were all git-grep
zero-occupancy anchored against HEAD 2026-10-27, rc=1).

Face under proof: APIMarketFace.api_market_hour_heatmap. Every time
axis the market had was a month (api_market_months, api_revenue_months,
api_buyer_months, api_category_refund_months) or an event list
(api_market_feed), so "which hour of the day and which weekday does
the market trade in" had no face at all. This suite pins the new grid:

  - the sixteen-key envelope, the always-complete 24/7/168 grid and
    the honest empty world first;
  - conservation across all three views plus the per-row net law;
  - the cash-basis double axis: a sale books at purchased_utc, a
    refund at refunded_utc and never rewrites the sale bucket;
  - participant authority (within-row distinct counts vs the
    lifetime envelope count, the honest asymmetry);
  - the peak law: count, then gross, then the lower index; a
    refund-only bucket is never a peak; None on an empty market;
  - orthogonality with the existing faces (unchanged byte for byte)
    and with write actions (a delist does not move history);
  - the pure-read law, the no-argument contract and cross-restart
    byte identity.

Usage: python test_apimarket_hourheatmap.py
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
    "hour_count", "weekday_count", "cell_count", "sales_count",
    "gross", "refund_count", "refunded", "net", "buyer_count",
    "seller_count", "busiest_hour", "busiest_weekday", "disclaimer",
    "hours", "weekdays", "cells"}

HOUR_KEYS = {
    "hour", "sales_count", "gross", "refund_count", "refunded",
    "net", "buyer_count", "seller_count"}

WEEKDAY_KEYS = {
    "weekday", "weekday_name", "sales_count", "gross", "refund_count",
    "refunded", "net", "buyer_count", "seller_count"}

CELL_KEYS = {"weekday", "hour", "sales_count", "refund_count"}

WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions",
          "apimarket_rating_revisions")

# Fixed instants: 2026-10-26 is a Monday, 2026-10-27 a Tuesday,
# 2026-10-24 a Saturday and 2026-10-25 a Sunday.
MON_0915 = "2026-10-26T09:15:00Z"
MON_0945 = "2026-10-26T09:45:00Z"
SUN_1820 = "2026-10-25T18:20:00Z"
TUE_1400 = "2026-10-27T14:00:00Z"
SUN_0305 = "2026-10-25T03:05:00Z"
SAT_2130 = "2026-10-24T21:30:00Z"
TUE_2310 = "2026-10-27T23:10:00Z"
SUN_2240 = "2026-10-25T22:40:00Z"


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


def backdate_purchase(am, purchase_id, stamp):
    """Fixture setup only: the face reads what the append-only table
    stores, and the public purchase door stamps the wall clock, so a
    deterministic hour grid needs fixed instants."""
    conn = sqlite3.connect(am.db_path)
    conn.execute("UPDATE apimarket_purchases SET purchased_utc = ?"
                 " WHERE purchase_id = ?", (stamp, purchase_id))
    conn.commit()
    conn.close()


def backdate_refund(am, purchase_id, stamp):
    conn = sqlite3.connect(am.db_path)
    conn.execute("UPDATE apimarket_refunds SET refunded_utc = ?"
                 " WHERE purchase_id = ?", (stamp, purchase_id))
    conn.commit()
    conn.close()


def fund(led, who):
    led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:" + who, "credit", 400)],
               "manual:fund-" + who, "suite funding " + who)


def seed_world(led, dk, am):
    """dana owns d1 (data, 10) and d2 (tools, 3); gina owns g1
    (media, 6). Six purchases across four weekdays and six hours;
    two of them refunded inside a different bucket than the sale."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-MHH-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-MHH-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        fund(led, who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:gina", "gina-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True,
                        category="tools")["listing_id"]
    g1 = am.publish_api("usr:gina", "media-pack", "Media Pack API",
                        "media pipeline pack", PAYLOAD, 6, False,
                        category="media")["listing_id"]
    p_bob_d1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")
    p_bob_d2 = am.purchase_api("usr:bob", d2, "ref-bob-d2")
    p_bob_g1 = am.purchase_api("usr:bob", g1, "ref-bob-g1")
    p_carol = am.purchase_api("usr:carol", d1, "ref-carol-d1")
    p_erin = am.purchase_api("usr:erin", d1, "ref-erin-d1")
    p_dave = am.purchase_api("usr:dave", g1, "ref-dave-g1")
    backdate_purchase(am, p_bob_d1["purchase_id"], MON_0915)
    backdate_purchase(am, p_bob_d2["purchase_id"], MON_0945)
    backdate_purchase(am, p_bob_g1["purchase_id"], SUN_1820)
    backdate_purchase(am, p_carol["purchase_id"], TUE_1400)
    backdate_purchase(am, p_erin["purchase_id"], SUN_0305)
    backdate_purchase(am, p_dave["purchase_id"], SAT_2130)
    am.refund_api("usr:carol", p_carol["purchase_id"],
                  "listing did not match description")
    am.refund_api("usr:erin", p_erin["purchase_id"],
                  "changed my mind")
    backdate_refund(am, p_carol["purchase_id"], TUE_2310)
    backdate_refund(am, p_erin["purchase_id"], SUN_2240)
    return {"d1": d1, "d2": d2, "g1": g1}


def hour_row(env, hour):
    for row in env["hours"]:
        if row["hour"] == hour:
            return row
    return None


def weekday_row(env, day):
    for row in env["weekdays"]:
        if row["weekday"] == day:
            return row
    return None


def cell_row(env, day, hour):
    for row in env["cells"]:
        if row["weekday"] == day and row["hour"] == hour:
            return row
    return None


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-hourheatmap-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    ids = seed_world(led, dk, am)

    # -- AC-MHH1 the contract, honest empty first ----------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-mhh-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_hour_heatmap()
    close_stack(e_am, e_dk, e_metered, e_led)
    warm = am.api_market_hour_heatmap()
    ok1 = (set(warm.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and warm["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and warm["hour_count"] == 24
           and warm["weekday_count"] == 7
           and warm["cell_count"] == 168
           and [r["hour"] for r in warm["hours"]] == list(range(24))
           and [r["weekday"] for r in warm["weekdays"]]
           == list(range(7))
           and [r["weekday_name"] for r in warm["weekdays"]]
           == list(WEEKDAY_NAMES)
           and [(r["weekday"], r["hour"]) for r in warm["cells"]]
           == [(d, h) for d in range(7) for h in range(24)]
           and all(set(r.keys()) == HOUR_KEYS for r in warm["hours"])
           and all(set(r.keys()) == WEEKDAY_KEYS
                   for r in warm["weekdays"])
           and all(set(r.keys()) == CELL_KEYS for r in warm["cells"])
           and empty["sales_count"] == 0
           and empty["gross"] == 0
           and empty["refund_count"] == 0
           and empty["refunded"] == 0
           and empty["net"] == 0
           and empty["buyer_count"] == 0
           and empty["seller_count"] == 0
           and empty["busiest_hour"] is None
           and empty["busiest_weekday"] is None
           and len(empty["hours"]) == 24
           and len(empty["weekdays"]) == 7
           and len(empty["cells"]) == 168
           and all(r["sales_count"] == 0 and r["gross"] == 0
                   for r in empty["hours"]))
    record("AC-MHH1", ok1,
           "env_keys=%d exact=%r grid=%r empty_zero=%r"
           % (len(warm), set(warm.keys()) == ENVELOPE_KEYS,
              (warm["hour_count"], warm["weekday_count"],
               warm["cell_count"]),
              (empty["sales_count"], empty["busiest_hour"])))

    # -- AC-MHH2 conservation across all three views -------------------
    hour_sales = sum(r["sales_count"] for r in warm["hours"])
    hour_gross = sum(r["gross"] for r in warm["hours"])
    hour_refunds = sum(r["refund_count"] for r in warm["hours"])
    hour_refunded = sum(r["refunded"] for r in warm["hours"])
    day_sales = sum(r["sales_count"] for r in warm["weekdays"])
    day_gross = sum(r["gross"] for r in warm["weekdays"])
    day_refunds = sum(r["refund_count"] for r in warm["weekdays"])
    day_refunded = sum(r["refunded"] for r in warm["weekdays"])
    cell_sales = sum(r["sales_count"] for r in warm["cells"])
    cell_refunds = sum(r["refund_count"] for r in warm["cells"])
    ok2 = (warm["sales_count"] == hour_sales == day_sales
           == cell_sales == 6
           and warm["gross"] == hour_gross == day_gross == 45
           and warm["refund_count"] == hour_refunds == day_refunds
           == cell_refunds == 2
           and warm["refunded"] == hour_refunded == day_refunded == 20
           and warm["net"] == 25
           and all(r["net"] == r["gross"] - r["refunded"]
                   for r in warm["hours"] + warm["weekdays"])
           and warm["hour_count"] == len(warm["hours"])
           and warm["weekday_count"] == len(warm["weekdays"])
           and warm["cell_count"] == len(warm["cells"]))
    record("AC-MHH2", ok2,
           "sales=%r gross=%r refunds=%r refunded=%r net=%r"
           % ((warm["sales_count"], hour_sales, day_sales, cell_sales),
              (warm["gross"], hour_gross, day_gross),
              (warm["refund_count"], hour_refunds, day_refunds,
               cell_refunds),
              (warm["refunded"], hour_refunded, day_refunded),
              warm["net"]))

    # -- AC-MHH3 the cash-basis double axis ----------------------------
    h9 = hour_row(warm, 9)
    h18 = hour_row(warm, 18)
    h3 = hour_row(warm, 3)
    h14 = hour_row(warm, 14)
    h21 = hour_row(warm, 21)
    h22 = hour_row(warm, 22)
    h23 = hour_row(warm, 23)
    mon = weekday_row(warm, 0)
    tue = weekday_row(warm, 1)
    sat = weekday_row(warm, 5)
    sun = weekday_row(warm, 6)
    months = am.api_market_months()
    ok3 = (h9["sales_count"] == 2 and h9["gross"] == 13
           and h9["refund_count"] == 0 and h9["refunded"] == 0
           and h9["net"] == 13
           and h18["sales_count"] == 1 and h18["gross"] == 6
           and h3["sales_count"] == 1 and h3["gross"] == 10
           and h14["sales_count"] == 1 and h14["gross"] == 10
           and h21["sales_count"] == 1 and h21["gross"] == 6
           and h22["sales_count"] == 0 and h22["gross"] == 0
           and h22["refund_count"] == 1 and h22["refunded"] == 10
           and h22["net"] == -10
           and h23["sales_count"] == 0 and h23["gross"] == 0
           and h23["refund_count"] == 1 and h23["refunded"] == 10
           and h23["net"] == -10
           and cell_row(warm, 0, 9) == {"weekday": 0, "hour": 9,
                                        "sales_count": 2,
                                        "refund_count": 0}
           and cell_row(warm, 1, 9) == {"weekday": 1, "hour": 9,
                                        "sales_count": 0,
                                        "refund_count": 0}
           and cell_row(warm, 6, 18) == {"weekday": 6, "hour": 18,
                                         "sales_count": 1,
                                         "refund_count": 0}
           and cell_row(warm, 0, 9)["sales_count"]
           == mon["sales_count"]
           and cell_row(warm, 6, 3)["sales_count"] == 1
           and cell_row(warm, 1, 23)["refund_count"] == 1
           and mon["sales_count"] == 2 and mon["gross"] == 13
           and mon["refund_count"] == 0
           and tue["sales_count"] == 1 and tue["gross"] == 10
           and tue["refund_count"] == 1 and tue["refunded"] == 10
           and tue["net"] == 0
           and sat["sales_count"] == 1 and sat["gross"] == 6
           and sun["sales_count"] == 2 and sun["gross"] == 16
           and sun["refund_count"] == 1 and sun["net"] == 6
           and months["lifetime_sales_count"] == warm["sales_count"]
           and months["lifetime_gross"] == warm["gross"]
           and months["lifetime_refund_count"] == warm["refund_count"]
           and months["lifetime_refunded"] == warm["refunded"]
           and months["lifetime_net"] == warm["net"])
    record("AC-MHH3", ok3,
           "h9=%r h22=%r sun=%r cross_face=%r"
           % ((h9["sales_count"], h9["gross"]),
              (h22["sales_count"], h22["refund_count"], h22["net"]),
              (sun["sales_count"], sun["gross"], sun["net"]),
              months["lifetime_net"] == warm["net"]))

    # -- AC-MHH4 participant authority ---------------------------------
    hour_buyer_sum = sum(r["buyer_count"] for r in warm["hours"])
    hour_seller_sum = sum(r["seller_count"] for r in warm["hours"])
    ok4 = (warm["buyer_count"] == 4
           and warm["seller_count"] == 2
           and hour_buyer_sum == 5
           and hour_buyer_sum > warm["buyer_count"]
           and h9["buyer_count"] == 1
           and h9["seller_count"] == 1
           and h18["buyer_count"] == 1
           and all(r["buyer_count"] == 0 and r["seller_count"] == 0
                   for r in warm["hours"]
                   if r["sales_count"] == 0)
           and h22["buyer_count"] == 0 and h22["seller_count"] == 0
           and h23["buyer_count"] == 0 and h23["seller_count"] == 0
           and sum(r["buyer_count"] for r in warm["weekdays"])
           == hour_buyer_sum
           and sum(r["seller_count"] for r in warm["weekdays"])
           == hour_seller_sum)
    record("AC-MHH4", ok4,
           "env=%r hour_sum=%r h9=%r refund_only_zero=%r"
           % ((warm["buyer_count"], warm["seller_count"]),
              (hour_buyer_sum, hour_seller_sum),
              (h9["buyer_count"], h9["seller_count"]),
              h22["buyer_count"] == 0))

    # -- AC-MHH5 the peak law ------------------------------------------
    tie_tmp = tempfile.mkdtemp(prefix="apimarket-mhh-tie-")
    t_led, t_metered, t_dk, _t_gate, t_am = build_stack(
        os.path.join(tie_tmp, "ledger.db"), cfg, lobby_cfg)
    t_led.mint_to_pool("pool:reserve", 5000, "SETTLE-MHH-TA",
                       "settlement")
    t_led.mint_to_pool("pool:share", 5000, "SETTLE-MHH-TS",
                       "settlement")
    for who in ("frank", "gina"):
        fund(t_led, who)
    t_dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    t1 = t_am.publish_api("usr:dana", "flat-svc", "Flat Service",
                          "evenly priced service", PAYLOAD, 5, False,
                          category="data")["listing_id"]
    tp1 = t_am.purchase_api("usr:frank", t1, "ref-frank")
    tp2 = t_am.purchase_api("usr:gina", t1, "ref-gina")
    backdate_purchase(t_am, tp1["purchase_id"],
                      "2026-10-26T11:10:00Z")
    backdate_purchase(t_am, tp2["purchase_id"],
                      "2026-10-26T04:10:00Z")
    tie = t_am.api_market_hour_heatmap()
    close_stack(t_am, t_dk, t_metered, t_led)
    ok5 = (warm["busiest_hour"] == 9
           and warm["busiest_weekday"] == 6
           and sun["sales_count"] == mon["sales_count"] == 2
           and sun["gross"] > mon["gross"]
           and hour_row(warm, 22)["sales_count"] == 0
           and hour_row(warm, 23)["sales_count"] == 0
           and tie["sales_count"] == 2
           and tie["busiest_hour"] == 4
           and tie["busiest_weekday"] == 0
           and hour_row(tie, 4)["gross"] == hour_row(tie, 11)["gross"]
           == 5)
    record("AC-MHH5", ok5,
           "peak_hour=%r peak_day=%r tie_hour=%r"
           " (sun %d/%d vs mon %d/%d)"
           % (warm["busiest_hour"], warm["busiest_weekday"],
              tie["busiest_hour"], sun["sales_count"], sun["gross"],
              mon["sales_count"], mon["gross"]))

    # -- AC-MHH6 orthogonality with the existing faces -----------------
    stats_before = dumps(am.api_market_stats())
    months_before = dumps(am.api_market_months())
    feed_before = dumps(am.api_market_feed())
    heat_before = dumps(am.api_market_hour_heatmap())
    for _ in range(3):
        am.api_market_hour_heatmap()
    stats_after = dumps(am.api_market_stats())
    months_after = dumps(am.api_market_months())
    feed_after = dumps(am.api_market_feed())
    am.delist_api("usr:dana", ids["d1"])
    after_delist = dumps(am.api_market_hour_heatmap())
    am.relist_api("usr:dana", ids["d1"])
    after_relist = dumps(am.api_market_hour_heatmap())
    ok6 = (stats_before == stats_after
           and months_before == months_after
           and feed_before == feed_after
           and heat_before == after_delist == after_relist)
    record("AC-MHH6", ok6,
           "stats=%r months=%r feed=%r delist_same=%r relist_same=%r"
           % (stats_before == stats_after, months_before == months_after,
              feed_before == feed_after, heat_before == after_delist,
              heat_before == after_relist))

    # -- AC-MHH7 the pure-read law and the no-argument contract --------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    first = dumps(am.api_market_hour_heatmap())
    second = dumps(am.api_market_hour_heatmap())
    third = dumps(am.api_market_hour_heatmap())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    arg_forms = []
    for bad in (1, "x", True, [], {}):
        try:
            am.api_market_hour_heatmap(bad)
            arg_forms.append("NO-ERROR:%r" % (bad,))
        except TypeError:
            arg_forms.append("TypeError")
        except Exception as exc:                  # noqa: BLE001
            arg_forms.append(type(exc).__name__)
    ok7 = (first == second == third
           and digests_before == digests_after
           and tx_before == tx_after
           and arg_forms == ["TypeError"] * 5)
    record("AC-MHH7", ok7,
           "repeat=%r frozen=%r tx=%r args=%r"
           % (first == second == third,
              digests_before == digests_after, tx_before == tx_after,
              arg_forms))

    # -- AC-MHH8 cross-restart identity and the wiring ------------------
    final = dumps(am.api_market_hour_heatmap())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_inst = dumps(am.api_market_hour_heatmap())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_inst = dumps(am.api_market_hour_heatmap())
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_market_hour_heatmap()
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    with open(os.path.abspath(__file__), "rb") as handle:
        own_text = handle.read().decode("ascii")
    ok8 = (final == second_inst == third_inst
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-hourheatmap" in runner_text
           and len(own_text) > 0)
    record("AC-MHH8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r ascii=%r"
           % (hashlib.sha256(final.encode("utf-8"))
              .hexdigest()[:16],
              final == second_inst == third_inst,
              tx_b == tx_a, dig_b == dig_a,
              shas_before == shas_after,
              "ledger-apimarket-hourheatmap" in runner_text,
              len(own_text) > 0))

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