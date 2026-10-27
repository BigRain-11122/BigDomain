"""Acceptance suite for the apimarket monthly buyer cohort face
(BigDomain R2173; criteria AC-MBC1..AC-MBC8 were registered in the
R2173 explore-queue row BEFORE this code existed - honesty law; the
AC-MBC prefix, api_market_buyer_cohort, new_buyer_count,
returning_buyer_count, this suite name and the ledger-apimarket-
buyercohort runner label were all git-grep zero-occupancy anchored
against HEAD 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_market_buyer_cohort. The months
face carries money and participant counts, the repeat face answers the
lifetime question only, and the per-buyer / per-seller faces are single
timelines - none of them separates a first-time buyer from a resident
who came back in a given month. This suite pins the new face:

  - the eleven-key envelope and the nine-key rows, honest empty first,
    and the no-argument contract (any argument is a TypeError, never a
    silent ignore);
  - the cohort law on the live reading (new == this month is the
    buyer's earliest net month; a buyer is counted new exactly once);
  - the refund recomputation law (the refunded purchase leaves the
    month, the buyer's cohort origin moves to the next net month, and
    the lifetime buyer set is unchanged);
  - the fully refunded month disappearing (net-purchase axis, the
    honest asymmetry against the cash-basis months face);
  - conservation (row sums against the envelope, new plus returning
    purchase counts, per-row buyer partitions) and the cross-face
    identity against api_market_months and api_repeat_purchase;
  - the degenerate worlds (same-month multi-purchase, all-refunded);
  - the pure-read law with frozen table digests and a constant
    ledger_tx set;
  - cross-restart byte identity over three instances plus product-file
    and runner wiring.

Usage: python test_apimarket_buyercohort.py
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
    "month_count", "purchase_count", "gross", "buyer_count",
    "repeat_buyer_count", "repeat_rate", "returning_purchase_count",
    "first_month", "last_month", "disclaimer", "months"}

ROW_KEYS = {
    "month", "purchase_count", "gross", "buyer_count",
    "new_buyer_count", "returning_buyer_count",
    "new_purchase_count", "returning_purchase_count",
    "avg_purchases_per_buyer"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


class Clock(object):
    """Deterministic stamp holder: the suite sets one explicit UTC
    string before each write so the month buckets are reproducible
    (module clock patched, restored in main's finally block)."""

    def __init__(self):
        self.value = "2026-01-10T00:00:00Z"

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


def by_month(env):
    return {row["month"]: row for row in env["months"]}


def seed_world(led, dk, am, clock):
    """dana owns d1 (10) and d2 (3); frank owns f1 (5) and f2 (4).

    Net purchases: bob d1 in JAN, bob d2 in FEB, dave f1 in FEB,
    bob f1 in MAR, carol f1 in MAR, erin d1 in MAR. carol's JAN d2
    purchase is refunded later, so her cohort origin moves to MAR and
    JAN loses a buyer without losing bob. gina buys f2 in APR and
    refunds it in APR, so APR is a fully refunded month and gina never
    exists on the net axis.
    """
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-MBC-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-MBC-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin", "gina"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True,
                        category="data")["listing_id"]
    f1 = am.publish_api("usr:frank", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 5,
                        False, category="tools")["listing_id"]
    f2 = am.publish_api("usr:frank", "loose-pack", "Loose Pack API",
                        "uncategorized payload pack", PAYLOAD, 4,
                        False)["listing_id"]
    clock.value = "2026-01-10T00:00:00Z"
    p1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")["purchase_id"]
    clock.value = "2026-01-15T00:00:00Z"
    p2 = am.purchase_api("usr:carol", d2, "ref-carol-d2")[
        "purchase_id"]
    clock.value = "2026-02-05T00:00:00Z"
    am.purchase_api("usr:bob", d2, "ref-bob-d2")
    clock.value = "2026-02-20T00:00:00Z"
    am.purchase_api("usr:dave", f1, "ref-dave-f1")
    clock.value = "2026-03-02T00:00:00Z"
    am.purchase_api("usr:bob", f1, "ref-bob-f1")
    clock.value = "2026-03-10T00:00:00Z"
    am.purchase_api("usr:carol", f1, "ref-carol-f1")
    clock.value = "2026-03-15T00:00:00Z"
    am.purchase_api("usr:erin", d1, "ref-erin-d1")
    clock.value = "2026-04-01T00:00:00Z"
    p8 = am.purchase_api("usr:gina", f2, "ref-gina-f2")[
        "purchase_id"]
    clock.value = "2026-04-05T00:00:00Z"
    am.refund_api("usr:gina", p8, "same-month refund")
    clock.value = "2026-04-06T00:00:00Z"
    am.refund_api("usr:carol", p2, "month-crossing refund")
    return d1, d2, f1, f2, p1, p2, p8


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyercohort-")
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
        return run(db_path, cfg, lobby_cfg, shas_before, clock, orig_now)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, shas_before, clock, orig_now):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, f1, f2, p1, p2, p8 = seed_world(led, dk, am, clock)

    # -- AC-MBC1 the contract, honest empty first, no arguments -------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-mbc-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_buyer_cohort()
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_market_buyer_cohort()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in market["months"])
    arg_forms = []
    for bad in ("", 1, None, [], {"x": 1}, False):
        try:
            am.api_market_buyer_cohort(bad)
            arg_forms.append("NO-ERROR:%r" % (bad,))
        except TypeError:
            arg_forms.append("TypeError")
    ok1 = (set(market.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and row_keys_ok
           and market["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["purchase_count"] == 0
           and empty["gross"] == 0
           and empty["buyer_count"] == 0
           and empty["repeat_buyer_count"] == 0
           and empty["repeat_rate"] is None
           and empty["returning_purchase_count"] == 0
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["months"] == []
           and arg_forms == ["TypeError"] * 6)
    record("AC-MBC1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r args=%r"
           % (len(market), set(market.keys()) == ENVELOPE_KEYS,
              row_keys_ok, empty["months"], arg_forms))

    # -- AC-MBC2 the cohort law on the live reading -------------------
    base = am.api_market_buyer_cohort()
    bm = by_month(base)
    ok2 = (base["month_count"] == 3
           and base["first_month"] == "2026-01"
           and base["last_month"] == "2026-03"
           and sorted(bm) == ["2026-01", "2026-02", "2026-03"]
           and bm["2026-01"]["buyer_count"] == 1
           and bm["2026-01"]["new_buyer_count"] == 1
           and bm["2026-01"]["returning_buyer_count"] == 0
           and bm["2026-01"]["purchase_count"] == 1
           and bm["2026-02"]["buyer_count"] == 2
           and bm["2026-02"]["new_buyer_count"] == 1
           and bm["2026-02"]["returning_buyer_count"] == 1
           and bm["2026-02"]["new_purchase_count"] == 1
           and bm["2026-02"]["returning_purchase_count"] == 1
           and bm["2026-03"]["buyer_count"] == 3
           and bm["2026-03"]["new_buyer_count"] == 2
           and bm["2026-03"]["returning_buyer_count"] == 1
           and bm["2026-03"]["new_purchase_count"] == 2
           and bm["2026-03"]["returning_purchase_count"] == 1
           and all(row["new_buyer_count"]
                   + row["returning_buyer_count"] == row["buyer_count"]
                   for row in base["months"]))
    record("AC-MBC2", ok2,
           "months=%r" % ([(row["month"], row["buyer_count"],
                            row["new_buyer_count"],
                            row["returning_buyer_count"])
                           for row in base["months"]],))

    # -- AC-MBC3 the refund recomputation law -------------------------
    # gina's April purchase and refund left nothing; carol's January
    # purchase is refunded, so January loses her and March gains her
    # as a new buyer while bob keeps his January origin.
    ok3 = ("2026-04" not in bm
           and "usr:gina" not in json.dumps(base)
           and base["purchase_count"] == 6
           and base["buyer_count"] == 4
           and base["repeat_buyer_count"] == 1
           and base["repeat_rate"] == 0.25
           and base["returning_purchase_count"] == 2
           and bm["2026-01"]["buyer_count"] == 1
           and bm["2026-03"]["new_buyer_count"] == 2
           and len(am.api_library("usr:carol")["purchases"]) == 2)
    record("AC-MBC3", ok3,
           "purchases=%d buyers=%d repeat=%d rate=%r ret_purch=%d"
           " jan_buyers=%d mar_new=%d carol_library=%d"
           % (base["purchase_count"], base["buyer_count"],
              base["repeat_buyer_count"], base["repeat_rate"],
              base["returning_purchase_count"],
              bm["2026-01"]["buyer_count"],
              bm["2026-03"]["new_buyer_count"],
              len(am.api_library("usr:carol")["purchases"])))

    # -- AC-MBC4 the fully refunded month disappears ------------------
    # (gina's April purchase plus its refund are entirely absent from
    # the gross axis as well, so the net authority is the only input)
    ok4 = (all(row["gross"] > 0 for row in base["months"])
           and sum(row["gross"] for row in base["months"]) == 38
           and all(row["purchase_count"] > 0
                   for row in base["months"]))
    record("AC-MBC4", ok4,
           "grosses=%r total=%d"
           % ([row["gross"] for row in base["months"]],
              sum(row["gross"] for row in base["months"])))

    # -- AC-MBC5 conservation and cross-face identity -----------------
    months_face = am.api_market_months()
    repeat_face = am.api_repeat_purchase()
    ok5 = (sum(row["purchase_count"] for row in base["months"])
           == base["purchase_count"]
                      == (months_face["lifetime_sales_count"]
                          - months_face["lifetime_refund_count"])
                      and sum(row["gross"] for row in base["months"]) == 38
                      and sum(row["gross"] for row in base["months"])
                      == (months_face["lifetime_gross"]
                          - months_face["lifetime_refunded"])
                      and sum(row["new_buyer_count"] for row in base["months"])
           == base["buyer_count"]
           and sum(row["new_purchase_count"] + row["returning_purchase_count"]
                   for row in base["months"]) == base["purchase_count"]
           and sum(row["returning_purchase_count"]
                   for row in base["months"])
           == base["returning_purchase_count"]
           and sum(row["returning_buyer_count"]
                   for row in base["months"]) == 2
           and repeat_face["buyer_count"] == base["buyer_count"]
           and repeat_face["repeat_buyer_count"]
           == base["repeat_buyer_count"]
           and [row["month"] for row in base["months"]]
           == sorted(set(row["month"] for row in base["months"]))
           and all(row["avg_purchases_per_buyer"]
                   == row["purchase_count"] / float(row["buyer_count"])
                   for row in base["months"]))
    record("AC-MBC5", ok5,
           "sum_p=%d env_p=%d months_face=%d sum_b=%d env_b=%d"
           " repeat=%r month_order=%r"
           % (sum(row["purchase_count"] for row in base["months"]),
              base["purchase_count"],
              months_face["lifetime_sales_count"],
              sum(row["new_buyer_count"] for row in base["months"]),
              base["buyer_count"],
              (repeat_face["repeat_buyer_count"],
               base["repeat_buyer_count"]),
              [row["month"] for row in base["months"]]))

    # -- AC-MBC6 the degenerate worlds --------------------------------
    one_tmp = tempfile.mkdtemp(prefix="apimarket-mbc-one-")
    o_led, o_metered, o_dk, _o_gate, o_am = build_stack(
        os.path.join(one_tmp, "ledger.db"), cfg, lobby_cfg)
    o_led.mint_to_pool("pool:reserve", 1000, "SETTLE-MBC1-A",
                       "settlement")
    o_led.mint_to_pool("pool:share", 1000, "SETTLE-MBC1-S",
                       "settlement")
    o_led.ensure_account("usr:bob", census_avatar_id="bob")
    o_led.adjust([("pool:reserve", "debit", 200),
                  ("usr:bob", "credit", 200)],
                 "manual:fund-bob-one", "suite funding bob")
    o_dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    o1 = o_am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                          "portfolio risk scan endpoint", PAYLOAD, 10,
                          False, category="data")["listing_id"]
    o2 = o_am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                          "daily macro data feed", PAYLOAD, 3, True,
                          category="data")["listing_id"]
    clock.value = "2026-05-04T00:00:00Z"
    o_p1 = o_am.purchase_api("usr:bob", o1, "ref-one-bob-1")[
        "purchase_id"]
    clock.value = "2026-05-20T00:00:00Z"
    o_p2 = o_am.purchase_api("usr:bob", o2, "ref-one-bob-2")[
        "purchase_id"]
    one = o_am.api_market_buyer_cohort()
    o_am.refund_api("usr:bob", o_p1, "single world refund")
    o_am.refund_api("usr:bob", o_p2, "second single world refund")
    gone = o_am.api_market_buyer_cohort()
    close_stack(o_am, o_dk, o_metered, o_led)
    one_row = one["months"][0] if one["months"] else {}
    ok6 = (one["month_count"] == 1
           and one["purchase_count"] == 2
           and one["buyer_count"] == 1
           and one["repeat_buyer_count"] == 0
           and one["repeat_rate"] == 0.0
           and one_row.get("new_buyer_count") == 1
           and one_row.get("returning_buyer_count") == 0
           and one_row.get("new_purchase_count") == 2
           and one_row.get("returning_purchase_count") == 0
           and one_row.get("avg_purchases_per_buyer") == 2.0
           and gone["months"] == []
           and gone["month_count"] == 0
           and gone["buyer_count"] == 0
           and gone["purchase_count"] == 0
           and gone["repeat_rate"] is None
           and gone["first_month"] is None)
    record("AC-MBC6", ok6,
           "one=%r all_refunded=%r"
           % ({k: one[k] for k in ("month_count", "purchase_count",
                                   "buyer_count",
                                   "repeat_buyer_count",
                                   "repeat_rate")},
              {k: gone[k] for k in ("month_count", "buyer_count",
                                    "purchase_count")}))

    # -- AC-MBC7 the pure-read law and determinism --------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    first = dumps(am.api_market_buyer_cohort())
    second = dumps(am.api_market_buyer_cohort())
    third = dumps(am.api_market_buyer_cohort())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (first == second == third
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-MBC7", ok7,
           "identical=%r frozen=%r tx=%r sha16=%s"
           % (first == second == third,
              digests_before == digests_after, tx_before == tx_after,
              hashlib.sha256(first.encode("utf-8")).hexdigest()[:16]))

    # -- AC-MBC8 cross-restart identity and the wiring ----------------
    final = dumps(am.api_market_buyer_cohort())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_market_buyer_cohort())
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_market_buyer_cohort())
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_market_buyer_cohort()
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (final == second_market == third_market
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-buyercohort" in runner_text)
    record("AC-MBC8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_market == third_market, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-buyercohort" in runner_text))

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