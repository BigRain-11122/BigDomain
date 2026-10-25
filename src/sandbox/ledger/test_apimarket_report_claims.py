"""Acceptance suite for the post-sale claim block on the apimarket
settlement report (BigDomain R2134; canon = the R2134 explore-queue
claim row, criteria AC-AMCLM1..AC-AMCLM8 registered there BEFORE this
code existed - honesty law; the AC-AMCLM prefix, claim_block,
CLAIM_COLUMNS, CLAIM_EMPTY, claim_debt, the <h2>Claims</h2> heading,
this suite name, the ledger-apimarket-reportclaims runner label and
report["claims"] were all git-grep -F zero-occupancy anchored
2026-10-26, rc=0 matches).

Product under proof: api_claims already answered the buyer view, the
seller view and the operator view (AC-AMCL5/AC-AMCL6), but nothing
consumed it - a git grep found only its own suite, so the operator's
offline ledger could not answer "which post-sale claims are still
unresolved, who owes an answer, and how long has the oldest waited".
apimarket_report.py now carries the market-wide envelope verbatim, a
Claims page section, and a claim_debt attention family derived from
that same block.

Criteria:
  AC-AMCLM1 Contract and derived set: report["claims"] carries the
    nine-key envelope and sixteen-key rows, claim_count equals the row
    count, and all four status counters equal the row-derived counts.
  AC-AMCLM2 Same source, no cache: the block equals a direct
    api_claims() call on the same database, and a claim opened after
    one collect appears in the very next collect.
  AC-AMCLM3 Status precedence: refunded beats withdrawn beats answered
    beats open, proven row by row on a world carrying all four states
    plus the stored evidence for each.
  AC-AMCLM4 claim_debt family: exactly one finding per seller with at
    least one open claim, severity warn, detail carrying the count and
    the oldest opened_utc, ref equal to that stamp; a seller with no
    open claim carries none, and the finding order plus the five-key
    shape stay intact.
  AC-AMCLM5 Additive contract: schema_version equals the module
    constant (17), the JSON envelope still has exactly
    schema_version/report/attention, and market / market_months /
    board / activity / refunds / duty / attention equal their direct
    face calls.
  AC-AMCLM6 Pure read: twenty table digests and the ledger tx count
    are unchanged by a collect.
  AC-AMCLM7 HTML surface: the Claims heading, the four-counter line,
    the sixteen column headers and every claim id are on the page; a
    hostile claim_text is escaped; a report dict without the claims
    key renders the honest empty state.
  AC-AMCLM8 Regression + wiring: the base report, JSON and refund
    register suites still pass and the runner label
    ledger-apimarket-reportclaims(8) is registered.

Usage: python test_apimarket_report_claims.py
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

ENVELOPE_KEYS = ("answered_count", "buyer_id", "claim_count", "claims",
                 "dev_account", "disclaimer", "open_count",
                 "refunded_count", "withdrawn_count")
ROW_KEYS = ("claim_id", "purchase_id", "listing_id", "listing_title",
            "dev_account", "buyer_id", "price_paid", "claim_text",
            "opened_utc", "status", "refund_id", "refunded_utc",
            "response_id", "response_text", "responded_utc",
            "withdrawn_utc")

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers", "apimarket_providers",
          "apimarket_reviews", "apimarket_claims",
          "apimarket_claim_responses", "apimarket_claim_withdrawals")

HOSTILE = "<script>x</script>"


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


def open_stack(db):
    return R.build_stack(db)


def close_stack(led, mtr, dk, am):
    am.close()
    dk.close()
    mtr.close()
    led.close()


def fresh_world(tag):
    tmp = tempfile.mkdtemp(prefix="apimarket-claims-" + tag + "-")
    db = os.path.join(tmp, "ledger.db")
    led, mtr, dk, am = open_stack(db)
    ids = R.seed_demo(am, led, dk)
    close_stack(led, mtr, dk, am)
    return tmp, db, ids


def collect_with(db):
    led, mtr, dk, am = open_stack(db)
    try:
        return R.collect(am)
    finally:
        close_stack(led, mtr, dk, am)


def with_pinned(db, fn):
    """Run fn(am) on an open stack under a pinned clock."""
    class _C(object):
        def now_utc(self):
            return "2026-10-10T00:00:00Z"

    led, mtr, dk, am = open_stack(db)
    clock = _C()
    orig = A._now_utc
    orig_led = R.L.now_utc
    try:
        A._now_utc = clock.now_utc
        R.L.now_utc = clock.now_utc
        return fn(am)
    finally:
        A._now_utc = orig
        R.L.now_utc = orig_led
        close_stack(led, mtr, dk, am)


def seed_claims(db, ids, hostile=False):
    """Build a world carrying all four claim states on two sellers.

    dana owns listing 2 and frank owns listing 3. Each claim sits on its
    own purchase so the four statuses are independent evidence, and the
    stamped clock makes the oldest-debt row deterministic."""
    d2, d3 = ids["listings"][1], ids["listings"][2]

    def run(am):
        p_open = am.purchase_api("usr:dave", d2, "claim-open")[
            "purchase_id"]
        p_ans = am.purchase_api("usr:erin", d2, "claim-answered")[
            "purchase_id"]
        p_wdr = am.purchase_api("usr:bob", d3, "claim-withdrawn")[
            "purchase_id"]
        p_ref = am.purchase_api("usr:carol", d3, "claim-refunded")[
            "purchase_id"]
        text = HOSTILE if hostile else "open probe"
        c_open = am.open_claim("usr:dave", p_open, text)["claim_id"]
        c_ans = am.open_claim("usr:erin", p_ans, "answered probe")[
            "claim_id"]
        am.respond_claim("usr:dana", c_ans, "resolved by email")
        c_wdr = am.open_claim("usr:bob", p_wdr, "withdraw probe")[
            "claim_id"]
        am.respond_claim("usr:frank", c_wdr, "looked into it")
        am.withdraw_claim("usr:bob", c_wdr)
        c_ref = am.open_claim("usr:carol", p_ref, "refund probe")[
            "claim_id"]
        am.respond_claim("usr:frank", c_ref, "refund issued")
        am.refund_api("usr:carol", p_ref, "refund probe reason")
        return {"open": c_open, "answered": c_ans,
                "withdrawn": c_wdr, "refunded": c_ref}

    return with_pinned(db, run)


def check_contract(db):
    report = collect_with(db)
    claims = report["claims"]
    keys = tuple(sorted(claims.keys()))
    row_keys = set()
    for row in claims["claims"]:
        row_keys |= set(row.keys())
    counts = {"open": 0, "answered": 0, "refunded": 0, "withdrawn": 0}
    for row in claims["claims"]:
        counts[row["status"]] += 1
    ok = (keys == ENVELOPE_KEYS
          and row_keys == set(ROW_KEYS)
          and claims["claim_count"] == len(claims["claims"])
          and claims["open_count"] == counts["open"]
          and claims["answered_count"] == counts["answered"]
          and claims["refunded_count"] == counts["refunded"]
          and claims["withdrawn_count"] == counts["withdrawn"])
    record("AC-AMCLM1", ok,
           "keys=%d rows=%d count=%d states=%s"
           % (len(keys), claims["claim_count"], counts["open"],
              ",".join("%s%d" % (k, counts[k]) for k in sorted(counts))))


def check_same_source(db, ids):
    report = collect_with(db)
    led, mtr, dk, am = open_stack(db)
    try:
        direct = am.api_claims()
    finally:
        close_stack(led, mtr, dk, am)
    same = report["claims"] == direct
    before = report["claims"]["claim_count"]
    d2 = ids["listings"][1]
    with_pinned(db, lambda am: am.open_claim(
        "usr:frank", am.purchase_api("usr:frank", d2, "claim-late")[
            "purchase_id"], "late probe"))
    after = collect_with(db)["claims"]
    record("AC-AMCLM2", same and after["claim_count"] == before + 1,
           "same=%s count %d->%d" % (same, before,
                                     after["claim_count"]))


def check_precedence(db, cids):
    claims = collect_with(db)["claims"]["claims"]
    by_id = {row["claim_id"]: row for row in claims}
    ok = True
    for state, cid in sorted(cids.items()):
        row = by_id[cid]
        ok = ok and row["status"] == state
    # The stored evidence must agree with the derived status.
    ok = ok and by_id[cids["refunded"]]["refund_id"] is not None
    ok = ok and by_id[cids["refunded"]]["refunded_utc"] is not None
    ok = ok and by_id[cids["withdrawn"]]["withdrawn_utc"] is not None
    ok = ok and by_id[cids["withdrawn"]]["response_id"] is not None
    ok = ok and by_id[cids["answered"]]["response_id"] is not None
    ok = ok and by_id[cids["answered"]]["withdrawn_utc"] is None
    ok = ok and by_id[cids["open"]]["response_id"] is None
    ok = ok and by_id[cids["open"]]["refund_id"] is None
    record("AC-AMCLM3", ok,
           "states=%s" % ",".join("%s=%s" % (k, by_id[v]["status"])
                                  for k, v in sorted(cids.items())))


def check_claim_debt(db, cids):
    report = collect_with(db)
    findings = report["attention"]["findings"]
    debt = [f for f in findings if f["kind"] == "claim_debt"]
    rows = report["claims"]["claims"]
    open_rows = [row for row in rows if row["status"] == "open"]
    by_seller = {}
    for row in open_rows:
        by_seller.setdefault(row["dev_account"], []).append(row)
    one_each = len(debt) == len({f["subject"] for f in debt})
    shape = all(set(f.keys()) == {"kind", "severity", "subject",
                                 "detail", "ref"} for f in findings)
    ok = one_each and shape and len(debt) == len(by_seller)
    for finding in debt:
        mine = by_seller.get(finding["subject"]) or []
        oldest = min(row["opened_utc"] for row in mine) if mine else None
        ok = (ok and bool(mine)
              and finding["severity"] == "warn"
              and finding["ref"] == oldest
              and ("%d open claim(s)" % len(mine)) in finding["detail"]
              and oldest in finding["detail"])
    record("AC-AMCLM4", ok,
           "debt=%d subjects=%s open_sellers=%d"
           % (len(debt), ",".join(sorted(f["subject"] for f in debt)),
              len(by_seller)))


def check_contract_additive(db):
    report = collect_with(db)
    payload = R.api_report_payload(report)
    keys = tuple(sorted(payload.keys()))
    led, mtr, dk, am = open_stack(db)
    try:
        same = (report["market"] == am.api_market_stats()
                and report["market_months"] == am.api_market_months()
                and report["board"] == am.api_board()
                and report["activity"]
                == am.api_market_feed(limit=R.FEED_LIMIT)
                and report["refunds"] == am.api_refund_register()
                and report["claims"] == am.api_claims())
    finally:
        close_stack(led, mtr, dk, am)
    ok = (keys == ("attention", "report", "schema_version")
          and payload["schema_version"] == R.REPORT_SCHEMA == 17
          and same)
    record("AC-AMCLM5", ok,
           "keys=%s schema=%s same=%s"
           % (",".join(keys), payload["schema_version"], same))


def check_pure_read(db):
    before = table_digest(db)
    collect_with(db)
    after = table_digest(db)
    record("AC-AMCLM6", before == after,
           "digest=%s tx=%d" % (after[0][:16], after[1]))


def html_checks(db, cids):
    """The page must show the heading, the four counters, the sixteen
    columns and every claim id, and must degrade honestly for an older
    report dict that carries no claims key."""
    report = collect_with(db)
    page = R.render_html(report)
    claims = report["claims"]
    head = "%s claim(s): open %s / answered %s / refunded %s / withdrawn %s" % (
        claims["claim_count"], claims["open_count"],
        claims["answered_count"], claims["refunded_count"],
        claims["withdrawn_count"])
    ok = "<h2>Claims</h2>" in page and head in page
    ok = ok and all(("<th>%s</th>" % col) in page
                    for col in R.CLAIM_COLUMNS)
    for row in claims["claims"]:
        ok = ok and (">%d<" % row["claim_id"]) in page
    legacy = dict(report)
    legacy.pop("claims")
    degrade = R.CLAIM_EMPTY in R.render_html(legacy)
    return ok and degrade, len(claims["claims"]), degrade


def escape_ok():
    tmp, db, ids = fresh_world("escape")
    seed_claims(db, ids, hostile=True)
    page = R.render_html(collect_with(db))
    return (HOSTILE not in page
            and "&lt;script&gt;x&lt;/script&gt;" in page
            and R.MARKER in page
            and R.DISCLAIMER in page)


def check_regression():
    base = os.path.dirname(BASE)
    labels = ("test_apimarket_report.py",
              "test_apimarket_report_json.py",
              "test_apimarket_report_refundregister.py")
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
        wired = ('"ledger-apimarket-reportclaims"' in src
                 and "test_apimarket_report_claims.py" in src)
    except OSError:
        wired = False
    record("AC-AMCLM8", all(c == 0 for c in codes) and wired,
           "rc=%s wired=%s" % (codes, wired))


def main():
    tmp, db, ids = fresh_world("main")
    cids = seed_claims(db, ids)
    check_contract(db)
    check_same_source(db, ids)
    check_precedence(db, cids)
    check_claim_debt(db, cids)
    check_contract_additive(db)
    check_pure_read(db)
    ok, rows, degrade = html_checks(db, cids)
    esc = escape_ok()
    record("AC-AMCLM7", ok and esc,
           "heads=%d rows=%d degrade=%s escape=%s"
           % (len(R.CLAIM_COLUMNS), rows, degrade, esc))
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