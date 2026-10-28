"""Acceptance suite for the apimarket monthly question volume (BigDomain
R2205; canon = the R2202 explore-queue seed row claimed in R2205,
criteria AC-MQM1..AC-MQM8 registered in that row BEFORE this code
existed).

Face under proof: APIMarketFace.api_market_question_months. The
question family answers one shelf (api_listing_qna), one seller
(api_seller_questions, api_seller_answers) and one buyer
(api_buyer_questions), so the market carried a live queue but no
monthly view of how much pre-sale pressure landed. This suite pins:

  - the sixteen-key envelope, the nine-key month rows and the honest
    empty world;
  - the booking law: a question books in its own asked_utc month while
    the ANSWERING leg is credited to the asking month, so a March
    answer raises the January row and leaves the March row alone, and
    an answer landing after the last asking month never extends the
    grid;
  - the contiguous grid with an honest zero month whose answer_rate is
    None rather than a fabricated zero, plus the running accumulator;
  - conservation of counts, the answer-rate arithmetic and the
    participant asymmetry (per-month distinct against the lifetime
    distinct envelope);
  - the peak law with the earlier-month tie-break and the honest None
    on an empty world;
  - cross-face identity against api_seller_questions summed over every
    seller and against api_buyer_questions summed over every buyer;
  - the no-argument contract (a supplied argument is a TypeError, not a
    silently ignored scope) and the pure-read law (frozen table
    digests, constant ledger_tx set);
  - cross-instance byte identity over two full-stack restarts, wiring
    and ASCII/LF hygiene.

Usage: python test_apimarket_questionmonths.py
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
    "month_count", "active_month_count", "peak_month",
    "peak_question_count", "first_month", "last_month",
    "latest_month_question_count", "disclaimer", "months"}

ROW_KEYS = {
    "month", "question_count", "answered_count", "unanswered_count",
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


def seed_world(led, dk, am, clock):
    """Two sellers. dana owns t1 and d1, gina owns g1.

    JAN: bo asks on t1, cy asks on t1, di asks on g1 (3 questions);
    di's own question is answered inside January.
    FEB: no question at all (the honest zero row of the grid).
    MAR: ed asks on d1, fa asks on t1, gi asks on g1 (3 questions);
    cy's JANUARY question is answered in March (the cross-month leg).
    APR: ed's MARCH question is answered in April, which is after the
    last asking month and must not extend the grid.

    Market: 6 questions, 3 answered, 3 unanswered, rate 0.5, 6
    distinct buyers, 2 sellers, 3 listings, grid JAN..MAR with FEB
    honestly zero, peak January with 3 (earlier tie-break against
    March 3), January carrying 2 answered (di + the later cy answer).
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-MQM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-MQM-S",
                     "settlement")
    for dev in ("dana", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)
    for who in ("bo", "cy", "di", "ed", "fa", "gi"):
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

    clock.value = "2026-01-08T00:00:00Z"
    am.ask_question("usr:bo", t1, "does the payload carry timestamps")
    clock.value = "2026-01-09T00:00:00Z"
    q_cy = am.ask_question("usr:cy", t1, "is there a rate limit")[
        "question_id"]
    clock.value = "2026-01-10T00:00:00Z"
    q_di = am.ask_question("usr:di", g1, "does gina ship samples")[
        "question_id"]
    clock.value = "2026-01-11T00:00:00Z"
    am.answer_question("usr:gina", q_di, "yes, ask for one")

    clock.value = "2026-03-02T00:00:00Z"
    q_ed = am.ask_question("usr:ed", d1, "which feed powers d1")[
        "question_id"]
    clock.value = "2026-03-03T00:00:00Z"
    am.ask_question("usr:fa", t1, "can I dedupe by key")
    clock.value = "2026-03-04T00:00:00Z"
    am.ask_question("usr:gi", g1, "is there a sandbox tier")
    clock.value = "2026-03-20T00:00:00Z"
    am.answer_question("usr:dana", q_cy, "sixty calls per minute")

    clock.value = "2026-04-05T00:00:00Z"
    am.answer_question("usr:dana", q_ed, "an in-house settlement feed")

    return {"t1": t1, "d1": d1, "g1": g1,
            "q_cy": q_cy, "q_di": q_di, "q_ed": q_ed}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-questionmonths-")
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

    # -- AC-MQM1 the contract and the honest empty world ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-mqm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_question_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_market_question_months()
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
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
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_question_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_question_count"] is None)
    record("AC-MQM1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              (empty["month_count"], empty["answer_rate"],
               empty["months"], empty["peak_month"])))

    # -- AC-MQM2 booking law: the answer lands on the asking month --
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    grid = [row["month"] for row in env["months"]]
    ok2 = (grid == ["2026-01", "2026-02", "2026-03"]
           and jan["question_count"] == 3
           and jan["answered_count"] == 2
           and jan["unanswered_count"] == 1
           and mar["question_count"] == 3
           and mar["answered_count"] == 1
           and mar["unanswered_count"] == 2
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-03"
           and env["question_count"] == 6
           and env["answered_count"] == 3)
    record("AC-MQM2", ok2,
           "grid=%r jan=%r mar=%r totals=%r"
           % (grid, (jan["question_count"], jan["answered_count"]),
              (mar["question_count"], mar["answered_count"]),
              (env["question_count"], env["answered_count"])))

    # -- AC-MQM3 contiguous grid, honest zero month, accumulator ----
    feb = month_row(env, "2026-02")
    ok3 = (env["month_count"] == len(env["months"]) == 3
           and env["active_month_count"] == 2
           and feb["question_count"] == 0
           and feb["answered_count"] == 0
           and feb["unanswered_count"] == 0
           and feb["answer_rate"] is None
           and feb["buyer_count"] == 0
           and feb["seller_count"] == 0
           and feb["listing_count"] == 0
           and feb["running_question"] == jan["running_question"] == 3
           and [row["running_question"] for row in env["months"]]
           == [3, 3, 6]
           and env["months"][-1]["running_question"]
           == env["question_count"] == 6
           and env["latest_month_question_count"] == 3)
    record("AC-MQM3", ok3,
           "months=%d active=%d feb=%r running=%r"
           % (env["month_count"], env["active_month_count"],
              (feb["question_count"], feb["answer_rate"]),
              [row["running_question"] for row in env["months"]]))

    # -- AC-MQM4 conservation, answer rate, participants ------------
    sum_q = sum(row["question_count"] for row in env["months"])
    sum_a = sum(row["answered_count"] for row in env["months"])
    sum_u = sum(row["unanswered_count"] for row in env["months"])
    ok4 = (sum_q == env["question_count"] == 6
           and sum_a == env["answered_count"] == 3
           and sum_u == env["unanswered_count"] == 3
           and env["answer_rate"] == 0.5
           and env["answer_rate"] == round(
               env["answered_count"] / float(env["question_count"]), 4)
           and all(row["answered_count"] + row["unanswered_count"]
                   == row["question_count"] for row in env["months"])
           and all(
               (row["answer_rate"] is None
                if row["question_count"] == 0
                else row["answer_rate"] == round(
                    row["answered_count"] / float(row["question_count"]),
                    4))
               for row in env["months"])
           and jan["answer_rate"] == 0.6667
           and mar["answer_rate"] == 0.3333
           and env["buyer_count"] == 6
           and env["seller_count"] == 2
           and env["listing_count"] == 3
           and jan["buyer_count"] == 3
           and jan["seller_count"] == 2
           and jan["listing_count"] == 2
           and mar["buyer_count"] == 3
           and mar["seller_count"] == 2
           and mar["listing_count"] == 3
           and env["buyer_count"] <= sum(row["buyer_count"]
                                         for row in env["months"])
           and env["seller_count"] <= sum(row["seller_count"]
                                          for row in env["months"])
           and env["listing_count"] <= sum(row["listing_count"]
                                           for row in env["months"]))
    record("AC-MQM4", ok4,
           "sums=%r rate=%r participants=%r jan=%r mar=%r"
           % ((sum_q, sum_a, sum_u), env["answer_rate"],
              (env["buyer_count"], env["seller_count"],
               env["listing_count"]),
              (jan["buyer_count"], jan["seller_count"],
               jan["listing_count"]),
              (mar["buyer_count"], mar["seller_count"],
               mar["listing_count"])))

    # -- AC-MQM5 peak law with the earlier-month tie-break ----------
    ok5 = (env["peak_month"] == "2026-01"
           and env["peak_question_count"] == 3
           and empty["peak_month"] is None
           and empty["peak_question_count"] is None
           and month_row(env, "2026-02")["question_count"]
           < env["peak_question_count"])
    record("AC-MQM5", ok5,
           "peak=%r empty=%r"
           % ((env["peak_month"], env["peak_question_count"]),
              (empty["peak_month"], empty["peak_question_count"])))

    # -- AC-MQM6 cross-face identity over sellers and buyers --------
    dana = am.api_seller_questions("usr:dana")
    gina = am.api_seller_questions("usr:gina")
    buyer_total = 0
    buyer_answered = 0
    for who in ("bo", "cy", "di", "ed", "fa", "gi"):
        hist = am.api_buyer_questions("usr:" + who)
        buyer_total += hist["question_count"]
        buyer_answered += hist["answered_count"]
    ok6 = (dana["total_question_count"] == 4
           and dana["answered_count"] == 2
           and dana["unanswered_count"] == 2
           and gina["total_question_count"] == 2
           and gina["answered_count"] == 1
           and gina["unanswered_count"] == 1
           and dana["total_question_count"]
           + gina["total_question_count"] == env["question_count"]
           and dana["answered_count"]
           + gina["answered_count"] == env["answered_count"]
           and buyer_total == env["question_count"]
           and buyer_answered == env["answered_count"])
    record("AC-MQM6", ok6,
           "dana=%r gina=%r buyer=%r env=%r"
           % ((dana["total_question_count"], dana["answered_count"]),
              (gina["total_question_count"], gina["answered_count"]),
              (buyer_total, buyer_answered),
              (env["question_count"], env["answered_count"])))

    # -- AC-MQM7 no-argument contract and the pure read -------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    raised = 0
    for form in (None, "usr:dana", "", 0):
        try:
            am.api_market_question_months(form)
        except TypeError:
            raised += 1
    call_a = dumps(am.api_market_question_months())
    call_b = dumps(am.api_market_question_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (raised == 4
           and call_a == call_b == dumps(env)
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-MQM7", ok7,
           "typeerror=%d/4 deterministic=%r digests_same=%r"
           " tx_same=%r"
           % (raised, call_a == call_b,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-MQM8 restarts, wiring and hygiene ----------------------
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_market_question_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_market_question_months())
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (call_a == call_c == call_d == dumps(env)
           and b'"ledger-apimarket-questionmonths"' in recon
           and b"test_apimarket_questionmonths.py" in recon
           and b"def api_market_question_months" in src
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-MQM8", ok8,
           "bytes_same=%r wired=%r ascii=%r crlf_clean=%r"
           % (call_a == call_d,
              b'"ledger-apimarket-questionmonths"' in recon,
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