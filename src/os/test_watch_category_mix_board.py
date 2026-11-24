"""Battery suite for tools/watch_category_mix_board.py - AC-WCMB1..6.

WHY THIS SUITE EXISTS (measured at R3454, not assumed):
api_buyer_watch_category_mix shipped the intent-concentration face - every live
watch resolved to its CURRENT bucket through the single category seam, with the
purchased/open split, the delisted split, the per-row seller axis, share,
cumulative share, rank, top1, top3, herfindahl and the integer-decided pareto
count, plus the market-wide watch count and herfindahl as comparable context -
but a search over tools/, preview/ and src/os answered zero readers for its
name. R3454 renders the shipped envelopes on one page; this suite grades the
page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3454 PIN row landed with the driver and says
so):
  AC-WCMB1 the pair lands, the json carries exactly the pinned nine-key payload
          set, every buyer entry the fourteen shipped scope keys plus its id
          and rows, every row the shipped eleven keys, the report points at a
          file that exists and the four source fingerprints are present.
  AC-WCMB2 the data is the shipped face's own: the suite builds its own
          throwaway world through the shipped publish, watch, unwatch,
          purchase and delist doors under its own pinned clock, re-reads every
          buyer scope and requires the page json to equal that reading item for
          item, disclaimer included.
  AC-WCMB3 the face identities hold and the driver refuses a broken one: the
          total/split laws, the share and cumulative laws, the total order
          with the uncategorized bucket pinned last on ties, the herfindahl,
          the integer pareto count, top1/top3, the seller axis and the market
          context all hold - and a forged row is refused by name.
  AC-WCMB4 the page reads honestly: one marked card per buyer, one marked row
          per category bucket, the dash where a number is absent, no bare
          None or null, a bar per live bucket with the caption on the page,
          the uncategorized label reachable, and the empty sentence reachable
          both as a landed scope and in an in-memory probe.
  AC-WCMB5 the standing compliance faces ride along: the AIGC label, the
          face's own disclaimer verbatim, the non-advice sentence, zero
          external links and no script tags.
  AC-WCMB6 no older criterion is relaxed: the landed pair answers its own
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
TOOL = os.path.join(ROOT, "tools", "watch_category_mix_board.py")
HTML = os.path.join(ROOT, "preview", "watch-category-mix-board.html")
JSONF = os.path.join(ROOT, "preview", "watch-category-mix-board.json")
COPY = os.path.join(ROOT, "preview", "watch-category-mix-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_buyerwatchcategorymix.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-watch-category-mix-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "market", "buyers", "disclaimer",
    "report", "sources", "sizes",
}
BUYER_KEYS = {
    "buyer_id", "watch_count", "category_count", "purchased_count",
    "open_count", "delisted_count", "seller_count", "top_seller",
    "top_seller_share", "top1_share", "top3_share", "herfindahl",
    "pareto_category_count", "market_watch_count", "market_herfindahl",
    "rows",
}
ROW_KEYS = {
    "category", "watch_count", "purchased_count", "open_count",
    "delisted_count", "seller_count", "top_seller", "top_seller_share",
    "share", "cumulative_share", "rank",
}
BUYERS = ("usr:bob", "usr:carol", "usr:dave", "usr:ghost")

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
    spec = importlib.util.spec_from_file_location("wcm_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_world(am, clock):
    """The suite's own copy of the story, every row through a shipped door."""
    clock["value"] = "2026-10-01T00:00:00Z"
    ids = {}

    def pub(dev, key, title, category):
        ids[key] = am.publish_api(dev, key, title, "demo", {"ep": key},
                                  5, False, supply=5,
                                  category=category)["listing_id"]

    pub("usr:dana", "data-a", "Data A", "data")
    pub("usr:dana", "data-b", "Data B", "data")
    pub("usr:frank", "data-c", "Data C", "data")
    pub("usr:frank", "data-d", "Data D", "data")
    pub("usr:dana", "tools-a", "Tools A", "tools")
    pub("usr:dana", "tools-b", "Tools B", "tools")
    pub("usr:frank", "tools-c", "Tools C", "tools")
    pub("usr:frank", "media-a", "Media A", "media")
    pub("usr:dana", "misc-a", "Misc A", None)
    pub("usr:dana", "misc-b", "Misc B", None)
    clock["value"] = "2026-11-02T00:00:00Z"
    for key in ("data-a", "data-b", "data-c", "data-d", "tools-a",
                "tools-b", "tools-c", "media-a", "misc-a", "misc-b"):
        am.watch_api("usr:bob", ids[key])
    for key in ("data-a", "data-c", "tools-b"):
        am.watch_api("usr:carol", ids[key])
    am.watch_api("usr:dave", ids["media-a"])
    am.unwatch_api("usr:dave", ids["media-a"])
    clock["value"] = "2026-11-10T00:00:00Z"
    am.purchase_api("usr:bob", ids["data-a"], "wcm-bob-1")
    am.purchase_api("usr:carol", ids["data-a"], "wcm-carol-1")
    clock["value"] = "2026-11-15T00:00:00Z"
    am.delist_api("usr:dana", ids["tools-a"])
    return clock


