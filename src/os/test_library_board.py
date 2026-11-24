"""Battery suite for tools/library_board.py - AC-LIBB1..6.

WHY THIS SUITE EXISTS (measured at R3435, not assumed):
api_library shipped with its own AC-AML1..8 criteria
(src/sandbox/ledger/test_apimarket_library.py on disk) but a git grep over
tools/ and preview/ answered rc=1 with zero hits, so the resident's own
question - "what did I buy, what did each one cost and what do I own now" -
could not be opened by anyone. api_sales is the seller side and the R3430
account statement prints totals; no page listed the individual purchases with
the charged price, the live asking price, the refund stamp, the retirement
stamp and this buyer's own stars side by side. R3435 renders the market row
plus one card per buyer; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3435 PIN
BEFORE the driver existed):
  AC-LIBB1 the page and its json land, the json carries exactly the pinned
           eleven-key payload set, every buyer block carries the shipped 8-key
           envelope, every purchase row carries the shipped 17-key row, the
           market block carries its six pinned keys, buyer_count equals the
           block count, the report points at a file that exists, and the four
           source fingerprints are recorded.
  AC-LIBB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates buyers through the shipped board
           and sales faces, reads api_library() per buyer, and requires the
           page json's buyers (including the disclaimer) to equal that
           reading item for item - no typed fixture.
  AC-LIBB3 the face's identities hold: purchase count equals rows, total spend
           equals the sum of charged prices, refund count equals refunded rows,
           net spend is total spend minus refunded, each row's two split legs
           add up to its charged price, the delisted flag is exactly the
           retirement stamp, the refunded flag is exactly the two refund
           stamps, a rating is absent or inside [1,5], purchase ids strictly
           ascend, the live asking price is non-negative, and the market block
           is the column sum of every printed envelope.
  AC-LIBB4 the page reads honestly: one card per buyer marked data-buyer, one
           row per purchase marked data-listing and data-refund, the refunded
           rows carry the refund badge, a retired shelf carries the delist
           badge with its stamp, the unrated row carries the unrated word, an
           honest empty buyer prints the named quiet sentence instead of an
           empty table, every buyer's KPI strip equals the shipped envelope,
           the twelve law sentences are present, and no bare None.
  AC-LIBB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer and the not-advice sentence are on the page
           and there are zero external links.
  AC-LIBB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, the
           producer is named in tools/deliverable_index.py, and the shipped
           face's own suite is still on disk with AC-AML arms.

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
TOOL = os.path.join(ROOT, "tools", "library_board.py")
HTML = os.path.join(ROOT, "preview", "library-board.html")
JSONF = os.path.join(ROOT, "preview", "library-board.json")
COPY = os.path.join(ROOT, "preview", "library-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
INDEX = os.path.join(ROOT, "tools", "deliverable_index.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_library.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-library-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "scope", "buyer_count",
    "buyers", "market", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "buyer_id", "purchase_count", "total_spent", "refund_count",
    "total_refunded", "net_spent", "disclaimer", "purchases",
}
ROW_KEYS = {
    "purchase_id", "listing_id", "listing_key", "title", "dev_account",
    "price_paid", "dev_share", "platform_share", "spend_tx",
    "purchased_utc", "current_price", "delisted", "delisted_utc",
    "my_rating", "refunded", "refunded_utc", "refund_tx",
}
MARKET_KEYS = {"buyer_count", "purchase_count", "total_spent",
               "refund_count", "total_refunded", "net_spent"}

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
    tmp_root = tempfile.mkdtemp(prefix="libb-suite-")
    db = os.path.join(tmp_root, "libb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        buyers = set()
        for row in board["listings"]:
            buyers.add(str(row["dev_account"]))
            sales = am.api_sales(str(row["dev_account"]))
            for sale in (sales.get("sales") or sales.get("rows") or []):
                if sale.get("buyer_id"):
                    buyers.add(str(sale["buyer_id"]))
        for who in ("bob", "carol", "dave", "erin"):
            buyers.add("usr:" + who)
        envelopes = [dict(am.api_library(buyer)) for buyer in sorted(buyers)]
        return envelopes, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("libb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row_problems(block, label):
    problems = []
    rows = block["purchases"]
    if int(block["purchase_count"]) != len(rows):
        problems.append("%s count" % label)
    if int(block["total_spent"]) != sum(int(r["price_paid"]) for r in rows):
        problems.append("%s total_spent" % label)
    if int(block["refund_count"]) != sum(1 for r in rows if r["refunded"]):
        problems.append("%s refund_count" % label)
    if int(block["net_spent"]) != (int(block["total_spent"])
                                  - int(block["total_refunded"])):
        problems.append("%s net_spent" % label)
    ids = [int(r["purchase_id"]) for r in rows]
    if ids != sorted(ids):
        problems.append("%s order" % label)
    for row in rows:
        tag = "%s#%s" % (label, row["purchase_id"])
        if (int(row["dev_share"]) + int(row["platform_share"])
                != int(row["price_paid"])):
            problems.append("%s split" % tag)
        if bool(row["delisted"]) != (row["delisted_utc"] is not None):
            problems.append("%s delist" % tag)
        if bool(row["refunded"]) != (row["refunded_utc"] is not None
                                     and row["refund_tx"] is not None):
            problems.append("%s refund stamps" % tag)
        stars = row["my_rating"]
        if stars is not None and not (1 <= int(stars) <= 5):
            problems.append("%s rating" % tag)
        if int(row["current_price"]) < 0:
            problems.append("%s live price" % tag)
        if not str(row.get("purchased_utc") or ""):
            problems.append("%s stamp" % tag)
    return problems


def empty_envelope():
    return {
        "buyer_id": "usr:probe", "purchase_count": 0, "total_spent": 0,
        "refund_count": 0, "total_refunded": 0, "net_spent": 0,
        "disclaimer": "probe disclaimer", "purchases": [],
    }


def row(pid, **over):
    base = {
        "purchase_id": pid, "listing_id": 10 + pid, "listing_key": "probe",
        "title": "Probe API", "dev_account": "usr:probe-dev",
        "price_paid": 10, "dev_share": 7, "platform_share": 3,
        "spend_tx": "deadbeefcafe0000", "purchased_utc": "2026-08-01T00:00:00Z",
        "current_price": 10, "delisted": False, "delisted_utc": None,
        "my_rating": None, "refunded": False, "refunded_utc": None,
        "refund_tx": None,
    }
    base.update(over)
    return base


def retired_envelope():
    """A retired shelf with no refund and no rating, so the delist badge and
    the dash both have a landed row to print."""
    rows = [row(1, delisted=True, delisted_utc="2026-09-02T03:04:05Z")]
    return {
        "buyer_id": "usr:probe", "purchase_count": 1, "total_spent": 10,
        "refund_count": 0, "total_refunded": 0, "net_spent": 10,
        "disclaimer": "probe disclaimer", "purchases": rows,
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    buyers = doc.get("buyers") or []
    market = doc.get("market") or {}

    # ---- AC-LIBB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelopes_ok = all(set(block.keys()) == ENVELOPE_KEYS for block in buyers)
    rows_ok = all(set(item.keys()) == ROW_KEYS
                  for block in buyers for item in block["purchases"])
    market_ok = set(market.keys()) == MARKET_KEYS
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-LIBB1", landed and keys == PAYLOAD_KEYS and envelopes_ok
       and rows_ok and market_ok and sources_ok and bool(buyers)
       and int(doc.get("buyer_count", -1)) == len(buyers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelopes=%s rows=%s "
       "market=%s sources=%s count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelopes_ok, rows_ok, market_ok,
          sources_ok, len(buyers), int(doc.get("buyer_count", -1)),
          report_ok))

    # ---- AC-LIBB2: every printed number is the shipped face's own.
    live_buyers, live_disclaimer = live_world()
    same = json.dumps(buyers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in ENVELOPE_KEYS} for block in live_buyers],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-LIBB2", same and disc_same and bool(buyers),
       "buyers_same=%s disclaimer_same=%s buyers=%d purchases=%d"
       % (same, disc_same, len(buyers),
          sum(int(b["purchase_count"]) for b in buyers)))

    # ---- AC-LIBB3: the face's identities hold on these envelopes.
    problems = []
    seen = set()
    for block in buyers:
        label = str(block.get("buyer_id"))
        problems.extend(row_problems(block, label))
        if label in seen:
            problems.append("%s duplicated" % label)
        seen.add(label)
    for key in ("purchase_count", "total_spent", "refund_count",
                "total_refunded", "net_spent"):
        want = sum(int(block[key]) for block in buyers)
        if int(market.get(key, -1)) != want:
            problems.append("market %s" % key)
    if int(market.get("buyer_count", -1)) != len(buyers):
        problems.append("market buyer_count")
    ok("AC-LIBB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-LIBB4: honest page face, badges, dashes, quiet accounts.
    dash = labels.get("none", "-")
    sections = len(re.findall(r'<div class=card data-buyer="', page))
    landed_rows = len(re.findall(r"<tr data-listing=\"", page))
    total_rows = sum(int(b["purchase_count"]) for b in buyers)
    refunded_rows = sum(1 for b in buyers for r in b["purchases"]
                        if r["refunded"])
    refund_markers = len(re.findall(r"<tr data-listing=\"\d+\" "
                                    r"data-refund=\"1\"", page))
    unrated_rows = sum(1 for b in buyers for r in b["purchases"]
                       if r["my_rating"] is None)
    unrated_mark = '<span class="badge quiet">%s</span>' % labels.get(
        "badge_unrated", "@@")
    unrated_badges = page.count(unrated_mark)
    rated_rows = total_rows - unrated_rows
    rated_mark = '<span class="badge rated">%s</span>' % labels.get(
        "badge_rated", "@@")
    rated_badges = page.count(rated_mark)
    empty_buyers = sum(1 for b in buyers if not b["purchases"])
    empty_sentences = page.count(labels.get("empty_buyer", "@@"))
    no_none = ">None<" not in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_spend", "law_refund", "law_net", "law_split",
             "law_delist", "law_refundstamp", "law_rating", "law_order",
             "law_live", "law_market", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    kpi_ok = False
    empty_ok = retired_ok = True
    try:
        driver = load_driver()
        e = driver.html.escape
        kpi_ok = all(driver.kpi_html(block, labels, e, dash) in page
                     for block in buyers)
        probe = empty_envelope()
        empty_html = driver.build_html(
            [probe], driver.market_block([probe], "probe disclaimer"),
            labels, "2026-01-01 00:00:00Z", "probe disclaimer")
        empty_ok = (labels.get("empty_buyer", "") in empty_html
                    and "<tr data-listing=" not in empty_html
                    and ">None<" not in empty_html)
        retired = retired_envelope()
        retired_html = driver.build_html(
            [retired], driver.market_block([retired], "probe disclaimer"),
            labels, "2026-01-01 00:00:00Z", "probe disclaimer")
        retired_ok = ('<span class="badge delist">%s</span>'
                      % labels.get("badge_delisted", "@@") in retired_html
                      and "2026-09-02T03:04:05Z" in retired_html
                      and '<span class="badge refund">' not in retired_html
                      and unrated_mark in retired_html
                      and ">None<" not in retired_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
        kpi_ok = False
    ok("AC-LIBB4", sections == len(buyers) and landed_rows == total_rows
       and refund_markers == refunded_rows
       and unrated_badges == unrated_rows and rated_badges == rated_rows
       and empty_sentences == empty_buyers and no_none and laws_ok
       and kpi_ok and empty_ok and retired_ok,
       "sections=%d/%d rows=%d/%d refund_markers=%d/%d unrated=%d/%d "
       "rated=%d/%d empty=%d/%d laws=%s kpi=%s empty_probe=%s "
       "retired_probe=%s bare_none=%s"
       % (sections, len(buyers), landed_rows, total_rows, refund_markers,
          refunded_rows, unrated_badges, unrated_rows, rated_badges,
          rated_rows, empty_sentences, empty_buyers, laws_ok, kpi_ok,
          empty_ok, retired_ok, not no_none))

    # ---- AC-LIBB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    not_advice = labels.get("law_notadvice", "") in page
    external = len(re.findall(r"https?://", page))
    ok("AC-LIBB5", aigc and on_page and not_advice and external == 0,
       "aigc=%s disclaimer_on_page=%s not_advice=%s external_links=%d"
       % (aigc, on_page, not_advice, external))

    # ---- AC-LIBB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-AML" in read(FACE_SUITE)
    producer = open(INDEX, encoding="utf-8").read()
    producer_ok = '"library-board.json": "tools/library_board.py"' in producer
    ok("AC-LIBB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok and producer_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s producer=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok, producer_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
