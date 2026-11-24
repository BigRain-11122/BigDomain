"""Battery suite for tools/refund_propensity_board.py - criteria AC-BRFPB1..6.

WHY THIS SUITE EXISTS (measured at R3419, not assumed):
api_buyer_refund_propensity shipped with its own AC-RFP1..8 criteria
(src/sandbox/ledger/test_apimarket_buyerrefundpropensity.py) but a git grep
over tools/ and preview/ answered rc=1 with zero hits, so the question "how
heavy is my refund behaviour per purchase, and how does it compare with the
market" could not be opened by anyone. R3419 renders one reading per buyer on
one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3419 PIN
BEFORE the driver existed):
  AC-BRFPB1 the page and its json land, the json carries exactly the pinned
           payload key set including the market, smoothing, sizes and sources
           blocks, every buyer block carries the shipped sixteen-key envelope,
           buyer_count equals the block count, and the report points at a file
           that exists.
  AC-BRFPB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates buyers through the shipped board,
           sales and ratings faces, reads api_buyer_refund_propensity() over
           it, and requires the page json's buyers, market and smoothing
           strength to equal that reading item for item plus the disclaimer
           verbatim - no typed fixture, no synthesized row.
  AC-BRFPB3 the face's identities hold: refunds never exceed purchases, the
           non-refunded count, net spend, both rates, the market ratio, the raw
           delta and the shrinkage form all recompute from the printed
           numerator and denominator, and the market block is one world.
  AC-BRFPB4 the page reads honestly: one row per buyer with its named marker,
           percent text for both rates, a signed delta with its direction, a
           bar that the page calls a width with the market marker placed at the
           market rate, an explicit dash for an absent rate with no bare None,
           and an empty-base block handed to the driver's own renderer prints
           the dash instead of a fake zero (in-memory probe only).
  AC-BRFPB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-BRFPB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-RFP arms.

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
TOOL = os.path.join(ROOT, "tools", "refund_propensity_board.py")
HTML = os.path.join(ROOT, "preview", "refund-propensity-board.html")
JSONF = os.path.join(ROOT, "preview", "refund-propensity-board.json")
COPY = os.path.join(ROOT, "preview", "refund-propensity-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_buyerrefundpropensity.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-refund-propensity-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "source_face", "buyer_count",
    "buyers", "market", "smoothing_strength", "disclaimer", "report",
    "sources", "sizes",
}
BUYER_KEYS = {
    "buyer_id", "purchase_count", "refund_count",
    "non_refunded_purchase_count", "gross_spent", "refunded_tokens",
    "net_spent", "refund_rate", "refund_amount_rate", "market_purchase_count",
    "market_refund_count", "market_refund_rate", "refund_rate_delta",
    "smoothing_strength", "smoothed_refund_rate", "disclaimer",
}
MARKET_KEYS = {"purchase_count", "refund_count", "refund_rate"}

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
    tmp_root = tempfile.mkdtemp(prefix="rfpb-suite-")
    db = os.path.join(tmp_root, "rfpb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        seen = set()
        for dev in sorted(set(str(row["dev_account"])
                              for row in board["listings"])):
            for row in (dict(am.api_sales(dev)).get("sales") or []):
                if row.get("buyer_id"):
                    seen.add(str(row["buyer_id"]))
        for listing in board["listings"]:
            for row in (dict(am.api_ratings(listing["listing_id"]))
                        .get("ratings") or []):
                if row.get("buyer_id"):
                    seen.add(str(row["buyer_id"]))
        blocks = [dict(am.api_buyer_refund_propensity(buyer))
                  for buyer in sorted(seen)]
        market = {"purchase_count": blocks[0]["market_purchase_count"],
                  "refund_count": blocks[0]["market_refund_count"],
                  "refund_rate": blocks[0]["market_refund_rate"]}
        strength = blocks[0]["smoothing_strength"]
        return blocks, market, strength, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("rfpb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_problems(blocks, market, strength):
    problems = []

    def close(left, right):
        if left is None or right is None:
            return left is right or (left is None and right is None)
        return abs(float(left) - float(right)) <= 1e-9

    market_rate = market.get("refund_rate")
    if market.get("purchase_count"):
        if not close(market_rate, float(market["refund_count"])
                     / float(market["purchase_count"])):
            problems.append("market rate")
    elif market_rate is not None:
        problems.append("market rate on empty market")
    for block in blocks:
        name = str(block.get("buyer_id"))
        purchases = int(block.get("purchase_count", 0))
        refunds = int(block.get("refund_count", 0))
        gross = int(block.get("gross_spent", 0))
        refunded = int(block.get("refunded_tokens", 0))
        if refunds > purchases:
            problems.append("%s count bound" % name)
        if int(block.get("non_refunded_purchase_count", 0)) != purchases - refunds:
            problems.append("%s non refunded" % name)
        if int(block.get("net_spent", 0)) != gross - refunded:
            problems.append("%s net" % name)
        if int(block.get("market_purchase_count", -1)) != market["purchase_count"]:
            problems.append("%s market purchases" % name)
        if int(block.get("market_refund_count", -1)) != market["refund_count"]:
            problems.append("%s market refunds" % name)
        if int(block.get("smoothing_strength", 0)) != int(strength):
            problems.append("%s strength" % name)
        if purchases:
            if not close(block.get("refund_rate"),
                         float(refunds) / float(purchases)):
                problems.append("%s rate" % name)
        elif block.get("refund_rate") is not None:
            problems.append("%s rate on empty base" % name)
        if gross:
            if not close(block.get("refund_amount_rate"),
                         float(refunded) / float(gross)):
                problems.append("%s amount rate" % name)
        elif block.get("refund_amount_rate") is not None:
            problems.append("%s amount rate on empty gross" % name)
        rate = block.get("refund_rate")
        delta = block.get("refund_rate_delta")
        if rate is None or market_rate is None:
            if delta is not None:
                problems.append("%s delta without a side" % name)
        elif not close(delta, float(rate) - float(market_rate)):
            problems.append("%s delta" % name)
        smoothed = block.get("smoothed_refund_rate")
        if purchases and market_rate is not None:
            want = ((refunds + float(strength) * float(market_rate))
                    / (purchases + float(strength)))
            if not close(smoothed, want):
                problems.append("%s smoothed" % name)
        elif smoothed is not None:
            problems.append("%s smoothed without denominator" % name)
    return problems


def probe_empty(disclaimer, market):
    """A buyer with no purchase base: never landed, only handed to renderer."""
    return [{
        "buyer_id": "usr:probe-empty", "purchase_count": 0, "refund_count": 0,
        "non_refunded_purchase_count": 0, "gross_spent": 0,
        "refunded_tokens": 0, "net_spent": 0, "refund_rate": None,
        "refund_amount_rate": None,
        "market_purchase_count": market["purchase_count"],
        "market_refund_count": market["refund_count"],
        "market_refund_rate": market["refund_rate"],
        "refund_rate_delta": None, "smoothing_strength": 10,
        "smoothed_refund_rate": None, "disclaimer": disclaimer,
    }]


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    blocks = doc.get("buyers") or []
    market = doc.get("market") or {}
    strength = doc.get("smoothing_strength")

    # ---- AC-BRFPB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    blocks_ok = all(set(block.keys()) == BUYER_KEYS for block in blocks)
    market_ok = set(market.keys()) == MARKET_KEYS
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-BRFPB1", landed and keys == PAYLOAD_KEYS and blocks_ok and market_ok
       and sources_ok and bool(blocks)
       and int(doc.get("buyer_count", -1)) == len(blocks) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s blocks=%s market=%s sources=%s "
       "buyers=%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), blocks_ok, market_ok, sources_ok,
          len(blocks), report_ok))

    # ---- AC-BRFPB2: every printed number is the shipped face's own.
    live, live_market, live_strength, live_disclaimer = live_world()
    same = json.dumps(blocks, sort_keys=True) == json.dumps(
        live, sort_keys=True)
    market_same = (json.dumps(market, sort_keys=True)
                   == json.dumps(live_market, sort_keys=True))
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-BRFPB2", same and market_same and disc_same
       and strength == live_strength and bool(blocks),
       "identical=%s market_same=%s strength=%r/%r disclaimer_same=%s "
       "buyers=%d" % (same, market_same, strength, live_strength, disc_same,
                      len(blocks)))

    # ---- AC-BRFPB3: the face's identities hold on this envelope.
    problems = identity_problems(blocks, market, strength) if blocks \
        else ["no buyers"]
    ok("AC-BRFPB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-BRFPB4: honest page face, dashes, width bar with market marker.
    page_rows = page.count('<tr class="buyer')
    marked = all(('data-buyer="%s"' % block["buyer_id"]) in page
                 for block in blocks)
    rate_texts = all(("%.1f%%" % (float(block["refund_rate"]) * 100.0)) in page
                     for block in blocks if block["refund_rate"] is not None)
    delta_texts = all(("%+.1fpp" % (float(block["refund_rate_delta"]) * 100.0))
                      in page for block in blocks
                      if block["refund_rate_delta"] is not None)
    direction_ok = all((labels["dir_above"] in page if block["refund_rate_delta"]
                        and block["refund_rate_delta"] > 0 else True)
                       and (labels["dir_below"] in page
                            if block["refund_rate_delta"]
                            and block["refund_rate_delta"] < 0 else True)
                       for block in blocks)
    bar_ok = (page.count("<div class=bar>") == len(blocks)
              and page.count("<u style=") == len(blocks)
              and labels["law_bar"] in page)
    stand_in = ">None<" in page
    laws = [labels.get(key, "") for key in
            ("law_bound", "law_nonrefund", "law_net", "law_rate", "law_market",
             "law_delta", "law_smooth", "law_bar", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    extremes_ok = (labels.get("extremes_above", "") in page
                   and labels.get("extremes_below", "") in page)
    empty_probe_ok = False
    try:
        driver = load_driver()
        disclaimer = doc.get("disclaimer") or ""
        probe_html = driver.build_html(probe_empty(disclaimer, market), market,
                                       strength, labels,
                                       "2026-01-01 00:00:00Z", disclaimer)
        empty_probe_ok = (labels.get("none", "") in probe_html
                          and ">None<" not in probe_html
                          and probe_html.count('<tr class="buyer') == 1)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-BRFPB4", page_rows == len(blocks) and marked and rate_texts
       and delta_texts and direction_ok and bar_ok and not stand_in and laws_ok
       and extremes_ok and empty_probe_ok,
       "rows=%d/%d marked=%s rates=%s deltas=%s directions=%s bar=%s laws=%s "
       "extremes=%s empty_probe=%s stand_in_none=%s"
       % (page_rows, len(blocks), marked, rate_texts, delta_texts,
          direction_ok, bar_ok, laws_ok, extremes_ok, empty_probe_ok, stand_in))

    # ---- AC-BRFPB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-BRFPB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-BRFPB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-RFP" in read(FACE_SUITE)
    ok("AC-BRFPB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
