"""Acceptance suite for the apimarket refund / return axis
(BigDomain R2088; canon = the explore-queue row seeded and claimed
in R2088, criteria AC-AMRF1..AC-AMRF8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMRF prefix,
refund_api, api_refund, the apimarket_refunds table, the four new
error codes, this file name and the ledger-apimarket-refund runner
label were all git grep -F zero-occupancy anchored 2026-10-24,
rc=1).

Face under proof: the buyer-side refund door. Every forward door
on this market was irreversible - purchase_api spent tokens and
wrote one immutable purchase row, and no surface anywhere could
reverse it: a buyer who received nothing usable had no remedy and
a seller had no return leg. This window pins the post-sale remedy:

  - a four-entry ledger reversal that puts buyer, seller and both
    pools back to their pre-purchase balances exactly (integer
    split law, zero rounding);
  - one append-only refund row per purchase (UNIQUE purchase_id),
    the ledger ref derived from the purchase id (never caller
    injected) so the UNIQUE(ref) rule is a second idempotency key;
  - the pinned gate order (account shape, purchase-id shape,
    purchase existence, ownership, already-refunded, funding);
  - the constitutional AC-L2 balance floor: a seller who already
    spent the proceeds cannot fund the reversal, so the refund
    fails closed with zero token movement (refuse, never chase);
  - a refunded unit returns to the shelf (sold = purchases minus
    refunds) and another buyer can take it, while the original
    buyer stays subject to the purchase uniqueness law;
  - additive refund columns on api_view / api_library / api_sales
    plus the api_refund provenance read face; ratings are never
    deleted by a refund (append-only history);
  - pure reads, cross-restart byte identity, an idempotent forward
    migration and runner wiring.

Usage: python test_apimarket_refund.py
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

BAD_ACCOUNTS = ["", None, "bob", 7, 1.5, True, {}, []]
BAD_PURCHASE_IDS = [0, -1, True, "1", None, 1.5, {}, []]

REFUND_KEYS = {"refund_id", "purchase_id", "listing_id", "buyer_id",
               "dev_account", "amount", "dev_share",
               "platform_share", "refund_tx", "refunded_utc",
               "reason", "disclaimer"}

LIBRARY_KEYS = {"buyer_id", "purchase_count", "total_spent",
                "refund_count", "total_refunded", "net_spent",
                "disclaimer", "purchases"}

LIBRARY_ROW_KEYS = {"purchase_id", "listing_id", "listing_key",
                    "title", "dev_account", "price_paid",
                    "dev_share", "platform_share", "spend_tx",
                    "purchased_utc", "current_price", "delisted",
                    "delisted_utc", "my_rating", "refunded",
                    "refunded_utc", "refund_tx"}

SALES_KEYS = {"dev_account", "disclaimer", "refunded_count",
              "refunded_total", "sales"}

SALES_ROW_KEYS = {"purchase_id", "listing_id", "listing_key",
                  "buyer_id", "price_paid", "dev_share",
                  "platform_share", "spend_tx", "dev_share_tx",
                  "purchased_utc", "refunded", "refunded_utc",
                  "refund_tx"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_refunds")

OLD_SCHEMA = """
CREATE TABLE apimarket_listings (
    listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dev_account TEXT NOT NULL,
    listing_key TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    token_price INTEGER NOT NULL CHECK (token_price > 0),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0, 1)),
    listed_utc TEXT NOT NULL,
    supply INTEGER,
    UNIQUE (dev_account, listing_key)
);
CREATE TABLE apimarket_purchases (
    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    price_paid INTEGER NOT NULL CHECK (price_paid > 0),
    dev_share INTEGER NOT NULL CHECK (dev_share >= 0),
    platform_share INTEGER NOT NULL CHECK (platform_share >= 0),
    spend_tx TEXT NOT NULL,
    dev_share_tx TEXT NOT NULL,
    purchased_utc TEXT NOT NULL,
    UNIQUE (buyer_id, listing_id)
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


def ledger_tx_ids(led):
    conn = sqlite3.connect(led.db_path)
    ids = set(str(r[0]) for r in conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall())
    conn.close()
    return ids


def balance_of(led, account):
    out = led.balance(account)
    if isinstance(out, dict):
        return int(out.get("balance", 0))
    return int(out)


def build_stack(db_path, cfg, lobby_cfg, gate=None):
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    if gate is None:
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


def fund(led, who, amount, tag):
    led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", amount),
                ("usr:" + who, "credit", amount)],
               "manual:fund-" + who + "-" + tag,
               "suite funding " + who + " " + tag)


