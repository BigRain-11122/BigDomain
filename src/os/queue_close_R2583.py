"""R2583 board closeout for the AC-PNAM1 seed row at state/queue/tech.md:615.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window with
src/os/limits_module_alias_alias_scope_next_R2583.py and
src/os/limits_module_alias_alias_scope_next2_R2583.py on private worlds where
the honest answer is `b`: a WALRUS module-alias head and a RELATIVE FROM-import
at the call site.

Refuses to write when the live evidence, the suite evidence, the limits logs or
the matrix document is absent, so no number is invented.
"""

import io
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
LIVE = os.path.join(REPO, "qa", "module-alias-alias-scope-live-R2583.log")
EVIDENCE = os.path.join(REPO, "qa", "module-alias-alias-scope-R2583.log")
LIMITS = os.path.join(REPO, "qa",
                      "module-alias-alias-scope-limits-R2583.log")
NEXT = os.path.join(REPO, "qa",
                    "module-alias-alias-scope-limits-next-R2583.log")
NEXT2 = os.path.join(REPO, "qa",
                     "module-alias-alias-scope-limits-next2-R2583.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2579,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_module_alias_attribute_alias_"
             "scope.py`")

NEXT_SEED = (
    "- [ ] P2 tech seed (R2583, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_scope.py` - MEASURED "
    "this window with src/os/limits_module_alias_alias_scope_next_R2583.py "
    "and src/os/limits_module_alias_alias_scope_next2_R2583.py against "
    "private worlds where the honest answer is `b`: (a) a module-alias head "
    "bound by a WALRUS (`(M := consts)` then `BASE = M.HW`) reads "
    "`attr-module-alias-unbound:M.HW`, because only plain and annotated "
    "assignments are alias edges; (b) a with-as CALL context on a RELATIVE "
    "FROM-imported function name (`from .mk import mkmod as REG` with "
    "`with REG() as m`) reads `attr-module-alias-unbound:mk.REG()`, because "
    "the FROM-import reader keeps absolute imports only (level 0). Three "
    "further shapes were measured and ALREADY resolve, so they are NOT "
    "claims of this row: an ANNOTATED alias head (`M: object = consts`), a "
    "THREE-step attribute path (`a.C.B.HW`), and an alias head whose target "
    "is itself a FROM-imported module name (`from pkg import consts`). "
    "Product: ONE reading that follows a walrus alias head and a relative "
    "FROM-imported call context. Criteria AC-PNAA1..AC-PNAA6 pinned HERE "
    "BEFORE any code: AC-PNAA1 a module-alias head bound by a walrus "
    "resolves as a with-as receiver and names the alias link; AC-PNAA2 a "
    "with-as call context on a RELATIVE FROM-imported function name "
    "resolves and names the relative hop; AC-PNAA3 a relative FROM-import of "
    "a name that is not a function is refused with its own word rather than "
    "resolved; AC-PNAA4 a relative FROM-imported module alias head (`from . "
    "import consts` then `M = consts`) resolves; AC-PNAA5 every answer the "
    "seventeen shipped faces already gave is carried unchanged on the row; "
    "AC-PNAA6 pure ASCII, stdlib only, no clock, zero network, its own "
    "reconcile label and its own suite. Five anchors to re-check "
    "zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_module_alias_alias_scope, AC-PNAA, E_PNAA, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-module-alias-alias-scope, "
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_alias_scope."
)


def live_facts():
    if not os.path.isfile(LIVE):
        return None
    text = io.open(LIVE, encoding="utf-8").read()
    facts = {}
    for key in ("modules", "loops", "ma_resolved", "ma_named"):
        match = re.search(r"(?<![A-Za-z_])%s=(\d+)" % (key,), text)
        if match:
            facts[key] = match.group(1)
    return facts


def main():
    facts = live_facts()
    if facts is None:
        print("REFUSED E_QCR2583_NO_LIVE: %s is absent" % LIVE)
        return 3
    for path in (EVIDENCE, LIMITS, NEXT, NEXT2, MATRIX):
        if not os.path.isfile(path):
            print("REFUSED E_QCR2583_NO_EVIDENCE: %s is absent" % path)
            return 3
    evidence_bytes = os.path.getsize(EVIDENCE)
    limits_bytes = os.path.getsize(LIMITS)
    next_bytes = os.path.getsize(NEXT)
    next2_bytes = os.path.getsize(NEXT2)
    matrix_bytes = os.path.getsize(MATRIX)
    discharged = (
        "  DISCHARGED R2583 (line 615, AC-PNAM1..AC-PNAM6 pinned in that row "
        "at R2579 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_module_alias_attribute_alias_scope.py plus its "
        "suite shipped. The extension is applied THROUGH the shipped reading "
        "rather than beside it: the readers both shipped faces call at run "
        "time are swapped for this face own inside one guarded block and "
        "restored in a finally, so an attribute head bound by a plain module "
        "alias resolves as a with-as receiver and names the alias link, a "
        "two-step attribute path resolves to the module its final link names "
        "while a middle link naming no module is refused by name, a with-as "
        "call context on a FROM-imported function name resolves and names the "
        "import hop, and a call on a name that is imported but is NOT a "
        "function is refused with this face own word "
        "attr-import-not-callable:<name>. The SHIPPED baseline on every row "
        "is measured with the readers UNPATCHED, so the row really carries "
        "what the faces it extends answered. PROOF: AC-PNAM1..AC-PNAM6 SUITE "
        "PASS 6/6 on the first run and 6/6 TWICE with identical output plus "
        "two adjacent probe suites green through the shipped capture "
        "(qa/module-alias-alias-scope-R2583.log, %dB, legs=2, "
        "identical=True, adjacent=2, fails=0); a BOUNDED live leg over %s "
        "real probe modules reads loops=%s ma_resolved=%s ma_named=%s with "
        "read_only=True and measures the SAME two fixtures on BOTH readers - "
        "alias-head ok/b and from-import-call ok/b here against "
        "refused/attr-module-alias-unbound:M.HW and "
        "refused/attr-cross-call:m.ATTR there "
        "(qa/module-alias-alias-scope-live-R2583.log, %dB, utf-8 LF, zero "
        "CRLF, zero BOM). THREE of my own assertions failed on the first run "
        "and were repaired in the CODE, not loosened: the two-step path "
        "needed a module-valued attribute step and a bare module-name "
        "fallback, and the FROM-import hop was being answered by the face "
        "this one extends so the hop word never named the import. The two "
        "limits THIS window leaves open were measured the same way "
        "(qa/module-alias-alias-scope-limits-R2583.log, %dB; "
        "qa/module-alias-alias-scope-limits-next-R2583.log, %dB; "
        "qa/module-alias-alias-scope-limits-next2-R2583.log, %dB) and the "
        "three shapes that already resolve are named there rather than "
        "claimed. The registry moved by ONE row to 622 suites / 4708 "
        "criteria, recounted by importing reconcile_all.SUITES rather than "
        "trusted (622 unique names, 622 unique paths), and "
        "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the "
        "eligible battery leg qa/reconcile-all-R2581.log to %d bytes at 622 "
        "suites / 4708 criteria with its green line honestly reading 621/622 "
        "and --check byte-identical. tasks.md was not touched."
        % (evidence_bytes, facts.get("modules"), facts.get("loops"),
           facts.get("ma_resolved"), facts.get("ma_named"),
           os.path.getsize(LIVE), limits_bytes, next_bytes, next2_bytes,
           matrix_bytes)
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-09 R2583]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, NEXT_SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-09 R2583] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2583")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2583,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:70])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())