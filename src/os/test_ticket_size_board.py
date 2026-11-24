"""Battery suite for tools/ticket_size_board.py - AC-TSZB1..6.

WHY THIS SUITE EXISTS (measured at R3443, not assumed):
api_market_ticket_size and api_market_ticket_size_months shipped the achieved
ticket size - the five-number band, the two refund conventions, the per-seller
scope and the monthly grid with its running accumulator - under AC-MTM1..8,
but a search over tools/, preview/ and src/os answered rc=1 for both names. The
market already had lifetime sale counts, monthly revenue and price bands, so
how large one ticket is, whether this month's tickets are richer than last
month's and whether refunds sit inside the average could only be read by
calling the sandbox from a shell. R3443 renders the shipped envelopes on one
page; this suite grades the page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3443 PIN row landed before any driver code):
  AC-TSZB1 the pair lands, the json carries exactly the pinned 12-key payload
           set, the two market envelopes and every seller envelope carry the
           shipped 19 keys, the monthly block carries its pinned keys, every
           month row the shipped 8 keys, the report points at a file that
           exists and the four source fingerprints are present.
  AC-TSZB2 the data is the shipped faces' own: the suite builds its own
           throwaway world, re-reads both refund conventions, every seller
           scope and the monthly envelope, and requires the page json to equal
           those readings item for item, disclaimer and ordering included.
  AC-TSZB3 the faces' identities hold and the driver refuses a broken one:
           category rows sum to each envelope, net equals gross minus refunds,
           the mean is gross over sales, the band is monotone and the spread is
           max minus min, the plain gross equals the refunded net, seller totals
           equal the market refunded totals, monthly totals equal the lifetime
           refunded totals, the running accumulator is monotone and ends at the
           monthly gross, the month grid is contiguous, and the peak and latest
           medians agree with the rows.
  AC-TSZB4 the page reads honestly: marked scope cards, marked seller cards,
           marked month and category rows, the dash where a scope has nothing,
           no bare None, the bar caption on the page, one bar per month with a
           p90 and no bar where there is none, an empty envelope and an empty
           month grid handed to the driver's own renderer print the honest empty
           sentence (in-memory probes only).
  AC-TSZB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer verbatim, the non-advice sentence, zero
           external links.
  AC-TSZB6 no older criterion is relaxed: the landed pair answers its own
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
TOOL = os.path.join(ROOT, "tools", "ticket_size_board.py")
HTML = os.path.join(ROOT, "preview", "ticket-size-board.html")
JSONF = os.path.join(ROOT, "preview", "ticket-size-board.json")
COPY = os.path.join(ROOT, "preview", "ticket-size-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_marketticketsizemonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-ticket-size-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "faces", "scope", "market_lifetime",
    "market_lifetime_refunded", "sellers", "months", "disclaimer", "report",
    "sources", "sizes",
}
LIFE_KEYS = {
    "scope", "dev_account", "include_refunded", "sale_count",
    "refunded_sale_count", "gross_tokens", "refunded_tokens",
    "net_gross_tokens", "mean_ticket", "p25_ticket", "p50_ticket",
    "p75_ticket", "p90_ticket", "min_ticket", "max_ticket", "spread",
    "category_count", "categories", "disclaimer",
}
CAT_KEYS = {
    "category", "sale_count", "refunded_sale_count", "gross_tokens",
    "net_gross_tokens", "refunded_tokens", "mean_ticket", "p50_ticket",
    "min_ticket", "max_ticket",
}
MONTH_BLOCK_KEYS = {
    "month_count", "first_month", "last_month", "sale_count",
    "refunded_sale_count", "gross_tokens", "mean_ticket", "median_ticket",
    "p90_ticket", "min_ticket", "max_ticket", "peak_month",
    "peak_median_ticket", "latest_month_median_ticket", "rows",
}
MONTH_ROW_KEYS = {
    "month", "sale_count", "refunded_sale_count", "gross_tokens",
    "mean_ticket", "median_ticket", "p90_ticket", "running_ticket_tokens",
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


def load_driver():
    spec = importlib.util.spec_from_file_location("tszb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_world():
    """Both refund conventions, every seller scope and the monthly envelope."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="tszb-suite-")
    db = os.path.join(tmp_root, "tszb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        plain = dict(am.api_market_ticket_size())
        refunded = dict(am.api_market_ticket_size(include_refunded=True))
        months = dict(am.api_market_ticket_size_months())
        sellers = sorted({row["dev_account"]
                          for row in (am.api_public_listings() or {})
                          .get("listings") or []})
        scoped = [(seller,
                   dict(am.api_market_ticket_size(seller, True)),
                   dict(am.api_market_ticket_size(seller)))
                  for seller in sellers]
        return plain, refunded, months, scoped
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def trim(envelope):
    doc = {key: envelope[key] for key in LIFE_KEYS if key != "categories"}
    doc["categories"] = [{key: row[key] for key in CAT_KEYS}
                         for row in envelope.get("categories") or []]
    return doc


def band_problems(envelope, tag):
    problems = []
    cats = envelope.get("categories") or []
    sales = int(envelope.get("sale_count", -1))
    if int(envelope.get("category_count", -1)) != len(cats):
        problems.append("%s category_count" % tag)
    for key in ("sale_count", "refunded_sale_count", "gross_tokens"):
        if sum(int(row[key]) for row in cats) != int(envelope.get(key, -1)):
            problems.append("%s %s sum" % (tag, key))
    if int(envelope.get("net_gross_tokens", -1)) != int(
            envelope.get("gross_tokens", -2)) - int(
                envelope.get("refunded_tokens", -3)):
        problems.append("%s net" % tag)
    if sales > 0:
        mean = envelope.get("mean_ticket")
        if mean is None or abs(float(mean) - int(envelope["gross_tokens"])
                               / float(sales)) > 1e-9:
            problems.append("%s mean" % tag)
        band = [envelope.get(key) for key in
                ("min_ticket", "p25_ticket", "p50_ticket", "p75_ticket",
                 "p90_ticket", "max_ticket")]
        if any(point is None for point in band):
            problems.append("%s band missing" % tag)
        else:
            nums = [float(point) for point in band]
            if nums != sorted(nums):
                problems.append("%s band order" % tag)
            if not (nums[0] <= float(mean) <= nums[-1]):
                problems.append("%s mean outside band" % tag)
            if abs(float(envelope.get("spread", -1)) -
                   (nums[-1] - nums[0])) > 1e-9:
                problems.append("%s spread" % tag)
    else:
        for key in ("mean_ticket", "p50_ticket", "min_ticket", "max_ticket",
                    "spread"):
            if envelope.get(key) is not None:
                problems.append("%s %s on zero scope" % (tag, key))
        if cats:
            problems.append("%s categories on zero scope" % tag)
    for row in cats:
        if set(row.keys()) != CAT_KEYS:
            problems.append("%s category keys" % tag)
    return problems


def empty_life(scope="market", refunded=False):
    return {
        "scope": scope, "dev_account": None,
        "include_refunded": refunded, "sale_count": 0,
        "refunded_sale_count": 0, "gross_tokens": 0, "refunded_tokens": 0,
        "net_gross_tokens": 0, "mean_ticket": None, "p25_ticket": None,
        "p50_ticket": None, "p75_ticket": None, "p90_ticket": None,
        "min_ticket": None, "max_ticket": None, "spread": None,
        "category_count": 0, "categories": [],
        "disclaimer": "sandbox stand-in disclaimer",
    }


def empty_months():
    return {
        "scope": "market", "sale_count": 0, "refunded_sale_count": 0,
        "gross_tokens": 0, "mean_ticket": None, "median_ticket": None,
        "p90_ticket": None, "min_ticket": None, "max_ticket": None,
        "month_count": 0, "first_month": None, "last_month": None,
        "peak_month": None, "peak_median_ticket": None,
        "latest_month_median_ticket": None,
        "disclaimer": "sandbox stand-in disclaimer", "months": [],
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    sellers = doc.get("sellers") or []
    block = doc.get("months") or {}
    rows = block.get("rows") or []

    # ---- AC-TSZB1: the pair landed with exactly the pinned key sets.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    plain = doc.get("market_lifetime") or {}
    refunded = doc.get("market_lifetime_refunded") or {}
    seller_keys_ok = all(
        set(item.keys()) == {"seller", "lifetime", "lifetime_plain"}
        and set(item["lifetime"].keys()) == LIFE_KEYS
        and set(item["lifetime_plain"].keys()) == LIFE_KEYS
        and all(set(row.keys()) == CAT_KEYS
                for row in item["lifetime"]["categories"])
        for item in sellers)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-TSZB1", landed and keys == PAYLOAD_KEYS
       and set(plain.keys()) == LIFE_KEYS and set(refunded.keys()) == LIFE_KEYS
       and set(block.keys()) == MONTH_BLOCK_KEYS
       and all(set(row.keys()) == MONTH_ROW_KEYS for row in rows)
       and seller_keys_ok and report_ok and sources_ok,
       "landed=%s keys_missing=%s keys_extra=%s life=%s/%s block=%s rows=%s "
       "sellers=%s report=%s sources=%s"
       % (landed, sorted(PAYLOAD_KEYS - keys), sorted(keys - PAYLOAD_KEYS),
          set(plain.keys()) == LIFE_KEYS, set(refunded.keys()) == LIFE_KEYS,
          set(block.keys()) == MONTH_BLOCK_KEYS,
          all(set(row.keys()) == MONTH_ROW_KEYS for row in rows),
          seller_keys_ok, report_ok, sources_ok))

    # ---- AC-TSZB2: every printed value is the shipped faces' own.
    live_plain, live_refunded, live_months, live_scoped = live_world()
    plain_same = json.dumps(trim(live_plain), sort_keys=True) == \
        json.dumps(plain, sort_keys=True)
    refunded_same = json.dumps(trim(live_refunded), sort_keys=True) == \
        json.dumps(refunded, sort_keys=True)
    live_rows = [{key: row[key] for key in MONTH_ROW_KEYS}
                 for row in live_months.get("months") or []]
    rows_same = json.dumps(rows, sort_keys=True) == \
        json.dumps(live_rows, sort_keys=True)
    block_fields = ("month_count", "first_month", "last_month", "sale_count",
                    "refunded_sale_count", "gross_tokens", "mean_ticket",
                    "median_ticket", "p90_ticket", "min_ticket", "max_ticket",
                    "peak_month", "peak_median_ticket",
                    "latest_month_median_ticket")
    block_same = all(block.get(key) == live_months.get(key)
                     for key in block_fields)
    live_by = {seller: (trim(ref), trim(pl))
               for seller, ref, pl in live_scoped}
    sellers_same = len(sellers) == len(live_scoped) and all(
        item["seller"] in live_by
        and json.dumps(item["lifetime"], sort_keys=True) ==
        json.dumps(live_by[item["seller"]][0], sort_keys=True)
        and json.dumps(item["lifetime_plain"], sort_keys=True) ==
        json.dumps(live_by[item["seller"]][1], sort_keys=True)
        for item in sellers)
    disc_same = (doc.get("disclaimer") == live_plain.get("disclaimer")
                 and doc.get("disclaimer") == live_refunded.get("disclaimer")
                 and doc.get("disclaimer") == live_months.get("disclaimer"))
    ok("AC-TSZB2", plain_same and refunded_same and rows_same and block_same
       and sellers_same and disc_same and bool(rows) and bool(sellers),
       "plain_same=%s refunded_same=%s rows_same=%s block_same=%s "
       "sellers_same=%s disclaimer_same=%s rows=%d sellers=%d"
       % (plain_same, refunded_same, rows_same, block_same, sellers_same,
          disc_same, len(rows), len(sellers)))

    # ---- AC-TSZB3: identities hold and the driver refuses a broken one.
    problems = band_problems(plain, "market")
    problems += band_problems(refunded, "market_refunded")
    if int(plain.get("gross_tokens", -1)) != int(
            refunded.get("net_gross_tokens", -2)):
        problems.append("plain gross != refunded net")
    seller_sales = sum(int(item["lifetime"]["sale_count"])
                       for item in sellers)
    seller_gross = sum(int(item["lifetime"]["gross_tokens"])
                       for item in sellers)
    if seller_sales != int(refunded.get("sale_count", -1)):
        problems.append("seller sales != market refunded")
    if seller_gross != int(refunded.get("gross_tokens", -1)):
        problems.append("seller gross != market refunded")
    totals = {"sale_count": sum(int(row["sale_count"]) for row in rows),
              "refunded_sale_count": sum(int(row["refunded_sale_count"])
                                         for row in rows),
              "gross_tokens": sum(int(row["gross_tokens"]) for row in rows)}
    for key in totals:
        if totals[key] != int(refunded.get(key, -2)):
            problems.append("monthly %s != lifetime refunded" % key)
        if totals[key] != int(block.get(key, -3)):
            problems.append("monthly %s != block" % key)
    running = [int(row["running_ticket_tokens"]) for row in rows]
    if running != sorted(running):
        problems.append("running not monotone")
    if running and running[-1] != int(block.get("gross_tokens", -1)):
        problems.append("running does not end at block gross")
    months_seen = [row["month"] for row in rows]
    if months_seen != sorted(months_seen):
        problems.append("months not ascending")
    for index in range(1, len(months_seen)):
        year, month = int(months_seen[index - 1][:4]), \
            int(months_seen[index - 1][5:7])
        month += 1
        if month > 12:
            month = 1
            year += 1
        if "%04d-%02d" % (year, month) != months_seen[index]:
            problems.append("month gap after %s" % months_seen[index - 1])
    medians = [(row["month"], row["median_ticket"]) for row in rows
               if row["median_ticket"] is not None]
    if medians:
        best = max(float(value) for _, value in medians)
        first = [month for month, value in medians
                 if float(value) == best][0]
        if block.get("peak_month") != first:
            problems.append("peak month")
        if abs(float(block.get("peak_median_ticket") or -1) - best) > 1e-9:
            problems.append("peak median")
        if block.get("latest_month_median_ticket") != rows[-1]["median_ticket"]:
            problems.append("latest median")
    driver = load_driver()
    driver_problems = driver.check_laws(
        live_plain, live_refunded,
        [{"seller": seller, "lifetime": ref, "lifetime_plain": pl}
         for seller, ref, pl in live_scoped], live_months)
    broken = empty_months()
    broken.update({"sale_count": 3, "gross_tokens": 9, "min_ticket": 1,
                   "max_ticket": 9, "mean_ticket": 3.0, "median_ticket": 3.0,
                   "p90_ticket": 3.0, "month_count": 1,
                   "first_month": "2026-09", "last_month": "2026-09",
                   "peak_month": "2026-09", "peak_median_ticket": 3.0,
                   "latest_month_median_ticket": 3.0,
                   "months": [{"month": "2026-09", "sale_count": 3,
                               "refunded_sale_count": 0, "gross_tokens": 9,
                               "mean_ticket": 3.0, "median_ticket": 3.0,
                               "p90_ticket": 3.0,
                               "running_ticket_tokens": 9}]})
    broken_problems = driver.check_laws(
        live_plain, live_refunded,
        [{"seller": seller, "lifetime": ref, "lifetime_plain": pl}
         for seller, ref, pl in live_scoped], broken)
    ok("AC-TSZB3", not problems and not driver_problems
       and bool(broken_problems),
       "problems=%s driver=%s broken_refused=%s"
       % (problems[:4] if problems else [], driver_problems[:3]
          if driver_problems else [], len(broken_problems)))

    # ---- AC-TSZB4: honest page face, dashes, empty probe.
    dash = labels.get("none", "-")
    marked_scopes = ('data-scope="plain"' in page
                     and 'data-scope="refunded"' in page)
    marked_sellers = all(('data-scope="%s"' % item["seller"]) in page
                         for item in sellers)
    marked_rows = all(('data-month="%s"' % row["month"]) in page
                      for row in rows)
    marked_cats = ('data-category=""' in page)
    zero_scope = [item for item in sellers
                  if int(item["lifetime"]["sale_count"]) == 0]
    dash_zero = bool(zero_scope) and ('<b>%s</b>' % dash in page)
    stand_in = ">None<" in page
    cap_ok = labels.get("bar_caption", "") in page
    bars = page.count('class="bar"')
    expected = sum(1 for row in rows if row["p90_ticket"] is not None)
    laws = [labels.get(key, "") for key in
            ("law_sum", "law_net", "law_mean", "law_band", "law_two_sides",
             "law_sellers", "law_months", "law_running", "law_grid",
             "law_peak", "law_row_band", "law_bar", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    empty_probe_ok = False
    quiet_month_ok = False
    dash_zero = False
    try:
        empty_html = driver.build_html(
            empty_life(), empty_life(refunded=True), [], empty_months(),
            labels, "2026-01-01 00:00:00Z",
            doc.get("disclaimer") or "")
        zero_plain = empty_life(scope="seller")
        zero_plain["dev_account"] = "usr:probe"
        zero_plain["include_refunded"] = True
        empty_probe_ok = (labels.get("empty", "") in empty_html
                          and ">None<" not in empty_html
                          and 'data-month="' not in empty_html
                          and 'class="bar"' not in empty_html)
        scope_html = driver.build_html(
            empty_life(), empty_life(refunded=True),
            [{"seller": "usr:probe", "lifetime": zero_plain,
              "lifetime_plain": zero_plain}], empty_months(), labels,
            "2026-01-01 00:00:00Z", doc.get("disclaimer") or "")
        dash_zero = ('<b>%s</b>' % dash) in scope_html
        zero_row = {"month": "2026-10", "sale_count": 0,
                    "refunded_sale_count": 0, "gross_tokens": 0,
                    "mean_ticket": None, "median_ticket": None,
                    "p90_ticket": None, "running_ticket_tokens": 9}
        zero_block = empty_months()
        zero_block.update({"month_count": 1, "first_month": "2026-10",
                           "last_month": "2026-10", "gross_tokens": 9,
                           "min_ticket": 1, "max_ticket": 9,
                           "months": [zero_row]})
        zero_html = driver.build_html(
            empty_life(), empty_life(refunded=True), [], zero_block, labels,
            "2026-01-01 00:00:00Z", doc.get("disclaimer") or "")
        quiet_section = zero_html.split('data-month="2026-10"', 1)[-1]
        quiet_month_ok = (zero_html.count('class="bar"') == 0
                          and "<td class=\"n\">%s</td>" % dash
                          in quiet_section
                          and labels.get("empty", "") not in quiet_section)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-TSZB4", marked_scopes and marked_sellers and marked_rows
       and marked_cats and dash_zero and not stand_in and cap_ok and laws_ok
       and bars == expected and empty_probe_ok and quiet_month_ok,
       "scopes=%s sellers=%s rows=%s cats=%s dash_zero=%s laws=%s cap=%s "
       "bars=%d/%d empty=%s quiet_month=%s stand_in_none=%s"
       % (marked_scopes, marked_sellers, marked_rows, marked_cats, dash_zero,
          laws_ok, cap_ok, bars, expected, empty_probe_ok, quiet_month_ok,
          stand_in))

    # ---- AC-TSZB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    notadvice = labels.get("law_notadvice", "") in page
    ok("AC-TSZB5", aigc and on_page and external == 0 and notadvice,
       "aigc=%s disclaimer_on_page=%s external_links=%d notadvice=%s"
       % (aigc, on_page, external, notadvice))

    # ---- AC-TSZB6: --check reads clean, writes nothing, wiring intact.
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
        "api_market_ticket_size_months(" in read(FACE_SUITE)
    ok("AC-TSZB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
