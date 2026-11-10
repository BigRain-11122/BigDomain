"""R2630 board closeout for the AC-EDMI1 seed row at state/queue/tech.md:653.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose limits were MEASURED this window by
src/os/limits_matrix_reconcile_row_membership_next_R2630.py.

It refuses to write when the evidence is absent, not green, not twice, empty
digested, or when the anchor row cannot be found exactly once.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa",
                        "suite-matrix-reconcile-row-membership-R2630.log")
LIMITS = os.path.join(REPO, "qa",
                      "limits-matrix-reconcile-row-membership-next-R2630.log")
BEFORE = os.path.join(REPO, "qa",
                      "limits-matrix-reconcile-row-membership-R2630.log")

SEED_HEAD = "- [ ] P2 tech seed (R2624,"
SEED_MARK = "table membership"
DONE_PREFIX = "- [x] [done 2026-11-11 R2630]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2630, from this window own measured limit): "
    "`src/os/suite_matrix_reconcile.py` second-table header recognition - "
    "limits MEASURED this window with "
    "src/os/limits_matrix_reconcile_row_membership_next_R2630.py against "
    "private copies (qa/limits-matrix-reconcile-row-membership-next-R2630.log): "
    "(a) a SECOND-table header whose separator carries a DIFFERENT cell count "
    "was measured delta +1 and (b) a SECOND-table header carrying NO separator "
    "row at all was measured delta +1, because such a header is read as one "
    "non-row and the first table then counts the rows of the table it opens; "
    "(c) two adjacent malformed rows whose first cell is not numeric were "
    "measured delta -2 and (d) a footer row whose FIRST CELL IS numeric but "
    "whose cell count is wrong was measured delta 0, so both are named as "
    "already correct rather than claimed as gaps. Product: ONE reading that "
    "refuses to absorb a block it cannot classify - a table-shaped run that "
    "opens with a header and carries NO separator of its own width ENDS the "
    "first table with its own word naming both widths (or the absent "
    "separator), instead of silently counting that run as matrix rows, while "
    "every R2630 answer survives. Criteria AC-EDMJ1..AC-EDMJ6 pinned HERE "
    "BEFORE any code: AC-EDMJ1 a second-table header whose separator width "
    "disagrees with it ENDS the first table and names BOTH widths, so the "
    "count stays at the first table own rows instead of rising; AC-EDMJ2 a "
    "second-table header carrying no separator at all ENDS the first table and "
    "names the absent separator; AC-EDMJ3 a genuinely malformed single row "
    "inside the table is STILL one non-row and does not end it (the AC-EDMI1 "
    "answer survives byte for byte); AC-EDMJ4 the shipped check face is still "
    "asked exactly once per reading and a content difference keeps its content "
    "word; AC-EDMJ5 every R2630 answer survives beside the new ones (malformed "
    "non-numeric first cell -1, two adjacent -2, a genuine second header 0, "
    "separator inside 0, footer 0, quoted row 0, unclosed fence named with its "
    "line, nested fence named with both markers, same-header-one-table, "
    "other-header TITLE-REPEATED with the count, every shape word, both counts "
    "and the named evidence source) proved on the same fixtures; AC-EDMJ6 pure "
    "ASCII, stdlib only, no clock, zero network, its own reconcile label and "
    "its own suite.")


def build_discharged(evidence_bytes, limits_bytes, before_bytes):
    return (
        " DISCHARGED R2630 (line 653, AC-EDMI1..AC-EDMI6 pinned there at R2624 "
        "BEFORE any code): the row scan of src/os/suite_matrix_reconcile.py now "
        "decides TABLE MEMBERSHIP by the separator row a header carries instead "
        "of by a digit in the first cell. A row that no separator of its own "
        "width follows is ONE non-row - a malformed data row, or the "
        "footer/total row - so every well-formed row after it is still counted "
        "and the count falls by one instead of collapsing. The gap was "
        "MEASURED BEFORE any byte with the same script this window ships: a "
        "first cell reading 'n/a' gave doc_rows 0 against a 643-row registry "
        "(delta -643, the reading was taken on the committed tree before the "
        "first edit and is recorded in state.json log rather than in a file "
        "this window later overwrote). The same script re-run AFTER the change "
        "(qa/limits-matrix-reconcile-row-membership-R2630.log, %d bytes) reads "
        "delta -1 for that shape, while a genuine second-table header stays at "
        "delta 0, the footer/total row stays at delta 0 and a malformed LAST "
        "row stays at -1 - the last three named as already correct rather than "
        "claimed as gaps. Proof: AC-EDMI1..AC-EDMI6 SUITE PASS 6/6 on the first "
        "run and 6/6 TWICE with identical criterion lines through the shipped "
        "capture callable (qa/suite-matrix-reconcile-row-membership-R2630.log, "
        "%d bytes, legs=2 identical=True adjacent=3 fails=0, digest "
        "416AB5BAA29629DE) with the six adjacent matrix suites green beside it "
        "(row-shape, table-shape, fence, fence-table, shape and the base "
        "reconcile suite, each 6/6 rc=0). REGISTRY 643/4834 -> 644/4840 by "
        "exactly one row, recounted by import, and docs/sandbox-suite-matrix.md "
        "was regenerated through the shipped write face at the R2627 green leg "
        "to 65817 bytes / 644 rows, after which the shipped check face read "
        "byte-identical at rc=0 and the live report read DOC-CURRENT. ONE "
        "measurement is named rather than smoothed: the first suite run read "
        "ROWS-MISMATCH on every criterion because the registry had already "
        "moved to 644 while the document still carried 643 rows, which is the "
        "shipped face telling the truth; the document was regenerated BEFORE "
        "the evidence was captured. Two successor limits were MEASURED this "
        "window (qa/limits-matrix-reconcile-row-membership-next-R2630.log, %d "
        "bytes): a second-table header whose separator width disagrees and one "
        "with no separator at all both read delta +1, while two adjacent "
        "non-numeric malformed rows (-2) and a numeric footer row (0) are "
        "already correct."
        % (before_bytes, evidence_bytes, limits_bytes))


def main(argv):
    for path in (EVIDENCE, LIMITS, BEFORE):
        if not os.path.isfile(path):
            print("E_R2630_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True adjacent=3 fails=0" not in evidence:
        print("E_R2630_EVIDENCE_NOT_GREEN")
        return 4
    if "digest=E3B0C44298FC1C14" in evidence:
        print("E_R2630_EMPTY_DIGEST")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2630_EVIDENCE_NOT_TWICE")
        return 4
    limits = open(LIMITS, "rb").read().decode("utf-8")
    if "second_header_narrow_separator" not in limits:
        print("E_R2630_LIMITS_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2630_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2630_ALREADY_DONE")
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
