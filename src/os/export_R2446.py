"""export_R2446 - refresh docs/status-export.json for the R2446 window.

The derivation, the atomic write and the read-back self-check live in the
shipped export_R2431 module; this driver only supplies this round's three
CEO lines and its one results row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2446 product window: the three-face compare reads a VERDICT and a "
           "publisher SET, so a per-line module rewrite under an agreeing "
           "verdict was invisible - the shipped reader now compares the values "
           "the faces actually share on every published (path, line), names a "
           "disagreement ROWS-SPLIT with the file, the line, the key and each "
           "face's own module, label and seam, and names a face that publishes "
           "nothing on a line the others publish as ROWS-SILENT instead of "
           "counting it as agreement")

base.LATEST = ("src/os/comma_binding_face_row_drift.py + "
               "src/os/test_comma_binding_face_row_drift.py + "
               "qa/comma-binding-face-row-drift-R2446.log (SUITE PASS 6/6 "
               "twice identical plus three adjacent comma suites green) + "
               "qa/comma-binding-face-row-drift-live-R2446.log (FACES-AGREE "
               "rc=0, 11 cells, 0 splits, 0 silent) + "
               "docs/sandbox-suite-matrix.md regenerated to 53223B at 551 "
               "suites / 4282 criteria with --check byte-identical")

base.NEXT = ("the battery the R2168 rule owes on the committed R2446 tree "
             "(reconcile-battery-R2447, first=yes in the register) at the "
             "pre-registered 551 suites / 4282 criteria, with the matrix "
             "regenerated from THAT green evidence because a render from an "
             "ineligible log reads as a face mismatch; then the product face "
             "at the tech head state/queue/tech.md:514 prefix AC-PDR1")

base.RESULT = (
    "2026-11-04 R2446 product window on the item the debt gate named first=yes "
    "(product-face-R2446, tech head state/queue/tech.md:512 prefix AC-PFRD1 "
    "comma_binding_face_row_drift, whose AC-PFRD1..AC-PFRD6 were pinned in that "
    "row at R2444 BEFORE any code): SHIPPED "
    "src/os/comma_binding_face_row_drift.py plus its six-criteria suite. It "
    "asks the SHIPPED compare at CALL time and keeps its report unchanged, then "
    "compares the values the three faces actually share on every (path, line) a "
    "face publishes; the compared keys are the intersection of the published "
    "key sets minus the row identity, derived per run rather than listed. The "
    "exact probe this row was seeded from is proved both ways - the identity "
    "detail row rewritten from closeout_export_parity_wire to drifted_wire "
    "still reads FACES-AGREE rc=0 differences=0 at the verdict level, and the "
    "new reading names it ROWS-SPLIT at the line with both modules - while a "
    "face that publishes nothing on a line the others publish reads "
    "ROWS-SILENT naming that face. SUITE PASS 6/6 twice with an identical "
    "digest plus three adjacent comma suites green (EVIDENCE CAPTURE "
    "round=R2446 legs=2 identical=True adjacent=3 fails=0) and a live capture "
    "on the real src/os reading FACES-AGREE rc=0 cells=11 compared="
    "module/receiver/state/text splits=0 silent=0 over 11 publishers; the real "
    "tree carries no row drift, so the split and silent cases are proved on "
    "fixtures only and are not claimed as live catches. Wired "
    "os-comma-binding-face-row-drift(6) so the registry reads 551 suites / 4282 "
    "criteria; docs/sandbox-suite-matrix.md was regenerated stamp-aligned from "
    "the only eligible evidence face to 53223B with --check byte-identical. "
    "Board: row 512 stamped, one REAL measured gap row seeded from this "
    "window's own limit (row_key_carrier_scope AC-PFKC1..AC-PFKC6: a key two "
    "faces carry and disagree on is dropped, measured as `kind` over 22 rows "
    "and `relative` over 11), floor FLOOR-MET 5/5 10/10 10/10. Debt: "
    "product-face-R2446 closed through the shipped debtor (114246B -> 114249B, "
    "line=182, open 3->2, done 160->161) and reconcile-battery-R2447 opened "
    "first=yes at 114249B -> 114707B because this window changed product src "
    "bytes and moved the registry count. Zero CEO-visible business surface.")

base.OUTS = ("src/os/comma_binding_face_row_drift.py + "
             "src/os/test_comma_binding_face_row_drift.py + "
             "qa/comma-binding-face-row-drift-R2446.log + "
             "qa/comma-binding-face-row-drift-live-R2446.log + "
             "docs/sandbox-suite-matrix.md (53223B, 551 suites / 4282 criteria)")

if __name__ == "__main__":
    sys.exit(base.main())