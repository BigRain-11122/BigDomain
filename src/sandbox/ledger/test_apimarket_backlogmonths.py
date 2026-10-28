"""Acceptance suite for the apimarket monthly question backlog (BigDomain
R2234; canon = the R2230 explore-queue seed row claimed in R2234,
criteria AC-MBM1..AC-MBM8 registered in that row BEFORE this code
existed).

Face under proof: APIMarketFace.api_market_backlog_months. The question
family shipped the monthly ARRIVALS (api_market_question_months) and a
seller's PRESENT debt (api_seller_inbox), so whether the whole market's
open question queue grew or shrank month over month had no reading.
This suite pins:

  - the eleven-key envelope, the seven-key month rows and the honest
    empty world;
  - the open-at-month-end law derived only from asked_utc and
    answered_utc, so an answer landing in a later month closes the debt
    in that month and never re-dates the asking month;
  - the contiguous union grid (asking or answering event) with an
    honest zero-event month that keeps the debt flat, and a month whose
    only event is an answer still showing the debt shrinking;
  - net-flow conservation per row and the honest None open_rate on a
    zero cumulative denominator;
  - the peak law with the earlier-month tie-break and the honest None
    on an empty world;
  - cross-face identity against api_market_question_months;
  - the no-argument contract (a supplied argument is a TypeError, not a
    silently ignored scope) and the pure-read law (frozen table
    digests, constant ledger_tx set);
  - cross-instance byte identity over two full-stack restarts, wiring
    and ASCII/LF hygiene.

Usage: python test_apimarket_backlogmonths.py
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
    "month_count", "first_month", "last_month", "asked_count",
    "answered_count", "open_count", "peak_month", "peak_open_count",
    "latest_month_open_count", "disclaimer", "months"}

ROW_KEYS = {
    "month", "asked_count", "answered_count", "net_change",
    "open_at_month_end", "cumulative_asked", "open_rate"}

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

    JAN: bo asks on t1, cy asks on t1, di asks on g1 (3 asked);
    di's own question is answered inside January (1 answered), so the
    debt at the January end is 2.
    FEB: no event at all - the honest zero-event month that keeps the
    debt flat at 2.
    MAR: ed asks on d1, fa asks on t1, gi asks on g1 (3 asked) while
    cy's JANUARY question is answered (1 answered): 2 + 3 - 1 = 4.
    APR: ed's MARCH question is answered and nothing is asked (0 asked,
    1 answered): 4 - 1 = 3, a month whose only event DISCHARGES debt
    and which exists only because the grid is the asking/answering
    union.

    Market: 6 asked, 3 answered, 3 open; grid JAN..APR; peak March with
    4 open (February's 2 ties January's 2 but March overtakes both).
    """

    led.mint_to_pool("pool:reserve", 40000, "SETTLE-MBM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-MBM-S",
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
    tmp = tempfile.mkdtemp(prefix="apimarket-backlogmonths-")
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

    # -- AC-MBM1 the contract and the honest empty world ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-mbm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_backlog_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_market_backlog_months()
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    empty_rows_ok = all(set(row.keys()) == ROW_KEYS
                        for row in empty["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok and empty_rows_ok
           and env["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["asked_count"] == 0
           and empty["answered_count"] == 0
           and empty["open_count"] == 0
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_open_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_open_count"] is None)
    record("AC-MBM1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              (empty["month_count"], empty["months"],
               empty["open_count"], empty["peak_month"])))

    # -- AC-MBM2 the open-at-month-end law --------------------------
    jan = month_row(env, "2026-01")
    feb = month_row(env, "2026-02")
    mar = month_row(env, "2026-03")
    apr = month_row(env, "2026-04")
    ok2 = (jan["asked_count"] == 3
           and jan["answered_count"] == 1
           and jan["open_at_month_end"] == 2
           and feb["open_at_month_end"] == 2
           and mar["asked_count"] == 3
           and mar["answered_count"] == 1
           and mar["open_at_month_end"] == 4
           and apr["asked_count"] == 0
           and apr["answered_count"] == 1
           and apr["open_at_month_end"] == 3
           and env["asked_count"] == 6
           and env["answered_count"] == 3
           and env["open_count"] == 3
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-04"
           and env["latest_month_open_count"] == 3)
    record("AC-MBM2", ok2,
           "jan=%r feb=%r mar=%r apr=%r totals=%r"
           % ((jan["asked_count"], jan["answered_count"],
               jan["open_at_month_end"]),
              (feb["asked_count"], feb["answered_count"],
               feb["open_at_month_end"]),
              (mar["asked_count"], mar["answered_count"],
               mar["open_at_month_end"]),
              (apr["asked_count"], apr["answered_count"],
               apr["open_at_month_end"]),
              (env["asked_count"], env["answered_count"],
               env["open_count"])))

    # -- AC-MBM3 union grid, honest zero month, monotone cumulative --
    grid = [row["month"] for row in env["months"]]
    cum = [row["cumulative_asked"] for row in env["months"]]
    ok3 = (grid == ["2026-01", "2026-02", "2026-03", "2026-04"]
           and env["month_count"] == len(env["months"]) == 4
           and feb["asked_count"] == 0
           and feb["answered_count"] == 0
           and feb["net_change"] == 0
           and cum == [3, 3, 6, 6]
           and cum == sorted(cum)
           and cum[-1] == env["asked_count"] == 6)
    record("AC-MBM3", ok3,
           "grid=%r months=%d feb=%r cumulative=%r"
           % (grid, env["month_count"],
              (feb["asked_count"], feb["answered_count"],
               feb["net_change"], feb["open_at_month_end"]), cum))

    # -- AC-MBM4 net-flow conservation and honest open_rate ---------
    deltas = []
    previous = 0
    for row in env["months"]:
        deltas.append(row["open_at_month_end"] - previous)
        previous = row["open_at_month_end"]
    net_ok = all(
        row["net_change"] == row["asked_count"] - row["answered_count"]
        for row in env["months"])
    rate_ok = all(
        (row["open_rate"] is None
         if row["cumulative_asked"] == 0
         else row["open_rate"] == round(
             row["open_at_month_end"]
             / float(row["cumulative_asked"]), 4))
        for row in env["months"])
    ok4 = (net_ok and rate_ok
           and [row["net_change"] for row in env["months"]] == [2, 0, 2, -1]
           and deltas == [row["net_change"] for row in env["months"]]
           and jan["open_rate"] == 0.6667
           and mar["open_rate"] == 0.6667
           and apr["open_rate"] == 0.5
           and sum(row["asked_count"] for row in env["months"])
           == env["asked_count"]
           and sum(row["answered_count"] for row in env["months"])
           == env["answered_count"]
           and env["open_count"] == (
               env["asked_count"] - env["answered_count"]))
    record("AC-MBM4", ok4,
           "net=%r deltas=%r rates=%r net_ok=%r rate_ok=%r"
           % ([row["net_change"] for row in env["months"]], deltas,
              (jan["open_rate"], mar["open_rate"], apr["open_rate"]),
              net_ok, rate_ok))

    # -- AC-MBM5 peak law with the earlier-month tie-break ----------
    ok5 = (env["peak_month"] == "2026-03"
           and env["peak_open_count"] == 4
           and jan["open_at_month_end"] == feb["open_at_month_end"] == 2
           and empty["peak_month"] is None
           and empty["peak_open_count"] is None)
    record("AC-MBM5", ok5,
           "peak=%r jan_feb_tie=%r empty=%r"
           % ((env["peak_month"], env["peak_open_count"]),
              (jan["open_at_month_end"], feb["open_at_month_end"]),
              (empty["peak_month"], empty["peak_open_count"])))

    # -- AC-MBM6 identity against the arrival face ------------------
    arrivals = am.api_market_question_months()
    ok6 = (arrivals["question_count"] == env["asked_count"] == 6
           and arrivals["answered_count"] == env["answered_count"] == 3
           and arrivals["unanswered_count"] == env["open_count"] == 3
           and [row["month"] for row in arrivals["months"]]
           == ["2026-01", "2026-02", "2026-03"]
           and arrivals["last_month"] == "2026-03"
           and env["last_month"] == "2026-04")
    record("AC-MBM6", ok6,
           "arrivals=%r env=%r arrival_grid=%r"
           % ((arrivals["question_count"], arrivals["answered_count"],
               arrivals["unanswered_count"]),
              (env["asked_count"], env["answered_count"],
               env["open_count"]),
              [row["month"] for row in arrivals["months"]]))

    # -- AC-MBM7 no-argument contract and the pure read -------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    raised = 0
    for form in (None, "usr:dana", "", 0):
        try:
            am.api_market_backlog_months(form)
        except TypeError:
            raised += 1
    call_a = dumps(am.api_market_backlog_months())
    call_b = dumps(am.api_market_backlog_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (raised == 4
           and call_a == call_b == dumps(env)
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-MBM7", ok7,
           "typeerror=%d/4 deterministic=%r digests_same=%r"
           " tx_same=%r"
           % (raised, call_a == call_b,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-MBM8 restarts, wiring and hygiene ----------------------
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_market_backlog_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_market_backlog_months())
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (call_a == call_c == call_d == dumps(env)
           and b'"ledger-apimarket-backlogmonths"' in recon
           and b"test_apimarket_backlogmonths.py" in recon
           and b"def api_market_backlog_months" in src
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-MBM8", ok8,
           "bytes_same=%r wired=%r ascii=%r crlf_clean=%r"
           % (call_a == call_d,
              b'"ledger-apimarket-backlogmonths"' in recon,
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