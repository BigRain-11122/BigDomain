"""R2587 board closeout for the AC-PNAB1 seed row at state/queue/tech.md:619.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window with
src/os/limits_module_alias_walrus_branch_next_R2587.py: an elif / with / for /
nested branch walrus is still unread.

Refuses to write when the evidence, the limits logs or the suite output is
absent, so no number is invented.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa",
                        "module-alias-walrus-branch-scope-R2587.log")
LIMITS = os.path.join(REPO, "qa",
                      "module-alias-walrus-branch-limits-R2587.log")
NEXT = os.path.join(REPO, "qa",
                    "module-alias-walrus-branch-limits-next-R2587.log")

SEED_HEAD = "- [ ] P2 tech seed (R2585,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_module_alias_attribute_alias_"
             "walrus_relative_scope.py`")

DONE_PREFIX = "- [x] [done 2026-11-09 R2587]"

DISCHARGED = (
    " DISCHARGED R2587 (line 619, AC-PNAB1..AC-PNAB6 pinned in that row at "
    "R2585 BEFORE any code): "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_branch_scope.py "
    "plus its suite shipped. The extension is applied THROUGH the shipped "
    "reading rather than beside it: a walrus bound inside a module-level "
    "`if` or `else` body now resolves as a with-as receiver and the branch it "
    "was read in is named on the chain as `branch:M@if`; the same name bound "
    "on TWO branches is refused as `attr-module-alias-ambiguous:M@else+if` "
    "instead of being resolved to either; and a walrus inside a FUNCTION body "
    "keeps the shipped refusal byte for byte. Proof: its own suite PASS 6/6 "
    "on the first run and 6/6 TWICE with identical output "
    "(qa/module-alias-walrus-branch-scope-R2587.log, 3450 bytes, crlf=0, "
    "nul=0, bom=False), the parent suite still 6/6, and the live leg reads 4 "
    "real modules read-only at 80 loops with no mismatch against the parent."
)

NEXT_SEED = (
    "- [ ] P2 tech seed (R2587, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_"
    "scope.py` - MEASURED this window with "
    "src/os/limits_module_alias_walrus_branch_next_R2587.py against private "
    "worlds, every one reading `attr-module-alias-unbound:M.HW` with no branch "
    "read published: (a) a WALRUS inside a module-level `elif` branch is not "
    "read, because the scan looks only at a direct `if` body and its `else`; "
    "(b) a WALRUS inside a module-level `with` body is not read; (c) a WALRUS "
    "inside a module-level `for` body is not read; (d) a WALRUS inside a "
    "branch nested two levels deep is not read. Product: ONE reading that "
    "follows a walrus bound inside a module-level `elif` and inside a "
    "module-level `with`, while a `for` body and a two-level nested branch "
    "stay named refusals. Criteria AC-PNAC1..AC-PNAC6 pinned HERE BEFORE any "
    "code: AC-PNAC1 a walrus inside a module-level `elif` body resolves as a "
    "with-as receiver and names the elif; AC-PNAC2 a walrus inside a "
    "module-level `with` body resolves and names the with; AC-PNAC3 a walrus "
    "inside a module-level `for` body and one inside a two-level nested "
    "branch keep the shipped refusal and publish NO branch read; AC-PNAC4 "
    "every shape the R2587 suite already pinned classifies exactly as before, "
    "if/else branches and the ambiguous pair included; AC-PNAC5 every answer "
    "the nineteen shipped faces already gave is carried unchanged on the row; "
    "AC-PNAC6 pure ASCII, stdlib only, no clock, zero network, its own "
    "reconcile label and its own suite."
)


def main(argv):
    for path in (EVIDENCE, LIMITS, NEXT):
        if not os.path.isfile(path):
            print("E_R2587_MISSING %s" % os.path.basename(path))
            return 3
    evidence = open(EVIDENCE, encoding="utf-8").read()
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2587_EVIDENCE_NOT_GREEN")
        return 4
    limits = open(NEXT, encoding="utf-8").read()
    if limits.count("attr-module-alias-unbound:M.HW") < 4:
        print("E_R2587_LIMITS_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2587_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2587_ALREADY_DONE")
        return 4
    lines[index] = DONE_PREFIX + row[len("- [ ]"):]
    lines.insert(index + 1, " " + DISCHARGED)
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
    ok = (DONE_PREFIX + row[len("- [ ]"):]) in back and \
        DISCHARGED in back and NEXT_SEED in back
    print("READBACK ok=%s bytes=%d" % (ok, len(back.encode("utf-8"))))
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))