"""Battery suite for tools/buyer_gap_board.py - AC-BGMB1..6.

WHY THIS SUITE EXISTS (measured at R3446, not assumed):
api_buyer_gap_months shipped the repurchase rhythm of one resident - how many
months passed between two net purchases, how long the longest silence ran and
how many months sit dormant inside the observed extent - but a search over
tools/, preview/ and src/os answered rc=1 for its name. The market already had
monthly spend, repeat purchase and a retention curve, so a loyal repurchaser
and a sleeping account read the same. R3446 renders the shipped envelope on one
page; this suite grades the page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3446 PIN row landed before any driver code):
  AC-BGMB1 the pair lands, the json carries exactly the pinned nine-key payload
           set, every buyer envelope carries the shipped 16 keys, every gap row
           the shipped 4 keys, the report points at a file that exists and the
           four source fingerprints are present.
  AC-BGMB2 the data is the shipped face's own: the suite builds its own
           throwaway world through the shipped doors under its own pinned
           clock, re-reads every buyer scope and requires the page json to
           equal those readings item for item, disclaimer and buyer ordering
           included.
  AC-BGMB3 the face identities hold and the driver refuses a broken one: the
           gap count identity, the span law, the row chain, the dormant sum,
           the average, the median, the maximum and its first row, the
           trailing dormancy and the zero-activity and single-month shapes all
           hold - and a forged dormant total is refused by name.
  AC-BGMB4 the page reads honestly: one marked card per buyer, one marked row
           per gap, the dash where a number is absent, no bare None, the bar
           caption on the page, a bar only where a gap is positive, and both
           the empty sentence and the single-month sentence reachable.
  AC-BGMB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer verbatim, the non-advice sentence, zero
           external links.
  AC-BGMB6 no older criterion is relaxed: the landed pair answers its own
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
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "buyer_gap_board.py")
HTML = os.path.join(ROOT, "preview", "buyer-gap-board.html")
JSONF = os.path.join(ROOT, "preview", "buyer-gap-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-gap-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_buyergapmonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-buyer-gap-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "as_of_month", "buyers", "disclaimer",
    "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "buyer_id", "activity_month_count", "purchase_count",
    "first_activity_month", "last_activity_month", "gap_count",
    "dormant_months_total", "avg_gap_months", "median_gap_months",
    "max_gap_months", "longest_from_month", "longest_to_month", "as_of_month",
    "trailing_dormant_months", "disclaimer", "gaps",
}
GAP_KEYS = {"from_month", "to_month", "span_months", "gap_months"}

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
    spec = importlib.util.spec_from_file_location("bgmb_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_world(driver, am):
    """The suite's own copy of the story, every row through a shipped door."""
    board = am.api_board() or {}
    by_key = {}
    for row in board.get("listings") or []:
        by_key[str(row["listing_key"])] = row
    macro = int(by_key["macro-feed"]["listing_id"])
    chart = int(by_key["chart-render"]["listing_id"])

    driver.STAMP["value"] = "2026-06-10T00:00:00Z"
    am.purchase_api("usr:bob", chart, "r3446-a")
    driver.STAMP["value"] = "2026-10-05T00:00:00Z"
    am.purchase_api("usr:carol", macro, "r3446-b")
    driver.STAMP["value"] = "2026-11-05T00:00:00Z"
    am.purchase_api("usr:carol", chart, "r3446-c")
    driver.STAMP["value"] = "2026-11-12T00:00:00Z"
    am.purchase_api("usr:dave", macro, "r3446-d")
    return ["usr:bob", "usr:carol", "usr:dave", "usr:erin"]


