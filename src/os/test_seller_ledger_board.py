"""Battery suite for tools/seller_ledger_board.py - criteria AC-SLG1..6.

WHY THIS SUITE EXISTS (measured at R3411, not assumed):
api_seller_ledger shipped with its own AC-AMLG1..8 criteria of its own
(src/sandbox/ledger/test_apimarket_sellerledger.py) but a git grep over
tools/ and preview/ answered rc=1 with zero hits, so the two questions a
seller actually asks - how much money do I have right now, and which ledger
entries produced it - could not be opened by anyone. R3411 renders the
statement onto one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3411 PIN
BEFORE the driver existed):
  AC-SLG1 the page and its json land, the json carries exactly the pinned
           payload key set including the sizes and sources blocks, every
           seller block carries the shipped ten-key envelope, and every entry
           row carries the shipped ten-key row set (an extra ai_label is
           allowed, as the face only adds it for AI-sourced rows).
  AC-SLG2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates sellers from the shipped
           api_board(), reads api_seller_ledger() for each, and requires the
           page json's seller list to equal those readings item for item plus
           the disclaimer verbatim - no typed seller ids, no synthesized
           entry.
  AC-SLG3 the face's identities hold: entry_count equals the row count, the
           credit and debit totals re-derive from the rows, net equals their
           difference, every amount is non-negative, every direction is one
           of credit/debit, and the entries run newest-first.
  AC-SLG4 the page reads honestly: one seller section and one data row per
           entry, a debit-heavy account keeps its minus sign on net rather
           than being clamped (verified by handing the driver's own renderer
           a negative-net envelope; nothing is added to the landed page), no
           bare None reaches it, the balance/count/order sentences are on the
           page, and a seller with zero entries renders an explicit empty
           line (same in-memory probe).
  AC-SLG5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-SLG6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-AMLG arms.

Read-only over the repository: the provenance world is built in a temp dir and
both probe renders happen in memory, never inside preview/.

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
TOOL = os.path.join(ROOT, "tools", "seller_ledger_board.py")
HTML = os.path.join(ROOT, "preview", "seller-ledger-board.html")
JSONF = os.path.join(ROOT, "preview", "seller-ledger-board.json")
COPY = os.path.join(ROOT, "preview", "seller-ledger-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_sellerledger.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-ledger-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "seller_count", "sellers",
    "disclaimer", "report", "sources", "sizes",
}
SELLER_KEYS = {
    "dev_account", "balance", "balance_known", "entry_count", "credit_total",
    "debit_total", "net", "limit", "disclaimer", "entries",
}
ENTRY_KEYS = {
    "tx_id", "ts_utc", "type", "action", "ref", "ref_type", "direction",
    "amount", "memo", "source_ai",
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
    tmp_root = tempfile.mkdtemp(prefix="slg-suite-")
    db = os.path.join(tmp_root, "slg.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = am.api_board()
        sellers = sorted(set(str(row["dev_account"])
                             for row in board["listings"]))
        return ([dict(am.api_seller_ledger(s)) for s in sellers],
                board["disclaimer"])
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("slg_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_problems(blocks):
    problems = []
    for block in blocks:
        name = str(block["dev_account"])
        entries = block["entries"]
        if int(block["entry_count"]) != len(entries):
            problems.append("%s entry_count" % name)
        credit = sum(int(row["amount"]) for row in entries
                     if row["direction"] == "credit")
        debit = sum(int(row["amount"]) for row in entries
                    if row["direction"] == "debit")
        if credit != int(block["credit_total"]):
            problems.append("%s credit_total" % name)
        if debit != int(block["debit_total"]):
            problems.append("%s debit_total" % name)
        if int(block["net"]) != credit - debit:
            problems.append("%s net" % name)
        stamps = [str(row["ts_utc"] or "") for row in entries]
        if stamps != sorted(stamps, reverse=True):
            problems.append("%s order" % name)
        for row in entries:
            if int(row["amount"]) < 0:
                problems.append("%s negative amount" % name)
            if row["direction"] not in ("credit", "debit"):
                problems.append("%s direction" % name)
    return problems


def probe_entry(amount, direction):
    return {
        "tx_id": "probe00000000cafe", "ts_utc": "2026-01-01T00:00:00Z",
        "type": "adjust", "action": "apimarket_dev_share",
        "ref": "apimarket:share:probe", "ref_type": "settlement",
        "direction": direction, "amount": amount, "memo": None,
        "source_ai": False,
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    blocks = doc.get("sellers") or []

    # ---- AC-SLG1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    seller_keys_ok = all(set(block.keys()) == SELLER_KEYS for block in blocks)
    entry_keys_ok = all(
        set(row.keys()) in (ENTRY_KEYS, ENTRY_KEYS | {"ai_label"})
        for block in blocks for row in block["entries"])
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    ok("AC-SLG1", landed and keys == PAYLOAD_KEYS and seller_keys_ok
       and entry_keys_ok and int(doc.get("seller_count", -1)) == len(blocks)
       and bool(blocks) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s seller_keys=%s entry_keys=%s "
       "sellers=%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), seller_keys_ok, entry_keys_ok,
          len(blocks), report_ok))

    # ---- AC-SLG2: every printed number is the shipped face's own.
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
    ok("AC-SLG2", not diffs and disc_same and bool(blocks)
       and all(len(b["entries"]) > 0 for b in blocks),
       "diffs=%s disclaimer_same=%s sellers=%d entries=%d"
       % (diffs[:4], disc_same, len(blocks),
          sum(len(b["entries"]) for b in blocks)))

    # ---- AC-SLG3: the face's identities hold on these envelopes.
    problems = identity_problems(blocks) if blocks else ["no sellers"]
    ok("AC-SLG3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-SLG4: honest page face, no clamping, explicit empty statement.
    entries = sum(len(block["entries"]) for block in blocks)
    page_rows = page.count('<tr class="entry">')
    sec_ok = all(('id="seller-%s"' % block["dev_account"]) in page
                 for block in blocks)
    stand_in = ">None<" in page
    law_ok = all(labels.get(key, "") in page for key in
                 ("law_balance", "law_count", "law_order", "law_dir",
                  "law_notadvice"))
    negative_ok = False
    empty_ok = False
    try:
        driver = load_driver()
        disclaimer = doc.get("disclaimer") or ""
        negative_block = {
            "dev_account": "usr:debit-probe", "balance": -5,
            "balance_known": True, "entry_count": 1, "credit_total": 0,
            "debit_total": 5, "net": -5, "limit": 50,
            "disclaimer": disclaimer,
            "entries": [probe_entry(5, "debit")],
        }
        negative_html = driver.build_html([negative_block], labels,
                                          "2026-01-01 00:00:00Z",
                                          disclaimer)
        negative_ok = (">-5</b>" in negative_html
                       and 'class="neg"' in negative_html)
        empty_block = {
            "dev_account": "usr:empty-probe", "balance": 0,
            "balance_known": False, "entry_count": 0, "credit_total": 0,
            "debit_total": 0, "net": 0, "limit": 50,
            "disclaimer": disclaimer, "entries": [],
        }
        empty_html = driver.build_html([empty_block], labels,
                                       "2026-01-01 00:00:00Z", disclaimer)
        empty_ok = (labels.get("no_entries", "") in empty_html
                    and '<tr class="entry">' not in empty_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-SLG4", page_rows == entries and not stand_in and sec_ok
       and negative_ok and empty_ok and law_ok,
       "rows=%d/%d sections=%s negative=%s empty=%s laws=%s stand_in_none=%s"
       % (page_rows, entries, sec_ok, negative_ok, empty_ok, law_ok,
          stand_in))

    # ---- AC-SLG5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-SLG5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-SLG6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-AMLG" in read(FACE_SUITE)
    ok("AC-SLG6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
