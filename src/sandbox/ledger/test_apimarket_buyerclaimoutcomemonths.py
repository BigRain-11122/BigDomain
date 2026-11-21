"""Acceptance suite for the apimarket buyer-side monthly claim OUTCOME
mix (BigDomain R3155; canon = the R3155 explore-queue claim row,
criteria AC-BCO1..AC-BCO8 registered in that row BEFORE this code
existed).

Face under proof: APIMarketFace.api_buyer_claim_outcome_months.

api_buyer_claim_months already carries the four outcome counts, but it
books every claim in the month it was OPENED. The question "how many
claims did I close this month, by which outcome, and how long did I
wait" had no face: a claim opened 08-05 and refunded 10-03 appears only
in August on the opened face and October is silently absent. This suite
pins:

  - the 28-key envelope, the 15-key month rows, the honest empty buyer
    and the scope/buyer_id contract;
  - the resolution-month booking law (a cross-month refund books in the
    refund month and NEVER in the opened month, and the opened month
    gains no row);
  - the api_claims seam precedence (refunded beats withdrawn beats
    answered beats open) partitioning resolved_count, with an
    answered-then-withdrawn claim counting as ONE withdrawn close at the
    withdrawal stamp;
  - the shares over resolved_count (None on a month that closed
    nothing), resolution_rate over claim_count, and the open claim
    staying out of the month rows;
  - pooled latency over closed claims (avg/median/fastest/slowest, None
    on a zero month), derived only from two stored stamps;
  - the contiguous grid with an honest zero month, the carried running
    accumulator and the earlier-month peak tie-break;
  - buyer isolation and cross-face identity against
    api_buyer_claim_months on the lifetime totals;
  - the seven-form account gate before any read, the pure-read law,
    cross-instance byte identity, the wiring and the ASCII/LF hygiene.
"""

import datetime
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
import apimarket as A                 # noqa: E402 (R3155 face)
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
    "claim_count", "resolved_count", "open_count", "answered_count",
    "withdrawn_count", "refunded_count", "answered_share",
    "withdrawn_share", "refunded_share", "resolution_rate",
    "claim_amount", "resolved_claim_amount", "refunded_amount",
    "avg_resolve_seconds", "median_resolve_seconds",
    "fastest_resolve_seconds", "slowest_resolve_seconds", "peak_month",
    "peak_resolved_count", "first_month", "last_month",
    "latest_month_resolved_count", "disclaimer", "months"}

ROW_KEYS = {
    "month", "resolved_count", "answered_count", "withdrawn_count",
    "refunded_count", "answered_share", "withdrawn_share",
    "refunded_share", "resolved_claim_amount", "refunded_amount",
    "avg_resolve_seconds", "median_resolve_seconds",
    "fastest_resolve_seconds", "slowest_resolve_seconds",
    "running_resolved_count"}

