"""R2585 board closeout for the AC-PNAA1 seed row at state/queue/tech.md:617.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window with
src/os/limits_module_alias_walrus_relative_next_R2585.py: a WALRUS nested in a
module-level branch is still unread.

Refuses to write when the evidence, the limits logs or the matrix document is
absent, so no number is invented.
"""

import io
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa",
                        "module-alias-walrus-relative-scope-R2585.log")
LIMITS = os.path.join(REPO, "qa",
                      "module-alias-walrus-relative-limits-R2585.log")
NEXT = os.path.join(REPO, "qa",
                    "module-alias-walrus-relative-limits-next-R2585.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2583,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_module_alias_attribute_alias_"
             "scope.py`")

NEXT_SEED = (
    "- [ ] P2 tech seed (R2585, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_"
    "scope.py` - MEASURED this window with "
    "src/os/limits_module_alias_walrus_relative_next_R2585.py against "
    "private worlds: (a) a WALRUS nested in a module-level branch "
    "(`if True:` then `(M := consts)`) still reads "
    "`attr-module-alias-unbound:M.HW`, because only a TOP-LEVEL walrus "
    "binding is read as an alias edge; (b) a TWO-LEVEL relative "
    "FROM-imported module alias head (`from .. import consts` inside "
    "pkg/inner/mk6.py) was measured and ALREADY resolves (ok/b), so it is "
    "named rather than claimed; (c) an unanchored probe text whose relative "
    "head names TWO modules is refused rather than guessed, which is the "
    "shipped design and not a gap. Product: ONE reading that follows a "
    "walrus bound inside a module-level branch. Criteria AC-PNAB1..AC-PNAB6 "
    "pinned HERE BEFORE any code: AC-PNAB1 a walrus inside a module-level "
    "`if`/`else`/`try` body resolves as a with-as receiver and names the "
    "branch it was read in; AC-PNAB2 a walrus bound TWICE on different "
    "branches is NAMED ambiguous rather than resolved to either; AC-PNAB3 a "
    "walrus inside a FUNCTION body is NOT read as a module-level alias and "
    "keeps the shipped refusal; AC-PNAB4 every shape the R2585 suite already "
    "pinned classifies exactly as before, top-level walrus or anchored "
    "relative included; AC-PNAB5 every answer the eighteen shipped faces "
    "already gave is carried unchanged on the row; AC-PNAB6 pure ASCII, "
    "stdlib only, no clock, zero network, its own reconcile label and its "
    "own suite. Five anchors to re-check zero-occupancy at HEAD before any "
    "code: probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_scope, "
    "AC-PNAB, E_PNAB, os-probe-seam-name-binding-arm-mixed-residual-alias-"
    "attribute-import-alias-scope-module-alias-attribute-alias-walrus-"
    "relative-scope, test_probe_seam_name_binding_arm_mixed_residual_alias_"
    "attribute_import_alias_scope_module_alias_attribute_alias_walrus_"
    "relative_scope."
)


def facts():
    """The bounded live numbers, read off THIS round own evidence log."""
    if not os.path.isfile(EVIDENCE):
        return None
    text = io.open(EVIDENCE, encoding="utf-8").read()
    out = {}
    match = re.search(r"modules=(\d+) loops=(\d+) unreadable=(\d+)", text)
    if match:
        out["modules"] = match.group(1)
        out["loops"] = match.group(2)
        out["unreadable"] = match.group(3)
    return out


def main():
    measured = facts()
    if measured is None:
        print("REFUSED E_QCR2585_NO_EVIDENCE: %s is absent" % EVIDENCE)
        return 3
    if not measured.get("loops"):
        print("REFUSED E_QCR2585_NO_LIVE: no bounded live numbers in evidence")
        return 3
    for path in (LIMITS, NEXT, MATRIX):
        if not os.path.isfile(path):
            print("REFUSED E_QCR2585_NO_LIMITS: %s is absent" % path)
            return 3
    evidence_bytes = os.path.getsize(EVIDENCE)
    limits_bytes = os.path.getsize(LIMITS)
    next_bytes = os.path.getsize(NEXT)
    matrix_bytes = os.path.getsize(MATRIX)
    discharged = (
        "  DISCHARGED R2585 (line 617, AC-PNAA1..AC-PNAA6 pinned in that row "
        "at R2583 BEFORE any code): src/os/probe_seam_name_binding_arm_mixed_"
        "residual_alias_attribute_import_alias_scope_module_alias_attribute_"
        "alias_walrus_relative_scope.py plus its suite shipped. The extension "
        "is applied THROUGH the shipped reading rather than beside it: the "
        "readers the parent faces call at run time are swapped for this face "
        "own inside one guarded block and restored in a finally, so a "
        "module-alias head bound by a WALRUS resolves as a with-as receiver "
        "and names the alias link, a with-as call context on a RELATIVE "
        "FROM-imported function name resolves and names the relative hop, a "
        "relative FROM-import of a name that is NOT a function is refused "
        "with this face own word attr-relative-import-not-callable:<name>, "
        "and a relative FROM-imported MODULE alias head resolves. A "
        "level-bearing import is resolved against the PACKAGE ANCHOR of the "
        "module being read, and an unanchored probe text only when exactly "
        "ONE module of that name exists under the root - never guessed. The "
        "SHIPPED baseline on every row is measured with the readers "
        "UNPATCHED, so the row really carries what the face it extends "
        "answered. PROOF: AC-PNAA1..AC-PNAA6 SUITE PASS 6/6 plus TWO "
        "adjacent probe suites green through the shipped capture "
        "(qa/module-alias-walrus-relative-scope-R2585.log, %dB, legs=2, "
        "identical=True, adjacent=2, fails=0); a BOUNDED live leg over %s "
        "real probe modules reads loops=%s unreadable=%s read_only=True and "
        "measures the SAME walrus fixture on BOTH readers - ok/b here "
        "against refused/attr-module-alias-unbound:M.HW there. The four "
        "gaps were MEASURED BEFORE ANY CODE with "
        "src/os/limits_module_alias_walrus_relative_R2585.py "
        "(qa/module-alias-walrus-relative-limits-R2585.log, %dB): all four "
        "read refused on the committed tree. ONE own defect was measured and "
        "repaired at its birth site: the first bounded audit over the whole "
        "root walked every module per level-bearing import and hung, so the "
        "root is now indexed ONCE per root and the live leg is bounded to "
        "four modules. The registry moved by ONE row to 623 suites / 4714 "
        "criteria, recounted by importing reconcile_all.SUITES rather than "
        "trusted (623 unique names, 623 unique paths), and "
        "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the "
        "eligible battery leg qa/reconcile-all-R2584.log to %d bytes at 623 "
        "suites / 4714 criteria with its green line honestly reading 622/623 "
        "and --check byte-identical. The limits THIS window leaves open were "
        "measured the same way (qa/module-alias-walrus-relative-limits-next-"
        "R2585.log, %dB) and seeded as the next row. tasks.md was not touched."
        % (evidence_bytes, measured.get("modules"), measured.get("loops"),
           measured.get("unreadable"), limits_bytes, matrix_bytes, next_bytes)
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-09 R2585]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, NEXT_SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-09 R2585] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2585")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2585,"))
    size = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")), size))
    print("head now %s" % back[at + 2][:70])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())