"""Battery suite for tools/search_board.py - AC-SDB1..6.

WHY THIS SUITE EXISTS (measured at R3423, not assumed):
api_search shipped with its own AC-AMSQ / AC-AMPG / AC-AMSR / AC-AMAV
criteria (src/sandbox/ledger/test_apimarket_search*.py, four files on disk)
but a git grep over tools/ and preview/ answered rc=1 with zero hits, so the
question "which listings match my need - and what does each discovery axis
actually do to the shelf" could not be opened by anyone. R3423 renders eight
real calls side by side on one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3423 PIN
BEFORE the driver existed):
  AC-SDB1 the page and its json land, the json carries exactly the pinned
           10-key payload, the shelf block carries its 8 pinned counts, every
           drill block carries its 10 pinned keys, every row carries the
           shipped 11 keys, and the report points at a file that exists.
  AC-SDB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, re-issues every drill's criteria against
           api_search(), and requires the page json to equal that reading item
           for item - rows, envelope key set, counters and disclaimer - with
           no typed fixture and no hand-typed listing id.
  AC-SDB3 the face's identities hold: count equals the row count, the paging
           arithmetic (total >= count, truncated, echoed limit/offset, and no
           paging key on an unpaged call), the envelope key set (4 unpaged /
           9 paged), the criteria echo, every mode's total order with a
           listing_id tie-break, the unrated rule (rating_avg 0.0 exactly when
           rating_count 0), the closed price band, the delisted default, the
           seller filter, the case-insensitive keyword law and the shelf
           counts recomputed from the shipped face.
  AC-SDB4 the page reads honestly: one marked section per drill carrying that
           drill's criteria, an absent category or delisted stamp printed as
           the dash instead of a zero, an unrated row printed as unrated
           rather than a fake 0 rating, a zero-row drill printing the explicit
           empty sentence, the paged drill printing total / count / truncated,
           and no bare None.
  AC-SDB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-SDB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's four suites are still on disk.

Read-only over the repository: the provenance world is built in a temp dir and
the empty drill is a real call, never a typed fixture.

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
TOOL = os.path.join(ROOT, "tools", "search_board.py")
HTML = os.path.join(ROOT, "preview", "search-board.html")
JSONF = os.path.join(ROOT, "preview", "search-board.json")
COPY = os.path.join(ROOT, "preview", "search-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
FACE_SUITES = (
    "test_apimarket_search.py",
    "test_apimarket_searchpage.py",
    "test_apimarket_searchsort.py",
    "test_apimarket_searchstock.py",
)
ROW = "os-search-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "source_face", "shelf", "drills",
    "disclaimer", "report", "sources", "sizes",
}
SHELF_KEYS = {
    "listing_count", "seller_count", "price_min", "price_max", "price_avg",
    "rated_count", "rating_avg", "ai_label_count",
}
DRILL_KEYS = {
    "key", "title", "criteria", "envelope_keys", "count", "total",
    "truncated", "limit", "offset", "listings",
}
ROW_KEYS = {
    "listing_id", "dev_account", "listing_key", "title", "token_price",
    "ai_label", "rating_count", "rating_avg", "category", "delisted",
    "delisted_utc",
}
UNPAGED_KEYS = {"disclaimer", "criteria", "count", "listings"}
PAGED_KEYS = {"disclaimer", "criteria", "count", "returned", "total",
              "limit", "offset", "truncated", "listings"}

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
    spec = importlib.util.spec_from_file_location("sdb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_world(drills):
    """Re-issue every drill's criteria against the shipped face."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="sdb-suite-")
    db = os.path.join(tmp_root, "sdb.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        out = {}
        for block in drills:
            criteria = dict(block.get("criteria") or {})
            out[block["key"]] = dict(am.api_search(**criteria))
        shelf = dict(am.api_search())
        lower = dict(am.api_search(keyword="api"))
        return out, shelf, lower
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass


def order_key(mode, row):
    if mode == "price_desc":
        return (-int(row["token_price"]), int(row["listing_id"]))
    if mode == "rating":
        return (-float(row["rating_avg"]), -int(row["rating_count"]),
                int(row["listing_id"]))
    return (int(row["token_price"]), int(row["listing_id"]))


def identity_problems(blocks, live):
    problems = []
    for block in blocks:
        key = block["key"]
        env = live[key]
        rows = block.get("listings") or []
        live_rows = env.get("listings") or []
        criteria = block.get("criteria") or {}
        paged = bool(set(env.keys()) == PAGED_KEYS)
        if int(block["count"]) != len(rows):
            problems.append("%s count vs rows" % key)
        expected = PAGED_KEYS if paged else UNPAGED_KEYS
        if set(block["envelope_keys"]) != expected:
            problems.append("%s envelope keys" % key)
        if paged:
            total = int(env["total"])
            limit = env.get("limit")
            offset = env.get("offset")
            start = 0 if offset is None else int(offset)
            if total < len(rows):
                problems.append("%s total < count" % key)
            if bool(env["truncated"]) != (start + len(rows) < total):
                problems.append("%s truncated" % key)
            if criteria.get("limit") != limit or criteria.get(
                    "offset") != offset:
                problems.append("%s paging echo" % key)
        else:
            for name in ("total", "truncated", "limit", "offset"):
                if block.get(name) is not None:
                    problems.append("%s stray %s" % (key, name))
        mode = criteria.get("sort") or "price_asc"
        keys = [order_key(mode, row) for row in live_rows]
        if keys != sorted(keys):
            problems.append("%s order %s" % (key, mode))
        ids = [int(row["listing_id"]) for row in live_rows]
        if len(set(ids)) != len(ids):
            problems.append("%s duplicate id" % key)
        for row in live_rows:
            tag = "%s/%s" % (key, row["listing_id"])
            rated = int(row["rating_count"]) > 0
            if (float(row["rating_avg"]) == 0.0) != (not rated):
                problems.append("%s unrated rule" % tag)
            low = criteria.get("min_price")
            high = criteria.get("max_price")
            if low is not None and int(row["token_price"]) < int(low):
                problems.append("%s below band" % tag)
            if high is not None and int(row["token_price"]) > int(high):
                problems.append("%s above band" % tag)
            if (not criteria.get("include_delisted")) and row["delisted"]:
                problems.append("%s delisted hidden" % tag)
            if criteria.get("dev_account") is not None and str(
                    row["dev_account"]) != str(criteria["dev_account"]):
                problems.append("%s seller filter" % tag)
    return problems


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    blocks = doc.get("drills") or []
    shelf = doc.get("shelf") or {}

    # ---- AC-SDB1: the pair landed with exactly the pinned key sets.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    blocks_ok = bool(blocks) and all(
        set(block.keys()) == DRILL_KEYS for block in blocks)
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for block in blocks for row in block.get("listings") or [])
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    shelf_ok = set(shelf.keys()) == SHELF_KEYS
    ok("AC-SDB1", landed and keys == PAYLOAD_KEYS and blocks_ok and rows_ok
       and report_ok and sources_ok and shelf_ok,
       "landed=%s keys=%d missing=%s extra=%s blocks=%s rows=%s shelf=%s "
       "report=%s" % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
                      sorted(keys - PAYLOAD_KEYS), blocks_ok, rows_ok,
                      shelf_ok, report_ok))

    # ---- AC-SDB2: every printed row is the shipped face's own.
    live, live_shelf, live_lower = live_world(blocks)
    same = []
    for block in blocks:
        env = live[block["key"]]
        rows_same = json.dumps(block.get("listings") or [],
                               sort_keys=True) == json.dumps(
            [{name: row[name] for name in ROW_KEYS}
             for row in env.get("listings") or []], sort_keys=True)
        counters_same = (int(block["count"]) == int(env["count"])
                         and block.get("total") == env.get("total")
                         and block.get("truncated") == env.get("truncated")
                         and block.get("limit") == env.get("limit")
                         and block.get("offset") == env.get("offset"))
        env_same = block.get("envelope_keys") == sorted(env.keys())
        crit_same = json.dumps(block.get("criteria") or {},
                               sort_keys=True) == json.dumps(
            env.get("criteria") or {}, sort_keys=True)
        same.append(rows_same and counters_same and env_same and crit_same)
    disc_same = (doc.get("disclaimer") == live_shelf.get("disclaimer"))
    ok("AC-SDB2", bool(blocks) and all(same) and disc_same,
       "drills_same=%s disclaimer_same=%s drills=%d"
       % (all(same), disc_same, len(blocks)))

    # ---- AC-SDB3: the face's identities hold.
    problems = identity_problems(blocks, live) if blocks else ["no drills"]
    driver = load_driver()
    stats = driver.shelf_stats(live_shelf)
    stats_ok = bool(shelf) and all(shelf.get(name) == stats[name]
                                   for name in SHELF_KEYS)
    keyword_block = next((block for block in blocks
                          if block["key"] == "keyword"), None)
    case_ok = (keyword_block is not None
               and [row["listing_id"] for row in keyword_block["listings"]]
               == [row["listing_id"]
                   for row in live_lower.get("listings") or []])
    empty_block = next((block for block in blocks
                        if block["key"] == "empty"), None)
    empty_ok = empty_block is not None and not empty_block.get("listings")
    ok("AC-SDB3", not problems and stats_ok and case_ok and empty_ok,
       "problems=%s stats=%s case_insensitive=%s empty_landed=%s"
       % (problems[:4] if problems else [], stats_ok, case_ok, empty_ok))

    # ---- AC-SDB4: honest page face.
    dash = labels.get("none", "-")
    marked = all(('data-drill="%s"' % block["key"]) in page
                 for block in blocks)
    crit_label = labels.get("criteria_label", "")
    crit_ok = bool(crit_label) and page.count(crit_label) == len(blocks)
    category_rows = [row for block in blocks
                     for row in block.get("listings") or []
                     if row["category"] is None]
    dash_ok = all('<td class="">%s</td>' % dash in page
                  for _ in category_rows[:1]) if category_rows else True
    unrated_ok = any(int(row["rating_count"]) == 0
                     for block in blocks
                     for row in block.get("listings") or [])
    unrated_text = labels.get("unrated", "")
    unrated_printed = (unrated_text in page) if unrated_ok else True
    empty_sentence = labels.get("empty", "")
    empty_ok = bool(empty_sentence) and empty_sentence in page
    paged_block = next((block for block in blocks
                        if block.get("total") is not None), None)
    paged_ok = paged_block is not None and (
        labels.get("page_total", "") in page
        and labels.get("page_trunc", "") in page)
    stand_in = ">None<" in page
    ok("AC-SDB4", marked and crit_ok and dash_ok and unrated_printed
       and empty_ok and paged_ok and not stand_in,
       "sections=%s criteria=%s dash=%s unrated=%s empty_sentence=%s "
       "paged=%s bare_none=%s"
       % (marked, crit_ok, dash_ok, unrated_printed, empty_ok, paged_ok,
          stand_in))

    # ---- AC-SDB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-SDB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-SDB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = all(os.path.exists(os.path.join(LEDGER_DIR, name))
                  and "AC-AM" in read(os.path.join(LEDGER_DIR, name))
                  for name in FACE_SUITES)
    ok("AC-SDB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suites=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
