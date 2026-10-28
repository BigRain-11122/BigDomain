"""Acceptance suite for the apimarket monthly repricing cadence face
(BigDomain R2201; canon = the R2189 seed 10/10 explore claim row,
criteria AC-SPC1..AC-SPC8 registered in that row BEFORE this code
existed).

Face under proof: APIMarketFace.api_seller_price_cadence_months.
api_price_volatility answers lifetime repricing magnitude and
api_price_step_distribution answers the lifetime band shape, so the time
axis of repricing - a seller that reprices twelve times in one month and
then goes silent reads exactly like one that adjusts once a month - had
no face. This suite pins:

  - the seventeen-key envelope, the nine-key month rows, the honest
    empty world and the keyword-signature contract;
  - the step attribution law (a revision's step is measured against the
    price that was actually live, and a later revision never rewrites
    the step an earlier month already measured);
  - the contiguous month grid with an honest zero month whose monthly
    average is None rather than a fabricated zero;
  - conservation of revisions, of the up/down split, and the disclosed
    distinct-vs-sum asymmetry of the participant counts;
  - the signed net and the monotone running accumulator;
  - the pooled magnitude law, which the mean-of-monthly-means would
    answer differently (30.0 pooled against 29.1667 averaged);
  - the scope law (market never benchmarks itself, a seller scope
    carries the market-wide pooled average by the same law, sellers
    never leak) and the peak tie-break toward the earlier month;
  - the eight-form account gate before any read, the bare prefix
    reading honestly empty, and the pure-read law;
  - cross-instance byte identity, the wiring and the ASCII/LF hygiene.

Usage: python test_apimarket_sellerpricecadencemonths.py
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
    "dev_account", "scope", "month_count", "active_month_count",
    "revision_count", "up_count", "down_count", "listing_count",
    "seller_count", "avg_abs_step_pct", "peak_month",
    "peak_revision_count", "first_month", "last_month",
    "latest_month_revision_count", "market_avg_abs_step_pct",
    "disclaimer", "months"}

ROW_KEYS = {
    "month", "revision_count", "up_count", "down_count", "net_count",
    "listing_count", "seller_count", "avg_abs_step_pct",
    "running_revision"}


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set
    before each write so the month buckets are reproducible."""

    def __init__(self):
        self.value = "2026-09-10T00:00:00Z"

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


