"""R2624 board closeout for the AC-EDMH1 seed row at state/queue/tech.md:652.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose limits were MEASURED this window by
src/os/limits_matrix_reconcile_row_shape_next_R2624.py.

It refuses to write when the evidence is absent, not green, not twice, or when
the anchor row cannot be found exactly once.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa",
                        "suite-matrix-reconcile-row-shape-R2624.log")
LIMITS = os.path.join(REPO, "qa",
                      "limits-matrix-reconcile-row-shape-next-R2624.log")
BEFORE = os.path.join(REPO, "qa",
                      "limits-matrix-reconcile-row-shape-R2624.log")

SEED_HEAD = "- [ ] P2 tech seed (R2621,"
SEED_MARK = "table-aware row law"
DONE_PREFIX = "- [x] [done 2026-11-11 R2624]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2624, from this window own measured limit): "
    "`src/os/suite_matrix_reconcile.py` row-scan table membership - limits "
    "MEASURED this window with "
    "src/os/limits_matrix_reconcile_row_shape_next_R2624.py against private "
    "copies (qa/limits-matrix-reconcile-row-shape-next-R2624.log): (a) a "
    "malformed row whose FIRST CELL is not numeric still ENDS the table, so "
    "the count collapses to zero again (measured doc_rows 0 against a 643-row "
    "registry, delta -643) because the scan decides table membership by a "
    "digit in the first cell; (b) a malformed row as the LAST row of the table "
    "was measured delta -1 and (c) TWO adjacent malformed rows delta -2, so "
    "both are named as already correct rather than claimed as gaps. Product: "
    "ONE reading that decides table membership by the SEPARATOR row a header "
    "carries rather than by its first cell, so a malformed row is always one "
    "non-row and only a real header ends the table, while every R2624 answer "
    "survives. Criteria AC-EDMI1..AC-EDMI6 pinned HERE BEFORE any code: "
    "AC-EDMI1 a malformed row whose FIRST CELL is not numeric is skipped as "
    "one non-row and every well-formed row after it is still counted, so the "
    "count falls by one rather than to zero; AC-EDMI2 a genuine header of a "
    "SECOND table still ENDS the first table, decided by the separator row "
    "that follows it, and the AC-EDMG1 fixture reads exactly as it does "
    "today; AC-EDMI3 the footer/total row after the last data row is still not "
    "counted and does not change the count; AC-EDMI4 the shipped check face is "
    "still asked exactly once per reading and a content difference keeps its "
    "content word; AC-EDMI5 every R2624 answer survives beside the new ones "
    "(numeric malformed row -1, two adjacent -2, genuine header 0, separator "
    "inside 0, quoted row 0, unclosed fence named with its line, nested fence "
    "named with both markers, same-header-one-table, other-header "
    "TITLE-REPEATED with the count, all shape words, both counts and the named "
    "evidence source) proved on the same fixtures; AC-EDMI6 pure ASCII, stdlib "
    "only, no clock, zero network, its own reconcile label and its own suite.")


def build_discharged(evidence_bytes, limits_bytes, before_bytes):
    return (
        " DISCHARGED R2624 (line 652, AC-EDMH1..AC-EDMH6 pinned there at R2621 "
        "BEFORE any code): the row scan of src/os/suite_matrix_reconcile.py "
        "now treats a data-shaped row whose CELL COUNT is wrong as ONE "
        "non-row. A pipe+digits+pipe row that does not carry six cells is "
        "skipped and every well-formed row after it is still counted, so one "
        "bad row undercounts by one instead of collapsing the count. The shape "
        "was MEASURED BEFORE any byte (qa/limits-matrix-reconcile-row-shape-"
        "R2624.log, %d bytes: a four-cell row and a seven-cell row both read "
        "doc_rows 0 against a 642-row registry, delta -642, ROWS-MISMATCH) and "
        "re-read inside the capture after the change (delta -1 in both cases, "
        "doc_rows 642 against the moved 643-row registry) while a genuine "
        "second-table header still ENDED the table (delta 0) and a separator "
        "row inside it still neither restarted nor ended it (delta 0, already "
        "correct and named as such rather than claimed as a gap). Proof: "
        "AC-EDMH1..AC-EDMH6 SUITE PASS 6/6 TWICE with identical criterion "
        "lines through the shipped capture callable (qa/suite-matrix-"
        "reconcile-row-shape-R2624.log, %d bytes, legs=2 identical=True "
        "adjacent=2 fails=0, digest 7B480522AEE30916) with the R2621 "
        "fence-table and the R2604 shape suites green beside it. REGISTRY "
        "642/4828 -> 643/4834 by exactly one row, recounted by import (643 "
        "unique names, 643 unique paths), and docs/sandbox-suite-matrix.md was "
        "regenerated through the shipped write face from that registry at the "
        "R2622 green leg to 65699 bytes / 643 rows, then read DOC-CURRENT at "
        "rc=0. ONE own defect was caught and repaired at its birth site rather "
        "than hidden: this suite first printed its criterion markers indented, "
        "so the shipped capture digested the EMPTY string (E3B0C44298FC1C14) "
        "and two legs would have looked identical for no reason; the markers "
        "were moved to column 0, the stale evidence deleted and the capture "
        "re-taken for the non-empty digest above. Three successor limits were "
        "MEASURED this window (qa/limits-matrix-reconcile-row-shape-next-"
        "R2624.log, %d bytes): a malformed row whose first cell is not numeric "
        "still zeroes the count (delta -643), while a malformed LAST row "
        "(delta -1) and two adjacent malformed rows (delta -2) are already "
        "correct."
        % (before_bytes, evidence_bytes, limits_bytes))


def main(argv):
    for path in (EVIDENCE, LIMITS, BEFORE):
        if not os.path.isfile(path):
            print("E_R2624_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True adjacent=2 fails=0" not in evidence:
        print("E_R2624_EVIDENCE_NOT_GREEN")
        return 4
    if "digest=E3B0C44298FC1C14" in evidence:
        print("E_R2624_EMPTY_DIGEST")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2624_EVIDENCE_NOT_TWICE")
        return 4
    limits = open(LIMITS, "rb").read().decode("utf-8")
    if "malformed_row_nonnumeric_first_cell" not in limits:
        print("E_R2624_LIMITS_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2624_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2624_ALREADY_DONE")
        return 4

    discharged = build_discharged(
        len(raw_evidence), len(open(LIMITS, "rb").read()),
        len(open(BEFORE, "rb").read()))
    lines[index] = DONE_PREFIX + row[len("- [ ]"):]
    lines.insert(index + 1, NEXT_SEED)
    lines.insert(index + 2, "  " + discharged)
    new_text = "\n".join(lines)
    execute = "--execute" in argv
    print("BOARD tech.md:%d -> done, seed inserted at %d, bytes %d -> %d, "
          "execute=%s" % (index + 1, index + 2, len(raw),
                          len(new_text.encode("utf-8")), execute))
    if not execute:
        return 0
    with open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(new_text)
    back = open(QUEUE, encoding="utf-8").read()
    ok = (DONE_PREFIX + row[len("- [ ]"):]) in back \
        and discharged in back and NEXT_SEED in back
    print("READBACK ok=%s bytes=%d" % (ok, len(back.encode("utf-8"))))
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
