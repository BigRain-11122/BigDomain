"""Acceptance suite for the apimarket seller-side monthly refund flow
(BigDomain R3152; canon = the R3152 explore-queue claim row, criteria
AC-SRFM1..AC-SRFM8 registered in that row BEFORE this code existed).

Face under proof: APIMarketFace.api_seller_refund_months.
api_buyer_refund_months answers the buyer axis, api_category_refund_months
the category axis and api_seller_refund_reasons only a lifetime reason
mix, so a seller could not read what it sold, what came back and what
that made the refund rate month by month. This suite pins:

  - the 27-key envelope, the 14-key month rows, the honest empty world
    and the scope/dev_account contract;
  - the two-clock booking law (a purchase books GROSS in its own
    purchased_utc month, a refund books in its own refunded_utc month,
    and neither rewrites the other), including an honest negative net;
  - money conservation against the raw tables, including the integer
    dev/platform split;
  - the refund-rate law: None on a zero-gross month rather than a
    fabricated 0.0, and a month that refunded more than it sold reading
    above 1.0 because the rate is never clamped;
  - the contiguous grid with honest zero rows, the carried running
    accumulator and the earlier-month peak tie-break;
  - seller isolation and the three-way partition of the market
    envelope, plus the prefix-valid unknown seller reading empty;
  - cross-face identity against every buyer's own monthly refund face;
  - the seven-form account gate before any read, the pure-read law,
    cross-instance byte identity, the wiring and the ASCII/LF hygiene.

Usage: python test_apimarket_sellerrefundmonths.py
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
import apimarket as A                 # noqa: E402 (R3152 face)
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
    "scope", "dev_account", "month_count", "active_month_count",
    "refund_count", "refunded", "gross", "net", "refund_rate",
    "dev_refunded", "platform_refunded", "listing_count",
    "buyer_count", "seller_count", "avg_refund_amount",
    "same_month_count", "largest_refund", "peak_month",
    "peak_refund_count", "first_month", "last_month",
    "latest_month_refund_count", "latest_month_refunded",
    "latest_month_refund_rate", "market_refund_rate",
    "disclaimer", "months"}

ROW_KEYS = {
    "month", "refund_count", "refunded", "gross", "net",
    "refund_rate", "dev_refunded", "platform_refunded",
    "listing_count", "buyer_count", "seller_count",
    "avg_refund_amount", "same_month_count",
    "running_refund_count"}


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set before
    each write so the month buckets are reproducible."""

    def __init__(self):
        self.value = "2026-08-01T00:00:00Z"

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


def market_digests(am):
    conn = sqlite3.connect(am.db_path)
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
        " ORDER BY name").fetchall()]
    out = {}
    for table in tables:
        rows = conn.execute(
            "SELECT * FROM " + table + " ORDER BY rowid").fetchall()
        out[table] = (len(rows),
                      hashlib.sha256(repr(rows).encode("utf-8"))
                      .hexdigest())
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


def month_row(env, month):
    for row in env["months"]:
        if row["month"] == month:
            return row
    raise AssertionError("month %r missing from months" % (month,))


def raw_market(am):
    conn = sqlite3.connect(am.db_path)
    gross, purchases = conn.execute(
        "SELECT COALESCE(SUM(price_paid), 0), COUNT(*)"
        " FROM apimarket_purchases").fetchone()
    refunded, refund_count, dev_share, platform_share = conn.execute(
        "SELECT COALESCE(SUM(amount), 0), COUNT(*),"
        " COALESCE(SUM(dev_share), 0), COALESCE(SUM(platform_share), 0)"
        " FROM apimarket_refunds").fetchone()
    conn.close()
    return (int(gross), int(purchases), int(refunded),
            int(refund_count), int(dev_share), int(platform_share))


