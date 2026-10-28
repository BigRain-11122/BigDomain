"""Acceptance suite for the apimarket seller monthly rating intake
(BigDomain R2236; canon = the R2230 4/6 explore-queue seed row claimed
in R2236, criteria AC-SRT1..AC-SRT8 registered in that row BEFORE this
code existed).

Face under proof: APIMarketFace.api_seller_rating_months. The trust
family answered the market month axis (api_market_rating_months) and a
seller's LIFETIME star shape (api_seller_quality), so a shop whose
stars fell after a service change and one that was always mediocre read
identically. This suite pins:

  - the twenty-key envelope, the fourteen-key month rows, the resident
    disclaimer and the honest empty envelope;
  - the booking law on rated_utc where a revision never moves the month
    but does move the effective stars;
  - the contiguous grid with an honest zero month (None average, None
    coverage, flat accumulator);
  - the star law (five histogram buckets summing to the count, the
    low-star split, the two-decimal row mean) and the POOLED envelope
    average that is not a mean of monthly means;
  - reply coverage through the same seam api_rating_replies reads, with
    a reply landing months later raising its own rating's month;
  - the scope law (market benchmark on a seller scope, none on the
    market scope) and cross-face identity with
    api_market_rating_months;
  - the fail-closed account gate and the pure-read law;
  - three-instance byte identity over two restarts plus wiring and
    ASCII/LF hygiene.

Usage: python test_apimarket_sellerratingmonths.py
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
    "scope", "dev_account", "month_count", "active_month_count",
    "rating_count", "buyer_count", "star_sum", "avg_stars",
    "five_star_count", "low_star_count", "replied_count",
    "reply_coverage", "peak_month", "peak_rating_count",
    "first_month", "last_month", "latest_month_rating_count",
    "market_avg_stars", "months", "disclaimer"}

ROW_KEYS = {
    "month", "rating_count", "buyer_count", "star_sum", "avg_stars",
    "five_star_count", "four_star_count", "three_star_count",
    "two_star_count", "one_star_count", "low_star_count",
    "replied_count", "reply_coverage", "running_rating"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_questions", "apimarket_answers",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_rating_replies", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set
    before each write so the month buckets are reproducible."""

    def __init__(self):
        self.value = "2026-01-05T00:00:00Z"

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


def month_row(env, month):
    for row in env["months"]:
        if row["month"] == month:
            return row
    raise AssertionError("month %r missing from months" % (month,))


