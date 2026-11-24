"""Battery suite for tools/listing_velocity_board.py - criteria AC-LVB1..6.

WHY THIS SUITE EXISTS (measured at R3420, not assumed):
api_listing_velocity shipped with its own AC-LV1..8 criteria
(src/sandbox/ledger/test_apimarket_listingvelocity.py) but a git grep over
tools/ and preview/ answered rc=1 with zero hits, so the question "how long did
this shelf sit before it sold, and how does that compare with the market"
could not be opened by anyone. R3420 renders the market reading plus one scoped
reading per seller on one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3420 PIN
BEFORE the driver existed):
  AC-LVB1 the page and its json land, the json carries exactly the pinned
           payload key set including the market, seller, sizes and sources
           blocks, every listing row carries the shipped eleven-key envelope,
           every seller block carries the shipped twelve keys,
           listing_count equals the row count, and the report points at a file
           that exists.
  AC-LVB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates sellers through the shipped board
           face, reads api_listing_velocity() over it (market and per seller),
           and requires the page json's rows, sellers, market fields and
           disclaimer to equal that reading item for item - no typed fixture,
           no synthesized row.
  AC-LVB3 the face's identities hold: the sold and unsold partitions sum to
           the listing count, an unsold row carries no stamp and no duration,
           a sold row's duration is the two-stamp difference clamped at zero,
           the mean and median recompute from the sold rows only, the extremes
           break ties on the lowest listing_id, the market average pools the
           whole market, the category average is the mean inside its bucket,
           and the rows keep the face's own order.
  AC-LVB4 the page reads honestly: one row per listing with its own marker,
           an unsold row printing the dash instead of a zero, durations printed
           as day/hour text, a bar that the page calls a width with no bar on
           an unsold row, no bare None, and an empty world handed to the
           driver's own renderer prints dashes instead of a fake zero
           (in-memory probe only).
  AC-LVB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-LVB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-LV arms.

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
TOOL = os.path.join(ROOT, "tools", "listing_velocity_board.py")
HTML = os.path.join(ROOT, "preview", "listing-velocity-board.html")
JSONF = os.path.join(ROOT, "preview", "listing-velocity-board.json")
COPY = os.path.join(ROOT, "preview", "listing-velocity-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_listingvelocity.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-listing-velocity-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "source_face", "scope",
    "listing_count", "sold_count", "unsold_count", "avg_seconds",
    "median_seconds", "fastest_seconds", "slowest_seconds",
    "fastest_listing_id", "slowest_listing_id", "market_avg_seconds",
    "rows", "sellers", "disclaimer", "report", "sources", "sizes",
}
ROW_KEYS = {
    "listing_id", "listing_key", "title", "category", "delisted",
    "current_price", "shelf_opened_utc", "first_sale_utc", "elapsed_seconds",
    "category_avg_seconds", "unsold",
}
SELLER_KEYS = {
    "dev_account", "listing_count", "sold_count", "unsold_count",
    "avg_seconds", "median_seconds", "fastest_seconds", "slowest_seconds",
    "fastest_listing_id", "slowest_listing_id", "market_avg_seconds",
    "disclaimer",
}
MARKET_FIELDS = (
    "listing_count", "sold_count", "unsold_count", "avg_seconds",
    "median_seconds", "fastest_seconds", "slowest_seconds",
    "fastest_listing_id", "slowest_listing_id", "market_avg_seconds",
)

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
    tmp_root = tempfile.mkdtemp(prefix="lvb-suite-")
    db = os.path.join(tmp_root, "lvb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        sellers = sorted({str(row["dev_account"]) for row in board["listings"]})
        market = dict(am.api_listing_velocity())
        scoped = [dict(am.api_listing_velocity(seller)) for seller in sellers]
        return market, scoped, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("lvb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def identity_problems(rows, market):
    problems = []
    if int(market["listing_count"]) != len(rows):
        problems.append("listing count")
    if int(market["sold_count"]) + int(market["unsold_count"]) != len(rows):
        problems.append("partition")
    for row in rows:
        name = "listing %s" % row["listing_id"]
        if row["unsold"]:
            if any(row[key] is not None for key in
                   ("elapsed_seconds", "first_sale_utc", "shelf_opened_utc")):
                problems.append("%s unsold stamps" % name)
            continue
        if None in (row["elapsed_seconds"], row["first_sale_utc"],
                    row["shelf_opened_utc"]):
            problems.append("%s sold stamps" % name)
            continue
        import datetime
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        want = max(0, int((datetime.datetime.strptime(row["first_sale_utc"], fmt)
                           - datetime.datetime.strptime(
                               row["shelf_opened_utc"], fmt)).total_seconds()))
        if int(row["elapsed_seconds"]) != want:
            problems.append("%s elapsed" % name)

    elapsed = [int(row["elapsed_seconds"]) for row in rows
               if not row["unsold"]]
    mean = float(sum(elapsed)) / len(elapsed) if elapsed else None
    if not close(market["avg_seconds"], mean):
        problems.append("avg")
    if elapsed:
        ordered = sorted(elapsed)
        mid = len(ordered) // 2
        median = (float(ordered[mid]) if len(ordered) % 2 else
                  (float(ordered[mid - 1]) + float(ordered[mid])) / 2.0)
        if not close(market["median_seconds"], median):
            problems.append("median")
        if int(market["fastest_seconds"]) != min(elapsed):
            problems.append("fastest")
        if int(market["slowest_seconds"]) != max(elapsed):
            problems.append("slowest")
        if market["fastest_listing_id"] != min(
                row["listing_id"] for row in rows
                if not row["unsold"]
                and int(row["elapsed_seconds"]) == min(elapsed)):
            problems.append("fastest id")
        if market["slowest_listing_id"] != min(
                row["listing_id"] for row in rows
                if not row["unsold"]
                and int(row["elapsed_seconds"]) == max(elapsed)):
            problems.append("slowest id")
    else:
        for key in ("avg_seconds", "median_seconds", "fastest_seconds",
                    "slowest_seconds", "fastest_listing_id",
                    "slowest_listing_id"):
            if market[key] is not None:
                problems.append("%s on no-sale world" % key)
    if not close(market["market_avg_seconds"], mean):
        problems.append("market avg")

    buckets = {}
    for row in rows:
        if row["elapsed_seconds"] is None:
            continue
        buckets.setdefault(row["category"], []).append(
            int(row["elapsed_seconds"]))
    for row in rows:
        bucket = buckets.get(row["category"], [])
        want = float(sum(bucket)) / len(bucket) if bucket else None
        if not close(row["category_avg_seconds"], want):
            problems.append("listing %s category avg" % row["listing_id"])

    def key(item):
        return (item["unsold"],
                0 if item["elapsed_seconds"] is None
                else int(item["elapsed_seconds"]), item["listing_id"])
    if [key(row) for row in rows] != sorted(key(row) for row in rows):
        problems.append("row order")
    return problems


def probe_empty(labels):
    """An empty world: never landed, only handed to the driver renderer."""
    market = {
        "rows": [], "listing_count": 0, "sold_count": 0, "unsold_count": 0,
        "avg_seconds": None, "median_seconds": None, "fastest_seconds": None,
        "slowest_seconds": None, "fastest_listing_id": None,
        "slowest_listing_id": None, "market_avg_seconds": None,
    }
    return market, []


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    rows = doc.get("rows") or []
    sellers = doc.get("sellers") or []

    # ---- AC-LVB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in rows)
    sellers_ok = all(set(block.keys()) == SELLER_KEYS for block in sellers)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-LVB1", landed and keys == PAYLOAD_KEYS and rows_ok and sellers_ok
       and sources_ok and bool(rows)
       and int(doc.get("listing_count", -1)) == len(rows) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s rows=%s sellers=%s sources=%s "
       "listings=%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), rows_ok, sellers_ok, sources_ok,
          len(rows), report_ok))

    # ---- AC-LVB2: every printed number is the shipped face's own.
    live_market, live_sellers, live_disclaimer = live_world()
    same = json.dumps(rows, sort_keys=True) == json.dumps(
        live_market["rows"], sort_keys=True)
    sellers_same = json.dumps(sellers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in SELLER_KEYS} for block in live_sellers],
        sort_keys=True)
    fields_same = all(doc.get(key) == live_market[key]
                      for key in MARKET_FIELDS)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-LVB2", same and sellers_same and fields_same and disc_same
       and bool(rows),
       "identical=%s sellers_same=%s fields_same=%s disclaimer_same=%s "
       "rows=%d sellers=%d"
       % (same, sellers_same, fields_same, disc_same, len(rows),
          len(sellers)))

    # ---- AC-LVB3: the face's identities hold on this envelope.
    problems = identity_problems(rows, doc) if rows else ["no rows"]
    ok("AC-LVB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-LVB4: honest page face, dashes, width bar, empty probe.
    page_rows = page.count('<tr class="')
    marked = all(('data-listing="%s"' % row["listing_id"]) in page
                 for row in rows)
    seller_marked = all(('data-seller="%s"' % block["dev_account"]) in page
                        for block in sellers)
    sold_rows = [row for row in rows if not row["unsold"]]
    unsold_rows = [row for row in rows if row["unsold"]]
    bars_ok = (page.count("<div class=bar>") == len(sold_rows))
    unsold_dash_ok = all(
        '<span class=empty>%s</span>' % labels.get("none", "-") in page
        for _ in unsold_rows)
    duration_ok = all(
        ("%d%s" % (int(row["elapsed_seconds"]) // 86400,
                   labels.get("unit_day", ""))) in page
        for row in sold_rows if int(row["elapsed_seconds"]) >= 86400)
    stand_in = ">None<" in page
    laws = [labels.get(key, "") for key in
            ("law_elapsed", "law_unsold", "law_avg", "law_extremes",
             "law_market", "law_category", "law_bar", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    empty_probe_ok = False
    try:
        driver = load_driver()
        probe_market, probe_sellers = probe_empty(labels)
        probe_html = driver.build_html(probe_market, probe_sellers, labels,
                                       "2026-01-01 00:00:00Z",
                                       doc.get("disclaimer") or "")
        empty_probe_ok = ('<tr class="sold' not in probe_html
                          and '<tr class="unsold' not in probe_html
                          and ">None<" not in probe_html
                          and labels.get("none", "-") in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-LVB4", page_rows == len(rows) + len(sellers) and marked
       and seller_marked and bars_ok and unsold_dash_ok and duration_ok
       and not stand_in and laws_ok and empty_probe_ok,
       "rows=%d/%d+sellers=%d marked=%s seller_marked=%s bars=%s "
       "unsold_dash=%s durations=%s laws=%s empty_probe=%s stand_in_none=%s"
       % (page_rows, len(rows), len(sellers), marked, seller_marked, bars_ok,
          unsold_dash_ok, duration_ok, laws_ok, empty_probe_ok, stand_in))

    # ---- AC-LVB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-LVB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-LVB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-LV" in read(FACE_SUITE)
    ok("AC-LVB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
