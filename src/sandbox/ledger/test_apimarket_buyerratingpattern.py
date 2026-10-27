"""Acceptance suite for the apimarket buyer star-giving tendency face
(BigDomain R2164; canon = the R2149 reseed row claimed in R2164,
criteria AC-BRP1..AC-BRP8 registered in that claim row BEFORE this code
existed - honesty law; the AC-BRP prefix and the api_buyer_rating_pattern
name occupy only that seed row text, while
test_apimarket_buyerratingpattern, ledger-apimarket-buyerratingpattern,
tendency_delta, harsh_ratio and rating_coverage were all git-grep
zero-occupancy anchored against HEAD 2026-10-27, rc=1).

Face under proof: APIMarketFace.api_buyer_rating_pattern. The buyer
profile face answers only rating_count and an average, so "is this
resident consistently harsh or generous, is it stricter than the
market, and how did its stars spread" had no face at all. This suite
pins the new aggregate face:

  - the twenty-key envelope, the five-bucket distribution and the
    honest empty world first;
  - distribution conservation and every derived figure (star_sum,
    avg, min/max, harsh/neutral/generous and the two ratios);
  - the effective-stars seam: a revision moves distribution and every
    aggregate in one step, the base stamp is never rewritten, and a
    revert restores all star-derived fields byte for byte while the
    revision counters legitimately keep growing;
  - count authority on this buyer's own ratings only, with delisting,
    relisting and a refund never removing a rating;
  - the market-relative tendency (market_avg over the whole market by
    design, tendency_delta and its None edges);
  - purchase coverage including refunded purchases;
  - the seven-form account gate, the pure-read law and cross-restart
    byte identity.

Usage: python test_apimarket_buyerratingpattern.py
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
    "buyer_id", "rating_count", "listing_count", "revision_count",
    "revised_rating_count", "star_sum", "avg_stars", "min_stars",
    "max_stars", "harsh_count", "neutral_count", "generous_count",
    "harsh_ratio", "generous_ratio", "market_avg_stars",
    "tendency_delta", "purchase_count", "rating_coverage",
    "star_distribution", "disclaimer"}

STAR_DERIVED = (
    "rating_count", "listing_count", "star_sum", "avg_stars",
    "min_stars", "max_stars", "harsh_count", "neutral_count",
    "generous_count", "harsh_ratio", "generous_ratio",
    "star_distribution")

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions",
          "apimarket_rating_revisions")


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


def star_fields(env):
    return {k: env[k] for k in STAR_DERIVED}


def seed_world(led, dk, am):
    """dana owns d1/d2 (data) and f1 (tools); gina owns g1 (media).
    bob buys d1/d2/f1 and rates 5/2/4 (the revision subject is d2).
    carol buys d1 and rates 1, then refunds the purchase - the rating
    survives the refund. dave buys g1 and rates 5 (single rating).
    erin buys d1, refunds it and never rates, so her coverage is 0.0
    with one purchase."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-BRP-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-BRP-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:gina", "gina-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True,
                        category="data")["listing_id"]
    f1 = am.publish_api("usr:dana", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 7,
                        False, category="tools")["listing_id"]
    g1 = am.publish_api("usr:gina", "media-pack", "Media Pack API",
                        "media pipeline pack", PAYLOAD, 6, False,
                        category="media")["listing_id"]
    am.purchase_api("usr:bob", d1, "ref-bob-d1")
    am.purchase_api("usr:bob", d2, "ref-bob-d2")
    am.purchase_api("usr:bob", f1, "ref-bob-f1")
    carol_d1 = am.purchase_api("usr:carol", d1, "ref-carol-d1")
    am.purchase_api("usr:dave", g1, "ref-dave-g1")
    erin_d1 = am.purchase_api("usr:erin", d1, "ref-erin-d1")
    am.refund_api("usr:carol", carol_d1["purchase_id"],
                  "listing did not match description")
    am.refund_api("usr:erin", erin_d1["purchase_id"],
                  "changed my mind")
    r_bob_d1 = am.rate_api("usr:bob", d1, 5)["rating_id"]
    r_bob_d2 = am.rate_api("usr:bob", d2, 2)["rating_id"]
    r_bob_f1 = am.rate_api("usr:bob", f1, 4)["rating_id"]
    r_carol = am.rate_api("usr:carol", d1, 1)["rating_id"]
    r_dave = am.rate_api("usr:dave", g1, 5)["rating_id"]
    return {"d1": d1, "d2": d2, "f1": f1, "g1": g1,
            "r_bob_d1": r_bob_d1, "r_bob_d2": r_bob_d2,
            "r_bob_f1": r_bob_f1, "r_carol": r_carol,
            "r_dave": r_dave}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerratingpattern-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    ids = seed_world(led, dk, am)

    # -- AC-BRP1 the contract, honest empty first ----------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-brp-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_rating_pattern("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    bob = am.api_buyer_rating_pattern("usr:bob")
    ok1 = (set(bob.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and bob["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["buyer_id"] == "usr:nobody"
           and empty["rating_count"] == 0
           and empty["listing_count"] == 0
           and empty["revision_count"] == 0
           and empty["revised_rating_count"] == 0
           and empty["star_sum"] == 0
           and empty["avg_stars"] is None
           and empty["min_stars"] is None
           and empty["max_stars"] is None
           and empty["harsh_count"] == 0
           and empty["neutral_count"] == 0
           and empty["generous_count"] == 0
           and empty["harsh_ratio"] is None
           and empty["generous_ratio"] is None
           and empty["market_avg_stars"] is None
           and empty["tendency_delta"] is None
           and empty["purchase_count"] == 0
           and empty["rating_coverage"] is None
           and empty["star_distribution"]
           == {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
           and bob["star_distribution"]
           == {"1": 0, "2": 1, "3": 0, "4": 1, "5": 1})
    record("AC-BRP1", ok1,
           "env_keys=%d exact=%r dist=%r empty_dist=%r"
           % (len(bob), set(bob.keys()) == ENVELOPE_KEYS,
              bob["star_distribution"], empty["star_distribution"]))

    # -- AC-BRP2 distribution conservation and derivations -------------
    carol = am.api_buyer_rating_pattern("usr:carol")
    dave = am.api_buyer_rating_pattern("usr:dave")
    ok2 = True
    for env in (bob, carol, dave):
        dist = env["star_distribution"]
        count = env["rating_count"]
        ok2 = (ok2
               and sum(dist.values()) == count
               and env["harsh_count"] + env["neutral_count"]
               + env["generous_count"] == count
               and env["star_sum"]
               == sum(int(k) * dist[k] for k in dist)
               and env["avg_stars"] == float(env["star_sum"]) / count
               and env["min_stars"] == min(
                   int(k) for k in dist if dist[k])
               and env["max_stars"] == max(
                   int(k) for k in dist if dist[k])
               and env["harsh_ratio"]
               == float(env["harsh_count"]) / count
               and env["generous_ratio"]
               == float(env["generous_count"]) / count)
    ok2 = (ok2
           and bob["rating_count"] == 3
           and bob["listing_count"] == 3
           and bob["star_sum"] == 11
           and abs(bob["avg_stars"] - 11.0 / 3) < 1e-12
           and bob["harsh_count"] == 1
           and bob["neutral_count"] == 0
           and bob["generous_count"] == 2
           and bob["min_stars"] == 2
           and bob["max_stars"] == 5
           and carol["harsh_count"] == 1
           and carol["generous_count"] == 0
           and carol["avg_stars"] == 1.0
           and dave["rating_count"] == 1
           and dave["min_stars"] == dave["max_stars"] == 5
           and dave["revision_count"] == 0
           and bob["revision_count"] == 0
           and bob["revised_rating_count"] == 0)
    record("AC-BRP2", ok2,
           "bob avg=%r harsh=%d generous=%d carol avg=%r dave=%r"
           % (bob["avg_stars"], bob["harsh_count"],
              bob["generous_count"], carol["avg_stars"],
              (dave["min_stars"], dave["max_stars"])))

    # -- AC-BRP3 the effective-stars seam ------------------------------
    base_before = dumps(bob)
    am.revise_rating("usr:bob", ids["r_bob_d2"], 5)
    revised = am.api_buyer_rating_pattern("usr:bob")
    base_row = sqlite3.connect(am.db_path).execute(
        "SELECT stars FROM apimarket_ratings WHERE rating_id = ?",
        (ids["r_bob_d2"],)).fetchone()[0]
    ok3 = (revised["star_distribution"]
           == {"1": 0, "2": 0, "3": 0, "4": 1, "5": 2}
           and revised["star_sum"] == 14
           and abs(revised["avg_stars"] - 14.0 / 3) < 1e-12
           and revised["min_stars"] == 4
           and revised["max_stars"] == 5
           and revised["harsh_count"] == 0
           and revised["generous_count"] == 3
           and revised["revision_count"] == 1
           and revised["revised_rating_count"] == 1
           and base_row == 2)
    am.revise_rating("usr:bob", ids["r_bob_d2"], 2)
    reverted = am.api_buyer_rating_pattern("usr:bob")
    ok3 = (ok3
           and star_fields(reverted) == star_fields(bob)
           and reverted["revision_count"] == 2
           and reverted["revised_rating_count"] == 1
           and dumps(reverted) != base_before)
    record("AC-BRP3", ok3,
           "revised_dist=%r sum=%d base_row=%d revert_stars=%r"
           " rev_counts=%r"
           % (revised["star_distribution"], revised["star_sum"],
              base_row, star_fields(reverted) == star_fields(bob),
              (reverted["revision_count"],
               reverted["revised_rating_count"])))

    # -- AC-BRP4 count authority and lifecycle -------------------------
    before4 = dumps(am.api_buyer_rating_pattern("usr:bob"))
    am.delist_api("usr:dana", ids["d1"])
    after_delist = am.api_buyer_rating_pattern("usr:bob")
    am.relist_api("usr:dana", ids["d1"])
    after_relist = am.api_buyer_rating_pattern("usr:bob")
    carol_after_refund = am.api_buyer_rating_pattern("usr:carol")
    bob_rates_carol_listing = None
    try:
        am.rate_api("usr:bob", ids["g1"], 1)
        bob_rates_carol_listing = "NO-ERROR"
    except A.ApiMarketError as exc:
        bob_rates_carol_listing = getattr(exc, "code", "?")
    ok4 = (dumps(after_delist) == before4
           and dumps(after_relist) == before4
           and carol_after_refund["rating_count"] == 1
           and carol_after_refund["star_distribution"]["1"] == 1
           and carol_after_refund["harsh_count"] == 1
           and bob["rating_count"] == 3
           and bob_rates_carol_listing in ("E_AM_NOT_BUYER",
                                           "E_AM_UNKNOWN_LISTING"))
    record("AC-BRP4", ok4,
           "delist_same=%r relist_same=%r carol_after_refund=%d"
           " foreign_rate=%r"
           % (dumps(after_delist) == before4,
              dumps(after_relist) == before4,
              carol_after_refund["rating_count"],
              bob_rates_carol_listing))

    # -- AC-BRP5 the market-relative tendency --------------------------
    market_rows = sqlite3.connect(am.db_path).execute(
        "SELECT COUNT(*), SUM(CASE WHEN r.revision_id IS NULL THEN g.stars"
        " ELSE r.stars END)"
        " FROM apimarket_ratings g LEFT JOIN"
        " (SELECT rating_id, MAX(revision_id) AS revision_id"
        "  FROM apimarket_rating_revisions GROUP BY rating_id) x"
        " ON x.rating_id = g.rating_id"
        " LEFT JOIN apimarket_rating_revisions r"
        " ON r.revision_id = x.revision_id").fetchone()
    market_avg = float(market_rows[1]) / market_rows[0]
    bob5 = am.api_buyer_rating_pattern("usr:bob")
    carol5 = am.api_buyer_rating_pattern("usr:carol")
    nobody = am.api_buyer_rating_pattern("usr:nobody")
    ok5 = (bob5["market_avg_stars"] == market_avg
           and carol5["market_avg_stars"] == market_avg
           and abs(bob5["tendency_delta"]
                   - (bob5["avg_stars"] - market_avg)) < 1e-12
           and abs(carol5["tendency_delta"] + 2.4) < 1e-12
           and bob5["tendency_delta"] > 0
           and carol5["tendency_delta"] < 0
           and nobody["rating_count"] == 0
           and nobody["avg_stars"] is None
           and nobody["market_avg_stars"] == market_avg
           and nobody["tendency_delta"] is None)
    record("AC-BRP5", ok5,
           "market_avg=%r bob_delta=%r carol_delta=%r nobody_delta=%r"
           % (market_avg, bob5["tendency_delta"],
              carol5["tendency_delta"], nobody["tendency_delta"]))

    # -- AC-BRP6 purchase coverage including refunds -------------------
    erin = am.api_buyer_rating_pattern("usr:erin")
    ok6 = (bob5["purchase_count"] == 3
           and bob5["rating_coverage"] == 1.0
           and erin["purchase_count"] == 1
           and erin["rating_count"] == 0
           and erin["rating_coverage"] == 0.0
           and carol5["purchase_count"] == 1
           and carol5["rating_coverage"] == 1.0
           and all(env["rating_count"] <= env["purchase_count"]
                   for env in (bob5, carol5, dave, erin)))
    record("AC-BRP6", ok6,
           "bob_cov=%r erin=%r carol_cov=%r"
           % (bob5["rating_coverage"],
              (erin["purchase_count"], erin["rating_count"],
               erin["rating_coverage"]), carol5["rating_coverage"]))

    # -- AC-BRP7 the gate family and the pure-read law -----------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    acct_codes = []
    for bad in (None, "", "  ", 123, [], {"usr:x": 1}, "carol"):
        try:
            am.api_buyer_rating_pattern(bad)
            acct_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            acct_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_buyer_rating_pattern("usr:")
    first = dumps(am.api_buyer_rating_pattern("usr:bob"))
    second = dumps(am.api_buyer_rating_pattern("usr:bob"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (acct_codes == ["E_AM_BAD_ACCOUNT"] * 7
           and prefix["rating_count"] == 0
           and prefix["star_distribution"]
           == {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
           and prefix["market_avg_stars"] == market_avg
           and first == second
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-BRP7", ok7,
           "acct=%r prefix=%r repeat=%r frozen=%r tx=%r"
           % (acct_codes, prefix["rating_count"], first == second,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-BRP8 cross-restart identity and the wiring ------------------
    final_bob = dumps(am.api_buyer_rating_pattern("usr:bob"))
    final_dave = dumps(am.api_buyer_rating_pattern("usr:dave"))
    final_nobody = dumps(am.api_buyer_rating_pattern("usr:nobody"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_bob = dumps(am.api_buyer_rating_pattern("usr:bob"))
    second_dave = dumps(am.api_buyer_rating_pattern("usr:dave"))
    second_nobody = dumps(am.api_buyer_rating_pattern("usr:nobody"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_bob = dumps(am.api_buyer_rating_pattern("usr:bob"))
    third_dave = dumps(am.api_buyer_rating_pattern("usr:dave"))
    third_nobody = dumps(am.api_buyer_rating_pattern("usr:nobody"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_buyer_rating_pattern("usr:bob")
        am.api_buyer_rating_pattern("usr:dave")
        am.api_buyer_rating_pattern("usr:nobody")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (final_bob == second_bob == third_bob
           and final_dave == second_dave == third_dave
           and final_nobody == second_nobody == third_nobody
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-buyerratingpattern" in runner_text)
    record("AC-BRP8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final_bob.encode("utf-8"))
              .hexdigest()[:16],
              final_bob == second_bob == third_bob and
              final_dave == second_dave == third_dave and
              final_nobody == second_nobody == third_nobody,
              tx_b == tx_a, dig_b == dig_a,
              shas_before == shas_after,
              "ledger-apimarket-buyerratingpattern" in runner_text))

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