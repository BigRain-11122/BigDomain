"""Battery suite for tools/market_relist_months_board.py - AC-MRMB1..6.

WHY THIS SUITE EXISTS (measured at R3452, not assumed):
api_market_relist_months shipped the market's monthly retirement and return
timeline - a delisting booked in the month of its own stamp, a re-listing in
its own month, a contiguous grid with honest zero rows, a same-month flow ratio
that answers None in a pure-return month and two monotone accumulators - but a
search over tools/, preview/ and src/os answered zero readers for its name.
R3452 renders the shipped envelope on one page; this suite grades the page, not
the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3452 PIN row landed with the driver and says so):
  AC-MRMB1 the pair lands, the json carries exactly the pinned eight-key payload
           set, the envelope the shipped 15 keys, every month row the shipped
           9 keys, the report points at a file that exists and the four source
           fingerprints are present.
  AC-MRMB2 the data is the shipped face's own: the suite builds its own
           throwaway world through the shipped delist and relist doors under its
           own pinned clock, re-reads the face and requires the page json to
           equal that reading item for item, disclaimer included.
  AC-MRMB3 the face identities hold and the driver refuses a broken one: the
           contiguous grid, the per-row net and flow-ratio laws, the running
           replay, the envelope sums, the two peaks with the earlier-month tie,
           the grid ends and the bare-world empty envelope all hold - and a
           forged month row is refused by name.
  AC-MRMB4 the page reads honestly: one marked row per month, the dash where a
           number is absent, no bare None, the bar caption on the page, a bar
           only where shelves retired, the honest zero badge, the pure-return
           badge and the empty sentence reachable.
  AC-MRMB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer verbatim, the non-advice sentence, zero
           external links and no script tags.
  AC-MRMB6 no older criterion is relaxed: the landed pair answers its own
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
TOOL = os.path.join(ROOT, "tools", "market_relist_months_board.py")
HTML = os.path.join(ROOT, "preview", "market-relist-months-board.html")
JSONF = os.path.join(ROOT, "preview", "market-relist-months-board.json")
COPY = os.path.join(ROOT, "preview", "market-relist-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_marketrelistmonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-market-relist-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "envelope", "disclaimer", "report",
    "sources", "sizes",
}
ENVELOPE_KEYS = {
    "month_count", "delist_count", "relist_count", "net_count", "relist_rate",
    "seller_count", "listing_count", "peak_delist_month",
    "peak_delist_count", "peak_relist_month", "peak_relist_count",
    "first_month", "last_month", "months", "disclaimer",
}
MONTH_KEYS = {
    "month", "delist_count", "relist_count", "net_count", "relist_rate",
    "seller_count", "listing_count", "running_delist", "running_relist",
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
    spec = importlib.util.spec_from_file_location("mrmb_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_world(am, clock):
    """The suite's own copy of the story, every row through a shipped door."""
    board = am.api_board() or {}
    ids = {}
    owners = {}
    for row in board.get("listings") or []:
        key = str(row["listing_key"])
        ids[key] = int(row["listing_id"])
        owners[key] = str(row.get("dev_account"))
    for key in ("macro-feed", "chart-render", "risk-scan"):
        if key not in ids:
            raise RuntimeError("shipped board lost %s" % key)

    clock["value"] = "2026-06-08T00:00:00Z"
    am.delist_api(owners["macro-feed"], ids["macro-feed"])
    clock["value"] = "2026-06-20T00:00:00Z"
    am.relist_api(owners["macro-feed"], ids["macro-feed"])
    clock["value"] = "2026-08-05T00:00:00Z"
    am.delist_api(owners["chart-render"], ids["chart-render"])
    clock["value"] = "2026-09-12T00:00:00Z"
    am.delist_api(owners["macro-feed"], ids["macro-feed"])
    clock["value"] = "2026-09-25T00:00:00Z"
    am.delist_api(owners["risk-scan"], ids["risk-scan"])
    clock["value"] = "2026-11-03T00:00:00Z"
    am.relist_api(owners["macro-feed"], ids["macro-feed"])
    clock["value"] = "2026-11-18T00:00:00Z"
    am.relist_api(owners["risk-scan"], ids["risk-scan"])
    return clock


