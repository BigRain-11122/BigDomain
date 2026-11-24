"""Battery suite for tools/category_watch_months_board.py - AC-CWMB1..6.

WHY THIS SUITE EXISTS (measured at R3450, not assumed):
api_category_watch_months shipped the market's attention by CATEGORY on a
monthly axis - watches and unwatches booked in the month of the event, a
running live count per category, the busy month and the month-over-month
change - but a search over tools/, preview/ and src/os answered rc=1 for its
name. R3450 renders the shipped envelope on one page; this suite grades the
page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3450 PIN row landed with the driver and says so):
  AC-CWMB1 the pair lands, the json carries exactly the pinned eight-key payload
           set, the envelope the shipped 15 keys, every month row the shipped 7
           keys and every cell the shipped 7 keys, the report points at a file
           that exists and the four source fingerprints are present.
  AC-CWMB2 the data is the shipped face's own: the suite builds its own
           throwaway world through the shipped publish, watch and unwatch doors
           under its own pinned clock, re-reads the face and requires the page
           json to equal that reading item for item, disclaimer and ordering
           included.
  AC-CWMB3 the face identities hold and the driver refuses a broken one: the
           contiguous grid, the per-row cell sums, the replay of every category
           cell, the ordered cells with the uncategorized bucket last, the
           envelope sums, the peak month, the month-over-month change and the
           flag-off subtraction all hold - and a forged live count is refused
           by name.
  AC-CWMB4 the page reads honestly: one marked card per month, one marked row
           per cell, the dash where a number is absent, no bare None, the bar
           caption on the page, a bar only where watches were opened, the
           honest zero month and the empty sentence both reachable.
  AC-CWMB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer verbatim, the non-advice sentence, zero
           external links.
  AC-CWMB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the face is still exercised by its shipped suite on disk.

Read-only over the repository: the provenance world is built in a temp dir and
the empty probe renders in memory, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import importlib.util
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "category_watch_months_board.py")
HTML = os.path.join(ROOT, "preview", "category-watch-months-board.html")
JSONF = os.path.join(ROOT, "preview", "category-watch-months-board.json")
COPY = os.path.join(ROOT, "preview", "category-watch-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_categorywatchmonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-category-watch-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "envelope", "disclaimer", "report",
    "sources", "sizes",
}
ENVELOPE_KEYS = {
    "month_count", "first_month", "last_month", "watch_count",
    "unwatch_count", "net_count", "live_watch_count", "category_count",
    "buyer_count", "listing_count", "peak_month", "peak_watch_count",
    "month_over_month_change", "months", "disclaimer",
}
MONTH_KEYS = {
    "month", "watch_count", "unwatch_count", "net_count", "active_count",
    "category_count", "categories",
}
CELL_KEYS = {
    "category", "watch_count", "unwatch_count", "net_count", "active_count",
    "buyer_count", "listing_count",
}

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


def load_driver():
    spec = importlib.util.spec_from_file_location("cwmb_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_world(am, clock):
    """The suite's own copy of the story, every row through a shipped door."""
    clock["value"] = "2026-06-01T00:00:00Z"
    am.publish_api("usr:dana", "data-lens", "Data Lens",
                   "row counts for one table",
                   {"endpoint": "/rows/count", "rows": 1200}, 12, True,
                   category="data")
    am.publish_api("usr:dana", "data-digest", "Data Digest",
                   "weekly digest of new rows",
                   {"endpoint": "/rows/digest", "rows": 40}, 9, True,
                   category="data")
    am.publish_api("usr:frank", "tools-forge", "Tools Forge",
                   "batch rename helper",
                   {"endpoint": "/tools/rename", "batch": 200}, 7, True,
                   category="tools")
    am.publish_api("usr:frank", "tools-mint", "Tools Mint",
                   "csv to json converter",
                   {"endpoint": "/tools/mint", "batch": 100}, 5, True,
                   category="tools")
    board = am.api_board() or {}
    by_key = {}
    for row in board.get("listings") or []:
        by_key[str(row["listing_key"])] = int(row["listing_id"])
    data_lens = by_key["data-lens"]
    data_digest = by_key["data-digest"]
    tools_forge = by_key["tools-forge"]
    tools_mint = by_key["tools-mint"]
    risk = by_key["risk-scan"]

    clock["value"] = "2026-06-10T00:00:00Z"
    am.watch_api("usr:bob", data_lens)
    am.watch_api("usr:carol", tools_forge)
    clock["value"] = "2026-07-08T00:00:00Z"
    am.watch_api("usr:dave", data_lens)
    am.watch_api("usr:bob", risk)
    clock["value"] = "2026-09-04T00:00:00Z"
    am.unwatch_api("usr:bob", data_lens)
    am.watch_api("usr:carol", tools_mint)
    am.unwatch_api("usr:bob", risk)
    clock["value"] = "2026-10-06T00:00:00Z"
    am.watch_api("usr:erin", data_digest)
    clock["value"] = "2026-11-03T00:00:00Z"
    am.unwatch_api("usr:carol", tools_forge)
    am.watch_api("usr:dave", tools_forge)
    return clock


