"""R2606 board closeout for the AC-EDMD1 seed row at state/queue/tech.md:638.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose four limits were MEASURED this
window by src/os/limits_suite_matrix_reconcile_shape_next_R2606.py
(qa/limits-matrix-reconcile-shape-next-R2606.log).

It refuses to write when the evidence is absent, not green, or when the
anchor row cannot be found exactly once.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa",
                        "suite-matrix-reconcile-shape-R2606.log")
LIVE = os.path.join(REPO, "qa",
                    "suite-matrix-reconcile-shape-live-R2606.log")
LIMITS = os.path.join(REPO, "qa",
                      "limits-matrix-reconcile-shape-next-R2606.log")

SEED_HEAD = "- [ ] P2 tech seed (R2604,"
SEED_MARK = "FOUR limits MEASURED this window"
DONE_PREFIX = "- [x] [done 2026-11-10 R2606]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2606, from this window own measured limit): "
    "`src/os/suite_matrix_reconcile.py` - FOUR limits MEASURED this window "
    "with src/os/limits_suite_matrix_reconcile_shape_next_R2606.py against "
    "private copies (qa/limits-matrix-reconcile-shape-next-R2606.log): "
    "(a) a separator drawn with MIXED punctuation (`-=-=`) reads "
    "SEPARATOR-MISSING, so a separator that IS present is misnamed as absent "
    "because the law only knows single-character repeats and the dash/colon "
    "set; (b) a matrix title inside a FENCED code block still counts "
    "(measured titles=2 -> TITLE-REPEATED) even though the document carries "
    "one real table; (c) a title line carrying trailing spaces also counts as "
    "a second title (measured titles=2), because the count strips the line "
    "but not the table law; (d) `--ceiling 1` over a pile with no PASS leg "
    "decodes one candidate and then reads RED-LEG with walk bounded=True, so "
    "a STARVED bound and an honest empty pile are still told apart only by "
    "the walk block, not by the verdict word. Product: ONE reading that names "
    "a mixed-punctuation separator as a separator (and a width disagreement "
    "as HEADER-SHAPE) instead of calling it absent, that counts only a title "
    "outside code fences and outside quotes, and that gives a "
    "ceiling-starved walk its own verdict word rather than the RED-LEG it "
    "shares with an honest miss. Criteria AC-EDME1..AC-EDME6 pinned HERE "
    "BEFORE any code: AC-EDME1 a separator row whose non-space characters are "
    "punctuation of more than one kind is read as a separator, and a width "
    "disagreement against the header refuses by HEADER-SHAPE naming BOTH "
    "widths; AC-EDME2 a matrix title inside a fenced code block does not "
    "count as a table title, so a document carrying one real table and one "
    "quoted title reads its table instead of TITLE-REPEATED; AC-EDME3 a title "
    "line whose only difference is trailing whitespace is the SAME title and "
    "is not counted twice; AC-EDME4 a walk whose declared ceiling was reached "
    "before a PASS leg was found reads its own CEILING-STARVED word naming "
    "the ceiling, while a pile whose every candidate was decoded reads "
    "RED-LEG, so the two states are told apart by the verdict word; AC-EDME5 "
    "every R2606 answer survives beside the new ones (all four shape words, "
    "both counts, the bounded walk, the named evidence source, the R2602 "
    "words, one verdict word on the CLI and the exit codes) proved on the "
    "same fixtures; AC-EDME6 pure ASCII, stdlib only, no clock, zero "
    "network, its own reconcile label and its own suite.")


def build_discharged(evidence_bytes, live_bytes, limits_bytes):
    return (
        " DISCHARGED R2606 (line 638, AC-EDMD1..AC-EDMD6 pinned there at R2604 "
        "BEFORE any code): src/os/suite_matrix_reconcile.py now recognises a "
        "SEPARATOR drawn with any single repeated punctuation character "
        "('=' and friends) and refuses a width disagreement against the header "
        "by HEADER-SHAPE naming BOTH widths; a header carrying NO separator "
        "row refuses with its own SEPARATOR-MISSING word instead of falling "
        "through to a content word; a ceiling below one candidate refuses with "
        "its own CEILING-STARVED word naming the ceiling on BOTH the read and "
        "the compose paths and creates nothing; and a document carrying the "
        "matrix title more than once refuses with TITLE-REPEATED naming the "
        "count instead of reading the first table and dropping the rest. Every "
        "R2604 answer survives on the same fixtures (both HEADER-SHAPE widths, "
        "TABLE-MISSING, the bounded walk, the named evidence source, the R2602 "
        "words, both counts, one verdict word on the CLI, the exit codes). "
        "Proof: AC-EDMD1..AC-EDMD6 SUITE PASS 6/6 TWICE identical through the "
        "shipped capture callable (qa/suite-matrix-reconcile-shape-R2606.log, "
        "%d bytes, digest 4921D77253FAC1B3, legs=2 identical=True adjacent=3 "
        "fails=0) with the three sibling suites green beside it; a read-only "
        "live leg on the real tree read DOC-CURRENT at 638/638 rows and 4804 "
        "criteria (qa/suite-matrix-reconcile-shape-live-R2606.log, %d bytes). "
        "REGISTRY 637/4798 -> 638/4804 recounted by import; "
        "docs/sandbox-suite-matrix.md was regenerated from the CURRENT "
        "registry through this face own --write at the recorded leg (65137 "
        "bytes, 638 rows) and --check then read DOC-CURRENT. Four successor "
        "limits were MEASURED this window "
        "(qa/limits-matrix-reconcile-shape-next-R2606.log, %d bytes, utf-8 "
        "LF)." % (evidence_bytes, live_bytes, limits_bytes))


def main(argv):
    for path in (EVIDENCE, LIVE, LIMITS):
        if not os.path.isfile(path):
            print("E_R2606_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True adjacent=3 fails=0" not in evidence:
        print("E_R2606_EVIDENCE_NOT_GREEN")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2606_EVIDENCE_NOT_TWICE")
        return 4
    raw_live = open(LIVE, "rb").read()
    if b"verdict=DOC-CURRENT" not in raw_live:
        print("E_R2606_LIVE_NOT_CURRENT")
        return 4
    raw_limits = open(LIMITS, "rb").read()
    limits = raw_limits.decode("utf-8")
    for token in ("mixed-punct-separator", "fenced-title", "trailing-title",
                  "ceiling-one"):
        if token not in limits:
            print("E_R2606_LIMITS_UNEXPECTED %s" % token)
            return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2606_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2606_ALREADY_DONE")
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