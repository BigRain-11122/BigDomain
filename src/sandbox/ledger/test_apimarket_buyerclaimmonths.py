"""Acceptance suite for the apimarket buyer-side monthly claim flow
(BigDomain R2209; canon = the R2209 explore-queue claim row, criteria
AC-BCM1..AC-BCM8 registered in that row BEFORE this code existed).

Face under proof: APIMarketFace.api_buyer_claim_months. api_buyer_claim_todo
answers the present debt of one resident (the claims waiting on a
decision, with no dates at all) and api_market_claim_months aggregates the
whole market, so one resident's own claim pressure over time had no face.
This suite pins:

  - the 22-key envelope, the 11-key month rows, the honest empty world
    and the keyword-signature contract;
  - the booking law (a claim books only in the UTC month of its own
    opened_utc; a refund landing two months later neither re-dates the
    claim nor invents a row in the refund month), and the deliberate
    divergence from api_buyer_refund_months, which books that cash in
    the month it came back;
  - the contiguous grid with honest zero months whose average is None
    and whose running accumulator is carried flat;
  - the five-state seam and the partition law (open + answered +
    withdrawn + refunded == claim_count) plus the closed share;
  - the pooled average, which a mean of monthly means would answer
    differently (6.2 pooled against 6.33 averaged);
  - noted_count as the buyer-side follow-up signal, independent of how
    the claim later resolved;
  - strict buyer isolation, the raw-table identity, and the peak law
    with the earlier-month tie-break;
  - the seven-form account gate before any read, the bare prefix
    reading honestly empty, the pure-read law and cross-instance
    byte identity, the wiring and the ASCII/LF hygiene.

Usage: python test_apimarket_buyerclaimmonths.py
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
import apimarket as A                 # noqa: E402 (R2209 face)
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
    "buyer_id", "scope", "month_count", "active_month_count",
    "claim_count", "open_count", "answered_count", "withdrawn_count",
    "refunded_count", "closed_count", "resolved_share", "claim_amount",
    "refunded_amount", "avg_claim_amount", "noted_count", "peak_month",
    "peak_claim_count", "first_month", "last_month",
    "latest_month_claim_count", "disclaimer", "months"}

ROW_KEYS = {
    "month", "claim_count", "open_count", "answered_count",
    "withdrawn_count", "refunded_count", "claim_amount",
    "refunded_amount", "avg_claim_amount", "noted_count",
    "running_claim_count"}


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set before
    each write so the month buckets are reproducible."""

    def __init__(self):
        self.value = "2026-06-01T00:00:00Z"

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
    raise AssertionError("month %r missing from months" % (month,))


