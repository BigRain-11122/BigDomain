"""Battery suite for tools/listing_view_board.py - AC-LVWB1..6.

WHY THIS SUITE EXISTS (measured at R3438, not assumed):
api_view shipped as the shelf detail face - price against base price, the
three revision families with their stamps, purchases, ratings, refunds and
the delist state - but a search over tools/, preview/ and src/os answered
rc=1 with zero hits, so the discovery page could print a listing id and
nothing could open it. R3438 renders every shelf on one page; this suite
grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3438 PIN
BEFORE the driver existed):
  AC-LVWB1 the page and its json land, the json carries exactly the pinned
           11-key payload set, every listing carries the shipped 28 keys,
           listing_count equals the row count, and the report points at a
           file that exists.
  AC-LVWB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates the listing ids from the shipped
           board face, re-reads api_view() for each and requires the page
           json to equal that reading item for item, disclaimer included.
  AC-LVWB3 the face's identities hold: net purchases equal purchases minus
           refunds, refunds and ratings never exceed purchases, a zero
           revision count carries no stamp, a delisted shelf carries its
           stamp, the AIGC flag is 0 or 1, ids ascend strictly, and the page's
           market strip recomputes from the printed rows.
  AC-LVWB4 the page reads honestly: one marked section per shelf, live and
           delisted badges plus the AIGC badge, the dash where the face has
           nothing (a zero-rating average is printed as the dash, never as a
           score of zero), no bare None, the laws on the page, and an empty
           world handed to the driver's own renderer prints the explicit
           empty sentence (in-memory probe only).
  AC-LVWB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer verbatim, the non-advice sentence, zero
           external links.
  AC-LVWB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the face is still exercised by its shipped suites on disk.

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
TOOL = os.path.join(ROOT, "tools", "listing_view_board.py")
HTML = os.path.join(ROOT, "preview", "listing-view-board.html")
JSONF = os.path.join(ROOT, "preview", "listing-view-board.json")
COPY = os.path.join(ROOT, "preview", "listing-view-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger", "test_apimarket.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-listing-view-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "scope", "listing_count",
    "listings", "market", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "listing_id", "dev_account", "listing_key", "title", "description",
    "token_price", "base_token_price", "base_title", "base_description",
    "metadata_revision_count", "latest_metadata_revision_utc",
    "revision_count", "latest_revision_utc", "ai_label", "listed_utc",
    "category", "base_category", "category_revision_count",
    "latest_category_revision_utc", "purchase_count", "rating_count",
    "rating_avg", "refund_count", "refunded_total", "net_purchase_count",
    "delisted", "delisted_utc", "disclaimer",
}
MARKET_KEYS = {
    "listing_count", "purchase_count", "rating_count", "refund_count",
    "refunded_total", "net_purchase_count", "revision_count",
    "metadata_revision_count", "category_revision_count", "ai_label_count",
    "delisted_count", "price_total", "top_price",
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


def live_world():
    """The shipped detail readings over the suite's throwaway demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="lvwb-suite-")
    db = os.path.join(tmp_root, "lvwb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = am.api_board()
        listings = []
        for listing_id in sorted(int(row["listing_id"])
                                 for row in board["listings"]):
            listings.append(dict(am.api_view(listing_id)))
        return listings
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("lvwb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_problems(listings, market):
    problems = []
    previous = None
    for row in listings:
        tag = "listing %s" % row["listing_id"]
        lid = int(row["listing_id"])
        if previous is not None and lid <= previous:
            problems.append("%s order" % tag)
        previous = lid
        purchases = int(row["purchase_count"])
        refunds = int(row["refund_count"])
        if refunds > purchases:
            problems.append("%s refunds" % tag)
        if int(row["rating_count"]) > purchases:
            problems.append("%s ratings" % tag)
        if int(row["net_purchase_count"]) != purchases - refunds:
            problems.append("%s net" % tag)
        for count_key, stamp_key in (
                ("revision_count", "latest_revision_utc"),
                ("metadata_revision_count", "latest_metadata_revision_utc"),
                ("category_revision_count", "latest_category_revision_utc")):
            if int(row[count_key]) == 0 and row[stamp_key] is not None:
                problems.append("%s %s stamp" % (tag, count_key))
        if bool(row["delisted"]) and row["delisted_utc"] is None:
            problems.append("%s delist stamp" % tag)
        if int(row["ai_label"]) not in (0, 1):
            problems.append("%s label" % tag)
    sums = {
        "purchase_count": sum(int(r["purchase_count"]) for r in listings),
        "refund_count": sum(int(r["refund_count"]) for r in listings),
        "refunded_total": sum(int(r["refunded_total"]) for r in listings),
        "net_purchase_count": sum(int(r["net_purchase_count"]) for r in listings),
        "listing_count": len(listings),
        "price_total": sum(int(r["token_price"]) for r in listings),
    }
    for key, value in sums.items():
        if int(market.get(key, -1)) != value:
            problems.append("market %s %s != %d" % (key, market.get(key), value))
    return problems


def probe_empty():
    """An empty pairing: never landed, only handed to the driver renderer."""
    market = {
        "listing_count": 0, "purchase_count": 0, "rating_count": 0,
        "refund_count": 0, "refunded_total": 0, "net_purchase_count": 0,
        "revision_count": 0, "metadata_revision_count": 0,
        "category_revision_count": 0, "ai_label_count": 0,
        "delisted_count": 0, "price_total": 0, "top_price": None,
    }
    return [], market


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    rows = doc.get("listings") or []

    # ---- AC-LVWB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    rows_ok = all(set(row.keys()) == ENVELOPE_KEYS for row in rows)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    market_ok = set((doc.get("market") or {}).keys()) == MARKET_KEYS
    ok("AC-LVWB1", landed and keys == PAYLOAD_KEYS and rows_ok and sources_ok
       and market_ok
       and int(doc.get("listing_count", -1)) == len(rows) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s rows=%s market=%s sources=%s "
       "count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), rows_ok, market_ok, sources_ok,
          len(rows), int(doc.get("listing_count", -1)), report_ok))

    # ---- AC-LVWB2: every printed value is the shipped face's own.
    live = live_world()
    rows_same = json.dumps(rows, sort_keys=True) == json.dumps(
        [{key: row[key] for key in ENVELOPE_KEYS} for row in live],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live[0]["disclaimer"]) if live \
        else False
    one_disc = len({row["disclaimer"] for row in rows}) == 1
    ids_same = [int(row["listing_id"]) for row in rows] == sorted(
        int(row["listing_id"]) for row in live)
    ok("AC-LVWB2", rows_same and disc_same and one_disc and ids_same
       and bool(rows),
       "identical=%s disclaimer_same=%s one_disclaimer=%s ids_same=%s "
       "rows=%d" % (rows_same, disc_same, one_disc, ids_same, len(rows)))

    # ---- AC-LVWB3: the face's identities and this page's own sums hold.
    driver = load_driver()
    problems = identity_problems(live, doc.get("market") or {}) if live \
        else ["no rows"]
    recomputed = driver.derived(live) if live else {}
    recomputed_ok = bool(live) and all(
        recomputed[key] == (doc.get("market") or {}).get(key)
        for key in MARKET_KEYS)
    law_problems = driver.check_laws(live, live[0]["disclaimer"]) if live \
        else ["no rows"]
    ok("AC-LVWB3", not problems and recomputed_ok and not law_problems,
       "problems=%s recomputed=%s driver_laws=%s"
       % (problems[:4] if problems else [], recomputed_ok,
          law_problems[:2] if law_problems else []))

    # ---- AC-LVWB4: honest page face, badges, dashes, empty probe.
    dash = labels.get("none", "-")
    marked = all(('data-listing="%s"' % row["listing_id"]) in page
                 for row in rows)
    live_badge = labels.get("badge_live", "")
    delist_badge = labels.get("badge_delisted", "")
    labeled_badge = labels.get("badge_labeled", "")
    unlabeled_badge = labels.get("badge_unlabeled", "")
    badges_ok = all(
        ((delist_badge if bool(row["delisted"]) else live_badge) in page
         and (labeled_badge if int(row["ai_label"]) == 1 else unlabeled_badge)
         in page)
        for row in rows)
    zero_avg = [row for row in rows if int(row["rating_count"]) == 0]
    dash_avg = all("<b>%s</b>" % dash in page for _ in zero_avg)
    stamps_null = [row for row in rows
                   if row["latest_revision_utc"] is None]
    dash_stamp = all("<td>%s</td>" % dash in page for _ in stamps_null)
    stand_in = ">None<" in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_net", "law_refund", "law_rating", "law_avg",
             "law_stamp", "law_delist", "law_label", "law_order",
             "law_market", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    empty_probe_ok = False
    try:
        empty_rows, empty_market = probe_empty()
        probe_html = driver.build_html(empty_rows, empty_market, labels,
                                      "2026-01-01 00:00:00Z",
                                      doc.get("disclaimer") or "")
        empty_probe_ok = (labels.get("empty", "") in probe_html
                          and ">None<" not in probe_html
                          and 'data-listing="' not in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-LVWB4", marked and badges_ok and dash_avg and dash_stamp
       and not stand_in and laws_ok and empty_probe_ok,
       "rows=%s badges=%s zero_avg=%d dash_avg=%s null_stamp=%d dash_stamp=%s "
       "laws=%s empty_probe=%s stand_in_none=%s"
       % (marked, badges_ok, len(zero_avg), dash_avg, len(stamps_null),
          dash_stamp, laws_ok, empty_probe_ok, stand_in))

    # ---- AC-LVWB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    notadvice = labels.get("law_notadvice", "") in page
    ok("AC-LVWB5", aigc and on_page and external == 0 and notadvice,
       "aigc=%s disclaimer_on_page=%s external_links=%d notadvice=%s"
       % (aigc, on_page, external, notadvice))

    # ---- AC-LVWB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "api_view(" in read(FACE_SUITE)
    ok("AC-LVWB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())