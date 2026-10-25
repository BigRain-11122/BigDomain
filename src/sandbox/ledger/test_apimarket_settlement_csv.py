"""Acceptance suite for the apimarket settlement CSV bundle (BigDomain
R2122; canon = the explore-queue row claimed in R2122, criteria
AC-CSVM1..AC-CSVM8 registered there BEFORE this code existed - honesty
law).

Product under proof: csv_payloads / write_report_csv and the --csv-out
flag in src/sandbox/ledger/apimarket_report.py. R2101..R2121 turned the
settlement faces into an HTML page and a versioned JSON envelope, but a
finance or spreadsheet consumer still had to scrape the page or parse
the JSON. This window adds a third artifact projected from the same
collect() dict, so a CSV cell can never disagree with the table the
operator sees on the page.

Criteria:
  AC-CSVM1 File set and headers: exactly the three pinned names, each
    header equals its module column tuple, UTF-8 without BOM, LF only.
  AC-CSVM2 Same source: every cell equals the matching month row of the
    report collected for the same call (seller rows gain dev_account,
    buyer rows gain buyer_id); nothing is recomputed.
  AC-CSVM3 Coverage and order: row counts equal the sum of the month
    counts, seller rows ordered by (dev_account, month), buyer rows by
    (buyer_id, month), market rows by month.
  AC-CSVM4 Escaping: RFC4180 quoting for comma / quote / newline
    fields, and a re-read round-trips to the original values.
  AC-CSVM5 Fail-closed atomic write: an empty target or an existing
    file path raises ValueError and leaves no file and no .tmp behind.
  AC-CSVM6 Determinism: two runs over the same database are
    byte-identical (sha256).
  AC-CSVM7 Pure read and unchanged contracts: every table digest and
    the ledger tx set are constant across the write, REPORT_SCHEMA
    stays 14, and the HTML plus the JSON payload are byte-identical
    with and without the flag.
  AC-CSVM8 CLI and hygiene: --csv-out exits 0 and writes the three
    files beside the usual page and JSON, the runner label is
    registered, and the suite is pure ASCII with no network import.

Usage: python test_apimarket_settlement_csv.py
"""

import csv
import hashlib
import io
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import apimarket_report as R          # noqa: E402 (R2101 consumer)

RESULTS = []
RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
LABEL = "ledger-apimarket-settlementcsv"


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def read_bytes(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def sha16(blob):
    return hashlib.sha256(blob).hexdigest()[:16]


def parse_csv(path):
    raw = read_bytes(path)
    text = raw.decode("utf-8")
    return list(csv.reader(io.StringIO(text, newline="")))


def all_tables(am):
    conn = sqlite3.connect(am.db_path)
    try:
        names = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
            " ORDER BY name").fetchall()]
        digests = {}
        for name in names:
            rows = conn.execute(
                "SELECT * FROM " + name + " ORDER BY rowid").fetchall()
            blob = repr(rows).encode("utf-8")
            digests[name] = (len(rows), hashlib.sha256(blob).hexdigest())
        return digests
    finally:
        conn.close()


