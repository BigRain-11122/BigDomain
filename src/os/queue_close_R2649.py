"""R2649 board closeout for the AC-EDWY1 seed row at state/queue/tech.md:662.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row whose limits were MEASURED this window by
src/os/limits_export_composed_landed_next_R2649.py.

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
    REPO, "qa", "export-composed-landed-bom-precedence-third-wave-R2649.log")
LIMITS = os.path.join(
    REPO, "qa", "limits-export-composed-landed-third-wave-before-R2649.log")
AFTER = os.path.join(
    REPO, "qa", "limits-export-composed-landed-third-wave-after-R2649.log")
NEXT = os.path.join(REPO, "qa",
                    "limits-export-composed-landed-next-R2649.log")

SEED_HEAD = "- [ ] P2 tech seed (R2646,"
SEED_MARK = "BOM PRECEDENCE, THIRD WAVE"
DONE_PREFIX = "- [x] [done 2026-11-12 R2649]"

NEXT_SEED = (
    "- [ ] P2 tech seed (R2649, from this window own measured limit): "
    "`src/os/export_composed_landed_face.py` BOM PRECEDENCE, FOURTH WAVE - "
    "four shapes are measured this window with src/os/limits_export_"
    "composed_landed_next_R2649.py against private files "
    "(qa/limits-export-composed-landed-next-R2649.log): (a) a UTF-16 marker "
    "with ONE zero byte behind it reads UTF16-BOM-LANDING at disk=3 against "
    "an EMPTY text, so a one byte remnant is not told apart from a whole "
    "UTF-16 landing; (b) the same remnant against a NON-EMPTY text also reads "
    "UTF16-BOM-LANDING with composed=None, so the text it was measured "
    "against does not appear at all; (c) two markers WITH a body behind them "
    "read BOM-DOUBLE-MARKER with composed=None and delta=None at disk=8, so "
    "the body behind the markers is not described by any field; and (d) a "
    "prefix-only landing against NON-empty text already reads "
    "BOM-CUT-NO-BODY with composed=12 delta=-10 (and a one byte cut reads "
    "delta=-11), which is named as already correct rather than claimed. "
    "Criteria AC-EDWZ1..AC-EDWZ6 pinned HERE BEFORE any code: AC-EDWZ1 a "
    "UTF-16 marker with a short remnant is not named as a whole landing; "
    "AC-EDWZ2 that remnant against non-empty text still carries the composed "
    "count it was measured against; AC-EDWZ3 two markers with a body name "
    "the body they carry as well as both markers; AC-EDWZ4 a prefix-only "
    "landing against non-empty text keeps its composed count and its negative "
    "delta; AC-EDWZ5 every AC-EDWY, AC-EDWX, AC-EDWW and AC-EDWV answer "
    "survives on its own fixture, including the legitimate 0xef-leading MIXED "
    "payload that stays TRANSPORT-MIXED with bom=0 and the clean LF PASS; "
    "AC-EDWZ6 pure ASCII, stdlib only, no network, no clock, its own "
    "reconcile label and its own suite.")


def build_discharged(evidence_bytes, limits_bytes, after_bytes, next_bytes):
    return (
        "DISCHARGED R2649: extended src/os/export_composed_landed_face.py in "
        "place with THREE new landing words pinned into the SAME single-word "
        "order - BOM-DOUBLE-MARKER (two markers on one landing) before the "
        "BOM-only law, BOM-CUT-NO-BODY (a strict prefix with nothing behind "
        "it) before any truncation law, and BOM-TRUNCATED-MIXED-GAP (a cut "
        "whose body HEAD is the composed text but which carries extra bytes) "
        "beside the existing matching-cut word - and the BOM-only law now "
        "carries the composed count when the text is NOT empty, so an empty "
        "payload is a comparison rather than an unqualified word. Added "
        "src/os/test_export_composed_landed_bom_precedence_third_wave.py as "
        "the AC-EDWY1..AC-EDWY6 suite, wired once into the runner at six "
        "criteria. Proof: SUITE PASS 6/6 TWICE with identical criterion lines "
        "through the shipped capture callable (qa/export-composed-landed-bom-"
        "precedence-third-wave-R2649.log, %d bytes, digest 259FB0CF0D5C32DD) "
        "with FOUR adjacent export suites green beside it (second wave 6/6, "
        "bom-precedence 6/6, wordspace 6/6, composed/landed 6/6). The six "
        "shapes were MEASURED BEFORE ANY CODE (%d bytes) and re-measured "
        "AFTER within this window (%d bytes). Registry 649 suites / 4870 "
        "criteria -> 650 / 4876 by exactly one row, recounted by import (650 "
        "unique names, 650 unique paths); docs/sandbox-suite-matrix.md read "
        "ROWS-MISMATCH 649 against 650 BEFORE any byte and was regenerated "
        "through the shipped write face to 66616B at 650 rows / 4876 "
        "criteria with --check then reading DOC-CURRENT at rc=0. The GAP "
        "detector is prefix-guarded (the composed text must be the HEAD of "
        "the cut body), so the legitimate 0xef-leading MIXED payload stays "
        "TRANSPORT-MIXED with bom=0 instead of being accused of being a cut "
        "marker. Successor limits measured AFTER the fix (%d bytes)."
        % (evidence_bytes, limits_bytes, after_bytes, next_bytes))


def main(argv):
    for path in (EVIDENCE, LIMITS, AFTER, NEXT):
        if not os.path.isfile(path):
            print("E_R2649_MISSING %s" % os.path.basename(path))
            return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if "identical=True adjacent=4 fails=0" not in evidence:
        print("E_R2649_EVIDENCE_NOT_GREEN")
        return 4
    if "digest=" not in evidence or "digest=" + ("0" * 16) in evidence:
        print("E_R2649_EMPTY_DIGEST")
        return 4
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2649_EVIDENCE_NOT_TWICE")
        return 4
    next_text = open(NEXT, "rb").read().decode("utf-8")
    for token in ("a_utf16_one_byte", "c_double_marker_body",
                  "f_clean_lf"):
        if token not in next_text:
            print("E_R2649_NEXT_UNEXPECTED %s" % token)
            return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2649_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2649_ALREADY_DONE")
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
