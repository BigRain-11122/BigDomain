"""export_R2479 - refresh docs/status-export.json for the R2479 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2479 TECH window: the battery's per-suite timeout is now ONE "
           "declared number the headroom instrument READS from the runner "
           "source (no second 300 literal can drift from the run again), with "
           "a declared per-suite override so a slow suite gets room without "
           "widening the global guard; the cap moved 300 -> 600s and the three "
           "ledger suites that had no load headroom left now read COMFORTABLE "
           "while a genuine outlier still reads BAND")

base.LATEST = ("src/os/runner_suite_timeout_cap.py (new owner of the reading, "
               "CLI --check exits 0 CAP-DECLARED / 2 UNDECLARED / 3 / 5) + "
               "src/sandbox/reconcile_all.py (SUITE_TIMEOUT_S = 600, "
               "SUITE_TIMEOUT_OVERRIDES, suite_timeout(), explicit run_cmd "
               "timeout, summary states 'suite cap=600s') + "
               "src/os/runner_suite_timeout_headroom.py (default cap now read "
               "from the runner, not a literal) + "
               "src/os/test_runner_suite_timeout_cap.py (AC-RSC1..AC-RSC6) + "
               "qa/runner-timeout-cap-R2479.log (SUITE PASS 6/6 twice, "
               "identical bodies, 1169B utf-8 LF) + docs/sandbox-suite-matrix.md "
               "(54575B, green=566/567 honest)")

base.NEXT = ("2026-11-06 the next window owes the reconcile battery FIRST "
             "(reconcile-battery-R2479, pre-registered 567 suites / 4378 "
             "criteria) on the committed tree before any product byte, and "
             "that battery should show the three ledger suites COMFORTABLE at "
             "the 600s cap; after that the standing candidate remains letting "
             "the hub page START a face from the browser, and every P-47 item "
             "beyond the shipped sandbox faces still waits on CEO physical "
             "items")

base.RESULT = (
    "2026-11-06 R2479 TECH window delivered: claims the runner-suite-timeout-"
    "cap seed row whose AC-RSC1..AC-RSC6 were pinned at R2478 BEFORE any code. "
    "The defect it answers is real and repeated three times - R2393 leg 3, "
    "R2466 leg 2 and R2478 leg 1 each lost a suite to a flat 300s per-suite "
    "cap while the SAME three ledger suites measured 232.2s / 268.1s / 300.1s, "
    "and the headroom instrument carried its own second 300.0 literal, so the "
    "reading and the run could disagree. SHIPPED: reconcile_all.py now carries "
    "ONE named SUITE_TIMEOUT_S = 600, a SUITE_TIMEOUT_OVERRIDES mapping, a "
    "suite_timeout(label) helper, an explicit run_cmd timeout, a marker that "
    "names the cap that actually ran, and a summary line stating 'suite "
    "cap=600s overrides=N'; src/os/runner_suite_timeout_cap.py is the single "
    "owner of the reading (read_cap returns cap plus declared-or-fallback plus "
    "occurrence count from the SOURCE, read_overrides parses rather than "
    "executes, CLI --check exits 0/2/3/5); and the headroom instrument now "
    "takes its default cap from that module instead of a literal, using the "
    "dunder import form because AC-RTH6 pins its import set. AC-RSC1..AC-RSC6 "
    "read SUITE PASS 6/6 twice with identical bodies through the shipped "
    "capture callable at qa/runner-timeout-cap-R2479.log (1169B, utf-8 LF, "
    "crlf=0, adjacent headroom suite green), including the negative controls: "
    "a fixture with no declaration reads the 300.0 fallback with occurrences=0, "
    "a 5s fixture under a declared 1s override returns 124 while its undeclared "
    "neighbour exits 0, and a synthetic 95s-under-100s outlier still reads "
    "BAND-HIT. One process defect was caught and re-taken in the same window: "
    "the first capture piped through PowerShell Tee-Object and wrote UTF-16, "
    "exactly the dialect defect R2478 had just repaired, so both files were "
    "deleted before any commit and the evidence was re-taken through the "
    "shipped writer. Registry 566 -> 567 suites and 4372 -> 4378 criteria, "
    "matrix restamped to 54575B with --check byte-identical and its green line "
    "honestly reading 566/567 because this window ran no battery; "
    "runner-suite-timeout-cap closed 124306B -> 124310B and "
    "reconcile-battery-R2479 opened with the pre-registered target. Honest: "
    "this is a TECH window, not a CEO-openable product face; the 600s cap is a "
    "judgement with 300s of headroom over the slowest measured suite rather "
    "than a proof against any load; the overrides map ships empty and the "
    "mechanism is proved through the seam; the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items; tasks.md was not touched."
)

base.OUTS = (
    "src/sandbox/reconcile_all.py + src/os/runner_suite_timeout_cap.py + "
    "src/os/test_runner_suite_timeout_cap.py + "
    "src/os/runner_suite_timeout_headroom.py + "
    "qa/runner-timeout-cap-R2479.log + docs/sandbox-suite-matrix.md + "
    "state/debt.md + state/queue/tech.md + src/os/state.json + "
    "src/os/state_append_R2479.py + src/os/export_R2479.py + "
    "docs/status-export.json + heartbeat.txt"
)

if __name__ == "__main__":
    print(base.main())