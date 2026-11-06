"""export_R2493 - refresh docs/status-export.json for the R2493 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2493 verification face: the R2492 registry (575 suites / 4426 "
           "criteria) is proved green on a committed tree, and the two real "
           "defects the red leg named - a matrix doc without its stamp-source "
           "provenance line and an evidence file captured through a PowerShell "
           "pipe - are repaired at their birth site")

base.LATEST = ("qa/reconcile-all-R2493-retry.log (868897B utf-8 LF, RUNNER PASS "
               "575/575 suites green, reconcile controls 7/7, 1164.3s, zero FAIL "
               "rows, criteria recounted to exactly 4426) plus the repair commit "
               "e3d9c7c1 (re-taken qa/relative-package-presence-refusal-R2492.log "
               "through the shipped capture writer and docs/sandbox-suite-matrix.md "
               "regenerated stamp-aligned at 55212B) at 2026-11-06")

base.NEXT = ("2026-11-07 a product face on the tech head state/queue/tech.md:528 "
             "prefix AC-MSFL1 (matrix_stamp_from_liveness, criteria AC-MSFL1.."
             "AC-MSFL6 pinned at R2442 before any code). Every P-47 item beyond "
             "the shipped sandbox faces still waits on CEO physical items "
             "(merchant id, mini-program appid/secret)")

base.RESULT = (
    "2026-11-06 R2493 VERIFICATION window on the battery the register owed "
    "(product-face-R2492, pre-registered 575 suites / 4426 criteria, target "
    "re-measured by importing reconcile_all.SUITES before the run). The FIRST "
    "leg was RED at 573/575 with three failed assertions and both causes were "
    "real birth-site defects rather than load noise: reconcile-daily-census cd7 "
    "read drift because qa/relative-package-presence-refusal-R2492.log was "
    "pwsh-capture (17 CRLF) instead of the shipped writer's utf-8 LF, and "
    "os-matrix-stamp-compare AC-MSC4 read FAIL because the shipped matrix doc "
    "carried no stamp-source provenance line, so suite_matrix --check passed at "
    "55158B while the live stamp leg re-rendered 55216B. Both were repaired at "
    "the birth site and committed ALONE as e3d9c7c1 before the retry: the "
    "evidence was re-taken through src/os/evidence_capture.py (1342B, legs=2 "
    "identical, adjacent=3 fails=0, census then DRIFT-CLEAN flags=0) and the "
    "matrix doc was regenerated stamp-aligned (55216B, both laws agreeing). "
    "RETRY GREEN on the committed repair tree: qa/reconcile-all-R2493-retry.log "
    "closes with RUNNER PASS (575/575 suites green, reconcile controls 7/7, "
    "1164.3s), zero FAIL suite rows, and an independent recount of the 575 PASS "
    "rows sums to exactly 4426 criteria. Four follow-up sections then read PASS "
    "(matrix dry-run FAIL then stamp-aligned regeneration at green=575/575, "
    "55212B, --check byte-identical; fingerprint CLEAN domains=5; profile "
    "byte-identical; census DRIFT-CLEAN) for VERDICT R2493 PASS. Debt: "
    "product-face-R2492 closed and product-face-R2493 opened first=yes through "
    "the shipped writers, naming the next product face AC-MSFL1. Honest: "
    "internal verification face, zero product points; both red causes were mine "
    "and are named; my aborted reconcile_daily --check left a truncated "
    "qa/reconcile-daily-20261106.log which was deleted rather than kept; the "
    "state fold ran in this window at the round-block boundary (items 1..89, "
    "336 tokens, 12452B, FOLD-CLEAR); Docker is absent so no containerised "
    "bring-up is claimed; the real 19.9 debit and the real msgSecCheck still "
    "wait on CEO physical items; tasks.md was not touched."
)

base.OUTS = (
    "qa/reconcile-all-R2493-retry.log + docs/sandbox-suite-matrix.md + "
    "qa/relative-package-presence-refusal-R2492.log + state/debt.md + "
    "src/os/closeout_R2493.py + src/os/fold_R2493.py + "
    "src/os/export_R2493.py + src/os/state.json + docs/status-export.json + "
    "src/os/backlog.md + heartbeat.txt"
)

if __name__ == "__main__":
    print(base.main())