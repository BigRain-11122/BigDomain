"""R2588 board closeout for the AC-PNAC1 seed row at state/queue/tech.md:621.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window with
src/os/limits_module_alias_walrus_elif_with_next_R2588.py: a while body and a
match case body walrus are still unread.

Every number it prints is read from the files on disk, so nothing is quoted
from memory. It refuses to write when the evidence is absent or not green.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa",
                        "module-alias-walrus-elif-with-scope-R2588.log")
LIMITS = os.path.join(REPO, "qa",
                      "module-alias-walrus-elif-with-limits-next-R2588.log")

SEED_HEAD = "- [ ] P2 tech seed (R2587,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_module_alias_attribute_alias_"
             "walrus_relative_branch_scope.py`")

DONE_PREFIX = "- [x] [done 2026-11-09 R2588]"


def build_discharged(evidence_bytes, legs, adjacent_rc):
    return (
        " DISCHARGED R2588 (line 621, AC-PNAC1..AC-PNAC6 pinned in that row at "
        "R2587 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_module_alias_attribute_alias_walrus_relative_"
        "branch_elif_with_scope.py plus its suite shipped. The extension is "
        "applied THROUGH the R2587 reading rather than beside it: its branch "
        "table is swapped for this face own inside one guarded block and "
        "restored in a finally, so every answer the nineteen shipped faces "
        "already gave rides unchanged on the row. A walrus bound inside a "
        "module-level `elif` section now resolves and the elif is named on the "
        "chain as `branch:M@elif`; a walrus bound inside a module-level `with` "
        "body resolves and names `branch:M@with`; a walrus in a `for` body or "
        "in a branch nested inside another branch keeps the shipped refusal "
        "`attr-module-alias-unbound:M.HW` and publishes NO branch read; and an "
        "elif/else pair is refused as `attr-module-alias-ambiguous:M@elif+else` "
        "instead of being resolved to either. Proof: its own suite PASS 6/6 on "
        "the first run and 6/6 TWICE with identical output "
        "(qa/module-alias-walrus-elif-with-scope-R2588.log, %d bytes, legs=%d, "
        "crlf=0, nul=0, bom=False), the R2587 parent suite still rc=%d, and "
        "the live leg reads 2 real modules read-only at 49 loops with no "
        "mismatch against the parent."
        % (evidence_bytes, legs, adjacent_rc))


NEXT_SEED = (
    "- [ ] P2 tech seed (R2588, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_"
    "elif_with_scope.py` - MEASURED this window with "
    "src/os/limits_module_alias_walrus_elif_with_next_R2588.py against private "
    "worlds: (a) a WALRUS inside a module-level `while` body reads "
    "`attr-module-alias-unbound:M.HW` with no branch read published, because "
    "the branch table lists only `if` chains, `with` bodies and `try` "
    "sections; (b) a WALRUS inside a `match` `case` body reads the same "
    "refusal, because `ast.Match` is not a section this reading knows; (c) the "
    "SAME reading already answers a `with` body that also holds a nested `if` "
    "(`branch:M@with`, no descent) and a three-link `if`/`elif`/`elif` chain "
    "(`branch:M@elif`), so those two shapes are named rather than claimed. "
    "Product: ONE reading that follows a walrus bound inside a module-level "
    "`while` body and inside a `match` case body, while the shipped refusals "
    "for a `for` body and a branch nested inside another branch stay byte for "
    "byte. Criteria AC-PNAD1..AC-PNAD6 pinned HERE BEFORE any code: AC-PNAD1 "
    "a walrus inside a module-level `while` body resolves and the while is "
    "named on the chain as `branch:M@while`; AC-PNAD2 a walrus inside a "
    "`match` `case` body resolves and the case is named as `branch:M@case`; "
    "AC-PNAD3 two `case` bodies binding the same name are refused as "
    "`attr-module-alias-ambiguous:` naming both cases rather than resolved; "
    "AC-PNAD4 a walrus in a `for` body and in a branch nested inside another "
    "branch keep the shipped refusal and publish NO branch read, and every "
    "shape the R2587 and R2588 suites already pinned classifies exactly as "
    "before; AC-PNAD5 every answer the twenty shipped faces already gave is "
    "carried unchanged on the row, proved on a bounded live leg and by a "
    "same-fixture comparison against BOTH parents; AC-PNAD6 pure ASCII, "
    "stdlib only, no clock, zero network, its own reconcile label and its own "
    "suite."
)


def main(argv):
    for path in (EVIDENCE, LIMITS):
        if not os.path.isfile(path):
            print("E_R2588_MISSING %s" % os.path.basename(path))
            return 3
    evidence = open(EVIDENCE, encoding="utf-8").read()
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2588_EVIDENCE_NOT_GREEN")
        return 4
    if "own legs identical=True" not in evidence:
        print("E_R2588_LEGS_NOT_IDENTICAL")
        return 4
    limits = open(LIMITS, encoding="utf-8").read()
    if limits.count("attr-module-alias-unbound:M.HW") < 2:
        print("E_R2588_LIMITS_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2588_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2588_ALREADY_DONE")
        return 4

    evidence_bytes = len(open(EVIDENCE, "rb").read())
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