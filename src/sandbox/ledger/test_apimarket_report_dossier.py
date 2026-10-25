"""Acceptance suite for the per-listing dossier section on the
apimarket settlement report (BigDomain R2109; canon = the R2109
explore-queue claim row, criteria AC-AMLD1..AC-AMLD8 registered there
BEFORE this code existed - honesty law; the AC-AMLD prefix,
DOSSIER_KEYS, collect_dossiers, dossier_block, DOSSIER_EMPTY, the
"Listing dossiers" heading, this suite name and the
ledger-apimarket-reportdossier runner label were all git grep -F
zero-occupancy anchored 2026-10-25, rc=1).

Product under proof: apimarket_report.py reads the seven per-listing
history faces once for every listing the market holds (live or
retired) into a "dossiers" block and renders it as the Listing
dossiers section, so those faces stop being faces with zero consumers
(the same idle form R2101, R2106 and R2108 closed for theirs).

Criteria:
  AC-AMLD1 Derived set: the dossier keys are exactly the listing ids
    the market itself reports through api_search(include_delisted=True),
    each block carries exactly DOSSIER_KEYS eight keys and every
    sub-face names that same listing.
  AC-AMLD2 Additive contract: REPORT_SCHEMA >= 4 (the v4 contract;
    later additive bumps only raise it), the JSON envelope
    still has exactly schema_version/report/attention, every earlier
    report key keeps its value and the buyer blocks keep their keys.
  AC-AMLD3 Same source + no cache: every block equals the direct face
    calls, and a price revision made after a collect shows up on the
    very next one.
  AC-AMLD4 Retirement keeps the dossier: a delisted listing stays in
    the dossiers with its delist stamp and lifecycle event while the
    board excludes it.
  AC-AMLD5 HTML surface: the Listing dossiers section holds one block
    per dossier with the six pinned sub-table heads, and an empty
    market renders the honest empty state.
  AC-AMLD6 Escaping + markers: a hostile listing title is escaped in
    the dossier section while the AIGC marker and the disclaimer
    survive.
  AC-AMLD7 Pure read: thirteen table digests and the ledger tx count
    are unchanged by a collect.
  AC-AMLD8 Determinism + degrade + regression: two seeded worlds
    render byte-identical HTML and JSON, a legacy report dict without
    the dossier key still renders, the five earlier report suites still
    pass and the runner label is registered.

Usage: python test_apimarket_report_dossier.py
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
OLD_KEYS = ["activity", "attention", "board", "buyers", "market",
            "market_months", "sellers"]
DOSSIER_HEADS = ("price history", "metadata history", "supply history",
                 "lifecycle", "ratings", "replies")


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
    tmp = tempfile.mkdtemp(prefix="apimarket-dossier-" + tag + "-")
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


def rich_world(db, ids):
    """Extend the seeded world so every dossier sub-table has content:
    a repriced listing, a replenished scarce listing, a renamed
    listing, a rated-and-answered listing and one retired listing."""
    d1, d2, d3 = ids["listings"]
    led, mtr, dk, am = open_stack(db)
    try:
        am.revise_price("usr:dana", d1, 12)
        am.edit_listing("usr:dana", d2,
                        title="Macro Feed API v2")
        d4 = am.publish_api("usr:dana", "limited-seat",
                            "Limited Seat API",
                            "two seats only", R.PAYLOAD, 7, False,
                            supply=2)["listing_id"]
        am.restock_api("usr:dana", d4, 1)
        am.purchase_api("usr:bob", d4, "ref-bob-d4")
        am.rate_api("usr:bob", d4, 4)
        rating_id = am.api_rating_replies(d4)["rows"][0]["rating_id"]
        am.reply_to_rating("usr:dana", rating_id, "thanks for the rating")
        am.delist_api("usr:frank", d3)
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    return d4


def direct_block(db, listing_id):
    led, mtr, dk, am = open_stack(db)
    try:
        return {
            "view": am.api_view(listing_id),
            "lifecycle": am.api_listing_lifecycle(listing_id),
            "price_history": am.api_price_history(listing_id),
            "metadata_history": am.api_metadata_history(listing_id),
            "supply": am.api_supply(listing_id),
            "supply_history": am.api_supply_history(listing_id),
            "ratings": am.api_ratings(listing_id),
            "rating_replies": am.api_rating_replies(listing_id),
            "feed": am.api_market_feed(listing_id=listing_id,
                                       limit=R.FEED_LIMIT),
        }
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()


def market_ids(db):
    led, mtr, dk, am = open_stack(db)
    try:
        rows = am.api_search(include_delisted=True)["listings"]
        board = am.api_board()["listings"]
        return rows, board
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()


def section(page):
    mark = "<h2>Listing dossiers</h2>"
    start = page.index(mark) + len(mark)
    end = page.index("<h2>", start)
    return page[start:end]


def check_shape(db):
    report = collect_with(db)
    rows, _board = market_ids(db)
    want = set(str(row["listing_id"]) for row in rows)
    got = set(report.get("dossiers") or {})
    keys_ok = all(sorted(block) == sorted(R.DOSSIER_KEYS)
                  for block in report["dossiers"].values())
    id_ok = all(block[face]["listing_id"] == int(key)
                for key, block in report["dossiers"].items()
                for face in R.DOSSIER_KEYS)
    cross = all(report["dossiers"][str(row["listing_id"])]["view"][
        "listing_key"] == row["listing_key"] for row in rows)
    record("AC-AMLD1", want == got and keys_ok and id_ok and cross,
           "keys=%s keys_ok=%s id_ok=%s cross=%s"
           % (sorted(got), keys_ok, id_ok, cross))


def check_contract(tmp, db):
    report = collect_with(db)
    keys_ok = set(OLD_KEYS + ["dossiers", "refunds"]) <= set(report)
    led, mtr, dk, am = open_stack(db)
    try:
        old_ok = (report["market"] == am.api_market_stats()
                  and report["market_months"] == am.api_market_months()
                  and report["board"] == am.api_board()
                  and report["activity"] == am.api_market_feed(
                      limit=R.FEED_LIMIT)
                  and report["attention"] == R.collect_attention(am, report))
        # R2110 repaired this birth station: the v4 buyer key set below
        # stays pinned as a literal SUBSET, because the additive v5 bump
        # adds the "history" key. Pinning the exact set here would make
        # every later additive buyer face look like a regression.
        buyer_ok = all(
            set(["months", "profile", "todo", "watch_alerts"]) <=
            set(report["buyers"][b])
            for b in report["buyers"])
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    out = os.path.join(tmp, "dos.html")
    js = os.path.join(tmp, "dos.json")
    R.main(["--db", db, "--out", out, "--json-out", js])
    doc = json.loads(io.open(js, "r", encoding="utf-8").read())
    env_ok = sorted(doc) == ["attention", "report", "schema_version"]
    record("AC-AMLD2",
           R.REPORT_SCHEMA >= 4 and keys_ok and old_ok and buyer_ok
           and env_ok and doc.get("schema_version") == R.REPORT_SCHEMA
           and doc["report"]["dossiers"] == report["dossiers"],
           "schema=%d top=%s old=%s buyer=%s env=%s json_same=%s"
           % (R.REPORT_SCHEMA, keys_ok, old_ok, buyer_ok, env_ok,
              doc["report"].get("dossiers") == report["dossiers"]))


def check_same_source(db, target):
    report = collect_with(db)
    same = all(report["dossiers"][key] == direct_block(db, int(key))
               for key in report["dossiers"])
    before = report["dossiers"][str(target)]["price_history"]
    before_view = report["dossiers"][str(target)]["view"]["token_price"]
    led, mtr, dk, am = open_stack(db)
    try:
        am.revise_price("usr:dana", target, 21)
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    after = collect_with(db)["dossiers"][str(target)]
    grew = (after["price_history"]["revision_count"]
            == before["revision_count"] + 1
            and after["price_history"]["revisions"][-1]["token_price"] == 21
            and after["view"]["token_price"] == 21)
    record("AC-AMLD3", same and grew,
           "same_source=%s revisions %d->%d price %s->%s"
           % (same, before["revision_count"],
              after["price_history"]["revision_count"],
              before_view, after["view"]["token_price"]))


def check_retired(db, retired_id):
    report = collect_with(db)
    _rows, board = market_ids(db)
    block = (report.get("dossiers") or {}).get(str(retired_id)) or {}
    view = block.get("view") or {}
    life = block.get("lifecycle") or {}
    board_ids = set(row["listing_id"] for row in board)
    events = [item["event"] for item in (life.get("history") or [])]
    ok = (bool(block) and view.get("delisted") is True
          and isinstance(view.get("delisted_utc"), str)
          and life.get("delist_count") == 1 and "delist" in events
          and retired_id not in board_ids
          and "price_history" in block and "ratings" in block)
    record("AC-AMLD4", ok,
           "present=%s delisted=%s delist_count=%s events=%s board=%s"
           % (bool(block), view.get("delisted"),
              life.get("delist_count"), events, retired_id not in board_ids))


def check_html(tmp, db):
    out = os.path.join(tmp, "dos.html")
    if not os.path.isfile(out):
        R.main(["--db", db, "--out", out])
    page = io.open(out, "r", encoding="utf-8").read()
    dossiers = collect_with(db)["dossiers"]
    body = section(page)
    blocks = body.count("<h3>#")
    heads_ok = all(head in body for head in DOSSIER_HEADS)
    cols_ok = ("<th>revision_id</th>" in body
               and "<th>event</th>" in body
               and "<th>rating_id</th>" in body)
    empty_tmp, empty_db, _ = fresh_world("empty", seed=False)
    empty_out = os.path.join(empty_tmp, "empty.html")
    R.main(["--db", empty_db, "--out", empty_out])
    empty_page = io.open(empty_out, "r", encoding="utf-8").read()
    empty_ok = R.DOSSIER_EMPTY in section(empty_page)
    record("AC-AMLD5",
           blocks == len(dossiers) and heads_ok and cols_ok and empty_ok,
           "blocks=%d dossiers=%d heads=%s cols=%s empty=%s"
           % (blocks, len(dossiers), heads_ok, cols_ok, empty_ok))


def check_escape(tmp, db):
    hostile = "Evil <script>alert('dossier')</script> & \"quote\""
    led, mtr, dk, am = open_stack(db)
    try:
        am.publish_api("usr:dana", "evil-dossier-key", hostile,
                       "hostile dossier probe", R.PAYLOAD, 4, False)
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
    record("AC-AMLD6", raw_absent and escaped_present and markers,
           "raw_absent=%s escaped=%s markers=%s"
           % (raw_absent, escaped_present, markers))


def check_pure_read(db):
    before = table_digest(db)
    report = collect_with(db)
    after = table_digest(db)
    record("AC-AMLD7", before == after and "dossiers" in report,
           "digest_same=%s tx=%d dossiers=%d"
           % (before == after, after[1], len(report["dossiers"])))


def check_determinism_degrade_regression():
    pages = []
    docs = []
    for tag in ("d1", "d2"):
        tmp, db, _ids = fresh_world(tag)
        out = os.path.join(tmp, "d.html")
        js = os.path.join(tmp, "d.json")
        R.main(["--db", db, "--out", out, "--json-out", js])
        pages.append(io.open(out, "rb").read())
        docs.append(io.open(js, "rb").read())
    det_ok = pages[0] == pages[1] and docs[0] == docs[1]

    tmp, db, _ids = fresh_world("degrade")
    report = collect_with(db)
    legacy = copy.deepcopy(report)
    legacy.pop("dossiers", None)
    texture = ""
    degrade_ok = False
    try:
        page = R.render_html(legacy)
        degrade_ok = (isinstance(page, str)
                      and R.DOSSIER_EMPTY in section(page))
        texture = "len=%d" % len(page)
    except KeyError as exc:
        texture = "KeyError %r" % (exc,)

    base = os.path.dirname(BASE)
    labels = ("test_apimarket_report.py",
              "test_apimarket_report_attention.py",
              "test_apimarket_report_json.py",
              "test_apimarket_report_workbench.py",
              "test_apimarket_report_activity.py")
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
        wired = ('"ledger-apimarket-reportdossier"' in src
                 and "test_apimarket_report_dossier.py" in src)
    except OSError:
        wired = False
    record("AC-AMLD8",
           det_ok and degrade_ok and all(c == 0 for c in codes) and wired,
           "det=%s html_sha16=%s degrade=%s(%s) rc=%s wired=%s"
           % (det_ok, hashlib.sha256(pages[0]).hexdigest()[:16],
              degrade_ok, texture, codes, wired))


def main():
    tmp, db, ids = fresh_world("main")
    rich_id = rich_world(db, ids)
    retired_id = ids["listings"][2]
    check_shape(db)
    check_contract(tmp, db)
    check_same_source(db, rich_id)
    check_retired(db, retired_id)
    check_html(tmp, db)
    check_escape(tmp, db)
    check_pure_read(db)
    check_determinism_degrade_regression()
    failed = [ac for ac, ok, _ in RESULTS if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              len(RESULTS) - len(failed), len(RESULTS)))
    if failed:
        print("FAILED: %s" % ",".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())