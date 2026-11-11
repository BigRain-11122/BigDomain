"""R2653 board closeout for the AC-EDWZ1 seed row at state/queue/tech.md:663.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose limits were MEASURED this window by
src/os/limits_export_composed_landed_next_R2653.py.

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
    REPO, "qa", "export-composed-landed-bom-precedence-fourth-wave-R2653.log")
LIMITS = os.path.join(
    REPO, "qa", "limits-export-composed-landed-fourth-wave-before-R2653.log")
AFTER = os.path.join(
    REPO, "qa", "limits-export-composed-landed-fourth-wave-after-R2653.log")
NEXT = os.path.join(REPO, "qa",
                    "limits-export-composed-landed-next-R2653.log")

SEED_HEAD = "- [ ] P2 tech seed (R2649,"
SEED_MARK = "BOM PRECEDENCE, FOURTH WAVE"
DONE_PREFIX = "- [x] [done 2026-11-12 R2653]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2653, from this window own measured limit): "
    "`src/os/export_composed_landed_face.py` BOM PRECEDENCE, FIFTH WAVE - "
    "three shapes are measured this window with src/os/limits_export_"
    "composed_landed_next_R2653.py against private files "
    "(qa/limits-export-composed-landed-next-R2653.log): (a) a WHOLE UTF-16LE "
    "landing that AGREES with the composed text and one that DISAGREES with "
    "it read the SAME word UTF16-BOM-LANDING with composed=None "
    "(disk=26 and disk=30), so agreement is never decided for a UTF-16 "
    "landing; (b) an ODD body behind TWO markers reads BOM-DOUBLE-MARKER "
    "with body=1 at disk=6, so the remnant is described only by its count "
    "and not named as short; and (c) a UTF-16BE marker with an odd body and "
    "an EVEN two byte body behind a UTF-16LE marker were re-measured AFTER "
    "the fix and read UTF16-BOM-SHORT-BODY composed=26 delta=-23 in its own "
    "byte order and UTF16-BOM-LANDING respectively, both named as already "
    "behaving rather than claimed. Criteria AC-EDXA1..AC-EDXA6 pinned HERE "
    "BEFORE any code: AC-EDXA1 a whole UTF-16 landing is compared with the "
    "composed text in its own byte order and an agreeing one is named apart "
    "from a disagreeing one; AC-EDXA2 that comparison carries both counts, "
    "so a delta is published rather than a bare word; AC-EDXA3 an odd body "
    "behind two markers names BOTH that it sits behind two markers and that "
    "it is short; AC-EDXA4 the even two byte body and the UTF-16BE short "
    "remnant keep the answers measured here; AC-EDXA5 every AC-EDWZ, AC-EDWY, "
    "AC-EDWX, AC-EDWW and AC-EDWV answer survives on its own fixture, "
    "including the legitimate 0xef-leading MIXED payload that stays "
    "TRANSPORT-MIXED with bom=0 and the clean LF PASS; AC-EDXA6 pure ASCII, "
    "stdlib only, no network, no clock, its own reconcile label and its own "
    "suite.")


def build_discharged(evidence_bytes, limits_bytes, after_bytes, next_bytes):
    return (
        "DISCHARGED R2653: extended src/os/export_composed_landed_face.py in "
        "place so the UTF-16 law reads the BODY instead of the marker alone: "
        "a UTF-16 body is an even number of bytes, so an ODD remnant earns "
        "UTF16-BOM-SHORT-BODY with kind=utf16-short and a body size - it is "
        "no longer called a whole landing - and that remnant now carries the "
        "count it was measured against (the whole landing it would have been, "
        "marker included, in the marker own byte order), so delta is "
        "published rather than None. The double-marker law was extended to "
        "describe what sits BEHIND both markers through its own fields (body "
        "and body_transport), so a body is no longer an invisible remainder "
        "under a marker count, while the word itself stays BOM-DOUBLE-MARKER "
        "and the single-word order is unchanged. Added src/os/test_export_"
        "composed_landed_bom_precedence_fourth_wave.py as the "
        "AC-EDWZ1..AC-EDWZ6 suite, wired once into the runner at six "
        "criteria. Proof: SUITE PASS 6/6 on the FIRST run and 6/6 TWICE with "
        "identical criterion lines through the shipped capture callable "
        "(qa/export-composed-landed-bom-precedence-fourth-wave-R2653.log, %d "
        "bytes, legs=2 identical=True adjacent=5 fails=0) with FIVE adjacent "
        "export suites green beside it (third wave 6/6, second wave 6/6, "
        "bom-precedence 6/6, wordspace 6/6, composed/landed 6/6). The four "
        "shapes were MEASURED BEFORE ANY CODE (%d bytes) and re-measured "
        "AFTER within this window (%d bytes). ONE parent assertion was "
        "amended AT ITS BIRTH SITE with the reason inline: the third-wave "
        "suite pinned the one byte remnant to UTF16-BOM-LANDING as a NAMED "
        "limitation, and AC-EDWZ1 deliberately replaces that word, so the "
        "assertion now demands the new word by EXACT equality with the "
        "reason written beside it - nothing was loosened to a subset. "
        "Registry 650 suites / 4876 criteria -> 651 / 4882 by exactly one "
        "row, recounted by import (651 unique names, 651 unique paths); "
        "docs/sandbox-suite-matrix.md read ROWS-MISMATCH 650 against 651 "
        "BEFORE any byte and was regenerated through the shipped write face "
        "to 66751 bytes at 651 rows / 4882 criteria with --check then "
        "reading DOC-CURRENT at rc=0. Successor limits measured AFTER the "
        "fix (%d bytes)."
        % (evidence_bytes, limits_bytes, after_bytes, next_bytes))


def main(argv):
    for path in (EVIDENCE, LIMITS, AFTER, NEXT):
        if not os.path.isfile(path):
            print("E_R2653_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True adjacent=5 fails=0" not in evidence:
        print("E_R2653_EVIDENCE_NOT_GREEN")
        return 4
    if "digest=" not in evidence or "digest=" + ("0" * 16) in evidence:
        print("E_R2653_EMPTY_DIGEST")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2653_EVIDENCE_NOT_TWICE")
        return 4
    next_text = open(NEXT, "rb").read().decode("utf-8")
    for token in ("a_utf16_whole_agree", "c_double_odd_body", "f_clean_lf"):
        if token not in next_text:
            print("E_R2653_NEXT_UNEXPECTED %s" % token)
            return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2653_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2653_ALREADY_DONE")
        return 4

    discharged = "  " + build_discharged(
        len(raw_evidence), len(open(LIMITS, "rb").read()),
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
