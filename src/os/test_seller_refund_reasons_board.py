"""Battery suite for tools/seller_refund_reasons_board.py - AC-SRRB1..6.

WHY THIS SUITE EXISTS (measured at R3424, not assumed):
api_seller_refund_reasons shipped with its own AC-SRR1..8 criteria
(src/sandbox/ledger/test_apimarket_sellerrefundreasons.py on disk) but a git
grep over tools/ and preview/ answered rc=1 with zero hits, so the seller's own
question - "what are my refunds actually caused by, and how heavy is that
against the market benchmark" - could not be opened by anyone. The market-wide
reason board (R3407) and the seller monthly board (R3421) answer other
questions. R3424 renders one market section plus one section per seller on one
page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3424 PIN
BEFORE the driver existed):
  AC-SRRB1 the page and its json land, the json carries exactly the pinned
           payload key set, the market block and every seller block carry the
           shipped 17-key envelope, every reason row carries the shipped 8
           keys, seller_count equals the block count, the report points at a
           file that exists, and the four source fingerprints are recorded.
  AC-SRRB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates sellers through the shipped board
           face, reads api_seller_refund_reasons() once for the market and once
           per seller, and requires the page json's market and sellers
           (including every reason row and the disclaimer) to equal that
           reading item for item - no typed fixture.
  AC-SRRB3 the face's identities hold: bucket counts sum to the envelope count,
           bucket amounts sum to the envelope total, labeled plus unlabeled
           equals the count, both legs add up to each bucket amount, the share
           and the bucket average recompute (and are None rather than a
           fabricated zero where their denominator is zero), the refund rate
           and the concentration measure recompute, the named cause is taken
           from labeled buckets only with its labeled denominator, the rows
           keep the face's own order with the unlabeled bucket last, and the
           market scope leaves both benchmark columns empty while the seller
           scope mirrors the market rate and this seller's share of the market
           refunded total.
  AC-SRRB4 the page reads honestly: one market section and one marked section
           per seller, an absent rate or share printed as the dash instead of a
           zero, no bare None, a bar the page calls a width and not a share, and
           two in-memory probes - a zero envelope and an envelope carrying an
           unlabeled bucket - printing the dash, the named unlabeled label and
           the unlabeled row last, never a fabricated row.
  AC-SRRB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-SRRB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with AC-SRR arms.

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
TOOL = os.path.join(ROOT, "tools", "seller_refund_reasons_board.py")
HTML = os.path.join(ROOT, "preview", "seller-refund-reasons-board.html")
JSONF = os.path.join(ROOT, "preview", "seller-refund-reasons-board.json")
COPY = os.path.join(ROOT, "preview", "seller-refund-reasons-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_sellerrefundreasons.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-refund-reasons-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "source_face", "scope",
    "seller_count", "market", "sellers", "disclaimer", "report", "sources",
    "sizes",
}
ENVELOPE_KEYS = {
    "scope", "dev_account", "purchase_count", "refund_count", "refund_rate",
    "refunded_total", "labeled_count", "unlabeled_count", "reason_count",
    "top_reason", "top_reason_count", "top_reason_share",
    "reason_herfindahl", "market_refund_rate", "market_refund_share",
    "rows", "disclaimer",
}
ROW_KEYS = {
    "reason", "refund_count", "refunded", "dev_share", "platform_share",
    "share", "avg_amount", "listing_count",
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
    """The shipped face's own reading over the suite's throwaway demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="srrb-suite-")
    db = os.path.join(tmp_root, "srrb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        sellers = sorted({str(row["dev_account"]) for row in board["listings"]})
        market = dict(am.api_seller_refund_reasons())
        scoped = [dict(am.api_seller_refund_reasons(seller))
                  for seller in sellers]
        return market, scoped, market["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("srrb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def order_of(row):
    return (1 if row["reason"] is None else 0,
            -int(row["refund_count"]), -int(row["refunded"]),
            row["reason"] or "")


def envelope_problems(envelope, label):
    problems = []
    rows = envelope["rows"]
    count = int(envelope["refund_count"])
    if count != sum(int(row["refund_count"]) for row in rows):
        problems.append("%s count sum" % label)
    if int(envelope["refunded_total"]) != sum(
            int(row["refunded"]) for row in rows):
        problems.append("%s total sum" % label)
    if int(envelope["labeled_count"]) + int(envelope["unlabeled_count"]) != count:
        problems.append("%s labeled split" % label)
    if int(envelope["labeled_count"]) != sum(
            int(row["refund_count"]) for row in rows
            if row["reason"] is not None):
        problems.append("%s labeled count" % label)
    if int(envelope["unlabeled_count"]) != sum(
            int(row["refund_count"]) for row in rows
            if row["reason"] is None):
        problems.append("%s unlabeled count" % label)
    if int(envelope["reason_count"]) != len(rows):
        problems.append("%s reason_count" % label)
    purchases = int(envelope["purchase_count"])
    want_rate = round(float(count) / purchases, 4) if purchases else None
    if not close(envelope["refund_rate"], want_rate):
        problems.append("%s rate" % label)
    want_hhi = None
    if count:
        want_hhi = round(sum(
            (float(row["refund_count"]) / count) ** 2 for row in rows
        ) * 10000, 2)
    if not close(envelope["reason_herfindahl"], want_hhi):
        problems.append("%s hhi" % label)
    for row in rows:
        tag = "%s/%s" % (label, row["reason"])
        if int(row["dev_share"]) + int(row["platform_share"]) != int(
                row["refunded"]):
            problems.append("%s legs" % tag)
        want_share = (round(float(row["refund_count"]) / count, 4)
                      if count else None)
        if not close(row["share"], want_share):
            problems.append("%s share" % tag)
        want_avg = (round(float(row["refunded"]) / int(row["refund_count"]), 2)
                    if int(row["refund_count"]) else None)
        if not close(row["avg_amount"], want_avg):
            problems.append("%s avg" % tag)
    labeled = [row for row in rows if row["reason"] is not None]
    if labeled:
        best = sorted(labeled, key=lambda row: (
            -int(row["refund_count"]), -int(row["refunded"]),
            row["reason"]))[0]
        if envelope["top_reason"] != best["reason"]:
            problems.append("%s top reason" % label)
        if int(envelope["top_reason_count"] or -1) != int(
                best["refund_count"]):
            problems.append("%s top count" % label)
        labeled_count = sum(int(row["refund_count"]) for row in labeled)
        want_share = round(float(best["refund_count"]) / labeled_count, 4) \
            if labeled_count else None
        if not close(envelope["top_reason_share"], want_share):
            problems.append("%s top share" % label)
    else:
        for key in ("top_reason", "top_reason_count", "top_reason_share"):
            if envelope[key] is not None:
                problems.append("%s %s" % (label, key))
    if [order_of(row) for row in rows] != sorted(order_of(row) for row in rows):
        problems.append("%s row order" % label)
    return problems


def zero_envelope(scope="market", dev_account=None):
    return {
        "scope": scope, "dev_account": dev_account, "purchase_count": 0,
        "refund_count": 0, "refund_rate": None, "refunded_total": 0,
        "labeled_count": 0, "unlabeled_count": 0, "reason_count": 0,
        "top_reason": None, "top_reason_count": None,
        "top_reason_share": None, "reason_herfindahl": None,
        "market_refund_rate": None, "market_refund_share": None,
        "rows": [], "disclaimer": "probe disclaimer",
    }


def mixed_envelope():
    """A probe envelope carrying one labeled bucket and one unlabeled one."""
    return {
        "scope": "market", "dev_account": None, "purchase_count": 4,
        "refund_count": 2, "refund_rate": 0.5, "refunded_total": 15,
        "labeled_count": 1, "unlabeled_count": 1, "reason_count": 2,
        "top_reason": "aaa", "top_reason_count": 1, "top_reason_share": 1.0,
        "reason_herfindahl": 5000.0, "market_refund_rate": None,
        "market_refund_share": None,
        "rows": [
            {"reason": "aaa", "refund_count": 1, "refunded": 10,
             "dev_share": 7, "platform_share": 3, "share": 0.5,
             "avg_amount": 10.0, "listing_count": 1},
            {"reason": None, "refund_count": 1, "refunded": 5,
             "dev_share": 4, "platform_share": 1, "share": 0.5,
             "avg_amount": 5.0, "listing_count": 1},
        ],
        "disclaimer": "probe disclaimer",
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    market = doc.get("market") or {}
    sellers = doc.get("sellers") or []
    all_rows = list(market.get("rows") or []) + [
        row for block in sellers for row in (block.get("rows") or [])]

    # ---- AC-SRRB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelopes_ok = (set(market.keys()) == ENVELOPE_KEYS
                    and all(set(block.keys()) == ENVELOPE_KEYS
                            for block in sellers))
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in all_rows)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-SRRB1", landed and keys == PAYLOAD_KEYS and envelopes_ok and rows_ok
       and sources_ok and bool(sellers)
       and int(doc.get("seller_count", -1)) == len(sellers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelopes=%s rows=%s "
       "sources=%s count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelopes_ok, rows_ok, sources_ok,
          len(sellers), int(doc.get("seller_count", -1)), report_ok))

    # ---- AC-SRRB2: every printed number is the shipped face's own.
    live_market, live_sellers, live_disclaimer = live_world()
    market_same = json.dumps(market, sort_keys=True) == json.dumps(
        {key: live_market[key] for key in ENVELOPE_KEYS}, sort_keys=True)
    sellers_same = json.dumps(sellers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in ENVELOPE_KEYS} for block in live_sellers],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    live_rows = len(live_market["rows"]) + sum(
        len(block["rows"]) for block in live_sellers)
    ok("AC-SRRB2", market_same and sellers_same and disc_same and bool(sellers),
       "market_same=%s sellers_same=%s disclaimer_same=%s sellers=%d rows=%d"
       % (market_same, sellers_same, disc_same, len(sellers), live_rows))

    # ---- AC-SRRB3: the face's identities hold on these envelopes.
    problems = envelope_problems(market, "market") if market else ["no market"]
    if market:
        if market.get("scope") != "market" or market.get("dev_account") is not None:
            problems.append("market scope")
        for key in ("market_refund_rate", "market_refund_share"):
            if market.get(key) is not None:
                problems.append("market %s" % key)
    for block in sellers:
        name = str(block["dev_account"])
        problems.extend(envelope_problems(block, name))
        if block["scope"] != "seller":
            problems.append("%s scope" % name)
        if not close(block["market_refund_rate"], live_market["refund_rate"]):
            problems.append("%s market rate" % name)
        want_share = (round(float(block["refunded_total"])
                            / float(live_market["refunded_total"]), 4)
                      if int(live_market["refunded_total"]) else None)
        if not close(block["market_refund_share"], want_share):
            problems.append("%s market share" % name)
    ok("AC-SRRB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-SRRB4: honest page face, dashes, width bar, two probes.
    dash = labels.get("none", "-")
    sellers_marked = all(('data-seller="%s"' % block["dev_account"]) in page
                         for block in sellers)
    rows_marked = all(('data-reason="%s"' % (
        row["reason"] if row["reason"] is not None
        else labels.get("unlabeled", ""))) in page for row in all_rows)
    bars_ok = page.count("<div class=bar>") == len(all_rows)
    no_none = ">None<" not in page
    laws = [labels.get(key, "") for key in
            ("law_legs", "law_share", "law_avg", "law_rate", "law_count",
             "law_top", "law_hhi", "law_order", "law_scope", "law_bar",
             "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    zero_ok = unlabeled_ok = False
    try:
        driver = load_driver()
        zero_html = driver.build_html(zero_envelope(), [], labels,
                                      "2026-01-01 00:00:00Z",
                                      "probe disclaimer")
        zero_ok = (zero_html.count("<div class=bar>") == 0
                   and ">None<" not in zero_html
                   and dash in zero_html
                   and labels.get("top_none", "") in zero_html)
        mixed_html = driver.build_html(mixed_envelope(), [], labels,
                                       "2026-01-01 00:00:00Z",
                                       "probe disclaimer")
        unlabeled_label = labels.get("unlabeled", "")
        unlabeled_ok = (unlabeled_label in mixed_html
                        and ">None<" not in mixed_html
                        and mixed_html.index(unlabeled_label)
                        > mixed_html.index("aaa"))
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-SRRB4", sellers_marked and rows_marked and bars_ok and no_none
       and laws_ok and zero_ok and unlabeled_ok,
       "sellers=%s rows=%s bars=%s laws=%s zero_probe=%s unlabeled_probe=%s "
       "stand_in_none=%s"
       % (sellers_marked, rows_marked, bars_ok, laws_ok, zero_ok,
          unlabeled_ok, not no_none))

    # ---- AC-SRRB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-SRRB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-SRRB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-SRR" in read(FACE_SUITE)
    ok("AC-SRRB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
