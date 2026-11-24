"""Battery suite for tools/seller_revenue_board.py - criteria AC-SRV1..6.

WHY THIS SUITE EXISTS (measured at R3410, not assumed):
api_revenue_months shipped with its own AC-REVM criteria of its own
(src/sandbox/ledger/test_apimarket_revenuemonths.py) but a git grep over
tools/ and preview/ answered rc=1 with zero hits, so the month-by-month money
a seller actually earned - and how much of it the platform kept - could not be
opened by anyone. R3410 renders it onto one page; this suite grades the page,
not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3410 PIN
BEFORE the driver existed):
  AC-SRV1 the page and its json land, the json carries exactly the pinned
           payload key set including the sizes and sources blocks, every
           seller block carries the shipped nine-key envelope, and every month
           row carries the shipped ten-key row set.
  AC-SRV2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates sellers from the shipped
           api_board(), reads api_revenue_months() for each, and requires the
           page json's seller list to equal those readings item for item plus
           the disclaimer verbatim - no typed seller ids, no synthesized
           month.
  AC-SRV3 the face's identities hold: the five lifetime totals equal their
           month-row sums, month_count equals the row count, each row's net
           re-derives as gross minus refunded, each row's two shares sum to
           gross and the two net shares sum to net, and the months ascend in
           YYYY-MM order.
  AC-SRV4 the page reads honestly: one seller section and one data row per
           month, a refund-only month keeps its minus sign rather than being
           clamped, the negative-month and not-investment-advice sentences are
           on the page, no bare None reaches it, and a seller with zero months
           renders an explicit empty line (verified by handing the driver's
           own renderer a zero-month envelope; nothing is added to the landed
           page).
  AC-SRV5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-SRV6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-REVM arms.

Read-only over the repository: the provenance world is built in a temp dir and
the empty-seller render happens in memory, never inside preview/.

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
TOOL = os.path.join(ROOT, "tools", "seller_revenue_board.py")
HTML = os.path.join(ROOT, "preview", "seller-revenue-board.html")
JSONF = os.path.join(ROOT, "preview", "seller-revenue-board.json")
COPY = os.path.join(ROOT, "preview", "seller-revenue-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_revenuemonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-revenue-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "seller_count", "sellers",
    "disclaimer", "report", "sources", "sizes",
}
SELLER_KEYS = {
    "dev_account", "month_count", "lifetime_sales_count", "lifetime_gross",
    "lifetime_refund_count", "lifetime_refunded", "lifetime_net", "months",
    "disclaimer",
}
MONTH_KEYS = {
    "month", "sales_count", "gross", "refund_count", "refunded", "net",
    "dev_share", "platform_share", "dev_share_net", "platform_share_net",
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


def seller_readings():
    """One envelope per seller the shipped board enumerates, own demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="srv-suite-")
    db = os.path.join(tmp_root, "srv.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = am.api_board()
        sellers = sorted(set(str(row["dev_account"])
                             for row in board["listings"]))
        return ([dict(am.api_revenue_months(s)) for s in sellers],
                board["disclaimer"])
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("srv_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_problems(blocks):
    problems = []
    for block in blocks:
        name = str(block["dev_account"])
        months = block["months"]
        if int(block["month_count"]) != len(months):
            problems.append("%s month_count" % name)
        for key, total in (("sales_count", "lifetime_sales_count"),
                           ("gross", "lifetime_gross"),
                           ("refund_count", "lifetime_refund_count"),
                           ("refunded", "lifetime_refunded"),
                           ("net", "lifetime_net")):
            if sum(int(row[key]) for row in months) != int(block[total]):
                problems.append("%s sum %s" % (name, key))
        names = [str(row["month"]) for row in months]
        if names != sorted(names):
            problems.append("%s order" % name)
        for row in months:
            if int(row["net"]) != (int(row["gross"]) - int(row["refunded"])):
                problems.append("%s %s net" % (name, row["month"]))
            if (int(row["dev_share"]) + int(row["platform_share"])
                    != int(row["gross"])):
                problems.append("%s %s gross split" % (name, row["month"]))
            if (int(row["dev_share_net"]) + int(row["platform_share_net"])
                    != int(row["net"])):
                problems.append("%s %s net split" % (name, row["month"]))
    return problems


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    blocks = doc.get("sellers") or []

    # ---- AC-SRV1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    seller_keys_ok = all(set(block.keys()) == SELLER_KEYS for block in blocks)
    month_keys_ok = all(set(row.keys()) == MONTH_KEYS
                        for block in blocks for row in block["months"])
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    ok("AC-SRV1", landed and keys == PAYLOAD_KEYS and seller_keys_ok
       and month_keys_ok and int(doc.get("seller_count", -1)) == len(blocks)
       and bool(blocks) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s seller_keys=%s month_keys=%s "
       "sellers=%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), seller_keys_ok, month_keys_ok,
          len(blocks), report_ok))

    # ---- AC-SRV2: every printed number is the shipped face's own.
    live, live_disclaimer = seller_readings()
    diffs = []
    if len(live) != len(blocks):
        diffs.append("seller_count")
    else:
        for got, want in zip(blocks, live):
            if json.dumps(got, sort_keys=True) != json.dumps(want,
                                                            sort_keys=True):
                diffs.append(str(want.get("dev_account")))
    disc_same = doc.get("disclaimer") == live_disclaimer
    ok("AC-SRV2", not diffs and disc_same and bool(blocks)
       and all(len(b["months"]) > 0 for b in blocks),
       "diffs=%s disclaimer_same=%s sellers=%d months=%d"
       % (diffs[:4], disc_same, len(blocks),
          sum(len(b["months"]) for b in blocks)))

    # ---- AC-SRV3: the face's identities hold on these envelopes.
    problems = identity_problems(blocks) if blocks else ["no sellers"]
    ok("AC-SRV3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-SRV4: honest page face, no clamping, explicit empty month.
    months = sum(len(block["months"]) for block in blocks)
    page_rows = page.count('<tr class="month">')
    neg_rows = [row for block in blocks for row in block["months"]
                if int(row["net"]) < 0]
    neg_printed = all((">%d</td>" % int(row["net"])) in page
                      for row in neg_rows)
    sec_ok = all(('id="seller-%s"' % block["dev_account"]) in page
                 for block in blocks)
    stand_in = ">None<" in page
    law_ok = (labels.get("law_negative", "") in page
              and labels.get("law_notadvice", "") in page)
    empty_block = {
        "dev_account": "usr:empty-probe", "month_count": 0,
        "lifetime_sales_count": 0, "lifetime_gross": 0,
        "lifetime_refund_count": 0, "lifetime_refunded": 0,
        "lifetime_net": 0, "months": [],
        "disclaimer": doc.get("disclaimer") or "",
    }
    try:
        driver = load_driver()
        empty_html = driver.build_html([empty_block], labels,
                                       "2026-01-01 00:00:00Z",
                                       doc.get("disclaimer") or "")
        empty_ok = (labels.get("no_months", "") in empty_html
                    and '<tr class="month">' not in empty_html)
    except Exception as exc:  # noqa: BLE001
        empty_html = ""
        empty_ok = False
        print("NOTE empty-render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-SRV4", page_rows == months and not stand_in and sec_ok
       and neg_printed and bool(neg_rows) and law_ok and empty_ok,
       "rows=%d/%d sections=%s negatives=%d printed=%s laws=%s empty=%s "
       "stand_in_none=%s"
       % (page_rows, months, sec_ok, len(neg_rows), neg_printed, law_ok,
          empty_ok, stand_in))

    # ---- AC-SRV5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-SRV5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-SRV6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-REVM" in read(FACE_SUITE)
    ok("AC-SRV6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
