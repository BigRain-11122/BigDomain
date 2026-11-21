"""Acceptance suite for the apimarket buyer-side monthly pre-sale
question volume (BigDomain R3157; canon = the R2248 explore-queue seed
row, criteria AC-BQM1..AC-BQM8 registered in the R3157 PIN row BEFORE
this code existed).

Face under proof: APIMarketFace.api_buyer_question_months.

api_market_question_months answers the whole market by month,
api_category_question_months one category and
api_seller_question_months one seller's INCOMING pressure, while the
buyer side carried only a lifetime timeline (api_buyer_questions) and an
answering-month wait face (api_buyer_answer_wait) - so a resident who
interrogated twenty shelves in August and went silent, and one who never
asked, read identically. This suite pins:

  - the 18-key envelope, the 9-key month rows, the usr: gate, the buyer
    scope and the honest empty world;
  - the booking law (a question books in its own asked_utc month, the
    answering leg is credited to the ASKING month, and an answer landing
    in a later month moves nothing);
  - the grid law (contiguous asking months only, an honest zero month
    whose answer_rate is None, monotone running accumulators ending at
    the envelope totals, and no row for the answering month);
  - participants (per-month event-derived distinct sellers and listings
    against lifetime distinct envelope counts, so the envelope is
    honestly <= the row sums);
  - the peak law (highest month, earlier-month tie-break, a zero month
    never a peak);
  - strict buyer isolation (another buyer's questions never leak) and
    the honest empty envelope for a prefix-valid account with none;
  - the cross-face identity against api_buyer_questions and
    api_market_question_months;
  - purity (zero row mutations, zero token movement), two-call and
    two-instance byte identity, the reconcile wiring and ASCII/LF
    hygiene.

Usage: python test_apimarket_buyerquestionmonths.py
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
import apimarket as A                 # noqa: E402 (R3157 face)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))

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
    "market_question_count", "month_count", "active_month_count",
    "peak_month", "peak_question_count", "first_month", "last_month",
    "latest_month_question_count", "disclaimer", "months"}

ROW_KEYS = {
    "month", "question_count", "answered_count", "unanswered_count",
    "answer_rate", "seller_count", "listing_count", "running_question",
    "running_answer"}


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set before
    each write so the month buckets are reproducible."""

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


def dumps(env):
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
    return None


def seed_world(led, dk, am, clock):
    """dana owns t1 (risk-scan), t2 (macro-feed) and t3 (alt-data).
    bob asks four questions and carol one, so the two axes separate:

      q1  t1  asked 2026-08-05 -> answered 2026-10-03  (cross-month)
      q2  t2  asked 2026-09-10 -> answered 2026-09-12  (same month)
      q3  t1  asked 2026-11-05 -> still open
      q4  t3  asked 2026-11-20 -> answered 2026-12-01  (cross-month)
      q5  t3  carol asked 2026-09-20 -> answered 2026-09-21

    bob therefore reads asking months 08:1 / 09:1 / 10:0 (honest zero) /
    11:2, with NO December row even though two answers landed in
    October and December; the August row carries answered=1 because the
    answering leg is credited to the ASKING month.
    """
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-BQM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-BQM-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)

    clock.value = "2026-07-01T00:00:00Z"
    t1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    t2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 10,
                        False)["listing_id"]
    t3 = am.publish_api("usr:dana", "alt-data", "Alt Data API",
                        "alternative data endpoint", PAYLOAD, 10,
                        False)["listing_id"]

    clock.value = "2026-08-05T10:00:00Z"
    q1 = am.ask_question("usr:bob", t1,
                         "what is the latency?")["question_id"]
    clock.value = "2026-09-10T11:00:00Z"
    q2 = am.ask_question("usr:bob", t2,
                         "which fields ship?")["question_id"]
    clock.value = "2026-11-05T08:00:00Z"
    q3 = am.ask_question("usr:bob", t1,
                         "is history included?")["question_id"]
    clock.value = "2026-11-20T09:00:00Z"
    q4 = am.ask_question("usr:bob", t3, "rate limits?")["question_id"]
    clock.value = "2026-09-20T09:00:00Z"
    q5 = am.ask_question("usr:carol", t3,
                         "does it cover HK?")["question_id"]

    clock.value = "2026-10-03T08:00:00Z"
    am.answer_question("usr:dana", q1, "about 90 ms p50")
    clock.value = "2026-09-12T07:00:00Z"
    am.answer_question("usr:dana", q2, "the v1 field set")
    clock.value = "2026-09-21T09:00:00Z"
    am.answer_question("usr:dana", q5, "yes, HK is covered")
    clock.value = "2026-12-01T09:00:00Z"
    am.answer_question("usr:dana", q4, "60 calls per minute")

    return {"t1": t1, "t2": t2, "t3": t3, "q1": q1, "q2": q2,
            "q3": q3, "q4": q4, "q5": q5}


