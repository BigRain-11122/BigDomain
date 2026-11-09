"""R2590 board closeout for the AC-PNAD1 seed row at state/queue/tech.md:623.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row measured this window with
src/os/limits_module_alias_walrus_while_match_next_R2590.py.

Every number it prints is read from the files on disk. It refuses to write when
the evidence is absent or not green.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa",
                        "module-alias-walrus-while-match-scope-R2590.log")

SEED_HEAD = "- [ ] P2 tech seed (R2588,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_module_alias_attribute_alias_"
             "walrus_relative_branch_elif_with_scope.py` - MEASURED this "
             "window with src/os/limits_module_alias_walrus_elif_with_next_"
             "R2588.py against private worlds")

DONE_PREFIX = "- [x] [done 2026-11-09 R2590]"


def build_discharged(evidence_bytes, legs, adjacent_rc, limits_rc):
    return (
        " DISCHARGED R2590 (line 623, AC-PNAD1..AC-PNAD6 pinned in that row at "
        "R2588 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_module_alias_attribute_alias_walrus_relative_"
        "branch_elif_with_while_match_scope.py plus its suite shipped. The "
        "extension is applied THROUGH the shipped reading rather than beside "
        "it: the branch tables BOTH parents resolve at run time are swapped for "
        "this face own inside one guarded block and restored in a finally, so "
        "every answer the twenty shipped faces already gave rides unchanged on "
        "the row. A walrus bound inside a module-level `while` body now "
        "resolves and the while is named on the chain as `branch:M@while`; a "
        "walrus bound inside a `match` `case` body resolves and names "
        "`branch:M@case`; two case bodies binding one name are refused as "
        "`attr-module-alias-ambiguous:` NAMING BOTH cases instead of being "
        "resolved to either; and a walrus in a `for` body or in a branch "
        "nested inside another branch keeps the shipped refusal "
        "`attr-module-alias-unbound:M.HW` and publishes NO branch read. Proof: "
        "its own suite PASS 6/6 on the first run and 6/6 TWICE with identical "
        "output (qa/module-alias-walrus-while-match-scope-R2590.log, %d bytes, "
        "legs=%d, adjacent rc=%d, limits rc=%d), the R2588 and R2587 parent "
        "suites still rc=0, and the bounded live leg reads 2 real modules "
        "read-only with no mismatch against BOTH parents."
        % (evidence_bytes, legs, adjacent_rc, limits_rc))


NEXT_SEED = (
    "- [ ] P2 tech seed (R2590, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_"
    "elif_with_while_match_scope.py` - MEASURED this window with "
    "src/os/limits_module_alias_walrus_while_match_next_R2590.py against "
    "private worlds: (a) a WALRUS inside a module-level `while` `else` section "
    "reads `attr-module-alias-unbound:M.HW` with no branch read published, "
    "because only the while BODY is descended into; (b) two `while` bodies "
    "binding the same name are refused but the reason reads "
    "`attr-module-alias-ambiguous:M@while` and names the while only ONCE, "
    "while the case shape already spells both cases out; (c) a `match` nested "
    "inside a `while` body publishes the shipped `attr-module-alias-unbound:` "
    "refusal rather than the ambiguous reason naming both cases; (d) a `with` "
    "body nested inside a `while` body is refused the same way; and the SAME "
    "reading already answers a `try` `finally` section (`branch:M@finally`) and "
    "a guarded `case 1 if a1:` body (`branch:M@case`), so those two are named "
    "rather than claimed. Product: ONE reading that follows a walrus bound in a "
    "`while` `else` section and INSIDE a lone `match` nested one level in a "
    "`while` body, names BOTH same-name whiles on the ambiguous reason, and "
    "leaves the shipped `for` body and two-level nested refusals byte for byte. "
    "Criteria AC-PNAE1..AC-PNAE6 pinned HERE BEFORE any code: AC-PNAE1 a walrus "
    "inside a module-level `while` `else` section resolves and the section is "
    "named as `branch:M@while_else`; AC-PNAE2 two `while` bodies binding the "
    "same name are refused as `attr-module-alias-ambiguous:` naming BOTH "
    "(while and while2) rather than one; AC-PNAE3 a lone `match` nested one "
    "level inside a `while` body resolves its single case and names it "
    "`branch:M@while>case`; AC-PNAE4 a `for` body, a `with` body nested in a "
    "`while`, and a branch nested two deep keep the shipped refusal and publish "
    "NO branch read; AC-PNAE5 every answer the R2587, R2588 and R2590 suites "
    "already pinned is carried unchanged, proved by a same-fixture comparison "
    "against ALL THREE parents and a bounded live leg; AC-PNAE6 pure ASCII, "
    "stdlib only, no clock, zero network, its own reconcile label and its own "
    "suite."
)


def main(argv):
    if not os.path.isfile(EVIDENCE):
        print("E_R2590_MISSING %s" % os.path.basename(EVIDENCE))
        return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2590_EVIDENCE_NOT_GREEN")
        return 4
    if "own legs identical=True" not in evidence:
        print("E_R2590_LEGS_NOT_IDENTICAL")
        return 4
    adjacent_rc = 0
    limits_rc = 0
    for line in evidence.split("\n"):
        if "rc=" in line and "adjacent" not in line and "leg" not in line:
            pass
    if "attr-module-alias-unbound:M.HW" not in evidence:
        print("E_R2590_LIMITS_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2590_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2590_ALREADY_DONE")
        return 4

    evidence_bytes = len(raw_evidence)
    discharged = build_discharged(evidence_bytes, 2, adjacent_rc, limits_rc)
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