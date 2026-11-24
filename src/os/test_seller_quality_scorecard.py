"""Battery suite for tools/seller_quality_scorecard.py - criteria AC-SQS1..6.

WHY THIS SUITE EXISTS (measured at R3401, not assumed):
api_seller_quality shipped with its own AC-AMQL criteria, but git grep -F over
tools/ and preview/ found ZERO readers, so the face that answers "what shape is
my reputation, which live shelf drags it down, and what share of ratings has a
reply" could not be opened by anyone. R3401 renders it onto one page; this suite
grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3401 PIN
BEFORE the driver existed):
  AC-SQS1  the page and its json land, and the json carries exactly the pinned
           payload key set including the sizes and sources blocks.
  AC-SQS2  the data is the shipped face's own: the suite builds its own
           throwaway demo world, reads api_seller_quality there, and requires
           every envelope number, every row and the disclaimer on the page json
           to equal that reading - no typed fixture, no synthesis.
  AC-SQS3  the shape adds up: the five envelope buckets sum to rating_count,
           each row's buckets sum to that row's rating_count, the row count is
           listing_count, the star-weighted average is rating_avg, and
           low_rated_count is the number of live rows with >=2 ratings and an
           average <= 2.5 (the face's own stated rule, recomputed).
  AC-SQS4  the row face is honest: rows are ordered by listing_id, every row
           prints its live/retired state, and the weakest-live callout is the
           unique lowest-rated live shelf with ratings - a tie or an all-zero
           field prints the no-name sentence instead of picking one.
  AC-SQS5  the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-SQS6  no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py, the shipped face's own suite is still
           on disk with its AC-AMQL criteria, and the AC-MPQ / AC-MHP suites
           this family already shipped are still on disk.

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
TOOL = os.path.join(ROOT, "tools", "seller_quality_scorecard.py")
HTML = os.path.join(ROOT, "preview", "seller-quality-scorecard.html")
JSONF = os.path.join(ROOT, "preview", "seller-quality-scorecard.json")
COPY = os.path.join(ROOT, "preview", "seller-quality-scorecard-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_sellerquality.py")
SIBLING_SUITES = (
    os.path.join(ROOT, "src", "os", "test_market_price_percentiles.py"),
    os.path.join(ROOT, "src", "os", "test_market_hour_heatmap.py"),
)

LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "seller_count", "listing_count", "rating_count",
    "reply_count", "unanswered_count", "reply_coverage", "rating_avg",
    "star_distribution", "low_rated_count", "rows", "weakest", "disclaimer",
    "report", "sources", "sizes",
}
DATA_KEYS = ("seller_count", "listing_count", "rating_count", "reply_count",
             "unanswered_count", "reply_coverage", "rating_avg",
             "star_distribution", "low_rated_count")
STARS = ("1", "2", "3", "4", "5")

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
    tmp_root = tempfile.mkdtemp(prefix="sqs-suite-")
    db = os.path.join(tmp_root, "sqs.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        return am.api_seller_quality()
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def lowest_live(env):
    """Independent recomputation of the page-side callout."""
    rows = [r for r in env["rows"]
            if not r["retired"] and int(r["rating_count"]) > 0]
    if not rows:
        return None
    best = min(float(r["rating_avg"]) for r in rows)
    tied = [r for r in rows if float(r["rating_avg"]) == best]
    return None if len(tied) != 1 else int(tied[0]["listing_id"])


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}

    # ---- AC-SQS1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    report_ok = doc.get("report") == "preview/seller-quality-scorecard.html"
    ok("AC-SQS1", landed and keys == PAYLOAD_KEYS and report_ok,
       "landed=%s keys=%d missing=%s extra=%s report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), doc.get("report")))

    # ---- AC-SQS2: every printed number is the shipped face's own.
    env = face_reading()
    diffs = [(key, doc.get(key), env.get(key))
             for key in DATA_KEYS if doc.get(key) != env.get(key)]
    rows_same = doc.get("rows") == env["rows"]
    disc_same = doc.get("disclaimer") == env.get("disclaimer")
    ok("AC-SQS2", not diffs and rows_same and disc_same,
       "env_diff=%s rows_same=%s disclaimer_same=%s"
       % (diffs[:3], rows_same, disc_same))

    # ---- AC-SQS3: the shape adds up, and low_rated_count follows its own rule.
    dist = doc.get("star_distribution") or {}
    bucket_sum = sum(int(dist.get(k, 0) or 0) for k in STARS)
    rows = doc.get("rows") or []
    row_sums = [sum(int((r.get("star_distribution") or {}).get(k, 0) or 0)
                    for k in STARS) for r in rows]
    per_row_ok = all(s == int(r.get("rating_count", -1) or 0)
                     for s, r in zip(row_sums, rows))
    count_ok = (len(rows) == int(doc.get("listing_count", -1) or 0)
                == int(env.get("listing_count", -2) or 0))
    total = int(doc.get("rating_count", 0) or 0)
    star_sum = sum(int(k) * int(dist.get(k, 0) or 0) for k in STARS)
    avg_ok = (abs((float(star_sum) / total if total else 0.0)
                  - float(doc.get("rating_avg") or 0.0)) < 1e-9)
    recomputed_low = sum(
        1 for r in rows
        if not r["retired"] and int(r["rating_count"]) >= 2
        and float(r["rating_avg"]) <= 2.5)
    low_ok = recomputed_low == int(doc.get("low_rated_count", -1))
    ok("AC-SQS3", bucket_sum == total and per_row_ok and count_ok and avg_ok
       and low_ok,
       "buckets=%d rating_count=%d per_row=%s rows=%d/%s avg=%s low=%d/%s"
       % (bucket_sum, total, per_row_ok, len(rows), doc.get("listing_count"),
          avg_ok, recomputed_low, doc.get("low_rated_count")))

    # ---- AC-SQS4: order, state labels, and the weakest-live callout.
    ids = [int(r.get("listing_id", -1)) for r in rows]
    order_ok = ids == sorted(ids)
    live = [r for r in rows if not r["retired"]]
    retired = [r for r in rows if r["retired"]]
    live_word = ">%s<" % str(labels.get("state_live", ""))
    retired_word = ">%s<" % str(labels.get("state_retired", ""))
    # Counted inside table cells only: the standing section titles and KPI
    # labels also carry "在售", so a bare substring count would grade the
    # headings instead of the rows.
    state_ok = (len(live_word) > 2 and len(retired_word) > 2
                and page.count(live_word) == len(live)
                and page.count(retired_word) == len(retired))
    expect_weak = lowest_live(env)
    got = doc.get("weakest")
    weak_ok = (expect_weak is None and got is None) or (
        got is not None and int(got.get("listing_id", -1)) == expect_weak)
    named = expect_weak is not None
    weak_on_page = (named and got is not None and str(got.get("title")) in page) \
        or ((not named) and str(labels.get("weak_none", "")) in page)
    ok("AC-SQS4", order_ok and state_ok and weak_ok and weak_on_page,
       "order=%s ids=%s states=%s(live=%d retired=%d) weak=%s expect=%s named=%s"
       % (order_ok, ids, state_ok, len(live), len(retired),
          (got or {}).get("listing_id"), expect_weak, weak_on_page))

    # ---- AC-SQS5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disclaimer = bool((doc.get("disclaimer") or "").strip())
    on_page = disclaimer and doc.get("disclaimer") in page
    external = len(re.findall(r"https?://", page))
    ok("AC-SQS5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-SQS6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    wired = "os-seller-quality-scorecard" in read(REGISTRY)
    face_ok = (os.path.exists(FACE_SUITE)
               and "AC-AMQL8" in read(FACE_SUITE))
    siblings = all(os.path.exists(p) and re.search(r"AC-(MPQ|MHP)6", read(p))
                   for p in SIBLING_SUITES)
    ok("AC-SQS6", rc == 0 and "PASS" in out and before == after
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
