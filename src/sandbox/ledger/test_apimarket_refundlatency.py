"""Acceptance suite for the apimarket refund latency distribution
(BigDomain R2179; canon = the explore-queue claim row seeded in R2178
and claimed in R2179, criteria AC-RFLT1..AC-RFLT8 registered in that
claim note BEFORE this code existed - honesty law; the AC-RFLT prefix
and the five band/aggregate names were git-grep -F zero-occupancy
anchored 2026-10-28 rc=1, while the api_refund_latency name, this
suite name and the ledger-apimarket-refundlatency runner label were
occupied only by the R2178 seed row that announced them - disclosed
in the claim note).

Face under proof: APIMarketFace.api_refund_latency. The refund family
(propensity / register / exposure / category_refund_months) answers
money and headcount only, so "how long from the sale to the money
coming back" had no face. This window pins it:

  - a fifteen-key envelope, five-key band rows (six bands always
    present) and five-key month rows;
  - latency derived ONLY from the two stored stamps of one purchase,
    never a wall clock, never a zero for an unrefunded purchase;
  - a left-closed right-open exhaustive band partition where a stamp
    exactly on a boundary belongs to the UPPER band;
  - five aggregates over refunded rows only (average, median,
    nearest-rank p90, fastest, slowest);
  - two named crossings (same UTC date as the sale, a week or more);
  - a contiguous monthly leg bucketed by the month the refund landed
    in, with honest zero months;
  - cross-face conservation against api_market_stats and the raw
    tables;
  - zero row mutations, zero token movement, no arguments accepted,
    cross-restart byte identity and runner wiring.

Usage: python test_apimarket_refundlatency.py
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
import apimarket as A                 # noqa: E402 (R2179 face)
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

ENVELOPE_KEYS = {"purchase_count", "refund_count", "unrefunded_count",
                 "refund_rate", "avg_refund_seconds",
                 "median_refund_seconds", "p90_refund_seconds",
                 "fastest_seconds", "slowest_seconds",
                 "same_day_count", "over_week_count", "month_count",
                 "bands", "months", "disclaimer"}
BAND_KEYS = {"band", "lower_seconds", "upper_seconds", "refund_count",
             "refunded"}
MONTH_KEYS = {"month", "refund_count", "median_refund_seconds",
              "avg_refund_seconds", "slowest_seconds"}
BAND_LABELS = ["0-1h", "1-6h", "6-24h", "1-3d", "3-7d", "7d+"]

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions")
POOLS = ("pool:reserve", "pool:share")


class Clock(object):
    """Deterministic stamp holder (module clock patched, restored in
    main's finally block) so every latency below is exact."""

    def __init__(self):
        self.value = "2026-08-01T10:00:00Z"

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
    """Ground truth straight from the market tables, never from the
    face under proof. Also returns the raw stamps so the expected
    latencies are recomputed independently."""
    conn = sqlite3.connect(am.db_path)
    purchases = int(conn.execute(
        "SELECT COUNT(*) FROM apimarket_purchases").fetchone()[0])
    refunds = conn.execute(
        "SELECT f.refunded_utc, p.purchased_utc, f.amount"
        " FROM apimarket_refunds f JOIN apimarket_purchases p"
        " ON p.purchase_id = f.purchase_id"
        " ORDER BY f.refund_id").fetchall()
    conn.close()
    return purchases, [(str(a), str(b), int(c)) for a, b, c in refunds]


def expected_latencies(am):
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    out = []
    for refunded, purchased, amount in raw_totals(am)[1]:
        start = A.datetime.datetime.strptime(purchased, fmt)
        end = A.datetime.datetime.strptime(refunded, fmt)
        out.append((int((end - start).total_seconds()), amount))
    return out


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
    """Owner dana (d1 price 10, d2 price 3) and frank (d3 price 5).
    Six purchases, four refunds, two left unrefunded:

      1. bob   d1  08-01T10:00:00Z -> refund 08-01T10:00:30Z  =     30s
      2. carol d1  08-02T10:00:00Z -> refund 09-20T10:00:00Z  = 4233600s
      3. dave  d2  08-03T00:00:00Z -> never refunded
      4. erin  d3  09-01T00:00:00Z -> never refunded
      5. frank d2  09-10T08:00:00Z -> refund 09-10T18:00:00Z  =  36000s
      6. grace d1  09-15T00:00:00Z -> refund 09-15T01:00:00Z  =   3600s
                                    (exactly the 1h boundary)

    Refund months: 2026-08 (one) and 2026-09 (three), contiguous with
    no gap to fabricate."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-RFLT-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-RFLT-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin", "grace"):
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
    clock.value = "2026-08-01T10:00:00Z"
    p1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")["purchase_id"]
    clock.value = "2026-08-02T10:00:00Z"
    p2 = am.purchase_api("usr:carol", d1, "ref-carol-d1")["purchase_id"]
    clock.value = "2026-08-03T00:00:00Z"
    am.purchase_api("usr:dave", d2, "ref-dave-d2")
    clock.value = "2026-09-01T00:00:00Z"
    am.purchase_api("usr:erin", d3, "ref-erin-d3")
    clock.value = "2026-09-10T08:00:00Z"
    p5 = am.purchase_api("usr:frank", d2, "ref-frank-d2")["purchase_id"]
    clock.value = "2026-09-15T00:00:00Z"
    p6 = am.purchase_api("usr:grace", d1, "ref-grace-d1")["purchase_id"]
    clock.value = "2026-08-01T10:00:30Z"
    am.refund_api("usr:bob", p1, "instant reversal")
    clock.value = "2026-09-10T18:00:00Z"
    am.refund_api("usr:frank", p5, "ten hour settlement")
    clock.value = "2026-09-15T01:00:00Z"
    am.refund_api("usr:grace", p6, "exactly one hour")
    clock.value = "2026-09-20T10:00:00Z"
    am.refund_api("usr:carol", p2, "seven week settlement")
    return d1, d2, d3, (p1, p2, p5, p6)


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-refundlatency-")
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
    seed_world(led, dk, am, clock)

    env = am.api_refund_latency()
    bands = {b["band"]: b for b in env["bands"]}
    months = {m["month"]: m for m in env["months"]}

    # -- AC-RFLT1 envelope + row contract ------------------------------
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and [b["band"] for b in env["bands"]] == BAND_LABELS
           and all(set(b.keys()) == BAND_KEYS for b in env["bands"])
           and all(set(m.keys()) == MONTH_KEYS for m in env["months"])
           and env["disclaimer"] == DISCLAIMER)
    record("AC-RFLT1", ok1,
           "keys ok=%r bands=%r band rows ok=%r month rows ok=%r"
           % (set(env.keys()) == ENVELOPE_KEYS,
              [b["band"] for b in env["bands"]],
              all(set(b.keys()) == BAND_KEYS for b in env["bands"]),
              all(set(m.keys()) == MONTH_KEYS for m in env["months"])))

    # -- AC-RFLT2 stamp-only derivation, no wall clock, no zero -------
    expected = expected_latencies(am)
    exp_values = sorted(s for s, _a in expected)
    before = dumps(env)
    clock.value = "2027-12-31T23:59:59Z"
    after = dumps(am.api_refund_latency())
    clock.value = "2026-09-20T10:00:00Z"
    ok2 = (all(s >= 0 for s, _a in expected)
           and exp_values == [30, 3600, 36000, 4233600]
           and env["refund_count"] == len(expected) == 4
           and env["unrefunded_count"] == 2
           and env["fastest_seconds"] == 30
           and env["slowest_seconds"] == 4233600
           and before == after)
    record("AC-RFLT2", ok2,
           "stamp latencies=%r all non-negative=%r clock-shift"
           " identical=%r unrefunded excluded from averages=%r"
           % (exp_values, all(s >= 0 for s, _a in expected),
              before == after, env["unrefunded_count"] == 2))

    # -- AC-RFLT3 band partition + boundary ownership -----------------
    counts = [b["refund_count"] for b in env["bands"]]
    ok3 = (counts == [1, 1, 1, 0, 0, 1]
           and sum(counts) == env["refund_count"] == 4
           and sum(b["refunded"] for b in env["bands"]) == 33
           and bands["1-6h"]["refund_count"] == 1
           and bands["1-6h"]["lower_seconds"] == 3600
           and bands["0-1h"]["upper_seconds"] == 3600
           and bands["7d+"]["upper_seconds"] is None
           and env["over_week_count"] == bands["7d+"]["refund_count"] == 1
           and env["same_day_count"] == 3
           and [b["refunded"] for b in env["bands"]]
           == [10, 10, 3, 0, 0, 10])
    record("AC-RFLT3", ok3,
           "band counts=%r sum=%d refunded sum=%d boundary 3600 lands"
           " in 1-6h=%r over_week=%d same_day=%d"
           % (counts, sum(counts),
              sum(b["refunded"] for b in env["bands"]),
              bands["1-6h"]["refund_count"] == 1,
              env["over_week_count"], env["same_day_count"]))

    # -- AC-RFLT4 aggregates over refunded rows only ------------------
    ok4 = (env["avg_refund_seconds"] == 1068307.5
           and env["median_refund_seconds"] == 19800.0
           and env["p90_refund_seconds"] == 4233600
           and round(float(sum(exp_values)) / len(exp_values), 2)
           == env["avg_refund_seconds"])
    record("AC-RFLT4", ok4,
           "avg=%r median=%r p90=%r fastest=%r slowest=%r"
           % (env["avg_refund_seconds"], env["median_refund_seconds"],
              env["p90_refund_seconds"], env["fastest_seconds"],
              env["slowest_seconds"]))

    # -- AC-RFLT5 contiguous monthly leg, honest zero months ----------
    ok5 = (sorted(months) == ["2026-08", "2026-09"]
           and env["month_count"] == 2
           and sum(m["refund_count"] for m in env["months"]) == 4
           and months["2026-08"]["refund_count"] == 1
           and months["2026-08"]["median_refund_seconds"] == 30.0
           and months["2026-08"]["avg_refund_seconds"] == 30.0
           and months["2026-09"]["refund_count"] == 3
           and months["2026-09"]["median_refund_seconds"] == 36000.0
           and months["2026-09"]["slowest_seconds"] == 4233600
           and A._contiguous_months(["2026-08", "2026-09"])
           == ["2026-08", "2026-09"])
    record("AC-RFLT5", ok5,
           "months=%r count sums=%d aug=%r sep=%r zero-month shape"
           " proven by helper=%r"
           % (sorted(months),
              sum(m["refund_count"] for m in env["months"]),
              (months["2026-08"]["refund_count"],
               months["2026-08"]["median_refund_seconds"]),
              (months["2026-09"]["refund_count"],
               months["2026-09"]["median_refund_seconds"]),
              A._contiguous_months(["2026-08", "2026-10"])
              == ["2026-08", "2026-09", "2026-10"]))

    # -- AC-RFLT6 cross-face conservation -----------------------------
    purchases, raw_refunds = raw_totals(am)
    stats = am.api_market_stats()
    ok6 = (env["purchase_count"] == purchases == stats["purchase_count"]
           == 6
           and env["refund_count"] == len(raw_refunds)
           == stats["refund_count"] == 4
           and env["unrefunded_count"] == 2
           and env["refund_rate"] == 0.6667
           and round(float(env["refund_count"]) / env["purchase_count"], 4)
           == env["refund_rate"]
           and sum(b["refunded"] for b in env["bands"])
           == stats["refunded_tokens"])
    record("AC-RFLT6", ok6,
           "purchases face/raw/stats=%d/%d/%d refunds=%d/%d/%d"
           " rate=%r band refunded==stats refunded (%d/%d)"
           % (env["purchase_count"], purchases, stats["purchase_count"],
              env["refund_count"], len(raw_refunds),
              stats["refund_count"], env["refund_rate"],
              sum(b["refunded"] for b in env["bands"]),
              stats["refunded_tokens"]))

    # -- AC-RFLT7 pure read, no arguments ----------------------------
    frozen_before = frozen_digests(am)
    tx_before = ledger_tx_ids(led)
    pools_before = pool_balances(led)
    first = dumps(am.api_refund_latency())
    second = dumps(am.api_refund_latency())
    no_args_ok = True
    for call in (lambda: am.api_refund_latency(1),
                 lambda: am.api_refund_latency(limit=2),
                 lambda: am.api_refund_latency(None)):
        try:
            call()
            no_args_ok = False
        except TypeError:
            pass
    frozen_after = frozen_digests(am)
    tx_after = ledger_tx_ids(led)
    pools_after = pool_balances(led)
    ok7 = (first == second and no_args_ok
           and frozen_before == frozen_after
           and tx_before == tx_after and pools_before == pools_after)
    record("AC-RFLT7", ok7,
           "repeat identical=%r args rejected=%r digests frozen=%r"
           " ledger tx frozen=%r pools frozen=%r"
           % (first == second, no_args_ok,
              frozen_before == frozen_after, tx_before == tx_after,
              pools_before == pools_after))

    # -- AC-RFLT8 cross-restart + empty world + wiring + hygiene -----
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    two = dumps(am2.api_refund_latency())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    three = dumps(am3.api_refund_latency())
    close_stack(am3, dk3, metered3, led3)

    empty_dir = os.path.join(tmp, "empty")
    os.makedirs(empty_dir)
    empty_db = os.path.join(empty_dir, "ledger.db")
    led4, metered4, dk4, gate4, am4 = build_stack(
        empty_db, cfg, lobby_cfg)
    empty = am4.api_refund_latency()
    close_stack(am4, dk4, metered4, led4)

    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-refundlatency" in handle.read()
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
    ok8 = (first == two == three
           and set(empty.keys()) == ENVELOPE_KEYS
           and empty["purchase_count"] == 0
           and empty["refund_count"] == 0
           and empty["unrefunded_count"] == 0
           and empty["refund_rate"] is None
           and empty["avg_refund_seconds"] is None
           and empty["median_refund_seconds"] is None
           and empty["p90_refund_seconds"] is None
           and empty["fastest_seconds"] is None
           and empty["slowest_seconds"] is None
           and empty["month_count"] == 0
           and empty["months"] == []
           and [b["refund_count"] for b in empty["bands"]] == [0] * 6
           and wired and shas_before == shas_after and ascii_ok
           and not net_imports and outside_repo)
    record("AC-RFLT8", ok8,
           "three instances identical=%r empty world=%r wired=%r"
           " consumer shas stable=%r ascii=%r net imports=%d"
           " outside repo=%r"
           % (first == two == three,
              (empty["purchase_count"], empty["refund_count"],
               empty["bands"][0]["refund_count"],
               empty["months"]), wired, shas_before == shas_after,
              ascii_ok, len(net_imports), outside_repo))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())