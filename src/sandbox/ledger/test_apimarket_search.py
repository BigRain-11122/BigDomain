"""Acceptance suite for the apimarket market discovery face
(BigDomain R2082; canon = the explore-queue row seeded and claimed
in R2082, criteria AC-AMSQ1..AC-AMSQ8 registered in that claim
note BEFORE this code existed - honesty law; the AC-AMSQ prefix,
the api_search name, this suite name and the
ledger-apimarket-search runner label were all git-grep
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.api_search. The market already had
five read faces that each answer one narrow question (api_view one
listing, api_sales one seller, api_library one buyer, api_board the
whole board, dev_sales_board the seller board). A resident looking
for a usable service could only enumerate everything - there was no
discovery door. This window pins it:

  - the envelope contract and the normalized criteria echo (F3:
    the echo is the value the face actually used, None stays None);
  - the keyword axis is a case-insensitive substring over TITLE or
    LISTING_KEY only - a word that lives only in the description
    never matches, and a no-match answers an honest empty list;
  - the price band is applied to the CURRENT asking price (a
    repriced listing moves bands), with the min bound inclusive
    and both bounds able to act together;
  - the seller axis filters to one developer and a prefix-valid
    seller with no listings gets an honest empty list;
  - retired listings are hidden by default and, when explicitly
    included, carry their stamp and their revision-derived price;
  - every gate runs before any read, with a pinned gate ORDER and
    zero side effects on the five market tables;
  - the ordering law (current price ASC, then listing_id ASC),
    repeat-call byte identity and the pure-read law;
  - cross-restart byte identity across three instances plus the
    runner wiring.

Usage: python test_apimarket_search.py
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

ENVELOPE_KEYS = {"disclaimer", "criteria", "count", "listings"}

CRITERIA_KEYS = {"keyword", "dev_account", "min_price", "max_price",
                 "include_delisted"}

ROW_KEYS = {"listing_id", "dev_account", "listing_key", "title",
            "token_price", "ai_label", "rating_count",
            "rating_avg", "delisted", "delisted_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions")

BAD_KEYWORDS = [123, True, "", "   "]
BAD_DEVS = ["bob", "", "usr"]
BAD_PRICES = [True, "10", 0, -5]
BAD_FLAGS = ["yes", 1, None]


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


def search_family(am):
    return {"all": dumps(am.api_search()),
            "kw": dumps(am.api_search(keyword="scan")),
            "dev": dumps(am.api_search(dev_account="usr:dana")),
            "band": dumps(am.api_search(min_price=5, max_price=11)),
            "retired": dumps(am.api_search(include_delisted=True))}


def ids(env):
    return [r["listing_id"] for r in env["listings"]]


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
    """Two sellers, five listings: dana publishes risk-scan at 30
    (then revises to 10), macro-feed at 3 (AIGC) and alpha-tool at
    12 whose title never carries the keyword; erin publishes
    scan-probe at 6 and roll-ups at 3 (the same-price tie anchor).
    bob buys risk-scan so the row carries an aggregate rating; a
    prefix-valid account with no listings ('usr:nobody') is the
    honest empty seller anchor."""
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AMS-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AMS-S",
                     "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:erin", "erin-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 30,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3,
                        True)["listing_id"]
    e1 = am.publish_api("usr:erin", "scan-probe", "Scan Probe API",
                        "probe endpoint for the scan pipeline",
                        PAYLOAD, 6, False)["listing_id"]
    e2 = am.publish_api("usr:erin", "roll-ups", "Roll Up Service",
                        "rolling aggregation service", PAYLOAD, 3,
                        False)["listing_id"]
    d3 = am.publish_api("usr:dana", "alpha-tool", "Service One",
                        "first service in the series", PAYLOAD, 12,
                        False)["listing_id"]
    am.revise_price("usr:dana", d1, 10)
    am.purchase_api("usr:bob", d1, "ref-bob-ams")
    am.rate_api("usr:bob", d1, 5)
    return d1, d2, e1, e2, d3


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-search-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, e1, e2, d3 = seed_world(led, dk, am)

    tx_before = ledger_tx_ids(led)
    digests_before = market_digests(am)

    # -- AC-AMSQ1 face contract ------------------------------------------
    env = am.api_search()
    rows = env["listings"]
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(env["criteria"].keys()) == CRITERIA_KEYS
           and env["criteria"] == {"keyword": None,
                                   "dev_account": None,
                                   "min_price": None,
                                   "max_price": None,
                                   "include_delisted": False}
           and env["count"] == len(rows) == 5
           and all(ROW_KEYS <= set(r.keys()) for r in rows)
           and env["disclaimer"] == DISCLAIMER
           and [r["listing_id"] for r in rows] == [d2, e2, e1, d1, d3]
           and rows[0]["listing_key"] == "macro-feed"
           and rows[0]["ai_label"] == 1
           and rows[0]["rating_count"] == 0
           and rows[0]["rating_avg"] == 0.0
           and rows[3]["listing_id"] == d1
           and rows[3]["token_price"] == 10
           and rows[3]["rating_count"] == 1
           and rows[3]["rating_avg"] == 5.0
           and rows[0]["delisted"] is False
           and rows[0]["delisted_utc"] is None)
    record("AC-AMSQ1", ok1,
           "envelope keys=%r rows=%d order=%r criteria=%r"
           " rated row=%d/%r"
           % (set(env.keys()) == ENVELOPE_KEYS, len(rows),
              [r["listing_id"] for r in rows], env["criteria"],
              rows[3]["rating_count"], rows[3]["rating_avg"]))

    # -- AC-AMSQ2 keyword axis (title OR listing_key only) ---------------
    upper = am.api_search(keyword="SCAN")
    lower = am.api_search(keyword="scan")
    padded = am.api_search(keyword="  scan  ")
    key_only = am.api_search(keyword="alpha")
    desc_only = am.api_search(keyword="portfolio")
    no_hit = am.api_search(keyword="zzz-nothing")
    ok2 = (ids(upper) == [e1, d1]
           and upper["listings"] == lower["listings"]
           == padded["listings"]
           and upper["criteria"]["keyword"] == "SCAN"
           and lower["criteria"]["keyword"] == "scan"
           and padded["criteria"]["keyword"] == "scan"
           and ids(key_only) == [d3]
           and ids(desc_only) == []
           and desc_only["count"] == 0
           and ids(no_hit) == []
           and no_hit["count"] == 0
           and no_hit["listings"] == [])
    record("AC-AMSQ2", ok2,
           "SCAN order=%r rows identical across case/padding=%r"
           " padded echo=%r key-only=%r description-only=%r"
           " no-hit rows=%d"
           % (ids(upper),
              upper["listings"] == lower["listings"]
              == padded["listings"],
              padded["criteria"]["keyword"], ids(key_only),
              ids(desc_only), no_hit["count"]))

    # -- AC-AMSQ3 price band on the CURRENT asking price ------------------
    wide = am.api_search(max_price=15)
    narrow = am.api_search(max_price=8)
    low_band = am.api_search(min_price=6)
    both = am.api_search(min_price=6, max_price=10)
    ok3 = (d1 in ids(wide)
           and d1 not in ids(narrow)
           and ids(narrow) == [d2, e2, e1]
           and ids(low_band) == [e1, d1, d3]
           and ids(both) == [e1, d1]
           and wide["criteria"]["max_price"] == 15)
    record("AC-AMSQ3", ok3,
           "revised listing 30->10: in max15=%r out of max8=%r"
           " max8 order=%r min6 order=%r band[6,10]=%r"
           % (d1 in ids(wide), d1 not in ids(narrow), ids(narrow),
              ids(low_band), ids(both)))

    # -- AC-AMSQ4 seller axis --------------------------------------------
    dana = am.api_search(dev_account="usr:dana")
    erin = am.api_search(dev_account="usr:erin")
    nobody = am.api_search(dev_account="usr:nobody")
    ok4 = (ids(dana) == [d2, d1, d3]
           and all(r["dev_account"] == "usr:dana"
                   for r in dana["listings"])
           and ids(erin) == [e2, e1]
           and nobody["count"] == 0
           and nobody["listings"] == []
           and nobody["criteria"]["dev_account"] == "usr:nobody")
    record("AC-AMSQ4", ok4,
           "dana order=%r erin order=%r nobody rows=%d"
           " echo=%r"
           % (ids(dana), ids(erin), nobody["count"],
              nobody["criteria"]["dev_account"]))

    # -- AC-AMSQ5 retirement axis ----------------------------------------
    delist = am.delist_api("usr:erin", e1)
    hidden = am.api_search(keyword="scan")
    shown = am.api_search(keyword="scan", include_delisted=True)
    row_e1 = [r for r in shown["listings"]
              if r["listing_id"] == e1][0]
    ok5 = (ids(hidden) == [d1]
           and ids(shown) == [e1, d1]
           and row_e1["delisted"] is True
           and row_e1["delisted_utc"] == delist["delisted_utc"]
           and row_e1["token_price"] == 6
           and shown["criteria"]["include_delisted"] is True
           and am.api_search()["count"] == 4)
    record("AC-AMSQ5", ok5,
           "default scan order=%r include_delisted order=%r"
           " stamp match=%r price=%d default count=%d"
           % (ids(hidden), ids(shown),
              row_e1["delisted_utc"] == delist["delisted_utc"],
              row_e1["token_price"], am.api_search()["count"]))

    # -- AC-AMSQ6 gate family, gate order, zero side effects --------------
    dig = market_digests(am)
    kw_codes = []
    for form in BAD_KEYWORDS:
        try:
            am.api_search(keyword=form)
            kw_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            kw_codes.append(code_of(exc))
    dev_codes = []
    for form in BAD_DEVS:
        try:
            am.api_search(dev_account=form)
            dev_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            dev_codes.append(code_of(exc))
    price_codes = []
    for form in BAD_PRICES:
        try:
            am.api_search(min_price=form)
            price_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            price_codes.append(code_of(exc))
    try:
        am.api_search(min_price=20, max_price=5)
        price_codes.append("NO-RAISE")
    except A.ApiMarketError as exc:
        price_codes.append(code_of(exc))
    flag_codes = []
    for form in BAD_FLAGS:
        try:
            am.api_search(include_delisted=form)
            flag_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            flag_codes.append(code_of(exc))
    order = []
    probes = [
        ({"keyword": 123, "dev_account": "bob"},
         "E_AM_BAD_ARGS"),
        ({"dev_account": "bob", "min_price": 0},
         "E_AM_BAD_ACCOUNT"),
        ({"keyword": "scan", "min_price": 0},
         "E_AM_BAD_PRICE"),
        ({"keyword": "scan", "min_price": 10, "max_price": 5},
         "E_AM_BAD_PRICE"),
        ({"keyword": "scan", "include_delisted": "yes"},
         "E_AM_BAD_ARGS"),
    ]
    for kwargs, _expected in probes:
        try:
            am.api_search(**kwargs)
            order.append("NO-RAISE")
        except A.ApiMarketError as exc:
            order.append(code_of(exc))
    dig_after = market_digests(am)
    ok6 = (kw_codes == ["E_AM_BAD_ARGS"] * len(BAD_KEYWORDS)
           and dev_codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_DEVS)
           and price_codes == ["E_AM_BAD_PRICE"] * (len(BAD_PRICES) + 1)
           and flag_codes == ["E_AM_BAD_ARGS"] * len(BAD_FLAGS)
           and order == [p[1] for p in probes]
           and dig_after == dig)
    record("AC-AMSQ6", ok6,
           "keyword=%r dev=%r price=%r flag=%r order=%r frozen=%r"
           % (kw_codes, dev_codes, price_codes, flag_codes, order,
              dig_after == dig))

    # -- AC-AMSQ7 ordering law + pure read -------------------------------
    fam_a = search_family(am)
    fam_b = search_family(am)
    dig_read = market_digests(am)
    tx_after = ledger_tx_ids(led)
    prices = [r["token_price"] for r in am.api_search()["listings"]]
    ok7 = (fam_a == fam_b
           and dig_read == dig_after
           and tx_after == tx_before
           and prices == sorted(prices)
           and am.api_search()["listings"][0]["listing_id"] == d2
           and am.api_search()["listings"][1]["listing_id"] == e2)
    record("AC-AMSQ7", ok7,
           "repeat identical=%r digests frozen=%r tx constant=%r"
           " price order=%r tie pair=%r"
           % (fam_a == fam_b, dig_read == dig_after,
              tx_after == tx_before, prices,
              (am.api_search()["listings"][0]["listing_id"] == d2,
               am.api_search()["listings"][1]["listing_id"] == e2)))

    # -- AC-AMSQ8 cross-restart identity + wiring ------------------------
    family_one = search_family(am)
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    family_two = search_family(am2)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    family_three = search_family(am3)
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-search" in handle.read()
    ok8 = (family_one == family_two == family_three and wired)
    record("AC-AMSQ8", ok8,
           "instance1==2==3 byte-identical=%r runner wiring=%r"
           % (family_one == family_two == family_three, wired))

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