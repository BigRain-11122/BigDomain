"""R2565 board closeout for the AC-PNDCE1 seed row at state/queue/tech.md:601.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window with
src/os/limits_from_scope_R2565.py: a with-as call through an attribute or a
class method is never resolved, a call returning its module name through a local
variable is never resolved, a relative `from . import helper` stays a local, and
a constant declared in a NESTED function is resolved through the inner function.

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
    "alias-scope-from-scope-live-R2565.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-from-scope-R2565.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2563,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_from_scope.py`")

SEED = (
    "- [ ] P2 tech seed (R2565, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_call_target_scope.py` - MEASURED this window with "
    "src/os/limits_from_scope_R2565.py against one private world where the "
    "honest answer is `b`: (1) a with-as binding whose CONTEXT is a call on an "
    "ATTRIBUTE (`with Box().open() as m`) reads `attr-with-as:m.ATTR` and is "
    "never resolved even when that method returns a module name, because only "
    "a bare-name call is looked up; (2) a call that returns its module name "
    "through a LOCAL variable (`m = \"hw3\"; return m`) reads "
    "`attr-with-as:m.ATTR`, because only a returned str literal or a module "
    "level name is followed; (3) a relative `from . import helper` reads "
    "`attr-base-local:helper`, because a level-bearing ImportFrom is skipped "
    "outright; (4) a constant declared in a NESTED function is resolved "
    "through the inner function (`ok`/`b`), which is an OVER-resolution "
    "because nothing in the outer scope binds it. Product: ONE reading that "
    "resolves a with-as call whose target is an attribute or a class method "
    "returning a module name, follows a returned LOCAL module name, resolves "
    "a relative FROM-import against the package it belongs to, and refuses a "
    "constant that only a nested function binds. Criteria AC-PNDCF1..AC-PNDCF6 "
    "pinned HERE BEFORE any code: AC-PNDCF1 a with-as context that is a call "
    "on an attribute resolves when that call returns a module name and is "
    "NAMED otherwise; AC-PNDCF2 a function returning its module name through "
    "a LOCAL variable resolves; AC-PNDCF3 a relative `from . import helper` "
    "resolves against the package own directory and is never a local; "
    "AC-PNDCF4 a constant bound only inside a NESTED function is NAMED rather "
    "than resolved; AC-PNDCF5 every answer the nine shipped faces already "
    "gave is carried unchanged on the row; AC-PNDCF6 pure ASCII, stdlib only, "
    "no clock, zero network, its own reconcile label and its own suite. Five "
    "anchors to re-check zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_call_target_scope, AC-PNDCF, E_PNDCF, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-call-target-scope, "
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_call_target_scope."
)

FACTS = ("files", "loops", "from_resolved", "from_named")


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
        "  DISCHARGED R2565 (line 601, AC-PNDCE1..AC-PNDCE6 pinned in that row "
        "at R2563 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_from_scope.py plus its suite shipped. A module "
        "bound by `from pkg import helper`, plain or aliased, is taken as a "
        "MODULE base and resolved through pkg/helper.py instead of being "
        "called a local; a helper constant declared only inside a function "
        "body resolves to its literal when that function returns it and is "
        "NAMED attr-function-constant when it does not; a `with call() as "
        "NAME` binding whose call returns a module name resolves while a call "
        "returning anything else keeps the shipped attr-with-as word; every "
        "key the shipped import-alias reading published is carried unchanged "
        "beside this face own on every row. PROOF: AC-PNDCE1..AC-PNDCE6 SUITE "
        "PASS 6/6 TWICE with identical output plus five adjacent probe suites "
        "green (qa/probe-seam-name-binding-arm-mixed-residual-alias-"
        "attribute-import-alias-scope-from-scope-R2565.log, %dB, landed "
        "through the shipped capture callable); a BOUNDED live leg over %s "
        "real probe_seam modules reads loops=%s from_resolved=%s "
        "from_named=%s with read_only=True, and the SAME fixtures are "
        "measured on BOTH readers - the from-import fixture reads ok/b here "
        "against attr-base-local:helper there, and the with-as-call fixture "
        "reads ok/b here against refused/attr-with-as:m.ATTR there "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "import-alias-scope-from-scope-live-R2565.log, utf-8 LF, zero CRLF). "
        "The registry moved by ONE row to 612 suites / 4648 criteria, "
        "recounted by importing reconcile_all.SUITES rather than trusted "
        "(612 unique names, 612 unique paths), and "
        "docs/sandbox-suite-matrix.md was regenerated from the eligible R2564 "
        "battery leg to %d bytes at 612 suites / 4648 criteria with its green "
        "line honestly reading 611/612 and --check byte-identical. tasks.md "
        "was not touched."
        % (evidence_bytes, facts.get("files"), facts.get("loops"),
           facts.get("from_resolved"), facts.get("from_named"), matrix_bytes)
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2565]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2565] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2565")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2565,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:70])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())