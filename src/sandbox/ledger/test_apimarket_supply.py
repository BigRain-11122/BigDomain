"""Acceptance suite for the apimarket supply / scarcity axis
(BigDomain R2087; canon = the explore-queue row seeded and claimed
in R2087, criteria AC-AMSP1..AC-AMSP8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMSP prefix, the
api_supply name, this suite name, the ledger-apimarket-supply
runner label, the E_AM_SUPPLY_EXHAUSTED code and the supply column
were all git grep -F zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: publish_api's optional supply argument, the
purchase_api exhaustion gate and the api_supply read face. Every
listing the marketplace could publish was infinitely purchasable:
publish_api wrote one row, purchase_api only enforced the
(buyer, listing) uniqueness, and no surface answered "how many
units are left". That is the first commercial fact of any market
(no scarcity, no pricing). This window pins the axis:

  - a nine-key api_supply envelope whose sold count is derived
    from the immutable purchase rows and whose remaining /
    sold_out are derived, never stored twice;
  - backward compatibility: a listing published without a supply
    keeps supply None / remaining None / sold_out False and stays
    infinitely purchasable, and the three read faces that this
    round did NOT touch keep their exact key sets;
  - scarcity arithmetic and conservation: supply 2 sells exactly
    two units, the third buyer answers E_AM_SUPPLY_EXHAUSTED with
    zero token movement and an unchanged purchase table;
  - the pinned gate order (account, listing, retired, self-buy,
    duplicate, exhausted) proven by ordered probes;
  - the supply shape gate at publish time refuses every bad form
    BEFORE the content gate, so a malformed scarcity declaration
    burns zero msgSecCheck calls and stores zero rows;
  - pure read: api_supply never moves a token and repeats byte
    identically, with frozen table digests;
  - the idempotent pre-supply migration: an old apimarket.db
    without the column is opened, the column is added once, and
    the legacy row stays unlimited across two restarts;
  - runner wiring plus suite hygiene (ASCII, no network imports,
    world outside the repo).

Usage: python test_apimarket_supply.py
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
BAD_SUPPLIES = [0, -1, True, "2", 1.5, [], {}]

# R2095 contract absorption: the replenishment axis added three
# additive keys (base_supply / restocked_units / restock_count) to
# the same envelope. The pre-existing criteria are unchanged - a
# listing with no restock rows still reports base_supply equal to
# the declared supply and restocked_units/restock_count zero.
SUPPLY_KEYS = {"listing_id", "listing_key", "dev_account", "supply",
               "sold", "remaining", "sold_out", "listed_utc",
               "base_supply", "restocked_units", "restock_count",
               "disclaimer"}

VIEW_KEYS = {"listing_id", "dev_account", "listing_key", "title",
             "description", "token_price", "base_token_price",
             "base_title", "base_description",
             "metadata_revision_count",
             "latest_metadata_revision_utc", "revision_count",
             "latest_revision_utc", "ai_label", "listed_utc",
             "purchase_count", "rating_count", "rating_avg",
             "refund_count", "refunded_total", "net_purchase_count",
             "delisted", "delisted_utc", "disclaimer"}

BOARD_KEYS = {"disclaimer", "listings"}

LIBRARY_KEYS = {"buyer_id", "purchase_count", "total_spent",
                "refund_count", "total_refunded", "net_spent",
                "disclaimer", "purchases"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings")

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
    UNIQUE (buyer_id, listing_id),
    CHECK (dev_share + platform_share = price_paid)
);
"""


class CountingGate(object):
    """Counting proxy around the real lobby content gate
    (AC-AMSP5): the publish-time supply shape gate must refuse
    before this proxy is ever reached, so a bad supply burns zero
    msgSecCheck calls while a good one costs exactly two."""

    def __init__(self, inner):
        self.inner = inner
        self.calls = []

    def check_text(self, text):
        self.calls.append(text)
        return self.inner.check_text(text)


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


def column_names(am):
    conn = sqlite3.connect(am.db_path)
    cols = [r[1] for r in conn.execute(
        "PRAGMA table_info(apimarket_listings)").fetchall()]
    conn.close()
    return cols


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


def fund(led, who, amount):
    led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", amount),
                ("usr:" + who, "credit", amount)],
               "manual:fund-" + who, "suite funding " + who)


