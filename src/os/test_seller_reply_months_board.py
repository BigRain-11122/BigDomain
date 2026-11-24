"""Battery suite for tools/seller_reply_months_board.py - AC-SRPM1..6.

WHY THIS SUITE EXISTS (measured at R3445, not assumed):
api_seller_reply_months shipped the monthly rating-reply cadence - a reply
books in the UTC month of its own immutable replied_utc, a cross-month
discharge counts as backlog and a silent month stays an honest zero row - but
a search over tools/, preview/ and src/os answered rc=1 for its name. The
reply family had a lifetime latency scorecard and no time axis, so a shop that
answered everything last quarter and then went silent read exactly like one
that never answered at all. R3445 renders the shipped envelope on one page;
this suite grades the page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3445 PIN row landed before any driver code):
  AC-SRPM1 the pair lands, the json carries exactly the pinned nine-key
           payload set, the market envelope and every seller envelope carry
           the shipped 25 keys, every month row the shipped 10 keys, the
           report points at a file that exists and the four source
           fingerprints are present.
  AC-SRPM2 the data is the shipped face's own: the suite builds its own
           throwaway world through the shipped doors under its own pinned
           clock, re-reads the market envelope and every seller scope, and
           requires the page json to equal those readings item for item,
           disclaimer and month ordering included.
  AC-SRPM3 the face identities hold and the driver refuses a broken one: the
           rating split, the coverage rounding, the contiguous month grid, the
           per-row backlog plus same-month conservation, the latency order,
           the null latencies on a silent month, the monotone accumulator, the
           envelope sums, the earliest peak, the seller benchmark and the
           market self-benchmark refusal all hold - and a forged month block
           is refused by name.
  AC-SRPM4 the page reads honestly: one marked month row per row, the same
           month and backlog badges, the dash where a number is absent, no
           bare None, the bar caption on the page, a bar only where a reply
           landed, and an empty envelope handed to the driver's own renderer
           prints the honest empty sentence (in-memory probe only).
  AC-SRPM5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer verbatim, the non-advice sentence, zero
           external links.
  AC-SRPM6 no older criterion is relaxed: the landed pair answers its own
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
TOOL = os.path.join(ROOT, "tools", "seller_reply_months_board.py")
HTML = os.path.join(ROOT, "preview", "seller-reply-months-board.html")
JSONF = os.path.join(ROOT, "preview", "seller-reply-months-board.json")
COPY = os.path.join(ROOT, "preview", "seller-reply-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_sellerreplymonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-reply-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "market", "sellers", "disclaimer",
    "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "dev_account", "scope", "owned_listing_count", "market_mean_seconds",
    "rating_count", "replied_count", "unreplied_count", "reply_coverage",
    "backlog_reply_count", "same_month_reply_count", "buyer_count",
    "listing_count", "month_count", "active_month_count", "peak_month",
    "peak_replied_count", "first_month", "last_month",
    "latest_month_replied_count", "fastest_seconds", "slowest_seconds",
    "mean_seconds", "oldest_unreplied_utc", "months", "disclaimer",
}
ROW_KEYS = {
    "month", "replied_count", "backlog_count", "same_month_count",
    "buyer_count", "listing_count", "fastest_seconds", "slowest_seconds",
    "mean_seconds", "running_replied",
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
    spec = importlib.util.spec_from_file_location("srpm_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_world(driver, am):
    """The suite's own copy of the story, every row through a shipped door."""
    board = am.api_board() or {}
    by_key = {}
    for row in board.get("listings") or []:
        by_key[str(row["listing_key"])] = row
    dana = str(by_key["risk-scan"]["dev_account"])
    frank = str(by_key["chart-render"]["dev_account"])
    frank_3 = int(by_key["chart-render"]["listing_id"])

    driver.STAMP["value"] = "2026-09-30T00:00:00Z"
    am.reply_to_rating(dana, 1, "yes it covers the tools we ship")
    driver.STAMP["value"] = "2026-11-10T08:00:00Z"
    am.purchase_api("usr:dave", frank_3, "r3445")
    am.rate_api("usr:dave", frank_3, 5)
    driver.STAMP["value"] = "2026-11-20T00:00:00Z"
    am.reply_to_rating(dana, 2, "thanks, glad it helped")
    return sorted({dana, frank})


