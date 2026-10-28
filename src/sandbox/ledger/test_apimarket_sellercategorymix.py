"""Acceptance suite for the apimarket seller-side category revenue mix
face (BigDomain R2189; canon = the R2189 explore claim row, criteria
AC-SCM1..AC-SCM8 registered in that row BEFORE this code existed -
honesty law; the AC-SCM prefix, api_seller_category_mix,
test_apimarket_sellercategorymix and
ledger-apimarket-sellercategorymix were all git-grep zero-occupancy
anchored against HEAD 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_seller_category_mix. The seller
side answers "how many residents is my money hanging on"
(api_seller_concentration) but nothing answered "which categories is
my money actually coming from". This suite pins:

  - the sixteen-key envelope and eleven-key rows, honest empty first;
  - the purchase-side row authority, the total order
    (-net_revenue, -gross_revenue, category) with the unclassified
    bucket pinned LAST on a genuine tie, rank 1..n and a
    cumulative_share landing on exactly 1.0;
  - conservation and the refund law (a fully refunded category stays
    on the roll at zero weight, never deleted, never inflating a
    share);
  - the share law (rows sum to 1.0 inside 1e-9, None when the net
    total is not positive - never a fake zero), top1 as the head and
    an honest top3;
  - the herfindahl law (monopoly 10000.0, two equal buckets 5000.0)
    and the pareto law on integers including a bucket landing exactly
    on 80%;
  - the single _category_state seam (a revision moves one bucket in
    one step and reverting restores the bytes) and the scope law
    (market scope never benchmarks itself; a seller scope carries the
    market-wide herfindahl);
  - the gate (eight forms), the bare prefix, strict seller isolation
    and cross-face identity with api_category_demand and
    api_seller_concentration;
  - the pure-read law, cross-restart byte identity and the wiring.

Usage: python test_apimarket_sellercategorymix.py
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
    "scope", "dev_account", "purchase_count", "refund_count",
    "category_count", "refunded_categories", "gross_revenue",
    "refunded_tokens", "net_revenue", "top1_share", "top3_share",
    "herfindahl", "pareto_category_count", "market_herfindahl",
    "disclaimer", "rows"}

ROW_KEYS = {
    "category", "rank", "purchase_count", "refund_count",
    "net_purchase_count", "gross_revenue", "refunded_tokens",
    "net_revenue", "listing_count", "share", "cumulative_share"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


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


def cat_row(env, category):
    for row in env["rows"]:
        if row["category"] == category:
            return row
    raise AssertionError("category %r missing from rows" % (category,))


def seed_world(led, dk, am):
    """Market nets: tools 50 (dana 40 + lia 10), data 30 (dana 10 +
    lia 10 + gina 10), music 10 (nina), unclassified 10 (ivan), art 0
    (jade 30 gross fully refunded). Gross 130, refunded 30, net 100.

    The market order is tools 50, data 30, music 10, unclassified 10,
    art 0 - music and the unclassified bucket tie on BOTH net (10) and
    gross (10), so the pinned category order (unclassified LAST) is the
    only thing that decides the two. The cumulative net reaches exactly
    80% after the second bucket, so the integer pareto law must count
    it. At dana's scope the first bucket is exactly 80% (40 of 50).
    lia holds two equal buckets (5000.0 = 10000/2), gina a monopoly
    (10000.0), jade a zero-net category that must stay on the roll."""
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SCM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SCM-S",
                     "settlement")
    for who in ("bob", "erin", "jade", "kate", "nate"):
        fund(led, who)
    for dev in ("dana", "lia", "gina", "ivan", "jade", "nina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 40, False,
                        category="tools")["listing_id"]
    d2 = am.publish_api("usr:dana", "d2", "Dana Data API",
                        "dana data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    l1 = am.publish_api("usr:lia", "l1", "Lia Tools API",
                        "lia tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    l2 = am.publish_api("usr:lia", "l2", "Lia Data API",
                        "lia data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    u1 = am.publish_api("usr:ivan", "u1", "Ivan Plain API",
                        "ivan plain payloads", PAYLOAD, 10, False
                        )["listing_id"]
    j1 = am.publish_api("usr:jade", "j1", "Jade Art API",
                        "jade art payloads", PAYLOAD, 30, False,
                        category="art")["listing_id"]
    m1 = am.publish_api("usr:nina", "m1", "Nina Music API",
                        "nina music payloads", PAYLOAD, 10, False,
                        category="music")["listing_id"]

    am.purchase_api("usr:bob", t1, "ref-bob-t1")
    am.purchase_api("usr:bob", d2, "ref-bob-d2")
    am.purchase_api("usr:bob", m1, "ref-bob-m1")
    am.purchase_api("usr:erin", l1, "ref-erin-l1")
    am.purchase_api("usr:erin", l2, "ref-erin-l2")
    am.purchase_api("usr:kate", g1, "ref-kate-g1")
    am.purchase_api("usr:jade", u1, "ref-jade-u1")
    p_nate = am.purchase_api("usr:nate", j1, "ref-nate-j1")
    am.refund_api("usr:nate", p_nate["purchase_id"],
                  "listing did not match description")


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-sellercategorymix-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    seed_world(led, dk, am)

    # -- AC-SCM1 the contract, honest empty first ---------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-scm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_category_mix("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_seller_category_mix()
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in market["rows"])
    ok1 = (set(market.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
           and market["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and market["scope"] == "market"
           and market["dev_account"] is None
           and empty["scope"] == "seller"
           and empty["dev_account"] == "usr:nobody"
           and empty["purchase_count"] == 0
           and empty["refund_count"] == 0
           and empty["category_count"] == 0
           and empty["refunded_categories"] == 0
           and empty["gross_revenue"] == 0
           and empty["refunded_tokens"] == 0
           and empty["net_revenue"] == 0
           and empty["top1_share"] is None
           and empty["top3_share"] is None
           and empty["herfindahl"] is None
           and empty["pareto_category_count"] is None
           and empty["market_herfindahl"] is None
           and empty["rows"] == [])
    record("AC-SCM1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r"
           % (len(market), set(market.keys()) == ENVELOPE_KEYS,
              rows_ok, (len(empty["rows"]), empty["net_revenue"])))

    # -- AC-SCM2 purchase-side authority, order, pin and cumulative ---
    order = [row["category"] for row in market["rows"]]
    ranks = [row["rank"] for row in market["rows"]]
    cum = [row["cumulative_share"] for row in market["rows"]]
    ok2 = (order == ["tools", "data", "music", None, "art"]
           and ranks == [1, 2, 3, 4, 5]
           and cum == [0.5, 0.8, 0.9, 1.0, 1.0]
           and cat_row(market, None)["rank"] == 4
           and cat_row(market, "music")["rank"] == 3
           and cat_row(market, "music")["net_revenue"]
           == cat_row(market, None)["net_revenue"] == 10
           and cat_row(market, "music")["gross_revenue"]
           == cat_row(market, None)["gross_revenue"] == 10
           and all(row["category"] != "nope"
                   for row in market["rows"]))
    record("AC-SCM2", ok2,
           "order=%r ranks=%r cum=%r" % (order, ranks, cum))

    # -- AC-SCM3 conservation and the refund law ----------------------
    sum_p = sum(r["purchase_count"] for r in market["rows"])
    sum_r = sum(r["refund_count"] for r in market["rows"])
    sum_g = sum(r["gross_revenue"] for r in market["rows"])
    sum_rf = sum(r["refunded_tokens"] for r in market["rows"])
    art = cat_row(market, "art")
    ok3 = (sum_p == market["purchase_count"] == 8
           and sum_r == market["refund_count"] == 1
           and sum_g == market["gross_revenue"] == 130
           and sum_rf == market["refunded_tokens"] == 30
           and market["net_revenue"] == 100
           and market["net_revenue"] == sum_g - sum_rf
           and all(r["net_purchase_count"]
                   == r["purchase_count"] - r["refund_count"]
                   for r in market["rows"])
           and all(r["net_revenue"]
                   == r["gross_revenue"] - r["refunded_tokens"]
                   for r in market["rows"])
           and art is not None
           and art["purchase_count"] == 1
           and art["refund_count"] == 1
           and art["net_revenue"] == 0
           and art["share"] == 0.0
           and market["refunded_categories"] == 1)
    record("AC-SCM3", ok3,
           "sums=%r art=%r" % ((sum_p, sum_r, sum_g, sum_rf),
                               (art["purchase_count"],
                                art["refund_count"],
                                art["net_revenue"])))

    # -- AC-SCM4 the share law, top1 and an honest top3 ---------------
    share_sum = sum(r["share"] for r in market["rows"])
    dana = am.api_seller_category_mix("usr:dana")
    ok4 = (abs(share_sum - 1.0) < 1e-9
           and market["top1_share"] == 0.5
           and market["top3_share"] == 0.9
           and market["rows"][0]["share"] == 0.5
           and cat_row(market, None)["share"] == 0.1
           and dana["top1_share"] == 0.8
           and dana["top3_share"] == 1.0
           and abs(sum(r["share"] for r in dana["rows"]) - 1.0) < 1e-9)
    record("AC-SCM4", ok4,
           "sum=%.12f top1=%r top3=%r dana=%r"
           % (share_sum, market["top1_share"], market["top3_share"],
              (dana["top1_share"], dana["top3_share"])))

    # -- AC-SCM5 herfindahl and the integer pareto law ----------------
    gina = am.api_seller_category_mix("usr:gina")
    lia = am.api_seller_category_mix("usr:lia")
    ok5 = (market["herfindahl"] == 3600.0
           and market["pareto_category_count"] == 2
           and dana["herfindahl"] == 6800.0
           and dana["pareto_category_count"] == 1
           and lia["herfindahl"] == 5000.0
           and lia["pareto_category_count"] == 2
           and gina["herfindahl"] == 10000.0
           and gina["category_count"] == 1
           and market["market_herfindahl"] is None
           and dana["market_herfindahl"] == 3600.0
           and gina["market_herfindahl"] == 3600.0)
    record("AC-SCM5", ok5,
           "h=%r pareto=%r dana=%r lia=%r gina=%r bench=%r"
           % (market["herfindahl"], market["pareto_category_count"],
              (dana["herfindahl"], dana["pareto_category_count"]),
              (lia["herfindahl"], lia["pareto_category_count"]),
              (gina["herfindahl"], gina["category_count"]),
              (market["market_herfindahl"],
               dana["market_herfindahl"])))

    # -- AC-SCM6 the single category seam and the zero-weight law -----
    before = dumps(market)
    am.revise_category("usr:dana", t1_id(am), category="music")
    moved = am.api_seller_category_mix()
    am.revise_category("usr:dana", t1_id(am), category="tools")
    restored = am.api_seller_category_mix()
    zero = am.api_seller_category_mix("usr:jade")
    ok6 = (cat_row(moved, "music")["net_revenue"] == 50
           and cat_row(moved, "tools")["net_revenue"] == 10
           and cat_row(moved, "music")["purchase_count"] == 2
           and cat_row(moved, "tools")["purchase_count"] == 1
           and moved["net_revenue"] == 100
           and dumps(restored) == before
           and zero["category_count"] == 1
           and zero["rows"][0]["category"] == "art"
           and zero["rows"][0]["net_revenue"] == 0
           and zero["rows"][0]["share"] is None
           and zero["net_revenue"] == 0
           and zero["top1_share"] is None
           and zero["herfindahl"] is None
           and zero["pareto_category_count"] is None)
    record("AC-SCM6", ok6,
           "moved=%r restored=%r zero=%r"
           % ((cat_row(moved, "music")["net_revenue"],
               cat_row(moved, "tools")["net_revenue"]),
              dumps(restored) == before,
              (zero["category_count"], zero["net_revenue"],
               zero["top1_share"])))

    # -- AC-SCM7 gates, isolation and cross-face identity -------------
    gate_codes = []
    for bad in ("", " ", 123, [], {}, "dana", False, 0):
        try:
            am.api_seller_category_mix(bad)
        except Exception as exc:  # noqa: BLE001
            gate_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_seller_category_mix("usr:")
    demand = am.api_category_demand(include_uncategorized=True)
    dem_by = {row["category"]: row for row in demand["categories"]}
    cross_demand = all(
        dem_by[row["category"]]["purchase_count"]
        == row["purchase_count"]
        and dem_by[row["category"]]["refund_count"]
        == row["refund_count"]
        and dem_by[row["category"]]["gross_tokens"]
        == row["gross_revenue"]
        and dem_by[row["category"]]["refunded_tokens"]
        == row["refunded_tokens"]
        and dem_by[row["category"]]["net_gross_tokens"]
        == row["net_revenue"]
        for row in market["rows"])
    conc = am.api_seller_concentration("usr:dana")
    ivan = am.api_seller_category_mix("usr:ivan")
    ok7 = (gate_codes == ["E_AM_BAD_ACCOUNT"] * 8
           and prefix["dev_account"] == "usr:"
           and prefix["category_count"] == 0
           and prefix["net_revenue"] == 0
           and prefix["rows"] == []
           and cross_demand
           and (conc["purchase_count"], conc["refund_count"],
                conc["gross_revenue"], conc["net_revenue"])
           == (dana["purchase_count"], dana["refund_count"],
               dana["gross_revenue"], dana["net_revenue"])
           and [row["category"] for row in dana["rows"]]
           == ["tools", "data"]
           and all(row["category"] not in ("music", "art")
                   for row in dana["rows"])
           and ivan["category_count"] == 1
           and ivan["rows"][0]["category"] is None
           and ivan["herfindahl"] == 10000.0)
    record("AC-SCM7", ok7,
           "gate=%r prefix=%r cross_demand=%r dana=%r ivan=%r"
           % (gate_codes, (prefix["category_count"],
                           prefix["net_revenue"]), cross_demand,
              [(r["category"], r["net_revenue"])
               for r in dana["rows"]],
              [(r["category"], r["net_revenue"])
               for r in ivan["rows"]]))

    # -- AC-SCM8 pure read, cross-restart identity and the wiring -----
    final_market = dumps(am.api_seller_category_mix())
    final_dana = dumps(am.api_seller_category_mix("usr:dana"))
    final_ivan = dumps(am.api_seller_category_mix("usr:ivan"))
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    again = dumps(am.api_seller_category_mix())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_seller_category_mix())
    second_dana = dumps(am.api_seller_category_mix("usr:dana"))
    second_ivan = dumps(am.api_seller_category_mix("usr:ivan"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_seller_category_mix())
    third_dana = dumps(am.api_seller_category_mix("usr:dana"))
    third_ivan = dumps(am.api_seller_category_mix("usr:ivan"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_seller_category_mix()
        am.api_seller_category_mix("usr:dana")
        am.api_seller_category_mix("usr:ivan")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (again == final_market
           and final_market == second_market == third_market
           and final_dana == second_dana == third_dana
           and final_ivan == second_ivan == third_ivan
           and digests_before == digests_after == dig_b == dig_a
           and tx_before == tx_after == tx_b == tx_a
           and shas_before == shas_after
           and "ledger-apimarket-sellercategorymix" in runner_text)
    record("AC-SCM8", ok8,
           "sha16=%s stable=%r identical=%r frozen=%r tx_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final_market.encode("utf-8"))
              .hexdigest()[:16], again == final_market,
              final_market == second_market == third_market,
              digests_before == digests_after, tx_b == tx_a,
              shas_before == shas_after,
              "ledger-apimarket-sellercategorymix" in runner_text))

    close_stack(am, dk, metered, led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    verdict = "SUITE PASS %d/%d" % (passed, total)
    if passed != total:
        verdict = "SUITE FAIL %d/%d" % (passed, total)
    print(verdict, flush=True)
    return 0 if passed == total else 1


def t1_id(am):
    """Resolve dana's tools listing id without depending on the seed
    return values (the revision criterion needs it after the fact)."""
    with am._lock:
        row = am._conn.execute(
            "SELECT listing_id FROM apimarket_listings"
            " WHERE dev_account = ? AND listing_key = ?",
            ("usr:dana", "t1")).fetchone()
    return int(row[0])


if __name__ == "__main__":
    sys.exit(main())