"""Close the AC-PNAK1 queue row at R2682 and seed ONE successor row.

Reads state/queue/tech.md, finds the single row carrying the AC-PNAK1 seed,
marks it done with a DISCHARGED note that keeps the original text, and inserts
ONE new seed row carrying AC-PNAL1..AC-PNAL6 measured in this window.
Writes atomically with a read-back and refuses on any ambiguity.

Dry run by default; --execute writes. Pure ASCII source, utf-8 data.
"""

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

MARK = "- [ ] P2 tech seed (R2679, from this window own measured limit):"

DONE_HEAD = "- [x] [done 2026-11-13 R2682] "

DISCHARGED = (
    " DISCHARGED R2682: shipped "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_"
    "while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_"
    "siblings_scope.py plus its six-criteria suite. The strict-prefix word now "
    "carries EVERY sibling that makes a label unnameable, in published order, "
    "so a caller can count the bindings that outrank it: measured before any "
    "byte here, `ack_unnameable(['a','ab','ac','ad'])` answered "
    "`{'a': 'strict-prefix-of:ab'}` on the R2679 face and now answers "
    "`{'a': 'strict-prefix-of:ab,ac,ad'}`, a flipped fixture "
    "`['a','ac','ab']` answers `strict-prefix-of:ac,ab` (published order, not "
    "sorted), and `['a','a','ab','ac']` answers "
    "`strict-prefix-of:ab,ac+duplicate:2` so the count and the full sibling "
    "list both ride. Every earlier answer rides byte for byte: the "
    "single-sibling word stays `strict-prefix-of:xy` for ['x','xy'] exactly "
    "as R2679 published it, the three-binding prefixes stay while2>, while2_ "
    "and while>, the else pair stays while_else> and while_else2, and the "
    "three parked refusals keep attr-module-alias-unbound:M.HW with no branch "
    "read and no ack labels. PROOF: AC-PNAK1..AC-PNAK6 SUITE PASS 6/6 twice "
    "byte-identical through the single-writer evidence face "
    "(qa/prefix-unnameable-siblings-R2682.log) with one bounded live leg "
    "reading 22 loops of one real module unchanged and read-only. Registry "
    "657 suites / 4918 criteria -> 658 / 4924 by exactly one row recounted by "
    "import. NO successor battery is owed by this row: the product window "
    "that shipped it registered one on its own line."
)

SEED = (
    "- [ ] P2 tech seed (R2682, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_"
    "while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_"
    "siblings_scope.py` - MEASURED this window on the face it ships: the "
    "sibling list is joined with a bare `,` and that separator is never "
    "escaped, so `ack_unnameable(['a','ab,ac'])` answers exactly "
    "`{'a': 'strict-prefix-of:ab,ac'}` - the SAME word `['a','ab','ac']` "
    "answers - and a caller therefore cannot tell ONE sibling named `ab,ac` "
    "from TWO siblings `ab` and `ac`. A second measured shape is named but "
    "not claimed as the product: `['a','ab','ab']` reads "
    "`{'a': 'strict-prefix-of:ab', 'ab': 'duplicate:2'}`, identical to "
    "`['a','ab']` on the sibling word, so a sibling own multiplicity survives "
    "only in its own row and never beside the name. Product: ONE reading in "
    "which a sibling label carrying the list separator is escaped (or refused "
    "with its own word) so one sibling can never be read as two, while the "
    "two-sibling word and every answer R2675, R2678, R2679 and R2682 pinned "
    "stay byte for byte. Criteria AC-PNAL1..AC-PNAL6 pinned HERE BEFORE any "
    "code: AC-PNAL1 a single sibling label containing the list separator is "
    "named so that it can never be read as two siblings, and it is "
    "distinguishable from the two-sibling word; AC-PNAL2 the ordinary "
    "two-sibling word stays byte for byte what R2682 published "
    "(`strict-prefix-of:ab,ac` for ['a','ab','ac']); AC-PNAL3 the "
    "single-sibling word stays byte for byte what R2679 published "
    "(`strict-prefix-of:xy` for ['x','xy']); AC-PNAL4 the duplicate count "
    "keeps riding beside the sibling list and the covered word is still "
    "withheld whenever any label is unnameable; AC-PNAL5 every answer the "
    "R2585/R2588/R2590/R2592/R2594/R2675/R2678/R2679/R2682 suites pinned "
    "rides unchanged, proved on the same fixtures plus one bounded live leg; "
    "AC-PNAL6 pure ASCII, stdlib only, no clock, zero network, own reconcile "
    "label and own suite."
)


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def main(argv):
    execute = "--execute" in argv
    text = read_text(TECH)
    lines = text.split("\n")
    hits = [index for index, line in enumerate(lines)
            if line.startswith(MARK)]
    if len(hits) != 1:
        sys.stdout.write("E_QC2682_HITS %d rows carry the AC-PNAK1 seed\n"
                         % len(hits))
        return 2
    index = hits[0]
    original = lines[index]
    if "AC-PNAK1" not in original or "unnameable_scope.py" not in original:
        sys.stdout.write("E_QC2682_SHAPE the row is not the AC-PNAK1 seed\n")
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
    tmp = TECH + ".tmp-R2682"
    with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(payload)
    os.replace(tmp, TECH)
    back = read_text(TECH)
    if back != payload:
        sys.stdout.write("E_QC2682_READBACK the file does not read back\n")
        return 3
    check = back.split("\n")
    ok = (check[index] == new_line and check[index + 1] == SEED
          and len(check) == len(new_lines))
    sys.stdout.write("readback=%s\n" % ("ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
