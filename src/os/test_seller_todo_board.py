"""Battery suite for tools/seller_todo_board.py - AC-STDB1..6.

WHY THIS SUITE EXISTS (measured at R3433, not assumed):
api_seller_inbox answers unanswered ratings, api_seller_questions unanswered
questions, api_claims the claim queue and the R2137 disputed state lived only
inside one claim thread; api_seller_todo merges all four into one queue with
its own AC-AMTD1..8 law, but a git grep over tools/ and preview/ answered zero
hits, so "what do I owe right now, and how long has the oldest one waited"
could only be asked of a shell. R3433 renders one summary table and one card
per seller; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3433 PIN
BEFORE the driver existed):
  AC-STDB1 the page and its json land, the json carries exactly the pinned
           payload key set, every seller block carries the shipped 11-key
           envelope, every duty row the shipped 8 keys, seller_count equals
           the block count, the report points at a file that exists, and the
           four source fingerprints are recorded.
  AC-STDB2 the data is the shipped face's own: the suite builds its own
           throwaway world (factory demo plus the driver's shipped-door duty
           fixture), enumerates sellers through the shipped board face, reads
           api_seller_todo() per seller, and requires the page json's sellers
           (including every row and the disclaimer) to equal that reading item
           for item - no typed fixture.
  AC-STDB3 the face's identities hold: the total is the row count, the four
           family counts are row tallies that partition the rows, listing_count
           is the distinct listing count, oldest_utc/oldest_kind are the first
           row (and None exactly when the queue is empty), rows run in the
           pinned (since_utc, kind rank, ref_id) order, every kind is one of
           the four families, and detail is None on rating rows only.
  AC-STDB4 the page reads honestly: one card per seller marked data-seller,
           every row marked data-kind and data-ref, a named badge per family,
           a dash wherever the face publishes None, no bare None, and both the
           empty-seller and four-family shapes render.
  AC-STDB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer and the not-advice sentence are on the page,
           with zero external links.
  AC-STDB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, the
           producer row is recorded for the json pair, and the shipped face's
           own suite is still on disk with AC-AMTD arms.

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
TOOL = os.path.join(ROOT, "tools", "seller_todo_board.py")
HTML = os.path.join(ROOT, "preview", "seller-todo-board.html")
JSONF = os.path.join(ROOT, "preview", "seller-todo-board.json")
COPY = os.path.join(ROOT, "preview", "seller-todo-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
INDEXER = os.path.join(ROOT, "tools", "deliverable_index.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_sellertodo.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-todo-board"
PAIR = "seller-todo-board.json"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "scope", "seller_count",
    "sellers", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "dev_account", "total_count", "rating_count", "question_count",
    "claim_open_count", "claim_disputed_count", "listing_count",
    "oldest_utc", "oldest_kind", "rows", "disclaimer",
}
ROW_KEYS = {
    "kind", "ref_id", "listing_id", "listing_key", "listing_title",
    "counterparty", "since_utc", "detail",
}
KIND_RANK = {"rating": 0, "question": 1, "claim_open": 2,
             "claim_disputed": 3}

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
    spec = importlib.util.spec_from_file_location("stdb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_world():
    """The shipped face's own reading over the suite's throwaway world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    driver = load_driver()
    tmp_root = tempfile.mkdtemp(prefix="stdb-suite-")
    db = os.path.join(tmp_root, "stdb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        driver.seed_duty(am)
        board = dict(am.api_board())
        sellers = sorted({str(row["dev_account"]) for row in board["listings"]})
        envelopes = [dict(am.api_seller_todo(dev)) for dev in sellers]
        return envelopes, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def envelope_problems(block, label):
    problems = []
    rows = list(block["rows"])
    if int(block["total_count"]) != len(rows):
        problems.append("%s total_count" % label)
    tallies = {"rating": 0, "question": 0, "claim_open": 0,
               "claim_disputed": 0}
    for row in rows:
        kind = str(row["kind"])
        if kind not in tallies:
            problems.append("%s unknown kind %s" % (label, kind))
            continue
        tallies[kind] += 1
    for kind in tallies:
        if int(block[kind + "_count"]) != tallies[kind]:
            problems.append("%s %s_count" % (label, kind))
    if sum(tallies.values()) != len(rows):
        problems.append("%s partition" % label)
    if int(block["listing_count"]) != len({int(r["listing_id"])
                                           for r in rows}):
        problems.append("%s listing_count" % label)
    if rows:
        if block["oldest_utc"] != rows[0]["since_utc"]:
            problems.append("%s oldest_utc" % label)
        if block["oldest_kind"] != rows[0]["kind"]:
            problems.append("%s oldest_kind" % label)
    elif block["oldest_utc"] is not None or block["oldest_kind"] is not None:
        problems.append("%s empty oldest" % label)
    order = [(str(r["since_utc"]), KIND_RANK.get(str(r["kind"]), 9),
              int(r["ref_id"])) for r in rows]
    if order != sorted(order):
        problems.append("%s row order" % label)
    for row in rows:
        name = "%s/%s" % (label, row["ref_id"])
        if row["detail"] is None and str(row["kind"]) != "rating":
            problems.append("%s missing detail" % name)
        if str(row["kind"]) == "rating" and row["detail"] is not None:
            problems.append("%s rating carries detail" % name)
        if not str(row["listing_key"] or "").strip():
            problems.append("%s empty key" % name)
        if not str(row["counterparty"] or "").startswith("usr:"):
            problems.append("%s counterparty" % name)
        if not str(row["since_utc"] or "").strip():
            problems.append("%s since" % name)
    return problems


def row_of(kind, ref, listing, key, title, who, since, detail):
    return {"kind": kind, "ref_id": ref, "listing_id": listing,
            "listing_key": key, "listing_title": title,
            "counterparty": who, "since_utc": since, "detail": detail}


def probe_envelope():
    rows = [
        row_of("rating", 1, 1, "alpha", "Alpha API", "usr:bob",
               "2026-01-01T00:00:00Z", None),
        row_of("question", 1, 1, "alpha", "Alpha API", "usr:bob",
               "2026-01-02T00:00:00Z", "does it batch?"),
        row_of("claim_open", 1, 2, "beta", "Beta API", "usr:carol",
               "2026-01-03T00:00:00Z", "returns 500"),
        row_of("claim_disputed", 2, 2, "beta", "Beta API", "usr:dave",
               "2026-01-04T00:00:00Z", "still broken"),
    ]
    return {
        "dev_account": "usr:probe", "total_count": 4,
        "rating_count": 1, "question_count": 1, "claim_open_count": 1,
        "claim_disputed_count": 1, "listing_count": 2,
        "oldest_utc": rows[0]["since_utc"], "oldest_kind": "rating",
        "rows": rows, "disclaimer": "probe disclaimer",
    }


def empty_envelope():
    return {
        "dev_account": "usr:empty", "total_count": 0, "rating_count": 0,
        "question_count": 0, "claim_open_count": 0,
        "claim_disputed_count": 0, "listing_count": 0,
        "oldest_utc": None, "oldest_kind": None, "rows": [],
        "disclaimer": "probe disclaimer",
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    sellers = doc.get("sellers") or []

    # ---- AC-STDB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelopes_ok = all(set(block.keys()) == ENVELOPE_KEYS for block in sellers)
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for block in sellers for row in (block.get("rows") or []))
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-STDB1", landed and keys == PAYLOAD_KEYS and envelopes_ok and rows_ok
       and sources_ok and bool(sellers)
       and int(doc.get("seller_count", -1)) == len(sellers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelopes=%s rows=%s sources=%s "
       "count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelopes_ok, rows_ok, sources_ok,
          len(sellers), int(doc.get("seller_count", -1)), report_ok))

    # ---- AC-STDB2: every printed number is the shipped face's own.
    live_sellers, live_disclaimer = live_world()
    same = json.dumps(sellers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in ENVELOPE_KEYS} for block in live_sellers],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-STDB2", same and disc_same and bool(sellers),
       "sellers_same=%s disclaimer_same=%s sellers=%d duties=%d disputed=%d"
       % (same, disc_same, len(sellers),
          sum(int(b["total_count"]) for b in sellers),
          sum(int(b["claim_disputed_count"]) for b in sellers)))

    # ---- AC-STDB3: the face's identities hold on these envelopes.
    problems = []
    for block in sellers:
        problems.extend(envelope_problems(block, str(block.get("dev_account"))))
    ok("AC-STDB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-STDB4: honest page face, badges, dashes, quiet empty scope.
    dash = labels.get("none", "-")
    sections = len(re.findall(r'<div class="?card"? data-seller="', page))
    rows_marked = len(re.findall(r'data-kind="[a-z_]+"', page))
    refs_marked = len(re.findall(r'data-ref="\d+"', page))
    landed_rows = sum(len(b["rows"]) for b in sellers)
    landed_kinds = {str(r["kind"]) for b in sellers for r in b["rows"]}
    want_dash = sum(1 for b in sellers for r in b["rows"]
                    if r["detail"] is None)
    want_dash += 3 * sum(1 for b in sellers if not b["rows"])
    dash_cells = page.count(">%s<" % dash)
    no_none = ">None<" not in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_partition", "law_listings", "law_oldest",
             "law_order", "law_family", "law_detail", "law_scope",
             "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    badges_ok = all(("badge " + kind.replace("_", "-")) in page
                    for kind in landed_kinds)
    empty_ok = probe_ok = False
    try:
        driver = load_driver()
        empty_html = driver.build_html([empty_envelope()], labels,
                                       "2026-01-01 00:00:00Z",
                                       "probe disclaimer")
        empty_ok = (labels.get("empty_scope", "") in empty_html
                    and ">None<" not in empty_html
                    and empty_html.count(">%s<" % dash) == 3)
        probe_html = driver.build_html([probe_envelope()], labels,
                                       "2026-01-01 00:00:00Z",
                                       "probe disclaimer")
        probe_ok = (
            len(re.findall(r'data-kind="[a-z_]+"', probe_html)) == 4
            and len(re.findall(r'data-ref="\d+"', probe_html)) == 4
            and all(("badge " + kind.replace("_", "-")) in probe_html
                    for kind in KIND_RANK)
            and probe_html.count(">%s<" % dash) == 1
            and ">None<" not in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-STDB4", sections == len(sellers) and rows_marked == landed_rows
       and refs_marked == landed_rows and no_none and laws_ok and badges_ok
       and dash_cells == want_dash and want_dash > 0 and empty_ok and probe_ok,
       "sections=%d/%d rows_marked=%d/%d refs=%d/%d dash_cells=%d/%d "
       "laws=%s badges=%s empty_probe=%s family_probe=%s bare_none=%s"
       % (sections, len(sellers), rows_marked, landed_rows, refs_marked,
          landed_rows, dash_cells, want_dash, laws_ok, badges_ok, empty_ok,
          probe_ok, not no_none))

    # ---- AC-STDB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    not_advice = labels.get("law_notadvice", "") in page
    external = len(re.findall(r"https?://", page))
    ok("AC-STDB5", aigc and on_page and not_advice and external == 0,
       "aigc=%s disclaimer_on_page=%s not_advice=%s external_links=%d"
       % (aigc, on_page, not_advice, external))

    # ---- AC-STDB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r'\),\s*(\d+)\)', registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    pair_row = ('"%s": "tools/seller_todo_board.py"' % PAIR) in read(INDEXER)
    face_ok = os.path.exists(FACE_SUITE) and "AC-AMTD" in read(FACE_SUITE)
    ok("AC-STDB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and pair_row and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d pair_row=%s face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, pair_row, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