def seed_world(led, dk, am, clock):
    """dana owns t1 (price 10), t2 (price 4) and t4 (price 5); frank owns
    t3 (price 6). Purchases book gross and refunds book on their own
    clock, so the two clocks disagree on purpose:

      bob   t1 08-02 -> refund 08-05  (same month, 10)
      carol t1 08-10 -> refund 08-12  (same month, 10)
      bob   t2 09-11 -> refund 10-03  (cross month, 4)
      bob   t4 09-20 -> refund 10-22  (cross month, 5)
      dave  t4 10-14 -> no refund     (gross only)
      bob   t3 11-01 -> refund 12-02  (cross month, 6)
      dave  t3 11-20 -> no refund     (gross only)

    dana therefore reads August 20/20 (rate 1.0), September 9/0 (rate
    0.0) and October 5/9 (rate 1.8, net -4): a month that refunded more
    than it sold. Frank reads November 12/0 and December 0/6 (rate None,
    net -6). The market grid spans 08..12 with December as the honest
    zero-gross month.
    """
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-SRFM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-SRFM-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)

    clock.value = "2026-08-01T00:00:00Z"
    t1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    t2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 4,
                        False)["listing_id"]
    t4 = am.publish_api("usr:dana", "gap-scan", "Gap Scan API",
                        "session gap scanner", PAYLOAD, 5,
                        False)["listing_id"]
    t3 = am.publish_api("usr:frank", "chart-render",
                        "Chart Render API",
                        "chart image render endpoint", PAYLOAD, 6,
                        False)["listing_id"]

    clock.value = "2026-08-02T10:00:00Z"
    p1 = am.purchase_api("usr:bob", t1, "ref-bob-t1")["purchase_id"]
    clock.value = "2026-08-05T10:00:00Z"
    am.refund_api("usr:bob", p1, "not what was described")

    clock.value = "2026-08-10T10:00:00Z"
    p2 = am.purchase_api("usr:carol", t1, "ref-carol-t1")["purchase_id"]
    clock.value = "2026-08-12T10:00:00Z"
    am.refund_api("usr:carol", p2, "endpoint too slow")

    clock.value = "2026-09-11T09:00:00Z"
    p3 = am.purchase_api("usr:bob", t2, "ref-bob-t2")["purchase_id"]
    clock.value = "2026-09-20T09:00:00Z"
    p4 = am.purchase_api("usr:bob", t4, "ref-bob-t4")["purchase_id"]
    clock.value = "2026-10-03T09:00:00Z"
    am.refund_api("usr:bob", p3, "stale feed")
    clock.value = "2026-10-14T09:00:00Z"
    am.purchase_api("usr:dave", t4, "ref-dave-t4")
    clock.value = "2026-10-22T09:00:00Z"
    am.refund_api("usr:bob", p4, "wrong payload")

    clock.value = "2026-11-01T09:00:00Z"
    p5 = am.purchase_api("usr:bob", t3, "ref-bob-t3")["purchase_id"]
    clock.value = "2026-11-20T09:00:00Z"
    am.purchase_api("usr:dave", t3, "ref-dave-t3")
    clock.value = "2026-12-02T09:00:00Z"
    am.refund_api("usr:bob", p5, "chart output broken")


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerrefundmonths-")
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
        return run(db_path, cfg, lobby_cfg, shas_before, clock)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, shas_before, clock):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)

    # -- AC-SRFM1 the contract, honest empty first, keyword signature --
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-srfm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_refund_months("usr:nobody")
    e_am.close()
    e_dk.close()
    e_metered.close()
    e_led.close()
    ok1_empty = (set(empty) == ENVELOPE_KEYS
                 and empty["scope"] == "seller"
                 and empty["dev_account"] == "usr:nobody"
                 and empty["month_count"] == 0
                 and empty["active_month_count"] == 0
                 and empty["refund_count"] == 0
                 and empty["refunded"] == 0
                 and empty["gross"] == 0
                 and empty["net"] == 0
                 and empty["refund_rate"] is None
                 and empty["avg_refund_amount"] is None
                 and empty["largest_refund"] is None
                 and empty["peak_month"] is None
                 and empty["peak_refund_count"] is None
                 and empty["first_month"] is None
                 and empty["last_month"] is None
                 and empty["latest_month_refund_count"] is None
                 and empty["latest_month_refund_rate"] is None
                 and empty["months"] == []
                 and empty["disclaimer"] == DISCLAIMER)

    seed_world(led, dk, am, clock)

    dana = am.api_seller_refund_months("usr:dana")
    frank = am.api_seller_refund_months("usr:frank")
    market = am.api_seller_refund_months()

    ok1 = (ok1_empty
           and set(market) == ENVELOPE_KEYS
           and all(set(row) == ROW_KEYS for row in market["months"])
           and market["scope"] == "market"
           and market["dev_account"] is None
           and market["disclaimer"] == DISCLAIMER
           and [row["month"] for row in market["months"]]
           == ["2026-08", "2026-09", "2026-10", "2026-11", "2026-12"])
    record("AC-SRFM1", ok1,
           "keys=%d empty=%r market_rows=%r scope=%r"
           % (len(empty), (empty["month_count"], empty["gross"],
                           empty["refund_rate"], empty["months"]),
              len(market["months"]), market["scope"]))

    # -- AC-SRFM2 the two clocks -------------------------------------
    aug = month_row(dana, "2026-08")
    sep = month_row(dana, "2026-09")
    oct_row = month_row(dana, "2026-10")
    dec = month_row(market, "2026-12")
    ok2 = (aug["gross"] == 20
           and aug["refund_count"] == 2
           and aug["net"] == 0
           and sep["gross"] == 9
           and sep["refund_count"] == 0
           and sep["net"] == 9
           and oct_row["gross"] == 5
           and oct_row["refund_count"] == 2
           and oct_row["net"] == -4
           and dec["gross"] == 0
           and dec["refund_count"] == 1
           and dec["net"] == -6
           and oct_row["same_month_count"] == 0
           and aug["same_month_count"] == 2)
    record("AC-SRFM2", ok2,
           "aug=%r sep=%r oct=%r dec=%r"
           % ((aug["gross"], aug["refund_count"], aug["net"]),
              (sep["gross"], sep["refund_count"], sep["net"]),
              (oct_row["gross"], oct_row["refund_count"],
               oct_row["net"]),
              (dec["gross"], dec["refund_count"], dec["net"])))

    # -- AC-SRFM3 money conservation against the raw tables ----------
    gross_t, purchases, refunded_t, refund_count_t, dev_t, plat_t = \
        raw_market(am)
    row_sum_gross = sum(row["gross"] for row in market["months"])
    row_sum_refunded = sum(row["refunded"] for row in market["months"])
    split_ok = all(
        row["refunded"] == row["dev_refunded"]
        + row["platform_refunded"]
        and row["net"] == row["gross"] - row["refunded"]
        for row in market["months"])
    ok3 = (market["gross"] == gross_t
           and market["refunded"] == refunded_t
           and market["refund_count"] == refund_count_t
           and market["dev_refunded"] == dev_t
           and market["platform_refunded"] == plat_t
           and market["dev_refunded"]
           + market["platform_refunded"] == market["refunded"]
           and market["net"] == market["gross"] - market["refunded"]
           and row_sum_gross == market["gross"]
           and row_sum_refunded == market["refunded"]
           and split_ok)
    record("AC-SRFM3", ok3,
           "raw=%r face=%r rows=%r split=%r"
           % ((gross_t, refunded_t, refund_count_t, dev_t, plat_t),
              (market["gross"], market["refunded"],
               market["refund_count"], market["dev_refunded"],
               market["platform_refunded"]),
              (row_sum_gross, row_sum_refunded), split_ok))

    # -- AC-SRFM4 the rate law: None, above 1.0 never clamped --------
    ok4 = (aug["refund_rate"] == 1.0
           and sep["refund_rate"] == 0.0
           and oct_row["refund_rate"] == 1.8
           and dec["refund_rate"] is None
           and market["refund_rate"]
           == round(float(market["refunded"]) / market["gross"], 2)
           and market["market_refund_rate"] is None
           and dana["market_refund_rate"] == market["refund_rate"]
           and dana["refund_rate"] == round(29.0 / 34.0, 2)
           and frank["refund_rate"] == 0.5)
    record("AC-SRFM4", ok4,
           "rates=%r market=%r bench=%r"
           % ((aug["refund_rate"], sep["refund_rate"],
               oct_row["refund_rate"], dec["refund_rate"]),
              market["refund_rate"], dana["market_refund_rate"]))

    # -- AC-SRFM5 the grid, honest zeros, accumulator, peak ----------
    dana_grid = [row["month"] for row in dana["months"]]
    frank_grid = [row["month"] for row in frank["months"]]
    ok5 = (dana_grid == ["2026-08", "2026-09", "2026-10"]
           and frank_grid == ["2026-11", "2026-12"]
           and [row["running_refund_count"] for row in market["months"]]
           == [2, 2, 4, 4, 5]
           and month_row(dana, "2026-09")["avg_refund_amount"] is None
           and market["active_month_count"] == 5
           and market["month_count"] == 5
           and market["peak_month"] == "2026-08"
           and market["peak_refund_count"] == 2
           and dana["peak_month"] == "2026-08"
           and frank["peak_month"] == "2026-12"
           and market["first_month"] == "2026-08"
           and market["last_month"] == "2026-12"
           and market["latest_month_refund_count"] == 1
           and market["latest_month_refund_rate"] is None)
    record("AC-SRFM5", ok5,
           "grids=%r running=%r peak=%r"
           % ((dana_grid, frank_grid),
              [row["running_refund_count"] for row in market["months"]],
              (market["peak_month"], market["peak_refund_count"])))

    # -- AC-SRFM6 isolation and the three-way partition --------------
    ok6 = (dana["seller_count"] == 1
           and dana["listing_count"] == 3
           and dana["buyer_count"] == 2
           and dana["refund_count"] + frank["refund_count"]
           == market["refund_count"] == refund_count_t
           and dana["refunded"] + frank["refunded"]
           == market["refunded"] == refunded_t
           and dana["gross"] + frank["gross"] == market["gross"]
           == gross_t
           and dana["scope"] == "seller"
           and frank["scope"] == "seller"
           and oct_row["listing_count"] == 2
           and oct_row["seller_count"] == 1
           and market["buyer_count"] == 2
           and market["seller_count"] == 2)
    record("AC-SRFM6", ok6,
           "dana=%r frank=%r market=%r"
           % ((dana["refund_count"], dana["refunded"], dana["gross"]),
              (frank["refund_count"], frank["refunded"],
               frank["gross"]),
              (market["refund_count"], market["refunded"],
               market["gross"])))

    # -- AC-SRFM7 cross-face identity against every buyer's face -----
    bob = am.api_buyer_refund_months("usr:bob")
    carol = am.api_buyer_refund_months("usr:carol")
    dave = am.api_buyer_refund_months("usr:dave")
    ok7 = (bob["refund_count"] + carol["refund_count"]
           + dave["refund_count"] == market["refund_count"]
           and bob["refunded"] + carol["refunded"] + dave["refunded"]
           == market["refunded"]
           and bob["refund_count"] == 4
           and bob["same_month_count"] + carol["same_month_count"] \
           + dave["same_month_count"] == market["same_month_count"])
    record("AC-SRFM7", ok7,
           "buyers=%r market=%r"
           % ((bob["refund_count"], carol["refund_count"],
               dave["refund_count"]),
              (market["refund_count"], market["same_month_count"])))

    # -- AC-SRFM8 gates before any read, purity, wiring, hygiene -----
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_forms = ["", "usr", "USR:bob", " usr:bob", "usr :bob",
                 "dev:bob", 123]
    bad_ok = []
    for form in bad_forms:
        try:
            am.api_seller_refund_months(form)
            bad_ok.append(False)
        except A.ApiMarketError as err:
            bad_ok.append(err.code == A.E_AM_BAD_ACCOUNT)
    digests_after_gates = market_digests(am)

    call_a = dumps(am.api_seller_refund_months("usr:dana"))
    call_b = dumps(am.api_seller_refund_months("usr:dana"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_seller_refund_months("usr:dana"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_seller_refund_months("usr:dana"))
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (all(bad_ok)
           and len(bad_ok) == 7
           and digests_before == digests_after_gates == digests_after
           and tx_before == tx_after
           and call_a == call_b == dumps(dana)
           and call_c == call_d == dumps(dana)
           and call_a != dumps(frank)
           and b'"ledger-apimarket-sellerrefundmonths"' in recon
           and b"test_apimarket_sellerrefundmonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-SRFM8", ok8,
           "gates=%r digests_same=%r tx_same=%r bytes=%r ascii=%r"
           % (all(bad_ok), digests_before == digests_after,
              tx_before == tx_after, call_c == call_d,
              all(b < 128 for b in test_src)))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
