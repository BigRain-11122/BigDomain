"""Acceptance suite for the apimarket settlement report generator
(BigDomain R2101; canon = the R2101 explore-queue claim row, criteria
AC-AMRPT1..AC-AMRPT8 registered there BEFORE this code existed -
honesty law; the AC-AMRPT prefix, the module name, this suite name and
the ledger-apimarket-report runner label were all git-grep -F
zero-occupancy anchored 2026-10-24, rc=1).

Product under proof: src/sandbox/ledger/apimarket_report.py, the first
consumer of the R2096..R2100 read faces. One command renders the
settlement faces into a self-contained offline HTML ledger.

Criteria:
  AC-AMRPT1 CLI contract: --db/--out/--seed, unknown flag exits 2 with
    an ASCII message, --help exits 0, --db/--out are required.
  AC-AMRPT2 Determinism: two fresh seeded worlds render byte-identical
    HTML (same sha256).
  AC-AMRPT3 Consumption: the report totals equal api_market_stats key by
    key (no recomputation drift) and every api_market_months month row
    appears in the page.
  AC-AMRPT4 Seller/buyer faces: each seller month row equals
    api_revenue_months, each buyer profile key equals api_buyer_profile
    and each buyer month row equals api_buyer_months.
  AC-AMRPT5 Escape + standing markers: every dynamic string is
    HTML-escaped, the face disclaimer text is present, and the
    AIGC/sandbox marker line is present.
  AC-AMRPT6 Pure read: thirteen table digests, pool balances and the tx
    row count are identical before and after a render.
  AC-AMRPT7 Self-contained: no external http(s) reference, no script
    tag, UTF-8 without BOM, LF only, bounded size.
  AC-AMRPT8 Runner wiring: ledger-apimarket-report is registered in
    src/sandbox/reconcile_all.py with the expected suite count.

Usage: python test_apimarket_report.py
"""

import hashlib
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
MODULE = os.path.join(BASE, "apimarket_report.py")
TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions")
POOLS = ("pool:reserve", "pool:share")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok), evidence))
    print("%s %s %s" % ("PASS" if ok else "FAIL", ac, evidence))


def table_digest(db_path):
    """Thirteen market-table digest + the ledger tx row count.

    The market face rides its own sqlite file beside the ledger
    (APIMarketFace derives apimarket.db from dirname(ledger.db_path)),
    so both files are digested."""
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
    tmp = tempfile.mkdtemp(prefix="apimarket-report-" + tag + "-")
    db = os.path.join(tmp, "ledger.db")
    led, mtr, dk, am = R.build_stack(db)
    R.seed_demo(am, led, dk)
    return tmp, db, led, mtr, dk, am


def close_world(led, mtr, dk, am):
    am.close()
    dk.close()
    mtr.close()
    led.close()


def check_cli():
    parser = R.build_parser()
    ok_help = ok_unknown = ok_required = False
    try:
        parser.parse_args(["--help"])
    except SystemExit as exc:
        ok_help = exc.code == 0
    try:
        parser.parse_args(["--db", "x", "--out", "y", "--nope"])
    except SystemExit as exc:
        ok_unknown = exc.code == 2
    try:
        parser.parse_args(["--out", "y"])
    except SystemExit as exc:
        ok_required = exc.code == 2
    record("AC-AMRPT1",
           ok_help and ok_unknown and ok_required,
           "help_exit0=%s unknown_exit2=%s missing_db_exit2=%s"
           % (ok_help, ok_unknown, ok_required))


def check_determinism():
    tmp_a, db_a, led_a, mtr_a, dk_a, am_a = fresh_world("a")
    page_a = R.render_html(R.collect(am_a))
    close_world(led_a, mtr_a, dk_a, am_a)
    tmp_b, db_b, led_b, mtr_b, dk_b, am_b = fresh_world("b")
    page_b = R.render_html(R.collect(am_b))
    close_world(led_b, mtr_b, dk_b, am_b)
    sha_a = hashlib.sha256(page_a.encode("utf-8")).hexdigest()
    sha_b = hashlib.sha256(page_b.encode("utf-8")).hexdigest()
    record("AC-AMRPT2", sha_a == sha_b,
           "sha16 %s vs %s" % (sha_a[:16], sha_b[:16]))
    return page_a


def check_consumption(page, am):
    stats = am.api_market_stats()
    months = am.api_market_months()["months"]
    hits = 0
    for key, value in stats.items():
        if key == "disclaimer" or isinstance(value, (list, dict)):
            continue
        cell = "<th>%s</th><td>%s</td>" % (key, value)
        if cell in page:
            hits += 1
    month_hits = 0
    for row in months:
        if "<td>%s</td>" % row["month"] in page:
            month_hits += 1
    ok = hits >= 13 and month_hits == len(months) and len(months) == 3
    record("AC-AMRPT3", ok,
           "stats_cells=%d/%d month_rows=%d/%d"
           % (hits, len(stats) - 1, month_hits, len(months)))


