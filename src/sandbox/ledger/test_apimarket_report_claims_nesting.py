"""Acceptance suite for the R2613 birth-site repair of the apimarket claim
block suite (canon: the R2613 tech-queue row AC-AMCF1..AC-AMCF6, pinned
there BEFORE this file existed - honesty law).

The red this repairs, measured at R2612 and re-measured at R2613: the owed
battery's ONLY failing row was ledger-apimarket-reportclaims
exit=124 pass-lines=0 criteria=8 600.2s - the runner's per-suite cap, not
an assertion. Its AC-AMCLM8 check_regression nested three child suites in
sequence: test_apimarket_report.py (measured 11.1s), test_apimarket_report_json.py
(measured 16.4s) and test_apimarket_report_refundregister.py (still running
past 60s on the same loaded tree). All three are already battery rows of
their own, so the nesting re-ran work the battery already pays for.

Criteria:
  AC-AMCF1 The nesting is bounded: the repaired suite never hands the
    heavy refund-register file to a child (asserted against its own
    source, read at call time) while both cheap children are still there.
  AC-AMCF2 The heavy coverage MOVED, it was not dropped: the shipped
    runner registry carries exactly one ledger-apimarket-refundregister
    row pointing at that file, and the file is on disk.
  AC-AMCF3 The cheap children are still the decision input: a doctored
    non-zero return code flips the verdict to FAIL naming child-rc, and
    the repaired source still calls subprocess.run inside the check.
  AC-AMCF4 This suite's own wiring is unchanged: exactly one
    ledger-apimarket-reportclaims row pointing at the repaired file with
    eight criteria.
  AC-AMCF5 Fail-closed: an unreadable registry and a missing heavy row
    each make the verdict FAIL naming the reason, and a doctored registry
    source with the heavy row removed really reads no heavy row.
  AC-AMCF6 The declared bound is honest and inside the cap: the budget is
    strictly below the runner's 600s cap, this suite measures its own wall
    time and lands well inside its own bound.

Usage: python test_apimarket_report_claims_nesting.py
"""

import io
import os
import sys
import tempfile
import time

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.dirname(BASE)
for _d in (BASE, os.path.join(SANDBOX, "lobby")):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import test_apimarket_report_claims as M      # noqa: E402

REPAIRED = os.path.join(BASE, "test_apimarket_report_claims.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok), evidence))
    print("%s %s %s" % ("PASS" if ok else "FAIL", ac, evidence))


def check_bounded():
    spawned = M.spawned_children()
    ok = (M.HEAVY_FILE not in spawned
          and set(M.CHEAP_CHILDREN) <= spawned)
    record("AC-AMCF1", ok,
           "spawned=%s heavy_absent=%s cheap_present=%s"
           % (",".join(sorted(spawned)),
              M.HEAVY_FILE not in spawned,
              set(M.CHEAP_CHILDREN) <= spawned))


def check_coverage_moved():
    rows = M.registered_rows(REGISTRY)
    heavy = [row for row in rows if row[0] == M.HEAVY_LABEL]
    on_disk = os.path.isfile(os.path.join(BASE, M.HEAVY_FILE))
    ok = (len(heavy) == 1
          and os.path.basename(heavy[0][1]) == M.HEAVY_FILE
          and on_disk)
    record("AC-AMCF2", ok,
           "heavy_rows=%d path=%s on_disk=%s"
           % (len(heavy), heavy[0][1] if heavy else "-", on_disk))


def check_children_still_decide():
    base = dict(bounded=True, covered=True, wired=True, elapsed=3.0)
    good, why_good = M.regression_verdict(codes=[0, 0], **base)
    bad, why_bad = M.regression_verdict(codes=[0, 1], **base)
    src = io.open(REPAIRED, "r", encoding="utf-8").read()
    runs = "subprocess.run(" in src and "proc.returncode" in src
    ok = (good and why_good == "ok" and (not bad)
          and "child-rc" in why_bad and runs)
    record("AC-AMCF3", ok,
           "good=%s bad=%s reason=%s source_runs=%s"
           % (good, bad, why_bad, runs))


def check_own_row():
    rows = M.registered_rows(REGISTRY)
    mine = [row for row in rows
            if row[0] == "ledger-apimarket-reportclaims"]
    ok = (len(mine) == 1
          and os.path.basename(mine[0][1])
          == os.path.basename(REPAIRED)
          and mine[0][2] == "8")
    record("AC-AMCF4", ok,
           "rows=%d path=%s criteria=%s"
           % (len(mine), mine[0][1] if mine else "-",
              mine[0][2] if mine else "-"))


def check_fail_closed():
    base = dict(bounded=True, codes=[0, 0], wired=True, elapsed=3.0)
    broke, why_broke = M.regression_verdict(
        covered=False, registry_error="OSError: missing", **base)
    missing, why_missing = M.regression_verdict(
        covered=False, **base)
    text = io.open(REGISTRY, "r", encoding="utf-8").read()
    start = text.index("SUITES = [")
    doctored = text[:start] + "SUITES = []\n"
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".py", delete=False, encoding="utf-8")
    try:
        handle.write(doctored)
        handle.close()
        rows = M.registered_rows(handle.name)
    finally:
        os.unlink(handle.name)
    no_heavy = not [row for row in rows if row[0] == M.HEAVY_LABEL]
    ok = ((not broke) and "registry-" in why_broke
          and (not missing) and "heavy-row-missing" in why_missing
          and no_heavy)
    record("AC-AMCF5", ok,
           "registry_error=%s missing_row=%s doctored_reads_empty=%s"
           % (why_broke, why_missing, no_heavy))


def check_budget(started):
    elapsed = time.time() - started
    inside_cap = 0 < M.NESTING_BUDGET_S < 600
    ok = inside_cap and elapsed < 60
    print("  elapsed=%.1fs budget=%ds cap=600s"
          % (elapsed, M.NESTING_BUDGET_S))
    # The measured wall time is printed above and never enters the
    # criterion line, so the two legs keep one digest.
    record("AC-AMCF6", ok,
           "budget=%ds cap=600s inside_cap=%s inside_own_bound=%s"
           % (M.NESTING_BUDGET_S, inside_cap, elapsed < 60))


def main():
    started = time.time()
    check_bounded()
    check_coverage_moved()
    check_children_still_decide()
    check_own_row()
    check_fail_closed()
    check_budget(started)
    failed = [ac for ac, ok, _ in RESULTS if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              len(RESULTS) - len(failed), len(RESULTS)))
    if failed:
        print("FAILED: %s" % ",".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())