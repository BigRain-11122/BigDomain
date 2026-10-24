"""Acceptance suite for the apimarket buyer-side watchlist faces
(BigDomain R2086; canon = the explore-queue row seeded and claimed
in R2086, criteria AC-AMWL1..AC-AMWL8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMWL prefix, the
watch_api / unwatch_api / api_watchlist names, this suite name, the
ledger-apimarket-watchlist runner label, the apimarket_watchlist
table name and the E_AM_WATCH_DUP / E_AM_NOT_WATCHED codes were all
git-grep -F zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.watch_api / unwatch_api /
api_watchlist. Every existing read face answers one narrow question
(one listing, the whole board, one listing's ratings, its price
history, its metadata history, the seller's sales, the buyer's
library, discovery, its paging, the seller profile, the seller
board) - but a resident weighing a purchase had nowhere to keep a
listing for later. This window pins the pre-purchase intent face:

  - one four-key envelope and ten-key rows, watch_count derived
    from the rows, ordered by watch_id, current_price from the
    newest revision, purchased only for this buyer;
  - strict buyer isolation, the developer account honest-empty, a
    prefix-valid account with no watches honest-empty;
  - unwatch writes an append-only apimarket_unwatchings row and
    never deletes the watch row; a re-watch writes a NEW watch row
    so both historical rows survive while the live set holds
    exactly one; the first unwatch stamp is never rewritten; an
    unwatch of a non-watched listing answers E_AM_NOT_WATCHED;
  - a retired listing cannot be newly watched (E_AM_DELISTED) but
    a listing watched BEFORE retirement stays visible with its
    stamp and revision-derived price;
  - the pinned gate order (account shape, listing shape/existence,
    retired state, duplicate state) with fail-closed zero side
    effects;
  - zero token movement and frozen table digests across the whole
    watch/unwatch/read cycle;
  - cross-restart byte identity of the watchlist family and of the
    two history tables;
  - runner wiring plus suite hygiene (ASCII, no network imports,
    world outside the repo).

Usage: python test_apimarket_watchlist.py
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
BAD_LISTING_IDS = [0, -1, True, "1", None]

ENVELOPE_KEYS = {"buyer_id", "watch_count", "disclaimer", "watches"}

ROW_KEYS = {"watch_id", "listing_id", "listing_key", "title",
            "dev_account", "current_price", "delisted",
            "delisted_utc", "purchased", "watched_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings")


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


def watch_family(am):
    return {"bob": dumps(am.api_watchlist("usr:bob")),
            "carol": dumps(am.api_watchlist("usr:carol")),
            "erin": dumps(am.api_watchlist("usr:erin")),
            "dana": dumps(am.api_watchlist("usr:dana"))}


def watch_rows(am, buyer_id, listing_id):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT watch_id, watched_utc FROM apimarket_watchlist"
        " WHERE buyer_id = ? AND listing_id = ? ORDER BY watch_id",
        (buyer_id, listing_id)).fetchall()
    conn.close()
    return rows


def unwatch_rows(am, buyer_id, listing_id):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT unwatch_id, watch_id, unwatched_utc FROM"
        " apimarket_unwatchings WHERE buyer_id = ? AND listing_id = ?"
        " ORDER BY unwatch_id", (buyer_id, listing_id)).fetchall()
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
    """Owner dana with two listings (10 and 3). bob buys d1 and
    watches both; carol buys d1 and watches it; erin is prefix-valid
    with no watches (the honest empty anchor)."""
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AMWL-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AMWL-S",
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
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    w1 = am.watch_api("usr:bob", d1)
    w2 = am.watch_api("usr:bob", d2)
    am.watch_api("usr:carol", d1)
    return d1, d2, w1, w2


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-watchlist-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, w1, w2 = seed_world(led, dk, am)

    tx_before = ledger_tx_ids(led)

    # -- AC-AMWL1 contract + current price --------------------------------
    am.revise_price("usr:dana", d1, 15)
    env = am.api_watchlist("usr:bob")
    rows = env["watches"]
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["buyer_id"] == "usr:bob"
           and env["disclaimer"] == DISCLAIMER
           and env["watch_count"] == len(rows) == 2
           and all(set(r.keys()) == ROW_KEYS for r in rows)
           and [r["listing_id"] for r in rows] == [d1, d2]
           and [r["watch_id"] for r in rows] == [w1["watch_id"],
                                                 w2["watch_id"]]
           and rows[0]["listing_key"] == "risk-scan"
           and rows[0]["title"] == "Risk Scan API"
           and rows[0]["dev_account"] == "usr:dana"
           and rows[0]["current_price"] == 15
           and rows[0]["purchased"] is True
           and rows[1]["current_price"] == 3
           and rows[1]["purchased"] is False
           and rows[0]["delisted"] is False
           and rows[0]["delisted_utc"] is None
           and rows[0]["watched_utc"] == w1["watched_utc"])
    record("AC-AMWL1", ok1,
           "envelope=%r rows=%d order=%r prices=%r purchased=%r"
           % (set(env.keys()) == ENVELOPE_KEYS, len(rows),
              [r["listing_id"] for r in rows],
              [r["current_price"] for r in rows],
              [r["purchased"] for r in rows]))

    # -- AC-AMWL2 isolation + honest empty -------------------------------
    env_carol = am.api_watchlist("usr:carol")
    env_erin = am.api_watchlist("usr:erin")
    env_dana = am.api_watchlist("usr:dana")
    ok2 = (env_carol["watch_count"] == 1
           and [r["listing_id"] for r in env_carol["watches"]] == [d1]
           and env_carol["watches"][0]["purchased"] is True
           and env_erin["watch_count"] == 0
           and env_erin["watches"] == []
           and env_erin["buyer_id"] == "usr:erin"
           and env_dana["watches"] == []
           and all(r["watch_id"] != w1["watch_id"]
                   for r in env_carol["watches"]))
    record("AC-AMWL2", ok2,
           "carol rows=%d erin empty=%r dana(dev) empty=%r"
           % (env_carol["watch_count"], env_erin["watches"] == [],
              env_dana["watches"] == []))

    # -- AC-AMWL3 unwatch / re-watch append-only -------------------------
    first_watch_d1 = watch_rows(am, "usr:bob", d1)
    un = am.unwatch_api("usr:bob", d1)
    after_un = am.api_watchlist("usr:bob")
    hist_after_un = watch_rows(am, "usr:bob", d1)
    un_hist = unwatch_rows(am, "usr:bob", d1)
    rew = am.watch_api("usr:bob", d1)
    after_rew = am.api_watchlist("usr:bob")
    hist_after_rew = watch_rows(am, "usr:bob", d1)
    un_hist_after = unwatch_rows(am, "usr:bob", d1)
    try:
        am.unwatch_api("usr:carol", d2)
        missing_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        missing_code = code_of(exc)
    second = am.unwatch_api("usr:bob", d1)
    try:
        am.unwatch_api("usr:bob", d1)
        repeat_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        repeat_code = code_of(exc)
    rew2 = am.watch_api("usr:bob", d1)
    after_rew2 = am.api_watchlist("usr:bob")
    hist_final = watch_rows(am, "usr:bob", d1)
    un_final = unwatch_rows(am, "usr:bob", d1)
    ok3 = (un["watch_id"] == w1["watch_id"]
           and un["watched_utc"] == w1["watched_utc"]
           and [r["listing_id"] for r in after_un["watches"]] == [d2]
           and len(hist_after_un) == 1
           and len(un_hist) == 1
           and un_hist[0][1] == w1["watch_id"]
           and rew["watch_id"] > w1["watch_id"]
           and len(hist_after_rew) == 2
           and [r[0] for r in hist_after_rew]
           == [w1["watch_id"], rew["watch_id"]]
           and un_hist_after == un_hist
           and hist_after_rew[0][1] == first_watch_d1[0][1]
           and [r["listing_id"] for r in after_rew["watches"]]
           == [d2, d1]
           and missing_code == "E_AM_NOT_WATCHED"
           and second["watch_id"] == rew["watch_id"]
           and repeat_code == "E_AM_NOT_WATCHED"
           and rew2["watch_id"] > rew["watch_id"]
           and len(hist_final) == 3
           and len(un_final) == 2
           and [r[1] for r in un_final]
           == [w1["watch_id"], rew["watch_id"]]
           and [r["listing_id"] for r in after_rew2["watches"]]
           == [d2, d1])
    record("AC-AMWL3", ok3,
           "unwatch watch_id=%r rows kept=%d rew id=%d rew2 id=%d"
           " history=%r unwatch history=%r missing=%s repeat=%s"
           % (un["watch_id"] == w1["watch_id"], len(hist_final),
              rew["watch_id"], rew2["watch_id"],
              [r[0] for r in hist_final],
              [r[0] for r in un_final], missing_code, repeat_code))

    # -- AC-AMWL4 retirement: refused new, kept old ----------------------
    delist = am.delist_api("usr:dana", d2)
    env_ret = am.api_watchlist("usr:bob")
    row_d2 = [r for r in env_ret["watches"]
              if r["listing_id"] == d2][0]
    try:
        am.watch_api("usr:erin", d2)
        retired_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        retired_code = code_of(exc)
    ok4 = (row_d2["delisted"] is True
           and row_d2["delisted_utc"] == delist["delisted_utc"]
           and row_d2["current_price"] == 3
           and row_d2["watch_id"] == w2["watch_id"]
           and retired_code == "E_AM_DELISTED"
           and am.api_watchlist("usr:erin")["watches"] == [])
    record("AC-AMWL4", ok4,
           "watched-before-retire kept=%r stamp match=%r new watch"
           " refused=%s"
           % (row_d2["delisted"],
              row_d2["delisted_utc"] == delist["delisted_utc"],
              retired_code))

    # -- AC-AMWL5 gate order + bad forms ---------------------------------
    dig = market_digests(am)
    codes = []
    for form in BAD_ACCOUNTS:
        try:
            am.watch_api(form, 999999)
            codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            codes.append(code_of(exc))
    try:
        am.watch_api("usr:bob", 999999)
        unknown_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        unknown_code = code_of(exc)
    try:
        am.watch_api("usr:bob", d2)
        order_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        order_code = code_of(exc)
    try:
        am.watch_api("usr:bob", d1)
        dup_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        dup_code = code_of(exc)
    bad_ids = []
    for form in BAD_LISTING_IDS:
        try:
            am.watch_api("usr:bob", form)
            bad_ids.append("NO-RAISE")
        except A.ApiMarketError as exc:
            bad_ids.append(code_of(exc))
    dig_after = market_digests(am)
    ok5 = (codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and unknown_code == "E_AM_UNKNOWN_LISTING"
           and order_code == "E_AM_DELISTED"
           and dup_code == "E_AM_WATCH_DUP"
           and bad_ids == ["E_AM_BAD_ARGS"] * len(BAD_LISTING_IDS)
           and dig_after == dig)
    record("AC-AMWL5", ok5,
           "bad accounts=%r unknown=%s retired-before-dup=%s dup=%s"
           " bad ids=%r frozen=%r"
           % (codes, unknown_code, order_code, dup_code, bad_ids,
              dig_after == dig))

    # -- AC-AMWL6 zero token + pure read ---------------------------------
    fam_a = watch_family(am)
    fam_b = watch_family(am)
    dig_read = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok6 = (fam_a == fam_b
           and dig_read == dig_after
           and tx_after == tx_before)
    record("AC-AMWL6", ok6,
           "repeat identical=%r digests frozen=%r ledger tx set"
           " constant=%r"
           % (fam_a == fam_b, dig_read == dig_after,
              tx_after == tx_before))

    # -- AC-AMWL7 cross-restart identity ---------------------------------
    family_before_restart = watch_family(am)
    counts_before = (len(watch_rows(am, "usr:bob", d1)),
                     len(unwatch_rows(am, "usr:bob", d1)))
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    family_two = watch_family(am2)
    counts_two = (len(watch_rows(am2, "usr:bob", d1)),
                  len(unwatch_rows(am2, "usr:bob", d1)))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    family_three = watch_family(am3)
    counts_three = (len(watch_rows(am3, "usr:bob", d1)),
                    len(unwatch_rows(am3, "usr:bob", d1)))
    close_stack(am3, dk3, metered3, led3)
    ok7 = (family_before_restart == family_two == family_three
           and counts_before == counts_two == counts_three == (3, 2))
    record("AC-AMWL7", ok7,
           "instance1==2==3 byte-identical=%r history counts=%r"
           " %r %r"
           % (family_before_restart == family_two == family_three,
              counts_before, counts_two, counts_three))

    # -- AC-AMWL8 wiring + hygiene ---------------------------------------
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-watchlist" in handle.read()
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
    ok8 = (wired and shas_before == shas_after and ascii_ok
           and not net_imports and outside)
    record("AC-AMWL8", ok8,
           "runner wiring=%r consumer shas stable=%r ascii=%r"
           " network imports=%d world outside repo=%r"
           % (wired, shas_before == shas_after, ascii_ok,
              len(net_imports), outside))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())