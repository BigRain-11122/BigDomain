"""R2621 board closeout for the AC-EDMG1 seed row at state/queue/tech.md:650.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose limits were MEASURED this window by
src/os/limits_matrix_reconcile_fence_table_next_R2621.py.

It refuses to write when the evidence is absent, not green, or when the anchor
row cannot be found exactly once.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa",
                        "suite-matrix-reconcile-fence-table-R2621.log")
LIMITS = os.path.join(REPO, "qa",
                      "limits-matrix-reconcile-fence-table-next-R2621.log")
BEFORE = os.path.join(REPO, "qa",
                      "limits-matrix-reconcile-fence-table-R2621.log")

SEED_HEAD = "- [ ] P2 tech seed (R2616,"
SEED_MARK = "fence and table-rowed law"
DONE_PREFIX = "- [x] [done 2026-11-11 R2621]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2621, from this window own measured limit): "
    "`src/os/suite_matrix_reconcile.py` table-aware row law - limits MEASURED "
    "this window with src/os/limits_matrix_reconcile_fence_table_next_R2621.py "
    "against private copies (qa/limits-matrix-reconcile-fence-table-next-"
    "R2621.log): (a) ONE malformed data row inside the matrix table collapses "
    "the count to zero, because the scan breaks on the first row that is "
    "neither data nor separator as if it were another table header (measured "
    "doc_rows 0 against a 642-row registry, delta -642, verdict "
    "ROWS-MISMATCH) - the honest answer for one bad row is 641, not 0; (b) a "
    "TILDE fence was measured and is NOT a counting hole - the quoted row sits "
    "outside the table and reads delta 0 - so the tilde dialect is named as "
    "already safe rather than claimed; (c) a bare six-cell row appended after "
    "the LAST table was measured delta 0 for the same reason and is likewise "
    "named as already safe. Product: ONE reading whose row scan ends a table "
    "only on a real header shape or a non-table line, so a single malformed "
    "row undercounts by one instead of zeroing the count, while every R2621 "
    "answer survives. Criteria AC-EDMH1..AC-EDMH6 pinned HERE BEFORE any code: "
    "AC-EDMH1 a data-shaped row with the WRONG CELL COUNT inside the matrix "
    "table is skipped as one non-row and every well-formed row after it is "
    "still counted, so the count falls by one rather than to zero; AC-EDMH2 a "
    "genuine header of a SECOND table still ENDS the first table, so the "
    "AC-EDMG1 second-table law is unchanged and proved on the same fixture; "
    "AC-EDMH3 a separator row reappearing inside the table does not restart or "
    "end it; AC-EDMH4 the shipped check face is still asked exactly once per "
    "reading and a content difference keeps its content word; AC-EDMH5 every "
    "R2621 answer survives beside the new ones (second table not counted, "
    "unclosed fence named with its line, nested fence named with both markers, "
    "quoted row not counted, same-header-one-table, other-header "
    "TITLE-REPEATED with the count, all shape words, both counts and the named "
    "evidence source) proved on the same fixtures; AC-EDMH6 pure ASCII, stdlib "
    "only, no clock, zero network, its own reconcile label and its own suite.")


def build_discharged(evidence_bytes, limits_bytes, before_bytes):
    return (
        " DISCHARGED R2621 (line 650, AC-EDMG1..AC-EDMG6 pinned there at R2616 "
        "BEFORE any code): the row law of src/os/suite_matrix_reconcile.py is "
        "now TABLE-AWARE as well as fence-aware - only rows of the FIRST table "
        "introduced by the shipped matrix title are matrix rows, so a "
        "data-shaped row in a SECOND table (with or without a separator, with "
        "the same header text or a different one) is not counted and a "
        "document whose only row difference sits there reads the shipped "
        "check face own content word instead of ROWS-MISMATCH. The fence law "
        "names its own malformations: an opening mark that is never closed is "
        "refused as FENCE-UNCLOSED naming the LINE it was opened on, and a "
        "closing mark SHORTER than the mark that opened the block is refused "
        "as FENCE-NESTED naming BOTH widths, instead of toggling blind and "
        "counting a quoted row. A blank line inside the table is tolerated "
        "(the artefact of deleting a row) and a real second header ends the "
        "first table. Proof: AC-EDMG1..AC-EDMG6 SUITE PASS 6/6 TWICE identical "
        "through the shipped capture callable (qa/suite-matrix-reconcile-"
        "fence-table-R2621.log, %d bytes, legs=2 identical=True adjacent=2 "
        "fails=0) with the R2616 fence-rows parent and the R2608 fence suite "
        "green beside it; the three shapes were MEASURED BEFORE any code "
        "(qa/limits-matrix-reconcile-fence-table-R2621.log, %d bytes: second "
        "table delta 1 -> ROWS-MISMATCH, unclosed fence delta 0 unnamed, "
        "nested fence delta 1 -> ROWS-MISMATCH) and re-read after the change "
        "inside the capture (delta 0 everywhere, FENCE-UNCLOSED and "
        "FENCE-NESTED both named). REGISTRY 641/4822 -> 642/4828 recounted by "
        "import (642 unique names, 642 unique paths) and "
        "docs/sandbox-suite-matrix.md was regenerated through the shipped "
        "write face from that registry at the R2616 green leg to 65597 bytes / "
        "642 rows, then read DOC-CURRENT at rc=0. ONE R2621 own defect was "
        "caught by the R2616 parent suite on the first run and repaired in the "
        "CODE rather than by loosening the assertion: the first table scan "
        "ended on a blank line, so a doctored document that merely DELETED a "
        "row read zero rows. Three successor limits were MEASURED this window "
        "(qa/limits-matrix-reconcile-fence-table-next-R2621.log, %d bytes)."
        % (evidence_bytes, before_bytes, limits_bytes))


def main(argv):
    for path in (EVIDENCE, LIMITS, BEFORE):
        if not os.path.isfile(path):
            print("E_R2621_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True adjacent=2 fails=0" not in evidence:
        print("E_R2621_EVIDENCE_NOT_GREEN")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2621_EVIDENCE_NOT_TWICE")
        return 4
    limits = open(LIMITS, "rb").read().decode("utf-8")
    if "(c) seven-cell row:" not in limits:
        print("E_R2621_LIMITS_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2621_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2621_ALREADY_DONE")
        return 4

    discharged = build_discharged(
        len(raw_evidence), len(open(LIMITS, "rb").read()),
        len(open(BEFORE, "rb").read()))
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
    ok = (DONE_PREFIX + row[len("- [ ]"):]) in back \
        and discharged in back and NEXT_SEED in back
    print("READBACK ok=%s bytes=%d" % (ok, len(back.encode("utf-8"))))
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
