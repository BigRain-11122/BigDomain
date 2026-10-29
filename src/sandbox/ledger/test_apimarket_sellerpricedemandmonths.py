"""Acceptance suite for the apimarket monthly repricing-response face
(BigDomain R2240; canon = the R2230 seed 6/6 explore claim row,
criteria AC-SPD1..AC-SPD8 registered in that row BEFORE this code
existed).

Face under proof: APIMarketFace.api_seller_price_demand_months.
api_seller_price_cadence_months answers how often a seller reprices,
api_seller_watch_months how much attention arrived and
api_seller_question_months how many pre-sale questions came in, so the
operating question "when interest rose, did I actually move the price"
had no face. This suite pins:

  - the twenty-two-key envelope, the ten-key month rows, the honest
    empty world and the keyword-signature contract;
  - the same-UTC-month join law (each leg books in its own stamp's
    month, an answer is not an event, an earlier month is frozen);
  - the response law (a response month needs a revision AND demand, a
    demand month needs a positive watch delta or a question, and the
    rate is None rather than a fabricated zero when no demand exists);
  - the contiguous UNION grid with an honest zero month and a flat
    running accumulator;
  - strict seller isolation and the seller partition of the market
    totals;
  - the market benchmark (never itself) and the earlier-month peak
    tie-break;
  - identity against all three source faces;
  - the eight-form account gate before any read, the bare prefix
    reading honestly empty, purity, three-instance byte identity, the
    wiring and the ASCII/LF hygiene.

Usage: python test_apimarket_sellerpricedemandmonths.py
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
    "revision_count", "up_count", "down_count", "watch_count",
    "unwatch_count", "watch_net_count", "question_count",
    "response_month_count", "demand_month_count", "response_rate",
    "peak_revision_month", "peak_revision_count",
    "market_response_rate", "latest_month_revision_count",
    "first_month", "last_month", "months", "disclaimer"}

ROW_KEYS = {
    "month", "revision_count", "up_count", "down_count", "net_count",
    "watch_count", "unwatch_count", "watch_net_count",
    "question_count", "running_revision"}


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
    the grid must start at the first EVENT month, never at September.

    t1 dana base 80, t2 lia base 200, t3 gina base 50.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SPD-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SPD-S",
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


def october(am, clock, ids):
    """OCTOBER: dana reprices 80 -> 100 (+25, up) while buyer1 watches
    and asks on t1; lia reprices 200 -> 160 (-20, down) with no
    demand on her shelf. So October is the market's response month.
    """
    clock.value = "2026-10-02T00:00:00Z"
    am.revise_price("usr:dana", ids["t1"], 100)
    clock.value = "2026-10-08T00:00:00Z"
    am.revise_price("usr:lia", ids["t2"], 160)
    clock.value = "2026-10-05T00:00:00Z"
    am.watch_api("usr:buyer1", ids["t1"])
    clock.value = "2026-10-06T00:00:00Z"
    am.ask_question("usr:buyer1", ids["t1"], "does it cover tools")


def november(am, clock, ids):
    """NOVEMBER: gina reprices twice (50 -> 40, 40 -> 50) with no
    demand at all, buyer2 watches lia's t2 and buyer1 unwatches dana's
    t1. The market watch delta nets to zero, so November is honestly
    NOT a demand month even though attention moved.
    """
    clock.value = "2026-11-02T00:00:00Z"
    am.revise_price("usr:gina", ids["t3"], 40)
    clock.value = "2026-11-18T00:00:00Z"
    am.revise_price("usr:gina", ids["t3"], 50)
    clock.value = "2026-11-11T00:00:00Z"
    am.watch_api("usr:buyer2", ids["t2"])
    clock.value = "2026-11-20T00:00:00Z"
    am.unwatch_api("usr:buyer1", ids["t1"])


def december(am, clock, ids):
    """DECEMBER: buyer3 asks on gina's t3 and nobody reprices, so
    December is a demand month WITHOUT a response."""
    clock.value = "2026-12-05T00:00:00Z"
    am.ask_question("usr:buyer3", ids["t3"], "is there a trial")


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerpricedemand-")
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

    # -- AC-SPD1 the contract, honest empty first, keyword signature --
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-spd-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_price_demand_months()
    close_stack(e_am, e_dk, e_metered, e_led)

    published_only = am.api_seller_price_demand_months()
    signature_ok = False
    try:
        am.api_seller_price_demand_months(bogus=1)
    except TypeError:
        signature_ok = True
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for row in published_only["months"])
    ok1 = (set(empty.keys()) == ENVELOPE_KEYS
           and set(published_only.keys()) == ENVELOPE_KEYS
           and rows_ok
           and len(empty) == 22
           and empty["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["active_month_count"] == 0
           and empty["months"] == []
           and empty["revision_count"] == 0
           and empty["up_count"] == 0
           and empty["down_count"] == 0
           and empty["watch_count"] == 0
           and empty["unwatch_count"] == 0
           and empty["watch_net_count"] == 0
           and empty["question_count"] == 0
           and empty["response_month_count"] == 0
           and empty["demand_month_count"] == 0
           and empty["response_rate"] is None
           and empty["peak_revision_month"] is None
           and empty["peak_revision_count"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_revision_count"] is None
           and empty["market_response_rate"] is None
           and empty["scope"] == "market"
           and published_only["months"] == []
           and published_only["revision_count"] == 0
           and signature_ok)
    record("AC-SPD1", ok1,
           "env_keys=%d exact=%r rows=%r len=%d empty=%r"
           " published_only=%r sig=%r"
           % (len(empty), set(empty.keys()) == ENVELOPE_KEYS, rows_ok,
              len(empty),
              (empty["month_count"], empty["response_rate"],
               empty["months"]), published_only["revision_count"],
              signature_ok))

    # -- AC-SPD2 same-month join, the earlier month frozen ------------
    october(am, _CLOCK, ids)
    oct_only = am.api_seller_price_demand_months()
    oct_row_a = month_row(oct_only, "2026-10")
    dana_oct_only = am.api_seller_price_demand_months("usr:dana")
    november(am, _CLOCK, ids)
    december(am, _CLOCK, ids)
    env = am.api_seller_price_demand_months()
    oct_row_b = month_row(env, "2026-10")
    dana = am.api_seller_price_demand_months("usr:dana")
    dana_oct = month_row(dana, "2026-10")
    dec_row = month_row(env, "2026-12")
    ok2 = (oct_only["first_month"] == "2026-10"
           and oct_only["last_month"] == "2026-10"
           and oct_row_a["revision_count"] == 2
           and oct_row_a["watch_count"] == 1
           and oct_row_a["question_count"] == 1
           and dumps(oct_row_a) == dumps(oct_row_b)
           and dumps(month_row(dana_oct_only, "2026-10")) == dumps(dana_oct)
           and dec_row["revision_count"] == 0
           and dec_row["question_count"] == 1
           and dec_row["watch_count"] == 0
           and dec_row["watch_net_count"] == 0)
    record("AC-SPD2", ok2,
           "octTwin=%r octNow=%r danaFrozen=%r dec=%r"
           % ((oct_row_a["revision_count"], oct_row_a["watch_count"],
               oct_row_a["question_count"]),
              (oct_row_b["revision_count"], oct_row_b["watch_count"],
               oct_row_b["question_count"]),
              dumps(month_row(dana_oct_only, "2026-10")) == dumps(dana_oct),
              (dec_row["revision_count"], dec_row["question_count"])))

    # -- AC-SPD3 the response law and the honest None rate ------------
    nov_row = month_row(env, "2026-11")
    lia = am.api_seller_price_demand_months("usr:lia")
    gina = am.api_seller_price_demand_months("usr:gina")
    ok3 = (env["demand_month_count"] == 2
           and env["response_month_count"] == 1
           and env["response_rate"] == 0.5
           and nov_row["watch_count"] == 1
           and nov_row["unwatch_count"] == 1
           and nov_row["watch_net_count"] == 0
           and nov_row["revision_count"] == 2
           and dana["demand_month_count"] == 1
           and dana["response_month_count"] == 1
           and dana["response_rate"] == 1.0
           and lia["demand_month_count"] == 1
           and lia["response_month_count"] == 0
           and lia["response_rate"] == 0.0
           and gina["demand_month_count"] == 1
           and gina["response_month_count"] == 0
           and gina["response_rate"] == 0.0
           and empty["response_rate"] is None)
    record("AC-SPD3", ok3,
           "market=%r nov=%r dana=%r lia=%r gina=%r"
           % ((env["response_month_count"], env["demand_month_count"],
               env["response_rate"]),
              (nov_row["watch_net_count"], nov_row["revision_count"]),
              dana["response_rate"], lia["response_rate"],
              gina["response_rate"]))

    # -- AC-SPD4 the contiguous UNION grid and the running row -------
    market_grid = [row["month"] for row in env["months"]]
    dana_grid = [row["month"] for row in dana["months"]]
    running = [row["running_revision"] for row in env["months"]]
    nets = [row["net_count"] for row in env["months"]]
    watch_nets = [row["watch_net_count"] for row in env["months"]]
    monotone = all(running[i] <= running[i + 1]
                   for i in range(len(running) - 1))
    sum_rows = sum(row["revision_count"] for row in env["months"])
    ok4 = (market_grid == ["2026-10", "2026-11", "2026-12"]
           and dana_grid == ["2026-10", "2026-11"]
           and nets == [0, 0, 0]
           and watch_nets == [1, 0, 0]
           and running == [2, 4, 4]
           and monotone
           and running[-1] == env["revision_count"] == sum_rows == 4
           and sum(row["up_count"] for row in env["months"]) == 2
           and sum(row["down_count"] for row in env["months"]) == 2
           and all(row["up_count"] + row["down_count"]
                   == row["revision_count"] for row in env["months"])
           and all(row["watch_net_count"] == row["watch_count"]
                   - row["unwatch_count"] for row in env["months"])
           and month_row(env, "2026-12")["running_revision"] == 4
           and env["active_month_count"] == 2)
    record("AC-SPD4", ok4,
           "grid=%r dana_grid=%r nets=%r watch_nets=%r running=%r"
           " active=%r"
           % (market_grid, dana_grid, nets, watch_nets, running,
              env["active_month_count"]))

    # -- AC-SPD5 strict seller isolation and the partition -----------
    dana_nov = month_row(dana, "2026-11")
    lia_dec_absent = "2026-12" not in [row["month"]
                                       for row in lia["months"]]
    gina_nov = month_row(gina, "2026-11")
    ok5 = (dana["revision_count"] + lia["revision_count"] \
           + gina["revision_count"] == env["revision_count"] == 4
           and dana["watch_count"] + lia["watch_count"] \
           + gina["watch_count"] == env["watch_count"] == 2
           and dana["unwatch_count"] + lia["unwatch_count"] \
           + gina["unwatch_count"] == env["unwatch_count"] == 1
           and dana["question_count"] + lia["question_count"] \
           + gina["question_count"] == env["question_count"] == 2
           and dana["question_count"] == 1
           and dana_nov["question_count"] == 0
           and dana_nov["watch_net_count"] == -1
           and lia["question_count"] == 0
           and lia_dec_absent
           and gina_nov["watch_count"] == 0
           and gina_nov["question_count"] == 0
           and gina["question_count"] == 1
           and gina["scope"] == "seller"
           and gina["dev_account"] == "usr:gina")
    record("AC-SPD5", ok5,
           "partition=%r/%r/%r/%r dana_nov=%r gina_nov=%r lia_dec=%r"
           % ((dana["revision_count"], lia["revision_count"],
               gina["revision_count"]),
              (dana["watch_count"], lia["watch_count"],
               gina["watch_count"]),
              (dana["unwatch_count"], lia["unwatch_count"],
               gina["unwatch_count"]),
              (dana["question_count"], lia["question_count"],
               gina["question_count"]),
              (dana_nov["watch_net_count"],
               dana_nov["question_count"]),
              (gina_nov["watch_count"], gina_nov["question_count"]),
              lia_dec_absent))

    # -- AC-SPD6 market benchmark and the earlier peak ---------------
    ok6 = (env["scope"] == "market"
           and env["market_response_rate"] is None
           and env["dev_account"] is None
           and env["peak_revision_month"] == "2026-10"
           and env["peak_revision_count"] == 2
           and dana["market_response_rate"] == env["response_rate"] == 0.5
           and lia["market_response_rate"] == 0.5
           and gina["market_response_rate"] == 0.5
           and dana["peak_revision_month"] == "2026-10"
           and dana["peak_revision_count"] == 1
           and lia["peak_revision_month"] == "2026-10"
           and lia["peak_revision_count"] == 1
           and gina["peak_revision_month"] == "2026-11"
           and gina["peak_revision_count"] == 2
           and env["latest_month_revision_count"] == 0
           and gina["latest_month_revision_count"] == 0
           and month_row(gina, "2026-11")["running_revision"] == 2)
    record("AC-SPD6", ok6,
           "market_peak=%r rates=%r gina_peak=%r latest=%r"
           % ((env["peak_revision_month"], env["peak_revision_count"]),
              (env["market_response_rate"], dana["market_response_rate"],
               gina["market_response_rate"]),
              (gina["peak_revision_month"], gina["peak_revision_count"]),
              env["latest_month_revision_count"]))

    # -- AC-SPD7 identity against all three source faces -------------
    cadence = am.api_seller_price_cadence_months()
    cadence_dana = am.api_seller_price_cadence_months("usr:dana")
    watch_face = am.api_seller_watch_months()
    watch_dana = am.api_seller_watch_months("usr:dana")
    question_market = am.api_market_question_months()
    question_dana = am.api_seller_question_months("usr:dana")
    question_gina = am.api_seller_question_months("usr:gina")
    window_ok = True
    for month in ("2026-10", "2026-11"):
        window_ok = window_ok and (
            month_row(env, month)["revision_count"]
            == month_row(cadence, month)["revision_count"])
    dana_window_ok = (
        month_row(dana, "2026-10")["revision_count"]
        == month_row(cadence_dana, "2026-10")["revision_count"])
    ok7 = (env["revision_count"] == cadence["revision_count"] == 4
           and env["up_count"] == cadence["up_count"] == 2
           and env["down_count"] == cadence["down_count"] == 2
           and dana["revision_count"] == cadence_dana["revision_count"]
           and env["watch_count"] == watch_face["watch_count"] == 2
           and env["unwatch_count"] == watch_face["unwatch_count"] == 1
           and dana["watch_count"] == watch_dana["watch_count"] == 1
           and dana["unwatch_count"] == watch_dana["unwatch_count"] == 1
           and env["question_count"] == question_market["question_count"] \
           == 2
           and dana["question_count"] == question_dana["question_count"]
           == 1
           and gina["question_count"] == question_gina["question_count"]
           == 1
           and window_ok
           and dana_window_ok)
    record("AC-SPD7", ok7,
           "cadence=%r watch=%r questions=%r window=%r dana_window=%r"
           % ((env["revision_count"], cadence["revision_count"],
               env["up_count"], cadence["up_count"]),
              (env["watch_count"], watch_face["watch_count"],
               env["unwatch_count"], watch_face["unwatch_count"]),
              (env["question_count"], question_market["question_count"],
               dana["question_count"],
               question_dana["question_count"]),
              window_ok, dana_window_ok))

    # -- AC-SPD8 gates, purity, hygiene and wiring -------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad = [None, "", "   ", 123, ["usr:x"], {"a": 1}, "usr", b"usr:x"]
    bad_ok = []
    for form in bad[1:]:
        try:
            am.api_seller_price_demand_months(form)
            bad_ok.append(False)
        except A.ApiMarketError as err:
            bad_ok.append(err.code == A.E_AM_BAD_ACCOUNT)
    bare = am.api_seller_price_demand_months("usr:")
    digests_after_gates = market_digests(am)

    call_a = dumps(am.api_seller_price_demand_months())
    call_b = dumps(am.api_seller_price_demand_months())
    call_c = dumps(am.api_seller_price_demand_months("usr:gina"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg, lobby_cfg)
    restart_a = dumps(am2.api_seller_price_demand_months())
    restart_b = dumps(am2.api_seller_price_demand_months("usr:gina"))
    restart_c = dumps(am2.api_seller_price_demand_months("usr:"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg, lobby_cfg)
    restart_d = dumps(am3.api_seller_price_demand_months())
    restart_e = dumps(am3.api_seller_price_demand_months("usr:gina"))
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
           and bare["market_response_rate"] == 0.5
           and digests_before == digests_after_gates == digests_after
           and tx_before == tx_after
           and call_a == call_b == restart_a == restart_d == dumps(env)
           and call_c == restart_b == restart_e == dumps(gina)
           and restart_c == dumps(bare)
           and call_a != call_c
           and b'"ledger-apimarket-sellerpricedemandmonths"' in recon
           and b"test_apimarket_sellerpricedemandmonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-SPD8", ok8,
           "gates=%r bare=%r digests_same=%r tables=%d tx_same=%r"
           " restart=%r wired=%r ascii=%r"
           % (all(bad_ok),
              (bare["month_count"], bare["revision_count"],
               bare["market_response_rate"]),
              digests_before == digests_after, len(digests_before),
              tx_before == tx_after,
              (call_c == restart_b == restart_e,
               call_a == restart_a == restart_d),
              b'"ledger-apimarket-sellerpricedemandmonths"' in recon,
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