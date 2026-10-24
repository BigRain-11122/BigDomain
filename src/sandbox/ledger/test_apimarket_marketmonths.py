"""Acceptance suite for the apimarket market-wide monthly trade timeline
(BigDomain R2099; canon = the explore-queue claim row seeded and claimed
in R2099, criteria AC-AMMM1..AC-AMMM8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMMM prefix, the
api_market_months name, this suite name and the
ledger-apimarket-marketmonths runner label were all git-grep -F
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.api_market_months. api_revenue_months
answers one seller's cash-basis months and api_market_stats answers the
whole market with lifetime aggregates only, so the market-level time
axis every trend, month-on-month comparison or monthly settlement view
needs was missing. This window pins it:

  - a ten-key envelope and a thirteen-key month row, months ordered
    ascending;
  - the cash-basis attribution law: a sale books in the UTC month of
    purchased_utc, a refund books in the UTC month of refunded_utc and
    never rewrites the month the sale landed in;
  - the month boundary law at 23:59:59Z vs 00:00:00Z;
  - participant counts derived from purchases only (a refund-only month
    honestly reports zero buyers/sellers/listings);
  - per-row arithmetic and split conservation;
  - lifetime conservation against api_market_stats, the raw rows and
    the union of every seller's api_revenue_months;
  - zero row mutations and zero token movement (pure read) plus the
    no-argument contract;
  - cross-restart byte identity and runner wiring.

Usage: python test_apimarket_marketmonths.py
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
import apimarket as A                 # noqa: E402 (R2099 face)
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

ENVELOPE_KEYS = {"month_count", "lifetime_sales_count",
                 "lifetime_gross", "lifetime_refund_count",
                 "lifetime_refunded", "lifetime_net",
                 "lifetime_dev_revenue", "lifetime_platform_revenue",
                 "disclaimer", "months"}
ROW_KEYS = {"month", "sales_count", "gross", "refund_count",
            "refunded", "net", "dev_share", "platform_share",
            "dev_share_net", "platform_share_net", "buyer_count",
            "seller_count", "listing_count"}
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


class Clock(object):
    """Deterministic stamp holder: the suite sets one explicit UTC
    string before each write so the month buckets are reproducible
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
    developer. Sales are stamped inside explicit months so the
    boundary law is provable: bob's d1 purchase lands at
    2026-08-31T23:59:59Z (AUG), carol's d1 purchase at
    2026-09-01T00:00:00Z (SEP, one second later), bob's d2 purchase
    and erin's d3 purchase in SEP. One refund is then booked in OCT,
    so the AUG market row must stay frozen while OCT carries a
    negative net and zero participants (refund-only month)."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMMM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMMM-S",
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
    am.refund_api("usr:bob", p1, "month-crossing refund")
    splits = {}
    for listing_id, price in ((d1, 10), (d2, 3), (d3, 5)):
        splits[listing_id] = A.split_amount(price, am.params)
    return d1, d2, d3, p1, splits


