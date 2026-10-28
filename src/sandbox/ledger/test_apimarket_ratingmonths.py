"""Acceptance suite for the apimarket monthly rating flow (BigDomain
R2202; canon = the R2202 explore-queue claim row, criteria
AC-RTM1..AC-RTM8 registered in that row BEFORE this code existed).

Face under proof: APIMarketFace.api_market_rating_months. Every rating
face answers a lifetime shape (api_ratings rows, api_seller_quality
histogram, api_market_stats average, api_rating_reply_latency delay,
api_rating_history one rating's revisions), so the market carried no
time axis over its trust signal. This suite pins:

  - the nineteen-key envelope, the nine-key month rows and the honest
    empty world;
  - the booking law (a rating books in its own rated_utc month and a
    revision never moves that month, nor does it add a month of its
    own);
  - the contiguous grid with an honest zero month whose average is
    None rather than a fabricated zero, plus the running accumulator;
  - conservation of counts, star sums, five-star and low-star counts,
    and the pooled (never mean-of-means) average law;
  - the peak laws with the earlier-month tie-break;
  - the scope law (seller isolation, the market benchmark on a seller
    scope, no self-benchmark on the market scope);
  - the front-door gate family and the honest empty prefix account;
  - cross-face identity with api_seller_quality;
  - the pure-read law (frozen table digests, constant ledger_tx set),
    cross-instance byte identity, wiring and ASCII/LF hygiene.

Usage: python test_apimarket_ratingmonths.py
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
    "five_star_count", "low_star_count", "revised_rating_count",
    "peak_month", "peak_rating_count", "first_month", "last_month",
    "latest_month_rating_count", "market_avg_stars", "disclaimer",
    "months"}

ROW_KEYS = {
    "month", "rating_count", "buyer_count", "star_sum", "avg_stars",
    "five_star_count", "low_star_count", "revised_count",
    "running_rating"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_refunds", "apimarket_category_revisions")


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
    """Two sellers. dana owns t1 and d1, gina owns g1.

    JAN: bo rates t1 five stars, cy rates t1 three stars (2 ratings,
    star sum 8, average 4.0).
    FEB: no rating at all (the honest zero row of the grid).
    MAR: di rates d1 one star, bo rates g1 four stars (2 ratings,
    star sum 5, average 2.5).
    APR: cy revises the JANUARY rating from three to two stars, so the
    January average becomes 3.5 while the January row stays January
    and April never becomes a month of its own.

    Market after the revision: 4 ratings, star sum 12, average 3.0,
    1 five-star, 2 low-star (one 2 and one 1), 3 distinct buyers,
    peak January with 2 (earlier tie-break against March 2).
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-RTM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-RTM-S",
                     "settlement")
    for dev in ("dana", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)
    for who in ("bo", "cy", "di"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)

    clock.value = "2026-01-05T00:00:00Z"
    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    d1 = am.publish_api("usr:dana", "d1", "Dana Data API",
                        "dana data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    clock.value = "2026-01-09T00:00:00Z"
    am.purchase_api("usr:bo", t1, "buy-bo-t1")
    am.purchase_api("usr:cy", t1, "buy-cy-t1")

    clock.value = "2026-01-12T00:00:00Z"
    bo_t1 = am.rate_api("usr:bo", t1, 5)["rating_id"]
    clock.value = "2026-01-13T00:00:00Z"
    cy_t1 = am.rate_api("usr:cy", t1, 3)["rating_id"]

    clock.value = "2026-03-02T00:00:00Z"
    am.purchase_api("usr:di", d1, "buy-di-d1")
    clock.value = "2026-03-04T00:00:00Z"
    am.purchase_api("usr:bo", g1, "buy-bo-g1")

    clock.value = "2026-03-09T00:00:00Z"
    am.rate_api("usr:di", d1, 1)
    clock.value = "2026-03-10T00:00:00Z"
    am.rate_api("usr:bo", g1, 4)

    clock.value = "2026-04-02T00:00:00Z"
    am.revise_rating("usr:cy", cy_t1, 2)

    return {"t1": t1, "d1": d1, "g1": g1,
            "bo_t1": bo_t1, "cy_t1": cy_t1}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-ratingmonths-")
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

    # -- AC-RTM1 the contract and the honest empty world ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-rtm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_rating_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_market_rating_months()
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
           and env["disclaimer"] == DISCLAIMER
           and env["scope"] == "market"
           and env["dev_account"] is None
           and env["market_avg_stars"] is None
           and empty["scope"] == "market"
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["rating_count"] == 0
           and empty["buyer_count"] == 0
           and empty["star_sum"] == 0
           and empty["avg_stars"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_rating_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_rating_count"] is None)
    record("AC-RTM1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              (empty["month_count"], empty["avg_stars"],
               empty["months"])))

    # -- AC-RTM2 booking law: the revision never moves the month ---
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    grid = [row["month"] for row in env["months"]]
    ok2 = (grid == ["2026-01", "2026-02", "2026-03"]
           and jan["rating_count"] == 2
           and jan["star_sum"] == 7
           and jan["avg_stars"] == 3.5
           and jan["revised_count"] == 1
           and mar["rating_count"] == 2
           and mar["star_sum"] == 5
           and mar["revised_count"] == 0
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-03"
           and env["revised_rating_count"] == 1
           and env["rating_count"] == 4)
    record("AC-RTM2", ok2,
           "grid=%r jan=%r mar=%r revised=%r"
           % (grid, (jan["rating_count"], jan["star_sum"],
                     jan["avg_stars"], jan["revised_count"]),
              (mar["rating_count"], mar["star_sum"]),
              env["revised_rating_count"]))

    # -- AC-RTM3 contiguous grid, honest zero month, accumulator ---
    feb = month_row(env, "2026-02")
    ok3 = (env["month_count"] == len(env["months"]) == 3
           and env["active_month_count"] == 2
           and feb["rating_count"] == 0
           and feb["buyer_count"] == 0
           and feb["star_sum"] == 0
           and feb["avg_stars"] is None
           and feb["five_star_count"] == 0
           and feb["low_star_count"] == 0
           and feb["revised_count"] == 0
           and feb["running_rating"] == jan["running_rating"] == 2
           and [row["running_rating"] for row in env["months"]]
           == [2, 2, 4]
           and env["months"][-1]["running_rating"]
           == env["rating_count"] == 4
           and env["latest_month_rating_count"] == 2)
    record("AC-RTM3", ok3,
           "months=%d active=%d feb=%r running=%r"
           % (env["month_count"], env["active_month_count"],
              (feb["rating_count"], feb["avg_stars"]),
              [row["running_rating"] for row in env["months"]]))

    # -- AC-RTM4 conservation and the pooled average law -----------
    sum_count = sum(row["rating_count"] for row in env["months"])
    sum_stars = sum(row["star_sum"] for row in env["months"])
    ok4 = (sum_count == env["rating_count"] == 4
           and sum_stars == env["star_sum"] == 12
           and env["avg_stars"] == 3.0
           and round(float(env["star_sum"]) / env["rating_count"], 2)
           == env["avg_stars"]
           and env["five_star_count"] == 1
           and env["low_star_count"] == 2
           and jan["five_star_count"] == 1
           and jan["low_star_count"] == 1
           and mar["five_star_count"] == 0
           and mar["low_star_count"] == 1
           and all(
               (row["avg_stars"] is None
                if row["rating_count"] == 0
                else row["avg_stars"] == round(
                    row["star_sum"] / float(row["rating_count"]), 2))
               for row in env["months"])
           and env["buyer_count"] == 3
           and jan["buyer_count"] == 2
           and mar["buyer_count"] == 2
           and env["buyer_count"] <= sum(row["buyer_count"]
                                          for row in env["months"]))
    record("AC-RTM4", ok4,
           "counts=%r stars=%r avg=%r five/low=%r buyers=%r"
           % (sum_count, sum_stars, env["avg_stars"],
              (env["five_star_count"], env["low_star_count"]),
              (env["buyer_count"], jan["buyer_count"],
               mar["buyer_count"])))

    # -- AC-RTM5 peak laws with the earlier-month tie-break --------
    empty_peak = empty_peak_pair(cfg, lobby_cfg)
    ok5 = (env["peak_month"] == "2026-01"
           and env["peak_rating_count"] == 2
           and empty_peak == (None, None))
    record("AC-RTM5", ok5,
           "peak=%r empty=%r"
           % ((env["peak_month"], env["peak_rating_count"]),
              empty_peak))

    # -- AC-RTM6 scope law: isolation and the market benchmark -----
    dana = am.api_market_rating_months("usr:dana")
    gina = am.api_market_rating_months("usr:gina")
    dana_grid = [row["month"] for row in dana["months"]]
    dana_jan = month_row(dana, "2026-01")
    ok6 = (dana["scope"] == "seller"
           and dana["dev_account"] == "usr:dana"
           and dana["rating_count"] == 3
           and dana["star_sum"] == 8
           and dana["avg_stars"] == 2.67
           and dana["market_avg_stars"] == 3.0
           and dana["low_star_count"] == 2
           and dana["five_star_count"] == 1
           and dana_grid == ["2026-01", "2026-02", "2026-03"]
           and dana_jan["star_sum"] == 7
           and month_row(dana, "2026-03")["rating_count"] == 1
           and gina["scope"] == "seller"
           and gina["rating_count"] == 1
           and gina["avg_stars"] == 4.0
           and gina["market_avg_stars"] == 3.0
           and gina["low_star_count"] == 0
           and [row["month"] for row in gina["months"]]
           == ["2026-03"]
           and gina["months"][0]["five_star_count"] == 0)
    record("AC-RTM6", ok6,
           "dana=%r gina=%r market_avg=%r"
           % ((dana["rating_count"], dana["avg_stars"],
               dana["low_star_count"]), (gina["rating_count"],
                                         gina["avg_stars"]),
              dana["market_avg_stars"]))

    # -- AC-RTM7 gate family, honest empty prefix, cross-face ------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad = ["", "u", "usr", "user:bo", 123, [], {"usr:bo": 1}, False]
    refused = 0
    for form in bad:
        try:
            am.api_market_rating_months(form)
        except A.ApiMarketError as exc:
            if str(exc).split(":")[0].strip() == A.E_AM_BAD_ACCOUNT:
                refused += 1
    bare = am.api_market_rating_months("usr:")
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    quality = am.api_seller_quality("usr:dana")
    ok7 = (refused == len(bad)
           and bare["scope"] == "seller"
           and bare["rating_count"] == 0
           and bare["months"] == []
           and bare["avg_stars"] is None
           and digests_before == digests_after
           and tx_before == tx_after
           and quality["rating_count"] == dana["rating_count"]
           and round(quality["rating_avg"], 2) == dana["avg_stars"])
    record("AC-RTM7", ok7,
           "refused=%d/%d bare=%r digests_same=%r tx_same=%r"
           " quality=%r"
           % (refused, len(bad),
              (bare["rating_count"], bare["months"]),
              digests_before == digests_after, tx_before == tx_after,
              (quality["rating_count"], round(quality["rating_avg"],
                                              2))))

    # -- AC-RTM8 pure read, determinism, hygiene and wiring --------
    call_a = dumps(am.api_market_rating_months())
    call_b = dumps(am.api_market_rating_months())
    digests_end = market_digests(am)
    tx_end = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_market_rating_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_market_rating_months())
    dana3 = dumps(am3.api_market_rating_months("usr:dana"))
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (digests_before == digests_end
           and tx_before == tx_end
           and call_a == call_b == call_c == call_d == dumps(env)
           and dana3 == dumps(dana)
           and b'"ledger-apimarket-ratingmonths"' in recon
           and b"test_apimarket_ratingmonths.py" in recon
           and b"def api_market_rating_months" in src
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-RTM8", ok8,
           "digests_same=%r tx_same=%r bytes=%r wired=%r ascii=%r"
           % (digests_before == digests_end, tx_before == tx_end,
              call_a == call_d,
              b'"ledger-apimarket-ratingmonths"' in recon,
              all(b < 128 for b in test_src)))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


def empty_peak_pair(cfg, lobby_cfg):
    tmp = tempfile.mkdtemp(prefix="apimarket-rtm-empty2-")
    led, metered, dk, gate, am = build_stack(
        os.path.join(tmp, "ledger.db"), cfg, lobby_cfg)
    env = am.api_market_rating_months()
    close_stack(am, dk, metered, led)
    return (env["peak_month"], env["peak_rating_count"])


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())