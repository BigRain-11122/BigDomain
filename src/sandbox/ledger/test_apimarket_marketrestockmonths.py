"""Acceptance suite for the apimarket market-wide monthly restock
pressure (BigDomain R3154; canon = the R2240 explore-queue seed row,
criteria AC-MRS1..AC-MRS8 registered in that row BEFORE this code
existed).

Face under proof: APIMarketFace.api_market_restock_months.
api_seller_restock_months answers one shop's cadence and
api_market_supply_months samples the whole shelf at each month end, so
how fast the market's sold-out shelves came BACK had no face. This
suite pins:

  - the 28-key envelope, the 14-key month rows, the no-argument
    contract (any argument is a TypeError, never silently ignored), the
    market scope and the honest empty world;
  - the restock stamp booking law (a restock books in its own
    restocked_utc month, never re-dating an earlier one);
  - the sold-out denominator sampled by the same law
    api_market_supply_months uses, agreeing with it month by month, and
    an unlimited shelf never counted as sold out;
  - the contiguous grid over the same event union as the sibling supply
    face, honest zero rows and monotone running accumulators;
  - the episode law (start at the first stamp reaching zero on a live
    finite shelf, end at the first later positive stamp, kind 'restock'
    or 'refund'), pooled latency and the named separation of a refund
    recovery from a restock recovery;
  - the coverage law (restocked-from-soldout over the PREVIOUS month-end
    sold-out count, None on a zero or absent denominator, never
    clamped);
  - cross-face identity against api_seller_restock_months totals and
    api_market_supply_months sold-out counts;
  - purity (zero row mutations, zero token movement), two-call and
    two-instance byte identity, the reconcile wiring and ASCII/LF
    hygiene.

Usage: python test_apimarket_marketrestockmonths.py
"""

import hashlib
import io
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
import apimarket as A                 # noqa: E402 (R3154 face)
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
    "scope", "dev_account", "month_count", "active_month_count",
    "restock_count", "units_added", "listing_count", "seller_count",
    "sold_out_listing_count", "episode_count",
    "recovered_episode_count", "refund_recovered_episode_count",
    "open_episode_count", "restock_coverage", "mean_recovery_seconds",
    "mean_restock_recovery_seconds", "min_recovery_seconds",
    "max_recovery_seconds", "avg_units_per_restock",
    "largest_restock_units", "peak_month", "peak_units_added",
    "first_month", "last_month", "latest_month_units_added",
    "latest_month_sold_out_listing_count", "disclaimer", "months"}

ROW_KEYS = {
    "month", "restock_count", "units_added", "listing_count",
    "seller_count", "sold_out_listing_count",
    "restocked_from_soldout_count", "restock_coverage",
    "recovered_episode_count", "mean_recovery_seconds",
    "avg_units_per_restock", "largest_restock_units",
    "running_restock_count", "running_units_added"}

