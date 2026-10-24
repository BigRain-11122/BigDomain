"""Acceptance suite for the apimarket buyer rating-revision faces
(BigDomain R2094; canon = the explore-queue row seeded and claimed in
R2094, criteria AC-AMRV1..AC-AMRV8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMRV prefix, the
revise_rating / api_rating_history names, the
apimarket_rating_revisions table, the E_AM_RATING_UNCHANGED code,
this suite name and the ledger-apimarket-ratingrev runner label were
all git-grep -F zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.revise_rating /
api_rating_history. The rating face used to be write-once (one
immutable stamp per buyer+listing, E_AM_RATE_DUP forever), so a
mis-clicked star stayed welded to the seller's reputation - the only
trust axis on this market with no remedy door. This window pins the
correction leg:

  - one eight-key revision row and one eight-key history envelope,
    the base rating row never rewritten;
  - the pinned gate order (account shape, rating-id shape, existence,
    ownership, star shape, unchanged state) with fail-closed zero
    side effects;
  - multi-revision chains whose previous_stars is the value in force
    at that moment (self-describing), revising back to an older value
    legal, a same-value revision refused with the first stamp
    preserved;
  - one effective-value seam feeding all five aggregate faces
    (api_view, api_ratings, api_rating_replies, dev_profile,
    api_buyer_profile) with rating_count unchanged by a revision;
  - zero drift for never-revised ratings (legacy byte identity);
  - pure read and cross-restart byte identity;
  - runner wiring plus suite hygiene (ASCII, no network imports,
    world outside the repo).

Usage: python test_apimarket_ratingrev.py
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

DOOR_KEYS = {"revision_id", "rating_id", "listing_id", "buyer_id",
             "previous_stars", "stars", "revised_utc", "disclaimer"}
ENVELOPE_KEYS = {"rating_id", "listing_id", "buyer_id", "base_stars",
                 "effective_stars", "revision_count", "rated_utc",
                 "disclaimer", "revisions"}
REV_KEYS = {"revision_id", "previous_stars", "stars", "revised_utc"}

FROZEN_TABLES = ("apimarket_listings", "apimarket_purchases",
                 "apimarket_ratings", "apimarket_refunds",
                 "apimarket_price_revisions",
                 "apimarket_listing_revisions",
                 "apimarket_delistings", "apimarket_relistings")
POOLS = ("pool:reserve", "pool:share")


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


def frozen_digests(am):
    conn = sqlite3.connect(am.db_path)
    out = {t: table_digest(conn, t) for t in FROZEN_TABLES}
    conn.close()
    return out


def revision_rows(am):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT revision_id, rating_id, listing_id, buyer_id,"
        " previous_stars, stars, revised_utc FROM"
        " apimarket_rating_revisions ORDER BY revision_id").fetchall()
    conn.close()
    return rows


def base_stars(am, rating_id):
    conn = sqlite3.connect(am.db_path)
    row = conn.execute(
        "SELECT stars, rated_utc FROM apimarket_ratings"
        " WHERE rating_id = ?", (rating_id,)).fetchone()
    conn.close()
    return row


def ledger_tx_ids(led):
    conn = sqlite3.connect(led.db_path)
    ids = set(str(r[0]) for r in conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall())
    conn.close()
    return ids


def pool_balances(led):
    return {pool: led.balance(pool) for pool in POOLS}


def read_family(am, ids):
    out = {}
    for lid in ids:
        out["view-%d" % lid] = dumps(am.api_view(lid))
        out["ratings-%d" % lid] = dumps(am.api_ratings(lid))
        out["replies-%d" % lid] = dumps(am.api_rating_replies(lid))
        out["history-%d" % lid] = dumps(
            am.api_rating_history(_first_rating_id(am, lid)))
    out["devprofile"] = dumps(am.dev_profile("usr:dana"))
    out["buyerprofile"] = dumps(am.api_buyer_profile("usr:bob"))
    out["market"] = dumps(am.api_market_stats())
    return out


def _first_rating_id(am, listing_id):
    conn = sqlite3.connect(am.db_path)
    row = conn.execute(
        "SELECT MIN(rating_id) FROM apimarket_ratings"
        " WHERE listing_id = ?", (listing_id,)).fetchone()
    conn.close()
    return int(row[0])


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


def expect(am, buyer_id, rating_id, stars):
    try:
        am.revise_rating(buyer_id, rating_id, stars)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def expect_history(am, rating_id):
    try:
        am.api_rating_history(rating_id)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am):
    """Owner dana with two listings; bob buys and rates both, carol
    buys and rates d1. Bob's own two ratings give the multi-listing
    aggregate anchors; carol is the ownership-gate outsider."""
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AMRV-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AMRV-S",
                     "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    am.purchase_api("usr:bob", d1, "ref-bob-d1")
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    am.purchase_api("usr:bob", d2, "ref-bob-d2")
    r_bob_d1 = am.rate_api("usr:bob", d1, 5)
    r_carol_d1 = am.rate_api("usr:carol", d1, 3)
    r_bob_d2 = am.rate_api("usr:bob", d2, 4)
    return d1, d2, r_bob_d1, r_carol_d1, r_bob_d2


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-ratingrev-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, rb1, rc1, rb2 = seed_world(led, dk, am)

    b1 = base_stars(am, rb1["rating_id"])
    unrevised_view_d2 = dumps(am.api_view(d2))
    unrevised_ratings_d2 = dumps(am.api_ratings(d2))
    tx_before = ledger_tx_ids(led)
    pools_before = pool_balances(led)

    # -- AC-AMRV1 contract + base row untouched --------------------------
    count_before = len(revision_rows(am))
    door = am.revise_rating("usr:bob", rb1["rating_id"], 1)
    rows1 = revision_rows(am)
    b1_after = base_stars(am, rb1["rating_id"])
    ok1 = (set(door.keys()) == DOOR_KEYS
           and door["rating_id"] == rb1["rating_id"]
           and door["listing_id"] == d1
           and door["buyer_id"] == "usr:bob"
           and door["previous_stars"] == 5
           and door["stars"] == 1
           and door["disclaimer"] == DISCLAIMER
           and len(rows1) == count_before + 1
           and rows1[-1][0] == door["revision_id"]
           and rows1[-1][4] == 5 and rows1[-1][5] == 1
           and b1_after == b1 and b1_after[0] == 5)
    record("AC-AMRV1", ok1,
           "door keys=%r prev/base=%r/%r rows=%d base untouched=%r"
           % (set(door.keys()) == DOOR_KEYS, door["previous_stars"],
              b1_after[0], len(rows1), b1_after == b1))

    # -- AC-AMRV2 pinned gate order + fail-closed battery ----------------
    frozen_mid = frozen_digests(am)
    revs_mid = len(revision_rows(am))
    bad_account = [expect(am, bad, rb1["rating_id"], 2)
                   for bad in ("", "bob", "usr:", None)]
    bad_id = [expect(am, "usr:bob", bad, 2)
              for bad in (0, -1, "1", True, None)]
    unknown_beat_stars = expect(am, "usr:bob", 999999, 9)
    not_buyer = expect(am, "usr:carol", rb1["rating_id"], 9)
    not_buyer_good = expect(am, "usr:carol", rb1["rating_id"], 4)
    bad_stars = [expect(am, "usr:bob", rb1["rating_id"], bad)
                 for bad in (0, 6, True, "5")]
    frozen_after_batt = frozen_digests(am)
    revs_after_batt = len(revision_rows(am))
    ok2 = (bad_account == ["E_AM_BAD_ACCOUNT", "E_AM_BAD_ACCOUNT",
                           "E_AM_NOT_BUYER", "E_AM_BAD_ACCOUNT"]
           and bad_id == ["E_AM_BAD_ARGS"] * 5
           and unknown_beat_stars == "E_AM_UNKNOWN_RATING"
           and not_buyer == "E_AM_NOT_BUYER"
           and not_buyer_good == "E_AM_NOT_BUYER"
           and bad_stars == ["E_AM_BAD_STARS"] * 4
           and frozen_after_batt == frozen_mid
           and revs_after_batt == revs_mid)
    record("AC-AMRV2", ok2,
           "account=%r id=%r unknown-before-stars=%s not-buyer=%s/%s"
           " stars=%r frozen=%r rows=%d"
           % (bad_account, bad_id, unknown_beat_stars, not_buyer,
              not_buyer_good, bad_stars,
              frozen_after_batt == frozen_mid, revs_after_batt))

    # -- AC-AMRV3 multi-revision chain (self-describing) -----------------
    second = am.revise_rating("usr:bob", rb1["rating_id"], 4)
    third = am.revise_rating("usr:bob", rb1["rating_id"], 1)
    chain = [(r[4], r[5]) for r in revision_rows(am)]
    env3 = am.api_rating_history(rb1["rating_id"])
    ok3 = (second["previous_stars"] == 1
           and third["previous_stars"] == 4
           and third["stars"] == 1
           and second["revision_id"] > door["revision_id"]
           and third["revision_id"] > second["revision_id"]
           and chain == [(5, 1), (1, 4), (4, 1)]
           and env3["effective_stars"] == 1
           and env3["base_stars"] == 5
           and env3["revision_count"] == 3
           and base_stars(am, rb1["rating_id"]) == b1)
    record("AC-AMRV3", ok3,
           "prev-chain=%r ids increasing=%r effective/base=%r/%r"
           " back-to-older legal=%r"
           % (chain, (door["revision_id"] < second["revision_id"]
                      < third["revision_id"]), env3["effective_stars"],
              env3["base_stars"], third["stars"] == 1))

    # -- AC-AMRV4 unchanged refusal (judged on EFFECTIVE value) ----------
    revs_pre4 = len(revision_rows(am))
    unchanged = expect(am, "usr:bob", rb1["rating_id"], 1)
    revs_post4 = len(revision_rows(am))
    hist4 = am.api_rating_history(rb1["rating_id"])
    first_rev = revision_rows(am)[0]
    ok4 = (unchanged == "E_AM_RATING_UNCHANGED"
           and revs_post4 == revs_pre4
           and hist4["effective_stars"] == 1
           and hist4["revisions"][0]["revision_id"] == first_rev[0]
           and hist4["revisions"][0]["revised_utc"] == first_rev[6]
           and hist4["revisions"][0]["stars"] == 1)
    record("AC-AMRV4", ok4,
           "same-value=%s rows=%d/%d effective=%d first stamp stable=%r"
           % (unchanged, revs_pre4, revs_post4,
              hist4["effective_stars"],
              hist4["revisions"][0]["revision_id"] == first_rev[0]))

    # -- AC-AMRV5 one effective seam feeding five aggregates -------------
    am.revise_rating("usr:bob", rb1["rating_id"], 2)
    view = am.api_view(d1)
    ratings = am.api_ratings(d1)
    replies = am.api_rating_replies(d1)
    profile = am.dev_profile("usr:dana")
    buyer = am.api_buyer_profile("usr:bob")
    reply_star = {r["rating_id"]: r["stars"] for r in replies["rows"]}
    ok5 = (view["rating_count"] == 2
           and abs(view["rating_avg"] - 2.5) < 1e-9
           and ratings["rating_count"] == 2
           and abs(ratings["rating_avg"] - 2.5) < 1e-9
           and [r["stars"] for r in ratings["ratings"]] == [2, 3]
           and reply_star[rb1["rating_id"]] == 2
           and reply_star[rc1["rating_id"]] == 3
           and abs(profile["avg_rating"] - 3.0) < 1e-9
           and profile["rating_count"] == 3
           and abs(buyer["avg_rating"] - 3.0) < 1e-9
           and buyer["rating_count"] == 2)
    record("AC-AMRV5", ok5,
           "view=%r/%r ratings=%r profile=%r buyer=%r"
           % (view["rating_count"], view["rating_avg"],
              [r["stars"] for r in ratings["ratings"]],
              profile["avg_rating"], buyer["avg_rating"]))

    # -- AC-AMRV6 never-revised rating zero drift ------------------------
    ok6 = (dumps(am.api_view(d2)) == unrevised_view_d2
           and dumps(am.api_ratings(d2)) == unrevised_ratings_d2)
    hist_d2 = am.api_rating_history(rb2["rating_id"])
    ok6 = (ok6 and hist_d2["base_stars"] == 4
           and hist_d2["effective_stars"] == 4
           and hist_d2["revision_count"] == 0
           and hist_d2["revisions"] == [])
    record("AC-AMRV6", ok6,
           "d2 view/ratings byte-identical=%r clean history=%r"
           % (dumps(am.api_view(d2)) == unrevised_view_d2
              and dumps(am.api_ratings(d2)) == unrevised_ratings_d2,
              hist_d2["revision_count"] == 0))

    # -- AC-AMRV7 history envelope, gates and isolation -----------------
    env7 = am.api_rating_history(rb1["rating_id"])
    rev_gates = [expect_history(am, bad)
                 for bad in (0, -1, "1", True, None)]
    unknown7 = expect_history(am, 999999)
    ok7 = (set(env7.keys()) == ENVELOPE_KEYS
           and env7["rating_id"] == rb1["rating_id"]
           and env7["listing_id"] == d1
           and env7["buyer_id"] == "usr:bob"
           and env7["base_stars"] == 5
           and env7["effective_stars"] == 2
           and env7["revision_count"] == 4
           and [r["stars"] for r in env7["revisions"]]
           == [1, 4, 1, 2]
           and all(set(r.keys()) == REV_KEYS
                   for r in env7["revisions"])
           and rev_gates == ["E_AM_BAD_ARGS"] * 5
           and unknown7 == "E_AM_UNKNOWN_RATING"
           and env7["disclaimer"] == DISCLAIMER)
    record("AC-AMRV7", ok7,
           "envelope=%r revisions=%r bad-id=%r unknown=%s"
           % (set(env7.keys()) == ENVELOPE_KEYS,
              [r["stars"] for r in env7["revisions"]], rev_gates,
              unknown7))

    # -- AC-AMRV8 pure read, token freeze, restart identity, wiring ------
    reply_before = dumps(am.api_rating_replies(d1))
    frozen_pre8 = frozen_digests(am)
    tx_after = ledger_tx_ids(led)
    pools_after = pool_balances(led)
    am.revise_rating("usr:bob", rb2["rating_id"], 2)
    frozen_post8 = frozen_digests(am)
    reply_after = dumps(am.api_rating_replies(d1))
    tx_post = ledger_tx_ids(led)
    pools_post = pool_balances(led)
    ids = (d1, d2)
    fam_before = read_family(am, ids)
    rows_before = len(revision_rows(am))
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    fam_two = read_family(am2, ids)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    fam_three = read_family(am3, ids)
    rows_three = len(revision_rows(am3))
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-ratingrev" in handle.read()
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    with open(os.path.abspath(__file__), "rb") as handle:
        blob = handle.read()
    try:
        blob.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        ascii_ok = False
    src = blob.decode("utf-8", "replace")
    net_imports = [line for line in src.splitlines()
                   if line.strip().startswith(("import requests",
                                               "import urllib",
                                               "import http"))]
    outside = not os.path.abspath(tmp).startswith(
        os.path.abspath(os.path.join(BASE, "..", "..", "..")))
    ok8 = (frozen_post8 == frozen_pre8
           and tx_after == tx_before and tx_post == tx_before
           and pools_after == pools_before
           and pools_post == pools_before
           and reply_after == reply_before
           and fam_before == fam_two == fam_three
           and rows_before == rows_three == 5
           and wired and shas_before == shas_after and ascii_ok
           and not net_imports and outside)
    record("AC-AMRV8", ok8,
           "tables frozen=%r tx frozen=%r reply binding stable=%r"
           " restart identity=%r revision rows=%d wired=%r ascii=%r"
           % (frozen_post8 == frozen_pre8,
              tx_after == tx_before and tx_post == tx_before,
              reply_after == reply_before,
              fam_before == fam_two == fam_three, rows_three,
              wired, ascii_ok))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())