"""Battery suite for tools/category_velocity_months_board.py - AC-CVMB1..6.

WHY THIS SUITE EXISTS (measured at R3441, not assumed):
api_category_velocity_months shipped as the per-category monthly net sell-through
velocity - the sale-month sampling law, the net authority, the cycle-opening
duration, the contiguous window and the whole-history benchmark - but a search
over tools/, preview/ and src/os answered rc=1 with zero hits. The market had a
lifetime velocity face, a supply face and an asking-price face, so "how many did
this category sell this month, how long did each sit, and is it slower than last
month" could only be read from a shell. R3441 renders the shipped envelope on
one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3441 PIN
BEFORE the driver existed):
  AC-CVMB1 the page and its json land, the json carries exactly the pinned
           19-key payload set, every month row carries the shipped 13 keys,
           every category cell the shipped 5 keys, month_count equals the row
           count, and the report points at a file that exists.
  AC-CVMB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world and requires the page json to equal a fresh
           api_category_velocity_months() reading item for item, disclaimer
           included, month order and category order included.
  AC-CVMB3 the face's identities hold: months are contiguous, cell counts sum
           to the month row, categories ascend with the uncategorized bucket
           last, fastest <= median <= slowest, the four aggregates exist
           exactly when the month sold something, the month count and the
           distinct listing count bound the envelope, the peak is the earliest
           maximum month, the month-over-month change needs two months, and the
           per-row benchmark equals the envelope one.
  AC-CVMB4 the page reads honestly: one marked section per month, one marked
           row per category bucket, a named badge for the uncategorized bucket,
           the dash where the face has nothing, no bare None, the laws on the
           page, and an empty envelope plus a synthetic zero-sale month handed
           to the driver's own renderer print the honest empty sentence and a
           barless dash row (in-memory probes only).
  AC-CVMB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer verbatim, the non-advice sentence, zero
           external links.
  AC-CVMB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the face is still exercised by its shipped suite on disk.

Read-only over the repository: the provenance world is built in a temp dir and
the probes render in memory, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "category_velocity_months_board.py")
HTML = os.path.join(ROOT, "preview", "category-velocity-months-board.html")
JSONF = os.path.join(ROOT, "preview", "category-velocity-months-board.json")
COPY = os.path.join(ROOT, "preview", "category-velocity-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_categoryvelocitymonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-category-velocity-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "month_count", "first_month",
    "last_month", "sale_count", "listing_count", "category_count",
    "peak_month", "peak_sale_count", "month_over_month_change",
    "market_avg_seconds", "market_median_seconds", "months", "disclaimer",
    "report", "sources", "sizes",
}
ROW_KEYS = {
    "month", "as_of", "sale_count", "listing_count", "category_count",
    "avg_seconds", "median_seconds", "fastest_seconds", "slowest_seconds",
    "fastest_listing_id", "slowest_listing_id", "market_avg_seconds",
    "categories",
}
CELL_KEYS = {"category", "sale_count", "listing_count", "avg_seconds",
             "median_seconds"}

CHECKS = []
FAILS = []


def ok(name, cond, detail):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def stamp(path):
    if not os.path.exists(path):
        return None
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def run_tool(args, cwd=ROOT):
    proc = subprocess.run(
        [sys.executable, TOOL] + args, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def live_world():
    """The shipped reading over the suite's own throwaway demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="cvmb-suite-")
    db = os.path.join(tmp_root, "cvmb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        return dict(am.api_category_velocity_months())
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("cvmb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_problems(months, envelope):
    problems = []
    seen = [row["month"] for row in months]
    if seen != sorted(seen):
        problems.append("months not ascending")
    for index in range(1, len(seen)):
        year, month = int(seen[index - 1][:4]), int(seen[index - 1][5:7])
        month += 1
        if month > 12:
            month = 1
            year += 1
        if "%04d-%02d" % (year, month) != seen[index]:
            problems.append("gap after %s" % seen[index - 1])
    if months and envelope.get("first_month") != seen[0]:
        problems.append("first_month")
    if months and envelope.get("last_month") != seen[-1]:
        problems.append("last_month")
    total_sales = 0
    listings_sum = 0
    listings_max = 0
    buckets = set()
    for row in months:
        tag = "month %s" % row["month"]
        cells = row.get("categories") or []
        if len(cells) != int(row["category_count"]):
            problems.append("%s cells" % tag)
        if sum(int(c["sale_count"]) for c in cells) != int(row["sale_count"]):
            problems.append("%s sale sum" % tag)
        if sum(int(c["listing_count"]) for c in cells) != \
                int(row["listing_count"]):
            problems.append("%s listing sum" % tag)
        if int(row["sale_count"]) == 0:
            if any(row[key] is not None for key in
                   ("avg_seconds", "median_seconds", "fastest_seconds",
                    "slowest_seconds")):
                problems.append("%s zero aggregates" % tag)
        else:
            trio = (row["fastest_seconds"], row["median_seconds"],
                    row["slowest_seconds"])
            if None in trio or not trio[0] <= trio[1] <= trio[2]:
                problems.append("%s order" % tag)
        if row["market_avg_seconds"] != envelope.get("market_avg_seconds"):
            problems.append("%s benchmark" % tag)
        total_sales += int(row["sale_count"])
        listings_sum += int(row["listing_count"])
        listings_max = max(listings_max, int(row["listing_count"]))
        named = [c["category"] for c in cells if c["category"] is not None]
        if named != sorted(named):
            problems.append("%s order" % tag)
        if cells and any(c["category"] is None for c in cells) and \
                cells[-1]["category"] is not None:
            problems.append("%s uncategorized placement" % tag)
        for cell in cells:
            buckets.add(cell["category"])
    if months and total_sales != int(envelope.get("sale_count", -1)):
        problems.append("envelope sale total")
    if months and not (listings_max <= int(envelope.get("listing_count", -1))
                       <= listings_sum):
        problems.append("envelope listing bound")
    expected = len([b for b in buckets if b is not None]) \
        + (1 if None in buckets else 0)
    if months and expected != int(envelope.get("category_count", -1)):
        problems.append("envelope bucket count")
    if len(months) >= 2:
        expected_change = (int(months[-1]["sale_count"])
                           - int(months[-2]["sale_count"]))
        if envelope.get("month_over_month_change") != expected_change:
            problems.append("month change")
    elif months and envelope.get("month_over_month_change") is not None:
        problems.append("month change without two months")
    return problems


def probe_empty():
    return {
        "month_count": 0, "first_month": None, "last_month": None,
        "sale_count": 0, "listing_count": 0, "category_count": 0,
        "peak_month": None, "peak_sale_count": None,
        "month_over_month_change": None, "market_avg_seconds": None,
        "market_median_seconds": None,
        "disclaimer": "sandbox stand-in disclaimer", "months": [],
    }


def probe_zero_month():
    sold = {
        "month": "2026-08", "as_of": "2026-08-31T23:59:59Z", "sale_count": 1,
        "listing_count": 1, "category_count": 1, "avg_seconds": 116.67,
        "median_seconds": 100.0, "fastest_seconds": 50,
        "slowest_seconds": 200, "fastest_listing_id": 1,
        "slowest_listing_id": 1, "market_avg_seconds": 100.0,
        "categories": [{"category": "data", "sale_count": 1,
                        "listing_count": 1, "avg_seconds": 100.0,
                        "median_seconds": 100.0}],
    }
    quiet = {
        "month": "2026-09", "as_of": "2026-09-30T23:59:59Z", "sale_count": 0,
        "listing_count": 0, "category_count": 0, "avg_seconds": None,
        "median_seconds": None, "fastest_seconds": None,
        "slowest_seconds": None, "fastest_listing_id": None,
        "slowest_listing_id": None, "market_avg_seconds": 100.0,
        "categories": [],
    }
    return {
        "month_count": 2, "first_month": "2026-08", "last_month": "2026-09",
        "sale_count": 1, "listing_count": 1, "category_count": 1,
        "peak_month": "2026-08", "peak_sale_count": 1,
        "month_over_month_change": -1, "market_avg_seconds": 100.0,
        "market_median_seconds": 100.0,
        "disclaimer": "sandbox stand-in disclaimer",
        "months": [sold, quiet],
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    months = doc.get("months") or []

    # ---- AC-CVMB1: the pair landed with exactly the pinned key sets.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in months)
    cells_ok = all(set(cell.keys()) == CELL_KEYS
                   for row in months for cell in row.get("categories") or [])
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-CVMB1", landed and keys == PAYLOAD_KEYS and rows_ok and cells_ok
       and int(doc.get("month_count", -1)) == len(months) and report_ok
       and sources_ok,
       "landed=%s keys=%d missing=%s extra=%s rows=%s cells=%s count=%d/%d "
       "report=%s sources=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), rows_ok, cells_ok,
          len(months), int(doc.get("month_count", -1)), report_ok,
          sources_ok))

    # ---- AC-CVMB2: every printed value is the shipped face's own.
    live = live_world()
    rows_same = json.dumps(months, sort_keys=True) == json.dumps(
        [{key: row[key] for key in ROW_KEYS}
         for row in live.get("months") or []], sort_keys=True)
    disc_same = doc.get("disclaimer") == live.get("disclaimer")
    bounds = ("first_month", "last_month", "sale_count", "listing_count",
              "category_count", "peak_month", "peak_sale_count",
              "month_over_month_change", "market_avg_seconds",
              "market_median_seconds")
    bounds_same = all(doc.get(key) == live.get(key) for key in bounds)
    ok("AC-CVMB2", rows_same and disc_same and bounds_same and bool(months),
       "identical=%s disclaimer_same=%s bounds_same=%s rows=%d"
       % (rows_same, disc_same, bounds_same, len(months)))

    # ---- AC-CVMB3: the face's identities and this page's own laws hold.
    driver = load_driver()
    problems = identity_problems(months, doc) if months else ["no months"]
    law_problems = driver.check_laws(doc if doc else live)
    ok("AC-CVMB3", not problems and not law_problems,
       "problems=%s driver_laws=%s"
       % (problems[:4] if problems else [], law_problems[:3]
          if law_problems else []))

    # ---- AC-CVMB4: honest page face, badges, dashes, empty and zero probes.
    dash = labels.get("none", "-")
    marked = all(('data-month="%s"' % row["month"]) in page for row in months)
    marked_cells = all(
        ('data-category="%s"' % ("" if cell["category"] is None
                                 else cell["category"])) in page
        for row in months for cell in row.get("categories") or [])
    uncategorized = any(cell["category"] is None
                        for row in months
                        for cell in row.get("categories") or [])
    badge_ok = (not uncategorized) or \
        labels.get("badge_uncategorized", "") in page
    null_change = doc.get("month_over_month_change") is None
    dash_change = (not null_change) or ("<b>%s</b>" % dash in page)
    stand_in = ">None<" in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_sampling", "law_window", "law_net", "law_cats",
             "law_nulls", "law_peak", "law_change", "law_benchmark", "law_bar",
             "law_scope", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    cap_ok = labels.get("bar_caption", "") in page
    empty_probe_ok = False
    zero_probe_ok = False
    try:
        empty_html = driver.build_html(probe_empty(), labels,
                                       "2026-01-01 00:00:00Z",
                                       doc.get("disclaimer") or "")
        empty_probe_ok = (labels.get("empty", "") in empty_html
                          and ">None<" not in empty_html
                          and 'data-month="' not in empty_html)
        zero_html = driver.build_html(probe_zero_month(), labels,
                                      "2026-01-01 00:00:00Z",
                                      doc.get("disclaimer") or "")
        quiet_section = zero_html.split('data-month="2026-09"', 1)[-1]
        zero_probe_ok = (zero_html.count('class="bar"') == 1
                         and "<b>%s</b>" % dash in quiet_section
                         and ">None<" not in zero_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-CVMB4", marked and marked_cells and badge_ok and dash_change
       and not stand_in and laws_ok and cap_ok and empty_probe_ok
       and zero_probe_ok,
       "months=%s cells=%s badge=%s dash=%s laws=%s cap=%s empty=%s zero=%s "
       "stand_in_none=%s"
       % (marked, marked_cells, badge_ok, dash_change, laws_ok, cap_ok,
          empty_probe_ok, zero_probe_ok, stand_in))

    # ---- AC-CVMB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    notadvice = labels.get("law_notadvice", "") in page
    ok("AC-CVMB5", aigc and on_page and external == 0 and notadvice,
       "aigc=%s disclaimer_on_page=%s external_links=%d notadvice=%s"
       % (aigc, on_page, external, notadvice))

    # ---- AC-CVMB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and \
        "api_category_velocity_months(" in read(FACE_SUITE)
    ok("AC-CVMB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
