"""Battery suite for tools/buyer_months_board.py - criteria AC-BMB1..6.

WHY THIS SUITE EXISTS (measured at R3416, not assumed):
api_buyer_months shipped with its own AC-AMBM1..8 criteria
(src/sandbox/ledger/test_apimarket_buyermonths.py) but a git grep over tools/
and preview/ answered rc=1 with zero page readers, so the buyer-side question
"what did I actually spend this month, and which month was a refund month"
could not be opened by anyone. (Honest boundary: apimarket_report.py already
writes the face into the settlement CSV bundle, so the CSV reader existed; the
openable page did not.) R3416 renders one section per buyer onto one page;
this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3416 PIN
BEFORE the driver existed):
  AC-BMB1 the page and its json land, the json carries exactly the pinned
           payload key set including the sizes and sources blocks, every buyer
           block carries the shipped eleven-key envelope, every month row
           carries the shipped eleven-key row set, buyer_count equals the block
           count, and the report points at a file that exists.
  AC-BMB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates buyers through the shipped board,
           sales and ratings faces, reads api_buyer_months() over it, and
           requires the page json's buyers to equal that reading item for item
           plus the disclaimer verbatim - no typed fixture, no synthesized
           month.
  AC-BMB3 the face's identities hold: per month net equals gross minus refunded
           and also equals the two net legs summed, per buyer every lifetime
           column equals the sum of its month column, lifetime net equals gross
           minus refunded, and months are strictly ascending YYYY-MM.
  AC-BMB4 the page reads honestly: one section and one data row set per buyer,
           a refund-only month prints its minus sign instead of a clamped zero,
           the page states the four laws it obeys, an empty envelope handed to
           the driver's own renderer prints an explicit line (in-memory probe
           only), and no bare None reaches the page.
  AC-BMB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-BMB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-AMBM arms.

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
TOOL = os.path.join(ROOT, "tools", "buyer_months_board.py")
HTML = os.path.join(ROOT, "preview", "buyer-months-board.html")
JSONF = os.path.join(ROOT, "preview", "buyer-months-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-months-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_buyermonths.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-buyer-months-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "source_face", "buyer_count",
    "buyers", "disclaimer", "report", "sources", "sizes",
}
BUYER_KEYS = {
    "buyer_id", "month_count", "lifetime_purchase_count",
    "lifetime_refund_count", "lifetime_gross_spent", "lifetime_refunded",
    "lifetime_net_spent", "lifetime_dev_paid", "lifetime_platform_paid",
    "months", "disclaimer",
}
MONTH_KEYS = {
    "month", "purchase_count", "refund_count", "gross_spent", "refunded",
    "net", "listing_count", "platform_paid", "dev_paid", "platform_paid_net",
    "dev_paid_net",
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
    tmp_root = tempfile.mkdtemp(prefix="bmb-suite-")
    db = os.path.join(tmp_root, "bmb.db")
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
        return ([dict(am.api_buyer_months(buyer)) for buyer in sorted(seen)],
                board["disclaimer"])
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("bmb_board_driver", TOOL)
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
        for key, total in (("purchase_count", "lifetime_purchase_count"),
                           ("refund_count", "lifetime_refund_count"),
                           ("gross_spent", "lifetime_gross_spent"),
                           ("refunded", "lifetime_refunded"),
                           ("net", "lifetime_net_spent"),
                           ("dev_paid_net", "lifetime_dev_paid"),
                           ("platform_paid_net", "lifetime_platform_paid")):
            if sum(int(row[key]) for row in months) != int(block[total]):
                problems.append("%s sum(%s)!=%s" % (name, key, total))
        if (int(block["lifetime_net_spent"])
                != int(block["lifetime_gross_spent"])
                - int(block["lifetime_refunded"])):
            problems.append("%s lifetime net" % name)
        for row in months:
            if int(row["net"]) != int(row["gross_spent"]) - int(row["refunded"]):
                problems.append("%s %s net" % (name, row["month"]))
            if (int(row["dev_paid_net"]) + int(row["platform_paid_net"])
                    != int(row["net"])):
                problems.append("%s %s legs" % (name, row["month"]))
            month = str(row["month"])
            if len(month) != 7 or month[4] != "-":
                problems.append("%s bad month" % name)
        names = [str(row["month"]) for row in months]
        if names != sorted(names):
            problems.append("%s order" % name)
    return problems


def probe_empty(disclaimer):
    """An empty envelope: never landed, only handed to the renderer."""
    return [{
        "buyer_id": "usr:probe-empty", "month_count": 0, "months": [],
        "lifetime_purchase_count": 0, "lifetime_refund_count": 0,
        "lifetime_gross_spent": 0, "lifetime_refunded": 0,
        "lifetime_net_spent": 0, "lifetime_dev_paid": 0,
        "lifetime_platform_paid": 0, "disclaimer": disclaimer,
    }]


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    blocks = doc.get("buyers") or []
    months = [row for block in blocks for row in (block.get("months") or [])]

    # ---- AC-BMB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    blocks_ok = all(set(block.keys()) == BUYER_KEYS for block in blocks)
    rows_ok = all(set(row.keys()) == MONTH_KEYS for row in months)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    ok("AC-BMB1", landed and keys == PAYLOAD_KEYS and blocks_ok and rows_ok
       and bool(blocks) and int(doc.get("buyer_count", -1)) == len(blocks)
       and report_ok,
       "landed=%s keys=%d missing=%s extra=%s blocks=%s rows=%s buyers=%d "
       "months=%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), blocks_ok, rows_ok, len(blocks),
          len(months), report_ok))

    # ---- AC-BMB2: every printed number is the shipped face's own.
    live, live_disclaimer = live_buyers()
    same = (json.dumps(blocks, sort_keys=True)
            == json.dumps(live, sort_keys=True))
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-BMB2", same and disc_same and bool(blocks),
       "identical=%s disclaimer_same=%s buyers=%d months=%d"
       % (same, disc_same, len(blocks), len(months)))

    # ---- AC-BMB3: the face's identities hold on this envelope.
    problems = identity_problems(blocks) if blocks else ["no buyers"]
    ok("AC-BMB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-BMB4: honest page face, negative refund months, empty probe.
    page_rows = page.count('<tr class="month')
    sections_ok = all(('id="buyer-%s"' % block["buyer_id"]) in page
                      for block in blocks)
    stand_in = ">None<" in page
    negatives = [row for row in months if int(row["net"]) < 0]
    negative_ok = all(('>%s<' % row["net"]) in page for row in negatives) \
        and ('n neg' in page)
    clamped = any(int(row["net"]) < 0 and row["refunded"] == 0
                  for row in months)
    laws = [labels.get(key, "") for key in
            ("law_net", "law_split", "law_sum", "law_order", "law_negative",
             "law_scope", "law_notadvice")]
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
    ok("AC-BMB4", page_rows == len(months) and sections_ok and not stand_in
       and negative_ok and not clamped and laws_ok and empty_probe_ok,
       "rows=%d/%d sections=%s negatives=%d neg_printed=%s clamped=%s "
       "laws=%s empty_probe=%s stand_in_none=%s"
       % (page_rows, len(months), sections_ok, len(negatives), negative_ok,
          clamped, laws_ok, empty_probe_ok, stand_in))

    # ---- AC-BMB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-BMB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-BMB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-AMBM" in read(FACE_SUITE)
    ok("AC-BMB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
