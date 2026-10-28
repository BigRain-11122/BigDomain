"""Acceptance suite for the apimarket buyer-side monthly watch flow
(BigDomain R2213; canon = the R2213 explore-queue claim row, criteria
AC-BWM1..AC-BWM8 registered in that row BEFORE this code).

Face under proof: APIMarketFace.api_buyer_watch_months. The market face
answers the whole market and the seller face one seller, both on a
monthly axis, while the buyer side carried only a live category mix and
a lifetime conversion funnel, so one resident's own attention timeline
had no face. This suite pins:

  - the fifteen-key envelope and eight-key month rows, honest empty
    first, the buyer scope label and the account echoed back;
  - the cash-basis booking law shared with the two sibling faces: a
    watch books in the watched_utc month, an unwatch in the
    unwatched_utc month, a later unwatch never rewrites the watch
    month, so a pure-unwatch month carries an honestly negative net;
  - the contiguous month grid, where a month with no watch event is an
    honest zero row even though a PURCHASE happened inside it;
  - the directional conversion law: a watch converts only when an
    unrefunded purchase is stamped at or after watched_utc, the
    conversion is booked in the WATCH month, a purchase made before the
    watch never converts, and a refunded purchase stops converting;
  - conservation per row and per envelope, the running active_count
    landing on the live watch count, the event-derived participant
    counts and both peak laws with the earlier-month tie-break;
  - strict buyer isolation against an identical-looking neighbour, the
    cross-face identity with api_watchlist, and the seven-form gate
    family failing closed before any read;
  - the pure-read law (frozen table digests, constant ledger_tx,
    byte-identical repeats), cross-instance and cross-restart byte
    identity, the wiring and the ASCII/LF source hygiene.

Usage: python test_apimarket_buyerwatchmonths.py
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
    "scope", "buyer_id", "month_count", "watch_count",
    "unwatch_count", "net_count", "live_watch_count", "converted_count",
    "converted_month", "listing_count", "seller_count", "busiest_month",
    "busiest_watch_count", "months", "disclaimer"}

ROW_KEYS = {
    "month", "watch_count", "unwatch_count", "net_count",
    "active_count", "converted_count", "listing_count", "seller_count"}

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
    """Four listings: t1 and t2 at dana, d1 at lia, g1 at gina.

    bob: JAN watch t1; FEB watch d1; MAR nothing (the honest zero row);
         APR buy d1 (converts the FEB watch) and buy t2 (no watch yet);
         MAY unwatch t1 (pure-unwatch month, honestly negative net);
         JUN watch t2 (its purchase predates the watch, so no conversion).
    kit: JAN watch t1 only (isolation control, never buys).
    erin: FEB watch g1; MAR buy g1; APR refund g1 (refund kills the
         conversion).
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-BWM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-BWM-S",
                     "settlement")
    for who in ("bob", "kit", "erin"):
        fund(led, who)
    for dev in ("dana", "lia", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    t2 = am.publish_api("usr:dana", "t2", "Dana Tools Pro",
                        "dana tools pro payloads", PAYLOAD, 10, False,
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

    clock.value = "2026-02-04T00:00:00Z"
    am.watch_api("usr:bob", d1)
    am.watch_api("usr:erin", g1)

    clock.value = "2026-04-09T00:00:00Z"
    am.purchase_api("usr:bob", d1, "BWM-BOB-D1")
    am.purchase_api("usr:bob", t2, "BWM-BOB-T2")
    am.purchase_api("usr:erin", g1, "BWM-ERIN-G1")

    clock.value = "2026-05-06T00:00:00Z"
    am.unwatch_api("usr:bob", t1)
    am.refund_api("usr:erin", am.api_library("usr:erin")
                  ["purchases"][0]["purchase_id"], "not as described")

    clock.value = "2026-06-03T00:00:00Z"
    am.watch_api("usr:bob", t2)

    return {"t1": t1, "t2": t2, "d1": d1, "g1": g1}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerwatchmonths-")
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

    bob = am.api_buyer_watch_months("usr:bob")
    kit = am.api_buyer_watch_months("usr:kit")
    erin = am.api_buyer_watch_months("usr:erin")

    # -- AC-BWM1 contract, honest empty first, scope labels ----------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-bwm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_watch_months("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for env in (bob, kit, erin)
                  for row in env["months"])
    ok1 = (set(bob.keys()) == ENVELOPE_KEYS
           and rows_ok
           and bob["scope"] == "buyer"
           and bob["buyer_id"] == "usr:bob"
           and bob["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["watch_count"] == 0
           and empty["live_watch_count"] == 0
           and empty["converted_count"] == 0
           and empty["converted_month"] is None
           and empty["busiest_month"] is None
           and empty["busiest_watch_count"] is None)
    record("AC-BWM1", ok1,
           "env_keys=%d exact=%r row_keys=%r scope=%r empty=%r"
           % (len(bob), set(bob.keys()) == ENVELOPE_KEYS, rows_ok,
              bob["scope"],
              (empty["month_count"], empty["months"],
               empty["converted_month"])))

    # -- AC-BWM2 booking law and the pure-unwatch month --------------
    b_jan = month_row(bob, "2026-01")
    b_feb = month_row(bob, "2026-02")
    b_may = month_row(bob, "2026-05")
    b_jun = month_row(bob, "2026-06")
    raw = _raw_buckets(am)
    ok2 = (b_jan["watch_count"] == 1 and b_jan["unwatch_count"] == 0
           and b_jan["net_count"] == 1
           and b_feb["watch_count"] == 1 and b_feb["unwatch_count"] == 0
           and b_may["watch_count"] == 0 and b_may["unwatch_count"] == 1
           and b_may["net_count"] == -1
           and b_jun["watch_count"] == 1 and b_jun["net_count"] == 1
           and raw[("usr:bob", "2026-01")] == (1, 0)
           and raw[("usr:bob", "2026-05")] == (0, 1))
    record("AC-BWM2", ok2,
           "jan=%r feb=%r may=%r jun=%r"
           % ((b_jan["watch_count"], b_jan["unwatch_count"],
               b_jan["net_count"]),
              (b_feb["watch_count"], b_feb["unwatch_count"]),
              (b_may["watch_count"], b_may["unwatch_count"],
               b_may["net_count"]),
              (b_jun["watch_count"], b_jun["net_count"])))

    # -- AC-BWM3 contiguous grid, the zero month and the purchase ----
    grid = [row["month"] for row in bob["months"]]
    b_mar = month_row(bob, "2026-03")
    b_apr = month_row(bob, "2026-04")
    ok3 = (grid == ["2026-01", "2026-02", "2026-03", "2026-04",
                    "2026-05", "2026-06"]
           and b_mar["watch_count"] == 0
           and b_mar["unwatch_count"] == 0
           and b_mar["net_count"] == 0
           and b_mar["converted_count"] == 0
           and b_mar["listing_count"] == 0
           and b_mar["seller_count"] == 0
           and b_mar["active_count"] == b_feb["active_count"] == 2
           and b_apr["watch_count"] == 0
           and b_apr["unwatch_count"] == 0
           and b_apr["converted_count"] == 0
           and b_apr["active_count"] == 2
           and [r["active_count"] for r in bob["months"]]
           == [1, 2, 2, 2, 1, 2])
    record("AC-BWM3", ok3,
           "grid=%r mar=%r apr=%r running=%r"
           % (grid,
              (b_mar["watch_count"], b_mar["active_count"]),
              (b_apr["watch_count"], b_apr["unwatch_count"],
               b_apr["active_count"]),
              [r["active_count"] for r in bob["months"]]))

    # -- AC-BWM4 directional conversion law -------------------------
    e_feb = month_row(erin, "2026-02")
    ok4 = (b_feb["converted_count"] == 1
           and b_jun["converted_count"] == 0
           and b_jan["converted_count"] == 0
           and bob["converted_count"] == 1
           and bob["converted_month"] == "2026-02"
           and sum(r["converted_count"] for r in bob["months"]) == 1
           and all(row["converted_count"] <= row["watch_count"]
                   for env in (bob, kit, erin)
                   for row in env["months"])
           and e_feb["converted_count"] == 0
           and erin["converted_count"] == 0
           and erin["converted_month"] is None)
    record("AC-BWM4", ok4,
           "bob_feb_conv=%r bob_jun_conv=%r bob_conv=%r/%r "
           "erin_feb_conv=%r"
           % (b_feb["converted_count"], b_jun["converted_count"],
              bob["converted_count"], bob["converted_month"],
              e_feb["converted_count"]))

    # -- AC-BWM5 conservation, participants and both peaks ----------
    ok5 = (sum(r["watch_count"] for r in bob["months"])
           == bob["watch_count"] == 3
           and sum(r["unwatch_count"] for r in bob["months"])
           == bob["unwatch_count"] == 1
           and bob["net_count"] == 2
           and bob["months"][-1]["active_count"]
           == bob["live_watch_count"] == 2
           and bob["listing_count"] == 3
           and bob["seller_count"] == 2
           and b_jan["listing_count"] == 1
           and b_jan["seller_count"] == 1
           and b_feb["seller_count"] == 1
           and bob["busiest_month"] == "2026-01"
           and bob["busiest_watch_count"] == 1
           and all(row["net_count"] == row["watch_count"]
                   - row["unwatch_count"]
                   for row in bob["months"]))
    record("AC-BWM5", ok5,
           "sums=%r live=%r participants=%r/%r peak=%r/%r"
           % ((bob["watch_count"], bob["unwatch_count"],
               bob["net_count"]), bob["live_watch_count"],
              bob["listing_count"], bob["seller_count"],
              bob["busiest_month"], bob["busiest_watch_count"]))

    # -- AC-BWM6 isolation and the cross-face identity --------------
    watchers = am.api_watchlist("usr:bob")
    kit_rows = am.api_watchlist("usr:kit")
    conn = sqlite3.connect(am.db_path)
    bob_watches = conn.execute(
        "SELECT COUNT(*) FROM apimarket_watchlist WHERE buyer_id = ?",
        ("usr:bob",)).fetchone()[0]
    bob_unwatches = conn.execute(
        "SELECT COUNT(*) FROM apimarket_unwatchings WHERE buyer_id = ?",
        ("usr:bob",)).fetchone()[0]
    conn.close()
    ok6 = (watchers["watch_count"] == bob["live_watch_count"] == 2
           and int(bob_watches) == bob["watch_count"] == 3
           and int(bob_unwatches) == bob["unwatch_count"] == 1
           and kit["watch_count"] == 1
           and kit["unwatch_count"] == 0
           and kit["live_watch_count"] == 1
           and kit["converted_count"] == 0
           and kit_rows["watch_count"] == 1
           and erin["watch_count"] == 1
           and erin["live_watch_count"] == 1
           and [r["month"] for r in kit["months"]] == ["2026-01"]
           and bob["month_count"] == 6)
    record("AC-BWM6", ok6,
           "cross_face=%r table=%r/%r kit=%r erin=%r"
           % (watchers["watch_count"] == bob["live_watch_count"],
              int(bob_watches), int(bob_unwatches),
              (kit["watch_count"], kit["live_watch_count"]),
              (erin["watch_count"], erin["converted_count"])))

    # -- AC-BWM7 gates, purity and deterministic bytes --------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_codes = []
    for bad in (123, [], {}, "  ", "bob", True, "usr"):
        try:
            am.api_buyer_watch_months(bad)
        except A.ApiMarketError as exc:
            bad_codes.append(exc.code)
        else:
            bad_codes.append("ACCEPTED")
    digests_mid = market_digests(am)
    call_a = dumps(am.api_buyer_watch_months("usr:bob"))
    call_b = dumps(am.api_buyer_watch_months("usr:bob"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, _gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    call_c = dumps(am2.api_buyer_watch_months("usr:bob"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, _gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    call_d = dumps(am3.api_buyer_watch_months("usr:bob"))
    call_ek = dumps(am3.api_buyer_watch_months("usr:kit"))
    close_stack(am3, dk3, metered3, led3)

    ok7 = (bad_codes == [A.E_AM_BAD_ACCOUNT] * 7
           and digests_before == digests_mid == digests_after
           and tx_before == tx_after
           and call_a == call_b == call_c == call_d == dumps(bob)
           and call_ek == dumps(kit))
    record("AC-BWM7", ok7,
           "gates=%r digests_same=%r tx_same=%r bytes_same=%r"
           % (bad_codes, digests_before == digests_after,
              tx_before == tx_after, call_a == call_d))

    # -- AC-BWM8 hygiene and the wiring -----------------------------
    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (b'"ledger-apimarket-buyerwatchmonths"' in recon
           and b"test_apimarket_buyerwatchmonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-BWM8", ok8,
           "wired=%r src_lf=%r test_ascii_lf=%r"
           % (b'"ledger-apimarket-buyerwatchmonths"' in recon,
              b"\r\n" not in src, b"\r\n" not in test_src))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("%s PRODUCT_SHA_STABLE %r"
          % ("PASS" if shas_before == shas_after else "FAIL",
             shas_before == shas_after), flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


def _raw_buckets(am):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT w.buyer_id, w.watched_utc, u.unwatched_utc"
        " FROM apimarket_watchlist w"
        " LEFT JOIN apimarket_unwatchings u ON u.watch_id = w.watch_id"
        " ORDER BY w.watch_id").fetchall()
    conn.close()
    out = {}
    for buyer, watched, unwatched in rows:
        key = (buyer, str(watched)[:7])
        w, u = out.get(key, (0, 0))
        out[key] = (w + 1, u)
        if unwatched is not None:
            key2 = (buyer, str(unwatched)[:7])
            w2, u2 = out.get(key2, (0, 0))
            out[key2] = (w2, u2 + 1)
    return out


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())