def seed_world(led, dk, am):
    """dana sells d1 (price 10, supply 2) and d2 (price 3,
    unlimited); bob and carol exhaust d1, erin buys d2, bob rates
    d1 five stars. hana sells d4 (price 20) for the funding leg."""
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AMRF-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AMRF-S",
                     "settlement")
    for who in ("bob", "carol", "erin", "frank", "gina"):
        fund(led, who, 300, "seed")
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:hana", "hana-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, supply=2)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True
                        )["listing_id"]
    d4 = am.publish_api("usr:hana", "deep-scan", "Deep Scan API",
                        "deep portfolio scan endpoint", PAYLOAD, 20,
                        False)["listing_id"]
    bob = am.purchase_api("usr:bob", d1, "ref-bob-d1")
    carol = am.purchase_api("usr:carol", d1, "ref-carol-d1")
    erin = am.purchase_api("usr:erin", d2, "ref-erin-d2")
    am.rate_api("usr:bob", d1, 5)
    return d1, d2, d4, bob["purchase_id"], carol["purchase_id"], \
        erin["purchase_id"]


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-refund-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d4, bob_pid, carol_pid, erin_pid = seed_world(led, dk, am)

    # -- AC-AMRF1 full reversal arithmetic -------------------------------
    accounts = ("usr:frank", "usr:dana", "pool:reserve", "pool:share")
    before = {a: balance_of(led, a) for a in accounts}
    bought = am.purchase_api("usr:frank", d2, "ref-frank-d2")
    erin_pid2 = bought["purchase_id"]
    moved = {a: balance_of(led, a) for a in accounts}
    env = am.refund_api("usr:frank", erin_pid2, "service unusable")
    after = {a: balance_of(led, a) for a in accounts}
    ok1 = (set(env.keys()) == REFUND_KEYS
           and env["purchase_id"] == erin_pid2
           and env["listing_id"] == d2
           and env["buyer_id"] == "usr:frank"
           and env["dev_account"] == "usr:dana"
           and env["amount"] == bought["price_paid"]
           and env["amount"] == env["dev_share"] + env["platform_share"]
           and env["dev_share"] == bought["dev_share"]
           and env["platform_share"] == bought["platform_share"]
           and bool(env["refund_tx"]) and bool(env["refunded_utc"])
           and env["reason"] == "service unusable"
           and env["disclaimer"] == DISCLAIMER
           and moved != before
           and after == before)
    record("AC-AMRF1", ok1,
           "keys=%r amount/dev/platform=%r balances moved=%r"
           " restored exactly=%r"
           % (set(env.keys()) == REFUND_KEYS,
              (env["amount"], env["dev_share"],
               env["platform_share"]), moved != before,
              after == before))

    # -- AC-AMRF2 ownership / existence / shape gates ---------------------
    dig2 = market_digests(am)
    tx2 = ledger_tx_ids(led)
    bad_codes = []
    for form in BAD_ACCOUNTS:
        try:
            am.refund_api(form, carol_pid)
            bad_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            bad_codes.append(code_of(exc))
    id_codes = []
    for form in BAD_PURCHASE_IDS:
        try:
            am.refund_api("usr:carol", form)
            id_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            id_codes.append(code_of(exc))
    try:
        am.refund_api("usr:frank", 999999)
        unknown_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        unknown_code = code_of(exc)
    try:
        am.refund_api("usr:frank", carol_pid)
        owner_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        owner_code = code_of(exc)
    ok2 = (bad_codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and id_codes == ["E_AM_BAD_ARGS"] * len(BAD_PURCHASE_IDS)
           and unknown_code == "E_AM_UNKNOWN_PURCHASE"
           and owner_code == "E_AM_NOT_BUYER"
           and market_digests(am) == dig2
           and ledger_tx_ids(led) == tx2)
    record("AC-AMRF2", ok2,
           "bad accounts=%r bad ids=%r unknown=%s non-buyer=%s"
           " digests frozen=%r tx set frozen=%r"
           % (sorted(set(bad_codes)), sorted(set(id_codes)),
              unknown_code, owner_code,
              market_digests(am) == dig2,
              ledger_tx_ids(led) == tx2))

    # -- AC-AMRF3 pinned gate order --------------------------------------
    order = []

    def probe(who, pid):
        try:
            am.refund_api(who, pid)
            return "NO-RAISE"
        except A.ApiMarketError as exc:
            return code_of(exc)

    order.append(probe("bob", 0))            # account before id shape
    order.append(probe("usr:bob", 0))        # id shape before existence
    order.append(probe("usr:bob", 999999))   # existence before owner
    order.append(probe("usr:frank", carol_pid))   # ownership reached
    ok3 = (order[0] == "E_AM_BAD_ACCOUNT"
           and order[1] == "E_AM_BAD_ARGS"
           and order[2] == "E_AM_UNKNOWN_PURCHASE"
           and order[3] == "E_AM_NOT_BUYER")
    record("AC-AMRF3", ok3, "probes=%r" % (order,))

    # -- AC-AMRF4 repeat refund immunity ---------------------------------
    first = am.refund_api("usr:bob", bob_pid, "")
    stamp, tx_id = first["refunded_utc"], first["refund_tx"]
    dig4 = market_digests(am)
    tx4 = ledger_tx_ids(led)
    try:
        am.refund_api("usr:bob", bob_pid, "second attempt")
        repeat_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        repeat_code = code_of(exc)
    conn = sqlite3.connect(am.db_path)
    refund_rows = conn.execute(
        "SELECT COUNT(*), MIN(refunded_utc), MIN(refund_tx)"
        " FROM apimarket_refunds WHERE purchase_id = ?",
        (bob_pid,)).fetchone()
    conn.close()
    ok4 = (repeat_code == "E_AM_ALREADY_REFUNDED"
           and int(refund_rows[0]) == 1
           and refund_rows[1] == stamp and refund_rows[2] == tx_id
           and market_digests(am) == dig4
           and ledger_tx_ids(led) == tx4)
    record("AC-AMRF4", ok4,
           "repeat=%s rows=%r stamp/tx unchanged=%r digests frozen=%r"
           % (repeat_code, int(refund_rows[0]),
              refund_rows[1] == stamp and refund_rows[2] == tx_id,
              market_digests(am) == dig4))

    # -- AC-AMRF5 no-overdraft funding gate ------------------------------
    gina_buy = am.purchase_api("usr:gina", d4, "ref-gina-d4")
    gina_pid = gina_buy["purchase_id"]
    hana_after_sale = balance_of(led, "usr:hana")
    led.spend("usr:hana", hana_after_sale, "ref-hana-burn")
    hana_drained = balance_of(led, "usr:hana")
    dig5 = market_digests(am)
    tx5 = ledger_tx_ids(led)
    gina_before = balance_of(led, "usr:gina")
    try:
        am.refund_api("usr:gina", gina_pid, "too late")
        unfunded_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        unfunded_code = code_of(exc)
    refused_frozen = (market_digests(am) == dig5
                      and ledger_tx_ids(led) == tx5
                      and balance_of(led, "usr:gina") == gina_before)
    fund(led, "hana", 20, "topup")
    funded = am.refund_api("usr:gina", gina_pid, "funded now")
    ok5 = (hana_after_sale == gina_buy["dev_share"]
           and hana_drained == 0
           and unfunded_code == "E_AM_REFUND_UNFUNDABLE"
           and refused_frozen
           and funded["purchase_id"] == gina_pid
           and balance_of(led, "usr:gina") == (
               gina_before + gina_buy["price_paid"])
           and balance_of(led, "usr:hana") == 20 - gina_buy["dev_share"])
    record("AC-AMRF5", ok5,
           "dev balance %r -> %r refused=%s frozen=%r funded refund=%r"
           " buyer restored=%r seller nets %r"
           % (hana_after_sale, hana_drained, unfunded_code,
              refused_frozen, funded["purchase_id"] == gina_pid,
              balance_of(led, "usr:gina") == (
                  gina_before + gina_buy["price_paid"]),
              balance_of(led, "usr:hana")))

    # -- AC-AMRF6 refunded unit returns to the shelf ---------------------
    shelf_after_refund = am.api_supply(d1)
    frank_buy = am.purchase_api("usr:frank", d1, "ref-frank-d1")
    shelf_resold = am.api_supply(d1)
    try:
        am.purchase_api("usr:bob", d1, "ref-bob-d1-again")
        re_buy_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        re_buy_code = code_of(exc)
    ok6 = (shelf_after_refund["supply"] == 2
           and shelf_after_refund["sold"] == 1
           and shelf_after_refund["remaining"] == 1
           and shelf_after_refund["sold_out"] is False
           and frank_buy["purchase_id"] > 0
           and shelf_resold["sold"] == 2
           and shelf_resold["remaining"] == 0
           and shelf_resold["sold_out"] is True
           and re_buy_code == "E_AM_PURCHASE_DUP")
    record("AC-AMRF6", ok6,
           "shelf after refund=%r after resale=%r re-buy=%s"
           % ((shelf_after_refund["sold"],
               shelf_after_refund["remaining"],
               shelf_after_refund["sold_out"]),
              (shelf_resold["sold"], shelf_resold["remaining"],
               shelf_resold["sold_out"]), re_buy_code))

    # -- AC-AMRF7 read-face refund columns -------------------------------
    view = am.api_view(d1)
    lib = am.api_library("usr:bob")
    lib_row = lib["purchases"][0]
    sales = am.api_sales("usr:dana")
    sales_rows = {r["purchase_id"]: r for r in sales["sales"]}
    ratings = am.api_ratings(d1)
    bob_rating = [r for r in ratings["ratings"]
                  if r["buyer_id"] == "usr:bob"]
    refund_env = am.api_refund(bob_pid)

    def api_code(fn):
        try:
            fn()
            return "NO-RAISE"
        except A.ApiMarketError as exc:
            return code_of(exc)

    not_refunded = api_code(lambda: am.api_refund(carol_pid))
    unknown_refund = api_code(lambda: am.api_refund(999999))
    bad_refund_ids = []
    for form in BAD_PURCHASE_IDS:
        bad_refund_ids.append(api_code(lambda f=form: am.api_refund(f)))
    ok7 = (view["purchase_count"] == 3
           and view["refund_count"] == 1
           and view["refunded_total"] == 10
           and view["net_purchase_count"] == 2
           and set(lib.keys()) == LIBRARY_KEYS
           and set(lib_row.keys()) == LIBRARY_ROW_KEYS
           and lib["purchase_count"] == 1
           and lib["total_spent"] == 10
           and lib["refund_count"] == 1
           and lib["total_refunded"] == 10
           and lib["net_spent"] == 0
           and lib_row["refunded"] is True
           and lib_row["refunded_utc"] == stamp
           and lib_row["refund_tx"] == tx_id
           and set(sales.keys()) == SALES_KEYS
           and set(sales_rows[bob_pid].keys()) == SALES_ROW_KEYS
           and sales["refunded_count"] == 2
           and sales["refunded_total"] == 13
           and sales_rows[bob_pid]["refunded"] is True
           and sales_rows[carol_pid]["refunded"] is False
           and sales_rows[carol_pid]["refunded_utc"] is None
           and len(bob_rating) == 1 and bob_rating[0]["stars"] == 5
           and set(refund_env.keys()) == REFUND_KEYS
           and refund_env["refund_id"] == first["refund_id"]
           and not_refunded == "E_AM_NOT_REFUNDED"
           and unknown_refund == "E_AM_UNKNOWN_PURCHASE"
           and bad_refund_ids == ["E_AM_BAD_ARGS"] * len(BAD_PURCHASE_IDS))
    record("AC-AMRF7", ok7,
           "view=%r library=%r sales=(%r,%r) bob rating kept=%r"
           " api_refund not-refunded=%s unknown=%s bad=%r"
           % ((view["refund_count"], view["refunded_total"],
               view["net_purchase_count"]),
              (lib["refund_count"], lib["total_refunded"],
               lib["net_spent"], lib_row["refunded"]),
              sales["refunded_count"], sales["refunded_total"],
              [r["stars"] for r in bob_rating], not_refunded,
              unknown_refund, sorted(set(bad_refund_ids))))

    # -- AC-AMRF8 pure read, restart identity, migration, wiring ---------
    snapshot_a = {
        "view": dumps(am.api_view(d1)),
        "view2": dumps(am.api_view(d2)),
        "lib": dumps(am.api_library("usr:bob")),
        "sales": dumps(am.api_sales("usr:dana")),
        "supply": dumps(am.api_supply(d1)),
        "refund": dumps(am.api_refund(bob_pid)),
    }
    tx8 = ledger_tx_ids(led)
    dig8 = market_digests(am)
    snapshot_a2 = {
        "view": dumps(am.api_view(d1)),
        "view2": dumps(am.api_view(d2)),
        "lib": dumps(am.api_library("usr:bob")),
        "sales": dumps(am.api_sales("usr:dana")),
        "supply": dumps(am.api_supply(d1)),
        "refund": dumps(am.api_refund(bob_pid)),
    }
    pure_read = (snapshot_a == snapshot_a2
                 and ledger_tx_ids(led) == tx8
                 and market_digests(am) == dig8)
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, _g2, am2 = build_stack(db_path, cfg,
                                                lobby_cfg)
    snapshot_b = {
        "view": dumps(am2.api_view(d1)),
        "view2": dumps(am2.api_view(d2)),
        "lib": dumps(am2.api_library("usr:bob")),
        "sales": dumps(am2.api_sales("usr:dana")),
        "supply": dumps(am2.api_supply(d1)),
        "refund": dumps(am2.api_refund(bob_pid)),
    }
    dig_b = market_digests(am2)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, _g3, am3 = build_stack(db_path, cfg,
                                                lobby_cfg)
    snapshot_c = {
        "view": dumps(am3.api_view(d1)),
        "view2": dumps(am3.api_view(d2)),
        "lib": dumps(am3.api_library("usr:bob")),
        "sales": dumps(am3.api_sales("usr:dana")),
        "supply": dumps(am3.api_supply(d1)),
        "refund": dumps(am3.api_refund(bob_pid)),
    }
    dig_c = market_digests(am3)
    close_stack(am3, dk3, metered3, led3)
    restart_ok = (snapshot_a == snapshot_b == snapshot_c
                  and dig8 == dig_b == dig_c)

    # legacy database without the refunds table (pre-R2088 shape)
    legacy_dir = tempfile.mkdtemp(prefix="apimarket-refund-legacy-")
    legacy_ledger = os.path.join(legacy_dir, "ledger.db")
    legacy_path = os.path.join(legacy_dir, "apimarket.db")
    conn = sqlite3.connect(legacy_path)
    conn.executescript(OLD_SCHEMA)
    conn.close()
    led4, metered4, dk4, _g4, am4 = build_stack(
        legacy_ledger, cfg, lobby_cfg)
    conn = sqlite3.connect(am4.db_path)
    has_table = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"
        " AND name = 'apimarket_refunds'").fetchone()[0]
    conn.close()
    migrated_code = "NO-RAISE"
    try:
        am4.refund_api("usr:bob", 1)
    except A.ApiMarketError as exc:
        migrated_code = code_of(exc)
    close_stack(am4, dk4, metered4, led4)

    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-refund" in handle.read()
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
    ok8 = (pure_read and restart_ok and int(has_table) == 1
           and migrated_code == "E_AM_UNKNOWN_PURCHASE"
           and wired and shas_before == shas_after and ascii_ok
           and not net_imports and outside)
    record("AC-AMRF8", ok8,
           "pure read=%r restart identity=%r legacy table=%r"
           " legacy probe=%s wiring=%r consumer shas stable=%r"
           " ascii=%r network imports=%d world outside repo=%r"
           % (pure_read, restart_ok, int(has_table) == 1,
              migrated_code, wired, shas_before == shas_after,
              ascii_ok, len(net_imports), outside))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())