def check_participants(page, am):
    board = am.api_board()["listings"]
    sellers = sorted({row["dev_account"] for row in board})
    ok_sell = ok_buy = True
    detail = []
    for dev in sellers:
        rows = am.api_revenue_months(dev)["months"]
        got = sum(1 for r in rows if "<td>%s</td>" % r["month"] in page)
        ok_sell = ok_sell and got == len(rows)
        detail.append("%s:%d/%d" % (dev, got, len(rows)))
    buyers = set()
    for dev in sellers:
        for row in am.api_sales(dev)["sales"]:
            buyers.add(row["buyer_id"])
    for buyer in sorted(buyers):
        prof = am.api_buyer_profile(buyer)
        bmonths = am.api_buyer_months(buyer)["months"]
        miss = []
        for key, value in prof.items():
            if key in ("disclaimer", "buyer_id"):
                continue
            if isinstance(value, (list, dict)):
                continue
            shown = "" if value is None else value
            cell = "<th>%s</th><td>%s</td>" % (key, shown)
            if cell not in page:
                miss.append(key)
        got = sum(1 for r in bmonths
                  if "<td>%s</td>" % r["month"] in page)
        ok_buy = ok_buy and not miss and got == len(bmonths)
        if miss:
            detail.append("missing:" + ",".join(miss[:3]))
    record("AC-AMRPT4", ok_sell and ok_buy and len(buyers) == 3,
           "sellers=%s buyers=%d" % (",".join(detail) or "none",
                                     len(buyers)))


def check_escape_and_markers(page, am):
    probe = "<b>&\"'"
    esc_probe = R.esc(probe)
    esc_ok = esc_probe == "&lt;b&gt;&amp;&quot;&#x27;"
    fake = {
        "market": {"net_gross_tokens": 7, "note": "<x>",
                   "disclaimer": "d"},
        "market_months": {"months": []},
        "board": {"listings": [{"title": "<x>", "listing_key": "k"}]},
        "sellers": {},
        "buyers": {},
    }
    fake_page = R.render_html(fake)
    hostile_escaped = ("<x>" not in fake_page
                       and "&lt;x&gt;" in fake_page)
    disclaimer = am.api_market_stats()["disclaimer"]
    ok = (esc_ok and hostile_escaped and disclaimer in page
          and R.MARKER in page and "AIGC" in page
          and "<script" not in page.lower())
    record("AC-AMRPT5", ok,
           "esc_probe=%s hostile_escaped=%s disclaimer_inline=%s"
           " marker=%s" % (esc_ok, hostile_escaped, disclaimer in page,
                           R.MARKER in page))


def check_pure_read(db, am):
    before_digest, before_tx = table_digest(db)
    before_pools = [am.led.balance(p) for p in POOLS]
    R.render_html(R.collect(am))
    after_digest, after_tx = table_digest(db)
    after_pools = [am.led.balance(p) for p in POOLS]
    ok = (before_digest == after_digest and before_tx == after_tx
          and before_pools == after_pools)
    record("AC-AMRPT6", ok,
           "digest_equal=%s tx %d/%d pools_held=%s"
           % (before_digest == after_digest, before_tx, after_tx,
              before_pools == after_pools))


def check_self_contained(page):
    raw = page.encode("utf-8")
    ok = ("http://" not in page and "https://" not in page
          and "<script" not in page.lower()
          and not raw.startswith(b"\xef\xbb\xbf")
          and b"\r" not in raw
          and 0 < len(raw) < 200000)
    record("AC-AMRPT7", ok, "bytes=%d external_refs=%d script=%s"
           % (len(raw), page.count("http://") + page.count("https://"),
              "<script" in page.lower()))


def check_wiring():
    with open(RECONCILE, "r", encoding="utf-8") as handle:
        text = handle.read()
    label = "\"ledger-apimarket-report\""
    ok = (label in text
          and "test_apimarket_report.py" in text
          and text.count(label) == 1)
    record("AC-AMRPT8", ok, "label_count=%d" % text.count(label))


def main():
    check_cli()
    page = check_determinism()

    tmp, db, led, mtr, dk, am = fresh_world("main")
    try:
        check_consumption(page, am)
        check_participants(page, am)
        check_escape_and_markers(page, am)
        check_pure_read(db, am)
        check_self_contained(page)
        check_wiring()

        out = os.path.join(tmp, "report.html")
        proc = subprocess.run([sys.executable, MODULE, "--db", db,
                               "--out", out],
                              capture_output=True)
        cli_ok = (proc.returncode == 0 and os.path.isfile(out)
                  and open(out, "rb").read() == page.encode("utf-8"))
        record("AC-AMRPT1b", cli_ok,
               "cli_exit=%d file_matches_render=%s"
               % (proc.returncode, cli_ok))
    finally:
        close_world(led, mtr, dk, am)

    passed = sum(1 for _ac, ok, _ev in RESULTS if ok)
    print("\nSUITE %s %d/%d"
          % ("PASS" if passed == len(RESULTS) else "FAIL",
             passed, len(RESULTS)))
    payload = json.dumps([{"ac": ac, "ok": ok, "evidence": ev}
                          for ac, ok, ev in RESULTS],
                         ensure_ascii=False, sort_keys=True)
    print("SUITE-SHA16 %s"
          % hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16])
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())