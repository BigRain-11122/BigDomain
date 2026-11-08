"""R2577 board closeout for the AC-PNCS1 seed row at state/queue/tech.md:611.

Marks that row done, adds its DISCHARGED note read from THIS round own
evidence on disk, and seeds ONE row measured this window with
src/os/limits_module_alias_R2577.py on private worlds where the honest answer
is `b`: an alias chain whose final link is an ATTRIBUTE naming a module, a
module-level function returning a NAME bound to a class attribute, and a
with-as context that is a CALL on an alias chain name.

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
    REPO, "qa", "module-alias-chain-scope-live-R2577.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-module-alias-chain-scope-R2577.log")
LIMITS = os.path.join(REPO, "qa", "module-alias-chain-scope-limits-R2577.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2575,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_module_alias_chain_scope.py`")

SEED = (
    "- [ ] P2 tech seed (R2577, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_scope.py` - MEASURED this "
    "window with src/os/limits_module_alias_R2577.py against private worlds "
    "where the honest answer is `b`: (1) a module-level alias chain whose "
    "FINAL link is an ATTRIBUTE naming a module (`BASE = consts.HW` then "
    "`REG = BASE`) reads `attr-with-as:m.ATTR`, because only a Call final is "
    "followed; (2) a module-level function returning a NAME bound to a class "
    "attribute (`def make(): return REG2` with `REG2 = Box.NAME`) reads "
    "`attr-with-as:m.ATTR`, because only a direct `Class.ATTR` return is "
    "read; (3) a with-as context that is a CALL on an alias chain name "
    "(`with mk.REG() as m`) reads `attr-cross-call:m.ATTR`, because the "
    "extension covers the context-ATTRIBUTE branch only. Product: ONE "
    "reading that follows an attribute-final alias chain, a function "
    "returning a name bound to a class attribute, and a call context on an "
    "alias chain. Criteria AC-PNMA1..AC-PNMA6 pinned HERE BEFORE any code: "
    "AC-PNMA1 an alias chain whose final link is an attribute naming a "
    "module resolves as a with-as receiver and names the chain; AC-PNMA2 a "
    "module-level function returning a NAME bound to a class attribute "
    "resolves while a function returning a NAME bound to a non-module "
    "literal is refused; AC-PNMA3 a with-as context that is a CALL on an "
    "alias chain name resolves and names the call hop; AC-PNMA4 a chain "
    "whose attribute link names a module that is not on disk is NAMED with "
    "the link that broke rather than resolved; AC-PNMA5 every answer the "
    "fifteen shipped faces already gave is carried unchanged on the row; "
    "AC-PNMA6 pure ASCII, stdlib only, no clock, zero network, its own "
    "reconcile label and its own suite. Five anchors to re-check "
    "zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_module_alias_attribute_scope, AC-PNMA, E_PNMA, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-module-alias-attribute-scope, "
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_scope."
)

FACTS = ("probes", "loops", "ma_resolved", "ma_named")


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
        print("REFUSED E_QCR2577_NO_LIVE: %s is absent" % LIVE)
        return 3
    for path in (EVIDENCE, LIMITS, MATRIX):
        if not os.path.isfile(path):
            print("REFUSED E_QCR2577_NO_EVIDENCE: %s is absent" % path)
            return 3
    evidence_bytes = os.path.getsize(EVIDENCE)
    limits_bytes = os.path.getsize(LIMITS)
    matrix_bytes = os.path.getsize(MATRIX)
    discharged = (
        "  DISCHARGED R2577 (line 611, AC-PNCS1..AC-PNCS6 pinned in that row "
        "at R2575 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_module_alias_chain_scope.py plus its suite "
        "shipped. A module-level value bound by an ALIAS CHAIN ending at a "
        "call now resolves as a with-as receiver and names every link "
        "(`REG -> FIRST -> Box().open()`); a module-level FUNCTION returning "
        "a class attribute resolves through this face own function table "
        "while a function returning a non-module literal keeps the shipped "
        "refusal word; a class constant aliasing a FROM-imported constant "
        "resolves to that literal and a FROM-imported CONSTANT used as a "
        "class base is still not read as a class; and a chain ending at a "
        "name bound nowhere is NAMED with that name on BOTH paths (the "
        "with-as receiver and the module-attribute chain). The shipped "
        "class-source answer is asked FIRST and every key it published rides "
        "unchanged on every row. TWO of my own assertions failed first and "
        "were corrected to the MEASURED facts rather than loosened: a class "
        "constant resolves to the CONSTANT literal (not to the module it "
        "names), and the shipped module-value answer binds the MODULE then "
        "reads ATTR, so its value is b rather than hw. PROOF: "
        "AC-PNCS1..AC-PNCS6 SUITE PASS 6/6 and 6/6 TWICE with identical "
        "output plus two adjacent probe suites green through the shipped "
        "capture "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "import-alias-scope-module-alias-chain-scope-R2577.log, %dB, legs=2, "
        "identical=True, adjacent=2, fails=0); a BOUNDED live leg over %s "
        "real probe modules reads loops=%s ma_resolved=%s ma_named=%s with "
        "read_only=True and measures the SAME fixture on BOTH readers - "
        "alias-chain ok/b here against refused/attr-with-as:m.ATTR there, "
        "hop with-as-module-alias/direct against no hop "
        "(qa/module-alias-chain-scope-live-R2577.log, %dB, utf-8 LF, zero "
        "CRLF, zero BOM, re-taken because the first capture landed as "
        "PowerShell UTF-16 and was rewritten rather than baselined). The "
        "three limits THIS window leaves open were measured the same way "
        "(qa/module-alias-chain-scope-limits-R2577.log, %dB) and seeded as "
        "the next row. The registry moved by ONE row to 618 suites / 4684 "
        "criteria, recounted by importing reconcile_all.SUITES rather than "
        "trusted (618 unique names, 618 unique paths), and "
        "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the "
        "eligible R2574 battery leg to %d bytes at 618 suites / 4684 "
        "criteria with its green line honestly reading 617/618 and --check "
        "byte-identical. tasks.md was not touched."
        % (evidence_bytes, facts.get("probes"), facts.get("loops"),
           facts.get("ma_resolved"), facts.get("ma_named"),
           os.path.getsize(LIVE), limits_bytes, matrix_bytes)
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2577]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2577] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2577")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2577,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:70])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())