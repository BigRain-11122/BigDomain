"""Acceptance suite for the apimarket category-directory axis
(BigDomain R2132; canon = the explore-queue row seeded and claimed in
R2132, criteria AC-AMCT1..AC-AMCT8 registered in that claim note BEFORE
this code existed - honesty law; the AC-AMCT prefix, category,
api_categories, E_AM_BAD_CATEGORY, this suite name and the
ledger-apimarket-category runner label were all git grep -F
zero-occupancy anchored 2026-10-26, rc=1).

Face under proof: publish_api's optional category declaration, the
api_search category filter, and the new api_categories directory face.
Every market surface answered one listing, one seller, one buyer, the
whole board, a search, a sort or a page - none answered "what is this
market made of". A listing carried only a key, a title and a
description, so discovery rested entirely on guessing keywords and no
operator could report the taxonomy. This window pins the axis:

  - the publish-time category shape gate runs BEFORE the registry read
    and BEFORE the content gate (a bad declaration burns zero
    msgSecCheck calls and stores zero rows), the trimmed string is
    stored, and api_view carries the declaration additively;
  - backward compatibility: a listing published without a category
    stays NULL, listed, searchable and purchasable, and api_search
    without a filter keeps the five-key legacy criteria contract;
  - the filter is exact on the trimmed declaration (documented, no
    case folding) and composes with keyword, seller, price band,
    retirement switch, sort and paging;
  - the directory envelope and six-key rows, its conservation law
    (listing_count == sum of rows + uncategorized) and its ordering;
  - the partition and live-price law across delist / relist / reprice;
  - the pinned gate order and zero side effects of every refusal;
  - pure read: zero row mutations and zero token movement, repeated
    calls byte identical;
  - the idempotent pre-category migration, cross-restart byte
    identity, runner wiring and suite hygiene.

Usage: python test_apimarket_category.py
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
import apimarket_report as RPT        # noqa: E402 (config loader)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apimarket_report.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

DIR_KEYS = {"category_count", "listing_count", "uncategorized_count",
            "disclaimer", "categories"}

CAT_ROW_KEYS = {"category", "listing_count", "live_listing_count",
                "retired_listing_count", "min_live_price",
                "max_live_price"}

SEARCH_ROW_KEYS = {"listing_id", "dev_account", "listing_key", "title",
                   "token_price", "ai_label", "rating_count",
                   "rating_avg", "delisted", "delisted_utc",
                   "category"}

LEGACY_CRITERIA = {"keyword", "dev_account", "min_price", "max_price",
                   "include_delisted"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_relistings")

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


class Clock(object):
    def __init__(self, value="2026-10-09T00:00:00Z"):
        self.value = value

    def now_utc(self):
        return self.value


class CountingGate(object):
    """Counting proxy around the lobby content gate (AC-AMCT1): the
    publish-time category shape gate must refuse before this proxy is
    ever reached, so a bad category burns zero msgSecCheck calls while
    a good one costs exactly two (title + description)."""

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


def frozen_digests(am):
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


def search_code(am, **kwargs):
    try:
        am.api_search(**kwargs)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def ids_of(env):
    return [r["listing_id"] for r in env["listings"]]


def cats_of(env):
    return {r["category"]: r for r in env["categories"]}


def seed_world(led, dk, am, clock):
    """Two developers, five listings across three declared categories
    plus one deliberately uncategorized legacy-style row, three
    purchases and one rating."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMCT-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMCT-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:erin", "erin-key", 10, ["backtest"], False)
    clock.value = "2026-10-09T00:00:01Z"
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    clock.value = "2026-10-09T00:00:02Z"
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True,
                        category=" data ")["listing_id"]
    clock.value = "2026-10-09T00:00:03Z"
    d3 = am.publish_api("usr:dana", "chart-render",
                        "Chart Render API",
                        "server-side chart rendering", PAYLOAD, 5,
                        False, category="render")["listing_id"]
    clock.value = "2026-10-09T00:00:04Z"
    d4 = am.publish_api("usr:dana", "legacy-util",
                        "Legacy Util API",
                        "uncategorized helper endpoint", PAYLOAD, 7,
                        False)["listing_id"]
    clock.value = "2026-10-09T00:00:05Z"
    d5 = am.publish_api("usr:erin", "text-summarise",
                        "Text Summarise API",
                        "short-form summarisation", PAYLOAD, 4, True,
                        category="nlp")["listing_id"]
    clock.value = "2026-10-09T00:00:10Z"
    am.purchase_api("usr:bob", d1, "BUY-AMCT-1")
    clock.value = "2026-10-09T00:00:11Z"
    am.purchase_api("usr:carol", d2, "BUY-AMCT-2")
    clock.value = "2026-10-09T00:00:12Z"
    am.purchase_api("usr:dave", d5, "BUY-AMCT-3")
    clock.value = "2026-10-09T00:00:13Z"
    am.rate_api("usr:bob", d1, 5)
    return {"d1": d1, "d2": d2, "d3": d3, "d4": d4, "d5": d5}


