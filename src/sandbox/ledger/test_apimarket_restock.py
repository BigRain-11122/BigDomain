"""Acceptance suite for the apimarket supply-replenishment faces
(BigDomain R2095; canon = the explore-queue row seeded and claimed in
R2095, criteria AC-AMRS1..AC-AMRS8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMRS prefix, the
restock_api / api_supply_history names, the
apimarket_supply_revisions table, the E_AM_BAD_UNITS /
E_AM_SUPPLY_UNLIMITED codes, this suite name and the
ledger-apimarket-restock runner label were all git-grep -F
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.restock_api / api_supply_history.
Supply used to be write-once at publish time: a listing that sold out
was dead forever, and the seller had to publish a new listing_key -
losing that listing's purchases, ratings and price history. This
window pins the replenishment leg:

  - one append-only restock row per call, the listing row and its
    base declaration never rewritten, effective supply = base + sum;
  - the pinned gate order (account shape, listing shape/existence,
    ownership, retired state, units shape, unlimited state) with
    fail-closed zero side effects;
  - remaining = effective - (purchases - refunds), sold-out clears
    and re-exhausts, declared supply unaffected by refunds;
  - one scarcity seam behind both the purchase gate and api_supply;
  - the replenishment history face with running totals ordered by
    revision_id (the clock is second-resolution, so the id - not the
    stamp - is the ordering authority);
  - zero drift for listings never restocked, legacy databases without
    the supply column, pure read and cross-restart byte identity;
  - runner wiring plus suite hygiene (ASCII, no network imports,
    world outside the repo).

Usage: python test_apimarket_restock.py
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

DOOR_KEYS = {"revision_id", "listing_id", "dev_account", "listing_key",
             "add_units", "base_supply", "restocked_units",
             "effective_supply", "remaining", "sold_out",
             "restock_count", "restocked_utc", "disclaimer"}
HISTORY_KEYS = {"listing_id", "listing_key", "dev_account",
                "base_supply", "restocked_units", "effective_supply",
                "restock_count", "sold", "remaining", "sold_out",
                "history", "disclaimer"}
EVENT_KEYS = {"revision_id", "add_units", "effective_supply",
              "restocked_utc"}

FROZEN_TABLES = ("apimarket_listings", "apimarket_purchases",
                 "apimarket_ratings", "apimarket_refunds",
                 "apimarket_price_revisions",
                 "apimarket_listing_revisions",
                 "apimarket_delistings", "apimarket_relistings",
                 "apimarket_supply_revisions")
POOLS = ("pool:reserve", "pool:share")

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


def frozen_digests(am):
    conn = sqlite3.connect(am.db_path)
    out = {t: table_digest(conn, t) for t in FROZEN_TABLES}
    conn.close()
    return out


def restock_rows(am, listing_id):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT revision_id, listing_id, dev_account, add_units,"
        " restocked_utc FROM apimarket_supply_revisions"
        " WHERE listing_id = ? ORDER BY revision_id",
        (listing_id,)).fetchall()
    conn.close()
    return rows


def listing_columns(am):
    conn = sqlite3.connect(am.db_path)
    cols = [r[1] for r in conn.execute(
        "PRAGMA table_info(apimarket_listings)").fetchall()]
    conn.close()
    return cols


def base_supply(am, listing_id):
    conn = sqlite3.connect(am.db_path)
    row = conn.execute(
        "SELECT supply FROM apimarket_listings WHERE listing_id = ?",
        (listing_id,)).fetchone()
    conn.close()
    return row[0] if row is not None else None


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
        out["supply-%d" % lid] = dumps(am.api_supply(lid))
        out["supplyhist-%d" % lid] = dumps(
            am.api_supply_history(lid))
        out["view-%d" % lid] = dumps(am.api_view(lid))
        out["life-%d" % lid] = dumps(am.api_listing_lifecycle(lid))
    out["market"] = dumps(am.api_market_stats())
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


def expect(am, dev_account, listing_id, add_units):
    try:
        am.restock_api(dev_account, listing_id, add_units)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def expect_purchase(am, buyer_id, listing_id, ref):
    try:
        am.purchase_api(buyer_id, listing_id, ref)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def expect_history(am, listing_id):
    try:
        am.api_supply_history(listing_id)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am):
    """Owner dana with four listings: d1 a finite shelf of one unit
    (the restock story), d2 an unlimited service (the refusal gate),
    d3 a finite shelf that gets retired (the retired gate) and d4 a
    quiet finite shelf reserved for the same-second ordering probe."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMRS-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMRS-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "evan"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, supply=1)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    d3 = am.publish_api("usr:dana", "retired-one", "Retired One",
                        "a shelf that gets retired", PAYLOAD, 5,
                        False, supply=1)["listing_id"]
    d4 = am.publish_api("usr:dana", "quiet-shelf", "Quiet Shelf",
                        "the same-second ordering shelf", PAYLOAD, 4,
                        False, supply=2)["listing_id"]
    am.delist_api("usr:dana", d3)
    return d1, d2, d3, d4


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-restock-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d3, d4 = seed_world(led, dk, am)

    cols = listing_columns(am)
    d2_supply_pre = dumps(am.api_supply(d2))
    d2_hist_pre = dumps(am.api_supply_history(d2))

    # -- AC-AMRS1 contract + immutable base ------------------------------
    fresh1 = am.api_supply(d1)
    bob_buy = am.purchase_api("usr:bob", d1, "ref-bob-d1")
    exhausted = am.api_supply(d1)
    view_d1_pre = dumps(am.api_view(d1))
    door = am.restock_api("usr:dana", d1, 2)
    view_d1_post = dumps(am.api_view(d1))
    rows1 = restock_rows(am, d1)
    after1 = am.api_supply(d1)
    ok1 = ("supply" in cols
           and fresh1["supply"] == 1
           and fresh1["base_supply"] == 1
           and fresh1["remaining"] == 1
           and fresh1["sold_out"] is False
           and bob_buy["price_paid"] == 10
           and exhausted["sold"] == 1
           and exhausted["remaining"] == 0
           and exhausted["sold_out"] is True
           and set(door.keys()) == DOOR_KEYS
           and door["listing_id"] == d1
           and door["dev_account"] == "usr:dana"
           and door["add_units"] == 2
           and door["base_supply"] == 1
           and door["restocked_units"] == 2
           and door["effective_supply"] == 3
           and door["remaining"] == 2
           and door["sold_out"] is False
           and door["restock_count"] == 1
           and door["disclaimer"] == DISCLAIMER
           and len(rows1) == 1
           and rows1[0][0] == door["revision_id"]
           and rows1[0][1] == d1
           and rows1[0][2] == "usr:dana"
           and rows1[0][3] == 2
           and rows1[0][4] == door["restocked_utc"]
           and base_supply(am, d1) == 1
           and after1["supply"] == 3
           and after1["base_supply"] == 1
           and after1["restocked_units"] == 2
           and after1["restock_count"] == 1
           and view_d1_post == view_d1_pre
           and dumps(am.api_supply(d2)) == d2_supply_pre
           and dumps(am.api_supply_history(d2)) == d2_hist_pre)
    record("AC-AMRS1", ok1,
           "door keys=%r base/restocked/effective=%r/%r/%r"
           " immutable base=%r view stable=%r"
           " no-restock listing stable=%r"
           % (set(door.keys()) == DOOR_KEYS, door["base_supply"],
              door["restocked_units"], door["effective_supply"],
              base_supply(am, d1) == 1,
              view_d1_post == view_d1_pre,
              dumps(am.api_supply(d2)) == d2_supply_pre))

    # -- AC-AMRS2 pinned gate order + fail-closed ------------------------
    frozen_mid = frozen_digests(am)
    rows_mid = len(restock_rows(am, d1))
    bad_account = [expect(am, bad, d1, 1)
                   for bad in ("", "dana", "usr:", None)]
    unknown_beats_shape = expect(am, "usr:dana", 999999, "bad")
    owner_beats_shape = expect(am, "usr:carol", d1, "bad")
    retired_beats_shape = expect(am, "usr:dana", d3, "bad")
    bad_units = [expect(am, "usr:dana", d1, bad)
                 for bad in (0, -1, "1", True, 1.5, None)]
    unlimited = expect(am, "usr:dana", d2, 5)
    frozen_after_batt = frozen_digests(am)
    rows_after_batt = len(restock_rows(am, d1))
    # The account gate is the truthful prefix-only shape check
    # (the R2077/R2078 finding): "usr:" passes the shape and lands on
    # the ownership gate, so the mixed answer is pinned as measured.
    ok2 = (bad_account == ["E_AM_BAD_ACCOUNT", "E_AM_BAD_ACCOUNT",
                           "E_AM_NOT_OWNER", "E_AM_BAD_ACCOUNT"]
           and unknown_beats_shape == "E_AM_UNKNOWN_LISTING"
           and owner_beats_shape == "E_AM_NOT_OWNER"
           and retired_beats_shape == "E_AM_DELISTED"
           and bad_units == ["E_AM_BAD_UNITS"] * 6
           and unlimited == "E_AM_SUPPLY_UNLIMITED"
           and frozen_after_batt == frozen_mid
           and rows_after_batt == rows_mid)
    record("AC-AMRS2", ok2,
           "account=%r unknown=%s owner=%s retired=%s units=%r"
           " unlimited=%s frozen=%r rows=%d"
           % (bad_account, unknown_beats_shape, owner_beats_shape,
              retired_beats_shape, bad_units, unlimited,
              frozen_after_batt == frozen_mid, rows_after_batt))

    # -- AC-AMRS3 supply arithmetic through trade and refund -------------
    carol_buy = am.purchase_api("usr:carol", d1, "ref-carol-d1")
    dave_buy = am.purchase_api("usr:dave", d1, "ref-dave-d1")
    sold_out_again = am.api_supply(d1)
    evan_code = expect_purchase(am, "usr:evan", d1, "ref-evan-d1")
    evan_balance = led.balance("usr:evan")["balance"]
    door2 = am.restock_api("usr:dana", d1, 1)
    bob_refund = am.refund_api("usr:bob", bob_buy["purchase_id"],
                               "not what I needed")
    final3 = am.api_supply(d1)
    tx_after_trade = ledger_tx_ids(led)
    pools_after_trade = pool_balances(led)
    ok3 = (carol_buy["price_paid"] == 10
           and dave_buy["price_paid"] == 10
           and sold_out_again["sold"] == 3
           and sold_out_again["remaining"] == 0
           and sold_out_again["sold_out"] is True
           and evan_code == "E_AM_SUPPLY_EXHAUSTED"
           and evan_balance == 300
           and door2["base_supply"] == 1
           and door2["restocked_units"] == 3
           and door2["effective_supply"] == 4
           and door2["remaining"] == 1
           and door2["sold_out"] is False
           and door2["restock_count"] == 2
           and bob_refund["amount"] == 10
           and final3["supply"] == 4
           and final3["base_supply"] == 1
           and final3["restocked_units"] == 3
           and final3["sold"] == 2
           and final3["remaining"] == 2
           and final3["sold_out"] is False
           and base_supply(am, d1) == 1)
    record("AC-AMRS3", ok3,
           "sold-out again=%r/%r exhausted=%s evan balance=%r"
           " restock2 eff=%r remaining=%r after-refund sold/rem=%r/%r"
           % (sold_out_again["sold"], sold_out_again["sold_out"],
              evan_code, evan_balance, door2["effective_supply"],
              door2["remaining"], final3["sold"], final3["remaining"]))

    # -- AC-AMRS4 door envelope + history running totals -----------------
    view4_before = dumps(am.api_view(d4))
    stats4_before = dumps(am.api_market_stats())
    hist1 = am.api_supply_history(d1)
    hist4_before = am.api_supply_history(d4)
    e1 = am.restock_api("usr:dana", d4, 1)
    e2 = am.restock_api("usr:dana", d4, 1)
    hist4 = am.api_supply_history(d4)
    view4_after = dumps(am.api_view(d4))
    stats4_after = dumps(am.api_market_stats())
    bad_ids = [expect_history(am, bad)
               for bad in (0, -1, "1", True, None)]
    unknown_hist = expect_history(am, 999999)
    ok4 = (set(hist1.keys()) == HISTORY_KEYS
           and hist1["base_supply"] == 1
           and hist1["restocked_units"] == 3
           and hist1["effective_supply"] == 4
           and hist1["restock_count"] == 2
           and hist1["sold"] == 2
           and hist1["remaining"] == 2
           and [r["add_units"] for r in hist1["history"]] == [2, 1]
           and [r["effective_supply"] for r in hist1["history"]]
           == [3, 4]
           and all(set(r.keys()) == EVENT_KEYS
                   for r in hist1["history"])
           and hist1["history"][0]["revision_id"] == door["revision_id"]
           and hist1["history"][1]["revision_id"] == door2["revision_id"]
           and hist1["history"][1]["revision_id"]
           > hist1["history"][0]["revision_id"]
           and hist1["history"][0]["restocked_utc"]
           == door["restocked_utc"]
           and hist4_before["history"] == []
           and hist4_before["restock_count"] == 0
           and hist4["base_supply"] == 2
           and hist4["restocked_units"] == 2
           and hist4["effective_supply"] == 4
           and hist4["restock_count"] == 2
           and [r["effective_supply"] for r in hist4["history"]]
           == [3, 4]
           and e1["revision_id"] < e2["revision_id"]
           and bad_ids == ["E_AM_BAD_ARGS"] * 5
           and unknown_hist == "E_AM_UNKNOWN_LISTING")
    record("AC-AMRS4", ok4,
           "envelope=%r running=%r same-second ids=%r/%r"
           " empty-history=%r bad-ids=%r"
           % (set(hist1.keys()) == HISTORY_KEYS,
              [r["effective_supply"] for r in hist1["history"]],
              e1["revision_id"], e2["revision_id"],
              hist4_before["history"] == [], bad_ids))

    # -- AC-AMRS5 one scarcity seam --------------------------------------
    supply5 = am.api_supply(d1)
    hist5 = am.api_supply_history(d1)
    d4_supply = am.api_supply(d4)
    d4_hist = am.api_supply_history(d4)
    ok5 = (supply5["supply"] == hist5["effective_supply"]
           and supply5["base_supply"] == hist5["base_supply"]
           and supply5["sold"] == hist5["sold"]
           and supply5["remaining"] == hist5["remaining"]
           and supply5["sold_out"] == hist5["sold_out"]
           and supply5["restock_count"] == hist5["restock_count"]
           and d4_supply["supply"] == d4_hist["effective_supply"] == 4
           and d4_supply["remaining"] == 4
           and view4_after == view4_before
           and stats4_after == stats4_before)
    record("AC-AMRS5", ok5,
           "supply==history=%r base=%r/%r view stable across restock=%r"
           " market stats frozen=%r d4 eff/rem=%r/%r"
           % (supply5["supply"] == hist5["effective_supply"],
              supply5["base_supply"], hist5["base_supply"],
              view4_after == view4_before,
              stats4_after == stats4_before,
              d4_supply["supply"], d4_supply["remaining"]))

    # -- AC-AMRS6 true change, no-op and multi-event law -----------------
    frozen6 = frozen_digests(am)
    tx6 = ledger_tx_ids(led)
    pools6 = pool_balances(led)
    rows6 = [len(restock_rows(am, lid)) for lid in (d1, d2, d3, d4)]
    bad6 = [expect(am, "usr:dana", d4, bad)
            for bad in (0, -2, 2.0, "2", None, True)]
    third = am.restock_api("usr:dana", d4, 1)
    rows6_after = [len(restock_rows(am, lid))
                   for lid in (d1, d2, d3, d4)]
    frozen6b = frozen_digests(am)
    tx6b = ledger_tx_ids(led)
    pools6b = pool_balances(led)
    ok6 = (bad6 == ["E_AM_BAD_UNITS"] * 6
           and rows6_after[3] == rows6[3] + 1
           and rows6_after[:3] == rows6[:3]
           and third["add_units"] == 1
           and third["effective_supply"] == 5
           and third["restock_count"] == 3
           and rows6_after[3] == 3
           and frozen6b["apimarket_listings"]
           == frozen6["apimarket_listings"]
           and frozen6b["apimarket_purchases"]
           == frozen6["apimarket_purchases"]
           and tx6 == tx_after_trade and tx6b == tx_after_trade
           and pools6 == pools_after_trade
           and pools6b == pools_after_trade)
    record("AC-AMRS6", ok6,
           "bad units=%r rows=%r->%r equal-add restocks legal=%r"
           " tx frozen=%r pools frozen=%r"
           % (bad6, rows6, rows6_after,
              third["restock_count"] == 3,
              tx6b == tx_after_trade,
              pools6b == pools_after_trade))

    # -- AC-AMRS7 pure read, restart identity, wiring, hygiene -----------
    ids = (d1, d2, d3, d4)
    fam_before = read_family(am, ids)
    frozen_pre7 = frozen_digests(am)
    fam_again = read_family(am, ids)
    frozen_post7 = frozen_digests(am)
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    fam_two = read_family(am2, ids)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    fam_three = read_family(am3, ids)
    rows_three = len(restock_rows(am3, d1)), len(restock_rows(am3, d4))
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-restock" in handle.read()
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
    ok7 = (fam_before == fam_again
           and frozen_post7 == frozen_pre7
           and fam_before == fam_two == fam_three
           and rows_three == (2, 3)
           and wired and shas_before == shas_after and ascii_ok
           and not net_imports and outside)
    record("AC-AMRS7", ok7,
           "read batch pure=%r restart identity=%r history rows=%r"
           " wired=%r ascii=%r product files=%r"
           % (fam_before == fam_again and frozen_post7 == frozen_pre7,
              fam_before == fam_two == fam_three, rows_three, wired,
              ascii_ok, shas_before == shas_after))

    # -- AC-AMRS8 legacy database without the supply axis ----------------
    legacy_dir = tempfile.mkdtemp(prefix="apimarket-restock-legacy-")
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
    conn.commit()
    conn.close()
    led4, metered4, dk4, gate4, am4 = build_stack(
        legacy_led, cfg, lobby_cfg)
    legacy_supply = am4.api_supply(1)
    legacy_hist = am4.api_supply_history(1)
    legacy_refusal = expect(am4, "usr:dana", 1, 1)
    conn = sqlite3.connect(legacy_am)
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()]
    legacy_rows = conn.execute(
        "SELECT COUNT(*) FROM apimarket_supply_revisions").fetchone()[0]
    legacy_cols = [r[1] for r in conn.execute(
        "PRAGMA table_info(apimarket_listings)").fetchall()]
    conn.close()
    ok8 = ("supply" in legacy_cols
           and "apimarket_supply_revisions" in tables
           and legacy_supply["supply"] is None
           and legacy_supply["base_supply"] is None
           and legacy_supply["restocked_units"] == 0
           and legacy_supply["restock_count"] == 0
           and legacy_supply["remaining"] is None
           and legacy_supply["sold_out"] is False
           and legacy_hist["history"] == []
           and legacy_hist["effective_supply"] is None
           and legacy_refusal == "E_AM_SUPPLY_UNLIMITED"
           and legacy_rows == 0
           and {p: sha_file(p) for p in PRODUCT_FILES} == shas_before)
    record("AC-AMRS8", ok8,
           "legacy cols=%r table=%r supply/base/rem=%r/%r/%r"
           " history=%r refusal=%s rows=%d product files=%r"
           % ("supply" in legacy_cols,
              "apimarket_supply_revisions" in tables,
              legacy_supply["supply"], legacy_supply["base_supply"],
              legacy_supply["remaining"], legacy_hist["history"],
              legacy_refusal, legacy_rows,
              {p: sha_file(p) for p in PRODUCT_FILES} == shas_before))

    close_stack(am4, dk4, metered4, led4)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())