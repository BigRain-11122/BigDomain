"""export_R2535 - refresh docs/status-export.json for the R2535 product window.

The derivation, the queue face and the proved write live in the shipped
export_R2431 / export_driver_queue_face modules; this driver only supplies this
round's CEO lines, its result row and its outs row.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.LATEST = ("src/os/probe_seam_nested_subscript_scope.py plus its "
               "six-criteria suite, green 6/6 twice with five adjacent probe "
               "suites and a live reading of the real tree, with "
               "qa/probe-seam-nested-subscript-scope-R2535.log and "
               "qa/probe-seam-nested-subscript-scope-live-R2535.log, "
               "2026-11-07")

base.NEXT = ("2026-11-07 VERIFICATION window on the battery this window owes: "
             "reconcile-battery-R2535 on the committed tree at the "
             "pre-registered 597 suites / 4558 criteria before any further "
             "product byte; every P-47 item beyond the shipped sandbox faces "
             "still waits on CEO physical items (merchant id, mini-program "
             "appid/secret)")

base.NEXT_DUE = "2026-11-08T23:00:00+08:00"

base.RESULT = (
    "2026-11-07 R2535 PRODUCT window on the tech head the register named "
    "(product-face-R2534, state/queue/tech.md:571 prefix AC-PCNS1, criteria "
    "AC-PCNS1..AC-PCNS6 pinned in that row at R2533 BEFORE any code). "
    "SHIPPED src/os/probe_seam_nested_subscript_scope.py plus its suite: a "
    "for-loop whose iterable is a CHAIN of two or more constant string "
    "subscripts on a literal container now resolves when the result holds "
    "EXACTLY ONE element and carries the chain with EVERY key, while a missing "
    "key, an integer index into a tuple, a call, a format and a comprehension "
    "step are NAMED with the HOP that broke (key@hop2, index@hop2, call@hop2, "
    "format@hop2, comprehension@hop1) instead of a bare shape word, and a "
    "two-element result is NAMED ambiguous and never resolved to its first "
    "element. PROOF measured: SUITE PASS 6/6 TWICE with byte-identical output "
    "plus five adjacent probe suites green and a live leg on the REAL tree "
    "reading SEAMS-NESTED-SUBSCRIPT-COVERED over 1447 probes with all three "
    "digests unchanged, and on the SAME fixture this face follows D['a']['b'] "
    "while the shipped subscript face still reads refused=nested. REGISTRY 596 "
    "/ 4552 -> 597 / 4558 by one row recounted by import; matrix regenerated "
    "stamp-aligned from the eligible battery leg qa/reconcile-all-R2533.log to "
    "57572 bytes with green honestly 596/597 and --check byte-identical. "
    "BOARD: row 571 closed at measured 1721378B and one row seeded from this "
    "window own measured limit (a NAME step bound to a str constant is named "
    "but not resolved), head now line 573 AC-PNKB1, floor FLOOR-MET. DEBT: "
    "product-face-R2534 closed, reconcile-battery-R2535 opened first=yes at "
    "597/4558 so the next window owes that battery before any product byte, "
    "and product-face-R2535 opened first=no; the expired residue declaration "
    "was re-pinned through its idempotent writer to R2545. HONEST: two product "
    "points, nothing a CEO could newly open; three defects were measured in my "
    "own first pass and fixed in the CODE rather than in the assertions; the "
    "fold is still DUE and was refused on token coverage rather than forced; "
    "Docker is absent, the real 19.9 debit and the real msgSecCheck still wait "
    "on CEO physical items, and the S4U lane reconcile still needs an elevated "
    "shell.")

base.OUTS = (
    "src/os/probe_seam_nested_subscript_scope.py + "
    "src/os/test_probe_seam_nested_subscript_scope.py + "
    "qa/probe-seam-nested-subscript-scope-R2535.log (6/6 twice, adjacent 5) + "
    "qa/probe-seam-nested-subscript-scope-live-R2535.log + "
    "src/sandbox/reconcile_all.py + docs/sandbox-suite-matrix.md + "
    "state/queue/tech.md + state/residue_triage.json + state/debt.md + "
    "src/os/state.json + src/os/backlog.md + docs/status-export.json + "
    "heartbeat.txt")

if __name__ == "__main__":
    print(base.main())