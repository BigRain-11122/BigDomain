"""Acceptance suite for the apimarket report ATTENTION digest
(BigDomain R2102; canon = the R2102 explore-queue claim row, criteria
AC-AMAT1..AC-AMAT8 registered there BEFORE this code existed - honesty
law; the AC-AMAT prefix, collect_attention, --attention-out, this suite
name and the ledger-apimarket-attention runner label were all git grep
-F zero-occupancy anchored 2026-10-24, rc=1).

Product under proof: the attention surface of
src/sandbox/ledger/apimarket_report.py. R2101 rendered a statement;
this window derives an ordered operator to-do list from faces that
already exist (api_seller_inbox debt, api_supply shelves, negative
settlement months) instead of leaving the reader to spot them.

Criteria:
  AC-AMAT1 Derived, never hardcoded: an empty market yields zero
    findings plus an honest empty state, and a second, different world
    yields a different finding set.
  AC-AMAT2 Signal completeness: rating_debt / sold_out / negative_net
    each align with their face values (unanswered_count, sold+supply,
    months net<0) with no phantom and no missing item.
  AC-AMAT3 Stable total order and severity mapping: sold_out=high,
    others=warn, sorted by (rank, kind, subject, detail); two runs are
    byte-identical.
  AC-AMAT4 Live state: replying to a rating clears its debt, restocking
    clears the sold-out finding, and nothing is cached between calls.
  AC-AMAT5 HTML section: the Attention block precedes the Sellers
    block, carries one row per finding, shows the empty text on a
    clean market, and escapes dynamic strings (injection probe).
  AC-AMAT6 JSON sidecar: --attention-out writes ASCII-escaped JSON with
    a fixed key set, byte-identical across runs and equal to the
    in-memory findings the HTML rendered.
  AC-AMAT7 Pure read: thirteen table digests, both pool balances and
    the ledger tx count are identical across collection and render.
  AC-AMAT8 Runner wiring: ledger-apimarket-attention is registered in
    src/sandbox/reconcile_all.py with nine criteria.

Usage: python test_apimarket_report_attention.py
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
MODULE = os.path.join(BASE, "apimarket_report.py")
TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions")
POOLS = ("pool:reserve", "pool:share")
PAYLOAD = {"handler": "sandbox.echo", "params": {"text": "string"}}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok), evidence))
    print("%s %s %s" % ("PASS" if ok else "FAIL", ac, evidence))


def market_db_path(db_path):
    return os.path.join(os.path.dirname(db_path), "apimarket.db")


def table_digest(db_path):
    h = hashlib.sha256()
    conn = sqlite3.connect(market_db_path(db_path))
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


def pool_snapshot(led):
    return tuple(led.balance(name) for name in POOLS)


def fresh_stack(tag):
    tmp = tempfile.mkdtemp(prefix="apimarket-attention-" + tag + "-")
    db = os.path.join(tmp, "ledger.db")
    led, mtr, dk, am = R.build_stack(db)
    return tmp, db, led, mtr, dk, am


def close_world(led, mtr, dk, am):
    am.close()
    dk.close()
    mtr.close()
    led.close()


def fund(led, who):
    led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", 300),
                ("usr:" + who, "credit", 300)],
               "manual:fund-" + who, "attention suite funding " + who)


def seed_attention_world(am, led, dk):
    """One seller, three listings: one shelf that sells out and stays
    sold out, one refunded purchase (the unit returns, so that shelf
    must NOT be flagged), one leftover rating debt after a reply, and
    one month-crossing refund (so a seller AND a buyer month both go
    negative). The sold-out title carries markup so the escape probe
    has a real dynamic string to escape."""
    clock = R.Clock()
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-ATT-A", "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-ATT-S", "settlement")
    for who in ("bob", "carol"):
        fund(led, who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)

    orig_now = A._now_utc
    orig_led_now = R.L.now_utc
    A._now_utc = clock.now_utc
    R.L.now_utc = clock.now_utc
    try:
        clock.value = "2026-09-01T09:00:00Z"
        a1 = am.publish_api("usr:dana", "hot-scan", "Hot Scan API",
                            "scan endpoint", PAYLOAD, 10, False,
                            supply=1)["listing_id"]
        a2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed",
                            "macro endpoint", PAYLOAD, 5, False)[
                                "listing_id"]
        a3 = am.publish_api("usr:dana", "dead-shelf",
                            "Dead Shelf <b>bold</b>",
                            "one unit endpoint", PAYLOAD, 7, False,
                            supply=1)["listing_id"]
        clock.value = "2026-09-10T09:00:00Z"
        p1 = am.purchase_api("usr:bob", a1, "ref-bob-a1")["purchase_id"]
        clock.value = "2026-09-11T09:00:00Z"
        am.purchase_api("usr:carol", a2, "ref-carol-a2")
        am.purchase_api("usr:carol", a3, "ref-carol-a3")
        clock.value = "2026-09-12T09:00:00Z"
        bob_rating = am.rate_api("usr:bob", a1, 4)["rating_id"]
        carol_rating = am.rate_api("usr:carol", a2, 5)["rating_id"]
        clock.value = "2026-09-13T09:00:00Z"
        am.reply_to_rating("usr:dana", carol_rating,
                           "thanks for the feedback")
        clock.value = "2026-10-05T09:00:00Z"
        am.refund_api("usr:bob", p1, "month-crossing refund")
    finally:
        A._now_utc = orig_now
        R.L.now_utc = orig_led_now
    return {"listings": [a1, a2, a3], "purchase": p1,
            "sold_out_listing": a3, "bob_rating": bob_rating,
            "clock": clock}


def render_to(am, path):
    report = R.collect(am)
    page = R.render_html(report)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(page)
    return report, page


def run_cli(*args):
    proc = subprocess.run(
        [sys.executable, MODULE] + list(args),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), \
        proc.stderr.decode("utf-8", "replace")


def main():
    # ---- AC-AMAT1 empty market + a different world --------------------
    tmp0, db0, led0, mtr0, dk0, am0 = fresh_stack("empty")
    empty = R.collect(am0)["attention"]
    page0 = R.render_html(R.collect(am0))
    empty_text_present = R.ATTENTION_EMPTY in page0
    close_world(led0, mtr0, dk0, am0)
    ok1 = (empty["finding_count"] == 0 and empty["findings"] == []
           and empty["severity_counts"] == {} and empty_text_present)
    record("AC-AMAT1-empty", ok1,
           "empty market => findings=%d counts=%s empty-text=%s"
           % (empty["finding_count"],
              json.dumps(empty["severity_counts"]), empty_text_present))

    # ---- fixture world ------------------------------------------------
    tmp, db, led, mtr, dk, am = fresh_stack("main")
    ids = seed_attention_world(am, led, dk)
    report = R.collect(am)
    attention = report["attention"]
    findings = attention["findings"]

    ok1b = (len(findings) == 4
            and {f["kind"] for f in findings}
            == {"rating_debt", "sold_out", "negative_net"})
    record("AC-AMAT1-derived", ok1b,
           "fixture world => %d findings, kinds=%s"
           % (len(findings), sorted({f["kind"] for f in findings})))

    # ---- AC-AMAT2 completeness and semantics --------------------------
    detail = []
    ok2 = True
    sold = [f for f in findings if f["kind"] == "sold_out"]
    supply = am.api_supply(ids["sold_out_listing"])
    ok2 = ok2 and len(sold) == 1
    if sold:
        ok2 = ok2 and sold[0]["severity"] == "high"
        ok2 = ok2 and ("%d of %d units" % (supply["sold"],
                                           supply["supply"])) in sold[0][
                                               "detail"]
        ok2 = ok2 and sold[0]["subject"] == (
            "listing:%d" % ids["sold_out_listing"])
        detail.append("sold_out=sold %d/%d supply=%s"
                      % (supply["sold"], supply["supply"],
                         supply["sold_out"]))
    debts = [f for f in findings if f["kind"] == "rating_debt"]
    inbox = am.api_seller_inbox("usr:dana")
    ok2 = ok2 and len(debts) == 1
    if debts:
        ok2 = ok2 and debts[0]["subject"] == "usr:dana"
        ok2 = ok2 and debts[0]["ref"] == inbox["oldest_unanswered_utc"]
        ok2 = ok2 and ("%d unanswered rating(s)"
                       % inbox["unanswered_count"]) in debts[0]["detail"]
        ok2 = ok2 and inbox["unanswered_count"] == 1
    detail.append("rating_debt=unanswered %d oldest %s"
                  % (inbox["unanswered_count"],
                     inbox["oldest_unanswered_utc"]))
    negs = [f for f in findings if f["kind"] == "negative_net"]
    neg_seller = am.api_revenue_months("usr:dana")["months"]
    neg_buyer = am.api_buyer_months("usr:bob")["months"]
    expected_neg = set()
    for row in neg_seller:
        if row["net"] < 0:
            expected_neg.add(("usr:dana", row["month"], row["net"]))
    for row in neg_buyer:
        if row["net"] < 0:
            expected_neg.add(("usr:bob", row["month"], row["net"]))
    got_neg = set()
    for item in negs:
        month = item["ref"]
        value = None
        for row in (neg_seller if item["subject"] == "usr:dana"
                    else neg_buyer):
            if row["month"] == month:
                value = row["net"]
        got_neg.add((item["subject"], month, value))
    ok2 = ok2 and got_neg == expected_neg and len(negs) == 2
    detail.append("negative_net=%s" % sorted(expected_neg))
    record("AC-AMAT2", ok2, "; ".join(detail))

    # ---- AC-AMAT3 order and determinism -------------------------------
    rank = R.SEVERITY
    keys = [(rank[f["severity"]], f["kind"], f["subject"], f["detail"])
            for f in findings]
    other = R.collect(am)["attention"]["findings"]
    ok3 = (keys == sorted(keys) and other == findings
           and [f["severity"] for f in findings if f["kind"] == "sold_out"]
           == ["high"]
           and all(f["severity"] == "warn" for f in findings
                   if f["kind"] != "sold_out"))
    record("AC-AMAT3", ok3,
           "sorted total order, high=1/warn=%d, replay identical"
           % (len(findings) - 1))

    # ---- AC-AMAT4 live state -----------------------------------------
    am.reply_to_rating("usr:dana", ids["bob_rating"], "thanks bob")
    after_reply = R.collect(am)["attention"]
    am.restock_api("usr:dana", ids["sold_out_listing"], 2)
    after_restock = R.collect(am)["attention"]
    ok4 = (all(f["kind"] != "rating_debt"
               for f in after_reply["findings"])
           and after_reply["finding_count"] == 3
           and all(f["kind"] != "sold_out"
                   for f in after_restock["findings"])
           and after_restock["finding_count"] == 2)
    record("AC-AMAT4", ok4,
           "reply clears debt (%d left), restock clears sold-out (%d left)"
           % (after_reply["finding_count"], after_restock["finding_count"]))

    # ---- AC-AMAT5 HTML section and escaping --------------------------
    escaped = "Dead Shelf &lt;b&gt;bold&lt;/b&gt;"
    page = R.render_html(report)
    ok5 = (0 <= page.find("<h2>Attention</h2>")
           < page.find("<h2>Sellers</h2>")
           and page.count("<h2>Attention</h2>") == 1
           and escaped in page and "<b>bold</b>" not in page
           and page.count("<td>high</td>") == 1)
    record("AC-AMAT5", ok5,
           "Attention precedes Sellers=%s esc=%s raw-tag-absent=%s"
           % (page.find("<h2>Attention</h2>")
              < page.find("<h2>Sellers</h2>"),
              escaped in page, "<b>bold</b>" not in page))

    # ---- AC-AMAT6 JSON sidecar ---------------------------------------
    # A second, independent CLI world keeps the sidecar honest: the
    # in-memory world above has already been mutated by AC-AMAT4.
    tmp2, db2, led2, mtr2, dk2, am2 = fresh_stack("cli")
    seed_attention_world(am2, led2, dk2)
    ref = R.collect(am2)["attention"]
    out_a = os.path.join(tmp2, "attention-a.json")
    out_b = os.path.join(tmp2, "attention-b.json")
    digest_before, tx_before = table_digest(db2)
    pools_before = pool_snapshot(led2)
    rc_a, so_a, err_a = run_cli("--db", db2,
                                "--out", os.path.join(tmp2, "r-a.html"),
                                "--attention-out", out_a)
    digest_after, tx_after = table_digest(db2)
    pools_after = pool_snapshot(led2)
    rc_b, so_b, _ = run_cli("--db", db2,
                            "--out", os.path.join(tmp2, "r-b.html"),
                            "--attention-out", out_b)
    raw_a = io.open(out_a, "rb").read()
    raw_b = io.open(out_b, "rb").read()
    doc = json.loads(raw_a.decode("utf-8"))
    try:
        # the CLI world must agree with a like-for-like in-memory read
        doc_ok = doc == ref
    finally:
        close_world(led2, mtr2, dk2, am2)
    ok6 = (rc_a == 0 and rc_b == 0 and doc_ok
           and raw_a == raw_b == io.open(out_b, "rb").read()
           and all(byte < 128 for byte in raw_a)
           and b"\r\n" not in raw_a
           and sorted(doc.keys()) ==
           ["finding_count", "findings", "severity_counts"])
    record("AC-AMAT6", ok6,
           "rc=%d/%d matches-in-memory=%s ascii=%s lf=%s identical=%s"
           % (rc_a, rc_b, doc_ok, all(byte < 128 for byte in raw_a),
              b"\r\n" not in raw_a, raw_a == raw_b))

    # ---- AC-AMAT7 pure read ------------------------------------------
    ok7 = (digest_before == digest_after and tx_before == tx_after
           and pools_before == pools_after)
    record("AC-AMAT7", ok7,
           "digest stable=%s tx %d==%d pools stable=%s"
           % (digest_before == digest_after, tx_before, tx_after,
              pools_before == pools_after))

    # ---- AC-AMAT8 runner wiring --------------------------------------
    src = io.open(RECONCILE, encoding="utf-8").read()
    ok8 = ('"ledger-apimarket-attention"' in src
           and "test_apimarket_report_attention.py" in src
           and 'ledger-apimarket-attention", os.path.join(' in src)
    record("AC-AMAT8", ok8,
           "reconcile_all registers ledger-apimarket-attention=%s" % ok8)

    close_world(led, mtr, dk, am)

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(RESULTS)
                              else "FAIL", passed, len(RESULTS)))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())