"""R2604 board closeout for the AC-EDMC1 seed row at state/queue/tech.md:636.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose four limits were MEASURED this
window by src/os/limits_suite_matrix_reconcile_shape_next_R2604.py
(qa/limits-matrix-reconcile-shape-next-R2604.log).

It refuses to write when the evidence is absent, not green, or when the
anchor row cannot be found exactly once.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa",
                        "suite-matrix-reconcile-table-shape-R2604.log")
LIMITS = os.path.join(REPO, "qa",
                      "limits-matrix-reconcile-shape-next-R2604.log")

SEED_HEAD = "- [ ] P2 tech seed (R2602,"
SEED_MARK = "FOUR limits MEASURED this window"
DONE_PREFIX = "- [x] [done 2026-11-10 R2604]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2604, from this window own measured limit): "
    "`src/os/suite_matrix_reconcile.py` - FOUR limits MEASURED this window "
    "with src/os/limits_suite_matrix_reconcile_shape_next_R2604.py against "
    "private copies (qa/limits-matrix-reconcile-shape-next-R2604.log): "
    "(a) a separator drawn with '=' characters reads separator=None, so the "
    "shape law never sees it and the run falls through to STALE-CONTENT, a "
    "content word for a broken separator; (b) a header with NO separator row "
    "at all is tolerated - the rows are counted and the run falls through to a "
    "content word, so an absent separator is never named; (c) `--ceiling 0` "
    "bounds the walk before a single candidate is read (measured decoded=0 "
    "bounded=True) and returns nothing, with no word saying the bound starved "
    "the reading; (d) a document carrying the matrix title TWICE reads only "
    "the first table (measured shape=(6, 6) from its own second table) and "
    "ignores the second in silence. Product: ONE reading that recognises a "
    "separator row drawn with any single repeated punctuation character, "
    "names a table whose separator row is ABSENT instead of falling through "
    "to content, refuses a ceiling that cannot read even one candidate rather "
    "than silently returning nothing, and names a document that carries the "
    "matrix title more than once instead of reading the first and dropping "
    "the rest. Criteria AC-EDMD1..AC-EDMD6 pinned HERE BEFORE any code: "
    "AC-EDMD1 a separator drawn with '=' (or any single repeated punctuation "
    "character) is read as the separator row and a width disagreement against "
    "the header refuses by HEADER-SHAPE naming BOTH widths; AC-EDMD2 a header "
    "carrying no separator row at all refuses with its own word naming the "
    "missing separator instead of falling through to a content word; "
    "AC-EDMD3 a ceiling below one candidate is refused by name rather than "
    "silently returning no leg, so a starved walk cannot look like an honest "
    "empty pile; AC-EDMD4 a document whose matrix title appears more than once "
    "refuses by name, naming the count, instead of reading the first table and "
    "ignoring the rest; AC-EDMD5 every R2604 answer survives beside the new "
    "ones (HEADER-SHAPE for separator width and for header width, "
    "TABLE-MISSING, the bounded walk, the named evidence source, all seven "
    "R2602 words, both counts, one verdict word on the CLI and the exit "
    "codes) proved on the same fixtures; AC-EDMD6 pure ASCII, stdlib only, "
    "no clock, zero network, its own reconcile label and its own suite.")


def build_discharged(evidence_bytes, limits_bytes):
    return (
        " DISCHARGED R2604 (line 636, AC-EDMC1..AC-EDMC6 pinned there at R2602 "
        "BEFORE any code): src/os/suite_matrix_reconcile.py now reads the "
        "matrix SHAPE as a shape - a separator row whose width disagrees with "
        "its own header refuses by HEADER-SHAPE naming BOTH widths instead of "
        "falling through to a content word; a document carrying no matrix "
        "table at all refuses with its own TABLE-MISSING word naming the "
        "missing table; the candidate walk is bounded by a DECLARED ceiling "
        "(WALK_CEILING, overridable with --ceiling), stops at it and says so; "
        "and a caller passing an explicit --evidence together with a --qa-dir "
        "is told which source answered and that the qa-dir was not used. Every "
        "R2602 answer survives on the same fixtures (all seven words, both "
        "counts, one verdict word on the CLI, the exit codes). Proof: "
        "AC-EDMC1..AC-EDMC6 SUITE PASS 6/6 TWICE identical through the shipped "
        "capture callable (qa/suite-matrix-reconcile-table-shape-R2604.log, "
        "%d bytes, legs=2 identical=True adjacent=2 fails=0), with the two "
        "R2602 sibling suites green beside it; a read-only live leg on the "
        "real tree read DOC-CURRENT at 637/637 rows and 4798 criteria "
        "(qa/suite-matrix-reconcile-table-shape-live-R2604.log). REGISTRY "
        "636/4792 -> 637/4798 recounted by import; "
        "docs/sandbox-suite-matrix.md was regenerated from the CURRENT "
        "registry through this face own --write at the recorded leg (65032 "
        "bytes, 637 rows) and --check then read DOC-CURRENT. Four successor "
        "limits were MEASURED this window "
        "(qa/limits-matrix-reconcile-shape-next-R2604.log, %d bytes, utf-8 "
        "LF)." % (evidence_bytes, limits_bytes))


def main(argv):
    if not os.path.isfile(EVIDENCE):
        print("E_R2604_MISSING %s" % os.path.basename(EVIDENCE))
        return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True adjacent=2 fails=0" not in evidence:
        print("E_R2604_EVIDENCE_NOT_GREEN")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2604_EVIDENCE_NOT_TWICE")
        return 4
    if not os.path.isfile(LIMITS):
        print("E_R2604_LIMITS_MISSING")
        return 3
    raw_limits = open(LIMITS, "rb").read()
    limits = raw_limits.decode("utf-8")
    for token in ("eq-separator", "no-separator", "ceiling-0", "title-twice"):
        if token not in limits:
            print("E_R2604_LIMITS_UNEXPECTED %s" % token)
            return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2604_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2604_ALREADY_DONE")
        return 4

    discharged = build_discharged(len(raw_evidence), len(raw_limits))
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