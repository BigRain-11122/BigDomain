"""R2608 board closeout for the AC-EDME1 seed row at state/queue/tech.md:640.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose limits were MEASURED this window by
src/os/limits_matrix_reconcile_fence_next_R2608.py.

It refuses to write when the evidence is absent, not green, or when the
anchor row cannot be found exactly once.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa", "suite-matrix-reconcile-fence-R2608.log")
LIVE = os.path.join(REPO, "qa",
                    "suite-matrix-reconcile-fence-live-R2608.log")
LIMITS = os.path.join(REPO, "qa",
                      "limits-matrix-reconcile-fence-next-R2608.log")

SEED_HEAD = "- [ ] P2 tech seed (R2606,"
SEED_MARK = "FOUR limits MEASURED this window"
DONE_PREFIX = "- [x] [done 2026-11-10 R2608]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2608, from this window own measured limit): "
    "`src/os/suite_matrix_reconcile.py` - limits MEASURED this window with "
    "src/os/limits_matrix_reconcile_fence_next_R2608.py against private "
    "copies (qa/limits-matrix-reconcile-fence-next-R2608.log): (a) a data row "
    "INSIDE a fenced code block is still counted by the row law (measured "
    "doc_rows=640 against a 639-row registry -> ROWS-MISMATCH), because ROW_RE "
    "has no fence awareness, so a quoted example table changes the verdict; "
    "(b) two titles carrying the SAME header text, one WITH a separator row "
    "and one WITHOUT, count as TWO distinct tables (measured titles=2 -> "
    "TITLE-REPEATED), because the signature includes the separator width, so "
    "one table is split in two by a missing separator; (c) two bare titles "
    "introduce no table and read ONE title (measured titles=1) and (d) the "
    "write path over a starved walk reads CEILING-STARVED and changes no byte "
    "(measured written=False bytes_changed=False), so those two are named as "
    "already correct rather than claimed as gaps. Product: ONE reading whose "
    "row law is fence-aware (a quoted data row is named as quoted rather than "
    "counted as a table row) and whose table signature treats a separator-less "
    "repeat with the SAME header text as the same table instead of a second "
    "title. Criteria AC-EDMF1..AC-EDMF6 pinned HERE BEFORE any code: AC-EDMF1 "
    "data rows inside a fenced code block are not counted as matrix rows, and "
    "a document whose only row difference is inside a fence reads DOC-CURRENT "
    "rather than ROWS-MISMATCH; AC-EDMF2 a table whose separator row is absent "
    "but whose header text matches the first table is the SAME table, so a "
    "document repeating it in that shape does not read TITLE-REPEATED; "
    "AC-EDMF3 a table with a DIFFERENT header text still counts as a second "
    "table and still reads TITLE-REPEATED naming the count; AC-EDMF4 the "
    "shipped check face is still asked on every reading, so a document that "
    "differs in content rather than shape keeps its content word; AC-EDMF5 "
    "every R2608 answer survives beside the new ones (mixed-punctuation "
    "separator, fenced title, bare trailing title, starved and drained walks, "
    "all four shape words, both counts, the named evidence source, one verdict "
    "word on the CLI and the exit codes) proved on the same fixtures; "
    "AC-EDMF6 pure ASCII, stdlib only, no clock, zero network, its own "
    "reconcile label and its own suite.")


def build_discharged(evidence_bytes, live_bytes, limits_bytes):
    return (
        " DISCHARGED R2608 (line 640, AC-EDME1..AC-EDME6 pinned there at R2606 "
        "BEFORE any code): src/os/suite_matrix_reconcile.py now reads a "
        "SEPARATOR drawn with ANY mix of punctuation (so '-=-=' is a separator "
        "and a width disagreement still refuses by HEADER-SHAPE naming BOTH "
        "widths); counts only tables the shipped title introduces OUTSIDE "
        "fenced code blocks, so a quoted title reads the real table; treats a "
        "title that introduces no table as no title at all, so a bare trailing "
        "repeat is neither a second title nor a table; and gives a walk that "
        "reached its DECLARED ceiling its own CEILING-STARVED word naming the "
        "ceiling on the read, the write and the compose paths, while a pile "
        "whose every candidate was decoded keeps RED-LEG. Every R2606 answer "
        "survives on the same fixtures (both HEADER-SHAPE widths, "
        "TABLE-MISSING, the bounded walk block, the named evidence source, the "
        "R2602 words, both counts, one verdict word on the CLI, the exit "
        "codes). Proof: AC-EDME1..AC-EDME6 SUITE PASS 6/6 TWICE identical "
        "through the shipped capture callable "
        "(qa/suite-matrix-reconcile-fence-R2608.log, %d bytes, legs=2 "
        "identical=True adjacent=2 fails=0) with the R2606 shape suite and the "
        "R2601 reconciliation suite green beside it; a read-only live leg on "
        "the real tree read DOC-CURRENT at 639/639 rows and 4810 criteria "
        "(qa/suite-matrix-reconcile-fence-live-R2608.log, %d bytes). REGISTRY "
        "638/4804 -> 639/4810 recounted by import; "
        "docs/sandbox-suite-matrix.md was regenerated from the CURRENT "
        "registry through this face own --write at the R2607 green leg (65248 "
        "bytes, 639 rows) and --check then read byte-identical. TWO R2606 "
        "assertions were amended at their birth sites and that is disclosed "
        "rather than hidden: the row-drop fixture pinned one literal row "
        "INCLUDING its seconds, so it went inert on this window first restamp "
        "and now removes the first data row through the shipped row law, and "
        "the bounded-walk assertion moved from RED-LEG to CEILING-STARVED "
        "because AC-EDME4 renames exactly that state. Four successor limits "
        "were MEASURED this window "
        "(qa/limits-matrix-reconcile-fence-next-R2608.log, %d bytes, utf-8 "
        "LF)." % (evidence_bytes, live_bytes, limits_bytes))


def main(argv):
    for path in (EVIDENCE, LIVE, LIMITS):
        if not os.path.isfile(path):
            print("E_R2608_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True adjacent=2 fails=0" not in evidence:
        print("E_R2608_EVIDENCE_NOT_GREEN")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2608_EVIDENCE_NOT_TWICE")
        return 4
    raw_live = open(LIVE, "rb").read()
    if b"verdict=DOC-CURRENT" not in raw_live:
        print("E_R2608_LIVE_NOT_CURRENT")
        return 4
    raw_limits = open(LIMITS, "rb").read()
    limits = raw_limits.decode("utf-8")
    for token in ("fenced-data-row", "same-header-one-no-separator",
                  "two-bare-titles", "write-starved"):
        if token not in limits:
            print("E_R2608_LIMITS_UNEXPECTED %s" % token)
            return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2608_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2608_ALREADY_DONE")
        return 4

    discharged = build_discharged(len(raw_evidence), len(raw_live),
                                  len(raw_limits))
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
    print("READBACK ok=%s bytes=%d"
          % (ok, len(back.encode("utf-8"))))
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))