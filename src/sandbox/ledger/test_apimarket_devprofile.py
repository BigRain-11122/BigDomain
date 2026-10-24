"""Acceptance suite for the apimarket public seller-profile face
(BigDomain R2085; canon = the explore-queue row seeded and claimed
in R2085, criteria AC-AMDP1..AC-AMDP8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMDP prefix, the
dev_profile name, this suite name, the ledger-apimarket-devprofile
runner label and the dev_profile face were all git-grep
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.dev_profile. The nine existing read
faces each answer one narrow question - one listing (api_view), the
whole board (api_board), one listing's ratings (api_ratings), one
listing's price history (api_price_history), one listing's metadata
history (api_metadata_history), one seller's own sales (api_sales),
one buyer's library (api_library), one search result (api_search)
and the market-wide seller board (dev_sales_board). None answers
"who is this seller" for a buyer standing at a listing. This
window pins that face:

  - one envelope per developer with exactly the thirteen contract
    keys and nine per-row keys, rows ordered by listing_id;
  - the partition law: listing_count == live + retired ==
    len(listings), sales_count == sum of row sales, gross_sales ==
    sum of price_paid == dev_revenue + platform_revenue exactly
    (integer split, zero rounding);
  - a retired listing stays visible with its delist stamp and
    still contributes its historical sales and ratings (retirement
    never rewrites the trust history);
  - the cross-listing rating aggregate: rating_count == sum of row
    counts, avg_rating == sum(stars)/count pinned at 3.75 and at
    30/7 = 4.285714285714286, zero ratings -> 0.0 with count 0,
    and every per-row pair agreeing with the existing api_ratings
    face for the same listing;
  - strict seller isolation and the honest empty profile for a
    prefix-valid account with no listing rows (zeros,
    first_listed_utc None, empty listings), never an error;
  - the account shape gate fail-closed before any read with frozen
    digests, and the truthful prefix-only shape finding (a bare
    'usr:' passes the gate and lands on the honest empty profile);
  - the pure-read law (zero row mutations, zero token movement),
    cross-face agreement with dev_sales_board and api_view, and
    cross-restart byte identity.

Usage: python test_apimarket_devprofile.py
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

BAD_ACCOUNTS = ["", "bob", None, 123, 1.5, True, [], {}, "   "]

ENVELOPE_KEYS = {"dev_account", "listing_count",
                 "live_listing_count", "retired_listing_count",
                 "sales_count", "gross_sales", "dev_revenue",
                 "platform_revenue", "rating_count", "avg_rating",
                 "first_listed_utc", "disclaimer", "listings"}

ROW_KEYS = {"listing_id", "listing_key", "title", "token_price",
            "delisted", "delisted_utc", "sales_count",
            "rating_count", "avg_rating"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions",
          "apimarket_listing_revisions")

FRANK_STARS = [5, 5, 5, 5, 4, 3, 3]      # sum 30 over 7 raters


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


def profile_family(am):
    return {"dana": dumps(am.dev_profile("usr:dana")),
            "frank": dumps(am.dev_profile("usr:frank")),
            "gina": dumps(am.dev_profile("usr:gina")),
            "bob": dumps(am.dev_profile("usr:bob"))}


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
    """dana owns two listings (10 and 3), frank one (7), gina is
    prefix-valid with zero listings. bob/carol/dave buy from dana;
    u1..u7 buy frank's one listing and rate it 5/5/5/5/4/3/3."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-AMDP-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-AMDP-S",
                     "settlement")
    for who in ("bob", "carol", "dave") + tuple(
            "u%d" % i for i in range(1, 8)):
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
    am.purchase_api("usr:bob", d1, "ref-bob-d1")
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    am.purchase_api("usr:bob", d2, "ref-bob-d2")
    am.purchase_api("usr:dave", d2, "ref-dave-d2")
    for i, stars in enumerate(FRANK_STARS, start=1):
        buyer = "usr:u%d" % i
        am.purchase_api(buyer, f1, "ref-u%d-f1" % i)
        am.rate_api(buyer, f1, stars)
    am.rate_api("usr:bob", d1, 5)
    am.rate_api("usr:carol", d1, 2)
    am.rate_api("usr:bob", d2, 3)
    am.rate_api("usr:dave", d2, 5)
    return d1, d2, f1


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-devprofile-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, f1 = seed_world(led, dk, am)

    tx_before = ledger_tx_ids(led)
    digests_before = market_digests(am)

    # -- AC-AMDP1 envelope and row contract ------------------------------
    env = am.dev_profile("usr:dana")
    rows = env["listings"]
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["dev_account"] == "usr:dana"
           and env["disclaimer"] == DISCLAIMER
           and all(set(r.keys()) == ROW_KEYS for r in rows)
           and [r["listing_id"] for r in rows] == [d1, d2]
           and rows[0]["listing_key"] == "risk-scan"
           and rows[1]["listing_key"] == "macro-feed"
           and isinstance(env["first_listed_utc"], str)
           and len(env["first_listed_utc"]) >= 19)
    record("AC-AMDP1", ok1,
           "envelope keys=%r rows=%d row keys=%r order=%r"
           " first_listed_shape=%r"
           % (set(env.keys()) == ENVELOPE_KEYS, len(rows),
              all(set(r.keys()) == ROW_KEYS for r in rows),
              [r["listing_id"] for r in rows],
              isinstance(env["first_listed_utc"], str)
              and len(env["first_listed_utc"]) >= 19))

    # -- AC-AMDP2 partition conservation ---------------------------------
    ok2 = (env["listing_count"] == 2
           and env["live_listing_count"] == 2
           and env["retired_listing_count"] == 0
           and env["listing_count"]
           == env["live_listing_count"] + env["retired_listing_count"]
           == len(rows)
           and env["sales_count"] == 4
           and env["sales_count"] == sum(r["sales_count"] for r in rows)
           and env["gross_sales"] == 26
           and env["gross_sales"]
           == env["dev_revenue"] + env["platform_revenue"]
           and rows[0]["sales_count"] == 2
           and rows[1]["sales_count"] == 2)
    conn = sqlite3.connect(am.db_path)
    paid_sum = conn.execute(
        "SELECT COALESCE(SUM(price_paid), 0) FROM apimarket_purchases"
        " WHERE listing_id IN (?, ?)", (d1, d2)).fetchone()[0]
    conn.close()
    ok2 = ok2 and env["gross_sales"] == int(paid_sum)
    record("AC-AMDP2", ok2,
           "counts=%d/%d/%d sales=%d gross=%d dev+plat=%d/%d"
           " paid_sum=%d"
           % (env["listing_count"], env["live_listing_count"],
              env["retired_listing_count"], env["sales_count"],
              env["gross_sales"], env["dev_revenue"],
              env["platform_revenue"], int(paid_sum)))

    # -- AC-AMDP3 retired listing stays and keeps its history ------------
    delist = am.delist_api("usr:dana", d2)
    env_ret = am.dev_profile("usr:dana")
    row_d2 = [r for r in env_ret["listings"]
              if r["listing_id"] == d2][0]
    row_d1 = [r for r in env_ret["listings"]
              if r["listing_id"] == d1][0]
    ok3 = (env_ret["live_listing_count"] == 1
           and env_ret["retired_listing_count"] == 1
           and env_ret["listing_count"] == 2
           and row_d2["delisted"] is True
           and row_d2["delisted_utc"] == delist["delisted_utc"]
           and row_d1["delisted"] is False
           and row_d1["delisted_utc"] is None
           and row_d2["sales_count"] == 2
           and env_ret["sales_count"] == 4
           and env_ret["gross_sales"] == 26
           and env_ret["rating_count"] == 4)
    record("AC-AMDP3", ok3,
           "live=%d retired=%d d2 delisted=%r stamp match=%r"
           " d2 sales=%d totals sales=%d gross=%d ratings=%d"
           % (env_ret["live_listing_count"],
              env_ret["retired_listing_count"], row_d2["delisted"],
              row_d2["delisted_utc"] == delist["delisted_utc"],
              row_d2["sales_count"], env_ret["sales_count"],
              env_ret["gross_sales"], env_ret["rating_count"]))

    # -- AC-AMDP4 cross-listing rating aggregate -------------------------
    env_frank = am.dev_profile("usr:frank")
    rows_d = [r for r in env_ret["listings"]
              if r["listing_id"] == d1][0]
    rows_d2 = [r for r in env_ret["listings"]
               if r["listing_id"] == d2][0]
    api_rat_d1 = am.api_ratings(d1)
    api_rat_d2 = am.api_ratings(d2)
    api_rat_f1 = am.api_ratings(f1)
    frank_row = env_frank["listings"][0]
    sum_stars_d = 5 + 2 + 3 + 5
    ok4 = (env_ret["rating_count"] == 4
           and env_ret["avg_rating"] == 3.75
           and env_ret["avg_rating"] == float(sum_stars_d) / 4
           and env_ret["rating_count"]
           == sum(r["rating_count"] for r in env_ret["listings"])
           and rows_d["rating_count"] == 2
           and rows_d["avg_rating"] == 3.5
           and rows_d2["rating_count"] == 2
           and rows_d2["avg_rating"] == 4.0
           and env_frank["rating_count"] == 7
           and env_frank["avg_rating"] == 30.0 / 7.0
           and env_frank["avg_rating"] == 4.285714285714286
           and frank_row["rating_count"] == 7
           and frank_row["avg_rating"] == env_frank["avg_rating"]
           and api_rat_d1["rating_count"] == rows_d["rating_count"]
           and api_rat_d1["rating_avg"] == rows_d["avg_rating"]
           and api_rat_d2["rating_count"] == rows_d2["rating_count"]
           and api_rat_d2["rating_avg"] == rows_d2["avg_rating"]
           and api_rat_f1["rating_count"] == frank_row["rating_count"]
           and api_rat_f1["rating_avg"] == frank_row["avg_rating"])
    no_rat = am.dev_profile("usr:gina")
    ok4 = ok4 and (no_rat["rating_count"] == 0
                   and no_rat["avg_rating"] == 0.0)
    record("AC-AMDP4", ok4,
           "dana count=%d avg=%r (3.5/4.0 rows) frank count=%d"
           " avg=%r zero-rating gina=%r/%r"
           % (env_ret["rating_count"], env_ret["avg_rating"],
              env_frank["rating_count"], env_frank["avg_rating"],
              no_rat["rating_count"], no_rat["avg_rating"]))

    # -- AC-AMDP5 isolation + honest empty profile -----------------------
    env_bob = am.dev_profile("usr:bob")
    env_gina = am.dev_profile("usr:gina")
    bob_rows = purchase_rows(am)
    dana_ids = set(r["listing_id"] for r in env["listings"])
    frank_ids = set(r["listing_id"] for r in env_frank["listings"])
    ok5 = (env_gina["listing_count"] == 0
           and env_gina["sales_count"] == 0
           and env_gina["gross_sales"] == 0
           and env_gina["first_listed_utc"] is None
           and env_gina["listings"] == []
           and env_gina["dev_account"] == "usr:gina"
           and dana_ids.isdisjoint(frank_ids)
           and env_bob["listing_count"] == 0
           and env_bob["listings"] == []
           and len(bob_rows) == 4 + 7)
    record("AC-AMDP5", ok5,
           "gina empty=%r dana/frank ids disjoint=%r bob(dev)"
           " empty=%r purchase rows=%d"
           % (env_gina["listings"] == [], dana_ids.isdisjoint(
               frank_ids), env_bob["listings"] == [], len(bob_rows)))

    # -- AC-AMDP6 bad account gate fail-closed ---------------------------
    dig = market_digests(am)
    codes = []
    for form in BAD_ACCOUNTS:
        try:
            am.dev_profile(form)
            codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            codes.append(code_of(exc))
    dig_after = market_digests(am)
    bare = am.dev_profile("usr:")
    ok6 = (codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and dig_after == dig
           and bare["listing_count"] == 0
           and bare["listings"] == []
           and bare["avg_rating"] == 0.0)
    record("AC-AMDP6", ok6,
           "bad forms=%r digests frozen=%r bare usr: empty=%r"
           % (codes, dig_after == dig, bare["listings"] == []))

    # -- AC-AMDP7 pure-read law + cross-face agreement -------------------
    am.revise_price("usr:dana", d1, 15)
    dig_post_revise = market_digests(am)
    env_priced = am.dev_profile("usr:dana")
    view_d1 = am.api_view(d1)
    board = am.dev_sales_board()
    dana_board = [b for b in board["board"]
                  if b["dev_account"] == "usr:dana"][0]
    fam_a = profile_family(am)
    fam_b = profile_family(am)
    dig_read = market_digests(am)
    tx_after = ledger_tx_ids(led)
    priced_d1 = [r for r in env_priced["listings"]
                 if r["listing_id"] == d1][0]
    priced_d2 = [r for r in env_priced["listings"]
                 if r["listing_id"] == d2][0]
    ok7 = (fam_a == fam_b
           and dig_read == dig_post_revise
           and tx_after == tx_before
           and priced_d1["token_price"] == view_d1["token_price"] == 15
           and priced_d2["token_price"] == 3
           and env_priced["gross_sales"] == 26
           and dana_board["listing_count"] == 2
           and dana_board["purchase_count"] == 4
           and dana_board["gross_revenue"] == 26
           and dana_board["dev_revenue"] == env_priced["dev_revenue"]
           and dana_board["platform_revenue"]
           == env_priced["platform_revenue"])
    record("AC-AMDP7", ok7,
           "repeat identical=%r digests frozen=%r tx constant=%r"
           " d1 price %d->%d gross kept=%d board agreement=%r"
           % (fam_a == fam_b, dig_read == dig_post_revise,
              tx_after == tx_before, 10, view_d1["token_price"],
              env_priced["gross_sales"],
              dana_board["dev_revenue"] == env_priced["dev_revenue"]))

    # -- AC-AMDP8 cross-restart identity + wiring ------------------------
    family_before_restart = profile_family(am)
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    family_two = profile_family(am2)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    family_three = profile_family(am3)
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-devprofile" in handle.read()
    ok8 = (family_before_restart == family_two == family_three
           and wired)
    record("AC-AMDP8", ok8,
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
    outside = not os.path.abspath(tmp).startswith(
        os.path.abspath(os.path.join(BASE, "..", "..", "..")))
    hygiene = (shas_before == shas_after
               and ascii_ok
               and not net_imports
               and outside)
    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("HYGIENE: consumer shas stable=%r suite ascii=%r"
          " network imports=%d world outside repo=%r"
          % (shas_before == shas_after, ascii_ok, len(net_imports),
             outside))
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8 and hygiene) else 1


if __name__ == "__main__":
    sys.exit(main())