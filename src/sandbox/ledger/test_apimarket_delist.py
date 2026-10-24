"""Acceptance suite for the apimarket listing retirement (delist)
face and its purchase fail-closed window (BigDomain R2078; canon =
the explore-queue row seeded and claimed in R2078, criteria
AC-AMD1..AC-AMD8 registered in the claim note BEFORE this code
existed - honesty law; the AC-AMD prefix, the suite name and the
ledger-apimarket-delist runner label were all git-grep
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.delist_api / _delisted_utc /
purchase_api / api_view / api_board. Until this window the face
had publish/purchase/rate doors only - a listing, once published,
could never be retired. This window pins the seller-side door:

  - exactly one append-only delisting row per listing, with a
    seven-key envelope carrying the resident disclaimer;
  - the ownership gate (a registered non-owner is refused with
    zero rows and frozen table digests);
  - the repeat-delist refusal (E_AM_ALREADY_DELISTED, zero new
    rows, the first delisted_utc never rewritten);
  - the bad-args gate family AND its order (account shape first,
    then the listing shape/existence gate, then ownership - an
    unknown listing probed by a non-owner answers
    UNKNOWN_LISTING, not NOT_OWNER);
  - purchase fail-closed on a retired listing (zero spend, the
    delist gate preceding the self-buy gate), while a live
    listing in the same world stays purchasable;
  - the read-face semantics (api_view's additive delisted pair
    with every historical aggregate unchanged, the market board
    excluding retired rows, ratings/sales history still
    answering, the developer board keeping its listing-side row
    authority);
  - cross-restart persistence of the retired state across two
    full-stack restarts;
  - zero token movement from the retirement batch (the only new
    ledger txs are the one live purchase's spend + share pair),
    hygiene and registry wiring.

Usage: python test_apimarket_delist.py
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
BAD_LISTING_IDS = [0, -1, True, 2.5, "1", None]
UNKNOWN_LISTING = 999999

ENVELOPE_KEYS = {"listing_id", "dev_account", "listing_key",
                 "delisted", "delisted_utc", "already",
                 "disclaimer"}


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


TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings")


def market_digests(am):
    conn = sqlite3.connect(am.db_path)
    out = {t: table_digest(conn, t) for t in TABLES}
    conn.close()
    return out


def delist_rows(am):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT listing_id, dev_account, delisted_utc FROM"
        " apimarket_delistings ORDER BY delist_id").fetchall()
    conn.close()
    return rows


def ledger_tx_ids(led):
    conn = sqlite3.connect(led.db_path)
    ids = set(str(r[0]) for r in conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall())
    conn.close()
    return ids


def read_family(am, retired_id, live_id):
    out = {"view-retired": dumps(am.api_view(retired_id)),
           "view-live": dumps(am.api_view(live_id)),
           "board": dumps(am.api_board()),
           "ratings-retired": dumps(am.api_ratings(retired_id)),
           "sales-dana": dumps(am.api_sales("usr:dana")),
           "devboard": dumps(am.dev_sales_board())}
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


def seed_world(led, dk, am):
    """Owner dana with two listings; bob/carol buy the listing that
    will be retired and rate it; erin buys the one that stays
    live."""
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AMD-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AMD-S",
                     "settlement")
    for who in ("bob", "carol", "erin", "frank", "gina", "henry"):
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
    am.rate_api("usr:bob", d1, 5)
    am.rate_api("usr:carol", d1, 4)
    am.purchase_api("usr:erin", d2, "ref-erin-d2")
    return d1, d2


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-delist-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2 = seed_world(led, dk, am)

    view_before = am.api_view(d1)
    board_before = [r["listing_id"] for r in
                    am.api_board()["listings"]]
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)

    # -- AC-AMD1 retirement contract -------------------------------------
    env = am.delist_api("usr:dana", d1)
    rows = delist_rows(am)
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["listing_id"] == d1
           and env["dev_account"] == "usr:dana"
           and env["listing_key"] == "risk-scan"
           and env["delisted"] is True
           and env["already"] is False
           and env["delisted_utc"]
           and env["disclaimer"] == DISCLAIMER
           and len(rows) == 1
           and rows[0][0] == d1
           and rows[0][1] == "usr:dana"
           and rows[0][2] == env["delisted_utc"])
    record("AC-AMD1", ok1,
           "envelope seven keys=%r one delist row stamp match=%r"
           % (set(env.keys()) == ENVELOPE_KEYS, rows[0][2]
              == env["delisted_utc"]))
    stamp = env["delisted_utc"]

    # -- AC-AMD2 ownership gate fail-closed ------------------------------
    dig_two = market_digests(am)
    code_owner = None
    try:
        am.delist_api("usr:otto", d1)
    except A.ApiMarketError as exc:
        code_owner = code_of(exc)
    dig_two_after = market_digests(am)
    ok2 = (code_owner == "E_AM_NOT_OWNER"
           and dig_two_after == dig_two
           and len(delist_rows(am)) == 1)
    record("AC-AMD2", ok2,
           "non-owner code=%s digests frozen=%r rows=%d"
           % (code_owner, dig_two_after == dig_two,
              len(delist_rows(am))))

    # -- AC-AMD3 repeat delist refusal -----------------------------------
    code_dup = None
    try:
        am.delist_api("usr:dana", d1)
    except A.ApiMarketError as exc:
        code_dup = code_of(exc)
    rows_after_dup = delist_rows(am)
    ok3 = (code_dup == "E_AM_ALREADY_DELISTED"
           and len(rows_after_dup) == 1
           and rows_after_dup[0][2] == stamp)
    record("AC-AMD3", ok3,
           "repeat code=%s rows=%d stamp preserved=%r"
           % (code_dup, len(rows_after_dup),
              rows_after_dup[0][2] == stamp))

    # -- AC-AMD4 bad-args gate family and order --------------------------
    account_codes = []
    for form in BAD_ACCOUNTS:
        try:
            am.delist_api(form, UNKNOWN_LISTING)
            account_codes.append(None)
        except A.ApiMarketError as exc:
            account_codes.append(code_of(exc))
    id_codes = []
    for form in BAD_LISTING_IDS:
        try:
            am.delist_api("usr:dana", form)
            id_codes.append(None)
        except A.ApiMarketError as exc:
            id_codes.append(code_of(exc))
    unknown_code = None
    try:
        am.delist_api("usr:otto", UNKNOWN_LISTING)
    except A.ApiMarketError as exc:
        unknown_code = code_of(exc)
    dig_four = market_digests(am)
    # The account gate is prefix-only (the R2077 AC-AMRT3 finding):
    # "usr:" passes the shape gate and therefore reaches the listing
    # existence gate - the honest expected vector, amended in the
    # R2078 queue row.
    expected_accounts = ["E_AM_BAD_ACCOUNT", "E_AM_BAD_ACCOUNT",
                         "E_AM_UNKNOWN_LISTING", "E_AM_BAD_ACCOUNT"]
    ok4 = (account_codes == expected_accounts
           and id_codes == ["E_AM_BAD_ARGS"] * len(BAD_LISTING_IDS)
           and unknown_code == "E_AM_UNKNOWN_LISTING"
           and dig_four == dig_two
           and len(delist_rows(am)) == 1)
    record("AC-AMD4", ok4,
           "accounts=%r ids=%r unknown-by-non-owner=%s frozen=%r"
           % (account_codes, id_codes, unknown_code,
              dig_four == dig_two))

    # -- AC-AMD5 purchase fail-closed + gate order -----------------------
    code_frank = None
    try:
        am.purchase_api("usr:frank", d1, "ref-frank-d1")
    except A.ApiMarketError as exc:
        code_frank = code_of(exc)
    code_self = None
    try:
        am.purchase_api("usr:dana", d1, "ref-dana-d1")
    except A.ApiMarketError as exc:
        code_self = code_of(exc)
    live_env = am.purchase_api("usr:henry", d2, "ref-henry-d2")
    ok5 = (code_frank == "E_AM_DELISTED"
           and code_self == "E_AM_DELISTED"
           and live_env["price_paid"] == 3
           and live_env["disclaimer"] == DISCLAIMER)
    record("AC-AMD5", ok5,
           "retired-buy=%s owner-self-buy=%s live-buy-d2=%r"
           % (code_frank, code_self, live_env["price_paid"]))

    # -- AC-AMD6 read-face semantics -------------------------------------
    view_after = am.api_view(d1)
    view_live = am.api_view(d2)
    board_after = [r["listing_id"] for r in
                   am.api_board()["listings"]]
    ratings_after = am.api_ratings(d1)
    sales_after = am.api_sales("usr:dana")
    dev_rows = {row["dev_account"]: row
                for row in am.dev_sales_board()["board"]}
    dana_row = dev_rows["usr:dana"]
    ok6 = (view_before.get("delisted") is False
           and view_before.get("delisted_utc") is None
           and view_after["delisted"] is True
           and view_after["delisted_utc"] == stamp
           and view_live["delisted"] is False
           and view_after["purchase_count"]
           == view_before["purchase_count"]
           and view_after["rating_count"] == view_before["rating_count"]
           and view_after["rating_avg"] == view_before["rating_avg"]
           and board_before == [d1, d2]
           and board_after == [d2]
           and ratings_after["rating_count"] == 2
           and [r["stars"] for r in ratings_after["ratings"]] == [5, 4]
           and [r["buyer_id"] for r in sales_after["sales"]]
           == ["usr:bob", "usr:carol", "usr:erin", "usr:henry"]
           and dana_row["listing_count"] == 2
           and dana_row["purchase_count"] == 4
           and set(am.api_board().keys()) == {"disclaimer",
                                              "listings"})
    record("AC-AMD6", ok6,
           "view delisted=%r stamp=%r board %r->%r history alive=%r"
           % (view_after["delisted"],
              view_after["delisted_utc"] == stamp, board_before,
              board_after, ratings_after["rating_count"]))

    # -- AC-AMD7 cross-restart persistence -------------------------------
    fam_two = None
    code_restart = None
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    view_two = am.api_view(d1)
    try:
        am.purchase_api("usr:gina", d1, "ref-gina-d1")
        code_restart = "purchased"
    except A.ApiMarketError as exc:
        code_restart = code_of(exc)
    board_two = [r["listing_id"] for r in
                 am.api_board()["listings"]]
    fam_two = read_family(am, d1, d2)
    rows_two = delist_rows(am)
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    fam_three = read_family(am, d1, d2)
    rows_three = delist_rows(am)
    ok7 = (view_two["delisted"] is True
           and view_two["delisted_utc"] == stamp
           and code_restart == "E_AM_DELISTED"
           and board_two == [d2]
           and fam_three == fam_two
           and len(rows_two) == 1 and len(rows_three) == 1
           and rows_three == rows_two)
    record("AC-AMD7", ok7,
           "restart delisted=%r buy-code=%s board=%r family"
           " identical=%r rows=%d"
           % (view_two["delisted"], code_restart, board_two,
              fam_three == fam_two, len(rows_three)))

    # -- AC-AMD8 zero token movement, hygiene, wiring --------------------
    new_txs = ledger_tx_ids(led) - tx_before
    expected = {live_env["spend_tx"], live_env["dev_share_tx"]}
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    repo_root = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
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
    wired = ("ledger-apimarket-delist" in runner
             and "test_apimarket_delist.py" in runner)
    ok8 = (new_txs == expected
           and shas_after == shas_before
           and outside_repo and ascii_ok and not network_imports
           and wired and len(RESULTS) + 1 == 8)
    record("AC-AMD8", ok8,
           "only live-purchase txs=%r product sha unchanged=%r"
           " ascii=%r network=%r wired=%r criteria=%d"
           % (new_txs == expected, shas_after == shas_before,
              ascii_ok, network_imports, wired, len(RESULTS)))

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