def seed_world(led, dk, am):
    """Owner dana with two listings: d1 carries supply 2, d2 is
    unlimited (no supply argument) - the backward-compatibility
    anchor. bob and carol exhaust d1; erin and frank leave d2
    unlimited with two purchases."""
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AMSP-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AMSP-S",
                     "settlement")
    for who in ("bob", "carol", "erin", "frank", "gina"):
        fund(led, who, 300)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, supply=2)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True
                        )["listing_id"]
    am.purchase_api("usr:bob", d1, "ref-bob-d1")
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    am.purchase_api("usr:erin", d2, "ref-erin-d2")
    am.purchase_api("usr:frank", d2, "ref-frank-d2")
    return d1, d2


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-supply-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2 = seed_world(led, dk, am)

    tx_before = ledger_tx_ids(led)

    # -- AC-AMSP1 read-face contract -------------------------------------
    s1 = am.api_supply(d1)
    s2 = am.api_supply(d2)
    ok1 = (set(s1.keys()) == SUPPLY_KEYS
           and set(s2.keys()) == SUPPLY_KEYS
           and s1["listing_id"] == d1
           and s1["listing_key"] == "risk-scan"
           and s1["dev_account"] == "usr:dana"
           and s1["supply"] == 2
           and s1["sold"] == 2
           and s1["remaining"] == 0
           and s1["sold_out"] is True
           and s2["supply"] is None
           and s2["sold"] == 2
           and s2["remaining"] is None
           and s2["sold_out"] is False
           and s1["disclaimer"] == DISCLAIMER
           and bool(s1["listed_utc"]) and bool(s2["listed_utc"]))
    record("AC-AMSP1", ok1,
           "keys=%r d1 supply/sold/remaining/sold_out=%r d2=%r"
           % (set(s1.keys()) == SUPPLY_KEYS,
              (s1["supply"], s1["sold"], s1["remaining"],
               s1["sold_out"]),
              (s2["supply"], s2["sold"], s2["remaining"],
               s2["sold_out"])))

    # -- AC-AMSP2 backward compatibility + untouched faces ---------------
    gina_before = balance_of(led, "usr:gina")
    am.purchase_api("usr:gina", d2, "ref-gina-d2")
    unlimited_third = am.api_supply(d2)
    ok2 = (set(am.api_view(d2).keys()) == VIEW_KEYS
           and set(am.api_board().keys()) == BOARD_KEYS
           and set(am.api_library("usr:bob").keys()) == LIBRARY_KEYS
           and unlimited_third["supply"] is None
           and unlimited_third["sold"] == 3
           and unlimited_third["remaining"] is None
           and unlimited_third["sold_out"] is False
           and gina_before - balance_of(led, "usr:gina") == 3)
    record("AC-AMSP2", ok2,
           "view keys=%r board keys=%r library keys=%r unlimited"
           " after third sale sold=%r remaining=%r"
           % (set(am.api_view(d2).keys()) == VIEW_KEYS,
              set(am.api_board().keys()) == BOARD_KEYS,
              set(am.api_library("usr:bob").keys()) == LIBRARY_KEYS,
              unlimited_third["sold"], unlimited_third["remaining"]))

    # -- AC-AMSP3 scarcity arithmetic and conservation -------------------
    dig_before = market_digests(am)
    tx_before_refusal = ledger_tx_ids(led)
    erin_bal_before = balance_of(led, "usr:erin")
    balance_before = balance_of(led, "usr:erin")
    try:
        am.purchase_api("usr:erin", d1, "ref-erin-d1")
        sold_out_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        sold_out_code = code_of(exc)
    dig_after = market_digests(am)
    ok3 = (sold_out_code == "E_AM_SUPPLY_EXHAUSTED"
           and dig_after == dig_before
           and ledger_tx_ids(led) == tx_before_refusal
           and balance_of(led, "usr:erin") == erin_bal_before
           and am.api_supply(d1)["sold"] == 2
           and am.api_supply(d1)["remaining"] == 0)
    record("AC-AMSP3", ok3,
           "refused=%s digests frozen=%r token set constant=%r"
           " balance frozen=%r sold still 2=%r"
           % (sold_out_code, dig_after == dig_before,
              ledger_tx_ids(led) == tx_before_refusal,
              balance_of(led, "usr:erin") == balance_before,
              am.api_supply(d1)["sold"] == 2))

    # -- AC-AMSP4 gate order ---------------------------------------------
    dig_gate = market_digests(am)
    bad_codes = []
    for form in BAD_ACCOUNTS:
        try:
            am.purchase_api(form, 999999, "ref-bad")
            bad_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            bad_codes.append(code_of(exc))
    try:
        am.purchase_api("usr:erin", 999999, "ref-unknown")
        unknown_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        unknown_code = code_of(exc)
    try:
        am.purchase_api("usr:dana", d1, "ref-owner")
        self_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        self_code = code_of(exc)
    try:
        am.purchase_api("usr:bob", d1, "ref-bob-again")
        dup_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        dup_code = code_of(exc)
    am.delist_api("usr:dana", d1)
    try:
        am.purchase_api("usr:erin", d1, "ref-erin-d1-retired")
        retired_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        retired_code = code_of(exc)
    dig_gate_after = market_digests(am)
    ok4 = (bad_codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and unknown_code == "E_AM_UNKNOWN_LISTING"
           and self_code == "E_AM_SELF_BUY"
           and dup_code == "E_AM_PURCHASE_DUP"
           and retired_code == "E_AM_DELISTED"
           and dig_gate_after["apimarket_purchases"]
           == dig_gate["apimarket_purchases"])
    record("AC-AMSP4", ok4,
           "bad accounts=%r unknown=%s self=%s dup=%s retired=%s"
           " purchases frozen=%r"
           % (bad_codes, unknown_code, self_code, dup_code,
              retired_code,
              dig_gate_after["apimarket_purchases"]
              == dig_gate["apimarket_purchases"]))

    # -- AC-AMSP5 publish-time supply shape gate, zero gate calls --------
    tmp2 = tempfile.mkdtemp(prefix="apimarket-supply-gate-")
    counter = CountingGate(SecGate.from_config(lobby_cfg))
    led_g, metered_g, dk_g, gate_g, am_g = build_stack(
        os.path.join(tmp2, "ledger.db"), cfg, lobby_cfg, gate=counter)
    dk_g.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    bad_supply_codes = []
    for form in BAD_SUPPLIES:
        try:
            am_g.publish_api("usr:dana", "svc-bad", "T", "D",
                             PAYLOAD, 5, False, supply=form)
            bad_supply_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            bad_supply_codes.append(code_of(exc))
    calls_after_bad = len(counter.calls)
    rows_after_bad = am_g.api_board()["listings"]
    good = am_g.publish_api("usr:dana", "svc-one", "T", "D",
                            PAYLOAD, 5, False, supply=1)
    calls_after_good = len(counter.calls) - calls_after_bad
    close_stack(am_g, dk_g, metered_g, led_g)
    ok5 = (bad_supply_codes == ["E_AM_BAD_ARGS"] * len(BAD_SUPPLIES)
           and calls_after_bad == 0
           and rows_after_bad == []
           and good["supply"] == 1
           and calls_after_good == 2)
    record("AC-AMSP5", ok5,
           "bad supplies=%r gate calls on bad=%d rows on bad=%d"
           " good supply=%r gate calls on good=%d"
           % (bad_supply_codes, calls_after_bad, len(rows_after_bad),
              good["supply"], calls_after_good))

    # -- AC-AMSP6 pure read, zero token ---------------------------------
    dig_read_a = market_digests(am)
    read_a = dumps(am.api_supply(d1))
    read_b = dumps(am.api_supply(d1))
    read_c = dumps(am.api_supply(d2))
    dig_read_b = market_digests(am)
    ok6 = (read_a == read_b
           and dig_read_a == dig_read_b
           and bool(read_c)
           and ledger_tx_ids(led) == tx_before_refusal)
    record("AC-AMSP6", ok6,
           "repeat identical=%r digests frozen=%r ledger tx set"
           " constant=%r"
           % (read_a == read_b, dig_read_a == dig_read_b,
              ledger_tx_ids(led) == tx_before_refusal))

    # -- AC-AMSP7 pre-supply migration + cross-restart identity ---------
    mig_dir = tempfile.mkdtemp(prefix="apimarket-supply-mig-")
    mig_db = os.path.join(mig_dir, "ledger.db")
    led_m = L.Ledger(mig_db, cfg)
    led_m.mint_to_pool("pool:reserve", 2000, "SETTLE-AMSP-M",
                       "settlement")
    led_m.mint_to_pool("pool:share", 2000, "SETTLE-AMSP-M2",
                       "settlement")
    fund(led_m, "mig", 100)
    fund(led_m, "mig2", 100)
    led_m.close()
    mig_market = os.path.join(mig_dir, "apimarket.db")
    conn = sqlite3.connect(mig_market)
    conn.executescript(OLD_SCHEMA)
    conn.execute(
        "INSERT INTO apimarket_listings (dev_account, listing_key,"
        " title, description, payload_json, token_price, ai_label,"
        " listed_utc) VALUES (?,?,?,?,?,?,?,?)",
        ("usr:dana", "legacy-svc", "Legacy Service", "pre-supply row",
         json.dumps(PAYLOAD, sort_keys=True), 5, 0,
         "2026-10-24T00:00:00Z"))
    conn.commit()
    conn.close()
    conn = sqlite3.connect(mig_market)
    legacy_id = conn.execute(
        "SELECT listing_id FROM apimarket_listings").fetchone()[0]
    conn.close()
    led_m1, metered_m1, dk_m1, gate_m1, am_m1 = build_stack(
        mig_db, cfg, lobby_cfg)
    cols_one = column_names(am_m1)
    legacy_one = am_m1.api_supply(legacy_id)
    am_m1.purchase_api("usr:mig", legacy_id, "ref-mig-legacy")
    legacy_sold = am_m1.api_supply(legacy_id)
    close_stack(am_m1, dk_m1, metered_m1, led_m1)
    led_m2, metered_m2, dk_m2, gate_m2, am_m2 = build_stack(
        mig_db, cfg, lobby_cfg)
    cols_two = column_names(am_m2)
    legacy_two = am_m2.api_supply(legacy_id)
    am_m2.purchase_api("usr:mig2", legacy_id, "ref-mig2-legacy")
    legacy_unlimited = am_m2.api_supply(legacy_id)
    close_stack(am_m2, dk_m2, metered_m2, led_m2)
    ok7 = (cols_one.count("supply") == 1
           and cols_two.count("supply") == 1
           and cols_one == cols_two
           and legacy_one["supply"] is None
           and legacy_one["sold"] == 0
           and legacy_one["remaining"] is None
           and legacy_one["sold_out"] is False
           and legacy_sold["sold"] == 1
           and legacy_sold["remaining"] is None
           and dumps(legacy_sold) == dumps(legacy_two)
           and legacy_unlimited["sold"] == 2
           and legacy_unlimited["sold_out"] is False)
    record("AC-AMSP7", ok7,
           "supply column count=%r/%r stable=%r legacy before=%r"
           " after one sale=%r after two=%r"
           % (cols_one.count("supply"), cols_two.count("supply"),
              cols_one == cols_two,
              (legacy_one["supply"], legacy_one["sold"],
               legacy_one["remaining"], legacy_one["sold_out"]),
              (legacy_sold["sold"], legacy_sold["remaining"]),
              (legacy_unlimited["sold"],
               legacy_unlimited["sold_out"])))

    # -- cross-restart identity of the main world -----------------------
    supply_before = {"d1": dumps(am.api_supply(d1)),
                     "d2": dumps(am.api_supply(d2))}
    dig_before_restart = market_digests(am)
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    supply_two = {"d1": dumps(am2.api_supply(d1)),
                  "d2": dumps(am2.api_supply(d2))}
    dig_two = market_digests(am2)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    supply_three = {"d1": dumps(am3.api_supply(d1)),
                    "d2": dumps(am3.api_supply(d2))}
    dig_three = market_digests(am3)
    close_stack(am3, dk3, metered3, led3)
    restart_ok = (supply_before == supply_two == supply_three
                  and dig_before_restart == dig_two == dig_three)

    # -- AC-AMSP8 wiring + hygiene ---------------------------------------
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-supply" in handle.read()
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
           and not net_imports and outside and restart_ok)
    record("AC-AMSP8", ok8,
           "runner wiring=%r consumer shas stable=%r ascii=%r"
           " network imports=%d world outside repo=%r"
           " restart identity=%r"
           % (wired, shas_before == shas_after, ascii_ok,
              len(net_imports), outside, restart_ok))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())