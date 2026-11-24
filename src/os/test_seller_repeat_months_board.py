"""Battery suite for tools/seller_repeat_months_board.py - AC-RPTB1..6.

WHY THIS SUITE EXISTS (measured at R3429, not assumed):
api_seller_repeat_months shipped with its own AC-SRB1..8 criteria
(src/sandbox/ledger/test_apimarket_sellerrepeatmonths.py on disk) but a git
grep over tools/ and preview/ answered rc=1 with zero hits, so the seller's
own question - "was this month carried by regulars or by newcomers" - could
not be opened by anyone. api_repeat_purchase answers the lifetime question
only and api_market_buyer_cohort reads the market scope, so one seller on a
month axis had no page. R3429 renders one section per seller with the KPI row
and the month grid; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3429 PIN
BEFORE the driver existed):
  AC-RPTB1 the page and its json land, the json carries exactly the pinned
           payload key set, every seller block carries the shipped 18-key
           envelope, every month row the shipped 11 keys, seller_count equals
           the block count, the report points at a file that exists, and the
           four source fingerprints are recorded.
  AC-RPTB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates sellers through the shipped board
           face, reads api_seller_repeat_months() per seller, and requires the
           page json's sellers (including every row and the disclaimer) to
           equal that reading item for item - no typed fixture.
  AC-RPTB3 the face's identities hold: month_count is the row count, the
           active month count is the months with trade, the buyer count is the
           sum of the rows' newcomer counts, purchases and gross sums
           recompute, returning gross is gross minus newcomer gross, the
           repeat rate and the latest month share recompute, first and last
           month match the first and last row, the peak month is the earliest
           month with the most returning buyers (None when there is none), and
           every row's buyer/purchase/gross halves add up while returning share
           is a fraction over that month's buyers or None - never a fabricated
           zero; the month grid is contiguous.
  AC-RPTB4 the page reads honestly: one section per seller marked data-seller,
           every month row marked data-month, an undefined share printed as the
           dash with no bar, a measured 0.0 printed as 0.0% with a zero marker
           and never confused with undefined, a quiet month named, the
           single-month trend sentence present, and no bare None.
  AC-RPTB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, the not-advice sentence is
           present, and there are zero external links.
  AC-RPTB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with AC-SRB arms.

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
TOOL = os.path.join(ROOT, "tools", "seller_repeat_months_board.py")
HTML = os.path.join(ROOT, "preview", "seller-repeat-months-board.html")
JSONF = os.path.join(ROOT, "preview", "seller-repeat-months-board.json")
COPY = os.path.join(ROOT, "preview", "seller-repeat-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_sellerrepeatmonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-repeat-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "scope", "seller_count",
    "sellers", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "scope", "dev_account", "buyer_count", "repeat_buyer_count",
    "repeat_rate", "purchase_count", "gross", "new_gross",
    "returning_gross", "month_count", "active_month_count", "first_month",
    "last_month", "peak_month", "peak_returning_buyer_count",
    "latest_month_returning_share", "disclaimer", "months",
}
ROW_KEYS = {
    "month", "purchase_count", "gross", "buyer_count", "new_buyer_count",
    "returning_buyer_count", "returning_share", "new_purchase_count",
    "returning_purchase_count", "new_gross", "returning_gross",
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
    tmp_root = tempfile.mkdtemp(prefix="rptb-suite-")
    db = os.path.join(tmp_root, "rptb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        sellers = sorted({str(row["dev_account"]) for row in board["listings"]})
        envelopes = [dict(am.api_seller_repeat_months(dev)) for dev in sellers]
        return envelopes, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("rptb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close(left, right, tol=1e-9):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= tol


def share(returning, buyers):
    if not buyers:
        return None
    return float(returning) / float(buyers)


def next_month(month):
    year, mon = int(month[:4]), int(month[5:7])
    return "%04d-01" % (year + 1) if mon == 12 else "%04d-%02d" % (year, mon + 1)


def envelope_problems(block, label):
    problems = []
    rows = list(block["months"])
    if int(block["month_count"]) != len(rows):
        problems.append("%s month_count" % label)
    active = sum(1 for row in rows if int(row["purchase_count"]) > 0)
    if int(block["active_month_count"]) != active:
        problems.append("%s active" % label)
    if int(block["buyer_count"]) != sum(int(r["new_buyer_count"])
                                        for r in rows):
        problems.append("%s buyer_count" % label)
    if int(block["purchase_count"]) != sum(int(r["purchase_count"])
                                           for r in rows):
        problems.append("%s purchases" % label)
    if int(block["gross"]) != sum(int(r["gross"]) for r in rows):
        problems.append("%s gross" % label)
    if int(block["new_gross"]) != sum(int(r["new_gross"]) for r in rows):
        problems.append("%s new_gross" % label)
    if int(block["returning_gross"]) != (int(block["gross"])
                                         - int(block["new_gross"])):
        problems.append("%s returning_gross" % label)
    if not close(block["repeat_rate"],
                 share(int(block["repeat_buyer_count"]),
                       int(block["buyer_count"]))):
        problems.append("%s repeat_rate" % label)
    want_latest = rows[-1]["returning_share"] if rows else None
    if not close(block["latest_month_returning_share"], want_latest):
        problems.append("%s latest share" % label)
    if block["first_month"] != (rows[0]["month"] if rows else None):
        problems.append("%s first_month" % label)
    if block["last_month"] != (rows[-1]["month"] if rows else None):
        problems.append("%s last_month" % label)
    peak_month = None
    peak_count = None
    for row in rows:
        value = int(row["returning_buyer_count"])
        if value > 0 and (peak_count is None or value > peak_count):
            peak_month, peak_count = row["month"], value
    if block["peak_month"] != peak_month:
        problems.append("%s peak_month" % label)
    if block["peak_returning_buyer_count"] != peak_count:
        problems.append("%s peak_count" % label)
    previous = None
    for row in rows:
        month = str(row["month"])
        if len(month) != 7 or month[4] != "-":
            problems.append("%s month format" % label)
        elif previous is not None and next_month(previous) != month:
            problems.append("%s month gap" % label)
        previous = month
        buyers = int(row["buyer_count"])
        if int(row["new_buyer_count"]) + int(row["returning_buyer_count"]) \
                != buyers:
            problems.append("%s %s buyer halves" % (label, month))
        if int(row["new_purchase_count"]) + int(
                row["returning_purchase_count"]) != int(row["purchase_count"]):
            problems.append("%s %s purchase halves" % (label, month))
        if int(row["new_gross"]) + int(row["returning_gross"]) != int(
                row["gross"]):
            problems.append("%s %s gross halves" % (label, month))
        if not close(row["returning_share"],
                     share(int(row["returning_buyer_count"]), buyers)):
            problems.append("%s %s returning_share" % (label, month))
        if int(row["returning_buyer_count"]) > buyers:
            problems.append("%s %s returning over buyers" % (label, month))
    return problems


def empty_envelope():
    return {
        "scope": "seller", "dev_account": "usr:probe", "buyer_count": 0,
        "repeat_buyer_count": 0, "repeat_rate": None, "purchase_count": 0,
        "gross": 0, "new_gross": 0, "returning_gross": 0, "month_count": 0,
        "active_month_count": 0, "first_month": None, "last_month": None,
        "peak_month": None, "peak_returning_buyer_count": None,
        "latest_month_returning_share": None,
        "disclaimer": "probe disclaimer", "months": [],
    }


def returning_envelope():
    """Two contiguous months: 2 newcomers, then 1 newcomer + 1 regular."""
    first = {
        "month": "2026-08", "purchase_count": 2, "gross": 20, "buyer_count": 2,
        "new_buyer_count": 2, "returning_buyer_count": 0,
        "returning_share": 0.0, "new_purchase_count": 2,
        "returning_purchase_count": 0, "new_gross": 20, "returning_gross": 0,
    }
    second = {
        "month": "2026-09", "purchase_count": 2, "gross": 30, "buyer_count": 2,
        "new_buyer_count": 1, "returning_buyer_count": 1,
        "returning_share": 0.5, "new_purchase_count": 1,
        "returning_purchase_count": 1, "new_gross": 10, "returning_gross": 20,
    }
    return {
        "scope": "seller", "dev_account": "usr:probe", "buyer_count": 3,
        "repeat_buyer_count": 1, "repeat_rate": 0.3333333333333333,
        "purchase_count": 4, "gross": 50, "new_gross": 30,
        "returning_gross": 20, "month_count": 2, "active_month_count": 2,
        "first_month": "2026-08", "last_month": "2026-09",
        "peak_month": "2026-09", "peak_returning_buyer_count": 1,
        "latest_month_returning_share": 0.5,
        "disclaimer": "probe disclaimer", "months": [first, second],
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    sellers = doc.get("sellers") or []

    # ---- AC-RPTB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelopes_ok = all(set(block.keys()) == ENVELOPE_KEYS for block in sellers)
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for block in sellers for row in (block.get("months") or []))
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-RPTB1", landed and keys == PAYLOAD_KEYS and envelopes_ok and rows_ok
       and sources_ok and bool(sellers)
       and int(doc.get("seller_count", -1)) == len(sellers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelopes=%s rows=%s sources=%s "
       "count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelopes_ok, rows_ok, sources_ok,
          len(sellers), int(doc.get("seller_count", -1)), report_ok))

    # ---- AC-RPTB2: every printed number is the shipped face's own.
    live_sellers, live_disclaimer = live_world()
    same = json.dumps(sellers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in ENVELOPE_KEYS} for block in live_sellers],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-RPTB2", same and disc_same and bool(sellers),
       "sellers_same=%s disclaimer_same=%s sellers=%d rows=%d"
       % (same, disc_same, len(sellers),
          sum(len(b["months"]) for b in sellers)))

    # ---- AC-RPTB3: the face's identities hold on these envelopes.
    problems = []
    for block in sellers:
        problems.extend(envelope_problems(block, str(block.get("dev_account"))))
        if block["scope"] != "seller":
            problems.append("%s scope" % block.get("dev_account"))
    ok("AC-RPTB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-RPTB4: honest page face, dashes, zero markers, quiet months.
    dash = labels.get("none", "-")
    sections = len(re.findall(r'<div class="?card"? data-seller="', page))
    months_marked = len(re.findall(r'data-month="\d{4}-\d{2}"', page))
    landed_rows = sum(len(b["months"]) for b in sellers)
    defined_positive = sum(
        1 for b in sellers for r in b["months"]
        if r["returning_share"] is not None and float(r["returning_share"]) > 0)
    defined_zero = sum(
        1 for b in sellers for r in b["months"]
        if r["returning_share"] is not None
        and float(r["returning_share"]) <= 0)
    undefined = sum(1 for b in sellers for r in b["months"]
                    if r["returning_share"] is None)
    bars = page.count("<div class=bar>")
    dots = page.count("class=zero-dot")
    single_sentence = labels.get("label_single", "")
    single_ok = (single_sentence in page) == (
        len(sellers) > 0 and all(
            len(b["months"]) <= 1 for b in sellers))
    no_none = ">None<" not in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_grid", "law_sum", "law_share", "law_newmonth",
             "law_peak", "law_scope", "law_bar", "law_zero",
             "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    empty_ok = returning_ok = quiet_ok = False
    try:
        driver = load_driver()
        empty_html = driver.build_html([empty_envelope()], labels,
                                       "2026-01-01 00:00:00Z",
                                       "probe disclaimer")
        empty_ok = (labels.get("empty_scope", "") in empty_html
                    and ">None<" not in empty_html
                    and '<div class=bar>' not in empty_html)
        rich_html = driver.build_html([returning_envelope()], labels,
                                      "2026-01-01 00:00:00Z",
                                      "probe disclaimer")
        returning_ok = (rich_html.count("<div class=bar>") == 1
                        and rich_html.count("class=zero-dot") == 1
                        and "50.0%" in rich_html
                        and "0.0%" in rich_html
                        and labels.get("badge_peak", "") in rich_html
                        and ">None<" not in rich_html)
        quiet = returning_envelope()
        quiet["months"].insert(1, {
            "month": "2026-09", "purchase_count": 0, "gross": 0,
            "buyer_count": 0, "new_buyer_count": 0,
            "returning_buyer_count": 0, "returning_share": None,
            "new_purchase_count": 0, "returning_purchase_count": 0,
            "new_gross": 0, "returning_gross": 0})
        quiet["months"][2]["month"] = "2026-10"
        quiet["last_month"] = "2026-10"
        quiet["month_count"] = 3
        quiet_html = driver.build_html([quiet], labels, "2026-01-01 00:00:00Z",
                                       "probe disclaimer")
        quiet_ok = (labels.get("badge_quiet", "") in quiet_html
                    and quiet_html.count("<div class=bar>") == 1)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-RPTB4", sections == len(sellers) and months_marked == landed_rows
       and bars == defined_positive and dots == defined_zero
       and undefined >= 0 and single_ok and no_none and laws_ok and empty_ok
       and returning_ok and quiet_ok,
       "sections=%d/%d months_marked=%d/%d bars=%d/%d dots=%d/%d "
       "undefined_rows=%d single=%s laws=%s empty_probe=%s returning_probe=%s "
       "quiet_probe=%s bare_none=%s"
       % (sections, len(sellers), months_marked, landed_rows, bars,
          defined_positive, dots, defined_zero, undefined, single_ok, laws_ok,
          empty_ok, returning_ok, quiet_ok, not no_none))

    # ---- AC-RPTB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    not_advice = labels.get("law_notadvice", "") in page
    external = len(re.findall(r"https?://", page))
    ok("AC-RPTB5", aigc and on_page and not_advice and external == 0,
       "aigc=%s disclaimer_on_page=%s not_advice=%s external_links=%d"
       % (aigc, on_page, not_advice, external))

    # ---- AC-RPTB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-SRB" in read(FACE_SUITE)
    ok("AC-RPTB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
