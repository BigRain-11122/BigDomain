"""Acceptance suite for the resident workbench block on the apimarket
settlement report (BigDomain R2106; canon = the R2106 explore-queue
claim row, criteria AC-AMWB1..AC-AMWB8 registered there BEFORE this
code existed - honesty law; the AC-AMWB prefix, the todo/watch_alerts
buyer-block keys, this suite name and the
ledger-apimarket-reportworkbench runner label were all git-grep -F
zero-occupancy anchored 2026-10-25, rc=1).

Product under proof: apimarket_report.py now reads the two newest
resident faces into every buyer block, so the single consumer of the
market read faces finally serves the residents too (R2104
api_watch_alerts and R2105 api_buyer_todo had zero product call sites).

Criteria:
  AC-AMWB1 Same source: every buyer block carries todo and
    watch_alerts equal to a direct call on the same database, and each
    collect re-reads them (rating a purchase moves the queue in the
    very next collect).
  AC-AMWB2 Additive contract: the JSON envelope still has exactly
    schema_version/report/attention, schema_version equals the module
    constant (2 at birth; the R2108 activity block bumps it to 3
    additively), and the v1 buyer keys profile/months are unchanged.
  AC-AMWB3 HTML surface: each buyer block renders a "rating debt" and
    a "watch alerts" table whose row counts equal the envelope counts,
    with an explicit empty state.
  AC-AMWB4 Escaping: a hostile listing title is escaped on the page,
    and the AIGC marker plus the non-advisory disclaimer survive.
  AC-AMWB5 Pure read: thirteen table digests and the ledger tx count
    are unchanged by a collect.
  AC-AMWB6 Determinism: two seeded worlds render byte-identical HTML
    and byte-identical JSON.
  AC-AMWB7 Degrade: a legacy synthetic report dict without the two new
    buyer keys still renders (honest empty state, no KeyError).
  AC-AMWB8 Regression + wiring: the R2101/R2102/R2103 report suites
    still pass and the runner label is registered.

Usage: python test_apimarket_report_workbench.py
"""

import copy
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
    tmp = tempfile.mkdtemp(prefix="apimarket-workbench-" + tag + "-")
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
    """Deterministic stamp holder for the mutation legs."""
    class _C(object):
        def now_utc(self):
            return value
    return _C()


def seed_activity(db, ids):
    """Add one unrated purchase and one real watch event, so the two new
    blocks carry rows: carol buys dave-unrelated d3, then watches it
    while the seller cuts the price."""
    led, mtr, dk, am = open_stack(db)
    orig = A._now_utc
    orig_led = R.L.now_utc
    try:
        A._now_utc = with_clock("2026-10-10T00:00:00Z").now_utc
        R.L.now_utc = with_clock("2026-10-10T00:00:00Z").now_utc
        am.purchase_api("usr:carol", ids["listings"][2], "ref-carol-d3")
        am.watch_api("usr:bob", ids["listings"][2])
        A._now_utc = with_clock("2026-10-11T00:00:00Z").now_utc
        R.L.now_utc = with_clock("2026-10-11T00:00:00Z").now_utc
        am.revise_price("usr:frank", ids["listings"][2], 2)
    finally:
        A._now_utc = orig
        R.L.now_utc = orig_led
        am.close()
        dk.close()
        mtr.close()
        led.close()


def check_same_source(db):
    seed_activity(db, _IDS["main"])
    report = collect_with(db)
    ok = True
    details = []
    led, mtr, dk, am = open_stack(db)
    try:
        for buyer, block in sorted(report["buyers"].items()):
            want_todo = am.api_buyer_todo(buyer)
            want_alerts = am.api_watch_alerts(buyer)
            same = (block.get("todo") == want_todo
                    and block.get("watch_alerts") == want_alerts)
            ok = ok and same
            details.append("%s:pending=%d/alerts=%d"
                           % (buyer, want_todo["pending_count"],
                              want_alerts["alert_count"]))
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    # no-cache proof: rating the pending purchase drains the queue on
    # the very next collect.
    led, mtr, dk, am = open_stack(db)
    try:
        before = am.api_buyer_todo("usr:carol")
        am.rate_api("usr:carol", _IDS["main"]["listings"][2], 3)
        after = am.api_buyer_todo("usr:carol")
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    fresh = collect_with(db)
    moved = (before["pending_count"] == after["pending_count"] + 1
             and after["rated_count"] == before["rated_count"] + 1
             and fresh["buyers"]["usr:carol"]["todo"]["pending_count"]
             == after["pending_count"])
    ok = ok and before["pending_count"] >= 1 and moved
    record("AC-AMWB1", ok,
           "same_source=%s pending %d->%d rated %d->%d %s"
           % (ok, before["pending_count"], after["pending_count"],
              before["rated_count"], after["rated_count"],
              ",".join(details)))


