"""Battery suite for tools/seller_price_demand_board.py - AC-SPDB1..6.

WHY THIS SUITE EXISTS (measured at R3444, not assumed):
api_seller_price_demand_months shipped the monthly repricing response to
demand - the revision, watch, unwatch and question legs joined on the month
axis under AC-SPD1..8 - but a search over tools/, preview/ and src/os answered
rc=1 for its name. The market already had a cadence timeline, an attention
timeline and a question timeline and no page that put them side by side, so
"when interest rose, did anyone move the price" could only be read by calling
the sandbox from a shell. R3444 renders the shipped envelope on one page; this
suite grades the page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3444 PIN row landed before any driver code):
  AC-SPDB1 the pair lands, the json carries exactly the pinned nine-key payload
           set, the market envelope and every seller envelope carry the shipped
           22 keys, every month row the shipped 10 keys, the report points at a
           file that exists and the four source fingerprints are present.
  AC-SPDB2 the data is the shipped face's own: the suite builds its own
           throwaway world through the shipped doors under its own pinned
           clock, re-reads the market envelope and every seller scope, and
           requires the page json to equal those readings item for item,
           disclaimer and month ordering included.
  AC-SPDB3 the face identities hold and the driver refuses a broken one: the
           up/down split sums to the revision count, the net counts are the
           signed differences, the seven envelope counters equal the month
           sums, the demand and response months are recomputed from the rows,
           the rate is absent without demand and equal to response over demand
           with it, the accumulator is monotone and ends at the total, the peak
           takes the earliest maximum, seller totals equal the market, and the
           seller scope carries the market benchmark while the market scope
           never benchmarks itself.
  AC-SPDB4 the page reads honestly: one marked month row per row, the demand
           and response badges, the dash where a number is absent, no bare
           None, the bar caption on the page, a bar only where a revision
           landed, and an empty scope handed to the driver's own renderer
           prints the honest empty sentence with the market benchmark kept
           (in-memory probe only).
  AC-SPDB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer verbatim, the non-advice sentence, zero
           external links.
  AC-SPDB6 no older criterion is relaxed: the landed pair answers its own
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
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "seller_price_demand_board.py")
HTML = os.path.join(ROOT, "preview", "seller-price-demand-board.html")
JSONF = os.path.join(ROOT, "preview", "seller-price-demand-board.json")
COPY = os.path.join(ROOT, "preview", "seller-price-demand-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_sellerpricedemandmonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-price-demand-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "market", "sellers", "disclaimer",
    "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "dev_account", "scope", "month_count", "active_month_count",
    "revision_count", "up_count", "down_count", "watch_count",
    "unwatch_count", "watch_net_count", "question_count",
    "response_month_count", "demand_month_count", "response_rate",
    "peak_revision_month", "peak_revision_count", "market_response_rate",
    "latest_month_revision_count", "first_month", "last_month", "months",
    "disclaimer",
}
ROW_KEYS = {
    "month", "revision_count", "up_count", "down_count", "net_count",
    "watch_count", "unwatch_count", "watch_net_count", "question_count",
    "running_revision",
}
SUM_KEYS = ("revision_count", "up_count", "down_count", "watch_count",
            "unwatch_count", "watch_net_count", "question_count")

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


def load_driver():
    spec = importlib.util.spec_from_file_location("spdb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_world():
    """The suite's own world: same story, its own stack and its own clock."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket as A
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="spdb-suite-")
    db = os.path.join(tmp_root, "spdb.db")
    led, mtr, dk, am = R.build_stack(db)
    orig_now = A._now_utc
    clock = {"value": "2026-09-05T00:00:00Z"}
    try:
        R.seed_demo(am, led, dk)
        A._now_utc = lambda: clock["value"]
        board = am.api_public_listings() or {}
        by_key = {str(row["listing_key"]): row
                  for row in board.get("listings") or []}
        dana_shelf = int(by_key["risk-scan"]["listing_id"])
        frank_shelf = int(by_key["chart-render"]["listing_id"])
        dana = str(by_key["risk-scan"]["dev_account"])
        frank = str(by_key["chart-render"]["dev_account"])
        clock["value"] = "2026-09-05T00:00:00Z"
        am.revise_price(dana, dana_shelf,
                        int(by_key["risk-scan"]["token_price"]) + 2)
        clock["value"] = "2026-09-06T00:00:00Z"
        am.watch_api("usr:bob", dana_shelf)
        clock["value"] = "2026-09-07T00:00:00Z"
        am.ask_question("usr:bob", dana_shelf, "does it cover tools")
        clock["value"] = "2026-10-04T00:00:00Z"
        am.watch_api("usr:carol", frank_shelf)
        clock["value"] = "2026-11-03T00:00:00Z"
        am.unwatch_api("usr:bob", dana_shelf)
        clock["value"] = "2026-11-09T00:00:00Z"
        am.revise_price(frank, frank_shelf,
                        max(1, int(by_key["chart-render"]["token_price"]) - 1))
        sellers = sorted({dana, frank})
        market = dict(am.api_seller_price_demand_months())
        scoped = [{"seller": name,
                   "envelope": dict(
                       am.api_seller_price_demand_months(name))}
                  for name in sellers]
        empty = dict(am.api_seller_price_demand_months("usr:ghost"))
        return market, scoped, empty
    finally:
        A._now_utc = orig_now
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def trim(envelope):
    doc = {key: envelope[key] for key in ENVELOPE_KEYS if key != "months"}
    doc["months"] = [{key: row[key] for key in ROW_KEYS}
                     for row in envelope.get("months") or []]
    return doc


