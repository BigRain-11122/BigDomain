"""Acceptance suite for the apimarket re-listing (relist) door and
the listing-lifecycle read face (BigDomain R2089; canon = the
explore-queue row seeded and claimed in R2089, criteria
AC-AMRL1..AC-AMRL8 registered in the claim note BEFORE this code
existed - honesty law; the AC-AMRL prefix, relist_api,
api_listing_lifecycle, apimarket_relistings, E_AM_ALREADY_LIVE, the
suite name and the ledger-apimarket-relist runner label were all
git-grep -F zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.relist_api / api_listing_lifecycle /
_cycle_state / delist_api / purchase_api / api_view / api_board /
api_search / dev_profile.

Until this window retirement was terminal: delist_api wrote one
append-only row behind UNIQUE(listing_id), purchase_api failed
closed forever, and a seller who fixed a broken service had to
publish a new listing_key - losing that listing's purchases,
ratings and price history. This window pins the cycle law:

  - one append-only apimarket_relistings row per re-listing, the
    listing live again with every historical aggregate intact and
    every read face flipped by one seam (_delisted_utc ->
    _cycle_state);
  - the gate family AND its pinned order (account shape, listing
    shape/existence, ownership, already-live);
  - multi-cycle append-only retirement (delist -> relist -> delist
    -> relist ...) with no stamp ever rewritten and no row deleted;
  - the market-board exclusion being per CURRENT cycle, not per
    listing ever retired;
  - api_listing_lifecycle answering the whole open/close event
    stream in a deterministic order;
  - pure-read law and zero token movement;
  - cross-restart byte identity across two full-stack restarts;
  - the legacy-database migration (UNIQUE(listing_id) dropped once,
    every existing retirement preserved at cycle 1).

Usage: python test_apimarket_relist.py
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

RELIST_KEYS = {"listing_id", "dev_account", "listing_key", "cycle",
               "relisted_utc", "live", "already", "disclaimer"}
LIFE_KEYS = {"listing_id", "dev_account", "listing_key", "cycle",
             "live", "delisted", "delisted_utc", "delist_count",
             "relist_count", "history", "disclaimer"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings")

LEGACY_SCHEMA = """
CREATE TABLE IF NOT EXISTS apimarket_listings (
    listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dev_account TEXT NOT NULL,
    listing_key TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    token_price INTEGER NOT NULL CHECK (token_price > 0),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0, 1)),
    listed_utc TEXT NOT NULL,
    UNIQUE (dev_account, listing_key)
);
CREATE TABLE IF NOT EXISTS apimarket_purchases (
    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    price_paid INTEGER NOT NULL CHECK (price_paid > 0),
    dev_share INTEGER NOT NULL CHECK (dev_share >= 0),
    platform_share INTEGER NOT NULL CHECK (platform_share >= 0),
    spend_tx TEXT NOT NULL,
    dev_share_tx TEXT NOT NULL,
    purchased_utc TEXT NOT NULL,
    UNIQUE (buyer_id, listing_id),
    CHECK (dev_share + platform_share = price_paid)
);
CREATE TABLE IF NOT EXISTS apimarket_delistings (
    delist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    delisted_utc TEXT NOT NULL,
    UNIQUE (listing_id)
);
"""


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


def delist_rows(am):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT listing_id, dev_account, delisted_utc, cycle FROM"
        " apimarket_delistings ORDER BY delist_id").fetchall()
    conn.close()
    return rows


def relist_rows(am):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT listing_id, dev_account, relisted_utc, cycle FROM"
        " apimarket_relistings ORDER BY relist_id").fetchall()
    conn.close()
    return rows


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


def code_of(exc):
    return getattr(exc, "code", None)


def try_code(fn, *args):
    try:
        fn(*args)
        return None
    except A.ApiMarketError as exc:
        return code_of(exc)


def seed_world(led, dk, am):
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AMRL-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AMRL-S",
                     "settlement")
    for who in ("bob", "carol", "erin", "frank", "gina", "otto"):
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


def read_family(am, d1, d2):
    return {"view-d1": dumps(am.api_view(d1)),
            "view-d2": dumps(am.api_view(d2)),
            "board": dumps(am.api_board()),
            "life-d1": dumps(am.api_listing_lifecycle(d1)),
            "search": dumps(am.api_search()),
            "search_all": dumps(am.api_search(include_delisted=True)),
            "profile-dana": dumps(am.dev_profile("usr:dana")),
            "library-bob": dumps(am.api_library("usr:bob"))}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-relist-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2 = seed_world(led, dk, am)

    # -- AC-AMRL1 re-list contract + one-seam read-face flip ------------
    first_delist = am.delist_api("usr:dana", d1)
    env = am.relist_api("usr:dana", d1)
    rows = relist_rows(am)
    view1 = am.api_view(d1)
    board_ids = [r["listing_id"] for r in am.api_board()["listings"]]
    search_ids = [r["listing_id"] for r in am.api_search()["listings"]]
    search_all = [r["listing_id"] for r in
                  am.api_search(include_delisted=True)["listings"]]
    profile = am.dev_profile("usr:dana")
    life1 = am.api_listing_lifecycle(d1)
    ok1 = (set(env.keys()) == RELIST_KEYS
           and env["listing_id"] == d1
           and env["dev_account"] == "usr:dana"
           and env["listing_key"] == "risk-scan"
           and env["cycle"] == 2
           and env["live"] is True
           and env["already"] is False
           and env["relisted_utc"]
           and env["disclaimer"] == DISCLAIMER
           and len(rows) == 1
           and rows[0][0] == d1 and rows[0][3] == 2
           and rows[0][2] == env["relisted_utc"]
           and view1["delisted"] is False
           and view1["delisted_utc"] is None
           and view1["purchase_count"] == 2
           and view1["rating_count"] == 2
           and board_ids == [d1, d2]
           and sorted(search_ids) == [d1, d2]
           and sorted(search_all) == [d1, d2]
           and profile["live_listing_count"] == 2
           and profile["retired_listing_count"] == 0
           and life1["cycle"] == 2
           and life1["history"] == [
               {"event": "delist", "cycle": 1,
                "utc": first_delist["delisted_utc"]},
               {"event": "relist", "cycle": 2,
                "utc": env["relisted_utc"]}])
    record("AC-AMRL1", ok1,
           "envelope8=%r cycle=%r rows=%d board=%r search=%r "
           "profile_live=%r history=%r"
           % (set(env.keys()) == RELIST_KEYS, env["cycle"],
              len(rows), board_ids, sorted(search_ids),
              profile["live_listing_count"],
              [(e["event"], e["cycle"]) for e in life1["history"]]))

    # -- AC-AMRL2 gate family and pinned order --------------------------
    dig_before = market_digests(am)
    account_codes = [try_code(am.relist_api, form, UNKNOWN_LISTING)
                     for form in BAD_ACCOUNTS]
    id_codes = [try_code(am.relist_api, "usr:dana", form)
                for form in BAD_LISTING_IDS]
    unknown_nonowner = try_code(am.relist_api, "usr:otto",
                                UNKNOWN_LISTING)
    live_nonowner = try_code(am.relist_api, "usr:otto", d2)
    live_owner = try_code(am.relist_api, "usr:dana", d2)
    dig_after = market_digests(am)
    expected_accounts = ["E_AM_BAD_ACCOUNT", "E_AM_BAD_ACCOUNT",
                         "E_AM_UNKNOWN_LISTING", "E_AM_BAD_ACCOUNT"]
    ok2 = (account_codes == expected_accounts
           and id_codes == ["E_AM_BAD_ARGS"] * len(BAD_LISTING_IDS)
           and unknown_nonowner == "E_AM_UNKNOWN_LISTING"
           and live_nonowner == "E_AM_NOT_OWNER"
           and live_owner == "E_AM_ALREADY_LIVE"
           and dig_after == dig_before
           and len(relist_rows(am)) == 1)
    record("AC-AMRL2", ok2,
           "accounts=%r ids=%r unknown=%s nonowner-live=%s "
           "owner-live=%s frozen=%r"
           % (account_codes, id_codes, unknown_nonowner,
              live_nonowner, live_owner, dig_after == dig_before))

    # -- AC-AMRL3 multi-cycle append-only retirement --------------------
    stamps = [first_delist["delisted_utc"], env["relisted_utc"]]
    d_second = am.delist_api("usr:dana", d1)
    stamps.append(d_second["delisted_utc"])
    r_second = am.relist_api("usr:dana", d1)
    stamps.append(r_second["relisted_utc"])
    d_third = am.delist_api("usr:dana", d1)
    stamps.append(d_third["delisted_utc"])
    drows = delist_rows(am)
    rrows = relist_rows(am)
    ok3 = ([r[3] for r in drows] == [1, 2, 3]
           and [r[3] for r in rrows] == [2, 3]
           and [r[2] for r in drows] == [stamps[0], stamps[2],
                                         stamps[4]]
           and [r[2] for r in rrows] == [stamps[1], stamps[3]]
           and all(bool(s) for s in stamps)
           and am.api_view(d1)["delisted"] is True
           and am.api_view(d1)["delisted_utc"] == stamps[4]
           and am.api_view(d1)["purchase_count"] == 2
           and am.api_view(d1)["rating_count"] == 2)
    record("AC-AMRL3", ok3,
           "delist_cycles=%r relist_cycles=%r stamps_nonempty=%r "
           "clock_second_resolution_repeats=%r current_stamp=%s"
           % ([r[3] for r in drows], [r[3] for r in rrows],
              all(bool(s) for s in stamps),
              len(set(stamps)) < 5,
              am.api_view(d1)["delisted_utc"] == stamps[4]))

    # -- AC-AMRL4 cycle-scoped exclusion and post-relist trading --------
    retired_board = [r["listing_id"] for r in
                     am.api_board()["listings"]]
    retired_search = [r["listing_id"] for r in
                      am.api_search()["listings"]]
    retired_all = [r["listing_id"] for r in
                   am.api_search(include_delisted=True)["listings"]]
    retired_profile = am.dev_profile("usr:dana")
    gina_retired = try_code(am.purchase_api, "usr:gina", d1,
                            "ref-gina-retired")
    board_ok4 = (retired_board == [d2]
                 and retired_search == [d2]
                 and sorted(retired_all) == [d1, d2]
                 and retired_profile["live_listing_count"] == 1
                 and retired_profile["retired_listing_count"] == 1
                 and gina_retired == "E_AM_DELISTED")
    tx_cycle = ledger_tx_ids(led)
    r_fourth = am.relist_api("usr:dana", d1)
    gina_env = am.purchase_api("usr:gina", d1, "ref-gina-d1")
    bob_dup = try_code(am.purchase_api, "usr:bob", d1, "ref-bob-d1b")
    tx_after = ledger_tx_ids(led)
    live_board = [r["listing_id"] for r in am.api_board()["listings"]]
    ok4 = (board_ok4
           and r_fourth["cycle"] == 4
           and live_board == [d1, d2]
           and gina_env["price_paid"] == 10
           and gina_env["dev_share"] == 7
           and gina_env["platform_share"] == 3
           and bob_dup == "E_AM_PURCHASE_DUP"
           and len(tx_after) == len(tx_cycle) + 2
           and am.api_view(d1)["purchase_count"] == 3
           and am.api_view(d1)["rating_count"] == 2)
    record("AC-AMRL4", ok4,
           "retired_board=%r retired_search=%r all=%r gina_retired=%s "
           "cycle4=%r live_board=%r new_tx=%d bob_dup=%s"
           % (retired_board, retired_search, retired_all,
              gina_retired, r_fourth["cycle"], live_board,
              len(tx_after) - len(tx_cycle), bob_dup))

    # -- AC-AMRL5 lifecycle history exact -------------------------------
    life = am.api_listing_lifecycle(d1)
    expected_history = [
        {"event": "delist", "cycle": 1, "utc": stamps[0]},
        {"event": "relist", "cycle": 2, "utc": stamps[1]},
        {"event": "delist", "cycle": 2, "utc": stamps[2]},
        {"event": "relist", "cycle": 3, "utc": stamps[3]},
        {"event": "delist", "cycle": 3, "utc": stamps[4]},
        {"event": "relist", "cycle": 4,
         "utc": r_fourth["relisted_utc"]}]
    ok5 = (set(life.keys()) == LIFE_KEYS
           and life["listing_id"] == d1
           and life["dev_account"] == "usr:dana"
           and life["listing_key"] == "risk-scan"
           and life["cycle"] == 4
           and life["live"] is True
           and life["delisted"] is False
           and life["delisted_utc"] is None
           and life["delist_count"] == 3
           and life["relist_count"] == 3
           and life["history"] == expected_history
           and life["disclaimer"] == DISCLAIMER)
    record("AC-AMRL5", ok5,
           "life_keys=%r cycle=%r counts=%d/%d history_len=%d "
           "exact=%r"
           % (set(life.keys()) == LIFE_KEYS, life["cycle"],
              life["delist_count"], life["relist_count"],
              len(life["history"]),
              life["history"] == expected_history))

    # -- AC-AMRL6 pure read, zero token movement ------------------------
    dig_six = market_digests(am)
    tx_six = ledger_tx_ids(led)
    for _ in range(3):
        am.api_listing_lifecycle(d1)
        am.api_view(d1)
        am.api_board()
        am.api_search(include_delisted=True)
        am.dev_profile("usr:dana")
    dig_six_after = market_digests(am)
    tx_six_after = ledger_tx_ids(led)
    unknown_life = try_code(am.api_listing_lifecycle, UNKNOWN_LISTING)
    bad_life = [try_code(am.api_listing_lifecycle, form)
                for form in BAD_LISTING_IDS]
    ok6 = (dig_six_after == dig_six
           and tx_six_after == tx_six
           and unknown_life == "E_AM_UNKNOWN_LISTING"
           and bad_life == ["E_AM_BAD_ARGS"] * len(BAD_LISTING_IDS))
    record("AC-AMRL6", ok6,
           "digests_frozen=%r tx_frozen=%r unknown=%s bad_ids=%r"
           % (dig_six_after == dig_six, tx_six_after == tx_six,
              unknown_life, bad_life))

    # -- AC-AMRL7 cross-restart byte identity ---------------------------
    fam_first = read_family(am, d1, d2)
    close_stack(am, dk, metered, led)
    fam_two = None
    for _restart in range(2):
        led, metered, dk, gate, am = build_stack(db_path, cfg,
                                                 lobby_cfg)
        fam = read_family(am, d1, d2)
        close_stack(am, dk, metered, led)
        if fam_two is None:
            fam_two = fam
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    fam_three = read_family(am, d1, d2)
    life_restart = json.loads(fam_three["life-d1"])
    ok7 = (fam_first == fam_two == fam_three
           and life_restart["cycle"] == 4
           and len(life_restart["history"]) == 6)
    record("AC-AMRL7", ok7,
           "three instances identical=%r restart_cycle=%r "
           "restart_history=%d"
           % (fam_first == fam_two == fam_three,
              life_restart["cycle"],
              len(life_restart["history"])))

    # -- AC-AMRL8 legacy database migration -----------------------------
    legacy_dir = tempfile.mkdtemp(prefix="apimarket-relist-legacy-")
    legacy_led = os.path.join(legacy_dir, "ledger.db")
    legacy_am = os.path.join(legacy_dir, "apimarket.db")
    conn = sqlite3.connect(legacy_am)
    conn.executescript(LEGACY_SCHEMA)
    conn.execute(
        "INSERT INTO apimarket_listings (listing_id, dev_account,"
        " listing_key, title, description, payload_json, token_price,"
        " ai_label, listed_utc) VALUES (1, 'usr:dana', 'legacy-one',"
        " 'Legacy One', 'pre-axis row', '{}', 10, 0,"
        " '2026-01-01T00:00:00Z')")
    conn.execute(
        "INSERT INTO apimarket_delistings (listing_id, dev_account,"
        " delisted_utc) VALUES (1, 'usr:dana',"
        " '2026-01-02T00:00:00Z')")
    conn.commit()
    conn.close()
    led2, metered2, dk2, gate2, am2 = build_stack(legacy_led, cfg,
                                                  lobby_cfg)
    legacy_view = am2.api_view(1)
    legacy_life = am2.api_listing_lifecycle(1)
    conn = sqlite3.connect(legacy_am)
    indexes = conn.execute(
        "PRAGMA index_list(apimarket_delistings)").fetchall()
    legacy_rows = conn.execute(
        "SELECT delist_id, delisted_utc, cycle FROM"
        " apimarket_delistings ORDER BY delist_id").fetchall()
    conn.close()
    legacy_relist = am2.relist_api("usr:dana", 1)
    legacy_after = am2.api_listing_lifecycle(1)
    legacy_redelist = am2.delist_api("usr:dana", 1)
    unique_left = [r for r in indexes if r[2] == 1]
    ok8 = (legacy_view["delisted"] is True
           and legacy_view["delisted_utc"] == "2026-01-02T00:00:00Z"
           and legacy_life["cycle"] == 1
           and legacy_life["live"] is False
           and legacy_life["history"] == [
               {"event": "delist", "cycle": 1,
                "utc": "2026-01-02T00:00:00Z"}]
           and legacy_rows == [(1, "2026-01-02T00:00:00Z", 1)]
           and legacy_relist["cycle"] == 2
           and legacy_after["live"] is True
           and legacy_after["history"] == [
               {"event": "delist", "cycle": 1,
                "utc": "2026-01-02T00:00:00Z"},
               {"event": "relist", "cycle": 2,
                "utc": legacy_relist["relisted_utc"]}]
           and legacy_redelist["delisted"] is True
           and len(delist_rows(am2)) == 2
           and unique_left == []
           and {p: sha_file(p) for p in PRODUCT_FILES} == shas_before)
    record("AC-AMRL8", ok8,
           "legacy_cycle1=%r legacy_stamp_preserved=%r "
           "unique_indexes_left=%d relist_cycle=%r redelist_ok=%r "
           "product_files_unchanged=%r"
           % (legacy_life["cycle"], legacy_view["delisted_utc"]
              == "2026-01-02T00:00:00Z", len(unique_left),
              legacy_relist["cycle"], legacy_redelist["delisted"],
              {p: sha_file(p) for p in PRODUCT_FILES} == shas_before))

    close_stack(am2, dk2, metered2, led2)
    close_stack(am, dk, metered, led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %s %d/%d"
          % ("PASS" if passed == len(RESULTS) else "FAIL",
             passed, len(RESULTS)))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())