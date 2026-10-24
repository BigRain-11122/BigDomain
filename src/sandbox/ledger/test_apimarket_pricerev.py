"""Acceptance suite for the apimarket listing price-revision
(repricing) face (BigDomain R2079; canon = the explore-queue row
seeded and claimed in R2079, criteria AC-AMPR1..AC-AMPR8
registered in that claim note BEFORE this code existed - honesty
law; the AC-AMPR prefix, the suite name and the
ledger-apimarket-pricerev runner label were all git-grep
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.revise_price /
api_price_history / api_view / api_board / purchase_api. Until
this window a listing's asking price was frozen forever at
publish time (the listing row is immutable). This window pins the
seller-side repricing door:

  - one append-only revision row per call, never an UPDATE; the
    base listing price is preserved on the row and the newest
    revision is the live asking price;
  - the pinned gate order (account shape -> listing shape and
    existence -> ownership -> retired state -> price shape ->
    unchanged state), proven by probes that would answer a
    different code under any other order;
  - the unchanged-price refusal with zero rows, while a
    revise-back to an older price is legal;
  - purchase charged at the CURRENT price with the integer split
    law intact, older purchase rows keeping their original
    price_paid;
  - retirement interaction (repricing refused, history
    readable, board exclusion unchanged);
  - the read faces (api_view additive pair, api_price_history,
    per-listing isolation) and the pure-read law;
  - cross-restart byte identity of the read family and zero
    token movement across the revision batch.

Usage: python test_apimarket_pricerev.py
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

BAD_ACCOUNTS = ["", "bob", "usr:", None]
# The account gate is prefix-only (the truthful shape finding of
# R2077 AC-AMRT3 / R2078 AC-AMD4): the bare "usr:" form passes the
# shape gate and is then stopped by the ownership gate
# (E_AM_NOT_OWNER) - fail-closed either way. Pinned here rather
# than bending the product.
EXPECTED_ACCOUNT_CODES = ["E_AM_BAD_ACCOUNT", "E_AM_BAD_ACCOUNT",
                          "E_AM_NOT_OWNER", "E_AM_BAD_ACCOUNT"]
BAD_LISTING_IDS = [0, -1, True, 2.5, "1", None]
BAD_PRICES = [0, -1, True, 2.5, "7", None]
UNKNOWN_LISTING = 999999

REVISION_KEYS = {"revision_id", "listing_id", "dev_account",
                 "listing_key", "previous_price", "token_price",
                 "revision_count", "revised_utc", "disclaimer"}

HISTORY_KEYS = {"listing_id", "base_price", "current_price",
                "revision_count", "delisted", "delisted_utc",
                "disclaimer", "revisions"}

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


def revision_rows(am):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT revision_id, listing_id, dev_account, token_price,"
        " revised_utc FROM apimarket_price_revisions"
        " ORDER BY revision_id").fetchall()
    conn.close()
    return rows


def ledger_tx_ids(led):
    conn = sqlite3.connect(led.db_path)
    ids = set(str(r[0]) for r in conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall())
    conn.close()
    return ids


def read_family(am, d1, d2):
    return {"view-d1": dumps(am.api_view(d1)),
            "view-d2": dumps(am.api_view(d2)),
            "board": dumps(am.api_board()),
            "ratings-d1": dumps(am.api_ratings(d1)),
            "sales-dana": dumps(am.api_sales("usr:dana")),
            "history-d1": dumps(am.api_price_history(d1)),
            "history-d2": dumps(am.api_price_history(d2)),
            "devboard": dumps(am.dev_sales_board())}


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
    """Owner dana with two listings (10 and 3); bob/carol buy the
    listing that gets repriced and erin buys the one that is later
    retired. The pre-revision purchases are the old-price anchor
    for AC-AMPR5."""
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AMPR-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AMPR-S",
                     "settlement")
    for who in ("bob", "carol", "erin", "frank", "otto"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:otto", "otto-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3,
                        True)["listing_id"]
    am.purchase_api("usr:bob", d1, "ref-bob-d1")
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    am.purchase_api("usr:erin", d2, "ref-erin-d2")
    return d1, d2


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-pricerev-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2 = seed_world(led, dk, am)

    tx_before_revisions = ledger_tx_ids(led)
    digests_before = market_digests(am)

    # -- AC-AMPR1 revision contract --------------------------------------
    env = am.revise_price("usr:dana", d1, 15)
    rows = revision_rows(am)
    view1 = am.api_view(d1)
    board = {r["listing_id"]: r for r in am.api_board()["listings"]}
    ok1 = (set(env.keys()) == REVISION_KEYS
           and env["listing_id"] == d1
           and env["dev_account"] == "usr:dana"
           and env["listing_key"] == "risk-scan"
           and env["previous_price"] == 10
           and env["token_price"] == 15
           and env["revision_count"] == 1
           and env["revised_utc"]
           and env["disclaimer"] == DISCLAIMER
           and len(rows) == 1
           and rows[0][1] == d1
           and rows[0][2] == "usr:dana"
           and rows[0][3] == 15
           and rows[0][4] == env["revised_utc"]
           and view1["token_price"] == 15
           and view1["base_token_price"] == 10
           and view1["revision_count"] == 1
           and board[d1]["token_price"] == 15)
    record("AC-AMPR1", ok1,
           "envelope nine keys=%r one revision row=%r"
           " view price %d base %d board %d"
           % (set(env.keys()) == REVISION_KEYS, len(rows) == 1,
              view1["token_price"], view1["base_token_price"],
              board[d1]["token_price"]))
    first_stamp = env["revised_utc"]

    # -- AC-AMPR2 ownership + account gate fail-closed -------------------
    dig = market_digests(am)
    code_owner = None
    try:
        am.revise_price("usr:otto", d1, 20)
    except A.ApiMarketError as exc:
        code_owner = code_of(exc)
    account_codes = []
    for form in BAD_ACCOUNTS:
        try:
            am.revise_price(form, d1, 20)
            account_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            account_codes.append(code_of(exc))
    dig_after = market_digests(am)
    account_rejected = (account_codes == EXPECTED_ACCOUNT_CODES
                        and all(c != "NO-RAISE" for c in account_codes))
    ok2 = (code_owner == "E_AM_NOT_OWNER"
           and account_rejected
           and dig_after == dig
           and len(revision_rows(am)) == 1)
    record("AC-AMPR2", ok2,
           "non-owner=%s account codes=%r prefix-only usr: is"
           " stopped by ownership=%r digests frozen=%r rows=%d"
           % (code_owner, account_codes, account_rejected,
              dig_after == dig, len(revision_rows(am))))

    # -- AC-AMPR3 pinned gate order --------------------------------------
    order = {}

    def probe(label, fn):
        try:
            fn()
            order[label] = "NO-RAISE"
        except A.ApiMarketError as exc:
            order[label] = code_of(exc)

    probe("unknown+badprice",
          lambda: am.revise_price("usr:dana", UNKNOWN_LISTING, 0))
    probe("nonowner+badprice",
          lambda: am.revise_price("usr:otto", d1, 0))
    am.delist_api("usr:dana", d2)
    probe("retired+badprice",
          lambda: am.revise_price("usr:dana", d2, 0))
    probe("own-live+badprice",
          lambda: am.revise_price("usr:dana", d1, 0))
    shape_codes = []
    for form in BAD_LISTING_IDS:
        try:
            am.revise_price("usr:dana", form, 20)
            shape_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            shape_codes.append(code_of(exc))
    ok3 = (order == {"unknown+badprice": "E_AM_UNKNOWN_LISTING",
                     "nonowner+badprice": "E_AM_NOT_OWNER",
                     "retired+badprice": "E_AM_DELISTED",
                     "own-live+badprice": "E_AM_BAD_PRICE"}
           and shape_codes == ["E_AM_BAD_ARGS"] * len(BAD_LISTING_IDS)
           and len(revision_rows(am)) == 1)
    record("AC-AMPR3", ok3,
           "order=%r shape forms=%d all bad-args=%r rows=%d"
           % (order, len(shape_codes),
              all(c == "E_AM_BAD_ARGS" for c in shape_codes),
              len(revision_rows(am))))

    # -- AC-AMPR4 unchanged refusal + legal revise-back ------------------
    code_same = None
    try:
        am.revise_price("usr:dana", d1, 15)
    except A.ApiMarketError as exc:
        code_same = code_of(exc)
    rows_same = revision_rows(am)
    back = am.revise_price("usr:dana", d1, 10)
    up_again = am.revise_price("usr:dana", d1, 12)
    rows_end = revision_rows(am)
    ok4 = (code_same == "E_AM_PRICE_UNCHANGED"
           and len(rows_same) == 1
           and rows_same[0][4] == first_stamp
           and back["previous_price"] == 15
           and back["token_price"] == 10
           and back["revision_count"] == 2
           and up_again["previous_price"] == 10
           and up_again["token_price"] == 12
           and up_again["revision_count"] == 3
           and [r[3] for r in rows_end] == [15, 10, 12]
           and am.api_view(d1)["token_price"] == 12)
    record("AC-AMPR4", ok4,
           "same code=%s rows=%d stamp preserved=%r"
           " back=%d->%d up=%d->%d series=%r"
           % (code_same, len(rows_same),
              rows_same[0][4] == first_stamp,
              back["previous_price"], back["token_price"],
              up_again["previous_price"], up_again["token_price"],
              [r[3] for r in rows_end]))

    # -- AC-AMPR5 purchase charges the current price ---------------------
    tx_after_revisions = ledger_tx_ids(led)
    sale = am.purchase_api("usr:frank", d1, "ref-frank-d1")
    sales = {s["purchase_id"]: s
             for s in am.api_sales("usr:dana")["sales"]}
    bob_row = [s for s in sales.values() if s["buyer_id"] == "usr:bob"][0]
    tx_after_buy = ledger_tx_ids(led)
    new_tx = sorted(tx_after_buy - tx_after_revisions)
    ok5 = (sale["price_paid"] == 12
           and sale["dev_share"] == 9
           and sale["platform_share"] == 3
           and sale["dev_share"] + sale["platform_share"]
           == sale["price_paid"]
           and bob_row["price_paid"] == 10
           and bob_row["dev_share"] == 7
           and bob_row["platform_share"] == 3
           and len(new_tx) == 2)
    record("AC-AMPR5", ok5,
           "frank price=%d split=%d/%d older bob price=%d"
           " split=%d/%d new txs=%d"
           % (sale["price_paid"], sale["dev_share"],
              sale["platform_share"], bob_row["price_paid"],
              bob_row["dev_share"], bob_row["platform_share"],
              len(new_tx)))

    # -- AC-AMPR6 retirement interaction ---------------------------------
    code_retired = None
    try:
        am.revise_price("usr:dana", d2, 5)
    except A.ApiMarketError as exc:
        code_retired = code_of(exc)
    hist_d2 = am.api_price_history(d2)
    view_d2 = am.api_view(d2)
    board_ids = [r["listing_id"] for r in am.api_board()["listings"]]
    ok6 = (code_retired == "E_AM_DELISTED"
           and hist_d2["delisted"] is True
           and hist_d2["base_price"] == 3
           and hist_d2["current_price"] == 3
           and hist_d2["revision_count"] == 0
           and hist_d2["revisions"] == []
           and view_d2["delisted"] is True
           and view_d2["purchase_count"] == 1
           and d2 not in board_ids
           and d1 in board_ids)
    record("AC-AMPR6", ok6,
           "retired revise=%s history base=%d current=%d"
           " revisions=%d board excludes=%r"
           % (code_retired, hist_d2["base_price"],
              hist_d2["current_price"], hist_d2["revision_count"],
              d2 not in board_ids))

    # -- AC-AMPR7 read faces + isolation + pure read ---------------------
    hist_d1 = am.api_price_history(d1)
    view_now = am.api_view(d1)
    dig_read = market_digests(am)
    family_a = read_family(am, d1, d2)
    family_b = read_family(am, d1, d2)
    dig_after_read = market_digests(am)
    ok7 = (set(hist_d1.keys()) == HISTORY_KEYS
           and hist_d1["base_price"] == 10
           and hist_d1["current_price"] == 12
           and hist_d1["revision_count"] == 3
           and [r["token_price"] for r in hist_d1["revisions"]]
           == [15, 10, 12]
           and [r["revision_id"] for r in hist_d1["revisions"]]
           == [1, 2, 3]
           and view_now["revision_count"] == 3
           and view_now["latest_revision_utc"]
           == hist_d1["revisions"][-1]["revised_utc"]
           and hist_d2["revision_count"] == 0
           and family_a == family_b
           and dig_after_read == dig_read)
    record("AC-AMPR7", ok7,
           "history keys=%r series=%r view revs=%d latest=%r"
           " d2 revs=%d pure-read digests frozen=%r"
           % (set(hist_d1.keys()) == HISTORY_KEYS,
              [r["token_price"] for r in hist_d1["revisions"]],
              view_now["revision_count"],
              bool(view_now["latest_revision_utc"]),
              hist_d2["revision_count"],
              dig_after_read == dig_read))

    # -- AC-AMPR8 zero token movement + cross-restart identity ----------
    zero_move = (tx_before_revisions == tx_after_revisions)
    family_before_restart = read_family(am, d1, d2)
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    family_after_restart = read_family(am2, d1, d2)
    same = family_before_restart == family_after_restart
    same_rows = revision_rows(am2)
    code_after = None
    try:
        am2.revise_price("usr:dana", d1, 12)
    except A.ApiMarketError as exc:
        code_after = code_of(exc)
    close_stack(am2, dk2, metered2, led2)
    ok8 = (zero_move
           and same
           and len(same_rows) == 3
           and code_after == "E_AM_PRICE_UNCHANGED")
    record("AC-AMPR8", ok8,
           "revision batch moved zero tokens=%r restart family"
           " byte-identical=%r rows=%d post-restart no-op=%s"
           % (zero_move, same, len(same_rows), code_after))

    # -- hygiene ----------------------------------------------------------
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    ascii_ok = True
    with open(os.path.abspath(__file__), "rb") as handle:
        blob = handle.read()
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