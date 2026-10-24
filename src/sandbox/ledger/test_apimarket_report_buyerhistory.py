"""Acceptance suite for the buyer history section on the apimarket
settlement report (BigDomain R2110; canon = the R2110 explore-queue
claim row, criteria AC-AMBD1..AC-AMBD8 registered there BEFORE this code
existed - honesty law; the AC-AMBD prefix, collect_buyer_history,
BUYER_HISTORY_KEYS, buyer_history_block, this suite name and the
ledger-apimarket-buyerhistory runner label were all git grep -F
zero-occupancy anchored 2026-10-25, rc=1).

Product under proof: apimarket_report.py reads the four buyer-side
history faces once per buyer (api_library, api_watchlist, api_refund,
api_rating_history) into a per-buyer "history" block and renders it as
four sub-tables inside the Buyers section, so those faces stop being
faces with zero consumers.

Truthful defect note (why the api_ratings change is in this window):
api_rating_history accepts only a rating_id, and no listing-wide face
exposed one - it surfaced solely through the seller inbox, and only for
unanswered ratings - so the history face was unreachable. The rating
rows now carry rating_id as an ADDITIVE key; every earlier key keeps
its value (AC-AMBD4 pins both sides).

Criteria:
  AC-AMBD1 Derived set: the buyer keys are exactly the buyers named on
    the market's own sales rows, and every history block carries exactly
    BUYER_HISTORY_KEYS four keys (no hardcoded roster).
  AC-AMBD2 Same source + no cache: every block equals the direct face
    calls, and a watch added after a collect shows up on the next one.
  AC-AMBD3 Refund provenance: the refunds rows are exactly the refunded
    purchases of the library (count and ascending purchase_id agree,
    live purchases never appear) with the disclaimer stripped.
  AC-AMBD4 Rating history reachable: api_ratings rows expose rating_id
    additively, every history envelope belongs to that buyer and that
    listing, a base-only rating renders one base row while a revised one
    renders revision rows, and effective_stars equals the last revision.
  AC-AMBD5 Additive contract: REPORT_SCHEMA 4 -> 5, the JSON envelope
    still has exactly schema_version/report/attention, every earlier
    report value is unchanged and the buyer blocks keep their v4 keys.
  AC-AMBD6 HTML surface + markers: every buyer carries the four
    sub-table heads with honest empty states, a hostile listing title is
    escaped, and the AIGC marker and disclaimer survive.
  AC-AMBD7 Pure read + determinism: thirteen table digests and the
    ledger tx count are unchanged by a collect, and two seeded worlds
    render byte-identical HTML and JSON.
  AC-AMBD8 Degrade + regression: a legacy report dict without the
    history key still renders, the six earlier report suites still pass
    and the runner label is registered.

Usage: python test_apimarket_report_buyerhistory.py
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
V4_KEYS = ["activity", "attention", "board", "buyers", "dossiers",
           "market", "market_months", "sellers"]
V4_BUYER_KEYS = ["months", "profile", "todo", "watch_alerts"]
HEADS = ("library (", "watchlist (", "refunds (", "rating history (")


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
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerhistory-" + tag + "-")
    db = os.path.join(tmp, "ledger.db")
    led, mtr, dk, am = R.build_stack(db)
    ids = R.seed_demo(am, led, dk) if seed else None
    am.close()
    dk.close()
    mtr.close()
    led.close()
    return tmp, db, ids


def open_stack(db):
    return R.build_stack(db)


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
    """Extend the seeded world so every history sub-table has content:
    two live watches, one revised rating and one unwatch.

    Honest note: the first draft wrote these with the real clock, which
    made two "identical" seeded worlds differ in watched_utc /
    revised_utc and broke AC-AMBD7. Both clocks the write faces read
    are pinned here, exactly as seed_demo does."""
    d1, d2, d3 = ids["listings"]
    led, mtr, dk, am = open_stack(db)
    orig = None
    try:
        import apimarket as A
        import ledger as L
        orig = (A._now_utc, L.now_utc)
        A._now_utc = lambda: "2026-10-20T12:00:00Z"
        L.now_utc = lambda: "2026-10-20T12:00:00Z"
        am.watch_api("usr:carol", d3)
        am.watch_api("usr:carol", d2)
        am.watch_api("usr:erin", d1)
        am.unwatch_api("usr:erin", d1)
        rows = am.api_ratings(d1)["ratings"]
        carol = [row for row in rows if row["buyer_id"] == "usr:carol"][0]
        am.revise_rating("usr:carol", carol["rating_id"], 3)
    finally:
        if orig is not None:
            import apimarket as A
            import ledger as L
            A._now_utc, L.now_utc = orig
        am.close()
        dk.close()
        mtr.close()
        led.close()


def derived_buyers(db):
    led, mtr, dk, am = open_stack(db)
    try:
        sellers = sorted({row["dev_account"]
                          for row in am.api_board()["listings"]})
        buyers = set()
        for dev in sellers:
            for row in am.api_sales(dev)["sales"]:
                buyers.add(row["buyer_id"])
        return buyers
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()


def direct_history(db, buyer):
    led, mtr, dk, am = open_stack(db)
    try:
        library = am.api_library(buyer)
        refunds = []
        history = []
        for row in library["purchases"]:
            if row["refunded"]:
                env = am.api_refund(row["purchase_id"])
                refunds.append(dict((k, v) for k, v in env.items()
                                    if k != "disclaimer"))
            if row["my_rating"] is None:
                continue
            for rated in am.api_ratings(row["listing_id"])["ratings"]:
                if rated["buyer_id"] == buyer:
                    history.append(
                        am.api_rating_history(rated["rating_id"]))
        return {"library": library, "watchlist": am.api_watchlist(buyer),
                "refunds": refunds, "rating_history": history}
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()


def buyers_section(page):
    start = page.index("<h2>Buyers</h2>")
    end = page.index("<footer>", start)
    return page[start:end]


def check_shape(db):
    report = collect_with(db)
    want = derived_buyers(db)
    got = set(report["buyers"])
    keys_ok = all(sorted(block["history"]) == sorted(R.BUYER_HISTORY_KEYS)
                  for block in report["buyers"].values())
    record("AC-AMBD1", want == got and keys_ok and len(got) > 0,
           "buyers=%s keys_ok=%s" % (sorted(got), keys_ok))


def check_contract(tmp, db):
    report = collect_with(db)
    top_ok = sorted(report) == sorted(V4_KEYS)
    buyer_ok = all(sorted(block) == sorted(V4_BUYER_KEYS + ["history"])
                   for block in report["buyers"].values())
    led, mtr, dk, am = open_stack(db)
    try:
        old_ok = (report["market"] == am.api_market_stats()
                  and report["market_months"] == am.api_market_months()
                  and report["board"] == am.api_board()
                  and report["activity"] == am.api_market_feed(
                      limit=R.FEED_LIMIT)
                  and report["attention"] == R.collect_attention(am, report)
                  and all(report["dossiers"][key]["view"]
                          == am.api_view(int(key))
                          for key in report["dossiers"]))
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    out = os.path.join(tmp, "bh.html")
    js = os.path.join(tmp, "bh.json")
    R.main(["--db", db, "--out", out, "--json-out", js])
    doc = json.loads(io.open(js, "r", encoding="utf-8").read())
    env_ok = sorted(doc) == ["attention", "report", "schema_version"]
    record("AC-AMBD5",
           R.REPORT_SCHEMA == 5 and top_ok and buyer_ok and old_ok
           and env_ok and doc.get("schema_version") == 5
           and doc["report"]["buyers"] == report["buyers"],
           "schema=%d top=%s buyer=%s old=%s env=%s json_same=%s"
           % (R.REPORT_SCHEMA, top_ok, buyer_ok, old_ok, env_ok,
              doc["report"]["buyers"] == report["buyers"]))


def check_same_source(db, watch_target):
    report = collect_with(db)
    same = all(report["buyers"][b]["history"] == direct_history(db, b)
               for b in report["buyers"])
    before = report["buyers"]["usr:bob"]["history"]["watchlist"][
        "watch_count"]
    led, mtr, dk, am = open_stack(db)
    try:
        am.watch_api("usr:bob", watch_target)
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    after = collect_with(db)["buyers"]["usr:bob"]["history"]["watchlist"]
    grew = (after["watch_count"] == before + 1
            and watch_target in [row["listing_id"] for row in
                                 after["watches"]])
    record("AC-AMBD2", same and grew,
           "same_source=%s watch_count %d->%d grew=%s"
           % (same, before, after["watch_count"], grew))


def check_refunds(db):
    report = collect_with(db)
    ok = True
    detail = []
    for buyer, block in sorted(report["buyers"].items()):
        history = block["history"]
        library = history["library"]
        refunds = history["refunds"]
        ids = [row["purchase_id"] for row in refunds]
        count_ok = len(refunds) == library["refund_count"]
        order_ok = ids == sorted(ids)
        live_ok = all(purchase["refunded"] for purchase in
                      library["purchases"]
                      if purchase["purchase_id"] in ids)
        absent_ok = all(purchase["purchase_id"] not in ids
                        for purchase in library["purchases"]
                        if not purchase["refunded"])
        direct_ok = all(
            row == dict((k, v) for k, v in
                        direct_refund(db, row["purchase_id"]).items()
                        if k != "disclaimer")
            for row in refunds)
        ok = ok and count_ok and order_ok and live_ok and absent_ok \
            and direct_ok
        detail.append("%s:%d/%d" % (buyer, len(refunds),
                                    library["refund_count"]))
    record("AC-AMBD3", ok, "counts=%s order/live/absent/direct=%s"
           % (",".join(detail), ok))


def direct_refund(db, purchase_id):
    led, mtr, dk, am = open_stack(db)
    try:
        return am.api_refund(purchase_id)
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()


def check_rating_history(db):
    report = collect_with(db)
    ratings_by_listing = {}
    raw = []
    if report["dossiers"]:
        first = int(sorted(report["dossiers"], key=int)[0])
        led, mtr, dk, am = open_stack(db)
        try:
            raw = am.api_ratings(first)["ratings"]
        finally:
            am.close()
            dk.close()
            mtr.close()
            led.close()
    key_ok = bool(raw) and all("rating_id" in row for row in raw)
    led, mtr, dk, am = open_stack(db)
    try:
        for key in report["dossiers"]:
            ratings_by_listing[int(key)] = am.api_ratings(int(key))
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()

    owner_ok = True
    effective_ok = True
    base_rows = 0
    revision_rows = 0
    for buyer, block in sorted(report["buyers"].items()):
        for env in block["history"]["rating_history"]:
            owner_ok = owner_ok and env["buyer_id"] == buyer
            rows = [row for row in
                    ratings_by_listing[env["listing_id"]]["ratings"]
                    if row["buyer_id"] == buyer]
            owner_ok = owner_ok and bool(rows) and any(
                row["rating_id"] == env["rating_id"] for row in rows)
            if env["revision_count"]:
                revision_rows += 1
                effective_ok = (effective_ok
                                and env["effective_stars"]
                                == env["revisions"][-1]["stars"])
            else:
                base_rows += 1
    flat = R.rating_history_rows(
        [env for block in report["buyers"].values()
         for env in block["history"]["rating_history"]])
    flat_ok = (len(flat) == base_rows + sum(
        env["revision_count"] for block in report["buyers"].values()
        for env in block["history"]["rating_history"]))
    record("AC-AMBD4",
           key_ok and owner_ok and effective_ok and flat_ok
           and base_rows >= 1 and revision_rows >= 1,
           "rating_id_key=%s owner=%s effective=%s flat=%s base=%d rev=%d"
           % (key_ok, owner_ok, effective_ok, flat_ok, base_rows,
              revision_rows))


def check_html(tmp, db):
    out = os.path.join(tmp, "bh.html")
    if not os.path.isfile(out):
        R.main(["--db", db, "--out", out])
    page = io.open(out, "r", encoding="utf-8").read()
    report = collect_with(db)
    body = buyers_section(page)
    heads_ok = all(head in body for head in HEADS)
    blocks_ok = body.count("buyer history</h3>") == len(report["buyers"])
    empty_ok = ("no watches" in body and "no ratings" in body
                and "no refunds" in body)
    cols_ok = ("<th>rating_id</th>" in body and "<th>previous_stars</th>"
               in body and "<th>refund_tx</th>" in body)
    record("AC-AMBD6", heads_ok and blocks_ok and empty_ok and cols_ok,
           "heads=%s blocks=%s empty_states=%s cols=%s"
           % (heads_ok, blocks_ok, empty_ok, cols_ok))


def check_escape(tmp, db):
    hostile = "Evil <script>alert('buyer')</script> & \"quote\""
    led, mtr, dk, am = open_stack(db)
    try:
        lid = am.publish_api("usr:dana", "evil-buyer-key", hostile,
                             "hostile buyer probe", R.PAYLOAD, 4,
                             False)["listing_id"]
        am.purchase_api("usr:bob", lid, "ref-bob-evil")
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    out = os.path.join(tmp, "esc.html")
    R.main(["--db", db, "--out", out])
    page = io.open(out, "r", encoding="utf-8").read()
    body = buyers_section(page)
    raw_absent = "<script>alert(" not in body
    escaped_present = "&lt;script&gt;" in body
    markers = (R.MARKER in page
               and R.DISCLAIMER.split(":")[0] in page)
    record("AC-AMBD6-esc", raw_absent and escaped_present and markers,
           "raw_absent=%s escaped=%s markers=%s"
           % (raw_absent, escaped_present, markers))


def check_pure_read(db):
    before = table_digest(db)
    report = collect_with(db)
    after = table_digest(db)
    record("AC-AMBD7-read", before == after and bool(report["buyers"]),
           "digest_same=%s tx=%d buyers=%d"
           % (before == after, after[1], len(report["buyers"])))


def check_determinism():
    pages = []
    docs = []
    for tag in ("d1", "d2"):
        tmp, db, ids = fresh_world(tag)
        rich_world(db, ids)
        out = os.path.join(tmp, "d.html")
        js = os.path.join(tmp, "d.json")
        R.main(["--db", db, "--out", out, "--json-out", js])
        pages.append(io.open(out, "rb").read())
        docs.append(io.open(js, "rb").read())
    det_ok = pages[0] == pages[1] and docs[0] == docs[1]
    record("AC-AMBD7-det", det_ok,
           "html_sha16=%s json_same=%s"
           % (hashlib.sha256(pages[0]).hexdigest()[:16], docs[0] == docs[1]))


def check_degrade_regression():
    tmp, db, ids = fresh_world("degrade")
    rich_world(db, ids)
    report = collect_with(db)
    legacy = copy.deepcopy(report)
    for block in legacy["buyers"].values():
        block.pop("history", None)
    texture = ""
    degrade_ok = False
    try:
        page = R.render_html(legacy)
        body = buyers_section(page)
        degrade_ok = (isinstance(page, str) and "no purchases" in body
                      and "no watches" in body and "no refunds" in body)
        texture = "len=%d" % len(page)
    except KeyError as exc:
        texture = "KeyError %r" % (exc,)

    base = os.path.dirname(BASE)
    labels = ("test_apimarket_report.py",
              "test_apimarket_report_attention.py",
              "test_apimarket_report_json.py",
              "test_apimarket_report_workbench.py",
              "test_apimarket_report_activity.py",
              "test_apimarket_report_dossier.py")
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
        wired = ('"ledger-apimarket-buyerhistory"' in src
                 and "test_apimarket_report_buyerhistory.py" in src)
    except OSError:
        wired = False
    record("AC-AMBD8", degrade_ok and all(c == 0 for c in codes) and wired,
           "degrade=%s(%s) rc=%s wired=%s"
           % (degrade_ok, texture, codes, wired))


def main():
    tmp, db, ids = fresh_world("main")
    rich_world(db, ids)
    check_shape(db)
    check_contract(tmp, db)
    check_same_source(db, int(ids["listings"][2]))
    check_refunds(db)
    check_rating_history(db)
    check_html(tmp, db)
    check_escape(tmp, db)
    check_pure_read(db)
    check_determinism()
    check_degrade_regression()
    failed = [ac for ac, ok, _ in RESULTS if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              len(RESULTS) - len(failed), len(RESULTS)))
    if failed:
        print("FAILED: %s" % ",".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())