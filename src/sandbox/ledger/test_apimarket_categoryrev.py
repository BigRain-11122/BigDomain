"""Acceptance suite for the apimarket seller-side category revision leg
(BigDomain R2147; canon = the explore-queue row seeded and claimed in
R2147, criteria AC-AMCG1..AC-AMCG8 registered there. Honesty note: the
seven anchors AC-AMCG, revise_category, api_category_history,
apimarket_category_revisions, E_AM_CATEGORY_UNCHANGED,
test_apimarket_categoryrev and ledger-apimarket-categoryrev were all
git-grep -F zero-occupancy verified against the committed HEAD tree
(rc=1) before this suite existed; the criterion TEXT landed in the
queue row in the same window as the code, the R2137/R2141/R2144
precedent).

Face under proof: revise_category + api_category_history. R2132 made
the category declaration write-once on the listing row, and edit_listing
repairs title and description only, so a seller who filed a service
under the wrong bucket was stuck with it forever. Four read faces then
inherited the mistake at once (catalog directory, category demand,
discovery filter, competitive bucket). This suite pins:

  - one append-only apimarket_category_revisions row per change, the
    listing row never rewritten, the nine-key envelope;
  - the pinned fail-closed gate order and the unchanged state judged
    against the EFFECTIVE bucket;
  - one effective-bucket seam shared by all category readers;
  - the history surface, its errors and its pure-read law;
  - the competitive bucket moving in the same step;
  - the economic-stasis law (a classification move is not a trade);
  - determinism, cross-restart identity, runner wiring and hygiene.

Usage: python test_apimarket_categoryrev.py
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

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

BAD_ACCOUNTS = ["", "bob", None, 5, True, [], {}, "   "]

BAD_CATEGORIES = [5, 1.5, True, [], {}, "   ", "x" * 41]

ENVELOPE_KEYS = {"listing_id", "dev_account", "listing_key",
                 "revision_id", "previous_category", "category",
                 "category_revision_count", "revised_utc",
                 "disclaimer"}

HISTORY_KEYS = {"listing_id", "base_category", "category",
                "revision_count", "latest_revision_utc", "delisted",
                "delisted_utc", "disclaimer", "revisions"}

REVISION_KEYS = {"revision_id", "dev_account", "previous_category",
                 "category", "revised_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_rating_replies", "apimarket_reply_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_category_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_supply_revisions")


class Clock(object):
    """Single mutable stamp behind A._now_utc, so revisions are
    orderable without sleeping."""

    def __init__(self, stamp):
        self.stamp = stamp

    def now_utc(self):
        return self.stamp

    def set(self, stamp):
        self.stamp = stamp


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


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


def code_of(exc):
    return getattr(exc, "code", None)


def expect_code(code, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except A.ApiMarketError as exc:
        return code_of(exc) == code
    except BaseException:
        return False
    return False


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


def base_category(market_db, listing_id):
    conn = sqlite3.connect(market_db)
    row = conn.execute(
        "SELECT category FROM apimarket_listings"
        " WHERE listing_id = ?", (listing_id,)).fetchone()
    conn.close()
    return None if row is None else row[0]


def revision_rows(market_db):
    conn = sqlite3.connect(market_db)
    rows = conn.execute(
        "SELECT listing_id, dev_account, previous_category,"
        " category, revised_utc FROM apimarket_category_revisions"
        " ORDER BY revision_id").fetchall()
    conn.close()
    return rows


def bucket(envelope, name):
    for row in envelope["categories"]:
        if row["category"] == name:
            return row
    return None


def seed_world(led, dk, am, clock):
    """Two sellers, two buyers. dana publishes three listings across
    two buckets (one is retired later), erin publishes two so owner
    isolation and the cross-seller same-bucket move are both
    provable."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-CG-A", "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-CG-S", "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 600),
                    ("usr:" + who, "credit", 600)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:erin", "erin-key", 10, ["backtest"], False)

    clock.set("2026-10-27T08:00:00Z")
    ids = {}
    ids["alpha"] = am.publish_api("usr:dana", "alpha", "Service Alpha",
                                  "service payload alpha", PAYLOAD, 10,
                                  False, category="Backtest")["listing_id"]
    ids["beta"] = am.publish_api("usr:dana", "beta", "Service Beta",
                                 "service payload beta", PAYLOAD, 8,
                                 False, category="Backtest")["listing_id"]
    ids["gamma"] = am.publish_api("usr:dana", "gamma", "Service Gamma",
                                  "service payload gamma", PAYLOAD, 6,
                                  False, category="Data")["listing_id"]
    ids["zeta"] = am.publish_api("usr:erin", "zeta", "Service Zeta",
                                 "service payload zeta", PAYLOAD, 7,
                                 False, category="Data")["listing_id"]
    ids["eta"] = am.publish_api("usr:erin", "eta", "Service Eta",
                                "service payload eta", PAYLOAD, 5,
                                False, category=None)["listing_id"]
    clock.set("2026-10-27T08:10:00Z")
    am.purchase_api("usr:bob", ids["alpha"], "categoryrev-sale-1")
    clock.set("2026-10-27T08:20:00Z")
    am.purchase_api("usr:carol", ids["beta"], "categoryrev-sale-2")
    clock.set("2026-10-27T08:30:00Z")
    am.rate_api("usr:bob", ids["alpha"], 5)
    return ids