def check_contract(tmp, db):
    report = collect_with(db)
    blocks = sorted(report["buyers"])
    keys_ok = all(sorted(report["buyers"][b]) ==
                  ["months", "profile", "todo", "watch_alerts"]
                  for b in blocks)
    led, mtr, dk, am = open_stack(db)
    try:
        v1_ok = all(report["buyers"][b]["profile"] ==
                    am.api_buyer_profile(b)
                    and report["buyers"][b]["months"] ==
                    am.api_buyer_months(b) for b in blocks)
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    out = os.path.join(tmp, "wb.html")
    js = os.path.join(tmp, "wb.json")
    R.main(["--db", db, "--out", out, "--json-out", js])
    doc = json.loads(io.open(js, "r", encoding="utf-8").read())
    env_ok = sorted(doc) == ["attention", "report", "schema_version"]
    # R2108 erratum: this assertion was born hardcoded to 2. The R2108
    # activity block is another ADDITIVE bump (3) that keeps every v2
    # key in place, so the version check follows the module while the
    # v2 key sets above stay pinned as literals.
    record("AC-AMWB2",
           R.REPORT_SCHEMA >= 2 and keys_ok and v1_ok and env_ok
           and doc.get("schema_version") == R.REPORT_SCHEMA,
           "schema=%d blocks=%s v1=%s env=%s keys=%s"
           % (R.REPORT_SCHEMA, keys_ok, v1_ok, sorted(doc),
              [sorted(report["buyers"][b]) for b in blocks]))


def check_html(tmp, db):
    out = os.path.join(tmp, "wb.html")
    if not os.path.isfile(out):
        R.main(["--db", db, "--out", out])
    page = io.open(out, "r", encoding="utf-8").read()
    report = collect_with(db)
    ok = True
    details = []
    for buyer, block in sorted(report["buyers"].items()):
        pending = len(block["todo"]["pending"])
        alerts = len(block["watch_alerts"]["alerts"])
        head_debt = "%s - rating debt (%d)" % (buyer, pending)
        head_alert = "%s - watch alerts (%d)" % (buyer, alerts)
        found = head_debt in page and head_alert in page
        ok = ok and found
        details.append("%s:%d/%d" % (buyer, pending, alerts))
    empty_ok = ('<p class="empty">no pending ratings</p>' in page
                or 'no pending ratings' in page)
    empty_ok = empty_ok and 'no watch alerts' in page
    record("AC-AMWB3", ok and empty_ok,
           "heads=%s empty_state=%s %s"
           % (ok, empty_ok, ",".join(details)))


def check_escape(tmp, db):
    led, mtr, dk, am = open_stack(db)
    try:
        hostile = "Evil <script>alert('x')</script> & \"quote\""
        lid = am.publish_api("usr:dana", "evil-key", hostile,
                             "hostile title probe", R.PAYLOAD, 4,
                             False)["listing_id"]
        am.purchase_api("usr:dave", lid, "ref-dave-evil")
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    out = os.path.join(tmp, "esc.html")
    R.main(["--db", db, "--out", out])
    page = io.open(out, "r", encoding="utf-8").read()
    body = page.split("<body>", 1)[-1]
    ok_escape = "<script>alert(" not in body
    ok_shown = "&lt;script&gt;" in body
    ok_marker = R.MARKER in page and R.DISCLAIMER.split(":")[0] in page
    record("AC-AMWB4", ok_escape and ok_shown and ok_marker,
           "raw_tag_absent=%s escaped_present=%s marker=%s"
           % (ok_escape, ok_shown, ok_marker))


def check_pure_read(db):
    before = table_digest(db)
    report = collect_with(db)
    after = table_digest(db)
    ok = before == after and "buyers" in report
    record("AC-AMWB5", ok,
           "digest_same=%s tx=%d buyers=%d"
           % (before == after, after[1], len(report["buyers"])))


def check_determinism():
    pages = []
    docs = []
    for tag in ("d1", "d2"):
        tmp, db, ids = fresh_world(tag)
        seed_activity(db, ids)
        out = os.path.join(tmp, "d.html")
        js = os.path.join(tmp, "d.json")
        R.main(["--db", db, "--out", out, "--json-out", js])
        pages.append(io.open(out, "rb").read())
        docs.append(io.open(js, "rb").read())
    record("AC-AMWB6", pages[0] == pages[1] and docs[0] == docs[1],
           "html_same=%s json_same=%s html_sha16=%s"
           % (pages[0] == pages[1], docs[0] == docs[1],
              hashlib.sha256(pages[0]).hexdigest()[:16]))


def check_degrade(db):
    report = collect_with(db)
    legacy = copy.deepcopy(report)
    for block in legacy["buyers"].values():
        block.pop("todo", None)
        block.pop("watch_alerts", None)
    ok = False
    texture = ""
    try:
        page = R.render_html(legacy)
        ok = isinstance(page, str) and "no pending ratings" in page
        texture = "len=%d" % len(page)
    except KeyError as exc:
        texture = "KeyError %r" % (exc,)
    record("AC-AMWB7", ok, "%s" % texture)


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
        wired = ('"ledger-apimarket-reportworkbench"' in src
                 and "test_apimarket_report_workbench.py" in src)
    except OSError:
        wired = False
    record("AC-AMWB8", all(c == 0 for c in codes) and wired,
           "rc=%s wired=%s" % (codes, wired))


_IDS = {}


def main():
    tmp, db, ids = fresh_world("main")
    _IDS["main"] = ids
    check_same_source(db)
    check_contract(tmp, db)
    check_html(tmp, db)
    check_escape(tmp, db)
    check_pure_read(db)
    check_determinism()
    check_degrade(db)
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