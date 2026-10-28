"""Acceptance suite for the seller monthly answer cadence (BigDomain
R2206; canon = the R2202 explore-queue seed 2/8 row claimed in R2206,
criteria AC-SAM1..AC-SAM8 registered in that row BEFORE this code
existed).

Face under proof: APIMarketFace.api_seller_answer_months.
api_seller_answers reports lifetime fastest / slowest / mean latency
and one answered count, so a seller who answered everything promptly
last quarter and went silent this month read exactly like one that
never answered. This suite pins:

  - the nineteen-key envelope, the ten-key month rows and the honest
    empty world;
  - the cadence law: an answer books in the month of its own
    answered_utc, never the asked month, so a March discharge of a
    January question raises only the March row and a silent month
    stays an honest zero row;
  - the latency law: response seconds always measured asked->answered
    across the month boundary, month stats over the answers booked in
    that month, the integer-floor mean, and None latencies on a zero
    month rather than a fabricated zero;
  - the backlog split (backlog_count + same_month_count ==
    answered_count per row, envelope backlog total);
  - the contiguous grid, the monotone running_answered accumulator
    and the peak law with the earlier-month tie-break;
  - strict seller isolation, the account gate and the owned-listing
    envelope against the answered-listing row asymmetry;
  - the pure-read law (frozen table digests, constant ledger_tx set)
    and cross-face identity against api_seller_answers;
  - cross-instance byte identity over two full-stack restarts,
    wiring and ASCII/LF hygiene.

Usage: python test_apimarket_sellermonths.py
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
    "dev_account", "scope", "answered_count", "backlog_answered_count",
    "buyer_count", "listing_count", "answered_listing_count",
    "month_count", "active_month_count", "peak_month",
    "peak_answered_count", "first_month", "last_month",
    "latest_month_answered_count", "fastest_seconds", "slowest_seconds",
    "mean_seconds", "disclaimer", "months"}

ROW_KEYS = {
    "month", "answered_count", "backlog_count", "same_month_count",
    "buyer_count", "listing_count", "fastest_seconds",
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
    """Two sellers. dana owns t1, d1 and the never-answered d2; gina
    owns g1.

    JAN: bo asks on t1 and dana answers the same day (the same-month
    leg); cy asks on t1; gi asks on gina's g1.
    FEB: no answer at all (the honest zero row of the grid).
    MAR: dana answers cy's JANUARY question (the backlog leg, asked
    month strictly earlier than the booked month), publishes d2 with
    no question, then answers ed's March question on d1 the same day;
    gina answers her January backlog too.

    dana therefore books 1 answer in January (21600s) and 2 in March
    (4492800s backlog + 10800s same-month) with an honest zero
    February; gina is isolated to one March backlog answer.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SAM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SAM-S",
                     "settlement")
    for dev in ("dana", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)
    for who in ("bo", "cy", "di", "ed", "gi"):
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

    clock.value = "2026-03-01T00:00:00Z"
    d2 = am.publish_api("usr:dana", "d2", "Dana Quiet API",
                        "a shelf nobody asked about", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    clock.value = "2026-03-02T00:00:00Z"
    am.answer_question("usr:dana", q_cy, "sixty calls per minute")
    clock.value = "2026-03-05T00:00:00Z"
    q_ed = am.ask_question("usr:ed", d1, "which feed powers d1")[
        "question_id"]
    clock.value = "2026-03-05T03:00:00Z"
    am.answer_question("usr:dana", q_ed, "an in-house settlement feed")
    clock.value = "2026-03-20T00:00:00Z"
    am.answer_question("usr:gina", q_gi, "yes, ask for one")

    return {"t1": t1, "d1": d1, "d2": d2, "g1": g1,
            "q_bo": q_bo, "q_cy": q_cy, "q_gi": q_gi, "q_ed": q_ed}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-sellermonths-")
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

    # -- AC-SAM1 the contract and the honest empty world ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-sam-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_answer_months("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_seller_answer_months("usr:dana")
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
           and env["disclaimer"] == DISCLAIMER
           and env["scope"] == "seller"
           and env["dev_account"] == "usr:dana"
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["answered_count"] == 0
           and empty["backlog_answered_count"] == 0
           and empty["buyer_count"] == 0
           and empty["listing_count"] == 0
           and empty["answered_listing_count"] == 0
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_answered_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_answered_count"] is None
           and empty["fastest_seconds"] is None
           and empty["slowest_seconds"] is None
           and empty["mean_seconds"] is None)
    record("AC-SAM1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              (empty["month_count"], empty["months"],
               empty["fastest_seconds"])))

    # -- AC-SAM2 cadence law: the answer books on answered_utc ------
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    grid = [row["month"] for row in env["months"]]
    ok2 = (grid == ["2026-01", "2026-02", "2026-03"]
           and jan["answered_count"] == 1
           and jan["backlog_count"] == 0
           and jan["same_month_count"] == 1
           and mar["answered_count"] == 2
           and mar["backlog_count"] == 1
           and mar["same_month_count"] == 1
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-03"
           and env["answered_count"] == 3
           and env["backlog_answered_count"] == 1)
    record("AC-SAM2", ok2,
           "grid=%r jan=%r mar=%r totals=%r"
           % (grid, (jan["answered_count"], jan["backlog_count"]),
              (mar["answered_count"], mar["backlog_count"]),
              (env["answered_count"], env["backlog_answered_count"])))

    # -- AC-SAM3 latency law across the month boundary --------------
    ok3 = (jan["fastest_seconds"] == jan["slowest_seconds"]
           == jan["mean_seconds"] == 21600
           and mar["fastest_seconds"] == 10800
           and mar["slowest_seconds"] == 4492800
           and mar["mean_seconds"] == 2251800
           and env["fastest_seconds"] == 10800
           and env["slowest_seconds"] == 4492800
           and env["mean_seconds"] == 1508400
           and env["mean_seconds"] == (21600 + 4492800 + 10800) // 3)
    record("AC-SAM3", ok3,
           "jan=%r mar=%r env=%r"
           % ((jan["fastest_seconds"], jan["slowest_seconds"],
               jan["mean_seconds"]),
              (mar["fastest_seconds"], mar["slowest_seconds"],
               mar["mean_seconds"]),
              (env["fastest_seconds"], env["slowest_seconds"],
               env["mean_seconds"])))

    # -- AC-SAM4 backlog split, conservation, participants ----------
    feb = month_row(env, "2026-02")
    ok4 = (all(row["backlog_count"] + row["same_month_count"]
               == row["answered_count"] for row in env["months"])
           and sum(row["backlog_count"] for row in env["months"])
           == env["backlog_answered_count"] == 1
           and sum(row["answered_count"] for row in env["months"])
           == env["answered_count"] == 3
           and env["buyer_count"] == 3
           and env["listing_count"] == 3
           and env["answered_listing_count"] == 2
           and jan["buyer_count"] == 1
           and jan["listing_count"] == 1
           and mar["buyer_count"] == 2
           and mar["listing_count"] == 2
           and env["listing_count"]
           >= sum(row["listing_count"] for row in env["months"]) - 1)
    record("AC-SAM4", ok4,
           "backs=%r envelope=%r jan=%r mar=%r"
           % ([row["backlog_count"] for row in env["months"]],
              (env["answered_count"], env["backlog_answered_count"],
               env["buyer_count"], env["listing_count"],
               env["answered_listing_count"]),
              (jan["buyer_count"], jan["listing_count"]),
              (mar["buyer_count"], mar["listing_count"])))

    # -- AC-SAM5 contiguous grid, accumulator and the peak law ------
    ok5 = (env["month_count"] == len(env["months"]) == 3
           and env["active_month_count"] == 2
           and feb["answered_count"] == 0
           and feb["backlog_count"] == 0
           and feb["same_month_count"] == 0
           and feb["buyer_count"] == 0
           and feb["listing_count"] == 0
           and feb["fastest_seconds"] is None
           and feb["slowest_seconds"] is None
           and feb["mean_seconds"] is None
           and feb["running_answered"] == jan["running_answered"] == 1
           and [row["running_answered"] for row in env["months"]]
           == [1, 1, 3]
           and env["months"][-1]["running_answered"]
           == env["answered_count"] == 3
           and env["latest_month_answered_count"] == 2
           and env["peak_month"] == "2026-03"
           and env["peak_answered_count"] == 2)
    record("AC-SAM5", ok5,
           "months=%d active=%d feb=%r running=%r peak=%r"
           % (env["month_count"], env["active_month_count"],
              (feb["answered_count"], feb["mean_seconds"]),
              [row["running_answered"] for row in env["months"]],
              (env["peak_month"], env["peak_answered_count"])))

    # -- AC-SAM6 cross-face identity and strict isolation ----------
    life = am.api_seller_answers("usr:dana")
    gina = am.api_seller_answer_months("usr:gina")
    ok6 = (life["answered_count"] == env["answered_count"]
           and life["buyer_count"] == env["buyer_count"]
           and life["listing_count"] == env["listing_count"]
           and life["fastest_seconds"] == env["fastest_seconds"]
           and life["slowest_seconds"] == env["slowest_seconds"]
           and life["mean_seconds"] == env["mean_seconds"]
           and gina["answered_count"] == 1
           and gina["backlog_answered_count"] == 1
           and gina["buyer_count"] == 1
           and gina["listing_count"] == 1
           and gina["month_count"] == 1
           and gina["months"][0]["month"] == "2026-03"
           and gina["months"][0]["backlog_count"] == 1
           and gina["slowest_seconds"] == 5788800)
    record("AC-SAM6", ok6,
           "lifetime=%r face=%r gina=%r"
           % ((life["answered_count"], life["buyer_count"],
               life["listing_count"], life["mean_seconds"]),
              (env["answered_count"], env["buyer_count"],
               env["listing_count"], env["mean_seconds"]),
              (gina["answered_count"], gina["month_count"],
               gina["slowest_seconds"])))

    # -- AC-SAM7 account gate and the pure read --------------------
    codes = [error_code(am.api_seller_answer_months, form)
             for form in BAD_ACCOUNTS]
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_seller_answer_months("usr:dana"))
    call_b = dumps(am.api_seller_answer_months("usr:dana"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and call_a == call_b == dumps(env)
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-SAM7", ok7,
           "gate=%r deterministic=%r digests_same=%r tx_same=%r"
           % (codes, call_a == call_b,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-SAM8 restarts, wiring and hygiene ----------------------
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_seller_answer_months("usr:dana"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_seller_answer_months("usr:dana"))
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (call_a == call_c == call_d == dumps(env)
           and b'"ledger-apimarket-sellermonths"' in recon
           and b"test_apimarket_sellermonths.py" in recon
           and b"def api_seller_answer_months" in src
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-SAM8", ok8,
           "bytes_same=%r wired=%r ascii=%r crlf_clean=%r"
           % (call_a == call_d,
              b'"ledger-apimarket-sellermonths"' in recon,
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