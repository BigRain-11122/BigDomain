"""Acceptance suite for the market-wide refund register and its
settlement-report section (BigDomain R2111; canon = the R2111
explore-queue claim row, criteria AC-AMRR1..AC-AMRR8 registered there
BEFORE this code existed - honesty law; the AC-AMRR prefix,
api_refund_register, REFUND_KEYS, refund_block, this suite name and the
ledger-apimarket-refundregister runner label were all git grep -F
zero-occupancy anchored 2026-10-25, rc=1).

Product under proof: apimarket.api_refund_register() answers the
operator question "what came back, when, from which seller and which
listing" over one row set, and apimarket_report.py renders it as a
Refund register section. Refunds were previously reachable only per
purchase (api_refund) or per buyer (the R2110 history block), so every
settlement reconciliation merged those views by hand.

Truthful defect note (why two earlier suites changed in this window):
the report's top-level key set and the REPORT_SCHEMA literal are part
of the additive contract, so the R2108/R2109/R2110 suites are widened
to the v6 key set (activity/dossier: + "refunds"; buyerhistory: 5 -> 6
and V6_KEYS). No earlier report value changed - AC-AMRR5 re-proves it
from the faces.

Criteria:
  AC-AMRR1 Contract + derived set: the refunds block carries exactly
    the thirteen pinned keys, refund_count == len(refunds), and a world
    with no refunds reports an honest empty register.
  AC-AMRR2 Same source, no cache: the report value equals a direct
    api_refund_register() call, a refund created after a collect shows
    up on the next collect, and the dev_account / listing_id filters
    narrow exactly.
  AC-AMRR3 Half-open window: a row stamped exactly at since is in, one
    exactly at until is out, since>until raises E_AM_BAD_WINDOW, and a
    window intersected with a seller filter equals the two filters
    applied together.
  AC-AMRR4 Money conservation: every row satisfies dev_share +
    platform_share == amount and equals the stored apimarket_refunds
    row field by field; month sums, developer sums and totals agree.
  AC-AMRR5 Additive contract: REPORT_SCHEMA is 6, the JSON envelope
    still has exactly schema_version/report/attention, and every earlier
    report block still equals its direct face call.
  AC-AMRR6 Gate family fail-closed: eleven bad window/filter forms are
    rejected with E_AM_BAD_WINDOW or E_AM_BAD_ARGS, and each refusal
    leaves the thirteen table digests and the ledger tx count unchanged.
  AC-AMRR7 Pure read + determinism: a collect mutates no row and moves
    no token, and two same-seed worlds render byte-identical HTML and
    JSON.
  AC-AMRR8 HTML surface + degrade + regression: the page carries the
    Refund register section with its three sub-table heads, a hostile
    reason is escaped, a legacy report dict without the key still
    renders the honest empty state, the seven earlier report suites
    pass and the runner label is registered.

Usage: python test_apimarket_report_refundregister.py
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
V6_KEYS = ["activity", "attention", "board", "buyers", "dossiers",
           "market", "market_months", "refunds", "sellers"]
BLOCK_KEYS = ["kind", "since_utc", "until_utc", "dev_account",
              "listing_id", "refund_count", "amount", "dev_share",
              "platform_share", "months", "by_dev", "refunds",
              "disclaimer"]
V5_BUYER_KEYS = ["history", "months", "profile", "todo", "watch_alerts"]
HEADS = ("refunds by month (", "refunds by developer (", "refunds rows (")
EARLIER = ("test_apimarket_report.py",
           "test_apimarket_report_attention.py",
           "test_apimarket_report_json.py",
           "test_apimarket_report_workbench.py",
           "test_apimarket_report_activity.py",
           "test_apimarket_report_dossier.py",
           "test_apimarket_report_buyerhistory.py")


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
    tmp = tempfile.mkdtemp(prefix="apimarket-refundreg-" + tag + "-")
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


def direct_register(db, **kwargs):
    led, mtr, dk, am = open_stack(db)
    try:
        return am.api_refund_register(**kwargs)
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()


def stored_refunds(db):
    market_db = os.path.join(os.path.dirname(db), "apimarket.db")
    conn = sqlite3.connect(market_db)
    try:
        return conn.execute(
            "SELECT refund_id, purchase_id, listing_id, buyer_id,"
            " dev_account, amount, dev_share, platform_share,"
            " refund_tx, refunded_utc, reason"
            " FROM apimarket_refunds ORDER BY refunded_utc, refund_id"
        ).fetchall()
    finally:
        conn.close()


def purchase_of(db, buyer):
    """First still-live purchase id of one buyer (the suite only needs
    one legal refund target per rounding)."""
    led, mtr, dk, am = open_stack(db)
    try:
        for row in am.api_library(buyer)["purchases"]:
            if not row["refunded"]:
                return row["purchase_id"]
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    raise AssertionError("no live purchase for %s" % buyer)


def add_refund(db, buyer, purchase_id, reason, stamp):
    """Create one refund with both clocks pinned (the R2110 lesson: the
    real clock would make two 'identical' worlds differ)."""
    led, mtr, dk, am = open_stack(db)
    try:
        import apimarket as A
        import ledger as L
        orig = (A._now_utc, L.now_utc)
        A._now_utc = lambda: stamp
        L.now_utc = lambda: stamp
        try:
            return am.refund_api(buyer, purchase_id, reason)
        finally:
            A._now_utc, L.now_utc = orig
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()


def check_shape(db):
    report = collect_with(db)
    block = report.get("refunds") or {}
    keys_ok = sorted(block) == sorted(BLOCK_KEYS)
    count_ok = block.get("refund_count") == len(block.get("refunds") or [])
    rows = block.get("refunds") or []
    row_keys = ("refund_id", "purchase_id", "listing_id", "listing_key",
                "title", "buyer_id", "dev_account", "amount", "dev_share",
                "platform_share", "refund_tx", "refunded_utc", "reason")
    rows_ok = all(sorted(row) == sorted(row_keys) for row in rows)
    record("AC-AMRR1", keys_ok and count_ok and rows_ok and len(rows) == 2,
           "keys=%s count=%s rows=%d rows_ok=%s"
           % (keys_ok, block.get("refund_count"), len(rows), rows_ok))

    empty_tmp, empty_db, _ = fresh_world("empty", seed=False)
    empty = collect_with(empty_db)["refunds"]
    empty_ok = (empty["refund_count"] == 0 and empty["amount"] == 0
                and empty["dev_share"] == 0 and empty["platform_share"] == 0
                and empty["months"] == [] and empty["by_dev"] == []
                and empty["refunds"] == [])
    page_empty = R.render_html({"market": {}, "market_months": {"months": []},
                                "board": {"listings": []}, "sellers": {},
                                "buyers": {}, "refunds": empty})
    record("AC-AMRR1-empty", empty_ok and R.REFUND_EMPTY in page_empty,
           "count=%s sums=%s/%s/%s empty_text=%s"
           % (empty["refund_count"], empty["amount"], empty["dev_share"],
              empty["platform_share"], R.REFUND_EMPTY in page_empty))


def check_same_source(db, ids):
    report = collect_with(db)
    same = report["refunds"] == direct_register(db)
    d1 = ids["listings"][0]
    dev = report["refunds"]["refunds"][0]["dev_account"]
    by_dev = direct_register(db, dev_account=dev)
    by_listing = direct_register(db, listing_id=d1)
    dev_ok = (by_dev["refund_count"] > 0
              and all(row["dev_account"] == dev
                      for row in by_dev["refunds"]))
    listing_ok = (by_listing["refund_count"] > 0
                  and all(row["listing_id"] == d1
                          for row in by_listing["refunds"]))
    extra = add_refund(db, "usr:carol", purchase_of(db, "usr:carol"),
                       "late addition", "2026-10-20T00:00:00Z")
    after = collect_with(db)["refunds"]
    grew = (after["refund_count"] == report["refunds"]["refund_count"] + 1
            and after["refunds"][-1]["refund_id"] == extra["refund_id"])
    record("AC-AMRR2", same and dev_ok and listing_ok and grew,
           "same=%s dev=%s/%d listing=%s/%d grew=%s"
           % (same, dev_ok, by_dev["refund_count"], listing_ok,
              by_listing["refund_count"], grew))


def check_window(db):
    full = direct_register(db)
    window = direct_register(db, since_utc="2026-10-02T00:00:00Z",
                             until_utc="2026-10-03T00:00:00Z")
    inside = [row["refunded_utc"] for row in window["refunds"]]
    half_open = (window["refund_count"] == 1
                 and inside == ["2026-10-02T00:00:00Z"])
    empty = direct_register(db, since_utc="2026-10-03T00:00:00Z",
                            until_utc="2026-10-03T00:00:00Z")
    empty_ok = empty["refund_count"] == 0
    inverted = None
    try:
        direct_register(db, since_utc="2026-10-03T00:00:00Z",
                        until_utc="2026-10-02T00:00:00Z")
    except Exception as exc:                       # noqa: BLE001
        inverted = getattr(exc, "code", None) or str(exc)
    dev = full["refunds"][0]["dev_account"]
    both = direct_register(db, since_utc="2026-10-02T00:00:00Z",
                           until_utc="2026-10-04T00:00:00Z",
                           dev_account=dev)
    dev_only = direct_register(db, dev_account=dev)
    window_only = direct_register(db, since_utc="2026-10-02T00:00:00Z",
                                  until_utc="2026-10-04T00:00:00Z")
    inter = set(row["refund_id"] for row in dev_only["refunds"]) & set(
        row["refund_id"] for row in window_only["refunds"])
    inter_ok = (set(row["refund_id"] for row in both["refunds"]) == inter
                and both["refund_count"] == len(inter))
    record("AC-AMRR3", half_open and empty_ok and inverted == "E_AM_BAD_WINDOW"
           and inter_ok,
           "half_open=%s/%s empty=%s inverted=%s inter=%s/%d"
           % (half_open, inside, empty_ok, inverted, inter_ok,
              both["refund_count"]))


def check_money(db):
    block = direct_register(db)
    stored = stored_refunds(db)
    rows = block["refunds"]
    per_row = (len(stored) == len(rows)
               and all(int(s[0]) == r["refund_id"]
                       and int(s[1]) == r["purchase_id"]
                       and int(s[2]) == r["listing_id"]
                       and s[3] == r["buyer_id"]
                       and s[4] == r["dev_account"]
                       and int(s[5]) == r["amount"]
                       and int(s[6]) == r["dev_share"]
                       and int(s[7]) == r["platform_share"]
                       and s[8] == r["refund_tx"]
                       and s[9] == r["refunded_utc"]
                       and s[10] == r["reason"]
                       for s, r in zip(stored, rows)))
    split_ok = all(row["dev_share"] + row["platform_share"] == row["amount"]
                   for row in rows)
    totals = (block["amount"] == sum(row["amount"] for row in rows)
              and block["dev_share"] == sum(row["dev_share"] for row in rows)
              and block["platform_share"] == sum(row["platform_share"]
                                                 for row in rows))
    month_ok = (sum(row["amount"] for row in block["months"])
                == block["amount"]
                and sum(row["refund_count"] for row in block["months"])
                == block["refund_count"])
    dev_ok = (sum(row["amount"] for row in block["by_dev"])
              == block["amount"]
              and sum(row["refund_count"] for row in block["by_dev"])
              == block["refund_count"])
    ordered = ([row["month"] for row in block["months"]]
               == sorted(row["month"] for row in block["months"])
               and [row["dev_account"] for row in block["by_dev"]]
               == sorted(row["dev_account"] for row in block["by_dev"]))
    record("AC-AMRR4", per_row and split_ok and totals and month_ok
           and dev_ok and ordered,
           "per_row=%s split=%s totals=%s months=%s dev=%s order=%s"
           % (per_row, split_ok, totals, month_ok, dev_ok, ordered))


def check_contract(tmp, db):
    report = collect_with(db)
    keys_ok = sorted(report) == sorted(V6_KEYS)
    # R2119 birth-station repair: the buyer block legally gained the
    # questions key (additive), so every v5 key must still be there
    # rather than the full key set being frozen.
    buyers_ok = all(set(V5_BUYER_KEYS) <= set(block)
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
    out = os.path.join(tmp, "c.html")
    js = os.path.join(tmp, "c.json")
    R.main(["--db", db, "--out", out, "--json-out", js])
    doc = json.loads(io.open(js, "r", encoding="utf-8").read())
    env_ok = sorted(doc) == ["attention", "report", "schema_version"]
    record("AC-AMRR5", R.REPORT_SCHEMA >= 6 and keys_ok and buyers_ok
           and old_ok and env_ok and doc.get("schema_version") == R.REPORT_SCHEMA
           and doc["report"]["refunds"] == report["refunds"],
           "schema=%d keys=%s buyers=%s old=%s env=%s json_same=%s"
           % (R.REPORT_SCHEMA, keys_ok, buyers_ok, old_ok, env_ok,
              doc["report"]["refunds"] == report["refunds"]))


def check_gates(db):
    before = table_digest(db)
    bad_forms = (
        ("window", {"since_utc": "2026-10-02T00:00:00"}, "E_AM_BAD_WINDOW"),
        ("window", {"until_utc": "2026-10-2T00:00:00Z"}, "E_AM_BAD_WINDOW"),
        ("window", {"since_utc": 20261002}, "E_AM_BAD_WINDOW"),
        ("window", {"until_utc": "2026-10-03 00:00:00Z"},
         "E_AM_BAD_WINDOW"),
        ("window", {"since_utc": "2026-10-03T00:00:00Z",
                    "until_utc": "2026-10-02T00:00:00Z"},
         "E_AM_BAD_WINDOW"),
        ("filter", {"dev_account": 5}, "E_AM_BAD_ARGS"),
        ("filter", {"dev_account": ""}, "E_AM_BAD_ARGS"),
        ("filter", {"listing_id": 0}, "E_AM_BAD_ARGS"),
        ("filter", {"listing_id": -3}, "E_AM_BAD_ARGS"),
        ("filter", {"listing_id": True}, "E_AM_BAD_ARGS"),
        ("filter", {"listing_id": "3"}, "E_AM_BAD_ARGS"))
    codes = []
    for label, kwargs, want in bad_forms:
        got = None
        try:
            direct_register(db, **kwargs)
        except Exception as exc:                   # noqa: BLE001
            got = getattr(exc, "code", None) or str(exc)
        codes.append((label, got, want))
    after = table_digest(db)
    ok = (all(got == want for _, got, want in codes)
          and before == after)
    bad = [row for row in codes if row[1] != row[2]]
    record("AC-AMRR6", ok, "forms=%d bad=%s digests_same=%s"
           % (len(codes), bad, before == after))


def check_pure_read(db):
    before = table_digest(db)
    collect_with(db)
    after = table_digest(db)
    record("AC-AMRR7-read", before == after,
           "digest=%s tx=%s" % (after[0][:16], after[1]))


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
    det_ok = pages[0] == pages[1] and docs[0] == docs[1]
    record("AC-AMRR7-det", det_ok,
           "html_sha16=%s json_same=%s"
           % (hashlib.sha256(pages[0]).hexdigest()[:16], docs[0] == docs[1]))


def register_section(page, starts=("Refund register",)):
    start = page.index("<h2>%s</h2>" % starts[0])
    end = page.index("<h2>", start + 4)
    return page[start:end]


def check_html(tmp, db):
    report = collect_with(db)
    page = R.render_html(report)
    section = register_section(page)
    heads_ok = all(head in section for head in HEADS)
    marker_ok = R.MARKER in page and report["refunds"]["disclaimer"] in page
    record("AC-AMRR8-html", heads_ok and marker_ok,
           "heads=%s marker=%s section_len=%d"
           % (heads_ok, marker_ok, len(section)))

    legacy = copy.deepcopy(report)
    legacy.pop("refunds", None)
    page_legacy = R.render_html(legacy)
    legacy_ok = R.REFUND_EMPTY in register_section(page_legacy)
    record("AC-AMRR8-degrade", legacy_ok,
           "empty=%s" % R.REFUND_EMPTY)

    esc_tmp, esc_db, esc_ids = fresh_world("escape")
    hostile = "<script>alert('refund')</script>"
    add_refund(esc_db, "usr:carol", purchase_of(esc_db, "usr:carol"), hostile,
               "2026-10-25T00:00:00Z")
    page_esc = R.render_html(collect_with(esc_db))
    escaped = ("<script>alert" not in page_esc
               and "&lt;script&gt;alert" in page_esc)
    record("AC-AMRR8-escape", escaped, "escaped=%s" % escaped)


def check_regression():
    base = os.path.dirname(BASE)
    codes = []
    for name in EARLIER:
        proc = subprocess.run(
            [sys.executable, os.path.join(base, "ledger", name)],
            cwd=base, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        codes.append(proc.returncode)
        print("  child %s rc=%d" % (name, proc.returncode))
    wired = False
    try:
        src = io.open(RECONCILE, "r", encoding="utf-8").read()
        wired = ('"ledger-apimarket-refundregister"' in src
                 and "test_apimarket_report_refundregister.py" in src)
    except OSError:
        wired = False
    record("AC-AMRR8-regress", all(c == 0 for c in codes) and wired,
           "rc=%s wired=%s" % (codes, wired))


def main():
    tmp, db, ids = fresh_world("main")
    check_shape(db)
    check_same_source(db, ids)
    check_window(db)
    check_money(db)
    check_contract(tmp, db)
    check_gates(db)
    check_pure_read(db)
    check_determinism()
    check_html(tmp, db)
    check_regression()
    failed = [ac for ac, ok, _ in RESULTS if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              len(RESULTS) - len(failed), len(RESULTS)))
    if failed:
        print("FAILED: %s" % ",".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())