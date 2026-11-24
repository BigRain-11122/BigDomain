"""Battery suite for tools/seller_concentration_board.py - criteria AC-BCB1..6.

WHY THIS SUITE EXISTS (measured at R3409, not assumed):
api_seller_concentration has shipped with eight green criteria of its own
(test_apimarket_concentration.py, AC-SBC) but the R3409 reader re-measure over
the five faces the R3408 board named found ZERO hits under tools/ and
preview/ for every one of them. The seller question this face answers - how
many residents is my net revenue hanging on, how much rides on the single
biggest one - could not be opened by anyone. R3409 renders it onto one page;
this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3409 PIN
BEFORE the driver existed):
  AC-BCB1 the page and its json land, the json carries exactly the pinned
           payload key set including the sizes and sources blocks, and every
           buyer row carries the shipped ten-key row set.
  AC-BCB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, reads api_seller_concentration() there, and
           requires the page json's envelope fields and the whole buyer ladder
           to equal that reading item for item plus the disclaimer verbatim -
           no typed fixture, no synthesized buyers.
  AC-BCB3 the face's identities hold: row sums reproduce the envelope totals,
           a fully refunded buyer keeps a row with zero weight, per-row net and
           net counts re-derive, share and cumulative share re-derive from the
           net total, the Herfindahl index re-derives from the exact shares,
           the Pareto count is the smallest k reaching 80 percent on integers,
           top1 and top3 are the ladder head and the first three shares, and
           the ladder is sorted with contiguous ranks.
  AC-BCB4 the page reads honestly: one row per buyer, the zero-weight buyer is
           printed rather than dropped, an undefined share prints the no-value
           mark rather than a fake zero, the HHI scale carries a marker and the
           weight-not-count rule is on the page, and no bare None reaches it.
  AC-BCB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-BCB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-SBC arms.

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
TOOL = os.path.join(ROOT, "tools", "seller_concentration_board.py")
HTML = os.path.join(ROOT, "preview", "seller-concentration.html")
JSONF = os.path.join(ROOT, "preview", "seller-concentration.json")
COPY = os.path.join(ROOT, "preview", "seller-concentration-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_concentration.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-seller-concentration-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "dev_account", "scope", "purchase_count",
    "refund_count", "buyer_count", "refunded_buyers", "gross_revenue",
    "refunded_tokens", "net_revenue", "top1_share", "top3_share", "herfindahl",
    "pareto_buyer_count", "market_herfindahl", "buyers", "disclaimer",
    "report", "sources", "sizes",
}
ROW_KEYS = {
    "buyer_id", "purchase_count", "refund_count", "net_purchase_count",
    "gross_revenue", "refunded_tokens", "net_revenue", "share",
    "cumulative_share", "rank",
}
COMPARE = (
    "dev_account", "scope", "purchase_count", "refund_count", "buyer_count",
    "refunded_buyers", "gross_revenue", "refunded_tokens", "net_revenue",
    "top1_share", "top3_share", "herfindahl", "pareto_buyer_count",
    "market_herfindahl", "buyers",
)

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
    """One envelope read from the shipped face over a private demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="bcb-suite-")
    db = os.path.join(tmp_root, "bcb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        return dict(am.api_seller_concentration())
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def identity_problems(doc):
    problems = []
    rows = doc["buyers"]
    if int(doc["buyer_count"]) != len(rows):
        problems.append("buyer_count")
    for key in ("purchase_count", "refund_count", "gross_revenue",
                "refunded_tokens", "net_revenue"):
        if sum(int(r[key]) for r in rows) != int(doc[key]):
            problems.append("%s_sum" % key)
    refunded_buyers = sum(1 for r in rows if int(r["refund_count"]) > 0)
    if refunded_buyers != int(doc["refunded_buyers"]):
        problems.append("refunded_buyers")
    total = int(doc["net_revenue"])
    running = 0
    pareto = None
    squares = []
    for index, row in enumerate(rows, 1):
        if int(row["rank"]) != index:
            problems.append("rank_%d" % index)
        if int(row["net_revenue"]) != (int(row["gross_revenue"])
                                       - int(row["refunded_tokens"])):
            problems.append("%s net" % row["buyer_id"])
        if int(row["net_purchase_count"]) != (int(row["purchase_count"])
                                              - int(row["refund_count"])):
            problems.append("%s net_count" % row["buyer_id"])
        running += int(row["net_revenue"])
        if pareto is None and total > 0 and running * 5 >= total * 4:
            pareto = index
        if total > 0:
            exact = float(int(row["net_revenue"])) / total
            if row["share"] != round(exact, 6):
                problems.append("%s share" % row["buyer_id"])
            if row["cumulative_share"] != round(float(running) / total, 6):
                problems.append("%s cum" % row["buyer_id"])
            squares.append(exact * exact)
        elif row["share"] is not None or row["cumulative_share"] is not None:
            problems.append("%s share_on_empty" % row["buyer_id"])
    want_hhi = round(sum(squares) * 10000, 2) if total > 0 else None
    if doc["herfindahl"] != want_hhi:
        problems.append("herfindahl")
    if doc["pareto_buyer_count"] != pareto:
        problems.append("pareto")
    want_top1 = rows[0]["share"] if (rows and total > 0) else None
    if doc["top1_share"] != want_top1:
        problems.append("top1_share")
    want_top3 = (round(sum(r["share"] for r in rows[:3]), 6)
                 if (rows and total > 0) else None)
    if doc["top3_share"] != want_top3:
        problems.append("top3_share")
    ordered = sorted(rows, key=lambda r: (-int(r["net_revenue"]),
                                          str(r["buyer_id"])))
    if [r["buyer_id"] for r in ordered] != [r["buyer_id"] for r in rows]:
        problems.append("ladder_order")
    if rows and total > 0 and rows[0]["rank"] == 1:
        if rows[0]["share"] != max(r["share"] for r in rows):
            problems.append("head_not_largest")
    return problems


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    rows = doc.get("buyers") or []

    # ---- AC-BCB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    row_keys_ok = all(set(row.keys()) == ROW_KEYS for row in rows)
    ok("AC-BCB1", landed and keys == PAYLOAD_KEYS and row_keys_ok
       and int(doc.get("buyer_count", -1)) == len(rows),
       "landed=%s keys=%d missing=%s extra=%s row_keys=%s rows=%d"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), row_keys_ok, len(rows)))

    # ---- AC-BCB2: every printed number is the shipped face's own.
    live = face_reading()
    diffs = [key for key in COMPARE
             if json.dumps(doc.get(key), sort_keys=True)
             != json.dumps(live.get(key), sort_keys=True)]
    disc_same = doc.get("disclaimer") == live.get("disclaimer")
    ok("AC-BCB2", not diffs and disc_same and bool(rows),
       "diffs=%s disclaimer_same=%s rows=%d"
       % (diffs[:4], disc_same, len(rows)))

    # ---- AC-BCB3: the face's identities hold on this envelope.
    problems = identity_problems(doc) if rows else ["no rows"]
    ok("AC-BCB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-BCB4: honest page face, addressable rows, no bare None.
    none = labels.get("none", "-")
    mark = ">%s<" % none
    zero_weight = [row for row in rows if float(row["net_revenue"]) == 0.0]
    undefined = [row for row in rows
                 if row["share"] is None or row["cumulative_share"] is None]
    page_rows = page.count('<tr class="buyer">')
    stand_in = ">None<" in page
    zero_kept = all(("%s</td>" % row["buyer_id"]) in page for row in rows)
    head_buyer = rows[0]["buyer_id"] if rows else ""
    scale_ok = 'class="scale"' in page
    mark_ok = 'class="mark"' in page
    named_ok = labels.get("named_pareto", "") in page
    weight_rule = labels.get("law7", "") in page
    ok("AC-BCB4", page_rows == len(rows) and (not undefined or mark in page)
       and not stand_in and zero_kept and bool(head_buyer) and scale_ok
       and mark_ok and named_ok and weight_rule,
       "rows=%d/%d mark=%s stand_in_none=%s zero_kept=%s scale=%s mark=%s "
       "named=%s weight_rule=%s zero_rows=%d"
       % (page_rows, len(rows), mark in page, stand_in, zero_kept, scale_ok,
          mark_ok, named_ok, weight_rule, len(zero_weight)))

    # ---- AC-BCB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-BCB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-BCB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-SBC" in read(FACE_SUITE)
    ok("AC-BCB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
