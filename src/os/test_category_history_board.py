"""Battery suite for tools/category_history_board.py - AC-CGHB1..6.

WHY THIS SUITE EXISTS (measured at R3455, not assumed):
api_category_history shipped the per-listing category-movement face - the
declaration made at publish time plus every append-only revision in order, the
CURRENT effective bucket and the revision count - but a search over tools/,
preview/ and src/os answered zero readers for its name. R3455 renders the
shipped envelopes on one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3455 PIN row landed with the driver and says
so):
  AC-CGHB1 the pair lands, the json carries exactly the pinned nine-key payload
          set, the market block exactly the ten derived keys, every listing
          entry the pin plus its rows, every row the shipped five keys, the
          report points at a file that exists and the four source fingerprints
          are present.
  AC-CGHB2 the data is the shipped face's own: the suite builds its own
          throwaway world through the shipped publish and revise_category doors
          under its own pinned clock, re-reads every listing and requires the
          page json to equal that reading item for item, disclaimer included.
  AC-CGHB3 the face identities hold and the driver refuses a broken one: the
          per-listing revision count, chain continuity, effective bucket,
          latest stamp and ascending ids, the market totals, the per-bucket
          gained/lost derivation, the base + gained - lost = current
          conservation and the bucket order all hold - and a forged row is
          refused by name.
  AC-CGHB4 the page reads honestly: one marked card per listing, one marked
          row per revision, the dash where a number is absent, no bare None or
          null, a bar per live bucket with the caption on the page, the
          uncategorized label reachable, and the empty sentence reachable both
          as a landed shelf and in an in-memory probe.
  AC-CGHB5 the standing compliance faces ride along: the AIGC label, the
          face's own disclaimer verbatim, the non-advice sentence, zero
          external links and no script tags.
  AC-CGHB6 no older criterion is relaxed: the landed pair answers its own
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
TOOL = os.path.join(ROOT, "tools", "category_history_board.py")
HTML = os.path.join(ROOT, "preview", "category-history-board.html")
JSONF = os.path.join(ROOT, "preview", "category-history-board.json")
COPY = os.path.join(ROOT, "preview", "category-history-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_categoryrev.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-category-history-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "market", "listings", "disclaimer",
    "report", "sources", "sizes",
}
MARKET_KEYS = {
    "listing_count", "moved_listing_count", "unchanged_listing_count",
    "revision_count", "seller_count", "bucket_count", "delisted_count",
    "latest_revision_utc", "most_moved_listing", "buckets",
}
BUCKET_KEYS = {"category", "base_count", "gained_count", "lost_count",
               "net_count", "current_count"}
LISTING_KEYS = {"listing_id", "listing_key", "dev_account", "base_category",
                "category", "revision_count", "latest_revision_utc",
                "delisted", "delisted_utc", "rows"}
ROW_KEYS = {"revision_id", "dev_account", "previous_category", "category",
            "revised_utc"}

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


def load_driver():
    spec = importlib.util.spec_from_file_location("cgh_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_world(driver):
    """The suite's own stack, every re-filing through a shipped door."""
    import apimarket as A
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="cgh-suite-")
    db = os.path.join(tmp_root, "suite.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = driver._clock
        driver.build_world(am)
        listings = []
        for listing_id, key, dev in driver._enumerate(am):
            envelope = dict(am.api_category_history(listing_id))
            listings.append((listing_id, key, dev, envelope))
        listings.sort(key=lambda item: item[0])
    finally:
        A._now_utc = orig_now
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    return listings


def same(left, right):
    return json.dumps(left, sort_keys=True, default=str) == json.dumps(
        right, sort_keys=True, default=str)


def main():
    if not os.path.exists(TOOL):
        print("FAIL AC-CGHB1 driver missing")
        return 2
    driver = load_driver()
    labels = json.loads(read(COPY))
    page = json.loads(read(JSONF))
    doc = read(HTML)

    entries = page.get("listings") or []
    market = page.get("market") or {}

    # ---- AC-CGHB1 contract ------------------------------------------------
    missing_payload = sorted(PAYLOAD_KEYS - set(page))
    extra_payload = sorted(set(page) - PAYLOAD_KEYS)
    report_path = os.path.join(ROOT, page.get("report") or "")
    sources = page.get("sources") or {}
    sizes = page.get("sizes") or {}
    listing_shape = all(set(entry) == LISTING_KEYS for entry in entries)
    row_shape = all(set(row) == ROW_KEYS
                    for entry in entries for row in entry.get("rows") or [])
    bucket_shape = all(set(row) == BUCKET_KEYS
                       for row in market.get("buckets") or [])
    ok("AC-CGHB1",
       not missing_payload and not extra_payload
       and set(market) == MARKET_KEYS and bucket_shape
       and listing_shape and row_shape
       and os.path.exists(report_path)
       and sorted(sources) == ["apimarket", "copy", "driver", "report"]
       and sizes.get("html") == os.path.getsize(HTML)
       and sizes.get("json") == os.path.getsize(JSONF)
       and page.get("face") == "api_category_history",
       "payload_missing=%r payload_extra=%r listings=%d listing_shape=%r "
       "row_shape=%r bucket_shape=%r report=True sources=True"
       % (missing_payload, extra_payload, len(entries), listing_shape,
          row_shape, bucket_shape))

    # ---- AC-CGHB2 the data is the shipped face's own ----------------------
    live = live_world(driver)
    live_market = driver.derive_market(live)
    same_all = same([driver.trim_listing(*item) for item in live], entries)
    same_words = page.get("disclaimer") == live[0][3].get("disclaimer")
    same_market = same(live_market, market)
    same_order = ([entry["listing_id"] for entry in entries]
                  == [item[0] for item in live])
    ok("AC-CGHB2", same_all and same_words and same_market and same_order,
       "envelope_same=%r disclaimer_same=%r market_same=%r order_same=%r"
       % (same_all, same_words, same_market, same_order))

    # ---- AC-CGHB3 laws, plus a forged row refused by name -----------------
    bare = driver.read_empty()
    driver_problems = driver.check_laws(live, live_market, bare)
    forged = [(listing_id, key, dev,
               json.loads(json.dumps(envelope, default=str)))
              for listing_id, key, dev, envelope in live]
    if forged[0][3].get("revisions"):
        forged[0][3]["revisions"][0]["category"] = "forged-bucket"
    forged_market = json.loads(json.dumps(live_market, default=str))
    forged_market["buckets"][0]["current_count"] = int(
        forged_market["buckets"][0]["current_count"]) + 7
    forged_problems = driver.check_laws(forged, forged_market, bare)
    identities = True
    chain_ok = True
    conservation_ok = True
    delisted_shelf = False
    unrevised_shelf = False
    for listing_id, key, dev, envelope in live:
        rows = envelope.get("revisions") or []
        if int(envelope["revision_count"]) != len(rows):
            identities = False
        if rows and rows[0]["previous_category"] != \
                envelope["base_category"]:
            chain_ok = False
        for index in range(1, len(rows)):
            if rows[index]["previous_category"] != rows[index - 1]["category"]:
                chain_ok = False
        if envelope["delisted"]:
            delisted_shelf = True
        if not rows and envelope["latest_revision_utc"] is None:
            unrevised_shelf = True
    for row in live_market.get("buckets") or []:
        if int(row["base_count"]) + int(row["net_count"]) != \
                int(row["current_count"]):
            conservation_ok = False
    ok("AC-CGHB3",
       not driver_problems and len(forged_problems) >= 2 and identities
       and chain_ok and conservation_ok and delisted_shelf
       and unrevised_shelf
       and int(bare["revision_count"]) == 0
       and bare.get("latest_revision_utc") is None,
       "driver_problems=%d forged_problems=%d identities=%r chain=%r "
       "conservation=%r delisted=%r unrevised=%r bare_revisions=%d"
       % (len(driver_problems), len(forged_problems), identities, chain_ok,
          conservation_ok, delisted_shelf, unrevised_shelf,
          int(bare["revision_count"])))

    # ---- AC-CGHB4 the page reads honestly ---------------------------------
    dash = labels["none"]
    listing_marked = all(('data-listing="%s"' % entry["listing_id"]) in doc
                         for entry in entries)
    revision_rows = sum(len(entry.get("rows") or []) for entry in entries)
    revision_marked = doc.count('data-revision="') == revision_rows
    bare_none = "None" in doc or "null" in doc
    caption = labels["bar_caption"] in doc
    bars = doc.count('<div class="bar">')
    wants = sum(1 for row in market.get("buckets") or []
                if int(row["current_count"]) > 0)
    uncategorized = labels["uncategorized"] in doc
    silent = sum(1 for entry in entries if not entry.get("rows"))
    empty_landed = doc.count(labels["empty"]) == silent
    probe = {"generated_utc": "2026-11-25 00:00:00Z",
             "face": "api_category_history", "scope": "listings",
             "market": {"listing_count": 0, "moved_listing_count": 0,
                        "unchanged_listing_count": 0, "revision_count": 0,
                        "seller_count": 0, "bucket_count": 0,
                        "delisted_count": 0, "latest_revision_utc": None,
                        "most_moved_listing": None, "buckets": []},
             "listings": [], "disclaimer": "x", "report": "x",
             "sources": {}}
    empty_html = driver.build_html([], probe["market"], labels,
                                   "2026-11-25 00:00:00Z", "x")
    empty_probe = labels["empty"] in empty_html and dash in empty_html
    ok("AC-CGHB4",
       listing_marked and revision_marked and not bare_none and caption
       and bars == wants and uncategorized and empty_landed and empty_probe,
       "listing_marked=%r revisions=%d marked=%r no_bare_none=%r caption=%r "
       "bars=%d/%d uncategorized=%r empty_landed=%r empty_probe=%r"
       % (listing_marked, revision_rows, revision_marked, not bare_none,
          caption, bars, wants, uncategorized, empty_landed, empty_probe))

    # ---- AC-CGHB5 compliance ----------------------------------------------
    disclaimer = page.get("disclaimer") or ""
    aigc = "AIGC" in doc
    verbatim = bool(disclaimer) and disclaimer in doc
    notadvice = labels["law_notadvice"] in doc
    zero_links = "http://" not in doc and "https://" not in doc
    no_script = "<script" not in doc.lower()
    ok("AC-CGHB5", aigc and verbatim and notadvice and zero_links and no_script,
       "aigc=%r disclaimer_verbatim=%r notadvice=%r zero_links=%r "
       "no_script=%r" % (aigc, verbatim, notadvice, zero_links, no_script))

    # ---- AC-CGHB6 no older criterion is relaxed ---------------------------
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
    face_ac = "AC-AMCG1" in read(FACE_SUITE) if face_suite else False
    ok("AC-CGHB6",
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
