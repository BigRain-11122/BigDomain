"""Battery suite for tools/market_provider_months_board.py - AC-PMB1..6.

WHY THIS SUITE EXISTS (measured at R3453, not assumed):
api_market_provider_months shipped the market's monthly real-name timeline - a
registration booked in its own registered month, a revision in its own revised
month, a contiguous grid with honest zero rows, a redeclaration rate that
answers None in a month with no identity event, the distinct-account split and
one monotone revision accumulator - but a search over tools/, preview/ and
src/os answered zero readers for its name. R3453 renders the shipped envelope on
one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3453 PIN row landed with the driver and says so):
  AC-PMB1 the pair lands, the json carries exactly the pinned eight-key payload
          set, the envelope the shipped 14 keys, every month row the shipped
          8 keys, the report points at a file that exists and the four source
          fingerprints are present.
  AC-PMB2 the data is the shipped face's own: the suite builds its own
          throwaway world through the shipped register_provider and
          revise_provider doors under its own pinned clock, re-reads the face
          and requires the page json to equal that reading item for item,
          disclaimer included.
  AC-PMB3 the face identities hold and the driver refuses a broken one: the
          contiguous grid, the per-row event/rate laws, the distinct-account
          bound, the running replay, the envelope sums and average, the peak
          with the earlier-month tie, the grid ends, the latest event stamp and
          the bare-world empty envelope all hold - and a forged month row is
          refused by name.
  AC-PMB4 the page reads honestly: one marked row per month, the dash where a
          number is absent, no bare None, the bar caption on the page, a bar
          only where a revision landed, all four state badges reachable, and
          the empty sentence reachable in an in-memory probe only.
  AC-PMB5 the standing compliance faces ride along: the AIGC label, the face's
          own disclaimer verbatim, the non-advice sentence, zero external links
          and no script tags.
  AC-PMB6 no older criterion is relaxed: the landed pair answers its own
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
TOOL = os.path.join(ROOT, "tools", "market_provider_months_board.py")
HTML = os.path.join(ROOT, "preview", "market-provider-months-board.html")
JSONF = os.path.join(ROOT, "preview", "market-provider-months-board.json")
COPY = os.path.join(ROOT, "preview", "market-provider-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_marketprovidermonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-market-provider-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "envelope", "disclaimer", "report",
    "sources", "sizes",
}
ENVELOPE_KEYS = {
    "month_count", "registration_count", "revision_count", "event_count",
    "seller_count", "redeclared_seller_count",
    "avg_revisions_per_redeclared_seller", "peak_revision_month",
    "peak_revision_count", "first_month", "last_month", "latest_event_utc",
    "months", "disclaimer",
}
MONTH_KEYS = {
    "month", "registration_count", "revision_count", "event_count",
    "seller_count", "redeclared_seller_count", "redeclaration_rate",
    "running_revision",
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
    spec = importlib.util.spec_from_file_location("pmb_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_world(am, clock):
    """The suite's own copy of the story, every row through a shipped door."""
    clock["value"] = "2026-06-05T00:00:00Z"
    am.register_provider("usr:dana", "DANA Studio", "91350100MA1111111A")
    clock["value"] = "2026-07-10T00:00:00Z"
    am.register_provider("usr:frank", "Frank Works", "91350100MA2222222B")
    clock["value"] = "2026-07-18T00:00:00Z"
    am.revise_provider("usr:dana", provider_name="DANA Studio East")
    clock["value"] = "2026-07-26T00:00:00Z"
    am.revise_provider("usr:frank", provider_name="Frank Works 2")
    clock["value"] = "2026-08-09T00:00:00Z"
    am.revise_provider("usr:dana", provider_name="DANA Studio East 2")
    clock["value"] = "2026-09-04T00:00:00Z"
    am.revise_provider("usr:frank", provider_name="Frank Works 3")
    clock["value"] = "2026-09-15T00:00:00Z"
    am.revise_provider("usr:frank", provider_name="Frank Works 4")
    clock["value"] = "2026-09-27T00:00:00Z"
    am.revise_provider("usr:frank", credit_code="91350100MA2222222C")
    clock["value"] = "2026-11-06T00:00:00Z"
    am.revise_provider("usr:dana", credit_code="91350100MA1111111C")
    clock["value"] = "2026-11-21T00:00:00Z"
    am.revise_provider("usr:frank", provider_name="Frank Works 5")
    return clock


