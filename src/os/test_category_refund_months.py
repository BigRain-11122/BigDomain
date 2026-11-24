"""Battery suite for tools/category_refund_months.py - criteria AC-CRF1..6.

WHY THIS SUITE EXISTS (measured at R3402, not assumed):
api_category_refund_months shipped with its own AC-CRM criteria, but git grep -F
over tools/ and preview/ found ZERO readers, so the face that answers "is THIS
category's refund load abnormal THIS month" could not be opened by anyone.
R3402 renders it onto one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3402 PIN
BEFORE the driver existed):
  AC-CRF1  the page and its json land, and the json carries exactly the pinned
           payload key set including the sizes and sources blocks.
  AC-CRF2  the data is the shipped face's own: the suite builds its own
           throwaway demo world, reads api_category_refund_months there, and
           requires every envelope number, the whole category tree and the
           disclaimer on the page json to equal that reading - no typed
           fixture, no synthesized month.
  AC-CRF3  the shape adds up: each category's month rows sum to that category's
           own gross/refunded/refund_count, the categories sum to the envelope,
           net is gross minus refunded at every level, month_count is the size
           of the month union, and the row count is category_count.
  AC-CRF4  the month face is honest: months ascend inside each category, the
           uncategorized bucket sorts last, a zero-gross month is printed
           rather than dropped, its net carries the minus sign, and an
           undefined refund rate prints the no-value mark next to the page's own
           sentence saying such a month cannot win the highest-rate callout.
  AC-CRF5  the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-CRF6  no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py, the shipped face's own suite is still
           on disk with its AC-CRM criteria, and the AC-SQS / AC-MPQ / AC-MHP
           suites this family already shipped are still on disk.

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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "category_refund_months.py")
HTML = os.path.join(ROOT, "preview", "category-refund-months.html")
JSONF = os.path.join(ROOT, "preview", "category-refund-months.json")
COPY = os.path.join(ROOT, "preview", "category-refund-months-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_categoryrefundmonths.py")
SIBLING_SUITES = (
    os.path.join(ROOT, "src", "os", "test_seller_quality_scorecard.py"),
    os.path.join(ROOT, "src", "os", "test_market_price_percentiles.py"),
    os.path.join(ROOT, "src", "os", "test_market_hour_heatmap.py"),
)

LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "include_uncategorized", "category_count",
    "month_count", "trade_count", "gross", "refund_count", "refunded", "net",
    "refund_rate", "worst_refund_month", "worst_refund_rate",
    "top_refund_month", "categories", "disclaimer", "report", "sources",
    "sizes",
}
DATA_KEYS = ("include_uncategorized", "category_count", "month_count",
             "trade_count", "gross", "refund_count", "refunded", "net",
             "refund_rate", "worst_refund_month", "worst_refund_rate",
             "top_refund_month")

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
    """Read the shipped face over the suite's own throwaway demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    import apimarket  # noqa: F401  (imported for the face under proof)
    tmp_root = tempfile.mkdtemp(prefix="crf-suite-")
    db = os.path.join(tmp_root, "crf.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        return am.api_category_refund_months()
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}

    # ---- AC-CRF1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    report_ok = doc.get("report") == "preview/category-refund-months.html"
    ok("AC-CRF1", landed and keys == PAYLOAD_KEYS and report_ok,
       "landed=%s keys=%d missing=%s extra=%s report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), doc.get("report")))

    # ---- AC-CRF2: every printed number is the shipped face's own.
    env = face_reading()
    diffs = [(key, doc.get(key), env.get(key))
             for key in DATA_KEYS if doc.get(key) != env.get(key)]
    cats_same = doc.get("categories") == env["categories"]
    disc_same = doc.get("disclaimer") == env.get("disclaimer")
    ok("AC-CRF2", not diffs and cats_same and disc_same,
       "env_diff=%s categories_same=%s disclaimer_same=%s"
       % (diffs[:3], cats_same, disc_same))

    # ---- AC-CRF3: the shape adds up at every level.
    rows = doc.get("categories") or []
    per_row = []
    for row in rows:
        months = row.get("months") or []
        per_row.append((
            sum(int(m.get("gross", 0) or 0) for m in months)
            == int(row.get("gross", -1) or 0),
            sum(int(m.get("refunded", 0) or 0) for m in months)
            == int(row.get("refunded", -1) or 0),
            sum(int(m.get("refund_count", 0) or 0) for m in months)
            == int(row.get("refund_count", -1) or 0),
            sum(int(m.get("net", 0) or 0) for m in months)
            == int(row.get("net", -2) or 0),
            int(row.get("net", 0) or 0)
            == int(row.get("gross", 0) or 0) - int(row.get("refunded", 0) or 0),
            all(int(m.get("net", 0) or 0)
                == int(m.get("gross", 0) or 0) - int(m.get("refunded", 0) or 0)
                for m in months),
        ))
    rows_ok = all(all(flags) for flags in per_row) if per_row else True
    env_rows = (
        sum(int(r.get("gross", 0) or 0) for r in rows)
        == int(doc.get("gross", -1) or 0)
        and sum(int(r.get("refunded", 0) or 0) for r in rows)
        == int(doc.get("refunded", -1) or 0)
        and sum(int(r.get("refund_count", 0) or 0) for r in rows)
        == int(doc.get("refund_count", -1) or 0)
        and sum(int(r.get("trade_count", 0) or 0) for r in rows)
        == int(doc.get("trade_count", -1) or 0)
    )
    env_net = (int(doc.get("net", 0) or 0)
               == int(doc.get("gross", 0) or 0)
               - int(doc.get("refunded", 0) or 0))
    months = set()
    for row in rows:
        for month in row.get("months") or []:
            months.add(month.get("month"))
    count_ok = (len(rows) == int(doc.get("category_count", -1) or 0)
                and len(months) == int(doc.get("month_count", -2) or 0))
    ok("AC-CRF3", rows_ok and env_rows and env_net and count_ok,
       "per_row=%s envelope_sums=%s envelope_net=%s rows=%d/%s months=%d/%s"
       % (rows_ok, env_rows, env_net, len(rows), doc.get("category_count"),
          len(months), doc.get("month_count")))

    # ---- AC-CRF4: order, honest zero months, negative net, undefined rate.
    order_ok = True
    for row in rows:
        names = [m.get("month") for m in row.get("months") or []]
        if names != sorted(names):
            order_ok = False
    cats = [row.get("category") for row in rows]
    named = [c for c in cats if c is not None]
    cat_ok = named == sorted(named) and (
        None not in cats or cats[-1] is None)
    none_token = ">%s<" % str(labels.get("none", ""))
    zero_months = [m for row in rows for m in (row.get("months") or [])
                   if int(m.get("gross", 0) or 0) == 0]
    zero_printed = all(str(m.get("month")) in page for m in zero_months)
    neg_printed = all(("%d" % int(m.get("net"))) in page
                      for m in zero_months if int(m.get("net", 0) or 0) < 0)
    undefined = [m for m in zero_months if m.get("refund_rate") is None]
    mark_ok = (not undefined) or page.count(none_token) >= len(undefined)
    law_sentence = str(labels.get("law_undefined", ""))
    law_ok = bool(law_sentence) and law_sentence in page
    ok("AC-CRF4", order_ok and cat_ok and zero_printed and neg_printed
       and mark_ok and law_ok,
       "order=%s cats=%s zero_printed=%s(live=%d) neg_printed=%s "
       "undef_marks=%d/%d law=%s"
       % (order_ok, cat_ok, zero_printed, len(zero_months), neg_printed,
          page.count(none_token), len(undefined), law_ok))

    # ---- AC-CRF5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disclaimer = bool((doc.get("disclaimer") or "").strip())
    on_page = disclaimer and doc.get("disclaimer") in page
    external = len(re.findall(r"https?://", page))
    ok("AC-CRF5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-CRF6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    wired = "os-category-refund-months" in read(REGISTRY)
    face_ok = (os.path.exists(FACE_SUITE)
               and "AC-CRM8" in read(FACE_SUITE))
    siblings = all(os.path.exists(p) for p in SIBLING_SUITES)
    ok("AC-CRF6", rc == 0 and "PASS" in out and before == after
       and wired and face_ok and siblings and len(CHECKS) + 1 == DECLARED,
       "check_rc=%d wrote_nothing=%s wired=%s face_suite=%s siblings=%s "
       "criteria=%d/%d"
       % (rc, before == after, wired, face_ok, siblings,
          len(CHECKS) + 1, DECLARED))

    print("SUITE %s %d/%d criteria"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS)))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
