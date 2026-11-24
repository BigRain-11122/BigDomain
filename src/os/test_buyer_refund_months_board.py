"""Battery suite for tools/buyer_refund_months_board.py - AC-BRFM1..6.

WHY THIS SUITE EXISTS (measured at R3417, not assumed):
api_buyer_refund_months shipped with its own AC-BRM1..8 criteria
(src/sandbox/ledger/test_apimarket_buyerrefundmonths.py) but a git grep over
tools/ and preview/ answered rc=1 with zero page readers, so the buyer-side
question "how much money came back this month, and did the refund land in the
purchase month or a later one" could not be opened by anyone. R3417 renders one
section per buyer onto one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3417 PIN
BEFORE the driver existed):
  AC-BRFM1 the page and its json land, the json carries exactly the pinned
           payload key set including the sizes and sources blocks, every buyer
           block carries the shipped twenty-one-key envelope, every month row
           carries the shipped ten-key row set, buyer_count equals the block
           count, and the report points at a file that exists.
  AC-BRFM2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates buyers through the shipped board,
           sales and ratings faces, reads api_buyer_refund_months() over it,
           and requires the page json's buyers to equal that reading item for
           item plus the disclaimer verbatim - no typed fixture, no synthesized
           refund month.
  AC-BRFM3 the face's identities hold: per month refunded equals the two legs
           summed, listing_count equals refund_count while seller_count never
           exceeds it, the per-month average is pooled and a zero month carries
           None, the running accumulator never falls and lands on the envelope
           count, the envelope splits and sums agree, the gap grid is
           contiguous, and months are ascending YYYY-MM.
  AC-BRFM4 the page reads honestly: one section and one data row set per buyer,
           a buyer with no refund prints an explicit empty line, an empty
           envelope handed to the driver's own renderer prints the same line
           (in-memory probe only), the seven law sentences are on the page,
           and no bare None reaches it.
  AC-BRFM5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-BRFM6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-BRM arms.

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
TOOL = os.path.join(ROOT, "tools", "buyer_refund_months_board.py")
HTML = os.path.join(ROOT, "preview", "buyer-refund-months-board.html")
JSONF = os.path.join(ROOT, "preview", "buyer-refund-months-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-refund-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_buyerrefundmonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-buyer-refund-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "source_face", "buyer_count",
    "buyers", "disclaimer", "report", "sources", "sizes",
}
BUYER_KEYS = {
    "buyer_id", "scope", "month_count", "active_month_count", "refund_count",
    "refunded", "dev_refunded", "platform_refunded", "listing_count",
    "seller_count", "avg_refund_amount", "same_month_count", "largest_refund",
    "peak_month", "peak_refund_count", "first_month", "last_month",
    "latest_month_refund_count", "latest_month_refunded", "months",
    "disclaimer",
}
MONTH_KEYS = {
    "month", "refund_count", "refunded", "dev_refunded", "platform_refunded",
    "listing_count", "seller_count", "avg_refund_amount", "same_month_count",
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


def live_buyers():
    """The shipped face's own reading over the suite's throwaway demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="brfm-suite-")
    db = os.path.join(tmp_root, "brfm.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        seen = set()
        for dev in sorted(set(str(row["dev_account"])
                              for row in board["listings"])):
            for row in (dict(am.api_sales(dev)).get("sales") or []):
                if row.get("buyer_id"):
                    seen.add(str(row["buyer_id"]))
        for listing in board["listings"]:
            for row in (dict(am.api_ratings(listing["listing_id"]))
                        .get("ratings") or []):
                if row.get("buyer_id"):
                    seen.add(str(row["buyer_id"]))
        return ([dict(am.api_buyer_refund_months(buyer))
                 for buyer in sorted(seen)], board["disclaimer"])
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("brfm_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_problems(blocks):
    problems = []
    for block in blocks:
        name = str(block.get("buyer_id"))
        months = block.get("months") or []
        if int(block.get("month_count", -1)) != len(months):
            problems.append("%s month_count" % name)
        active = sum(1 for row in months if int(row["refund_count"]) > 0)
        if int(block.get("active_month_count", -1)) != active:
            problems.append("%s active_month_count" % name)
        for key in ("refund_count", "refunded", "dev_refunded",
                    "platform_refunded"):
            if sum(int(row[key]) for row in months) != int(block[key]):
                problems.append("%s sum(%s)" % (name, key))
        if (int(block["refunded"]) != int(block["dev_refunded"])
                + int(block["platform_refunded"])):
            problems.append("%s envelope split" % name)
        running = 0
        for row in months:
            if int(row["refunded"]) != (int(row["dev_refunded"])
                                        + int(row["platform_refunded"])):
                problems.append("%s %s split" % (name, row["month"]))
            if int(row["listing_count"]) != int(row["refund_count"]):
                problems.append("%s %s listings" % (name, row["month"]))
            if int(row["seller_count"]) > int(row["refund_count"]):
                problems.append("%s %s sellers" % (name, row["month"]))
            count = int(row["refund_count"])
            if count == 0:
                if row["avg_refund_amount"] is not None:
                    problems.append("%s %s zero avg" % (name, row["month"]))
            elif (row["avg_refund_amount"] is None
                  or round(float(row["refunded"]) / count, 2)
                  != row["avg_refund_amount"]):
                problems.append("%s %s avg" % (name, row["month"]))
            if int(row["running_refund_count"]) < running:
                problems.append("%s %s running" % (name, row["month"]))
            running = int(row["running_refund_count"])
        if months and running != int(block["refund_count"]):
            problems.append("%s running tail" % name)
        if months:
            if str(block["first_month"]) != str(months[0]["month"]):
                problems.append("%s first_month" % name)
            if str(block["last_month"]) != str(months[-1]["month"]):
                problems.append("%s last_month" % name)
        names = [str(row["month"]) for row in months]
        if names != sorted(names):
            problems.append("%s order" % name)
        for row in months:
            month = str(row["month"])
            if len(month) != 7 or month[4] != "-":
                problems.append("%s bad month" % name)
    return problems


def contiguous(names):
    """The face owes a contiguous YYYY-MM grid between the first and last."""
    if not names:
        return True
    year, month = int(names[0][:4]), int(names[0][5:7])
    expected = []
    while True:
        expected.append("%04d-%02d" % (year, month))
        if expected[-1] == names[-1]:
            break
        month += 1
        if month == 13:
            year, month = year + 1, 1
        if len(expected) > 240:
            return False
    return expected == list(names)


def probe_empty(disclaimer):
    """An empty envelope: never landed, only handed to the renderer."""
    return [{
        "buyer_id": "usr:probe-empty", "scope": "buyer", "month_count": 0,
        "active_month_count": 0, "refund_count": 0, "refunded": 0,
        "dev_refunded": 0, "platform_refunded": 0, "listing_count": 0,
        "seller_count": 0, "avg_refund_amount": None, "same_month_count": 0,
        "largest_refund": None, "peak_month": None, "peak_refund_count": None,
        "first_month": None, "last_month": None,
        "latest_month_refund_count": None, "latest_month_refunded": None,
        "months": [], "disclaimer": disclaimer,
    }]


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    blocks = doc.get("buyers") or []
    months = [row for block in blocks for row in (block.get("months") or [])]

    # ---- AC-BRFM1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    blocks_ok = all(set(block.keys()) == BUYER_KEYS for block in blocks)
    rows_ok = all(set(row.keys()) == MONTH_KEYS for row in months)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    ok("AC-BRFM1", landed and keys == PAYLOAD_KEYS and blocks_ok and rows_ok
       and bool(blocks) and int(doc.get("buyer_count", -1)) == len(blocks)
       and report_ok,
       "landed=%s keys=%d missing=%s extra=%s blocks=%s rows=%s buyers=%d "
       "months=%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), blocks_ok, rows_ok, len(blocks),
          len(months), report_ok))

    # ---- AC-BRFM2: every printed number is the shipped face's own.
    live, live_disclaimer = live_buyers()
    same = (json.dumps(blocks, sort_keys=True)
            == json.dumps(live, sort_keys=True))
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-BRFM2", same and disc_same and bool(blocks),
       "identical=%s disclaimer_same=%s buyers=%d months=%d"
       % (same, disc_same, len(blocks), len(months)))

    # ---- AC-BRFM3: the face's identities hold on this envelope.
    problems = identity_problems(blocks) if blocks else ["no buyers"]
    grid_ok = all(contiguous([str(row["month"]) for row in
                               (block.get("months") or [])])
                  for block in blocks)
    ok("AC-BRFM3", not problems and grid_ok,
       "problems=%s grid=%s" % (problems[:4] if problems else [], grid_ok))

    # ---- AC-BRFM4: honest page face, explicit empty line, laws, no None.
    page_rows = page.count('<tr class="month')
    sections_ok = all(('id="buyer-%s"' % block["buyer_id"]) in page
                      for block in blocks)
    stand_in = ">None<" in page
    empty_blocks = [block for block in blocks if not block["months"]]
    empty_ok = all(labels.get("no_months", "") in page for _ in empty_blocks)
    laws = [labels.get(key, "") for key in
            ("law_booking", "law_grid", "law_split", "law_running",
             "law_pooled", "law_distinct", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    empty_probe_ok = False
    try:
        driver = load_driver()
        disclaimer = doc.get("disclaimer") or ""
        probe_html = driver.build_html(probe_empty(disclaimer), labels,
                                       "2026-01-01 00:00:00Z", disclaimer)
        empty_probe_ok = (labels.get("no_months", "") in probe_html
                          and '<tr class="month' not in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-BRFM4", page_rows == len(months) and sections_ok and not stand_in
       and empty_ok and laws_ok and empty_probe_ok,
       "rows=%d/%d sections=%s empty_blocks=%d empty_printed=%s laws=%s "
       "empty_probe=%s stand_in_none=%s"
       % (page_rows, len(months), sections_ok, len(empty_blocks), empty_ok,
          laws_ok, empty_probe_ok, stand_in))

    # ---- AC-BRFM5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-BRFM5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-BRFM6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-BRM" in read(FACE_SUITE)
    ok("AC-BRFM6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
