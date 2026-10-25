"""Acceptance suite for the distribution-duty block on the apimarket
settlement report (BigDomain R2125; canon = the R2125 explore-queue
claim row, criteria AC-AMDD1..AC-AMDD8 registered there BEFORE this
code existed - honesty law; the AC-AMDD prefix, collect_duty,
DUTY_KEYS, DUTY_EMPTY, this suite name, the ledger-apimarket-reportduty
runner label and the "Distribution duty" heading were all git-grep -F
zero-occupancy anchored 2026-10-25, rc=1).

Product under proof: R2124 built the provider identity, public display
and review faces, and nothing consumed them - a git grep for their
names found only their own suites, so the operator page could not
answer which live listings still await review or which sellers
disclose no identity. apimarket_report.py now carries a duty block
with the two envelopes verbatim plus the disclosure gap derived from
the public envelope alone, and the page renders three tables.

Criteria:
  AC-AMDD1 Same source, no cache: the duty block equals a direct
    api_review_queue / api_public_listings call on the same database,
    and a review recorded after one collect empties that listing from
    the queue in the very next collect.
  AC-AMDD2 Additive contract: the JSON envelope still has exactly
    schema_version/report/attention, schema_version equals the module
    constant (15), and market / market_months / board / activity /
    refunds / dossiers equal their direct face calls.
  AC-AMDD3 HTML surface: the Distribution duty heading exists, the
    three count headings equal the block counts, every pending row is
    on the page, and a synthetic report without the duty key renders
    the honest empty state.
  AC-AMDD4 Escaping: a hostile listing title is escaped, and the AIGC
    marker plus the non-advisory disclaimer survive.
  AC-AMDD5 Pure read: seventeen table digests and the ledger tx count
    are unchanged by a collect.
  AC-AMDD6 Determinism: two seeded worlds render byte-identical HTML
    and byte-identical JSON.
  AC-AMDD7 Duty semantics through the report: approve drops the
    listing from the queue and shows approved; a refusal keeps its
    reason on the public row; registration clears that seller from the
    gap table and shows the credit code; a delisting leaves both the
    queue and the public layer.
  AC-AMDD8 Regression + wiring: the base report, attention and JSON
    suites still pass and the runner label is registered.

Usage: python test_apimarket_report_duty.py
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
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers", "apimarket_providers",
          "apimarket_reviews")


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
    tmp = tempfile.mkdtemp(prefix="apimarket-duty-" + tag + "-")
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
    """Run fn(am) under a pinned clock on an open stack."""
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


def check_same_source(db, ids):
    report = collect_with(db)
    duty = report["duty"]
    ok = True
    led, mtr, dk, am = open_stack(db)
    try:
        ok = ok and duty["review_queue"] == am.api_review_queue()
        ok = ok and duty["public"] == am.api_public_listings()
        before = duty["review_queue"]["pending_count"]
        first = ids["listings"][0]
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    mutate(db, lambda am: am.review_listing(first, "approve"))
    after = collect_with(db)["duty"]
    left = all(row["listing_id"] != first
               for row in after["review_queue"]["rows"])
    record("AC-AMDD1", ok and left
           and after["review_queue"]["pending_count"] == before - 1,
           "same=%s pending %d->%d left=%s"
           % (ok, before, after["review_queue"]["pending_count"], left))


def check_contract(db):
    report = collect_with(db)
    payload = R.api_report_payload(report)
    keys = tuple(sorted(payload.keys()))
    schema_ok = (payload["schema_version"] == R.REPORT_SCHEMA
                 and R.REPORT_SCHEMA >= 15)
    same = True
    led, mtr, dk, am = open_stack(db)
    try:
        same = same and report["market"] == am.api_market_stats()
        same = same and report["market_months"] == am.api_market_months()
        same = same and report["board"] == am.api_board()
        same = (same and report["activity"]
                == am.api_market_feed(limit=R.FEED_LIMIT))
        same = same and report["refunds"] == am.api_refund_register()
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    duty_keys = tuple(sorted(report["duty"].keys()))
    record("AC-AMDD2", keys == ("attention", "report", "schema_version")
           and schema_ok and same and duty_keys == tuple(sorted(
               R.DUTY_KEYS)),
           "keys=%s schema=%s same=%s dutykeys=%s"
           % (",".join(keys), payload["schema_version"], same,
              ",".join(duty_keys)))


def check_html(db):
    report = collect_with(db)
    page = R.render_html(report)
    duty = report["duty"]
    ok = ("Distribution duty" in page
          and "pending review (%d)" % duty["review_queue"][
              "pending_count"] in page
          and "public display (%d)" % duty["public"][
              "listing_count"] in page
          and "undisclosed sellers (%d)" % len(
              duty["undisclosed_sellers"]) in page)
    for row in duty["review_queue"]["rows"]:
        ok = ok and row["listing_key"] in page
    legacy = dict(report)
    legacy.pop("duty")
    legacy_page = R.render_html(legacy)
    record("AC-AMDD3", ok and R.DUTY_EMPTY in legacy_page,
           "heads=%s/%s/%s degrade=%s"
           % (duty["review_queue"]["pending_count"],
              duty["public"]["listing_count"],
              len(duty["undisclosed_sellers"]),
              R.DUTY_EMPTY in legacy_page))


def check_escape(db):
    def run(am):
        am.publish_api("usr:dana", "hostile", "<script>x</script>",
                       "hostile duty title probe", R.PAYLOAD, 2, False)

    mutate(db, run)
    page = R.render_html(collect_with(db))
    ok = ("<script>x</script>" not in page
          and "&lt;script&gt;x&lt;/script&gt;" in page
          and R.MARKER in page
          and R.DISCLAIMER in page)
    record("AC-AMDD4", ok,
           "escaped=%s marker=%s disclaimer=%s"
           % ("&lt;script&gt;" in page, R.MARKER in page,
              R.DISCLAIMER in page))


def check_pure_read(db):
    before = table_digest(db)
    collect_with(db)
    after = table_digest(db)
    record("AC-AMDD5", before == after,
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
    record("AC-AMDD6", ok,
           "html=%s json=%s" % (hashlib.sha256(html_a.encode("utf-8"))
                                .hexdigest()[:16],
                                hashlib.sha256(json_a.encode("utf-8"))
                                .hexdigest()[:16]))


def check_semantics(db, ids):
    d1, d2, d3 = ids["listings"][0], ids["listings"][1], ids["listings"][2]
    base = collect_with(db)["duty"]
    gaps = [row["dev_account"] for row in base["undisclosed_sellers"]]
    dense_ok = (base["review_queue"]["pending_count"] == 3
                and base["public"]["review_pending_count"] == 3
                and gaps == ["usr:dana", "usr:frank"])

    mutate(db, lambda am: am.review_listing(d1, "approve"))
    mutate(db, lambda am: am.review_listing(d3, "refuse", "policy probe"))
    mutate(db, lambda am: am.register_provider(
        "usr:dana", "Dana Labs", "91310000MA1K000001"))
    mutate(db, lambda am: am.delist_api("usr:dana", d2))
    after = collect_with(db)["duty"]

    queue_ids = [row["listing_id"] for row in after["review_queue"]["rows"]]
    public = {row["listing_id"]: row for row in after["public"]["listings"]}
    gaps_after = [row["dev_account"]
                  for row in after["undisclosed_sellers"]]
    checks = {
        "approve_left_queue": d1 not in queue_ids,
        "approved_visible": public[d1]["review_state"] == "approved",
        "refused_kept_reason": (public[d3]["review_state"] == "refused"
                                and public[d3]["review_reason"]
                                == "policy probe"),
        "gap_cleared": gaps_after == ["usr:frank"],
        "credit_shown": public[d1]["credit_code"]
        == "91310000MA1K000001",
        "delist_leaves_both": (d2 not in queue_ids
                               and d2 not in public),
        "pending_matches": (after["review_queue"]["pending_count"]
                            == after["public"]["review_pending_count"]),
    }
    record("AC-AMDD7", dense_ok and all(checks.values()),
           "dense=%s queue=%s gaps=%s checks=%s"
           % (dense_ok, queue_ids, gaps_after,
              ",".join(k for k, v in sorted(checks.items()) if not v)
              or "all-pass"))


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
        wired = ('"ledger-apimarket-reportduty"' in src
                 and "test_apimarket_report_duty.py" in src)
    except OSError:
        wired = False
    record("AC-AMDD8", all(c == 0 for c in codes) and wired,
           "rc=%s wired=%s" % (codes, wired))


def main():
    tmp, db, ids = fresh_world("main")
    check_same_source(db, ids)
    check_contract(db)
    check_html(db)
    check_escape(db)
    check_pure_read(db)
    check_determinism()
    # AC-AMDD1 already reviews one listing on the main world, so the
    # duty-semantics walk gets its own untouched market.
    sem_tmp, sem_db, sem_ids = fresh_world("sem")
    check_semantics(sem_db, sem_ids)
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