def live_world():
    import apimarket as A
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="mrmb-suite-")
    db = os.path.join(tmp_root, "suite.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    clock = {"value": "2026-06-01T00:00:00Z"}
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = lambda: clock["value"]
        build_world(am, clock)
        envelope = dict(am.api_market_relist_months())
    finally:
        A._now_utc = orig_now
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    return envelope


def empty_world():
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="mrmb-bare-")
    db = os.path.join(tmp_root, "bare.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        envelope = dict(am.api_market_relist_months())
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    return envelope


def trim(envelope):
    doc = {key: envelope[key] for key in ENVELOPE_KEYS if key != "months"}
    doc["months"] = [{key: row[key] for key in MONTH_KEYS}
                     for row in envelope.get("months") or []]
    return doc


def same(left, right):
    return json.dumps(left, sort_keys=True, default=str) == json.dumps(
        right, sort_keys=True, default=str)


def main():
    if not os.path.exists(TOOL):
        print("FAIL AC-MRMB1 driver missing")
        return 2
    driver = load_driver()
    labels = json.loads(read(COPY))
    page = json.loads(read(JSONF))
    doc = read(HTML)

    envelope = page.get("envelope") or {}
    rows = envelope.get("months") or []

    # ---- AC-MRMB1 contract ------------------------------------------------
    missing_payload = sorted(PAYLOAD_KEYS - set(page))
    extra_payload = sorted(set(page) - PAYLOAD_KEYS)
    report_path = os.path.join(ROOT, page.get("report") or "")
    sources = page.get("sources") or {}
    sizes = page.get("sizes") or {}
    ok("AC-MRMB1",
       not missing_payload and not extra_payload
       and set(envelope) == ENVELOPE_KEYS
       and all(set(row) == MONTH_KEYS for row in rows)
       and os.path.exists(report_path)
       and sorted(sources) == ["apimarket", "copy", "driver", "report"]
       and sizes.get("html") == os.path.getsize(HTML)
       and sizes.get("json") == os.path.getsize(JSONF)
       and page.get("face") == "api_market_relist_months",
       "payload_missing=%r payload_extra=%r months=%d report=True "
       "sources=True" % (missing_payload, extra_payload, len(rows)))

    # ---- AC-MRMB2 the data is the shipped face's own ----------------------
    live = live_world()
    same_all = same(trim(live), envelope)
    same_words = page.get("disclaimer") == live.get("disclaimer")
    same_order = ([row["month"] for row in rows]
                  == [row["month"] for row in live.get("months") or []])
    ok("AC-MRMB2", same_all and same_words and same_order,
       "envelope_same=%r disclaimer_same=%r order_same=%r months=%d"
       % (same_all, same_words, same_order, len(rows)))

    # ---- AC-MRMB3 laws, plus a forged row refused by name ----------------
    bare = empty_world()
    driver_problems = driver.check_laws(live, bare)
    forged = json.loads(json.dumps(live, default=str))
    forged["months"][0]["relist_count"] = int(
        forged["months"][0]["relist_count"]) + 7
    forged_problems = driver.check_laws(forged, bare)
    identities = True
    zero_row = False
    pure_return = False
    net_negative = False
    for row in rows:
        delist = int(row["delist_count"])
        relist = int(row["relist_count"])
        if delist == 0 and relist == 0:
            zero_row = True
            if row["relist_rate"] is not None:
                identities = False
        if delist == 0 and relist > 0:
            pure_return = True
            if row["relist_rate"] is not None:
                identities = False
        if int(row["net_count"]) < 0:
            net_negative = True
        if int(row["net_count"]) != delist - relist:
            identities = False
        if int(row["listing_count"]) > delist + relist:
            identities = False
    if int(envelope["net_count"]) != (int(envelope["delist_count"])
                                      - int(envelope["relist_count"])):
        identities = False
    ok("AC-MRMB3",
       not driver_problems and len(forged_problems) >= 2 and identities
       and zero_row and pure_return and net_negative
       and int(bare["month_count"]) == 0,
       "driver_problems=%d forged_problems=%d identities=%r zero_row=%r "
       "pure_return=%r net_negative=%r bare_months=%d"
       % (len(driver_problems), len(forged_problems), identities, zero_row,
          pure_return, net_negative, int(bare["month_count"])))

    # ---- AC-MRMB4 the page reads honestly ---------------------------------
    dash = labels["none"]
    month_marked = all(('data-month="%s"' % row["month"]) in doc
                       for row in rows)
    bare_none = "None" in doc or "null" in doc
    caption = labels["bar_caption"] in doc
    bars = doc.count('<div class="bar">')
    wants = sum(1 for row in rows if int(row["delist_count"]) > 0)
    zero_badge = labels["badge_zero"] in doc
    pure_badge = labels["badge_pure_return"] in doc
    dash_ok = dash in doc
    empty_ok = labels["empty"] not in doc
    probe = {key: None for key in ENVELOPE_KEYS}
    probe.update({"month_count": 0, "delist_count": 0, "relist_count": 0,
                  "net_count": 0, "seller_count": 0, "listing_count": 0,
                  "months": [], "disclaimer": "x"})
    empty_html = driver.build_html(probe, labels, "2026-11-25 00:00:00Z", "x")
    empty_probe = labels["empty"] in empty_html
    ok("AC-MRMB4",
       month_marked and not bare_none and caption and bars == wants
       and zero_badge and pure_badge and dash_ok and empty_ok and empty_probe,
       "month_marked=%r no_bare_none=%r caption=%r bars=%d/%d zero_badge=%r "
       "pure_badge=%r dash=%r no_empty_on_full=%r empty_probe=%r"
       % (month_marked, not bare_none, caption, bars, wants, zero_badge,
          pure_badge, dash_ok, empty_ok, empty_probe))

    # ---- AC-MRMB5 compliance ---------------------------------------------
    disclaimer = page.get("disclaimer") or ""
    aigc = "AIGC" in doc
    verbatim = bool(disclaimer) and disclaimer in doc
    notadvice = labels["law_notadvice"] in doc
    zero_links = "http://" not in doc and "https://" not in doc
    no_script = "<script" not in doc.lower()
    ok("AC-MRMB5", aigc and verbatim and notadvice and zero_links and no_script,
       "aigc=%r disclaimer_verbatim=%r notadvice=%r zero_links=%r "
       "no_script=%r" % (aigc, verbatim, notadvice, zero_links, no_script))

    # ---- AC-MRMB6 no older criterion is relaxed --------------------------
    before = (stamp(HTML), stamp(JSONF), stamp(COPY))
    import subprocess
    proc = subprocess.run([sys.executable, TOOL, "--check"], cwd=ROOT,
                          capture_output=True, text=True)
    after = (stamp(HTML), stamp(JSONF), stamp(COPY))
    registry = read(REGISTRY)
    registered = ('"%s"' % ROW) in registry
    row_block = registry.split('"%s"' % ROW, 1)[-1][:200]
    declared = ("%d)" % DECLARED) in row_block
    face_suite = os.path.exists(FACE_SUITE)
    face_ac = "AC-MRM1" in read(FACE_SUITE) if face_suite else False
    ok("AC-MRMB6",
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
