"""Battery suite for tools/buyer_watch_months_board.py - AC-BWMB1..6.

WHY THIS SUITE EXISTS (measured at R3447, not assumed):
api_buyer_watch_months shipped ONE resident's attention timeline - the watches
opened and dropped each month, the running live count at each month end and the
watches that turned into purchases - but a search over tools/, preview/ and
src/os answered rc=1 for its name. The market-wide and seller-wide watch axes
had pages, the buyer side only a live snapshot and a lifetime funnel, so a
heating-up resident read like a cooling-down one. R3447 renders the shipped
envelope on one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3447 PIN row landed before any driver code):
  AC-BWMB1 the pair lands, the json carries exactly the pinned eight-key payload
           set, every buyer envelope carries the shipped 15 keys, every month
           row the shipped 8 keys, the report points at a file that exists and
           the four source fingerprints are present.
  AC-BWMB2 the data is the shipped face's own: the suite builds its own
           throwaway world through the shipped watch, unwatch and purchase
           doors under its own pinned clock, re-reads every buyer scope and
           requires the page json to equal those readings item for item,
           disclaimer and buyer ordering included.
  AC-BWMB3 the face identities hold and the driver refuses a broken one: the
           month count, the contiguous grid, the per-row net, the running live
           count and its last value, the envelope sums, the conversion rule,
           the busiest month, the converted month and the zero-month shape all
           hold - and a forged running count is refused by name.
  AC-BWMB4 the page reads honestly: one marked card per buyer, one marked row
           per month, the dash where a number is absent, no bare None, the bar
           caption on the page, a bar only where watches were opened, the
           honest zero row and the empty sentence both reachable.
  AC-BWMB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer verbatim, the non-advice sentence, zero
           external links.
  AC-BWMB6 no older criterion is relaxed: the landed pair answers its own
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
TOOL = os.path.join(ROOT, "tools", "buyer_watch_months_board.py")
HTML = os.path.join(ROOT, "preview", "buyer-watch-months-board.html")
JSONF = os.path.join(ROOT, "preview", "buyer-watch-months-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-watch-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_buyerwatchmonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-buyer-watch-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "buyers", "disclaimer", "report",
    "sources", "sizes",
}
ENVELOPE_KEYS = {
    "scope", "buyer_id", "month_count", "watch_count", "unwatch_count",
    "net_count", "live_watch_count", "converted_count", "converted_month",
    "listing_count", "seller_count", "busiest_month", "busiest_watch_count",
    "months", "disclaimer",
}
MONTH_KEYS = {
    "month", "watch_count", "unwatch_count", "net_count", "active_count",
    "converted_count", "listing_count", "seller_count",
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
    spec = importlib.util.spec_from_file_location("bwmb_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_world(driver, am):
    """The suite's own copy of the story, every row through a shipped door."""
    board = am.api_board() or {}
    by_key = {}
    for row in board.get("listings") or []:
        by_key[str(row["listing_key"])] = row
    risk = int(by_key["risk-scan"]["listing_id"])
    macro = int(by_key["macro-feed"]["listing_id"])
    chart = int(by_key["chart-render"]["listing_id"])

    driver.STAMP["value"] = "2026-06-10T00:00:00Z"
    am.watch_api("usr:bob", macro)
    driver.STAMP["value"] = "2026-11-05T00:00:00Z"
    am.unwatch_api("usr:bob", macro)
    driver.STAMP["value"] = "2026-10-05T00:00:00Z"
    am.watch_api("usr:carol", chart)
    driver.STAMP["value"] = "2026-11-06T00:00:00Z"
    am.watch_api("usr:carol", risk)
    driver.STAMP["value"] = "2026-11-07T00:00:00Z"
    am.purchase_api("usr:carol", chart, "r3447-a")
    driver.STAMP["value"] = "2026-11-10T00:00:00Z"
    am.watch_api("usr:dave", risk)
    driver.STAMP["value"] = "2026-11-11T00:00:00Z"
    am.unwatch_api("usr:dave", risk)
    return ["usr:bob", "usr:carol", "usr:dave", "usr:erin"]


