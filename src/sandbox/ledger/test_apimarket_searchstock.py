"""Acceptance suite for the apimarket discovery availability axis
(BigDomain R2142; canon = the explore-queue row seeded and claimed in
R2142, criteria AC-AMAV1..AC-AMAV8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMAV prefix, the
in_stock parameter, this suite name and the ledger-apimarket-
searchstock runner label were all git-grep zero-occupancy anchored
2026-10-26, rc=1).

Face under proof: APIMarketFace.api_search. The discovery face could
already filter by category, order by five modes and page, but a
sold-out listing and a buyable one looked byte-identical, so a buyer
had to read every row and call api_supply per listing. This window
pins the new axis:

  - the backward-compatibility law (no in_stock => the pre-change
    envelope, criteria and row keys byte for byte);
  - the bool-only gate and its pinned position (after the keyword,
    seller, price-band, include_delisted and category gates, before
    paging and sort), fail-closed with zero side effects;
  - the partition law against api_supply (True + False == the
    unfiltered set, disjoint, union equal);
  - composition with every other axis and paging totals derived
    from the filtered set;
  - the scarcity dynamics (purchase empties, refund refills,
    restock refills, unlimited supply always in stock);
  - order preservation across all five sort modes;
  - honest empties and the retired-listing rule;
  - cross-restart byte identity, the pure-read law and the runner
    registration.

Usage: python test_apimarket_searchstock.py
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

ROW_KEYS = {
    "listing_id", "dev_account", "listing_key", "title",
    "token_price", "ai_label", "rating_count", "rating_avg",
    "category", "delisted", "delisted_utc"}

LEGACY_CRITERIA = {
    "keyword", "dev_account", "min_price", "max_price",
    "include_delisted"}

SORT_MODES = ("price_asc", "price_desc", "rating", "sales", "newest")


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
    names = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
        " AND name LIKE 'apimarket_%' ORDER BY name").fetchall()]
    out = {t: table_digest(conn, t) for t in names}
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


def ids(env):
    return [row["listing_id"] for row in env["listings"]]


def seed_world(led, dk, am):
    """dana: L1 (price 10, supply 2, data), L2 (price 3, supply 1,
    data), L3 (price 5, unlimited, uncategorized). frank: L4 (price
    7, supply 1, tools), L5 (price 4, supply 1, tools).

    Purchases: bob buys L2 and L4 (both sell out), carol buys one
    unit of L1 (one unit left). So in_stock=True is {L1, L3, L5}
    and in_stock=False is {L2, L4}."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-AMAV-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-AMAV-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 400),
                    ("usr:" + who, "credit", 400)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    l1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, supply=2, category="data")["listing_id"]
    l2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True,
                        supply=1, category="data")["listing_id"]
    l3 = am.publish_api("usr:dana", "chart-raw", "Raw Chart API",
                        "uncategorized chart payloads", PAYLOAD, 5,
                        False)["listing_id"]
    l4 = am.publish_api("usr:frank", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 7,
                        False, supply=1, category="tools")["listing_id"]
    l5 = am.publish_api("usr:frank", "docs-kit", "Docs Kit API",
                        "document pipeline kit", PAYLOAD, 4, False,
                        supply=1, category="tools")["listing_id"]
    bob_l2 = am.purchase_api("usr:bob", l2, "ref-bob-l2")
    bob_l4 = am.purchase_api("usr:bob", l4, "ref-bob-l4")
    carol_l1 = am.purchase_api("usr:carol", l1, "ref-carol-l1")
    return l1, l2, l3, l4, l5, bob_l2, bob_l4, carol_l1


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-searchstock-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    (l1, l2, l3, l4, l5,
     bob_l2, bob_l4, carol_l1) = seed_world(led, dk, am)

    # -- AC-AMAV1 backward compatibility and the row contract -----------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-searchstock-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_search()
    empty_stock = e_am.api_search(in_stock=True)
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_search()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in env["listings"])
    paged_keys = set(am.api_search(in_stock=True, limit=1, offset=0)
                     .keys())
    stock = am.api_search(in_stock=True)
    ok1 = (set(env.keys()) == {"disclaimer", "criteria", "count",
                               "listings"}
           and set(env["criteria"].keys()) == LEGACY_CRITERIA
           and "in_stock" not in env["criteria"]
           and row_keys_ok
           and env["count"] == 5
           and env["disclaimer"] == DISCLAIMER
           and set(stock["criteria"].keys())
           == LEGACY_CRITERIA | {"in_stock"}
           and stock["criteria"]["in_stock"] is True
           and all(set(row.keys()) == ROW_KEYS
                   for row in stock["listings"])
           and paged_keys == {"disclaimer", "criteria", "count",
                              "returned", "total", "limit", "offset",
                              "truncated", "listings"}
           and empty["count"] == 0
           and empty["listings"] == []
           and empty_stock["count"] == 0
           and empty_stock["criteria"]["in_stock"] is True)
    record("AC-AMAV1", ok1,
           "legacy=%r rows=%r stock_keys=%r paged=%r empty=%d"
           % (set(env["criteria"].keys()) == LEGACY_CRITERIA,
              row_keys_ok, set(stock["criteria"].keys()),
              paged_keys == {"disclaimer", "criteria", "count",
                             "returned", "total", "limit", "offset",
                             "truncated", "listings"},
              empty["count"]))

    # -- AC-AMAV2 bool-only gate, pinned order and zero side effects ----
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    gate_codes = []
    for bad in (1, 0, "yes", [], {}, 1.0):
        try:
            am.api_search(in_stock=bad)
            gate_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            gate_codes.append(getattr(exc, "code", "?"))
    order_codes = []
    for call in (lambda: am.api_search(min_price=10, max_price=1,
                                       in_stock=1),
                 lambda: am.api_search(keyword="   ", in_stock=1),
                 lambda: am.api_search(dev_account="bob",
                                       in_stock=1),
                 lambda: am.api_search(include_delisted="yes",
                                       in_stock=1),
                 lambda: am.api_search(category="  ", in_stock=1),
                 lambda: am.api_search(in_stock=1, limit=0)):
        try:
            call()
            order_codes.append("NO-ERROR")
        except A.ApiMarketError as exc:
            order_codes.append(getattr(exc, "code", "?"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok2 = (gate_codes == ["E_AM_BAD_ARGS"] * 6
           and order_codes == ["E_AM_BAD_PRICE", "E_AM_BAD_ARGS",
                               "E_AM_BAD_ACCOUNT", "E_AM_BAD_ARGS",
                               "E_AM_BAD_ARGS", "E_AM_BAD_ARGS"]
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-AMAV2", ok2,
           "gates=%r order=%r digests=%r tx=%r"
           % (gate_codes, order_codes,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-AMAV3 partition law against api_supply ----------------------
    full = am.api_search()
    live = am.api_search(in_stock=True)
    gone = am.api_search(in_stock=False)
    sold_map = {row["listing_id"]:
                bool(am.api_supply(row["listing_id"])["sold_out"])
                for row in full["listings"]}
    live_ids = set(ids(live))
    gone_ids = set(ids(gone))
    full_ids = set(ids(full))
    ok3 = (live_ids == set(k for k, v in sold_map.items() if not v)
           and gone_ids == set(k for k, v in sold_map.items() if v)
           and not (live_ids & gone_ids)
           and (live_ids | gone_ids) == full_ids
           and len(live_ids) + len(gone_ids) == len(full_ids)
           and live_ids == {l1, l3, l5}
           and gone_ids == {l2, l4})
    record("AC-AMAV3", ok3,
           "live=%r gone=%r union=%r counts=%d+%d==%d"
           % (sorted(live_ids), sorted(gone_ids),
              (live_ids | gone_ids) == full_ids,
              len(live_ids), len(gone_ids), len(full_ids)))

    # -- AC-AMAV4 composition with every other axis and paging ----------
    cat_stock = am.api_search(category="data", in_stock=True)
    cat_all = am.api_search(category="data")
    seller_stock = am.api_search(dev_account="usr:frank",
                                in_stock=True)
    band_stock = am.api_search(max_price=5, in_stock=True)
    kw_stock = am.api_search(keyword="api", in_stock=True)
    page1 = am.api_search(in_stock=True, limit=2, offset=0)
    page2 = am.api_search(in_stock=True, limit=2, offset=2)
    stitched = ids(page1) + ids(page2)
    ok4 = (ids(cat_stock) == [l1]
           and ids(cat_all) == [l2, l1]
           and ids(seller_stock) == [l5]
           and set(ids(band_stock)) == {l3, l5}
           and ids(kw_stock) == ids(live)
           and page1["total"] == len(live_ids)
           and page1["count"] == 2
           and page2["total"] == len(live_ids)
           and page2["truncated"] is False
           and stitched == ids(live))
    record("AC-AMAV4", ok4,
           "cat=%r seller=%r band=%r kw==live=%r stitch=%r total=%d"
           % (ids(cat_stock), ids(seller_stock), ids(band_stock),
              ids(kw_stock) == ids(live), stitched == ids(live),
              page1["total"]))

    # -- AC-AMAV5 scarcity dynamics move rows across the filter ---------
    before_live = ids(am.api_search(in_stock=True))
    am.purchase_api("usr:dave", l1, "ref-dave-l1")
    after_sold = ids(am.api_search(in_stock=True))
    moved_out = ids(am.api_search(in_stock=False))
    am.refund_api("usr:carol", carol_l1["purchase_id"], "suite refund")
    after_refund = ids(am.api_search(in_stock=True))
    am.restock_api("usr:dana", l2, 2)
    after_restock = ids(am.api_search(in_stock=True))
    unlimited_stock = am.api_search(in_stock=True)
    ordered_now = ids(am.api_search(in_stock=True))
    # after the restock the buyable set is {L1 10, L2 3, L3 5, L5 4}
    # in the default price-ascending order (L4 stays sold out at 7)
    ok5 = (l1 in before_live and l1 not in after_sold
           and l1 in moved_out
           and l1 in after_refund
           and l2 not in after_refund and l2 in after_restock
           and l3 in ids(unlimited_stock)
           and set(after_restock) == {l1, l2, l3, l5}
           and ordered_now == [l2, l5, l3, l1])
    record("AC-AMAV5", ok5,
           "sold_out_moves=%r refund_restores=%r restock_restores=%r"
           " unlimited=%r order_held=%r"
           % (l1 not in after_sold, l1 in after_refund,
              l2 in after_restock, l3 in ids(unlimited_stock),
              ordered_now == [l2, l5, l3, l1]))

    # -- AC-AMAV6 all five sort modes keep their order ------------------
    mode_results = {}
    ok6 = True
    live_now = set(ids(am.api_search(in_stock=True)))
    for mode in SORT_MODES:
        all_mode = am.api_search(sort=mode)
        kept = [row["listing_id"] for row in all_mode["listings"]
                if row["listing_id"] in live_now]
        filtered = ids(am.api_search(sort=mode, in_stock=True))
        mode_results[mode] = filtered == kept
        ok6 = ok6 and filtered == kept
    ok6 = ok6 and mode_results["price_asc"]
    record("AC-AMAV6", ok6, "modes=%r" % (mode_results,))

    # -- AC-AMAV7 honest empties and the retired-listing rule -----------
    no_match = am.api_search(category="nowhere", in_stock=True)
    am.delist_api("usr:frank", l5)
    hidden = am.api_search(in_stock=True)
    shown = am.api_search(in_stock=True, include_delisted=True)
    shown_rows = {row["listing_id"]: row for row in shown["listings"]}
    ok7 = (no_match["count"] == 0
           and no_match["listings"] == []
           and l5 not in ids(hidden)
           and l5 in ids(shown)
           and shown_rows[l5]["delisted"] is True
           and l4 in ids(am.api_search(in_stock=False,
                                      include_delisted=True)))
    record("AC-AMAV7", ok7,
           "empty=%d hidden_has_l5=%r shown_has_l5=%r delisted=%r"
           % (no_match["count"], l5 in ids(hidden), l5 in ids(shown),
              shown_rows.get(l5, {}).get("delisted")))

    # -- AC-AMAV8 pure read, cross-restart identity and wiring ----------
    # the identity view deliberately excludes the retired row: its
    # delisted_utc is a wall-clock stamp, so including it would make
    # the digest vary between processes rather than between restarts
    first = dumps(am.api_search(in_stock=True))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second = dumps(am.api_search(in_stock=True))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third = dumps(am.api_search(in_stock=True))
    tx_before = ledger_tx_ids(led)
    digests_before = market_digests(am)
    for _ in range(3):
        am.api_search(in_stock=True)
    tx_after = ledger_tx_ids(led)
    digests_after = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    with open(os.path.abspath(__file__), "rb") as handle:
        own = handle.read()
    ok8 = (first == second == third
           and tx_before == tx_after
           and digests_before == digests_after
           and shas_before == shas_after
           and "ledger-apimarket-searchstock" in runner_text
           and all(b < 128 for b in bytearray(own)))
    record("AC-AMAV8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r ascii=%r"
           % (hashlib.sha256(first.encode("utf-8")).hexdigest()[:16],
              first == second == third, tx_before == tx_after,
              digests_before == digests_after,
              shas_before == shas_after,
              "ledger-apimarket-searchstock" in runner_text,
              all(b < 128 for b in bytearray(own))))

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