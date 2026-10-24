"""Acceptance suite for the apimarket seller monthly revenue timeline
(BigDomain R2097; canon = the explore-queue row seeded and claimed in
R2097, criteria AC-REVM1..AC-REVM8 registered in that claim note BEFORE
this code existed - honesty law; the AC-REVM prefix, the
api_revenue_months name, this suite name and the
ledger-apimarket-revenuemonths runner label were all git-grep -F
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.api_revenue_months. api_sales answers
row by row (the caller buckets it), dev_profile answers lifetime totals
with no time axis, and api_market_stats answers the whole market, so
the per-seller month axis every statement or settlement run needs was
missing. This window pins it:

  - a nine-key envelope and a ten-key month row, months ordered
    ascending;
  - the cash-basis attribution law: a sale books in the UTC month of
    purchased_utc, a refund books in the UTC month of refunded_utc and
    never rewrites the month the sale landed in (so a later-month
    refund shows an honestly negative net there);
  - the month boundary law at 23:59:59Z vs 00:00:00Z;
  - per-row arithmetic and split conservation;
  - lifetime conservation against the raw purchase and refund rows;
  - seller isolation, an honest empty envelope for a prefix-valid
    account with no activity, and the account shape gate before any
    read, fail-closed with frozen table digests;
  - zero row mutations and zero token movement (pure read);
  - cross-restart byte identity and runner wiring.

Usage: python test_apimarket_revenuemonths.py
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
import apimarket as A                 # noqa: E402 (R2097 face)
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

ENVELOPE_KEYS = {"dev_account", "month_count", "lifetime_sales_count",
                 "lifetime_gross", "lifetime_refund_count",
                 "lifetime_refunded", "lifetime_net", "disclaimer",
                 "months"}
ROW_KEYS = {"month", "sales_count", "gross", "refund_count",
            "refunded", "net", "dev_share", "platform_share",
            "dev_share_net", "platform_share_net"}

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


def revenue_family(am, accounts):
    return {acc: dumps(am.api_revenue_months(acc)) for acc in accounts}


def raw_totals(am, dev_account):
    """Ground truth read straight from the market tables, never from
    the face under proof (so conservation is a real cross-check)."""
    conn = sqlite3.connect(am.db_path)
    gross, sales = conn.execute(
        "SELECT COALESCE(SUM(p.price_paid),0), COUNT(*)"
        " FROM apimarket_purchases p JOIN apimarket_listings l"
        " ON l.listing_id = p.listing_id WHERE l.dev_account = ?",
        (dev_account,)).fetchone()
    refunded, refunds = conn.execute(
        "SELECT COALESCE(SUM(f.amount),0), COUNT(*)"
        " FROM apimarket_refunds f WHERE f.dev_account = ?",
        (dev_account,)).fetchone()
    conn.close()
    return int(gross), int(sales), int(refunded), int(refunds)


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


def code_of(exc):
    return getattr(exc, "code", None)


def revenue_code(am, dev_account):
    try:
        am.api_revenue_months(dev_account)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am, clock, params):
    """Owner dana with two listings; frank a SECOND registered
    developer (isolation anchor). Sales are stamped inside explicit
    months so the boundary law is provable: bob's d1 purchase lands at
    2026-08-31T23:59:59Z (AUG), carol's d1 purchase at
    2026-09-01T00:00:00Z (SEP, one second later), bob's d2 purchase in
    mid-SEP, and erin's d3 purchase on frank's listing. One refund is
    then booked in OCT, so dana's AUG row must stay frozen while OCT
    carries a negative net."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-REVM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-REVM-S",
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


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-revenuemonths-")
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
    d1, d2, d3, p1, splits = seed_world(
        led, dk, am, clock, cfg.get("market") or {})
    dev1, plat1 = splits[d1]
    dev2, plat2 = splits[d2]

    env = am.api_revenue_months("usr:dana")
    months = env["months"]
    by_month = {m["month"]: m for m in months}

    # -- AC-REVM1 envelope + row contract -------------------------------
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["dev_account"] == "usr:dana"
           and env["month_count"] == len(months) == 3
           and [m["month"] for m in months]
           == ["2026-08", "2026-09", "2026-10"]
           and all(set(m.keys()) == ROW_KEYS for m in months)
           and env["disclaimer"] == DISCLAIMER)
    record("AC-REVM1", ok1,
           "keys ok=%r months=%r month_count=%d"
           % (set(env.keys()) == ENVELOPE_KEYS,
              [m["month"] for m in months], env["month_count"]))

    # -- AC-REVM2 cash-basis month attribution --------------------------
    aug, sep, octo = by_month["2026-08"], by_month["2026-09"], \
        by_month["2026-10"]
    ok2 = (aug["sales_count"] == 1
           and aug["gross"] == 10
           and aug["refund_count"] == 0
           and sep["sales_count"] == 2
           and sep["gross"] == 13
           and sep["refund_count"] == 0
           and octo["sales_count"] == 0
           and octo["refund_count"] == 1
           and octo["refunded"] == 10
           and octo["gross"] == 0)
    record("AC-REVM2", ok2,
           "aug={sales:%d gross:%d refunds:%d} sep={sales:%d gross:%d"
           " refunds:%d} oct={sales:%d gross:%d refunds:%d"
           " refunded:%d}"
           % (aug["sales_count"], aug["gross"], aug["refund_count"],
              sep["sales_count"], sep["gross"], sep["refund_count"],
              octo["sales_count"], octo["gross"],
              octo["refund_count"], octo["refunded"]))

    # -- AC-REVM3 per-row arithmetic and split conservation -------------
    row_ok = []
    for m in months:
        row_ok.append(m["gross"] == m["dev_share"] + m["platform_share"])
        row_ok.append(m["net"] == m["gross"] - m["refunded"])
    ok3 = (all(row_ok)
           and aug["dev_share"] == dev1
           and aug["platform_share"] == plat1
           and sep["dev_share"] == dev1 + dev2
           and sep["platform_share"] == plat1 + plat2
           and aug["dev_share_net"] == dev1
           and sep["dev_share_net"] == dev1 + dev2
           and octo["dev_share_net"] == -dev1
           and octo["platform_share_net"] == -plat1
           and octo["net"] == -10)
    record("AC-REVM3", ok3,
           "splits d1=%r d2=%r rows consistent=%r aug net dev=%d"
           " oct net dev=%d"
           % ((dev1, plat1), (dev2, plat2), row_ok,
              aug["dev_share_net"], octo["dev_share_net"]))

    # -- AC-REVM4 lifetime conservation against raw rows ----------------
    gross, sales, refunded, refunds = raw_totals(am, "usr:dana")
    ok4 = (env["lifetime_gross"] == gross == 23
           and env["lifetime_sales_count"] == sales == 3
           and env["lifetime_refunded"] == refunded == 10
           and env["lifetime_refund_count"] == refunds == 1
           and env["lifetime_net"] == gross - refunded == 13
           and sum(m["gross"] for m in months) == env["lifetime_gross"]
           and sum(m["refunded"] for m in months)
           == env["lifetime_refunded"]
           and sum(m["sales_count"] for m in months)
           == env["lifetime_sales_count"])
    record("AC-REVM4", ok4,
           "face/raw gross=%d/%d sales=%d/%d refunded=%d/%d"
           " refunds=%d/%d net=%d"
           % (env["lifetime_gross"], gross,
              env["lifetime_sales_count"], sales,
              env["lifetime_refunded"], refunded,
              env["lifetime_refund_count"], refunds,
              env["lifetime_net"]))

    # -- AC-REVM5 cross-month refund: frozen origin, negative net -------
    again = am.api_revenue_months("usr:dana")
    aug_again = {m["month"]: m for m in again["months"]}["2026-08"]
    ok5 = (aug_again == aug
           and aug["gross"] == 10
           and octo["net"] == -10
           and by_month["2026-10"]["refund_count"] == 1)
    record("AC-REVM5", ok5,
           "aug frozen=%r oct net=%d (negative allowed)"
           % (aug_again == aug, octo["net"]))

    # -- AC-REVM6 isolation, honest empty, account gate -----------------
    frank_env = am.api_revenue_months("usr:frank")
    empty_env = am.api_revenue_months("usr:nobody")
    bad_codes = [revenue_code(am, bad) for bad in
                 (None, "", "bob", 7, 1.5, True, [], {})]
    blank_code = revenue_code(am, "   ")
    ok6 = (set(frank_env.keys()) == ENVELOPE_KEYS
           and frank_env["lifetime_gross"] == 5
           and frank_env["lifetime_sales_count"] == 1
           and [m["month"] for m in frank_env["months"]] == ["2026-09"]
           and set(empty_env.keys()) == ENVELOPE_KEYS
           and empty_env["month_count"] == 0
           and empty_env["months"] == []
           and empty_env["lifetime_gross"] == 0
           and empty_env["lifetime_sales_count"] == 0
           and empty_env["lifetime_refunded"] == 0
           and empty_env["lifetime_net"] == 0
           and empty_env["disclaimer"] == DISCLAIMER
           and bad_codes == [A.E_AM_BAD_ACCOUNT] * 8
           and blank_code == A.E_AM_BAD_ACCOUNT)
    record("AC-REVM6", ok6,
           "frank gross=%d months=%r empty=%r bad=%r blank=%r"
           % (frank_env["lifetime_gross"],
              [m["month"] for m in frank_env["months"]],
              empty_env["months"], set(bad_codes), blank_code))

    # -- AC-REVM7 pure read: frozen digests, ledger, pools --------------
    tx_before = ledger_tx_ids(led)
    pools_before = pool_balances(led)
    frozen_before = frozen_digests(am)
    first = dumps(am.api_revenue_months("usr:dana"))
    second = dumps(am.api_revenue_months("usr:dana"))
    tx_after = ledger_tx_ids(led)
    pools_after = pool_balances(led)
    frozen_after = frozen_digests(am)
    ok7 = (tx_before == tx_after
           and pools_before == pools_after
           and frozen_before == frozen_after
           and first == second)
    record("AC-REVM7", ok7,
           "ledger tx frozen=%r pools frozen=%r thirteen-table"
           " digests frozen=%r repeat identical=%r"
           % (tx_before == tx_after, pools_before == pools_after,
              frozen_before == frozen_after, first == second))

    # -- AC-REVM8 cross-restart identity + wiring + hygiene -------------
    accounts = ("usr:dana", "usr:frank", "usr:nobody")
    ids = (d1, d2, d3)
    family_before = revenue_family(am, accounts)
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    family_two = revenue_family(am2, accounts)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    family_three = revenue_family(am3, accounts)
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-revenuemonths" in handle.read()
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
    ok8 = (family_before == family_two == family_three
           and wired and shas_before == shas_after and ascii_ok
           and not net_imports and outside and len(ids) == 3)
    record("AC-REVM8", ok8,
           "three instances byte-identical=%r runner wiring=%r"
           " consumer shas stable=%r ascii=%r network imports=%d"
           " world outside repo=%r"
           % (family_before == family_two == family_three, wired,
              shas_before == shas_after, ascii_ok,
              len(net_imports), outside))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())