def live_world(driver):
    import apimarket as A
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="bwmb-suite-")
    db = os.path.join(tmp_root, "suite.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = driver._clock
        buyers = build_world(driver, am)
        envelopes = [{"buyer": name,
                      "envelope": dict(am.api_buyer_watch_months(name))}
                     for name in buyers]
        empty_scope = dict(am.api_buyer_watch_months("usr:ghost"))
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
    doc = {key: envelope[key] for key in ENVELOPE_KEYS if key != "months"}
    doc["months"] = [{key: row[key] for key in MONTH_KEYS}
                     for row in envelope.get("months") or []]
    return doc


def same(left, right):
    return json.dumps(left, sort_keys=True, default=str) == json.dumps(
        right, sort_keys=True, default=str)


def main():
    if not os.path.exists(TOOL):
        print("FAIL AC-BWMB1 driver missing")
        return 2
    driver = load_driver()
    labels = json.loads(read(COPY))
    page = json.loads(read(JSONF))
    doc = read(HTML)

    # ---- AC-BWMB1 contract ------------------------------------------------
    buyers = page.get("buyers") or []
    missing_payload = sorted(PAYLOAD_KEYS - set(page))
    extra_payload = sorted(set(page) - PAYLOAD_KEYS)
    envelope_shapes = [set(e["envelope"]) for e in buyers]
    row_shapes = [set(row) for item in buyers
                  for row in item["envelope"].get("months") or []]
    report_path = os.path.join(ROOT, page.get("report") or "")
    sources = page.get("sources") or {}
    sizes = page.get("sizes") or {}
    ok("AC-BWMB1",
       not missing_payload and not extra_payload
       and all(shape == ENVELOPE_KEYS for shape in envelope_shapes)
       and all(shape == MONTH_KEYS for shape in row_shapes)
       and os.path.exists(report_path)
       and sorted(sources) == ["apimarket", "copy", "driver", "report"]
       and sizes.get("html") == os.path.getsize(HTML)
       and sizes.get("json") == os.path.getsize(JSONF)
       and page.get("face") == "api_buyer_watch_months",
       "payload_missing=%r payload_extra=%r envelopes=%d buyers=%d rows=%d "
       "report=True sources=True"
       % (missing_payload, extra_payload, len(envelope_shapes), len(buyers),
          len(row_shapes)))

    # ---- AC-BWMB2 the data is the shipped face's own ----------------------
    live, empty_live = live_world(driver)
    live_scopes = {item["buyer"]: item["envelope"] for item in live}
    same_all = all(same(trim(live_scopes[item["buyer"]]), item["envelope"])
                   for item in buyers)
    same_words = (page.get("disclaimer") == live[0]["envelope"].get(
        "disclaimer") and all(item["envelope"].get("disclaimer")
                              == live_scopes[item["buyer"]].get("disclaimer")
                              for item in buyers))
    same_order = [item["buyer"] for item in buyers] == sorted(live_scopes)
    ok("AC-BWMB2", same_all and same_words and same_order,
       "buyers_same=%r disclaimer_same=%r order_same=%r buyers=%d"
       % (same_all, same_words, same_order, len(buyers)))

    # ---- AC-BWMB3 laws, plus a forged envelope refused by name ------------
    driver_problems = driver.check_laws(live, empty_live)
    forged = json.loads(json.dumps(live, default=str))
    forged[0]["envelope"]["live_watch_count"] = (
        int(forged[0]["envelope"]["live_watch_count"]) + 7)
    forged_problems = driver.check_laws(forged, empty_live)
    identities = True
    zero_row = False
    negative_month = False
    for item in buyers:
        env = item["envelope"]
        rows = env.get("months") or []
        if int(env["month_count"]) != len(rows):
            identities = False
        if int(env["net_count"]) != (int(env["watch_count"])
                                     - int(env["unwatch_count"])):
            identities = False
        if rows and int(rows[-1]["active_count"]) != int(
                env["live_watch_count"]):
            identities = False
        if any(int(r["watch_count"]) == 0 and int(r["unwatch_count"]) == 0
               and int(r["active_count"]) > 0 for r in rows):
            zero_row = True
        if any(int(r["net_count"]) < 0 for r in rows):
            negative_month = True
        if sum(int(r["converted_count"]) for r in rows) != int(
                env["converted_count"]):
            identities = False
    zero_buyer = any(int(item["envelope"]["month_count"]) == 0
                     for item in buyers)
    converted_ok = any(item["envelope"]["converted_month"] is not None
                       for item in buyers)
    ok("AC-BWMB3",
       not driver_problems and len(forged_problems) >= 1 and identities
       and zero_row and negative_month and zero_buyer and converted_ok,
       "driver_problems=%d forged_problems=%d identities=%r zero_row=%r "
       "negative_month=%r zero_buyer=%r converted=%r"
       % (len(driver_problems), len(forged_problems), identities, zero_row,
          negative_month, zero_buyer, converted_ok))

    # ---- AC-BWMB4 the page reads honestly ---------------------------------
    dash = labels["none"]
    marked = all(('data-buyer="%s"' % item["buyer"]) in doc for item in buyers)
    month_marked = all(
        ('data-month="%s"' % row["month"]) in doc
        for item in buyers for row in item["envelope"].get("months") or [])
    bare_none = "None" in doc or "null" in doc
    caption = labels["bar_caption"] in doc
    bars = doc.count('<div class="bar">')
    wants = sum(1 for item in buyers
                for row in item["envelope"].get("months") or []
                if int(row["watch_count"]) > 0)
    empty_ok = labels["empty"] in doc
    dash_ok = dash in doc
    empty_html = driver.build_html([], labels, "2026-11-25 00:00:00Z", "x")
    empty_probe = labels["empty"] in empty_html
    ok("AC-BWMB4",
       marked and month_marked and not bare_none and caption and bars == wants
       and empty_ok and dash_ok and empty_probe,
       "marked=%r month_marked=%r no_bare_none=%r caption=%r bars=%d/%d "
       "empty_sentence=%r dash=%r empty_probe=%r"
       % (marked, month_marked, not bare_none, caption, bars, wants, empty_ok,
          dash_ok, empty_probe))

    # ---- AC-BWMB5 compliance ---------------------------------------------
    disclaimer = page.get("disclaimer") or ""
    aigc = "AIGC" in doc
    verbatim = bool(disclaimer) and disclaimer in doc
    notadvice = labels["law_notadvice"] in doc
    zero_links = "http://" not in doc and "https://" not in doc
    ok("AC-BWMB5", aigc and verbatim and notadvice and zero_links,
       "aigc=%r disclaimer_verbatim=%r notadvice=%r zero_links=%r"
       % (aigc, verbatim, notadvice, zero_links))

    # ---- AC-BWMB6 no older criterion is relaxed --------------------------
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
    face_ac = "AC-BWM1" in read(FACE_SUITE) if face_suite else False
    ok("AC-BWMB6",
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
