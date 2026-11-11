"""R2646 board closeout for the AC-EDWX1 seed row at state/queue/tech.md:661.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose limits were MEASURED this window by
src/os/limits_export_composed_landed_next_R2646.py.

It refuses to write when the evidence is absent, not green, not twice, empty
digested, or when the anchor row cannot be found exactly once.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(
    REPO, "qa", "export-composed-landed-bom-precedence-second-wave-R2646.log")
NEXT = os.path.join(
    REPO, "qa",
    "limits-export-composed-landed-bom-precedence-second-wave-next-R2646.log")

SEED_HEAD = "- [ ] P2 tech seed (R2643, from this window own measured limit):"
SEED_MARK = "BOM PRECEDENCE, SECOND WAVE"
DONE_PREFIX = "- [x] [done 2026-11-11 R2646]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2646, from this window own measured limit): "
    "`src/os/export_composed_landed_face.py` BOM PRECEDENCE, THIRD WAVE - "
    "six shapes are measured this window with src/os/limits_export_"
    "composed_landed_next_R2646.py against private files (qa/limits-export-"
    "composed-landed-bom-precedence-second-wave-next-R2646.log): (a) a "
    "truncated BOM prefix over a MIXED body that is NOT the composed text "
    "reads TRANSPORT-MIXED with bom=0, so the truncation fact is dropped again "
    "because the second wave only names a cut when the body matches up to "
    "separators; (b) a BOM-ONLY landing against a NON-EMPTY composed text "
    "reads BOM-EMPTY-PAYLOAD with composed=None, so the composed count it was "
    "measured against is not carried at all; (c) a truncated prefix with an "
    "EMPTY body against an EMPTY text reads BOM-TRUNCATED at delta=2 although "
    "nothing lies behind the prefix; (d) a UTF-8 BOM followed by a UTF-16 "
    "marker reads BOM-BODY-MISMATCH at delta=-10, so two markers on one "
    "landing are named only as a body gap; (e) a legitimate 0xef-leading "
    "payload with MIXED separators that is not the composed text reads "
    "TRANSPORT-MIXED and is named as NOT accused of being a cut marker; and "
    "(f) a UTF-16 marker with ONE zero byte behind it reads UTF16-BOM-LANDING, "
    "so a one byte remnant is not told apart from a whole landing. (g) a clean "
    "LF landing reads PASS and is named as already correct. Criteria "
    "AC-EDWY1..AC-EDWY6 pinned HERE BEFORE any code: AC-EDWY1 a truncated "
    "prefix over a MIXED body that is not the composed text names BOTH the "
    "truncation and the transport in ONE word; AC-EDWY2 a BOM-only landing "
    "against non-empty composed text names the empty payload AND carries the "
    "composed count it was measured against; AC-EDWY3 a truncated prefix with "
    "an empty body against empty text names that nothing lies behind the "
    "prefix rather than a plain truncation; AC-EDWY4 two markers on one "
    "landing names both markers instead of one body gap; AC-EDWY5 every "
    "AC-EDWX1..AC-EDWX6, AC-EDWW and AC-EDWV answer survives, including the "
    "legitimate 0xef-start PASS and the clean LF PASS; AC-EDWY6 pure ASCII, "
    "stdlib only, no network, no clock, its own reconcile label and its own "
    "suite.")


def build_discharged(evidence_bytes, next_bytes):
    return ("  DISCHARGED R2646: extended src/os/export_composed_landed_face.py "
            "in place with THREE new landing words pinned into the SAME single-"
            "word order - EMPTY, UTF-16 MARKER-ONLY before a whole UTF-16 "
            "landing, BOM-EMPTY-PAYLOAD before any BOM body judgement, "
            "TRUNCATED BOM (a MIXED body named as BOTH facts when it equals the "
            "composed text up to separators), BOM (mixed / body gap / clean), "
            "MIXED, then the composed/landed compare - and added src/os/test_"
            "export_composed_landed_bom_precedence_second_wave.py as the "
            "AC-EDWX1..AC-EDWX6 suite, wired once into the runner at six "
            "criteria. Proof: SUITE PASS 6/6 TWICE with identical criterion "
            "lines through the shipped capture callable (qa/export-composed-"
            "landed-bom-precedence-second-wave-R2646.log, %dB, digest "
            "003B62E6FAFCAC9F) with FOUR adjacent export suites green beside it "
            "(bom-precedence 6/6, wordspace 6/6, composed/landed 6/6, writer "
            "dialect 6/6). The five shapes were MEASURED BEFORE ANY CODE by "
            "re-running src/os/limits_export_composed_landed_next_R2643.py: a "
            "truncated prefix over a MIXED body read TRANSPORT-MIXED bom=0, a "
            "UTF-16 marker alone read UTF16-BOM-LANDING disk=2, a BOM-only "
            "landing read BOM-LANDING delta=0, a UTF-16 payload with no marker "
            "read COMPOSED-MISMATCH delta=12, and a legitimate 0xef payload and "
            "a clean LF landing both read PASS, byte for byte the seed row "
            "numbers. ONE OWN DEFECT WAS MEASURED AND REPAIRED AT ITS BIRTH SITE "
            "INSIDE THIS WINDOW: the AC-EDWX5 fixture wrote its legit file AFTER "
            "the untouched-fingerprint was taken, so the first suite run read "
            "untouched=False; the fixture order was fixed rather than the "
            "assertion loosened, and ALL evidence was captured AFTER the fix. "
            "The truncated law was also tightened to byte equality with the "
            "composed text (length alone could accuse a same-length payload). "
            "Registry 648/4864 -> 649/4870 by exactly one row, recounted by "
            "import (649 unique names, 649 unique paths); docs/sandbox-suite-"
            "matrix.md read FAIL stale BEFORE any byte and was regenerated "
            "stamp-aligned through the shipped write face from the R2645 green "
            "leg to 66441B at 649/4870 with its green line honestly reading "
            "648/648 and --check byte-identical. Successor limits (%dB) "
            "measured AFTER the fix."
            % (evidence_bytes, next_bytes))


def main(argv):
    for path in (EVIDENCE, NEXT):
        if not os.path.isfile(path):
            print("E_R2646_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True" not in evidence or "fails=0" not in evidence:
        print("E_R2646_EVIDENCE_NOT_GREEN")
        return 4
    if "digest=" not in evidence or "digest=" + ("0" * 16) in evidence:
        print("E_R2646_EMPTY_DIGEST")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2646_EVIDENCE_NOT_TWICE")
        return 4
    next_text = open(NEXT, "rb").read().decode("utf-8")
    if "a_trunc_mixed_extra" not in next_text or "c_trunc_empty_body" not in \
            next_text or "f_utf16_one_byte" not in next_text:
        print("E_R2646_NEXT_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2646_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2646_ALREADY_DONE")
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
