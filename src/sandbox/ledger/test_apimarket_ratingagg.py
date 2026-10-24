"""Acceptance suite for the apimarket rating aggregate precision
and gate-order example window (BigDomain R2077; canon = the
explore-queue row seeded by R2076 and claimed in R2077, criteria
AC-AMRT1..AC-AMRT8 registered in the claim note BEFORE this code
existed - honesty law; the AC-AMRT prefix, the suite name and the
ledger-apimarket-ratingagg runner label were all git-grep
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.rate_api / _agg_rating /
api_view / api_board / api_ratings. AC-AM5 pinned the single
rating seat (purchaser-only, one immutable row). This window
pins the aggregate and ordering surface around it:

  - the baseline read family (count, float average, rater order)
    agreeing across api_view, api_board and api_ratings;
  - purchaser-only fail-closed plus append-only immutability (a
    repeat is rejected and the first value is never updated);
  - the bad-args gate family and its ORDER: the account gate
    precedes the star gate, and the star gate precedes the
    listing lookup (an unknown listing with bad stars answers
    BAD_STARS, not UNKNOWN_LISTING);
  - aggregate arithmetic exactness (integer ratios, a repeating
    decimal compared by float repr, single-rater and zero-rater
    honest states);
  - cross-listing zero permeation;
  - cross-restart byte identity of the whole read family;
  - the pure-read law and zero token movement (ratings never
    touch the ledger);
  - hygiene: product sha256 double-proof, pure ASCII, zero
    network imports, registry wiring, criteria count.

Usage: python test_apimarket_ratingagg.py
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

BAD_STARS = [0, 6, -1, True, 2.5, "5", None]
BAD_ACCOUNTS = ["", "bob", "usr:", None]
UNKNOWN_LISTING = 999999


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
    out = {t: table_digest(conn, t) for t in
           ("apimarket_listings", "apimarket_purchases",
            "apimarket_ratings")}
    conn.close()
    return out


def ledger_tx_ids(led):
    conn = sqlite3.connect(led.db_path)
    ids = set(str(r[0]) for r in conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall())
    conn.close()
    return ids


def read_family(am, ids):
    out = {}
    for name, lid in ids:
        out[name] = dumps(am.api_view(lid))
        out["ratings:" + name] = dumps(am.api_ratings(lid))
    out["board"] = dumps(am.api_board())
    return out


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


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-ratingagg-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AMRT-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AMRT-S",
                     "settlement")
    buyers = ("bob", "carol", "dave", "erin", "alice", "frank",
              "gina", "henry")
    for who in buyers:
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)

    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)
    d2 = d2["listing_id"]
    d3 = am.publish_api("usr:dana", "signal-desk", "Signal Desk API",
                        "rating-free listing", PAYLOAD, 5,
                        False)["listing_id"]
    for who, lid, ref in (("bob", d1, "ref-bob-d1"),
                          ("carol", d1, "ref-carol-d1"),
                          ("dave", d1, "ref-dave-d1"),
                          ("erin", d2, "ref-erin-d2"),
                          ("bob", d3, "ref-bob-d3")):
        am.purchase_api("usr:" + who, lid, ref)

    # token baseline AFTER the purchase world (purchases do move
    # tokens; the rating face must never move any)
    tx_after_purchases = ledger_tx_ids(led)

    am.rate_api("usr:bob", d1, 5)
    am.rate_api("usr:carol", d1, 4)
    am.rate_api("usr:dave", d1, 1)
    am.rate_api("usr:erin", d2, 3)

    ids = [("d1", d1), ("d2", d2), ("d3", d3)]

    # -- AC-AMRT1 baseline read family -----------------------------------
    view1 = am.api_view(d1)
    view2 = am.api_view(d2)
    ratings1 = am.api_ratings(d1)
    board = am.api_board()
    board_by_id = {row["listing_id"]: row for row in board["listings"]}
    order = [r["buyer_id"] for r in ratings1["ratings"]]
    ok1 = (view1["rating_count"] == 3
           and view1["rating_avg"] == 10.0 / 3.0
           and ratings1["rating_count"] == 3
           and order == ["usr:bob", "usr:carol", "usr:dave"]
           and [r["stars"] for r in ratings1["ratings"]] == [5, 4, 1]
           and board_by_id[d1]["rating_count"] == 3
           and board_by_id[d1]["rating_avg"] == view1["rating_avg"]
           and view2["rating_count"] == 1
           and view2["rating_avg"] == 3.0
           and board_by_id[d2]["rating_avg"] == 3.0
           and view1["disclaimer"] == DISCLAIMER
           and board["disclaimer"] == DISCLAIMER)
    record("AC-AMRT1", ok1,
           "count/avg/order pinned d1={3,%r} d2={1,3.0} board agrees"
           % view1["rating_avg"])

    # -- AC-AMRT2 purchaser-only + append-only immutability --------------
    digests_before = market_digests(am)
    snap_before = (view1["rating_count"], view1["rating_avg"])
    code_not_buyer = None
    try:
        am.rate_api("usr:alice", d1, 5)
    except A.ApiMarketError as exc:
        code_not_buyer = code_of(exc)
    code_dup = None
    try:
        am.rate_api("usr:bob", d1, 1)
    except A.ApiMarketError as exc:
        code_dup = code_of(exc)
    after = am.api_ratings(d1)
    bob_stars = [r["stars"] for r in after["ratings"]
                 if r["buyer_id"] == "usr:bob"]
    digests_after = market_digests(am)
    ok2 = (code_not_buyer == "E_AM_NOT_BUYER"
           and code_dup == "E_AM_RATE_DUP"
           and bob_stars == [5]
           and (after["rating_count"], after["rating_avg"]) == snap_before
           and digests_after == digests_before)
    record("AC-AMRT2", ok2,
           "not-buyer=%s dup=%s bob-stars=%r tables frozen=%r"
           % (code_not_buyer, code_dup, bob_stars,
              digests_after == digests_before))

    # -- AC-AMRT3 bad-args gate family AND gate order --------------------
    star_codes = []
    for form in BAD_STARS:
        try:
            am.rate_api("usr:bob", d2, form)
            star_codes.append(None)
        except A.ApiMarketError as exc:
            star_codes.append(code_of(exc))
    account_codes = []
    for form in BAD_ACCOUNTS:
        try:
            am.rate_api(form, d1, 5)
            account_codes.append(None)
        except A.ApiMarketError as exc:
            account_codes.append(code_of(exc))
    unknown_code = None
    try:
        am.rate_api("usr:bob", UNKNOWN_LISTING, 7)
    except A.ApiMarketError as exc:
        unknown_code = code_of(exc)
    order_account = None
    try:
        am.rate_api("bob", UNKNOWN_LISTING, 7)
    except A.ApiMarketError as exc:
        order_account = code_of(exc)
    digests_after_bad = market_digests(am)
    # the account shape gate is a prefix gate: "usr:" passes the
    # shape test and is then stopped by the purchaser gate, which
    # is still fail-closed (no purchase row can name an empty id)
    expect_accounts = ["E_AM_BAD_ACCOUNT", "E_AM_BAD_ACCOUNT",
                       "E_AM_NOT_BUYER", "E_AM_BAD_ACCOUNT"]
    ok3 = (star_codes == ["E_AM_BAD_STARS"] * len(BAD_STARS)
           and account_codes == expect_accounts
           and unknown_code == "E_AM_BAD_STARS"
           and order_account == "E_AM_BAD_ACCOUNT"
           and digests_after_bad == digests_before)
    record("AC-AMRT3", ok3,
           "stars=%r accounts=%r (usr: empty-suffix caught by the"
           " purchaser gate) unknown-listing-with-bad-stars=%s"
           " account-gate-first=%s tables frozen=%r"
           % (star_codes, account_codes, unknown_code,
              order_account, digests_after_bad == digests_before))

    # -- AC-AMRT4 aggregate arithmetic -----------------------------------
    # every purchase of this block lands first, so the token
    # baseline for the zero-token proof sits exactly between the
    # purchase world and the rating calls that follow
    for who in ("alice", "frank", "gina", "henry"):
        am.purchase_api("usr:" + who, d1, "ref-" + who + "-d1")
    tx_after_all_purchases = ledger_tx_ids(led)
    am.rate_api("usr:alice", d1, 5)          # now 4 raters, 15 / 4
    four = am.api_view(d1)
    ok4a = four["rating_count"] == 4 and four["rating_avg"] == 3.75
    for who in ("frank", "gina", "henry"):
        am.rate_api("usr:" + who, d1, 5)     # now 7 raters, 30 / 7
    seven = am.api_view(d1)
    expected = 30.0 / 7.0
    ok4b = (seven["rating_count"] == 7
            and repr(seven["rating_avg"]) == repr(expected))
    single = am.api_view(d2)
    zero = am.api_view(d3)
    ok4 = (ok4a and ok4b
           and single["rating_avg"] == 3.0
           and single["rating_count"] == 1
           and zero["rating_count"] == 0
           and zero["rating_avg"] == 0.0)
    record("AC-AMRT4", ok4,
           "4 raters=%r 7 raters repr=%r expected=%r single=%r zero=%r"
           % (four["rating_avg"], repr(seven["rating_avg"]),
              repr(expected), single["rating_avg"], zero["rating_avg"]))

    # -- AC-AMRT5 cross-listing zero permeation --------------------------
    board_after = am.api_board()
    by_id = {row["listing_id"]: row for row in board_after["listings"]}
    view_after = {lid: am.api_view(lid) for _n, lid in ids}
    ok5 = True
    for lid in (d1, d2, d3):
        ok5 = ok5 and (by_id[lid]["rating_count"]
                       == view_after[lid]["rating_count"])
        ok5 = ok5 and (by_id[lid]["rating_avg"]
                       == view_after[lid]["rating_avg"])
    ok5 = ok5 and by_id[d2]["rating_count"] == 1
    ok5 = ok5 and by_id[d3]["rating_count"] == 0
    ok5 = ok5 and by_id[d1]["rating_count"] == 7
    record("AC-AMRT5", ok5,
           "board-per-view agree d1=%d d2=%d d3=%d"
           % (by_id[d1]["rating_count"], by_id[d2]["rating_count"],
              by_id[d3]["rating_count"]))

    # -- AC-AMRT6 cross-restart byte identity ----------------------------
    snapshot = read_family(am, ids)
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    reopened = read_family(am, ids)
    diff = [k for k in snapshot if snapshot[k] != reopened[k]]
    record("AC-AMRT6", not diff,
           "five read faces byte-identical across restart, diff=%r"
           % diff)

    # -- AC-AMRT7 pure-read law + zero token movement --------------------
    digests_read_before = market_digests(am)
    for _ in range(2):
        for _n, lid in ids:
            am.api_view(lid)
            am.api_ratings(lid)
        am.api_board()
    digests_read_after = market_digests(am)
    tx_final = ledger_tx_ids(led)
    ok7 = (digests_read_before == digests_read_after
           and tx_final == tx_after_all_purchases)
    record("AC-AMRT7", ok7,
           "read battery digests frozen=%r ledger_tx count=%d"
           " unchanged-since-last-purchase=%r"
           % (digests_read_before == digests_read_after,
              len(tx_final), tx_final == tx_after_all_purchases))

    # -- AC-AMRT8 hygiene + delivery -------------------------------------
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    outside_repo = not os.path.abspath(tmp).startswith(
        os.path.abspath(repo_root) + os.sep)
    src = open(os.path.abspath(__file__), "rb").read()
    ascii_ok = all(b < 128 for b in src)
    network_imports = []
    for line in src.decode("ascii").split("\n"):
        stripped = line.strip()
        if not stripped.startswith(("import ", "from ")):
            continue
        for lib in ("urllib", "requests", "socket", "http", "ftplib"):
            if lib in stripped:
                network_imports.append(stripped)
    runner = open(os.path.join(os.path.dirname(BASE),
                               "reconcile_all.py"), "rb").read().decode(
                                   "utf-8")
    wired = ("ledger-apimarket-ratingagg" in runner
             and "test_apimarket_ratingagg.py" in runner)
    ok8 = (shas_after == shas_before and outside_repo and ascii_ok
           and not network_imports and wired
           and len(RESULTS) + 1 == 8)
    record("AC-AMRT8", ok8,
           "product sha unchanged=%r world outside repo=%r ascii=%r"
           " network-imports=%r wired=%r criteria=%d"
           % (shas_after == shas_before, outside_repo, ascii_ok,
              network_imports, wired, len(RESULTS)))

    close_stack(am, dk, metered, led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %s %d/%d criteria=%d"
          % ("PASS" if passed == total else "FAIL", passed, total,
             total))
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()