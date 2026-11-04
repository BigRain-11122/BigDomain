"""export_R2455 - refresh docs/status-export.json for the R2455 window.

The derivation, the atomic write and the read-back self-check live in the
shipped export_R2431 module; this driver only supplies this round's three CEO
lines and its one results row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2455 verification window: the battery the R2454 product edit owed "
           "was run on the committed tree and came back green - 555/555 suites "
           "plus controls 7/7 at exactly the pre-registered 4306 criteria - and "
           "the suite matrix was regenerated from THIS round own green evidence "
           "so the published registry is self-describing instead of borrowed")

base.LATEST = ("qa/reconcile-all-R2455.log (855799B at the green leg, 859638B "
               "with both follow-up legs, one utf-8 LF single writer through "
               "src/os/battery_stream.py, crlf=0 bom=False, RUNNER PASS 555/555 "
               "suites + controls 7/7 in 1209.1s at criteria 4306) + "
               "docs/sandbox-suite-matrix.md regenerated from that evidence "
               "through --stamp-from to 53657B at 555 suites / 4306 criteria "
               "with --check byte-identical and its own green line reading "
               "555/555 + src/os/closeout_R2455.py (state, backlog and "
               "heartbeat writers for this window)")

base.NEXT = ("the debt gate now names product-face-R2456 first=yes and the "
             "tech head reads state/queue/tech.md:522 prefix AC-PFKC1 "
             "row_key_carrier_scope - the row key is carried by more than one "
             "face with no reading that says which carrier a given line came "
             "from; criteria AC-PFKC1..AC-PFKC6 were pinned in that row at "
             "R2446 before any code, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2455 verification window on the debt gate first=yes item "
    "reconcile-battery-R2455 (carried from R2454 at the pre-registered 555 "
    "suites / 4306 criteria): ZERO product code changed, the R2168 mixed-tree "
    "rule honoured. The battery ran on the committed b216bfa9 tree with an "
    "empty git status, launched detached and unfiltered so the filtering-pipe "
    "trap was not re-paid, and read RUNNER PASS 555/555 suites green plus "
    "reconcile controls 7/7 in 1209.1s at criteria total=4306 EXACTLY as "
    "pre-registered, TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 "
    "reclaimed 326.59 MiB, evidence written by one utf-8 LF single writer "
    "(crlf=0 bom=False). The four follow-up sections produced the designed "
    "order: matrix FAILED first on the stale doc (on-disk=53662B against "
    "regenerated=53657B) with no byte written, the doc was regenerated from "
    "THIS round own eligible green evidence through --stamp-from to 53657B at "
    "555/4306, --check read byte-identical, and the re-run read matrix "
    "byte-identical, fingerprint CLEAN domains=5, profile byte-identical, "
    "census DRIFT-CLEAN for VERDICT R2455 PASS failing=none. Debt: "
    "reconcile-battery-R2455 closed at 118758B -> 118761B (line=191, open "
    "2->1, done 170->171, readback ok) and NO successor battery owed because "
    "no product src byte changed and the registry is unmoved, so "
    "product-face-R2456 was opened first=yes at 118761B -> 118972B naming the "
    "tech head state/queue/tech.md:522 prefix AC-PFKC1. Zero product points "
    "claimed; no P-47 business surface was rebuilt and every P-47 item "
    "remains blocked on CEO physical pieces."
)

if __name__ == "__main__":
    sys.exit(base.main())