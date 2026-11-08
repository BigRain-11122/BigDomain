"""export_R2563 - refresh docs/status-export.json for the R2563 round.

The current, latest, milestone and queue lines are DERIVED by the shipped
export_R2431 driver from the live tree; this module only supplies this round's
results row and the outs list.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.RESULT = (
    "2026-11-08 R2563 PRODUCT window on the tech head the register named "
    "(product-face-R2562, state/queue/tech.md:599 prefix AC-PNDC1, criteria "
    "AC-PNDC1..AC-PNDC6 pinned in that row at R2561 BEFORE any code). The "
    "three gaps the seed row names were RE-MEASURED before any code with "
    "src/os/limits_attribute_import_alias_R2563.py over one private world "
    "where the honest answer is `b`, and the measurement also surfaced a real "
    "OVER-resolution (a helper carrying two values through an alias read `ok` "
    "on the predicate face). SHIPPED "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope.py plus its six-criteria suite: a plain `import m` base "
    "resolves and is NAMED attr-plain-import when it cannot be, an "
    "`import m as x` alias and a with-as module binding resolve through the "
    "ACTUAL module name instead of being called locals, a constant that is an "
    "alias of another constant is followed to its literal while two values "
    "read name-mixed, and a `from other import NAME` re-export resolves "
    "through that module; every key the shipped predicate reading published "
    "is carried unchanged beside this face own. PROOF measured, not quoted: "
    "AC-PNDC1..AC-PNDC6 SUITE PASS 6/6 TWICE with legs=2 identical=True "
    "adjacent=5 fails=0 (qa/probe-seam-name-binding-arm-mixed-residual-alias-"
    "attribute-import-alias-scope-R2563.log, 4891B) and the same suite green "
    "alone at closeout; a bounded live leg over 5 real probe_seam modules "
    "reads ia_resolved=0 ia_named=0 over 161 loops with unreadable=0 and both "
    "module digests unchanged, and the SAME fixture reads refused "
    "attr-base-local:h on the predicate face where this face reads ok b "
    "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-live-R2563.log, 932B). The registry moved by ONE row to 611 "
    "suites / 4642 criteria recounted by import (611 unique names, 611 unique "
    "paths) and docs/sandbox-suite-matrix.md was regenerated from the eligible "
    "R2562 battery leg to 59700 bytes at 611/4642 with green honestly reading "
    "610/611, --check byte-identical at rc=0. Board row 599 closed and its "
    "AC-PNDCE1 seed pinned; debt: product-face-R2562 closed and "
    "reconcile-battery-R2563 opened first=yes, so the next window owes that "
    "battery before any further product byte. Zero cloud calls, zero external "
    "API touches."
)

base.OUTS = (
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope.py (21285B) + its suite (13022B, 6/6 twice) + "
    "qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-R2563.log (4891B) + the live leg (932B) + "
    "docs/sandbox-suite-matrix.md (59700B, 611 suites / 4642 criteria, --check "
    "byte-identical) + state/queue/tech.md (row 599 closed, AC-PNDCE1 seed) + "
    "state/debt.md + src/os/state.json + src/os/backlog.md + "
    "docs/status-export.json + heartbeat.txt"
)

if __name__ == "__main__":
    print(base.main())