def seed_tie_world(led, dk, am, clock, listing_id):
    """dave asks two questions in May and two in July, so the peak is a
    tie broken toward the EARLIER month (2026-05)."""
    clock.value = "2026-05-04T10:00:00Z"
    am.ask_question("usr:dave", listing_id, "may question one")
    clock.value = "2026-05-19T10:00:00Z"
    am.ask_question("usr:dave", listing_id, "may question two")
    clock.value = "2026-07-02T10:00:00Z"
    am.ask_question("usr:dave", listing_id, "july question one")
    clock.value = "2026-07-25T10:00:00Z"
    am.ask_question("usr:dave", listing_id, "july question two")


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerquestion-")
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
        return run(db_path, cfg, lobby_cfg, shas_before, clock, tmp)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, shas_before, clock, tmp):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)

    # -- AC-BQM1 the contract, honest empty first --------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-bqm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_question_months("usr:nobody")
    bare = e_am.api_buyer_question_months("usr:")
    try:
        e_am.api_buyer_question_months("nobody")
        bad_gate = False
    except A.ApiMarketError as exc:
        bad_gate = (exc.code == A.E_AM_BAD_ACCOUNT)
    e_am.close()
    e_dk.close()
    e_metered.close()
    e_led.close()

    ok1_empty = (set(empty) == ENVELOPE_KEYS
                 and empty["buyer_id"] == "usr:nobody"
                 and empty["scope"] == "buyer"
                 and empty["question_count"] == 0
                 and empty["answered_count"] == 0
                 and empty["unanswered_count"] == 0
                 and empty["answer_rate"] is None
                 and empty["seller_count"] == 0
                 and empty["listing_count"] == 0
                 and empty["market_question_count"] == 0
                 and empty["month_count"] == 0
                 and empty["active_month_count"] == 0
                 and empty["peak_month"] is None
                 and empty["peak_question_count"] is None
                 and empty["first_month"] is None
                 and empty["last_month"] is None
                 and empty["latest_month_question_count"] == 0
                 and empty["disclaimer"] == DISCLAIMER
                 and empty["months"] == [])
    ok1_bare = (set(bare) == ENVELOPE_KEYS and bare["months"] == []
                and bare["question_count"] == 0
                and bare["answer_rate"] is None)
    ok1_sizes = (len(ENVELOPE_KEYS) == 18 and len(ROW_KEYS) == 9)
    record("AC-BQM1 contract+honest-empty",
           ok1_empty and ok1_bare and ok1_sizes and bad_gate,
           "envelope=%d row=%d empty_months=%d bare=%s gate=%s"
           % (len(empty), len(ROW_KEYS), len(empty["months"]),
              ok1_bare, bad_gate))

    ids = seed_world(led, dk, am, clock)
    env = am.api_buyer_question_months("usr:bob")

    # -- AC-BQM2 booking law ----------------------------------------
    aug = month_row(env, "2026-08")
    sep = month_row(env, "2026-09")
    octo = month_row(env, "2026-10")
    nov = month_row(env, "2026-11")
    ok2 = (aug is not None and aug["question_count"] == 1
           and aug["answered_count"] == 1
           and aug["unanswered_count"] == 0
           and octo is not None and octo["question_count"] == 0
           and octo["answered_count"] == 0
           and month_row(env, "2026-12") is None
           and env["last_month"] == "2026-11")
    record("AC-BQM2 asked-month booking", ok2,
           "aug=%s oct_q=%s dec_row=%s last=%s"
           % (aug and (aug["question_count"], aug["answered_count"]),
              octo and octo["question_count"],
              month_row(env, "2026-12") is not None,
              env["last_month"]))

    # -- AC-BQM3 grid law -------------------------------------------
    grid = [row["month"] for row in env["months"]]
    runs = [(row["running_question"], row["running_answer"])
            for row in env["months"]]
    mono = all(runs[i][0] <= runs[i + 1][0]
               and runs[i][1] <= runs[i + 1][1]
               for i in range(len(runs) - 1))
    ok3 = (grid == ["2026-08", "2026-09", "2026-10", "2026-11"]
           and octo["answer_rate"] is None
           and mono
           and runs[-1][0] == env["question_count"]
           and runs[-1][1] == env["answered_count"]
           and sum(row["question_count"] for row in env["months"])
           == env["question_count"]
           and sum(row["unanswered_count"] for row in env["months"])
           == env["unanswered_count"])
    record("AC-BQM3 contiguous grid+running", ok3,
           "grid=%s runs=%s env_q=%d env_a=%d"
           % (grid, runs, env["question_count"], env["answered_count"]))

    # -- AC-BQM4 participants ---------------------------------------
    ok4 = (nov["seller_count"] == 1 and nov["listing_count"] == 2
           and sep["listing_count"] == 1
           and env["seller_count"] == 1
           and env["listing_count"] == 3
           and env["listing_count"]
           <= sum(row["listing_count"] for row in env["months"]))
    record("AC-BQM4 event-derived participants", ok4,
           "nov=%s sep_list=%d env_sellers=%d env_listings=%d"
           % ((nov["seller_count"], nov["listing_count"]),
              sep["listing_count"], env["seller_count"],
              env["listing_count"]))

    # -- AC-BQM5 peak law (tie breaks to the earlier month) ---------
    tie_led, tie_metered, tie_dk, _tie_gate, tie_am = build_stack(
        os.path.join(tempfile.mkdtemp(prefix="apimarket-bqm-tie-"),
                     "ledger.db"), cfg, lobby_cfg)
    tie_led.mint_to_pool("pool:reserve", 20000, "SETTLE-BQM-T",
                         "settlement")
    tie_led.ensure_account("usr:dave", census_avatar_id="dave")
    tie_dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    clock.value = "2026-04-01T00:00:00Z"
    tie_listing = tie_am.publish_api(
        "usr:dana", "tie-scan", "Tie Scan API",
        "portfolio risk scan endpoint", PAYLOAD, 10, False)["listing_id"]
    seed_tie_world(tie_led, tie_dk, tie_am, clock, tie_listing)
    tie_env = tie_am.api_buyer_question_months("usr:dave")
    tie_am.close()
    tie_dk.close()
    tie_metered.close()
    tie_led.close()
    ok5 = (env["peak_month"] == "2026-11"
           and env["peak_question_count"] == 2
           and month_row(env, "2026-10")["question_count"] == 0
           and tie_env["peak_month"] == "2026-05"
           and tie_env["peak_question_count"] == 2)
    record("AC-BQM5 peak+tie-break", ok5,
           "bob_peak=%s/%s dave_peak=%s/%s"
           % (env["peak_month"], env["peak_question_count"],
              tie_env["peak_month"], tie_env["peak_question_count"]))

    # -- AC-BQM6 strict buyer isolation ----------------------------
    carol = am.api_buyer_question_months("usr:carol")
    ok6 = (env["question_count"] == 4
           and carol["question_count"] == 1
           and carol["months"][0]["month"] == "2026-09"
           and carol["listing_count"] == 1
           and month_row(env, "2026-09")["question_count"] == 1
           and env["market_question_count"] == 5
           and env["seller_count"] == 1)
    record("AC-BQM6 buyer isolation", ok6,
           "bob_q=%d carol_q=%d carol_month=%s market=%d"
           % (env["question_count"], carol["question_count"],
              carol["months"][0]["month"], env["market_question_count"]))

    # -- AC-BQM7 cross-face identity -------------------------------
    life = am.api_buyer_questions("usr:bob")
    market = am.api_market_question_months()
    per_month_ok = True
    for row in env["months"]:
        mrow = month_row(market, row["month"])
        if mrow is None or row["question_count"] > mrow["question_count"]:
            per_month_ok = False
    ok7 = (env["question_count"] == life["question_count"]
           and env["answered_count"] == life["answered_count"]
           and env["unanswered_count"] == life["unanswered_count"]
           and env["market_question_count"] == market["question_count"]
           and per_month_ok)
    record("AC-BQM7 cross-face identity", ok7,
           "life=%d/%d/%d market=%d per_month=%s"
           % (life["question_count"], life["answered_count"],
              life["unanswered_count"], market["question_count"],
              per_month_ok))

    # -- AC-BQM8 purity, determinism, wiring, hygiene --------------
    digests_before = market_digests(am)
    txs_before = ledger_tx_ids(led)
    first = dumps(am.api_buyer_question_months("usr:bob"))
    second = dumps(am.api_buyer_question_months("usr:bob"))
    digests_after = market_digests(am)
    txs_after = ledger_tx_ids(led)
    twin_led, twin_metered, twin_dk, _tg, twin_am = build_stack(
        db_path, cfg, lobby_cfg)
    twin = dumps(twin_am.api_buyer_question_months("usr:bob"))
    twin_am.close()
    twin_dk.close()
    twin_metered.close()
    twin_led.close()

    reg_path = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
    with io.open(reg_path, "r", encoding="utf-8") as handle:
        registry = handle.read()
    name = "ledger-apimarket-buyerquestionmonths"
    at = registry.find(name)
    wired = (at > 0
             and "test_apimarket_buyerquestionmonths.py"
             in registry[at:at + 200]
             and ", 8)," in registry[at:at + 200])

    def hygiene(path):
        with open(path, "rb") as handle:
            blob = handle.read()
        return (all(b < 128 for b in blob) and b"\r" not in blob)

    ok8 = (digests_before == digests_after
           and txs_before == txs_after
           and first == second
           and first == twin
           and wired
           and hygiene(os.path.join(BASE, "apimarket.py"))
           and hygiene(os.path.abspath(__file__)))
    record("AC-BQM8 purity+determinism+wiring", ok8,
           "tables_same=%s tx_same=%s twice=%s twin=%s wired=%s"
           % (digests_before == digests_after,
              txs_before == txs_after, first == second,
              first == twin, wired))

    # -- product files untouched by the suite itself ---------------
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    ok_pure = (shas_before == shas_after)
    record("AC-BQM8 product files byte-identical", ok_pure,
           "files=%d" % len(PRODUCT_FILES))

    close_stack(am, dk, metered, led)

    total = len(RESULTS)
    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %s %d/%d" % ("PASS" if green == total else "FAIL",
                              green, total), flush=True)
    return 0 if green == total else 1


if __name__ == "__main__":
    sys.exit(main())