def live_world():
    import apimarket as A
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="pmb-suite-")
    db = os.path.join(tmp_root, "suite.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    clock = {"value": "2026-06-01T00:00:00Z"}
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = lambda: clock["value"]
        build_world(am, clock)
        envelope = dict(am.api_market_provider_months())
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
    tmp_root = tempfile.mkdtemp(prefix="pmb-bare-")
    db = os.path.join(tmp_root, "bare.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        envelope = dict(am.api_market_provider_months())
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
        print("FAIL AC-PMB1 driver missing")
        return 2
    driver = load_driver()
    labels = json.loads(read(COPY))
    page = json.loads(read(JSONF))
    doc = read(HTML)

    envelope = page.get("envelope") or {}
    rows = envelope.get("months") or []

    # ---- AC-PMB1 contract -------------------------------------------------
    missing_payload = sorted(PAYLOAD_KEYS - set(page))
    extra_payload = sorted(set(page) - PAYLOAD_KEYS)
    report_path = os.path.join(ROOT, page.get("report") or "")
    sources = page.get("sources") or {}
    sizes = page.get("sizes") or {}
    ok("AC-PMB1",
       not missing_payload and not extra_payload
       and set(envelope) == ENVELOPE_KEYS
       and all(set(row) == MONTH_KEYS for row in rows)
       and os.path.exists(report_path)
       and sorted(sources) == ["apimarket", "copy", "driver", "report"]
       and sizes.get("html") == os.path.getsize(HTML)
       and sizes.get("json") == os.path.getsize(JSONF)
       and page.get("face") == "api_market_provider_months",
       "payload_missing=%r payload_extra=%r months=%d report=True "
       "sources=True" % (missing_payload, extra_payload, len(rows)))

    # ---- AC-PMB2 the data is the shipped face's own -----------------------
    live = live_world()
    same_all = same(trim(live), envelope)
    same_words = page.get("disclaimer") == live.get("disclaimer")
    same_order = ([row["month"] for row in rows]
                  == [row["month"] for row in live.get("months") or []])
    ok("AC-PMB2", same_all and same_words and same_order,
       "envelope_same=%r disclaimer_same=%r order_same=%r months=%d"
       % (same_all, same_words, same_order, len(rows)))

    # ---- AC-PMB3 laws, plus a forged row refused by name ------------------
    bare = empty_world()
    driver_problems = driver.check_laws(live, bare)
    forged = json.loads(json.dumps(live, default=str))
    forged["months"][0]["revision_count"] = int(
        forged["months"][0]["revision_count"]) + 7
    forged_problems = driver.check_laws(forged, bare)
    identities = True
    zero_row = False
    mixed_row = False
    distinct_row = False
    for row in rows:
        reg = int(row["registration_count"])
        rev = int(row["revision_count"])
        events = int(row["event_count"])
        if reg == 0 and rev == 0:
            zero_row = True
            if row["redeclaration_rate"] is not None:
                identities = False
        if reg > 0 and rev > 0:
            mixed_row = True
        if rev > int(row["seller_count"]):
            distinct_row = True
        if events != reg + rev:
            identities = False
        if int(row["seller_count"]) > events:
            identities = False
        if int(row["redeclared_seller_count"]) > int(row["seller_count"]):
            identities = False
    if int(envelope["event_count"]) != (int(envelope["registration_count"])
                                       + int(envelope["revision_count"])):
        identities = False
    ok("AC-PMB3",
       not driver_problems and len(forged_problems) >= 2 and identities
       and zero_row and mixed_row and distinct_row
       and int(bare["month_count"]) == 0,
       "driver_problems=%d forged_problems=%d identities=%r zero_row=%r "
       "mixed_row=%r distinct_row=%r bare_months=%d"
       % (len(driver_problems), len(forged_problems), identities, zero_row,
          mixed_row, distinct_row, int(bare["month_count"])))

    # ---- AC-PMB4 the page reads honestly ----------------------------------
    dash = labels["none"]
    month_marked = all(('data-month="%s"' % row["month"]) in doc
                       for row in rows)
    bare_none = "None" in doc or "null" in doc
    caption = labels["bar_caption"] in doc
    bars = doc.count('<div class="bar">')
    wants = sum(1 for row in rows if int(row["revision_count"]) > 0)
    badges = all(labels[key] in doc
                 for key in ("badge_zero", "badge_register",
                             "badge_revision", "badge_mixed"))
    dash_ok = dash in doc
    empty_ok = labels["empty"] not in doc
    probe = {key: None for key in ENVELOPE_KEYS}
    probe.update({"month_count": 0, "registration_count": 0,
                  "revision_count": 0, "event_count": 0, "seller_count": 0,
                  "redeclared_seller_count": 0,
                  "avg_revisions_per_redeclared_seller": None,
                  "months": [], "disclaimer": "x"})
    empty_html = driver.build_html(probe, labels, "2026-11-25 00:00:00Z", "x")
    empty_probe = labels["empty"] in empty_html
    ok("AC-PMB4",
       month_marked and not bare_none and caption and bars == wants
       and badges and dash_ok and empty_ok and empty_probe,
       "month_marked=%r no_bare_none=%r caption=%r bars=%d/%d badges=%r "
       "dash=%r no_empty_on_full=%r empty_probe=%r"
       % (month_marked, not bare_none, caption, bars, wants, badges,
          dash_ok, empty_ok, empty_probe))

    # ---- AC-PMB5 compliance ----------------------------------------------
    disclaimer = page.get("disclaimer") or ""
    aigc = "AIGC" in doc
    verbatim = bool(disclaimer) and disclaimer in doc
    notadvice = labels["law_notadvice"] in doc
    zero_links = "http://" not in doc and "https://" not in doc
    no_script = "<script" not in doc.lower()
    ok("AC-PMB5", aigc and verbatim and notadvice and zero_links and no_script,
       "aigc=%r disclaimer_verbatim=%r notadvice=%r zero_links=%r "
       "no_script=%r" % (aigc, verbatim, notadvice, zero_links, no_script))

    # ---- AC-PMB6 no older criterion is relaxed ---------------------------
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
    face_ac = "AC-PIM1" in read(FACE_SUITE) if face_suite else False
    ok("AC-PMB6",
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