def seed_world(led, dk, am, clock):
    """dana owns t1 (10), t2 (4), t4 (5) and t5 (6); frank owns t3 (6).
    Claims open in June, September and October, so the grid must carry
    July and August as honest zero months and December must never
    appear even though a refund lands there.

      bob   t1 06-02 -> claim 06-06 -> refund 06-09   (refunded)
      bob   t2 06-10 -> claim 06-12 -> answer 06-15 + note 06-18
      bob   t4 10-05 -> claim 10-07 -> withdraw 10-09
      bob   t5 10-20 -> claim 10-22 -> refund 12-15   (refund month 12)
      bob   t3 10-25 -> claim 10-27                   (open)
      carol t1 09-10 -> claim 09-15                   (open)
      dave  t1 08-08 -> claim 08-12                   (open)
      dave  t2 10-08 -> claim 10-12                   (open; one claim
                                                        in two months so
                                                        the peak is a tie)
    """
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-BCM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-BCM-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)

    clock.value = "2026-06-01T00:00:00Z"
    t1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    t2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 4,
                        False)["listing_id"]
    t4 = am.publish_api("usr:dana", "gap-scan", "Gap Scan API",
                        "session gap scanner", PAYLOAD, 5,
                        False)["listing_id"]
    t5 = am.publish_api("usr:dana", "alpha-notes", "Alpha Notes API",
                        "research note feed", PAYLOAD, 6,
                        False)["listing_id"]
    t3 = am.publish_api("usr:frank", "chart-render",
                        "Chart Render API",
                        "chart image render endpoint", PAYLOAD, 6,
                        False)["listing_id"]

    clock.value = "2026-06-02T10:00:00Z"
    p1 = am.purchase_api("usr:bob", t1, "ref-bob-t1")["purchase_id"]
    clock.value = "2026-06-06T10:00:00Z"
    c1 = am.open_claim("usr:bob", p1, "output does not match docs")[
        "claim_id"]
    clock.value = "2026-06-09T10:00:00Z"
    am.refund_api("usr:bob", p1, "not what was described")

    clock.value = "2026-06-10T09:00:00Z"
    p2 = am.purchase_api("usr:bob", t2, "ref-bob-t2")["purchase_id"]
    clock.value = "2026-06-12T09:00:00Z"
    c2 = am.open_claim("usr:bob", p2, "feed is stale")["claim_id"]
    clock.value = "2026-06-15T09:00:00Z"
    am.respond_claim("usr:dana", c2, "refreshing the feed tonight")
    clock.value = "2026-06-18T09:00:00Z"
    am.add_claim_note("usr:bob", c2, "still stale three days later")

    clock.value = "2026-09-10T09:00:00Z"
    p6 = am.purchase_api("usr:carol", t1, "ref-carol-t1")[
        "purchase_id"]
    clock.value = "2026-09-15T09:00:00Z"
    am.open_claim("usr:carol", p6, "billed twice")

    clock.value = "2026-08-08T09:00:00Z"
    p7 = am.purchase_api("usr:dave", t1, "ref-dave-t1")[
        "purchase_id"]
    clock.value = "2026-08-12T09:00:00Z"
    am.open_claim("usr:dave", p7, "unusable output")

    clock.value = "2026-10-05T09:00:00Z"
    p3 = am.purchase_api("usr:bob", t4, "ref-bob-t4")["purchase_id"]
    clock.value = "2026-10-07T09:00:00Z"
    c3 = am.open_claim("usr:bob", p3, "wrong payload")["claim_id"]
    clock.value = "2026-10-09T09:00:00Z"
    am.withdraw_claim("usr:bob", c3)

    clock.value = "2026-10-08T09:00:00Z"
    p8 = am.purchase_api("usr:dave", t2, "ref-dave-t2")[
        "purchase_id"]
    clock.value = "2026-10-12T09:00:00Z"
    am.open_claim("usr:dave", p8, "late data")

    clock.value = "2026-10-20T09:00:00Z"
    p4 = am.purchase_api("usr:bob", t5, "ref-bob-t5")["purchase_id"]
    clock.value = "2026-10-22T09:00:00Z"
    am.open_claim("usr:bob", p4, "notes are empty")["claim_id"]
    clock.value = "2026-12-15T09:00:00Z"
    am.refund_api("usr:bob", p4, "endpoint down")

    clock.value = "2026-10-25T09:00:00Z"
    p5 = am.purchase_api("usr:bob", t3, "ref-bob-t3")["purchase_id"]
    clock.value = "2026-10-27T09:00:00Z"
    am.open_claim("usr:bob", p5, "chart renders blank")

    return {"t1": t1, "t2": t2, "t3": t3, "t4": t4, "t5": t5,
            "c1": c1, "c2": c2, "c3": c3}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerclaimmonths-")
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

    # -- AC-BCM1 the contract, honest empty first, keyword signature --
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-bcm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_claim_months("usr:bob")
    close_stack(e_am, e_dk, e_metered, e_led)

    seed_world(led, dk, am, _CLOCK)
    env = am.api_buyer_claim_months("usr:bob")

    signature_ok = False
    try:
        am.api_buyer_claim_months("usr:bob", bogus=1)
    except TypeError:
        signature_ok = True
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for row in env["months"])
    ok1 = (set(empty.keys()) == ENVELOPE_KEYS
           and set(env.keys()) == ENVELOPE_KEYS
           and rows_ok
           and len(env) == 22
           and empty["disclaimer"] == DISCLAIMER
           and empty["buyer_id"] == "usr:bob"
           and empty["scope"] == "buyer"
           and empty["month_count"] == 0
           and empty["active_month_count"] == 0
           and empty["months"] == []
           and empty["claim_count"] == 0
           and empty["open_count"] == 0
           and empty["answered_count"] == 0
           and empty["withdrawn_count"] == 0
           and empty["refunded_count"] == 0
           and empty["closed_count"] == 0
           and empty["resolved_share"] is None
           and empty["claim_amount"] == 0
           and empty["refunded_amount"] == 0
           and empty["avg_claim_amount"] is None
           and empty["noted_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_claim_count"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_claim_count"] is None
           and signature_ok)
    record("AC-BCM1", ok1,
           "env_keys=%d exact=%r rows=%d empty=%r sig=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS,
              len(env["months"]),
              (empty["month_count"], empty["claim_count"],
               empty["avg_claim_amount"], empty["peak_month"]),
              signature_ok))

    # -- AC-BCM2 the booking law, never the refund month -------------
    conn = sqlite3.connect(am.db_path)
    raw = conn.execute(
        "SELECT c.opened_utc, c.price_paid, f.refunded_utc"
        " FROM apimarket_claims c"
        " LEFT JOIN apimarket_refunds f"
        " ON f.purchase_id = c.purchase_id"
        " WHERE c.buyer_id = 'usr:bob' ORDER BY c.claim_id"
    ).fetchall()
    conn.close()
    raw_month = {}
    for opened_utc, price, _refunded in raw:
        cell = raw_month.setdefault(str(opened_utc)[:7],
                                    {"count": 0, "money": 0})
        cell["count"] += 1
        cell["money"] += int(price)
    jun = month_row(env, "2026-06")
    oct_row = month_row(env, "2026-10")
    refund_months = am.api_buyer_refund_months("usr:bob")
    refund_grid = [row["month"] for row in refund_months["months"]]
    refund_dec = [row for row in refund_months["months"]
                  if row["month"] == "2026-12"][0]
    ok2 = (sorted(raw_month) == ["2026-06", "2026-10"]
           and jun["claim_count"] == 2
           and jun["claim_amount"] == 14
           and oct_row["claim_count"] == 3
           and oct_row["claim_amount"] == 17
           and env["claim_count"] == 5
           and env["claim_amount"] == 31
           and [row["month"] for row in env["months"]]
           == ["2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]
           and "2026-12" not in [row["month"]
                                 for row in env["months"]]
           and refund_grid == ["2026-06", "2026-07", "2026-08",
                               "2026-09", "2026-10", "2026-11",
                               "2026-12"]
           and refund_dec["refund_count"] == 1
           and refund_dec["refunded"] == 6
           and refund_months["refunded"] == env["refunded_amount"]
           and jun["refunded_amount"] == 10
           and oct_row["refunded_amount"] == 6
           and all(month_row(env, month)["claim_count"]
                   == cell["count"]
                   and month_row(env, month)["claim_amount"]
                   == cell["money"]
                   for month, cell in raw_month.items()))
    record("AC-BCM2", ok2,
           "raw_months=%r jun=%r oct=%r refund_grid=%r money=%r/%r"
           % (sorted(raw_month),
              (jun["claim_count"], jun["claim_amount"],
               jun["refunded_amount"]),
              (oct_row["claim_count"], oct_row["claim_amount"],
               oct_row["refunded_amount"]),
              refund_grid, env["refunded_amount"],
              refund_months["refunded"]))

    # -- AC-BCM3 contiguous grid, honest zero months, flat running ---
    jul = month_row(env, "2026-07")
    aug = month_row(env, "2026-08")
    sep = month_row(env, "2026-09")
    zero_ok = all(
        row["claim_count"] == 0
        and row["open_count"] == 0
        and row["answered_count"] == 0
        and row["withdrawn_count"] == 0
        and row["refunded_count"] == 0
        and row["claim_amount"] == 0
        and row["refunded_amount"] == 0
        and row["avg_claim_amount"] is None
        and row["noted_count"] == 0
        for row in (jul, aug, sep))
    ok3 = (env["month_count"] == 5
           and env["active_month_count"] == 2
           and zero_ok
           and jul["running_claim_count"] == 2
           and aug["running_claim_count"] == 2
           and sep["running_claim_count"] == 2
           and oct_row["running_claim_count"] == 5
           and env["first_month"] == "2026-06"
           and env["last_month"] == "2026-10")
    record("AC-BCM3", ok3,
           "month_count=%r active=%r zeros=%r carried=%r"
           % (env["month_count"], env["active_month_count"], zero_ok,
              (jul["running_claim_count"], aug["running_claim_count"],
               sep["running_claim_count"],
               oct_row["running_claim_count"])))

    # -- AC-BCM4 partition, closed share and conservation -------------
    partition_ok = all(
        row["open_count"] + row["answered_count"]
        + row["withdrawn_count"] + row["refunded_count"]
        == row["claim_count"] for row in env["months"])
    running = [row["running_claim_count"] for row in env["months"]]
    monotone = all(running[i] <= running[i + 1]
                   for i in range(len(running) - 1))
    conn = sqlite3.connect(am.db_path)
    raw_count, raw_money = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(price_paid), 0)"
        " FROM apimarket_claims WHERE buyer_id = 'usr:bob'"
    ).fetchone()
    conn.close()
    ok4 = (partition_ok
           and env["claim_count"] == sum(row["claim_count"]
                                         for row in env["months"])
           == int(raw_count) == 5
           and env["claim_amount"] == int(raw_money) == 31
           and env["open_count"] == 1
           and env["answered_count"] == 1
           and env["withdrawn_count"] == 1
           and env["refunded_count"] == 2
           and env["closed_count"] == 3
           and env["closed_count"] == (env["refunded_count"]
                                       + env["withdrawn_count"])
           and env["resolved_share"] == 0.6
           and monotone
           and running[-1] == env["claim_count"])
    record("AC-BCM4", ok4,
           "partition=%r counts=%r closed=%r share=%r raw=%r/%r"
           " running=%r"
           % (partition_ok,
              (env["claim_count"], env["open_count"],
               env["answered_count"], env["withdrawn_count"],
               env["refunded_count"]),
              (env["closed_count"], env["resolved_share"]),
              env["resolved_share"], int(raw_count), int(raw_money),
              running))

    # -- AC-BCM5 the status seam, one bucket per claim ---------------
    conn = sqlite3.connect(am.db_path)
    states = []
    for claim_id, in conn.execute(
            "SELECT claim_id FROM apimarket_claims"
            " WHERE buyer_id = 'usr:bob' ORDER BY claim_id").fetchall():
        row = conn.execute(
            "SELECT f.refund_id, w.withdrawn_utc, r.replied_utc"
            " FROM apimarket_claims c"
            " LEFT JOIN apimarket_refunds f"
            " ON f.purchase_id = c.purchase_id"
            " LEFT JOIN apimarket_claim_responses r"
            " ON r.claim_id = c.claim_id"
            " LEFT JOIN apimarket_claim_withdrawals w"
            " ON w.claim_id = c.claim_id"
            " WHERE c.claim_id = ?", (claim_id,)).fetchone()
        if row[0] is not None:
            states.append("refunded")
        elif row[1] is not None:
            states.append("withdrawn")
        elif row[2] is not None:
            states.append("answered")
        else:
            states.append("open")
    conn.close()
    ok5 = (states == ["refunded", "answered", "withdrawn",
                      "refunded", "open"]
           and states.count("refunded") == env["refunded_count"]
           and states.count("answered") == env["answered_count"]
           and states.count("withdrawn") == env["withdrawn_count"]
           and states.count("open") == env["open_count"]
           and len(states) == env["claim_count"])
    record("AC-BCM5", ok5, "states=%r counts=%r"
           % (states, (env["open_count"], env["answered_count"],
                       env["withdrawn_count"],
                       env["refunded_count"])))

    # -- AC-BCM6 follow-up notes and the pooled average ---------------
    month_means = [row["avg_claim_amount"] for row in env["months"]
                   if row["claim_count"] > 0]
    averaged = round(sum(month_means) / len(month_means), 2)
    ok6 = (env["noted_count"] == 1
           and jun["noted_count"] == 1
           and oct_row["noted_count"] == 0
           and env["avg_claim_amount"] == 6.2
           and month_means == [7.0, 5.67]
           and averaged == 6.33
           and env["avg_claim_amount"] != averaged
           and jun["avg_claim_amount"] == 7.0
           and oct_row["avg_claim_amount"] == 5.67
           and env["latest_month_claim_count"] == 3)
    record("AC-BCM6", ok6,
           "noted=%r pooled=%r month_means=%r mean_of_means=%r"
           " latest=%r"
           % (env["noted_count"], env["avg_claim_amount"],
              month_means, averaged,
              env["latest_month_claim_count"]))

    # -- AC-BCM7 isolation, raw market identity and the peak law ------
    carol = am.api_buyer_claim_months("usr:carol")
    dave = am.api_buyer_claim_months("usr:dave")
    carol_grid = [row["month"] for row in carol["months"]]
    dave_grid = [row["month"] for row in dave["months"]]
    conn = sqlite3.connect(am.db_path)
    market_count = conn.execute(
        "SELECT COUNT(*) FROM apimarket_claims").fetchone()[0]
    conn.close()
    ok7 = (carol["claim_count"] == 1
           and carol_grid == ["2026-09"]
           and carol["open_count"] == 1
           and carol["resolved_share"] == 0.0
           and carol["claim_amount"] == 10
           and dave["claim_count"] == 2
           and dave_grid == ["2026-08", "2026-09", "2026-10"]
           and dave["peak_month"] == "2026-08"
           and dave["peak_claim_count"] == 1
           and env["peak_month"] == "2026-10"
           and env["peak_claim_count"] == 3
           and carol["peak_month"] == "2026-09"
           and empty["peak_month"] is None
           and env["claim_count"] + carol["claim_count"] \
           + dave["claim_count"] == int(market_count) == 8
           and env["claim_amount"] + carol["claim_amount"] \
           + dave["claim_amount"] == 55)
    record("AC-BCM7", ok7,
           "carol=%r dave=%r peak=%r market=%r"
           % ((carol["claim_count"], carol_grid,
               carol["resolved_share"]),
              (dave["claim_count"], dave_grid, dave["peak_month"]),
              (env["peak_month"], env["peak_claim_count"]),
              int(market_count)))

    # -- AC-BCM8 gates, purity, hygiene and wiring --------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad = ["", "   ", 123, ["usr:x"], {"a": 1}, "usr", b"usr:x"]
    bad_ok = []
    for form in bad:
        try:
            am.api_buyer_claim_months(form)
            bad_ok.append(False)
        except A.ApiMarketError as err:
            bad_ok.append(err.code == A.E_AM_BAD_ACCOUNT)
    bare = am.api_buyer_claim_months("usr:")
    digests_after_gates = market_digests(am)

    call_a = dumps(am.api_buyer_claim_months("usr:bob"))
    call_b = dumps(am.api_buyer_claim_months("usr:bob"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    todo = am.api_buyer_claim_todo("usr:bob")

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_buyer_claim_months("usr:bob"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_buyer_claim_months("usr:bob"))
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (all(bad_ok)
           and bare["month_count"] == 0
           and bare["claim_count"] == 0
           and bare["months"] == []
           and bare["scope"] == "buyer"
           and digests_before == digests_after_gates == digests_after
           and tx_before == tx_after
           and call_a == call_b == dumps(env)
           and call_c == call_d == dumps(env)
           and call_a != dumps(carol)
           and todo["claim_count"] == env["claim_count"]
           and b'"ledger-apimarket-buyerclaimmonths"' in recon
           and b"test_apimarket_buyerclaimmonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-BCM8", ok8,
           "gates=%r bare=%r digests_same=%r tables=%d tx_same=%r"
           " bytes=%r wired=%r crossface=%r ascii=%r"
           % (all(bad_ok),
              (bare["month_count"], bare["claim_count"]),
              digests_before == digests_after, len(digests_before),
              tx_before == tx_after, call_c == call_d,
              b'"ledger-apimarket-buyerclaimmonths"' in recon,
              todo["claim_count"] == env["claim_count"],
              all(b < 128 for b in test_src)))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())