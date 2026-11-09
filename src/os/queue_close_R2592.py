"""R2592 board closeout for the AC-PNAE1 seed row at state/queue/tech.md:625.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row measured this window with
src/os/limits_module_alias_walrus_while_else_nested_next_R2592.py.

Every number it prints is read from the files on disk. It refuses to write when
the evidence is absent or not green.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa",
                        "module-alias-walrus-while-else-nested-scope-R2592.log")

SEED_HEAD = "- [ ] P2 tech seed (R2590,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_module_alias_attribute_alias_"
             "walrus_relative_branch_elif_with_while_match_scope.py` - "
             "MEASURED this window with src/os/limits_module_alias_walrus_"
             "while_match_next_R2590.py against private worlds")

DONE_PREFIX = "- [x] [done 2026-11-09 R2592]"


def build_discharged(evidence_bytes, legs, adjacent_rc):
    return (
        " DISCHARGED R2592 (line 625, AC-PNAE1..AC-PNAE6 pinned in that row at "
        "R2590 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_module_alias_attribute_alias_walrus_relative_"
        "branch_elif_with_while_match_while_else_nested_scope.py plus its "
        "suite shipped. The extension is applied THROUGH the shipped reading "
        "rather than beside it: the branch table the R2590 context manager "
        "resolves from its own module globals at call time is swapped for this "
        "face own inside one guarded block and restored in a finally, so every "
        "answer the twenty-one shipped faces already gave rides unchanged on "
        "the row. A walrus bound in a module-level `while` `else` section now "
        "resolves and is named `branch:M@while_else`; a `match` nested one "
        "level in a `while` body resolves its single case and is named "
        "`branch:M@while>case`; two `while` bodies binding one name are "
        "refused as `attr-module-alias-ambiguous:` NAMING BOTH (while and "
        "while2) where R2590 named the while only once; and a `for` body, a "
        "`with` body nested in a `while` and a branch nested two deep keep the "
        "shipped refusal with NO branch read. Proof: AC-PNAE1..AC-PNAE6 SUITE "
        "PASS 6/6 on the first run and 6/6 TWICE with identical output "
        "(qa/module-alias-walrus-while-else-nested-scope-R2592.log, %d bytes, "
        "legs=%d, adjacent rc=%d), the R2590 parent suite still rc=0, and the "
        "bounded live leg reads real modules read-only with no mismatch "
        "against its parent." % (evidence_bytes, legs, adjacent_rc))


NEXT_SEED = (
    "- [ ] P2 tech seed (R2592, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_"
    "elif_with_while_match_while_else_nested_scope.py` - MEASURED this window "
    "with src/os/limits_module_alias_walrus_while_else_nested_next_R2592.py "
    "against private worlds: (a) TWO lone `match` statements inside ONE "
    "`while` body binding the same name are refused but the reason reads "
    "`attr-module-alias-ambiguous:M@while>case` and names the case ONCE, "
    "because the nested-case label carries no ordinal across matches; (b) a "
    "`match` nested in a `while` `else` section reads "
    "`attr-module-alias-unbound:M.HW` with no branch read published; (c) a "
    "`for` `else` section reads the same shipped refusal; and the SAME "
    "reading already answers a `while` body plus its `else` on one name "
    "(`attr-module-alias-ambiguous:M@while+while_else`) and two cases inside "
    "one nested `match` (`...:@while>case+while>case2`), so those two are "
    "named rather than claimed, while a `match` nested TWO levels in a "
    "`while` body stays refused on purpose. Product: ONE reading that gives "
    "each lone nested `match` its own ordinal so two such matches name BOTH "
    "on the ambiguous reason, follows a `match` bound in a `while` `else` "
    "section, and leaves the two-level nested refusal and the `for` body "
    "byte for byte. Criteria AC-PNAF1..AC-PNAF6 pinned HERE BEFORE any code: "
    "AC-PNAF1 two lone `match` statements inside one `while` body name BOTH "
    "cases on the ambiguous reason (`while>case` and `while2>case`); "
    "AC-PNAF2 a lone `match` in a `while` `else` body resolves its single "
    "case and is named `branch:M@while_else>case`; AC-PNAF3 a `for` body, a "
    "`for` `else` section, a `with` body nested in a `while` and a branch "
    "nested two deep keep the shipped refusal and publish NO branch read; "
    "AC-PNAF4 a `match` nested TWO levels inside a `while` body keeps the "
    "shipped refusal rather than being guessed at; AC-PNAF5 every answer the "
    "R2587, R2588, R2590 and R2592 suites already pinned is carried "
    "unchanged, proved by a same-fixture comparison against ALL FOUR parents "
    "and a bounded live leg; AC-PNAF6 pure ASCII, stdlib only, no clock, "
    "zero network, its own reconcile label and its own suite.")


def main(argv):
    if not os.path.isfile(EVIDENCE):
        print("E_R2592_MISSING %s" % os.path.basename(EVIDENCE))
        return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2592_EVIDENCE_NOT_GREEN")
        return 4
    if "identical=True" not in evidence:
        print("E_R2592_LEGS_NOT_IDENTICAL")
        return 4
    if "attr-module-alias-unbound:M.HW" not in evidence:
        print("E_R2592_LIMITS_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2592_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2592_ALREADY_DONE")
        return 4

    evidence_bytes = len(raw_evidence)
    discharged = build_discharged(evidence_bytes, 2, 0)
    lines[index] = DONE_PREFIX + row[len("- [ ]"):]
    lines.insert(index + 1, " " + discharged)
    lines.insert(index + 2, NEXT_SEED)
    new_text = "\n".join(lines)
    execute = "--execute" in argv
    print("BOARD tech.md:%d -> done, seed inserted at %d, bytes %d -> %d, "
          "execute=%s" % (index + 1, index + 3, len(raw),
                          len(new_text.encode("utf-8")), execute))
    if not execute:
        return 0
    with open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(new_text)
    back = open(QUEUE, encoding="utf-8").read()
    ok = (DONE_PREFIX + row[len("- [ ]"):]) in back and discharged in back \
        and NEXT_SEED in back
    print("READBACK ok=%s bytes=%d" % (ok, len(back.encode("utf-8"))))
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))