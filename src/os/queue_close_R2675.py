"""Close the AC-PNAG1 queue row at R2675 and seed ONE successor row.

Reads state/queue/tech.md, finds the single row that carries the AC-PNAG1 seed
prefix, marks it done with a DISCHARGED note that keeps the original text, and
inserts ONE new seed row carrying AC-PNAH1..AC-PNAH6 measured in this window.
Writes atomically with a read-back and refuses on any ambiguity.

Dry run by default; --execute writes. Pure ASCII source, utf-8 data.
"""

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

MARK = "- [ ] P2 tech seed (R2594, from this window own measured limit):"

DONE_HEAD = "- [x] [done 2026-11-12 R2675] "

DISCHARGED = (
    " DISCHARGED R2675: shipped "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_"
    "while_match_while_else_nested_match_ordinal_unique_scope.py plus its "
    "six-criteria suite. The match ordinal is now unique ACROSS matches and "
    "whiles: the FIRST while keeps the shipped labels (while>case, "
    "while2>case) and every LATER while names its matches with its own prefix "
    "plus _body (while2_body>case), so one while with two matches plus a "
    "second while with one match names THREE distinct labels where the "
    "measured baseline named two; a while else section names its second match "
    "while_else2>case instead of the join artifact while_elsem2>case; a match "
    "in a for body nested in a while, a match in a while inside a while and "
    "an if nested in a match case keep the shipped "
    "attr-module-alias-unbound:M.HW refusal with NO branch read. Measured "
    "BEFORE any code with src/os/limits_module_alias_match_ordinal_unique_"
    "R2675.py (3 bindings -> 2 labels, else second label while_elsem2>case) "
    "and AFTER it (3 labels, while_else2>case). PROOF: AC-PNAG1..AC-PNAG6 "
    "SUITE PASS 6/6 twice through the shipped capture callable, every one of "
    "the five parents (R2585/R2588/R2590/R2592/R2594) asked on the same "
    "fixtures and carried on the row, and one bounded live leg on the real "
    "tree. Registry 654 suites / 4900 criteria -> 655 / 4906 by exactly one "
    "row recounted by import. The R2168 mixed-tree rule now puts the FULL "
    "battery on the committed tree BEFORE the next product byte."
)

SEED = (
    "- [ ] P2 tech seed (R2675, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_"
    "while_match_while_else_nested_match_ordinal_unique_scope.py` - MEASURED "
    "this window on the closed fixture (one while with two matches plus a "
    "second while with one match) that the three labels are `while>case`, "
    "`while2>case` and `while2_body>case`, so a PREFIX ack on `while2` matches "
    "TWO different bindings (2 hits) and a prefix ack on `while` matches all "
    "three: a caller that acks a binding by prefix cannot tell the first "
    "while own second match from the second while own first match. Product: "
    "ONE reading whose labels are prefix-FREE among themselves, so every "
    "prefix that names a binding matches exactly ONE label in the reason, "
    "while the labels the five parents pinned (while>case, while2>case, "
    "while_else>case, while_else2>case) stay byte for byte. Criteria "
    "AC-PNAH1..AC-PNAH6 pinned HERE BEFORE any code: AC-PNAH1 in a reason "
    "carrying N labels, every published label own prefix matches exactly ONE "
    "label; AC-PNAH2 the three-binding fixture still names three distinct "
    "bindings; AC-PNAH3 the else-section pair still reads while_else>case and "
    "while_else2>case; AC-PNAH4 the three parked refusals keep "
    "attr-module-alias-unbound:M.HW with no branch read; AC-PNAH5 every "
    "answer the R2585/R2588/R2590/R2592/R2594/R2675 suites pinned rides "
    "unchanged, proved on the same fixtures plus one bounded live leg; "
    "AC-PNAH6 pure ASCII, stdlib only, no clock, zero network, own reconcile "
    "label and own suite."
)


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def main(argv):
    execute = "--execute" in argv
    text = read_text(TECH)
    lines = text.split("\n")
    hits = [index for index, line in enumerate(lines) if line.startswith(MARK)]
    if len(hits) != 1:
        sys.stdout.write("E_QC2675_ROWS ambiguous hits=%d\n" % len(hits))
        return 2
    index = hits[0]
    original = lines[index]
    if "probe_seam_name_binding" not in original:
        sys.stdout.write("E_QC2675_SHAPE the row is not the AC-PNAG1 seed\n")
        return 2
    body = original[len("- [ ] "):]
    new_line = DONE_HEAD + body + DISCHARGED
    new_lines = list(lines)
    new_lines[index] = new_line
    new_lines.insert(index + 1, SEED)
    payload = "\n".join(new_lines)
    sys.stdout.write("row=%d before=%d after=%d lines=%d->%d\n"
                     % (index + 1, len(text.encode("utf-8")),
                        len(payload.encode("utf-8")), len(lines),
                        len(new_lines)))
    if not execute:
        sys.stdout.write("PLANNED (dry run, nothing written)\n")
        return 0
    tmp = TECH + ".tmp-R2675"
    with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(payload)
    os.replace(tmp, TECH)
    back = read_text(TECH)
    if back != payload:
        sys.stdout.write("E_QC2675_READBACK the file does not read back\n")
        return 3
    check = back.split("\n")
    ok = (check[index] == new_line and check[index + 1] == SEED
          and len(check) == len(new_lines))
    sys.stdout.write("readback=%s\n" % ("ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
