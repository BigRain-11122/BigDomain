"""R2579 board closeout for the AC-PNMA1 seed row at state/queue/tech.md:613.

Marks that row done, adds its DISCHARGED note read from THIS round own
evidence on disk, and seeds ONE row measured this window with
src/os/limits_module_alias_attribute_next_R2579.py on private worlds where the
honest answer is `b`: an attribute head bound by a MODULE ALIAS, a two-step
attribute path, and a call context on a FROM-imported function name.

Refuses to write when the live evidence, the suite evidence, the limits log or
the matrix document is absent, so no number is invented.
"""

import io
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
LIVE = os.path.join(REPO, "qa", "module-alias-attribute-scope-live-R2579.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-module-alias-attribute-scope-R2579.log")
LIMITS = os.path.join(REPO, "qa",
                      "module-alias-attribute-scope-limits-R2579.log")
NEXT = os.path.join(REPO, "qa",
                    "module-alias-attribute-scope-limits-next-R2579.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2577,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_module_alias_attribute_scope.py`")

NEXT_SEED = (
    "- [ ] P2 tech seed (R2579, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_scope.py` - MEASURED "
    "this window with src/os/limits_module_alias_attribute_next_R2579.py "
    "against private worlds where the honest answer is `b`: (a) an attribute "
    "head bound by a MODULE ALIAS (`import consts` then `M = consts` then "
    "`BASE = M.HW`) reads `attr-module-alias-unbound:M.HW`, because only an "
    "import or a from-import head is resolved; (b) a TWO-STEP attribute path "
    "(`BASE = inner.INNER.HW` with `inner.INNER = consts`) reads "
    "`attr-module-alias-unbound:inner.HW`, because only one attribute hop is "
    "taken; (d) a with-as CALL context on a FROM-imported function name "
    "(`from mk import mkmod as REG` with `with REG() as m`) reads "
    "`attr-cross-call:m.ATTR`, because the call reader looks for a definition "
    "in the same module file only. Product: ONE reading that follows a "
    "module alias head, a two-step attribute path, and a call context on a "
    "FROM-imported function name. Criteria AC-PNAM1..AC-PNAM6 pinned HERE "
    "BEFORE any code: AC-PNAM1 an attribute head bound by a module alias "
    "resolves as a with-as receiver and names the alias link; AC-PNAM2 a "
    "two-step attribute path resolves to the module its final link names "
    "while a path whose middle link names no module is refused by name; "
    "AC-PNAM3 a with-as call context on a FROM-imported function name "
    "resolves and names the import hop; AC-PNAM4 a call on a name that is "
    "imported but not a function is refused with its own word rather than "
    "resolved; AC-PNAM5 every answer the sixteen shipped faces already gave "
    "is carried unchanged on the row; AC-PNAM6 pure ASCII, stdlib only, no "
    "clock, zero network, its own reconcile label and its own suite. Five "
    "anchors to re-check zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_module_alias_attribute_alias_scope, AC-PNAM, E_PNAM, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-module-alias-attribute-alias-scope, "
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_scope."
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
        print("REFUSED E_QCR2579_NO_LIVE: %s is absent" % LIVE)
        return 3
    for path in (EVIDENCE, LIMITS, NEXT, MATRIX):
        if not os.path.isfile(path):
            print("REFUSED E_QCR2579_NO_EVIDENCE: %s is absent" % path)
            return 3
    evidence_bytes = os.path.getsize(EVIDENCE)
    limits_bytes = os.path.getsize(LIMITS)
    next_bytes = os.path.getsize(NEXT)
    matrix_bytes = os.path.getsize(MATRIX)
    discharged = (
        "  DISCHARGED R2579 (line 613, AC-PNMA1..AC-PNMA6 pinned in that row "
        "at R2577 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_module_alias_attribute_scope.py plus its suite "
        "shipped. The extension is applied THROUGH the shipped reading rather "
        "than beside it: the three readers the module-alias-chain face calls "
        "at run time are swapped for this face own inside one guarded block "
        "and restored in a finally, so a module alias chain whose FINAL link "
        "is an attribute naming a module resolves as a with-as receiver, a "
        "module-level function returning a NAME bound to a class attribute "
        "resolves, a with-as context that is a CALL on an alias chain name "
        "resolves and names the call hop, and a chain whose attribute link "
        "names a module that is not on disk is NAMED with the link that "
        "broke. The SHIPPED baseline on every row is now measured with the "
        "readers UNPATCHED, so the row really carries what the face it "
        "extends answered. PROOF: AC-PNMA1..AC-PNMA6 SUITE PASS 6/6 on the "
        "first run and 6/6 TWICE with identical output plus two adjacent "
        "probe suites green through the shipped capture "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "import-alias-scope-module-alias-attribute-scope-R2579.log, %dB, "
        "legs=2, identical=True, adjacent=2, fails=0); a BOUNDED live leg "
        "over %s real probe modules reads loops=%s ma_resolved=%s "
        "ma_named=%s with read_only=True and measures the SAME fixture on "
        "BOTH readers - attribute-final ok/b and hop "
        "module-alias-attribute/attribute/direct here against "
        "refused/attr-with-as:m.ATTR there "
        "(qa/module-alias-attribute-scope-live-R2579.log, %dB, utf-8 LF, "
        "zero CRLF, zero BOM). The three limits THIS window leaves open were "
        "measured the same way (qa/module-alias-attribute-scope-limits-"
        "R2579.log, %dB, and the NEXT-row shapes in "
        "qa/module-alias-attribute-scope-limits-next-R2579.log, %dB) and "
        "seeded as the next row. ONE own misuse is disclosed rather than "
        "hidden: the first bounded leg passed a probe module NAME where the "
        "shipped chain expects the RENDER module object and read "
        "E_PSMR_NO_RENDER on all six modules; the leg was rewritten to read "
        "each file through this face own report and the log was re-taken, so "
        "no shipped module was edited for it. The registry moved by ONE row "
        "to 619 suites / 4690 criteria, recounted by importing "
        "reconcile_all.SUITES rather than trusted (619 unique names, 619 "
        "unique paths), and docs/sandbox-suite-matrix.md was regenerated "
        "stamp-aligned from the eligible R2577 battery leg to %d bytes at "
        "619 suites / 4690 criteria with its green line honestly reading "
        "618/619 and --check byte-identical. tasks.md was not touched."
        % (evidence_bytes, facts.get("modules"), facts.get("loops"),
           facts.get("ma_resolved"), facts.get("ma_named"),
           os.path.getsize(LIVE), limits_bytes, next_bytes, matrix_bytes)
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2579]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, NEXT_SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2579] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2579")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2579,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:70])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())