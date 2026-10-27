"""Acceptance suite for the apimarket category refund-months face
(BigDomain R2163; canon = the R2149 explore seed claimed in R2163,
criteria AC-CRM1..AC-CRM8 registered in that claim note BEFORE this
code existed - honesty law; the AC-CRM prefix, api_category_refund_months,
this suite name and the ledger-apimarket-categoryrefundmonths runner
label were git-grep anchored against HEAD 2026-10-27 with the code face
at zero occupancy, rc=1 for the suite and runner labels and the AC-CRM /
face-name text occupancy coming only from the seed row itself).

Face under proof: APIMarketFace.api_category_refund_months. The catalog
demand face sums a category over its whole life, the market months face
sums the whole market per month and the refund register lists refunds
one by one - none of them answers "is THIS category's refund load
abnormal THIS month". This suite pins the new face:

  - the fourteen-key envelope, the eight-key category rows and the
    six-key month rows, honest empty world first;
  - the cash-basis bucketing law (a sale books in the UTC month of its
    purchased_utc, a refund in the UTC month of its refunded_utc, and a
    refund never rewrites the month its sale landed in);
  - refund authority (a refund-only month carries zero trade next to a
    positive refund instead of inventing a sale) and the honest None
    refund_rate wherever nothing settled;
  - conservation across categories and months plus the global
    identities;
  - the two different extremes (worst rate among months that settled
    something, top refunded amount over all months, ties to earliest);
  - the one effective-category seam moving gross and refunded together;
  - the bool-only gate, the pure-read law and cross-restart byte
    identity, and the runner wiring.

Usage: python test_apimarket_categoryrefundmonths.py
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
    "include_uncategorized", "category_count", "month_count",
    "trade_count", "gross", "refund_count", "refunded", "net",
    "refund_rate", "categories", "worst_refund_month",
    "worst_refund_rate", "top_refund_month", "disclaimer"}

ROW_KEYS = {
    "category", "gross", "refund_count", "refunded", "net",
    "refund_rate", "months", "trade_count"}

MONTH_KEYS = {
    "month", "gross", "refund_count", "refunded", "net", "refund_rate"}

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
        self.value = "2026-08-31T23:59:59Z"

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


def raw_totals(am):
    """Ground truth read straight from the market tables, never from
    the face under proof (so conservation is a real cross-check)."""
    conn = sqlite3.connect(am.db_path)
    gross, sales = conn.execute(
        "SELECT COALESCE(SUM(price_paid),0), COUNT(*)"
        " FROM apimarket_purchases").fetchone()
    refunded, refunds = conn.execute(
        "SELECT COALESCE(SUM(amount),0), COUNT(*)"
        " FROM apimarket_refunds").fetchone()
    conn.close()
    return int(gross), int(sales), int(refunded), int(refunds)


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


def seed_world(led, dk, am, clock):
    """dana owns d1 ("data", 10) and d2 ("data", 3); frank owns d3
    ("tools", 5) and d4 (uncategorized, 4).

    Sales: bob d1 in AUG (23:59:59, the last second of the month),
    carol d1 in SEP (00:00:00, the first second of the next month),
    bob d2 in SEP, erin d3 in SEP, dave d4 in OCT, faye d3 in OCT
    (a buyer cannot buy the same listing twice, so the October tools
    sale needs its own buyer). Refunds: bob p1 in OCT, faye's OCT d3
    in OCT, then three NOV
    refunds (carol p2, bob p3, dave p5) so NOV is a refund-only month
    that outranks OCT on amount while settling nothing - the two
    extremes must therefore dissociate.
    """
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-CRM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-CRM-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin", "faye"):
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
    d3 = am.publish_api("usr:frank", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 5,
                        False, category="tools")["listing_id"]
    d4 = am.publish_api("usr:frank", "loose-pack", "Loose Pack API",
                        "uncategorized payload pack", PAYLOAD, 4,
                        False)["listing_id"]
    clock.value = "2026-08-31T23:59:59Z"
    p1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")["purchase_id"]
    clock.value = "2026-09-01T00:00:00Z"
    p2 = am.purchase_api("usr:carol", d1, "ref-carol-d1")[
        "purchase_id"]
    clock.value = "2026-09-15T12:00:00Z"
    p3 = am.purchase_api("usr:bob", d2, "ref-bob-d2")["purchase_id"]
    clock.value = "2026-09-20T08:30:00Z"
    am.purchase_api("usr:erin", d3, "ref-erin-d3-sep")
    clock.value = "2026-10-02T00:00:00Z"
    p5 = am.purchase_api("usr:dave", d4, "ref-dave-d4")["purchase_id"]
    clock.value = "2026-10-05T00:00:00Z"
    p6 = am.purchase_api("usr:faye", d3, "ref-faye-d3-oct")[
        "purchase_id"]
    clock.value = "2026-10-10T00:00:00Z"
    am.refund_api("usr:bob", p1, "month-crossing data refund")
    clock.value = "2026-10-12T00:00:00Z"
    am.refund_api("usr:faye", p6, "same-month tools refund")
    clock.value = "2026-11-01T00:00:00Z"
    am.refund_api("usr:carol", p2, "late data refund")
    clock.value = "2026-11-03T00:00:00Z"
    am.refund_api("usr:bob", p3, "late data refund two")
    clock.value = "2026-11-05T00:00:00Z"
    am.refund_api("usr:dave", p5, "late uncategorized refund")
    return d1, d2, d3, d4


def by_cat(env):
    return {row["category"]: row for row in env["categories"]}


def by_month(months):
    return {m["month"]: m for m in months}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-categoryrefundmonths-")
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
    d1, d2, d3, d4 = seed_world(led, dk, am, clock)

    env = am.api_category_refund_months()
    cats = by_cat(env)
    data = cats["data"]
    tools = cats["tools"]
    unc = cats[None]
    order = [row["category"] for row in env["categories"]]

    # -- AC-CRM1 contract, honest empty world first --------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-crm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_category_refund_months()
    empty_strict = e_am.api_category_refund_months(False)
    close_stack(e_am, e_dk, e_metered, e_led)
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in env["categories"])
    month_keys_ok = all(set(m.keys()) == MONTH_KEYS
                        for row in env["categories"]
                        for m in row["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and row_keys_ok and month_keys_ok
           and env["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["include_uncategorized"] is True
           and empty["category_count"] == 0
           and empty["month_count"] == 0
           and empty["trade_count"] == 0
           and empty["gross"] == 0
           and empty["refund_count"] == 0
           and empty["refunded"] == 0
           and empty["net"] == 0
           and empty["refund_rate"] is None
           and empty["worst_refund_month"] is None
           and empty["worst_refund_rate"] is None
           and empty["top_refund_month"] is None
           and empty["categories"] == []
           and empty_strict["categories"] == []
           and empty_strict["refund_rate"] is None)
    record("AC-CRM1", ok1,
           "env_keys=14 exact=%r row_keys=%r month_keys=%r cats=%d"
           " empty_cats=%d"
           % (set(env.keys()) == ENVELOPE_KEYS, row_keys_ok,
              month_keys_ok, len(env["categories"]),
              len(empty["categories"])))

    # -- AC-CRM2 cash-basis bucketing and the frozen sale month --------
    dm = by_month(data["months"])
    ok2 = ([m["month"] for m in data["months"]]
           == ["2026-08", "2026-09", "2026-10", "2026-11"]
           and dm["2026-08"]["gross"] == 10
           and dm["2026-08"]["refund_count"] == 0
           and dm["2026-08"]["refunded"] == 0
           and dm["2026-09"]["gross"] == 13
           and dm["2026-09"]["refund_count"] == 0
           and dm["2026-10"]["gross"] == 0
           and dm["2026-10"]["gross"] == 0
           and dm["2026-10"]["refund_count"] == 1
           and dm["2026-10"]["refunded"] == 10
           and dm["2026-10"]["net"] == -10
           and dm["2026-11"]["refund_count"] == 2
           and dm["2026-11"]["refunded"] == 13
           and dm["2026-11"]["gross"] == 0
           and dm["2026-11"]["net"] == -13)
    record("AC-CRM2", ok2,
           "data_months=%r"
           % [(m["month"], m["gross"], m["refunded"], m["net"])
              for m in data["months"]])

    # -- AC-CRM3 effective-category seam -------------------------------
    before = dumps(env)
    am.revise_category("usr:dana", d1, "tools")
    moved = am.api_category_refund_months()
    moved_cats = by_cat(moved)
    ok3 = (moved_cats["tools"]["gross"] == 30
           and moved_cats["tools"]["refunded"] == 25
           and moved_cats["tools"]["refund_count"] == 3
           and moved_cats["tools"]["trade_count"] == 4
           and moved_cats["data"]["gross"] == 3
           and moved_cats["data"]["refunded"] == 3
           and moved_cats["data"]["refund_count"] == 1
           and set(moved_cats) == {"data", "tools", None}
           and moved["gross"] == env["gross"]
           and moved["refunded"] == env["refunded"])
    am.revise_category("usr:dana", d1, "data")
    restored = am.api_category_refund_months()
    ok3 = ok3 and dumps(restored) == before
    record("AC-CRM3", ok3,
           "tools_gross=%d->%d tools_refunded=%d->%d roundtrip=%r"
           % (tools["gross"], moved_cats["tools"]["gross"],
              tools["refunded"], moved_cats["tools"]["refunded"],
              dumps(restored) == before))

    # -- AC-CRM4 conservation and the global identities ----------------
    gross_raw, sales_raw, refunded_raw, refunds_raw = raw_totals(am)
    per_month_gross = {}
    for row in env["categories"]:
        for m in row["months"]:
            per_month_gross[m["month"]] = (per_month_gross.get(
                m["month"], 0) + m["gross"])
    ok4 = (env["gross"] == gross_raw
           and env["refunded"] == refunded_raw
           and env["trade_count"] == sales_raw
           and env["refund_count"] == refunds_raw
           and env["net"] == env["gross"] - env["refunded"]
           and env["refund_rate"] == float(env["refunded"])
           / env["gross"]
           and sum(row["gross"] for row in env["categories"])
           == env["gross"]
           and sum(row["refunded"] for row in env["categories"])
           == env["refunded"]
           and sum(row["refund_count"] for row in env["categories"])
           == env["refund_count"]
           and sum(row["trade_count"] for row in env["categories"])
           == env["trade_count"]
           and all(sum(m["gross"] for m in row["months"]) == row["gross"]
                   for row in env["categories"])
           and all(sum(m["refunded"] for m in row["months"])
                   == row["refunded"]
                   for row in env["categories"])
           and all(m["net"] == m["gross"] - m["refunded"]
                   for row in env["categories"]
                   for m in row["months"])
           and all(row["refund_rate"]
                   == (float(row["refunded"]) / row["gross"]
                       if row["gross"] else None)
                   for row in env["categories"])
           and sorted(per_month_gross) == ["2026-08", "2026-09",
                                           "2026-10", "2026-11"]
           and env["month_count"] == 4
           and env["category_count"] == 3)
    record("AC-CRM4", ok4,
           "gross=%d/%d refunded=%d/%d trades=%d/%d refunds=%d/%d"
           " months=%d cats=%d"
           % (env["gross"], gross_raw, env["refunded"], refunded_raw,
              env["trade_count"], sales_raw, env["refund_count"],
              refunds_raw, env["month_count"], env["category_count"]))

    # -- AC-CRM5 refund authority, no invented sales -------------------
    ok5 = (dm["2026-10"]["gross"] == 0
           and dm["2026-10"]["refund_count"] == 1
           and dm["2026-11"]["gross"] == 0
           and dm["2026-11"]["refund_count"] == 2
           and dm["2026-10"]["refund_rate"] is None
           and dm["2026-11"]["refund_rate"] is None
           and unc["gross"] == 4
           and unc["refunded"] == 4
           and unc["trade_count"] == 1
           and unc["net"] == 0
           and unc["months"][0]["month"] == "2026-10"
           and unc["months"][0]["refund_count"] == 0)
    record("AC-CRM5", ok5,
           "oct=%r nov=%r uncat=%r"
           % ((dm["2026-10"]["gross"],
               dm["2026-10"]["refund_count"],
               dm["2026-10"]["refund_rate"]),
              (dm["2026-11"]["gross"],
               dm["2026-11"]["refund_count"],
               dm["2026-11"]["refund_rate"]),
              (unc["gross"], unc["refunded"], unc["trade_count"])))

    # -- AC-CRM6 the two dissociated extremes and the ordering ---------
    ok6 = (order == ["data", "tools", None]
           and env["worst_refund_month"] == "2026-10"
           and env["worst_refund_rate"] == 15.0 / 9.0
           and env["top_refund_month"] == "2026-11"
           and tools["refund_rate"] == 0.5
           and data["refund_rate"] == 1.0
           and unc["refund_rate"] == 1.0
           and [m["month"] for m in tools["months"]]
           == ["2026-09", "2026-10"]
           and tools["months"][1]["refund_rate"] == 1.0
           and data["months"][0]["refund_rate"] == 0.0)
    record("AC-CRM6", ok6,
           "order=%r worst=%r@%r top=%r"
           % (order, env["worst_refund_month"],
              env["worst_refund_rate"], env["top_refund_month"]))

    # -- AC-CRM7 the bool-only gate and the pure-read law --------------
    digests_before = frozen_digests(am)
    tx_before = ledger_tx_ids(led)
    codes = []
    for bad in (0, 1, "", "yes", None, [], {"a": 1}, 1.0):
        try:
            am.api_category_refund_months(bad)
            codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            codes.append(getattr(exc, "code", "?"))
    strict = am.api_category_refund_months(False)
    first = dumps(am.api_category_refund_months())
    second = dumps(am.api_category_refund_months())
    digests_after = frozen_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (codes == ["E_AM_BAD_ARGS"] * 8
           and strict["include_uncategorized"] is False
           and strict["category_count"] == 2
           and set(by_cat(strict)) == {"data", "tools"}
           and strict["gross"] == 33
           and strict["refunded"] == 28
           and strict["trade_count"] == 5
           and strict["month_count"] == 4
           and first == second
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-CRM7", ok7,
           "codes=%r strict=%r repeated=%r frozen=%r tx=%r"
           % (codes, (strict["category_count"], strict["gross"],
                      strict["refunded"]),
              first == second, digests_before == digests_after,
              tx_before == tx_after))

    # -- AC-CRM8 cross-restart identity and the wiring -----------------
    final = dumps(am.api_category_refund_months())
    final_strict = dumps(am.api_category_refund_months(False))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_env = dumps(am.api_category_refund_months())
    second_strict = dumps(am.api_category_refund_months(False))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_env = dumps(am.api_category_refund_months())
    tx_b = ledger_tx_ids(led)
    dig_b = frozen_digests(am)
    for _ in range(3):
        am.api_category_refund_months()
        am.api_category_refund_months(False)
    tx_a = ledger_tx_ids(led)
    dig_a = frozen_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (final == second_env == third_env
           and final_strict == second_strict
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-categoryrefundmonths" in runner_text)
    record("AC-CRM8", ok8,
           "sha16=%s identical=%r strict=%r tx_equal=%r frozen=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_env == third_env,
              final_strict == second_strict, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-categoryrefundmonths" in runner_text))

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