"""Acceptance suite for the machine-readable report contract on the
apimarket settlement report generator (BigDomain R2103; canon = the
R2103 explore-queue claim row, criteria AC-AMJ1..AC-AMJ8 registered
there BEFORE this code existed - honesty law; the AC-AMJ prefix,
--json-out, write_report_json, this suite name, the
ledger-apimarket-reportjson runner label and REPORT_SCHEMA were all
git-grep -F zero-occupancy anchored 2026-10-24, rc=1).

Product under proof: apimarket_report.py --json-out, a versioned
ASCII JSON envelope wrapping the same collect() dict the HTML renderer
consumes, written atomically.

Criteria:
  AC-AMJ1 Contract shape: the envelope carries exactly
    schema_version/report/attention, schema_version == REPORT_SCHEMA,
    and the file is pure ASCII with LF endings and no BOM.
  AC-AMJ2 Same source: the JSON report equals a fresh collect() dict
    (same read pass, no second derivation) and the attention member is
    byte-identical to the --attention-out sidecar of the same run.
  AC-AMJ3 Conservation: partition and trade identities hold on the
    JSON market block.
  AC-AMJ4 Derived participants: the sellers/buyers key sets equal the
    sets derived from api_board and api_sales.
  AC-AMJ5 Determinism: two seeded worlds write byte-identical JSON.
  AC-AMJ6 Pure read: thirteen table digests and the ledger tx count are
    unchanged by a JSON write.
  AC-AMJ7 Atomic write: an empty or directory path exits 2 without
    leaving a partial file (no .tmp survivor).
  AC-AMJ8 Regression: the HTML page is byte-identical whether or not
    --json-out is passed (a purely additive surface) and the runner
    wiring is registered.

Usage: python test_apimarket_report_json.py
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
    tmp = tempfile.mkdtemp(prefix="apimarket-reportjson-" + tag + "-")
    db = os.path.join(tmp, "ledger.db")
    led, mtr, dk, am = R.build_stack(db)
    R.seed_demo(am, led, dk)
    am.close()
    dk.close()
    mtr.close()
    led.close()
    return tmp, db


def run_cli(db, out, extra):
    argv = ["--db", db, "--out", out] + list(extra)
    code = R.main(argv)
    return code


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.loads(handle.read())


def check_contract(tmp, db):
    out = os.path.join(tmp, "report.html")
    js = os.path.join(tmp, "report.json")
    code = run_cli(db, out, ["--json-out", js])
    raw = io.open(js, "rb").read()
    ok_ascii = True
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        ok_ascii = False
        text = ""
    ok_lf = b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf")
    doc = json.loads(text) if ok_ascii else {}
    ok_shape = sorted(doc) == ["attention", "report", "schema_version"]
    ok_schema = doc.get("schema_version") == R.REPORT_SCHEMA
    record("AC-AMJ1", code == 0 and ok_ascii and ok_lf and ok_shape
           and ok_schema,
           "exit=%d ascii=%s lf=%s keys=%s schema=%s"
           % (code, ok_ascii, ok_lf, sorted(doc), doc.get("schema_version")))
    return js


def check_same_source(db, js):
    led, mtr, dk, am = R.build_stack(db)
    try:
        report = R.collect(am)
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    written = read_json(js)
    ok_report = written["report"] == report
    side = os.path.join(os.path.dirname(js), "attention.json")
    out = os.path.join(os.path.dirname(js), "report2.html")
    run_cli(db, out, ["--attention-out", side])
    side_bytes = io.open(side, "rb").read()
    want = (json.dumps(written["attention"], sort_keys=True, indent=1,
                       ensure_ascii=True) + "\n").encode("ascii")
    record("AC-AMJ2", ok_report and side_bytes == want,
           "report_equal=%s attention_bytes_equal=%s"
           % (ok_report, side_bytes == want))


def check_conservation(js):
    market = read_json(js)["report"]["market"]
    ok_part = market["listing_count"] == (market["live_listing_count"]
                                          + market["retired_listing_count"])
    ok_trade = (market["gross_tokens"]
                == market["net_gross_tokens"] + market["refunded_tokens"]
                and market["net_gross_tokens"]
                == market["dev_revenue"] + market["platform_revenue"])
    record("AC-AMJ3", ok_part and ok_trade,
           "partition=%s trade=%s gross=%s net=%s refunded=%s"
           % (ok_part, ok_trade, market["gross_tokens"],
              market["net_gross_tokens"], market["refunded_tokens"]))


def check_participants(js):
    led, mtr, dk, am = R.build_stack(os.path.join(
        os.path.dirname(js), "ledger.db"))
    try:
        board = am.api_board()
        sellers = sorted({row["dev_account"]
                          for row in board["listings"]})
        buyers = set()
        for dev in sellers:
            for row in am.api_sales(dev)["sales"]:
                buyers.add(row["buyer_id"])
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    report = read_json(js)["report"]
    ok = (sorted(report["sellers"]) == sellers
          and sorted(report["buyers"]) == sorted(buyers))
    record("AC-AMJ4", ok, "sellers=%s buyers=%s"
           % (sorted(report["sellers"]), sorted(report["buyers"])))


def check_determinism():
    digests = []
    for tag in ("a", "b"):
        tmp, db = fresh_world(tag)
        out = os.path.join(tmp, "r.html")
        js = os.path.join(tmp, "r.json")
        run_cli(db, out, ["--json-out", js])
        digests.append(hashlib.sha256(io.open(js, "rb").read()).hexdigest())
    record("AC-AMJ5", digests[0] == digests[1], "sha256=%s" % digests[0])


def check_pure_read(tmp, db):
    before = table_digest(db)
    out = os.path.join(tmp, "pr.html")
    js = os.path.join(tmp, "pr.json")
    run_cli(db, out, ["--json-out", js])
    after = table_digest(db)
    record("AC-AMJ6", before == after, "digest=%s tx=%s"
           % (after[0][:16], after[1]))


def check_atomic(tmp, db):
    out = os.path.join(tmp, "at.html")
    code_empty = run_cli(db, out, ["--json-out", ""])
    d = os.path.join(tmp, "adir")
    os.makedirs(d)
    code_dir = run_cli(db, out, ["--json-out", d])
    survivors = [n for n in os.listdir(tmp) if n.endswith(".tmp")]
    code_ok = run_cli(db, out, ["--json-out",
                                os.path.join(tmp, "sub", "deep.json")])
    deep = os.path.isfile(os.path.join(tmp, "sub", "deep.json"))
    record("AC-AMJ7", code_empty == 2 and code_dir == 2
           and not survivors and code_ok == 0 and deep,
           "empty=%d dir=%d tmp_survivors=%d nested=%s"
           % (code_empty, code_dir, len(survivors), deep))


def check_regression():
    pages = []
    for tag in ("n1", "n2"):
        tmp, db = fresh_world(tag)
        out = os.path.join(tmp, "r.html")
        extra = [] if tag == "n1" else ["--json-out",
                                        os.path.join(tmp, "r.json")]
        run_cli(db, out, extra)
        pages.append(io.open(out, "rb").read())
    wired = False
    try:
        src = io.open(RECONCILE, "r", encoding="utf-8").read()
        wired = ('"ledger-apimarket-reportjson"' in src
                 and "test_apimarket_report_json.py" in src)
    except OSError:
        wired = False
    record("AC-AMJ8", pages[0] == pages[1] and wired,
           "html_identical=%s wired=%s" % (pages[0] == pages[1], wired))


def main():
    tmp, db = fresh_world("main")
    js = check_contract(tmp, db)
    check_same_source(db, js)
    check_conservation(js)
    check_participants(js)
    check_determinism()
    check_pure_read(tmp, db)
    check_atomic(tmp, db)
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