def live_world(driver):
    import apimarket as A
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="srpm-suite-")
    db = os.path.join(tmp_root, "suite.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = driver._clock
        sellers = build_world(driver, am)
        market = dict(am.api_seller_reply_months())
        scoped = [{"seller": name,
                   "envelope": dict(am.api_seller_reply_months(name))}
                  for name in sellers]
        empty_scope = dict(am.api_seller_reply_months("usr:ghost"))
    finally:
        A._now_utc = orig_now
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    return market, scoped, empty_scope


def trim(envelope):
    doc = {key: envelope[key] for key in ENVELOPE_KEYS if key != "months"}
    doc["months"] = [{key: row[key] for key in ROW_KEYS}
                     for row in envelope.get("months") or []]
    return doc


def same(left, right):
    return json.dumps(left, sort_keys=True, default=str) == json.dumps(
        right, sort_keys=True, default=str)


def main():
    if not os.path.exists(TOOL):
        print("FAIL AC-SRPM1 driver missing")
        return 2
    driver = load_driver()
    labels = json.loads(read(COPY))
    page = json.loads(read(JSONF))
    doc = read(HTML)

    # ---- AC-SRPM1 contract ------------------------------------------------
    market = page.get("market") or {}
    sellers = page.get("sellers") or []
    missing_payload = sorted(PAYLOAD_KEYS - set(page))
    extra_payload = sorted(set(page) - PAYLOAD_KEYS)
    market_keys = set(k for k in market if k != "months")
    row_shapes = [set(row) for envelope in [market] + [s["envelope"]
                                                      for s in sellers]
                  for row in envelope.get("months") or []]
    report_path = os.path.join(ROOT, page.get("report") or "")
    sources = page.get("sources") or {}
    sizes = page.get("sizes") or {}
    ok("AC-SRPM1",
       not missing_payload and not extra_payload
       and market_keys == ENVELOPE_KEYS - {"months"}
       and all(shape == ROW_KEYS for shape in row_shapes)
       and os.path.exists(report_path)
       and sorted(sources) == ["apimarket", "copy", "driver", "report"]
       and sizes.get("html") == os.path.getsize(HTML)
       and sizes.get("json") == os.path.getsize(JSONF)
       and page.get("face") == "api_seller_reply_months",
       "landed=True payload_missing=%r payload_extra=%r market=True rows=%d "
       "sellers=%d report=True sources=True"
       % (missing_payload, extra_payload, len(row_shapes), len(sellers)))

    # ---- AC-SRPM2 the data is the shipped face's own ----------------------
    market_live, scoped_live, empty_live = live_world(driver)
    live_scopes = {item["seller"]: item["envelope"] for item in scoped_live}
    same_market = same(trim(market_live), market)
    same_sellers = all(same(trim(live_scopes[s["seller"]]), s["envelope"])
                       for s in sellers)
    same_words = (page.get("disclaimer") == market_live.get("disclaimer")
                  and all(s["envelope"].get("disclaimer")
                          == live_scopes[s["seller"]].get("disclaimer")
                          for s in sellers))
    same_order = ([s["seller"] for s in sellers] == sorted(live_scopes)
                  and [r["month"] for r in market.get("months") or []]
                  == [r["month"] for r in market_live.get("months") or []])
    ok("AC-SRPM2",
       same_market and same_sellers and same_words and same_order,
       "market_same=%r sellers_same=%r disclaimer_same=%r order_same=%r "
       "rows=%d sellers=%d"
       % (same_market, same_sellers, same_words, same_order,
          len(market.get("months") or []), len(sellers)))

    # ---- AC-SRPM3 laws, plus a forged month block refused by name ---------
    driver_problems = driver.check_laws(market_live, scoped_live, empty_live)
    forged = json.loads(json.dumps(market_live, default=str))
    forged["months"][0]["replied_count"] = (
        int(forged["months"][0]["replied_count"]) + 7)
    forged_problems = driver.check_laws(forged, scoped_live, empty_live)
    page_rows = market.get("months") or []
    split_ok = all(int(r["backlog_count"]) + int(r["same_month_count"])
                   == int(r["replied_count"]) for r in page_rows)
    running = [int(r["running_replied"]) for r in page_rows]
    peak_ok = (market.get("peak_month") == page_rows[0]["month"]
               and int(market.get("peak_replied_count"))
               == int(page_rows[0]["replied_count"]))
    coverage_ok = (market.get("reply_coverage")
                   == round(int(market["replied_count"])
                            / float(market["rating_count"]), 4))
    ok("AC-SRPM3",
       not driver_problems and len(forged_problems) >= 1
       and split_ok and running == sorted(running)
       and running[-1] == int(market["replied_count"])
       and peak_ok and coverage_ok,
       "driver_problems=%d forged_problems=%d split=%r running=%r peak=%r "
       "coverage=%r"
       % (len(driver_problems), len(forged_problems), split_ok, running,
          peak_ok, coverage_ok))

    # ---- AC-SRPM4 the page reads honestly ---------------------------------
    dash = labels["none"]
    months = page_rows
    marked = all(('data-month="%s"' % r["month"]) in doc for r in months)
    badges = (labels["badge_silent"] in doc and labels["badge_same"] in doc
              and labels["badge_backlog"] in doc)
    bare_none = "None" in doc or "null" in doc
    caption = labels["bar_caption"] in doc
    bars = doc.count('<div class="bar">')
    wants = sum(1 for envelope in [market] + [s["envelope"] for s in sellers]
                for r in envelope.get("months") or []
                if int(r["replied_count"]) > 0)
    kpi_value = ('<b>%d</b>' % int(market["rating_count"])) in doc
    empty_html = driver.build_html(
        {"scope": "market", "months": [], "disclaimer": "x",
         "reply_coverage": None, "market_mean_seconds": None},
        [], labels, "2026-11-25 00:00:00Z", "x")
    empty_ok = labels["empty"] in empty_html
    ok("AC-SRPM4",
       marked and badges and not bare_none and caption
       and bars == wants and kpi_value and empty_ok,
       "marked=%r badges=%r no_bare_none=%r caption=%r bars=%d/%d "
       "kpi=%r empty=%r dash=%s"
       % (marked, badges, not bare_none, caption, bars, wants, kpi_value,
          empty_ok, dash))

    # ---- AC-SRPM5 compliance ---------------------------------------------
    disclaimer = market.get("disclaimer") or ""
    aigc = "AIGC" in doc
    verbatim = disclaimer and disclaimer in doc
    notadvice = labels["law_notadvice"] in doc
    zero_links = "http://" not in doc and "https://" not in doc
    ok("AC-SRPM5", aigc and verbatim and notadvice and zero_links,
       "aigc=%r disclaimer_verbatim=%r notadvice=%r zero_links=%r"
       % (aigc, bool(verbatim), notadvice, zero_links))

    # ---- AC-SRPM6 no older criterion is relaxed --------------------------
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
    face_ac = "AC-SRM1" in read(FACE_SUITE) if face_suite else False
    ok("AC-SRPM6",
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
