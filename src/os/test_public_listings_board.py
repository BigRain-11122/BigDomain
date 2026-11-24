"""Battery suite for tools/public_listings_board.py - AC-PLB1..6.

WHY THIS SUITE EXISTS (measured at R3422, not assumed):
api_public_listings shipped with its own AC-AMPI4 criteria
(src/sandbox/ledger/test_apimarket_provideridentity.py on disk) but a git grep
over tools/ and preview/ answered rc=1 with zero hits, so the question "what
does the outside reader see on the shelf right now - review state, registered
provider identity, AIGC label, price" could not be opened by anyone. R3422
renders the whole shelf on one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3422 PIN
BEFORE the driver existed):
  AC-PLB1 the page and its json land, the json carries exactly the pinned
           16-key payload set, every listing row carries the shipped 13 keys,
           listing_count equals the row count, and the report points at a
           file that exists.
  AC-PLB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, reads api_public_listings(), and requires the
           page json's listings (including the disclaimer) to equal that
           reading item for item - no typed fixture.
  AC-PLB3 the face's identities hold: the disclosure flag equals the presence
           of both the provider name and the credit code, the review state is
           one of the three shipped words with a reason only on a refusal and
           a review stamp only off pending, rows are strictly ascending by
           listing id, the three shipped counters equal their row counts, the
           page's own counts recompute, and the pending count equals the
           review queue face's pending_count.
  AC-PLB4 the page reads honestly: one marked row per listing, an absent
           reason/stamp/provider printed as the dash instead of a zero, the two
           shipped flags printed side by side with the page saying out loud
           that it does not decide launch readiness, no bare None, and an
           empty world handed to the driver's own renderer prints the explicit
           empty sentence instead of a fake row (in-memory probe only).
  AC-PLB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-PLB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with AC-AMPI arms.

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
TOOL = os.path.join(ROOT, "tools", "public_listings_board.py")
HTML = os.path.join(ROOT, "preview", "public-listings-board.html")
JSONF = os.path.join(ROOT, "preview", "public-listings-board.json")
COPY = os.path.join(ROOT, "preview", "public-listings-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_provideridentity.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-public-listings-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "source_face", "listing_count",
    "review_pending_count", "disclosure_ok_count", "ai_label_count",
    "disclosed_and_labeled", "seller_count", "shelf_total", "top_price",
    "listings", "disclaimer", "report", "sources", "sizes",
}
LISTING_KEYS = {
    "listing_id", "dev_account", "listing_key", "title", "token_price",
    "ai_label", "listed_utc", "provider_name", "credit_code",
    "disclosure_ok", "review_state", "review_reason", "reviewed_utc",
}
STATES = {"pending", "approved", "refused"}

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
    tmp_root = tempfile.mkdtemp(prefix="plb-suite-")
    db = os.path.join(tmp_root, "plb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        env = dict(am.api_public_listings())
        queue = dict(am.api_review_queue())
        return env, queue
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("plb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_problems(env, queue):
    problems = []
    rows = env.get("listings") or []
    if int(env["listing_count"]) != len(rows):
        problems.append("listing_count")
    pending = [row for row in rows if row["review_state"] == "pending"]
    if int(env["review_pending_count"]) != len(pending):
        problems.append("review_pending_count")
    if int(env["disclosure_ok_count"]) != len(
            [row for row in rows if row["disclosure_ok"]]):
        problems.append("disclosure_ok_count")
    if int(queue.get("pending_count", -1)) != int(env["review_pending_count"]):
        problems.append("cross-face pending")
    previous = None
    for row in rows:
        tag = "listing %s" % row["listing_id"]
        lid = int(row["listing_id"])
        if previous is not None and lid <= previous:
            problems.append("%s order" % tag)
        previous = lid
        if row["review_state"] not in STATES:
            problems.append("%s state" % tag)
        identity = (row["provider_name"] is not None
                    and row["credit_code"] is not None)
        if bool(row["disclosure_ok"]) != identity:
            problems.append("%s disclosure" % tag)
        if row["review_state"] == "refused":
            if not str(row["review_reason"] or "").strip():
                problems.append("%s reason missing" % tag)
        elif row["review_reason"] is not None:
            problems.append("%s stray reason" % tag)
        if row["review_state"] == "pending":
            if row["reviewed_utc"] is not None:
                problems.append("%s stray stamp" % tag)
        elif row["reviewed_utc"] is None:
            problems.append("%s stamp missing" % tag)
    return problems


def probe_empty():
    """An empty envelope: never landed, only handed to the driver renderer."""
    return {"listing_count": 0, "disclosure_ok_count": 0,
            "review_pending_count": 0, "disclaimer": "",
            "listings": []}


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    rows = doc.get("listings") or []

    # ---- AC-PLB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    rows_ok = all(set(row.keys()) == LISTING_KEYS for row in rows)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-PLB1", landed and keys == PAYLOAD_KEYS and rows_ok and sources_ok
       and int(doc.get("listing_count", -1)) == len(rows) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s rows=%s sources=%s "
       "count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), rows_ok, sources_ok,
          len(rows), int(doc.get("listing_count", -1)), report_ok))

    # ---- AC-PLB2: every printed number is the shipped face's own.
    live_env, live_queue = live_world()
    rows_same = json.dumps(rows, sort_keys=True) == json.dumps(
        [{key: row[key] for key in LISTING_KEYS}
         for row in live_env["listings"]], sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_env["disclaimer"])
    counters_same = (
        int(doc.get("listing_count", -1)) == int(live_env["listing_count"])
        and int(doc.get("review_pending_count", -1))
        == int(live_env["review_pending_count"])
        and int(doc.get("disclosure_ok_count", -1))
        == int(live_env["disclosure_ok_count"]))
    ok("AC-PLB2", rows_same and disc_same and counters_same and bool(rows),
       "identical=%s disclaimer_same=%s counters_same=%s rows=%d"
       % (rows_same, disc_same, counters_same, len(rows)))

    # ---- AC-PLB3: the face's identities hold, including the cross-face law.
    problems = identity_problems(live_env, live_queue) if rows \
        else ["no rows"]
    driver = load_driver()
    stats = driver.derived(doc) if rows else {}
    stats_ok = bool(rows) and (
        int(doc["ai_label_count"]) == stats["ai_label_count"]
        and int(doc["disclosed_and_labeled"]) == stats["disclosed_and_labeled"]
        and int(doc["seller_count"]) == stats["seller_count"]
        and int(doc["shelf_total"]) == stats["shelf_total"]
        and doc["top_price"] == stats["top_price"])
    ok("AC-PLB3", not problems and stats_ok,
       "problems=%s stats=%s"
       % (problems[:4] if problems else [], stats_ok))

    # ---- AC-PLB4: honest page face, dashes, side-by-side flags, empty probe.
    dash = labels.get("none", "-")
    marked = all(('data-listing="%s"' % row["listing_id"]) in page
                 for row in rows)
    absent = [row for row in rows if row["review_reason"] is None]
    dash_reason = all('<td class="">%s</td>' % dash in page for _ in absent)
    pending_rows = [row for row in rows if row["review_state"] == "pending"]
    dash_stamp = all('<td class="">%s</td>' % dash in page
                     for _ in pending_rows)
    flag_yes = '<td class="flag-yes">%s</td>' % labels.get("yes", "yes")
    flag_no = '<td class="flag-no">%s</td>' % labels.get("no", "no")
    flags_ok = all(
        ((flag_yes if bool(row["disclosure_ok"]) else flag_no) in page
         and (flag_yes if int(row["ai_label"]) == 1 else flag_no) in page)
        for row in rows)
    stand_in = ">None<" in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_pending", "law_disclosure", "law_label",
             "law_both", "law_reason", "law_order", "law_cross",
             "law_notready", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    empty_probe_ok = False
    try:
        probe_html = driver.build_html(probe_empty(), labels,
                                      "2026-01-01 00:00:00Z",
                                      doc.get("disclaimer") or "")
        empty_probe_ok = (labels.get("empty", "") in probe_html
                          and ">None<" not in probe_html
                          and "<tr data-listing=" not in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-PLB4", marked and dash_reason and dash_stamp and flags_ok
       and not stand_in and laws_ok and empty_probe_ok,
       "rows=%s absent=%d dash_reason=%s pending=%d dash_stamp=%s flags=%s "
       "laws=%s empty_probe=%s stand_in_none=%s"
       % (marked, len(absent), dash_reason, len(pending_rows), dash_stamp,
          flags_ok, laws_ok, empty_probe_ok, stand_in))

    # ---- AC-PLB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-PLB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-PLB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-AMPI" in read(FACE_SUITE)
    ok("AC-PLB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
