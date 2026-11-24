"""Battery suite for tools/seller_rating_months_board.py - AC-SRMB1..6.

WHY THIS SUITE EXISTS (measured at R3427, not assumed):
api_seller_rating_months shipped with its own AC-SRT1..8 criteria
(src/sandbox/ledger/test_apimarket_sellerratingmonths.py on disk) but a git
grep over tools/ and preview/ answered rc=1 with zero hits, so the seller's own
question - "is my rating intake and my star level moving month over month" -
could not be opened by anyone. The reply latency board (R3425) reads the
waiting time and the owed queue, and the seller quality scorecard (R3401) reads
the lifetime star shape; neither shows the month axis with the five bucket
histogram beside it. R3427 renders one market section plus one section per
seller on one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3427 PIN
BEFORE the driver existed):
  AC-SRMB1 the page and its json land, the json carries exactly the pinned
           payload key set, the market block and every seller block carry the
           shipped 20-key envelope, every month row carries the shipped 14
           keys, seller_count equals the block count, the report points at a
           file that exists, and the four source fingerprints are recorded.
  AC-SRMB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates sellers through the shipped board
           face, reads api_seller_rating_months() once for the market and once
           per seller, and requires the page json's market and sellers
           (including every month row and the disclaimer) to equal that reading
           item for item - no typed fixture.
  AC-SRMB3 the face's identities hold: month count equals the row count, the
           active month count is the months with ratings, the rating total is
           the row sum and the last running accumulator, the star sum, five
           star count, low star count and replied count each recompute over
           the rows, the pooled average and the coverage recompute and are None
           rather than a fabricated zero when the denominator is zero, the peak
           month is the first largest non-zero month, the first and last months
           and the latest month count match the grid, every month row's five
           buckets sum to its rating count, its low count is the two and one
           buckets, its average and coverage recompute, the running accumulator
           is monotone and equals its prefix, the months ascend and are
           YYYY-MM, the market envelope carries no seller account and no
           self-benchmark, and a seller envelope carries the pooled market
           average.
  AC-SRMB4 the page reads honestly: one market section and one marked section
           per seller, one marked row per month, an undefined average or
           coverage printed as the dash instead of a zero, the peak month
           carrying its named badge, no bare None, a count bar the page calls a
           width and not a share - proved by two in-memory probes: an empty
           scope printing the dash and the explicit empty sentence, and a two
           month envelope printing both bars and its peak badge.
  AC-SRMB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-SRMB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with AC-SRT arms.

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
TOOL = os.path.join(ROOT, "tools", "seller_rating_months_board.py")
HTML = os.path.join(ROOT, "preview", "seller-rating-months-board.html")
JSONF = os.path.join(ROOT, "preview", "seller-rating-months-board.json")
COPY = os.path.join(ROOT, "preview", "seller-rating-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_sellerratingmonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-rating-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "scope", "seller_count",
    "market", "sellers", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "scope", "dev_account", "month_count", "active_month_count",
    "rating_count", "buyer_count", "star_sum", "avg_stars",
    "five_star_count", "low_star_count", "replied_count", "reply_coverage",
    "peak_month", "peak_rating_count", "first_month", "last_month",
    "latest_month_rating_count", "months", "market_avg_stars", "disclaimer",
}
ROW_KEYS = {
    "month", "rating_count", "buyer_count", "star_sum", "avg_stars",
    "five_star_count", "four_star_count", "three_star_count",
    "two_star_count", "one_star_count", "low_star_count", "replied_count",
    "reply_coverage", "running_rating",
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


def live_world():
    """The shipped face's own reading over the suite's throwaway demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="srmb-suite-")
    db = os.path.join(tmp_root, "srmb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        sellers = sorted({str(row["dev_account"]) for row in board["listings"]})
        market = dict(am.api_seller_rating_months())
        scoped = [dict(am.api_seller_rating_months(seller))
                  for seller in sellers]
        return market, scoped, market["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("srmb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def want_avg(star_sum, count):
    if not count:
        return None
    return round(float(star_sum) / float(count), 2)


def want_coverage(replied, count):
    if not count:
        return None
    return round(float(replied) / float(count), 4)


def envelope_problems(envelope, label):
    problems = []
    rows = envelope["months"]
    count = int(envelope["rating_count"])
    if int(envelope["month_count"]) != len(rows):
        problems.append("%s month_count" % label)
    active = sum(1 for row in rows if int(row["rating_count"]) > 0)
    if int(envelope["active_month_count"]) != active:
        problems.append("%s active_month_count" % label)
    row_sum = sum(int(row["rating_count"]) for row in rows)
    if count != row_sum:
        problems.append("%s rating_count" % label)
    running = 0
    for row in rows:
        running += int(row["rating_count"])
        if int(row["running_rating"]) != running:
            problems.append("%s running_rating %s" % (label, row["month"]))
    if rows and int(rows[-1]["running_rating"]) != count:
        problems.append("%s last running" % label)
    star_sum = sum(int(row["star_sum"]) for row in rows)
    if int(envelope["star_sum"]) != star_sum:
        problems.append("%s star_sum" % label)
    if not close(envelope["avg_stars"], want_avg(star_sum, count)):
        problems.append("%s avg_stars" % label)
    for column in ("five_star_count", "low_star_count", "replied_count"):
        if int(envelope[column]) != sum(int(row[column]) for row in rows):
            problems.append("%s %s" % (label, column))
    if not close(envelope["reply_coverage"],
                 want_coverage(int(envelope["replied_count"]), count)):
        problems.append("%s reply_coverage" % label)
    peak_month = None
    peak_count = None
    for row in rows:
        value = int(row["rating_count"])
        if value > 0 and (peak_count is None or value > peak_count):
            peak_month = row["month"]
            peak_count = value
    if envelope["peak_month"] != peak_month:
        problems.append("%s peak_month" % label)
    if envelope["peak_rating_count"] != peak_count:
        problems.append("%s peak_rating_count" % label)
    if envelope["first_month"] != (rows[0]["month"] if rows else None):
        problems.append("%s first_month" % label)
    if envelope["last_month"] != (rows[-1]["month"] if rows else None):
        problems.append("%s last_month" % label)
    want_latest = int(rows[-1]["rating_count"]) if rows else 0
    if int(envelope["latest_month_rating_count"]) != want_latest:
        problems.append("%s latest_month_rating_count" % label)
    previous = None
    for row in rows:
        month = str(row["month"])
        if len(month) != 7 or month[4] != "-":
            problems.append("%s month shape %r" % (label, month))
        elif previous is not None and month <= previous:
            problems.append("%s month order %r" % (label, month))
        previous = month
        row_count = int(row["rating_count"])
        buckets = sum(int(row[key]) for key in (
            "five_star_count", "four_star_count", "three_star_count",
            "two_star_count", "one_star_count"))
        if buckets != row_count:
            problems.append("%s %s buckets" % (label, month))
        if int(row["low_star_count"]) != (int(row["two_star_count"])
                                          + int(row["one_star_count"])):
            problems.append("%s %s low_star_count" % (label, month))
        if not close(row["avg_stars"],
                     want_avg(int(row["star_sum"]), row_count)):
            problems.append("%s %s avg_stars" % (label, month))
        if not close(row["reply_coverage"],
                     want_coverage(int(row["replied_count"]), row_count)):
            problems.append("%s %s reply_coverage" % (label, month))
    return problems


def zero_envelope():
    return {
        "scope": "market", "dev_account": None, "month_count": 0,
        "active_month_count": 0, "rating_count": 0, "buyer_count": 0,
        "star_sum": 0, "avg_stars": None, "five_star_count": 0,
        "low_star_count": 0, "replied_count": 0, "reply_coverage": None,
        "peak_month": None, "peak_rating_count": None, "first_month": None,
        "last_month": None, "latest_month_rating_count": 0, "months": [],
        "market_avg_stars": None, "disclaimer": "probe disclaimer",
    }


def answered_envelope():
    rows = [
        {"month": "2026-01", "rating_count": 2, "buyer_count": 2,
         "star_sum": 9, "avg_stars": 4.5, "five_star_count": 1,
         "four_star_count": 1, "three_star_count": 0, "two_star_count": 0,
         "one_star_count": 0, "low_star_count": 0, "replied_count": 2,
         "reply_coverage": 1.0, "running_rating": 2},
        {"month": "2026-02", "rating_count": 1, "buyer_count": 1,
         "star_sum": 3, "avg_stars": 3.0, "five_star_count": 0,
         "four_star_count": 0, "three_star_count": 1, "two_star_count": 0,
         "one_star_count": 0, "low_star_count": 0, "replied_count": 0,
         "reply_coverage": 0.0, "running_rating": 3},
    ]
    return {
        "scope": "market", "dev_account": None, "month_count": 2,
        "active_month_count": 2, "rating_count": 3, "buyer_count": 3,
        "star_sum": 12, "avg_stars": 4.0, "five_star_count": 1,
        "low_star_count": 0, "replied_count": 2, "reply_coverage": 0.6667,
        "peak_month": "2026-01", "peak_rating_count": 2,
        "first_month": "2026-01", "last_month": "2026-02",
        "latest_month_rating_count": 1, "months": rows,
        "market_avg_stars": None, "disclaimer": "probe disclaimer",
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    market = doc.get("market") or {}
    sellers = doc.get("sellers") or []
    all_rows = list(market.get("months") or []) + [
        row for block in sellers for row in (block.get("months") or [])]

    # ---- AC-SRMB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelopes_ok = (set(market.keys()) == ENVELOPE_KEYS
                    and all(set(block.keys()) == ENVELOPE_KEYS
                            for block in sellers))
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in all_rows)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-SRMB1", landed and keys == PAYLOAD_KEYS and envelopes_ok and rows_ok
       and sources_ok and bool(sellers)
       and int(doc.get("seller_count", -1)) == len(sellers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelopes=%s rows=%s "
       "sources=%s count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelopes_ok, rows_ok, sources_ok,
          len(sellers), int(doc.get("seller_count", -1)), report_ok))

    # ---- AC-SRMB2: every printed number is the shipped face's own.
    live_market, live_sellers, live_disclaimer = live_world()
    market_same = json.dumps(market, sort_keys=True) == json.dumps(
        {key: live_market[key] for key in ENVELOPE_KEYS}, sort_keys=True)
    sellers_same = json.dumps(sellers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in ENVELOPE_KEYS} for block in live_sellers],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    live_rows = len(live_market["months"]) + sum(
        len(block["months"]) for block in live_sellers)
    ok("AC-SRMB2", market_same and sellers_same and disc_same and bool(sellers),
       "market_same=%s sellers_same=%s disclaimer_same=%s sellers=%d rows=%d"
       % (market_same, sellers_same, disc_same, len(sellers), live_rows))

    # ---- AC-SRMB3: the face's identities hold on these envelopes.
    problems = envelope_problems(market, "market") if market else ["no market"]
    if market:
        if market.get("dev_account") is not None:
            problems.append("market dev_account")
        if market.get("market_avg_stars") is not None:
            problems.append("market self benchmark")
    for block in sellers:
        name = str(block["dev_account"])
        problems.extend(envelope_problems(block, name))
        if not name.startswith("usr:"):
            problems.append("%s account" % name)
        if block.get("scope") != "seller":
            problems.append("%s scope" % name)
        if not close(block.get("market_avg_stars"), market.get("avg_stars")):
            problems.append("%s market_avg_stars" % name)
    ok("AC-SRMB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-SRMB4: honest page face, dashes, width bar, two probes.
    dash = labels.get("none", "-")
    sellers_marked = all(('data-seller="%s"' % block["dev_account"]) in page
                         for block in sellers)
    rows_marked = all(('data-month="%s"' % row["month"]) in page
                      for row in all_rows)
    active_rows = [row for row in all_rows if int(row["rating_count"]) > 0]
    peak_badges = page.count(labels.get("badge_peak", "")) >= len(active_rows)
    landed_bars = page.count("<div class=bar>")
    bars_honest = landed_bars == len(active_rows)
    no_none = ">None<" not in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_grid", "law_pooled", "law_hist", "law_lowstar",
             "law_coverage", "law_peak", "law_running", "law_distinct",
             "law_scope", "law_bar", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    zero_ok = answered_ok = False
    try:
        driver = load_driver()
        zero_html = driver.build_html(zero_envelope(), [], labels,
                                      "2026-01-01 00:00:00Z",
                                      "probe disclaimer")
        zero_ok = (zero_html.count("<div class=bar>") == 0
                   and ">None<" not in zero_html
                   and dash in zero_html
                   and labels.get("empty_scope", "") in zero_html)
        answered_html = driver.build_html(answered_envelope(), [], labels,
                                          "2026-01-01 00:00:00Z",
                                          "probe disclaimer")
        answered_ok = (answered_html.count("<div class=bar>") == 2
                       and "4.5" in answered_html
                       and "1.0" in answered_html
                       and ">None<" not in answered_html
                       and labels.get("badge_peak", "") in answered_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-SRMB4", sellers_marked and rows_marked and peak_badges
       and bars_honest and no_none and laws_ok and zero_ok and answered_ok,
       "sellers=%s rows=%s peak_badges=%s bars=%d/%d laws=%s zero_probe=%s "
       "answered_probe=%s bare_none=%s"
       % (sellers_marked, rows_marked, peak_badges, landed_bars, len(active_rows),
          laws_ok, zero_ok, answered_ok, not no_none))

    # ---- AC-SRMB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-SRMB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-SRMB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-SRT" in read(FACE_SUITE)
    ok("AC-SRMB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
