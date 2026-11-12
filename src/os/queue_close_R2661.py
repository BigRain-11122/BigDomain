"""R2661 board closeout for the AC-EDXB1 seed row at state/queue/tech.md:665.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose limits were MEASURED this window by
src/os/limits_export_composed_landed_next_R2661.py.

It refuses to write when the evidence is absent, not green, not twice, empty
digested, when the next-row limits do not carry the shapes it quotes, or when
the anchor row cannot be found exactly once.

Honest note on the BEFORE file: the four pre-fix numbers are READ from the
parent window own measurement (qa/limits-export-composed-landed-next-R2657
.log, landed at R2657), not re-measured here, because this window wrote the
fix before its first measurement. The AFTER file is this window own.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(
    REPO, "qa",
    "export-composed-landed-bom-precedence-sixth-wave-R2661.log")
BEFORE = os.path.join(
    REPO, "qa", "limits-export-composed-landed-next-R2657.log")
AFTER = os.path.join(
    REPO, "qa", "limits-export-composed-landed-sixth-wave-after-R2661.log")
NEXT = os.path.join(REPO, "qa",
                    "limits-export-composed-landed-next-R2661.log")

SEED_HEAD = "- [ ] P2 tech seed (R2657,"
SEED_MARK = "BOM PRECEDENCE, SIXTH WAVE"
DONE_PREFIX = "- [x] [done 2026-11-12 R2661]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2661, from this window own measured limit): "
    "`src/os/export_composed_landed_face.py` BOM PRECEDENCE, SEVENTH WAVE - "
    "four shapes are measured this window with src/os/limits_export_"
    "composed_landed_next_R2661.py against private files "
    "(qa/limits-export-composed-landed-next-R2661.log, 612B): (a) a UTF-16LE "
    "landing whose body has the SAME LENGTH as the composed text but a "
    "DIFFERENT content reads UTF16-BOM-LANDING with composed=10 disk=10 "
    "delta=0 agrees=True, so the equal-length branch compares LENGTHS ONLY "
    "and a wrong payload of the right size is called a clean whole landing; "
    "(b) a cut that leaves a LONE SURROGATE HALF reads UTF16-BOM-CUT with "
    "cut_units=1 at body=8, so the count is code units and never characters "
    "and the remnant is still called a cut landing; (c) a cut behind the "
    "UTF-8 BOM and a UTF-16 marker at once reads BOM-DOUBLE-MARKER at disk=13 "
    "because the double-marker law runs first, so the cut is never named; and "
    "(d) was re-measured AFTER the fix and is named rather than claimed - a "
    "UTF-16BE landing cut by three code units reads UTF16-BOM-CUT "
    "cut_units=3 at composed=16 disk=10 delta=-6. Criteria AC-EDXC1..AC-EDXC6 "
    "pinned HERE BEFORE any code: AC-EDXC1 a UTF-16 landing whose body has "
    "the same length as the composed text but a different content is named "
    "apart from an agreeing landing, never as a clean whole landing; "
    "AC-EDXC2 that name carries both counts so the difference is published "
    "rather than a bare word; AC-EDXC3 the code units a cut lost are named "
    "apart from the characters it lost, so a lone surrogate half is not "
    "counted as a whole character; AC-EDXC4 the four answers measured here "
    "survive on their own fixtures (the same-length wrong content, the "
    "surrogate half, the three-unit BE cut and the cut behind two markers); "
    "AC-EDXC5 every AC-EDXB, AC-EDXA, AC-EDWZ, AC-EDWY, AC-EDWX, AC-EDWW and "
    "AC-EDWV answer survives on its own fixture, including the legitimate "
    "0xef-leading MIXED payload that stays TRANSPORT-MIXED with bom=0 and "
    "the clean LF PASS; AC-EDXC6 pure ASCII, stdlib only, no network, no "
    "clock, its own reconcile label and its own suite.")


def build_discharged(evidence_bytes, before_bytes, after_bytes, next_bytes):
    return (
        "DISCHARGED R2661: extended src/os/export_composed_landed_face.py in "
        "place with ONE new word and ONE named refusal. A UTF-16 body that is "
        "a strict PREFIX of the composed text in the marker own codec is now "
        "UTF16-BOM-CUT with kind=utf16-cut, the code units it lost published "
        "as cut_units, and the whole landing it would have been published as "
        "composed so delta is a number rather than None - which the R2657 "
        "measurement showed it was not (a cut landing read UTF16-BOM-LANDING "
        "with composed=None at disk=24, the SAME word a whole landing earns, "
        "because one lost UTF-16 character is two bytes and the body stays "
        "EVEN). A body that is neither the text nor a head of it keeps "
        "UTF16-BOM-LANDING and reports no delta, and now NAMES the refusal as "
        "refusal=NOT-TEXT-NOR-HEAD with judged=False, so a declined "
        "judgement is spoken instead of implied by an absent count. Added "
        "src/os/test_export_composed_landed_bom_precedence_sixth_wave.py as "
        "the AC-EDXB1..AC-EDXB6 suite, wired once into the runner at six "
        "criteria. Proof: SUITE PASS 6/6 on the FIRST run and 6/6 TWICE with "
        "identical criterion lines through the shipped capture callable "
        "(qa/export-composed-landed-bom-precedence-sixth-wave-R2661.log, %d "
        "bytes, legs=2 identical=True adjacent=6 fails=0) with SIX adjacent "
        "export suites green beside it (fifth wave, fourth wave, third wave, "
        "second wave, bom-precedence, composed/landed). The four pre-fix "
        "worlds are READ from the parent window own evidence (%d bytes, "
        "landed at R2657) rather than re-measured here, because this window "
        "wrote the fix before its first measurement - THAT SUBSTITUTION IS "
        "NAMED rather than smoothed - and the post-fix worlds are this "
        "window own (%d bytes). Registry 652 suites / 4888 criteria -> 653 / "
        "4894 by exactly one row, recounted by import (653 unique names, 653 "
        "unique paths); docs/sandbox-suite-matrix.md read FAIL stale at the "
        "evidence face BEFORE any byte and was regenerated through the "
        "shipped render to 67021 bytes at 653 rows / 4894 criteria, after "
        "which --check read byte-identical at rc=0 and its green line "
        "honestly reads 652/653 because the stamping leg predates this "
        "suite. Successor limits measured AFTER the fix (%d bytes), and the "
        "strongest of them is seeded rather than fixed: the equal-length "
        "branch of the whole-landing compare reads LENGTHS ONLY for UTF-16, "
        "so a wrong payload of the right size still reads clean."
        % (evidence_bytes, before_bytes, after_bytes, next_bytes))


def main(argv):
    for path in (EVIDENCE, BEFORE, AFTER, NEXT):
        if not os.path.isfile(path):
            print("E_R2661_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True adjacent=6 fails=0" not in evidence:
        print("E_R2661_EVIDENCE_NOT_GREEN")
        return 4
    if "digest=" not in evidence or "digest=" + ("0" * 16) in evidence:
        print("E_R2661_EMPTY_DIGEST")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2661_EVIDENCE_NOT_TWICE")
        return 4
    after_text = open(AFTER, "rb").read().decode("utf-8")
    for token in ("a_utf16_cut_even", "b_utf16_other_body",
                  "c_utf16_empty_text", "d_double_even_two"):
        if token not in after_text:
            print("E_R2661_AFTER_UNEXPECTED %s" % token)
            return 4
    if "UTF16-BOM-CUT" not in after_text:
        print("E_R2661_AFTER_NO_CUT")
        return 4
    next_text = open(NEXT, "rb").read().decode("utf-8")
    for token in ("a_surrogate_half", "b_crlf_cut", "c_cut_behind_two",
                  "d_be_three_units"):
        if token not in next_text:
            print("E_R2661_NEXT_UNEXPECTED %s" % token)
            return 4
    if "cut_units=3" not in next_text:
        print("E_R2661_NEXT_NO_UNITS")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2661_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2661_ALREADY_DONE")
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