def seller_union(am, accounts):
    """Aggregate every seller's api_revenue_months into one market
    month table (the cross-face consistency anchor of AC-AMMM4)."""
    union = {}
    for acc in accounts:
        for m in am.api_revenue_months(acc)["months"]:
            b = union.setdefault(
                m["month"], {k: 0 for k in MONEY_KEYS})
            for k in MONEY_KEYS:
                b[k] += m[k]
    return union


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-marketmonths-")
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

    env = am.api_market_months()
    months = env["months"]
    by_month = {m["month"]: m for m in months}

    # -- AC-AMMM1 envelope + row contract ------------------------------
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["month_count"] == len(months) == 3
           and [m["month"] for m in months]
           == ["2026-08", "2026-09", "2026-10"]
           and all(set(m.keys()) == ROW_KEYS for m in months)
           and env["disclaimer"] == DISCLAIMER)
    record("AC-AMMM1", ok1,
           "keys ok=%r months=%r month_count=%d"
           % (set(env.keys()) == ENVELOPE_KEYS,
              [m["month"] for m in months], env["month_count"]))

    # -- AC-AMMM2 cash basis, boundary, refund-only participants -------
    aug, sep, octo = by_month["2026-08"], by_month["2026-09"], \
        by_month["2026-10"]
    ok2 = (aug["sales_count"] == 1
           and aug["gross"] == 10
           and aug["buyer_count"] == 1
           and aug["seller_count"] == 1
           and aug["listing_count"] == 1
           and sep["sales_count"] == 3
           and sep["gross"] == 18
           and sep["buyer_count"] == 3
           and sep["seller_count"] == 2
           and sep["listing_count"] == 3
           and octo["sales_count"] == 0
           and octo["gross"] == 0
           and octo["refund_count"] == 1
           and octo["refunded"] == 10
           and octo["buyer_count"] == 0
           and octo["seller_count"] == 0
           and octo["listing_count"] == 0)
    record("AC-AMMM2", ok2,
           "aug={sales:%d gross:%d b:%d s:%d l:%d}"
           " sep={sales:%d gross:%d b:%d s:%d l:%d}"
           " oct={sales:%d refunds:%d refunded:%d b:%d s:%d l:%d}"
           % (aug["sales_count"], aug["gross"], aug["buyer_count"],
              aug["seller_count"], aug["listing_count"],
              sep["sales_count"], sep["gross"], sep["buyer_count"],
              sep["seller_count"], sep["listing_count"],
              octo["sales_count"], octo["refund_count"],
              octo["refunded"], octo["buyer_count"],
              octo["seller_count"], octo["listing_count"]))

    # -- AC-AMMM3 per-row arithmetic and split conservation ------------
    row_ok = []
    for m in months:
        row_ok.append(m["gross"] == m["dev_share"] + m["platform_share"])
        row_ok.append(m["net"] == m["gross"] - m["refunded"])
        row_ok.append(m["net"] == (m["dev_share_net"]
                                   + m["platform_share_net"]))
    ok3 = (all(row_ok)
           and aug["dev_share"] == dev1
           and aug["platform_share"] == plat1
           and aug["dev_share_net"] == dev1
           and octo["dev_share_net"] == -dev1
           and octo["platform_share_net"] == -plat1
           and octo["net"] == -10)
    record("AC-AMMM3", ok3,
           "rows consistent=%r d1=%r aug net dev=%d oct net dev=%d"
           % (row_ok, (dev1, plat1), aug["dev_share_net"],
              octo["dev_share_net"]))

    # -- AC-AMMM4 lifetime conservation across three independent read
    # faces (the face under proof, api_market_stats, the raw rows) and
    # the seller union.
    gross, sales, refunded, refunds, dev_net, plat_net = raw_totals(am)
    stats = am.api_market_stats()
    union = seller_union(am, ("usr:dana", "usr:frank"))
    union_ok = []
    for m in months:
        u = union.get(m["month"], {k: 0 for k in MONEY_KEYS})
        union_ok.append(all(m[k] == u[k] for k in MONEY_KEYS))
    ok4 = (env["lifetime_gross"] == gross == 28
           == stats["gross_tokens"]
           and env["lifetime_sales_count"] == sales == 4
           == stats["purchase_count"]
           and env["lifetime_refunded"] == refunded == 10
           == stats["refunded_tokens"]
           and env["lifetime_refund_count"] == refunds == 1
           == stats["refund_count"]
           and env["lifetime_net"] == 18 == stats["net_gross_tokens"]
           and env["lifetime_dev_revenue"] == dev_net
           == stats["dev_revenue"]
           and env["lifetime_platform_revenue"] == plat_net
           == stats["platform_revenue"]
           and sum(m["gross"] for m in months) == env["lifetime_gross"]
           and sum(m["refunded"] for m in months)
           == env["lifetime_refunded"]
           and sum(m["sales_count"] for m in months)
           == env["lifetime_sales_count"]
           and all(union_ok)
           and set(union) == set(by_month))
    record("AC-AMMM4", ok4,
           "face/stats/raw gross=%d/%d/%d sales=%d/%d/%d"
           " refunded=%d/%d/%d net=%d dev=%d/%d/%d plat=%d/%d/%d"
           " seller-union months=%r all rows equal=%r"
           % (env["lifetime_gross"], stats["gross_tokens"], gross,
              env["lifetime_sales_count"], stats["purchase_count"],
              sales, env["lifetime_refunded"],
              stats["refunded_tokens"], refunded, env["lifetime_net"],
              env["lifetime_dev_revenue"], stats["dev_revenue"],
              dev_net, env["lifetime_platform_revenue"],
              stats["platform_revenue"], plat_net,
              sorted(union), all(union_ok)))

    # -- AC-AMMM5 cross-month refund: frozen origin, negative net ------
    again = dict((m["month"], m) for m in
                 am.api_market_months()["months"])
    ok5 = (again["2026-08"] == aug
           and aug["gross"] == 10
           and octo["net"] == -10
           and octo["refund_count"] == 1
           and by_month["2026-10"]["refunded"] == 10)
    record("AC-AMMM5", ok5,
           "aug frozen=%r oct net=%d (negative allowed)"
           % (again["2026-08"] == aug, octo["net"]))

    # -- AC-AMMM6 pure read + no-argument contract ---------------------
    tx_before = ledger_tx_ids(led)
    pools_before = pool_balances(led)
    frozen_before = frozen_digests(am)
    first = dumps(am.api_market_months())
    second = dumps(am.api_market_months())
    tx_after = ledger_tx_ids(led)
    pools_after = pool_balances(led)
    frozen_after = frozen_digests(am)
    try:
        am.api_market_months(bogus=1)
        kwarg_refused = False
    except TypeError:
        kwarg_refused = True
    ok6 = (tx_before == tx_after
           and pools_before == pools_after
           and frozen_before == frozen_after
           and first == second
           and kwarg_refused)
    record("AC-AMMM6", ok6,
           "ledger tx frozen=%r pools frozen=%r thirteen-table"
           " digests frozen=%r repeat identical=%r kwargs=TypeError %r"
           % (tx_before == tx_after, pools_before == pools_after,
              frozen_before == frozen_after, first == second,
              kwarg_refused))

    # -- AC-AMMM7 cross-restart byte identity + honest empty market ----
    before = dumps(am.api_market_months())
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    two = dumps(am2.api_market_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    three = dumps(am3.api_market_months())
    close_stack(am3, dk3, metered3, led3)
    empty_dir = os.path.join(tmp, "empty")
    os.makedirs(empty_dir)
    empty_db = os.path.join(empty_dir, "ledger.db")
    led4, metered4, dk4, gate4, am4 = build_stack(
        empty_db, cfg, lobby_cfg)
    empty = am4.api_market_months()
    close_stack(am4, dk4, metered4, led4)
    ok7 = (before == two == three
           and set(empty.keys()) == ENVELOPE_KEYS
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["lifetime_gross"] == 0
           and empty["lifetime_sales_count"] == 0
           and empty["lifetime_refunded"] == 0
           and empty["lifetime_net"] == 0
           and empty["disclaimer"] == DISCLAIMER)
    record("AC-AMMM7", ok7,
           "three instances byte-identical=%r empty market=%r"
           % (before == two == three,
              (empty["month_count"], empty["months"])))

    # -- AC-AMMM8 wiring + hygiene -------------------------------------
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-marketmonths" in handle.read()
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
    outside = not os.path.abspath(tmp).startswith(
        os.path.abspath(os.path.join(BASE, "..", "..", "..")))
    ok8 = (wired and shas_before == shas_after and ascii_ok
           and not net_imports and outside)
    record("AC-AMMM8", ok8,
           "runner wiring=%r consumer shas stable=%r ascii=%r"
           " network imports=%d world outside repo=%r"
           % (wired, shas_before == shas_after, ascii_ok,
              len(net_imports), outside))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())