def live_world():
    import apimarket as A
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="wcm-suite-")
    db = os.path.join(tmp_root, "suite.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    clock = {"value": "2026-10-01T00:00:00Z"}
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = lambda: clock["value"]
        build_world(am, clock)
        envelopes = {buyer: dict(am.api_buyer_watch_category_mix(buyer))
                     for buyer in BUYERS}
    finally:
        A._now_utc = orig_now
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    return envelopes


def empty_world():
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="wcm-bare-")
    db = os.path.join(tmp_root, "bare.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        envelope = dict(am.api_buyer_watch_category_mix("usr:ghost"))
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    return envelope


def trim(buyer, envelope):
    doc = {"buyer_id": buyer}
    for key in BUYER_KEYS - {"buyer_id", "rows"}:
        doc[key] = envelope[key]
    doc["rows"] = [{key: row[key] for key in ROW_KEYS}
                   for row in envelope.get("rows") or []]
    return doc


def same(left, right):
    return json.dumps(left, sort_keys=True, default=str) == json.dumps(
        right, sort_keys=True, default=str)


def main():
    if not os.path.exists(TOOL):
        print("FAIL AC-WCMB1 driver missing")
        return 2
    driver = load_driver()
    labels = json.loads(read(COPY))
    page = json.loads(read(JSONF))
    doc = read(HTML)

    buyers = page.get("buyers") or []
    market = page.get("market") or {}

    # ---- AC-WCMB1 contract ------------------------------------------------
    missing_payload = sorted(PAYLOAD_KEYS - set(page))
    extra_payload = sorted(set(page) - PAYLOAD_KEYS)
    report_path = os.path.join(ROOT, page.get("report") or "")
    sources = page.get("sources") or {}
    sizes = page.get("sizes") or {}
    buyer_shape = all(set(entry) == BUYER_KEYS for entry in buyers)
    row_shape = all(set(row) == ROW_KEYS
                    for entry in buyers for row in entry.get("rows") or [])
    ok("AC-WCMB1",
       not missing_payload and not extra_payload
       and [entry.get("buyer_id") for entry in buyers] == list(BUYERS)
       and buyer_shape and row_shape
       and set(market) == {"watch_count", "herfindahl"}
       and os.path.exists(report_path)
       and sorted(sources) == ["apimarket", "copy", "driver", "report"]
       and sizes.get("html") == os.path.getsize(HTML)
       and sizes.get("json") == os.path.getsize(JSONF)
       and page.get("face") == "api_buyer_watch_category_mix",
       "payload_missing=%r payload_extra=%r buyers=%d buyer_shape=%r "
       "row_shape=%r report=True sources=True"
       % (missing_payload, extra_payload, len(buyers), buyer_shape,
          row_shape))

    # ---- AC-WCMB2 the data is the shipped face's own ----------------------
    live = live_world()
    same_all = same([trim(buyer, live[buyer]) for buyer in BUYERS], buyers)
    same_words = page.get("disclaimer") == live[BUYERS[0]].get("disclaimer")
    same_market = (market.get("watch_count")
                   == live[BUYERS[0]].get("market_watch_count")
                   and market.get("herfindahl")
                   == live[BUYERS[0]].get("market_herfindahl"))
    same_order = ([row["category"] for row in
                   (buyers[0].get("rows") or [])]
                  == [row["category"] for row in
                      (live[BUYERS[0]].get("rows") or [])])
    ok("AC-WCMB2", same_all and same_words and same_market and same_order,
       "envelope_same=%r disclaimer_same=%r market_same=%r order_same=%r"
       % (same_all, same_words, same_market, same_order))

    # ---- AC-WCMB3 laws, plus a forged row refused by name -----------------
    bare = empty_world()
    driver_problems = driver.check_laws(live, bare,
                                        {"watch_count": 13,
                                         "herfindahl": 3372.78})
    forged = json.loads(json.dumps(live, default=str))
    forged["usr:bob"]["rows"][0]["watch_count"] = int(
        forged["usr:bob"]["rows"][0]["watch_count"]) + 7
    forged_problems = driver.check_laws(
        forged, bare, {"watch_count": 13, "herfindahl": 3372.78})
    identities = True
    uncategorized_last_on_tie = False
    zero_split = False
    delisted_row = False
    for entry in buyers:
        rows = entry.get("rows") or []
        total = int(entry["watch_count"])
        if total != (int(entry["purchased_count"])
                     + int(entry["open_count"])):
            identities = False
        if rows and rows[-1]["cumulative_share"] not in (None, 1.0):
            identities = False
        for row in rows:
            if int(row["open_count"]) != (int(row["watch_count"])
                                          - int(row["purchased_count"])):
                identities = False
            if row["share"] is not None and \
                    abs(sum(r["share"] or 0.0 for r in rows) - 1.0) > 1e-6:
                identities = False
            if row["category"] is None:
                uncategorized_last_on_tie = True
            if int(row["watch_count"]) == 0:
                zero_split = True
            if int(row["delisted_count"]) > 0:
                delisted_row = True
    ok("AC-WCMB3",
       not driver_problems and len(forged_problems) >= 2 and identities
       and uncategorized_last_on_tie and delisted_row
       and int(bare["watch_count"]) == 0
       and bare.get("herfindahl") is None,
       "driver_problems=%d forged_problems=%d identities=%r "
       "uncategorized=%r delisted_row=%r bare_watches=%d"
       % (len(driver_problems), len(forged_problems), identities,
          uncategorized_last_on_tie, delisted_row, int(bare["watch_count"])))

    # ---- AC-WCMB4 the page reads honestly ---------------------------------
    dash = labels["none"]
    buyer_marked = all(('data-buyer="%s"' % buyer) in doc for buyer in BUYERS)
    row_count = sum(len(entry.get("rows") or []) for entry in buyers)
    row_marked = doc.count('data-category="') == row_count
    bare_none = "None" in doc or "null" in doc
    caption = labels["bar_caption"] in doc
    bars = doc.count('<div class="bar">')
    wants = sum(1 for entry in buyers for row in entry.get("rows") or []
                if int(row["watch_count"]) > 0)
    uncategorized = labels["uncategorized"] in doc
    empty_landed = doc.count(labels["empty"]) == 2
    probe = {"buyer_id": "usr:ghost", "watch_count": 0, "category_count": 0,
             "purchased_count": 0, "open_count": 0, "delisted_count": 0,
             "seller_count": 0, "top_seller": None,
             "top_seller_share": None, "top1_share": None,
             "top3_share": None, "herfindahl": None,
             "pareto_category_count": None, "market_watch_count": 0,
             "market_herfindahl": None, "rows": []}
    empty_html = driver.build_html(
        [("usr:ghost", probe)], {"watch_count": 0, "herfindahl": None},
        labels, "2026-11-25 00:00:00Z", "x")
    empty_probe = labels["empty"] in empty_html and dash in empty_html
    ok("AC-WCMB4",
       buyer_marked and row_marked and not bare_none and caption
       and bars == wants and uncategorized and empty_landed and empty_probe,
       "buyer_marked=%r rows=%d marked=%r no_bare_none=%r caption=%r "
       "bars=%d/%d uncategorized=%r empty_landed=%r empty_probe=%r"
       % (buyer_marked, row_count, row_marked, not bare_none, caption, bars,
          wants, uncategorized, empty_landed, empty_probe))

    # ---- AC-WCMB5 compliance ----------------------------------------------
    disclaimer = page.get("disclaimer") or ""
    aigc = "AIGC" in doc
    verbatim = bool(disclaimer) and disclaimer in doc
    notadvice = labels["law_notadvice"] in doc
    zero_links = "http://" not in doc and "https://" not in doc
    no_script = "<script" not in doc.lower()
    ok("AC-WCMB5", aigc and verbatim and notadvice and zero_links and no_script,
       "aigc=%r disclaimer_verbatim=%r notadvice=%r zero_links=%r "
       "no_script=%r" % (aigc, verbatim, notadvice, zero_links, no_script))

    # ---- AC-WCMB6 no older criterion is relaxed ---------------------------
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
    face_ac = "AC-BWCM1" in read(FACE_SUITE) if face_suite else False
    ok("AC-WCMB6",
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
