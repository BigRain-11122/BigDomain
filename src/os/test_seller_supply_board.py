"""Battery suite for tools/seller_supply_board.py - AC-SSSB1..6.

WHY THIS SUITE EXISTS (measured at R3432, not assumed):
api_supply answers one shelf and api_supply_history that shelf's restocks, while
api_seller_supply rolls a whole shop up with its own AC-SSUP1..8 law; a git
grep over tools/ and preview/ answered zero hits, so "how many shelves are
live, how many are limited, which are sold out, which sit at the low-stock
line, how many units are left, how many sold, how often did I restock" could
only be asked of a shell. R3432 renders one summary table and one card per
seller; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3432 PIN
BEFORE the driver existed):
  AC-SSSB1 the page and its json land, the json carries exactly the pinned
           payload key set, every seller block carries the shipped 16-key
           envelope, every shelf row the shipped 11 keys, seller_count equals
           the block count, the report points at a file that exists, and the
           four source fingerprints are recorded.
  AC-SSSB2 the data is the shipped face's own: the suite builds its own
           throwaway world (factory demo plus the driver's shipped-door
           scarcity fixture), enumerates sellers through the shipped board
           face, reads api_seller_supply() per seller, and requires the page
           json's sellers (including every row and the disclaimer) to equal
           that reading item for item - no typed fixture.
  AC-SSSB3 the face's identities hold: counts are row tallies, live+retired
           and tracked+unlimited both cover the shelf set, sold/restock totals
           are row sums, the two supply totals are null exactly when no shelf
           is limited and otherwise the limited row sums, sold_out follows a
           zero remaining, low_stock follows the threshold, an unlimited shelf
           never claims scarcity or a remaining, and rows run in ascending
           listing_id with no repeat.
  AC-SSSB4 the page reads honestly: one card per seller marked data-seller,
           every row marked data-shelf and data-track, named shelf and metering
           badges, a dash where a total is undefined, no bare None, and the
           empty-shop and limited-shop shapes both render.
  AC-SSSB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer and the not-advice sentence are on the page,
           with zero external links.
  AC-SSSB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with AC-SSUP arms.

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
TOOL = os.path.join(ROOT, "tools", "seller_supply_board.py")
HTML = os.path.join(ROOT, "preview", "seller-supply-board.html")
JSONF = os.path.join(ROOT, "preview", "seller-supply-board.json")
COPY = os.path.join(ROOT, "preview", "seller-supply-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_sellersupply.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-supply-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "scope", "seller_count",
    "sellers", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "dev_account", "listing_count", "live_listing_count",
    "retired_listing_count", "tracked_listing_count",
    "unlimited_listing_count", "sold_out_listing_count",
    "low_stock_listing_count", "total_effective_supply", "total_sold",
    "total_remaining", "total_restocked_units", "total_restock_count",
    "low_stock_threshold", "disclaimer", "listings",
}
ROW_KEYS = {
    "listing_id", "listing_key", "delisted", "supply", "base_supply",
    "restocked_units", "restock_count", "sold", "remaining", "sold_out",
    "low_stock",
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


def load_driver():
    spec = importlib.util.spec_from_file_location("sssb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_world():
    """The shipped face's own reading over the suite's throwaway world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    driver = load_driver()
    tmp_root = tempfile.mkdtemp(prefix="sssb-suite-")
    db = os.path.join(tmp_root, "sssb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        driver.seed_scarcity(am)
        board = dict(am.api_board())
        sellers = sorted({str(row["dev_account"]) for row in board["listings"]})
        envelopes = [dict(am.api_seller_supply(dev)) for dev in sellers]
        return envelopes, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def envelope_problems(block, label):
    problems = []
    rows = list(block["listings"])
    threshold = int(block["low_stock_threshold"])
    if int(block["listing_count"]) != len(rows):
        problems.append("%s listing_count" % label)
    live = sum(1 for row in rows if not row["delisted"])
    if int(block["live_listing_count"]) != live:
        problems.append("%s live" % label)
    if int(block["retired_listing_count"]) != len(rows) - live:
        problems.append("%s retired" % label)
    tracked = [row for row in rows if row["supply"] is not None]
    if int(block["tracked_listing_count"]) != len(tracked):
        problems.append("%s tracked" % label)
    if int(block["unlimited_listing_count"]) != len(rows) - len(tracked):
        problems.append("%s unlimited" % label)
    if int(block["sold_out_listing_count"]) != sum(
            1 for row in tracked if row["sold_out"]):
        problems.append("%s sold_out count" % label)
    if int(block["low_stock_listing_count"]) != sum(
            1 for row in tracked if row["low_stock"]):
        problems.append("%s low_stock count" % label)
    if int(block["total_sold"]) != sum(int(row["sold"]) for row in rows):
        problems.append("%s total_sold" % label)
    if int(block["total_restocked_units"]) != sum(
            int(row["restocked_units"]) for row in rows):
        problems.append("%s total_restocked_units" % label)
    if int(block["total_restock_count"]) != sum(
            int(row["restock_count"]) for row in rows):
        problems.append("%s total_restock_count" % label)
    want_eff = sum(int(row["supply"]) for row in tracked) if tracked else None
    want_rem = (sum(int(row["remaining"] or 0) for row in tracked)
                if tracked else None)
    if block["total_effective_supply"] != want_eff:
        problems.append("%s total_effective_supply" % label)
    if block["total_remaining"] != want_rem:
        problems.append("%s total_remaining" % label)
    ids = [int(row["listing_id"]) for row in rows]
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        problems.append("%s row order" % label)
    for row in rows:
        name = "%s/%s" % (label, row["listing_id"])
        if (row["supply"] is None) != (row["base_supply"] is None):
            problems.append("%s supply/base" % name)
        if not str(row["listing_key"] or "").strip():
            problems.append("%s key" % name)
        if row["supply"] is None:
            if row["remaining"] is not None:
                problems.append("%s unlimited remaining" % name)
            if row["sold_out"] or row["low_stock"]:
                problems.append("%s unlimited scarcity" % name)
            continue
        if bool(row["sold_out"]) != (int(row["remaining"] or 0) == 0):
            problems.append("%s sold_out law" % name)
        if bool(row["low_stock"]) != (int(row["remaining"] or 0) <= threshold):
            problems.append("%s low_stock law" % name)
        if int(row["supply"]) < 0 or int(row["base_supply"]) < 0:
            problems.append("%s negative quantity" % name)
        for key in ("sold", "restocked_units", "restock_count"):
            if int(row[key]) < 0:
                problems.append("%s %s negative" % (name, key))
    return problems


def probe_envelope():
    rows = [
        {"listing_id": 1, "listing_key": "alpha", "delisted": False,
         "supply": 4, "base_supply": 4, "restocked_units": 0,
         "restock_count": 0, "sold": 1, "remaining": 3, "sold_out": False,
         "low_stock": False},
        {"listing_id": 2, "listing_key": "beta", "delisted": False,
         "supply": 2, "base_supply": 2, "restocked_units": 0,
         "restock_count": 0, "sold": 2, "remaining": 0, "sold_out": True,
         "low_stock": True},
        {"listing_id": 3, "listing_key": "gamma", "delisted": True,
         "supply": 4, "base_supply": 2, "restocked_units": 2,
         "restock_count": 1, "sold": 1, "remaining": 3, "sold_out": False,
         "low_stock": False},
        {"listing_id": 4, "listing_key": "delta", "delisted": False,
         "supply": None, "base_supply": None, "restocked_units": 0,
         "restock_count": 0, "sold": 7, "remaining": None, "sold_out": False,
         "low_stock": False},
    ]
    return {
        "dev_account": "usr:probe", "listing_count": 4,
        "live_listing_count": 3, "retired_listing_count": 1,
        "tracked_listing_count": 3, "unlimited_listing_count": 1,
        "sold_out_listing_count": 1, "low_stock_listing_count": 1,
        "total_effective_supply": 10, "total_sold": 11,
        "total_remaining": 6, "total_restocked_units": 2,
        "total_restock_count": 1, "low_stock_threshold": 1,
        "disclaimer": "probe disclaimer", "listings": rows,
    }


def empty_envelope():
    return {
        "dev_account": "usr:empty", "listing_count": 0,
        "live_listing_count": 0, "retired_listing_count": 0,
        "tracked_listing_count": 0, "unlimited_listing_count": 0,
        "sold_out_listing_count": 0, "low_stock_listing_count": 0,
        "total_effective_supply": None, "total_sold": 0,
        "total_remaining": None, "total_restocked_units": 0,
        "total_restock_count": 0, "low_stock_threshold": 1,
        "disclaimer": "probe disclaimer", "listings": [],
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    sellers = doc.get("sellers") or []

    # ---- AC-SSSB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelopes_ok = all(set(block.keys()) == ENVELOPE_KEYS for block in sellers)
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for block in sellers for row in (block.get("listings") or []))
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-SSSB1", landed and keys == PAYLOAD_KEYS and envelopes_ok and rows_ok
       and sources_ok and bool(sellers)
       and int(doc.get("seller_count", -1)) == len(sellers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelopes=%s rows=%s sources=%s "
       "count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelopes_ok, rows_ok, sources_ok,
          len(sellers), int(doc.get("seller_count", -1)), report_ok))

    # ---- AC-SSSB2: every printed number is the shipped face's own.
    live_sellers, live_disclaimer = live_world()
    same = json.dumps(sellers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in ENVELOPE_KEYS} for block in live_sellers],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-SSSB2", same and disc_same and bool(sellers),
       "sellers_same=%s disclaimer_same=%s sellers=%d shelves=%d tracked=%d"
       % (same, disc_same, len(sellers),
          sum(len(b["listings"]) for b in sellers),
          sum(int(b["tracked_listing_count"]) for b in sellers)))

    # ---- AC-SSSB3: the face's identities hold on these envelopes.
    problems = []
    for block in sellers:
        problems.extend(envelope_problems(block, str(block.get("dev_account"))))
    ok("AC-SSSB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-SSSB4: honest page face, badges, dashes, quiet empty scope.
    dash = labels.get("none", "-")
    sections = len(re.findall(r'<div class="?card"? data-seller="', page))
    rows_marked = len(re.findall(r'data-shelf="(?:live|retired)"', page))
    tracks_marked = len(re.findall(r'data-track="(?:tracked|unlimited)"', page))
    landed_rows = sum(len(b["listings"]) for b in sellers)
    want_dash = 0
    for block in sellers:
        want_dash += sum(1 for key in ("total_effective_supply",
                                       "total_remaining")
                         if block[key] is None) * 2
        for row in block["listings"]:
            want_dash += sum(1 for key in ("supply", "base_supply", "remaining")
                             if row[key] is None)
    dash_cells = page.count(">%s<" % dash)
    no_none = ">None<" not in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_partition", "law_totals", "law_unlimited",
             "law_soldout", "law_low", "law_restock", "law_order", "law_scope",
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
            probe_html.count('data-shelf="retired"') == 1
            and probe_html.count('data-shelf="live"') == 3
            and probe_html.count('data-track="tracked"') == 3
            and probe_html.count('data-track="unlimited"') == 1
            and labels.get("label_unlimited", "") in probe_html
            and labels.get("label_tracked", "") in probe_html
            and labels.get("label_retired", "") in probe_html
            and labels.get("label_live", "") in probe_html
            and labels.get("label_yes", "") in probe_html
            and ">None<" not in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-SSSB4", sections == len(sellers) and rows_marked == landed_rows
       and tracks_marked == landed_rows and no_none and laws_ok
       and dash_cells == want_dash and want_dash > 0 and empty_ok and probe_ok,
       "sections=%d/%d rows_marked=%d/%d tracks=%d/%d dash_cells=%d/%d "
       "laws=%s empty_probe=%s shelf_probe=%s bare_none=%s"
       % (sections, len(sellers), rows_marked, landed_rows, tracks_marked,
          landed_rows, dash_cells, want_dash, laws_ok, empty_ok, probe_ok,
          not no_none))

    # ---- AC-SSSB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    not_advice = labels.get("law_notadvice", "") in page
    external = len(re.findall(r"https?://", page))
    ok("AC-SSSB5", aigc and on_page and not_advice and external == 0,
       "aigc=%s disclaimer_on_page=%s not_advice=%s external_links=%d"
       % (aigc, on_page, not_advice, external))

    # ---- AC-SSSB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r'\),\s*(\d+)\)', registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-SSUP" in read(FACE_SUITE)
    ok("AC-SSSB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
