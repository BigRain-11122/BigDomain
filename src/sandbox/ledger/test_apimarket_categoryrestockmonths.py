"""Acceptance suite for the apimarket per-category monthly RESTOCK
pressure (BigDomain R3156; canon = the R2248 explore-queue seed row,
criteria AC-CRS1..AC-CRS8 registered in the R3156 PIN row BEFORE this
code existed).

Face under proof: APIMarketFace.api_category_restock_months.

api_market_restock_months answers the whole shelf and
api_seller_restock_months one shop, and the nine api_category_*_months
faces answer refunds, claims, supply, price, velocity, questions,
watch attention, watch conversion and ratings - so WHICH categories
absorb restock month over month had no face. This suite pins:

  - the 29-key envelope, the 15-key month rows, the 14-key category
    cells, the real-bool gate, the market scope and the honest empty
    world;
  - the booking law (a restock books in its own restocked_utc month AND
    under the category in force AT THAT STAMP, so one shelf that is
    revised between two restocks books under two buckets while neither
    month moves);
  - conservation (every month row equals its cells, the running
    accumulators end at the envelope totals) and the cross-face
    identity against api_market_restock_months on the market scope;
  - the sold-out denominator sampled by the same trio the category
    supply face uses, and the coverage law (numerator is a subset of
    the previous month-end denominator, None on a zero or absent
    denominator, never clamped);
  - the episode law (start at the first stamp reaching zero on a live
    finite shelf, end at the first later positive stamp, kind restock
    or refund), an episode booked under its START bucket while its
    restock books under the stamp bucket, pooled latency and the open
    episode;
  - the contiguous grid, the honest zero month, the category ordering
    with the uncategorized bucket last and the peak/earlier-month law;
  - the category axis and the include_uncategorized flag on every
    aggregate;
  - purity (zero row mutations, zero token movement), two-call and
    two-instance byte identity, the reconcile wiring and ASCII/LF
    hygiene.

Usage: python test_apimarket_categoryrestockmonths.py
"""

import hashlib
import io
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
import apimarket as A                 # noqa: E402 (R3156 face)
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
    "scope", "include_uncategorized", "month_count",
    "active_month_count", "category_count", "restock_count",
    "units_added", "listing_count", "seller_count",
    "sold_out_listing_count", "episode_count",
    "recovered_episode_count", "refund_recovered_episode_count",
    "open_episode_count", "restock_coverage", "mean_recovery_seconds",
    "mean_restock_recovery_seconds", "min_recovery_seconds",
    "max_recovery_seconds", "avg_units_per_restock",
    "largest_restock_units", "peak_month", "peak_units_added",
    "first_month", "last_month", "latest_month_units_added",
    "latest_month_sold_out_listing_count", "disclaimer", "months"}

ROW_KEYS = {
    "month", "as_of", "restock_count", "units_added",
    "listing_count", "seller_count", "category_count",
    "sold_out_listing_count", "restocked_from_soldout_count",
    "restock_coverage", "recovered_episode_count",
    "mean_recovery_seconds", "running_restock_count",
    "running_units_added", "categories"}

CELL_KEYS = {
    "category", "restock_count", "units_added", "listing_count",
    "seller_count", "sold_out_listing_count",
    "restocked_from_soldout_count", "restock_coverage",
    "recovered_episode_count", "mean_recovery_seconds",
    "avg_units_per_restock", "largest_restock_units",
    "running_restock_count", "running_units_added"}

