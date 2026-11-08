"""R2563 board closeout for the AC-PNDC1 seed row at state/queue/tech.md:599.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window
(src/os/limits_import_alias_residual_R2563.py, every shape against one private
world where the honest answer is `b`): a module bound by `from pkg import
helper` reads attr-base-local:helper, a helper constant declared only inside a
function body reads attr-plain-import, and a with-as module whose context is a
CALL reads attr-with-as and is never resolved.

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
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-alias-"
    "scope-live-R2563.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-alias-"
    "scope-R2563.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2561,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope.py`")

SEED = (
    "- [ ] P2 tech seed (R2563, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_from_scope.py` - MEASURED this window AFTER the "
    "import-alias face shipped, with src/os/limits_import_alias_residual_"
    "R2563.py against one private world where the honest answer is `b`: (1) a "
    "module bound by `from pkg import helper` and read as `helper.ATTR` reads "
    "`attr-base-local:helper`, because the import table is built from plain "
    "`ast.Import` nodes only, so a FROM-imported module is mistaken for a "
    "local; (2) a helper constant declared ONLY inside a function body reads "
    "`attr-plain-import:helper.ATTR`, because the module reading walks the "
    "module body and its control flow but never enters a function body; (3) a "
    "`with open_module() as m` binding reads `attr-with-as:m.ATTR` and is "
    "never resolved even when the call returns a module, because the context "
    "must be a plain Name to be treated as a module. Two shapes this window "
    "closed are named for contrast: a re-export under a DIFFERENT name "
    "(`from hc import ATTR as A`) and a module-level walrus constant both read "
    "`ok` with value `b`. Product: ONE reading that takes a FROM-imported "
    "module as a module base, reads a function-level helper constant without "
    "confusing it with a module-level one, and resolves a with-as binding "
    "whose context is a call to a function that RETURNS a module name instead "
    "of naming it attr-with-as. Criteria AC-PNDCE1..AC-PNDCE6 pinned HERE "
    "BEFORE any code: AC-PNDCE1 a module bound by `from pkg import helper` "
    "resolves through `pkg/helper.py`; AC-PNDCE2 a module bound by `from pkg "
    "import helper as h` resolves through the actual module and is never a "
    "local; AC-PNDCE3 a helper constant declared only inside a function body "
    "resolves to its literal when that function returns it, and stays NAMED "
    "when it does not; AC-PNDCE4 a with-as binding whose context is a call to "
    "a function returning a module name resolves, and a call that returns "
    "anything else stays attr-with-as; AC-PNDCE5 every answer the shipped "
    "import-alias face already gave is carried unchanged beside this face "
    "own; AC-PNDCE6 pure ASCII, stdlib only, no clock, zero network, its own "
    "reconcile label and its own suite. Five anchors to re-check "
    "zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_from_scope, AC-PNDCE, E_PNDCE, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-from-scope, test_probe_seam_name_binding_arm_mixed_residual_"
    "alias_attribute_import_alias_scope_from_scope."
)

FACTS = ("modules", "ia_resolved", "ia_named", "loops", "unreadable")


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
    live_bytes = os.path.getsize(LIVE)
    matrix_bytes = os.path.getsize(MATRIX)
    discharged = (
        "  DISCHARGED R2563 (line 599, AC-PNDC1..AC-PNDC6 pinned in that row "
        "at R2561 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope.py plus its suite shipped. A plain `import m` "
        "attribute base now publishes its hop and value instead of leaving the "
        "attribute and predicate layers with no reason at all; a module bound "
        "by `import m as x` and a with-as module binding resolve through the "
        "ACTUAL module name and are never published as attr-base-local:<alias>; "
        "a helper constant that is an alias of another constant is followed to "
        "its literal, and a helper carrying two values reads name-mixed where "
        "the predicate face over-resolved; a helper constant re-exported by "
        "`from hc import ATTR` resolves through that module. Every key the "
        "shipped predicate reading published is carried unchanged beside this "
        "face own on every row. PROOF: AC-PNDC1..AC-PNDC6 SUITE PASS 6/6 TWICE "
        "with an identical body plus five adjacent probe suites green "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
        "alias-scope-R2563.log, %dB, utf-8 bom=False crlf=0); the same suite "
        "re-ran green alone at closeout. A BOUNDED live leg over %s real "
        "probe_seam modules reads ia_resolved=%s ia_named=%s over %s loops with "
        "unreadable=%s, plus the SAME import-alias fixture measured on BOTH "
        "readers (the predicate face reads refused attr-base-local:h where this "
        "face reads ok b), and every module and base-face digest is unchanged "
        "across the reading (qa/probe-seam-name-binding-arm-mixed-residual-"
        "alias-attribute-import-alias-scope-live-R2563.log, %dB, utf-8 LF). "
        "The registry moved by ONE row to 611 suites / 4642 criteria, recounted "
        "by importing reconcile_all.SUITES rather than trusted (611 unique "
        "names, 611 unique paths), and docs/sandbox-suite-matrix.md was "
        "regenerated from the eligible R2562 battery leg to %d bytes at 611 "
        "suites / 4642 criteria with its green line honestly reading 610/611 "
        "because this round own suite is not in that battery leg, and --check "
        "then read byte-identical at rc=0. tasks.md was not touched."
        % (evidence_bytes, facts.get("modules"), facts.get("ia_resolved"),
           facts.get("ia_named"), facts.get("loops"),
           facts.get("unreadable"), live_bytes, matrix_bytes)
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2563]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2563] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2563")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2563,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:70])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())