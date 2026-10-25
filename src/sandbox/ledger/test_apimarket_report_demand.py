"""Acceptance suite for the seller demand block on the apimarket
settlement report (BigDomain R2116; canon = the R2116 explore-queue
claim row, criteria AC-AMDS1..AC-AMDS8 registered there BEFORE this
code existed - honesty law; the AC-AMDS prefix, the DEMAND_EMPTY
constant, this suite name and the ledger-apimarket-reportdemand runner
label were all git-grep -F zero-occupancy anchored 2026-10-25, rc=1).

Product under proof: apimarket_report.py now reads api_listing_demand
into every seller block. That was the last read face without a block
consumer - it surfaced only through the attention digest, so a seller
could not see the per-listing watcher/conversion table anywhere on the
page.

Criteria:
  AC-AMDS1 Same source: every seller block carries demand equal to a
    direct api_listing_demand call on the same database, and each
    collect re-reads it (a watch placed after one collect moves the
    watcher count in the very next collect).
  AC-AMDS2 Additive contract: the JSON envelope still has exactly
    schema_version/report/attention, schema_version equals the module
    constant (9), every earlier seller key keeps its value, and the
    buyer block keys are untouched.
  AC-AMDS3 HTML surface: each seller renders a "seller demand" heading
    whose row count equals the envelope listing count, and a synthetic
    seller block without the demand key renders the honest empty state.
  AC-AMDS4 Escaping: a hostile listing title is escaped on the page,
    and the AIGC marker plus the non-advisory disclaimer survive.
  AC-AMDS5 Pure read: thirteen table digests and the ledger tx count
    are unchanged by a collect.
  AC-AMDS6 Determinism: two seeded worlds render byte-identical HTML
    and byte-identical JSON.
  AC-AMDS7 Demand semantics through the report: rows stay dense (every
    listing of the seller, retired included), an unwatch lowers the
    reported count, and a refunded purchase reads as pending rather
    than converted.
  AC-AMDS8 Regression + wiring: the base report, attention and JSON
    suites still pass and the runner label is registered.

Usage: python test_apimarket_report_demand.py
"""

import hashlib
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import apimarket as A                 # noqa: E402
import apimarket_report as R          # noqa: E402

RESULTS = []
RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok), evidence))
    print("%s %s %s" % ("PASS" if ok else "FAIL", ac, evidence))


