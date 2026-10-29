"""Acceptance suite for the apimarket seller-scoped monthly
watch-to-purchase conversion (BigDomain R2241; canon = the R2240
explore seed row a, criteria AC-SWCV1..AC-SWCV8 registered in that row
BEFORE this code existed).

Face under proof: APIMarketFace.api_seller_watch_conversion_months.
The market face answers the whole market on a month axis, the category
face one bucket and the listing funnel face one listing's lifetime, so
whether a single SELLER's own attention converted had no reading. This
suite pins:

  - the twenty-key envelope, fourteen-key month rows, the market and
    seller scope shapes and the honest empty seller world;
  - the cohort law on the watch month, with an unwatch proven not to be
    an event for this face;
  - the three conversion legs (converted, pre_owned excluded from the
    funnel, pending that also absorbs a refunded purchase);
  - the contiguous grid with an honest zero month whose rate and all
    four latencies are None rather than fabricated zeros;
  - strict seller isolation partitioning the market envelope, and the
    market scope publishing no self-benchmark while a seller scope
    carries the true market rate of every month;
  - identity against api_market_conversion_months (envelope and grid)
    and against api_seller_watch_months (per-seller watch counts);
  - the usr: shape gate failing closed before any read, the pure-read
    law (frozen table digests, constant ledger_tx, byte-identical
    repeats across instances and restarts), the wiring and the
    ASCII/LF source hygiene.

Usage: python test_apimarket_sellerwatchconversionmonths.py
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
    "scope", "dev_account", "month_count", "first_month", "last_month",
    "watch_count", "pre_owned_count", "funnel_count", "converted_count",
    "pending_count", "conversion_rate", "avg_convert_seconds",
    "median_convert_seconds", "fastest_convert_seconds",
    "slowest_convert_seconds", "buyer_count", "listing_count",
    "market_conversion_rate", "disclaimer", "months"}

ROW_KEYS = {
    "month", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate",
    "avg_convert_seconds", "median_convert_seconds",
    "fastest_convert_seconds", "slowest_convert_seconds",
    "buyer_count", "listing_count", "market_conversion_rate"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set
    before each write so the month buckets are reproducible."""

    def __init__(self):
        self.value = "2026-01-10T00:00:00Z"

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


def fund(led, who):
    led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:" + who, "credit", 400)],
               "manual:fund-" + who, "suite funding " + who)


def month_row(env, month):
    for row in env["months"]:
        if row["month"] == month:
            return row
    raise AssertionError("month %r missing from months" % (month,))


