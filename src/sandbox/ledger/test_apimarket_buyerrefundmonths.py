"""Acceptance suite for the apimarket buyer-side monthly refund flow
(BigDomain R2203; canon = the R2203 explore-queue claim row, criteria
AC-BRM1..AC-BRM8 registered in that row BEFORE this code existed).

Face under proof: APIMarketFace.api_buyer_refund_months. api_buyer_profile
answers lifetime refunded money and count and api_refund_latency answers
the market-wide settlement delay with one monthly leg, so a resident's own
refund rhythm - how much came back in which month, and whether a refund
landed in the purchase month or a later one - had no face. This suite
pins:

  - the 21-key envelope, the 10-key month rows, the honest empty world
    and the keyword-signature contract;
  - the booking law (a refund books only in the UTC month of its own
    refunded_utc; a later refund never rewrites the purchase month);
  - the contiguous grid with honest zero months whose average is None
    rather than a fabricated zero, and the running accumulator that is
    carried across them;
  - conservation of count, money and the integer dev/platform split
    against the raw tables;
  - the pooled average, which a mean of monthly means would answer
    differently (6.25 pooled against 6.83 averaged);
  - the distinct-vs-sum asymmetry of the participant counts and strict
    buyer isolation, with cross-face identity against api_buyer_profile;
  - the peak law with the earlier-month tie-break and the honest empty
    peak;
  - the seven-form account gate before any read, the bare prefix reading
    honestly empty, and the pure-read law;
  - cross-instance byte identity, the wiring and the ASCII/LF hygiene.

Usage: python test_apimarket_buyerrefundmonths.py
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
import apimarket as A                 # noqa: E402 (R2203 face)
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
    "buyer_id", "scope", "month_count", "active_month_count",
    "refund_count", "refunded", "dev_refunded", "platform_refunded",
    "listing_count", "seller_count", "avg_refund_amount",
    "same_month_count", "largest_refund", "peak_month",
    "peak_refund_count", "first_month", "last_month",
    "latest_month_refund_count", "latest_month_refunded",
    "disclaimer", "months"}

ROW_KEYS = {
    "month", "refund_count", "refunded", "dev_refunded",
    "platform_refunded", "listing_count", "seller_count",
    "avg_refund_amount", "same_month_count", "running_refund_count"}


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


def raw_refunds(am, buyer_id):
    """Ground truth straight from the market tables: the buyer's refund
    rows joined to their purchases, ordered by refund id."""
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT f.refunded_utc, f.amount, f.dev_share,"
        " f.platform_share, f.listing_id, f.dev_account,"
        " p.purchased_utc"
        " FROM apimarket_refunds f JOIN apimarket_purchases p"
        " ON p.purchase_id = f.purchase_id"
        " WHERE f.buyer_id = ? ORDER BY f.refund_id",
        (buyer_id,)).fetchall()
    conn.close()
    return [tuple(str(v) if i in (0, 5, 6) else int(v)
                  for i, v in enumerate(row)) for row in rows]


def seed_world(led, dk, am, clock):
    """dana owns t1 (price 10), t2 (price 4) and t4 (price 5); frank owns
    t3 (price 6). Refunds land in August, October and December, so the
    grid must carry September and November as honest zero months.

      bob   t1 08-02 -> refund 08-05  (same month, 10)
      bob   t2 09-11 -> refund 10-03  (cross month, 4)
      bob   t4 10-14 -> refund 10-20  (same month, 5)
      bob   t3 11-01 -> refund 12-02  (cross month, 6)
      carol t1 08-10 -> refund 08-12  (same month, 10)
      dave  t1 08-15 -> refund 08-20  (same month, 10)
      dave  t2 09-20 -> refund 10-22  (cross month, 4)
    """
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-BRM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-BRM-S",
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

    clock.value = "2026-09-11T09:00:00Z"
    p2 = am.purchase_api("usr:bob", t2, "ref-bob-t2")["purchase_id"]
    clock.value = "2026-10-03T09:00:00Z"
    am.refund_api("usr:bob", p2, "stale feed")

    clock.value = "2026-10-14T09:00:00Z"
    p3 = am.purchase_api("usr:bob", t4, "ref-bob-t4")["purchase_id"]
    clock.value = "2026-10-20T09:00:00Z"
    am.refund_api("usr:bob", p3, "wrong payload")

    clock.value = "2026-11-01T09:00:00Z"
    p4 = am.purchase_api("usr:bob", t3, "ref-bob-t3")["purchase_id"]
    clock.value = "2026-12-02T09:00:00Z"
    am.refund_api("usr:bob", p4, "endpoint down")

    clock.value = "2026-08-10T09:00:00Z"
    p5 = am.purchase_api("usr:carol", t1, "ref-carol-t1")[
        "purchase_id"]
    clock.value = "2026-08-12T09:00:00Z"
    am.refund_api("usr:carol", p5, "duplicate charge")

    clock.value = "2026-08-15T09:00:00Z"
    p6 = am.purchase_api("usr:dave", t1, "ref-dave-t1")[
        "purchase_id"]
    clock.value = "2026-08-20T09:00:00Z"
    am.refund_api("usr:dave", p6, "unusable output")

    clock.value = "2026-09-20T09:00:00Z"
    p7 = am.purchase_api("usr:dave", t2, "ref-dave-t2")[
        "purchase_id"]
    clock.value = "2026-10-22T09:00:00Z"
    am.refund_api("usr:dave", p7, "late data")

    return {"t1": t1, "t2": t2, "t3": t3, "t4": t4}

def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerrefundmonths-")
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

    # -- AC-BRM1 the contract, honest empty first, keyword signature --
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-brm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_refund_months("usr:bob")
    close_stack(e_am, e_dk, e_metered, e_led)

    seed_world(led, dk, am, _CLOCK)
    env = am.api_buyer_refund_months("usr:bob")

    signature_ok = False
    try:
        am.api_buyer_refund_months("usr:bob", bogus=1)
    except TypeError:
        signature_ok = True
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for row in env["months"])
    ok1 = (set(empty.keys()) == ENVELOPE_KEYS
           and set(env.keys()) == ENVELOPE_KEYS
           and rows_ok
           and empty["disclaimer"] == DISCLAIMER
           and empty["buyer_id"] == "usr:bob"
           and empty["scope"] == "buyer"
           and empty["month_count"] == 0
           and empty["active_month_count"] == 0
           and empty["months"] == []
           and empty["refund_count"] == 0
           and empty["refunded"] == 0
           and empty["dev_refunded"] == 0
           and empty["platform_refunded"] == 0
           and empty["listing_count"] == 0
           and empty["seller_count"] == 0
           and empty["avg_refund_amount"] is None
           and empty["same_month_count"] == 0
           and empty["largest_refund"] is None
           and empty["peak_month"] is None
           and empty["peak_refund_count"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_refund_count"] is None
           and empty["latest_month_refunded"] is None
           and signature_ok)
    record("AC-BRM1", ok1,
           "env_keys=%d exact=%r rows=%d empty=%r sig=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS,
              len(env["months"]),
              (empty["month_count"], empty["refund_count"],
               empty["avg_refund_amount"], empty["peak_month"]),
              signature_ok))

    # -- AC-BRM2 the booking law, never the purchase month -----------
    raw = raw_refunds(am, "usr:bob")
    raw_month = {}
    for refunded_utc, amount, _dev, _plat, _lid, _seller, \
            purchased_utc in raw:
        cell = raw_month.setdefault(str(refunded_utc)[:7],
                                     {"count": 0, "money": 0,
                                      "same": 0})
        cell["count"] += 1
        cell["money"] += int(amount)
        if str(refunded_utc)[:7] == str(purchased_utc)[:7]:
            cell["same"] += 1
    aug = month_row(env, "2026-08")
    sep = month_row(env, "2026-09")
    oct_row = month_row(env, "2026-10")
    dec = month_row(env, "2026-12")
    months_match = all(
        month_row(env, month)["refund_count"] == cell["count"]
        and month_row(env, month)["refunded"] == cell["money"]
        and month_row(env, month)["same_month_count"] == cell["same"]
        for month, cell in raw_month.items())
    ok2 = (sorted(raw_month) == ["2026-08", "2026-10", "2026-12"]
           and aug["refund_count"] == 1
           and aug["refunded"] == 10
           and aug["same_month_count"] == 1
           and oct_row["refund_count"] == 2
           and oct_row["refunded"] == 9
           and oct_row["same_month_count"] == 1
           and dec["refund_count"] == 1
           and dec["refunded"] == 6
           and dec["same_month_count"] == 0
           and sep["refund_count"] == 0
           and sep["refunded"] == 0
           and env["refund_count"] == 4
           and env["refunded"] == 25
           and months_match)
    record("AC-BRM2", ok2,
           "raw_months=%r aug=%r oct=%r dec=%r sep=%r match=%r"
           % (sorted(raw_month),
              (aug["refund_count"], aug["refunded"],
               aug["same_month_count"]),
              (oct_row["refund_count"], oct_row["refunded"],
               oct_row["same_month_count"]),
              (dec["refund_count"], dec["refunded"],
               dec["same_month_count"]),
              (sep["refund_count"], sep["refunded"]), months_match))

    # -- AC-BRM3 contiguous grid and the honest zero months ----------
    grid = [row["month"] for row in env["months"]]
    nov = month_row(env, "2026-11")
    zero_ok = all(
        row["refund_count"] == 0 and row["refunded"] == 0
        and row["dev_refunded"] == 0
        and row["platform_refunded"] == 0
        and row["listing_count"] == 0
        and row["seller_count"] == 0
        and row["avg_refund_amount"] is None
        and row["same_month_count"] == 0
        for row in (sep, nov))
    ok3 = (grid == ["2026-08", "2026-09", "2026-10",
                    "2026-11", "2026-12"]
           and env["month_count"] == 5
           and env["active_month_count"] == 3
           and zero_ok
           and sep["running_refund_count"] == 1
           and nov["running_refund_count"] == 3
           and env["first_month"] == "2026-08"
           and env["last_month"] == "2026-12")
    record("AC-BRM3", ok3,
           "grid=%r month_count=%r active=%r zeros=%r carried=%r"
           % (grid, env["month_count"], env["active_month_count"],
              zero_ok, (sep["running_refund_count"],
                        nov["running_refund_count"])))

    # -- AC-BRM4 conservation, raw identity and the running leg ------
    conn = sqlite3.connect(am.db_path)
    raw_count, raw_money = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(amount), 0)"
        " FROM apimarket_refunds WHERE buyer_id = 'usr:bob'"
    ).fetchone()
    conn.close()
    sum_count = sum(row["refund_count"] for row in env["months"])
    sum_money = sum(row["refunded"] for row in env["months"])
    sum_dev = sum(row["dev_refunded"] for row in env["months"])
    sum_plat = sum(row["platform_refunded"] for row in env["months"])
    split_ok = all(row["refunded"] == row["dev_refunded"]
                   + row["platform_refunded"]
                   for row in env["months"])
    running = [row["running_refund_count"] for row in env["months"]]
    monotone = all(running[i] <= running[i + 1]
                   for i in range(len(running) - 1))
    ok4 = (sum_count == env["refund_count"] == int(raw_count) == 4
           and sum_money == env["refunded"] == int(raw_money) == 25
           and env["refunded"] == env["dev_refunded"]
           + env["platform_refunded"]
           and sum_dev == env["dev_refunded"]
           and sum_plat == env["platform_refunded"]
           and split_ok
           and running == [1, 1, 3, 3, 4]
           and monotone
           and running[-1] == env["refund_count"])
    record("AC-BRM4", ok4,
           "sums=%r raw=%r money=%r/%r split=%r running=%r"
           % ((sum_count, env["refund_count"]),
              int(raw_count), sum_money, int(raw_money), split_ok,
              running))

    # -- AC-BRM5 pooled average, never a mean of monthly means -------
    month_means = [row["avg_refund_amount"] for row in env["months"]
                   if row["refund_count"] > 0]
    averaged = round(sum(month_means) / len(month_means), 2)
    ok5 = (env["avg_refund_amount"] == 6.25
           and month_means == [10.0, 4.5, 6.0]
           and averaged == 6.83
           and env["avg_refund_amount"] != averaged
           and oct_row["avg_refund_amount"] == 4.5
           and env["largest_refund"] == 10
           and env["same_month_count"] == 2
           and env["latest_month_refund_count"] == 1
           and env["latest_month_refunded"] == 6)
    record("AC-BRM5", ok5,
           "pooled=%r month_means=%r mean_of_means=%r largest=%r"
           " same_month=%r latest=%r"
           % (env["avg_refund_amount"], month_means, averaged,
              env["largest_refund"], env["same_month_count"],
              (env["latest_month_refund_count"],
               env["latest_month_refunded"])))

    # -- AC-BRM6 cross-face identity, asymmetry and isolation --------
    profile = am.api_buyer_profile("usr:bob")
    carol = am.api_buyer_refund_months("usr:carol")
    dave = am.api_buyer_refund_months("usr:dave")
    carol_grid = [row["month"] for row in carol["months"]]
    conn = sqlite3.connect(am.db_path)
    market_count, market_money = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(amount), 0)"
        " FROM apimarket_refunds").fetchone()
    conn.close()
    sum_sellers = sum(row["seller_count"] for row in env["months"])
    ok6 = (env["refund_count"] == profile["refund_count"]
           and env["refunded"] == profile["refunded_total"]
           and carol["refund_count"] == 1
           and carol["refunded"] == 10
           and carol_grid == ["2026-08"]
           and carol["listing_count"] == 1
           and carol["seller_count"] == 1
           and oct_row["seller_count"] == 1
           and oct_row["listing_count"] == 2
           and oct_row["refund_count"] == 2
           and env["seller_count"] == 2
           and sum_sellers == 3
           and env["seller_count"] < sum_sellers
           and env["listing_count"] == 4
           and carol["refund_count"] + env["refund_count"] \
           + dave["refund_count"] == int(market_count) == 7
           and carol["refunded"] + env["refunded"] \
           + dave["refunded"] == int(market_money) == 49)
    record("AC-BRM6", ok6,
           "profile=%r carol=%r oct=%r envelope=%r marketsum=%r"
           % ((profile["refund_count"], profile["refunded_total"]),
              (carol["refund_count"], carol["refunded"],
               carol_grid),
              (oct_row["refund_count"], oct_row["seller_count"],
               oct_row["listing_count"]),
              (env["seller_count"], env["listing_count"]),
              (int(market_count), int(market_money))))

    # -- AC-BRM7 the peak law and the earlier-month tie-break --------
    dave_grid = [row["month"] for row in dave["months"]]
    ok7 = (env["peak_month"] == "2026-10"
           and env["peak_refund_count"] == 2
           and carol["peak_month"] == "2026-08"
           and carol["peak_refund_count"] == 1
           and dave_grid == ["2026-08", "2026-09", "2026-10"]
           and dave["peak_month"] == "2026-08"
           and dave["peak_refund_count"] == 1
           and empty["peak_month"] is None
           and env["scope"] == "buyer")
    record("AC-BRM7", ok7,
           "peak=%r dave=%r grid=%r empty_peak=%r"
           % ((env["peak_month"], env["peak_refund_count"]),
              (dave["peak_month"], dave["peak_refund_count"],
               dave_grid), dave_grid, empty["peak_month"]))

    # -- AC-BRM8 gates, purity, hygiene and wiring -------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad = ["", "   ", 123, ["usr:x"], {"a": 1}, "usr", b"usr:x"]
    bad_ok = []
    for form in bad:
        try:
            am.api_buyer_refund_months(form)
            bad_ok.append(False)
        except A.ApiMarketError as err:
            bad_ok.append(err.code == A.E_AM_BAD_ACCOUNT)
    bare = am.api_buyer_refund_months("usr:")
    digests_after_gates = market_digests(am)

    call_a = dumps(am.api_buyer_refund_months("usr:bob"))
    call_b = dumps(am.api_buyer_refund_months("usr:bob"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_buyer_refund_months("usr:bob"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_buyer_refund_months("usr:bob"))
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (all(bad_ok)
           and bare["month_count"] == 0
           and bare["refund_count"] == 0
           and bare["months"] == []
           and bare["scope"] == "buyer"
           and digests_before == digests_after_gates == digests_after
           and tx_before == tx_after
           and call_a == call_b == dumps(env)
           and call_c == call_d == dumps(env)
           and call_a != dumps(carol)
           and b'"ledger-apimarket-buyerrefundmonths"' in recon
           and b"test_apimarket_buyerrefundmonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-BRM8", ok8,
           "gates=%r bare=%r digests_same=%r tables=%d tx_same=%r"
           " bytes=%r wired=%r ascii=%r"
           % (all(bad_ok),
              (bare["month_count"], bare["refund_count"]),
              digests_before == digests_after, len(digests_before),
              tx_before == tx_after, call_c == call_d,
              b'"ledger-apimarket-buyerrefundmonths"' in recon,
              all(b < 128 for b in test_src)))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())