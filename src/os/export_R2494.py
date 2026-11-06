"""export_R2494 - refresh docs/status-export.json for the R2494 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2494 product face: a borrowed stamp now says whether the document "
           "it names still exists - one reading answers LIVE / MISSING / "
           "AMBIGUOUS / NONE for docs/sandbox-suite-matrix.md at call time and "
           "names every dangling or ambiguous borrow instead of copying the "
           "recorded string")

base.LATEST = ("src/os/matrix_stamp_from_liveness.py + src/os/"
               "test_matrix_stamp_from_liveness.py with qa/"
               "matrix-stamp-from-liveness-live-R2494.log (506B utf-8 LF, "
               "shipped doc reads LIVE at rc 0 and a dangling-borrow copy reads "
               "MISSING at rc 2) and qa/matrix-stamp-from-liveness-R2494.log "
               "(SUITE PASS 6/6 twice identical, adjacent=2 fails=0) at "
               "2026-11-06")

base.NEXT = ("2026-11-07 the battery this window owes, on the committed tree at "
             "the pre-registered 576 suites / 4432 criteria, then a product face "
             "on the tech head state/queue/tech.md:531 prefix AC-EDQF1 "
             "(export_driver_queue_face). Every P-47 item beyond the shipped "
             "sandbox faces still waits on CEO physical items (merchant id, "
             "mini-program appid/secret)")

base.RESULT = (
    "2026-11-06 R2494 PRODUCT window on the tech head the register named "
    "(state/queue/tech.md:529 prefix AC-MSFL1 matrix_stamp_from_liveness, "
    "criteria AC-MSFL1..AC-MSFL6 pinned in that row at R2442 BEFORE any code). "
    "CLAIM: R2442 gave an artifact a provenance line naming the document its "
    "stamp was borrowed from, but recorded_source() handed the recorded string "
    "back verbatim, so a doc borrowing from a source deleted the next day read "
    "exactly like a live one. SHIPPED src/os/matrix_stamp_from_liveness.py plus "
    "src/os/test_matrix_stamp_from_liveness.py: the provenance reader stays the "
    "R2442 law asked at CALL time, the recorded string is published verbatim, "
    "and the tree is asked in two steps with no picking - the recorded path "
    "joined onto the root reads LIVE when present, otherwise one root-wide walk "
    "for the basename reads LIVE on a single match publishing the resolved "
    "path, AMBIGUOUS naming every candidate, MISSING for none, and a doc with "
    "no borrow reads NONE at exit 0. PROOF: AC-MSFL1..AC-MSFL6 SUITE PASS 6/6 "
    "TWICE identical plus two adjacent matrix suites green (qa/"
    "matrix-stamp-from-liveness-R2494.log 4259B, legs=2 identical=True "
    "adjacent=2 fails=0) and a live reading of the real tree (qa/"
    "matrix-stamp-from-liveness-live-R2494.log 506B utf-8 LF crlf=0). Registry "
    "575/4426 -> 576/4432 by exactly one row os-matrix-stamp-from-liveness(6); "
    "matrix restamped stamp-aligned to 55317B at 576/4432 with --check "
    "byte-identical and its green line honestly reading 575/576. The tech floor "
    "was SHORT at open (9/10, one open row gated) and was refilled with two "
    "real measured gaps, AC-PLR1 patterns_label_readability and AC-EUC1 "
    "evidence_utf8_capture, so the gauge reads FLOOR-MET 5/5 10/10 10/10. Debt: "
    "reconcile-battery-R2495 appended first=no at 130269B -> 131097B (readback "
    "ok) at the pre-registered 576/4432. Honest: two of the suite's own "
    "assertions first read RED and both were my faults (the shipped doc is "
    "restamped at closeout; a fresh render carries a fresh stamp) - the suite "
    "was corrected and no criterion loosened; the first live capture landed "
    "crlf=10 with codepage-mangled text and was deleted and re-taken with "
    "PYTHONIOENCODING=utf-8 (the trap is seeded, not merely mentioned); the "
    "mojibake label measured in suite_matrix_patterns.json is PRE-EXISTING and "
    "was not fixed here; suite_matrix.py was not modified; no battery ran and "
    "none is claimed; the real 19.9 debit and the real msgSecCheck still wait on "
    "CEO physical items."
)

base.OUTS = (
    "src/os/matrix_stamp_from_liveness.py + src/os/"
    "test_matrix_stamp_from_liveness.py + "
    "qa/matrix-stamp-from-liveness-R2494.log + "
    "qa/matrix-stamp-from-liveness-live-R2494.log + "
    "src/sandbox/reconcile_all.py + docs/sandbox-suite-matrix.md + "
    "state/queue/tech.md + state/debt.md + src/os/export_R2494.py + "
    "src/os/state.json + docs/status-export.json + src/os/backlog.md + "
    "heartbeat.txt"
)

if __name__ == "__main__":
    print(base.main())