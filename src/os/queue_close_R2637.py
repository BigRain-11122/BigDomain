"""R2637 board closeout for the AC-EDWT1 seed row at state/queue/tech.md:658.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose limits were MEASURED this window by
src/os/limits_export_composed_landed_next_R2637.py.

It refuses to write when the evidence is absent, not green, not twice, empty
digested, or when the anchor row cannot be found exactly once.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa", "export-composed-landed-R2637.log")
LIMITS = os.path.join(REPO, "qa", "limits-export-composed-landed-R2637.log")
NEXT = os.path.join(REPO, "qa",
                    "limits-export-composed-landed-next-R2637.log")

SEED_HEAD = "- [ ] P2 tech seed (R2596,"
SEED_MARK = "composed-text / landed-bytes"
DONE_PREFIX = "- [x] [done 2026-11-11 R2637]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2637, from this window own measured limit): "
    "`src/os/export_composed_landed_face.py` WORD SPACE - three shapes are "
    "measured this window with src/os/limits_export_composed_landed_next_"
    "R2637.py against private files (qa/limits-export-composed-landed-next-"
    "R2637.log): (a) a MIXED landing (one CRLF and one lone LF) reads "
    "transport=mixed but is answered COMPOSED-MISMATCH with composed=None and "
    "delta=None, so the transport fact has no word of its own; (b) an EMPTY "
    "landing (disk=0) is answered COMPOSED-MISMATCH with delta=-12 rather "
    "than an empty-landing word; (c) a landing carrying a UTF-8 BOM shows "
    "delta=3 and cannot be told apart from a genuine three byte content gap; "
    "(d) the CRLF-caller double-charge this window repaired was re-measured "
    "AFTER the fold and now reads PASS at composed=15 disk=15, and (e) a "
    "single line with no newline already reads PASS - both are named as "
    "already correct rather than claimed as gaps. Criteria AC-EDWV1..AC-EDWV6 "
    "pinned HERE BEFORE any code: AC-EDWV1 a MIXED landing earns its own word "
    "and still carries the bytes it read; AC-EDWV2 an EMPTY landing earns its "
    "own word distinct from COMPOSED-MISMATCH; AC-EDWV3 a BOM landing is named "
    "as a BOM landing rather than as a content delta of three; AC-EDWV4 (a) to "
    "(e) each keep exactly one verdict word and nothing is written; AC-EDWV5 "
    "every AC-EDWT1..AC-EDWT6 answer survives on the same fixtures, including "
    "the CRLF caller PASS and the five pre-existing export verdict words; "
    "AC-EDWV6 pure ASCII, stdlib only, no network, no clock, its own reconcile "
    "label and its own suite.")


def build_discharged(evidence_bytes, limits_bytes, next_bytes):
    """The DISCHARGED note, built from this round own bytes on disk."""
    return ("  DISCHARGED R2637: shipped src/os/export_composed_landed_face.py "
            "plus its six-criteria suite, wired into src/os/export_R2431.py as "
            "ONE term after the queue/disk pair so a composed/landed gap earns "
            "COMPOSED-MISMATCH with BOTH counts while every pre-existing "
            "verdict word rides unchanged at the six-argument call shape. "
            "AC-EDWT1..AC-EDWT6 SUITE PASS 6/6 twice identical through the "
            "shipped capture callable (qa/export-composed-landed-R2637.log, "
            "%dB) with four adjacent export suites rc=0, and the gap itself "
            "was MEASURED BEFORE any byte with "
            "src/os/limits_export_composed_landed_R2637.py (%dB): LF composed=12 "
            "landed=12, CRLF composed=12 landed=15 delta=3, and the shipped "
            "classify() answered PASS with that gap invisible. ONE OWN DEFECT "
            "was measured and repaired at its birth site INSIDE this window - "
            "a caller handing CRLF composed text was charged for the CR twice "
            "(18 composed against 15 landed) and read COMPOSED-MISMATCH, so the "
            "fold to bare LF now precedes the transport expansion and AC-EDWT2 "
            "carries that shape as an assertion; the evidence file was re-taken "
            "AFTER the repair and the pre-repair capture is disclosed rather "
            "than presented. Registry 645/4846 -> 646/4852 by exactly one row, "
            "recounted by import; docs/sandbox-suite-matrix.md read FAIL (stale) "
            "BEFORE any byte and was regenerated to 66064B at 646/4852 with its "
            "green line honestly reading 645/646 and --check byte-identical. "
            "The real export still reads VERDICT PASS at 402578B after the "
            "change, so the new term did not redden a healthy face. Successor "
            "limits (%dB) were measured AFTER the fix." % (
                evidence_bytes, limits_bytes, next_bytes))


def main(argv):
    for path in (EVIDENCE, LIMITS, NEXT):
        if not os.path.isfile(path):
            print("E_R2637_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True adjacent=4 fails=0" not in evidence:
        print("E_R2637_EVIDENCE_NOT_GREEN")
        return 4
    if "digest=" not in evidence or "digest=" + ("0" * 16) in evidence:
        print("E_R2637_EMPTY_DIGEST")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2637_EVIDENCE_NOT_TWICE")
        return 4
    next_text = open(NEXT, "rb").read().decode("utf-8")
    if "d_caller_crlf" not in next_text or "word=PASS" not in next_text:
        print("E_R2637_NEXT_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2637_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2637_ALREADY_DONE")
        return 4

    discharged = build_discharged(
        len(raw_evidence), len(open(LIMITS, "rb").read()),
        len(open(NEXT, "rb").read()))
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
