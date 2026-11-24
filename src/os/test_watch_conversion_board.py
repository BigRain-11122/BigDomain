"""Battery suite for tools/watch_conversion_board.py - AC-WCVB1..6.

WHY THIS SUITE EXISTS (measured at R3436, not assumed):
api_watch_conversion shipped with its own AC-WCV1..8 criteria
(src/sandbox/ledger/test_apimarket_watchconversion.py on disk) but a git
grep over tools/, preview/ and the report collector answered rc=1 with zero
hits, so the resident's question - "did what I watched actually sell, how
long did it take and what share converted" - could not be opened by anyone.
api_listing_demand answers counts per listing and publishes no rate, no
latency and no aggregate. R3436 renders the market card plus one scoped card
per seller; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3436 PIN
BEFORE the driver existed):
  AC-WCVB1 the page and its json land, the json carries exactly the pinned
           eleven-key payload set, the market block and every seller block
           carry the shipped 15-key envelope, every category row carries the
           shipped 12-key row, seller_count equals the block count, the
           report points at a file that exists, and the four source
           fingerprints are recorded.
  AC-WCVB2 the data is the shipped face's own: the suite re-seeds the funnel
           through the shipped doors and re-reads api_watch_conversion() for
           the market and for every seller, and requires the page json
           (including the disclaimer and the category order) to equal that
           reading item for item - no typed fixture, no padded row.
  AC-WCVB3 the face's identities hold on the printed numbers: watch equals
           pre-owned plus funnel, funnel equals converted plus pending, the
           rate is converted over funnel, the four latency fields are null
           exactly when nothing converted and otherwise ordered fastest <=
           median <= slowest with the average inside the extremes, the
           oldest pending stamp is present exactly when something is
           pending, category counters sum to their envelope, categories are
           unique with the uncategorized bucket last, and the seller
           counters sum to the market counters.
  AC-WCVB4 the page reads honestly: one market card marked data-market, one
           card per seller marked data-seller, one row per category marked
           data-category, the three state badges carry the envelope counts,
           a rate bar is drawn exactly where the rate is defined and a dash
           is printed where it is not, a seller with no watched listing
           prints the named quiet sentence instead of an empty table, no bare
           None, and every KPI strip equals the shipped envelope.
  AC-WCVB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer and the not-advice sentence are on the page
           and there are zero external links.
  AC-WCVB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, the
           producer is named in tools/deliverable_index.py, and the shipped
           face's own suite is still on disk with AC-WCV arms.

Read-only over the repository: the world is rebuilt in a temp dir and the
probes render in memory, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "watch_conversion_board.py")
HTML = os.path.join(ROOT, "preview", "watch-conversion-board.html")
JSONF = os.path.join(ROOT, "preview", "watch-conversion-board.json")
COPY = os.path.join(ROOT, "preview", "watch-conversion-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
INDEX = os.path.join(ROOT, "tools", "deliverable_index.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_watchconversion.py")
ROW = "os-watch-conversion-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "scope", "seller_count",
    "sellers", "market", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "dev_account", "include_uncategorized", "watch_count",
    "pre_owned_count", "funnel_count", "converted_count", "pending_count",
    "conversion_rate", "avg_convert_seconds", "median_convert_seconds",
    "fastest_convert_seconds", "slowest_convert_seconds",
    "oldest_pending_watch_utc", "categories", "disclaimer",
}
ROW_KEYS = {
    "category", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate",
    "avg_convert_seconds", "median_convert_seconds",
    "fastest_convert_seconds", "slowest_convert_seconds",
    "oldest_pending_watch_utc",
}
COUNTERS = ("watch_count", "pre_owned_count", "funnel_count",
            "converted_count", "pending_count")

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
    spec = importlib.util.spec_from_file_location("wcvb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def block_problems(block, label):
    problems = []
    watches = int(block["watch_count"])
    pre_owned = int(block["pre_owned_count"])
    funnel = int(block["funnel_count"])
    converted = int(block["converted_count"])
    pending = int(block["pending_count"])
    if watches != pre_owned + funnel:
        problems.append("%s watch split" % label)
    if funnel != converted + pending:
        problems.append("%s funnel split" % label)
    rate = block["conversion_rate"]
    want = (float(converted) / funnel) if funnel else None
    if rate is None or want is None:
        if rate is not None or want is not None:
            problems.append("%s rate presence" % label)
    elif abs(float(rate) - want) > 1e-9:
        problems.append("%s rate value" % label)
    lat = [block["fastest_convert_seconds"],
           block["median_convert_seconds"],
           block["slowest_convert_seconds"],
           block["avg_convert_seconds"]]
    if converted == 0:
        if any(item is not None for item in lat):
            problems.append("%s latency with zero conversions" % label)
    else:
        if any(item is None for item in lat):
            problems.append("%s latency with conversions" % label)
        elif not (lat[0] <= lat[1] <= lat[2] and lat[0] <= lat[3] <= lat[2]):
            problems.append("%s latency order" % label)
    if (block["oldest_pending_watch_utc"] is None) != (pending == 0):
        problems.append("%s oldest pending" % label)
    cats = [row["category"] for row in block["categories"]]
    if len(set(cats)) != len(cats):
        problems.append("%s duplicate category" % label)
    if cats != sorted(cats, key=lambda c: (c is None, c)):
        problems.append("%s category order" % label)
    for key in COUNTERS:
        want_sum = sum(int(row[key]) for row in block["categories"])
        if want_sum != int(block[key]):
            problems.append("%s %s row sum" % (label, key))
    return problems


def empty_envelope():
    return {
        "dev_account": None, "include_uncategorized": True,
        "watch_count": 0, "pre_owned_count": 0, "funnel_count": 0,
        "converted_count": 0, "pending_count": 0, "conversion_rate": None,
        "avg_convert_seconds": None, "median_convert_seconds": None,
        "fastest_convert_seconds": None, "slowest_convert_seconds": None,
        "oldest_pending_watch_utc": None, "categories": [],
        "disclaimer": "probe disclaimer",
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    market = doc.get("market") or {}
    sellers = doc.get("sellers") or []

    # ---- AC-WCVB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    blocks_ok = (set(market.keys()) == ENVELOPE_KEYS
                 and all(set(block.keys()) == ENVELOPE_KEYS
                         for block in sellers))
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for block in [market] + sellers
                  for row in block["categories"])
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-WCVB1", landed and keys == PAYLOAD_KEYS and blocks_ok and rows_ok
       and sources_ok and bool(sellers) and bool(market.get("categories"))
       and int(doc.get("seller_count", -1)) == len(sellers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s blocks=%s rows=%s sources=%s "
       "sellers=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), blocks_ok, rows_ok, sources_ok,
          len(sellers), int(doc.get("seller_count", -1)), report_ok))

    # ---- AC-WCVB2: every printed number is the shipped face's own.
    driver = None
    live_ok = False
    live_detail = "driver unavailable"
    try:
        driver = load_driver()
        live_market, live_blocks, live_sellers, live_disclaimer = (
            driver.read_world())
        market_same = json.dumps(market, sort_keys=True) == json.dumps(
            {key: live_market[key] for key in ENVELOPE_KEYS}, sort_keys=True)
        sellers_same = json.dumps(sellers, sort_keys=True) == json.dumps(
            [{key: block[key] for key in ENVELOPE_KEYS}
             for block in live_blocks], sort_keys=True)
        ids_same = ([str(block["dev_account"]) for block in sellers]
                    == [str(block["dev_account"]) for block in live_blocks])
        disc_same = (doc.get("disclaimer") == live_disclaimer)
        order_same = ([row["category"] for row in market["categories"]]
                      == [row["category"]
                          for row in live_market["categories"]])
        live_ok = (market_same and sellers_same and ids_same and disc_same
                   and order_same)
        live_detail = ("market_same=%s sellers_same=%s ids_same=%s "
                       "disclaimer_same=%s order_same=%s sellers=%d "
                       "watches=%d"
                       % (market_same, sellers_same, ids_same, disc_same,
                          order_same, len(sellers),
                          int(market.get("watch_count", -1))))
    except Exception as exc:  # noqa: BLE001
        live_detail = "read_world raised %s: %s" % (type(exc).__name__, exc)
    ok("AC-WCVB2", live_ok, live_detail)

    # ---- AC-WCVB3: the face's identities hold on the printed numbers.
    problems = block_problems(market, "market")
    seen = set()
    for block in sellers:
        label = str(block.get("dev_account"))
        problems.extend(block_problems(block, label))
        if label in seen:
            problems.append("%s duplicated" % label)
        seen.add(label)
    for key in COUNTERS:
        want = sum(int(block[key]) for block in sellers)
        if int(market.get(key, -1)) != want:
            problems.append("market %s vs seller sum" % key)
    ok("AC-WCVB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-WCVB4: honest page face, badges, bars, dashes, quiet sellers.
    dash = labels.get("none", "-")
    market_cards = len(re.findall(r"<div class=card data-market=1>", page))
    seller_cards = len(re.findall(r'<div class=card data-seller="', page))
    printed_rows = len(re.findall(r"<tr data-category=\"", page))
    expected_rows = sum(len(block["categories"])
                        for block in [market] + sellers)
    defined = sum(1 for block in [market] + sellers
                  for row in block["categories"]
                  if row["conversion_rate"] is not None)
    undefined = expected_rows - defined
    bars = page.count('<span class="bar">')
    dash_cells = page.count(">%s<" % dash)
    no_none = ">None<" not in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_preowned", "law_funnel", "law_pending",
             "law_rate", "law_latency", "law_order", "law_scope", "law_bar",
             "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    kpi_ok = mix_ok = False
    empty_ok = no_cat_ok = True
    try:
        e = driver.html.escape
        kpi_ok = all(driver.kpi_html(block, labels, e, dash) in page
                     for block in [market] + sellers)
        mix_ok = all(driver.mix_cell(block, labels, e) in page
                     for block in [market] + sellers)
        probe = empty_envelope()
        no_seller_html = driver.build_html(
            probe, [], labels, "2026-01-01 00:00:00Z", "probe disclaimer")
        empty_ok = (labels.get("empty_seller", "@@") in no_seller_html
                    and ">None<" not in no_seller_html)
        one = dict(probe)
        one["dev_account"] = "usr:probe"
        no_cat_html = driver.build_html(
            probe, [one], labels, "2026-01-01 00:00:00Z", "probe disclaimer")
        no_cat_ok = (labels.get("empty_categories", "@@") in no_cat_html
                     and labels.get("empty_seller", "@@") not in no_cat_html
                     and ">None<" not in no_cat_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
        kpi_ok = mix_ok = False
    ok("AC-WCVB4", market_cards == 1 and seller_cards == len(sellers)
       and printed_rows == expected_rows and bars == defined
       and dash_cells >= undefined and no_none and laws_ok and kpi_ok
       and mix_ok and empty_ok and no_cat_ok,
       "market_cards=%d seller_cards=%d/%d rows=%d/%d bars=%d/%d "
       "dashes=%d/%d laws=%s kpi=%s mix=%s empty_probe=%s nocat_probe=%s "
       "bare_none=%s"
       % (market_cards, seller_cards, len(sellers), printed_rows,
          expected_rows, bars, defined, dash_cells, undefined, laws_ok,
          kpi_ok, mix_ok, empty_ok, no_cat_ok, not no_none))

    # ---- AC-WCVB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    not_advice = labels.get("law_notadvice", "") in page
    external = len(re.findall(r"https?://", page))
    ok("AC-WCVB5", aigc and on_page and not_advice and external == 0,
       "aigc=%s disclaimer_on_page=%s not_advice=%s external_links=%d"
       % (aigc, on_page, not_advice, external))

    # ---- AC-WCVB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-WCV" in read(FACE_SUITE)
    producer = read(INDEX)
    producer_ok = ('"watch-conversion-board.json": '
                   '"tools/watch_conversion_board.py"') in producer
    ok("AC-WCVB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok and producer_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s producer=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok, producer_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