def main():
    tmpdir = tempfile.mkdtemp(prefix="amamct-")
    db_path = os.path.join(tmpdir, "am.db")
    cfg = RPT.load_configs()[0]
    lobby_cfg = RPT.load_configs()[1]
    led = None
    am = None
    clock = Clock()
    real_now = A._now_utc
    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}
    try:
        A._now_utc = clock.now_utc
        led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
        ids = seed_world(led, dk, am, clock)

        # -- AC-AMCT1 declaration, view key, and the pre-gate --------
        view_d1 = am.api_view(ids["d1"])
        view_d2 = am.api_view(ids["d2"])
        view_d4 = am.api_view(ids["d4"])
        listing_cols = [r[1] for r in sqlite3.connect(
            am.db_path).execute(
            "PRAGMA table_info(apimarket_listings)").fetchall()]
        ok1 = ("category" in listing_cols
               and view_d1.get("category") == "data"
               and view_d2.get("category") == "data"
               and view_d4.get("category") is None
               and view_d1["disclaimer"] == DISCLAIMER)
        gate2 = CountingGate(SecGate.from_config(lobby_cfg))
        probe_dir = tempfile.mkdtemp(prefix="amamct-probe-")
        probe_led = None
        probe_am = None
        try:
            probe_led, probe_m, probe_dk, _g, probe_am = build_stack(
                os.path.join(probe_dir, "am.db"), cfg, lobby_cfg,
                gate=gate2)
            probe_dk.issue_key("usr:dana", "dana-key", 10,
                               ["backtest"], False)
            bad_cats = [0, -1, True, 1.5, [], {}]
            codes = []
            for bad in bad_cats:
                try:
                    probe_am.publish_api(
                        "usr:dana", "bad-%r" % (bad,), "T", "D",
                        PAYLOAD, 5, False, category=bad)
                    codes.append("NO-RAISE")
                except A.ApiMarketError as exc:
                    codes.append(code_of(exc))
            blank_codes = []
            for blank in ("", "   "):
                try:
                    probe_am.publish_api(
                        "usr:dana", "blank", "T", "D", PAYLOAD, 5,
                        False, category=blank)
                    blank_codes.append("NO-RAISE")
                except A.ApiMarketError as exc:
                    blank_codes.append(code_of(exc))
            long_code = None
            try:
                probe_am.publish_api("usr:dana", "long", "T", "D",
                                     PAYLOAD, 5, False,
                                     category="x" * 41)
                long_code = "NO-RAISE"
            except A.ApiMarketError as exc:
                long_code = code_of(exc)
            calls_after_bad = len(gate2.calls)
            good = probe_am.publish_api("usr:dana", "good", "T", "D",
                                        PAYLOAD, 5, False,
                                        category=" tools ")
            calls_after_good = len(gate2.calls)
            ok1 = (ok1
                   and codes == ["E_AM_BAD_ARGS"] * 6
                   and blank_codes == ["E_AM_BAD_ARGS"] * 2
                   and long_code == "E_AM_BAD_ARGS"
                   and calls_after_bad == 0
                   and calls_after_good == 2
                   and good["category"] == "tools")
        finally:
            if probe_am is not None:
                probe_am.close()
            if probe_led is not None:
                probe_led.close()
        record("AC-AMCT1", ok1,
               "col=%r d1=%r d2=%r d4=%r bad=%r blank=%r long=%r"
               " gate_calls_bad=%d gate_calls_good=%d trim=%r"
               % ("category" in listing_cols, view_d1.get("category"),
                  view_d2.get("category"), view_d4.get("category"),
                  codes, blank_codes, long_code, calls_after_bad,
                  calls_after_good, good["category"]))

        # -- AC-AMCT2 backward compatibility -------------------------
        legacy = am.api_search()
        ok2 = (set(legacy) == {"disclaimer", "criteria", "count",
                              "listings"}
               and set(legacy["criteria"]) == LEGACY_CRITERIA
               and legacy["count"] == 5
               and all(row["category"] in (None, "data", "render",
                                           "nlp")
                       for row in legacy["listings"]))
        ok2 = ok2 and am.api_view(ids["d4"])["category"] is None
        clock.value = "2026-10-09T00:00:20Z"
        buy_legacy = am.purchase_api("usr:bob", ids["d4"],
                                     "BUY-AMCT-LEGACY")
        ok2 = (ok2 and buy_legacy["price_paid"] == 7
               and ids["d4"] in {r["listing_id"]
                                 for r in am.api_search(
                                     keyword="legacy")["listings"]})
        record("AC-AMCT2", ok2,
               "legacy_keys=%r criteria=%r count=%d uncategorized_buy=%r"
               % (sorted(legacy), sorted(legacy["criteria"]),
                  legacy["count"], buy_legacy["price_paid"]))

        # -- AC-AMCT3 exact-match filter and composition -------------
        data_rows = am.api_search(category="data")
        ok3 = (ids_of(data_rows) == [ids["d2"], ids["d1"]]
               and data_rows["criteria"].get("category") == "data"
               and all(r["category"] == "data"
                       for r in data_rows["listings"]))
        ok3 = ok3 and am.api_search(category=" Data ")["count"] == 0
        ok3 = ok3 and ids_of(am.api_search(category="  data  ")) == \
            [ids["d2"], ids["d1"]]
        ok3 = ok3 and ids_of(am.api_search(category="data",
                                           keyword="macro")) == [ids["d2"]]
        ok3 = ok3 and ids_of(am.api_search(category="nlp")) == [ids["d5"]]
        ok3 = ok3 and ids_of(am.api_search(category="data",
                                           dev_account="usr:dana")) == \
            [ids["d2"], ids["d1"]]
        ok3 = ok3 and ids_of(am.api_search(category="data",
                                           min_price=4)) == [ids["d1"]]
        ok3 = ok3 and ids_of(am.api_search(category="data",
                                           max_price=4)) == [ids["d2"]]
        paged = am.api_search(category="data", limit=1, offset=1)
        ok3 = ok3 and ids_of(paged) == [ids["d1"]] \
            and paged["total"] == 2
        ok3 = ok3 and ids_of(am.api_search(category="data",
                                           sort="price_desc")) == \
            [ids["d1"], ids["d2"]]
        record("AC-AMCT3", ok3,
               "data=%r case=%d trim=%r kw=%r nlp=%r seller=%r"
               " band=%r/%r page=%r sort=%r"
               % (ids_of(data_rows),
                  am.api_search(category=" Data ")["count"],
                  ids_of(am.api_search(category="  data  ")),
                  ids_of(am.api_search(category="data",
                                       keyword="macro")),
                  ids_of(am.api_search(category="nlp")),
                  ids_of(am.api_search(category="data",
                                       dev_account="usr:dana")),
                  ids_of(am.api_search(category="data", min_price=4)),
                  ids_of(am.api_search(category="data", max_price=4)),
                  ids_of(paged), ids_of(am.api_search(
                      category="data", sort="price_desc"))))

        # -- AC-AMCT4 directory contract and conservation -----------
        # d4 is now bought once; that must not move the taxonomy.
        env = am.api_categories()
        rows = env["categories"]
        cats = cats_of(env)
        ok4 = (set(env) == DIR_KEYS
               and all(set(r) == CAT_ROW_KEYS for r in rows)
               and [r["category"] for r in rows] == sorted(cats)
               and env["category_count"] == len(rows) == 3
               and env["listing_count"] == 5
               and env["uncategorized_count"] == 1
               and env["disclaimer"] == DISCLAIMER
               and env["listing_count"] == env["uncategorized_count"]
               + sum(r["listing_count"] for r in rows)
               and cats["data"]["listing_count"] == 2
               and cats["nlp"]["listing_count"] == 1
               and cats["render"]["listing_count"] == 1)
        record("AC-AMCT4", ok4,
               "keys=%r rowkeys=%r cats=%r total=%d uncat=%d"
               " count=%d"
               % (set(env) == DIR_KEYS,
                  all(set(r) == CAT_ROW_KEYS for r in rows),
                  [r["category"] for r in rows],
                  env["listing_count"], env["uncategorized_count"],
                  env["category_count"]))

        # -- AC-AMCT5 partition and live-price law ------------------
        base = cats_of(am.api_categories())
        ok5 = (base["data"]["live_listing_count"] == 2
               and base["data"]["retired_listing_count"] == 0
               and base["data"]["min_live_price"] == 3
               and base["data"]["max_live_price"] == 10
               and base["render"]["min_live_price"] == 5
               and base["render"]["max_live_price"] == 5)
        clock.value = "2026-10-09T00:01:00Z"
        am.delist_api("usr:dana", ids["d2"])
        after_delist = cats_of(am.api_categories())
        ok5 = (ok5
               and after_delist["data"]["live_listing_count"] == 1
               and after_delist["data"]["retired_listing_count"] == 1
               and after_delist["data"]["listing_count"] == 2
               and after_delist["data"]["min_live_price"] == 10
               and after_delist["data"]["max_live_price"] == 10
               and ids_of(am.api_search(category="data")) == [ids["d1"]]
               and ids_of(am.api_search(category="data",
                                        include_delisted=True)) ==
               [ids["d2"], ids["d1"]])
        clock.value = "2026-10-09T00:01:10Z"
        am.relist_api("usr:dana", ids["d2"])
        after_relist = cats_of(am.api_categories())
        ok5 = (ok5
               and after_relist["data"]["live_listing_count"] == 2
               and after_relist["data"]["retired_listing_count"] == 0
               and after_relist["data"]["min_live_price"] == 3)
        clock.value = "2026-10-09T00:01:20Z"
        am.revise_price("usr:dana", ids["d3"], 20)
        after_reprice = cats_of(am.api_categories())
        ok5 = (ok5
               and after_reprice["render"]["min_live_price"] == 20
               and after_reprice["render"]["max_live_price"] == 20
               and any(r["listing_id"] == ids["d3"]
                       and r["token_price"] == 20
                       for r in am.api_search(category="render")[
                           "listings"]))
        record("AC-AMCT5", ok5,
               "base=%r/%r delist=%r/%r relist=%r/%r reprice=%r/%r"
               % (base["data"]["min_live_price"],
                  base["data"]["max_live_price"],
                  after_delist["data"]["live_listing_count"],
                  after_delist["data"]["retired_listing_count"],
                  after_relist["data"]["live_listing_count"],
                  after_relist["data"]["retired_listing_count"],
                  after_reprice["render"]["min_live_price"],
                  after_reprice["render"]["max_live_price"]))

        # -- AC-AMCT6 gate order and zero side effects --------------
        before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        order = []
        order.append(search_code(am, dev_account="bob",
                                 category=0))
        order.append(search_code(am, min_price=50, max_price=1,
                                 category=0))
        bad_codes = [search_code(am, category=bad)
                     for bad in (0, -1, True, 1.5, [], {})]
        blank_codes = [search_code(am, category=bad)
                       for bad in ("", "   ")]
        after = frozen_digests(am)
        tx_after = ledger_tx_ids(led)
        ok6 = (order == ["E_AM_BAD_ACCOUNT", "E_AM_BAD_PRICE"]
               and bad_codes == ["E_AM_BAD_ARGS"] * 6
               and blank_codes == ["E_AM_BAD_ARGS"] * 2
               and before == after
               and tx_before == tx_after)
        record("AC-AMCT6", ok6,
               "order=%r bad=%r blank=%r digests_frozen=%r tx=%r"
               % (order, bad_codes, blank_codes, before == after,
                  tx_before == tx_after))

        # -- AC-AMCT7 pure read -------------------------------------
        tx_before = ledger_tx_ids(led)
        dir_a = dumps(am.api_categories())
        dir_b = dumps(am.api_categories())
        s1 = dumps(am.api_search(category="data"))
        s2 = dumps(am.api_search(category="data"))
        after = frozen_digests(am)
        tx_after = ledger_tx_ids(led)
        ok7 = (dir_a == dir_b and s1 == s2 and before == after
               and tx_before == tx_after)
        record("AC-AMCT7", ok7,
               "dir_repeat=%r search_repeat=%r digests=%r tx=%r"
               % (dir_a == dir_b, s1 == s2, before == after,
                  tx_before == tx_after))

        # -- AC-AMCT8 migration, restart identity, wiring -----------
        leg_dir = tempfile.mkdtemp(prefix="amamct-leg-")
        leg_db = os.path.join(leg_dir, "apimarket.db")
        conn = sqlite3.connect(leg_db)
        conn.executescript(OLD_SCHEMA)
        conn.execute(
            "INSERT INTO apimarket_listings (dev_account, listing_key,"
            " title, description, payload_json, token_price, ai_label,"
            " listed_utc) VALUES (?,?,?,?,?,?,?,?)",
            ("usr:dana", "legacy", "Legacy API", "old row",
             json.dumps(PAYLOAD, sort_keys=True), 6, 0,
             "2026-10-08T00:00:00Z"))
        conn.commit()
        conn.close()
        leg_led = leg_m = leg_dk = leg_am = None
        try:
            leg_led, leg_m, leg_dk, _lg, leg_am = build_stack(
                leg_db, cfg, lobby_cfg)
            cols_a = [r[1] for r in sqlite3.connect(leg_db).execute(
                "PRAGMA table_info(apimarket_listings)").fetchall()]
            dir_leg = leg_am.api_categories()
            ok8 = ("category" in cols_a
                   and dir_leg["listing_count"] == 1
                   and dir_leg["uncategorized_count"] == 1
                   and dir_leg["categories"] == []
                   and leg_am.api_view(1)["category"] is None)
        finally:
            if leg_am is not None:
                leg_am.close()
            if leg_led is not None:
                leg_led.close()
        leg_led2 = leg_am2 = None
        try:
            leg_led2, leg_m2, leg_dk2, _gl, leg_am2 = build_stack(
                leg_db, cfg, lobby_cfg)
            cols_b = [r[1] for r in sqlite3.connect(leg_db).execute(
                "PRAGMA table_info(apimarket_listings)").fetchall()]
            ok8 = (ok8 and cols_b == cols_a
                   and dumps(leg_am2.api_categories()) ==
                   dumps(dir_leg))
        finally:
            if leg_am2 is not None:
                leg_am2.close()
            if leg_led2 is not None:
                leg_led2.close()
        base_dir = dumps(am.api_categories())
        base_search = dumps(am.api_search(category="data"))
        restarts = []
        for _ in range(2):
            close_stack(am, dk, metered, led)
            led, metered, dk, gate, am = build_stack(
                db_path, cfg, lobby_cfg)
            restarts.append((dumps(am.api_categories()),
                             dumps(am.api_search(category="data"))))
        ok8 = (ok8 and all(d == base_dir and s == base_search
                           for d, s in restarts))
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            reconcile_text = handle.read()
        wired = "ledger-apimarket-category" in reconcile_text
        with open(os.path.abspath(__file__), "rb") as handle:
            ascii_ok = all(b < 128 for b in handle.read())
        import ast
        with open(os.path.abspath(__file__), "r",
                  encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mods.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        net_marks = {"socket", "http", "urllib", "requests", "ftplib"}
        net_ok = not (mods & net_marks)
        outside_ok = not os.path.abspath(db_path).startswith(
            os.path.join(os.path.dirname(BASE), ""))
        shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
        shipped_ok = (shas_after[PRODUCT_FILES[2]]
                      == shas_before[PRODUCT_FILES[2]]
                      and shas_after[PRODUCT_FILES[3]]
                      == shas_before[PRODUCT_FILES[3]])
        ok8 = ok8 and wired and ascii_ok and net_ok and shipped_ok \
            and outside_ok
        record("AC-AMCT8", ok8,
               "migrated=%r idempotent=%r restarts=%d wired=%r"
               " ascii=%r no_net=%r shipped=%r outside=%r"
               % ("category" in cols_a, cols_a == cols_b,
                  len(restarts), wired, ascii_ok, net_ok, shipped_ok,
                  outside_ok))

        passed = sum(1 for _ac, ok in RESULTS if ok)
        print("\nSUITE %s %d/%d"
              % ("PASS" if passed == len(RESULTS) else "FAIL", passed,
                 len(RESULTS)), flush=True)
        return 0 if passed == len(RESULTS) else 1
    finally:
        A._now_utc = real_now
        if am is not None:
            try:
                am.close()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())