def problem_list(envelope, tag, market_rate):
    """The suite's own reading of the shipped laws, independent of the driver."""
    problems = []
    rows = envelope.get("months") or []
    if int(envelope.get("month_count", -1)) != len(rows):
        problems.append("%s month_count" % tag)
    sums = dict((key, 0) for key in SUM_KEYS)
    demand = 0
    response = 0
    running = []
    for row in rows:
        if set(row.keys()) != ROW_KEYS:
            problems.append("%s row keys" % tag)
            continue
        for key in sums:
            sums[key] += int(row[key])
        if int(row["up_count"]) + int(row["down_count"]) != int(
                row["revision_count"]):
            problems.append("%s split" % tag)
        if int(row["net_count"]) != int(row["up_count"]) - int(
                row["down_count"]):
            problems.append("%s net" % tag)
        if int(row["watch_net_count"]) != int(row["watch_count"]) - int(
                row["unwatch_count"]):
            problems.append("%s watch net" % tag)
        has_demand = int(row["watch_net_count"]) > 0 or int(
            row["question_count"]) > 0
        if has_demand:
            demand += 1
            if int(row["revision_count"]) > 0:
                response += 1
        running.append(int(row["running_revision"]))
    for key in sums:
        if sums[key] != int(envelope.get(key, -2)):
            problems.append("%s %s sum" % (tag, key))
    if running and running != sorted(running):
        problems.append("%s accumulator" % tag)
    if running and running[-1] != int(envelope.get("revision_count", -1)):
        problems.append("%s accumulator end" % tag)
    if demand != int(envelope.get("demand_month_count", -1)):
        problems.append("%s demand months" % tag)
    if response != int(envelope.get("response_month_count", -1)):
        problems.append("%s response months" % tag)
    rate = envelope.get("response_rate")
    if demand == 0:
        if rate is not None:
            problems.append("%s rate on no demand" % tag)
    elif rate is None or abs(float(rate) - round(response / float(demand), 4)) \
            > 1e-12:
        problems.append("%s rate value" % tag)
    if rows:
        if envelope.get("first_month") != rows[0]["month"]:
            problems.append("%s first month" % tag)
        if envelope.get("last_month") != rows[-1]["month"]:
            problems.append("%s last month" % tag)
        peaks = [(row["month"], int(row["revision_count"])) for row in rows
                 if int(row["revision_count"]) > 0]
        if peaks:
            best = max(count for _, count in peaks)
            first = [month for month, count in peaks if count == best][0]
            if envelope.get("peak_revision_month") != first:
                problems.append("%s peak month" % tag)
            if int(envelope.get("peak_revision_count") or -1) != best:
                problems.append("%s peak count" % tag)
    if envelope.get("scope") == "market":
        if envelope.get("market_response_rate") is not None:
            problems.append("%s self benchmark" % tag)
    elif envelope.get("market_response_rate") != market_rate:
        problems.append("%s benchmark" % tag)
    return problems


