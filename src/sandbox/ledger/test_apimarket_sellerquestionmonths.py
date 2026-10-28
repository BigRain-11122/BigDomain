"""Acceptance suite for the seller monthly question pressure face
(BigDomain R2231; canon = the R2230 explore-queue seed 1/6 row,
criteria AC-SQM1..AC-SQM8 registered in that row BEFORE this code
existed).

Face under proof: APIMarketFace.api_seller_question_months.
The question family answers the whole market by month
(api_market_question_months), one category by month
(api_category_question_months) and one seller's own answers by month
(api_seller_answer_months), while api_seller_questions carries a single
lifetime inbox. So a seller drowning in pre-sale questions last month
and a seller nobody asked read identically. This suite pins:

  - the eighteen-key envelope, the nine-key month rows and the honest
    empty world;
  - the booking law: a question books in the month of its own
    asked_utc and the ANSWERING leg is credited to the ASKING month,
    never to the month the answer landed in;
  - the contiguous grid with an honest zero row whose answer_rate is
    None, and both monotone running accumulators landing on the
    envelope totals;
  - event-derived participants per month against lifetime distinct
    envelope counts;
  - the peak law with the earlier-month tie-break and no peak on a
    zero month;
  - strict seller isolation on the usr: account gate and the
    owned-listing envelope against the asked-listing row asymmetry;
  - cross-face identity against a raw join over the question table
    and the open-row count;
  - the pure-read law (frozen table digests, constant ledger_tx set)
    and cross-instance byte identity over two full-stack restarts,
    wiring and ASCII/LF hygiene.

Usage: python test_apimarket_sellerquestionmonths.py
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
    "dev_account", "scope", "question_count", "answered_count",
    "unanswered_count", "answer_rate", "buyer_count", "listing_count",
    "market_question_count", "month_count", "active_month_count",
    "peak_month", "peak_question_count", "first_month", "last_month",
    "latest_month_question_count", "disclaimer", "months"}

ROW_KEYS = {
    "month", "question_count", "answered_count", "unanswered_count",
    "answer_rate", "buyer_count", "listing_count", "running_question",
    "running_answer"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_questions", "apimarket_answers",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_refunds", "apimarket_category_revisions")

BAD_ACCOUNTS = (None, "", "u", "usrX:dana", 123, False, [],
                {}, {"usr:x": 1})


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


def error_code(fn, *args):
    try:
        fn(*args)
    except A.ApiMarketError as exc:
        return exc.code
    return None


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
    """Two sellers. dana owns t1, d1 and d2; gina owns g1.

    JAN: bo asks on t1 and dana answers the same day (the same-month
    leg); cy asks on t1 and is left open; gi asks on gina's g1.
    FEB: no question and no answer at all (the honest zero row).
    MAR: dana answers cy's JANUARY question (its answer must be
    credited to the ASKING month), publishes nothing new, then ed asks
    on d1 and dana answers the same day; fay asks on d2 and is never
    answered; gina answers her January question too.

    dana therefore books 2 questions in January with 2 answered, an
    honest zero February, and 2 questions in March with only 1
    answered - so the tie for the peak (2 vs 2) must resolve to the
    earlier month. gina is isolated to one January question.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SQM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SQM-S",
                     "settlement")
    for dev in ("dana", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)
    for who in ("bo", "cy", "ed", "fay", "gi"):
        led.ensure_account("usr:" + who, census_avatar_id=who)

    clock.value = "2026-01-02T00:00:00Z"
    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    d1 = am.publish_api("usr:dana", "d1", "Dana Data API",
                        "dana data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    d2 = am.publish_api("usr:dana", "d2", "Dana Quiet API",
                        "a shelf nobody bought from", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    clock.value = "2026-01-03T00:00:00Z"
    q_bo = am.ask_question("usr:bo", t1,
                           "does the payload carry timestamps")[
        "question_id"]
    clock.value = "2026-01-03T06:00:00Z"
    am.answer_question("usr:dana", q_bo, "yes, every row is stamped")

    clock.value = "2026-01-09T00:00:00Z"
    q_cy = am.ask_question("usr:cy", t1, "is there a rate limit")[
        "question_id"]
    clock.value = "2026-01-12T00:00:00Z"
    q_gi = am.ask_question("usr:gi", g1, "does gina ship samples")[
        "question_id"]

    clock.value = "2026-03-02T00:00:00Z"
    am.answer_question("usr:dana", q_cy, "sixty calls per minute")
    clock.value = "2026-03-05T00:00:00Z"
    q_ed = am.ask_question("usr:ed", d1, "which feed powers d1")[
        "question_id"]
    clock.value = "2026-03-05T03:00:00Z"
    am.answer_question("usr:dana", q_ed, "an in-house settlement feed")
    clock.value = "2026-03-12T00:00:00Z"
    q_fay = am.ask_question("usr:fay", d2, "is d2 still maintained")[
        "question_id"]
    clock.value = "2026-03-20T00:00:00Z"
    am.answer_question("usr:gina", q_gi, "yes, ask for one")

    return {"t1": t1, "d1": d1, "d2": d2, "g1": g1,
            "q_bo": q_bo, "q_cy": q_cy, "q_gi": q_gi,
            "q_ed": q_ed, "q_fay": q_fay}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerquestionmonths-")
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

    # -- AC-SQM1 the contract and the honest empty world ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-sqm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_question_months("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_seller_question_months("usr:dana")
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and len(ENVELOPE_KEYS) == 18
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
           and len(ROW_KEYS) == 9
           and env["disclaimer"] == DISCLAIMER
           and env["scope"] == "seller"
           and env["dev_account"] == "usr:dana"
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["question_count"] == 0
           and empty["answered_count"] == 0
           and empty["unanswered_count"] == 0
           and empty["answer_rate"] is None
           and empty["buyer_count"] == 0
           and empty["listing_count"] == 0
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["peak_month"] is None
           and empty["peak_question_count"] is None
           and empty["latest_month_question_count"] == 0)
    record("AC-SQM1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              (empty["month_count"], empty["months"],
               empty["answer_rate"])))

    # -- AC-SQM2 booking law: the answering leg stays on the asking
    # month, so the March discharge of a January question raises
    # January and leaves the March row untouched by it ---------------
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    grid = [row["month"] for row in env["months"]]
    ok2 = (grid == ["2026-01", "2026-02", "2026-03"]
           and jan["question_count"] == 2
           and jan["answered_count"] == 2
           and jan["unanswered_count"] == 0
           and jan["answer_rate"] == 1.0
           and mar["question_count"] == 2
           and mar["answered_count"] == 1
           and mar["unanswered_count"] == 1
           and mar["answer_rate"] == 0.5
           and env["question_count"] == 4
           and env["answered_count"] == 3
           and env["unanswered_count"] == 1
           and env["answer_rate"] == 0.75)
    record("AC-SQM2", ok2,
           "grid=%r jan=%r mar=%r totals=%r"
           % (grid,
              (jan["question_count"], jan["answered_count"]),
              (mar["question_count"], mar["answered_count"]),
              (env["question_count"], env["answered_count"],
               env["answer_rate"])))

    # -- AC-SQM3 contiguous grid, honest zero row, accumulators -----
    feb = month_row(env, "2026-02")
    ok3 = (env["month_count"] == len(env["months"]) == 3
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-03"
           and feb["question_count"] == 0
           and feb["answered_count"] == 0
           and feb["unanswered_count"] == 0
           and feb["answer_rate"] is None
           and feb["buyer_count"] == 0
           and feb["listing_count"] == 0
           and [row["running_question"] for row in env["months"]]
           == [2, 2, 4]
           and [row["running_answer"] for row in env["months"]]
           == [2, 2, 3]
           and env["months"][-1]["running_question"]
           == env["question_count"]
           and env["months"][-1]["running_answer"]
           == env["answered_count"])
    record("AC-SQM3", ok3,
           "months=%d feb=%r running=%r"
           % (env["month_count"],
              (feb["question_count"], feb["answer_rate"]),
              ([row["running_question"] for row in env["months"]],
               [row["running_answer"] for row in env["months"]])))

    # -- AC-SQM4 participants, event-derived against lifetime ------
    ok4 = (jan["buyer_count"] == 2
           and jan["listing_count"] == 1
           and mar["buyer_count"] == 2
           and mar["listing_count"] == 2
           and env["buyer_count"] == 4
           and env["listing_count"] == 3
           and env["buyer_count"] <= sum(
               row["buyer_count"] for row in env["months"])
           and env["listing_count"] <= sum(
               row["listing_count"] for row in env["months"]) + 1)
    record("AC-SQM4", ok4,
           "jan=%r mar=%r envelope=%r"
           % ((jan["buyer_count"], jan["listing_count"]),
              (mar["buyer_count"], mar["listing_count"]),
              (env["buyer_count"], env["listing_count"])))

    # -- AC-SQM5 peak with the earlier-month tie-break --------------
    ok5 = (env["active_month_count"] == 2
           and env["latest_month_question_count"] == 2
           and env["peak_month"] == "2026-01"
           and env["peak_question_count"] == 2
           and env["month_count"] == 3)
    record("AC-SQM5", ok5,
           "active=%d latest=%d peak=%r"
           % (env["active_month_count"],
              env["latest_month_question_count"],
              (env["peak_month"], env["peak_question_count"])))

    # -- AC-SQM6 strict seller isolation ---------------------------
    gina = am.api_seller_question_months("usr:gina")
    ok6 = (gina["question_count"] == 1
           and gina["answered_count"] == 1
           and gina["unanswered_count"] == 0
           and gina["month_count"] == 1
           and gina["months"][0]["month"] == "2026-01"
           and gina["months"][0]["question_count"] == 1
           and gina["months"][0]["answered_count"] == 1
           and gina["buyer_count"] == 1
           and gina["listing_count"] == 1
           and gina["first_month"] == gina["last_month"] == "2026-01"
           and gina["peak_month"] == "2026-01"
           and label_mismatch(gina, env))
    record("AC-SQM6", ok6,
           "gina=%r dana=%r"
           % ((gina["question_count"], gina["answered_count"],
               gina["month_count"], gina["buyer_count"]),
              (env["question_count"], env["answered_count"],
               env["buyer_count"])))

    # -- AC-SQM7 identity against the raw join ---------------------
    conn = sqlite3.connect(am.db_path)
    raw_count = conn.execute(
        "SELECT COUNT(*) FROM apimarket_questions q"
        " JOIN apimarket_listings l ON l.listing_id = q.listing_id"
        " WHERE l.dev_account = 'usr:dana'").fetchone()[0]
    raw_open = conn.execute(
        "SELECT COUNT(*) FROM apimarket_questions q"
        " JOIN apimarket_listings l ON l.listing_id = q.listing_id"
        " LEFT JOIN apimarket_answers a"
        " ON a.question_id = q.question_id"
        " WHERE l.dev_account = 'usr:dana'"
        " AND a.answer_id IS NULL").fetchone()[0]
    market = conn.execute(
        "SELECT COUNT(*) FROM apimarket_questions").fetchone()[0]
    conn.close()
    ok7 = (raw_count == env["question_count"] == 4
           and raw_open == env["unanswered_count"] == 1
           and market == env["market_question_count"] == 5
           and env["answered_count"] + env["unanswered_count"]
           == env["question_count"]
           and sum(row["question_count"] for row in env["months"])
           == env["question_count"]
           and sum(row["answered_count"] for row in env["months"])
           == env["answered_count"])
    record("AC-SQM7", ok7,
           "raw_open_market=%r"
           % ((raw_count, raw_open, market,
               env["question_count"], env["unanswered_count"],
               env["market_question_count"]),))

    # -- AC-SQM8 gate, pure read, restart identity and wiring ------
    codes = [error_code(am.api_seller_question_months, form)
             for form in BAD_ACCOUNTS]
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_seller_question_months("usr:dana"))
    call_b = dumps(am.api_seller_question_months("usr:dana"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_seller_question_months("usr:dana"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_seller_question_months("usr:dana"))
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and call_a == call_b == call_c == call_d == dumps(env)
           and digests_before == digests_after
           and tx_before == tx_after
           and b'"ledger-apimarket-sellerquestionmonths"' in recon
           and b"test_apimarket_sellerquestionmonths.py" in recon
           and b"def api_seller_question_months" in src
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-SQM8", ok8,
           "gate=%r bytes_same=%r digests_same=%r tx_same=%r"
           " wired=%r ascii=%r crlf_clean=%r"
           % (codes, call_a == call_d,
              digests_before == digests_after, tx_before == tx_after,
              b'"ledger-apimarket-sellerquestionmonths"' in recon,
              all(b < 128 for b in test_src),
              b"\r\n" not in test_src))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


def label_mismatch(a, b):
    """The two scopes must never share an account label."""
    return (a["dev_account"] == "usr:gina"
            and b["dev_account"] == "usr:dana"
            and a["market_question_count"] == b["market_question_count"])


_CLOCK = Clock()

if __name__ == "__main__":
    sys.exit(main())