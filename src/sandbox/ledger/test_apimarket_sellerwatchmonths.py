"""Acceptance suite for the apimarket seller-side monthly watch-inflow
timeline (BigDomain R2204; canon = the R2202 seed explore claim row,
criteria AC-SWM1..AC-SWM8 registered in that row BEFORE this code).

Face under proof: APIMarketFace.api_seller_watch_months. The market
face answers the whole market and the conversion face answers one
funnel, so a seller could not read how attention on its own shelves
moved month by month. This suite pins:

  - the thirteen-key envelope and seven-key month rows (no
    seller_count, because the scope is one seller), honest empty first,
    and the scope labels;
  - the cash-basis double stamp shared with the market face: a watch
    books in the watched_utc month, an unwatch in the unwatched_utc
    month, and a later unwatch never rewrites the watch month, so a
    pure-unwatch month carries an honestly negative net;
  - the contiguous month grid with a zero-event month in the middle and
    a flat running active_count;
  - conservation of watches, unwatches, nets and the running
    active_count landing on the live watch count per scope;
  - the event-derived participant law per month plus the lifetime
    distinct counts in the envelope, and the busiest-month law with the
    earlier-month tie-break and None on an empty world;
  - scope identity with api_market_watch_months on every shared key and
    strict seller isolation (another seller's watches never leak);
  - the gate family (seven bad account forms fail closed before any
    read, bare 'usr:' passing to an honest empty), the pure-read law
    (frozen table digests, constant ledger_tx, byte-identical repeats)
    and cross-instance plus cross-restart byte identity;
  - the wiring and the ASCII/LF source hygiene.

Usage: python test_apimarket_sellerwatchmonths.py
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
    "scope", "dev_account", "month_count", "watch_count",
    "unwatch_count", "net_count", "live_watch_count", "buyer_count",
    "listing_count", "busiest_month", "busiest_watch_count", "months",
    "disclaimer"}

ROW_KEYS = {
    "month", "watch_count", "unwatch_count", "net_count",
    "active_count", "buyer_count", "listing_count"}

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
    """Three listings: t1 at dana (tools), d1 at lia (data), g1 at gina
    (data).

    JAN: bob watches t1, kit watches t1, erin watches d1.
    FEB: no event at all (the zero row that proves the grid).
    MAR: bob watches d1, sol watches g1; erin unwatches d1.
    APR: bob watches g1.
    MAY: kit unwatches t1 (pure-unwatch month, honestly negative net).

    Per scope: dana 2 watches / 1 unwatch / live 1; lia 2 / 1 / live 1;
    gina 2 / 0 / live 2. Market 6 / 2 / live 4.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SWM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SWM-S",
                     "settlement")
    for who in ("bob", "kit", "erin", "sol"):
        fund(led, who)
    for dev in ("dana", "lia", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    d1 = am.publish_api("usr:lia", "d1", "Lia Data API",
                        "lia data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    clock.value = "2026-01-10T00:00:00Z"
    am.watch_api("usr:bob", t1)
    am.watch_api("usr:kit", t1)
    am.watch_api("usr:erin", d1)

    clock.value = "2026-03-05T00:00:00Z"
    am.watch_api("usr:bob", d1)
    am.watch_api("usr:sol", g1)
    am.unwatch_api("usr:erin", d1)

    clock.value = "2026-04-02T00:00:00Z"
    am.watch_api("usr:bob", g1)

    clock.value = "2026-05-07T00:00:00Z"
    am.unwatch_api("usr:kit", t1)

    return {"t1": t1, "d1": d1, "g1": g1}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerwatchmonths-")
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

    dana = am.api_seller_watch_months("usr:dana")
    lia = am.api_seller_watch_months("usr:lia")
    gina = am.api_seller_watch_months("usr:gina")
    market = am.api_seller_watch_months()

    # -- AC-SWM1 contract, honest empty first, scope labels ----------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-swm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_watch_months("usr:nobody")
    empty_market = e_am.api_seller_watch_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for env in (dana, lia, gina, market)
                  for row in env["months"])
    ok1 = (set(dana.keys()) == ENVELOPE_KEYS
           and set(market.keys()) == ENVELOPE_KEYS
           and rows_ok
           and dana["scope"] == "seller"
           and dana["dev_account"] == "usr:dana"
           and market["scope"] == "market"
           and market["dev_account"] is None
           and dana["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["watch_count"] == 0
           and empty["live_watch_count"] == 0
           and empty["busiest_month"] is None
           and empty["busiest_watch_count"] is None
           and empty_market["month_count"] == 0
           and empty_market["scope"] == "market")
    record("AC-SWM1", ok1,
           "env_keys=%d exact=%r row_keys=%r scope=%r/%r empty=%r"
           % (len(dana), set(dana.keys()) == ENVELOPE_KEYS, rows_ok,
              dana["scope"], market["scope"],
              (empty["month_count"], empty["months"])))

    # -- AC-SWM2 booking law per seller ------------------------------
    d_jan = month_row(dana, "2026-01")
    d_may = month_row(dana, "2026-05")
    l_jan = month_row(lia, "2026-01")
    l_mar = month_row(lia, "2026-03")
    g_mar = month_row(gina, "2026-03")
    g_apr = month_row(gina, "2026-04")
    raw = _raw_buckets(am)
    ok2 = (d_jan["watch_count"] == 2 and d_jan["unwatch_count"] == 0
           and d_may["watch_count"] == 0 and d_may["unwatch_count"] == 1
           and d_may["net_count"] == -1
           and l_jan["watch_count"] == 1 and l_jan["unwatch_count"] == 0
           and l_mar["watch_count"] == 1 and l_mar["unwatch_count"] == 1
           and l_mar["net_count"] == 0
           and g_mar["watch_count"] == 1 and g_apr["watch_count"] == 1
           and raw[("usr:dana", "2026-01")] == (2, 0)
           and raw[("usr:dana", "2026-05")] == (0, 1)
           and raw[("usr:lia", "2026-03")] == (1, 1)
           and raw[("usr:gina", "2026-04")] == (1, 0))
    record("AC-SWM2", ok2,
           "dana_jan=%r dana_may=%r lia_mar=%r gina=%r"
           % ((d_jan["watch_count"], d_jan["unwatch_count"]),
              (d_may["watch_count"], d_may["unwatch_count"],
               d_may["net_count"]),
              (l_mar["watch_count"], l_mar["unwatch_count"],
               l_mar["net_count"]),
              (g_mar["watch_count"], g_apr["watch_count"])))

    # -- AC-SWM3 contiguous grid and the flat zero month -------------
    d_grid = [row["month"] for row in dana["months"]]
    d_feb = month_row(dana, "2026-02")
    g_grid = [row["month"] for row in gina["months"]]
    ok3 = (d_grid == ["2026-01", "2026-02", "2026-03", "2026-04",
                      "2026-05"]
           and d_feb["watch_count"] == 0
           and d_feb["unwatch_count"] == 0
           and d_feb["net_count"] == 0
           and d_feb["buyer_count"] == 0
           and d_feb["active_count"] == d_jan["active_count"] == 2
           and g_grid == ["2026-03", "2026-04"])
    record("AC-SWM3", ok3,
           "dana_grid=%r feb=%r gina_grid=%r"
           % (d_grid, (d_feb["watch_count"], d_feb["active_count"]),
              g_grid))

    # -- AC-SWM4 running net lands on the live count -----------------
    ok4 = (dana["months"][-1]["active_count"]
           == dana["live_watch_count"] == 1
           and lia["months"][-1]["active_count"]
           == lia["live_watch_count"] == 1
           and gina["months"][-1]["active_count"]
           == gina["live_watch_count"] == 2
           and market["months"][-1]["active_count"]
           == market["live_watch_count"] == 4
           and all(row["net_count"] == row["watch_count"]
                   - row["unwatch_count"]
                   for env in (dana, lia, gina, market)
                   for row in env["months"]))
    record("AC-SWM4", ok4,
           "live=%r/%r/%r/%r"
           % (dana["live_watch_count"], lia["live_watch_count"],
              gina["live_watch_count"], market["live_watch_count"]))

    # -- AC-SWM5 conservation, participants, busiest ----------------
    d_sw = sum(r["watch_count"] for r in dana["months"])
    d_su = sum(r["unwatch_count"] for r in dana["months"])
    l_sw = sum(r["watch_count"] for r in lia["months"])
    g_sw = sum(r["watch_count"] for r in gina["months"])
    ok5 = (d_sw == dana["watch_count"] == 2
           and d_su == dana["unwatch_count"] == 1
           and dana["net_count"] == 1
           and l_sw == lia["watch_count"] == 2
           and g_sw == gina["watch_count"] == 2
           and dana["buyer_count"] == 2 and dana["listing_count"] == 1
           and lia["buyer_count"] == 2 and lia["listing_count"] == 1
           and gina["buyer_count"] == 2 and gina["listing_count"] == 1
           and market["buyer_count"] == 4
           and market["listing_count"] == 3
           and dana["busiest_month"] == "2026-01"
           and dana["busiest_watch_count"] == 2
           and lia["busiest_month"] == "2026-01"
           and lia["busiest_watch_count"] == 1
           and gina["busiest_month"] == "2026-03"
           and gina["busiest_watch_count"] == 1
           and market["busiest_month"] == "2026-01"
           and market["busiest_watch_count"] == 3)
    record("AC-SWM5", ok5,
           "sums=%r busiest=%r/%r/%r/%r"
           % ((d_sw, d_su, l_sw, g_sw),
              dana["busiest_month"], lia["busiest_month"],
              gina["busiest_month"], market["busiest_month"]))

    # -- AC-SWM6 scope identity and strict isolation ----------------
    face = am.api_market_watch_months()
    shared = ("month", "watch_count", "unwatch_count", "net_count",
              "active_count", "buyer_count", "listing_count")
    face_rows = [{k: row[k] for k in shared} for row in face["months"]]
    market_rows = [{k: row[k] for k in shared}
                   for row in market["months"]]
    bare = am.api_seller_watch_months("usr:")
    isolated = (dana["buyer_count"] == 2 and dana["listing_count"] == 1
                and lia["listing_count"] == 1
                and gina["listing_count"] == 1
                and dana["live_watch_count"]
                + lia["live_watch_count"]
                + gina["live_watch_count"]
                == market["live_watch_count"] == 4)
    ok6 = (face_rows == market_rows
           and face["watch_count"] == market["watch_count"] == 6
           and face["unwatch_count"] == market["unwatch_count"] == 2
           and face["live_watch_count"] == market["live_watch_count"] == 4
           and isolated
           and bare["month_count"] == 0
           and bare["watch_count"] == 0
           and bare["scope"] == "seller")
    record("AC-SWM6", ok6,
           "identity=%r bare=%r isolated=%r"
           % (face_rows == market_rows, bare["month_count"], isolated))

    # -- AC-SWM7 gates, purity and deterministic bytes --------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_codes = []
    for bad in (123, [], {}, "  ", "dana", True, "usr"):
        try:
            am.api_seller_watch_months(bad)
        except A.ApiMarketError as exc:
            bad_codes.append(exc.code)
        else:
            bad_codes.append("ACCEPTED")
    digests_mid = market_digests(am)
    call_a = dumps(am.api_seller_watch_months("usr:dana"))
    call_b = dumps(am.api_seller_watch_months("usr:dana"))
    call_m = dumps(am.api_seller_watch_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, _gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    call_c = dumps(am2.api_seller_watch_months("usr:dana"))
    call_cm = dumps(am2.api_seller_watch_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, _gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    call_d = dumps(am3.api_seller_watch_months("usr:dana"))
    call_dm = dumps(am3.api_seller_watch_months())
    close_stack(am3, dk3, metered3, led3)

    ok7 = (bad_codes == [A.E_AM_BAD_ACCOUNT] * 7
           and digests_before == digests_mid == digests_after
           and tx_before == tx_after
           and call_a == call_b == call_c == call_d == dumps(dana)
           and call_m == call_cm == call_dm == dumps(market))
    record("AC-SWM7", ok7,
           "gates=%r digests_same=%r tx_same=%r bytes_same=%r"
           % (bad_codes, digests_before == digests_after,
              tx_before == tx_after, call_a == call_d))

    # -- AC-SWM8 hygiene and the wiring -----------------------------
    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (b'"ledger-apimarket-sellerwatchmonths"' in recon
           and b"test_apimarket_sellerwatchmonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-SWM8", ok8,
           "wired=%r src_lf=%r test_ascii_lf=%r"
           % (b'"ledger-apimarket-sellerwatchmonths"' in recon,
              b"\r\n" not in src, b"\r\n" not in test_src))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


def _raw_buckets(am):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT l.dev_account, w.watched_utc, u.unwatched_utc"
        " FROM apimarket_watchlist w"
        " JOIN apimarket_listings l ON l.listing_id = w.listing_id"
        " LEFT JOIN apimarket_unwatchings u ON u.watch_id = w.watch_id"
        " ORDER BY w.watch_id").fetchall()
    conn.close()
    out = {}
    for dev, watched, unwatched in rows:
        key = (dev, str(watched)[:7])
        w, u = out.get(key, (0, 0))
        out[key] = (w + 1, u)
        if unwatched is not None:
            key2 = (dev, str(unwatched)[:7])
            w2, u2 = out.get(key2, (0, 0))
            out[key2] = (w2, u2 + 1)
    return out


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())