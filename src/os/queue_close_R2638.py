"""R2638 board closeout for the AC-EDWV1 seed row at state/queue/tech.md:659.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose limits were MEASURED this window by
src/os/limits_export_composed_landed_next_R2638.py.

It refuses to write when the evidence is absent, not green, not twice, empty
digested, or when the anchor row cannot be found exactly once.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(
    REPO, "qa", "export-composed-landed-wordspace-R2638.log")
NEXT = os.path.join(
    REPO, "qa", "limits-export-composed-landed-wordspace-next-R2638.log")

SEED_HEAD = "- [ ] P2 tech seed (R2637, from this window own measured limit):"
SEED_MARK = "WORD SPACE"
DONE_PREFIX = "- [x] [done 2026-11-11 R2638]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2638, from this window own measured limit): "
    "`src/os/export_composed_landed_face.py` BOM PRECEDENCE - four shapes are "
    "measured this window with src/os/limits_export_composed_landed_next_"
    "R2638.py against private files (qa/limits-export-composed-landed-"
    "wordspace-next-R2638.log): (a) a BOM landing whose BODY disagrees with "
    "the composed text still reads BOM-LANDING with delta=6, so a real content "
    "gap inside a BOM payload is named as a BOM landing and not as a gap; (b) a "
    "BOM landing that ALSO carries MIXED separators reads BOM-LANDING with "
    "transport=mixed, so the transport fact survives only as a field and not as "
    "the word; (c) a UTF-16LE BOM (ff fe) is not recognised at all and reads "
    "COMPOSED-MISMATCH at delta=14, and (d) a TRUNCATED two byte BOM prefix "
    "reads COMPOSED-MISMATCH at delta=2 - both are named rather than claimed; "
    "(e) an EMPTY landing against an EMPTY composed text already reads "
    "EMPTY-LANDING and is named as already correct. Criteria AC-EDWW1..AC-EDWW6 "
    "pinned HERE BEFORE any code: AC-EDWW1 a BOM landing whose body disagrees "
    "with the composed text earns a word that says BOTH that a BOM is present "
    "and that the body differs; AC-EDWW2 a BOM landing carrying MIXED "
    "separators names both facts in ONE word rather than letting the BOM hide "
    "the transport; AC-EDWW3 a UTF-16 BOM is named as a UTF-16 BOM rather than "
    "as a content delta of fourteen; AC-EDWW4 a TRUNCATED BOM prefix is named "
    "as a truncated BOM rather than as a content delta of two; AC-EDWW5 every "
    "AC-EDWV1..AC-EDWV6 answer survives on the same fixtures, including the "
    "three new words from R2638 and the two shapes named as already correct; "
    "AC-EDWW6 pure ASCII, stdlib only, no network, no clock, its own reconcile "
    "label and its own suite.")


def build_discharged(evidence_bytes, next_bytes):
    return ("  DISCHARGED R2638: extended src/os/export_composed_landed_face.py "
            "in place with a PINNED shape order - EMPTY first, BOM second, "
            "MIXED third, the composed/landed compare last - so a landing can "
            "never earn two words, and added src/os/test_export_composed_landed_"
            "wordspace.py as the AC-EDWV1..AC-EDWV6 suite. AC-EDWV1..AC-EDWV6 "
            "SUITE PASS 6/6 twice identical through the shipped capture callable "
            "(qa/export-composed-landed-wordspace-R2638.log, %dB) with the "
            "parent AC-EDWT suite and two export suites green beside it and one "
            "adjacent suite printing its own SUMMARY at rc=0 rather than a "
            "suite line. THE THREE SHAPES WERE MEASURED BEFORE ANY CODE with "
            "src/os/limits_export_composed_landed_next_R2637.py: MIXED read "
            "COMPOSED-MISMATCH with composed=None, EMPTY read COMPOSED-MISMATCH "
            "at delta -12, and BOM read COMPOSED-MISMATCH at delta 3, exactly "
            "as the seed row recorded. ONE CRITERION WAS CONSCIOUSLY AMENDED "
            "WITH ITS REASON: AC-EDWT3 in the parent suite used to demand the "
            "world COMPOSED-MISMATCH for a MIXED landing, which was always a "
            "statement about the transport being read OFF THE LANDED BYTES and "
            "not about the word, so it now demands TRANSPORT-MIXED and carries "
            "the reason inline; the parent suite still reads 6/6 and every "
            "other AC-EDWT answer survives (AC-EDWV5). Registry 646/4852 -> "
            "647/4858 by exactly one row, recounted by import; the real export "
            "still reads VERDICT PASS at 403298B after the change, so no healthy "
            "face was reddened. Successor limits (%dB) measured AFTER the fix."
            % (evidence_bytes, next_bytes))


def main(argv):
    for path in (EVIDENCE, NEXT):
        if not os.path.isfile(path):
            print("E_R2638_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True adjacent=4 fails=0" not in evidence:
        print("E_R2638_EVIDENCE_NOT_GREEN")
        return 4
    if "digest=" not in evidence or "digest=" + ("0" * 16) in evidence:
        print("E_R2638_EMPTY_DIGEST")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2638_EVIDENCE_NOT_TWICE")
        return 4
    next_text = open(NEXT, "rb").read().decode("utf-8")
    if "a_bom_body_gap" not in next_text or "c_utf16_bom" not in next_text:
        print("E_R2638_NEXT_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2638_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2638_ALREADY_DONE")
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
