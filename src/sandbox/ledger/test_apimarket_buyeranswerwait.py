"""Acceptance suite for the buyer monthly answer wait face
(BigDomain R2232; canon = the R2230 explore-queue seed 2/6 row,
criteria AC-BAW1..AC-BAW8 registered in that row BEFORE this code
existed).

Face under proof: APIMarketFace.api_buyer_answer_wait.
api_buyer_questions merges every question of one buyer into a lifetime
timeline and api_buyer_claims covers the after-sales side, but nothing
told a buyer how long it actually waited for answers month over month.
This suite pins:

  - the twenty-one-key envelope, the ten-key month rows and the honest
    empty world;
  - the booking law: an answer books in the month of its own
    answered_utc, never the month the question was asked, so a
    February question discharged in March leaves February an honest
    zero row;
  - the wait law measured asked_utc -> answered_utc with the integer
    floor mean, the row extremes and honest None latencies;
  - the backlog split (backlog_count + same_month_count ==
    answered_count) and the completed month grid with monotone running
    accumulators landing on the envelope total;
  - the peak law with the earlier-month tie-break and no peak on a
    zero month;
  - strict buyer isolation on the usr: account gate and the
    asked-side envelope against the answered-side row asymmetry;
  - cross-face identity against api_buyer_questions on the same world;
  - the pure-read law (frozen table digests, constant ledger_tx set)
    and cross-instance byte identity over two full-stack restarts,
    wiring and ASCII/LF hygiene.

Usage: python test_apimarket_buyeranswerwait.py
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
    "buyer_id", "scope", "question_count", "answered_count",
    "unanswered_count", "answer_rate", "seller_count", "listing_count",
    "backlog_answered_count", "month_count", "active_month_count",
    "peak_month", "peak_answered_count", "first_month", "last_month",
    "latest_month_answered_count", "fastest_seconds",
    "slowest_seconds", "mean_seconds", "disclaimer", "months"}

ROW_KEYS = {
    "month", "answered_count", "backlog_count", "same_month_count",
    "seller_count", "listing_count", "fastest_seconds",
    "slowest_seconds", "mean_seconds", "running_answered"}

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
    """Two sellers. dana owns t1 and d1; gina owns g1.

    Buyer bo: JAN 03 asks on t1 and dana answers the same day seven
    seconds after six; JAN 05 asks on d1 and dana answers JAN 20; JAN
    09 asks on t1 and is left open. FEB 10 asks on g1 and gina answers
    FEB 10 - no, answers on MAR 07, so February must stay an honest
    zero row even though a question was asked in it. MAR 05 asks on d1
    and dana answers three hours later; MAR 12 asks on d1 and is left
    open. Buyer cy asks once on d1 in JAN and is answered, so cy must
    never leak into bo's face.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-BAW-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-BAW-S",
                     "settlement")
    for dev in ("dana", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)
    for who in ("bo", "cy"):
        led.ensure_account("usr:" + who, census_avatar_id=who)

    clock.value = "2026-01-02T00:00:00Z"
    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    d1 = am.publish_api("usr:dana", "d1", "Dana Data API",
                        "dana data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    clock.value = "2026-01-03T00:00:00Z"
    q_jan_fast = am.ask_question("usr:bo", t1,
                                 "does the payload carry timestamps")[
        "question_id"]
    clock.value = "2026-01-03T06:00:07Z"
    am.answer_question("usr:dana", q_jan_fast,
                       "yes, every row is stamped")

    clock.value = "2026-01-04T00:00:00Z"
    q_cy = am.ask_question("usr:cy", d1, "is d1 mirrored nightly")[
        "question_id"]
    clock.value = "2026-01-04T01:00:00Z"
    am.answer_question("usr:dana", q_cy, "yes, at 01:00 UTC")

    clock.value = "2026-01-05T00:00:00Z"
    q_jan_slow = am.ask_question("usr:bo", d1,
                                 "which feed powers d1")["question_id"]
    clock.value = "2026-01-20T00:00:00Z"
    am.answer_question("usr:dana", q_jan_slow,
                       "an in-house settlement feed")

    clock.value = "2026-01-09T00:00:00Z"
    q_open_jan = am.ask_question("usr:bo", t1,
                                 "is there a rate limit")["question_id"]

    clock.value = "2026-02-10T00:00:00Z"
    q_feb = am.ask_question("usr:bo", g1,
                            "does gina ship samples")["question_id"]

    clock.value = "2026-03-05T00:00:00Z"
    q_mar = am.ask_question("usr:bo", d1,
                            "can d1 export parquet")["question_id"]
    clock.value = "2026-03-05T03:00:00Z"
    am.answer_question("usr:dana", q_mar, "parquet and csv")

    clock.value = "2026-03-07T00:00:00Z"
    am.answer_question("usr:gina", q_feb, "yes, ask for one")

    clock.value = "2026-03-12T00:00:00Z"
    q_open_mar = am.ask_question("usr:bo", d1,
                                 "is d1 still maintained")["question_id"]

    return {"t1": t1, "d1": d1, "g1": g1, "q_cy": q_cy,
            "q_open_jan": q_open_jan, "q_open_mar": q_open_mar}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-buyeranswerwait-")
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

    # -- AC-BAW1 the contract and the honest empty world ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-baw-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_answer_wait("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_buyer_answer_wait("usr:bo")
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and len(ENVELOPE_KEYS) == 21
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
           and len(ROW_KEYS) == 10
           and env["disclaimer"] == DISCLAIMER
           and env["scope"] == "buyer"
           and env["buyer_id"] == "usr:bo"
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["question_count"] == 0
           and empty["answered_count"] == 0
           and empty["unanswered_count"] == 0
           and empty["answer_rate"] is None
           and empty["seller_count"] == 0
           and empty["listing_count"] == 0
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["peak_month"] is None
           and empty["peak_answered_count"] is None
           and empty["fastest_seconds"] is None
           and empty["slowest_seconds"] is None
           and empty["mean_seconds"] is None
           and empty["latest_month_answered_count"] == 0)
    record("AC-BAW1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              (empty["month_count"], empty["months"],
               empty["mean_seconds"])))

    # -- AC-BAW2 booking law: the February question discharged in
    # March raises only the March row and leaves February zero ------
    jan = month_row(env, "2026-01")
    feb = month_row(env, "2026-02")
    mar = month_row(env, "2026-03")
    grid = [row["month"] for row in env["months"]]
    ok2 = (grid == ["2026-01", "2026-02", "2026-03"]
           and jan["answered_count"] == 2
           and feb["answered_count"] == 0
           and mar["answered_count"] == 2
           and env["question_count"] == 6
           and env["answered_count"] == 4
           and env["unanswered_count"] == 2
           and env["answer_rate"] == 0.6667
           and env["backlog_answered_count"] == 1)
    record("AC-BAW2", ok2,
           "grid=%r months=%r totals=%r"
           % (grid,
              [row["answered_count"] for row in env["months"]],
              (env["question_count"], env["answered_count"],
               env["unanswered_count"], env["answer_rate"])))

    # -- AC-BAW3 the wait law: asked -> answered seconds, row and
    # envelope extremes, the integer floor mean --------------------
    ok3 = (jan["fastest_seconds"] == 21607
           and jan["slowest_seconds"] == 1296000
           and jan["mean_seconds"] == 658803
           and mar["fastest_seconds"] == 10800
           and mar["slowest_seconds"] == 2160000
           and mar["mean_seconds"] == 1085400
           and env["fastest_seconds"] == 10800
           and env["slowest_seconds"] == 2160000
           and env["mean_seconds"] == 872101)
    record("AC-BAW3", ok3,
           "jan=%r mar=%r env=%r"
           % ((jan["fastest_seconds"], jan["slowest_seconds"],
               jan["mean_seconds"]),
              (mar["fastest_seconds"], mar["slowest_seconds"],
               mar["mean_seconds"]),
              (env["fastest_seconds"], env["slowest_seconds"],
               env["mean_seconds"])))

    # -- AC-BAW4 backlog split and the completed row grid -----------
    ok4 = (jan["backlog_count"] == 0
           and jan["same_month_count"] == 2
           and mar["backlog_count"] == 1
           and mar["same_month_count"] == 1
           and all(row["backlog_count"] + row["same_month_count"]
                   == row["answered_count"] for row in env["months"])
           and feb["backlog_count"] == 0
           and feb["same_month_count"] == 0
           and [row["running_answered"] for row in env["months"]]
           == [2, 2, 4]
           and env["months"][-1]["running_answered"]
           == env["answered_count"]
           and env["month_count"] == 3
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-03")
    record("AC-BAW4", ok4,
           "split=%r running=%r"
           % ([(row["backlog_count"], row["same_month_count"],
                row["answered_count"]) for row in env["months"]],
              [row["running_answered"] for row in env["months"]]))

    # -- AC-BAW5 peak with the earlier-month tie-break --------------
    ok5 = (env["active_month_count"] == 2
           and env["latest_month_answered_count"] == 2
           and env["peak_month"] == "2026-01"
           and env["peak_answered_count"] == 2
           and feb["answered_count"] == 0
           and feb["fastest_seconds"] is None
           and feb["slowest_seconds"] is None
           and feb["mean_seconds"] is None)
    record("AC-BAW5", ok5,
           "active=%d latest=%d peak=%r"
           % (env["active_month_count"],
              env["latest_month_answered_count"],
              (env["peak_month"], env["peak_answered_count"])))

    # -- AC-BAW6 strict buyer isolation ----------------------------
    cy = am.api_buyer_answer_wait("usr:cy")
    ok6 = (cy["question_count"] == 1
           and cy["answered_count"] == 1
           and cy["unanswered_count"] == 0
           and cy["month_count"] == 1
           and cy["months"][0]["month"] == "2026-01"
           and cy["months"][0]["answered_count"] == 1
           and cy["months"][0]["mean_seconds"] == 3600
           and cy["listing_count"] == 1
           and cy["seller_count"] == 1
           and cy["peak_month"] == "2026-01"
           and cy["buyer_id"] == "usr:cy"
           and env["buyer_id"] == "usr:bo"
           and env["question_count"] == 6
           and env["answered_count"] == 4)
    record("AC-BAW6", ok6,
           "cy=%r bo=%r"
           % ((cy["question_count"], cy["answered_count"],
               cy["month_count"], cy["listing_count"]),
              (env["question_count"], env["answered_count"],
               env["listing_count"])))

    # -- AC-BAW7 identity against api_buyer_questions -------------
    lifetime = am.api_buyer_questions("usr:bo")
    ok7 = (lifetime["question_count"] == env["question_count"] == 6
           and lifetime["answered_count"] == env["answered_count"] == 4
           and lifetime["unanswered_count"]
           == env["unanswered_count"] == 2
           and lifetime["listing_count"] == env["listing_count"] == 3
           and lifetime["oldest_open_utc"] == "2026-01-09T00:00:00Z"
           and env["seller_count"] == 2
           and sum(row["answered_count"] for row in env["months"])
           == env["answered_count"]
           and sum(row["seller_count"] for row in env["months"]) >= 2
           and jan["listing_count"] == 2
           and mar["listing_count"] == 2
           and jan["seller_count"] == 1
           and mar["seller_count"] == 2)
    record("AC-BAW7", ok7,
           "lifetime=%r env=%r rows=%r"
           % ((lifetime["question_count"], lifetime["answered_count"],
               lifetime["unanswered_count"],
               lifetime["listing_count"]),
              (env["question_count"], env["answered_count"],
               env["listing_count"], env["seller_count"]),
              [(row["seller_count"], row["listing_count"])
               for row in env["months"]]))

    # -- AC-BAW8 gate, pure read, restart identity and wiring ------
    codes = [error_code(am.api_buyer_answer_wait, form)
             for form in BAD_ACCOUNTS]
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_buyer_answer_wait("usr:bo"))
    call_b = dumps(am.api_buyer_answer_wait("usr:bo"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_buyer_answer_wait("usr:bo"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_buyer_answer_wait("usr:bo"))
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and call_a == call_b == call_c == call_d == dumps(env)
           and digests_before == digests_after
           and tx_before == tx_after
           and (b'"ledger-apimarket-buyeranswerwait"' in recon
                or b"ledger-apimarket-buyeranswerwait"
                in recon)
           and b"test_apimarket_buyeranswerwait.py" in recon
           and b"def api_buyer_answer_wait" in src
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-BAW8", ok8,
           "gate=%r bytes_same=%r digests_same=%r tx_same=%r"
           " wired=%r ascii=%r crlf_clean=%r"
           % (codes, call_a == call_d,
              digests_before == digests_after, tx_before == tx_after,
              b"test_apimarket_buyeranswerwait.py" in recon,
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