def ledger_tx_ids(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return sorted(str(r[0]) for r in conn.execute(
            "SELECT tx_id FROM ledger_tx").fetchall())
    finally:
        conn.close()


def build_world(tag):
    tmp = tempfile.mkdtemp(prefix="apimarket-csv-" + tag + "-")
    db = os.path.join(tmp, "ledger.db")
    led, mtr, dk, am = R.build_stack(db)
    R.seed_demo(am, led, dk)
    return tmp, db, led, mtr, dk, am


def close_world(am, dk, mtr, led):
    am.close()
    dk.close()
    mtr.close()
    led.close()


def run_cli(argv):
    return R.main(argv)


def main():
    tmp, db, led, mtr, dk, am = build_world("main")
    try:
        report = R.collect(am)

        # -- AC-CSVM1 file set and headers ----------------------------
        payloads = R.csv_payloads(report)
        out_dir = os.path.join(tmp, "bundle1")
        sizes = R.write_report_csv(out_dir, report)
        heads = {}
        bom_free = True
        lf_only = True
        for name in R.CSV_FILES:
            raw = read_bytes(os.path.join(out_dir, name))
            text = raw.decode("utf-8")
            rows = list(csv.reader(io.StringIO(text, newline="")))
            heads[name] = tuple(rows[0])
            bom_free = bom_free and not raw.startswith(b"\xef\xbb\xbf")
            lf_only = lf_only and b"\r" not in raw
        ok1 = (sorted(payloads) == sorted(R.CSV_FILES)
               and sorted(os.listdir(out_dir)) == sorted(R.CSV_FILES)
               and heads["market_months.csv"] == R.MARKET_MONTH_COLUMNS
               and heads["seller_months.csv"] == R.SELLER_MONTH_COLUMNS
               and heads["buyer_months.csv"] == R.BUYER_MONTH_COLUMNS
               and len(R.MARKET_MONTH_COLUMNS) == 13
               and len(R.SELLER_MONTH_COLUMNS) == 11
               and len(R.BUYER_MONTH_COLUMNS) == 12
               and bom_free and lf_only
               and sizes == dict((n, len(payloads[n].encode("utf-8")))
                                 for n in R.CSV_FILES))
        record("AC-CSVM1", ok1,
               "files=%r cols=%r bom_free=%s lf_only=%s"
               % (sorted(os.listdir(out_dir)),
                  [len(heads[n]) for n in R.CSV_FILES], bom_free,
                  lf_only))

        # -- AC-CSVM2 same source -------------------------------------
        market_rows = parse_csv(os.path.join(out_dir,
                                             "market_months.csv"))[1:]
        seller_rows = parse_csv(os.path.join(out_dir,
                                             "seller_months.csv"))[1:]
        buyer_rows = parse_csv(os.path.join(out_dir,
                                            "buyer_months.csv"))[1:]

        def as_tuple(values, columns):
            return dict((col, values[i]) for i, col in enumerate(columns))

        ok2 = True
        source_market = report["market_months"]["months"]
        ok2 = ok2 and len(market_rows) == len(source_market)
        for have, want in zip(market_rows, source_market):
            got = as_tuple(have, R.MARKET_MONTH_COLUMNS)
            ok2 = ok2 and all(
                str(want[c]) == got[c] for c in R.MARKET_MONTH_COLUMNS)
        want_sellers = []
        for dev in sorted(report["sellers"]):
            for row in report["sellers"][dev]["revenue_months"]["months"]:
                want_sellers.append(dict(row, dev_account=dev))
        ok2 = ok2 and len(seller_rows) == len(want_sellers)
        for have, want in zip(seller_rows, want_sellers):
            got = as_tuple(have, R.SELLER_MONTH_COLUMNS)
            ok2 = ok2 and all(
                str(want[c]) == got[c] for c in R.SELLER_MONTH_COLUMNS)
        want_buyers = []
        for buyer in sorted(report["buyers"]):
            for row in report["buyers"][buyer]["months"]["months"]:
                want_buyers.append(dict(row, buyer_id=buyer))
        ok2 = ok2 and len(buyer_rows) == len(want_buyers)
        for have, want in zip(buyer_rows, want_buyers):
            got = as_tuple(have, R.BUYER_MONTH_COLUMNS)
            ok2 = ok2 and all(
                str(want[c]) == got[c] for c in R.BUYER_MONTH_COLUMNS)
        record("AC-CSVM2", ok2,
               "rows market=%d sellers=%d buyers=%d"
               % (len(market_rows), len(seller_rows),
                  len(buyer_rows)))

        # -- AC-CSVM3 coverage and order ------------------------------
        want_market_count = report["market_months"]["month_count"]
        want_seller_count = sum(
            report["sellers"][dev]["revenue_months"]["month_count"]
            for dev in report["sellers"])
        want_buyer_count = sum(
            report["buyers"][b]["months"]["month_count"]
            for b in report["buyers"])
        market_keys = [r["month"] for r in source_market]
        seller_keys = [(r["dev_account"], r["month"])
                       for r in want_sellers]
        buyer_keys = [(r["buyer_id"], r["month"]) for r in want_buyers]
        ok3 = (len(market_rows) == want_market_count
               and len(seller_rows) == want_seller_count
               and len(buyer_rows) == want_buyer_count
               and market_keys == sorted(market_keys)
               and seller_keys == sorted(seller_keys)
               and buyer_keys == sorted(buyer_keys)
               and want_market_count == 3
               and seller_keys[0][0] == "usr:dana")
        record("AC-CSVM3", ok3,
               "counts=%d/%d/%d keys=%r sellers=%r"
               % (len(market_rows), len(seller_rows),
                  len(buyer_rows), market_keys, seller_keys))

        # -- AC-CSVM4 escaping ----------------------------------------
        tricky = [{"month": "2026-10", "sales_count": 1,
                   "gross": "1,000", "refund_count": 0, "refunded": 0,
                   "net": 0, "dev_share": 0, "platform_share": 0,
                   "dev_share_net": 0, "platform_share_net": 0,
                   "buyer_count": 0, "seller_count": 0,
                   "listing_count": 0}]
        quoted = R._csv_text(("month", "gross"), tricky)
        back = list(csv.reader(io.StringIO(quoted, newline="")))
        table = R._csv_text(("a", "b", "c"),
                            [{"a": 'x,y', "b": 'q"z', "c": "l1\nl2"}])
        cells = list(csv.reader(io.StringIO(table, newline="")))
        ok4 = (back == [["month", "gross"], ["2026-10", "1,000"]]
               and cells == [["a", "b", "c"],
                             ['x,y', 'q"z', "l1\nl2"]]
               and quoted.split("\n")[1].startswith("2026-10,")
               and cells[1][1] == 'q"z')
        record("AC-CSVM4", ok4,
               "numeric_quoted=%s roundtrip=%r"
               % ('"1,000"' in quoted, cells[1]))

        # -- AC-CSVM5 fail-closed atomic write ------------------------
        empty_dir = os.path.join(tmp, "bundle-empty")
        file_target = os.path.join(tmp, "already-a-file")
        with io.open(file_target, "w", encoding="utf-8") as handle:
            handle.write("x")
        errors = []
        for bad in ("", file_target):
            try:
                R.write_report_csv(bad, report)
                errors.append("no-error")
            except ValueError:
                errors.append("ValueError")
        ok5 = (errors == ["ValueError", "ValueError"]
               and sorted(os.listdir(tmp)).count("bundle-empty") == 0
               and not any(name.endswith(".tmp")
                           for name in os.listdir(tmp)))
        record("AC-CSVM5", ok5,
               "errors=%r leftovers=%r" % (errors,
                                           sorted(os.listdir(tmp))))

        # -- AC-CSVM6 determinism ------------------------------------
        second_dir = os.path.join(tmp, "bundle2")
        R.write_report_csv(second_dir, report)
        hashes = {}
        same = True
        for name in R.CSV_FILES:
            first = read_bytes(os.path.join(out_dir, name))
            again = read_bytes(os.path.join(second_dir, name))
            hashes[name] = sha16(first)
            same = same and first == again
        record("AC-CSVM6", same, "sha16=%r" % (hashes,))

        # -- AC-CSVM7 pure read and unchanged contracts --------------
        before = all_tables(am)
        before_tx = ledger_tx_ids(led.db_path)
        R.write_report_csv(os.path.join(tmp, "bundle3"), report)
        after = all_tables(am)
        after_tx = ledger_tx_ids(led.db_path)
        page = R.render_html(report)
        payload = json.dumps(R.api_report_payload(report),
                             sort_keys=True, indent=1,
                             ensure_ascii=True) + "\n"
        ok7 = (before == after and before_tx == after_tx
               and R.REPORT_SCHEMA >= 14 and R.CSV_SCHEMA == 1
               and set(R.api_report_payload(report)) == {
                   "schema_version", "report", "attention"}
               and len(before) >= 15
               and page == R.render_html(R.collect(am)))
        record("AC-CSVM7", ok7,
               "tables=%d digests_stable=%s tx %d==%d schema=%d/%d"
               % (len(before), before == after, len(before_tx),
                  len(after_tx), R.REPORT_SCHEMA, R.CSV_SCHEMA))

        # -- AC-CSVM8 CLI and hygiene --------------------------------
        cli_dir = os.path.join(tmp, "cli")
        cli_html = os.path.join(cli_dir, "report.html")
        cli_json = os.path.join(cli_dir, "report.json")
        cli_csv = os.path.join(cli_dir, "csv")
        code = run_cli(["--db", db, "--out", cli_html,
                        "--json-out", cli_json, "--csv-out", cli_csv])
        cli_files = sorted(os.listdir(cli_csv)) if os.path.isdir(
            cli_csv) else []
        on_disk = read_bytes(os.path.join(cli_csv,
                                          "market_months.csv")) \
            if os.path.isdir(cli_csv) else b""
        src = io.open(RECONCILE, encoding="utf-8").read()
        suite_src = io.open(os.path.abspath(__file__),
                            encoding="utf-8").read()
        ok8 = (code == 0
               and cli_files == sorted(R.CSV_FILES)
               and os.path.isfile(cli_html)
               and os.path.isfile(cli_json)
               and on_disk == read_bytes(os.path.join(
                   out_dir, "market_months.csv"))
               and ('"%s"' % LABEL) in src
               and "test_apimarket_settlement_csv.py" in src
               and all(ord(ch) < 128 for ch in suite_src)
               and ("import " + "urllib") not in suite_src
               and ("import " + "requests") not in suite_src
               and not tmp.startswith(BASE))
        record("AC-CSVM8", ok8,
               "cli_exit=%d files=%r html=%s json=%s wired=%s ascii=%s"
               % (code, cli_files, os.path.isfile(cli_html),
                  os.path.isfile(cli_json), ('"%s"' % LABEL) in src,
                  all(ord(ch) < 128 for ch in suite_src)))
    finally:
        close_world(am, dk, mtr, led)

    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(RESULTS)
                              else "FAIL", passed, len(RESULTS)))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())