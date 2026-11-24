"""Battery suite for tools/seller_reviews_board.py - AC-SVRB1..6.

WHY THIS SUITE EXISTS (measured at R3431, not assumed):
api_seller_reviews shipped with its own AC-AMRC6 law, but the operator holds
api_review_queue and the outside reader holds api_public_listings while the
seller had no page at all: a git grep over tools/ and preview/ answered zero
hits, so "which of my listings are waiting, which were refused and why, and how
many times did I resubmit" could only be asked of a shell. R3431 renders one
summary table and one section per seller; this suite grades the page, not the
face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3431 PIN
BEFORE the driver existed):
  AC-SVRB1 the page and its json land, the json carries exactly the pinned
           payload key set, every seller block carries the shipped 8-key
           envelope, every listing row the shipped 10 keys, seller_count
           equals the block count, the report points at a file that exists,
           and the four source fingerprints are recorded.
  AC-SVRB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates sellers through the shipped board
           face, reads api_seller_reviews() per seller, and requires the page
           json's sellers (including every row and the disclaimer) to equal
           that reading item for item - no typed fixture.
  AC-SVRB3 the face's identities hold: listing_count is the row count, each of
           the three verdict counts is that verdict's tally, the resubmit total
           is the row sum, rows run in ascending listing_id with no repeat, a
           refusal reason appears exactly on refused rows, a reviewed stamp
           appears exactly off pending rows, and every cycle is at least 1.
  AC-SVRB4 the page reads honestly: one section per seller marked data-seller,
           every listing row marked data-state, a named badge per verdict, the
           reason printed on refused rows and the dash elsewhere, no bare None,
           and the disclaimer rides on the page.
  AC-SVRB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, the not-advice sentence is
           present, and there are zero external links.
  AC-SVRB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with AC-AMRC arms.

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
TOOL = os.path.join(ROOT, "tools", "seller_reviews_board.py")
HTML = os.path.join(ROOT, "preview", "seller-reviews-board.html")
JSONF = os.path.join(ROOT, "preview", "seller-reviews-board.json")
COPY = os.path.join(ROOT, "preview", "seller-reviews-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_reviewcycle.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-reviews-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "scope", "seller_count",
    "sellers", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "dev_account", "listing_count", "pending_count", "approved_count",
    "refused_count", "resubmit_count", "disclaimer", "rows",
}
ROW_KEYS = {
    "listing_id", "listing_key", "title", "token_price", "delisted",
    "review_cycle", "review_state", "review_reason", "reviewed_utc",
    "resubmit_count",
}
STATES = ("pending", "approved", "refused")

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
    tmp_root = tempfile.mkdtemp(prefix="svrb-suite-")
    db = os.path.join(tmp_root, "svrb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        sellers = sorted({str(row["dev_account"]) for row in board["listings"]})
        envelopes = [dict(am.api_seller_reviews(dev)) for dev in sellers]
        return envelopes, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("svrb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def envelope_problems(block, label):
    problems = []
    rows = list(block["rows"])
    if int(block["listing_count"]) != len(rows):
        problems.append("%s listing_count" % label)
    for state in STATES:
        want = sum(1 for row in rows if row["review_state"] == state)
        if int(block["%s_count" % state]) != want:
            problems.append("%s %s_count" % (label, state))
    if int(block["resubmit_count"]) != sum(int(row["resubmit_count"])
                                           for row in rows):
        problems.append("%s resubmit_count" % label)
    ids = [int(row["listing_id"]) for row in rows]
    if ids != sorted(ids):
        problems.append("%s order" % label)
    if len(ids) != len(set(ids)):
        problems.append("%s duplicate id" % label)
    for row in rows:
        state = row["review_state"]
        name = "%s/%s" % (label, row["listing_id"])
        if state not in STATES:
            problems.append("%s state" % name)
            continue
        if (row["review_reason"] is None) != (state != "refused"):
            problems.append("%s reason scope" % name)
        if (row["reviewed_utc"] is None) != (state == "pending"):
            problems.append("%s stamp scope" % name)
        if int(row["review_cycle"]) < 1:
            problems.append("%s cycle" % name)
        if int(row["resubmit_count"]) < 0:
            problems.append("%s resubmit" % name)
        if not str(row["listing_key"] or "").strip():
            problems.append("%s key" % name)
        if not str(row["title"] or "").strip():
            problems.append("%s title" % name)
    return problems


def probe_envelope():
    """Three rows, one per verdict: the demo world only ever has pending."""
    rows = [
        {"listing_id": 1, "listing_key": "alpha", "title": "Alpha API",
         "token_price": 10, "delisted": False, "review_cycle": 1,
         "review_state": "pending", "review_reason": None,
         "reviewed_utc": None, "resubmit_count": 0},
        {"listing_id": 2, "listing_key": "beta", "title": "Beta API",
         "token_price": 3, "delisted": False, "review_cycle": 2,
         "review_state": "refused", "review_reason": "price too low",
         "reviewed_utc": "2026-09-30T00:00:00Z", "resubmit_count": 1},
        {"listing_id": 3, "listing_key": "gamma", "title": "Gamma API",
         "token_price": 5, "delisted": True, "review_cycle": 1,
         "review_state": "approved", "review_reason": None,
         "reviewed_utc": "2026-09-28T00:00:00Z", "resubmit_count": 0},
    ]
    return {
        "dev_account": "usr:probe", "listing_count": 3, "pending_count": 1,
        "approved_count": 1, "refused_count": 1,
        "resubmit_count": sum(row["resubmit_count"] for row in rows),
        "disclaimer": "probe disclaimer", "rows": rows,
    }


def empty_envelope():
    return {
        "dev_account": "usr:empty", "listing_count": 0, "pending_count": 0,
        "approved_count": 0, "refused_count": 0, "resubmit_count": 0,
        "disclaimer": "probe disclaimer", "rows": [],
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    sellers = doc.get("sellers") or []

    # ---- AC-SVRB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelopes_ok = all(set(block.keys()) == ENVELOPE_KEYS for block in sellers)
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for block in sellers for row in (block.get("rows") or []))
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-SVRB1", landed and keys == PAYLOAD_KEYS and envelopes_ok and rows_ok
       and sources_ok and bool(sellers)
       and int(doc.get("seller_count", -1)) == len(sellers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelopes=%s rows=%s sources=%s "
       "count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelopes_ok, rows_ok, sources_ok,
          len(sellers), int(doc.get("seller_count", -1)), report_ok))

    # ---- AC-SVRB2: every printed number is the shipped face's own.
    live_sellers, live_disclaimer = live_world()
    same = json.dumps(sellers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in ENVELOPE_KEYS} for block in live_sellers],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-SVRB2", same and disc_same and bool(sellers),
       "sellers_same=%s disclaimer_same=%s sellers=%d rows=%d"
       % (same, disc_same, len(sellers),
          sum(len(b["rows"]) for b in sellers)))

    # ---- AC-SVRB3: the face's identities hold on these envelopes.
    problems = []
    for block in sellers:
        problems.extend(envelope_problems(block, str(block.get("dev_account"))))
    ok("AC-SVRB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-SVRB4: honest page face, badges, dashes, quiet empty scope.
    dash = labels.get("none", "-")
    sections = len(re.findall(r'<div class="?card"? data-seller="', page))
    rows_marked = len(re.findall(r'data-state="(?:pending|approved|refused)"',
                                page))
    landed_rows = sum(len(b["rows"]) for b in sellers)
    state_counts = {state: sum(1 for b in sellers for r in b["rows"]
                               if r["review_state"] == state)
                    for state in STATES}
    dash_cells = page.count("<td>%s</td>" % dash)
    reasons = sum(1 for b in sellers for r in b["rows"]
                  if r["review_reason"])
    no_none = ">None<" not in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_states", "law_reason", "law_stamp", "law_order",
             "law_scope", "law_reason_scope", "law_resubmit",
             "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    empty_ok = probe_ok = False
    try:
        driver = load_driver()
        empty_html = driver.build_html([empty_envelope()], labels,
                                       "2026-01-01 00:00:00Z",
                                       "probe disclaimer")
        empty_ok = (labels.get("empty_scope", "") in empty_html
                    and ">None<" not in empty_html)
        probe_html = driver.build_html([probe_envelope()], labels,
                                       "2026-01-01 00:00:00Z",
                                       "probe disclaimer")
        probe_ok = (
            probe_html.count('data-state="refused"') == 1
            and probe_html.count('data-state="approved"') == 1
            and probe_html.count('data-state="pending"') == 1
            and "price too low" in probe_html
            and labels.get("badge_refused", "") in probe_html
            and labels.get("badge_approved", "") in probe_html
            and labels.get("badge_pending", "") in probe_html
            and labels.get("label_delisted", "") in probe_html
            and labels.get("label_live", "") in probe_html
            and ">None<" not in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-SVRB4", sections == len(sellers) and rows_marked == landed_rows
       and all(labels.get("badge_" + state, "") in page
               for state in STATES)
       and no_none and laws_ok and empty_ok and probe_ok,
       "sections=%d/%d rows_marked=%d/%d states=%s dash_cells=%d reasons=%d "
       "laws=%s empty_probe=%s verdict_probe=%s bare_none=%s"
       % (sections, len(sellers), rows_marked, landed_rows, state_counts,
          dash_cells, reasons, laws_ok, empty_ok, probe_ok, not no_none))

    # ---- AC-SVRB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    not_advice = labels.get("law_notadvice", "") in page
    external = len(re.findall(r"https?://", page))
    ok("AC-SVRB5", aigc and on_page and not_advice and external == 0,
       "aigc=%s disclaimer_on_page=%s not_advice=%s external_links=%d"
       % (aigc, on_page, not_advice, external))

    # ---- AC-SVRB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r'\),\s*(\d+)\)', registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-AMRC" in read(FACE_SUITE)
    ok("AC-SVRB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
