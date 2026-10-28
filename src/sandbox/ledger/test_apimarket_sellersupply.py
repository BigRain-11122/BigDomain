"""Acceptance suite for the apimarket seller-side supply rollup
(BigDomain R2188; criteria AC-SSUP1..AC-SSUP8 were registered in the
R2178 10/10 explore-queue row BEFORE this code existed - honesty law).

Face under proof: APIMarketFace.api_seller_supply(dev_account,
low_stock_threshold=1). The two existing supply faces answer ONE
listing (api_supply, api_supply_history) and api_seller_todo answers
one duty row, so a seller holding N listings had to call api_supply N
times to learn how much stock the shop carries. This suite pins the
rollup:

  - the sixteen-key envelope, the eleven-key rows, the honest empty
    seller and the seven-form account gate;
  - the live/retired partition and the fact that a retired row keeps
    every historical figure while re-listing flips only the flag;
  - the tracked/unlimited partition: an unlimited shelf reports None
    supply and None remaining, never counts as sold out or low stock,
    and is excluded from the two supply totals while its sales still
    count;
  - the four aggregate laws and the deriving of every count from the
    rows;
  - the scarcity seam: a purchase lowers remaining and flips sold_out
    (and low_stock), a refund hands the unit back and clears both, a
    restock raises remaining and clears sold_out - one face call
    sees each step;
  - the low-stock threshold law (default 1, explicit 0 counts only
    sold-out shelves, a wide threshold counts healthy ones, bad forms
    fail closed and the account gate runs first);
  - the pure-read law with frozen table digests and a constant
    ledger_tx set plus strict seller isolation and row ordering;
  - cross-restart byte identity over three instances, unchanged
    product file hashes and the runner wiring.

Usage: python test_apimarket_sellersupply.py
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

ENVELOPE_KEYS = {
    "dev_account", "listing_count", "live_listing_count",
    "retired_listing_count", "tracked_listing_count",
    "unlimited_listing_count", "sold_out_listing_count",
    "low_stock_listing_count", "total_effective_supply", "total_sold",
    "total_remaining", "total_restocked_units", "total_restock_count",
    "low_stock_threshold", "disclaimer", "listings"}

ROW_KEYS = {
    "listing_id", "listing_key", "delisted", "supply", "base_supply",
    "restocked_units", "restock_count", "sold", "remaining",
    "sold_out", "low_stock"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions",
          "apimarket_supply_revisions")


class Clock(object):
    """Deterministic stamp holder; the suite sets one explicit UTC
    string before each write (module clock patched in main)."""

    def __init__(self):
        self.value = "2026-09-01T00:00:00Z"

    def now_utc(self):
        return self.value


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


def fund(led, who):
    led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:" + who, "credit", 400)],
               "manual:fund-" + who, "suite funding " + who)


def rows_by_id(env):
    return {row["listing_id"]: row for row in env["listings"]}


def seed_world(led, dk, am, clock):
    """dana runs a shop of five shelves; erin runs one shelf that must
    never leak into dana's rollup.

    d1 supply 3 (two sales -> one unit left, low stock at the default
    threshold), d2 supply 2 (+2 restocked, one sale refunded then two
    more sales -> two left), d3 unlimited (one sale, never a shelf
    quantity), d4 supply 5 retired and re-listed with zero sales, d5
    supply 1 sold out."""
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SSUP-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SSUP-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin", "faye", "gus", "hal"):
        fund(led, who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:erin", "erin-key", 10, ["backtest"], False)

    clock.value = "2026-09-01T00:00:00Z"
    d1 = am.publish_api("usr:dana", "scan-api", "Scan API",
                        "portfolio scan endpoint", PAYLOAD, 10,
                        False, supply=3, category="data")["listing_id"]
    d2 = am.publish_api("usr:dana", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 6,
                        False, supply=2, category="tools")["listing_id"]
    d3 = am.publish_api("usr:dana", "loose-pack", "Loose Pack API",
                        "uncategorized payload pack", PAYLOAD, 5,
                        False)["listing_id"]
    d4 = am.publish_api("usr:dana", "report-pack", "Report Pack API",
                        "monthly report payloads", PAYLOAD, 4,
                        False, supply=5, category="data")["listing_id"]
    d5 = am.publish_api("usr:dana", "single-shot", "Single Shot API",
                        "one unit only", PAYLOAD, 3,
                        False, supply=1)["listing_id"]
    e1 = am.publish_api("usr:erin", "foreign-api", "Foreign API",
                        "another seller shelf", PAYLOAD, 9,
                        False, supply=7, category="data")["listing_id"]
    return d1, d2, d3, d4, d5, e1


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-ssup-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    clock = Clock()
    orig_now = A._now_utc
    A._now_utc = clock.now_utc
    try:
        return run(db_path, cfg, lobby_cfg, shas_before, clock)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, shas_before, clock):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d3, d4, d5, e1 = seed_world(led, dk, am, clock)

    # -- AC-SSUP1 the contract, the honest empty seller, the gate ----
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-ssup-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_supply("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    shelf = am.api_seller_supply("usr:dana")
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in shelf["listings"])
    gate_forms = []
    for bad in (None, "", "   ", 123, [], {"a": 1}, "dana"):
        try:
            am.api_seller_supply(bad)
            gate_forms.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            gate_forms.append(str(exc).split(":")[0].strip())
    ok1 = (set(shelf.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and row_keys_ok
           and shelf["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["listing_count"] == 0
           and empty["live_listing_count"] == 0
           and empty["retired_listing_count"] == 0
           and empty["tracked_listing_count"] == 0
           and empty["unlimited_listing_count"] == 0
           and empty["sold_out_listing_count"] == 0
           and empty["low_stock_listing_count"] == 0
           and empty["total_effective_supply"] is None
           and empty["total_sold"] == 0
           and empty["total_remaining"] is None
           and empty["total_restocked_units"] == 0
           and empty["total_restock_count"] == 0
           and empty["low_stock_threshold"] == 1
           and empty["listings"] == []
           and gate_forms == ["E_AM_BAD_ACCOUNT"] * 7)
    record("AC-SSUP1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r gate=%r"
           % (len(shelf), set(shelf.keys()) == ENVELOPE_KEYS,
              row_keys_ok, empty["listings"], gate_forms))

    # -- AC-SSUP2 the live/retired partition and the cycle law ------
    # the world opens with five live dana shelves, then d4 is retired
    # and re-listed: the retired reading keeps d4's row and every
    # historical figure, and the re-listed reading differs only in the
    # delisted flag.
    base = rows_by_id(shelf)
    ok2 = (shelf["listing_count"] == 5
           and shelf["live_listing_count"] == 5
           and shelf["retired_listing_count"] == 0
           and shelf["listing_count"]
           == (shelf["live_listing_count"]
               + shelf["retired_listing_count"])
           and shelf["listing_count"] == len(shelf["listings"])
           and all(not row["delisted"] for row in shelf["listings"]))
    clock.value = "2026-09-10T12:00:00Z"
    am.delist_api("usr:dana", d4)
    retired_env = am.api_seller_supply("usr:dana")
    rbi = rows_by_id(retired_env)
    ok2 = (ok2
           and retired_env["retired_listing_count"] == 1
           and retired_env["live_listing_count"] == 4
           and retired_env["listing_count"] == 5
           and rbi[d4]["delisted"] is True
           and rbi[d4]["supply"] == 5
           and rbi[d4]["base_supply"] == 5
           and rbi[d4]["remaining"] == 5
           and retired_env["total_effective_supply"] == 11)
    clock.value = "2026-09-20T12:00:00Z"
    am.relist_api("usr:dana", d4)
    relive = am.api_seller_supply("usr:dana")
    rbi2 = rows_by_id(relive)
    stripped_old = dict(rbi[d4])
    stripped_old.pop("delisted")
    stripped_new = dict(rbi2[d4])
    stripped_new.pop("delisted")
    ok2 = (ok2
           and relive["retired_listing_count"] == 0
           and relive["live_listing_count"] == 5
           and rbi2[d4]["delisted"] is False
           and stripped_old == stripped_new
           and dumps(relive) == dumps(shelf))
    record("AC-SSUP2", ok2,
           "live=%r retired=%r cycle_identical=%r"
           % (relive["live_listing_count"],
              retired_env["retired_listing_count"],
              dumps(relive) == dumps(shelf)))

    # -- AC-SSUP3 the tracked/unlimited partition -------------------
    ok3 = (shelf["tracked_listing_count"] == 4
           and shelf["unlimited_listing_count"] == 1
           and shelf["tracked_listing_count"]
           == (shelf["listing_count"]
               - shelf["unlimited_listing_count"])
           and shelf["tracked_listing_count"]
           == len([r for r in shelf["listings"]
                   if r["supply"] is not None])
           and base[d3]["supply"] is None
           and base[d3]["base_supply"] is None
           and base[d3]["remaining"] is None
           and base[d3]["sold_out"] is False
           and base[d3]["low_stock"] is False
           and base[d1]["supply"] == 3
           and base[d1]["base_supply"] == 3)
    # a wide threshold must never turn the unlimited shelf into a
    # low-stock row.
    wide = am.api_seller_supply("usr:dana", 5)
    wide_rows = rows_by_id(wide)
    ok3 = (ok3
           and wide_rows[d3]["low_stock"] is False
           and wide_rows[d3]["sold_out"] is False)
    record("AC-SSUP3", ok3,
           "tracked=%r unlimited=%r d3=%r"
           % (shelf["tracked_listing_count"],
              shelf["unlimited_listing_count"], base[d3]))

    # -- AC-SSUP4 the four aggregate laws --------------------------
    ok4 = (shelf["total_effective_supply"] == 11
           and shelf["total_sold"] == 0
           and shelf["total_remaining"] == 11
           and shelf["total_restocked_units"] == 0
           and shelf["total_restock_count"] == 0
           and shelf["total_effective_supply"]
           == sum(r["supply"] for r in shelf["listings"]
                  if r["supply"] is not None)
           and shelf["total_remaining"]
           == sum(r["remaining"] for r in shelf["listings"]
                  if r["remaining"] is not None)
           and shelf["total_sold"]
           == sum(r["sold"] for r in shelf["listings"])
           and shelf["total_restocked_units"]
           == sum(r["restocked_units"] for r in shelf["listings"])
           and shelf["total_restock_count"]
           == sum(r["restock_count"] for r in shelf["listings"])
           and shelf["sold_out_listing_count"]
           == len([r for r in shelf["listings"] if r["sold_out"]])
           and shelf["low_stock_listing_count"]
           == len([r for r in shelf["listings"] if r["low_stock"]]))
    record("AC-SSUP4", ok4,
           "effective=%r sold=%r remaining=%r restock=%r/%r"
           % (shelf["total_effective_supply"], shelf["total_sold"],
              shelf["total_remaining"], shelf["total_restocked_units"],
              shelf["total_restock_count"]))

    # -- AC-SSUP5 the scarcity seam, one step at a time -------------
    steps = {}

    def snap(tag):
        env = am.api_seller_supply("usr:dana")
        rows = rows_by_id(env)
        steps[tag] = {
            "d1": (rows[d1]["sold"], rows[d1]["remaining"],
                   rows[d1]["sold_out"], rows[d1]["low_stock"]),
            "d2": (rows[d2]["sold"], rows[d2]["remaining"],
                   rows[d2]["sold_out"], rows[d2]["low_stock"]),
            "d5": (rows[d5]["sold"], rows[d5]["remaining"],
                   rows[d5]["sold_out"], rows[d5]["low_stock"]),
            "sold_out_count": env["sold_out_listing_count"],
            "low_stock_count": env["low_stock_listing_count"],
            "total_sold": env["total_sold"],
            "total_remaining": env["total_remaining"],
        }

    snap("start")
    clock.value = "2026-09-21T10:00:00Z"
    am.purchase_api("usr:bob", d1, "ref-bob-d1")
    snap("d1_one")
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    snap("d1_two")
    bob_d2 = am.purchase_api("usr:dave", d2, "ref-dave-d2")
    am.purchase_api("usr:faye", d2, "ref-faye-d2")
    snap("d2_sold_out")
    clock.value = "2026-09-22T10:00:00Z"
    am.refund_api("usr:dave", bob_d2["purchase_id"],
                  "listing did not match description")
    snap("d2_refunded")
    clock.value = "2026-09-23T10:00:00Z"
    am.restock_api("usr:dana", d2, 2)
    snap("d2_restocked")
    am.purchase_api("usr:gus", d2, "ref-gus-d2")
    snap("d2_two_again")
    clock.value = "2026-09-24T10:00:00Z"
    am.purchase_api("usr:hal", d5, "ref-hal-d5")
    snap("d5_sold_out")
    ok5 = (steps["start"]["d1"] == (0, 3, False, False)
           and steps["d1_one"]["d1"] == (1, 2, False, False)
           and steps["d1_two"]["d1"] == (2, 1, False, True)
           and steps["d2_sold_out"]["d2"] == (2, 0, True, True)
           and steps["d2_sold_out"]["sold_out_count"] == 1
           and steps["d2_refunded"]["d2"] == (1, 1, False, True)
           and steps["d2_refunded"]["sold_out_count"] == 0
           and steps["d2_restocked"]["d2"] == (1, 3, False, False)
           and steps["d2_two_again"]["d2"] == (2, 2, False, False)
           and steps["d5_sold_out"]["d5"] == (1, 0, True, True)
           and steps["d5_sold_out"]["sold_out_count"] == 1
           and steps["d5_sold_out"]["low_stock_count"] == 2
           and steps["d5_sold_out"]["total_sold"] == 5
           and steps["d5_sold_out"]["total_remaining"] == 8)
    # the unlimited shelf sold once, so its sold count must be in the
    # total although it never contributes a unit count.
    am.purchase_api("usr:bob", d3, "ref-bob-d3")
    after_unlimited = am.api_seller_supply("usr:dana")
    ok5 = (ok5
           and rows_by_id(after_unlimited)[d3]["sold"] == 1
           and rows_by_id(after_unlimited)[d3]["supply"] is None
           and after_unlimited["total_sold"] == 6
           and after_unlimited["total_remaining"] == 8)
    record("AC-SSUP5", ok5,
           "start=%r one=%r two=%r soldout=%r refund=%r restock=%r"
           " again=%r"
           % (steps["start"]["d1"], steps["d1_one"]["d1"],
              steps["d1_two"]["d1"], steps["d2_sold_out"]["d2"],
              steps["d2_refunded"]["d2"], steps["d2_restocked"]["d2"],
              steps["d2_two_again"]["d2"]))

    # -- AC-SSUP6 the threshold law and the gate order -------------
    roomy = am.api_seller_supply("usr:dana")
    tight = am.api_seller_supply("usr:dana", 0)
    loose = am.api_seller_supply("usr:dana", 5)
    tight_rows = rows_by_id(tight)
    loose_rows = rows_by_id(loose)
    bad_forms = []
    for bad in (True, False, "1", 1.5, -1, [], {}):
        try:
            am.api_seller_supply("usr:dana", bad)
            bad_forms.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            bad_forms.append(str(exc).split(":")[0].strip())
    order_probe = []
    for acct, thr in ((None, -1), ("dana", "x"), ("", True)):
        try:
            am.api_seller_supply(acct, thr)
            order_probe.append("NO-ERROR")
        except A.ApiMarketError as exc:
            order_probe.append(str(exc).split(":")[0].strip())
    ok6 = (roomy["low_stock_threshold"] == 1
           and roomy["low_stock_listing_count"] == 2
           and tight["low_stock_threshold"] == 0
           and tight["low_stock_listing_count"] == 1
           and tight_rows[d5]["low_stock"] is True
           and tight_rows[d1]["low_stock"] is False
           and tight_rows[d2]["low_stock"] is False
           and loose["low_stock_threshold"] == 5
           and loose["low_stock_listing_count"] == 4
           and loose_rows[d4]["low_stock"] is True
           and loose_rows[d3]["low_stock"] is False
           and bad_forms == ["E_AM_BAD_ARGS"] * 7
           and order_probe == ["E_AM_BAD_ACCOUNT"] * 3)
    record("AC-SSUP6", ok6,
           "default=%r zero=%r zero_rows=%r wide=%r bad=%r order=%r"
           % (roomy["low_stock_listing_count"],
              tight["low_stock_listing_count"],
              (tight_rows[d1]["low_stock"], tight_rows[d5]["low_stock"]),
              loose["low_stock_listing_count"], bad_forms, order_probe))

    # -- AC-SSUP7 pure read, isolation and row ordering ------------
    env_a = am.api_seller_supply("usr:dana")
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    first = dumps(am.api_seller_supply("usr:dana"))
    second = dumps(am.api_seller_supply("usr:dana"))
    third = dumps(am.api_seller_supply("usr:dana", 3))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    erin_env = am.api_seller_supply("usr:erin")
    ids = [row["listing_id"] for row in env_a["listings"]]
    ok7 = (first == second
           and digests_before == digests_after
           and tx_before == tx_after
           and ids == sorted(ids)
           and e1 not in ids
           and erin_env["listing_count"] == 1
           and erin_env["listings"][0]["listing_id"] == e1
           and erin_env["total_effective_supply"] == 7
           and all(row["listing_id"] in (d1, d2, d3, d4, d5)
                   for row in env_a["listings"]))
    record("AC-SSUP7", ok7,
           "identical=%r frozen=%r tx=%r ordered=%r isolated=%r"
           " sha16=%s"
           % (first == second, digests_before == digests_after,
              tx_before == tx_after, ids == sorted(ids),
              e1 not in ids,
              hashlib.sha256(first.encode("utf-8")).hexdigest()[:16]))

    # -- AC-SSUP8 cross-restart identity and the wiring ------------
    final = dumps(am.api_seller_supply("usr:dana"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_env = dumps(am.api_seller_supply("usr:dana"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_env = dumps(am.api_seller_supply("usr:dana"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_seller_supply("usr:dana")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (final == second_env == third_env
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-sellersupply" in runner_text)
    record("AC-SSUP8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_env == third_env, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-sellersupply" in runner_text))

    close_stack(am, dk, metered, led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    verdict = "SUITE PASS %d/%d" % (passed, total)
    if passed != total:
        verdict = "SUITE FAIL %d/%d" % (passed, total)
    print(verdict, flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())