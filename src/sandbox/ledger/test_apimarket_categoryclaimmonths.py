"""Acceptance suite for the apimarket per-category monthly claim
pressure (BigDomain R2229; canon = the R2213 explore-queue seed row
claimed in R2229, criteria AC-CKM1..AC-CKM8 registered in that row
BEFORE this code existed).

Face under proof: APIMarketFace.api_category_claim_months.

api_market_claim_months answers the whole market on a month axis,
api_claims the three present status views, api_claim_latency how long
each leg took and api_category_refund_months the refunded money by
category. Nothing answered WHICH CATEGORIES absorb after-sales claim
pressure month over month. This suite pins:

  - the eighteen-key envelope, the twelve-key month rows, the
    eleven-key category cells, the disclaimer and the honest empty
    world;
  - the booking law: a claim books in its own opened_utc month and in
    the category in force AT THAT INSTANT, so a later category
    revision moves neither an already-booked month nor its bucket;
  - the status seam (refunded beats withdrawn beats answered beats
    open) partitioning claim_count, and the money law keeping money on
    the claim side so a refund with no claim never appears;
  - the contiguous grid with an honest zero month whose refund_rate is
    None, the monotone running total and the per-category running
    cells;
  - the bucket ordering (category ascending, uncategorized last) and
    the include_uncategorized flag, which drops that bucket AND
    recomputes every aggregate, plus the fail-closed shape gate;
  - the peak law with the earlier-month tie-break and the honest None
    on an empty world;
  - cross-face identity against api_market_claim_months;
  - the pure-read law (frozen table digests, constant ledger_tx set),
    cross-instance byte identity over two full-stack restarts, wiring
    and ASCII/LF hygiene.

Usage: python test_apimarket_categoryclaimmonths.py
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
    "claim_count", "open_count", "answered_count", "withdrawn_count",
    "refunded_count", "claim_amount", "refunded_amount", "refund_rate",
    "category_count", "month_count", "active_month_count", "peak_month",
    "peak_claim_count", "first_month", "last_month",
    "latest_month_claim_count", "disclaimer", "months"}

ROW_KEYS = {
    "month", "claim_count", "open_count", "answered_count",
    "withdrawn_count", "refunded_count", "claim_amount",
    "refunded_amount", "refund_rate", "category_count", "running_claim",
    "categories"}

CELL_KEYS = {
    "category", "claim_count", "open_count", "answered_count",
    "withdrawn_count", "refunded_count", "claim_amount",
    "refunded_amount", "refund_rate", "avg_claim_amount",
    "running_claim"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_claims", "apimarket_claim_responses",
          "apimarket_claim_withdrawals", "apimarket_claim_notes",
          "apimarket_questions", "apimarket_answers",
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


def cell(row, category):
    for entry in row["categories"]:
        if entry["category"] == category:
            return entry
    raise AssertionError("category %r missing from %r"
                         % (category, row["month"]))


def seed_world(led, dk, am, clock):
    """Two sellers. dana owns t1 (tools) and d1 (data); gina owns
    g1 (data) and u1 (uncategorized).

    JAN: cy claims on t1 (tools, refunded in APRIL), jo claims on d1
    (data, answered inside January), di claims on g1 (data, withdrawn
    in February), hi claims on u1 (the uncategorized bucket, still
    open).
    FEB 15: dana re-files d1 from data to audio - a revision that must
    never move a January bucket already booked.
    MAR: ed claims on d1 (now audio), fa claims on t1 (tools,
    answered inside March).
    MAR 20: bo's purchase with NO claim is refunded - it must never
    appear on this face.
    APR 10: cy's JANUARY claim is settled by refund - the claim stays
    in January and April never becomes a row.

    Market scope: 6 claims; open 2, answered 2, withdrawn 1, refunded
    1; claim_amount 60; refunded_amount 10; refund_rate 0.1667;
    4 buckets; grid JAN..MAR with FEB honestly zero; peak January 4.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-CKM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-CKM-S",
                     "settlement")
    for dev in ("dana", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)
    for who in ("cy", "jo", "di", "hi", "ed", "fa", "bo"):
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
    u1 = am.publish_api("usr:gina", "u1", "Gina Misc API",
                        "gina misc payloads", PAYLOAD, 10, False,
                        category=None)["listing_id"]

    clock.value = "2026-01-06T00:00:00Z"
    p_cy = am.purchase_api("usr:cy", t1, "BUY-CKM-1")["purchase_id"]
    clock.value = "2026-01-06T00:00:01Z"
    p_jo = am.purchase_api("usr:jo", d1, "BUY-CKM-2")["purchase_id"]
    clock.value = "2026-01-06T00:00:02Z"
    p_di = am.purchase_api("usr:di", g1, "BUY-CKM-3")["purchase_id"]
    clock.value = "2026-01-06T00:00:03Z"
    p_hi = am.purchase_api("usr:hi", u1, "BUY-CKM-4")["purchase_id"]
    clock.value = "2026-01-06T00:00:04Z"
    p_fa = am.purchase_api("usr:fa", t1, "BUY-CKM-5")["purchase_id"]
    clock.value = "2026-01-14T00:00:00Z"
    p_bo = am.purchase_api("usr:bo", t1, "BUY-CKM-6")["purchase_id"]

    clock.value = "2026-01-08T00:00:00Z"
    c_cy = am.open_claim("usr:cy", p_cy,
                         "output unusable")["claim_id"]
    clock.value = "2026-01-09T00:00:00Z"
    c_jo = am.open_claim("usr:jo", p_jo,
                         "stale columns")["claim_id"]
    clock.value = "2026-01-11T00:00:00Z"
    c_di = am.open_claim("usr:di", p_di,
                         "missing rows")["claim_id"]
    clock.value = "2026-01-12T00:00:00Z"
    c_hi = am.open_claim("usr:hi", p_hi,
                         "what is this shelf")["claim_id"]
    clock.value = "2026-01-20T00:00:00Z"
    am.respond_claim("usr:dana", c_jo, "columns refreshed today")
    clock.value = "2026-02-05T00:00:00Z"
    am.withdraw_claim("usr:di", c_di)

    clock.value = "2026-02-15T00:00:00Z"
    am.revise_category("usr:dana", d1, "audio")

    clock.value = "2026-03-01T00:00:00Z"
    p_ed = am.purchase_api("usr:ed", d1, "BUY-CKM-7")["purchase_id"]
    clock.value = "2026-03-02T00:00:00Z"
    c_ed = am.open_claim("usr:ed", p_ed,
                         "audio stream drops")["claim_id"]
    clock.value = "2026-03-03T00:00:00Z"
    c_fa = am.open_claim("usr:fa", p_fa,
                         "quota wrong")["claim_id"]
    clock.value = "2026-03-10T00:00:00Z"
    am.respond_claim("usr:dana", c_fa, "quota corrected")

    # A refund with NO claim: must never appear on this face.
    clock.value = "2026-03-20T00:00:00Z"
    am.refund_api("usr:bo", p_bo, "changed my mind")
    # The January claim's refund lands in April: the claim must stay in
    # January and April must not become a row.
    clock.value = "2026-04-10T00:00:00Z"
    am.refund_api("usr:cy", p_cy, "claim settled by refund")

    return {"t1": t1, "d1": d1, "g1": g1, "u1": u1,
            "c_cy": c_cy, "c_jo": c_jo, "c_di": c_di, "c_hi": c_hi,
            "c_ed": c_ed, "c_fa": c_fa}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-categoryclaimmonths-")
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

    # -- AC-CKM1 the contract and the honest empty world ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-ckm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_category_claim_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_category_claim_months()
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    cells_ok = all(set(entry.keys()) == CELL_KEYS
                   for row in env["months"]
                   for entry in row["categories"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and len(env) == 18
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok and cells_ok
           and env["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["claim_count"] == 0
           and empty["open_count"] == 0
           and empty["answered_count"] == 0
           and empty["withdrawn_count"] == 0
           and empty["refunded_count"] == 0
           and empty["claim_amount"] == 0
           and empty["refunded_amount"] == 0
           and empty["refund_rate"] is None
           and empty["category_count"] == 0
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_claim_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_claim_count"] is None)
    record("AC-CKM1", ok1,
           "env_keys=%d exact=%r rows=%r cells=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              cells_ok, (empty["month_count"], empty["refund_rate"],
                         empty["months"], empty["peak_month"])))

    # -- AC-CKM2 booking law: month AND bucket at the open instant --
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    grid = [row["month"] for row in env["months"]]
    ok2 = (grid == ["2026-01", "2026-02", "2026-03"]
           and jan["claim_count"] == 4
           and cell(jan, "data")["claim_count"] == 2
           and cell(jan, "tools")["claim_count"] == 1
           and cell(jan, None)["claim_count"] == 1
           and "audio" not in [e["category"]
                               for e in jan["categories"]]
           and mar["claim_count"] == 2
           and cell(mar, "audio")["claim_count"] == 1
           and cell(mar, "tools")["claim_count"] == 1
           and "data" not in [e["category"]
                              for e in mar["categories"]]
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-03"
           and env["claim_count"] == 6
           and env["category_count"] == 4)
    record("AC-CKM2", ok2,
           "grid=%r jan=%r mar=%r totals=%r"
           % (grid, [(c["category"], c["claim_count"])
                     for c in jan["categories"]],
              [(c["category"], c["claim_count"])
               for c in mar["categories"]],
              (env["claim_count"], env["category_count"])))

    # -- AC-CKM3 status seam and the claim-side money law -----------
    ok3 = (jan["open_count"] == 1
           and jan["answered_count"] == 1
           and jan["withdrawn_count"] == 1
           and jan["refunded_count"] == 1
           and jan["claim_amount"] == 40
           and jan["refunded_amount"] == 10
           and cell(jan, "tools")["refunded_count"] == 1
           and cell(jan, "tools")["answered_count"] == 0
           and cell(jan, "tools")["refund_rate"] == 1.0
           and cell(jan, "data")["answered_count"] == 1
           and cell(jan, "data")["withdrawn_count"] == 1
           and cell(jan, "data")["open_count"] == 0
           and cell(jan, "data")["refund_rate"] == 0.0
           and cell(jan, None)["open_count"] == 1
           and cell(jan, None)["avg_claim_amount"] == 10.0
           and mar["open_count"] == 1
           and mar["answered_count"] == 1
           and mar["claim_amount"] == 20
           and env["open_count"] == 2
           and env["answered_count"] == 2
           and env["withdrawn_count"] == 1
           and env["refunded_count"] == 1
           and env["claim_amount"] == 60
           and env["refunded_amount"] == 10
           and env["refund_rate"] == round(1 / 6.0, 4))
    record("AC-CKM3", ok3,
           "jan=%r jan_tools=%r totals=%r rate=%r"
           % ((jan["open_count"], jan["answered_count"],
               jan["withdrawn_count"], jan["refunded_count"],
               jan["claim_amount"], jan["refunded_amount"]),
              (cell(jan, "tools")["refunded_count"],
               cell(jan, "tools")["refund_rate"]),
              (env["claim_count"], env["open_count"],
               env["answered_count"], env["withdrawn_count"],
               env["refunded_count"]), env["refund_rate"]))

    # -- AC-CKM4 contiguous grid, honest zero month, accumulators ---
    feb = month_row(env, "2026-02")
    ok4 = (env["month_count"] == len(env["months"]) == 3
           and env["active_month_count"] == 2
           and feb["claim_count"] == 0
           and feb["open_count"] == 0
           and feb["refunded_count"] == 0
           and feb["claim_amount"] == 0
           and feb["refunded_amount"] == 0
           and feb["refund_rate"] is None
           and feb["category_count"] == 0
           and feb["categories"] == []
           and feb["running_claim"] == jan["running_claim"] == 4
           and [row["running_claim"] for row in env["months"]]
           == [4, 4, 6]
           and env["months"][-1]["running_claim"]
           == env["claim_count"] == 6
           and env["latest_month_claim_count"] == 2
           and all(sum(entry["claim_count"]
                       for entry in row["categories"])
                   == row["claim_count"] for row in env["months"]))
    record("AC-CKM4", ok4,
           "months=%d active=%d feb=%r running=%r"
           % (env["month_count"], env["active_month_count"],
              (feb["claim_count"], feb["refund_rate"]),
              [row["running_claim"] for row in env["months"]]))

    # -- AC-CKM5 bucket ordering, per-cell running, flag scope ------
    jan_order = [entry["category"] for entry in jan["categories"]]
    mar_order = [entry["category"] for entry in mar["categories"]]
    narrow = am.api_category_claim_months(
        include_uncategorized=False)
    n_jan = month_row(narrow, "2026-01")
    n_mar = month_row(narrow, "2026-03")
    n_order = [entry["category"] for entry in n_jan["categories"]]
    ok5 = (jan_order == ["data", "tools", None]
           and mar_order == ["audio", "tools"]
           and n_order == ["data", "tools"]
           and jan["category_count"] == 3
           and mar["category_count"] == 2
           and cell(jan, "data")["running_claim"] == 2
           and cell(jan, "tools")["running_claim"] == 1
           and cell(jan, None)["running_claim"] == 1
           and cell(mar, "audio")["running_claim"] == 1
           and cell(mar, "tools")["running_claim"] == 2
           and len(narrow["months"]) == 3
           and n_jan["claim_count"] == 3
           and n_jan["category_count"] == 2
           and n_mar["claim_count"] == 2
           and narrow["claim_count"] == 5
           and narrow["open_count"] == 1
           and narrow["answered_count"] == 2
           and narrow["withdrawn_count"] == 1
           and narrow["refunded_count"] == 1
           and narrow["claim_amount"] == 50
           and narrow["refunded_amount"] == 10
           and narrow["refund_rate"] == round(1 / 5.0, 4)
           and narrow["category_count"] == 3
           and narrow["peak_month"] == "2026-01"
           and narrow["peak_claim_count"] == 3)
    record("AC-CKM5", ok5,
           "order=%r/%r narrow=%r narrow_totals=%r"
           % (jan_order, mar_order, n_order,
              (narrow["claim_count"], narrow["refunded_count"],
               narrow["category_count"], narrow["peak_claim_count"])))

    # -- AC-CKM6 fail-closed shape gate before any read -------------
    digests_pre = market_digests(am)
    tx_pre = ledger_tx_ids(led)
    bad_codes = []
    for form in (None, "yes", 1, 0, [], {}):
        try:
            am.api_category_claim_months(include_uncategorized=form)
            bad_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            bad_codes.append(exc.code)
    digests_post = market_digests(am)
    tx_post = ledger_tx_ids(led)
    ok6 = (bad_codes == [A.E_AM_BAD_ARGS] * 6
           and digests_pre == digests_post
           and tx_pre == tx_post
           and am.api_category_claim_months(
               include_uncategorized=True) == env
           and am.api_category_claim_months(
               include_uncategorized=False) == narrow)
    record("AC-CKM6", ok6,
           "codes=%r digests_same=%r tx_same=%r"
           % (bad_codes, digests_pre == digests_post, tx_pre == tx_post))

    # -- AC-CKM7 cross-face identity with api_market_claim_months ---
    market = am.api_market_claim_months()
    nonzero = [row["month"] for row in env["months"]
               if row["claim_count"] > 0]
    ok7 = (market["claim_count"] == env["claim_count"] == 6
           and market["open_count"] == env["open_count"] == 2
           and market["answered_count"] == env["answered_count"] == 2
           and market["withdrawn_count"] == env["withdrawn_count"] == 1
           and market["refunded_count"] == env["refunded_count"] == 1
           and market["claim_amount"] == env["claim_amount"] == 60
           and market["refunded_amount"] == env["refunded_amount"] == 10
           and nonzero == ["2026-01", "2026-03"]
           and [row["month"] for row in market["months"]]
           == ["2026-01", "2026-03"]
           and sum(row["claim_count"] for row in env["months"]
                   if row["month"] == "2026-01") == 4
           and narrow["claim_count"] == env["claim_count"] - 1)
    record("AC-CKM7", ok7,
           "market=%r self=%r nonzero=%r"
           % ((market["claim_count"], market["open_count"],
               market["answered_count"], market["withdrawn_count"],
               market["refunded_count"]),
              (env["claim_count"], env["open_count"],
               env["answered_count"], env["withdrawn_count"],
               env["refunded_count"]), nonzero))

    # -- AC-CKM8 conservation, peak, pure read ---------------------
    sum_c = sum(row["claim_count"] for row in env["months"])
    sum_o = sum(row["open_count"] for row in env["months"])
    sum_ref = sum(row["refunded_count"] for row in env["months"])
    cells_c = sum(entry["claim_count"]
                  for row in env["months"]
                  for entry in row["categories"])
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(env)
    call_b = dumps(am.api_category_claim_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok8 = (sum_c == env["claim_count"] == cells_c == 6
           and sum_o == env["open_count"] == 2
           and sum_ref == env["refunded_count"] == 1
           and (env["open_count"] + env["answered_count"]
                + env["withdrawn_count"] + env["refunded_count"])
           == env["claim_count"]
           and all(row["open_count"] + row["answered_count"]
                   + row["withdrawn_count"] + row["refunded_count"]
                   == row["claim_count"] for row in env["months"])
           and all((row["refund_rate"] is None
                    if row["claim_count"] == 0
                    else row["refund_rate"] == round(
                        row["refunded_count"]
                        / float(row["claim_count"]), 4))
                   for row in env["months"])
           and env["peak_month"] == "2026-01"
           and env["peak_claim_count"] == 4
           and call_a == call_b
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-CKM8", ok8,
           "sums=%r cells=%r peak=%r pure=%r"
           % ((sum_c, sum_o, sum_ref), cells_c,
              (env["peak_month"], env["peak_claim_count"]),
              (digests_before == digests_after, tx_before == tx_after)))

    # -- restarts, wiring and hygiene (folded into the AC-CKM8 run)
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_category_claim_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_category_claim_months())
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    print("RESTART_SAME %r" % (call_a == call_c == call_d),
          flush=True)
    print("WIRED %r" % (
        b'"ledger-apimarket-categoryclaimmonths"' in recon
        and b"test_apimarket_categoryclaimmonths.py" in recon),
        flush=True)
    print("ASCII_LF %r" % (
        all(b < 128 for b in test_src) and b"\r\n" not in test_src
        and b"\r\n" not in src), flush=True)

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())