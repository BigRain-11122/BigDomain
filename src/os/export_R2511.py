"""export_R2511 - refresh docs/status-export.json for the R2511 product window.

The derivation, the queue face and the proved write live in the shipped
export_R2431 / export_driver_queue_face modules; this driver only supplies
this round's result row and its outs row.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.RESULT = (
    "2026-11-07 R2511 PRODUCT window on the tech head the register named "
    "(product-face-R2510, state/queue/tech.md:549 prefix AC-STPT1 "
    "stamp_text_coverage, criteria AC-STPT1..AC-STPT6 pinned there at R2509 "
    "BEFORE any code). Five-silence scan at open was clean at HEAD 7802a2da "
    "(git status empty, no index.lock, zero @BigDomain ledger rows, "
    "content-addressed decisions diff new=0 at a measured 189 rows, group "
    "orders tail unchanged at 2026-11-06 23:46, benchmarks 2026-11-03 inside "
    "the gate) and debt_gate read CLAIM-FIRST on product-face-R2510 with "
    "queue_head naming line 549 claimable=10 and all five anchors free of "
    "shipped code. CLAIM: every shipped gate reads the patterns document, the "
    "DISK or the evidence path, while suite_matrix.render also prints two "
    "CALLER-SUPPLIED strings - the generation stamp and the --stamp-from "
    "provenance source - and a broken codepoint in either reached the "
    "CEO-visible artifact with every existing reading still publishable=True "
    "(measured at R2509). SHIPPED src/os/stamp_text_coverage.py plus its "
    "suite, and render now asks it one statement after the evidence-name seam "
    "at BOTH the check path and the generate path, refusing at exit 4 with "
    "FAIL stamp-text naming the piece and the value and no artifact byte "
    "opened. Coverage is DERIVED, not listed: the real render is composed once "
    "with the values in hand and the printed stamp line and provenance line "
    "are read back through the SHIPPED laws (suite_matrix.doc_stamp, "
    "matrix_stamp_provenance_line.recorded_source) before the shipped "
    "per-codepoint law is asked at CALL time; a render given no stamp_from "
    "prints no provenance line and claims no such piece. PROOF: "
    "AC-STPT1..AC-STPT6 SUITE PASS 6/6 TWICE identical plus three adjacent "
    "readability suites green (qa/stamp-text-coverage-R2511.log, "
    "legs=2 identical=True fails=0 adjacent=3, digest 52ADD8ADF4C4F5A3) and a "
    "live leg on the REAL tree reading CLEAN with a doctored stamp and a "
    "doctored stamp_from each refused while the patterns and artifact digests "
    "stayed identical (qa/stamp-text-coverage-live-R2511.log). The first suite "
    "run was RED on two real counts - the committed matrix doc still carried "
    "584 registry rows against the new 585, and this module docstring named "
    "the borrow path literally so AC-STPT4 caught it - both repaired at the "
    "birth site: the doc regenerated stamp-aligned at 56263B over 585 suites / "
    "4486 criteria with --check byte-identical, and the docstring reworded. "
    "BIRTH-SITE REPAIR also landed in artifact_disk_text_readability and "
    "evidence_name_text_coverage, which now read the new seam off the module "
    "instead of freezing the seam names they shipped with. REGISTRY "
    "584/4480 -> 585/4486 by one row os-stamp-text-coverage(6). BOARD: row 549 "
    "closed and one seed pinned from this window own birth-site repair "
    "(probe_seam_registry, head line 551 prefix AC-PSMR1) refilling the tech "
    "floor to claimable=10. DEBT: product-face-R2510 closed "
    "(145469B -> 145472B, readback ok), reconcile-battery-R2511 opened "
    "first=yes at 585/4486 (145472B -> 146223B, readback ok) because the "
    "registry moved, and product-face-R2511 opened first=no "
    "(146223B -> 146646B, readback ok). Honest: the increment is a runnable "
    "guard on the CEO-visible artifact rather than a new feature, the coverage "
    "probe patches five seams for one compose and restores them in a finally "
    "block (disclosed limit), no battery ran by design, Docker is absent so no "
    "containerised bring-up is claimed, and every P-47 item still waits on CEO "
    "physical pieces (merchant id, mini-program appid/secret)."
)

base.OUTS = (
    "src/os/stamp_text_coverage.py + src/os/test_stamp_text_coverage.py + "
    "src/sandbox/suite_matrix.py + src/sandbox/reconcile_all.py + "
    "src/os/artifact_disk_text_readability.py + "
    "src/os/evidence_name_text_coverage.py + docs/sandbox-suite-matrix.md + "
    "qa/stamp-text-coverage-R2511.log + "
    "qa/stamp-text-coverage-live-R2511.log + state/queue/tech.md + "
    "state/debt.md + src/os/state.json + docs/status-export.json + "
    "src/os/backlog.md + heartbeat.txt + src/os/capture_R2511.py + "
    "src/os/live_R2511.py + src/os/state_append_R2511.py + "
    "src/os/export_R2511.py"
)

if __name__ == "__main__":
    print(base.main())