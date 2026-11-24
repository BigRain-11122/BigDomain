"""Battery suite for tools/category_price_months_board.py - AC-CPMB1..6.

WHY THIS SUITE EXISTS (measured at R3439, not assumed):
api_category_price_months shipped as the per-category monthly asking-price band
- the month-end sampling law, the quartiles, the median and its month-over-month
change - but a search over tools/, preview/ and src/os answered rc=1 with zero
hits. The market had two snapshot price faces and a time axis that only
answered turnover, so "what did this category's median do from month to month"
could only be read from a shell. R3439 renders the shipped envelope on one page;
this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3439 PIN
BEFORE the driver existed):
  AC-CPMB1 the page and its json land, the json carries exactly the pinned
           13-key payload set, every month row carries the shipped 12 keys,
           every category cell the shipped 5 keys, month_count equals the row
           count, and the report points at a file that exists.
  AC-CPMB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world and requires the page json to equal a fresh
           api_category_price_months() reading item for item, disclaimer
           included, month order and category order included.
  AC-CPMB3 the face's identities hold: category_count equals the cell count,
           live counts sum over cells, the month band is the cell extreme,
           the quartiles are ordered, the change exists exactly when both
           medians do and equals their difference, categories ascend with the
           uncategorized bucket last, and the window bounds match the rows.
  AC-CPMB4 the page reads honestly: one marked section per month, one marked
           row per category bucket, a named badge for the uncategorized
           bucket, the dash where the face has nothing, no bare None, the
           laws on the page, and an empty envelope handed to the driver's own
           renderer prints the explicit empty sentence (in-memory probe only).
  AC-CPMB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer verbatim, the non-advice sentence, zero
           external links.
  AC-CPMB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the face is still exercised by its shipped suite on disk.

Read-only over the repository: the provenance world is built in a temp dir and
the probe renders in memory, never inside preview/.

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
TOOL = os.path.join(ROOT, "tools", "category_price_months_board.py")
HTML = os.path.join(ROOT, "preview", "category-price-months-board.html")
JSONF = os.path.join(ROOT, "preview", "category-price-months-board.json")
COPY = os.path.join(ROOT, "preview", "category-price-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_categorypricemonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-category-price-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "month_count", "first_month",
    "last_month", "listing_count", "category_count", "months", "disclaimer",
    "report", "sources", "sizes",
}
ROW_KEYS = {
    "month", "as_of", "live_listing_count", "category_count", "min_price",
    "max_price", "p25_price", "p50_price", "p75_price", "mean_price",
    "p50_change", "categories",
}
CELL_KEYS = {"category", "live_listing_count", "min_price", "max_price",
             "p50_price"}

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
    tmp_root = tempfile.mkdtemp(prefix="cpmb-suite-")
    db = os.path.join(tmp_root, "cpmb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        return dict(am.api_category_price_months())
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("cpmb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_problems(months, envelope):
    problems = []
    seen = [row["month"] for row in months]
    if seen != sorted(seen):
        problems.append("months not ascending")
    if months and envelope.get("first_month") != seen[0]:
        problems.append("first_month")
    if months and envelope.get("last_month") != seen[-1]:
        problems.append("last_month")
    previous = None
    for row in months:
        tag = "month %s" % row["month"]
        cells = row.get("categories") or []
        if len(cells) != int(row["category_count"]):
            problems.append("%s cells" % tag)
        if sum(int(c["live_listing_count"]) for c in cells) != \
                int(row["live_listing_count"]):
            problems.append("%s live sum" % tag)
        lows = [int(c["min_price"]) for c in cells]
        highs = [int(c["max_price"]) for c in cells]
        if lows and row["min_price"] != min(lows):
            problems.append("%s min" % tag)
        if highs and row["max_price"] != max(highs):
            problems.append("%s max" % tag)
        trio = (row["p25_price"], row["p50_price"], row["p75_price"])
        if None not in trio and not (trio[0] <= trio[1] <= trio[2]):
            problems.append("%s quartiles" % tag)
        change = row["p50_change"]
        median = row["p50_price"]
        if change is not None:
            if previous is None or median is None:
                problems.append("%s change without medians" % tag)
            elif float(change) != float(median) - float(previous):
                problems.append("%s change value" % tag)
        if median is None:
            previous = None
        else:
            previous = median
        named = [c["category"] for c in cells if c["category"] is not None]
        if named != sorted(named):
            problems.append("%s order" % tag)
        if cells and any(c["category"] is None for c in cells) and \
                cells[-1]["category"] is not None:
            problems.append("%s uncategorized placement" % tag)
    return problems


def probe_empty():
    return {
        "month_count": 0, "first_month": None, "last_month": None,
        "listing_count": 0, "category_count": 0,
        "disclaimer": "sandbox stand-in disclaimer", "months": [],
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    months = doc.get("months") or []

    # ---- AC-CPMB1: the pair landed with exactly the pinned key sets.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in months)
    cells_ok = all(set(cell.keys()) == CELL_KEYS
                   for row in months for cell in row.get("categories") or [])
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-CPMB1", landed and keys == PAYLOAD_KEYS and rows_ok and cells_ok
       and int(doc.get("month_count", -1)) == len(months) and report_ok
       and sources_ok,
       "landed=%s keys=%d missing=%s extra=%s rows=%s cells=%s count=%d/%d "
       "report=%s sources=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), rows_ok, cells_ok,
          len(months), int(doc.get("month_count", -1)), report_ok,
          sources_ok))

    # ---- AC-CPMB2: every printed value is the shipped face's own.
    live = live_world()
    rows_same = json.dumps(months, sort_keys=True) == json.dumps(
        [{key: row[key] for key in ROW_KEYS}
         for row in live.get("months") or []], sort_keys=True)
    disc_same = doc.get("disclaimer") == live.get("disclaimer")
    bounds_same = (doc.get("first_month") == live.get("first_month")
                   and doc.get("last_month") == live.get("last_month")
                   and doc.get("listing_count") == live.get("listing_count")
                   and doc.get("category_count") == live.get("category_count"))
    ok("AC-CPMB2", rows_same and disc_same and bounds_same and bool(months),
       "identical=%s disclaimer_same=%s bounds_same=%s rows=%d"
       % (rows_same, disc_same, bounds_same, len(months)))

    # ---- AC-CPMB3: the face's identities and this page's own laws hold.
    driver = load_driver()
    problems = identity_problems(months, doc) if months else ["no months"]
    law_problems = driver.check_laws(doc if doc else live)
    ok("AC-CPMB3", not problems and not law_problems,
       "problems=%s driver_laws=%s"
       % (problems[:4] if problems else [], law_problems[:3]
          if law_problems else []))

    # ---- AC-CPMB4: honest page face, badges, dashes, empty probe.
    dash = labels.get("none", "-")
    marked = all(('data-month="%s"' % row["month"]) in page for row in months)
    marked_cells = all(
        ('data-category="%s"' % ("" if cell["category"] is None
                                 else cell["category"])) in page
        for row in months for cell in row.get("categories") or [])
    uncategorized = any(cell["category"] is None
                        for row in months for cell in row.get("categories") or [])
    badge_ok = (not uncategorized) or labels.get("badge_uncategorized", "") in page
    null_change = [row for row in months if row["p50_change"] is None]
    dash_change = all("<b>%s</b>" % dash in page for _ in null_change)
    stand_in = ">None<" in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_sampling", "law_window", "law_median",
             "law_order", "law_change", "law_bar", "law_scope",
             "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    cap_ok = labels.get("bar_caption", "") in page
    empty_probe_ok = False
    try:
        probe_html = driver.build_html(probe_empty(), labels,
                                       "2026-01-01 00:00:00Z",
                                       doc.get("disclaimer") or "")
        empty_probe_ok = (labels.get("empty", "") in probe_html
                          and ">None<" not in probe_html
                          and 'data-month="' not in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-CPMB4", marked and marked_cells and badge_ok and dash_change
       and not stand_in and laws_ok and cap_ok and empty_probe_ok,
       "months=%s cells=%s badge=%s null_change=%d dash=%s laws=%s cap=%s "
       "empty_probe=%s stand_in_none=%s"
       % (marked, marked_cells, badge_ok, len(null_change), dash_change,
          laws_ok, cap_ok, empty_probe_ok, stand_in))

    # ---- AC-CPMB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    notadvice = labels.get("law_notadvice", "") in page
    ok("AC-CPMB5", aigc and on_page and external == 0 and notadvice,
       "aigc=%s disclaimer_on_page=%s external_links=%d notadvice=%s"
       % (aigc, on_page, external, notadvice))

    # ---- AC-CPMB6: --check reads clean, writes nothing, wiring intact.
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
        "api_category_price_months(" in read(FACE_SUITE)
    ok("AC-CPMB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