def seed_world(led, dk, am, clock):
    """Three listings, two sellers: t1 at dana (tools), d1 and u1 at
    lia (data, the second one honestly uncategorized - the face has no
    category axis, so they only widen lia's watch span).

    JAN: erin buys d1 on 01-05 and only watches it on 01-10, so that
         watch is pre_owned; bob and kit watch t1 on 01-10 and bob buys
         t1 on 01-12 (converted, 172800s).
    FEB: kit unwatches t1 on 02-10 - an unwatch is not an event for
         this face, so the month carries no weight at all.
    MAR: bob watches d1 on 03-05 and buys it on 03-08 (converted,
         259200s); sol watches u1 on 03-05 (pending).
    APR: kit watches d1 on 04-02 (pending).

    dana: 2 watches / 0 pre_owned / 1 converted / 1 pending.
    lia: 4 watches / 1 pre_owned / funnel 3 / 1 converted / 2 pending.
    market: 6 watches / 1 pre_owned / funnel 5 / 2 converted /
    3 pending.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SWCV-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SWCV-S",
                     "settlement")
    for who in ("bob", "kit", "erin", "sol"):
        fund(led, who)
    for dev in ("dana", "lia"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    d1 = am.publish_api("usr:lia", "d1", "Lia Data API",
                        "lia data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    u1 = am.publish_api("usr:lia", "u1", "Lia Unsorted API",
                        "lia unsorted payloads", PAYLOAD, 10,
                        False)["listing_id"]

    clock.value = "2026-01-05T00:00:00Z"
    am.purchase_api("usr:erin", d1, "BUY-SWCV-1")

    clock.value = "2026-01-10T00:00:00Z"
    am.watch_api("usr:bob", t1)
    am.watch_api("usr:kit", t1)
    am.watch_api("usr:erin", d1)

    clock.value = "2026-01-12T00:00:00Z"
    am.purchase_api("usr:bob", t1, "BUY-SWCV-2")

    clock.value = "2026-02-10T00:00:00Z"
    am.unwatch_api("usr:kit", t1)

    clock.value = "2026-03-05T00:00:00Z"
    am.watch_api("usr:bob", d1)
    am.watch_api("usr:sol", u1)

    clock.value = "2026-03-08T00:00:00Z"
    am.purchase_api("usr:bob", d1, "BUY-SWCV-3")

    clock.value = "2026-04-02T00:00:00Z"
    am.watch_api("usr:kit", d1)

    return {"t1": t1, "d1": d1, "u1": u1}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerwc-")
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
    seed_world(led, dk, am, _CLOCK)

    market = am.api_seller_watch_conversion_months()
    dana = am.api_seller_watch_conversion_months("usr:dana")
    lia = am.api_seller_watch_conversion_months("usr:lia")

    # -- AC-SWCV1 contract shape and the honest empty seller ---------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-swcv-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_watch_conversion_months("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    ok1 = (set(market) == ENVELOPE_KEYS
           and set(dana) == ENVELOPE_KEYS
           and all(set(row) == ROW_KEYS for row in market["months"])
           and all(set(row) == ROW_KEYS for row in lia["months"])
           and market["scope"] == "market"
           and market["dev_account"] is None
           and dana["scope"] == "seller"
           and dana["dev_account"] == "usr:dana"
           and market["disclaimer"] == DISCLAIMER
           and dana["disclaimer"] == DISCLAIMER
           and set(empty) == ENVELOPE_KEYS
           and empty["scope"] == "seller"
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["watch_count"] == 0
           and empty["conversion_rate"] is None
           and empty["buyer_count"] == 0)
    record("AC-SWCV1", ok1,
           "envelope=%d row=%d empty_months=%d"
           % (len(market), len(ROW_KEYS), empty["month_count"]))

    # -- AC-SWCV2 cohort law: the watch month owns the watch, and an
    # unwatch is not an event for this face --------------------------
    dana_months = [row["month"] for row in dana["months"]]
    ok2 = (market["months"][0]["month"] == "2026-01"
           and market["months"][-1]["month"] == "2026-04"
           and dana_months == ["2026-01"]
           and dana["watch_count"] == 2
           and any(row["month"] == "2026-02"
                   and row["watch_count"] == 0
                   and row["converted_count"] == 0
                   and row["pre_owned_count"] == 0
                   and row["pending_count"] == 0
                   for row in market["months"])
           and lia["watch_count"] == 4)
    record("AC-SWCV2", ok2,
           "market_span=%s..%s dana_months=%r dana_watch=%d"
           % (market["months"][0]["month"],
              market["months"][-1]["month"], dana_months,
              dana["watch_count"]))

    # -- AC-SWCV3 the three legs and their conservation --------------
    legs = all(row["converted_count"] + row["pre_owned_count"]
               + row["pending_count"] == row["watch_count"]
               and row["funnel_count"] == row["watch_count"]
               - row["pre_owned_count"]
               and row["pending_count"] == row["funnel_count"]
               - row["converted_count"]
               for row in market["months"] + lia["months"]
               + dana["months"])
    ok3 = (legs
           and market["converted_count"] == 2
           and market["pre_owned_count"] == 1
           and market["funnel_count"] == 5
           and market["pending_count"] == 3
           and lia["pre_owned_count"] == 1
           and lia["funnel_count"] == 3
           and lia["converted_count"] == 1
           and lia["pending_count"] == 2
           and dana["converted_count"] == 1
           and dana["pending_count"] == 1
           and dana["pre_owned_count"] == 0)
    record("AC-SWCV3", ok3,
           "market c/p/pd=%d/%d/%d lia=%d/%d/%d dana=%d/%d/%d"
           % (market["converted_count"], market["pre_owned_count"],
              market["pending_count"], lia["converted_count"],
              lia["pre_owned_count"], lia["pending_count"],
              dana["converted_count"], dana["pre_owned_count"],
              dana["pending_count"]))

    # -- AC-SWCV4 contiguous grid, honest zero month, envelope equals
    # the row sums ---------------------------------------------------
    feb = month_row(market, "2026-02")
    lia_feb = month_row(lia, "2026-02")
    ok4 = ([row["month"] for row in lia["months"]]
           == ["2026-01", "2026-02", "2026-03", "2026-04"]
           and [row["month"] for row in market["months"]]
           == ["2026-01", "2026-02", "2026-03", "2026-04"]
           and feb["conversion_rate"] is None
           and feb["avg_convert_seconds"] is None
           and feb["median_convert_seconds"] is None
           and feb["fastest_convert_seconds"] is None
           and feb["slowest_convert_seconds"] is None
           and lia_feb["conversion_rate"] is None
           and sum(row["watch_count"] for row in market["months"])
           == market["watch_count"]
           and sum(row["pre_owned_count"] for row in market["months"])
           == market["pre_owned_count"]
           and sum(row["converted_count"] for row in market["months"])
           == market["converted_count"]
           and sum(row["pending_count"] for row in market["months"])
           == market["pending_count"])
    record("AC-SWCV4", ok4,
           "grid=%d zero_rate=%r sums=%d/%d/%d/%d"
           % (market["month_count"], feb["conversion_rate"],
              sum(row["watch_count"] for row in market["months"]),
              sum(row["pre_owned_count"] for row in market["months"]),
              sum(row["converted_count"] for row in market["months"]),
              sum(row["pending_count"] for row in market["months"])))

    # -- AC-SWCV5 strict isolation and the partition ------------------
    unknown = am.api_seller_watch_conversion_months("usr:ghost")
    ok5 = (dana["watch_count"] + lia["watch_count"]
           == market["watch_count"]
           and dana["converted_count"] + lia["converted_count"]
           == market["converted_count"]
           and dana["pre_owned_count"] + lia["pre_owned_count"]
           == market["pre_owned_count"]
           and dana["listing_count"] == 1
           and lia["listing_count"] == 2
           and dana["buyer_count"] == 2
           and lia["buyer_count"] == 4
           and unknown["watch_count"] == 0
           and unknown["months"] == []
           and unknown["conversion_rate"] is None)
    record("AC-SWCV5", ok5,
           "partition=%d+%d=%d unknown_watch=%d"
           % (dana["watch_count"], lia["watch_count"],
              market["watch_count"], unknown["watch_count"]))

    # -- AC-SWCV6 the benchmark column -------------------------------
    ok6 = (market["market_conversion_rate"] is None
           and all(row["market_conversion_rate"] is None
                   for row in market["months"])
           and dana["conversion_rate"] == 0.5
           and dana["months"][0]["market_conversion_rate"] == 0.5
           and lia["conversion_rate"] == 1.0 / 3.0
           and lia["market_conversion_rate"] == 0.4
           and month_row(lia, "2026-01")["market_conversion_rate"] \
           == 0.5
           and month_row(lia, "2026-02")["market_conversion_rate"] \
           is None
           and month_row(lia, "2026-03")["market_conversion_rate"] \
           == 0.5
           and month_row(lia, "2026-04")["market_conversion_rate"] \
           == 0.0)
    record("AC-SWCV6", ok6,
           "market_none=%r lia_env=%r jan=%r feb=%r apr=%r"
           % (market["market_conversion_rate"] is None,
              lia["market_conversion_rate"],
              month_row(lia, "2026-01")["market_conversion_rate"],
              month_row(lia, "2026-02")["market_conversion_rate"],
              month_row(lia, "2026-04")["market_conversion_rate"]))

    # -- AC-SWCV7 identity against the two source faces --------------
    conv = am.api_market_conversion_months()
    shared = ("watch_count", "pre_owned_count", "funnel_count",
              "converted_count", "pending_count", "conversion_rate",
              "avg_convert_seconds", "median_convert_seconds",
              "fastest_convert_seconds", "slowest_convert_seconds")
    seller_vol_dana = am.api_seller_watch_months("usr:dana")
    seller_vol_lia = am.api_seller_watch_months("usr:lia")
    ok7 = (all(market[k] == conv[k] for k in shared)
           and [row["month"] for row in market["months"]]
           == [row["month"] for row in conv["months"]]
           and all(month_row(market, month)["watch_count"]
                   == month_row(conv, month)["watch_count"]
                   for month in ("2026-01", "2026-02", "2026-03",
                                 "2026-04"))
           and dana["watch_count"] == seller_vol_dana["watch_count"]
           and lia["watch_count"] == seller_vol_lia["watch_count"]
           and market["avg_convert_seconds"] == 216000.0
           and market["median_convert_seconds"] == 216000.0
           and market["fastest_convert_seconds"] == 172800
           and market["slowest_convert_seconds"] == 259200
           and lia["avg_convert_seconds"] == 259200.0
           and dana["fastest_convert_seconds"] == 172800)
    record("AC-SWCV7", ok7,
           "identity=%r dana_vol=%d lia_vol=%d avg=%r median=%r"
           % (all(market[k] == conv[k] for k in shared),
              dana["watch_count"], lia["watch_count"],
              market["avg_convert_seconds"],
              market["median_convert_seconds"]))

    # -- AC-SWCV8 the gate, the pure read and the wiring -------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_forms = ("", "  ", 123, [], {}, "dana", "usr")
    bad_ok = 0
    for bad in bad_forms:
        try:
            am.api_seller_watch_conversion_months(bad)
        except A.ApiMarketError as exc:
            if str(exc).find(A.E_AM_BAD_ACCOUNT) >= 0:
                bad_ok += 1
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    call_a = dumps(am.api_seller_watch_conversion_months("usr:lia"))
    call_b = dumps(am.api_seller_watch_conversion_months("usr:lia"))
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, _gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    call_c = dumps(am2.api_seller_watch_conversion_months("usr:lia"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, _gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    call_d = dumps(am3.api_seller_watch_conversion_months("usr:lia"))
    close_stack(am3, dk3, metered3, led3)
    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (bad_ok == len(bad_forms)
           and digests_before == digests_after
           and tx_before == tx_after
           and call_a == call_b == call_c == call_d == dumps(lia)
           and b'"ledger-apimarket-sellerwatchconversionmonths"' \
           in recon
           and b"test_apimarket_sellerwatchconversionmonths.py" \
           in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-SWCV8", ok8,
           "bad=%d/%d frozen=%r tx_same=%r bytes_same=%r wired=%r"
           " ascii_lf=%r"
           % (bad_ok, len(bad_forms),
              digests_before == digests_after,
              tx_before == tx_after,
              call_a == call_d,
              b'"ledger-apimarket-sellerwatchconversionmonths"'
              in recon,
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