def live_world(driver):
    import apimarket as A
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="cwmb-suite-")
    db = os.path.join(tmp_root, "suite.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    clock = {"value": "2026-06-01T00:00:00Z"}
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = lambda: clock["value"]
        build_world(am, clock)
        envelope = dict(am.api_category_watch_months())
        no_uncat = dict(am.api_category_watch_months(
            include_uncategorized=False))
    finally:
        A._now_utc = orig_now
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    return envelope, no_uncat


def trim(envelope):
    doc = {key: envelope[key] for key in ENVELOPE_KEYS if key != "months"}
    months = []
    for row in envelope.get("months") or []:
        item = {key: row[key] for key in MONTH_KEYS if key != "categories"}
        item["categories"] = [{key: cell[key] for key in CELL_KEYS}
                              for cell in row.get("categories") or []]
        months.append(item)
    doc["months"] = months
    return doc


def same(left, right):
    return json.dumps(left, sort_keys=True, default=str) == json.dumps(
        right, sort_keys=True, default=str)


def main():
    if not os.path.exists(TOOL):
        print("FAIL AC-CWMB1 driver missing")
        return 2
    driver = load_driver()
    labels = json.loads(read(COPY))
    page = json.loads(read(JSONF))
    doc = read(HTML)

    envelope = page.get("envelope") or {}
    rows = envelope.get("months") or []
    cells = [cell for row in rows for cell in row.get("categories") or []]

    # ---- AC-CWMB1 contract ------------------------------------------------
    missing_payload = sorted(PAYLOAD_KEYS - set(page))
    extra_payload = sorted(set(page) - PAYLOAD_KEYS)
    report_path = os.path.join(ROOT, page.get("report") or "")
    sources = page.get("sources") or {}
    sizes = page.get("sizes") or {}
    ok("AC-CWMB1",
       not missing_payload and not extra_payload
       and set(envelope) == ENVELOPE_KEYS
       and all(set(row) == MONTH_KEYS for row in rows)
       and all(set(cell) == CELL_KEYS for cell in cells)
       and os.path.exists(report_path)
       and sorted(sources) == ["apimarket", "copy", "driver", "report"]
       and sizes.get("html") == os.path.getsize(HTML)
       and sizes.get("json") == os.path.getsize(JSONF)
       and page.get("face") == "api_category_watch_months",
       "payload_missing=%r payload_extra=%r months=%d cells=%d report=True "
       "sources=True" % (missing_payload, extra_payload, len(rows),
                         len(cells)))

    # ---- AC-CWMB2 the data is the shipped face's own ----------------------
    live, live_no_uncat = live_world(driver)
    same_all = same(trim(live), envelope)
    same_words = page.get("disclaimer") == live.get("disclaimer")
    same_order = ([cell["category"] for cell in cells]
                  == [cell["category"] for row in live.get("months") or []
                      for cell in row.get("categories") or []])
    ok("AC-CWMB2", same_all and same_words and same_order,
       "envelope_same=%r disclaimer_same=%r order_same=%r months=%d cells=%d"
       % (same_all, same_words, same_order, len(rows), len(cells)))

    # ---- AC-CWMB3 laws, plus a forged envelope refused by name ------------
    driver_problems = driver.check_laws(live, live_no_uncat)
    forged = json.loads(json.dumps(live, default=str))
    forged["live_watch_count"] = int(forged["live_watch_count"]) + 7
    forged_problems = driver.check_laws(forged, live_no_uncat)
    identities = True
    zero_row = False
    negative_row = False
    uncategorized = False
    last_live = 0
    for row in rows:
        if int(row["watch_count"]) == 0 and int(row["unwatch_count"]) == 0:
            zero_row = True
        if int(row["net_count"]) < 0:
            negative_row = True
        if any(cell["category"] is None for cell in row.get("categories")
               or []):
            uncategorized = True
        if sum(int(cell["net_count"]) for cell in row.get("categories") or []
               ) != int(row["net_count"]):
            identities = False
    if rows:
        last_live = int(rows[-1]["active_count"])
        if last_live != int(envelope["live_watch_count"]):
            identities = False
    if int(envelope["net_count"]) != (int(envelope["watch_count"])
                                      - int(envelope["unwatch_count"])):
        identities = False
    ok("AC-CWMB3",
       not driver_problems and len(forged_problems) >= 1 and identities
       and zero_row and negative_row and uncategorized,
       "driver_problems=%d forged_problems=%d identities=%r zero_row=%r "
       "negative_row=%r uncategorized=%r" % (len(driver_problems),
                                             len(forged_problems), identities,
                                             zero_row, negative_row,
                                             uncategorized))

    # ---- AC-CWMB4 the page reads honestly ---------------------------------
    dash = labels["none"]
    month_marked = all(('data-month="%s"' % row["month"]) in doc
                       for row in rows)
    cell_marked = all(
        ('data-category="%s"' % ("uncategorized" if cell["category"] is None
                                 else cell["category"])) in doc
        for cell in cells)
    bare_none = "None" in doc or "null" in doc
    caption = labels["bar_caption"] in doc
    bars = doc.count('<div class="bar">')
    wants = sum(1 for cell in cells if int(cell["watch_count"]) > 0)
    empty_ok = labels["empty"] in doc
    dash_ok = dash in doc
    probe = {key: None for key in ENVELOPE_KEYS}
    probe.update({"month_count": 0, "watch_count": 0, "unwatch_count": 0,
                  "net_count": 0, "live_watch_count": 0, "category_count": 0,
                  "buyer_count": 0, "listing_count": 0, "months": [],
                  "disclaimer": "x"})
    empty_html = driver.build_html(probe, labels, "2026-11-25 00:00:00Z", "x")
    empty_probe = labels["empty"] in empty_html
    ok("AC-CWMB4",
       month_marked and cell_marked and not bare_none and caption
       and bars == wants and empty_ok and dash_ok and empty_probe,
       "month_marked=%r cell_marked=%r no_bare_none=%r caption=%r bars=%d/%d "
       "empty_sentence=%r dash=%r empty_probe=%r"
       % (month_marked, cell_marked, not bare_none, caption, bars, wants,
          empty_ok, dash_ok, empty_probe))

    # ---- AC-CWMB5 compliance ---------------------------------------------
    disclaimer = page.get("disclaimer") or ""
    aigc = "AIGC" in doc
    verbatim = bool(disclaimer) and disclaimer in doc
    notadvice = labels["law_notadvice"] in doc
    zero_links = "http://" not in doc and "https://" not in doc
    ok("AC-CWMB5", aigc and verbatim and notadvice and zero_links,
       "aigc=%r disclaimer_verbatim=%r notadvice=%r zero_links=%r"
       % (aigc, verbatim, notadvice, zero_links))

    # ---- AC-CWMB6 no older criterion is relaxed --------------------------
    before = (stamp(HTML), stamp(JSONF), stamp(COPY))
    import subprocess
    proc = subprocess.run([sys.executable, TOOL, "--check"], cwd=ROOT,
                          capture_output=True, text=True)
    after = (stamp(HTML), stamp(JSONF), stamp(COPY))
    registry = read(REGISTRY)
    registered = ('"%s"' % ROW) in registry
    row_block = registry.split('"%s"' % ROW, 1)[-1][:160]
    declared = ("%d)" % DECLARED) in row_block
    face_suite = os.path.exists(FACE_SUITE)
    face_ac = "AC-CWM1" in read(FACE_SUITE) if face_suite else False
    ok("AC-CWMB6",
       proc.returncode == 0 and "CHECK PASS" in proc.stdout
       and before == after and registered and declared and face_suite
       and face_ac,
       "readonly=%r check_rc=%d registered=%r declared_hit=%r face_suite=%r"
       % (before == after, proc.returncode, registered, declared, face_suite))

    print("SUITE %s %d/%d declared=%d row=%s"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED, ROW))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.path.insert(0, LEDGER_DIR)
    sys.exit(main())