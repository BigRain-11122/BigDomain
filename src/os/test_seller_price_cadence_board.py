"""Battery suite for tools/seller_price_cadence_board.py - AC-SPCB1..6.

WHY THIS SUITE EXISTS (measured at R3442, not assumed):
api_seller_price_cadence_months shipped as the monthly repricing cadence - the
step attribution law, the pooled magnitude, the contiguous month grid, the
monotone accumulator and the two scopes - but a search over tools/, preview/
and src/os answered rc=1 with zero hits. The market already had two lifetime
repricing faces (api_price_volatility and api_price_step_distribution), both
whole-history scalars, so a seller that repriced twelve times in one month and
then went silent for a quarter read exactly like one that adjusted once a
month for a year. R3442 renders the shipped envelopes on one page; this suite
grades the page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3442 PIN row was filed at closeout and carries
an honesty note saying the row landed after the driver):
  AC-SPCB1 the page and its json land, the json carries exactly the pinned
           22-key payload set, every month row carries the shipped 9 keys,
           every seller scope the shipped 17 keys, month_count equals the row
           count, and the report points at a file that exists.
  AC-SPCB2 the data is the shipped face's own: the suite builds its own
           throwaway world through the driver's shipped-door fixture and
           requires the page json market envelope and every seller scope to
           equal a fresh api_seller_price_cadence_months() reading item for
           item, disclaimer and month order included.
  AC-SPCB3 the face's identities hold: up+down equals the revision count and
           net equals the difference per row, months are contiguous with the
           honest zero row, running_revision is monotone and ends at the
           envelope total, the monthly average exists exactly when the month
           repriced, the pooled envelope average sits inside the monthly range
           it pools, the peak is the earliest maximum month, the distinct
           listing count is bounded by the row counts, and the seller scope
           carries the market benchmark while the market scope carries none.
  AC-SPCB4 the page reads honestly: one marked scope card, one marked row per
           month, the dash where the face has nothing, no bare None, the bar
           caption on the page, a bar only on months that repriced, and an
           empty envelope plus a synthetic zero-month scope handed to the
           driver's own renderer print the honest empty sentence and a
           barless dash row (in-memory probes only).
  AC-SPCB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer verbatim, the non-advice sentence, zero
           external links.
  AC-SPCB6 no older criterion is relaxed: the landed pair answers its own
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
TOOL = os.path.join(ROOT, "tools", "seller_price_cadence_board.py")
HTML = os.path.join(ROOT, "preview", "seller-price-cadence-board.html")
JSONF = os.path.join(ROOT, "preview", "seller-price-cadence-board.json")
COPY = os.path.join(ROOT, "preview", "seller-price-cadence-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_sellerpricecadencemonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-price-cadence-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "month_count", "active_month_count",
    "revision_count", "up_count", "down_count", "listing_count",
    "seller_count", "avg_abs_step_pct", "peak_month", "peak_revision_count",
    "first_month", "last_month", "latest_month_revision_count",
    "market_avg_abs_step_pct", "months", "sellers", "disclaimer", "report",
    "sources", "sizes",
}
ROW_KEYS = {
    "month", "revision_count", "up_count", "down_count", "net_count",
    "listing_count", "seller_count", "avg_abs_step_pct",
    "running_revision",
}
SCOPE_KEYS = {
    "dev_account", "scope", "month_count", "active_month_count",
    "revision_count", "up_count", "down_count", "listing_count",
    "seller_count", "avg_abs_step_pct", "peak_month", "peak_revision_count",
    "first_month", "last_month", "latest_month_revision_count",
    "market_avg_abs_step_pct", "months",
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
    spec = importlib.util.spec_from_file_location("spcb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_world(driver):
    """The shipped readings over this suite's own throwaway world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="spcb-suite-")
    db = os.path.join(tmp_root, "spcb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        driver.seed_world(am)
        market = dict(am.api_seller_price_cadence_months())
        sellers = sorted({row["dev_account"]
                          for row in (am.api_public_listings() or {})
                          .get("listings") or []})
        scopes = [dict(am.api_seller_price_cadence_months(seller))
                  for seller in sellers]
        return market, scopes
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def identity_problems(envelope, pooled):
    problems = []
    months = envelope.get("months") or []
    tag = "scope %s" % (envelope.get("dev_account") or "market")
    if int(envelope.get("month_count", -1)) != len(months):
        problems.append("%s month_count" % tag)
    seen = [row["month"] for row in months]
    if seen != sorted(seen):
        problems.append("%s months not ascending" % tag)
    for index in range(1, len(seen)):
        year, month = int(seen[index - 1][:4]), int(seen[index - 1][5:7])
        month += 1
        if month > 12:
            month = 1
            year += 1
        if "%04d-%02d" % (year, month) != seen[index]:
            problems.append("%s gap after %s" % (tag, seen[index - 1]))
    revisions = up = down = 0
    lists_sum = lists_max = 0
    avgs = []
    for row in months:
        count = int(row["revision_count"])
        row_up = int(row["up_count"])
        row_down = int(row["down_count"])
        if row_up + row_down != count:
            problems.append("%s %s count split" % (tag, row["month"]))
        if int(row["net_count"]) != row_up - row_down:
            problems.append("%s %s net" % (tag, row["month"]))
        if count == 0 and row["avg_abs_step_pct"] is not None:
            problems.append("%s %s zero average" % (tag, row["month"]))
        if count and row["avg_abs_step_pct"] is None:
            problems.append("%s %s missing average" % (tag, row["month"]))
        if count and int(row["listing_count"]) < 1:
            problems.append("%s %s listing count" % (tag, row["month"]))
        if row["avg_abs_step_pct"] is not None:
            avgs.append(abs(float(row["avg_abs_step_pct"])))
        revisions += count
        up += row_up
        down += row_down
        lists_sum += int(row["listing_count"])
        lists_max = max(lists_max, int(row["listing_count"]))
    if months:
        running = [int(row["running_revision"]) for row in months]
        if running != sorted(running):
            problems.append("%s running not monotone" % tag)
        if running[-1] != int(envelope.get("revision_count", -1)):
            problems.append("%s running does not end at the total" % tag)
        if envelope.get("first_month") != months[0]["month"]:
            problems.append("%s first_month" % tag)
        if envelope.get("last_month") != months[-1]["month"]:
            problems.append("%s last_month" % tag)
        distinct = int(envelope.get("listing_count", -1))
        if not (lists_max <= distinct <= lists_sum):
            problems.append("%s listing bound" % tag)
        best = max(int(row["revision_count"]) for row in months)
        if best > 0:
            first = [row["month"] for row in months
                     if int(row["revision_count"]) == best][0]
            if envelope.get("peak_month") != first:
                problems.append("%s peak month" % tag)
        elif envelope.get("peak_month") is not None:
            problems.append("%s peak on all-zero scope" % tag)
    if revisions != int(envelope.get("revision_count", -1)):
        problems.append("%s revision total" % tag)
    if up != int(envelope.get("up_count", -1)):
        problems.append("%s up total" % tag)
    if down != int(envelope.get("down_count", -1)):
        problems.append("%s down total" % tag)
    avg = envelope.get("avg_abs_step_pct")
    if avgs:
        if avg is None or not (min(avgs) - 0.005 <= float(avg)
                               <= max(avgs) + 0.005):
            problems.append("%s pooled average outside the range" % tag)
    elif avg is not None:
        problems.append("%s average with zero steps" % tag)
    if envelope.get("scope") == "market":
        if envelope.get("market_avg_abs_step_pct") is not None:
            problems.append("%s market self-benchmark" % tag)
    elif envelope.get("market_avg_abs_step_pct") != pooled:
        problems.append("%s market benchmark" % tag)
    return problems


def probe_empty():
    return {
        "dev_account": None, "scope": "market", "month_count": 0,
        "active_month_count": 0, "revision_count": 0, "up_count": 0,
        "down_count": 0, "listing_count": 0, "seller_count": 0,
        "avg_abs_step_pct": None, "peak_month": None,
        "peak_revision_count": None, "first_month": None, "last_month": None,
        "latest_month_revision_count": None, "market_avg_abs_step_pct": None,
        "disclaimer": "sandbox stand-in disclaimer", "months": [],
    }


def probe_zero_scope():
    moved = {
        "month": "2026-09", "revision_count": 2, "up_count": 1,
        "down_count": 1, "net_count": 0, "listing_count": 2,
        "seller_count": 1, "avg_abs_step_pct": 12.5, "running_revision": 2,
    }
    quiet = {
        "month": "2026-10", "revision_count": 0, "up_count": 0,
        "down_count": 0, "net_count": 0, "listing_count": 0,
        "seller_count": 0, "avg_abs_step_pct": None, "running_revision": 2,
    }
    return {
        "dev_account": "usr:probe", "scope": "seller", "month_count": 2,
        "active_month_count": 1, "revision_count": 2, "up_count": 1,
        "down_count": 1, "listing_count": 2, "seller_count": 1,
        "avg_abs_step_pct": 12.5, "peak_month": "2026-09",
        "peak_revision_count": 2, "first_month": "2026-09",
        "last_month": "2026-10", "latest_month_revision_count": 0,
        "market_avg_abs_step_pct": 12.5,
        "disclaimer": "sandbox stand-in disclaimer",
        "months": [moved, quiet],
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    months = doc.get("months") or []
    sellers = doc.get("sellers") or []

    # ---- AC-SPCB1: the pair landed with exactly the pinned key sets.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    market_months = doc.get("months") or []
    sellers_rows_ok = all(
        set(scope.keys()) == SCOPE_KEYS
        and all(set(row.keys()) == ROW_KEYS for row in scope["months"])
        for scope in sellers)
    market_rows_ok = all(set(row.keys()) == ROW_KEYS
                         for row in market_months)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-SPCB1", landed and keys == PAYLOAD_KEYS and market_rows_ok
       and sellers_rows_ok and int(doc.get("month_count", -1))
       == len(market_months) and report_ok and sources_ok,
       "landed=%s keys=%d missing=%s extra=%s rows=%s seller_rows=%s "
       "count=%d/%d sellers=%d report=%s sources=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), market_rows_ok, sellers_rows_ok,
          len(market_months), int(doc.get("month_count", -1)), len(sellers),
          report_ok, sources_ok))

    # ---- AC-SPCB2: every printed value is the shipped face's own.
    driver = load_driver()
    live_market, live_scopes = live_world(driver)
    bounds = ("scope", "month_count", "active_month_count", "revision_count",
              "up_count", "down_count", "listing_count", "seller_count",
              "avg_abs_step_pct", "peak_month", "peak_revision_count",
              "first_month", "last_month",
              "latest_month_revision_count")
    market_same = all(doc.get(key) == live_market.get(key) for key in bounds)
    market_months_same = json.dumps(market_months, sort_keys=True) == \
        json.dumps([{key: row[key] for key in ROW_KEYS}
                    for row in live_market.get("months") or []],
                   sort_keys=True)
    live_by_name = {scope["dev_account"]: scope for scope in live_scopes}
    sellers_same = len(sellers) == len(live_scopes) and all(
        live_by_name.get(scope["dev_account"]) is not None
        and all(scope.get(key) == live_by_name[scope["dev_account"]][key]
                for key in SCOPE_KEYS)
        for scope in sellers)
    disc_same = doc.get("disclaimer") == live_market.get("disclaimer")
    ok("AC-SPCB2", market_same and market_months_same and sellers_same
       and disc_same and bool(months) and bool(sellers),
       "market_same=%s months_same=%s sellers_same=%s disclaimer_same=%s "
       "months=%d sellers=%d"
       % (market_same, market_months_same, sellers_same, disc_same,
          len(months), len(sellers)))

    # ---- AC-SPCB3: the face's identities and this page's own laws hold.
    pooled = doc.get("avg_abs_step_pct")
    problems = identity_problems(doc, None) if months else ["no months"]
    for scope in sellers:
        problems.extend(identity_problems(scope, pooled))
    law_problems = driver.check_laws(doc, sellers) if months else ["no months"]
    ok("AC-SPCB3", not problems and not law_problems,
       "problems=%s driver_laws=%s"
       % (problems[:4] if problems else [], law_problems[:3]
          if law_problems else []))

    # ---- AC-SPCB4: honest page face, dashes, empty and zero probes.
    dash = labels.get("none", "-")
    marked_scopes = ('data-scope="market"' in page) and all(
        ('data-scope="%s"' % scope["dev_account"]) in page
        for scope in sellers)
    marked_rows = all(('data-month="%s"' % row["month"]) in page
                      for row in months)
    zero_months = [row for scope in [doc] + sellers
                   for row in scope.get("months") or []
                   if int(row["revision_count"]) == 0]
    dash_zero = bool(zero_months) and ('<td class="n">%s</td>' % dash in page)
    stand_in = ">None<" in page
    cap_ok = labels.get("bar_caption", "") in page
    bars = page.count('class="bar"')
    expected_bars = sum(1 for scope in [doc] + sellers
                        for row in scope.get("months") or []
                        if row["avg_abs_step_pct"] is not None)
    laws = [labels.get(key, "") for key in
            ("law_count", "law_step", "law_window", "law_running", "law_pool",
             "law_peak", "law_scope", "law_distinct", "law_nosame", "law_bar",
             "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    empty_probe_ok = False
    zero_probe_ok = False
    try:
        empty_html = driver.build_html(probe_empty(), [], labels,
                                       "2026-01-01 00:00:00Z",
                                       doc.get("disclaimer") or "")
        empty_probe_ok = (labels.get("empty", "") in empty_html
                          and ">None<" not in empty_html
                          and 'data-month="' not in empty_html)
        zero_html = driver.build_html(probe_zero_scope(), [], labels,
                                      "2026-01-01 00:00:00Z",
                                      doc.get("disclaimer") or "")
        quiet_section = zero_html.split('data-month="2026-10"', 1)[-1]
        zero_probe_ok = (zero_html.count('class="bar"') == 1
                         and "<td class=\"n\">%s</td>" % dash in quiet_section
                         and ">None<" not in zero_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-SPCB4", marked_scopes and marked_rows and dash_zero
       and not stand_in and cap_ok and laws_ok and bars == expected_bars
       and empty_probe_ok and zero_probe_ok,
       "scopes=%s rows=%s dash_zero=%s laws=%s cap=%s bars=%d/%d empty=%s "
       "zero=%s stand_in_none=%s"
       % (marked_scopes, marked_rows, dash_zero, laws_ok, cap_ok, bars,
          expected_bars, empty_probe_ok, zero_probe_ok, stand_in))

    # ---- AC-SPCB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    notadvice = labels.get("law_notadvice", "") in page
    ok("AC-SPCB5", aigc and on_page and external == 0 and notadvice,
       "aigc=%s disclaimer_on_page=%s external_links=%d notadvice=%s"
       % (aigc, on_page, external, notadvice))

    # ---- AC-SPCB6: --check reads clean, writes nothing, wiring intact.
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
        "api_seller_price_cadence_months(" in read(FACE_SUITE)
    ok("AC-SPCB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