def forge(envelope):
    """Break a month block three named ways without touching the source."""
    broken = json.loads(json.dumps(envelope))
    rows = broken.get("months") or []
    if rows:
        rows[0]["up_count"] = int(rows[0]["up_count"]) + 3
        rows[0]["watch_net_count"] = int(rows[0]["watch_net_count"]) - 2
        rows[-1]["running_revision"] = int(rows[-1]["running_revision"]) - 1
    return broken


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    market = doc.get("market") or {}
    sellers = doc.get("sellers") or []
    rows = market.get("months") or []

    # ---- AC-SPDB1: the pair landed with exactly the pinned key sets.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    seller_keys_ok = all(
        set(item.keys()) == {"seller", "envelope"}
        and set(item["envelope"].keys()) == ENVELOPE_KEYS
        and all(set(row.keys()) == ROW_KEYS
                for row in item["envelope"]["months"])
        for item in sellers)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-SPDB1", landed and keys == PAYLOAD_KEYS
       and set(market.keys()) == ENVELOPE_KEYS
       and all(set(row.keys()) == ROW_KEYS for row in rows)
       and seller_keys_ok and report_ok and sources_ok
       and set(labels.keys()) >= set(json.loads(read(COPY)).keys()),
       "landed=%s payload_missing=%s payload_extra=%s market=%s rows=%s "
       "sellers=%s report=%s sources=%s"
       % (landed, sorted(PAYLOAD_KEYS - keys), sorted(keys - PAYLOAD_KEYS),
          set(market.keys()) == ENVELOPE_KEYS,
          all(set(row.keys()) == ROW_KEYS for row in rows),
          seller_keys_ok, report_ok, sources_ok))

    # ---- AC-SPDB2: every printed value is the shipped face's own.
    live_market, live_scoped, live_empty = live_world()
    market_same = json.dumps(trim(live_market), sort_keys=True) == \
        json.dumps(market, sort_keys=True)
    live_by = {item["seller"]: trim(item["envelope"])
               for item in live_scoped}
    sellers_same = len(sellers) == len(live_scoped) and all(
        item["seller"] in live_by
        and json.dumps(item["envelope"], sort_keys=True) ==
        json.dumps(live_by[item["seller"]], sort_keys=True)
        for item in sellers)
    disc_same = (doc.get("disclaimer") == live_market.get("disclaimer")
                 and all(item["envelope"].get("disclaimer")
                         == live_market.get("disclaimer")
                         for item in sellers))
    ok("AC-SPDB2", market_same and sellers_same and disc_same
       and bool(rows) and bool(sellers),
       "market_same=%s sellers_same=%s disclaimer_same=%s rows=%d sellers=%d"
       % (market_same, sellers_same, disc_same, len(rows), len(sellers)))

    # ---- AC-SPDB3: identities hold and the driver refuses a broken block.
    market_rate = live_market.get("response_rate")
    problems = problem_list(live_market, "market", market_rate)
    totals = dict((key, 0) for key in SUM_KEYS)
    for item in live_scoped:
        problems += problem_list(item["envelope"], "seller %s"
                                 % item["seller"], market_rate)
        for key in totals:
            totals[key] += int(item["envelope"].get(key, 0))
    for key in totals:
        if totals[key] != int(live_market.get(key, -2)):
            problems.append("partition %s" % key)
    driver = load_driver()
    driver_problems = driver.check_laws(
        live_market, live_scoped, live_empty)
    forged = forge(live_market)
    forged_problems = driver.check_laws(
        forged, live_scoped, live_empty)
    ok("AC-SPDB3", not problems and not driver_problems
       and len(forged_problems) >= 3,
       "suite_problems=%d driver_problems=%d forged_problems=%d"
       % (len(problems), len(driver_problems), len(forged_problems)))

    # ---- AC-SPDB4: the page reads honestly.
    marked = all(('data-month="%s"' % row["month"]) in page for row in rows)
    badges = (labels.get("badge_response", "") in page
              and labels.get("badge_demand", "") in page
              and labels.get("badge_quiet", "") in page)
    dash = labels.get("none") or "-"
    no_bare_none = "None" not in page
    caption = (labels.get("bar_caption") or "") in page
    bars = page.count("<div class=\"bar\">")
    envelopes = [live_market] + [item["envelope"] for item in live_scoped]
    want_bars = sum(
        1 for envelope in envelopes
        for row in envelope.get("months") or []
        if envelope.get("peak_revision_count")
        and int(row["revision_count"]) > 0)
    kpi_ok = ('<b>%d</b>' % int(live_market.get("revision_count", -1))) in page
    empty_page = driver.build_html(
        live_empty, [], labels, "2026-11-25 00:00:00Z",
        live_empty.get("disclaimer"))
    empty_ok = (labels.get("empty", "") in empty_page
                and str(live_market.get("response_rate")) in empty_page
                and dash in page)
    ok("AC-SPDB4", marked and badges and no_bare_none and caption
       and bars == want_bars and kpi_ok and empty_ok,
       "marked=%s badges=%s no_bare_none=%s caption=%s bars=%d/%d kpi=%s "
       "empty=%s dash=%s"
       % (marked, badges, no_bare_none, caption, bars, want_bars, kpi_ok,
          empty_ok, dash))

    # ---- AC-SPDB5: the standing compliance faces ride along.
    disclaimer = live_market.get("disclaimer") or ""
    aigc = labels.get("aigc", "") in page and "AIGC" in page
    verbatim = bool(disclaimer) and disclaimer in page
    notadvice = labels.get("law_notadvice", "") in page
    no_links = not re.search(r"https?://", page)
    ok("AC-SPDB5", aigc and verbatim and notadvice and no_links,
       "aigc=%s disclaimer_verbatim=%s notadvice=%s zero_links=%s"
       % (aigc, verbatim, notadvice, no_links))

    # ---- AC-SPDB6: no older criterion is relaxed.
    before = (stamp(HTML), stamp(JSONF))
    check_rc, check_out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    readonly = before == after and check_rc == 0 and "fails=0" in check_out
    registry = read(REGISTRY)
    registered = ('"%s"' % ROW) in registry and \
        "test_seller_price_demand_board.py" in registry and \
        re.search(r'test_seller_price_demand_board\.py"\), %d\)' % DECLARED,
                  registry) is not None
    face_suite = os.path.exists(FACE_SUITE) and \
        "AC-SPD" in read(FACE_SUITE)
    ok("AC-SPDB6", readonly and registered and face_suite,
       "readonly=%s check_rc=%d registered=%s face_suite=%s"
       % (readonly, check_rc, registered, face_suite))

    verdict = "SUITE PASS 6/6" if not FAILS else "SUITE FAIL %d/6" % (
        6 - len(FAILS))
    print("%s declared=%d row=%s" % (verdict, DECLARED, ROW))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
