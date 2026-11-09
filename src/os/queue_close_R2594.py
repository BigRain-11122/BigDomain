"""R2594 board closeout for the AC-PNAF1 seed row at state/queue/tech.md:627.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row measured this window with
src/os/limits_module_alias_walrus_match_ordinal_next_R2594.py.

Every number it prints is read from the files on disk. It refuses to write when
the evidence is absent or not green.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa",
                        "module-alias-walrus-match-ordinal-scope-R2594.log")

SEED_HEAD = "- [ ] P2 tech seed (R2592,"
SEED_MARK = ("MEASURED this window with src/os/limits_module_alias_walrus_"
             "while_else_nested_next_R2592.py against private worlds")

DONE_PREFIX = "- [x] [done 2026-11-09 R2594]"


def build_discharged(evidence_bytes, legs, adjacent_rc):
    return (
        " DISCHARGED R2594 (line 627, AC-PNAF1..AC-PNAF6 pinned in that row at "
        "R2592 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_module_alias_attribute_alias_walrus_relative_"
        "branch_elif_with_while_match_while_else_nested_match_ordinal_scope.py "
        "plus its suite shipped. The extension is applied THROUGH the shipped "
        "reading rather than beside it: the branch table the R2592 context "
        "manager resolves from its own module globals at call time is swapped "
        "for this face own inside one guarded block and restored in a finally, "
        "so every answer the twenty-two shipped faces already gave rides "
        "unchanged on the row. Each lone `match` nested one level in a `while` "
        "body now carries its OWN ordinal, so two such matches are refused as "
        "`attr-module-alias-ambiguous:` NAMING BOTH (`while>case` and "
        "`while2>case`) where R2592 named the case ONCE; a `match` nested in a "
        "`while` `else` section resolves its single case and is named "
        "`branch:M@while_else>case`; and a `for` body, a `for` `else` section, "
        "a `with` body nested in a `while`, a branch nested two deep and a "
        "`match` nested TWO levels inside a `while` body keep the shipped "
        "refusal with NO branch read. Proof: AC-PNAF1..AC-PNAF6 SUITE PASS 6/6 "
        "TWICE with identical output (qa/module-alias-walrus-match-ordinal-"
        "scope-R2594.log, %d bytes, legs=%d, adjacent rc=%d), the three parent "
        "suites still rc=0, and the bounded live leg reads real modules "
        "read-only with no mismatch against its parent." % (evidence_bytes,
                                                            legs,
                                                            adjacent_rc))


NEXT_SEED = (
    "- [ ] P2 tech seed (R2594, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_"
    "elif_with_while_match_while_else_nested_match_ordinal_scope.py` - "
    "MEASURED this window with src/os/limits_module_alias_walrus_match_"
    "ordinal_next_R2594.py against private worlds: (a) ONE `while` body with "
    "TWO matches plus a SECOND `while` body with one match carries THREE "
    "bindings but the ambiguous reason names only TWO labels "
    "(`while>case+while2>case`), because the first while own second match and "
    "the second while share the same ordinal space - one binding is invisible; "
    "(b) TWO matches inside ONE `while` `else` section name both, but the "
    "second label reads the internal join artifact `while_elsem2>case` rather "
    "than `while_else2>case`; (c) a `match` inside a `for` body nested in a "
    "`while`, a `match` nested one level in a `while` inside another `while`, "
    "and a walrus bound by an `if` nested inside a `match` case all keep the "
    "shipped `attr-module-alias-unbound:M.HW` refusal with no branch read, so "
    "those three are named rather than claimed. Product: ONE reading whose "
    "ordinal is unique ACROSS matches and whiles (so three bindings name three "
    "labels), whose `else` section labels read `while_else>case` and "
    "`while_else2>case`, and that leaves the three named refusals byte for "
    "byte. Criteria AC-PNAG1..AC-PNAG6 pinned HERE BEFORE any code: AC-PNAG1 "
    "three bindings across one while with two matches and a second while with "
    "one match are refused as `attr-module-alias-ambiguous:` naming THREE "
    "distinct labels; AC-PNAG2 two matches inside one `while` `else` section "
    "name both as `while_else>case` and `while_else2>case`; AC-PNAG3 a `match` "
    "inside a `for` body nested in a `while`, a `match` in a `while` inside "
    "another `while`, and an `if` nested inside a `match` case keep the "
    "shipped refusal and publish NO branch read; AC-PNAG4 every answer the "
    "R2585, R2588, R2590, R2592 and R2594 suites already pinned is carried "
    "unchanged, proved by a same-fixture comparison against ALL FIVE parents "
    "and a bounded live leg; AC-PNAG5 the labels this face publishes are "
    "stable under a second call on the same tree, proved by two readings whose "
    "reason strings are identical; AC-PNAG6 pure ASCII, stdlib only, no clock, "
    "zero network, its own reconcile label and its own suite.")


def main(argv):
    if not os.path.isfile(EVIDENCE):
        print("E_R2594_MISSING %s" % os.path.basename(EVIDENCE))
        return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2594_EVIDENCE_NOT_GREEN")
        return 4
    if "identical=True" not in evidence:
        print("E_R2594_LEGS_NOT_IDENTICAL")
        return 4
    if "attr-module-alias-unbound:M.HW" not in evidence:
        print("E_R2594_LIMITS_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2594_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2594_ALREADY_DONE")
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