def seed_world(led, dk, am, clock):
    """Two sellers. dana owns t1 and d2, gina owns g1.

    JAN: bo buys t1 and rates 5, cy buys t1 and rates 4, di buys g1 and
    rates 2; dana answers bo's rating inside January.
    FEB: no rating at all - the honest zero month.
    MAR: ed buys t1 and rates 3, and bo REVISES his January rating down
    to 1 star - which must stay in January and lower that row's mean.
    dana answers cy's January rating in MARCH, so the January row's
    reply coverage moves and March gains no row of its own.
    APR: cy buys d2 and rates 5 (dana), nobody answers it.

    dana: 4 ratings over JAN(2), FEB(0), MAR(1), APR(1); star sum
    1 + 4 + 3 + 5 = 13, pooled mean 3.25 against a 3.5 mean of monthly
    means; 2 answered, coverage 0.5; peak January with 2.
    gina: 1 rating of 2 stars in January.
    Market: 5 ratings, star sum 15, pooled mean 3.0, 4 distinct buyers.
    """

    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SRT-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SRT-S",
                     "settlement")
    for dev in ("dana", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)
    for who in ("bo", "cy", "di", "ed"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)

    clock.value = "2026-01-02T00:00:00Z"
    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    d2 = am.publish_api("usr:dana", "d2", "Dana Data API",
                        "dana data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    clock.value = "2026-01-05T00:00:00Z"
    p_bo = am.purchase_api("usr:bo", t1, "ref-srt-bo")["purchase_id"]
    r_bo = am.rate_api("usr:bo", t1, 5)["rating_id"]
    clock.value = "2026-01-06T00:00:00Z"
    am.purchase_api("usr:cy", t1, "ref-srt-cy")
    r_cy = am.rate_api("usr:cy", t1, 4)["rating_id"]
    clock.value = "2026-01-07T00:00:00Z"
    am.purchase_api("usr:di", g1, "ref-srt-di")
    am.rate_api("usr:di", g1, 2)
    clock.value = "2026-01-09T00:00:00Z"
    am.reply_to_rating("usr:dana", r_bo, "thanks for the note")

    clock.value = "2026-03-02T00:00:00Z"
    am.purchase_api("usr:ed", t1, "ref-srt-ed")
    r_ed = am.rate_api("usr:ed", t1, 3)["rating_id"]
    clock.value = "2026-03-05T00:00:00Z"
    am.revise_rating("usr:bo", r_bo, 1)
    clock.value = "2026-03-20T00:00:00Z"
    am.reply_to_rating("usr:dana", r_cy, "working on the rate limit")

    clock.value = "2026-04-05T00:00:00Z"
    am.purchase_api("usr:cy", d2, "ref-srt-cy2")
    am.rate_api("usr:cy", d2, 5)

    return {"t1": t1, "d2": d2, "g1": g1, "r_bo": r_bo,
            "r_cy": r_cy, "r_ed": r_ed, "p_bo": p_bo}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerratingmonths-")
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

    # -- AC-SRT1 the contract and the honest empty envelope --------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-srt-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_rating_months()
    nobody = e_am.api_seller_rating_months("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_seller_rating_months("usr:dana")
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and set(nobody.keys()) == ENVELOPE_KEYS
           and rows_ok
           and env["disclaimer"] == DISCLAIMER
           and env["scope"] == "seller"
           and env["dev_account"] == "usr:dana"
           and nobody["month_count"] == 0
           and nobody["months"] == []
           and nobody["rating_count"] == 0
           and nobody["avg_stars"] is None
           and nobody["reply_coverage"] is None
           and nobody["star_sum"] == 0
           and nobody["first_month"] is None
           and nobody["last_month"] is None
           and empty["scope"] == "market"
           and empty["dev_account"] is None
           and empty["month_count"] == 0
           and empty["avg_stars"] is None
           and empty["market_avg_stars"] is None)
    record("AC-SRT1", ok1,
           "env_keys=%d exact=%r rows=%r empty=%r nobody=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              (empty["month_count"], empty["avg_stars"]),
              (nobody["month_count"], nobody["avg_stars"])))

    # -- AC-SRT2 the booking law on rated_utc ----------------------
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    ok2 = (jan["rating_count"] == 2
           and jan["star_sum"] == 5
           and mar["rating_count"] == 1
           and mar["star_sum"] == 3
           and [row["month"] for row in env["months"]] ==
           ["2026-01", "2026-02", "2026-03", "2026-04"])
    record("AC-SRT2", ok2,
           "jan=%r mar=%r grid=%r"
           % ((jan["rating_count"], jan["star_sum"]),
              (mar["rating_count"], mar["star_sum"]),
              [row["month"] for row in env["months"]]))

    # -- AC-SRT3 the contiguous grid with an honest zero month -----
    feb = month_row(env, "2026-02")
    ok3 = (feb["rating_count"] == 0
           and feb["avg_stars"] is None
           and feb["reply_coverage"] is None
           and feb["star_sum"] == 0
           and feb["running_rating"] == 2
           and feb["five_star_count"] == 0
           and env["active_month_count"] == 3
           and env["month_count"] == 4)
    record("AC-SRT3", ok3,
           "feb=%r active=%d months=%d"
           % ((feb["rating_count"], feb["avg_stars"],
               feb["reply_coverage"], feb["running_rating"]),
              env["active_month_count"], env["month_count"]))

    # -- AC-SRT4 the star law and the pooled envelope average ------
    apr = month_row(env, "2026-04")
    histogram_ok = all(
        (row["five_star_count"] + row["four_star_count"]
         + row["three_star_count"] + row["two_star_count"]
         + row["one_star_count"]) == row["rating_count"]
        for row in env["months"])
    pooled = round(env["star_sum"] / float(env["rating_count"]), 2)
    means = [row["avg_stars"] for row in env["months"]
             if row["rating_count"] > 0]
    mean_of_means = round(sum(means) / float(len(means)), 2)
    ok4 = (histogram_ok
           # bo's January rating was REVISED to one star, so January
           # carries no five-star bucket at all and the revision moved
           # the effective stars without moving the month (AC-SRT2/4).
           and jan["five_star_count"] == 0
           and jan["four_star_count"] == 1
           and jan["one_star_count"] == 1
           and jan["low_star_count"] == 1
           and jan["avg_stars"] == 2.5
           and mar["avg_stars"] == 3.0
           and apr["avg_stars"] == 5.0
           and env["rating_count"] == 4
           and env["star_sum"] == 13
           and env["avg_stars"] == 3.25
           and pooled == 3.25
           and mean_of_means == 3.5
           and env["avg_stars"] != mean_of_means
           and env["five_star_count"] == 1
           and env["low_star_count"] == 1)
    record("AC-SRT4", ok4,
           "hist=%r jan_avg=%r env_avg=%r pooled=%r mean_of_means=%r"
           % (histogram_ok, jan["avg_stars"], env["avg_stars"],
              pooled, mean_of_means))

    # -- AC-SRT5 reply coverage through the reply seam -------------
    gina = am.api_seller_rating_months("usr:gina")
    g_jan = month_row(gina, "2026-01")
    ok5 = (jan["replied_count"] == 2
           and jan["reply_coverage"] == 1.0
           and mar["replied_count"] == 0
           and mar["reply_coverage"] == 0.0
           and apr["replied_count"] == 0
           and env["replied_count"] == 2
           and env["reply_coverage"] == 0.5
           and all(row["replied_count"] <= row["rating_count"]
                   for row in env["months"])
           and g_jan["replied_count"] == 0
           and g_jan["reply_coverage"] == 0.0)
    record("AC-SRT5", ok5,
           "jan=%r mar=%r apr=%r env=%r gina=%r"
           % ((jan["replied_count"], jan["reply_coverage"]),
              (mar["replied_count"], mar["reply_coverage"]),
              (apr["replied_count"], apr["reply_coverage"]),
              (env["replied_count"], env["reply_coverage"]),
              (g_jan["replied_count"], g_jan["reply_coverage"])))

    # -- AC-SRT6 scope law and cross-face identity -----------------
    market = am.api_seller_rating_months()
    mkt = am.api_market_rating_months()
    ok6 = (env["market_avg_stars"] == 3.0
           and market["market_avg_stars"] is None
           and market["scope"] == "market"
           and env["rating_count"] == 4
           and gina["rating_count"] == 1
           and gina["dev_account"] == "usr:gina"
           and market["rating_count"] == mkt["rating_count"] == 5
           and market["buyer_count"] == mkt["buyer_count"] == 4
           and market["star_sum"] == mkt["star_sum"] == 15
           and market["avg_stars"] == mkt["avg_stars"] == 3.0
           and market["peak_month"] == "2026-01"
           and market["peak_rating_count"] == 3)
    record("AC-SRT6", ok6,
           "seller_bench=%r market_bench=%r market=%r cross=%r"
           % (env["market_avg_stars"], market["market_avg_stars"],
              (market["rating_count"], market["buyer_count"],
               market["avg_stars"]),
              (mkt["rating_count"], mkt["buyer_count"],
               mkt["avg_stars"])))

    # -- AC-SRT7 the gate and the pure read -----------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    raised = 0
    for form in ("", "  ", "dana", 123, [], {}, 1.0):
        try:
            am.api_seller_rating_months(form)
        except A.ApiMarketError as exc:
            if exc.code == A.E_AM_BAD_ACCOUNT:
                raised += 1
    bare = am.api_seller_rating_months("usr:")
    call_a = dumps(am.api_seller_rating_months("usr:dana"))
    call_b = dumps(am.api_seller_rating_months("usr:dana"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (raised == 7
           and bare["month_count"] == 0
           and call_a == call_b == dumps(env)
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-SRT7", ok7,
           "gate=%d/7 bare=%r deterministic=%r digests=%r tx=%r"
           % (raised, bare["month_count"], call_a == call_b,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-SRT8 restarts, wiring and hygiene ---------------------
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_seller_rating_months("usr:dana"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_seller_rating_months("usr:dana"))
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (call_a == call_c == call_d == dumps(env)
           and b'"ledger-apimarket-sellerratingmonths"' in recon
           and b"test_apimarket_sellerratingmonths.py" in recon
           and b"def api_seller_rating_months" in src
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-SRT8", ok8,
           "bytes_same=%r wired=%r ascii=%r crlf_clean=%r"
           % (call_a == call_d,
              b'"ledger-apimarket-sellerratingmonths"' in recon,
              all(b < 128 for b in test_src),
              b"\r\n" not in test_src))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())