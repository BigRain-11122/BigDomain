"""export_R2451 - refresh docs/status-export.json for the R2451 window.

The derivation, the atomic write and the read-back self-check live in the
shipped export_R2431 module; this driver only supplies this round's three CEO
lines and its one results row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2451 verification window: the carried reconcile battery ran on "
           "the committed R2450 tree, came back RED at 550/553, and named "
           "three real defects of that window - a suite that asked the "
           "shipped readers with a cwd-relative root, a live capture taken "
           "through a PowerShell redirect, and five delivered rounds left "
           "untriaged in the residue declaration - all three repaired at "
           "their birth sites and committed alone, after which the retry "
           "battery read RUNNER PASS 553/553 suites at criteria 4294 exactly "
           "as pre-registered")

base.LATEST = ("src/os/test_status_export_writer_dialect_wire.py (cwd-relative "
               "root repaired, 6/6 from both the repo root and src/os) + "
               "src/os/repair_R2451.py (evidence normalised, 414B -> 409B, "
               "crlf 5 -> 0, line set proved identical, readback ok) + "
               "state/residue_triage.json (five rounds spliced through the "
               "shipped batch channel, 275 -> 280 entries, TRIAGED 280/280) + "
               "qa/reconcile-all-R2451.log (red leg, 854416B) + "
               "qa/reconcile-all-R2451-retry.log (green leg, 853328B) + "
               "docs/sandbox-suite-matrix.md regenerated to 53443B at 553 "
               "suites / 4294 criteria, --check byte-identical")

base.NEXT = ("the next PRODUCT face at the deliverable-aware tech head "
             "state/queue/tech.md:518 prefix AC-SEWS1 "
             "(status_export_writer_transport_scope): prove the transport of "
             "every derived export writer, naming an UNPROVABLE writer with "
             "its refusal code instead of silently dropping it - no successor "
             "battery is owed because this window changed no product module "
             "and the registry is unmoved at 553 suites / 4294 criteria")

base.RESULT = (
    "2026-11-05 R2451 verification window on the debt gate first=yes item "
    "(reconcile-battery-R2451, carried from R2450 at the pre-registered 553 "
    "suites / 4294 criteria): zero product edits until green, the R2168 "
    "mixed-tree rule honoured. The first battery was RED - 550/553 suites, 4 "
    "failed assertions, 1350.5s, red leg kept - and all three reds were real: "
    "(1) os-status-export-writer-dialect-wire asked GWDA.report(\".\") and "
    "SEWD.check(\".\"), while the runner executes suites at cwd=src/os, so the "
    "audit resolved src/os/src/os and raised E_GWDA_UNREADABLE; repaired by "
    "passing REPO at three call sites, proved 6/6 from BOTH cwds. (2) "
    "reconcile-daily-census flagged the R2450 live capture as class=pwsh-"
    "capture (414B, five CRLF); normalised by repair_R2451.py with the line "
    "set proved identical before the write and the census baseline untouched "
    "(414B->409B, crlf 5->0, readback ok), census then DRIFT-CLEAN files=2526 "
    "flag=0. (3) os-residue-triage read 5/6 with five untriaged rounds "
    "R2440/R2442/R2444/R2446/R2448, all DELIVERED when read live; spliced "
    "through residue_triage_append_batch at the predicted 275->280 entries and "
    "77117B->78117B, now TRIAGED 280/280. Repairs committed alone, then the "
    "retry battery read RUNNER PASS 553/553 suites plus controls 7/7 in "
    "1259.7s at criteria 4294 exactly, TMP RECLAIM 932/932, and the four "
    "follow-up sections read PASS after the designed matrix FAIL and its "
    "stamp-aligned regeneration to 53443B (--check byte-identical) for "
    "VERDICT R2451 PASS failing=none. Debt: reconcile-battery-R2451 closed at "
    "116580B -> 116583B (line=187, open 2->1, done 166->167, readback ok) and "
    "product-face-R2452 opened first=yes at 116583B -> 116959B on tech head "
    "state/queue/tech.md:518 prefix AC-SEWS1; no successor battery owed. Zero "
    "product points claimed for a window that bought back three real repairs."
)

if __name__ == "__main__":
    sys.exit(base.main())