def publish_world(led, dk, am, clock):
    """Three sellers, one listing each, all declared in SEPTEMBER so
    September never carries a revision and the grid must start at the
    first repricing month.

    t1 dana base 80, t2 lia base 200, t3 gina base 50.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SPC-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SPC-S",
                     "settlement")
    for dev in ("dana", "lia", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    clock.value = "2026-09-10T00:00:00Z"
    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 80, False,
                        category="tools")["listing_id"]
    clock.value = "2026-09-15T00:00:00Z"
    t2 = am.publish_api("usr:lia", "t2", "Lia Data API",
                        "lia data payloads", PAYLOAD, 200, False,
                        category="data")["listing_id"]
    clock.value = "2026-09-20T00:00:00Z"
    t3 = am.publish_api("usr:gina", "t3", "Gina Data API",
                        "gina data payloads", PAYLOAD, 50, False,
                        category="data")["listing_id"]
    return {"t1": t1, "t2": t2, "t3": t3}


def reprice_october(am, clock, ids):
    """OCTOBER: t1 twice (80 -> 100 = +25.00, 100 -> 95 = -5.00) and
    t2 once (200 -> 160 = -20.00)."""
    clock.value = "2026-10-02T00:00:00Z"
    am.revise_price("usr:dana", ids["t1"], 100)
    clock.value = "2026-10-20T00:00:00Z"
    am.revise_price("usr:dana", ids["t1"], 95)
    clock.value = "2026-10-08T00:00:00Z"
    am.revise_price("usr:lia", ids["t2"], 160)


def reprice_later(am, clock, ids):
    """NOVEMBER: t1 95 -> 190 = +100.00; t3 50 -> 40 = -20.00 and then
    40 -> 50 = +25.00. DECEMBER: t2 160 -> 200 = +25.00 (measured from
    the OCTOBER price, never from the base) and t3 50 -> 40 = -20.00."""
    clock.value = "2026-11-10T00:00:00Z"
    am.revise_price("usr:dana", ids["t1"], 190)
    clock.value = "2026-11-02T00:00:00Z"
    am.revise_price("usr:gina", ids["t3"], 40)
    clock.value = "2026-11-18T00:00:00Z"
    am.revise_price("usr:gina", ids["t3"], 50)
    clock.value = "2026-12-05T00:00:00Z"
    am.revise_price("usr:lia", ids["t2"], 200)
    clock.value = "2026-12-09T00:00:00Z"
    am.revise_price("usr:gina", ids["t3"], 40)


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerpricecadence-")
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
    ids = publish_world(led, dk, am, _CLOCK)

    # -- AC-SPC1 the contract, honest empty first, keyword signature --
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-spc-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_price_cadence_months()
    close_stack(e_am, e_dk, e_metered, e_led)

    no_revision = am.api_seller_price_cadence_months()
    signature_ok = False
    try:
        am.api_seller_price_cadence_months(bogus=1)
    except TypeError:
        signature_ok = True
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for row in no_revision["months"])
    ok1 = (set(empty.keys()) == ENVELOPE_KEYS
           and set(no_revision.keys()) == ENVELOPE_KEYS
           and rows_ok
           and empty["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["active_month_count"] == 0
           and empty["months"] == []
           and empty["revision_count"] == 0
           and empty["up_count"] == 0
           and empty["down_count"] == 0
           and empty["listing_count"] == 0
           and empty["seller_count"] == 0
           and empty["avg_abs_step_pct"] is None
           and empty["peak_month"] is None
           and empty["peak_revision_count"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_revision_count"] is None
           and empty["market_avg_abs_step_pct"] is None
           and empty["scope"] == "market"
           and no_revision["months"] == []
           and no_revision["revision_count"] == 0
           and signature_ok)
    record("AC-SPC1", ok1,
           "env_keys=%d exact=%r rows=%d empty=%r published_only=%r sig=%r"
           % (len(empty), set(empty.keys()) == ENVELOPE_KEYS,
              len(no_revision["months"]),
              (empty["month_count"], empty["avg_abs_step_pct"],
               empty["peak_month"]), no_revision["revision_count"],
              signature_ok))

    # -- AC-SPC2 step attribution, frozen earlier months --------------
    reprice_october(am, _CLOCK, ids)
    oct_only = am.api_seller_price_cadence_months()
    oct_row_a = month_row(oct_only, "2026-10")
    reprice_later(am, _CLOCK, ids)
    env = am.api_seller_price_cadence_months()
    oct_row_b = month_row(env, "2026-10")
    dec_row = month_row(env, "2026-12")
    ok2 = (oct_only["first_month"] == "2026-10"
           and oct_only["last_month"] == "2026-10"
           and oct_only["revision_count"] == 3
           and oct_row_a["revision_count"] == 3
           and oct_row_a["up_count"] == 1
           and oct_row_a["down_count"] == 2
           and oct_row_a["avg_abs_step_pct"] == 16.67
           and dumps(oct_row_a) == dumps(oct_row_b)
           and dec_row["revision_count"] == 2
           and dec_row["up_count"] == 1
           and dec_row["down_count"] == 1
           and dec_row["avg_abs_step_pct"] == 22.5)
    record("AC-SPC2", ok2,
           "octTwin=%r octNow=%r dec=%r frozen=%r"
           % ((oct_row_a["revision_count"], oct_row_a["up_count"],
               oct_row_a["down_count"], oct_row_a["avg_abs_step_pct"]),
              (oct_row_b["revision_count"], oct_row_b["up_count"],
               oct_row_b["down_count"], oct_row_b["avg_abs_step_pct"]),
              (dec_row["revision_count"], dec_row["avg_abs_step_pct"]),
              dumps(oct_row_a) == dumps(oct_row_b)))

    # -- AC-SPC3 contiguous grid and the honest zero month -----------
    lia = am.api_seller_price_cadence_months("usr:lia")
    lia_grid = [row["month"] for row in lia["months"]]
    lia_nov = month_row(lia, "2026-11")
    market_grid = [row["month"] for row in env["months"]]
    ok3 = (market_grid == ["2026-10", "2026-11", "2026-12"]
           and lia_grid == ["2026-10", "2026-11", "2026-12"]
           and lia_nov["revision_count"] == 0
           and lia_nov["up_count"] == 0
           and lia_nov["down_count"] == 0
           and lia_nov["net_count"] == 0
           and lia_nov["listing_count"] == 0
           and lia_nov["seller_count"] == 0
           and lia_nov["avg_abs_step_pct"] is None
           and lia_nov["running_revision"] == 1
           and lia["active_month_count"] == 2
           and lia["month_count"] == 3)
    record("AC-SPC3", ok3,
           "market_grid=%r lia_grid=%r lia_nov=%r active=%r"
           % (market_grid, lia_grid,
              (lia_nov["revision_count"], lia_nov["avg_abs_step_pct"],
               lia_nov["running_revision"]), lia["active_month_count"]))

    # -- AC-SPC4 conservation and the distinct-vs-sum asymmetry ------
    conn = sqlite3.connect(am.db_path)
    raw_revisions = conn.execute(
        "SELECT COUNT(*) FROM apimarket_price_revisions").fetchone()[0]
    conn.close()
    sum_rows = sum(row["revision_count"] for row in env["months"])
    sum_up = sum(row["up_count"] for row in env["months"])
    sum_down = sum(row["down_count"] for row in env["months"])
    rows_split_ok = all(row["up_count"] + row["down_count"]
                        == row["revision_count"]
                        for row in env["months"])
    listing_sum = sum(row["listing_count"] for row in env["months"])
    seller_sum = sum(row["seller_count"] for row in env["months"])
    ok4 = (sum_rows == env["revision_count"] == raw_revisions == 8
           and sum_up == env["up_count"] == 4
           and sum_down == env["down_count"] == 4
           and rows_split_ok
           and env["listing_count"] == 3
           and env["seller_count"] == 3
           and listing_sum == 6
           and seller_sum == 6
           and env["listing_count"] < listing_sum
           and env["seller_count"] < seller_sum)
    record("AC-SPC4", ok4,
           "sums=%r/%r raw=%r split=%r distinct=%r rowsum=%r"
           % (sum_rows, env["revision_count"], raw_revisions,
              rows_split_ok,
              (env["listing_count"], env["seller_count"]),
              (listing_sum, seller_sum)))

    # -- AC-SPC5 signed net and the running accumulator --------------
    nets = [row["net_count"] for row in env["months"]]
    running = [row["running_revision"] for row in env["months"]]
    net_ok = all(row["net_count"] == row["up_count"] - row["down_count"]
                 for row in env["months"])
    monotone = all(running[i] <= running[i + 1]
                   for i in range(len(running) - 1))
    ok5 = (nets == [-1, 1, 0]
           and net_ok
           and running == [3, 6, 8]
           and monotone
           and running[-1] == env["revision_count"] == 8
           and sum(nets) == 0
           and env["up_count"] - env["down_count"] == 0
           and month_row(env, "2026-10")["net_count"] < 0)
    record("AC-SPC5", ok5,
           "nets=%r running=%r monotone=%r total=%r"
           % (nets, running, monotone, env["revision_count"]))

    # -- AC-SPC6 pooled magnitude, never a mean of month means -------
    step_sum = 25.0 + 5.0 + 20.0 + 100.0 + 20.0 + 25.0 + 25.0 + 20.0
    pooled = round(step_sum / 8.0, 2)
    month_means = [row["avg_abs_step_pct"] for row in env["months"]]
    averaged = round(sum(month_means) / len(month_means), 2)
    ok6 = (env["avg_abs_step_pct"] == pooled == 30.0
           and month_means == [16.67, 48.33, 22.5]
           and averaged == 29.17
           and env["avg_abs_step_pct"] != averaged
           and month_row(env, "2026-11")["avg_abs_step_pct"] == 48.33
           and am.api_seller_price_cadence_months("usr:gina")[
               "avg_abs_step_pct"] == 21.67
           and am.api_seller_price_cadence_months("usr:dana")[
               "avg_abs_step_pct"] == 43.33)
    record("AC-SPC6", ok6,
           "pooled=%r month_means=%r mean_of_means=%r gina=%r dana=%r"
           % (env["avg_abs_step_pct"], month_means, averaged,
              am.api_seller_price_cadence_months("usr:gina")[
                  "avg_abs_step_pct"],
              am.api_seller_price_cadence_months("usr:dana")[
                  "avg_abs_step_pct"]))

    # -- AC-SPC7 scope law and the peak tie-break --------------------
    dana = am.api_seller_price_cadence_months("usr:dana")
    gina = am.api_seller_price_cadence_months("usr:gina")
    dana_months = [row["month"] for row in dana["months"]]
    gina_months = [row["month"] for row in gina["months"]]
    ok7 = (env["scope"] == "market"
           and env["market_avg_abs_step_pct"] is None
           and env["peak_month"] == "2026-10"
           and env["peak_revision_count"] == 3
           and lia["scope"] == "seller"
           and lia["market_avg_abs_step_pct"] == env["avg_abs_step_pct"]
           and dana["market_avg_abs_step_pct"] == env["avg_abs_step_pct"]
           and dana["peak_month"] == "2026-10"
           and dana["peak_revision_count"] == 2
           and dana["revision_count"] == 3
           and dana["listing_count"] == 1
           and dana["seller_count"] == 1
           and dana_months == ["2026-10", "2026-11"]
           and gina["revision_count"] == 3
           and gina["peak_month"] == "2026-11"
           and gina["peak_revision_count"] == 2
           and gina["months"][-1]["revision_count"] == 1
           and gina_months == ["2026-11", "2026-12"]
           and lia["peak_month"] == "2026-10"
           and lia["peak_revision_count"] == 1
           and dana["revision_count"] + lia["revision_count"] \
           + gina["revision_count"] == env["revision_count"])
    record("AC-SPC7", ok7,
           "peak=%r market_avg=%r lia=%r dana=%r gina=%r scopesum=%r"
           % ((env["peak_month"], env["peak_revision_count"]),
              (env["market_avg_abs_step_pct"],
               lia["market_avg_abs_step_pct"]),
              (lia["peak_month"], lia["peak_revision_count"]),
              (dana["peak_month"], dana["peak_revision_count"],
               dana["revision_count"]),
              (gina["peak_month"], gina["peak_revision_count"],
               gina["revision_count"]),
              dana["revision_count"] + lia["revision_count"]
              + gina["revision_count"]))

    # -- AC-SPC8 gates, purity, hygiene and wiring -------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad = [None, "", "   ", 123, ["usr:x"], {"a": 1}, "usr", b"usr:x"]
    bad_ok = []
    for form in bad[1:]:
        try:
            am.api_seller_price_cadence_months(form)
            bad_ok.append(False)
        except A.ApiMarketError as err:
            bad_ok.append(err.code == A.E_AM_BAD_ACCOUNT)
    bare = am.api_seller_price_cadence_months("usr:")
    digests_after_gates = market_digests(am)

    call_a = dumps(am.api_seller_price_cadence_months())
    call_b = dumps(am.api_seller_price_cadence_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg, lobby_cfg)
    call_c = dumps(am2.api_seller_price_cadence_months("usr:dana"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg, lobby_cfg)
    call_d = dumps(am3.api_seller_price_cadence_months("usr:dana"))
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (all(bad_ok)
           and bare["month_count"] == 0
           and bare["revision_count"] == 0
           and bare["months"] == []
           and bare["scope"] == "seller"
           and digests_before == digests_after_gates == digests_after
           and tx_before == tx_after
           and call_a == call_b == dumps(env)
           and call_c == call_d == dumps(dana)
           and call_a != call_c
           and b'"ledger-apimarket-sellerpricecadencemonths"' in recon
           and b"test_apimarket_sellerpricecadencemonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-SPC8", ok8,
           "gates=%r bare=%r digests_same=%r tables=%d tx_same=%r"
           " bytes=%r wired=%r ascii=%r"
           % (all(bad_ok),
              (bare["month_count"], bare["revision_count"]),
              digests_before == digests_after, len(digests_before),
              tx_before == tx_after, call_c == call_d,
              b'"ledger-apimarket-sellerpricecadencemonths"' in recon,
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