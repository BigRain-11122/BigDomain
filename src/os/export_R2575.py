"""export_R2575 - refresh docs/status-export.json for the R2575 round."""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = (
    "R2575 product window on the debt gate head the register named: a "
    "cross-module base / module-value receiver / class-constant-alias reading "
    "shipped with six criteria, its suite green twice, a bounded live leg on "
    "the real tree, and the registry moved by exactly one row"
)

base.LATEST = (
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_class_source_scope.py (28772B, AC-PNDCI1..AC-PNDCI6) + "
    "qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-class-source-scope-R2575.log (6834B, legs=2 "
    "identical=True adjacent=5 fails=0) + qa/...-class-source-scope-live-"
    "R2575.log (387B, 7 modules, 178 loops, four fixtures resolved here and "
    "refused by the shipped reader) + docs/sandbox-suite-matrix.md (60982B at "
    "617 suites / 4678 criteria, green=616/617)"
)

base.NEXT_DUE = "2026-11-09T20:00:00+08:00"

base.NEXT = (
    "the full reconcile battery the debt register now names first "
    "(reconcile-battery-R2574) on the committed tree at the pre-registered "
    "617 suites / 4678 criteria, BEFORE any further product byte"
)

base.RESULT = (
    "2026-11-08 R2575 PRODUCT window. The debt gate named product-face-R2574 "
    "first, so no battery was owed before product bytes. SHIPPED "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_class_source_scope.py plus its six-criteria suite: a base "
    "class imported from ANOTHER module in the same root resolves through the "
    "subclass path, cycle-guarded by (module, path) and bounded at depth 8, "
    "so a two-hop cross base resolves and a base cycle returns the subclass "
    "own value instead of recursing; a method returning an inherited class "
    "attribute through self is re-read through that cross table; a "
    "module-level value bound by a call returning a class attribute resolves "
    "as a with-as receiver (hop with-as-module-value); and a class-constant "
    "alias resolves to the same literal to a fixpoint, including a two-step "
    "chain, while an alias cycle resolves nothing and does not hang. The "
    "shipped class-base face is asked FIRST and never overwritten. PROOF: "
    "AC-PNDCI1..AC-PNDCI6 SUITE PASS 6/6 TWICE with byte-identical output plus "
    "five adjacent probe suites green through the shipped capture callable. A "
    "BOUNDED live leg on the REAL tree reads 7 probe modules / 178 loops with "
    "read_only=True and measures FOUR fixtures on BOTH readers: "
    "cross-module-base ok/b here against "
    "refused/attr-class-base-constant:cls.K.ATTR there, self-cross-base ok/b "
    "against refused/attr-cross-call:m.ATTR, module-value ok/b against "
    "refused/attr-with-as:m.ATTR, and class-alias ok/b against "
    "refused/attr-class-base-constant:cls.K.OTHER. ONE SEED CLAIM CORRECTED "
    "AGAINST MEASUREMENT: the seed called a self-through-a-base method still "
    "open, but the shipped face already merges a SAME-module base and measured "
    "ok/b at HEAD, so that answer is carried and only the CROSS-module base "
    "shape is re-read. TWO own defects were measured and fixed in the CODE, "
    "and one assertion was corrected to measurement. REGISTRY 616/4672 -> "
    "617/4678 recounted by import (617 unique names, 617 unique paths); "
    "matrix regenerated stamp-aligned to 60982 bytes with green honestly "
    "616/617 and --check byte-identical at rc=0 after a designed dry-run FAIL "
    "that wrote no byte. BOARD: row 609 closed through queue_close_R2575.py at "
    "its predicted and measured 1805831B and ONE row seeded from this window "
    "own measured limit (AC-PNCS1..AC-PNCS6 at line 611, floor FLOOR-MET). "
    "DEBT: product-face-R2574 closed (line 322, open 30->29, done 274->275), "
    "reconcile-battery-R2574 opened first=yes (181058B -> 181436B), "
    "product-face-R2575 opened first=no (181436B -> 181815B); the gate reads "
    "CLAIM-FIRST reconcile-battery-R2574 first=1 open=31. HONEST: one product "
    "point and nothing a CEO could newly open; a base supplied by an installed "
    "package is not read; a module-level alias of a call is the seeded next "
    "row; Docker is absent; the real 19.9 debit and the real msgSecCheck still "
    "wait on CEO physical items; tasks.md untouched. Zero cloud calls, zero "
    "external API touches."
)

base.OUTS = (
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_class_source_scope.py + src/os/test_probe_seam_name_binding_"
    "arm_mixed_residual_alias_attribute_import_alias_scope_class_source_"
    "scope.py + qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
    "import-alias-scope-class-source-scope-R2575.log + qa/probe-seam-name-"
    "binding-arm-mixed-residual-alias-attribute-import-alias-scope-class-"
    "source-scope-live-R2575.log + src/sandbox/reconcile_all.py + "
    "docs/sandbox-suite-matrix.md + state/queue/tech.md + state/debt.md + "
    "src/os/state.json + src/os/queue_close_R2575.py + "
    "src/os/live_class_source_R2575.py + src/os/state_append_R2575.py + "
    "src/os/export_R2575.py + src/os/backlog.md + docs/status-export.json + "
    "heartbeat.txt"
)

if __name__ == "__main__":
    print(base.main())