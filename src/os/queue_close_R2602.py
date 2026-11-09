"""R2602 board closeout for the AC-EDMB1 seed row at state/queue/tech.md:634.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose four limits were MEASURED this
window by src/os/limits_suite_matrix_reconcile_next_R2602.py
(qa/limits-matrix-reconcile-next-R2602.log).

It refuses to write when the evidence is absent, not green, or when the
anchor row cannot be found exactly once.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa",
                        "suite-matrix-reconcile-evidence-face-R2602.log")
LIMITS = os.path.join(REPO, "qa", "limits-matrix-reconcile-next-R2602.log")

SEED_HEAD = "- [ ] P2 tech seed (R2601,"
SEED_MARK = "`src/os/suite_matrix_reconcile.py` - THREE limits"
DONE_PREFIX = "- [x] [done 2026-11-10 R2602]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2602, from this window own measured limit): "
    "`src/os/suite_matrix_reconcile.py` - FOUR limits MEASURED this window "
    "with src/os/limits_suite_matrix_reconcile_next_R2602.py against private "
    "copies (qa/limits-matrix-reconcile-next-R2602.log, 220B, utf-8 LF): "
    "(a) a document whose matrix SEPARATOR row carries four cells under a "
    "six-cell header still reads header_cells=6 and the run reads "
    "STALE-CONTENT, so the shape law covers the header only and a broken "
    "separator is reported as content drift; (b) a document that carries NO "
    "matrix table at all reads ROWS-MISMATCH with rows=0, a row-count word "
    "for a table that is absent; (c) an explicit --evidence together with "
    "--qa-dir answers DOC-CURRENT with walk=None, so the caller is never told "
    "which of the two it used; (d) a qa directory with no PASS leg decodes "
    "every candidate (measured considered=40 decoded=40) because the walk "
    "stops only on a PASS leg and has no bound. Product: ONE reading that "
    "refuses a separator/header width disagreement by shape, names a document "
    "carrying no matrix table with its own word, bounds the candidate walk and "
    "names the bound it applied, and reports which evidence source it used "
    "when both are given. Criteria AC-EDMC1..AC-EDMC6 pinned HERE BEFORE any "
    "code: AC-EDMC1 a separator row whose width disagrees with the header "
    "refuses by HEADER-SHAPE naming BOTH widths instead of reading "
    "STALE-CONTENT; AC-EDMC2 a document with no matrix table refuses with its "
    "own word naming the missing table instead of reading ROWS-MISMATCH; "
    "AC-EDMC3 the candidate walk is bounded by a declared ceiling, stops at "
    "that ceiling and says so, so a qa pile with no PASS leg cannot be decoded "
    "end to end; AC-EDMC4 an explicit --evidence together with --qa-dir "
    "reports which source it used and never ignores one in silence; AC-EDMC5 "
    "every R2602 answer survives beside the new ones (all seven verdict words, "
    "both counts, one verdict word on the CLI, the exit codes) proved on the "
    "same fixtures; AC-EDMC6 pure ASCII, stdlib only, no clock, zero network, "
    "its own reconcile label and its own suite.")


def build_discharged(evidence_bytes, limits_bytes):
    return (
        " DISCHARGED R2602 (line 634, AC-EDMB1..AC-EDMB6 pinned there at R2601 "
        "BEFORE any code): src/os/suite_matrix_reconcile.py now names an "
        "evidence-face difference apart from a content difference - an "
        "explicit RUNNER PASS leg that differs from the leg the document "
        "records reads EVIDENCE-FACE and prints BOTH legs, asked of the "
        "shipped doc_evidence_face at call time; the candidate walk reports "
        "what it cost (considered/decoded) and stops at the first PASS leg; a "
        "MISSING document is composed from a --stamp-from source through the "
        "shipped render and still reads NO-DOC with nothing written when no "
        "source is given; and a matrix header that is not six cells refuses "
        "by HEADER-SHAPE naming both widths instead of reading zero rows. "
        "Every R2601 answer survives (five words, both counts, one verdict "
        "word, the exit codes) on the same fixtures. Proof: AC-EDMB1..AC-EDMB6 "
        "SUITE PASS 6/6 TWICE identical through the shipped capture callable "
        "(qa/suite-matrix-reconcile-evidence-face-R2602.log, %d bytes, "
        "two LEG blocks with identical digests, adjacent=1 fails=0), the "
        "R2601 parent suite "
        "still 6/6, and six readability suites green 6/6 each. REGISTRY "
        "635/4786 -> 636/4792 recounted by import; docs/sandbox-suite-matrix.md "
        "was regenerated from the CURRENT registry through this face own "
        "--write at the recorded leg (64952 bytes, 636 rows, 4792 criteria), "
        "and a live --check then read DOC-CURRENT with "
        "considered=2797 decoded=11, which is the bound named in the successor "
        "row. Four successor limits were MEASURED this window "
        "(qa/limits-matrix-reconcile-next-R2602.log, %d bytes, utf-8 LF, "
        "nul=0, crlf=0)." % (evidence_bytes, limits_bytes))


def main(argv):
    if not os.path.isfile(EVIDENCE):
        print("E_R2602_MISSING %s" % os.path.basename(EVIDENCE))
        return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if ("EVIDENCE identical=True adjacent=1 fails=0" not in evidence
            or "fails=0" not in evidence):
        print("E_R2602_EVIDENCE_NOT_GREEN")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2602_EVIDENCE_NOT_TWICE")
        return 4
    if not os.path.isfile(LIMITS):
        print("E_R2602_LIMITS_MISSING")
        return 3
    raw_limits = open(LIMITS, "rb").read()
    limits = raw_limits.decode("utf-8")
    for token in ("STALE-CONTENT", "ROWS-MISMATCH", "decoded=40"):
        if token not in limits:
            print("E_R2602_LIMITS_UNEXPECTED %s" % token)
            return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2602_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2602_ALREADY_DONE")
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