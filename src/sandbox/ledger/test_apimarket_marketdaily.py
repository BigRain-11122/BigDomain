"""Acceptance suite for the apimarket market-wide calendar-day trade
timeline (BigDomain R2178; canon = the explore-queue claim row seeded
and claimed in R2178, criteria AC-MDL1..AC-MDL8 registered in that
claim note BEFORE this code existed - honesty law; the AC-MDL prefix,
the api_market_daily name, this suite name and the
ledger-apimarket-marketdaily runner label were all git-grep -F
zero-occupancy anchored 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_market_daily. api_market_months
answers one UTC month, api_market_hour_heatmap answers an hour-of-day
x weekday slot aggregated across the whole history (no date at all),
api_market_buyer_retention answers cohort month cells and
api_market_feed answers event rows, so the daily settlement sheet -
"what did the market do on one calendar day, and which day was the
busiest" - had no face. This window pins it:

  - a seventeen-key envelope and a thirteen-key day row, days
    ascending;
  - the cash-basis attribution law one granularity finer than the
    month face: a sale books on the day of purchased_utc, a refund
    books on the day of refunded_utc and never rewrites the day the
    sale landed in;
  - the day boundary law at 23:59:59Z vs 00:00:00Z;
  - CONTIGUITY: every day of the activity extent is present and a
    quiet day is an honest zero row, never a gap;
  - participant counts derived from purchases only (a refund-only day
    honestly reports zero buyers/sellers/listings);
  - per-row arithmetic, envelope-as-window conservation and a raw
    table cross-check plus the api_market_stats identity;
  - inclusive start_day/end_day clipping, the window gate family and
    the honest empty envelope for a window holding no activity;
  - busiest/quietest/mean extremes over ACTIVE days only;
  - zero row mutations, zero token movement and cross-restart byte
    identity plus runner wiring.

Usage: python test_apimarket_marketdaily.py
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
import apimarket as A                 # noqa: E402 (R2178 face)
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

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

ENVELOPE_KEYS = {"day_count", "active_day_count", "zero_day_count",
                 "window_start", "window_end", "lifetime_sales_count",
                 "lifetime_gross", "lifetime_refund_count",
                 "lifetime_refunded", "lifetime_net",
                 "lifetime_dev_revenue", "lifetime_platform_revenue",
                 "busiest_day", "quietest_active_day",
                 "avg_net_per_active_day", "disclaimer", "days"}
ROW_KEYS = {"day", "sales_count", "gross", "refund_count", "refunded",
            "net", "dev_share", "platform_share", "dev_share_net",
            "platform_share_net", "buyer_count", "seller_count",
            "listing_count"}
MONEY_KEYS = ("sales_count", "gross", "refund_count", "refunded",
              "net", "dev_share", "platform_share", "dev_share_net",
              "platform_share_net")

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions")
POOLS = ("pool:reserve", "pool:share")

BAD_DAYS = (123, "", "2026-8-31", "2026-13-01", "2026-02-30",
            "20260831", "2026-08-31T00:00:00Z", "2026-08-31 ")


class Clock(object):
    """Deterministic stamp holder: the suite sets one explicit UTC
    string before each write so the day buckets are reproducible
    (module clock patched, restored in main's finally block)."""

    def __init__(self):
        self.value = "2026-08-31T23:59:59Z"

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


def frozen_digests(am):
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


def pool_balances(led):
    return {pool: led.balance(pool) for pool in POOLS}


def raw_totals(am):
    """Ground truth read straight from the market tables, never from
    the face under proof (so conservation is a real cross-check)."""
    conn = sqlite3.connect(am.db_path)
    gross, sales = conn.execute(
        "SELECT COALESCE(SUM(price_paid),0), COUNT(*)"
        " FROM apimarket_purchases").fetchone()
    refunded, refunds, dev_back, plat_back = conn.execute(
        "SELECT COALESCE(SUM(amount),0), COUNT(*),"
        " COALESCE(SUM(dev_share),0), COALESCE(SUM(platform_share),0)"
        " FROM apimarket_refunds").fetchone()
    dev_fwd, plat_fwd = conn.execute(
        "SELECT COALESCE(SUM(dev_share),0),"
        " COALESCE(SUM(platform_share),0)"
        " FROM apimarket_purchases").fetchone()
    conn.close()
    return (int(gross), int(sales), int(refunded), int(refunds),
            int(dev_fwd) - int(dev_back),
            int(plat_fwd) - int(plat_back))


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


def seed_world(led, dk, am, clock):
    """Owner dana with two listings; frank a SECOND registered
    developer. Sales are stamped so both the DAY boundary and the
    quiet-day honesty are provable: bob's d1 purchase lands at
    2026-08-31T23:59:59Z (AUG 31), carol's d1 purchase at
    2026-09-01T00:00:00Z (SEP 01, one second later), bob's d2
    purchase on 2026-09-15 and erin's d3 purchase on 2026-09-20.
    One refund is then booked on 2026-10-02, so the AUG 31 row must
    stay frozen while the refund day carries a negative net and zero
    participants (a refund-only day)."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-MDL-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-MDL-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    d3 = am.publish_api("usr:frank", "chart-render",
                        "Chart Render API",
                        "chart image render endpoint", PAYLOAD, 5,
                        False)["listing_id"]
    clock.value = "2026-08-31T23:59:59Z"
    p1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")["purchase_id"]
    clock.value = "2026-09-01T00:00:00Z"
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    clock.value = "2026-09-15T12:00:00Z"
    am.purchase_api("usr:bob", d2, "ref-bob-d2")
    clock.value = "2026-09-20T08:30:00Z"
    am.purchase_api("usr:erin", d3, "ref-erin-d3")
    clock.value = "2026-10-02T00:00:00Z"
    am.refund_api("usr:bob", p1, "day-crossing refund")
    splits = {}
    for listing_id, price in ((d1, 10), (d2, 3), (d3, 5)):
        splits[listing_id] = A.split_amount(price, am.params)
    return d1, d2, d3, p1, splits


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-marketdaily-")
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
        return run(db_path, cfg, lobby_cfg, tmp, shas_before, clock)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, tmp, shas_before, clock):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d3, p1, splits = seed_world(led, dk, am, clock)
    dev1, plat1 = splits[d1]

    env = am.api_market_daily()
    days = env["days"]
    by_day = {r["day"]: r for r in days}

    # -- AC-MDL1 envelope + row contract -------------------------------
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["day_count"] == len(days) == 33
           and env["window_start"] == "2026-08-31"
           and env["window_end"] == "2026-10-02"
           and [r["day"] for r in days] == sorted(r["day"] for r in days)
           and all(set(r.keys()) == ROW_KEYS for r in days)
           and env["disclaimer"] == DISCLAIMER)
    record("AC-MDL1", ok1,
           "keys ok=%r day_count=%d window=%s..%s ordered=%r"
           % (set(env.keys()) == ENVELOPE_KEYS, env["day_count"],
              env["window_start"], env["window_end"],
              [r["day"] for r in days] == sorted(
                  r["day"] for r in days)))

    # -- AC-MDL2 day boundary, cash basis, refund-day honesty ----------
    aug = by_day["2026-08-31"]
    sep1 = by_day["2026-09-01"]
    sep15 = by_day["2026-09-15"]
    sep20 = by_day["2026-09-20"]
    oct2 = by_day["2026-10-02"]
    ok2 = (aug["sales_count"] == 1
           and aug["gross"] == 10
           and aug["buyer_count"] == 1
           and aug["seller_count"] == 1
           and aug["listing_count"] == 1
           and sep1["sales_count"] == 1
           and sep1["gross"] == 10
           and sep15["gross"] == 3
           and sep20["gross"] == 5
           and oct2["sales_count"] == 0
           and oct2["gross"] == 0
           and oct2["refund_count"] == 1
           and oct2["refunded"] == 10
           and oct2["net"] == -10
           and oct2["buyer_count"] == 0
           and oct2["seller_count"] == 0
           and oct2["listing_count"] == 0)
    record("AC-MDL2", ok2,
           "aug31={s:%d g:%d b:%d s:%d l:%d} sep01={s:%d g:%d}"
           " oct02={s:%d r:%d refunded:%d net:%d parts:%d/%d/%d}"
           % (aug["sales_count"], aug["gross"], aug["buyer_count"],
              aug["seller_count"], aug["listing_count"],
              sep1["sales_count"], sep1["gross"], oct2["sales_count"],
              oct2["refund_count"], oct2["refunded"], oct2["net"],
              oct2["buyer_count"], oct2["seller_count"],
              oct2["listing_count"]))

    # -- AC-MDL3 per-row arithmetic + envelope conservation + raw ------
    row_ok = []
    for r in days:
        row_ok.append(r["gross"] == r["dev_share"] + r["platform_share"])
        row_ok.append(r["net"] == r["gross"] - r["refunded"])
        row_ok.append(r["net"] == (r["dev_share_net"]
                                   + r["platform_share_net"]))
    gross, sales, refunded, refunds, dev_net, plat_net = raw_totals(am)
    sum_ok = (sum(r["gross"] for r in days) == env["lifetime_gross"]
              and sum(r["refunded"] for r in days)
              == env["lifetime_refunded"]
              and sum(r["sales_count"] for r in days)
              == env["lifetime_sales_count"]
              and sum(r["refund_count"] for r in days)
              == env["lifetime_refund_count"]
              and sum(r["net"] for r in days) == env["lifetime_net"]
              and sum(r["dev_share_net"] for r in days)
              == env["lifetime_dev_revenue"]
              and sum(r["platform_share_net"] for r in days)
              == env["lifetime_platform_revenue"])
    ok3 = (all(row_ok) and sum_ok
           and env["lifetime_gross"] == gross == 28
           and env["lifetime_sales_count"] == sales == 4
           and env["lifetime_refunded"] == refunded == 10
           and env["lifetime_refund_count"] == refunds == 1
           and env["lifetime_net"] == 18
           and env["lifetime_dev_revenue"] == dev_net
           and env["lifetime_platform_revenue"] == plat_net
           and aug["dev_share"] == dev1
           and aug["platform_share"] == plat1
           and oct2["dev_share_net"] == -dev1
           and oct2["platform_share_net"] == -plat1)
    record("AC-MDL3", ok3,
           "rows consistent=%r envelope==sums=%r raw g/s/rf/n=%d/%d/%d/%d"
           " net=%d dev=%d plat=%d d1=%r"
           % (all(row_ok), sum_ok, gross, sales, refunded, refunds,
              env["lifetime_net"], env["lifetime_dev_revenue"],
              env["lifetime_platform_revenue"], (dev1, plat1)))

    # -- AC-MDL4 contiguity + honest zero days -------------------------
    labels = [r["day"] for r in days]
    contiguous = all(
        (A.datetime.datetime.strptime(labels[i + 1], "%Y-%m-%d")
         - A.datetime.datetime.strptime(labels[i], "%Y-%m-%d")).days == 1
        for i in range(len(labels) - 1))
    active = [r for r in days
              if r["sales_count"] or r["refund_count"]]
    quiet = [r for r in days
             if not r["sales_count"] and not r["refund_count"]]
    quiet_clean = all(
        all(r[k] == 0 for k in MONEY_KEYS)
        and r["buyer_count"] == 0 and r["seller_count"] == 0
        and r["listing_count"] == 0 for r in quiet)
    ok4 = (len(set(labels)) == len(labels)
           and contiguous
           and env["active_day_count"] == len(active) == 5
           and env["zero_day_count"] == len(quiet) == 28
           and env["active_day_count"] + env["zero_day_count"]
           == env["day_count"]
           and quiet_clean
           and [r["day"] for r in active]
           == ["2026-08-31", "2026-09-01", "2026-09-15", "2026-09-20",
               "2026-10-02"])
    record("AC-MDL4", ok4,
           "unique=%r contiguous=%r active=%d zero=%d sum=%d"
           " quiet rows all-zero=%r"
           % (len(set(labels)) == len(labels), contiguous,
              env["active_day_count"], env["zero_day_count"],
              env["active_day_count"] + env["zero_day_count"],
              quiet_clean))

    # -- AC-MDL5 cross-face identity (month rebucket + market stats) ---
    months = {m["month"]: m for m in am.api_market_months()["months"]}
    rebucket = {}
    for r in days:
        b = rebucket.setdefault(r["day"][:7],
                                {k: 0 for k in MONEY_KEYS})
        for k in MONEY_KEYS:
            b[k] += r[k]
    month_ok = []
    for month, row in months.items():
        b = rebucket.get(month)
        month_ok.append(b is not None
                        and all(row[k] == b[k] for k in MONEY_KEYS))
    stats = am.api_market_stats()
    ok5 = (all(month_ok)
           and set(rebucket) == set(months)
           and env["lifetime_gross"] == stats["gross_tokens"]
           and env["lifetime_sales_count"] == stats["purchase_count"]
           and env["lifetime_refunded"] == stats["refunded_tokens"]
           and env["lifetime_net"] == stats["net_gross_tokens"]
           and env["lifetime_dev_revenue"] == stats["dev_revenue"]
           and env["lifetime_platform_revenue"]
           == stats["platform_revenue"])
    record("AC-MDL5", ok5,
           "month rebucket equal=%r months=%r face/stats gross=%d/%d"
           " net=%d/%d dev=%d/%d plat=%d/%d"
           % (all(month_ok), sorted(rebucket), env["lifetime_gross"],
              stats["gross_tokens"], env["lifetime_net"],
              stats["net_gross_tokens"], env["lifetime_dev_revenue"],
              stats["dev_revenue"], env["lifetime_platform_revenue"],
              stats["platform_revenue"]))

    # -- AC-MDL6 window clipping + gate family + honest empty ----------
    start_only = am.api_market_daily(start_day="2026-09-02")
    end_only = am.api_market_daily(end_day="2026-09-01")
    both = am.api_market_daily(start_day="2026-09-15",
                               end_day="2026-09-20")
    one_day = am.api_market_daily(start_day="2026-09-15",
                                 end_day="2026-09-15")
    outside = am.api_market_daily(start_day="2027-01-01",
                                  end_day="2027-01-31")
    frozen_before = frozen_digests(am)
    tx_before = ledger_tx_ids(led)
    refused = []
    for bad in BAD_DAYS:
        for label in ("start_day", "end_day"):
            try:
                am.api_market_daily(**{label: bad})
                refused.append(False)
            except A.ApiMarketError as exc:
                refused.append(exc.code == A.E_AM_BAD_WINDOW)
    inverted_ok = False
    try:
        am.api_market_daily(start_day="2026-09-20",
                            end_day="2026-09-01")
    except A.ApiMarketError as exc:
        inverted_ok = exc.code == A.E_AM_BAD_WINDOW
    frozen_after = frozen_digests(am)
    tx_after = ledger_tx_ids(led)
    window_ok = (
        start_only["window_start"] == "2026-09-02"
        and start_only["window_end"] == "2026-10-02"
        and start_only["day_count"] == 31
        and start_only["lifetime_gross"] == 8
        and start_only["lifetime_net"] == -2
        and end_only["window_start"] == "2026-08-31"
        and end_only["window_end"] == "2026-09-01"
        and end_only["day_count"] == 2
        and end_only["lifetime_gross"] == 20
        and end_only["lifetime_refunded"] == 0
        and both["day_count"] == 6
        and both["window_start"] == "2026-09-15"
        and both["window_end"] == "2026-09-20"
        and both["lifetime_gross"] == 8
        and one_day["day_count"] == 1
        and one_day["lifetime_gross"] == 3
        and outside["day_count"] == 0
        and outside["days"] == []
        and outside["window_start"] is None
        and outside["busiest_day"] is None
        and outside["avg_net_per_active_day"] is None
        and outside["lifetime_net"] == 0)
    ok6 = (window_ok and all(refused) and inverted_ok
           and frozen_before == frozen_after
           and tx_before == tx_after)
    record("AC-MDL6", ok6,
           "start_only(%d d, g=%d) end_only(%d d, g=%d) both(%d d)"
           " one_day(%d d) outside(%d d) gates=%r inverted=%r"
           " digests frozen=%r"
           % (start_only["day_count"], start_only["lifetime_gross"],
              end_only["day_count"], end_only["lifetime_gross"],
              both["day_count"], one_day["day_count"],
              outside["day_count"], all(refused), inverted_ok,
              frozen_before == frozen_after))

    # -- AC-MDL7 extremes over ACTIVE days only ------------------------
    nets = {r["day"]: r["net"] for r in active}
    ok7 = (env["busiest_day"] == "2026-08-31"
           and nets["2026-08-31"] == 10
           and nets["2026-09-01"] == 10
           and env["quietest_active_day"] == "2026-10-02"
           and nets["2026-10-02"] == -10
           and env["avg_net_per_active_day"] == 3.6
           and quiet[0]["day"] not in (env["busiest_day"],
                                       env["quietest_active_day"]))
    record("AC-MDL7", ok7,
           "busiest=%r (tie 08-31/09-01 at 10) quietest=%r avg=%r"
           % (env["busiest_day"], env["quietest_active_day"],
              env["avg_net_per_active_day"]))

    # -- AC-MDL8 pure read + cross-restart + wiring + hygiene ----------
    tx_b2 = ledger_tx_ids(led)
    pools_b2 = pool_balances(led)
    frozen_b2 = frozen_digests(am)
    first = dumps(am.api_market_daily())
    second = dumps(am.api_market_daily())
    tx_a2 = ledger_tx_ids(led)
    pools_a2 = pool_balances(led)
    frozen_a2 = frozen_digests(am)

    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    two = dumps(am2.api_market_daily())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    three = dumps(am3.api_market_daily())
    close_stack(am3, dk3, metered3, led3)

    empty_dir = os.path.join(tmp, "empty")
    os.makedirs(empty_dir)
    empty_db = os.path.join(empty_dir, "ledger.db")
    led4, metered4, dk4, gate4, am4 = build_stack(
        empty_db, cfg, lobby_cfg)
    empty = am4.api_market_daily()
    close_stack(am4, dk4, metered4, led4)

    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-marketdaily" in handle.read()
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    with open(os.path.abspath(__file__), "rb") as handle:
        blob = handle.read()
    ascii_ok = True
    try:
        blob.decode("ascii")
    except UnicodeDecodeError:
        ascii_ok = False
    src = blob.decode("utf-8", "replace")
    net_imports = [line for line in src.splitlines()
                   if line.strip().startswith(("import requests",
                                               "import urllib",
                                               "import http"))]
    outside_repo = not os.path.abspath(tmp).startswith(
        os.path.abspath(os.path.join(BASE, "..", "..", "..")))
    ok8 = (tx_b2 == tx_a2
           and pools_b2 == pools_a2
           and frozen_b2 == frozen_a2
           and first == second
           and first == two == three
           and set(empty.keys()) == ENVELOPE_KEYS
           and empty["day_count"] == 0
           and empty["days"] == []
           and empty["lifetime_gross"] == 0
           and empty["avg_net_per_active_day"] is None
           and wired and shas_before == shas_after and ascii_ok
           and not net_imports and outside_repo)
    record("AC-MDL8", ok8,
           "ledger tx frozen=%r pools frozen=%r digests frozen=%r"
           " repeat identical=%r three instances identical=%r"
           " empty=%r wired=%r consumer shas stable=%r ascii=%r"
           " net imports=%d outside repo=%r"
           % (tx_b2 == tx_a2, pools_b2 == pools_a2,
              frozen_b2 == frozen_a2, first == second,
              first == two == three,
              (empty["day_count"], empty["days"]), wired,
              shas_before == shas_after, ascii_ok, len(net_imports),
              outside_repo))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())