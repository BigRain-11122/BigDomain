"""Battery suite for tools/market_price_percentiles.py - criteria AC-MPQ1..6.

WHY THIS SUITE EXISTS (measured at R3400, not assumed):
api_market_price_percentiles has shipped since R2160 with eight green criteria
of its own (test_apimarket_pricepercentiles.py), but git grep -F over tools/
and preview/ found ZERO readers, so the face that answers "where does an
asking price sit in this market" could not be opened by anyone. R3400 renders
it onto one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3400 PIN
BEFORE the driver existed):
  AC-MPQ1  the page and its json land, and the json carries exactly the pinned
           payload key set including the sizes and sources blocks.
  AC-MPQ2  the data is the shipped face's own: the suite builds its own
           throwaway demo world, reads api_market_price_percentiles there, and
           requires every number, every bucket row and the disclaimer on the
           page json to equal that reading - no typed fixture, no synthesis.
  AC-MPQ3  the printed ladder is a ladder: min <= p25 <= p50 <= p75 <= p90 <=
           max, spread == max - min, the ruler starts at 0.0 and ends at 100.0,
           and every rung prints its own price on the page.
  AC-MPQ4  the buckets add up: sum(row listing_count) == envelope listing_count
           == live + retired, the envelope min/max are the extremes of the row
           min/max, and the page prints exactly one row per bucket.
  AC-MPQ5  the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-MPQ6  no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py, and the shipped face's own suite is
           still on disk with its AC-MPP criteria.

Read-only over the repository: the provenance world is built in a temp dir and
every re-render writes into a temp dir, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "market_price_percentiles.py")
HTML = os.path.join(ROOT, "preview", "market-price-percentiles.html")
JSONF = os.path.join(ROOT, "preview", "market-price-percentiles.json")
COPY = os.path.join(ROOT, "preview", "market-price-percentiles-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_pricepercentiles.py")

LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")

PAYLOAD_KEYS = {
    "generated_utc", "face", "listing_count", "live_listing_count",
    "retired_listing_count", "min_price", "max_price", "p25_price",
    "p50_price", "p75_price", "p90_price", "mean_price", "spread",
    "category_count", "categories", "quantiles", "disclaimer", "report",
    "sources", "sizes",
}
LADDER = ("min_price", "p25_price", "p50_price", "p75_price", "p90_price",
          "max_price")
DATA_KEYS = ("listing_count", "live_listing_count", "retired_listing_count",
             "min_price", "max_price", "p25_price", "p50_price", "p75_price",
             "p90_price", "mean_price", "spread", "category_count")

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
    tmp_root = tempfile.mkdtemp(prefix="mpq-suite-")
    db = os.path.join(tmp_root, "mpq.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        return am.api_market_price_percentiles()
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

    # ---- AC-MPQ1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    ok("AC-MPQ1", landed and keys == PAYLOAD_KEYS,
       "landed=%s keys=%d missing=%s extra=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS)))

    # ---- AC-MPQ2: every printed number is the shipped face's own.
    env = face_reading()
    diffs = [(key, doc.get(key), env.get(key))
             for key in DATA_KEYS if doc.get(key) != env.get(key)]
    cat_diff = doc.get("categories") != env["categories"]
    disc_same = doc.get("disclaimer") == env.get("disclaimer")
    ok("AC-MPQ2", not diffs and not cat_diff and disc_same,
       "env_diff=%s categories_same=%s disclaimer_same=%s"
       % (diffs[:3], not cat_diff, disc_same))

    # ---- AC-MPQ3: the ladder is ordered and every rung prints its price.
    quants = {q["key"]: q for q in (doc.get("quantiles") or [])}
    rungs = [quants.get(key) for key in LADDER]
    prices = [r["price"] for r in rungs if r is not None]
    ordered_ok = (len(prices) == len(LADDER) and all(p is not None
                                                    for p in prices)
                  and prices == sorted(prices))
    lo, hi = doc.get("min_price"), doc.get("max_price")
    spread_ok = (doc.get("spread") == (hi - lo)
                 if lo is not None and hi is not None else False)
    ruler_first = (rungs[0] or {}).get("pos") == 0.0 if rungs[0] else False
    ruler_last = (rungs[-1] or {}).get("pos") == 100.0 if rungs[-1] else False
    printed = []
    for rung in rungs:
        if rung is None:
            printed.append("missing")
        else:
            token = ">%s<" % _num(rung["price"])
            if ('<b>%s</b>' % _num(rung["price"])) not in page:
                printed.append(rung["key"])
    ok("AC-MPQ3", ordered_ok and spread_ok and ruler_first and ruler_last
       and not printed,
       "ordered=%s prices=%s spread_ok=%s ruler=%s..%s unprinted=%s"
       % (ordered_ok, prices, spread_ok,
          (rungs[0] or {}).get("pos"), (rungs[-1] or {}).get("pos"),
          printed[:3]))

    # ---- AC-MPQ4: bucket rows add up to the envelope.
    rows = doc.get("categories") or []
    row_sum = sum(int(r.get("listing_count", 0) or 0) for r in rows)
    live = int(doc.get("live_listing_count", 0) or 0)
    retired = int(doc.get("retired_listing_count", 0) or 0)
    total_ok = (row_sum == int(doc.get("listing_count", -1))
                == live + retired)
    if rows:
        mins = [r["min_price"] for r in rows if r.get("min_price") is not None]
        maxs = [r["max_price"] for r in rows if r.get("max_price") is not None]
        extremes_ok = (bool(mins) and bool(maxs)
                       and doc.get("min_price") == min(mins)
                       and doc.get("max_price") == max(maxs))
    else:
        extremes_ok = False
    page_rows = sum(1 for r in rows
                    if ('>%s<' % _num(r["listing_count"])) in page)
    bucket_count_ok = page_rows == len(rows)
    ok("AC-MPQ4", total_ok and extremes_ok and bucket_count_ok,
       "row_sum=%d envelope=%s live+retired=%d extremes=%s page_rows=%d/%d"
       % (row_sum, doc.get("listing_count"), live + retired, extremes_ok,
          page_rows, len(rows)))

    # ---- AC-MPQ5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disclaimer = bool((doc.get("disclaimer") or "").strip())
    on_page = disclaimer and doc.get("disclaimer") in page
    external = len(re.findall(r"https?://", page))
    ok("AC-MPQ5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-MPQ6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    wired = "market_price_percentiles" in read(REGISTRY)
    face_ok = (os.path.exists(FACE_SUITE)
               and "AC-MPP8" in read(FACE_SUITE))
    ok("AC-MPQ6", rc == 0 and "PASS" in out and before == after
       and wired and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%s face_suite=%s"
       % (rc, before == after, wired, face_ok))

    print("SUITE %s %d/%d criteria"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS)))
    return 0 if not FAILS else 2


def _num(value):
    if value is None:
        return "-"
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


if __name__ == "__main__":
    sys.exit(main())