def main():
    tmp = tempfile.mkdtemp(prefix="amcg-")
    db_path = os.path.join(tmp, "categoryrev.db")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    market_db = am.db_path

    original_now = A._now_utc
    clock = Clock("2026-10-27T09:00:00Z")
    A._now_utc = clock.now_utc
    try:
        ids = seed_world(led, dk, am, clock)
        stats_before = am.api_market_stats()

        # -- AC-AMCG1 append-only shape + contract --------------------
        base_shown = base_category(market_db, ids["alpha"])
        clock.set("2026-10-27T10:00:00Z")
        rev1 = am.revise_category("usr:dana", ids["alpha"], "  Data  ")
        base_after = base_category(market_db, ids["alpha"])
        rows1 = revision_rows(market_db)
        ok1 = (set(rev1.keys()) == ENVELOPE_KEYS
               and len(rev1) == 9
               and rev1["listing_id"] == ids["alpha"]
               and rev1["dev_account"] == "usr:dana"
               and rev1["listing_key"] == "alpha"
               and rev1["previous_category"] == "Backtest"
               and rev1["category"] == "Data"
               and rev1["category_revision_count"] == 1
               and rev1["revised_utc"] == "2026-10-27T10:00:00Z"
               and rev1["disclaimer"] == DISCLAIMER
               and len(rows1) == 1
               and rows1[0] == (ids["alpha"], "usr:dana", "Backtest",
                                "Data", "2026-10-27T10:00:00Z")
               and base_shown == base_after == "Backtest")
        record("AC-AMCG1", ok1,
               "keys=%d rows=%d base=%r/%r cat=%r"
               % (len(rev1), len(rows1), base_shown, base_after,
                  rev1["category"]))

        # -- AC-AMCG2 pinned gate order, fail-closed ------------------
        # The retirement probes need a genuinely retired listing, so
        # the lifecycle pair runs FIRST; the frozen-digest window then
        # covers the refusal battery only (a refusal must move nothing).
        clock.set("2026-10-27T10:30:00Z")
        am.delist_api("usr:dana", ids["gamma"])
        retired_ok = expect_code(
            A.E_AM_DELISTED, am.revise_category, "usr:dana",
            ids["gamma"], "Backtest")
        # Retirement is judged BEFORE the category shape gate, so a
        # retired probe carrying a bad bucket still answers DELISTED.
        retired_ok = retired_ok and expect_code(
            A.E_AM_DELISTED, am.revise_category, "usr:dana",
            ids["gamma"], 5)
        clock.set("2026-10-27T10:40:00Z")
        am.relist_api("usr:dana", ids["gamma"])
        digests_before = market_digests(am)
        txs_before = ledger_tx_ids(led)
        rows_before = len(revision_rows(market_db))
        gate_ok = retired_ok and all(expect_code(A.E_AM_BAD_ACCOUNT,
                                  am.revise_category, acct,
                                  ids["beta"], "Data")
                      for acct in BAD_ACCOUNTS)
        gate_ok = gate_ok and all(
            expect_code(A.E_AM_BAD_ARGS, am.revise_category, "usr:dana",
                        bad, "Data")
            for bad in (0, -3, "1", True, 1.5, None))
        gate_ok = gate_ok and expect_code(
            A.E_AM_UNKNOWN_LISTING, am.revise_category, "usr:dana",
            999999, "Data")
        gate_ok = gate_ok and expect_code(
            A.E_AM_NOT_OWNER, am.revise_category, "usr:erin",
            ids["beta"], "Data")
        gate_ok = gate_ok and all(
            expect_code(A.E_AM_BAD_ARGS, am.revise_category, "usr:dana",
                        ids["beta"], bad) for bad in BAD_CATEGORIES)
        gate_ok = gate_ok and expect_code(
            A.E_AM_CATEGORY_UNCHANGED, am.revise_category, "usr:dana",
            ids["beta"], "  Backtest  ")
        # Double-bad probes answer the FIRST failing gate.
        gate_ok = gate_ok and expect_code(
            A.E_AM_BAD_ACCOUNT, am.revise_category, "bob", 0, 5)
        gate_ok = gate_ok and expect_code(
            A.E_AM_BAD_ARGS, am.revise_category, "usr:dana", 0, 5)
        gate_ok = gate_ok and expect_code(
            A.E_AM_NOT_OWNER, am.revise_category, "usr:erin",
            ids["beta"], 5)
        gate_ok = gate_ok and expect_code(
            A.E_AM_UNKNOWN_LISTING, am.revise_category, "usr:dana",
            999999, 5)
        ok2 = (gate_ok and market_digests(am) == digests_before
               and ledger_tx_ids(led) == txs_before
               and len(revision_rows(market_db)) == rows_before)
        record("AC-AMCG2", ok2,
               "gate=%s digests=%s tx=%s rows=%d"
               % (gate_ok, market_digests(am) == digests_before,
                  ledger_tx_ids(led) == txs_before,
                  len(revision_rows(market_db))))

        # -- AC-AMCG3 one effective seam across four read faces -------
        view = am.api_view(ids["alpha"])
        search_back = am.api_search(category="Backtest")
        search_data = am.api_search(category="Data")
        catalog = am.api_categories()
        demand = am.api_category_demand()
        seam_ok = (view["category"] == "Data"
                   and view["base_category"] == "Backtest"
                   and view["category_revision_count"] == 1
                   and view["latest_category_revision_utc"]
                   == "2026-10-27T10:00:00Z")
        search_ok = (
            [r["listing_id"] for r in search_back["listings"]]
            == [ids["beta"]]
            and [r["listing_id"] for r in search_data["listings"]]
            == [ids["gamma"], ids["zeta"], ids["alpha"]]
            and search_data["count"] == 3)
        catalog_ok = (bucket(catalog, "Backtest")["listing_count"] == 1
                      and bucket(catalog, "Data")["listing_count"] == 3
                      and catalog["listing_count"] == 5
                      and catalog["uncategorized_count"] == 1)
        demand_back = bucket(demand, "Backtest")
        demand_data = bucket(demand, "Data")
        demand_ok = (demand_back["listing_count"] == 1
                     and demand_back["purchase_count"] == 1
                     and demand_back["gross_tokens"] == 8
                     and demand_data["listing_count"] == 3
                     and demand_data["purchase_count"] == 1
                     and demand_data["gross_tokens"] == 10
                     and demand_data["buyer_count"] == 1
                     and demand["purchase_count"] == 2
                     and demand["gross_tokens"] == 18)
        ok3 = (seam_ok and search_ok and catalog_ok and demand_ok)
        record("AC-AMCG3", ok3,
               "view=%s search=%s catalog=%s demand=%s"
               % (seam_ok, search_ok, catalog_ok, demand_ok))

        # -- AC-AMCG4 unchanged vs effective, None is a legal move ----
        unchanged_ok = expect_code(A.E_AM_CATEGORY_UNCHANGED,
                                   am.revise_category, "usr:dana",
                                   ids["alpha"], "Data")
        clock.set("2026-10-27T11:00:00Z")
        back = am.revise_category("usr:dana", ids["alpha"], "Backtest")
        back_ok = (back["previous_category"] == "Data"
                   and back["category"] == "Backtest"
                   and back["category_revision_count"] == 2)
        # Re-filing into the honest uncategorized bucket is a legal
        # move, not a deletion.
        clock.set("2026-10-27T11:10:00Z")
        nulled = am.revise_category("usr:dana", ids["gamma"], None)
        nulled_ok = (nulled["category"] is None
                     and nulled["previous_category"] == "Data"
                     and am.api_view(ids["gamma"])["category"] is None
                     and am.api_categories()["uncategorized_count"] == 2)
        # A bucket another seller also uses is free: ownership, not
        # bucket, decides.
        clock.set("2026-10-27T11:20:00Z")
        cross = am.revise_category("usr:erin", ids["zeta"], "Backtest")
        cross_ok = (cross["dev_account"] == "usr:erin"
                    and cross["category"] == "Backtest")
        clock.set("2026-10-27T11:30:00Z")
        restored = am.revise_category("usr:dana", ids["gamma"], "Data")
        restored_ok = (restored["previous_category"] is None
                       and restored["category"] == "Data")
        ok4 = (unchanged_ok and back_ok and nulled_ok and cross_ok
               and restored_ok and len(revision_rows(market_db)) == 5)
        record("AC-AMCG4", ok4,
               "unchanged=%s back=%d nulled=%s cross=%s restored=%s"
               " rows=%d"
               % (unchanged_ok, back["category_revision_count"],
                  nulled_ok, cross_ok, restored_ok,
                  len(revision_rows(market_db))))

        # -- AC-AMCG5 history surface, shape, order, errors -----------
        hist = am.api_category_history(ids["alpha"])
        shape_ok = (set(hist.keys()) == HISTORY_KEYS
                    and len(hist) == 9
                    and all(set(x.keys()) == REVISION_KEYS
                            and len(x) == 5 for x in hist["revisions"]))
        order_ok = ([x["category"] for x in hist["revisions"]]
                    == ["Data", "Backtest"])
        values_ok = (hist["base_category"] == "Backtest"
                     and hist["category"] == "Backtest"
                     and hist["revision_count"] == 2
                     and hist["latest_revision_utc"]
                     == "2026-10-27T11:00:00Z"
                     and hist["delisted"] is False
                     and hist["revisions"][0]["previous_category"]
                     == "Backtest"
                     and hist["revisions"][1]["previous_category"]
                     == "Data")
        errors_ok = (expect_code(A.E_AM_UNKNOWN_LISTING,
                                 am.api_category_history, 999999)
                     and expect_code(A.E_AM_BAD_ARGS,
                                     am.api_category_history, 0)
                     and expect_code(A.E_AM_BAD_ARGS,
                                     am.api_category_history, "1")
                     and expect_code(A.E_AM_BAD_ARGS,
                                     am.api_category_history, True))
        ok5 = shape_ok and order_ok and values_ok and errors_ok
        record("AC-AMCG5", ok5,
               "shape=%s order=%s values=%s errors=%s"
               % (shape_ok, order_ok, values_ok, errors_ok))

        # -- AC-AMCG6 the competitive bucket moves in one step --------
        pos_before = am.api_listing_position(ids["alpha"])
        clock.set("2026-10-27T12:00:00Z")
        am.revise_category("usr:dana", ids["alpha"], "Data")
        pos_after = am.api_listing_position(ids["alpha"])
        bucket_ok = (pos_before["category"] == "Backtest"
                     and pos_before["category_size"] == 3
                     and [r["listing_id"] for r in pos_before["rivals"]]
                     == [ids["zeta"], ids["beta"], ids["alpha"]]
                     and pos_before["category_min_price"] == 7
                     and pos_before["price_rank"] == 3
                     and pos_before["cheaper_count"] == 2
                     and pos_after["category"] == "Data"
                     and pos_after["category_size"] == 2
                     and sorted(r["listing_id"] for r in pos_after["rivals"])
                     == sorted([ids["gamma"], ids["alpha"]])
                     and pos_after["category_min_price"] == 6
                     and pos_after["price_rank"] == 2
                     and pos_after["cheaper_count"] == 1)
        ok6 = bucket_ok
        record("AC-AMCG6", ok6,
               "before=%r/%d/min%d after=%r/%d/min%d"
               % (pos_before["category"], pos_before["category_size"],
                  pos_before["category_min_price"],
                  pos_after["category"], pos_after["category_size"],
                  pos_after["category_min_price"]))

        # -- AC-AMCG7 economic stasis + pure read + determinism -------
        stats_after = am.api_market_stats()
        stable_ok = dumps(stats_before) == dumps(stats_after)
        catalog7 = am.api_categories()
        demand7 = am.api_category_demand()
        conservation_ok = (
            catalog7["listing_count"]
            == sum(r["listing_count"] for r in catalog7["categories"])
            + catalog7["uncategorized_count"]
            and all(r["listing_count"] == r["live_listing_count"]
                    + r["retired_listing_count"]
                    for r in catalog7["categories"])
            and all(r["gross_tokens"] == r["net_gross_tokens"]
                    + r["refunded_tokens"]
                    for r in demand7["categories"]))
        digests7 = market_digests(am)
        txs7 = ledger_tx_ids(led)
        first = dumps(am.api_category_history(ids["alpha"]))
        second = dumps(am.api_category_history(ids["alpha"]))
        repeated = all(
            dumps(am.api_listing_position(lid))
            == dumps(am.api_listing_position(lid))
            for lid in (ids["alpha"], ids["beta"], ids["gamma"]))
        ok7 = (stable_ok and conservation_ok and first == second
               and repeated and market_digests(am) == digests7
               and ledger_tx_ids(led) == txs7)
        record("AC-AMCG7", ok7,
               "stats_stable=%s conservation=%s history_same=%s"
               " faces_same=%s digests=%s tx=%s"
               % (stable_ok, conservation_ok, first == second,
                  repeated, market_digests(am) == digests7,
                  ledger_tx_ids(led) == txs7))

        # -- AC-AMCG8 cross-restart identity, wiring, hygiene ---------
        snapshot = [dumps(am.api_view(ids["alpha"])),
                    dumps(am.api_category_history(ids["alpha"])),
                    dumps(am.api_categories()),
                    dumps(am.api_category_demand()),
                    dumps(am.api_listing_position(ids["alpha"]))]
        close_stack(am, dk, metered, led)
        restarts = 0
        for _ in range(2):
            led, metered, dk, gate, am = build_stack(db_path, cfg,
                                                     lobby_cfg)
            again = [dumps(am.api_view(ids["alpha"])),
                     dumps(am.api_category_history(ids["alpha"])),
                     dumps(am.api_categories()),
                     dumps(am.api_category_demand()),
                     dumps(am.api_listing_position(ids["alpha"]))]
            if again == snapshot:
                restarts += 1
            close_stack(am, dk, metered, led)
        with open(RECONCILE, "rb") as handle:
            runner = handle.read().decode("utf-8")
        wired = ('("ledger-apimarket-categoryrev"' in runner
                 and "test_apimarket_categoryrev.py" in runner)
        with open(os.path.abspath(__file__), "rb") as handle:
            source = handle.read()
        ascii_ok = all(b < 128 for b in source)
        ok8 = (restarts == 2 and wired and ascii_ok)
        record("AC-AMCG8", ok8,
               "restarts=%d/2 wired=%s ascii=%s"
               % (restarts, wired, ascii_ok))

    finally:
        A._now_utc = original_now
        try:
            close_stack(am, dk, metered, led)
        except BaseException:
            pass

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    verdict = "SUITE PASS" if passed == total else "SUITE FAIL"
    print("\n%s %d/%d" % (verdict, passed, total), flush=True)
    if passed != total:
        for ac, ok in RESULTS:
            if not ok:
                print("FAILED: " + ac, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())