"""Battery suite for tools/buyer_concentration_board.py - AC-BCCB1..6.

WHY THIS SUITE EXISTS (measured at R3428, not assumed):
api_buyer_concentration shipped with its own AC-BC1..8 criteria
(src/sandbox/ledger/test_apimarket_buyerconcentration.py on disk) but a git
grep over tools/ and preview/ answered rc=1 with zero hits, so the resident's
own question - "is my money all on one shop and one category, or is it spread"
- could not be opened by anyone. The seller side carries
api_seller_concentration; the buyer side carried only two share tables with no
index at all. R3428 renders one summary table plus one section per buyer
carrying both axes; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3428 PIN
BEFORE the driver existed):
  AC-BCCB1 the page and its json land, the json carries exactly the pinned
           payload key set, every buyer block carries the shipped 20-key
           envelope, every seller row carries the shipped 11 keys and every
           category row the shipped 11 keys, buyer_count equals the block
           count, the report points at a file that exists, and the four source
           fingerprints are recorded.
  AC-BCCB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates buyers through the shipped board,
           sales and ratings faces, reads api_buyer_concentration() per buyer,
           and requires the page json's buyers (including every row and the
           disclaimer) to equal that reading item for item - no typed fixture.
  AC-BCCB3 the face's identities hold: on both axes the envelope counts and
           amounts are the row sums, the net is gross minus refunded, the
           bucket count is the row count, the refunded seller count is the
           sellers with a refund, each row's net purchase count and net spend
           recompute, the ranks are 1..n in the face's own total order, and
           the share, cumulative share, top1, top3, herfindahl and pareto
           count recompute from the exact fractions - None rather than a
           fabricated zero when the net is not positive.
  AC-BCCB4 the page reads honestly: a summary table plus one section per buyer
           with both axes marked, every row marked with its rank, an undefined
           share or index printed as the dash, a null category printed as the
           named uncategorized label, the width bar called a width, and the
           explicit sentence about a non-positive net - proved by two in-memory
           probes: a fully refunded envelope printing dashes and no bar, and a
           three-equal-bucket envelope printing six bars, a 3333.33 index and
           a cumulative of 100%.
  AC-BCCB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, the not-advice sentence is
           present, and there are zero external links.
  AC-BCCB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with AC-BC arms.

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
TOOL = os.path.join(ROOT, "tools", "buyer_concentration_board.py")
HTML = os.path.join(ROOT, "preview", "buyer-concentration-board.html")
JSONF = os.path.join(ROOT, "preview", "buyer-concentration-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-concentration-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_buyerconcentration.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-buyer-concentration-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "sales_face", "ratings_face",
    "buyer_count", "buyers", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "buyer_id", "purchase_count", "refund_count", "seller_count",
    "category_count", "refunded_sellers", "gross_spend", "refunded_tokens",
    "net_spend", "top1_seller_share", "top3_seller_share",
    "seller_herfindahl", "pareto_seller_count", "top1_category_share",
    "top3_category_share", "category_herfindahl", "pareto_category_count",
    "disclaimer", "sellers", "categories",
}
ROW_COMMON = {
    "purchase_count", "refund_count", "net_purchase_count", "gross_spend",
    "refunded_tokens", "net_spend", "listing_count", "share",
    "cumulative_share", "rank",
}
SELLER_ROW_KEYS = ROW_COMMON | {"dev_account"}
CATEGORY_ROW_KEYS = ROW_COMMON | {"category"}

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
    tmp_root = tempfile.mkdtemp(prefix="bccb-suite-")
    db = os.path.join(tmp_root, "bccb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        sellers = sorted({str(row["dev_account"]) for row in board["listings"]})
        seen = set()
        for dev in sellers:
            for row in (am.api_sales(dev).get("sales") or []):
                if row.get("buyer_id"):
                    seen.add(str(row["buyer_id"]))
        for listing in board["listings"]:
            for row in (am.api_ratings(listing["listing_id"]).get("ratings")
                        or []):
                if row.get("buyer_id"):
                    seen.add(str(row["buyer_id"]))
        buyers = [dict(am.api_buyer_concentration(b)) for b in sorted(seen)]
        return buyers, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("bccb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close(left, right, tol=1e-6):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= tol


def axis_problems(block, axis, label):
    problems = []
    rows = list(block[axis])
    total = int(block["net_spend"])
    if int(block["purchase_count"]) != sum(int(r["purchase_count"])
                                           for r in rows):
        problems.append("%s %s purchases" % (label, axis))
    if int(block["refund_count"]) != sum(int(r["refund_count"]) for r in rows):
        problems.append("%s %s refunds" % (label, axis))
    if int(block["gross_spend"]) != sum(int(r["gross_spend"]) for r in rows):
        problems.append("%s %s gross" % (label, axis))
    if int(block["refunded_tokens"]) != sum(int(r["refunded_tokens"])
                                            for r in rows):
        problems.append("%s %s refunded" % (label, axis))
    if total != sum(int(r["net_spend"]) for r in rows):
        problems.append("%s %s net" % (label, axis))
    if int(block["gross_spend"]) - int(block["refunded_tokens"]) != total:
        problems.append("%s %s net!=gross-refunded" % (label, axis))
    key = "dev_account" if axis == "sellers" else "category"
    counted = int(block["seller_count" if axis == "sellers"
                        else "category_count"])
    if counted != len(rows):
        problems.append("%s %s bucket_count" % (label, axis))
    order = sorted(rows, key=lambda r: (-int(r["net_spend"]),
                                        -int(r["gross_spend"]), str(r[key])))
    if [r[key] for r in order] != [r[key] for r in rows]:
        problems.append("%s %s order" % (label, axis))
    for index, row in enumerate(rows, 1):
        if int(row["rank"]) != index:
            problems.append("%s %s rank" % (label, axis))
        if int(row["net_purchase_count"]) != (int(row["purchase_count"])
                                             - int(row["refund_count"])):
            problems.append("%s %s net purchases" % (label, axis))
        if int(row["net_spend"]) != (int(row["gross_spend"])
                                     - int(row["refunded_tokens"])):
            problems.append("%s %s row net" % (label, axis))
    suffix = "seller" if axis == "sellers" else "category"
    top1 = block["top1_%s_share" % suffix]
    top3 = block["top3_%s_share" % suffix]
    hhi = block["%s_herfindahl" % suffix]
    pareto = block["pareto_%s_count" % suffix]
    if total > 0:
        exact = [float(r["net_spend"]) / total for r in rows]
        if not close(top1, round(exact[0], 6)):
            problems.append("%s %s top1" % (label, axis))
        if not close(top3, round(sum(exact[:3]), 6)):
            problems.append("%s %s top3" % (label, axis))
        if not close(hhi, round(sum(v * v for v in exact) * 10000, 2), 1e-3):
            problems.append("%s %s hhi" % (label, axis))
        running = 0
        want_pareto = None
        for index, row in enumerate(rows, 1):
            running += int(row["net_spend"])
            if running * 5 >= total * 4:
                want_pareto = index
                break
        if pareto != want_pareto:
            problems.append("%s %s pareto" % (label, axis))
        running = 0
        for row in rows:
            if not close(row["share"],
                         round(float(row["net_spend"]) / total, 6)):
                problems.append("%s %s share" % (label, axis))
            running += int(row["net_spend"])
            if not close(row["cumulative_share"],
                         round(float(running) / total, 6)):
                problems.append("%s %s cumulative" % (label, axis))
        if rows and not close(rows[-1]["cumulative_share"], 1.0):
            problems.append("%s %s last cumulative" % (label, axis))
    else:
        for name, value in (("top1", top1), ("top3", top3), ("hhi", hhi),
                            ("pareto", pareto)):
            if value is not None:
                problems.append("%s %s %s not None" % (label, axis, name))
        for row in rows:
            if row["share"] is not None or row["cumulative_share"] is not None:
                problems.append("%s %s row share not None" % (label, axis))
    if axis == "sellers":
        refunded = sum(1 for r in rows if int(r["refund_count"]) > 0)
        if int(block["refunded_sellers"]) != refunded:
            problems.append("%s refunded_sellers" % label)
    return problems


def zero_net_envelope():
    row = {
        "purchase_count": 1, "refund_count": 1, "net_purchase_count": 0,
        "gross_spend": 5, "refunded_tokens": 5, "net_spend": 0,
        "listing_count": 1, "share": None, "cumulative_share": None, "rank": 1,
    }
    seller = dict(row)
    seller["dev_account"] = "usr:probe"
    category = dict(row)
    category["category"] = None
    return {
        "buyer_id": "usr:probe", "purchase_count": 1, "refund_count": 1,
        "seller_count": 1, "category_count": 1, "refunded_sellers": 1,
        "gross_spend": 5, "refunded_tokens": 5, "net_spend": 0,
        "top1_seller_share": None, "top3_seller_share": None,
        "seller_herfindahl": None, "pareto_seller_count": None,
        "top1_category_share": None, "top3_category_share": None,
        "category_herfindahl": None, "pareto_category_count": None,
        "disclaimer": "probe disclaimer",
        "sellers": [seller], "categories": [category],
    }


def three_bucket_envelope():
    def rows(key, names):
        out = []
        running = 0
        for index, name in enumerate(names, 1):
            running += 10
            entry = {
                "purchase_count": 1, "refund_count": 0,
                "net_purchase_count": 1, "gross_spend": 10,
                "refunded_tokens": 0, "net_spend": 10, "listing_count": 1,
                "share": 0.333333,
                "cumulative_share": round(running / 30.0, 6),
                "rank": index,
            }
            entry[key] = name
            out.append(entry)
        return out
    return {
        "buyer_id": "usr:probe", "purchase_count": 3, "refund_count": 0,
        "seller_count": 3, "category_count": 3, "refunded_sellers": 0,
        "gross_spend": 30, "refunded_tokens": 0, "net_spend": 30,
        "top1_seller_share": 0.333333, "top3_seller_share": 1.0,
        "seller_herfindahl": 3333.33, "pareto_seller_count": 3,
        "top1_category_share": 0.333333, "top3_category_share": 1.0,
        "category_herfindahl": 3333.33, "pareto_category_count": 3,
        "disclaimer": "probe disclaimer",
        "sellers": rows("dev_account", ["usr:a", "usr:b", "usr:c"]),
        "categories": rows("category", ["cat-a", "cat-b", "cat:c"]),
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    buyers = doc.get("buyers") or []

    # ---- AC-BCCB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelopes_ok = all(set(block.keys()) == ENVELOPE_KEYS for block in buyers)
    rows_ok = all(set(row.keys()) == SELLER_ROW_KEYS
                  for block in buyers for row in (block.get("sellers") or []))
    cats_ok = all(set(row.keys()) == CATEGORY_ROW_KEYS
                  for block in buyers
                  for row in (block.get("categories") or []))
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-BCCB1", landed and keys == PAYLOAD_KEYS and envelopes_ok and rows_ok
       and cats_ok and sources_ok and bool(buyers)
       and int(doc.get("buyer_count", -1)) == len(buyers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelopes=%s seller_rows=%s "
       "category_rows=%s sources=%s count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelopes_ok, rows_ok, cats_ok,
          sources_ok, len(buyers), int(doc.get("buyer_count", -1)),
          report_ok))

    # ---- AC-BCCB2: every printed number is the shipped face's own.
    live_buyers, live_disclaimer = live_world()
    same = json.dumps(buyers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in ENVELOPE_KEYS} for block in live_buyers],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-BCCB2", same and disc_same and bool(buyers),
       "buyers_same=%s disclaimer_same=%s buyers=%d rows=%d"
       % (same, disc_same, len(buyers),
          sum(len(b["sellers"]) + len(b["categories"]) for b in buyers)))

    # ---- AC-BCCB3: the face's identities hold on these envelopes.
    problems = []
    for block in buyers:
        name = str(block.get("buyer_id"))
        problems.extend(axis_problems(block, "sellers", name))
        problems.extend(axis_problems(block, "categories", name))
        if int(block["seller_count"]) != len(block["sellers"]):
            problems.append("%s seller_count" % name)
        if int(block["category_count"]) != len(block["categories"]):
            problems.append("%s category_count" % name)
    ok("AC-BCCB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-BCCB4: honest page face, dashes, width bars, two probes.
    dash = labels.get("none", "-")
    summary_marked = (len(re.findall(r'<tr class=buyer data-buyer="', page))
                      == len(buyers))
    axes_marked = page.count('data-axis="sellers"') >= len(buyers) and \
        page.count('data-axis="categories"') >= len(buyers)
    landed_rows = sum(len(b["sellers"]) + len(b["categories"])
                      for b in buyers)
    ranks_marked = len(re.findall(r'data-rank="\d+"', page)) == landed_rows
    bars_honest = page.count("<div class=bar>") == sum(
        1 for b in buyers for row in (b["sellers"] + b["categories"])
        if row["share"] is not None)
    zero_net_sentence = labels.get("zero_net", "") in page
    uncategorized = labels.get("label_uncategorized", "") in page
    no_none = ">None<" not in page
    laws = [labels.get(key, "") for key in
            ("law_totals", "law_rows", "law_rank", "law_share", "law_cumulative",
             "law_top1", "law_hhi", "law_pareto", "law_bar", "law_zero",
             "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    zero_ok = three_ok = False
    try:
        driver = load_driver()
        zero_html = driver.build_html([zero_net_envelope()], labels,
                                      "2026-01-01 00:00:00Z",
                                      "probe disclaimer")
        zero_ok = (zero_html.count("<div class=bar>") == 0
                   and ">None<" not in zero_html
                   and dash in zero_html
                   and labels.get("zero_net", "") in zero_html
                   and labels.get("label_uncategorized", "") in zero_html)
        three_html = driver.build_html([three_bucket_envelope()], labels,
                                       "2026-01-01 00:00:00Z",
                                       "probe disclaimer")
        three_ok = (three_html.count("<div class=bar>") == 6
                    and "3333.33" in three_html
                    and "100.0%" in three_html
                    and ">None<" not in three_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-BCCB4", summary_marked and axes_marked and ranks_marked
       and bars_honest and zero_net_sentence and uncategorized and no_none
       and laws_ok and zero_ok and three_ok,
       "summary=%s axes=%s ranks=%s bars=%s zero_sentence=%s uncategorized=%s "
       "laws=%s zero_probe=%s three_probe=%s bare_none=%s"
       % (summary_marked, axes_marked, ranks_marked, bars_honest,
          zero_net_sentence, uncategorized, laws_ok, zero_ok, three_ok,
          not no_none))

    # ---- AC-BCCB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    not_advice = labels.get("law_notadvice", "") in page
    external = len(re.findall(r"https?://", page))
    ok("AC-BCCB5", aigc and on_page and not_advice and external == 0,
       "aigc=%s disclaimer_on_page=%s not_advice=%s external_links=%d"
       % (aigc, on_page, not_advice, external))

    # ---- AC-BCCB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-BC" in read(FACE_SUITE)
    ok("AC-BCCB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
