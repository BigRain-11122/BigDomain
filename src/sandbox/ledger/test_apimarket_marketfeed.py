"""Acceptance suite for the apimarket public activity feed
(BigDomain R2107; canon = the explore-queue row seeded and claimed in
R2107, criteria AC-AMF1..AC-AMF8 registered in that claim note BEFORE
this code existed - honesty law; the AC-AMF prefix, api_market_feed,
market_feed, this suite name and the ledger-apimarket-marketfeed
runner label were all git-grep -F zero-occupancy anchored 2026-10-25,
rc=1).

Face under proof: APIMarketFace.api_market_feed(since_utc, until_utc,
kinds, limit). Every read face answers a question about the market's
current state; nothing answered WHAT JUST HAPPENED. Eleven append-only
event families already existed in separate tables, so this window
merges them into one chronologically ordered public stream:

  - one thirteen-key row shape with None for fields a kind does not
    carry, and no buyer identity anywhere (the feed is public);
  - ascending total order (event_utc, kind_rank, ref_id) with the
    module-fixed kind rank, so a same-second batch has one answer;
  - a half-open [since_utc, until_utc) window with strict instant
    shapes and an inverted-window refusal;
  - a kinds filter normalized to rank order, an empty filter refused;
  - a tail truncation law: limit keeps the NEWEST N events, total is
    always the pre-truncation count;
  - gate order before any read, fail-closed, with frozen table
    digests and a constant ledger tx set;
  - per-kind counts agreeing with the faces that already own them;
  - cross-restart byte identity plus suite hygiene.

Usage: python test_apimarket_marketfeed.py
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

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

KINDS = ("published", "relisted", "price_revised", "metadata_revised",
         "restocked", "purchased", "rated", "rating_revised",
         "rating_replied", "refunded", "delisted")

ROW_KEYS = {"kind", "event_utc", "ref_id", "listing_id",
            "listing_key", "title", "dev_account", "token_price",
            "stars", "previous_stars", "amount", "units", "detail"}

ENVELOPE_KEYS = {"kinds", "since_utc", "until_utc", "limit", "total",
                 "returned", "truncated", "disclaimer", "events"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions")

T_PUB = "2026-10-25T09:00:00Z"
T_RESTOCK = "2026-10-25T09:20:00Z"
T_PRICE = "2026-10-25T09:20:00Z"
T_META = "2026-10-25T09:30:00Z"
T_BUY = "2026-10-25T09:40:00Z"
T_RATE = "2026-10-25T09:50:00Z"
T_REVISE = "2026-10-25T10:00:00Z"
T_REPLY = "2026-10-25T10:10:00Z"
T_REFUND = "2026-10-25T10:20:00Z"
T_DELIST = "2026-10-25T10:30:00Z"
T_RELIST = "2026-10-25T10:40:00Z"

EXPECTED_ORDER = ["published", "price_revised", "restocked",
                  "metadata_revised", "purchased", "rated",
                  "rating_revised", "rating_replied", "refunded",
                  "delisted", "relisted"]

EXPECTED_STAMPS = [T_PUB, T_PRICE, T_RESTOCK, T_META, T_BUY, T_RATE,
                   T_REVISE, T_REPLY, T_REFUND, T_DELIST, T_RELIST]


class Clock(object):
    """Single mutable stamp behind A._now_utc, so every product write
    lands on a pinned instant and windows are testable without
    sleeping."""

    def __init__(self, stamp):
        self.stamp = stamp

    def now_utc(self):
        return self.stamp

    def set(self, stamp):
        self.stamp = stamp


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(env):
    return json.dumps(env, sort_keys=True)


def sha_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


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


def code_of(exc):
    return getattr(exc, "code", None)


def expect_code(fn, code):
    try:
        fn()
    except A.ApiMarketError as exc:
        return code_of(exc) == code
    return False


def kinds_of(events):
    return [e["kind"] for e in events]


def seed_world(led, dk, am):
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMF-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMF-S",
                     "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 400),
                    ("usr:" + who, "credit", 400)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)


def main():
    tmp = tempfile.mkdtemp(prefix="ammarketfeed-")
    db_path = os.path.join(tmp, "feed.db")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)

    original_now = A._now_utc
    clock = Clock(T_PUB)
    A._now_utc = clock.now_utc
    try:
        seed_world(led, dk, am)
        clock.set(T_PUB)
        listing_id = am.publish_api(
            "usr:dana", "flow", "Flow Service", "service payload",
            PAYLOAD, 10, False, 5)["listing_id"]

        # the same-second pair: restock is written FIRST, the price
        # revision second, so the pinned kind rank (price_revised
        # before restocked) is proven independent of write order.
        clock.set(T_RESTOCK)
        am.restock_api("usr:dana", listing_id, 3)
        clock.set(T_PRICE)
        am.revise_price("usr:dana", listing_id, 8)
        clock.set(T_META)
        am.edit_listing("usr:dana", listing_id, title="Flow Service v2")
        clock.set(T_BUY)
        buy = am.purchase_api("usr:bob", listing_id, "ref-amf-buy")
        clock.set(T_RATE)
        am.rate_api("usr:bob", listing_id, 5)
        rating_id = am.api_rating_replies(
            listing_id)["rows"][0]["rating_id"]
        clock.set(T_REVISE)
        am.revise_rating("usr:bob", rating_id, 3)
        clock.set(T_REPLY)
        am.reply_to_rating("usr:dana", rating_id,
                           "thanks for the feedback")
        clock.set(T_REFUND)
        am.refund_api("usr:bob", buy["purchase_id"],
                      reason="flawed service")
        clock.set(T_DELIST)
        am.delist_api("usr:dana", listing_id)
        clock.set(T_RELIST)
        am.relist_api("usr:dana", listing_id)

        # -- AC-AMF1 event family and per-kind fields ----------------
        env = am.api_market_feed()
        rows = env["events"]
        by_kind = {}
        for row in rows:
            by_kind[row["kind"]] = row
        ok1 = (set(env.keys()) == ENVELOPE_KEYS
               and len(rows) == 11
               and set(by_kind) == set(KINDS)
               and all(set(r.keys()) == ROW_KEYS for r in rows)
               and env["disclaimer"] == DISCLAIMER
               and env["total"] == 11 and env["returned"] == 11
               and env["truncated"] is False
               and env["kinds"] == list(KINDS)
               and by_kind["published"]["token_price"] == 10
               and by_kind["published"]["event_utc"] == T_PUB
               and by_kind["published"]["ref_id"] == listing_id
               and by_kind["price_revised"]["token_price"] == 8
               and by_kind["restocked"]["units"] == 3
               and by_kind["metadata_revised"]["detail"]
               == "Flow Service v2"
               and by_kind["purchased"]["token_price"] == 8
               and by_kind["rated"]["stars"] == 5
               and by_kind["rating_revised"]["previous_stars"] == 5
               and by_kind["rating_revised"]["stars"] == 3
               and by_kind["rating_replied"]["detail"]
               == "thanks for the feedback"
               and by_kind["refunded"]["amount"] == 8
               and by_kind["refunded"]["detail"] == "flawed service"
               and by_kind["delisted"]["amount"] is None
               and by_kind["relisted"]["units"] is None
               and by_kind["rated"]["token_price"] is None
               and by_kind["published"]["stars"] is None
               and by_kind["purchased"]["previous_stars"] is None
               and all(r["listing_id"] == listing_id for r in rows)
               and all(r["dev_account"] == "usr:dana" for r in rows))
        record("AC-AMF1", ok1,
               "kinds=%d rows=%d distinct=%d keys=%r"
               % (len(env["kinds"]), len(rows), len(by_kind),
                  sorted(set(len(r) for r in rows))))

        # -- AC-AMF2 total order + determinism ----------------------
        order = kinds_of(rows)
        stamps = [r["event_utc"] for r in rows]
        again = am.api_market_feed()
        ok2 = (order == EXPECTED_ORDER
               and stamps == EXPECTED_STAMPS
               and dumps(env) == dumps(again)
               and A._FEED_KIND_RANK["price_revised"]
               < A._FEED_KIND_RANK["restocked"]
               and order.index("price_revised")
               < order.index("restocked"))
        record("AC-AMF2", ok2,
               "order=%r stable=%s same-second pair=%r"
               % (order, dumps(env) == dumps(again),
                  order[1:3]))

        # -- AC-AMF3 half-open window law ---------------------------
        win = am.api_market_feed(since_utc=T_RESTOCK,
                                 until_utc=T_BUY)
        empty = am.api_market_feed(since_utc="2026-10-25T11:00:00Z",
                                   until_utc="2026-10-25T12:00:00Z")
        ok3 = (kinds_of(win["events"]) == ["price_revised",
                                           "restocked",
                                           "metadata_revised"]
               and win["total"] == 3
               and win["since_utc"] == T_RESTOCK
               and win["until_utc"] == T_BUY
               and empty["events"] == [] and empty["total"] == 0
               and empty["returned"] == 0
               and expect_code(
                   lambda: am.api_market_feed(
                       since_utc=T_BUY, until_utc=T_RESTOCK),
                   A.E_AM_BAD_WINDOW)
               and expect_code(
                   lambda: am.api_market_feed(since_utc="2026-10-25 9:0"),
                   A.E_AM_BAD_WINDOW)
               and expect_code(
                   lambda: am.api_market_feed(until_utc=5),
                   A.E_AM_BAD_WINDOW)
               and expect_code(
                   lambda: am.api_market_feed(
                       since_utc="2026-10-25T09:00:00"),
                   A.E_AM_BAD_WINDOW))
        record("AC-AMF3", ok3,
               "window=%r empty_total=%d refusals=%s"
               % (kinds_of(win["events"]), empty["total"], ok3))

        # -- AC-AMF4 kinds filter law -------------------------------
        pick = am.api_market_feed(kinds=["rated", "published"])
        dup = am.api_market_feed(kinds=["rated", "rated", "published"])
        ok4 = (kinds_of(pick["events"]) == ["published", "rated"]
               and pick["kinds"] == ["published", "rated"]
               and pick["total"] == 2
               and dumps(pick) == dumps(dup)
               and dup["kinds"] == ["published", "rated"]
               and expect_code(
                   lambda: am.api_market_feed(kinds=["nope"]),
                   A.E_AM_BAD_ARGS)
               and expect_code(
                   lambda: am.api_market_feed(kinds=[]),
                   A.E_AM_BAD_ARGS)
               and expect_code(
                   lambda: am.api_market_feed(kinds="rated"),
                   A.E_AM_BAD_ARGS)
               and expect_code(
                   lambda: am.api_market_feed(kinds=5),
                   A.E_AM_BAD_ARGS))
        record("AC-AMF4", ok4,
               "pick=%r echo=%r dedupe=%s"
               % (kinds_of(pick["events"]), pick["kinds"],
                  dumps(pick) == dumps(dup)))

        # -- AC-AMF5 tail truncation law ----------------------------
        tail = am.api_market_feed(limit=3)
        full = am.api_market_feed(limit=11)
        one = am.api_market_feed(limit=1)
        ok5 = (kinds_of(tail["events"]) == ["refunded", "delisted",
                                            "relisted"]
               and tail["total"] == 11 and tail["returned"] == 3
               and tail["truncated"] is True and tail["limit"] == 3
               and full["total"] == 11 and full["returned"] == 11
               and full["truncated"] is False
               and kinds_of(one["events"]) == ["relisted"]
               and one["total"] == 11 and one["returned"] == 1
               and all(expect_code(
                   lambda: am.api_market_feed(limit=bad),
                   A.E_AM_BAD_ARGS)
                   for bad in (0, -1, 1.5, True, "3")))
        record("AC-AMF5", ok5,
               "tail=%r total=%d returned=%d truncated=%s"
               % (kinds_of(tail["events"]), tail["total"],
                  tail["returned"], tail["truncated"]))

        # -- AC-AMF6 gate order before any read ---------------------
        before = market_digests(am)
        tx_before = ledger_tx_ids(led)
        gate_ok = (
            expect_code(
                lambda: am.api_market_feed(since_utc="bad",
                                           kinds=["nope"]),
                A.E_AM_BAD_WINDOW)
            and expect_code(
                lambda: am.api_market_feed(since_utc=T_BUY,
                                           until_utc=T_RESTOCK,
                                           kinds=["nope"]),
                A.E_AM_BAD_WINDOW)
            and expect_code(
                lambda: am.api_market_feed(kinds=["nope"],
                                           limit=0),
                A.E_AM_BAD_ARGS)
            and expect_code(
                lambda: am.api_market_feed(since_utc=T_BUY,
                                           until_utc=T_RESTOCK,
                                           limit=0),
                A.E_AM_BAD_WINDOW))
        after = market_digests(am)
        ok6 = (gate_ok and before == after
               and ledger_tx_ids(led) == tx_before)
        record("AC-AMF6", ok6,
               "gate order=%s digests frozen=%s"
               % (gate_ok, before == after))

        # -- AC-AMF7 derivation and pure read -----------------------
        price_hist = am.api_price_history(listing_id)
        supply_hist = am.api_supply_history(listing_id)
        sales = am.api_sales("usr:dana")
        ratings = am.api_ratings(listing_id)
        replies = am.api_rating_replies(listing_id)
        lifecycle = am.api_listing_lifecycle(listing_id)
        counts = {}
        for row in rows:
            counts[row["kind"]] = counts.get(row["kind"], 0) + 1
        ok7_counts = (
            counts["price_revised"] == price_hist["revision_count"]
            and counts["restocked"] == supply_hist["restock_count"]
            and counts["purchased"] == len(sales["sales"])
            and counts["refunded"] == sales["refunded_count"]
            and counts["rated"] == ratings["rating_count"]
            and counts["rating_replied"] == replies["reply_count"]
            and counts["delisted"] == lifecycle["delist_count"]
            and counts["relisted"] == lifecycle["relist_count"]
            and counts["metadata_revised"]
            == am.api_metadata_history(listing_id)["revision_count"])
        read_before = market_digests(am)
        tx_read = ledger_tx_ids(led)
        for _ in range(3):
            am.api_market_feed()
        am.api_market_feed(since_utc=T_RESTOCK, until_utc=T_BUY)
        read_after = market_digests(am)
        ok7 = (ok7_counts and read_before == read_after
               and ledger_tx_ids(led) == tx_read)
        record("AC-AMF7", ok7,
               "counts=%r digests frozen=%s"
               % (counts, read_before == read_after))

        # -- AC-AMF8 privacy and cross-restart ---------------------
        no_buyer = all("buyer_id" not in r for r in rows)
        snap = dumps(am.api_market_feed())
        am.close()
        dk.close()
        metered.close()
        led.close()
        led, metered, dk, gate, am = build_stack(db_path, cfg,
                                                lobby_cfg)
        restarted = dumps(am.api_market_feed())
        with open(os.path.join(BASE, "apimarket.py"), "rb") as handle:
            src = handle.read()
        ok8 = (no_buyer and snap == restarted
               and b"\r" not in src
               and all(b < 128 for b in src[:2000]))
        record("AC-AMF8", ok8,
               "buyer keys=%s restart identical=%s"
               % (no_buyer, snap == restarted))
    finally:
        A._now_utc = original_now
        try:
            am.close()
            dk.close()
            metered.close()
            led.close()
        except Exception:
            pass

    total = len(RESULTS)
    passed = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d %s" % (passed, total,
                             "PASS" if passed == total else "FAIL"),
          flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())