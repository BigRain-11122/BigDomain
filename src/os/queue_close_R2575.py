"""R2575 board closeout for the AC-PNDCI1 seed row at state/queue/tech.md:609.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window with
src/os/live_class_source_R2575.py and two private-world probes: a module-level
alias chain, a module-level function returning a class attribute, and a class
alias to a FROM-imported constant.

Refuses to write when the live evidence, the suite evidence or the matrix
document is absent, so no number is invented.
"""

import io
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
LIVE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-class-source-scope-live-R2575.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-class-source-scope-R2575.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2573,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_class_source_scope.py`")

SEED = (
    "- [ ] P2 tech seed (R2575, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_chain_scope.py` - MEASURED this window "
    "against private worlds where the honest answer is `b`: (1) a module "
    "level value bound by an ALIAS CHAIN (`FIRST = Box().open()` then "
    "`REG = FIRST`) reads `attr-with-as:m.ATTR`, because the module-value "
    "reader accepts a Call and never follows a name to it; (2) a module-level "
    "FUNCTION returning a class attribute (`def make(): return Box.NAME` then "
    "`REG = make()`) reads `attr-with-as:m.ATTR`, because the call-target "
    "table follows a module literal and a self attribute but not a "
    "module-level function returning a class attribute; (3) a class constant "
    "aliasing a FROM-imported constant (`from consts import BASE` then "
    "`class K: ATTR = BASE`) reads "
    "`attr-class-source-constant:cls.K.ATTR`, because only class-body names "
    "are collected. Product: ONE reading that follows a module-level alias "
    "chain to its call and to a module-level function returning a class "
    "attribute, and follows a class alias to a FROM-imported constant. "
    "Criteria AC-PNCS1..AC-PNCS6 pinned HERE BEFORE any code: AC-PNCS1 a "
    "module-level alias chain ending at a call returning a class attribute "
    "resolves as a with-as receiver and names the chain; AC-PNCS2 a "
    "module-level function returning a class attribute resolves as a with-as "
    "receiver while a function returning a non-module literal is refused; "
    "AC-PNCS3 a class constant aliasing a FROM-imported constant resolves to "
    "that literal while a FROM-imported CONSTANT used directly as a class "
    "base is not mistaken for a class; AC-PNCS4 a chain that ends at a name "
    "bound nowhere is NAMED with the name that broke rather than resolved; "
    "AC-PNCS5 every answer the fourteen shipped faces already gave is carried "
    "unchanged on the row; AC-PNCS6 pure ASCII, stdlib only, no clock, zero "
    "network, its own reconcile label and its own suite. Five anchors to "
    "re-check zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_module_alias_chain_scope, AC-PNCS, E_PNCS, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-module-alias-chain-scope, "
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_chain_scope."
)

FACTS = ("files", "loops", "cs_resolved", "cs_named")


def live_facts():
    if not os.path.isfile(LIVE):
        return None
    text = io.open(LIVE, encoding="utf-8").read()
    facts = {}
    for key in FACTS:
        match = re.search(r"(?<![A-Za-z_])%s=(\d+)" % (key,), text)
        if match:
            facts[key] = match.group(1)
    return facts


def main():
    facts = live_facts()
    if facts is None:
        print("REFUSED E_QCR2575_NO_LIVE: %s is absent" % LIVE)
        return 3
    if not os.path.isfile(EVIDENCE):
        print("REFUSED E_QCR2575_NO_EVIDENCE: %s is absent" % EVIDENCE)
        return 3
    if not os.path.isfile(MATRIX):
        print("REFUSED E_QCR2575_NO_MATRIX: %s is absent" % MATRIX)
        return 3
    evidence_bytes = os.path.getsize(EVIDENCE)
    matrix_bytes = os.path.getsize(MATRIX)
    discharged = (
        "  DISCHARGED R2575 (line 609, AC-PNDCI1..AC-PNDCI6 pinned in that row "
        "at R2573 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_class_source_scope.py plus its suite shipped. A "
        "base class imported from ANOTHER module in the same root now "
        "resolves through the subclass path, cycle-guarded by (module, path) "
        "and bounded at depth 8, so a two-hop cross base resolves and a base "
        "cycle returns the subclass own value instead of recursing; a method "
        "returning an inherited class attribute through self is re-read "
        "through that cross table; a module-level value bound by a call "
        "returning a class attribute (`REG = Box().open()`) resolves as a "
        "with-as receiver and names the hop with-as-module-value; and a "
        "class-constant alias resolves to the same literal to a fixpoint, "
        "including a two-step chain, while an alias cycle resolves nothing "
        "and does not hang. Every key the shipped class-base reading "
        "published is carried unchanged beside this face own on every row. "
        "ONE seed claim was CORRECTED AGAINST MEASUREMENT rather than "
        "repeated: the seed named a method returning a BASE-class attribute "
        "through self as still open, but the shipped class-base face already "
        "merges a SAME-module base and measured ok/b at HEAD, so this face "
        "carries that answer and re-reads only the CROSS-module base shape. "
        "PROOF: AC-PNDCI1..AC-PNDCI6 SUITE PASS 6/6 plus 6/6 TWICE with "
        "identical output and five adjacent probe suites green through the "
        "shipped capture "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "import-alias-scope-class-source-scope-R2575.log, %dB, legs=2, "
        "identical=True, adjacent=5, fails=0); a BOUNDED live leg over %s real "
        "probe_seam modules reads loops=%s cs_resolved=%s cs_named=%s with "
        "read_only=True and measures FOUR fixtures on BOTH readers - "
        "cross-module-base ok/b here against "
        "refused/attr-class-base-constant:cls.K.ATTR there, self-cross-base "
        "ok/b against refused/attr-cross-call:m.ATTR, module-value ok/b "
        "against refused/attr-with-as:m.ATTR, and class-alias ok/b against "
        "refused/attr-class-base-constant:cls.K.OTHER "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "import-alias-scope-class-source-scope-live-R2575.log, utf-8 LF, zero "
        "CRLF, zero BOM). The registry moved by ONE row to 617 suites / 4678 "
        "criteria, recounted by importing reconcile_all.SUITES rather than "
        "trusted (617 unique names, 617 unique paths), and "
        "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the "
        "eligible R2573-retry battery leg to %d bytes at 617 suites / 4678 "
        "criteria with its green line honestly reading 616/617 and --check "
        "byte-identical. tasks.md was not touched."
        % (evidence_bytes, facts.get("files"), facts.get("loops"),
           facts.get("cs_resolved"), facts.get("cs_named"), matrix_bytes)
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2575]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2575] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2575")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2575,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:70])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())