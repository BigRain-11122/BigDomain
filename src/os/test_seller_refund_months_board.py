"""Battery suite for tools/seller_refund_months_board.py - AC-SRFMB1..6.

WHY THIS SUITE EXISTS (measured at R3421, not assumed):
api_seller_refund_months shipped with its own AC-SRFM1..8 criteria
(src/sandbox/ledger/ test suite on disk) but a git grep over tools/ and
preview/ answered rc=1 with zero hits, so the question "how much money came
back this month, who paid it, and is my refund pressure heavier than the
market" could not be opened by anyone. R3421 renders one section per seller on
one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3421 PIN
BEFORE the driver existed):
  AC-SRFMB1 the page and its json land, the json carries exactly the pinned
           payload key set, every seller block carries the shipped 27-key
           envelope, every month row carries the shipped 14 keys, seller_count
           equals the block count, and the report points at a file that exists.
  AC-SRFMB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates sellers through the shipped board
           face, reads api_seller_refund_months() per seller, and requires the
           page json's sellers (including every month row and the disclaimer)
           to equal that reading item for item - no typed fixture.
  AC-SRFMB3 the face's identities hold: month net equals gross minus refunded,
           refunded splits into the developer and platform legs, the month
           average and rate recompute (and are None rather than a fabricated
           zero where their denominator is zero), the rate is never clamped,
           the running accumulator is non-decreasing and ends on the envelope
           count, the envelope sums equal the month sums, the same-month count
           is bounded, the peak and largest refund are absent on a zero-refund
           envelope, the latest fields mirror the last month, the scope is
           seller, and the market rate matches the market-scope face.
  AC-SRFMB4 the page reads honestly: one section per seller with every month
           row marked, an absent rate printed as the dash instead of a zero, a
           refund-only month's negative net keeping its minus sign, a bar the
           page calls a width and not a share, no bare None, and an empty
           envelope handed to the driver's own renderer prints dashes instead
           of a fake zero (in-memory probe only).
  AC-SRFMB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-SRFMB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with AC-SRFM arms.

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
TOOL = os.path.join(ROOT, "tools", "seller_refund_months_board.py")
HTML = os.path.join(ROOT, "preview", "seller-refund-months-board.html")
JSONF = os.path.join(ROOT, "preview", "seller-refund-months-board.json")
COPY = os.path.join(ROOT, "preview", "seller-refund-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_sellerrefundmonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-refund-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "source_face", "scope",
    "seller_count", "sellers", "disclaimer", "report", "sources", "sizes",
}
SELLER_KEYS = {
    "dev_account", "scope", "month_count", "active_month_count",
    "refund_count", "refunded", "gross", "net", "refund_rate",
    "dev_refunded", "platform_refunded", "listing_count", "buyer_count",
    "seller_count", "avg_refund_amount", "same_month_count",
    "largest_refund", "peak_month", "peak_refund_count", "first_month",
    "last_month", "latest_month_refund_count", "latest_month_refunded",
    "latest_month_refund_rate", "market_refund_rate", "disclaimer", "months",
}
MONTH_KEYS = {
    "month", "refund_count", "refunded", "gross", "net", "refund_rate",
    "dev_refunded", "platform_refunded", "listing_count", "buyer_count",
    "seller_count", "avg_refund_amount", "same_month_count",
    "running_refund_count",
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
    tmp_root = tempfile.mkdtemp(prefix="srfmb-suite-")
    db = os.path.join(tmp_root, "srfmb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        sellers = sorted({str(row["dev_account"]) for row in board["listings"]})
        market = dict(am.api_seller_refund_months())
        scoped = [dict(am.api_seller_refund_months(seller))
                  for seller in sellers]
        return market, scoped, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("srfmb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def next_month(month):
    year, mon = str(month).split("-")
    year = int(year)
    mon = int(mon) + 1
    if mon > 12:
        year += 1
        mon = 1
    return "%04d-%02d" % (year, mon)


def identity_problems(sellers, market):
    problems = []
    for block in sellers:
        name = str(block["dev_account"])
        months = block["months"]
        if block["scope"] != "seller":
            problems.append("%s scope" % name)
        if int(block["month_count"]) != len(months):
            problems.append("%s month_count" % name)
        active = sum(1 for row in months
                     if int(row["refund_count"]) > 0 or int(row["gross"]) > 0)
        if int(block["active_month_count"]) != active:
            problems.append("%s active" % name)
        if not close(block["market_refund_rate"], market["refund_rate"]):
            problems.append("%s market rate" % name)
        running = 0
        previous = None
        sums = {"refund_count": 0, "refunded": 0, "gross": 0,
                "dev_refunded": 0, "platform_refunded": 0,
                "same_month_count": 0}
        for row in months:
            tag = "%s/%s" % (name, row["month"])
            if previous is not None and row["month"] != next_month(previous):
                problems.append("%s gap" % tag)
            previous = row["month"]
            if int(row["net"]) != int(row["gross"]) - int(row["refunded"]):
                problems.append("%s net" % tag)
            if int(row["refunded"]) != (int(row["dev_refunded"])
                                       + int(row["platform_refunded"])):
                problems.append("%s legs" % tag)
            count = int(row["refund_count"])
            want_avg = round(float(row["refunded"]) / count, 2) if count \
                else None
            if not close(row["avg_refund_amount"], want_avg):
                problems.append("%s avg" % tag)
            want_rate = round(float(row["refunded"]) / int(row["gross"]), 2) \
                if int(row["gross"]) > 0 else None
            if not close(row["refund_rate"], want_rate):
                problems.append("%s rate" % tag)
            running += count
            if int(row["running_refund_count"]) != running:
                problems.append("%s running" % tag)
            if int(row["same_month_count"]) > count:
                problems.append("%s same month" % tag)
            for key in sums:
                sums[key] += int(row[key])
        for key in sorted(sums):
            if int(block[key]) != sums[key]:
                problems.append("%s %s sum" % (name, key))
        if int(block["net"]) != int(block["gross"]) - int(block["refunded"]):
            problems.append("%s net" % name)
        want_rate = round(float(block["refunded"]) / int(block["gross"]), 2) \
            if int(block["gross"]) > 0 else None
        if not close(block["refund_rate"], want_rate):
            problems.append("%s rate" % name)
        want_avg = round(float(block["refunded"])
                         / int(block["refund_count"]), 2) \
            if int(block["refund_count"]) else None
        if not close(block["avg_refund_amount"], want_avg):
            problems.append("%s avg" % name)
        if months:
            if block["first_month"] != months[0]["month"]:
                problems.append("%s first" % name)
            if block["last_month"] != months[-1]["month"]:
                problems.append("%s last" % name)
            if not close(block["latest_month_refund_count"],
                         months[-1]["refund_count"]):
                problems.append("%s latest count" % name)
            if not close(block["latest_month_refunded"],
                         months[-1]["refunded"]):
                problems.append("%s latest refunded" % name)
            if not close(block["latest_month_refund_rate"],
                         months[-1]["refund_rate"]):
                problems.append("%s latest rate" % name)
        if int(block["refund_count"]) == 0:
            for key in ("largest_refund", "peak_month", "peak_refund_count"):
                if block[key] is not None:
                    problems.append("%s %s on zero refunds" % (name, key))
        else:
            if block["largest_refund"] is None:
                problems.append("%s largest missing" % name)
            elif int(block["largest_refund"]) > int(block["refunded"]):
                problems.append("%s largest" % name)
            peaks = [int(row["refund_count"]) for row in months
                     if int(row["refund_count"]) > 0]
            if block["peak_refund_count"] is None or block["peak_month"] is None:
                problems.append("%s peak missing" % name)
            elif int(block["peak_refund_count"]) != max(peaks):
                problems.append("%s peak count" % name)
            elif not any(row["month"] == block["peak_month"]
                         for row in months):
                problems.append("%s peak month" % name)
    return problems


def probe_empty():
    """An empty envelope: never landed, only handed to the driver renderer."""
    block = {
        "dev_account": "usr:nobody", "scope": "seller", "month_count": 0,
        "active_month_count": 0, "refund_count": 0, "refunded": 0, "gross": 0,
        "net": 0, "refund_rate": None, "dev_refunded": 0,
        "platform_refunded": 0, "listing_count": 0, "buyer_count": 0,
        "seller_count": 0, "avg_refund_amount": None, "same_month_count": 0,
        "largest_refund": None, "peak_month": None, "peak_refund_count": None,
        "first_month": None, "last_month": None,
        "latest_month_refund_count": None, "latest_month_refunded": None,
        "latest_month_refund_rate": None, "market_refund_rate": None,
        "disclaimer": "", "months": [],
    }
    return [block]


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    sellers = doc.get("sellers") or []
    month_rows = [row for block in sellers for row in (block.get("months") or [])]

    # ---- AC-SRFMB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    sellers_ok = all(set(block.keys()) == SELLER_KEYS for block in sellers)
    months_ok = all(set(row.keys()) == MONTH_KEYS for row in month_rows)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-SRFMB1", landed and keys == PAYLOAD_KEYS and sellers_ok
       and months_ok and sources_ok and bool(sellers)
       and int(doc.get("seller_count", -1)) == len(sellers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s sellers=%s months=%s "
       "sources=%s count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), sellers_ok, months_ok, sources_ok,
          len(sellers), int(doc.get("seller_count", -1)), report_ok))

    # ---- AC-SRFMB2: every printed number is the shipped face's own.
    live_market, live_sellers, live_disclaimer = live_world()
    sellers_same = json.dumps(sellers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in SELLER_KEYS} for block in live_sellers],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    live_rows = sum(len(block["months"]) for block in live_sellers)
    ok("AC-SRFMB2", sellers_same and disc_same and bool(sellers),
       "identical=%s disclaimer_same=%s sellers=%d months=%d"
       % (sellers_same, disc_same, len(sellers), live_rows))

    # ---- AC-SRFMB3: the face's identities hold on this envelope.
    problems = identity_problems(sellers, live_market) if sellers \
        else ["no sellers"]
    ok("AC-SRFMB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-SRFMB4: honest page face, dashes, minus net, width bar.
    dash = labels.get("none", "-")
    marked = all(('data-seller="%s"' % block["dev_account"]) in page
                 for block in sellers)
    month_marked = all(('data-month="%s"' % row["month"]) in page
                       for row in month_rows)
    refund_only = [row for row in month_rows
                   if int(row["gross"]) == 0 and int(row["refund_count"]) > 0]
    minus_ok = all(('>%d<' % int(row["net"])) in page for row in refund_only)
    dash_rate_ok = all(('<td class="n">%s</td>' % dash) in page
                       for row in month_rows if row["refund_rate"] is None)
    bars_ok = page.count("<div class=bar>") == len(month_rows)
    stand_in = ">None<" in page
    laws = [labels.get(key, "") for key in
            ("law_net", "law_legs", "law_rate", "law_zero", "law_running",
             "law_sums", "law_peak", "law_scope", "law_bar", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    empty_probe_ok = False
    try:
        driver = load_driver()
        probe_html = driver.build_html(probe_empty(), labels,
                                       "2026-01-01 00:00:00Z",
                                       doc.get("disclaimer") or "")
        empty_probe_ok = (probe_html.count("<div class=bar>") == 0
                          and ">None<" not in probe_html
                          and dash in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-SRFMB4", marked and month_marked and minus_ok and dash_rate_ok
       and bars_ok and not stand_in and laws_ok and empty_probe_ok,
       "sellers=%s months=%s refund_only=%d minus=%s dash_rate=%s bars=%s "
       "laws=%s empty_probe=%s stand_in_none=%s"
       % (marked, month_marked, len(refund_only), minus_ok, dash_rate_ok,
          bars_ok, laws_ok, empty_probe_ok, stand_in))

    # ---- AC-SRFMB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-SRFMB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-SRFMB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-SRFM" in read(FACE_SUITE)
    ok("AC-SRFMB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
