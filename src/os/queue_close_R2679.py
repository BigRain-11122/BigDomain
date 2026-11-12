"""Close the AC-PNAJ1 queue row at R2679 and seed ONE successor row.

Reads state/queue/tech.md, finds the single row carrying the AC-PNAJ1 seed,
marks it done with a DISCHARGED note that keeps the original text, and inserts
ONE new seed row carrying AC-PNAK1..AC-PNAK6 measured in this window.
Writes atomically with a read-back and refuses on any ambiguity.

Dry run by default; --execute writes. Pure ASCII source, utf-8 data.
"""

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

MARK = "- [ ] P2 tech seed (R2678, from this window own measured limit):"

DONE_HEAD = "- [x] [done 2026-11-12 R2679] "

DISCHARGED = (
    " DISCHARGED R2679: shipped "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_"
    "while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_"
    "scope.py plus its six-criteria suite. The covered word is now withheld "
    "whenever any label in the reason is unnameable, and each unnameable "
    "label carries its OWN word: `strict-prefix-of:<sibling>` for a label "
    "that is a strict prefix of a sibling (measured ['x','xy'] -> {'x': "
    "'strict-prefix-of:xy'}) and `duplicate:<n>` for one string published "
    "more than once (measured ['a','a'] -> {'a': 'duplicate:2'}), with both "
    "words joined by '+' when both apply. Both shapes were MEASURED on the "
    "R2678 face at R2679 BEFORE any byte here: each read ack_index with a "
    "None entry, a non-empty ack_unmatched, prefix_free True and therefore "
    "SEAMS-MATCH-ORDINAL-UNIQUE-PREFIX-COVERED, which is the exact false "
    "green this family exists to refuse. Every answer R2678 published rides "
    "byte for byte: the three-binding prefixes stay while2>, while2_ and "
    "while>, the else pair stays while_else> and while_else2, and the three "
    "parked refusals keep attr-module-alias-unbound:M.HW with no branch read "
    "and no ack labels. PROOF: AC-PNAJ1..AC-PNAJ6 SUITE PASS 6/6 twice "
    "byte-identical through the single-writer evidence face "
    "(qa/prefix-unnameable-R2679-a.log and -b.log, 3023 bytes each, sha16 "
    "ecc4f03b01e8b69d, utf-8 LF, no BOM, no CRLF, 37 PASS lines) with one "
    "bounded live leg reading 22 loops of one real module unchanged and "
    "read-only. Registry 656 suites / 4912 criteria -> 657 / 4918 by exactly "
    "one row recounted by import. The R2168 mixed-tree rule now puts the FULL "
    "battery on the committed tree BEFORE the next product byte."
)

SEED = (
    "- [ ] P2 tech seed (R2679, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_"
    "while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_"
    "scope.py` - MEASURED this window on the face it ships: "
    "`ack_unnameable(['a','ab','ac'])` answers `{'a': 'strict-prefix-of:ab'}` "
    "and therefore names ONE sibling where TWO siblings make `a` unnameable, "
    "so a caller cannot tell how many bindings outranked it from the word "
    "alone; a fatter shape reads "
    "`ack_unnameable(['a','a','ab'])` -> "
    "`{'a': 'strict-prefix-of:ab+duplicate:2'}` where the sibling list is "
    "again truncated to the first hit even though the count is kept. Product: "
    "ONE reading in which the strict-prefix word carries EVERY sibling that "
    "makes the label unnameable, in published order, while the duplicate word "
    "keeps its count and every answer R2675, R2678 and R2679 pinned stays "
    "byte for byte. Criteria AC-PNAK1..AC-PNAK6 pinned HERE BEFORE any code: "
    "AC-PNAK1 a label that is a strict prefix of TWO siblings names BOTH of "
    "them in its own word, in published order, not just the first; AC-PNAK2 "
    "the same label carrying two copies AND two siblings keeps both the "
    "duplicate count and the full sibling list; AC-PNAK3 the single-sibling "
    "word stays byte for byte what R2679 published "
    "(`strict-prefix-of:xy` for ['x','xy']); AC-PNAK4 every nameable label "
    "keeps a None reason and the covered word is still withheld whenever any "
    "label is unnameable; AC-PNAK5 every answer the R2585/R2588/R2590/R2592/"
    "R2594/R2675/R2678/R2679 suites pinned rides unchanged, proved on the "
    "same fixtures plus one bounded live leg; AC-PNAK6 pure ASCII, stdlib "
    "only, no clock, zero network, own reconcile label and own suite."
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
        sys.stdout.write("E_QC2679_HITS %d rows carry the AC-PNAJ1 seed\n"
                         % len(hits))
        return 2
    index = hits[0]
    original = lines[index]
    if "AC-PNAJ1" not in original or "unnameable" not in original:
        sys.stdout.write("E_QC2679_SHAPE the row is not the AC-PNAJ1 seed\n")
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
    tmp = TECH + ".tmp-R2679"
    with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(payload)
    os.replace(tmp, TECH)
    back = read_text(TECH)
    if back != payload:
        sys.stdout.write("E_QC2679_READBACK the file does not read back\n")
        return 3
    check = back.split("\n")
    ok = (check[index] == new_line and check[index + 1] == SEED
          and len(check) == len(new_lines))
    sys.stdout.write("readback=%s\n" % ("ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
