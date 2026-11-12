"""R2657 board closeout for the AC-EDXA1 seed row at state/queue/tech.md:664.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose limits were MEASURED this window by
src/os/limits_export_composed_landed_next_R2657.py.

It refuses to write when the evidence is absent, not green, not twice, empty
digested, when the next-row limits do not carry the shapes it quotes, or when
the anchor row cannot be found exactly once.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(
    REPO, "qa", "export-composed-landed-bom-precedence-fifth-wave-R2657.log")
BEFORE = os.path.join(
    REPO, "qa", "limits-export-composed-landed-fifth-wave-before-R2657.log")
AFTER = os.path.join(
    REPO, "qa", "limits-export-composed-landed-fifth-wave-after-R2657.log")
NEXT = os.path.join(REPO, "qa",
                    "limits-export-composed-landed-next-R2657.log")

SEED_HEAD = "- [ ] P2 tech seed (R2653,"
SEED_MARK = "BOM PRECEDENCE, FIFTH WAVE"
DONE_PREFIX = "- [x] [done 2026-11-12 R2657]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2657, from this window own measured limit): "
    "`src/os/export_composed_landed_face.py` BOM PRECEDENCE, SIXTH WAVE - "
    "four shapes are measured this window with src/os/limits_export_"
    "composed_landed_next_R2657.py against private files "
    "(qa/limits-export-composed-landed-next-R2657.log, 748B): (a) a UTF-16LE "
    "landing CUT by exactly one code unit, whose body is an EVEN number of "
    "bytes and a strict PREFIX of the text encoding, still reads "
    "UTF16-BOM-LANDING with composed=None at disk=24, so a lost character in "
    "a UTF-16 landing is named by no word and no delta; (b) an EVEN body that "
    "is neither the text nor a head of it reads the historical whole-landing "
    "word with composed=None at disk=4, so no judgement is made about a "
    "payload that is simply another document; and (c)/(d) were re-measured "
    "AFTER the fifth wave and are named rather than claimed - a whole UTF-16 "
    "landing against EMPTY composed text reads UTF16-BOM-BODY-GAP "
    "composed=2 delta=24, and an EVEN two byte body behind two markers reads "
    "BOM-DOUBLE-MARKER body=2 body_short=False. Criteria AC-EDXB1..AC-EDXB6 "
    "pinned HERE BEFORE any code: AC-EDXB1 a UTF-16 landing whose body is the "
    "text encoding minus a whole number of code units is named as a CUT with "
    "the units it lost, never as a whole landing; AC-EDXB2 that name carries "
    "the whole landing it would have been so a delta is published rather "
    "than None; AC-EDXB3 a body that is neither the text nor a head of it "
    "keeps the historical whole-landing word and reports no delta, and the "
    "refusal to judge is named as a refusal rather than left silent; "
    "AC-EDXB4 the two answers measured here survive on their own fixtures "
    "(the empty-text gap and the even two byte body behind two markers); "
    "AC-EDXB5 every AC-EDXA, AC-EDWZ, AC-EDWY, AC-EDWX, AC-EDWW and AC-EDWV "
    "answer survives on its own fixture, including the legitimate "
    "0xef-leading MIXED payload that stays TRANSPORT-MIXED with bom=0 and "
    "the clean LF PASS; AC-EDXB6 pure ASCII, stdlib only, no network, no "
    "clock, its own reconcile label and its own suite.")


def build_discharged(evidence_bytes, before_bytes, after_bytes, next_bytes):
    return (
        "DISCHARGED R2657: extended src/os/export_composed_landed_face.py in "
        "place so a WHOLE UTF-16 landing is COMPARED with the composed text "
        "in the marker own byte order instead of being named and dropped: an "
        "agreeing landing keeps UTF16-BOM-LANDING and now publishes "
        "composed=marker+body and delta=0, while a landing that carries the "
        "text plus extra bytes earns the new word UTF16-BOM-BODY-GAP with "
        "kind=utf16-gap and its delta published - so agreement is DECIDED, "
        "which the R2653 measurement showed it was not (both shapes read the "
        "same word with composed=None at disk=26 and disk=30). The "
        "double-marker law now publishes body_short on an ODD body behind "
        "both markers and renders body_short=1 beside the body count, while "
        "the word stays BOM-DOUBLE-MARKER because AC-EDWZ3 own three byte "
        "fixture must survive (AC-EDXA5). Added src/os/test_export_composed_"
        "landed_bom_precedence_fifth_wave.py as the AC-EDXA1..AC-EDXA6 suite, "
        "wired once into the runner at six criteria. Proof: SUITE PASS 6/6 "
        "TWICE with identical criterion lines through the shipped capture "
        "callable (qa/export-composed-landed-bom-precedence-fifth-wave-"
        "R2657.log, %d bytes, legs=2 identical=True adjacent=6 fails=0) with "
        "SIX adjacent export suites green beside it (fourth wave 6/6, third "
        "wave 6/6, second wave 6/6, bom-precedence 6/6, composed/landed 6/6, "
        "wordspace 6/6). The worlds were MEASURED BEFORE ANY CODE (%d bytes) "
        "and re-measured AFTER within this window (%d bytes). ONE parent "
        "assertion was amended AT ITS BIRTH SITE with the reason inline: the "
        "first-wave AC-EDWW3 pinned the agreeing UTF-16 landing to delta=None "
        "as a named limitation, and AC-EDXA2 deliberately publishes that "
        "delta, so the assertion now demands delta==0 on BOTH byte orders by "
        "EXACT equality - nothing was loosened. Registry 651 suites / 4882 "
        "criteria -> 652 / 4888 by exactly one row, recounted by import (652 "
        "unique names, 652 unique paths); docs/sandbox-suite-matrix.md read "
        "FAIL stale at the doc evidence face BEFORE any byte and was "
        "regenerated through the shipped render to 66886 bytes at 652 rows / "
        "4888 criteria, after which --check read byte-identical at rc=0 and "
        "its green line honestly reads 651/652 because the stamping leg "
        "predates this suite. Successor limits measured AFTER the fix (%d "
        "bytes)."
        % (evidence_bytes, before_bytes, after_bytes, next_bytes))


def main(argv):
    for path in (EVIDENCE, BEFORE, AFTER, NEXT):
        if not os.path.isfile(path):
            print("E_R2657_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True adjacent=6 fails=0" not in evidence:
        print("E_R2657_EVIDENCE_NOT_GREEN")
        return 4
    if "digest=" not in evidence or "digest=" + ("0" * 16) in evidence:
        print("E_R2657_EMPTY_DIGEST")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2657_EVIDENCE_NOT_TWICE")
        return 4
    next_text = open(NEXT, "rb").read().decode("utf-8")
    for token in ("a_utf16_cut_even", "b_utf16_other_body",
                  "c_utf16_empty_text", "d_double_even_two"):
        if token not in next_text:
            print("E_R2657_NEXT_UNEXPECTED %s" % token)
            return 4
    if "UTF16-BOM-BODY-GAP" not in next_text:
        print("E_R2657_NEXT_NO_GAP")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2657_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2657_ALREADY_DONE")
        return 4

    discharged = "  " + build_discharged(
        len(raw_evidence), len(open(BEFORE, "rb").read()),
        len(open(AFTER, "rb").read()), len(open(NEXT, "rb").read()))
    lines[index] = DONE_PREFIX + row[len("- [ ]"):]
    lines.insert(index + 1, NEXT_SEED)
    lines.insert(index + 2, discharged)
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