DAY = 86400


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set
    before each write so the month buckets are reproducible."""

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


def payload(env):
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


def cell(row, category):
    for item in row["categories"]:
        if item["category"] == category:
            return item
    raise AssertionError("category %r missing from %r"
                         % (category, row["month"]))


def seed_world(led, dk, am, clock):
    """dana and frank publish six shelves across four buckets. Every law
    has one witness and one control:

      l1 tools supply 2: sells out 08-11, restocked 08-20 (+3), moves to
         data on 09-01, restocked again 09-10 (+2)
         -> the SAME shelf books 3 units under tools in August and 2
            under data in September, month blocks never re-dated
      l2 data supply 1: sells out 08-15, restocked 09-05 (+1)
         -> an August denominator cell and a September recovery (21d)
      l3 uncategorized supply 1: sells out 08-14, refunded 08-16
         -> a refund recovery (2d) that is never counted as restock
      l4 tools unlimited: bought 08-22
         -> an unlimited shelf is never sold out
      l5 media supply 1: sells out 09-25, never restocked
         -> an OPEN episode under media
      l6 tools supply 1: sells out 08-25, moves to media on 09-01,
         restocked 09-05 (+1)
         -> the episode books under its START bucket (tools, 11d) while
            the restock books under the STAMP bucket (media)
    """
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-CRS-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-CRS-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 500),
                    ("usr:" + who, "credit", 500)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)

    clock.value = "2026-08-01T00:00:00Z"
    l1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, supply=2, category="tools")["listing_id"]
    l2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 4, False,
                        supply=1, category="data")["listing_id"]
    l3 = am.publish_api("usr:frank", "chart-render", "Chart Render",
                        "chart image render endpoint", PAYLOAD, 6,
                        False, supply=1)["listing_id"]
    l4 = am.publish_api("usr:frank", "free-tier", "Free Tier API",
                        "unlimited sample endpoint", PAYLOAD, 4, False,
                        category="tools")["listing_id"]
    l5 = am.publish_api("usr:dana", "sample-pack", "Sample Pack",
                        "sample payload pack", PAYLOAD, 7, False,
                        supply=1, category="media")["listing_id"]
    l6 = am.publish_api("usr:dana", "audit-log", "Audit Log",
                        "audit trail export", PAYLOAD, 5, False,
                        supply=1, category="tools")["listing_id"]

    clock.value = "2026-08-10T10:00:00Z"
    am.purchase_api("usr:bob", l1, "ref-bob-l1")
    clock.value = "2026-08-11T10:00:00Z"
    am.purchase_api("usr:carol", l1, "ref-carol-l1")
    clock.value = "2026-08-14T10:00:00Z"
    p3 = am.purchase_api("usr:carol", l3, "ref-carol-l3")["purchase_id"]
    clock.value = "2026-08-15T10:00:00Z"
    am.purchase_api("usr:bob", l2, "ref-bob-l2")
    clock.value = "2026-08-16T10:00:00Z"
    am.refund_api("usr:carol", p3, "render stale")
    clock.value = "2026-08-20T10:00:00Z"
    am.restock_api("usr:dana", l1, 3)
    clock.value = "2026-08-22T10:00:00Z"
    am.purchase_api("usr:dave", l4, "ref-dave-l4")
    clock.value = "2026-08-25T10:00:00Z"
    am.purchase_api("usr:carol", l6, "ref-carol-l6")

    clock.value = "2026-09-01T00:00:00Z"
    am.revise_category("usr:dana", l1, category="data")
    am.revise_category("usr:dana", l6, category="media")
    clock.value = "2026-09-02T10:00:00Z"
    am.purchase_api("usr:dave", l1, "ref-dave-l1")
    am.purchase_api("usr:erin", l1, "ref-erin-l1")
    clock.value = "2026-09-05T10:00:00Z"
    am.restock_api("usr:dana", l2, 1)
    am.restock_api("usr:dana", l6, 1)
    clock.value = "2026-09-10T10:00:00Z"
    am.restock_api("usr:dana", l1, 2)
    clock.value = "2026-09-25T10:00:00Z"
    am.purchase_api("usr:bob", l5, "ref-bob-l5")
    return {"l1": l1, "l2": l2, "l3": l3, "l4": l4, "l5": l5, "l6": l6}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-categoryrestockmonths-")
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

    # -- AC-CRS1 contract, honest empty, real-bool gate --
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-crs-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_category_restock_months()
    bad_flag = []
    for bad in ("yes", 1, 0, None, [], {}):
        try:
            e_am.api_category_restock_months(bad)
            bad_flag.append(bad)
        except A.ApiMarketError as exc:
            if "E_AM_BAD_ARGS" not in str(exc):
                bad_flag.append(bad)
    e_am.close()
    e_dk.close()
    e_metered.close()
    e_led.close()

    ok1_empty = (
        set(empty) == ENVELOPE_KEYS
        and empty["scope"] == "market"
        and empty["include_uncategorized"] is True
        and empty["month_count"] == 0
        and empty["active_month_count"] == 0
        and empty["category_count"] == 0
        and empty["restock_count"] == 0
        and empty["units_added"] == 0
        and empty["listing_count"] == 0
        and empty["seller_count"] == 0
        and empty["sold_out_listing_count"] == 0
        and empty["episode_count"] == 0
        and empty["recovered_episode_count"] == 0
        and empty["refund_recovered_episode_count"] == 0
        and empty["open_episode_count"] == 0
        and empty["restock_coverage"] is None
        and empty["mean_recovery_seconds"] is None
        and empty["mean_restock_recovery_seconds"] is None
        and empty["min_recovery_seconds"] is None
        and empty["max_recovery_seconds"] is None
        and empty["avg_units_per_restock"] is None
        and empty["largest_restock_units"] is None
        and empty["peak_month"] is None
        and empty["peak_units_added"] is None
        and empty["first_month"] is None
        and empty["last_month"] is None
        and empty["latest_month_units_added"] == 0
        and empty["latest_month_sold_out_listing_count"] == 0
        and empty["months"] == []
        and empty["disclaimer"] == DISCLAIMER)

    ids = seed_world(led, dk, am, clock)
    env = am.api_category_restock_months()
    first_call = payload(env)

    ok1 = (ok1_empty
           and set(env) == ENVELOPE_KEYS
           and all(set(row) == ROW_KEYS for row in env["months"])
           and all(set(item) == CELL_KEYS
                   for row in env["months"]
                   for item in row["categories"])
           and env["scope"] == "market"
           and env["disclaimer"] == DISCLAIMER
           and bad_flag == [])
    record("AC-CRS1", ok1,
           "envelope=%d keys, rows=%d x %d keys, cells %d keys, empty"
           " world honest, six bad flags fail closed with"
           " E_AM_BAD_ARGS before any read"
           % (len(ENVELOPE_KEYS), len(env["months"]), len(ROW_KEYS),
              len(CELL_KEYS)))

    # -- AC-CRS2 booking law: own month, category at the stamp --
    aug = month_row(env, "2026-08")
    sep = month_row(env, "2026-09")
    conn = sqlite3.connect(am.db_path)
    raw = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(add_units), 0)"
        " FROM apimarket_supply_revisions").fetchone()
    raw_aug = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(add_units), 0)"
        " FROM apimarket_supply_revisions"
        " WHERE restocked_utc LIKE '2026-08%'").fetchone()
    raw_rev = conn.execute(
        "SELECT COUNT(*) FROM apimarket_category_revisions").fetchone()[0]
    conn.close()
    aug_tools = cell(aug, "tools")
    sep_data = cell(sep, "data")
    sep_media = cell(sep, "media")
    ok2 = (aug["restock_count"] == int(raw_aug[0])
           and aug["units_added"] == int(raw_aug[1])
           and env["restock_count"] == int(raw[0])
           and env["units_added"] == int(raw[1])
           and raw_rev == 2
           and aug["restock_count"] == 1
           and aug["units_added"] == 3
           and aug_tools["restock_count"] == 1
           and aug_tools["units_added"] == 3
           and cell(aug, "data")["restock_count"] == 0
           and sep["restock_count"] == 3
           and sep["units_added"] == 4
           and sep_data["restock_count"] == 2
           and sep_data["units_added"] == 3
           and sep_data["listing_count"] == 2
           and sep_media["restock_count"] == 1
           and sep_media["units_added"] == 1
           and cell(sep, "tools")["restock_count"] == 0)
    record("AC-CRS2", ok2,
           "restocks book in their own restocked_utc month and under"
           " the category in force at the stamp: l1 books 3 units under"
           " tools in Aug, then 2 under data in Sep after the 09-01"
           " revision; l6 books 1 under media; no earlier month moved")

    # -- AC-CRS3 conservation and cross-face identity --
    def row_equals_cells(row):
        for key in ("restock_count", "units_added", "listing_count",
                    "seller_count", "sold_out_listing_count",
                    "restocked_from_soldout_count",
                    "recovered_episode_count"):
            if row[key] != sum(c[key] for c in row["categories"]):
                return False
        return True

    mrs = am.api_market_restock_months()
    family = ("restock_count", "units_added", "listing_count",
              "seller_count", "episode_count",
              "recovered_episode_count",
              "refund_recovered_episode_count", "open_episode_count",
              "restock_coverage", "mean_recovery_seconds",
              "mean_restock_recovery_seconds", "min_recovery_seconds",
              "max_recovery_seconds", "avg_units_per_restock",
              "largest_restock_units", "peak_month", "peak_units_added",
              "first_month", "last_month", "latest_month_units_added",
              "latest_month_sold_out_listing_count")
    ok3 = (all(row_equals_cells(row) for row in env["months"])
           and aug["running_restock_count"] == 1
           and aug["running_units_added"] == 3
           and sep["running_restock_count"] == 4
           and sep["running_units_added"] == 7
           and env["restock_count"] == 4
           and env["units_added"] == 7
           and env["listing_count"] == 3
           and env["seller_count"] == 1
           and aug["seller_count"] == 1
           and sep["seller_count"] == 2
           and all(env[key] == mrs[key] for key in family)
           and all(month_row(env, row["month"])["restock_count"]
                   == row["restock_count"]
                   and month_row(env, row["month"])["units_added"]
                   == row["units_added"]
                   and month_row(env, row["month"])[
                       "sold_out_listing_count"]
                   == row["sold_out_listing_count"]
                   for row in mrs["months"]))
    record("AC-CRS3", ok3,
           "every month row equals its cells; running 1/3 then 4/7; and"
           " all %d restock-family numbers equal"
           " api_market_restock_months (the Sep seller_count reads 2"
           " seller-category pairs against 1 distinct seller, named)"
           % len(family))

    # -- AC-CRS4 denominator and coverage law --
    csm = am.api_category_supply_months()
    csm_rows = {row["month"]: row for row in csm["months"]}
    shared = [row["month"] for row in env["months"]
              if row["month"] in csm_rows]
    agree = True
    for month in shared:
        supply_cells = {c["category"]: c["sold_out_listing_count"]
                        for c in csm_rows[month]["categories"]}
        for item in month_row(env, month)["categories"]:
            if item["sold_out_listing_count"] != \
                    supply_cells.get(item["category"], 0):
                agree = False
    aug_data = cell(aug, "data")
    aug_tools_cell = cell(aug, "tools")
    ok4 = (agree
           and len(shared) == 2
           and aug["sold_out_listing_count"] == 2
           and aug_data["sold_out_listing_count"] == 1
           and aug_tools_cell["sold_out_listing_count"] == 1
           and aug["restock_coverage"] is None
           and aug["restocked_from_soldout_count"] == 0
           and sep["restocked_from_soldout_count"] == 1
           and sep["restock_coverage"] == 0.5
           and sep_data["restocked_from_soldout_count"] == 1
           and sep_data["restock_coverage"] == 1.0
           and cell(sep, "tools")["restocked_from_soldout_count"] == 0
           and cell(sep, "tools")["restock_coverage"] == 0.0
           and cell(sep, "media")["restock_coverage"] is None
           and sep["sold_out_listing_count"] == 1
           and cell(sep, "media")["sold_out_listing_count"] == 1)
    record("AC-CRS4", ok4,
           "sold-out cells agree with api_category_supply_months on both"
           " shared months (Aug data=1 tools=1); coverage divides by"
           " the PREVIOUS month-end same-bucket count: Aug None, Sep"
           " data 1/1=1.0, tools 0/1=0.0, media None on a zero"
           " denominator, row 1/2=0.5; the unlimited shelf is never"
           " sold out")

    # -- AC-CRS5 episode law, start-bucket attribution, latency --
    ok5 = (env["episode_count"] == 5
           and env["recovered_episode_count"] == 3
           and env["refund_recovered_episode_count"] == 1
           and env["open_episode_count"] == 1
           and env["restock_coverage"] == 0.6
           and env["mean_restock_recovery_seconds"] == (
               (9 * DAY + 21 * DAY + 11 * DAY) // 3)
           and env["min_recovery_seconds"] == 2 * DAY
           and env["max_recovery_seconds"] == 21 * DAY
           and env["mean_recovery_seconds"] == (
               (9 * DAY + 21 * DAY + 2 * DAY + 11 * DAY) // 4)
           and cell(aug, "tools")["recovered_episode_count"] == 1
           and cell(aug, "tools")["mean_recovery_seconds"] == 9 * DAY
           and cell(aug, None)["recovered_episode_count"] == 1
           and cell(aug, None)["mean_recovery_seconds"] == 2 * DAY
           and cell(sep, "data")["mean_recovery_seconds"] == 21 * DAY
           and cell(sep, "tools")["recovered_episode_count"] == 1
           and cell(sep, "tools")["mean_recovery_seconds"] == 11 * DAY
           and cell(sep, "media")["recovered_episode_count"] == 0)
    record("AC-CRS5", ok5,
           "five episodes: l1 restock 9d (tools), l2 restock 21d (data),"
           " l3 refund 2d (uncategorized), l5 open (media), l6 restock"
           " 11d booked under its START bucket tools even though its"
           " restock books under media; pooled envelope mean %s"
           % env["mean_recovery_seconds"])

    # -- AC-CRS6 grid, zero rows, ordering, peak --
    months = [row["month"] for row in env["months"]]
    aug_order = [item["category"] for item in aug["categories"]]
    ok6 = (months == ["2026-08", "2026-09"]
           and env["first_month"] == "2026-08"
           and env["last_month"] == "2026-09"
           and env["month_count"] == 2
           and env["active_month_count"] == 2
           and aug_order == ["data", "media", "tools", None]
           and aug["category_count"] == 4
           and aug["as_of"] == "2026-08-31T23:59:59Z"
           and sep["as_of"] == "2026-09-30T23:59:59Z"
           and env["peak_month"] == "2026-09"
           and env["peak_units_added"] == 4
           and env["latest_month_units_added"] == 4
           and env["avg_units_per_restock"] == 1
           and env["largest_restock_units"] == 3
           and cell(aug, "data")["restock_count"] == 0
           and cell(aug, "data")["avg_units_per_restock"] is None
           and cell(aug, "data")["largest_restock_units"] is None
           and cell(sep, "tools")["running_restock_count"] == 1
           and cell(sep, "tools")["running_units_added"] == 3)
    record("AC-CRS6", ok6,
           "one contiguous Aug..Sep window with month-end as_of"
           " stamps, cells ordered data/media/tools/uncategorized last,"
           " a zero-restock cell carries honest Nones, the peak takes"
           " Sep (4 units over Aug 3), 7 units over 4 restocks floors"
           " to 1 and the largest single restock is 3")

    # -- AC-CRS7 category axis and the flag on every aggregate --
    noflag = am.api_category_restock_months(False)
    noflag_aug = month_row(noflag, "2026-08")
    ok7 = (noflag["include_uncategorized"] is False
           and [item["category"] for item in noflag_aug["categories"]]
           == ["data", "media", "tools"]
           and noflag["category_count"] == 3
           and noflag["restock_count"] == 4
           and noflag["units_added"] == 7
           and noflag["episode_count"] == 4
           and noflag["recovered_episode_count"] == 3
           and noflag["refund_recovered_episode_count"] == 0
           and noflag["open_episode_count"] == 1
           and noflag["restock_coverage"] == 0.75
           and noflag["mean_recovery_seconds"] == (
               (9 * DAY + 21 * DAY + 11 * DAY) // 3)
           and noflag["sold_out_listing_count"] == 1
           and noflag_aug["sold_out_listing_count"] == 2
           and all(item["category"] is not None
                   for row in noflag["months"]
                   for item in row["categories"]))
    record("AC-CRS7", ok7,
           "the flag drops the uncategorized bucket from every cell AND"
           " every aggregate: three categories, the 2d refund episode"
           " leaves the episode family (5 -> 4), coverage reads 3/4,"
           " and no month row keeps a None cell")

    # -- AC-CRS8 purity, byte identity, wiring, hygiene --
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    second = am.api_category_restock_months()
    third = am.api_category_restock_months()
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    other_tmp = tempfile.mkdtemp(prefix="apimarket-crs-inst-")
    o_led, o_metered, o_dk, _o_gate, o_am = build_stack(
        os.path.join(other_tmp, "ledger.db"), cfg, lobby_cfg)
    other_empty = o_am.api_category_restock_months()
    o_am.close()
    o_dk.close()
    o_metered.close()
    o_led.close()

    bad_kwarg = False
    try:
        am.api_category_restock_months(include_uncategorized=True,
                                       dev_account="usr:dana")
    except TypeError:
        bad_kwarg = True
    except Exception:
        bad_kwarg = False

    wire = io.open(os.path.join(
        os.path.dirname(BASE), "reconcile_all.py"),
        encoding="utf-8").read()
    src_text = io.open(os.path.join(BASE, "apimarket.py"),
                       encoding="utf-8").read()
    src_bytes = io.open(os.path.join(BASE, "apimarket.py"),
                        "rb").read()
    suite_bytes = io.open(os.path.abspath(__file__), "rb").read()
    ok8 = (bad_kwarg
           and payload(second) == first_call
           and payload(third) == first_call
           and digests_before == digests_after
           and tx_before == tx_after
           and other_empty["months"] == []
           and "ledger-apimarket-categoryrestockmonths" in wire
           and wire.count(
               "ledger-apimarket-categoryrestockmonths") == 1
           and src_text.count("def api_category_restock_months(") == 1
           and all(byte < 128 for byte in src_bytes)
           and b"\r\n" not in suite_bytes
           and not suite_bytes.startswith(b"\xef\xbb\xbf"))
    record("AC-CRS8", ok8,
           "an unknown argument raises TypeError, two calls and two"
           " instances read byte-identically, table digests and"
           " ledger_tx sets unchanged, wired exactly once, ASCII/LF and"
           " BOM-free")

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    ok_files = shas_before == shas_after

    total = len(RESULTS)
    passed = sum(1 for _ac, ok in RESULTS if ok)
    print("\nSUITE %s %d/%d" % ("PASS" if passed == total else "FAIL",
                                passed, total))
    if not ok_files:
        print("FAIL product files mutated during the run")
    close_stack(am, dk, metered, led)
    return 0 if passed == total and ok_files else 1


if __name__ == "__main__":
    sys.exit(main())