FMT = "%Y-%m-%dT%H:%M:%SZ"


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set before
    each write so the month buckets are reproducible."""

    def __init__(self):
        self.value = "2026-08-01T00:00:00Z"

    def now_utc(self):
        return self.value


def seconds(earlier, later):
    return int((datetime.datetime.strptime(later, FMT)
                - datetime.datetime.strptime(earlier, FMT))
               .total_seconds())


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
    """dana owns t1 (price 10); frank owns t2 (price 4). bob's five
    claims each end on a different stamp so the two month axes separate:

      c1 t1 opened 08-05 -> refunded 10-03  (refunded, Oct, 10 tokens)
      c2 t1 opened 09-12 -> answered 09-13  (answered, Sep, 86400 s)
      c3 t1 opened 09-20 -> answered 09-21 -> withdrawn 09-25
                                            (withdrawn, Sep, 432000 s)
      c4 t2 opened 11-05 -> still open      (no month row at all)
      c6 t2 opened 11-20 -> answered 12-01  (answered, Dec, 950400 s)

    carol's claim c5 (t1, refunded 09-16) must never leak into bob.
    bob therefore reads months 09 / 10 / 11 (honest zero) / 12, with
    August absent because nothing CLOSED in August even though c1 was
    opened there.
    """
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-BCO-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-BCO-S",
                     "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)

    clock.value = "2026-08-01T00:00:00Z"
    t1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    t2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 10,
                        False)["listing_id"]
    t3 = am.publish_api("usr:dana", "alt-data", "Alt Data API",
                        "alternative data endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    t4 = am.publish_api("usr:frank", "chart-render",
                        "Chart Render API",
                        "chart image render endpoint", PAYLOAD, 4,
                        False)["listing_id"]
    t5 = am.publish_api("usr:frank", "pdf-render", "PDF Render API",
                        "pdf render endpoint", PAYLOAD, 4,
                        False)["listing_id"]

    clock.value = "2026-08-02T10:00:00Z"
    p1 = am.purchase_api("usr:bob", t1, "ref-bob-t1")["purchase_id"]
    clock.value = "2026-09-10T10:00:00Z"
    p2 = am.purchase_api("usr:bob", t2, "ref-bob-t2")["purchase_id"]
    clock.value = "2026-09-18T09:00:00Z"
    p3 = am.purchase_api("usr:bob", t3, "ref-bob-t3")["purchase_id"]
    clock.value = "2026-11-01T09:00:00Z"
    p4 = am.purchase_api("usr:bob", t4, "ref-bob-t4")["purchase_id"]
    clock.value = "2026-11-18T09:00:00Z"
    p5 = am.purchase_api("usr:bob", t5, "ref-bob-t5")["purchase_id"]
    clock.value = "2026-09-14T09:00:00Z"
    p6 = am.purchase_api("usr:carol", t1, "ref-carol-t1")["purchase_id"]

    clock.value = "2026-08-05T10:00:00Z"
    c1 = am.open_claim("usr:bob", p1, "endpoint returned 500")["claim_id"]
    clock.value = "2026-09-12T11:00:00Z"
    c2 = am.open_claim("usr:bob", p2,
                       "risk numbers look wrong")["claim_id"]
    clock.value = "2026-09-20T08:00:00Z"
    c3 = am.open_claim("usr:bob", p3, "scan result truncated")["claim_id"]
    clock.value = "2026-11-05T08:00:00Z"
    c4 = am.open_claim("usr:bob", p4, "chart output broken")["claim_id"]
    clock.value = "2026-11-20T09:00:00Z"
    c6 = am.open_claim("usr:bob", p5, "render timed out")["claim_id"]
    clock.value = "2026-09-15T09:00:00Z"
    c5 = am.open_claim("usr:carol", p6, "scan mispriced")["claim_id"]

    clock.value = "2026-09-13T11:00:00Z"
    am.respond_claim("usr:dana", c2, "recomputed the scan by hand")
    clock.value = "2026-09-21T08:00:00Z"
    am.respond_claim("usr:dana", c3, "re-ran the scan")
    clock.value = "2026-09-25T08:00:00Z"
    am.withdraw_claim("usr:bob", c3)
    clock.value = "2026-09-16T09:00:00Z"
    am.refund_api("usr:carol", p6, "scan mispriced")
    clock.value = "2026-10-03T08:00:00Z"
    am.refund_api("usr:bob", p1, "broken endpoint")
    clock.value = "2026-12-01T09:00:00Z"
    am.respond_claim("usr:frank", c6, "re-rendered the chart")

    return {"c1": c1, "c2": c2, "c3": c3, "c4": c4, "c5": c5,
            "c6": c6}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerclaimoutcome-")
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

    # -- AC-BCO1 the contract, honest empty first --------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-bco-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_claim_outcome_months("usr:nobody")
    e_am.close()
    e_dk.close()
    e_metered.close()
    e_led.close()
    ok1_empty = (set(empty) == ENVELOPE_KEYS
                 and empty["buyer_id"] == "usr:nobody"
                 and empty["scope"] == "buyer"
                 and empty["month_count"] == 0
                 and empty["active_month_count"] == 0
                 and empty["claim_count"] == 0
                 and empty["resolved_count"] == 0
                 and empty["open_count"] == 0
                 and empty["claim_amount"] == 0
                 and empty["resolved_claim_amount"] == 0
                 and empty["refunded_amount"] == 0
                 and empty["answered_share"] is None
                 and empty["withdrawn_share"] is None
                 and empty["refunded_share"] is None
                 and empty["resolution_rate"] is None
                 and empty["avg_resolve_seconds"] is None
                 and empty["median_resolve_seconds"] is None
                 and empty["fastest_resolve_seconds"] is None
                 and empty["slowest_resolve_seconds"] is None
                 and empty["peak_month"] is None
                 and empty["peak_resolved_count"] is None
                 and empty["first_month"] is None
                 and empty["last_month"] is None
                 and empty["latest_month_resolved_count"] is None
                 and empty["months"] == []
                 and empty["disclaimer"] == DISCLAIMER)

    seed_world(led, dk, am, clock)

    bob = am.api_buyer_claim_outcome_months("usr:bob")
    carol = am.api_buyer_claim_outcome_months("usr:carol")
    ok1 = (ok1_empty
           and set(bob) == ENVELOPE_KEYS
           and all(set(row) == ROW_KEYS for row in bob["months"])
           and bob["scope"] == "buyer"
           and bob["buyer_id"] == "usr:bob"
           and bob["disclaimer"] == DISCLAIMER
           and [row["month"] for row in bob["months"]]
           == ["2026-09", "2026-10", "2026-11", "2026-12"])
    record("AC-BCO1", ok1,
           "keys=%d empty=%r grid=%r rows=%d"
           % (len(empty), (empty["month_count"], empty["resolved_count"],
                           empty["resolution_rate"], empty["months"]),
              [row["month"] for row in bob["months"]],
              len(bob["months"])))

    sep = month_row(bob, "2026-09")
    oct_row = month_row(bob, "2026-10")
    nov = month_row(bob, "2026-11")
    dec = month_row(bob, "2026-12")

    # -- AC-BCO2 resolution-month booking law ------------------------
    ok2 = ("2026-08" not in [row["month"] for row in bob["months"]]
           and [row["month"] for row in carol["months"]] == ["2026-09"]
           and sep["resolved_count"] == 2
           and sep["answered_count"] == 1
           and sep["withdrawn_count"] == 1
           and sep["refunded_count"] == 0
           and oct_row["resolved_count"] == 1
           and oct_row["refunded_count"] == 1
           and oct_row["refunded_amount"] == 10
           and dec["resolved_count"] == 1
           and dec["answered_count"] == 1
           and bob["resolved_count"] == 4
           and bob["claim_count"] == 5)
    record("AC-BCO2", ok2,
           "grid=%r sep=%r oct=%r dec=%r"
           % ([row["month"] for row in bob["months"]],
              (sep["resolved_count"], sep["answered_count"],
               sep["withdrawn_count"], sep["refunded_count"]),
              (oct_row["resolved_count"], oct_row["refunded_count"],
               oct_row["refunded_amount"]),
              (dec["resolved_count"], dec["answered_count"])))

    # -- AC-BCO3 the seam partitions resolved_count ------------------
    def partitions(env):
        rows_ok = all(
            row["resolved_count"] == row["answered_count"]
            + row["withdrawn_count"] + row["refunded_count"]
            for row in env["months"])
        env_ok = (env["resolved_count"] == env["answered_count"]
                  + env["withdrawn_count"] + env["refunded_count"])
        return rows_ok and env_ok

    ok3 = (partitions(bob) and partitions(carol)
           and bob["answered_count"] == 2
           and bob["withdrawn_count"] == 1
           and bob["refunded_count"] == 1
           and bob["open_count"] == 1
           and bob["resolved_count"] + bob["open_count"]
           == bob["claim_count"] == 5
           and carol["refunded_count"] == 1
           and carol["answered_count"] == 0
           and nov["resolved_count"] == 0)
    record("AC-BCO3", ok3,
           "bob=%r carol=%r nov=%r"
           % ((bob["answered_count"], bob["withdrawn_count"],
               bob["refunded_count"], bob["open_count"]),
              (carol["resolved_count"], carol["refunded_count"]),
              nov["resolved_count"]))

    # -- AC-BCO4 shares over resolved_count, rate over claim_count ---
    ok4 = (bob["answered_share"] == 0.5
           and bob["withdrawn_share"] == 0.25
           and bob["refunded_share"] == 0.25
           and sep["answered_share"] == 0.5
           and sep["withdrawn_share"] == 0.5
           and sep["refunded_share"] == 0.0
           and oct_row["refunded_share"] == 1.0
           and nov["answered_share"] is None
           and nov["withdrawn_share"] is None
           and nov["refunded_share"] is None
           and bob["resolution_rate"] == 0.8
           and carol["resolution_rate"] == 1.0
           and all(
               row["answered_share"]
               == round(float(row["answered_count"])
                        / row["resolved_count"], 4)
               and row["withdrawn_share"]
               == round(float(row["withdrawn_count"])
                        / row["resolved_count"], 4)
               and row["refunded_share"]
               == round(float(row["refunded_count"])
                        / row["resolved_count"], 4)
               for row in bob["months"] if row["resolved_count"])
           and bob["claim_amount"] == 38
           and bob["resolved_claim_amount"] == 34
           and bob["refunded_amount"] == 10
           and sep["refunded_amount"] == 0
           and dec["refunded_amount"] == 0
           and oct_row["resolved_claim_amount"] == 10
           and bob["resolved_claim_amount"]
           == bob["claim_amount"] - 4)
    record("AC-BCO4", ok4,
           "shares=%r rates=%r money=%r"
           % ((bob["answered_share"], bob["withdrawn_share"],
               bob["refunded_share"]),
              (bob["resolution_rate"], carol["resolution_rate"]),
              (bob["claim_amount"], bob["resolved_claim_amount"],
               bob["refunded_amount"])))

    # -- AC-BCO5 pooled latency over closed claims -------------------
    lat_sep_1 = seconds("2026-09-12T11:00:00Z", "2026-09-13T11:00:00Z")
    lat_sep_2 = seconds("2026-09-20T08:00:00Z", "2026-09-25T08:00:00Z")
    lat_oct = seconds("2026-08-05T10:00:00Z", "2026-10-03T08:00:00Z")
    lat_dec = seconds("2026-11-20T09:00:00Z", "2026-12-01T09:00:00Z")
    ok5 = (lat_sep_1 == 86400
           and lat_sep_2 == 432000
           and lat_oct == 5090400
           and lat_dec == 950400
           and sep["fastest_resolve_seconds"] == 86400
           and sep["slowest_resolve_seconds"] == 432000
           and sep["avg_resolve_seconds"] == 259200.0
           and sep["median_resolve_seconds"] == 259200.0
           and oct_row["fastest_resolve_seconds"] == 5090400
           and oct_row["slowest_resolve_seconds"] == 5090400
           and oct_row["avg_resolve_seconds"] == 5090400.0
           and nov["avg_resolve_seconds"] is None
           and nov["median_resolve_seconds"] is None
           and nov["fastest_resolve_seconds"] is None
           and nov["slowest_resolve_seconds"] is None
           and dec["avg_resolve_seconds"] == 950400.0
           and bob["fastest_resolve_seconds"] == 86400
           and bob["slowest_resolve_seconds"] == 5090400
           and bob["avg_resolve_seconds"]
           == round(float(86400 + 432000 + 5090400 + 950400) / 4, 2)
           and bob["median_resolve_seconds"]
           == (432000.0 + 950400.0) / 2.0)
    record("AC-BCO5", ok5,
           "sep=%r oct=%r env=%r"
           % ((sep["avg_resolve_seconds"], sep["median_resolve_seconds"],
               sep["fastest_resolve_seconds"],
               sep["slowest_resolve_seconds"]),
              (oct_row["avg_resolve_seconds"],
               oct_row["fastest_resolve_seconds"]),
              (bob["avg_resolve_seconds"], bob["median_resolve_seconds"],
               bob["fastest_resolve_seconds"],
               bob["slowest_resolve_seconds"])))

    # -- AC-BCO6 grid, zero month, accumulator, peak -----------------
    running = [row["running_resolved_count"] for row in bob["months"]]
    ok6 = (running == [2, 3, 3, 4]
           and bob["month_count"] == 4
           and bob["active_month_count"] == 3
           and nov["running_resolved_count"] == 3
           and nov["resolved_claim_amount"] == 0
           and nov["refunded_amount"] == 0
           and bob["peak_month"] == "2026-09"
           and bob["peak_resolved_count"] == 2
           and bob["first_month"] == "2026-09"
           and bob["last_month"] == "2026-12"
           and bob["latest_month_resolved_count"] == 1
           and carol["peak_month"] == "2026-09"
           and empty["peak_month"] is None
           and empty["peak_resolved_count"] is None)
    record("AC-BCO6", ok6,
           "running=%r peak=%r window=%r"
           % (running,
              (bob["peak_month"], bob["peak_resolved_count"]),
              (bob["first_month"], bob["last_month"],
               bob["latest_month_resolved_count"])))

    # -- AC-BCO7 isolation and cross-face identity -------------------
    opened = am.api_buyer_claim_months("usr:bob")
    ok7 = (bob["claim_count"] == opened["claim_count"]
           and bob["open_count"] == opened["open_count"]
           and bob["answered_count"] == opened["answered_count"]
           and bob["withdrawn_count"] == opened["withdrawn_count"]
           and bob["refunded_count"] == opened["refunded_count"]
           and sum(row["resolved_count"] for row in bob["months"])
           == bob["resolved_count"]
           and sum(row["resolved_claim_amount"]
                   for row in bob["months"])
           == bob["resolved_claim_amount"]
           and sum(row["refunded_amount"] for row in bob["months"])
           == bob["refunded_amount"]
           and sep["resolved_count"] == 2
           and carol["resolved_count"] == 1
           and bob["resolved_count"] + carol["resolved_count"] == 5
           and "2026-08" not in [row["month"] for row in bob["months"]]
           and "2026-09" in [row["month"] for row in bob["months"]])
    record("AC-BCO7", ok7,
           "opened=%r bob=%r sum=%r carol=%r"
           % ((opened["claim_count"], opened["open_count"],
               opened["answered_count"], opened["withdrawn_count"],
               opened["refunded_count"]),
              (bob["claim_count"], bob["open_count"],
               bob["answered_count"], bob["withdrawn_count"],
               bob["refunded_count"]),
              (sum(row["resolved_count"] for row in bob["months"]),
               bob["resolved_count"]),
              carol["resolved_count"]))

    # -- AC-BCO8 gates before any read, purity, wiring, hygiene ------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_forms = ["", "usr", "USR:bob", " usr:bob", "usr :bob",
                 "dev:bob", 123]
    bad_ok = []
    for form in bad_forms:
        try:
            am.api_buyer_claim_outcome_months(form)
            bad_ok.append(False)
        except A.ApiMarketError as err:
            bad_ok.append(err.code == A.E_AM_BAD_ACCOUNT)
    digests_after_gates = market_digests(am)

    call_a = dumps(am.api_buyer_claim_outcome_months("usr:bob"))
    call_b = dumps(am.api_buyer_claim_outcome_months("usr:bob"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                 lobby_cfg)
    call_c = dumps(am2.api_buyer_claim_outcome_months("usr:bob"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                 lobby_cfg)
    call_d = dumps(am3.api_buyer_claim_outcome_months("usr:bob"))
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (all(bad_ok)
           and len(bad_ok) == 7
           and digests_before == digests_after_gates == digests_after
           and tx_before == tx_after
           and call_a == call_b == dumps(bob)
           and call_c == call_d == dumps(bob)
           and call_a != dumps(carol)
           and b'"ledger-apimarket-buyerclaimoutcomemonths"' in recon
           and b"test_apimarket_buyerclaimoutcomemonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-BCO8", ok8,
           "gates=%r digests_same=%r tx_same=%r bytes=%r ascii=%r"
           % (all(bad_ok), digests_before == digests_after,
              tx_before == tx_after, call_c == call_d,
              all(b < 128 for b in test_src)))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
