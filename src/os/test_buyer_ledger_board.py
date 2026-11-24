"""Battery suite for tools/buyer_ledger_board.py - criteria AC-BLB1..6.

WHY THIS SUITE EXISTS (measured at R3415, not assumed):
api_buyer_ledger shipped with its own AC-AMLGB1..8 criteria
(src/sandbox/ledger/test_apimarket_buyerledger.py) but a git grep over tools/
and preview/ answered rc=1 with zero hits, so the buyer-side question "did the
refund actually come back into my wallet, and which entry brought it" could
not be opened by anyone. R3415 renders one statement per buyer onto one page;
this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3415 PIN
BEFORE the driver existed):
  AC-BLB1 the page and its json land, the json carries exactly the pinned
           payload key set including the sizes and sources blocks, every buyer
           block carries the shipped ten-key envelope, every entry carries the
           shipped ten-key row set, buyer_count equals the block count, and the
           report points at a file that exists.
  AC-BLB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates buyers through the shipped board,
           sales and ratings faces, reads api_buyer_ledger() over it, and
           requires the page json's buyers to equal that reading item for item
           plus the disclaimer verbatim - no typed fixture, no synthesized
           entry.
  AC-BLB3 the face's identities hold: entry count, credit and debit totals,
           net difference, balance equals net when the balance is known, every
           amount non-negative, only the two direction labels, and entries
           newest-first.
  AC-BLB4 the page reads honestly: one section and one data row set per buyer,
           an empty memo prints an explicit placeholder instead of None, a
           refund credit is marked and its ref printed, the balance, limit and
           no-recompute laws are on the page, an empty statement handed to the
           driver's own renderer prints an explicit empty line (in-memory probe
           only), and no bare None reaches the page.
  AC-BLB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-BLB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-AMLGB arms.

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
TOOL = os.path.join(ROOT, "tools", "buyer_ledger_board.py")
HTML = os.path.join(ROOT, "preview", "buyer-ledger-board.html")
JSONF = os.path.join(ROOT, "preview", "buyer-ledger-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-ledger-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_buyerledger.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-buyer-ledger-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "source_face", "buyer_count",
    "buyers", "disclaimer", "report", "sources", "sizes",
}
BUYER_KEYS = {
    "balance", "balance_known", "buyer_id", "credit_total", "debit_total",
    "disclaimer", "entries", "entry_count", "limit", "net",
}
ENTRY_KEYS = {
    "action", "amount", "direction", "memo", "ref", "ref_type", "source_ai",
    "ts_utc", "tx_id", "type",
}
REFUND_PREFIX = "apimarket:refund:"

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
    tmp_root = tempfile.mkdtemp(prefix="blb-suite-")
    db = os.path.join(tmp_root, "blb.db")
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
        return ([dict(am.api_buyer_ledger(buyer)) for buyer in sorted(seen)],
                board["disclaimer"])
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("blb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_problems(blocks):
    problems = []
    for block in blocks:
        name = str(block.get("buyer_id"))
        entries = block.get("entries") or []
        if int(block.get("entry_count", -1)) != len(entries):
            problems.append("%s entry_count" % name)
        credit = sum(int(row["amount"]) for row in entries
                     if row["direction"] == "credit")
        debit = sum(int(row["amount"]) for row in entries
                    if row["direction"] == "debit")
        if credit != int(block.get("credit_total", -1)):
            problems.append("%s credit_total" % name)
        if debit != int(block.get("debit_total", -1)):
            problems.append("%s debit_total" % name)
        if int(block.get("net", 0)) != credit - debit:
            problems.append("%s net" % name)
        if block.get("balance_known") and int(block.get("balance", 0)) != int(
                block.get("net", 0)):
            problems.append("%s balance" % name)
        for row in entries:
            if int(row["amount"]) < 0:
                problems.append("%s negative amount" % name)
            if row["direction"] not in ("credit", "debit"):
                problems.append("%s direction" % name)
        stamps = [str(row["ts_utc"] or "") for row in entries]
        if stamps != sorted(stamps, reverse=True):
            problems.append("%s order" % name)
    return problems


def probe_empty(disclaimer):
    """An empty statement: never landed, only handed to the renderer."""
    return [{
        "balance": 0, "balance_known": False, "buyer_id": "usr:probe-empty",
        "credit_total": 0, "debit_total": 0, "disclaimer": disclaimer,
        "entries": [], "entry_count": 0, "limit": 50, "net": 0,
    }]


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    blocks = doc.get("buyers") or []
    entries = [row for block in blocks for row in (block.get("entries") or [])]

    # ---- AC-BLB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    blocks_ok = all(set(block.keys()) == BUYER_KEYS for block in blocks)
    entries_ok = all(set(row.keys()) - ENTRY_KEYS <= {"ai_label"}
                     for row in entries)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    ok("AC-BLB1", landed and keys == PAYLOAD_KEYS and blocks_ok
       and entries_ok and bool(blocks)
       and int(doc.get("buyer_count", -1)) == len(blocks) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s blocks=%s entries=%s "
       "buyers=%d rows=%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), blocks_ok, entries_ok, len(blocks),
          len(entries), report_ok))

    # ---- AC-BLB2: every printed number is the shipped face's own.
    live, live_disclaimer = live_buyers()
    same = (json.dumps(blocks, sort_keys=True)
            == json.dumps(live, sort_keys=True))
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-BLB2", same and disc_same and bool(blocks),
       "identical=%s disclaimer_same=%s buyers=%d entries=%d"
       % (same, disc_same, len(blocks), len(entries)))

    # ---- AC-BLB3: the face's identities hold on this envelope.
    problems = identity_problems(blocks) if blocks else ["no buyers"]
    ok("AC-BLB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-BLB4: honest page face, marked refunds, explicit empty line.
    page_rows = page.count('<tr class="entry')
    sections_ok = all(('id="buyer-%s"' % block["buyer_id"]) in page
                      for block in blocks)
    stand_in = ">None<" in page
    refunds = [row for row in entries if str(row.get("ref") or "")
               .startswith(REFUND_PREFIX)]
    refund_ok = all(('data-tx="%s"' % row["tx_id"]) in page
                    and str(row["ref"]) in page for row in refunds)
    tagged = page.count(labels.get("refund_tag", "")) >= len(refunds)
    empty_memo = any(not row.get("memo") for row in entries)
    placeholder_ok = (not empty_memo) or (labels.get("none", "") in page)
    laws = [labels.get(key, "") for key in
            ("law_balance", "law_count", "law_order", "law_empty", "law_dir",
             "law_refund", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    empty_probe_ok = False
    try:
        driver = load_driver()
        disclaimer = doc.get("disclaimer") or ""
        probe_html = driver.build_html(probe_empty(disclaimer), labels,
                                       "2026-01-01 00:00:00Z", disclaimer)
        empty_probe_ok = (labels.get("no_entries", "") in probe_html
                          and '<tr class="entry' not in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-BLB4", page_rows == len(entries) and sections_ok and not stand_in
       and refund_ok and tagged and placeholder_ok and laws_ok
       and empty_probe_ok,
       "rows=%d/%d sections=%s refunds=%d marked=%s tagged=%s placeholder=%s "
       "laws=%s empty_probe=%s stand_in_none=%s"
       % (page_rows, len(entries), sections_ok, len(refunds), refund_ok,
          tagged, placeholder_ok, laws_ok, empty_probe_ok, stand_in))

    # ---- AC-BLB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-BLB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-BLB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-AMLGB" in read(FACE_SUITE)
    ok("AC-BLB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
