"""Acceptance suite for the market-wide monthly watch-to-purchase
conversion face (BigDomain R2219; canon = the R2213 explore-queue seed
row claimed in R2219, criteria AC-MCV1..AC-MCV8 registered in that row
BEFORE this code existed).

Face under proof: APIMarketFace.api_market_conversion_months.
api_watch_conversion answers a LIFETIME funnel over the LIVE watch set
and api_market_watch_months answers watch flow, so whether one month's
attention actually turned into sales had no face. This suite pins:

  - the fifteen-key envelope, the eleven-key month rows and the
    honest empty world (no account key at all: the face has no scope
    argument);
  - the booking law: a watch books ONLY in the month of its own
    watched_utc, an unwatch never moves or deletes a booked month (the
    disclosed asymmetry against the live-set funnel face) and a
    purchase never re-dates the watch month;
  - the directional law: converted at or after the watch stamp (an
    equal stamp converts at zero seconds), pre_owned when the purchase
    predates the watch and pending when nothing was bought or the
    purchase was refunded;
  - the contiguous grid with an honest zero month, and the counter
    conservation per row and in the envelope;
  - the pooled rate and latency law (the envelope average is pooled
    over converted watches, never the mean of the month means);
  - the refund law: a refund returns a converted watch to pending in
    the same step while the month keys stay byte-identical;
  - the pure-read law with frozen table digests and a constant
    ledger_tx set, and the no-argument surface;
  - cross-instance byte identity over two full-stack restarts,
    wiring and ASCII/LF hygiene.

Usage: python test_apimarket_marketconversionmonths.py
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
import apimarket_report as RPT        # noqa: E402 (config loader)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apimarket_report.py"),
    os.path.join(BASE, "apidev.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

ENVELOPE_KEYS = {
    "month_count", "first_month", "last_month", "watch_count",
    "pre_owned_count", "funnel_count", "converted_count",
    "pending_count", "conversion_rate", "avg_convert_seconds",
    "median_convert_seconds", "fastest_convert_seconds",
    "slowest_convert_seconds", "disclaimer", "months"}

ROW_KEYS = {
    "month", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate",
    "avg_convert_seconds", "median_convert_seconds",
    "fastest_convert_seconds", "slowest_convert_seconds"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_questions", "apimarket_answers",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_rating_replies", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")

DAY = 86400


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set
    before each write so the month buckets are reproducible."""

    def __init__(self):
        self.value = "2026-01-01T00:00:00Z"

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
    """Two sellers, seven residents. JAN carries four watches (one
    converted with a three-day wait, one converting at the same
    instant in zero seconds, one pending forever and one pre-owned).
    FEB carries no watch at all - the honest zero row. MAR carries
    four watches (two convert, one is withdrawn and stays pending,
    one converts and is later refunded in APR, so the refund moves the
    MARCH cohort without inventing an APR row)."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-MCV-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-MCV-S",
                     "settlement")
    for dev in ("dana", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)
    for who in ("bo", "cy", "di", "ed", "fi", "gi", "ha", "iv"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)

    clock.value = "2026-01-01T00:00:00Z"
    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    d1 = am.publish_api("usr:dana", "d1", "Dana Data API",
                        "dana data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    # -- JAN: four watches, three funnel legs ---------------------
    clock.value = "2026-01-02T00:00:00Z"
    am.watch_api("usr:bo", t1)
    clock.value = "2026-01-05T00:00:00Z"
    p_bo = am.purchase_api("usr:bo", t1, "BUY-MCV-1")["purchase_id"]

    clock.value = "2026-01-03T00:00:00Z"
    am.watch_api("usr:cy", t1)
    p_cy = am.purchase_api("usr:cy", t1, "BUY-MCV-2")["purchase_id"]

    clock.value = "2026-01-10T00:00:00Z"
    am.watch_api("usr:di", g1)

    clock.value = "2026-01-15T00:00:00Z"
    p_ed = am.purchase_api("usr:ed", t1, "BUY-MCV-3")["purchase_id"]
    clock.value = "2026-01-20T00:00:00Z"
    am.watch_api("usr:ed", t1)

    # -- FEB: no watch at all (honest zero row) --------------------
    clock.value = "2026-02-10T00:00:00Z"
    am.api_market_watch_months()

    # -- MAR: four watches, one withdrawn, one refunded later -----
    clock.value = "2026-03-01T00:00:00Z"
    am.watch_api("usr:fi", g1)
    clock.value = "2026-03-04T00:00:00Z"
    p_fi = am.purchase_api("usr:fi", g1, "BUY-MCV-4")["purchase_id"]

    clock.value = "2026-03-02T00:00:00Z"
    am.watch_api("usr:gi", g1)
    clock.value = "2026-03-05T00:00:00Z"
    am.unwatch_api("usr:gi", g1)

    clock.value = "2026-03-06T00:00:00Z"
    am.watch_api("usr:ha", d1)
    clock.value = "2026-03-07T00:00:00Z"
    p_ha = am.purchase_api("usr:ha", d1, "BUY-MCV-5")["purchase_id"]

    clock.value = "2026-03-02T00:00:00Z"
    am.watch_api("usr:iv", d1)
    clock.value = "2026-03-30T00:00:00Z"
    p_iv = am.purchase_api("usr:iv", d1, "BUY-MCV-6")["purchase_id"]

    return {"t1": t1, "d1": d1, "g1": g1,
            "p_bo": p_bo, "p_cy": p_cy, "p_ed": p_ed,
            "p_fi": p_fi, "p_ha": p_ha, "p_iv": p_iv}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-marketconversionmonths-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}
    cfg, lobby_cfg = RPT.load_configs()

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

    # -- AC-MCV1 the contract and the honest empty world ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-mcv-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_conversion_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_market_conversion_months()
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
           and env["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["watch_count"] == 0
           and empty["pre_owned_count"] == 0
           and empty["funnel_count"] == 0
           and empty["converted_count"] == 0
           and empty["pending_count"] == 0
           and empty["conversion_rate"] is None
           and empty["avg_convert_seconds"] is None
           and empty["median_convert_seconds"] is None
           and empty["fastest_convert_seconds"] is None
           and empty["slowest_convert_seconds"] is None
           and "scope" not in env and "dev_account" not in env)
    record("AC-MCV1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              (empty["month_count"], empty["months"],
               empty["conversion_rate"])))

    # -- AC-MCV2 booking law and the unwatch asymmetry --------------
    grid = [row["month"] for row in env["months"]]
    jan = month_row(env, "2026-01")
    feb = month_row(env, "2026-02")
    mar = month_row(env, "2026-03")
    funnel_face = am.api_watch_conversion()
    ok2 = (grid == ["2026-01", "2026-02", "2026-03"]
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-03"
           and env["month_count"] == 3
           and jan["watch_count"] == 4
           and mar["watch_count"] == 4
           and env["watch_count"] == 8
           and funnel_face["watch_count"] == 7
           and funnel_face["converted_count"]
           == env["converted_count"]
           and funnel_face["pre_owned_count"]
           == env["pre_owned_count"])
    record("AC-MCV2", ok2,
           "grid=%r jan_w=%d mar_w=%d env_w=%d live_w=%d"
           % (grid, jan["watch_count"], mar["watch_count"],
              env["watch_count"], funnel_face["watch_count"]))

    # -- AC-MCV3 directional law and counter conservation -----------
    def conserves(block):
        return (block["funnel_count"]
                == block["watch_count"] - block["pre_owned_count"]
                and block["pending_count"]
                == block["funnel_count"] - block["converted_count"]
                and block["converted_count"] + block["pending_count"]
                + block["pre_owned_count"] == block["watch_count"])

    ok3 = (conserves(jan) and conserves(feb) and conserves(mar)
           and jan["pre_owned_count"] == 1
           and jan["converted_count"] == 2
           and jan["pending_count"] == 1
           and mar["pre_owned_count"] == 0
           and mar["converted_count"] == 3
           and mar["pending_count"] == 1
           and env["pre_owned_count"] == 1
           and env["converted_count"] == 5
           and env["pending_count"] == 2
           and env["funnel_count"] == 7)
    record("AC-MCV3", ok3,
           "jan=%r mar=%r env=%r"
           % ((jan["pre_owned_count"], jan["converted_count"],
               jan["pending_count"]),
              (mar["pre_owned_count"], mar["converted_count"],
               mar["pending_count"]),
              (env["pre_owned_count"], env["converted_count"],
               env["pending_count"])))

    # -- AC-MCV4 contiguous grid, honest zero month, row sums -------
    zero_ok = (feb["watch_count"] == 0
               and feb["pre_owned_count"] == 0
               and feb["funnel_count"] == 0
               and feb["converted_count"] == 0
               and feb["pending_count"] == 0
               and feb["conversion_rate"] is None
               and feb["avg_convert_seconds"] is None
               and feb["median_convert_seconds"] is None
               and feb["fastest_convert_seconds"] is None
               and feb["slowest_convert_seconds"] is None)
    sums_ok = all(
        sum(row[key] for row in env["months"]) == env[key]
        for key in ("watch_count", "pre_owned_count", "funnel_count",
                    "converted_count", "pending_count"))
    ok4 = zero_ok and sums_ok and len(env["months"]) == 3
    record("AC-MCV4", ok4,
           "zero_month=%r sums=%r grid=%d"
           % (zero_ok, sums_ok, len(env["months"])))

    # -- AC-MCV5 pooled rate and latency law -----------------------
    mean_of_means = (jan["avg_convert_seconds"]
                     + mar["avg_convert_seconds"]) / 2.0
    ok5 = (jan["conversion_rate"] == 2.0 / 3.0
           and mar["conversion_rate"] == 3.0 / 4.0
           and env["conversion_rate"] == 5.0 / 7.0
           and jan["avg_convert_seconds"] == 129600.0
           and jan["median_convert_seconds"] == 129600.0
           and jan["fastest_convert_seconds"] == 0
           and jan["slowest_convert_seconds"] == 3 * DAY
           and mar["avg_convert_seconds"] == 921600.0
           and mar["median_convert_seconds"] == 3 * DAY
           and mar["fastest_convert_seconds"] == DAY
           and mar["slowest_convert_seconds"] == 28 * DAY
           and env["avg_convert_seconds"] == 604800.0
           and env["avg_convert_seconds"] != mean_of_means
           and env["median_convert_seconds"] == 3 * DAY
           and env["fastest_convert_seconds"] == 0
           and env["slowest_convert_seconds"] == 28 * DAY)
    record("AC-MCV5", ok5,
           "pooled=%r mean_of_means=%r jan=%r mar=%r"
           % (env["avg_convert_seconds"], mean_of_means,
              (jan["conversion_rate"], jan["avg_convert_seconds"]),
              (mar["conversion_rate"], mar["avg_convert_seconds"])))

    # -- AC-MCV6 the refund law: pending, keys frozen ---------------
    keys_before = grid
    _CLOCK.value = "2026-04-02T00:00:00Z"
    am.refund_api("usr:ha", ids["p_ha"], "not what was described")
    after = am.api_market_conversion_months()
    mar2 = month_row(after, "2026-03")
    ok6 = ([row["month"] for row in after["months"]] == keys_before
           and after["month_count"] == 3
           and mar2["watch_count"] == 4
           and mar2["converted_count"] == 2
           and mar2["pending_count"] == 2
           and mar2["conversion_rate"] == 0.5
           and mar2["avg_convert_seconds"] == 1339200.0
           and mar2["median_convert_seconds"] == 1339200.0
           and after["converted_count"] == 4
           and after["pending_count"] == 3
           and after["conversion_rate"] == 4.0 / 7.0
           and after["avg_convert_seconds"] == 734400.0
           and jan == month_row(after, "2026-01"))
    record("AC-MCV6", ok6,
           "keys=%r mar=%r env=%r"
           % ([row["month"] for row in after["months"]],
              (mar2["converted_count"], mar2["pending_count"],
               mar2["conversion_rate"]),
              (after["converted_count"], after["pending_count"],
               after["conversion_rate"])))

    # -- AC-MCV7 pure read and the no-argument surface --------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_market_conversion_months())
    call_b = dumps(am.api_market_conversion_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    try:
        am.api_market_conversion_months(dev_account="usr:dana")
        kwarg_refused = False
    except TypeError:
        kwarg_refused = True
    ok7 = (call_a == call_b
           and digests_before == digests_after
           and tx_before == tx_after
           and kwarg_refused)
    record("AC-MCV7", ok7,
           "deterministic=%r digests_same=%r tx_same=%r no_kwarg=%r"
           % (call_a == call_b, digests_before == digests_after,
              tx_before == tx_after, kwarg_refused))

    # -- AC-MCV8 restarts, wiring and hygiene ----------------------
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_market_conversion_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_market_conversion_months())
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (call_a == call_c == call_d == dumps(after)
           and b'"ledger-apimarket-marketconversionmonths"' in recon
           and b"test_apimarket_marketconversionmonths.py" in recon
           and b"def api_market_conversion_months" in src
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-MCV8", ok8,
           "bytes_same=%r wired=%r ascii=%r crlf_clean=%r"
           % (call_a == call_d,
              b'"ledger-apimarket-marketconversionmonths"' in recon,
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