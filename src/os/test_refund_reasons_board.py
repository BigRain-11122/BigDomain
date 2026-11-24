"""Battery suite for tools/refund_reasons_board.py - criteria AC-RRB1..6.

WHY THIS SUITE EXISTS (measured at R3407, not assumed):
api_refund_reasons has shipped with eight green criteria of its own
(test_apimarket_refundreasons.py, AC-RFR) but the R3407 reader census over every
api_* face found ZERO hits under tools/ and preview/, so the question a seller
asks after a refund - is this refund load a quality problem, a description
mismatch or noise - could not be opened by anyone. R3407 renders it onto one
page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3407 PIN
BEFORE the driver existed):
  AC-RRB1 the page and its json land, the json carries exactly the pinned
           payload key set including the sizes and sources blocks, and every
           reason row carries the shipped seven-key row set.
  AC-RRB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, reads api_refund_reasons() there, and requires
           the page json's twelve envelope fields and the whole by_reason table
           to equal that reading item for item plus the disclaimer verbatim -
           no typed fixture, no synthesized distribution.
  AC-RRB3 the face's identities hold: buckets sum to the refund count and to
           labeled plus unlabeled, row money sums to the refunded total and the
           two splits sum to it as well, per-row share and average re-derive
           from the counts, the refund rate and the average re-derive with None
           on an honest empty, the named reason is a labeled bucket whose count
           and labeled-only share match, and an unlabeled bucket sorts last.
  AC-RRB4 the page reads honestly: one table row per bucket, the unlabeled
           bucket prints its named label rather than a blank, an undefined
           share or average prints the no-value mark rather than a fake zero,
           the named reason rides once in its own section, and no bare None
           reaches the page.
  AC-RRB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-RRB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-RFR arms.

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
TOOL = os.path.join(ROOT, "tools", "refund_reasons_board.py")
HTML = os.path.join(ROOT, "preview", "refund-reasons.html")
JSONF = os.path.join(ROOT, "preview", "refund-reasons.json")
COPY = os.path.join(ROOT, "preview", "refund-reasons-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_refundreasons.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-refund-reasons-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "purchase_count", "refund_count", "refund_rate",
    "labeled_count", "unlabeled_count", "reason_count", "refunded_total",
    "avg_refunded", "top_reason", "top_reason_count", "top_reason_share",
    "by_reason", "disclaimer", "report", "sources", "sizes",
}
ROW_KEYS = {
    "reason", "refund_count", "refunded", "dev_share", "platform_share",
    "share", "avg_amount",
}
COMPARE = (
    "purchase_count", "refund_count", "refund_rate", "labeled_count",
    "unlabeled_count", "reason_count", "refunded_total", "avg_refunded",
    "top_reason", "top_reason_count", "top_reason_share", "by_reason",
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
    tmp_root = tempfile.mkdtemp(prefix="rrb-suite-")
    db = os.path.join(tmp_root, "rrb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        return dict(am.api_refund_reasons())
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def identity_problems(doc):
    problems = []
    rows = doc["by_reason"]
    count = int(doc["refund_count"])
    labeled = int(doc["labeled_count"])
    unlabeled = int(doc["unlabeled_count"])
    if int(doc["reason_count"]) != len(rows):
        problems.append("reason_count")
    if sum(int(r["refund_count"]) for r in rows) != count:
        problems.append("count_sum")
    if labeled + unlabeled != count:
        problems.append("labeled_plus_unlabeled")
    if sum(int(r["refunded"]) for r in rows) != int(doc["refunded_total"]):
        problems.append("refunded_sum")
    splits = sum(int(r["dev_share"]) + int(r["platform_share"])
                 for r in rows)
    if splits != int(doc["refunded_total"]):
        problems.append("split_sum")
    for row in rows:
        name = row["reason"]
        n = int(row["refund_count"])
        want_share = (round(float(n) / count, 4) if count else None)
        if row["share"] != want_share:
            problems.append("%s share" % name)
        want_avg = (round(float(row["refunded"]) / n, 2) if n else None)
        if row["avg_amount"] != want_avg:
            problems.append("%s avg" % name)
        if int(row["dev_share"]) + int(row["platform_share"]) != int(
                row["refunded"]):
            problems.append("%s split" % name)
    purchases = int(doc["purchase_count"])
    want_rate = (round(float(count) / purchases, 4) if purchases else None)
    if doc["refund_rate"] != want_rate:
        problems.append("refund_rate")
    want_avg = (round(float(doc["refunded_total"]) / count, 2)
                if count else None)
    if doc["avg_refunded"] != want_avg:
        problems.append("avg_refunded")
    named = [r for r in rows if r["reason"] is not None]
    if named:
        best = sorted(named, key=lambda c: (-int(c["refund_count"]),
                                            -int(c["refunded"]),
                                            c["reason"]))[0]
        if doc["top_reason"] != best["reason"]:
            problems.append("top_reason")
        if doc["top_reason_count"] != best["refund_count"]:
            problems.append("top_reason_count")
        want_share = (round(float(best["refund_count"]) / labeled, 4)
                      if labeled else None)
        if doc["top_reason_share"] != want_share:
            problems.append("top_reason_share")
    elif (doc["top_reason"] is not None
          or doc["top_reason_count"] is not None
          or doc["top_reason_share"] is not None):
        problems.append("top_reason_on_empty")
    blank = [i for i, r in enumerate(rows) if r["reason"] is None]
    if blank and blank != [len(rows) - 1]:
        problems.append("unlabeled_not_last")
    return problems


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    rows = doc.get("by_reason") or []

    # ---- AC-RRB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    row_keys_ok = all(set(row.keys()) == ROW_KEYS for row in rows)
    ok("AC-RRB1", landed and keys == PAYLOAD_KEYS and row_keys_ok
       and int(doc.get("reason_count", -1)) == len(rows),
       "landed=%s keys=%d missing=%s extra=%s row_keys=%s rows=%d"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), row_keys_ok, len(rows)))

    # ---- AC-RRB2: every printed number is the shipped face's own.
    live = face_reading()
    diffs = [key for key in COMPARE
             if json.dumps(doc.get(key), sort_keys=True)
             != json.dumps(live.get(key), sort_keys=True)]
    disc_same = doc.get("disclaimer") == live.get("disclaimer")
    ok("AC-RRB2", not diffs and disc_same and bool(rows),
       "diffs=%s disclaimer_same=%s rows=%d"
       % (diffs[:4], disc_same, len(rows)))

    # ---- AC-RRB3: the face's identities hold on this envelope.
    problems = identity_problems(doc) if rows else ["no rows"]
    ok("AC-RRB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-RRB4: honest page face, addressable rows, no bare None.
    none = labels.get("none", "-")
    mark = ">%s<" % none
    undefined = [row for row in rows
                 if row["share"] is None or row["avg_amount"] is None]
    page_rows = page.count('<tr class="reason">')
    stand_in = ">None<" in page
    unlabeled_label = labels.get("unlabeled", "")
    unlabeled_ok = (unlabeled_label in page
                    if int(doc.get("unlabeled_count") or 0) > 0 else True)
    blank_reason = bool(rows) and rows[0]["reason"] is not None
    top_heading = labels.get("sec_top", "") in page
    top_named = (str(doc.get("top_reason")) in page
                 if doc.get("top_reason") is not None
                 else labels.get("top_none", "") in page)
    ok("AC-RRB4", page_rows == len(rows) and (not undefined or mark in page)
       and not stand_in and unlabeled_ok and blank_reason and top_heading
       and top_named,
       "rows=%d/%d mark=%s stand_in_none=%s unlabeled_ok=%s top=%s/%s"
       % (page_rows, len(rows), mark in page, stand_in, unlabeled_ok,
          top_heading, top_named))

    # ---- AC-RRB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-RRB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-RRB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-RFR" in read(FACE_SUITE)
    ok("AC-RRB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
