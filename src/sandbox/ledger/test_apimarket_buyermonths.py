"""Acceptance suite for the apimarket buyer-side monthly spend timeline
(BigDomain R2100; canon = the explore-queue claim row seeded and claimed
in R2100, criteria AC-AMBM1..AC-AMBM8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMBM prefix, the
api_buyer_months name, this suite name and the
ledger-apimarket-buyermonths runner label were all git-grep -F
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.api_buyer_months. The seller side had a
cash-basis month table (api_revenue_months) while the buyer side only had
lifetime aggregates (api_buyer_profile) and rows (api_library), so a
resident could not answer "what did I spend this month, and what came
back", and the month a refund lands in was invisible. This window pins
the mirror face:

  - an eleven-key envelope and an eleven-key month row, months ordered
    ascending;
  - the cash-basis attribution law: a purchase books in the UTC month of
    purchased_utc, a refund books in the UTC month of refunded_utc and
    never rewrites the month the purchase landed in;
  - the month boundary law at 23:59:59Z vs 00:00:00Z;
  - listing_count derived from purchases only (a refund-only month
    honestly reports zero listings);
  - per-row arithmetic and split conservation;
  - lifetime conservation against api_buyer_profile and the raw rows;
  - strict buyer isolation, honest empty envelope and the prefix-only
    account gate;
  - zero row mutations and zero token movement (pure read);
  - three-instance cross-restart byte identity and runner wiring.

Usage: python test_apimarket_buyermonths.py
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
import apimarket as A                 # noqa: E402 (R2100 face)
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

ENVELOPE_KEYS = {"buyer_id", "month_count", "lifetime_purchase_count",
                 "lifetime_gross_spent", "lifetime_refund_count",
                 "lifetime_refunded", "lifetime_net_spent",
                 "lifetime_dev_paid", "lifetime_platform_paid",
                 "disclaimer", "months"}
ROW_KEYS = {"month", "purchase_count", "gross_spent", "refund_count",
            "refunded", "net", "dev_paid", "platform_paid",
            "dev_paid_net", "platform_paid_net", "listing_count"}

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


def raw_totals(am, buyer):
    """Ground truth read straight from the market tables, never from
    the face under proof (so conservation is a real cross-check)."""
    conn = sqlite3.connect(am.db_path)
    gross, sales = conn.execute(
        "SELECT COALESCE(SUM(price_paid),0), COUNT(*)"
        " FROM apimarket_purchases WHERE buyer_id = ?",
        (buyer,)).fetchone()
    refunded, refunds, dev_back, plat_back = conn.execute(
        "SELECT COALESCE(SUM(amount),0), COUNT(*),"
        " COALESCE(SUM(dev_share),0), COALESCE(SUM(platform_share),0)"
        " FROM apimarket_refunds WHERE buyer_id = ?",
        (buyer,)).fetchone()
    dev_fwd, plat_fwd = conn.execute(
        "SELECT COALESCE(SUM(dev_share),0),"
        " COALESCE(SUM(platform_share),0)"
        " FROM apimarket_purchases WHERE buyer_id = ?",
        (buyer,)).fetchone()
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
    """Owner dana publishes three listings; two registered buyers buy
    on pinned stamps so the boundary law is provable. bob's d1
    purchase lands at 2026-08-31T23:59:59Z (AUG) and his d2 purchase
    at 2026-09-01T00:00:00Z (SEP, one second later); d3 lands later in
    SEP, and the AUG purchase is refunded in OCT. carol buys once in
    SEP so buyer isolation has a real second account."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMBM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMBM-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    d3 = am.publish_api("usr:dana", "chart-render",
                        "Chart Render API",
                        "chart image render endpoint", PAYLOAD, 5,
                        False)["listing_id"]
    clock.value = "2026-08-31T23:59:59Z"
    p1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")["purchase_id"]
    clock.value = "2026-09-01T00:00:00Z"
    am.purchase_api("usr:bob", d2, "ref-bob-d2")
    clock.value = "2026-09-20T08:30:00Z"
    am.purchase_api("usr:bob", d3, "ref-bob-d3")
    clock.value = "2026-09-10T10:00:00Z"
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    clock.value = "2026-10-02T00:00:00Z"
    am.refund_api("usr:bob", p1, "month-crossing refund")
    splits = {}
    for listing_id, price in ((d1, 10), (d2, 3), (d3, 5)):
        splits[listing_id] = A.split_amount(price, am.params)
    return d1, d2, d3, p1, splits


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyermonths-")
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
    dev2, plat2 = splits[d2]
    dev3, plat3 = splits[d3]

    env = am.api_buyer_months("usr:bob")
    months = env["months"]
    by_month = {m["month"]: m for m in months}

    # -- AC-AMBM1 envelope + row contract ------------------------------
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["buyer_id"] == "usr:bob"
           and env["month_count"] == len(months) == 3
           and [m["month"] for m in months]
           == ["2026-08", "2026-09", "2026-10"]
           and all(set(m.keys()) == ROW_KEYS for m in months)
           and env["disclaimer"] == DISCLAIMER)
    record("AC-AMBM1", ok1,
           "keys ok=%r months=%r month_count=%d"
           % (set(env.keys()) == ENVELOPE_KEYS,
              [m["month"] for m in months], env["month_count"]))

    # -- AC-AMBM2 cash basis, boundary, refund-only month --------------
    aug, sep, octo = (by_month["2026-08"], by_month["2026-09"],
                      by_month["2026-10"])
    ok2 = (aug["purchase_count"] == 1
           and aug["gross_spent"] == 10
           and aug["listing_count"] == 1
           and sep["purchase_count"] == 2
           and sep["gross_spent"] == 8
           and sep["listing_count"] == 2
           and octo["purchase_count"] == 0
           and octo["gross_spent"] == 0
           and octo["refund_count"] == 1
           and octo["refunded"] == 10
           and octo["net"] == -10
           and octo["listing_count"] == 0)
    record("AC-AMBM2", ok2,
           "aug={p:%d g:%d l:%d} sep={p:%d g:%d l:%d}"
           " oct={p:%d refunds:%d refunded:%d net:%d l:%d}"
           % (aug["purchase_count"], aug["gross_spent"],
              aug["listing_count"], sep["purchase_count"],
              sep["gross_spent"], sep["listing_count"],
              octo["purchase_count"], octo["refund_count"],
              octo["refunded"], octo["net"], octo["listing_count"]))

    # -- AC-AMBM3 per-row arithmetic and split conservation ------------
    row_ok = []
    for m in months:
        row_ok.append(m["gross_spent"]
                      == m["dev_paid"] + m["platform_paid"])
        row_ok.append(m["net"] == m["gross_spent"] - m["refunded"])
        row_ok.append(m["net"] == (m["dev_paid_net"]
                                   + m["platform_paid_net"]))
    ok3 = (all(row_ok)
           and aug["dev_paid"] == dev1
           and aug["platform_paid"] == plat1
           and aug["dev_paid_net"] == dev1
           and octo["dev_paid_net"] == -dev1
           and octo["platform_paid_net"] == -plat1
           and octo["net"] == -10)
    record("AC-AMBM3", ok3,
           "rows consistent=%r d1 split=%r aug net dev=%d"
           " oct net dev=%d" % (row_ok, (dev1, plat1),
                                aug["dev_paid_net"],
                                octo["dev_paid_net"]))

    # -- AC-AMBM4 lifetime conservation against api_buyer_profile and
    # the raw rows (two independent read faces + ground truth).
    gross, sales, refunded, refunds, dev_net, plat_net = raw_totals(
        am, "usr:bob")
    prof = am.api_buyer_profile("usr:bob")
    ok4 = (env["lifetime_gross_spent"] == gross == 18
           == prof["gross_spent"]
           and env["lifetime_purchase_count"] == sales == 3
           == prof["purchase_count"]
           and env["lifetime_refunded"] == refunded == 10
           == prof["refunded_total"]
           and env["lifetime_refund_count"] == refunds == 1
           == prof["refund_count"]
           and env["lifetime_net_spent"] == 8 == prof["net_spent"]
           and env["lifetime_dev_paid"] == dev_net == prof["dev_paid"]
           and env["lifetime_platform_paid"] == plat_net
           == prof["platform_paid"]
           and sum(m["gross_spent"] for m in months)
           == env["lifetime_gross_spent"]
           and sum(m["refunded"] for m in months)
           == env["lifetime_refunded"]
           and sum(m["purchase_count"] for m in months)
           == env["lifetime_purchase_count"]
           and dev_net == dev2 + dev3
           and plat_net == plat2 + plat3)
    record("AC-AMBM4", ok4,
           "face/profile/raw gross=%d/%d/%d purchases=%d/%d/%d"
           " refunded=%d/%d/%d net=%d dev=%d/%d/%d plat=%d/%d/%d"
           " net split d2+d3=%r"
           % (env["lifetime_gross_spent"], prof["gross_spent"], gross,
              env["lifetime_purchase_count"],
              prof["purchase_count"], sales,
              env["lifetime_refunded"], prof["refunded_total"],
              refunded, env["lifetime_net_spent"],
              env["lifetime_dev_paid"], prof["dev_paid"], dev_net,
              env["lifetime_platform_paid"], prof["platform_paid"],
              plat_net, (dev2 + dev3, plat2 + plat3)))

    # -- AC-AMBM5 buyer isolation, honest empty, prefix-only gate ------
    carol = am.api_buyer_months("usr:carol")
    dave = am.api_buyer_months("usr:dave")
    try:
        am.api_buyer_months("bob")
        gate_refused = False
    except A.ApiMarketError as err:
        gate_refused = err.code == A.E_AM_BAD_ACCOUNT
    ok5 = (carol["month_count"] == 1
           and carol["months"][0]["month"] == "2026-09"
           and carol["months"][0]["gross_spent"] == 10
           and carol["lifetime_gross_spent"] == 10
           and carol["lifetime_refund_count"] == 0
           and dave["month_count"] == 0
           and dave["months"] == []
           and dave["lifetime_gross_spent"] == 0
           and dave["lifetime_net_spent"] == 0
           and set(dave.keys()) == ENVELOPE_KEYS
           and gate_refused)
    record("AC-AMBM5", ok5,
           "carol months=%r gross=%d | dave empty=%r keys=%r"
           " | bad account gate=%r"
           % ([m["month"] for m in carol["months"]],
              carol["lifetime_gross_spent"], dave["months"],
              set(dave.keys()) == ENVELOPE_KEYS, gate_refused))

    # -- AC-AMBM6 pure read ---------------------------------------------
    tx_before = ledger_tx_ids(led)
    pools_before = pool_balances(led)
    frozen_before = frozen_digests(am)
    first = dumps(am.api_buyer_months("usr:bob"))
    second = dumps(am.api_buyer_months("usr:bob"))
    tx_after = ledger_tx_ids(led)
    pools_after = pool_balances(led)
    frozen_after = frozen_digests(am)
    ok6 = (tx_before == tx_after
           and pools_before == pools_after
           and frozen_before == frozen_after
           and first == second)
    record("AC-AMBM6", ok6,
           "ledger tx frozen=%r pools frozen=%r thirteen-table"
           " digests frozen=%r repeat identical=%r"
           % (tx_before == tx_after, pools_before == pools_after,
              frozen_before == frozen_after, first == second))

    # -- AC-AMBM7 cross-restart byte identity ---------------------------
    before = dumps(am.api_buyer_months("usr:bob"))
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    two = dumps(am2.api_buyer_months("usr:bob"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    three = dumps(am3.api_buyer_months("usr:bob"))
    carol_again = dumps(am3.api_buyer_months("usr:carol"))
    close_stack(am3, dk3, metered3, led3)
    ok7 = (before == two == three
           and carol_again == dumps(carol))
    record("AC-AMBM7", ok7,
           "three-instance bob byte-identical=%r carol replay=%r"
           % (before == two == three, carol_again == dumps(carol)))

    # -- AC-AMBM8 wiring + hygiene --------------------------------------
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-buyermonths" in handle.read()
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
    record("AC-AMBM8", ok8,
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