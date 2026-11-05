"""export_R2483 - refresh docs/status-export.json for the R2483 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2483 verification window: the two batteries R2481 and R2482 owed are "
           "now run and green on a committed tree - 569/569 suites and exactly "
           "4390 criteria - and the battery earned its keep by catching four "
           "R2482 evidence files written in PowerShell UTF-16, which were "
           "re-captured through the shipped utf-8 writer")

base.LATEST = ("qa/reconcile-all-R2483-retry.log (864674B, utf-8 LF, closing line "
               "'RUNNER PASS (569/569 suites green, reconcile controls 7/7, "
               "1652.7s)' with an independent recount of exactly 4390 criteria) + "
               "qa/panel-lobby-R2483.log (1532B, identical legs, digest "
               "10C09149A5755E9A) + qa/start-all-R2483.log (464B) + "
               "docs/sandbox-suite-matrix.md (54691B, green=569/569, --check "
               "byte-identical) at 2026-11-06 R2483")

base.NEXT = ("2026-11-07 the battery debt is clear and the gate now names "
             "product-face-R2456 (prefix AC-PFKC1) as CLAIM-FIRST, so the next "
             "window owes a BUSINESS face rather than another battery; the "
             "strongest candidate remains wiring the control panel into the hub "
             "payload so the one entry page leads to it, and every P-47 item "
             "beyond the shipped sandbox faces still waits on CEO physical items "
             "(merchant id, mini-program appid/secret)")

base.RESULT = (
    "2026-11-06 R2483 verification window: the two owed batteries were run and "
    "the first leg was RED - 568/569 suites with one real failure, "
    "reconcile-daily-census cd7-live-real-tree exit=2. The suite reproduced "
    "alone in 5s and the census named the cause in four lines: the four R2482 "
    "evidence files (panel-R2482-adjacent.log, panel-lobby-R2482-a.log, "
    "panel-lobby-R2482-b.log, start-all-R2482-adjacent.log) were PowerShell "
    "UTF-16, class=ps-utf16, DRIFT-FLAG. Repaired at the birth site: those four "
    "files were deleted and the evidence re-taken through the shipped "
    "src/os/evidence_capture.py as two utf-8 LF files (qa/panel-lobby-R2483.log "
    "1532B, qa/start-all-R2483.log 464B, both crlf=0, no BOM), after which the "
    "census read DRIFT-CLEAN flags=0 and the red suite read 8/8 alone; the "
    "repair was committed as 6f2e6eb4 so the retry ran on a committed tree. "
    "RETRY GREEN: qa/reconcile-all-R2483-retry.log 864674B, 'RUNNER PASS "
    "(569/569 suites green, reconcile controls 7/7, 1652.7s)', 4390 criteria by "
    "independent recount, zero FAIL rows. Four follow-up sections: matrix FAIL "
    "then regenerated stamp-aligned to 54691B with --check byte-identical, so "
    "VERDICT R2483 PASS failing=none. Debt: reconcile-battery-R2481 and "
    "reconcile-battery-R2482 both closed through their shipped writer "
    "(125387B -> 125391B -> 125395B, readback ok each); no successor battery is "
    "owed because no registry module or suite changed post-battery and the "
    "registry is unmoved at 569/4390. Honest: zero product points, the defect "
    "was self-inflicted by R2482 and only surfaced because a battery finally "
    "ran, my own 'reconcile_all.py --help' invocation created a stray file named "
    "'--help' (deleted before commit, no evidence written, and the runner has no "
    "unknown-flag refusal - an unfixed rough edge, not claimed as fixed), the "
    "four old R2482 evidence paths no longer exist by design, Docker is absent "
    "so no containerised bring-up is claimed, the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items, and tasks.md was not touched."
)

base.OUTS = (
    "qa/reconcile-all-R2483.log + qa/reconcile-all-R2483-retry.log + "
    "qa/panel-lobby-R2483.log + qa/start-all-R2483.log + "
    "docs/sandbox-suite-matrix.md + state/debt.md + src/os/state.json + "
    "src/os/state_append_R2483.py + src/os/export_R2483.py + "
    "docs/status-export.json + heartbeat.txt + src/os/backlog.md"
)

if __name__ == "__main__":
    print(base.main())