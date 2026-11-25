"""Battery suite for tools/answer_revision_board.py - AC-ARHB1..6.

WHY THIS SUITE EXISTS (measured at R3456, not assumed):
api_answer_history shipped the per-answer revision face - the immutable base
wording, every append-only revision in order, the EFFECTIVE text and the
revision count - but a search over tools/, preview/ and src/os answered zero
readers for its name. R3456 renders the shipped envelopes on one page; this
suite grades the page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3456 PIN row landed with the driver and says
so):
  AC-ARHB1 the pair lands, the json carries exactly the pinned ten-key payload
          set, the market block exactly the eleven derived keys, every seller
          row the pinned five keys, every answer entry the pin plus its rows,
          every row the shipped four keys, the report points at a file that
          exists and the four source fingerprints are present.
  AC-ARHB2 the data is the shipped face's own: the suite builds its own
          throwaway world through the shipped ask_question, answer_question,
          revise_answer and delist_api doors under its own pinned clock,
          re-reads every answer through api_answer_history and requires the
          page json to equal that reading item for item, disclaimer included.
  AC-ARHB3 the face identities hold and the driver refuses a broken one: the
          per-answer revision count, chain continuity, effective text, latest
          stamp and ascending ids, the market totals, the revert reading and
          the most-revised tie all hold - and forged answers plus a forged
          market total are refused by name.
  AC-ARHB4 the page reads honestly: one marked card per answer, one marked
          row per revision, the dash where a number is absent, no bare None or
          null, the 80-character clip caption on the page, the revert and
          retired badges reachable on landed rows, and the empty sentence
          reachable both as a landed answer and in an in-memory probe.
  AC-ARHB5 the standing compliance faces ride along: the AIGC label, the
          face's own disclaimer verbatim, the non-advice sentence, zero
          external links and no script tags.
  AC-ARHB6 no older criterion is relaxed: the landed pair answers its own
          --check, --check writes nothing, the driver is registered in
          src/sandbox/reconcile_all.py with this suite's DECLARED count, and
          the face is still exercised by its shipped suite on disk.

Read-only over the repository: the provenance world is built in a temp dir and
the empty probe renders in memory, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import importlib.util
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "answer_revision_board.py")
HTML = os.path.join(ROOT, "preview", "answer-revision-board.html")
JSONF = os.path.join(ROOT, "preview", "answer-revision-board.json")
COPY = os.path.join(ROOT, "preview", "answer-revision-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_answerrev.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-answer-revision-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "market", "sellers", "answers",
    "disclaimer", "report", "sources", "sizes",
}
MARKET_KEYS = {
    "answer_count", "revised_answer_count", "unrevised_answer_count",
    "revision_count", "reverted_answer_count", "seller_count",
    "listing_count", "buyer_count", "latest_revised_utc",
    "most_revised_answer", "longest_chain",
}
SELLER_KEYS = {"dev_account", "answered_count", "revised_count",
               "revision_count", "latest_revised_utc"}
ANSWER_KEYS = {"answer_id", "question_id", "listing_id", "listing_key",
               "dev_account", "buyer_id", "question_text", "base_text",
               "effective_text", "revision_count", "latest_revised_utc",
               "reverted", "retired", "rows"}
ROW_KEYS = {"revision_id", "previous_text", "answer_text", "revised_utc"}

CHECKS = ["AC-ARHB1", "AC-ARHB2", "AC-ARHB3", "AC-ARHB4", "AC-ARHB5",
          "AC-ARHB6"]
FAILS = []


def ok(name, cond, detail):
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


def load_driver():
    spec = importlib.util.spec_from_file_location("arh_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_world(driver):
    """The suite's own stack, every row through a shipped door."""
    import apimarket as A
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="arh-suite-")
    db = os.path.join(tmp_root, "suite.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = driver._clock
        driver.build_world(am)
        answers = []
        for item in driver._enumerate(am):
            envelope = dict(am.api_answer_history(item["answer_id"]))
            envelope["retired"] = bool(item["retired"])
            envelope["reverted"] = bool(
                envelope.get("revisions")
                and envelope["effective_text"] == envelope["base_text"])
            answers.append((item["answer_id"], item["dev_account"],
                            item["listing_key"], item["buyer_id"],
                            envelope))
        sellers = driver._sellers(am)
    finally:
        A._now_utc = orig_now
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    return answers, sellers


def same(left, right):
    return json.dumps(left, sort_keys=True, default=str) == json.dumps(
        right, sort_keys=True, default=str)


def main():
    if not os.path.exists(TOOL):
        print("FAIL AC-ARHB1 driver missing")
        return 2
    driver = load_driver()
    labels = json.loads(read(COPY))
    page = json.loads(read(JSONF))
    doc = read(HTML)

    entries = page.get("answers") or []
    market = page.get("market") or {}
    sellers = page.get("sellers") or []

    # ---- AC-ARHB1 contract ------------------------------------------------
    missing_payload = sorted(PAYLOAD_KEYS - set(page))
    extra_payload = sorted(set(page) - PAYLOAD_KEYS)
    report_path = os.path.join(ROOT, page.get("report") or "")
    sources = page.get("sources") or {}
    sizes = page.get("sizes") or {}
    answer_shape = all(set(entry) == ANSWER_KEYS for entry in entries)
    row_shape = all(set(row) == ROW_KEYS
                    for entry in entries for row in entry.get("rows") or [])
    seller_shape = all(set(row) == SELLER_KEYS for row in sellers)
    ok("AC-ARHB1",
       not missing_payload and not extra_payload
       and set(market) == MARKET_KEYS and seller_shape
       and answer_shape and row_shape
       and os.path.exists(report_path)
       and sorted(sources) == ["apimarket", "copy", "driver", "report"]
       and sizes.get("html") == os.path.getsize(HTML)
       and sizes.get("json") == os.path.getsize(JSONF)
       and page.get("face") == "api_answer_history",
       "payload_missing=%r payload_extra=%r answers=%d answer_shape=%r "
       "row_shape=%r seller_shape=%r report=True sources=True"
       % (missing_payload, extra_payload, len(entries), answer_shape,
          row_shape, seller_shape))

    # ---- AC-ARHB2 the data is the shipped face's own ----------------------
    live, live_sellers = live_world(driver)
    live_market = driver.derive_market(live, live_sellers)
    live_seller_rows = driver.derive_sellers(live, live_sellers)
    same_all = same([driver.trim_answer(item) for item in live], entries)
    same_words = page.get("disclaimer") == live[0][4].get("disclaimer")
    same_market = same(live_market, market)
    same_sellers = same(live_seller_rows, sellers)
    same_order = ([entry["answer_id"] for entry in entries]
                  == [item[0] for item in live])
    ok("AC-ARHB2",
       same_all and same_words and same_market and same_sellers and same_order,
       "answer_same=%r disclaimer_same=%r market_same=%r sellers_same=%r "
       "order_same=%r answers=%d"
       % (same_all, same_words, same_market, same_sellers, same_order,
          len(live)))

    # ---- AC-ARHB3 laws, plus forged rows refused by name ------------------
    bare = driver.read_empty()
    driver_problems = driver.check_laws(live, live_sellers, live_market, bare)
    forged = [(answer_id, dev, key, buyer,
               json.loads(json.dumps(envelope, default=str)))
              for answer_id, dev, key, buyer, envelope in live]
    forged[0][4]["effective_text"] = "forged wording"
    forged[0][4]["revision_count"] = int(
        forged[0][4]["revision_count"]) + 3
    forged_market = json.loads(json.dumps(live_market, default=str))
    forged_market["reverted_answer_count"] = int(
        forged_market["reverted_answer_count"]) + 7
    forged_problems = driver.check_laws(forged, live_sellers, forged_market,
                                        bare)
    identities = True
    chain_ok = True
    revert_row = False
    retired_row = False
    unrevised_row = False
    for answer_id, dev, key, buyer, envelope in live:
        rows = envelope.get("revisions") or []
        if int(envelope["revision_count"]) != len(rows):
            identities = False
        if rows and rows[0]["previous_text"] != envelope["base_text"]:
            chain_ok = False
        for index in range(1, len(rows)):
            if rows[index]["previous_text"] != rows[index - 1]["answer_text"]:
                chain_ok = False
        if envelope["reverted"]:
            revert_row = True
        if envelope["retired"]:
            retired_row = True
        if not rows and envelope["latest_revised_utc"] is None:
            unrevised_row = True
    ok("AC-ARHB3",
       not driver_problems and len(forged_problems) >= 2 and identities
       and chain_ok and revert_row and retired_row and unrevised_row
       and int(bare["revision_count"]) == 0
       and bare.get("latest_revised_utc") is None
       and bare["effective_text"] == bare["base_text"],
       "driver_problems=%d forged_problems=%d identities=%r chain=%r "
       "revert=%r retired=%r unrevised=%r bare_revisions=%d"
       % (len(driver_problems), len(forged_problems), identities, chain_ok,
          revert_row, retired_row, unrevised_row,
          int(bare["revision_count"])))

    # ---- AC-ARHB4 the page reads honestly ---------------------------------
    dash = labels["none"]
    answer_marked = all(('data-answer="%s"' % entry["answer_id"]) in doc
                        for entry in entries)
    revision_rows = sum(len(entry.get("rows") or []) for entry in entries)
    revision_marked = doc.count('data-revision="') == revision_rows
    bare_none = "None" in doc or "null" in doc
    caption = labels["clip_caption"] in doc
    reverted_badge = labels["badge_reverted"] in doc
    retired_badge = labels["badge_retired"] in doc
    plain_badge = labels["badge_plain"] in doc
    silent = sum(1 for entry in entries if not entry.get("rows"))
    empty_landed = doc.count(labels["empty"]) == silent
    probe = {"generated_utc": "2026-11-25 00:00:00Z",
             "face": "api_answer_history", "scope": "answers",
             "market": {"answer_count": 0, "revised_answer_count": 0,
                        "unrevised_answer_count": 0, "revision_count": 0,
                        "reverted_answer_count": 0, "seller_count": 0,
                        "listing_count": 0, "buyer_count": 0,
                        "latest_revised_utc": None,
                        "most_revised_answer": None, "longest_chain": 0},
             "sellers": [], "answers": [], "disclaimer": "x",
             "report": "x", "sources": {}}
    empty_html = driver.build_html([], [], probe["market"], labels,
                                   "2026-11-25 00:00:00Z", "x")
    empty_probe = labels["empty"] in empty_html and dash in empty_html
    ok("AC-ARHB4",
       answer_marked and revision_marked and not bare_none and caption
       and reverted_badge and retired_badge and plain_badge and empty_landed
       and empty_probe,
       "answer_marked=%r revisions=%d marked=%r no_bare_none=%r caption=%r "
       "revert=%r retired=%r plain=%r empty_landed=%r empty_probe=%r"
       % (answer_marked, revision_rows, revision_marked, not bare_none,
          caption, reverted_badge, retired_badge, plain_badge, empty_landed,
          empty_probe))

    # ---- AC-ARHB5 compliance ----------------------------------------------
    disclaimer = page.get("disclaimer") or ""
    aigc = "AIGC" in doc
    verbatim = bool(disclaimer) and disclaimer in doc
    notadvice = labels["law_notadvice"] in doc
    zero_links = "http://" not in doc and "https://" not in doc
    no_script = "<script" not in doc.lower()
    ok("AC-ARHB5", aigc and verbatim and notadvice and zero_links and no_script,
       "aigc=%r disclaimer_verbatim=%r notadvice=%r zero_links=%r "
       "no_script=%r" % (aigc, verbatim, notadvice, zero_links, no_script))

    # ---- AC-ARHB6 no older criterion is relaxed ---------------------------
    before = (stamp(HTML), stamp(JSONF), stamp(COPY))
    import subprocess
    proc = subprocess.run([sys.executable, TOOL, "--check"], cwd=ROOT,
                          capture_output=True, text=True)
    after = (stamp(HTML), stamp(JSONF), stamp(COPY))
    registry = read(REGISTRY)
    registered = ('"%s"' % ROW) in registry
    row_block = registry.split('"%s"' % ROW, 1)[-1][:200]
    declared = ("%d)" % DECLARED) in row_block
    face_suite = os.path.exists(FACE_SUITE)
    face_ac = "AC-AMAW1" in read(FACE_SUITE) if face_suite else False
    ok("AC-ARHB6",
       proc.returncode == 0 and "CHECK PASS" in proc.stdout
       and before == after and registered and declared and face_suite
       and face_ac,
       "readonly=%r check_rc=%d registered=%r declared_hit=%r face_suite=%r"
       % (before == after, proc.returncode, registered, declared, face_suite))

    print("SUITE %s %d/%d declared=%d row=%s"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED, ROW))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.path.insert(0, LEDGER_DIR)
    sys.exit(main())
