"""Acceptance suite for the apimarket buyer account-profile face
(BigDomain R2091; canon = the explore-queue row seeded and claimed
in R2091, criteria AC-AMBY1..AC-AMBY8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMBY prefix, the
api_buyer_profile name, this suite name and the
ledger-apimarket-buyerprofile runner label were all git-grep
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.api_buyer_profile. The reading
chain had a seller profile (dev_profile), a market overview
(api_market_stats) and a row-level buyer library (api_library), but
nothing answered the buyer's aggregate question "what has this
account spent, got back and rated". This window pins that face:

  - the eighteen-key envelope on an honest empty account (zeros,
    avg_rating None, disclaimer present) and on the loaded world;
  - spend conservation: net_spent == gross_spent - refunded_total,
    purchase_count == net_purchase_count + refund_count, and
    dev_paid + platform_paid == net_spent exactly (integer split);
  - strict buyer isolation: another buyer's spend, ratings and
    watch rows never leak into this account;
  - a refund lowers only the net side while purchase_count and
    listing_count keep counting the trades that did happen;
  - rating aggregates from this buyer's own ratings only (3.5 and
    5.0 exact, None on an honest empty history);
  - watch_count counts every append-only watch row while
    live_watch_count counts the active set, so an unwatch never
    erases history;
  - the account shape gate runs before any read, fails closed on
    four bad forms and moves zero rows and zero tokens;
  - cross-restart byte identity across three instances.

Usage: python test_apimarket_buyerprofile.py
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
    "buyer_id", "purchase_count", "refund_count",
    "net_purchase_count", "listing_count", "gross_spent",
    "refunded_total", "net_spent", "dev_paid", "platform_paid",
    "rating_count", "avg_rating", "watch_count",
    "live_watch_count", "first_purchase_utc", "last_purchase_utc",
    "disclaimer"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings",
          "apimarket_price_revisions",
          "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_refunds")


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


def seed_world(led, dk, am):
    """dana owns d1 (10) and d2 (3), frank owns f1 (7). bob buys
    d1+d2, carol buys d1, dave buys d2, e1 buys f1."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-AMBY-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-AMBY-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "e1"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3,
                        True)["listing_id"]
    f1 = am.publish_api("usr:frank", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 7,
                        False)["listing_id"]
    bob_d1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")
    bob_d2 = am.purchase_api("usr:bob", d2, "ref-bob-d2")
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    am.purchase_api("usr:dave", d2, "ref-dave-d2")
    am.purchase_api("usr:e1", f1, "ref-e1-f1")
    return d1, d2, f1, bob_d1["purchase_id"], bob_d2["purchase_id"]


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerprofile-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, f1, bob_p1, bob_p2 = seed_world(led, dk, am)

    # -- AC-AMBY1 envelope contract, honest empty account first ---------
    led.ensure_account("usr:idle", census_avatar_id="idle")
    env = am.api_buyer_profile("usr:bob")
    empty = am.api_buyer_profile("usr:idle")
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and env["disclaimer"] == DISCLAIMER
           and env["buyer_id"] == "usr:bob"
           and empty["buyer_id"] == "usr:idle"
           and empty["purchase_count"] == 0
           and empty["refund_count"] == 0
           and empty["net_purchase_count"] == 0
           and empty["listing_count"] == 0
           and empty["gross_spent"] == 0
           and empty["refunded_total"] == 0
           and empty["net_spent"] == 0
           and empty["dev_paid"] == 0
           and empty["platform_paid"] == 0
           and empty["rating_count"] == 0
           and empty["avg_rating"] is None
           and empty["watch_count"] == 0
           and empty["live_watch_count"] == 0
           and empty["first_purchase_utc"] is None
           and empty["last_purchase_utc"] is None)
    record("AC-AMBY1", ok1,
           "keys=%d exact=%r bob_purchases=%d idle=%r avg=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS,
              env["purchase_count"], empty["purchase_count"],
              empty["avg_rating"]))

    # -- AC-AMBY2 spend and pool conservation on the loaded account -----
    paid_row = None
    conn = sqlite3.connect(am.db_path)
    paid_row = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(price_paid), 0)"
        " FROM apimarket_purchases WHERE buyer_id = ?",
        ("usr:bob",)).fetchone()
    conn.close()
    ok2 = (env["purchase_count"] == 2
           and env["listing_count"] == 2
           and env["gross_spent"] == 13
           and env["refund_count"] == 0
           and env["net_purchase_count"] == 2
           and env["refunded_total"] == 0
           and env["net_spent"] == 13
           and env["dev_paid"] + env["platform_paid"]
           == env["net_spent"]
           and env["gross_spent"]
           == env["net_spent"] + env["refunded_total"]
           and env["net_spent"] == env["gross_spent"]
           and env["first_purchase_utc"] is not None
           and env["last_purchase_utc"] is not None
           and env["first_purchase_utc"] <= env["last_purchase_utc"]
           and int(paid_row[0]) == env["purchase_count"]
           and int(paid_row[1]) == env["gross_spent"])
    record("AC-AMBY2", ok2,
           "purchases=%d listings=%d gross=%d net=%d dev+plat=%d/%d"
           " utc=%r..%r"
           % (env["purchase_count"], env["listing_count"],
              env["gross_spent"], env["net_spent"],
              env["dev_paid"], env["platform_paid"],
              env["first_purchase_utc"], env["last_purchase_utc"]))

    # -- AC-AMBY3 strict buyer isolation -------------------------------
    carol = am.api_buyer_profile("usr:carol")
    dave = am.api_buyer_profile("usr:dave")
    e1 = am.api_buyer_profile("usr:e1")
    ok3 = (carol["purchase_count"] == 1
           and carol["gross_spent"] == 10
           and dave["purchase_count"] == 1
           and dave["gross_spent"] == 3
           and e1["purchase_count"] == 1
           and e1["gross_spent"] == 7
           and carol["gross_spent"] != env["gross_spent"]
           and carol["listing_count"] == 1
           and e1["listing_count"] == 1)
    record("AC-AMBY3", ok3,
           "carol=%d/%d dave=%d/%d e1=%d/%d bob=%d/%d"
           % (carol["purchase_count"], carol["gross_spent"],
              dave["purchase_count"], dave["gross_spent"],
              e1["purchase_count"], e1["gross_spent"],
              env["purchase_count"], env["gross_spent"]))

    # -- AC-AMBY4 a refund lowers only the net side --------------------
    refund = am.refund_api("usr:bob", bob_p2, "suite refund")
    after_refund = am.api_buyer_profile("usr:bob")
    ok4 = (after_refund["refund_count"] == 1
           and after_refund["purchase_count"] == 2
           and after_refund["net_purchase_count"] == 1
           and after_refund["listing_count"] == 2
           and after_refund["gross_spent"] == 13
           and after_refund["refunded_total"] == refund["amount"]
           and after_refund["net_spent"]
           == 13 - refund["amount"]
           and after_refund["dev_paid"]
           == env["dev_paid"] - refund["dev_share"]
           and after_refund["platform_paid"]
           == env["platform_paid"] - refund["platform_share"]
           and after_refund["dev_paid"] + after_refund["platform_paid"]
           == after_refund["net_spent"]
           and after_refund["purchase_count"]
           == after_refund["net_purchase_count"]
           + after_refund["refund_count"])
    record("AC-AMBY4", ok4,
           "refund=%r/%r/%r purchases=%d net_purchases=%d"
           " gross=%d net=%d dev+plat=%d/%d"
           % (refund["amount"], refund["dev_share"],
              refund["platform_share"],
              after_refund["purchase_count"],
              after_refund["net_purchase_count"],
              after_refund["gross_spent"], after_refund["net_spent"],
              after_refund["dev_paid"], after_refund["platform_paid"]))

    # -- AC-AMBY5 rating aggregates from this buyer's own ratings ------
    am.rate_api("usr:bob", d1, 4)
    am.rate_api("usr:bob", d2, 3)
    am.rate_api("usr:dave", d2, 5)
    bob_rated = am.api_buyer_profile("usr:bob")
    dave_rated = am.api_buyer_profile("usr:dave")
    carol_rated = am.api_buyer_profile("usr:carol")
    ok5 = (bob_rated["rating_count"] == 2
           and bob_rated["avg_rating"] == 3.5
           and dave_rated["rating_count"] == 1
           and dave_rated["avg_rating"] == 5.0
           and carol_rated["rating_count"] == 0
           and carol_rated["avg_rating"] is None)
    record("AC-AMBY5", ok5,
           "bob=%d/%r dave=%d/%r carol=%d/%r"
           % (bob_rated["rating_count"], bob_rated["avg_rating"],
              dave_rated["rating_count"], dave_rated["avg_rating"],
              carol_rated["rating_count"], carol_rated["avg_rating"]))

    # -- AC-AMBY6 watch history vs the live active set -----------------
    am.watch_api("usr:bob", d1)
    am.watch_api("usr:bob", f1)
    am.unwatch_api("usr:bob", f1)
    bob_watch = am.api_buyer_profile("usr:bob")
    carol_watch = am.api_buyer_profile("usr:carol")
    conn = sqlite3.connect(am.db_path)
    watch_rows = conn.execute(
        "SELECT COUNT(*) FROM apimarket_watchlist WHERE buyer_id = ?",
        ("usr:bob",)).fetchone()[0]
    conn.close()
    ok6 = (bob_watch["watch_count"] == 2
           and bob_watch["live_watch_count"] == 1
           and int(watch_rows) == bob_watch["watch_count"]
           and carol_watch["watch_count"] == 0
           and carol_watch["live_watch_count"] == 0)
    record("AC-AMBY6", ok6,
           "bob=%d/%d rows=%d carol=%d/%d"
           % (bob_watch["watch_count"],
              bob_watch["live_watch_count"], int(watch_rows),
              carol_watch["watch_count"],
              carol_watch["live_watch_count"]))

    # -- AC-AMBY7 the account gate runs first and moves nothing --------
    tx_before = ledger_tx_ids(led)
    digests_before = market_digests(am)
    bad_forms = [None, "", "bob", 123]
    codes = []
    for bad in bad_forms:
        try:
            am.api_buyer_profile(bad)
            codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            codes.append(exc.code)
    tx_after = ledger_tx_ids(led)
    digests_after = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    ok7 = (codes == [A.E_AM_BAD_ACCOUNT] * 4
           and tx_before == tx_after
           and digests_before == digests_after
           and shas_before == shas_after)
    record("AC-AMBY7", ok7,
           "codes=%r tx_equal=%r digests_equal=%r files_equal=%r"
           % (codes, tx_before == tx_after,
              digests_before == digests_after,
              shas_before == shas_after))

    # -- AC-AMBY8 cross-restart byte identity ---------------------------
    final_bob = am.api_buyer_profile("usr:bob")
    first = dumps(final_bob)
    first_empty = dumps(am.api_buyer_profile("usr:idle"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second = dumps(am.api_buyer_profile("usr:bob"))
    second_empty = dumps(am.api_buyer_profile("usr:idle"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third = dumps(am.api_buyer_profile("usr:bob"))
    third_empty = dumps(am.api_buyer_profile("usr:idle"))
    ok8 = (first == second == third
           and first_empty == second_empty == third_empty)
    record("AC-AMBY8", ok8,
           "sha16=%s identical=%r empty_identical=%r"
           % (hashlib.sha256(first.encode("utf-8")).hexdigest()[:16],
              first == second == third,
              first_empty == second_empty == third_empty))

    close_stack(am, dk, metered, led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    verdict = "SUITE PASS %d/%d" % (passed, total)
    if passed != total:
        verdict = "SUITE FAIL %d/%d" % (passed, total)
    print(verdict, flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())