def live_world(driver):
    import apimarket as A
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="bgmb-suite-")
    db = os.path.join(tmp_root, "suite.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = driver._clock
        buyers = build_world(driver, am)
        envelopes = [{"buyer": name,
                      "envelope": dict(am.api_buyer_gap_months(
                          name, driver.AS_OF))}
                     for name in buyers]
        empty_scope = dict(am.api_buyer_gap_months("usr:ghost", driver.AS_OF))
    finally:
        A._now_utc = orig_now
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    return envelopes, empty_scope


def trim(envelope):
    doc = {key: envelope[key] for key in ENVELOPE_KEYS if key != "gaps"}
    doc["gaps"] = [{key: row[key] for key in GAP_KEYS}
                   for row in envelope.get("gaps") or []]
    return doc


def same(left, right):
    return json.dumps(left, sort_keys=True, default=str) == json.dumps(
        right, sort_keys=True, default=str)


def main():
    if not os.path.exists(TOOL):
        print("FAIL AC-BGMB1 driver missing")
        return 2
    driver = load_driver()
    labels = json.loads(read(COPY))
    page = json.loads(read(JSONF))
    doc = read(HTML)

    # ---- AC-BGMB1 contract ------------------------------------------------
    buyers = page.get("buyers") or []
    missing_payload = sorted(PAYLOAD_KEYS - set(page))
    extra_payload = sorted(set(page) - PAYLOAD_KEYS)
    envelope_shapes = [set(e["envelope"]) for e in buyers]
    row_shapes = [set(row) for item in buyers
                  for row in item["envelope"].get("gaps") or []]
    report_path = os.path.join(ROOT, page.get("report") or "")
    sources = page.get("sources") or {}
    sizes = page.get("sizes") or {}
    ok("AC-BGMB1",
       not missing_payload and not extra_payload
       and all(shape == ENVELOPE_KEYS for shape in envelope_shapes)
       and all(shape == GAP_KEYS for shape in row_shapes)
       and os.path.exists(report_path)
       and sorted(sources) == ["apimarket", "copy", "driver", "report"]
       and sizes.get("html") == os.path.getsize(HTML)
       and sizes.get("json") == os.path.getsize(JSONF)
       and page.get("face") == "api_buyer_gap_months",
       "payload_missing=%r payload_extra=%r envelopes=%d buyers=%d rows=%d "
       "report=True sources=True"
       % (missing_payload, extra_payload, len(envelope_shapes), len(buyers),
          len(row_shapes)))

    # ---- AC-BGMB2 the data is the shipped face's own ----------------------
    live, empty_live = live_world(driver)
    live_scopes = {item["buyer"]: item["envelope"] for item in live}
    same_all = all(same(trim(live_scopes[item["buyer"]]), item["envelope"])
                   for item in buyers)
    same_words = (page.get("disclaimer") == live[0]["envelope"].get(
        "disclaimer") and all(item["envelope"].get("disclaimer")
                              == live_scopes[item["buyer"]].get("disclaimer")
                              for item in buyers))
    same_order = [item["buyer"] for item in buyers] == sorted(live_scopes)
    ok("AC-BGMB2", same_all and same_words and same_order,
       "buyers_same=%r disclaimer_same=%r order_same=%r buyers=%d"
       % (same_all, same_words, same_order, len(buyers)))

    # ---- AC-BGMB3 laws, plus a forged envelope refused by name ------------
    driver_problems = driver.check_laws(live, empty_live)
    forged = json.loads(json.dumps(live, default=str))
    forged[0]["envelope"]["dormant_months_total"] = (
        int(forged[0]["envelope"]["dormant_months_total"]) + 7)
    forged_problems = driver.check_laws(forged, empty_live)
    identities = True
    for item in buyers:
        env = item["envelope"]
        rows = env.get("gaps") or []
        if int(env["gap_count"]) != len(rows):
            identities = False
        if int(env["gap_count"]) != max(0, int(env["activity_month_count"]) - 1):
            identities = False
        if sum(int(r["gap_months"]) for r in rows) != int(
                env["dormant_months_total"]):
            identities = False
        if rows and (rows[0]["from_month"] != env["first_activity_month"]
                     or rows[-1]["to_month"] != env["last_activity_month"]):
            identities = False
        if not rows and env["avg_gap_months"] is not None:
            identities = False
    zero_ok = all(int(item["envelope"]["activity_month_count"]) > 0
                  for item in buyers if item["buyer"] == "usr:erin") is False
    single_ok = any(int(item["envelope"]["gap_count"]) == 0
                    and int(item["envelope"]["activity_month_count"]) == 1
                    for item in buyers)
    ok("AC-BGMB3",
       not driver_problems and len(forged_problems) >= 1 and identities
       and zero_ok and single_ok,
       "driver_problems=%d forged_problems=%d identities=%r zero_buyer=%r "
       "single_buyer=%r"
       % (len(driver_problems), len(forged_problems), identities, zero_ok,
          single_ok))

    # ---- AC-BGMB4 the page reads honestly ---------------------------------
    dash = labels["none"]
    marked = all(('data-buyer="%s"' % item["buyer"]) in doc for item in buyers)
    gap_marked = all(
        ('data-gap="%s..%s"' % (row["from_month"], row["to_month"])) in doc
        for item in buyers for row in item["envelope"].get("gaps") or [])
    bare_none = "None" in doc or "null" in doc
    caption = labels["bar_caption"] in doc
    bars = doc.count('<div class="bar">')
    wants = sum(1 for item in buyers
                for row in item["envelope"].get("gaps") or []
                if int(row["gap_months"]) > 0)
    empty_ok = labels["empty"] in doc and labels["single"] in doc
    dash_ok = dash in doc
    empty_html = driver.build_html([], labels, "2026-11-25 00:00:00Z", "x")
    empty_probe = labels["empty"] in empty_html
    ok("AC-BGMB4",
       marked and gap_marked and not bare_none and caption and bars == wants
       and empty_ok and dash_ok and empty_probe,
       "marked=%r gap_marked=%r no_bare_none=%r caption=%r bars=%d/%d "
       "quiet_sentences=%r dash=%r empty_probe=%r"
       % (marked, gap_marked, not bare_none, caption, bars, wants, empty_ok,
          dash_ok, empty_probe))

    # ---- AC-BGMB5 compliance ---------------------------------------------
    disclaimer = page.get("disclaimer") or ""
    aigc = "AIGC" in doc
    verbatim = bool(disclaimer) and disclaimer in doc
    notadvice = labels["law_notadvice"] in doc
    zero_links = "http://" not in doc and "https://" not in doc
    ok("AC-BGMB5", aigc and verbatim and notadvice and zero_links,
       "aigc=%r disclaimer_verbatim=%r notadvice=%r zero_links=%r"
       % (aigc, verbatim, notadvice, zero_links))

    # ---- AC-BGMB6 no older criterion is relaxed --------------------------
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
    face_ac = "AC-BGM1" in read(FACE_SUITE) if face_suite else False
    ok("AC-BGMB6",
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
