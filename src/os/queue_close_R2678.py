"""Close the AC-PNAH1 queue row at R2678 and seed ONE successor row.

Reads state/queue/tech.md, finds the single row carrying the AC-PNAH1 seed,
marks it done with a DISCHARGED note that keeps the original text, and inserts
ONE new seed row carrying AC-PNAJ1..AC-PNAJ6 measured in this window.
Writes atomically with a read-back and refuses on any ambiguity.

Dry run by default; --execute writes. Pure ASCII source, utf-8 data.
"""

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

MARK = "- [ ] P2 tech seed (R2675, from this window own measured limit):"

DONE_HEAD = "- [x] [done 2026-11-12 R2678] "

DISCHARGED = (
    " DISCHARGED R2678: shipped "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_"
    "while_match_while_else_nested_match_ordinal_unique_prefix_scope.py plus "
    "its six-criteria suite. Every label the R2675 face published is kept "
    "byte for byte and the reason now also carries an ACK INDEX: for each "
    "label, the SHORTEST prefix of that label naming exactly ONE label in the "
    "same reason. Measured on the closed three-binding fixture the prefixes "
    "read while2> for while2>case, while2_ for while2_body>case and while> "
    "for while>case, so the two bindings a bare `while2` ack used to confuse "
    "now carry different prefixes and no published prefix is a prefix of "
    "another; the coarse stems stay MEASURED as ambiguous (while2 names TWO "
    "labels, while names THREE) rather than hidden. The else pair reads "
    "while_else> and while_else2, the three parked refusals keep "
    "attr-module-alias-unbound:M.HW with no branch read and carry NO ack "
    "labels, and the three carried fixtures (module-level if branch, while "
    "else direct walrus, two matches in one while) answer exactly what R2675 "
    "answered. PROOF: AC-PNAH1..AC-PNAH6 SUITE PASS 6/6 twice byte-identical "
    "through the single-writer evidence face (qa/prefix-ack-R2678-a.log and "
    "-b.log, 2720 bytes each, sha16 9d107becacb0fe51, utf-8 LF, no BOM, no "
    "CRLF) with one bounded live leg reading 22 loops of one real module "
    "unchanged and read-only. Registry 655 suites / 4906 criteria -> 656 / "
    "4912 by exactly one row recounted by import. The R2168 mixed-tree rule "
    "now puts the FULL battery on the committed tree BEFORE the next product "
    "byte."
)

SEED = (
    "- [ ] P2 tech seed (R2678, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_"
    "while_match_while_else_nested_match_ordinal_unique_prefix_scope.py` - "
    "MEASURED this window before any successor byte: `ack_index(['x','xy'])` "
    "answers `{'x': None, 'xy': 'xy'}` and `ack_unmatched` names `['x']`, yet "
    "`prefix_free` reads True and the face therefore still publishes "
    "SEAMS-MATCH-ORDINAL-UNIQUE-PREFIX-COVERED - a label that is a STRICT "
    "PREFIX of a sibling label is unnameable (no prefix of `x` can be unique "
    "while `xy` exists) and `ack_index(['a','a'])` reads `{'a': None}` with "
    "`prefix_free` True as well, so a duplicated label hides the same way. A "
    "COVERED verdict beside a non-empty `ack_unmatched` is therefore a FALSE "
    "GREEN of exactly the kind this family exists to refuse. Product: ONE "
    "reading that never publishes COVERED while any label is unnameable, "
    "whose unnameable labels carry their OWN word and the measured reason "
    "(strict prefix of a sibling, or the same string twice), while every "
    "answer R2675 and R2678 pinned stays byte for byte. Criteria "
    "AC-PNAJ1..AC-PNAJ6 pinned HERE BEFORE any code: AC-PNAJ1 a reason whose "
    "labels are `x` and `xy` names `x` unnameable with its own word and NEVER "
    "reads COVERED; AC-PNAJ2 two copies of one label are named unnameable by "
    "their own reason word, not merged into one; AC-PNAJ3 the three-binding "
    "and else fixtures still publish the R2678 prefixes byte for byte; AC-"
    "PNAJ4 the three parked refusals keep attr-module-alias-unbound:M.HW with "
    "no branch read and no ack labels; AC-PNAJ5 every answer the "
    "R2585/R2588/R2590/R2592/R2594/R2675/R2678 suites pinned rides unchanged, "
    "proved on the same fixtures plus one bounded live leg; AC-PNAJ6 pure "
    "ASCII, stdlib only, no clock, zero network, own reconcile label and own "
    "suite."
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
        sys.stdout.write("E_QC2678_ROWS ambiguous hits=%d\n" % len(hits))
        return 2
    index = hits[0]
    original = lines[index]
    if "AC-PNAH1" not in original or "prefix-FREE" not in original:
        sys.stdout.write("E_QC2678_SHAPE the row is not the AC-PNAH1 seed\n")
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
    tmp = TECH + ".tmp-R2678"
    with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(payload)
    os.replace(tmp, TECH)
    back = read_text(TECH)
    if back != payload:
        sys.stdout.write("E_QC2678_READBACK the file does not read back\n")
        return 3
    check = back.split("\n")
    ok = (check[index] == new_line and check[index + 1] == SEED
          and len(check) == len(new_lines))
    sys.stdout.write("readback=%s\n" % ("ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
