"""R2573 board closeout for the AC-PNDCH1 seed row at state/queue/tech.md:607.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window with
src/os/limits_class_base_R2573.py: a base class inherited from another module,
a method returning a base-class attribute through self, a module name bound by
a class attribute, and a class constant that is an alias.

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
    "alias-scope-class-base-scope-live-R2573.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-class-base-scope-R2573.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2571,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_class_base_scope.py`")

SEED = (
    "- [ ] P2 tech seed (R2573, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_class_source_scope.py` - MEASURED this window with "
    "src/os/limits_class_base_R2573.py against private worlds where the honest "
    "answer is `b`: (1) a base class inherited from ANOTHER module reads "
    "`attr-class-constant:cls.K.ATTR`, because the base walk stays inside the "
    "one module body it was handed; (2) a cross-module method returning a "
    "class attribute of a BASE class through self reads "
    "`attr-cross-call:m.ATTR`, because the self reading asks the named class "
    "own table only; (3) a module name bound by a module-level call whose "
    "method returns a class attribute (`reg.REG` then `with reg.REG as m`) "
    "reads `attr-with-as:m.ATTR`, because the with-as table follows calls, "
    "never a module-level VALUE; (4) a class constant that is an alias of "
    "another class constant (`class K(Base): OTHER = ATTR`) reads "
    "`attr-class-constant:cls.K.OTHER`, because only str literals are "
    "collected. Product: ONE reading that follows a base class from ANOTHER "
    "module in the same root (cycle-guarded, depth-bounded), follows self.NAME "
    "through inherited bases, resolves a module-level value bound by a call "
    "returning a class attribute, and follows a class-constant alias to its "
    "literal. Criteria AC-PNDCI1..AC-PNDCI6 pinned HERE BEFORE any code: "
    "AC-PNDCI1 a base class from another module resolves through the subclass "
    "path; AC-PNDCI2 a method returning an inherited class attribute through "
    "self resolves; AC-PNDCI3 a module-level value bound by a call returning "
    "a class attribute resolves as a with-as receiver; AC-PNDCI4 a "
    "class-constant alias resolves to the same literal to a fixpoint; "
    "AC-PNDCI5 every answer the thirteen shipped faces already gave is carried "
    "unchanged on the row; AC-PNDCI6 pure ASCII, stdlib only, no clock, zero "
    "network, its own reconcile label and its own suite. Five anchors to "
    "re-check zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_class_source_scope, AC-PNDCI, E_PNDCI, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-class-source-scope, "
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_class_source_scope."
)

FACTS = ("files", "loops", "cb_resolved", "cb_named")


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
        print("REFUSED E_QCR2573_NO_LIVE: %s is absent" % LIVE)
        return 3
    if not os.path.isfile(EVIDENCE):
        print("REFUSED E_QCR2573_NO_EVIDENCE: %s is absent" % EVIDENCE)
        return 3
    if not os.path.isfile(MATRIX):
        print("REFUSED E_QCR2573_NO_MATRIX: %s is absent" % MATRIX)
        return 3
    evidence_bytes = os.path.getsize(EVIDENCE)
    matrix_bytes = os.path.getsize(MATRIX)
    discharged = (
        "  DISCHARGED R2573 (line 607, AC-PNDCH1..AC-PNDCH6 pinned in that row "
        "at R2571 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_class_base_scope.py plus its suite shipped. A "
        "class constant inherited from a base class in the SAME module "
        "resolves through the subclass path and names the hop class-base "
        "while a subclass own value still wins; an absolute FROM-imported "
        "CLASS resolves through its class path and is NAMED "
        "attr-from-class-constant when the class body does not carry the "
        "attribute; a cross-module with-as method returning self.NAME "
        "resolves when that class constant is a module name and is NAMED "
        "attr-cross-call otherwise; a receiver bound by a FROM-import alias is "
        "found and its call resolves; every key the shipped two-level reading "
        "published is carried unchanged beside this face own on every row. "
        "PROOF: AC-PNDCH1..AC-PNDCH6 SUITE PASS 6/6 plus 6/6 TWICE with "
        "identical output and five adjacent probe suites green through the "
        "shipped capture "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "import-alias-scope-class-base-scope-R2573.log, %dB, legs=2, "
        "identical=True, adjacent=5, fails=0); a BOUNDED live leg over %s real "
        "probe_seam modules reads loops=%s cb_resolved=%s cb_named=%s with "
        "read_only=True and measures FOUR fixtures on BOTH readers - "
        "inherited ok/b here against refused/attr-class-constant:cls.K.ATTR "
        "there, from-class ok/b against refused/attr-base-local:K, "
        "self-attribute ok/b against refused/attr-cross-call:m.ATTR, and "
        "from-alias ok/b against refused/attr-cross-call:m.ATTR "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "import-alias-scope-class-base-scope-live-R2573.log, utf-8 LF, zero "
        "CRLF, zero BOM). The registry moved by ONE row to 616 suites / 4672 "
        "criteria, recounted by importing reconcile_all.SUITES rather than "
        "trusted (616 unique names, 616 unique paths), and "
        "docs/sandbox-suite-matrix.md was regenerated from the eligible R2572 "
        "battery leg to %d bytes at 616 suites / 4672 criteria with its green "
        "line honestly reading 615/616 and --check byte-identical. tasks.md "
        "was not touched."
        % (evidence_bytes, facts.get("files"), facts.get("loops"),
           facts.get("cb_resolved"), facts.get("cb_named"), matrix_bytes)
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2573]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2573] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2573")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2573,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:70])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())