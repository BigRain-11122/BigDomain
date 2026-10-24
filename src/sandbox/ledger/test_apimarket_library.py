"""Acceptance suite for the apimarket buyer-side purchase library
face (BigDomain R2081; canon = the explore-queue row seeded and
claimed in R2081, criteria AC-AML1..AC-AML8 registered in that
claim note BEFORE this code existed - honesty law; the AC-AML
prefix, the api_library name, this suite name and the
ledger-apimarket-buyerlibrary runner label were all git-grep
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.api_library. Until this window the
market had four seller/aggregate read faces (api_sales,
dev_sales_board, api_view, api_board) and no buyer-side face at
all: a resident who spent tokens had no way to see what it owns.
This window pins the buyer library:

  - one envelope per buyer with exactly the five contract keys and
    fourteen per-row keys, purchase_count and total_spent derived
    from the rows (F3: no hardcoded numbers);
  - strict buyer isolation (no cross-buyer row permeation, the
    developer's own account has no self-purchase rows, a
    prefix-valid account with no purchases gets an honest empty
    library instead of an error);
  - a retired listing stays in the library with its delisted flag
    and stamp while the purchase row itself is unchanged (history
    is not destroyed by retirement);
  - price_paid (historical) and current_price (live asking price)
    are separate quantities, so a later revision never rewrites
    what was charged;
  - my_rating is this buyer's own stars only - None before the
    rating, and another buyer's rating never leaks;
  - the account shape gate runs before any read and every bad
    form is fail-closed with frozen digests;
  - the pure-read law (zero row mutations, zero token movement)
    and cross-restart byte identity of the library family.

Usage: python test_apimarket_library.py
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

BAD_ACCOUNTS = ["", "bob", None]

ENVELOPE_KEYS = {"buyer_id", "purchase_count", "total_spent",
                 "disclaimer", "purchases"}

ROW_KEYS = {"purchase_id", "listing_id", "listing_key", "title",
            "dev_account", "price_paid", "dev_share",
            "platform_share", "spend_tx", "purchased_utc",
            "current_price", "delisted", "delisted_utc",
            "my_rating"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions")


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


def library_family(am):
    return {"bob": dumps(am.api_library("usr:bob")),
            "carol": dumps(am.api_library("usr:carol")),
            "erin": dumps(am.api_library("usr:erin")),
            "dana": dumps(am.api_library("usr:dana"))}


def purchase_rows(am):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT purchase_id, listing_id, buyer_id, price_paid"
        " FROM apimarket_purchases ORDER BY purchase_id").fetchall()
    conn.close()
    return rows


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


def seed_world(led, dk, am):
    """Owner dana with two listings (10 and 3). bob buys both
    (the two-row library anchor), carol buys one (the isolation
    anchor), erin is prefix-valid with no purchases (the honest
    empty anchor)."""
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AML-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AML-S",
                     "settlement")
    for who in ("bob", "carol", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3,
                        True)["listing_id"]
    am.purchase_api("usr:bob", d1, "ref-bob-d1")
    am.purchase_api("usr:bob", d2, "ref-bob-d2")
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    return d1, d2


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-library-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2 = seed_world(led, dk, am)

    tx_before = ledger_tx_ids(led)
    digests_before = market_digests(am)

    # -- AC-AML1 library contract ----------------------------------------
    env = am.api_library("usr:bob")
    rows = env["purchases"]
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["buyer_id"] == "usr:bob"
           and env["disclaimer"] == DISCLAIMER
           and env["purchase_count"] == len(rows) == 2
           and env["total_spent"] == 13
           and all(set(r.keys()) == ROW_KEYS for r in rows)
           and [r["listing_id"] for r in rows] == [d1, d2]
           and [r["purchase_id"] for r in rows]
           == sorted(r["purchase_id"] for r in rows)
           and rows[0]["listing_key"] == "risk-scan"
           and rows[0]["title"] == "Risk Scan API"
           and rows[0]["dev_account"] == "usr:dana"
           and rows[0]["price_paid"] == 10
           and rows[0]["spend_tx"]
           and rows[0]["purchased_utc"]
           and rows[1]["price_paid"] == 3)
    record("AC-AML1", ok1,
           "envelope keys=%r rows=%d total_spent=%d row keys=%r"
           " order=%r"
           % (set(env.keys()) == ENVELOPE_KEYS, len(rows),
              env["total_spent"],
              all(set(r.keys()) == ROW_KEYS for r in rows),
              [r["listing_id"] for r in rows]))

    # -- AC-AML2 buyer isolation -----------------------------------------
    env_carol = am.api_library("usr:carol")
    env_erin = am.api_library("usr:erin")
    env_dana = am.api_library("usr:dana")
    bob_rows = purchase_rows(am)
    ok2 = (env_carol["purchase_count"] == 1
           and [r["listing_id"] for r in env_carol["purchases"]] == [d1]
           and env_carol["total_spent"] == 10
           and env_erin["purchase_count"] == 0
           and env_erin["total_spent"] == 0
           and env_erin["purchases"] == []
           and env_erin["buyer_id"] == "usr:erin"
           and env_dana["purchases"] == []
           and all(r["purchase_id"] != env_carol["purchases"][0]
                   ["purchase_id"] for r in rows)
           and len(bob_rows) == 3)
    record("AC-AML2", ok2,
           "carol rows=%d total=%d erin empty=%r dana(dev) empty=%r"
           " purchase table rows=%d"
           % (env_carol["purchase_count"], env_carol["total_spent"],
              env_erin["purchases"] == [],
              env_dana["purchases"] == [], len(bob_rows)))

    # -- AC-AML3 retired listing stays readable --------------------------
    delist = am.delist_api("usr:dana", d2)
    env_retired = am.api_library("usr:bob")
    row_d2 = [r for r in env_retired["purchases"]
              if r["listing_id"] == d2][0]
    row_d1 = [r for r in env_retired["purchases"]
              if r["listing_id"] == d1][0]
    ok3 = (row_d2["delisted"] is True
           and row_d2["delisted_utc"] == delist["delisted_utc"]
           and row_d2["price_paid"] == 3
           and row_d2["purchase_id"]
           == [r for r in rows if r["listing_id"] == d2][0]
           ["purchase_id"]
           and row_d1["delisted"] is False
           and row_d1["delisted_utc"] is None
           and [r["listing_id"] for r in env_retired["purchases"]]
           == [d1, d2]
           and env_retired["total_spent"] == 13)
    record("AC-AML3", ok3,
           "retired row delisted=%r stamp match=%r price_paid=%d"
           " live row delisted=%r order=%r"
           % (row_d2["delisted"],
              row_d2["delisted_utc"] == delist["delisted_utc"],
              row_d2["price_paid"], row_d1["delisted"],
              [r["listing_id"] for r in env_retired["purchases"]]))

    # -- AC-AML4 historical price vs live asking price -------------------
    am.revise_price("usr:dana", d1, 15)
    env_bob = am.api_library("usr:bob")
    env_carol2 = am.api_library("usr:carol")
    bob_d1 = [r for r in env_bob["purchases"]
              if r["listing_id"] == d1][0]
    carol_d1 = env_carol2["purchases"][0]
    ok4 = (bob_d1["current_price"] == 15
           and bob_d1["price_paid"] == 10
           and carol_d1["current_price"] == 15
           and carol_d1["price_paid"] == 10
           and env_bob["total_spent"] == 13
           and env_carol2["total_spent"] == 10)
    record("AC-AML4", ok4,
           "bob current=%d paid=%d carol current=%d paid=%d"
           " totals bob=%d carol=%d"
           % (bob_d1["current_price"], bob_d1["price_paid"],
              carol_d1["current_price"], carol_d1["price_paid"],
              env_bob["total_spent"], env_carol2["total_spent"]))

    # -- AC-AML5 my_rating face ------------------------------------------
    before_rate = am.api_library("usr:bob")
    none_before = [r["my_rating"] for r in before_rate["purchases"]]
    am.rate_api("usr:bob", d1, 5)
    am.rate_api("usr:carol", d1, 2)
    after_rate = am.api_library("usr:bob")
    after_carol = am.api_library("usr:carol")
    bob_d1_rated = [r for r in after_rate["purchases"]
                    if r["listing_id"] == d1][0]
    bob_d2_rated = [r for r in after_rate["purchases"]
                    if r["listing_id"] == d2][0]
    carol_d1_rated = after_carol["purchases"][0]
    ok5 = (none_before == [None, None]
           and bob_d1_rated["my_rating"] == 5
           and bob_d2_rated["my_rating"] is None
           and carol_d1_rated["my_rating"] == 2
           and bob_d1_rated["price_paid"] == 10
           and bob_d1_rated["purchase_id"]
           == bob_d1["purchase_id"]
           and after_rate["total_spent"] == 13)
    record("AC-AML5", ok5,
           "pre-rating=%r bob d1=%r bob d2=%r carol d1=%r"
           % (none_before, bob_d1_rated["my_rating"],
              bob_d2_rated["my_rating"], carol_d1_rated["my_rating"]))

    # -- AC-AML6 bad account gate fail-closed ----------------------------
    dig = market_digests(am)
    codes = []
    for form in BAD_ACCOUNTS:
        try:
            am.api_library(form)
            codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            codes.append(code_of(exc))
    dig_after = market_digests(am)
    bare = am.api_library("usr:")
    ok6 = (codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and dig_after == dig
           and bare["purchase_count"] == 0
           and bare["purchases"] == [])
    record("AC-AML6", ok6,
           "bad forms=%r digests frozen=%r bare usr: empty=%r"
           % (codes, dig_after == dig,
              bare["purchase_count"] == 0))

    # -- AC-AML7 pure-read law -------------------------------------------
    fam_a = library_family(am)
    fam_b = library_family(am)
    dig_read = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (fam_a == fam_b
           and dig_read == dig_after
           and tx_after == tx_before)
    record("AC-AML7", ok7,
           "repeat identical=%r digests frozen=%r ledger tx set"
           " constant=%r"
           % (fam_a == fam_b, dig_read == dig_after,
              tx_after == tx_before))

    # -- AC-AML8 cross-restart identity + wiring -------------------------
    family_before_restart = library_family(am)
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    family_two = library_family(am2)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    family_three = library_family(am3)
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-buyerlibrary" in handle.read()
    ok8 = (family_before_restart == family_two == family_three
           and wired)
    record("AC-AML8", ok8,
           "instance1==2==3 byte-identical=%r runner wiring=%r"
           % (family_before_restart == family_two == family_three,
              wired))

    # -- hygiene ----------------------------------------------------------
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    with open(os.path.abspath(__file__), "rb") as handle:
        blob = handle.read()
    ascii_ok = True
    try:
        blob.decode("ascii")
    except UnicodeDecodeError:
        ascii_ok = False
    src = blob.decode("utf-8", "replace")
    net_imports = [line for line in src.splitlines()
                   if line.strip().startswith(("import requests",
                                               "import urllib",
                                               "import http"))]
    hygiene = (shas_before == shas_after
               and ascii_ok
               and not net_imports
               and not os.path.abspath(tmp).startswith(
                   os.path.abspath(os.path.join(BASE, "..", "..",
                                                ".."))))
    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("HYGIENE: consumer shas stable=%r suite ascii=%r"
          " network imports=%d world outside repo=%r"
          % (shas_before == shas_after, ascii_ok, len(net_imports),
             not os.path.abspath(tmp).startswith(
                 os.path.abspath(os.path.join(BASE, "..", "..",
                                              "..")))))
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8 and hygiene) else 1


if __name__ == "__main__":
    sys.exit(main())