"""Acceptance suite for the apimarket seller-side monthly claim pressure
(BigDomain R3153; canon = the R3153 explore-queue claim row, criteria
AC-SCLM1..AC-SCLM8 registered in that row BEFORE this code existed).

Face under proof: APIMarketFace.api_seller_claim_months.
api_market_claim_months answers the market month axis,
api_category_claim_months one category and api_buyer_claim_months one
buyer, while api_claims only lists a seller's claims with their current
status - so a seller could not read whether its own after-sales
pressure is rising month over month. This suite pins:

  - the 26-key envelope, the 14-key month rows, the honest empty world
    and the scope/dev_account contract;
  - the opened_utc booking law (a later refund, answer or withdrawal
    neither shifts the claim month nor invents a row in that month);
  - the five-state seam (refunded beats withdrawn beats answered beats
    open) partitioning claim_count in every row and in the envelope;
  - money on the claim side: claim_amount is the frozen price_paid,
    refunded_amount the joined refund amount, and a refund with no claim
    never appears here;
  - the count-ratio refund_rate (None on a zero-claim month, never a
    fabricated 0.0), and the pooled average;
  - the contiguous grid with honest zero rows, the carried running
    accumulator and the earlier-month peak tie-break;
  - seller isolation and the market envelope partition, plus the
    prefix-valid unknown seller reading empty;
  - cross-face identity against api_market_claim_months and against
    every buyer's own monthly claim face;
  - the seven-form account gate before any read, the pure-read law,
    cross-instance byte identity, the wiring and the ASCII/LF hygiene.

Usage: python test_apimarket_sellerclaimmonths.py
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
import apimarket as A                 # noqa: E402 (R3153 face)
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
    "claim_count", "open_count", "answered_count", "withdrawn_count",
    "refunded_count", "claim_amount", "refunded_amount",
    "avg_claim_amount", "refund_rate", "listing_count", "buyer_count",
    "seller_count", "largest_claim", "peak_month", "peak_claim_count",
    "first_month", "last_month", "latest_month_claim_count",
    "latest_month_refunded_count", "market_claim_rate", "disclaimer",
    "months"}

ROW_KEYS = {
    "month", "claim_count", "open_count", "answered_count",
    "withdrawn_count", "refunded_count", "claim_amount",
    "refunded_amount", "refund_rate", "avg_claim_amount",
    "listing_count", "buyer_count", "seller_count",
    "running_claim_count"}


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


def raw_claim_totals(am):
    conn = sqlite3.connect(am.db_path)
    count, price = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(price_paid), 0)"
        " FROM apimarket_claims").fetchone()
    joined = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(f.amount), 0)"
        " FROM apimarket_claims c JOIN apimarket_refunds f"
        " ON f.purchase_id = c.purchase_id").fetchone()
    conn.close()
    return int(count), int(price), int(joined[0]), int(joined[1])


def seed_world(led, dk, am, clock, claims):
    """dana owns t1 (price 10) and t2 (price 4); frank owns t3 (price 6).
    Claims book on their own opened_utc, so a cross-month refund must not
    move the claim:

      bob   t1 opened 08-05 -> refund 08-06  (refunded, same month, 10)
      carol t1 opened 08-12 -> answered 08-13 (answered, 10)
      bob   t2 opened 09-15 -> refund 10-03  (refunded, claim stays 09, 4)
      dave  t2 opened 09-25 -> withdrawn 09-27 (withdrawn, 4)
      dave  t3 opened 11-05 -> open          (open, 6, frank)
      bob   t3 opened 11-10 -> refund 12-02  (refunded, claim stays 11, 6)

    dana therefore reads August 2 claims / 20 disputed / 10 refunded
    (rate 0.5) and September 2 claims / 8 disputed / 4 refunded, with
    October absent from her grid. Frank reads November 2/12/6, and the
    December refund adds NO row to anyone - a refund never re-dates a
    claim month. The market grid spans 08..11 with October as its one
    honest zero month.
    """
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-SCLM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-SCLM-S",
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
    t3 = am.publish_api("usr:frank", "chart-render",
                        "Chart Render API",
                        "chart image render endpoint", PAYLOAD, 6,
                        False)["listing_id"]

    clock.value = "2026-08-02T10:00:00Z"
    p1 = am.purchase_api("usr:bob", t1, "ref-bob-t1")["purchase_id"]
    clock.value = "2026-08-10T10:00:00Z"
    p2 = am.purchase_api("usr:carol", t1, "ref-carol-t1")["purchase_id"]
    clock.value = "2026-09-11T09:00:00Z"
    p3 = am.purchase_api("usr:bob", t2, "ref-bob-t2")["purchase_id"]
    clock.value = "2026-09-20T09:00:00Z"
    p4 = am.purchase_api("usr:dave", t2, "ref-dave-t2")["purchase_id"]
    clock.value = "2026-11-01T09:00:00Z"
    p5 = am.purchase_api("usr:dave", t3, "ref-dave-t3")["purchase_id"]
    clock.value = "2026-11-20T09:00:00Z"
    p6 = am.purchase_api("usr:bob", t3, "ref-bob-t3")["purchase_id"]

    clock.value = "2026-08-05T10:00:00Z"
    c1 = am.open_claim("usr:bob", p1, "endpoint returned 500")["claim_id"]
    clock.value = "2026-08-06T10:00:00Z"
    am.refund_api("usr:bob", p1, "broken endpoint")

    clock.value = "2026-08-12T11:00:00Z"
    c2 = am.open_claim("usr:carol", p2,
                       "risk numbers look wrong")["claim_id"]
    clock.value = "2026-08-13T11:00:00Z"
    am.respond_claim("usr:dana", c2, "recomputed the scan by hand")

    clock.value = "2026-09-15T08:00:00Z"
    c3 = am.open_claim("usr:bob", p3, "feed stale for a week")["claim_id"]
    clock.value = "2026-09-25T08:00:00Z"
    c4 = am.open_claim("usr:dave", p4, "payload schema changed")["claim_id"]
    clock.value = "2026-09-27T08:00:00Z"
    am.withdraw_claim("usr:dave", c4)
    clock.value = "2026-10-03T08:00:00Z"
    am.refund_api("usr:bob", p3, "stale feed")

    clock.value = "2026-11-05T08:00:00Z"
    c5 = am.open_claim("usr:dave", p5, "chart output broken")["claim_id"]
    clock.value = "2026-11-10T08:00:00Z"
    c6 = am.open_claim("usr:bob", p6, "render timed out")["claim_id"]
    clock.value = "2026-12-02T08:00:00Z"
    am.refund_api("usr:bob", p6, "chart output broken")

    claims.update({"c1": c1, "c3": c3, "c4": c4, "c5": c5, "c6": c6})


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerclaimmonths-")
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

    # -- AC-SCLM1 the contract, honest empty first, keyword signature --
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-sclm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_claim_months("usr:nobody")
    e_am.close()
    e_dk.close()
    e_metered.close()
    e_led.close()
    ok1_empty = (set(empty) == ENVELOPE_KEYS
                 and empty["scope"] == "seller"
                 and empty["dev_account"] == "usr:nobody"
                 and empty["month_count"] == 0
                 and empty["active_month_count"] == 0
                 and empty["claim_count"] == 0
                 and empty["refunded_amount"] == 0
                 and empty["claim_amount"] == 0
                 and empty["refund_rate"] is None
                 and empty["avg_claim_amount"] is None
                 and empty["largest_claim"] is None
                 and empty["peak_month"] is None
                 and empty["peak_claim_count"] is None
                 and empty["first_month"] is None
                 and empty["last_month"] is None
                 and empty["latest_month_claim_count"] is None
                 and empty["latest_month_refunded_count"] is None
                 and empty["months"] == []
                 and empty["disclaimer"] == DISCLAIMER)

    claims = {}
    seed_world(led, dk, am, clock, claims)

    dana = am.api_seller_claim_months("usr:dana")
    frank = am.api_seller_claim_months("usr:frank")
    market = am.api_seller_claim_months()

    ok1 = (ok1_empty
           and set(market) == ENVELOPE_KEYS
           and all(set(row) == ROW_KEYS for row in market["months"])
           and market["scope"] == "market"
           and market["dev_account"] is None
           and market["disclaimer"] == DISCLAIMER
           and [row["month"] for row in market["months"]]
           == ["2026-08", "2026-09", "2026-10", "2026-11"])
    record("AC-SCLM1", ok1,
           "keys=%d empty=%r market_rows=%r scope=%r"
           % (len(empty), (empty["month_count"], empty["claim_count"],
                           empty["refund_rate"], empty["months"]),
              len(market["months"]), market["scope"]))

    # -- AC-SCLM2 the opened_utc booking law -------------------------
    aug = month_row(dana, "2026-08")
    sep = month_row(dana, "2026-09")
    oct_row = month_row(market, "2026-10")
    nov = month_row(market, "2026-11")
    ok2 = ([row["month"] for row in dana["months"]]
           == ["2026-08", "2026-09"]
           and [row["month"] for row in frank["months"]]
           == ["2026-11"]
           and aug["claim_count"] == 2
           and aug["refunded_count"] == 1
           and aug["refunded_amount"] == 10
           and sep["claim_count"] == 2
           and sep["refunded_count"] == 1
           and sep["refunded_amount"] == 4
           and oct_row["claim_count"] == 0
           and oct_row["refunded_count"] == 0
           and nov["claim_count"] == 2
           and nov["refunded_count"] == 1
           and nov["refunded_amount"] == 6
           and "2026-12" not in [row["month"]
                                 for row in market["months"]]
           and market["claim_count"] == 6)
    record("AC-SCLM2", ok2,
           "dana_grid=%r frank_grid=%r aug=%r sep=%r oct=%r nov=%r"
           % ([row["month"] for row in dana["months"]],
              [row["month"] for row in frank["months"]],
              (aug["claim_count"], aug["refunded_count"],
               aug["refunded_amount"]),
              (sep["claim_count"], sep["refunded_count"],
               sep["refunded_amount"]),
              (oct_row["claim_count"], oct_row["refunded_count"]),
              (nov["claim_count"], nov["refunded_count"],
               nov["refunded_amount"])))

    # -- AC-SCLM3 the five-state seam partitions every row -----------
    def partitions(env):
        rows_ok = all(
            row["claim_count"] == row["open_count"]
            + row["answered_count"] + row["withdrawn_count"]
            + row["refunded_count"] for row in env["months"])
        env_ok = (env["claim_count"] == env["open_count"]
                  + env["answered_count"] + env["withdrawn_count"]
                  + env["refunded_count"])
        return rows_ok and env_ok

    ok3 = (partitions(dana) and partitions(frank) and partitions(market)
           and aug["answered_count"] == 1
           and sep["withdrawn_count"] == 1
           and month_row(frank, "2026-11")["open_count"] == 1
           and market["refunded_count"] == 3
           and market["answered_count"] == 1
           and market["withdrawn_count"] == 1
           and market["open_count"] == 1
           and market["claim_amount"] == 40)
    record("AC-SCLM3", ok3,
           "dana=%r sep=%r frank11=%r market=%r"
           % ((aug["open_count"], aug["answered_count"],
               aug["withdrawn_count"], aug["refunded_count"]),
              (sep["open_count"], sep["answered_count"],
               sep["withdrawn_count"], sep["refunded_count"]),
              (month_row(frank, "2026-11")["open_count"],
               month_row(frank, "2026-11")["refunded_count"]),
              (market["claim_count"], market["refunded_count"],
               market["claim_amount"])))

    # -- AC-SCLM4 money on the claim side ----------------------------
    count_t, price_t, joined_count, joined_amount = raw_claim_totals(am)
    refunds_only = am.api_seller_refund_months()
    ok4 = (market["claim_amount"] == price_t == 40
           and sum(row["claim_amount"] for row in market["months"])
           == price_t
           and market["refunded_count"] == joined_count
           and market["refunded_amount"] == joined_amount == 20
           and sum(row["refunded_amount"] for row in market["months"])
           == joined_amount
           and market["claim_count"] == count_t == 6
           and refunds_only["refunded"] == joined_amount
           and all(
               row["avg_claim_amount"]
               == round(float(row["claim_amount"]) / row["claim_count"], 2)
               for row in market["months"] if row["claim_count"])
           and market["avg_claim_amount"] == round(40.0 / 6.0, 2))
    record("AC-SCLM4", ok4,
           "raw=%r face=%r refunds_face=%r"
           % ((count_t, price_t, joined_count, joined_amount),
              (market["claim_count"], market["claim_amount"],
               market["refunded_count"], market["refunded_amount"]),
              (refunds_only["refund_count"], refunds_only["refunded"])))

    # -- AC-SCLM5 the grid, honest zeros, accumulator, peak ----------
    running = [row["running_claim_count"] for row in market["months"]]
    ok5 = (running == [2, 4, 4, 6]
           and market["month_count"] == 4
           and market["active_month_count"] == 3
           and oct_row["refund_rate"] is None
           and oct_row["avg_claim_amount"] is None
           and market["peak_month"] == "2026-08"
           and market["peak_claim_count"] == 2
           and dana["peak_month"] == "2026-08"
           and frank["peak_month"] == "2026-11"
           and market["first_month"] == "2026-08"
           and market["last_month"] == "2026-11"
           and market["latest_month_claim_count"] == 2
           and market["latest_month_refunded_count"] == 1
           and frank["latest_month_claim_count"] == 2
           and frank["latest_month_refunded_count"] == 1
           and month_row(frank, "2026-11")["running_claim_count"] == 2)
    record("AC-SCLM5", ok5,
           "running=%r peaks=%r latest=%r"
           % (running,
              (market["peak_month"], dana["peak_month"],
               frank["peak_month"]),
              (market["latest_month_claim_count"],
               market["latest_month_refunded_count"])))

    # -- AC-SCLM6 isolation and the market partition -----------------
    ok6 = (dana["listing_count"] == 2
           and dana["buyer_count"] == 3
           and dana["seller_count"] == 1
           and frank["listing_count"] == 1
           and frank["buyer_count"] == 2
           and frank["seller_count"] == 1
           and dana["claim_count"] + frank["claim_count"]
           == market["claim_count"] == 6
           and dana["claim_amount"] + frank["claim_amount"]
           == market["claim_amount"] == 40
           and dana["refunded_amount"] + frank["refunded_amount"]
           == market["refunded_amount"] == 20
           and dana["refunded_count"] + frank["refunded_count"]
           == market["refunded_count"] == 3
           and dana["open_count"] + frank["open_count"]
           == market["open_count"]
           and dana["answered_count"] + frank["answered_count"]
           == market["answered_count"]
           and dana["withdrawn_count"] + frank["withdrawn_count"]
           == market["withdrawn_count"]
           and market["seller_count"] == 2
           and market["listing_count"] == 3
           and market["buyer_count"] == 3
           and month_row(frank, "2026-11")["seller_count"] == 1
           and month_row(frank, "2026-11")["buyer_count"] == 2)
    record("AC-SCLM6", ok6,
           "dana=%r frank=%r market=%r"
           % ((dana["claim_count"], dana["claim_amount"],
               dana["refunded_amount"]),
              (frank["claim_count"], frank["claim_amount"],
               frank["refunded_amount"]),
              (market["claim_count"], market["claim_amount"],
               market["refunded_amount"])))

    # -- AC-SCLM7 cross-face identity --------------------------------
    face_market = am.api_market_claim_months()
    buyer_total = {"claim_count": 0, "claim_amount": 0,
                   "refunded_amount": 0}
    for who in ("bob", "carol", "dave"):
        one = am.api_buyer_claim_months("usr:" + who)
        for key in buyer_total:
            buyer_total[key] += one[key]
    ok7 = (face_market["claim_count"] == market["claim_count"]
           and face_market["claim_amount"] == market["claim_amount"]
           and face_market["refunded_amount"]
           == market["refunded_amount"]
           and buyer_total["claim_count"] == market["claim_count"]
           and buyer_total["claim_amount"] == market["claim_amount"]
           and buyer_total["refunded_amount"]
           == market["refunded_amount"]
           and [row["claim_count"] for row in face_market["months"]]
           == [month_row(market, row["month"])["claim_count"]
               for row in face_market["months"]]
           and [row["month"] for row in face_market["months"]]
           == [row["month"] for row in market["months"]
               if row["claim_count"] > 0])
    record("AC-SCLM7", ok7,
           "market_face=%r buyers=%r seller=%r"
           % ((face_market["claim_count"], face_market["claim_amount"],
               face_market["refunded_amount"]),
              buyer_total,
              (market["claim_count"], market["claim_amount"],
               market["refunded_amount"])))

    # -- AC-SCLM8 gates before any read, purity, wiring, hygiene -----
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_forms = ["", "usr", "USR:bob", " usr:bob", "usr :bob",
                 "dev:bob", 123]
    bad_ok = []
    for form in bad_forms:
        try:
            am.api_seller_claim_months(form)
            bad_ok.append(False)
        except A.ApiMarketError as err:
            bad_ok.append(err.code == A.E_AM_BAD_ACCOUNT)
    digests_after_gates = market_digests(am)

    call_a = dumps(am.api_seller_claim_months("usr:dana"))
    call_b = dumps(am.api_seller_claim_months("usr:dana"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_seller_claim_months("usr:dana"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_seller_claim_months("usr:dana"))
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
           and b'"ledger-apimarket-sellerclaimmonths"' in recon
           and b"test_apimarket_sellerclaimmonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-SCLM8", ok8,
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