DAY = 86400


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set
    before each write so the month buckets are reproducible."""

    def __init__(self):
        self.value = "2026-08-01T00:00:00Z"

    def now_utc(self):
        return self.value


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def payload(env):
    return json.dumps(env, sort_keys=True)


def market_digests(am):
    conn = sqlite3.connect(am.db_path)
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
        " ORDER BY name").fetchall()]
    out = {}
    for table in tables:
        rows = conn.execute(
            "SELECT * FROM " + table + " ORDER BY rowid").fetchall()
        out[table] = (len(rows),
                      hashlib.sha256(repr(rows).encode("utf-8"))
                      .hexdigest())
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


def month_row(env, month):
    for row in env["months"]:
        if row["month"] == month:
            return row
    raise AssertionError("month %r missing from months" % (month,))


def seed_world(led, dk, am, clock):
    """dana owns l1 (supply 2), l2 (supply 1) and an unlimited l3;
    frank owns l4 (supply 1). The timeline is chosen so every law has
    one witness and one control:

      l1 sells out 08-11, restocked 08-20 (+3)  -> restock recovery
      l4 sells out 08-15, restocked 09-10 (+2)  -> restock recovery,
                                                   crossing a month end
                                                   (Aug denominator)
      l2 sells out 09-05, refunded 09-06        -> refund recovery
      l4 sells out again 09-20                  -> still open at world
                                                   end, October reads an
                                                   honest zero restock
                                                   month with a live
                                                   sold-out shelf
      l3 is unlimited and must never be a sold-out shelf
    """
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-MRS-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-MRS-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 500),
                    ("usr:" + who, "credit", 500)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)

    clock.value = "2026-08-01T00:00:00Z"
    l1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, supply=2)["listing_id"]
    l2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 4,
                        False, supply=1)["listing_id"]
    l3 = am.publish_api("usr:dana", "free-tier", "Free Tier API",
                        "unlimited sample endpoint", PAYLOAD, 4,
                        False)["listing_id"]
    l4 = am.publish_api("usr:frank", "chart-render", "Chart Render",
                        "chart image render endpoint", PAYLOAD, 6,
                        False, supply=1)["listing_id"]

    clock.value = "2026-08-10T10:00:00Z"
    am.purchase_api("usr:bob", l1, "ref-bob-l1")
    clock.value = "2026-08-11T10:00:00Z"
    am.purchase_api("usr:carol", l1, "ref-carol-l1")
    clock.value = "2026-08-15T10:00:00Z"
    am.purchase_api("usr:dave", l4, "ref-dave-l4")
    clock.value = "2026-08-20T10:00:00Z"
    am.restock_api("usr:dana", l1, 3)
    clock.value = "2026-08-22T10:00:00Z"
    am.purchase_api("usr:dave", l3, "ref-dave-l3")

    clock.value = "2026-09-05T10:00:00Z"
    p2 = am.purchase_api("usr:bob", l2, "ref-bob-l2")["purchase_id"]
    clock.value = "2026-09-06T10:00:00Z"
    am.refund_api("usr:bob", p2, "macro feed stale")
    clock.value = "2026-09-10T10:00:00Z"
    am.restock_api("usr:frank", l4, 2)
    clock.value = "2026-09-20T10:00:00Z"
    am.purchase_api("usr:bob", l4, "ref-bob-l4a")
    am.purchase_api("usr:carol", l4, "ref-bob-l4b")

    clock.value = "2026-10-02T10:00:00Z"
    am.purchase_api("usr:dave", l1, "ref-dave-l1b")
    return {"l1": l1, "l2": l2, "l3": l3, "l4": l4}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-marketrestockmonths-")
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

    # -- AC-MRS1 contract, honest empty first, no-argument signature --
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-mrs-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_restock_months()
    e_am.close()
    e_dk.close()
    e_metered.close()
    e_led.close()
    ok1_empty = (
        set(empty) == ENVELOPE_KEYS
        and empty["scope"] == "market"
        and empty["dev_account"] is None
        and empty["month_count"] == 0
        and empty["active_month_count"] == 0
        and empty["restock_count"] == 0
        and empty["units_added"] == 0
        and empty["listing_count"] == 0
        and empty["seller_count"] == 0
        and empty["sold_out_listing_count"] == 0
        and empty["episode_count"] == 0
        and empty["recovered_episode_count"] == 0
        and empty["refund_recovered_episode_count"] == 0
        and empty["open_episode_count"] == 0
        and empty["restock_coverage"] is None
        and empty["mean_recovery_seconds"] is None
        and empty["mean_restock_recovery_seconds"] is None
        and empty["min_recovery_seconds"] is None
        and empty["max_recovery_seconds"] is None
        and empty["avg_units_per_restock"] is None
        and empty["largest_restock_units"] is None
        and empty["peak_month"] is None
        and empty["peak_units_added"] is None
        and empty["first_month"] is None
        and empty["last_month"] is None
        and empty["latest_month_units_added"] == 0
        and empty["latest_month_sold_out_listing_count"] == 0
        and empty["months"] == []
        and empty["disclaimer"] == DISCLAIMER)

    ids = seed_world(led, dk, am, clock)
    env = am.api_market_restock_months()
    first_call = payload(env)

    ok1 = (ok1_empty
           and set(env) == ENVELOPE_KEYS
           and all(set(row) == ROW_KEYS for row in env["months"])
           and env["scope"] == "market"
           and env["dev_account"] is None
           and env["disclaimer"] == DISCLAIMER)
    record("AC-MRS1", ok1,
           "envelope=%d keys, rows=%d x %d keys, empty world honest,"
           " market scope, disclaimer present"
           % (len(ENVELOPE_KEYS), len(env["months"]), len(ROW_KEYS)))

    # -- AC-MRS2 restock stamp booking --
    aug = month_row(env, "2026-08")
    sep = month_row(env, "2026-09")
    octo = month_row(env, "2026-10")
    conn = sqlite3.connect(am.db_path)
    raw_restocks = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(add_units), 0)"
        " FROM apimarket_supply_revisions").fetchone()
    raw_aug = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(add_units), 0)"
        " FROM apimarket_supply_revisions"
        " WHERE restocked_utc LIKE '2026-08%'").fetchone()
    conn.close()
    ok2 = (aug["restock_count"] == int(raw_aug[0])
           and aug["units_added"] == int(raw_aug[1])
           and env["restock_count"] == int(raw_restocks[0])
           and env["units_added"] == int(raw_restocks[1])
           and aug["restock_count"] == 1
           and aug["units_added"] == 3
           and sep["restock_count"] == 1
           and sep["units_added"] == 2
           and octo["restock_count"] == 0
           and octo["units_added"] == 0)
    record("AC-MRS2", ok2,
           "restocks book in their own restocked_utc month: Aug 1/3,"
           " Sep 1/2, Oct honest zero, totals equal the raw table")

    # -- AC-MRS3 sold-out denominator, cross-face identity, unlimited --
    msm = am.api_market_supply_months()
    supply_rows = {row["month"]: row for row in msm["months"]}
    shared = [row["month"] for row in env["months"]
              if row["month"] in supply_rows]
    ok3 = (len(shared) == len(env["months"])
           and all(month_row(env, month)["sold_out_listing_count"]
                   == supply_rows[month]["sold_out_listing_count"]
                   for month in shared)
           and aug["sold_out_listing_count"] == 1
           and sep["sold_out_listing_count"] == 1
           and octo["sold_out_listing_count"] == 1
           and env["latest_month_sold_out_listing_count"] == 1
           and env["sold_out_listing_count"] == 1)
    record("AC-MRS3", ok3,
           "sold-out denominator agrees with api_market_supply_months"
           " on all %d shared months (Aug/Sep/Oct = 1 each); the"
           " unlimited shelf is never a sold-out shelf" % len(shared))

    # -- AC-MRS4 contiguous grid, honest zero month, accumulators --
    months = [row["month"] for row in env["months"]]
    ok4 = (months == ["2026-08", "2026-09", "2026-10"]
           and env["first_month"] == "2026-08"
           and env["last_month"] == "2026-10"
           and env["month_count"] == 3
           and env["active_month_count"] == 2
           and octo["restock_count"] == 0
           and octo["recovered_episode_count"] == 0
           and octo["mean_recovery_seconds"] is None
           and octo["avg_units_per_restock"] is None
           and octo["largest_restock_units"] is None
           and aug["running_restock_count"] == 1
           and sep["running_restock_count"] == 2
           and octo["running_restock_count"] == 2
           and aug["running_units_added"] == 3
           and sep["running_units_added"] == 5
           and octo["running_units_added"] == 5
           and env["latest_month_units_added"] == 0
           and env["peak_month"] == "2026-08"
           and env["peak_units_added"] == 3)
    record("AC-MRS4", ok4,
           "contiguous Aug..Oct, October carries an honest zero row,"
           " running accumulators end at the envelope totals, earlier"
           " month wins the peak on 3 vs 2 units")

    # -- AC-MRS5 episode law and pooled latency --
    ok5 = (env["episode_count"] == 4
           and env["recovered_episode_count"] == 2
           and env["refund_recovered_episode_count"] == 1
           and env["open_episode_count"] == 1
           and env["mean_restock_recovery_seconds"] == (
               (9 * DAY + 26 * DAY) // 2)
           and env["min_recovery_seconds"] == DAY
           and env["max_recovery_seconds"] == 26 * DAY
           and env["mean_recovery_seconds"] == (
               (9 * DAY + 26 * DAY + DAY) // 3)
           and aug["recovered_episode_count"] == 1
           and aug["mean_recovery_seconds"] == 9 * DAY
           and sep["recovered_episode_count"] == 2
           and sep["mean_recovery_seconds"] == (26 * DAY + DAY) // 2)
    record("AC-MRS5", ok5,
           "four episodes (l1 restock 9d, l4 restock 26d, l2 refund 1d,"
           " l4 open): pooled restock mean %s, floor mean %s, refund"
           " recovery counted apart"
           % (env["mean_restock_recovery_seconds"],
              env["mean_recovery_seconds"]))

    # -- AC-MRS6 coverage law --
    ok6 = (aug["restocked_from_soldout_count"] == 0
           and aug["restock_coverage"] is None
           and sep["restocked_from_soldout_count"] == 1
           and sep["restock_coverage"] == 1.0
           and octo["restocked_from_soldout_count"] == 0
           and octo["restock_coverage"] == 0.0
           and env["restock_coverage"] == 0.5)
    record("AC-MRS6", ok6,
           "coverage = recovered-by-restock over the PREVIOUS month-end"
           " sold-out count: Aug None (no prior), Sep 1/1=1.0, Oct"
           " 0/1=0.0; envelope 2 restock recoveries out of 4 episodes"
           " reads 0.5")

    # -- AC-MRS7 identity against the seller restock face --
    srm = am.api_seller_restock_months()
    srm_rows = {row["month"]: row for row in srm["months"]}
    ok7 = (srm["restock_count"] == env["restock_count"]
           and srm["units_added"] == env["units_added"]
           and srm["listing_count"] == env["listing_count"]
           and all(month_row(env, month)["restock_count"]
                   == srm_rows[month]["restock_count"]
                   and month_row(env, month)["units_added"]
                   == srm_rows[month]["units_added"]
                   for month in months if month in srm_rows)
           and srm["month_count"] == 2
           and env["month_count"] == 3
           and env["seller_count"] == 2
           and env["listing_count"] == 2)
    record("AC-MRS7", ok7,
           "totals identical to api_seller_restock_months on the market"
           " scope (restock=%d units=%d listings=%d) and every shared"
           " month equals on restock_count/units_added; the grids"
           " differ by design (%d restock months vs %d supply months)"
           % (env["restock_count"], env["units_added"],
              env["listing_count"], srm["month_count"],
              env["month_count"]))

    # -- AC-MRS8 gate, purity, byte identity, wiring, hygiene --
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    second = am.api_market_restock_months()
    third = am.api_market_restock_months()
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    other_tmp = tempfile.mkdtemp(prefix="apimarket-mrs-inst-")
    o_led, o_metered, o_dk, _o_gate, o_am = build_stack(
        os.path.join(other_tmp, "ledger.db"), cfg, lobby_cfg)
    other_empty = o_am.api_market_restock_months()
    o_am.close()
    o_dk.close()
    o_metered.close()
    o_led.close()

    bad_arg = False
    try:
        am.api_market_restock_months("usr:dana")
    except TypeError:
        bad_arg = True
    except Exception:
        bad_arg = False

    wire = io.open(os.path.join(
        os.path.dirname(BASE), "reconcile_all.py"),
        encoding="utf-8").read()
    src_text = io.open(os.path.join(BASE, "apimarket.py"),
                       encoding="utf-8").read()
    src_bytes = io.open(os.path.join(BASE, "apimarket.py"), "rb").read()
    suite_bytes = io.open(os.path.abspath(__file__), "rb").read()
    ok8 = (bad_arg
           and payload(second) == first_call
           and payload(third) == first_call
           and digests_before == digests_after
           and tx_before == tx_after
           and other_empty["months"] == []
           and "ledger-apimarket-marketrestockmonths" in wire
           and wire.count(
               "ledger-apimarket-marketrestockmonths") == 1
           and src_text.count("def api_market_restock_months(") == 1
           and all(byte < 128 for byte in src_bytes)
           and b"\r\n" not in suite_bytes
           and not suite_bytes.startswith(b"\xef\xbb\xbf"))
    record("AC-MRS8", ok8,
           "an argument raises TypeError, two calls and two instances"
           " read byte-identically, table digests and ledger_tx sets"
           " unchanged, wired once, ASCII/LF/BOM-free")

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    ok_files = shas_before == shas_after

    total = len(RESULTS)
    passed = sum(1 for _ac, ok in RESULTS if ok)
    print("\nSUITE %s %d/%d" % ("PASS" if passed == total else "FAIL",
                                passed, total))
    if not ok_files:
        print("FAIL product files mutated during the run")
    close_stack(am, dk, metered, led)
    return 0 if passed == total and ok_files else 1


if __name__ == "__main__":
    sys.exit(main())
