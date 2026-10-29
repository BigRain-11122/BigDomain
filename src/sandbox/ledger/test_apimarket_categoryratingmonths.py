"""Acceptance suite for the apimarket per-category monthly rating
intake (BigDomain R2242; canon = the R2240 explore-queue seed row 2/6
claimed in R2242, criteria AC-CRA1..AC-CRA8 registered in that row
BEFORE this code existed).

Face under proof: APIMarketFace.api_category_rating_months. The trust
family published the market month axis (api_market_rating_months) and a
seller's monthly intake (api_seller_rating_months) but never a category
axis, so a bucket whose service quality moved read exactly like the
market average around it. This suite pins:

  - the fifteen-key envelope, the ten-key month rows, the seven-key
    category cells, the resident disclaimer and the honest empty
    envelope;
  - the booking law on rated_utc where a revision never moves the
    month but does move the effective stars;
  - the contiguous grid with an honest zero month (None average, flat
    accumulator);
  - the star law (cells summing into their row, the low-star split,
    the pooled envelope average that is not a mean of the monthly
    means);
  - the category seam (_category_at_instant): a later revision never
    rewrites a booked month while later ratings fall into the new
    bucket;
  - the uncategorized flag (own bucket, dropped and recomputed when
    False, fail-closed on a non-bool);
  - the pure-read law and the byte-identical repeat;
  - three-instance byte identity over two restarts plus wiring and
    ASCII/LF hygiene.

Usage: python test_apimarket_categoryratingmonths.py
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
    "month_count", "active_month_count", "first_month", "last_month",
    "rating_count", "buyer_count", "star_sum", "avg_stars",
    "five_star_count", "low_star_count", "category_count",
    "peak_month", "peak_rating_count", "months", "disclaimer"}

ROW_KEYS = {
    "month", "rating_count", "buyer_count", "star_sum", "avg_stars",
    "five_star_count", "low_star_count", "category_count",
    "running_rating", "categories"}

CELL_KEYS = {
    "category", "rating_count", "buyer_count", "star_sum",
    "avg_stars", "five_star_count", "low_star_count"}

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


def cell_of(row, category):
    for cell in row["categories"]:
        if cell["category"] == category:
            return cell
    raise AssertionError("cell %r missing from %r"
                         % (category, row["month"]))


def seed_world(led, dk, am, clock):
    """Two sellers. dana owns t1 (tools, later data) and d2 (data);
    gina owns g1 (data) and u1 (no category at all).

    JAN: bo buys t1 and rates 5, cy buys t1 and rates 4 (both tools),
    di buys g1 and rates 2 (data). FEB: no rating at all - the honest
    zero month. MAR: dana revises t1 from tools to data, ed buys t1 and
    rates 3 so that rating books in the DATA bucket of March, and bo
    REVISES his January rating down to 1 star, which must stay in the
    January tools cell and lower that cell's mean. APR: cy buys d2 and
    rates 5, fa buys g1's uncategorized sibling u1 and rates 4.

    January: tools cell 2 ratings star sum 5, data cell 1 rating star
    sum 2, row 3 ratings star sum 7 average 2.33.
    March: data cell 1 rating of 3 stars.
    April: data cell 1 rating of 5 stars, uncategorized cell 1 rating
    of 4 stars.
    Pooled: 6 ratings, star sum 19, average 3.17, 5 distinct buyers,
    1 five-star, 2 low-star, three buckets (tools, data, uncategorized).
    """

    led.mint_to_pool("pool:reserve", 40000, "SETTLE-CRA-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-CRA-S",
                     "settlement")
    for dev in ("dana", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)
    for who in ("bo", "cy", "di", "ed", "fa"):
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
    u1 = am.publish_api("usr:gina", "u1", "Gina Plain API",
                        "gina plain payloads", PAYLOAD, 10,
                        False)["listing_id"]

    clock.value = "2026-01-05T00:00:00Z"
    am.purchase_api("usr:bo", t1, "ref-cra-bo")
    r_bo = am.rate_api("usr:bo", t1, 5)["rating_id"]
    clock.value = "2026-01-06T00:00:00Z"
    am.purchase_api("usr:cy", t1, "ref-cra-cy")
    am.rate_api("usr:cy", t1, 4)
    clock.value = "2026-01-07T00:00:00Z"
    am.purchase_api("usr:di", g1, "ref-cra-di")
    am.rate_api("usr:di", g1, 2)

    clock.value = "2026-03-01T00:00:00Z"
    am.revise_category("usr:dana", t1, category="data")
    clock.value = "2026-03-02T00:00:00Z"
    am.purchase_api("usr:ed", t1, "ref-cra-ed")
    am.rate_api("usr:ed", t1, 3)
    clock.value = "2026-03-05T00:00:00Z"
    am.revise_rating("usr:bo", r_bo, 1)

    clock.value = "2026-04-05T00:00:00Z"
    am.purchase_api("usr:cy", d2, "ref-cra-cy2")
    am.rate_api("usr:cy", d2, 5)
    clock.value = "2026-04-06T00:00:00Z"
    am.purchase_api("usr:fa", u1, "ref-cra-fa")
    am.rate_api("usr:fa", u1, 4)

    return {"t1": t1, "d2": d2, "g1": g1, "u1": u1, "r_bo": r_bo}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-categoryratingmonths-")
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
    seed_world(led, dk, am, _CLOCK)

    # -- AC-CRA1 the contract and the honest empty envelope -------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-cra-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_category_rating_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_category_rating_months()
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    cells_ok = all(set(cell.keys()) == CELL_KEYS
                   for row in env["months"]
                   for cell in row["categories"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok and cells_ok
           and env["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["active_month_count"] == 0
           and empty["months"] == []
           and empty["rating_count"] == 0
           and empty["star_sum"] == 0
           and empty["avg_stars"] is None
           and empty["category_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_rating_count"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None)
    record("AC-CRA1", ok1,
           "env_keys=%d exact=%r rows=%r cells=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              cells_ok, (empty["month_count"], empty["avg_stars"],
                         empty["peak_month"])))

    # -- AC-CRA2 the booking law on rated_utc ---------------------
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    jan_tools = cell_of(jan, "tools")
    mar_data = cell_of(mar, "data")
    ok2 = (jan_tools["rating_count"] == 2
           and jan_tools["star_sum"] == 5
           and mar_data["rating_count"] == 1
           and mar_data["star_sum"] == 3
           and [row["month"] for row in env["months"]] ==
           ["2026-01", "2026-02", "2026-03", "2026-04"])
    record("AC-CRA2", ok2,
           "jan_tools=%r mar_data=%r grid=%r"
           % ((jan_tools["rating_count"], jan_tools["star_sum"]),
              (mar_data["rating_count"], mar_data["star_sum"]),
              [row["month"] for row in env["months"]]))

    # -- AC-CRA3 the contiguous grid with an honest zero month ----
    feb = month_row(env, "2026-02")
    ok3 = (feb["rating_count"] == 0
           and feb["avg_stars"] is None
           and feb["star_sum"] == 0
           and feb["categories"] == []
           and feb["category_count"] == 0
           and feb["running_rating"] == 3
           and feb["five_star_count"] == 0
           and env["active_month_count"] == 3
           and env["month_count"] == 4
           and mar["running_rating"] == 4
           and env["months"][-1]["running_rating"] == 6)
    record("AC-CRA3", ok3,
           "feb=%r active=%d months=%d running=%r"
           % ((feb["rating_count"], feb["avg_stars"],
               feb["categories"], feb["running_rating"]),
              env["active_month_count"], env["month_count"],
              [row["running_rating"] for row in env["months"]]))

    # -- AC-CRA4 the star law and the pooled envelope average -----
    apr = month_row(env, "2026-04")
    sum_ok = all(
        row["rating_count"] == sum(c["rating_count"]
                                   for c in row["categories"])
        and row["star_sum"] == sum(c["star_sum"]
                                   for c in row["categories"])
        for row in env["months"])
    pooled = round(env["star_sum"] / float(env["rating_count"]), 2)
    means = [row["avg_stars"] for row in env["months"]
             if row["rating_count"] > 0]
    mean_of_means = round(sum(means) / float(len(means)), 2)
    ok4 = (sum_ok
           and jan_tools["five_star_count"] == 0
           and jan_tools["low_star_count"] == 1
           and jan_tools["avg_stars"] == 2.5
           and jan["avg_stars"] == 2.33
           and mar["avg_stars"] == 3.0
           and apr["avg_stars"] == 4.5
           and env["rating_count"] == 6
           and env["star_sum"] == 19
           and env["avg_stars"] == 3.17
           and pooled == 3.17
           and mean_of_means == 3.28
           and env["avg_stars"] != mean_of_means
           and env["five_star_count"] == 1
           and env["low_star_count"] == 2)
    record("AC-CRA4", ok4,
           "sum=%r jan_tools=%r env_avg=%r pooled=%r mom=%r"
           % (sum_ok, (jan_tools["avg_stars"],
                       jan_tools["five_star_count"],
                       jan_tools["low_star_count"]),
              env["avg_stars"], pooled, mean_of_means))

    # -- AC-CRA5 the category seam on revise_category -------------
    jan_data = cell_of(jan, "data")
    ok5 = (jan_data["rating_count"] == 1
           and jan_data["star_sum"] == 2
           and jan_data["avg_stars"] == 2.0
           and jan["category_count"] == 2
           and mar["category_count"] == 1
           and len(jan["categories"]) == 2
           and cell_of(mar, "data")["rating_count"] == 1
           and env["category_count"] == 3)
    record("AC-CRA5", ok5,
           "jan_cells=%d jan_data=%r mar_cells=%d buckets=%d"
           % (len(jan["categories"]),
              (jan_data["rating_count"], jan_data["star_sum"]),
              len(mar["categories"]), env["category_count"]))

    # -- AC-CRA6 the uncategorized flag ---------------------------
    tight = am.api_category_rating_months(include_uncategorized=False)
    t_apr = month_row(tight, "2026-04")
    ok6 = (env["category_count"] == 3
           and len(apr["categories"]) == 2
           and cell_of(apr, None)["rating_count"] == 1
           and cell_of(apr, None)["star_sum"] == 4
           and tight["rating_count"] == 5
           and tight["star_sum"] == 15
           and tight["avg_stars"] == 3.0
           and tight["buyer_count"] == 4
           and tight["category_count"] == 2
           and t_apr["rating_count"] == 1
           and len(t_apr["categories"]) == 1
           and tight["months"][-1]["running_rating"] == 5
           and [r["month"] for r in tight["months"]] ==
           ["2026-01", "2026-02", "2026-03", "2026-04"])
    raised = 0
    for bad in ("", 0, 1, [], {}, "yes", None):
        try:
            am.api_category_rating_months(include_uncategorized=bad)
        except A.ApiMarketError as exc:
            if exc.code == A.E_AM_BAD_ARGS:
                raised += 1
    ok6 = ok6 and raised == 7
    record("AC-CRA6", ok6,
           "full=%r tight=%r flag_gate=%d/7"

           % ((env["rating_count"], env["category_count"]),
              (tight["rating_count"], tight["category_count"]),
              raised))

    # -- AC-CRA7 purity and byte-identical repeat -----------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_category_rating_months())
    call_tight = dumps(am.api_category_rating_months(
        include_uncategorized=False))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    mkt = am.api_market_rating_months()
    ok7 = (call_a == dumps(env)
           and call_tight == dumps(tight)
           and env["rating_count"] == mkt["rating_count"] == 6
           and env["buyer_count"] == mkt["buyer_count"] == 5
           and env["star_sum"] == mkt["star_sum"] == 19
           and env["avg_stars"] == mkt["avg_stars"] == 3.17
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-CRA7", ok7,
           "repeat=%r cross=%r digests=%r tx=%r"
           % (call_a == dumps(env),
              (mkt["rating_count"], mkt["buyer_count"],
               mkt["avg_stars"]),
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-CRA8 restarts, wiring and hygiene ---------------------
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_category_rating_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_category_rating_months())
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (call_a == call_c == call_d == dumps(env)
           and b'"ledger-apimarket-categoryratingmonths"' in recon
           and b"test_apimarket_categoryratingmonths.py" in recon
           and b"def api_category_rating_months" in src
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-CRA8", ok8,
           "bytes_same=%r wired=%r ascii=%r crlf_clean=%r"
           % (call_a == call_d,
              b'"ledger-apimarket-categoryratingmonths"' in recon,
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