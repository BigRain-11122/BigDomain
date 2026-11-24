"""Battery suite for tools/refund_latency_board.py - AC-RFLB1..6.

WHY THIS SUITE EXISTS (measured at R3440, not assumed):
api_refund_latency shipped as the market refund latency distribution - two stored
stamps of the same purchase, a six-band partition, five aggregates over refunded
rows only, two named crossings and a contiguous monthly leg - with its own
AC-RFLT1..8 suite on disk, but no page under tools/ or preview/ ever called it.
The refund family answered money and headcount four ways and time zero ways. R3440
renders the shipped envelope on one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3440 PIN
BEFORE the driver existed):
  AC-RFLB1 the pair lands, the json carries exactly the pinned 12-key payload
           set, the envelope carries the shipped 15 keys, every band row the
           shipped 5 keys, every month row the shipped 5 keys, both counters
           equal their row counts, and the report points at a file that exists.
  AC-RFLB2 the data is the shipped face's own: the suite builds its own throwaway
           demo world and requires the page json to equal a fresh
           api_refund_latency() reading item for item, disclaimer included, band
           order and month order included.
  AC-RFLB3 the face's identities hold: the refund count splits against purchases
           and unrefunded, the bands sum to it and form one half-open partition
           from zero with no upper bound on the last band, the rate is the face's
           own ratio, the four aggregates never invert, the crossings stay inside
           the refund count, and the months are contiguous with honest empty rows.
  AC-RFLB4 the page reads honestly: one marked row per band, one per month, the
           no-upper-bound label instead of a bare null, the keys and the bar
           caption on the page, no bare None, and a zero-refund envelope handed to
           the driver's own renderer prints the explicit empty sentence with the
           dash rather than a zero second (in-memory probe only).
  AC-RFLB5 the standing compliance faces ride along: the AIGC label, the face's
           own disclaimer verbatim, the non-advice sentence, zero external links.
  AC-RFLB6 no older criterion is relaxed: the landed pair answers its own --check,
           --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and the
           face is still exercised by its shipped suite on disk.

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
TOOL = os.path.join(ROOT, "tools", "refund_latency_board.py")
HTML = os.path.join(ROOT, "preview", "refund-latency-board.html")
JSONF = os.path.join(ROOT, "preview", "refund-latency-board.json")
COPY = os.path.join(ROOT, "preview", "refund-latency-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_refundlatency.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-refund-latency-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "band_count", "month_count", "envelope",
    "bands", "months", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "purchase_count", "refund_count", "unrefunded_count", "refund_rate",
    "avg_refund_seconds", "median_refund_seconds", "p90_refund_seconds",
    "fastest_seconds", "slowest_seconds", "same_day_count", "over_week_count",
    "month_count", "bands", "months", "disclaimer",
}
BAND_KEYS = {"band", "lower_seconds", "upper_seconds", "refund_count",
             "refunded"}
MONTH_KEYS = {"month", "refund_count", "median_refund_seconds",
              "avg_refund_seconds", "slowest_seconds"}

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
    tmp_root = tempfile.mkdtemp(prefix="rflb-suite-")
    db = os.path.join(tmp_root, "rflb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        return dict(am.api_refund_latency())
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("rflb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_problems(envelope, bands, months):
    problems = []
    purchases = int(envelope["purchase_count"])
    refunds = int(envelope["refund_count"])
    if refunds != purchases - int(envelope["unrefunded_count"]):
        problems.append("refund/unrefunded split")
    if sum(int(row["refund_count"]) for row in bands) != refunds:
        problems.append("band sum")
    if sum(int(row["refund_count"]) for row in months) != refunds:
        problems.append("month sum")
    if bands and int(bands[0]["lower_seconds"]) != 0:
        problems.append("band origin")
    if bands and bands[-1]["upper_seconds"] is not None:
        problems.append("open last band")
    labels = [row["band"] for row in bands]
    if len(labels) != len(set(labels)):
        problems.append("duplicate band label")
    for row in months:
        if int(row["refund_count"]) == 0 and any(
                row[key] is not None for key in
                ("median_refund_seconds", "avg_refund_seconds",
                 "slowest_seconds")):
            problems.append("empty month statistics")
    seen = [row["month"] for row in months]
    if seen != sorted(seen):
        problems.append("months not ascending")
    return problems


def probe_empty():
    return {
        "purchase_count": 1, "refund_count": 0, "unrefunded_count": 1,
        "refund_rate": 0.0, "avg_refund_seconds": None,
        "median_refund_seconds": None, "p90_refund_seconds": None,
        "fastest_seconds": None, "slowest_seconds": None,
        "same_day_count": 0, "over_week_count": 0, "month_count": 1,
        "bands": [{"band": "0-1h", "lower_seconds": 0,
                   "upper_seconds": 3600, "refund_count": 0, "refunded": 0},
                  {"band": "7d+", "lower_seconds": 604800,
                   "upper_seconds": None, "refund_count": 0, "refunded": 0}],
        "months": [{"month": "2026-01", "refund_count": 0,
                    "median_refund_seconds": None,
                    "avg_refund_seconds": None, "slowest_seconds": None}],
        "disclaimer": "sandbox stand-in disclaimer",
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    envelope = doc.get("envelope") or {}
    bands = doc.get("bands") or []
    months = doc.get("months") or []

    # ---- AC-RFLB1: the pair landed with exactly the pinned key sets.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    env_ok = set(envelope.keys()) == ENVELOPE_KEYS
    bands_ok = all(set(row.keys()) == BAND_KEYS for row in bands)
    months_ok = all(set(row.keys()) == MONTH_KEYS for row in months)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-RFLB1", landed and keys == PAYLOAD_KEYS and env_ok and bands_ok
       and months_ok and int(doc.get("band_count", -1)) == len(bands)
       and int(doc.get("month_count", -1)) == len(months) and report_ok
       and sources_ok,
       "landed=%s keys=%d missing=%s extra=%s env=%s bands=%s months=%s "
       "count=%d/%d report=%s sources=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), env_ok, bands_ok, months_ok,
          len(bands), len(months), report_ok, sources_ok))

    # ---- AC-RFLB2: every printed value is the shipped face's own.
    live = live_world()
    bands_same = json.dumps(bands, sort_keys=True) == json.dumps(
        [{key: row[key] for key in BAND_KEYS}
         for row in live.get("bands") or []], sort_keys=True)
    months_same = json.dumps(months, sort_keys=True) == json.dumps(
        [{key: row[key] for key in MONTH_KEYS}
         for row in live.get("months") or []], sort_keys=True)
    scalars = [key for key in ENVELOPE_KEYS
               if key not in ("bands", "months", "disclaimer")]
    scalars_same = all(envelope.get(key) == live.get(key) for key in scalars)
    disc_same = doc.get("disclaimer") == live.get("disclaimer")
    ok("AC-RFLB2", bands_same and months_same and scalars_same and disc_same
       and bool(bands),
       "bands_same=%s months_same=%s scalars_same=%s disclaimer_same=%s "
       "bands=%d months=%d"
       % (bands_same, months_same, scalars_same, disc_same, len(bands),
          len(months)))

    # ---- AC-RFLB3: the face's identities and this page's own laws hold.
    driver = load_driver()
    problems = identity_problems(envelope, bands, months) if envelope else \
        ["no envelope"]
    law_problems = driver.check_laws(envelope if envelope else live)
    ok("AC-RFLB3", not problems and not law_problems,
       "problems=%s driver_laws=%s"
       % (problems[:4] if problems else [], law_problems[:3]
          if law_problems else []))

    # ---- AC-RFLB4: honest page face, labels, dashes, empty probe.
    dash = labels.get("none", "-")
    marked_bands = all(('data-band="%s"' % row["band"]) in page
                       for row in bands)
    marked_months = all(('data-month="%s"' % row["month"]) in page
                        for row in months)
    open_label = any(row["upper_seconds"] is None for row in bands)
    open_ok = (not open_label) or labels.get("band_all", "") in page
    laws = [labels.get(key, "") for key in
            ("law_derive", "law_bands", "law_null", "law_median", "law_order",
             "law_months", "law_crossings", "law_bar", "law_scope",
             "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    cap_ok = labels.get("bar_caption", "") in page
    stand_in = ">None<" in page
    empty_probe_ok = False
    empty_dash = False
    try:
        probe_html = driver.build_html(probe_empty(), labels,
                                       "2026-01-01 00:00:00Z",
                                       doc.get("disclaimer") or "")
        empty_dash = ("<b>%s</b>" % dash) in probe_html
        empty_probe_ok = (labels.get("empty", "") in probe_html
                          and ">None<" not in probe_html and empty_dash
                          and labels.get("band_all", "") in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-RFLB4", marked_bands and marked_months and open_ok and laws_ok
       and cap_ok and empty_probe_ok and not stand_in,
       "bands=%s months=%s open_label=%s laws=%s cap=%s empty_probe=%s "
       "dash=%s stand_in_none=%s"
       % (marked_bands, marked_months, open_ok, laws_ok, cap_ok,
          empty_probe_ok, empty_dash, stand_in))

    # ---- AC-RFLB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    notadvice = labels.get("law_notadvice", "") in page
    ok("AC-RFLB5", aigc and on_page and external == 0 and notadvice,
       "aigc=%s disclaimer_on_page=%s external_links=%d notadvice=%s"
       % (aigc, on_page, external, notadvice))

    # ---- AC-RFLB6: --check reads clean, writes nothing, wiring intact.
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
        "api_refund_latency(" in read(FACE_SUITE)
    ok("AC-RFLB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
