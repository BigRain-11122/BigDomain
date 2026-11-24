"""Battery suite for tools/seller_cohort_board.py - criteria AC-SCB1..6.

WHY THIS SUITE EXISTS (measured at R3414, not assumed):
api_market_seller_cohort shipped with its own AC-MSC1..8 criteria
(src/sandbox/ledger/test_apimarket_sellercohort.py) but a git grep over
tools/ and preview/ answered rc=1 with zero hits, so the monthly question
"of the sellers putting supply on the shelf this month, how many are first
timers and how many came back" could not be opened by anyone. R3414 renders
the seller cohort onto one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3414 PIN
BEFORE the driver existed):
  AC-SCB1 the page and its json land, the json carries exactly the pinned
           payload key set including the sizes and sources blocks, the nested
           cohort carries the shipped twelve-key envelope, every month row
           carries the shipped nine-key row set, month_count equals the row
           count, and the report points at a file that exists.
  AC-SCB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, reads api_market_seller_cohort() over it, and
           requires the page json's cohort to equal that reading item for
           item plus the disclaimer verbatim - no typed fixture, no
           synthesized month.
  AC-SCB3 the face's identities hold: seller and event partitions, the
           relisting subset bound, the per-seller average, the envelope sums
           of listing, relisting and returning events, month ordering and
           shape, first/last month, and a None repeat rate on an empty world.
  AC-SCB4 the page reads honestly: one data row per month, the event,
           repeat and no-recompute laws are on the page, a zero-returning
           world prints an explicit sentence (measured on the landed page),
           an empty envelope handed to the driver's own renderer prints an
           explicit empty line (in-memory probe only), and no bare None
           reaches the page.
  AC-SCB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-SCB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-MSC arms.

Read-only over the repository: the provenance world is built in a temp dir and
the empty probe renders in memory, never inside preview/.

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
TOOL = os.path.join(ROOT, "tools", "seller_cohort_board.py")
HTML = os.path.join(ROOT, "preview", "seller-cohort.html")
JSONF = os.path.join(ROOT, "preview", "seller-cohort.json")
COPY = os.path.join(ROOT, "preview", "seller-cohort-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_sellercohort.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-cohort-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "month_count", "cohort",
    "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "month_count", "seller_count", "listing_event_count",
    "relisting_event_count", "relisting_seller_count",
    "repeat_seller_count", "repeat_rate", "returning_event_count",
    "first_month", "last_month", "disclaimer", "months",
}
ROW_KEYS = {
    "month", "seller_count", "new_seller_count", "returning_seller_count",
    "listing_event_count", "relisting_event_count", "new_event_count",
    "returning_event_count", "avg_events_per_seller",
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


def run_tool(args, cwd=ROOT):
    proc = subprocess.run(
        [sys.executable, TOOL] + args, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def live_cohort():
    """The shipped face's own reading over the suite's throwaway demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="scb-suite-")
    db = os.path.join(tmp_root, "scb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        return dict(am.api_market_seller_cohort())
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("scb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_problems(envelope):
    rows = envelope.get("months") or []
    problems = []
    if int(envelope.get("month_count", -1)) != len(rows):
        problems.append("month_count")
    for key in ("listing_event_count", "relisting_event_count",
                "returning_event_count"):
        if int(envelope.get(key, -1)) != sum(int(row[key]) for row in rows):
            problems.append(key)
    months = [str(row["month"]) for row in rows]
    if months != sorted(months):
        problems.append("order")
    if any(not re.match(r"^\d{4}-\d{2}$", name) for name in months):
        problems.append("shape")
    if envelope.get("first_month") != (months[0] if months else None):
        problems.append("first_month")
    if envelope.get("last_month") != (months[-1] if months else None):
        problems.append("last_month")
    sellers = int(envelope.get("seller_count", -1))
    repeat = int(envelope.get("repeat_seller_count", -1))
    if repeat > sellers:
        problems.append("repeat > seller_count")
    if int(envelope.get("relisting_seller_count", -1)) > sellers:
        problems.append("relisting_sellers > seller_count")
    rate = envelope.get("repeat_rate")
    if sellers == 0:
        if rate is not None:
            problems.append("rate on empty world")
    else:
        want = repeat / float(sellers)
        if rate is None or abs(float(rate) - want) > 1e-9:
            problems.append("rate")
    for row in rows:
        tag = str(row["month"])
        count = int(row["seller_count"])
        events = int(row["listing_event_count"])
        if count < 1:
            problems.append("%s zero sellers" % tag)
        if events < 1:
            problems.append("%s zero events" % tag)
        if count != (int(row["new_seller_count"])
                     + int(row["returning_seller_count"])):
            problems.append("%s seller partition" % tag)
        if events != (int(row["new_event_count"])
                      + int(row["returning_event_count"])):
            problems.append("%s event partition" % tag)
        if int(row["relisting_event_count"]) > events:
            problems.append("%s relist subset" % tag)
        for key in ("seller_count", "new_seller_count",
                    "returning_seller_count", "listing_event_count",
                    "relisting_event_count", "new_event_count",
                    "returning_event_count"):
            if int(row[key]) < 0:
                problems.append("%s negative %s" % (tag, key))
        avg = row["avg_events_per_seller"]
        want_avg = events / float(count)
        if avg is None or abs(float(avg) - want_avg) > 1e-9:
            problems.append("%s avg" % tag)
    return problems


def probe_empty(disclaimer):
    """An empty cohort: never landed, only handed to the renderer."""
    return {
        "month_count": 0, "seller_count": 0, "listing_event_count": 0,
        "relisting_event_count": 0, "relisting_seller_count": 0,
        "repeat_seller_count": 0, "repeat_rate": None,
        "returning_event_count": 0, "first_month": None,
        "last_month": None, "disclaimer": disclaimer, "months": [],
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    cohort = doc.get("cohort") or {}
    rows = cohort.get("months") or []

    # ---- AC-SCB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelope_ok = set(cohort.keys()) == ENVELOPE_KEYS
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in rows)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    ok("AC-SCB1", landed and keys == PAYLOAD_KEYS and envelope_ok
       and rows_ok and bool(rows)
       and int(doc.get("month_count", -1)) == len(rows)
       and int(cohort.get("month_count", -1)) == len(rows) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelope=%s rows=%s "
       "months=%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelope_ok, rows_ok, len(rows),
          report_ok))

    # ---- AC-SCB2: every printed number is the shipped face's own.
    live = live_cohort()
    same = (json.dumps(cohort, sort_keys=True)
            == json.dumps(live, sort_keys=True))
    disc_same = (doc.get("disclaimer") == live.get("disclaimer"))
    ok("AC-SCB2", same and disc_same and bool(rows),
       "identical=%s disclaimer_same=%s months=%d sellers=%s events=%s"
       % (same, disc_same, len(rows), cohort.get("seller_count"),
          cohort.get("listing_event_count")))

    # ---- AC-SCB3: the face's identities hold on this envelope.
    problems = identity_problems(cohort) if rows else ["no rows"]
    ok("AC-SCB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-SCB4: honest page face, explicit zero-returning sentence.
    page_rows = page.count('<tr class="month"')
    sections_ok = all(('data-month="%s"' % row["month"]) in page
                      for row in rows)
    stand_in = ">None<" in page
    law_new = labels.get("law_new", "") in page
    law_event = labels.get("law_event", "") in page
    law_repeat = labels.get("law_repeat", "") in page
    law_recompute = labels.get("law_norecompute", "") in page
    repeat_zero = int(cohort.get("repeat_seller_count", -1)) == 0
    zero_sentence = labels.get("repeat_none", "") in page
    zero_ok = zero_sentence if repeat_zero else True
    empty_probe_ok = False
    try:
        driver = load_driver()
        disclaimer = doc.get("disclaimer") or ""
        probe_html = driver.build_html(probe_empty(disclaimer), labels,
                                       "2026-01-01 00:00:00Z", disclaimer)
        empty_probe_ok = (labels.get("empty", "") in probe_html
                          and '<tr class="month"' not in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-SCB4", page_rows == len(rows) and sections_ok and not stand_in
       and law_new and law_event and law_repeat and law_recompute and zero_ok
       and empty_probe_ok,
       "rows=%d/%d sections=%s laws=%s/%s/%s/%s zero_sentence=%s "
       "empty_probe=%s stand_in_none=%s"
       % (page_rows, len(rows), sections_ok, law_new, law_event, law_repeat,
          law_recompute, zero_ok, empty_probe_ok, stand_in))

    # ---- AC-SCB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-SCB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-SCB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-MSC" in read(FACE_SUITE)
    ok("AC-SCB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
