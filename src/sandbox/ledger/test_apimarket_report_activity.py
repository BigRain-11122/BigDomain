"""Acceptance suite for the public activity section on the apimarket
settlement report (BigDomain R2108; canon = the R2108 explore-queue
claim row, criteria AC-AMAF1..AC-AMAF8 registered there BEFORE this
code existed - honesty law; the AC-AMAF prefix, api_market_activity,
activity_block, FEED_LIMIT, this suite name and the
ledger-apimarket-activity runner label were all git-grep -F
zero-occupancy anchored 2026-10-25, rc=1).

Product under proof: apimarket_report.py reads the R2107 public
activity feed into an "activity" block and renders it as the Public
activity section, so the feed stops being a face with zero consumers
(the same idle form R2101 and R2106 closed for their faces).

Criteria:
  AC-AMAF1 Same source + no cache: the activity block equals a direct
    api_market_feed(limit=FEED_LIMIT) call on the same database, and a
    publication made after a collect shows up on the very next one.
  AC-AMAF2 Additive contract: REPORT_SCHEMA >= 3 (the R2109 dossier
    block bumped it 3 -> 4, so the assertion tracks the module constant
    instead of a frozen number - honest correction noted in the R2109
    claim row), the JSON envelope
    still has exactly schema_version/report/attention, every earlier
    report key keeps its value and the buyer blocks keep their keys.
  AC-AMAF3 HTML surface: the Public activity section states shown of
    total, its table carries returned+header rows and the pinned six
    column heads, and an empty market renders the honest empty state.
  AC-AMAF4 Escaping + markers: a hostile listing title is escaped in
    the activity rows while the AIGC marker and the disclaimer survive.
  AC-AMAF5 Pure read: thirteen table digests and the ledger tx count
    are unchanged by a collect.
  AC-AMAF6 Determinism: two seeded worlds render byte-identical HTML
    and byte-identical JSON.
  AC-AMAF7 Degrade: a legacy report dict without the activity key still
    renders (honest empty state, no KeyError).
  AC-AMAF8 Regression + wiring: the R2101/R2102/R2103/R2106 report
    suites still pass and the runner label is registered.

Usage: python test_apimarket_report_activity.py
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
OLD_KEYS = ["attention", "board", "buyers", "market", "market_months",
            "sellers"]


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


def fresh_world(tag, seed=True):
    tmp = tempfile.mkdtemp(prefix="apimarket-activity-" + tag + "-")
    db = os.path.join(tmp, "ledger.db")
    led, mtr, dk, am = R.build_stack(db)
    ids = R.seed_demo(am, led, dk) if seed else None
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


def feed_direct(db):
    led, mtr, dk, am = open_stack(db)
    try:
        return am.api_market_feed(limit=R.FEED_LIMIT)
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()


def section(page):
    mark = "<h2>Public activity</h2>"
    start = page.index(mark) + len(mark)
    end = page.index("<h2>", start)
    return page[start:end]


def check_same_source(db):
    report = collect_with(db)
    direct = feed_direct(db)
    same = report.get("activity") == direct
    before_total = direct["total"]
    led, mtr, dk, am = open_stack(db)
    try:
        fresh = am.publish_api("usr:dana", "activity-probe",
                               "Activity Probe API",
                               "probe listing for the activity block",
                               R.PAYLOAD, 2, False)
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    after = collect_with(db)["activity"]
    grew = (after["total"] == before_total + 1
            and after["returned"] == len(after["events"])
            and after["events"][-1]["kind"] == "published"
            and after["events"][-1]["listing_id"] == fresh["listing_id"])
    record("AC-AMAF1", same and grew,
           "same_source=%s total %d->%d tail=%s/%s"
           % (same, before_total, after["total"],
              after["events"][-1]["kind"],
              after["events"][-1]["listing_id"]))


def check_contract(tmp, db):
    report = collect_with(db)
    keys_ok = set(OLD_KEYS + ["activity", "dossiers", "refunds"]) <= set(
        report)
    buyer_keys = sorted({tuple(sorted(block))
                         for block in report["buyers"].values()})
    led, mtr, dk, am = open_stack(db)
    try:
        old_ok = (report["market"] == am.api_market_stats()
                  and report["market_months"] == am.api_market_months()
                  and report["board"] == am.api_board()
                  and report["attention"] == R.collect_attention(am, report))
        buyer_ok = all(
            report["buyers"][b]["profile"] == am.api_buyer_profile(b)
            and report["buyers"][b]["months"] == am.api_buyer_months(b)
            for b in report["buyers"])
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    out = os.path.join(tmp, "act.html")
    js = os.path.join(tmp, "act.json")
    R.main(["--db", db, "--out", out, "--json-out", js])
    doc = json.loads(io.open(js, "r", encoding="utf-8").read())
    env_ok = sorted(doc) == ["attention", "report", "schema_version"]
    record("AC-AMAF2",
           R.REPORT_SCHEMA >= 3 and keys_ok and old_ok and buyer_ok
           and env_ok and doc.get("schema_version") == R.REPORT_SCHEMA
           and doc["report"]["activity"] == report["activity"],
           "schema=%d top=%s old=%s buyer=%s env=%s buyer_keys=%s"
           % (R.REPORT_SCHEMA, keys_ok, old_ok, buyer_ok, env_ok,
              buyer_keys))


def check_html(tmp, db):
    out = os.path.join(tmp, "act.html")
    if not os.path.isfile(out):
        R.main(["--db", db, "--out", out])
    page = io.open(out, "r", encoding="utf-8").read()
    activity = collect_with(db)["activity"]
    body = section(page)
    heads_ok = all("<th>%s</th>" % col in body
                   for col in R.ACTIVITY_COLUMNS)
    rows = body.count("<tr>")
    summary = ("showing %d of %d event(s)"
               % (activity["returned"], activity["total"]))
    empty_tmp, empty_db, _ = fresh_world("empty", seed=False)
    empty_out = os.path.join(empty_tmp, "empty.html")
    R.main(["--db", empty_db, "--out", empty_out])
    empty_page = io.open(empty_out, "r", encoding="utf-8").read()
    empty_ok = R.ACTIVITY_EMPTY in section(empty_page)
    record("AC-AMAF3",
           heads_ok and rows == activity["returned"] + 1
           and summary in body and empty_ok,
           "heads=%s rows=%d returned=%d summary=%s empty=%s"
           % (heads_ok, rows, activity["returned"],
              summary in body, empty_ok))


def check_escape(tmp, db):
    led, mtr, dk, am = open_stack(db)
    try:
        hostile = "Evil <script>alert('x')</script> & \"quote\""
        am.publish_api("usr:dana", "evil-activity-key", hostile,
                       "hostile activity probe", R.PAYLOAD, 4, False)
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    out = os.path.join(tmp, "esc.html")
    R.main(["--db", db, "--out", out])
    page = io.open(out, "r", encoding="utf-8").read()
    body = section(page)
    raw_absent = "<script>alert(" not in body
    escaped_present = "&lt;script&gt;" in body
    markers = (R.MARKER in page
               and R.DISCLAIMER.split(":")[0] in page)
    record("AC-AMAF4", raw_absent and escaped_present and markers,
           "raw_absent=%s escaped=%s markers=%s"
           % (raw_absent, escaped_present, markers))


def check_pure_read(db):
    before = table_digest(db)
    report = collect_with(db)
    after = table_digest(db)
    record("AC-AMAF5", before == after and "activity" in report,
           "digest_same=%s tx=%d returned=%d"
           % (before == after, after[1],
              report["activity"]["returned"]))


def check_determinism():
    pages = []
    docs = []
    for tag in ("d1", "d2"):
        tmp, db, ids = fresh_world(tag)
        out = os.path.join(tmp, "d.html")
        js = os.path.join(tmp, "d.json")
        R.main(["--db", db, "--out", out, "--json-out", js])
        pages.append(io.open(out, "rb").read())
        docs.append(io.open(js, "rb").read())
    record("AC-AMAF6", pages[0] == pages[1] and docs[0] == docs[1],
           "html_same=%s json_same=%s html_sha16=%s"
           % (pages[0] == pages[1], docs[0] == docs[1],
              hashlib.sha256(pages[0]).hexdigest()[:16]))


def check_degrade(db):
    report = collect_with(db)
    legacy = copy.deepcopy(report)
    legacy.pop("activity", None)
    ok = False
    texture = ""
    try:
        page = R.render_html(legacy)
        ok = (isinstance(page, str)
              and R.ACTIVITY_EMPTY in section(page))
        texture = "len=%d" % len(page)
    except KeyError as exc:
        texture = "KeyError %r" % (exc,)
    record("AC-AMAF7", ok, texture)


def check_regression():
    base = os.path.dirname(BASE)
    labels = ("test_apimarket_report.py",
              "test_apimarket_report_attention.py",
              "test_apimarket_report_json.py",
              "test_apimarket_report_workbench.py")
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
        wired = ('"ledger-apimarket-activity"' in src
                 and "test_apimarket_report_activity.py" in src)
    except OSError:
        wired = False
    record("AC-AMAF8", all(c == 0 for c in codes) and wired,
           "rc=%s wired=%s" % (codes, wired))


def main():
    tmp, db, ids = fresh_world("main")
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