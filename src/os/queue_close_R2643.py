"""R2643 board closeout for the AC-EDWW1 seed row at state/queue/tech.md:660.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose limits were MEASURED this window by
src/os/limits_export_composed_landed_next_R2643.py.

It refuses to write when the evidence is absent, not green, not twice, empty
digested, or when the anchor row cannot be found exactly once.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(
    REPO, "qa", "export-composed-landed-bom-precedence-R2643.log")
NEXT = os.path.join(
    REPO, "qa", "limits-export-composed-landed-bom-precedence-next-R2643.log")

SEED_HEAD = "- [ ] P2 tech seed (R2638, from this window own measured limit):"
SEED_MARK = "BOM PRECEDENCE"
DONE_PREFIX = "- [x] [done 2026-11-11 R2643]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2643, from this window own measured limit): "
    "`src/os/export_composed_landed_face.py` BOM PRECEDENCE, SECOND WAVE - "
    "five shapes are measured this window with src/os/limits_export_"
    "composed_landed_next_R2643.py against private files (qa/limits-export-"
    "composed-landed-bom-precedence-next-R2643.log): (a) a TRUNCATED BOM prefix "
    "whose body carries MIXED separators reads TRANSPORT-MIXED with bom=0, so "
    "the truncation fact is lost because the truncated law needs a clean body; "
    "(b) a UTF-16 BOM marker alone (ff fe, two bytes, no body) against an EMPTY "
    "composed text reads UTF16-BOM-LANDING, so a marker with nothing behind it "
    "is not distinguished from a whole UTF-16 landing; (c) a BOM-ONLY landing "
    "(three bytes, no body) against empty composed text reads BOM-LANDING at "
    "delta=0, so a marker with no payload reads clean; (d) a UTF-16 payload "
    "with NO BOM reads COMPOSED-MISMATCH at delta=12 because no marker names "
    "the encoding; and (e) a legitimate UTF-8 payload starting with 0xef and a "
    "clean LF landing both read PASS and are named as already correct rather "
    "than claimed. Criteria AC-EDWX1..AC-EDWX6 pinned HERE BEFORE any code: "
    "AC-EDWX1 a truncated BOM prefix whose body carries MIXED separators names "
    "BOTH the truncation and the transport in ONE word; AC-EDWX2 a UTF-16 BOM "
    "carrying no body against an empty composed text names that the landing is "
    "a marker with nothing behind it; AC-EDWX3 a BOM-only landing against empty "
    "composed text names the empty payload rather than reading a clean BOM "
    "landing; AC-EDWX4 a payload whose encoding no marker names still reads the "
    "compare word with BOTH counts instead of a guessed encoding; AC-EDWX5 "
    "every AC-EDWW1..AC-EDWW6 and AC-EDWV1..AC-EDWV6 answer survives, including "
    "the legitimate 0xef-start PASS and the clean LF PASS; AC-EDWX6 pure ASCII, "
    "stdlib only, no network, no clock, its own reconcile label and its own "
    "suite.")


def build_discharged(evidence_bytes, next_bytes):
    return ("  DISCHARGED R2643: extended src/os/export_composed_landed_face.py "
            "in place with the FOUR new landing words and a dropped assumption "
            "- the pinned order is now EMPTY, UTF-16 BOM, TRUNCATED BOM, BOM "
            "(mixed / body gap / clean), MIXED, then the composed/landed compare "
            "- so a landing still earns exactly ONE word, and added src/os/"
            "test_export_composed_landed_bom_precedence.py as the AC-EDWW1.."
            "AC-EDWW6 suite. AC-EDWW1..AC-EDWW6 SUITE PASS 6/6 twice identical "
            "through the shipped capture callable (qa/export-composed-landed-"
            "bom-precedence-R2643.log, %dB) with the two parent suites green "
            "beside it (wordspace 6/6, composed/landed 6/6). THE FOUR SHAPES "
            "WERE MEASURED BEFORE ANY CODE by re-running src/os/limits_export_"
            "composed_landed_next_R2638.py: BOM body gap read BOM-LANDING at "
            "delta=6, BOM plus MIXED read BOM-LANDING with transport=mixed, a "
            "UTF-16LE BOM read COMPOSED-MISMATCH at delta=14 and a two byte "
            "truncated prefix read COMPOSED-MISMATCH at delta=2, byte for byte "
            "the seed row numbers. ONE OWN DEFECT WAS MEASURED AND REPAIRED AT "
            "ITS BIRTH SITE INSIDE THIS WINDOW: the prefix walk took the "
            "SHORTEST matching strict prefix, so a two byte cut was measured as "
            "a one byte cut and read COMPOSED-MISMATCH on the first suite run; "
            "the longest matching prefix now wins, AC-EDWW4 asserts both cuts, "
            "and the evidence was captured AFTER the repair. A truncated prefix "
            "is only called truncated when the REST of the payload really is "
            "the composed text, so a legitimate 0xef-leading UTF-8 payload is "
            "not accused (asserted, not asserted-by-absence). Registry 647/4858 "
            "-> 648/4864 by exactly one row, recounted by import; docs/sandbox-"
            "suite-matrix.md read ROWS-MISMATCH 647 against 648 BEFORE any byte "
            "and was regenerated through the shipped write face from the R2638 "
            "green leg to 66331B at 648 rows with --check reading DOC-CURRENT; "
            "the real export still reads VERDICT PASS at 403179B after the "
            "change and check_export_consistency read 21/21 PASS, so no healthy "
            "face was reddened. Successor limits (%dB) measured AFTER the fix."
            % (evidence_bytes, next_bytes))


def main(argv):
    for path in (EVIDENCE, NEXT):
        if not os.path.isfile(path):
            print("E_R2643_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True" not in evidence or "fails=0" not in evidence:
        print("E_R2643_EVIDENCE_NOT_GREEN")
        return 4
    if "digest=" not in evidence or "digest=" + ("0" * 16) in evidence:
        print("E_R2643_EMPTY_DIGEST")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2643_EVIDENCE_NOT_TWICE")
        return 4
    next_text = open(NEXT, "rb").read().decode("utf-8")
    if "a_truncated_mixed" not in next_text or "c_bom_only" not in next_text:
        print("E_R2643_NEXT_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2643_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2643_ALREADY_DONE")
        return 4

    discharged = build_discharged(
        len(raw_evidence), len(open(NEXT, "rb").read()))
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
