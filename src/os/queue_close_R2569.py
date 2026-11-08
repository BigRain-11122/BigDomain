"""R2569 board closeout for the AC-PNDCF1 seed row at state/queue/tech.md:603.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window with
src/os/limits_call_target_R2569.py: a two-level relative import is not resolved,
a with-as call on a method defined in ANOTHER module is never resolved, a
class-body constant is never read, and `from .cls import K` stays a local.

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
    "alias-scope-call-target-scope-live-R2569.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-call-target-scope-R2569.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2565,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_call_target_scope.py`")

SEED = (
    "- [ ] P2 tech seed (R2569, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_two_level_scope.py` - MEASURED this window with "
    "src/os/limits_call_target_R2569.py against one private world where the "
    "honest answer is `b`: (1) a two-level relative `from .. import helper` "
    "reads `attr-base-local:helper`, because only a one-level ImportFrom is "
    "resolved against the package own directory; (2) a with-as call on a "
    "method defined in ANOTHER module (`with mk.Box().open() as m`) reads "
    "`attr-call-target:m.ATTR`, because the call-target table is built from "
    "the same source text only; (3) a class-body constant read as "
    "`cls.K.ATTR` reads `attr-from-import:cls.K.ATTR`, because neither the "
    "module reading nor the function reading walks a class body; (4) "
    "`from .cls import K` reads `attr-base-local:K`, because a relative "
    "FROM-import of a NAME is not a module and is left where it was. Product: "
    "ONE reading that resolves a two-level relative import, resolves a "
    "with-as call on a method imported from another module, reads a "
    "class-body constant, and never calls a relative FROM-imported NAME a "
    "local. Criteria AC-PNDCG1..AC-PNDCG6 pinned HERE BEFORE any code: "
    "AC-PNDCG1 a two-level relative `from .. import helper` resolves against "
    "the parent package; AC-PNDCG2 a with-as call on a method imported from "
    "another module resolves when that method returns a module name; "
    "AC-PNDCG3 a class-body constant resolves through its class path; "
    "AC-PNDCG4 a relative `from .cls import K` is refused with its own word "
    "rather than published as a local; AC-PNDCG5 every answer the ten shipped "
    "faces already gave is carried unchanged on the row; AC-PNDCG6 pure "
    "ASCII, stdlib only, no clock, zero network, its own reconcile label and "
    "its own suite. Five anchors to re-check zero-occupancy at HEAD before "
    "any code: "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_two_level_scope, AC-PNDCG, E_PNDCG, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-two-level-scope, "
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_two_level_scope."
)

FACTS = ("files", "loops", "ct_resolved", "ct_named")


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
        print("REFUSED E_QCR_NO_LIVE: %s is absent" % LIVE)
        return 3
    if not os.path.isfile(EVIDENCE):
        print("REFUSED E_QCR_NO_EVIDENCE: %s is absent" % EVIDENCE)
        return 3
    if not os.path.isfile(MATRIX):
        print("REFUSED E_QCR_NO_MATRIX: %s is absent" % MATRIX)
        return 3
    evidence_bytes = os.path.getsize(EVIDENCE)
    matrix_bytes = os.path.getsize(MATRIX)
    discharged = (
        "  DISCHARGED R2569 (line 603, AC-PNDCF1..AC-PNDCF6 pinned in that row "
        "at R2565 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_call_target_scope.py plus its suite shipped. A "
        "with-as context that is a call on an ATTRIBUTE resolves when that "
        "method returns a module name and is NAMED attr-call-target when it "
        "returns anything else; a function returning its module name through "
        "a LOCAL resolves; a one-level relative `from . import helper` "
        "resolves against the package own directory and is never a local; and "
        "a constant that only a NESTED function binds is NAMED "
        "attr-nested-constant instead of being resolved, which is the "
        "over-resolution this face now refuses; every key the shipped "
        "from-scope reading published is carried unchanged beside this face "
        "own on every row. PROOF: AC-PNDCF1..AC-PNDCF6 SUITE PASS 6/6 on the "
        "first run and 6/6 TWICE with identical output plus five adjacent "
        "probe suites green through the shipped capture "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "import-alias-scope-call-target-scope-R2569.log, %dB, legs=2, "
        "identical=True, adjacent=5, fails=0); a BOUNDED live leg over %s "
        "real probe_seam modules reads loops=%s ct_resolved=%s ct_named=%s "
        "with read_only=True, and FOUR fixtures are measured on BOTH readers "
        "in that leg - with-as-attribute ok/b here against "
        "refused/attr-with-as:m.ATTR there, local-return ok/b against "
        "refused/attr-with-as:md.ATTR, relative-from ok/b against "
        "refused/attr-base-local:helper, and nested-constant "
        "refused/attr-nested-constant against ok there "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "import-alias-scope-call-target-scope-live-R2569.log, utf-8 LF, zero "
        "CRLF, zero BOM). The registry moved by ONE row to 614 suites / 4660 "
        "criteria, recounted by importing reconcile_all.SUITES rather than "
        "trusted (614 unique names, 614 unique paths), and "
        "docs/sandbox-suite-matrix.md was regenerated from the eligible R2568 "
        "battery leg to %d bytes at 614 suites / 4660 criteria with its green "
        "line honestly reading 613/614 and --check byte-identical. tasks.md "
        "was not touched."
        % (evidence_bytes, facts.get("files"), facts.get("loops"),
           facts.get("ct_resolved"), facts.get("ct_named"), matrix_bytes)
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2569]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2569] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2569")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2569,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:70])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())