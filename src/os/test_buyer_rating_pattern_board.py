"""Battery suite for tools/buyer_rating_pattern_board.py - criteria AC-BRPB1..6.

WHY THIS SUITE EXISTS (measured at R3406, not assumed):
api_buyer_rating_pattern has shipped with eight green criteria of its own
(test_apimarket_buyerratingpattern.py, AC-BRP) but git grep -F over tools/
and preview/ found no reader at all, so the marketplace's buyer-side question -
is this resident consistently harsh or generous, is it stricter than the market,
and how did its stars spread - could not be opened by anyone. R3406 renders it
onto one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3406 PIN
BEFORE the driver existed):
  AC-BRPB1 the page and its json land, the json carries exactly the pinned
           payload key set including the sizes and sources blocks, and every
           buyer block carries the shipped twenty-key envelope with a five-
           bucket star distribution.
  AC-BRPB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates buyers through the shipped
           api_board() and api_ratings() faces (never typed ids), reads
           api_buyer_rating_pattern() per buyer there, and requires the page
           json to equal those readings item for item plus the board
           disclaimer verbatim - no typed fixture, no synthesized spread.
  AC-BRPB3 the face's identities hold on every buyer: buckets sum to the
           rating count and to harsh+neutral+generous, star_sum re-derives from
           the buckets, the average and the two ratios re-derive from the
           counts with None on an honest empty, min/max are the measured
           extremes, tendency_delta is avg minus market average (None when
           either side is absent), and coverage is ratings over purchases.
  AC-BRPB4 the page reads honestly: buyer rows ascend by buyer id, exactly one
           table row per buyer in each of the two tables, an undefined ratio, an
           undefined tendency delta and a missing market average print the
           no-value mark rather than a fake zero, and the market average rides
           once and named.
  AC-BRPB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-BRPB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-BRP arms.

Read-only over the repository: the provenance world is built in a temp dir and
every re-render writes into a temp dir, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "buyer_rating_pattern_board.py")
HTML = os.path.join(ROOT, "preview", "buyer-rating-pattern-board.html")
JSONF = os.path.join(ROOT, "preview", "buyer-rating-pattern-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-rating-pattern-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_buyerratingpattern.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-buyer-rating-pattern-board"

DECLARED = 6

BUCKETS = ("1", "2", "3", "4", "5")

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "ratings_face", "buyer_count",
    "market_avg_stars", "buyers", "disclaimer", "report", "sources", "sizes",
}
BUYER_KEYS = {
    "buyer_id", "rating_count", "listing_count", "revision_count",
    "revised_rating_count", "star_sum", "avg_stars", "min_stars", "max_stars",
    "harsh_count", "neutral_count", "generous_count", "harsh_ratio",
    "generous_ratio", "market_avg_stars", "tendency_delta", "purchase_count",
    "rating_coverage", "star_distribution", "disclaimer",
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


def face_reading():
    """One envelope per buyer the shipped board and ratings faces enumerate."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="brpb-suite-")
    db = os.path.join(tmp_root, "brpb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = am.api_board()
        seen = set()
        for listing in board["listings"]:
            rated = am.api_ratings(listing["listing_id"])
            for row in rated.get("ratings") or []:
                buyer = row.get("buyer_id")
                if buyer:
                    seen.add(str(buyer))
        buyers = [dict(am.api_buyer_rating_pattern(buyer))
                  for buyer in sorted(seen)]
        return buyers, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def identity_problems(block):
    problems = []
    name = block.get("buyer_id")
    count = int(block["rating_count"])
    dist = block["star_distribution"]
    buckets = [int(dist[b]) for b in BUCKETS]
    harsh = int(block["harsh_count"])
    neutral = int(block["neutral_count"])
    generous = int(block["generous_count"])
    if sum(buckets) != count:
        problems.append("%s buckets_sum" % name)
    if harsh + neutral + generous != count:
        problems.append("%s three_ways" % name)
    if harsh != buckets[0] + buckets[1]:
        problems.append("%s harsh" % name)
    if neutral != buckets[2]:
        problems.append("%s neutral" % name)
    if generous != buckets[3] + buckets[4]:
        problems.append("%s generous" % name)
    want_sum = sum((i + 1) * n for i, n in enumerate(buckets))
    if int(block["star_sum"]) != want_sum:
        problems.append("%s star_sum" % name)
    want_avg = (float(want_sum) / count) if count else None
    if block["avg_stars"] != want_avg:
        problems.append("%s avg" % name)
    live = [i + 1 for i, n in enumerate(buckets) if n]
    if block["min_stars"] != (min(live) if live else None):
        problems.append("%s min" % name)
    if block["max_stars"] != (max(live) if live else None):
        problems.append("%s max" % name)
    for key, part in (("harsh_ratio", harsh), ("generous_ratio", generous)):
        want = (float(part) / count) if count else None
        if block[key] != want:
            problems.append("%s %s" % (name, key))
    market = block["market_avg_stars"]
    want_delta = (want_avg - market
                  if want_avg is not None and market is not None else None)
    if block["tendency_delta"] != want_delta:
        problems.append("%s tendency_delta" % name)
    bought = int(block["purchase_count"])
    want_cov = (float(count) / bought) if bought else None
    if block["rating_coverage"] != want_cov:
        problems.append("%s coverage" % name)
    return problems


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    buyers = doc.get("buyers") or []

    # ---- AC-BRPB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    buyer_keys_ok = all(set(block.keys()) == BUYER_KEYS for block in buyers)
    dist_ok = all(isinstance(block.get("star_distribution"), dict)
                  and sorted(block["star_distribution"].keys())
                  == list(BUCKETS) for block in buyers)
    ok("AC-BRPB1", landed and keys == PAYLOAD_KEYS and buyer_keys_ok
       and dist_ok and int(doc.get("buyer_count", -1)) == len(buyers),
       "landed=%s keys=%d missing=%s extra=%s buyer_keys=%s dist=%s"
       " buyers=%d"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), buyer_keys_ok, dist_ok, len(buyers)))

    # ---- AC-BRPB2: every printed number is the shipped face's own.
    live_buyers, disclaimer = face_reading()
    same_len = len(buyers) == len(live_buyers)
    diffs = []
    if same_len:
        for landed_buyer, live_buyer in zip(buyers, live_buyers):
            if json.dumps(landed_buyer, sort_keys=True) != json.dumps(
                    live_buyer, sort_keys=True):
                diffs.append(landed_buyer.get("buyer_id"))
    disc_same = doc.get("disclaimer") == disclaimer
    market_same = (doc.get("market_avg_stars")
                   == (live_buyers[0]["market_avg_stars"]
                       if live_buyers else None))
    ok("AC-BRPB2", same_len and not diffs and disc_same and market_same,
       "buyers=%d/%d diffs=%s disclaimer_same=%s market_avg_same=%s"
       % (len(buyers), len(live_buyers), diffs[:3], disc_same, market_same))

    # ---- AC-BRPB3: the face's identities hold on every buyer.
    problems = []
    for block in buyers:
        problems.extend(identity_problems(block))
    ok("AC-BRPB3", bool(buyers) and not problems,
       "buyers=%d problems=%s" % (len(buyers), problems[:4] if problems
                                  else []))

    # ---- AC-BRPB4: honest ordering, no-value marks, addressable rows.
    ids = [str(block["buyer_id"]) for block in buyers]
    order_ok = ids == sorted(ids)
    none = labels.get("none", "-")
    mark = ">%s<" % none
    undefined = [block for block in buyers
                 if block["harsh_ratio"] is None
                 or block["generous_ratio"] is None
                 or block["tendency_delta"] is None
                 or block["avg_stars"] is None]
    stand_in = ">None<" in page
    buyer_rows = page.count('<tr class="buyer">')
    shape_rows = page.count('<tr class="shape">')
    market_named = False
    if labels.get("kpi_marketavg"):
        market_named = labels["kpi_marketavg"] in page
    ok("AC-BRPB4", order_ok and buyer_rows == len(buyers)
       and shape_rows == len(buyers) and (not undefined or mark in page)
       and not stand_in and market_named,
       "order=%s buyer_rows=%d/%d shape_rows=%d/%d mark=%s stand_in_none=%s"
       " market_named=%s"
       % (order_ok, buyer_rows, len(buyers), shape_rows, len(buyers),
          mark in page, stand_in, market_named))

    # ---- AC-BRPB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-BRPB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-BRPB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    # The path element carries parentheses and commas of its own, so the count
    # is read from the first closing paren followed by , N ) after the name.
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-BRP" in read(FACE_SUITE)
    ok("AC-BRPB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
