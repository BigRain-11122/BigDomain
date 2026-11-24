"""Battery suite for tools/price_reaction_board.py - AC-BPRB1..6.

WHY THIS SUITE EXISTS (measured at R3437, not assumed):
api_buyer_price_reaction shipped with its own AC-BPR1..AC-BPR8 criteria
(src/sandbox/ledger/test_apimarket_buyerpricereaction.py on disk) but a grep
over tools/, preview/ and the report collector answered zero hits, so the
resident's question - "of the shelves I watched, what did the price do, and
did I buy" - could not be opened by anyone. api_watch_alerts says what moved
and api_watch_budget says what the shelf costs now; neither links a movement
to the purchase that followed it. R3437 renders one section per buyer plus a
market card that adds those columns; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3437 PIN
BEFORE the driver existed):
  AC-BPRB1 the page and its json land, the json carries exactly the pinned
           eleven-key payload set, the market block and every buyer block
           carry the shipped 25-key envelope, every direction row carries the
           shipped 11-key row in the pinned drop/flat/rise order, buyer_count
           equals the block count, the report points at a file that exists,
           and the four source fingerprints are recorded.
  AC-BPRB2 the data is the shipped face's own: the suite re-seeds the fixture
           through the shipped doors, re-reads api_buyer_price_reaction() for
           every buyer on the shipped sales face and re-derives the market
           card, and requires the page json to equal that reading item for
           item - no typed fixture, no padded row.
  AC-BPRB3 the face's identities hold on the printed numbers: watch equals
           pre-owned plus funnel, funnel equals converted plus pending, every
           counter equals the sum of its three direction rows, delta_sum
           does too, a rate is null exactly when its funnel is empty, the
           average is null exactly when the watch set is empty, and the
           market card equals the column-wise sum of the buyer blocks.
  AC-BPRB4 the page reads honestly: one market card marked data-market, one
           card per buyer marked data-buyer, one row per direction marked
           data-direction, a rate bar is drawn exactly where the rate is
           defined, a dash is printed where it is not, a buyer with no watch
           prints the named quiet sentence instead of an empty table, no bare
           None, and every KPI strip equals the shipped envelope.
  AC-BPRB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer and the not-advice sentence are on the page
           and there are zero external links.
  AC-BPRB6 no older criterion is relaxed: the landed pair answers its own
           --check read-only and writes nothing, the reconcile registry
           declares six arms, the face's own suite is still on disk, and the
           deliverable index names this producer.

Usage: python src/os/test_price_reaction_board.py -> exit 0 all six green.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "price_reaction_board.py")
HTML = os.path.join(ROOT, "preview", "price-reaction-board.html")
JSONF = os.path.join(ROOT, "preview", "price-reaction-board.json")
COPY = os.path.join(ROOT, "preview", "price-reaction-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
DELIVERABLES = os.path.join(ROOT, "tools", "deliverable_index.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_buyerpricereaction.py")
ROW = "os-price-reaction-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "scope", "buyer_count",
    "buyers", "market", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "scope", "buyer_id", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate", "drop_count",
    "drop_converted_count", "drop_rate", "flat_count",
    "flat_converted_count", "flat_rate", "rise_count",
    "rise_converted_count", "rise_rate", "delta_sum", "avg_delta",
    "largest_drop", "largest_rise", "listing_count", "seller_count",
    "directions", "disclaimer",
}
ROW_KEYS = {
    "direction", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate", "delta_sum",
    "avg_delta", "largest_drop", "largest_rise",
}
COUNTERS = ("watch_count", "pre_owned_count", "funnel_count",
            "converted_count", "pending_count")
DIRECTIONS = ["drop", "flat", "rise"]

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


def run_tool(args):
    proc = subprocess.run(
        [sys.executable, TOOL] + args, cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def load_driver():
    spec = importlib.util.spec_from_file_location("prb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def block_problems(block, label):
    problems = []
    watches = int(block["watch_count"])
    pre_owned = int(block["pre_owned_count"])
    funnel = int(block["funnel_count"])
    converted = int(block["converted_count"])
    pending = int(block["pending_count"])
    if watches != pre_owned + funnel:
        problems.append("%s watch split" % label)
    if funnel != converted + pending:
        problems.append("%s funnel split" % label)
    rate = block["conversion_rate"]
    want = (float(converted) / funnel) if funnel else None
    if rate is None or want is None:
        if rate is not None or want is not None:
            problems.append("%s rate presence" % label)
    elif abs(float(rate) - want) > 1e-9:
        problems.append("%s rate value" % label)
    if (block["avg_delta"] is None) != (watches == 0):
        problems.append("%s average presence" % label)
    elif watches:
        if int(block["avg_delta"]) != int(block["delta_sum"]) // watches:
            problems.append("%s average floor" % label)
    if [row["direction"] for row in block["directions"]] != DIRECTIONS:
        problems.append("%s direction order" % label)
    for key in COUNTERS:
        walked = sum(int(row[key]) for row in block["directions"])
        if walked != int(block[key]):
            problems.append("%s %s row sum" % (label, key))
    if sum(int(row["delta_sum"]) for row in block["directions"]) != int(
            block["delta_sum"]):
        problems.append("%s delta sum" % label)
    for row in block["directions"]:
        if int(row["funnel_count"]) != int(row["converted_count"]) + int(
                row["pending_count"]):
            problems.append("%s %s funnel split" % (label, row["direction"]))
        if int(row["watch_count"]) != int(row["pre_owned_count"]) + int(
                row["funnel_count"]):
            problems.append("%s %s watch split" % (label, row["direction"]))
        want_rate = (float(row["converted_count"]) / int(row["funnel_count"])
                     if int(row["funnel_count"]) else None)
        if row["conversion_rate"] is None or want_rate is None:
            if row["conversion_rate"] is not None or want_rate is not None:
                problems.append("%s %s row rate" % (label, row["direction"]))
    drops = [int(b["largest_drop"]) for b in [block] if b["largest_drop"]
             is not None]
    if drops and min(drops) > 0:
        problems.append("%s drop sign" % label)
    return problems


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    market = doc.get("market") or {}
    buyers = doc.get("buyers") or []

    # ---- AC-BPRB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    blocks_ok = (set(market.keys()) == ENVELOPE_KEYS
                 and all(set(block.keys()) == ENVELOPE_KEYS
                         for block in buyers))
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for block in [market] + buyers
                  for row in block["directions"])
    order_ok = ([row["direction"] for row in market.get("directions", [])]
                == DIRECTIONS)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-BPRB1", landed and keys == PAYLOAD_KEYS and blocks_ok and rows_ok
       and order_ok and sources_ok and bool(buyers)
       and int(doc.get("buyer_count", -1)) == len(buyers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s blocks=%s rows=%s sources=%s "
       "buyers=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), blocks_ok, rows_ok, sources_ok,
          len(buyers), int(doc.get("buyer_count", -1)), report_ok))

    # ---- AC-BPRB2: every printed number is the shipped face's own.
    live_ok = False
    live_detail = "driver unavailable"
    try:
        driver = load_driver()
        live_blocks, live_buyers, live_disclaimer = driver.read_world()
        live_market = driver.rollup(live_blocks)
        market_same = json.dumps(market, sort_keys=True) == json.dumps(
            live_market, sort_keys=True)
        buyers_same = json.dumps(buyers, sort_keys=True) == json.dumps(
            live_blocks, sort_keys=True)
        ids_same = ([str(block["buyer_id"]) for block in buyers]
                    == [str(buyer) for buyer in live_buyers])
        disc_same = (doc.get("disclaimer") == live_disclaimer)
        order_same = all(
            [row["direction"] for row in block["directions"]] == DIRECTIONS
            for block in buyers)
        live_ok = (market_same and buyers_same and ids_same and disc_same
                   and order_same)
        live_detail = ("market_same=%s buyers_same=%s ids_same=%s "
                       "disclaimer_same=%s order_same=%s buyers=%d "
                       "watches=%d"
                       % (market_same, buyers_same, ids_same, disc_same,
                          order_same, len(buyers),
                          int(market.get("watch_count", -1))))
    except Exception as exc:  # noqa: BLE001
        live_detail = "read_world raised %s: %s" % (type(exc).__name__, exc)
    ok("AC-BPRB2", live_ok, live_detail)

    # ---- AC-BPRB3: the face's identities hold on the printed numbers.
    problems = block_problems(market, "market")
    seen = set()
    for block in buyers:
        label = str(block.get("buyer_id"))
        problems.extend(block_problems(block, label))
        if label in seen:
            problems.append("%s duplicated" % label)
        seen.add(label)
    for key in COUNTERS + ("delta_sum",):
        want = sum(int(block[key]) for block in buyers)
        if int(market.get(key, -1)) != want:
            problems.append("market %s vs buyer sum" % key)
    ok("AC-BPRB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-BPRB4: honest page face, badges, bars, dashes, quiet buyers.
    dash = labels.get("none", "\u2014")
    market_cards = len(re.findall(r'<div class="kpi" data-market>', page))
    buyer_cards = len(re.findall(r'<div class="card" data-buyer="', page))
    printed_rows = len(re.findall(r'<tr data-direction="', page))
    non_empty = [block for block in buyers if int(block["watch_count"])]
    expected_rows = 3 * (1 + len(non_empty))
    defined = sum(1 for block in [market] + non_empty
                  for row in block["directions"]
                  if row["conversion_rate"] is not None)
    bars = page.count('<span class="bar">')
    dash_cells = page.count(">%s<" % dash)
    no_none = ">None<" not in page
    badges = all(('<span class="badge %s">' % name) in page
                 for name in DIRECTIONS)
    empty_sentence = labels.get("empty_buyer", "empty buyer")
    quiet = page.count(empty_sentence)
    empty_buyers = sum(1 for block in buyers
                       if int(block["watch_count"]) == 0)
    kpi_ok = all(str(market[key]) in page for key in COUNTERS)
    ok("AC-BPRB4", market_cards == 1 and buyer_cards == len(buyers)
       and printed_rows == expected_rows and badges
       and bars == defined and dash_cells >= 1 and no_none
       and quiet == empty_buyers and kpi_ok,
       "market_cards=%d buyer_cards=%d/%d rows=%d/%d bars=%d/%d dashes=%d "
       "badges=%s empty=%d/%d kpi=%s bare_none=%s"
       % (market_cards, buyer_cards, len(buyers), printed_rows,
          expected_rows, bars, defined, dash_cells, badges, quiet,
          empty_buyers, kpi_ok, not no_none))

    # ---- AC-BPRB5: compliance faces ride along, zero external links.
    aigc = labels.get("aigc", "AIGC") in page
    disc_on_page = bool(doc.get("disclaimer")) and str(
        doc["disclaimer"]) in page
    not_advice = labels.get("law_notadvice", "not advice") in page
    links = len(re.findall(r"https?://", page))
    ok("AC-BPRB5", aigc and disc_on_page and not_advice and links == 0,
       "aigc=%s disclaimer_on_page=%s not_advice=%s external_links=%d"
       % (aigc, disc_on_page, not_advice, links))

    # ---- AC-BPRB6: no older criterion relaxed.
    before = (stamp(HTML), stamp(JSONF))
    rc1, out1 = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY) if os.path.exists(REGISTRY) else ""
    row_ok = ('("%s",' % ROW) in registry and registry.count(ROW) >= 1
    declared_ok = re.search(
        re.escape('"%s",' % ROW) + r"\s*\n?\s*os\.path\.join\([^)]*\),\s*6\)",
        registry) is not None
    face_ok = os.path.exists(FACE_SUITE) and "AC-BPR" in read(FACE_SUITE)
    producer = ("price-reaction-board.json" in read(DELIVERABLES)
                if os.path.exists(DELIVERABLES) else False)
    ok("AC-BPRB6", rc1 == 0 and before == after and row_ok and declared_ok
       and face_ok and producer,
       "check_rc=%d wrote_nothing=%s registry=%s declared=%s face_suite=%s "
       "producer=%s"
       % (rc1, before == after, row_ok, declared_ok, face_ok, producer))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    if len(CHECKS) != DECLARED:
        return 2
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
