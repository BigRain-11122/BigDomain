"""export_R2445 - refresh docs/status-export.json for the R2445 window.

The derivation, the atomic write and the read-back self-check live in the
shipped export_R2431 module; this driver only supplies this round's three
CEO lines and its one results row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2445 verification window: the debt gate named the battery the "
           "R2168 rule owed on the committed R2444 tree, so the full "
           "reconcile battery ran FIRST at the pre-registered 550 suites / "
           "4276 criteria and came back red twice on one face - the matrix "
           "document recorded the R2444 product suite log while the checker "
           "resolves only eligible all-green battery evidence; the document "
           "was re-rendered from the one eligible face and committed alone, "
           "after which the final leg read RUNNER PASS 550/550 at the same "
           "criteria total with all four follow-up sections green")

base.LATEST = ("qa/reconcile-all-R2445.log + qa/reconcile-all-R2445-retry.log"
               " (both red legs, 851226B / 851228B) + "
               "qa/reconcile-all-R2445-final.log (RUNNER PASS 550/550, "
               "1387.4s, criteria 4276) + docs/sandbox-suite-matrix.md "
               "regenerated stamp-aligned to 53114B at 550 suites / 4276 "
               "criteria with --check byte-identical")

base.NEXT = ("product face on the tech head state/queue/tech.md:512 prefix "
             "AC-PFRD1 (comma_binding_face_row_drift: the three-face compare "
             "reads verdicts and publisher sets only, so a per-line module "
             "drift under an unchanged verdict still reads FACES-AGREE), "
             "whose criteria were pinned in that row at R2444 before any code")

base.RESULT = (
    "2026-11-04 R2445 verification window on the item the debt gate named "
    "first=yes (reconcile-battery-R2445, carried from R2444 at the "
    "pre-registered 550 suites / 4276 criteria): zero product code changed, "
    "the R2168 mixed-tree rule honoured. Leg 1 read 549/550 suites with the "
    "criteria total 4276 exactly as pre-registered and the only red was "
    "os-matrix-stamp-compare AC-MSC4, whose detail printed check=2 against "
    "the module verdict PASS; suite_matrix --check named the cause as an "
    "evidence-face mismatch, because R2444 had rendered the document from its "
    "own product suite log while the checker resolves only eligible all-green "
    "battery evidence. The retry leg reproduced the identical single red, "
    "which proved it deterministic. Repaired at the birth site: the document "
    "was re-rendered through the shipped generator with --stamp-from from the "
    "one eligible evidence face (53113B, --check PASS byte-identical, suite "
    "6/6 with AC-MSC4 green) and the repair was committed ALONE as 2ed31668. "
    "Final leg on the committed repair tree: RUNNER PASS 550/550 plus controls "
    "7/7 in 1387.4s at criteria 4276, TMP RECLAIM 932/932. Four follow-up "
    "sections then gave the designed matrix FAIL (53113B vs 53114B), a "
    "stamp-aligned regeneration to 53114B at 550/4276 and VERDICT R2445 PASS "
    "failing=none (fingerprint CLEAN 5 domains, profile byte-identical, "
    "census DRIFT-CLEAN). Debt: battery closed through the shipped debtor "
    "(line=180, open 3->2, done 159->160) and product-face-R2446 opened "
    "first=yes at 113812B -> 114246B naming state/queue/tech.md:512 "
    "AC-PFRD1; no successor battery owed because only a document changed. "
    "Zero product points claimed.")

base.OUTS = ("qa/reconcile-all-R2445.log + qa/reconcile-all-R2445-retry.log "
             "(red legs) plus qa/reconcile-all-R2445-final.log (RUNNER PASS "
             "550/550, criteria 4276) and docs/sandbox-suite-matrix.md "
             "regenerated to 53114B")

if __name__ == "__main__":
    sys.exit(base.main())