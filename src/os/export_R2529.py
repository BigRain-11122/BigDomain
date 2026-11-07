"""export_R2529 - refresh docs/status-export.json for the R2529 window.

The derivation, the queue face and the proved write live in the shipped
export_R2431 / export_driver_queue_face modules; this driver only supplies this
round's result row and its outs row. The three CEO lines are derived at call
time from state, from what actually landed under qa/ for this tick, and from
the open first=yes debt row - never typed as constants that can go stale.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.RESULT = (
    "2026-11-07 R2529 PRODUCT window on the tech head the register named "
    "(product-face-R2528, state/queue/tech.md:565 prefix AC-PCAE1 "
    "probe_seam_alias_expression_scope, criteria pinned at R2527 BEFORE any "
    "code). SHIPPED src/os/probe_seam_alias_expression_scope.py plus its "
    "six-criteria suite: a for-loop over a single NAMED constant, an annotated "
    "alias whose value is a subscript or attribute chain into a same-root "
    "module, and a container alias whose elements are names now resolve through "
    "the SHIPPED tables and carry the chain they took, while a call, a format, "
    "an arithmetic expression, a comprehension, a nested container and an "
    "unresolvable chain are NAMED on the row instead of reading silently "
    "absent. PROOF measured not quoted: AC-PCAE1..AC-PCAE6 SUITE PASS 6/6 "
    "TWICE with exit 0 on both legs plus five adjacent probe suites green "
    "(qa/probe-seam-alias-expression-scope-R2529.log); a live leg on the REAL "
    "tree reads SEAMS-ALIAS-COVERED over 1424 probes (3 covered, 174 "
    "out-of-scope, 1247 historical, missing=0) with the module and render "
    "digests unchanged "
    "(qa/probe-seam-alias-expression-scope-live-R2529.log, exit 0). REGISTRY "
    "593/4534 -> 594/4540 by exactly one row recounted by importing "
    "reconcile_all.SUITES rather than trusted; docs/sandbox-suite-matrix.md "
    "regenerated stamp-aligned from the eligible battery leg to 57227 bytes at "
    "594/4540 with green=593/594 self-describing and --check byte-identical at "
    "rc=0. BOARD: row 565 closed through the per-round writer at its predicted "
    "1707371 bytes (measured 1707371) and ONE row seeded from this window own "
    "MEASURED limit - a for-loop over a NAME bound to a constant CONTAINER "
    "still reads empty and names nothing - as AC-PCAF1..AC-PCAF6; head now line "
    "567, claimable=11, floor MET. DEBT: product-face-R2528 closed at its "
    "predicted 160016B -> 160019B (open 12->11, done 227->228, readback ok); "
    "because the registry moved, reconcile-battery-R2529 was appended first=yes "
    "at 160019B -> 160249B so the NEXT window owes that battery BEFORE any "
    "further product byte, and product-face-R2529 was appended first=no at "
    "160249B -> 160450B. HONEST: two product points and nothing a CEO could "
    "open is new; my first container reading published nested trees into the "
    "shipped table and the shipped element reader raised TypeError, so the "
    "entries were flattened to the SHIPPED format and a nested container is now "
    "refused as nested by name; two assertions in my own suite were corrected "
    "against measurement rather than loosening the code; the walk shape is a "
    "fourth copy; Docker is absent; the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items; tasks.md was not touched; "
    "the state_fold layout defect from R2522 is still open and the append used "
    "a proved load+dump round-trip; the S4U lane reconcile still needs an "
    "ELEVATED shell.")

base.OUTS = (
    "src/os/probe_seam_alias_expression_scope.py + "
    "src/os/test_probe_seam_alias_expression_scope.py + "
    "qa/probe-seam-alias-expression-scope-R2529.log + "
    "qa/probe-seam-alias-expression-scope-live-R2529.log + "
    "src/sandbox/reconcile_all.py + docs/sandbox-suite-matrix.md + "
    "state/queue/tech.md + state/debt.md + src/os/queue_close_R2529.py + "
    "src/os/closeout_R2529.py + src/os/export_R2529.py + src/os/state.json + "
    "docs/status-export.json + src/os/backlog.md + heartbeat.txt")

if __name__ == "__main__":
    print(base.main())