def table_digest(db_path):
    market_db = os.path.join(os.path.dirname(db_path), "apimarket.db")
    h = hashlib.sha256()
    conn = sqlite3.connect(market_db)
    try:
        for name in TABLES:
            rows = conn.execute(
                "SELECT * FROM %s ORDER BY rowid" % name).fetchall()
            h.update(("%s|%d|%r" % (name, len(rows), rows)).encode("utf-8"))
    finally:
        conn.close()
    conn = sqlite3.connect(db_path)
    try:
        tx = conn.execute("SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
    finally:
        conn.close()
    return h.hexdigest(), tx


def fresh_world(tag):
    tmp = tempfile.mkdtemp(prefix="apimarket-demand-" + tag + "-")
    db = os.path.join(tmp, "ledger.db")
    led, mtr, dk, am = R.build_stack(db)
    ids = R.seed_demo(am, led, dk)
    am.close()
    dk.close()
    mtr.close()
    led.close()
    return tmp, db, ids


def open_stack(db):
    led, mtr, dk, am = R.build_stack(db)
    return led, mtr, dk, am


def collect_with(db):
    led, mtr, dk, am = open_stack(db)
    try:
        return R.collect(am)
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()


def with_clock(value):
    class _C(object):
        def now_utc(self):
            return value
    return _C()


def mutate(db, fn):
    """Run fn(am, ids) under a pinned clock on an open stack."""
    led, mtr, dk, am = open_stack(db)
    orig = A._now_utc
    orig_led = R.L.now_utc
    try:
        A._now_utc = with_clock("2026-10-10T00:00:00Z").now_utc
        R.L.now_utc = with_clock("2026-10-10T00:00:00Z").now_utc
        return fn(am)
    finally:
        A._now_utc = orig
        R.L.now_utc = orig_led
        am.close()
        dk.close()
        mtr.close()
        led.close()


def seed_watches(db, ids):
    """d1: bob and carol watch (carol bought it unrefunded), dave
    watches then unwatches; d2: erin watches (her purchase was
    refunded by the demo seed)."""

    def run(am):
        am.watch_api("usr:bob", ids["listings"][0])
        am.watch_api("usr:carol", ids["listings"][0])
        am.watch_api("usr:dave", ids["listings"][0])
        am.unwatch_api("usr:dave", ids["listings"][0])
        am.watch_api("usr:erin", ids["listings"][1])

    mutate(db, run)


def check_same_source(db, ids):
    seed_watches(db, ids)
    report = collect_with(db)
    ok = True
    details = []
    led, mtr, dk, am = open_stack(db)
    try:
        for dev, block in sorted(report["sellers"].items()):
            want = am.api_listing_demand(dev)
            same = block.get("demand") == want
            ok = ok and same
            details.append("%s:rows=%d/watchers=%d"
                           % (dev, want["listing_count"],
                              want["total_watchers"]))
        before = am.api_listing_demand("usr:dana")["total_watchers"]
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    mutate(db, lambda am: am.watch_api("usr:bob", ids["listings"][1]))
    after = collect_with(db)["sellers"]["usr:dana"]["demand"]
    grew = after["total_watchers"] == before + 1
    record("AC-AMDS1", ok and grew,
           "same=%s -> %s; re-read %d->%d"
           % (same, ",".join(details), before, after["total_watchers"]))


def check_contract(db):
    report = collect_with(db)
    payload = R.api_report_payload(report)
    keys = tuple(sorted(payload.keys()))
    # birth station: this criterion pinned schema 9 when the seller
    # demand block was born (R2116). R2117 added the seller quality key
    # as an ADDITIVE bump (9 -> 10), so the assertion follows the module
    # constant instead of pinning a literal while still proving the
    # envelope shape the additive rule promises.
    schema_ok = (payload["schema_version"] == R.REPORT_SCHEMA
                 and R.REPORT_SCHEMA >= 9)
    legacy = True
    led, mtr, dk, am = open_stack(db)
    try:
        for dev, block in sorted(report["sellers"].items()):
            legacy = legacy and block["profile"] == am.dev_profile(dev)
            legacy = legacy and block["revenue_months"] == \
                am.api_revenue_months(dev)
            legacy = legacy and block["sales"] == am.api_sales(dev)
        buyer_keys = {tuple(sorted(b.keys()))
                      for b in report["buyers"].values()}
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    expected = {("history", "months", "profile", "todo", "watch_alerts")}
    record("AC-AMDS2", keys == ("attention", "report", "schema_version")
           and schema_ok and legacy and buyer_keys == expected,
           "keys=%s schema=%s legacy=%s buyerkeys=%s"
           % (",".join(keys), payload["schema_version"], legacy,
              buyer_keys))


def check_html(db):
    report = collect_with(db)
    page = R.render_html(report)
    heads = []
    ok = True
    for dev, block in sorted(report["sellers"].items()):
        want = block["demand"]["listing_count"]
        head = "%s - seller demand (%d)" % (dev, want)
        heads.append(head)
        ok = ok and head in page
        ok = ok and block["demand"]["rows"][0]["listing_key"] in page
    legacy = dict(report)
    legacy["sellers"] = {"usr:ghost": {
        "profile": {"dev_account": "usr:ghost"},
        "revenue_months": {"months": []},
        "sales": {"sales": []}}}
    legacy_page = R.render_html(legacy)
    degrade = R.DEMAND_EMPTY in legacy_page
    record("AC-AMDS3", ok and degrade,
           "heads=%s degrade=%s" % ("|".join(heads), degrade))


def check_escape(db, ids):
    def run(am):
        am.publish_api("usr:dana", "hostile", "<script>x</script>",
                       "hostile title probe", R.PAYLOAD, 2, False)

    mutate(db, run)
    page = R.render_html(collect_with(db))
    ok = ("<script>x</script>" not in page
          and "&lt;script&gt;x&lt;/script&gt;" in page
          and R.MARKER in page
          and R.DISCLAIMER in page)
    record("AC-AMDS4", ok,
           "escaped=%s marker=%s disclaimer=%s"
           % ("&lt;script&gt;" in page, R.MARKER in page,
              R.DISCLAIMER in page))


def check_pure_read(db):
    before = table_digest(db)
    collect_with(db)
    after = table_digest(db)
    record("AC-AMDS5", before == after,
           "digest=%s tx=%d" % (after[0][:16], after[1]))


def check_determinism():
    a_tmp, a_db, _ = fresh_world("det-a")
    b_tmp, b_db, _ = fresh_world("det-b")
    html_a = R.render_html(collect_with(a_db))
    html_b = R.render_html(collect_with(b_db))
    json_a = json.dumps(R.api_report_payload(collect_with(a_db)),
                        sort_keys=True)
    json_b = json.dumps(R.api_report_payload(collect_with(b_db)),
                        sort_keys=True)
    ok = html_a == html_b and json_a == json_b
    record("AC-AMDS6", ok,
           "html=%s json=%s" % (hashlib.sha256(html_a.encode("utf-8"))
                                .hexdigest()[:16],
                                hashlib.sha256(json_a.encode("utf-8"))
                                .hexdigest()[:16]))


def check_semantics(db, ids):
    demand = collect_with(db)["sellers"]["usr:frank"]["demand"]
    dense = (demand["listing_count"] == len(demand["rows"]) == 1)
    # dana keeps one live listing, so she stays in the board-derived
    # seller set and her retired shelf must stay visible as a row.
    retire = mutate(db, lambda am: am.delist_api(
        "usr:dana", ids["listings"][1]))
    retired = collect_with(db)["sellers"]["usr:dana"]["demand"]
    by_key = {row["listing_key"]: row for row in retired["rows"]}
    retired_kept = (retired["listing_count"] == len(retired["rows"])
                    and by_key["macro-feed"]["delisted"] is True)
    d1 = by_key["risk-scan"]
    d2 = by_key["macro-feed"]
    unwatch_ok = (d1["watcher_count"] == 2
                  and d1["converted_count"] == 1
                  and d1["pending_count"] == 1)
    # bob watched d1 and his d1 purchase was refunded by the demo seed,
    # so he must read as pending (1) while carol's unrefunded purchase
    # reads as the single conversion - a refund never fakes a
    # conversion.
    refund_pending = (d1["pending_count"] == 1
                      and d1["converted_count"] == 1)
    record("AC-AMDS7",
           dense and retired_kept and unwatch_ok and refund_pending,
           "dense=%s retired=%s d1(w/c/p)=%d/%d/%d d2(c/p)=%d/%d"
           % (dense, retired_kept, d1["watcher_count"],
              d1["converted_count"], d1["pending_count"],
              d2["converted_count"], d2["pending_count"]))


def check_regression():
    base = os.path.dirname(BASE)
    labels = ("test_apimarket_report.py",
              "test_apimarket_report_attention.py",
              "test_apimarket_report_json.py")
    codes = []
    for name in labels:
        proc = subprocess.run(
            [sys.executable, os.path.join(base, "ledger", name)],
            cwd=base, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        codes.append(proc.returncode)
        print("  child %s rc=%d" % (name, proc.returncode))
    wired = False
    try:
        src = io.open(RECONCILE, "r", encoding="utf-8").read()
        wired = ('"ledger-apimarket-reportdemand"' in src
                 and "test_apimarket_report_demand.py" in src)
    except OSError:
        wired = False
    record("AC-AMDS8", all(c == 0 for c in codes) and wired,
           "rc=%s wired=%s" % (codes, wired))


def main():
    tmp, db, ids = fresh_world("main")
    check_same_source(db, ids)
    check_contract(db)
    check_html(db)
    check_escape(db, ids)
    check_pure_read(db)
    check_determinism()
    check_semantics(db, ids)
    check_regression()
    failed = [ac for ac, ok, _ in RESULTS if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              len(RESULTS) - len(failed), len(RESULTS)))
    if failed:
        print("FAILED: %s" % ",".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())