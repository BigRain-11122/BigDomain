"""Acceptance suite for the apimarket per-category monthly question
volume (BigDomain R2215; canon = the R2213 explore-queue seed row
claimed in R2215, criteria AC-CQM1..AC-CQM8 registered in that row
before the suite evidence).

Face under proof: APIMarketFace.api_category_question_months. The
question family answers one shelf (api_listing_qna), one seller
(api_seller_questions, api_seller_answers), one buyer
(api_buyer_questions) and the whole market on a month axis
(api_market_question_months), while the category faces answer supply,
price and watch flow by month. Nothing answered WHICH CATEGORIES
absorb pre-sale pressure month over month. This suite pins:

  - the seventeen-key envelope, the eleven-key month rows, the
    nine-key category cells, the disclaimer and the honest empty
    world;
  - the booking law: a question books in its own asked_utc month and
    in the category in force AT THAT INSTANT, so a later revision
    never moves a month already booked;
  - the answering law: the answered leg is credited to the ASKING
    month and the ASKING bucket, so a March answer raises January and
    leaves March untouched, and an answer landing after the last
    asking month never extends the grid;
  - the contiguous grid with an honest zero month whose answer_rate
    is None, the monotone running total and the per-category running
    cells;
  - conservation of counts, the answer-rate arithmetic and the
    participant asymmetry (per-month distinct against the lifetime
    distinct envelope);
  - the bucket ordering (category ascending, uncategorized last) and
    the include_uncategorized flag, which drops that bucket AND
    recomputes every aggregate, plus the fail-closed shape gate;
  - the peak law with the earlier-month tie-break and the honest None
    on an empty world;
  - cross-face identity against api_market_question_months and against
    api_seller_questions summed over every seller;
  - the pure-read law (frozen table digests, constant ledger_tx set),
    cross-instance byte identity over two full-stack restarts, wiring
    and ASCII/LF hygiene.

Usage: python test_apimarket_categoryquestionmonths.py
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
    "question_count", "answered_count", "unanswered_count",
    "answer_rate", "buyer_count", "seller_count", "listing_count",
    "category_count", "month_count", "active_month_count", "peak_month",
    "peak_question_count", "first_month", "last_month",
    "latest_month_question_count", "disclaimer", "months"}

ROW_KEYS = {
    "month", "question_count", "answered_count", "unanswered_count",
    "answer_rate", "category_count", "buyer_count", "seller_count",
    "listing_count", "running_question", "categories"}

CELL_KEYS = {
    "category", "question_count", "answered_count", "unanswered_count",
    "answer_rate", "buyer_count", "seller_count", "listing_count",
    "running_question"}

TABLES = ("apimarket_listings", "apimarket_purchases",
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

    JAN: bo asks on t1, cy asks on t1, jo asks on d1, di asks on g1
    (answered inside January), hi asks on u1 (the uncategorized
    bucket).
    FEB 15: dana re-files d1 from data to audio - a revision that must
    never move a January bucket already booked.
    MAR: ed asks on d1 (now audio), fa asks on t1 (tools); cy's JANUARY
    question is answered on March 20 (the cross-month leg, credited to
    January).
    APR: ed's MARCH question is answered, which is after the last
    asking month and must not extend the grid.

    Market scope: 7 questions, 3 answered, 4 unanswered, rate 0.4286,
    7 distinct buyers, 2 sellers, 4 listings, 4 buckets, grid JAN..MAR
    with FEB honestly zero, peak January with 5.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-CQM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-CQM-S",
                     "settlement")
    for dev in ("dana", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)
    for who in ("bo", "cy", "jo", "di", "hi", "ed", "fa"):
        led.ensure_account("usr:" + who, census_avatar_id=who)

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

    clock.value = "2026-01-08T00:00:00Z"
    am.ask_question("usr:bo", t1, "does the payload carry timestamps")
    clock.value = "2026-01-09T00:00:00Z"
    q_cy = am.ask_question("usr:cy", t1, "is there a rate limit")[
        "question_id"]
    clock.value = "2026-01-10T00:00:00Z"
    am.ask_question("usr:jo", d1, "which format is d1 shipped in")
    clock.value = "2026-01-11T00:00:00Z"
    q_di = am.ask_question("usr:di", g1, "does gina ship samples")[
        "question_id"]
    am.answer_question("usr:gina", q_di, "yes, ask for one")
    clock.value = "2026-01-12T00:00:00Z"
    am.ask_question("usr:hi", u1, "what is this shelf for")

    clock.value = "2026-02-15T00:00:00Z"
    am.revise_category("usr:dana", d1, "audio")

    clock.value = "2026-03-02T00:00:00Z"
    q_ed = am.ask_question("usr:ed", d1, "which feed powers d1")[
        "question_id"]
    clock.value = "2026-03-03T00:00:00Z"
    am.ask_question("usr:fa", t1, "can I dedupe by key")
    clock.value = "2026-03-20T00:00:00Z"
    am.answer_question("usr:dana", q_cy, "sixty calls per minute")

    clock.value = "2026-04-05T00:00:00Z"
    am.answer_question("usr:dana", q_ed, "an in-house settlement feed")

    return {"t1": t1, "d1": d1, "g1": g1, "u1": u1,
            "q_cy": q_cy, "q_di": q_di, "q_ed": q_ed}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-categoryquestionmonths-")
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

    # -- AC-CQM1 the contract and the honest empty world ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-cqm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_category_question_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_category_question_months()
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    cells_ok = all(set(entry.keys()) == CELL_KEYS
                   for row in env["months"]
                   for entry in row["categories"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok and cells_ok
           and env["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["question_count"] == 0
           and empty["answered_count"] == 0
           and empty["unanswered_count"] == 0
           and empty["answer_rate"] is None
           and empty["buyer_count"] == 0
           and empty["seller_count"] == 0
           and empty["listing_count"] == 0
           and empty["category_count"] == 0
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_question_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_question_count"] is None)
    record("AC-CQM1", ok1,
           "env_keys=%d exact=%r rows=%r cells=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              cells_ok, (empty["month_count"], empty["answer_rate"],
                         empty["months"], empty["peak_month"])))

    # -- AC-CQM2 booking law: month AND bucket at the ask instant ---
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    grid = [row["month"] for row in env["months"]]
    ok2 = (grid == ["2026-01", "2026-02", "2026-03"]
           and jan["question_count"] == 5
           and cell(jan, "data")["question_count"] == 2
           and cell(jan, "tools")["question_count"] == 2
           and cell(jan, None)["question_count"] == 1
           and mar["question_count"] == 2
           and cell(mar, "audio")["question_count"] == 1
           and cell(mar, "tools")["question_count"] == 1
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-03"
           and env["question_count"] == 7
           and env["category_count"] == 4)
    record("AC-CQM2", ok2,
           "grid=%r jan=%r mar=%r totals=%r cats=%r"
           % (grid, [(c["category"], c["question_count"])
                     for c in jan["categories"]],
              [(c["category"], c["question_count"])
               for c in mar["categories"]],
              (env["question_count"], env["category_count"]),
              env["category_count"]))

    # -- AC-CQM3 answering law credits the asking month and bucket --
    jan_data = cell(jan, "data")
    jan_tools = cell(jan, "tools")
    ok3 = (jan["answered_count"] == 2
           and jan["unanswered_count"] == 3
           and jan_tools["answered_count"] == 1
           and jan_data["answered_count"] == 1
           and cell(jan, None)["answered_count"] == 0
           and mar["answered_count"] == 1
           and mar["unanswered_count"] == 1
           and cell(mar, "audio")["answered_count"] == 1
           and cell(mar, "tools")["answered_count"] == 0
           and env["answered_count"] == 3
           and env["unanswered_count"] == 4
           and env["month_count"] == 3)
    record("AC-CQM3", ok3,
           "jan=%r jan_data=%r mar=%r totals=%r"
           % ((jan["question_count"], jan["answered_count"]),
              (jan_data["question_count"], jan_data["answered_count"]),
              (mar["question_count"], mar["answered_count"]),
              (env["question_count"], env["answered_count"])))

    # -- AC-CQM4 contiguous grid, honest zero month, accumulators ---
    feb = month_row(env, "2026-02")
    ok4 = (env["month_count"] == len(env["months"]) == 3
           and env["active_month_count"] == 2
           and feb["question_count"] == 0
           and feb["answered_count"] == 0
           and feb["unanswered_count"] == 0
           and feb["answer_rate"] is None
           and feb["category_count"] == 0
           and feb["categories"] == []
           and feb["buyer_count"] == 0
           and feb["seller_count"] == 0
           and feb["listing_count"] == 0
           and feb["running_question"] == jan["running_question"] == 5
           and [row["running_question"] for row in env["months"]]
           == [5, 5, 7]
           and env["months"][-1]["running_question"]
           == env["question_count"] == 7
           and env["latest_month_question_count"] == 2)
    record("AC-CQM4", ok4,
           "months=%d active=%d feb=%r running=%r"
           % (env["month_count"], env["active_month_count"],
              (feb["question_count"], feb["answer_rate"]),
              [row["running_question"] for row in env["months"]]))

    # -- AC-CQM5 bucket ordering, per-cell running, flag scope ------
    jan_order = [entry["category"] for entry in jan["categories"]]
    mar_order = [entry["category"] for entry in mar["categories"]]
    narrow = am.api_category_question_months(
        include_uncategorized=False)
    n_jan = month_row(narrow, "2026-01")
    n_mar = month_row(narrow, "2026-03")
    n_order = [entry["category"] for entry in n_jan["categories"]]
    ok5 = (jan_order == ["data", "tools", None]
           and mar_order == ["audio", "tools"]
           and n_order == ["data", "tools"]
           and jan["category_count"] == 3
           and mar["category_count"] == 2
           and cell(jan, "data")["running_question"] == 2
           and cell(jan, "tools")["running_question"] == 2
           and cell(jan, None)["running_question"] == 1
           and cell(mar, "audio")["running_question"] == 1
           and cell(mar, "tools")["running_question"] == 3
           and len(narrow["months"]) == 3
           and n_jan["question_count"] == 4
           and n_jan["answered_count"] == 2
           and n_jan["category_count"] == 2
           and n_mar["question_count"] == 2
           and narrow["question_count"] == 6
           and narrow["answered_count"] == 3
           and narrow["unanswered_count"] == 3
           and narrow["answer_rate"] == 0.5
           and narrow["buyer_count"] == 6
           and narrow["seller_count"] == 2
           and narrow["listing_count"] == 3
           and narrow["category_count"] == 3
           and narrow["peak_month"] == "2026-01"
           and narrow["peak_question_count"] == 4)
    record("AC-CQM5", ok5,
           "order=%r/%r narrow=%r narrow_totals=%r"
           % (jan_order, mar_order, n_order,
              (narrow["question_count"], narrow["answered_count"],
               narrow["category_count"], narrow["listing_count"])))

    # -- AC-CQM6 fail-closed shape gate before any read -------------
    digests_pre = market_digests(am)
    tx_pre = ledger_tx_ids(led)
    bad_codes = []
    for form in (None, "yes", 1, 0, [], {}):
        try:
            am.api_category_question_months(include_uncategorized=form)
            bad_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            bad_codes.append(exc.code)
    digests_post = market_digests(am)
    tx_post = ledger_tx_ids(led)
    ok6 = (bad_codes == [A.E_AM_BAD_ARGS] * 6
           and digests_pre == digests_post
           and tx_pre == tx_post
           and am.api_category_question_months(
               include_uncategorized=True) == env
           and am.api_category_question_months(
               include_uncategorized=False) == narrow)
    record("AC-CQM6", ok6,
           "codes=%r digests_same=%r tx_same=%r"
           % (bad_codes, digests_pre == digests_post, tx_pre == tx_post))

    # -- AC-CQM7 cross-face identity -------------------------------
    market = am.api_market_question_months()
    seller_total = 0
    seller_answered = 0
    for dev in ("dana", "gina"):
        hist = am.api_seller_questions("usr:" + dev)
        seller_total += hist["total_question_count"]
        seller_answered += hist["answered_count"]
    ok7 = (market["question_count"] == env["question_count"] == 7
           and market["answered_count"] == env["answered_count"] == 3
           and market["unanswered_count"] == env["unanswered_count"] == 4
           and market["answer_rate"] == env["answer_rate"] == 0.4286
           and [row["month"] for row in market["months"]] == grid
           and seller_total == 7
           and seller_answered == 3
           and am.api_seller_questions("usr:dana")[
               "total_question_count"] == 5
           and am.api_seller_questions("usr:gina")[
               "total_question_count"] == 2
           and narrow["question_count"] == env["question_count"] - 1)
    record("AC-CQM7", ok7,
           "market=%r sellers=%r dana/gina=%r"
           % ((market["question_count"], market["answered_count"]),
              (seller_total, seller_answered),
              (am.api_seller_questions("usr:dana")[
                  "total_question_count"],
               am.api_seller_questions("usr:gina")[
                   "total_question_count"])))

    # -- AC-CQM8 conservation, peak, asymmetry, pure read ----------
    sum_q = sum(row["question_count"] for row in env["months"])
    sum_a = sum(row["answered_count"] for row in env["months"])
    sum_u = sum(row["unanswered_count"] for row in env["months"])
    cells_q = sum(entry["question_count"]
                  for row in env["months"]
                  for entry in row["categories"])
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(env)
    call_b = dumps(am.api_category_question_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok8 = (sum_q == env["question_count"] == cells_q == 7
           and sum_a == env["answered_count"] == 3
           and sum_u == env["unanswered_count"] == 4
           and env["answer_rate"] == round(3 / 7.0, 4)
           and all(row["answered_count"] + row["unanswered_count"]
                   == row["question_count"] for row in env["months"])
           and all(sum(entry["question_count"]
                       for entry in row["categories"])
                   == row["question_count"] for row in env["months"])
           and all((row["answer_rate"] is None
                    if row["question_count"] == 0
                    else row["answer_rate"] == round(
                        row["answered_count"]
                        / float(row["question_count"]), 4))
                   for row in env["months"])
           and env["peak_month"] == "2026-01"
           and env["peak_question_count"] == 5
           and env["buyer_count"] == 7
           and env["seller_count"] == 2
           and env["listing_count"] == 4
           and env["buyer_count"] <= sum(row["buyer_count"]
                                         for row in env["months"])
           and env["seller_count"] <= sum(row["seller_count"]
                                          for row in env["months"])
           and env["listing_count"] <= sum(row["listing_count"]
                                           for row in env["months"])
           and call_a == call_b
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-CQM8", ok8,
           "sums=%r/%r rate=%r peak=%r parts=%r pure=%r"
           % ((sum_q, sum_a, sum_u), cells_q, env["answer_rate"],
              (env["peak_month"], env["peak_question_count"]),
              (env["buyer_count"], env["seller_count"],
               env["listing_count"]),
              (digests_before == digests_after, tx_before == tx_after)))

    # -- restarts, wiring and hygiene (folded into AC-CQM8 evidence)
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_category_question_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_category_question_months())
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    print("RESTART_SAME %r" % (call_a == call_c == call_d),
          flush=True)
    print("WIRED %r" % (
        b'"ledger-apimarket-categoryquestionmonths"' in recon
        and b"test_apimarket_categoryquestionmonths.py" in recon),
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