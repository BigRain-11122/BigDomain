"""Battery suite for tools/category_question_months_board.py - AC-CQMB1..6.

WHY THIS SUITE EXISTS (measured at R3451, not assumed):
api_category_question_months shipped the market's pre-sale pressure BY CATEGORY
on a monthly axis - a question booked in the month it was asked and in the
category in force at that instant, the answered leg credited back to the asking
month, a contiguous grid with honest zero rows and a monotone per-category
accumulator - but a search over tools/, preview/ and src/os answered zero
readers for its name. R3451 renders the shipped envelope on one page; this
suite grades the page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3451 PIN row landed with the driver and says so):
  AC-CQMB1 the pair lands, the json carries exactly the pinned eight-key payload
           set, the envelope the shipped 17 keys, every month row the shipped 11
           keys and every cell the shipped 9 keys, the report points at a file
           that exists and the four source fingerprints are present.
  AC-CQMB2 the data is the shipped face's own: the suite builds its own
           throwaway world through the shipped publish, ask and answer doors
           under its own pinned clock, re-reads the face and requires the page
           json to equal that reading item for item, disclaimer and ordering
           included.
  AC-CQMB3 the face identities hold and the driver refuses a broken one: the
           contiguous grid, the per-row cell sums, the per-category replay, the
           ordered cells with the uncategorized bucket last, the envelope sums,
           the answer-rate law, the peak month, the latest month and the
           flag-off subtraction all hold - and a forged cell answer count is
           refused by name.
  AC-CQMB4 the page reads honestly: one marked card per month, one marked row
           per cell, the dash where a number is absent, no bare None, the bar
           caption on the page, a bar only where questions were asked, the
           honest zero month and the empty sentence both reachable.
  AC-CQMB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer verbatim, the non-advice sentence, zero
           external links.
  AC-CQMB6 no older criterion is relaxed: the landed pair answers its own
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
TOOL = os.path.join(ROOT, "tools", "category_question_months_board.py")
HTML = os.path.join(ROOT, "preview", "category-question-months-board.html")
JSONF = os.path.join(ROOT, "preview", "category-question-months-board.json")
COPY = os.path.join(ROOT, "preview",
                    "category-question-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_categoryquestionmonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-category-question-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "envelope", "disclaimer", "report",
    "sources", "sizes",
}
ENVELOPE_KEYS = {
    "question_count", "answered_count", "unanswered_count", "answer_rate",
    "buyer_count", "seller_count", "listing_count", "category_count",
    "month_count", "active_month_count", "peak_month", "peak_question_count",
    "first_month", "last_month", "latest_month_question_count", "disclaimer",
    "months",
}
MONTH_KEYS = {
    "month", "question_count", "answered_count", "unanswered_count",
    "answer_rate", "category_count", "buyer_count", "seller_count",
    "listing_count", "running_question", "categories",
}
CELL_KEYS = {
    "category", "question_count", "answered_count", "unanswered_count",
    "answer_rate", "buyer_count", "seller_count", "listing_count",
    "running_question",
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
    spec = importlib.util.spec_from_file_location("cqmb_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _qid(result):
    if isinstance(result, dict):
        return result["question_id"]
    return result


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
    ids = {}
    owners = {}
    for row in board.get("listings") or []:
        key = str(row["listing_key"])
        ids[key] = int(row["listing_id"])
        owners[key] = str(row.get("dev_account"))
    data_lens = ids["data-lens"]
    data_digest = ids["data-digest"]
    tools_forge = ids["tools-forge"]
    tools_mint = ids["tools-mint"]
    risk = ids["risk-scan"]

    clock["value"] = "2026-06-10T00:00:00Z"
    bob_june = _qid(am.ask_question("usr:bob", data_lens,
                                    "does this count one table only?"))
    carol_june = _qid(am.ask_question("usr:carol", data_lens,
                                      "is the count cached?"))
    clock["value"] = "2026-07-05T00:00:00Z"
    dave_july = _qid(am.ask_question("usr:dave", tools_forge,
                                     "does it keep file names?"))
    _qid(am.ask_question("usr:erin", risk, "which exchange does this read?"))
    clock["value"] = "2026-09-09T00:00:00Z"
    bob_sept = _qid(am.ask_question("usr:bob", data_digest,
                                    "how many rows per digest?"))
    carol_sept = _qid(am.ask_question("usr:carol", tools_mint,
                                      "can it read utf-8 csv?"))
    clock["value"] = "2026-10-12T00:00:00Z"
    _qid(am.ask_question("usr:dave", data_lens,
                         "does it follow schema changes?"))
    erin_oct = _qid(am.ask_question("usr:erin", risk, "is the feed delayed?"))
    clock["value"] = "2026-11-06T00:00:00Z"
    _qid(am.ask_question("usr:bob", tools_forge, "does it batch 500 files?"))

    clock["value"] = "2026-07-02T00:00:00Z"
    am.answer_question(owners["data-lens"], bob_june, "one table, yes")
    clock["value"] = "2026-07-06T00:00:00Z"
    am.answer_question(owners["tools-forge"], dave_july, "names are kept")
    clock["value"] = "2026-09-30T00:00:00Z"
    am.answer_question(owners["data-lens"], carol_june, "not cached")
    clock["value"] = "2026-10-01T00:00:00Z"
    am.answer_question(owners["data-digest"], bob_sept, "forty rows")
    clock["value"] = "2026-11-02T00:00:00Z"
    am.answer_question(owners["tools-mint"], carol_sept, "utf-8 only")
    clock["value"] = "2026-11-20T00:00:00Z"
    am.answer_question(owners["risk-scan"], erin_oct, "ten minute delay")
    return clock


def live_world():
    import apimarket as A
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="cqmb-suite-")
    db = os.path.join(tmp_root, "suite.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    clock = {"value": "2026-06-01T00:00:00Z"}
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = lambda: clock["value"]
        build_world(am, clock)
        envelope = dict(am.api_category_question_months())
        no_uncat = dict(am.api_category_question_months(
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
        print("FAIL AC-CQMB1 driver missing")
        return 2
    driver = load_driver()
    labels = json.loads(read(COPY))
    page = json.loads(read(JSONF))
    doc = read(HTML)

    envelope = page.get("envelope") or {}
    rows = envelope.get("months") or []
    cells = [cell for row in rows for cell in row.get("categories") or []]

    # ---- AC-CQMB1 contract ------------------------------------------------
    missing_payload = sorted(PAYLOAD_KEYS - set(page))
    extra_payload = sorted(set(page) - PAYLOAD_KEYS)
    report_path = os.path.join(ROOT, page.get("report") or "")
    sources = page.get("sources") or {}
    sizes = page.get("sizes") or {}
    ok("AC-CQMB1",
       not missing_payload and not extra_payload
       and set(envelope) == ENVELOPE_KEYS
       and all(set(row) == MONTH_KEYS for row in rows)
       and all(set(cell) == CELL_KEYS for cell in cells)
       and os.path.exists(report_path)
       and sorted(sources) == ["apimarket", "copy", "driver", "report"]
       and sizes.get("html") == os.path.getsize(HTML)
       and sizes.get("json") == os.path.getsize(JSONF)
       and page.get("face") == "api_category_question_months",
       "payload_missing=%r payload_extra=%r months=%d cells=%d report=True "
       "sources=True" % (missing_payload, extra_payload, len(rows),
                         len(cells)))

    # ---- AC-CQMB2 the data is the shipped face's own ----------------------
    live, live_no_uncat = live_world()
    same_all = same(trim(live), envelope)
    same_words = page.get("disclaimer") == live.get("disclaimer")
    same_order = ([cell["category"] for cell in cells]
                  == [cell["category"] for row in live.get("months") or []
                      for cell in row.get("categories") or []])
    ok("AC-CQMB2", same_all and same_words and same_order,
       "envelope_same=%r disclaimer_same=%r order_same=%r months=%d cells=%d"
       % (same_all, same_words, same_order, len(rows), len(cells)))

    # ---- AC-CQMB3 laws, plus a forged cell refused by name ----------------
    driver_problems = driver.check_laws(live, live_no_uncat)
    forged = json.loads(json.dumps(live, default=str))
    forged["months"][0]["categories"][0]["answered_count"] = int(
        forged["months"][0]["categories"][0]["answered_count"]) + 7
    forged_problems = driver.check_laws(forged, live_no_uncat)
    identities = True
    zero_row = False
    uncategorized = False
    backlog_row = False
    last_running = 0
    for row in rows:
        row_cells = row.get("categories") or []
        if int(row["question_count"]) == 0 and not row_cells:
            zero_row = True
        if any(cell["category"] is None for cell in row_cells):
            uncategorized = True
        if int(row["unanswered_count"]) > 0 and int(row["answered_count"]) > 0:
            backlog_row = True
        if sum(int(cell["question_count"]) for cell in row_cells) != \
                int(row["question_count"]):
            identities = False
        if sum(int(cell["answered_count"]) for cell in row_cells) != \
                int(row["answered_count"]):
            identities = False
        if int(row["unanswered_count"]) != (int(row["question_count"])
                                            - int(row["answered_count"])):
            identities = False
    if rows:
        last_running = int(rows[-1]["running_question"])
        if last_running != int(envelope["question_count"]):
            identities = False
    if int(envelope["unanswered_count"]) != (int(envelope["question_count"])
                                             - int(envelope["answered_count"])):
        identities = False
    ok("AC-CQMB3",
       not driver_problems and len(forged_problems) >= 2 and identities
       and zero_row and uncategorized and backlog_row,
       "driver_problems=%d forged_problems=%d identities=%r zero_row=%r "
       "uncategorized=%r backlog_row=%r" % (len(driver_problems),
                                            len(forged_problems), identities,
                                            zero_row, uncategorized,
                                            backlog_row))

    # ---- AC-CQMB4 the page reads honestly ---------------------------------
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
    wants = sum(1 for cell in cells if int(cell["question_count"]) > 0)
    empty_ok = labels["empty"] in doc
    dash_ok = dash in doc
    probe = {key: None for key in ENVELOPE_KEYS}
    probe.update({"question_count": 0, "answered_count": 0,
                  "unanswered_count": 0, "answer_rate": None,
                  "buyer_count": 0, "seller_count": 0, "listing_count": 0,
                  "category_count": 0, "month_count": 0,
                  "active_month_count": 0, "peak_question_count": None,
                  "latest_month_question_count": 0, "months": [],
                  "disclaimer": "x"})
    empty_html = driver.build_html(probe, labels, "2026-11-25 00:00:00Z", "x")
    empty_probe = labels["empty"] in empty_html
    ok("AC-CQMB4",
       month_marked and cell_marked and not bare_none and caption
       and bars == wants and empty_ok and dash_ok and empty_probe,
       "month_marked=%r cell_marked=%r no_bare_none=%r caption=%r bars=%d/%d "
       "empty_sentence=%r dash=%r empty_probe=%r"
       % (month_marked, cell_marked, not bare_none, caption, bars, wants,
          empty_ok, dash_ok, empty_probe))

    # ---- AC-CQMB5 compliance ---------------------------------------------
    disclaimer = page.get("disclaimer") or ""
    aigc = "AIGC" in doc
    verbatim = bool(disclaimer) and disclaimer in doc
    notadvice = labels["law_notadvice"] in doc
    zero_links = "http://" not in doc and "https://" not in doc
    ok("AC-CQMB5", aigc and verbatim and notadvice and zero_links,
       "aigc=%r disclaimer_verbatim=%r notadvice=%r zero_links=%r"
       % (aigc, verbatim, notadvice, zero_links))

    # ---- AC-CQMB6 no older criterion is relaxed --------------------------
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
    face_ac = "AC-CQM1" in read(FACE_SUITE) if face_suite else False
    ok("AC-CQMB6",
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
