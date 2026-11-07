"""R2547 board closeout for the AC-PNCT1 seed row at state/queue/tech.md:583.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: the exhaustive-path face resolves a group only when its root node
covers EVERY path, but MEASURED here an exhaustive chain NESTED inside another
arm is published as TWO groups and never resolved even when every inner arm
agrees, a try arm whose binding sits under a further nested block keeps that
inner guard, and a binding written on only SOME statements of an arm is still
counted as an arm binding because the reading is shape based rather than flow
sensitive.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2545,"
SEED_MARK = "`src/os/probe_seam_name_binding_control_flow_guard_exhaustive.py`"

DISCHARGED = (
    "  DISCHARGED R2547 (line 583, AC-PNCT1..AC-PNCT6 pinned in that row at "
    "R2545 BEFORE any code): "
    "src/os/probe_seam_name_binding_control_flow_guard_exhaustive.py plus its "
    "suite shipped. A binding now resolves ONLY when its guard group covers "
    "EVERY path and every arm binds the same single literal: an if/elif/else "
    "chain with a final else resolves where the shipped guard face withheld "
    "the elif arm entirely, a one-handler try/except with no else and no "
    "finally resolves when both arms agree, and a conditional expression "
    "publishes both operands (condexpr:b|z) and resolves only when they agree. "
    "A group whose arms differ publishes EVERY arm by name instead of one "
    "incomplete pair, and a match statement is COLLECTED as its own group with "
    "its case count (match:2-cases) and never resolved where the shipped face "
    "read the name unbound. The shipped guard and control-flow answers are "
    "carried on every row beside this face own, and the seam classifier is "
    "still the shipped registry single quiets. PROOF: AC-PNCT1..AC-PNCT6 SUITE "
    "PASS 6/6 TWICE with identical output plus five adjacent probe suites "
    "green (qa/probe-seam-name-binding-control-flow-guard-exhaustive-R2547.log, "
    "28865B, legs=2 identical=True fails=0 adjacent=5, landed through the "
    "shipped capture callable); a live leg on the REAL tree reads "
    "SEAMS-EXHAUSTIVE-COVERED over 1492 probes (3 covered, 183 out-of-scope, "
    "1306 historical, missing=0, unreadable=0) and the SAME agreeing-chain "
    "fixture reads ok/b here while the shipped guard face still reads "
    "guarded:if:2, written by one UTF-8 LF writer "
    "(qa/probe-seam-name-binding-control-flow-guard-exhaustive-live-R2547.log). "
    "The registry moved by ONE row to 603 suites / 4594 criteria, recounted by "
    "importing reconcile_all.SUITES rather than trusted, and "
    "docs/sandbox-suite-matrix.md was regenerated stamp-aligned to 58383 bytes "
    "with its green line honestly reading 602/603. One ASSERTION was corrected "
    "against measurement rather than the code loosened: the shipped guard face "
    "publishes the INNER pair of a differing chain as arms (not as a refusal), "
    "so the criterion now states that measured fact. Four LIMITS were MEASURED "
    "this window and are the row seeded below. tasks.md was not touched."
)

SEED = (
    "- [ ] P2 tech seed (R2547, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_nested_exhaustive_path.py` - MEASURED "
    "this window on the exhaustive face own reader: (1) "
    "`if a: (if b: KEY=\"b\" else: KEY=\"b\") else: KEY=\"b\"` agrees on every "
    "path yet reads as TWO groups (if:3 exhaustive, if:2 covering only its "
    "else arm) and is therefore never resolved, because the group key is the "
    "INNERMOST If and the outer arm that only contains a block binds nothing; "
    "(2) a binding written on only SOME statements of a try arm is still "
    "counted as that arm binding, so an arm that binds nothing on one path is "
    "published as if it did; (3) a loop inside an arm keeps the shipped loop "
    "guard and is never folded into the root group own coverage. Product: ONE "
    "reading that folds a nested guard whose every leaf agrees into the ROOT "
    "group own coverage - an arm that contains only a block is unwrapped to "
    "that block own arms, and the group resolves only when EVERY leaf path of "
    "the folded tree binds the same single literal - while a leaf that binds "
    "nothing, a partially binding arm and a loop inside an arm are NAMED "
    "rather than guessed. Criteria AC-PNCD1..AC-PNCD6 pre-registered HERE "
    "BEFORE any code: AC-PNCD1 a nested if that agrees on every leaf resolves "
    "to that value, proved against the exhaustive face which publishes two "
    "groups and resolves nothing; AC-PNCD2 an arm that binds nothing on one of "
    "its paths is NAMED partial:<arm> and never resolved; AC-PNCD3 a loop "
    "inside an arm is NAMED loop:<line> and never folded into coverage; "
    "AC-PNCD4 a nested tree whose leaves DISAGREE publishes every leaf by its "
    "full path rather than one word; AC-PNCD5 every answer the shipped guard "
    "face and this exhaustive face already gave is carried unchanged on the "
    "row; AC-PNCD6 pure ASCII, stdlib only, no clock, zero network, its own "
    "reconcile label and its own suite. Five anchors to re-check zero-"
    "occupancy at HEAD before any code: "
    "probe_seam_name_binding_nested_exhaustive_path, AC-PNCD, E_PNCD, "
    "os-probe-seam-name-binding-nested-exhaustive-path, "
    "test_probe_seam_name_binding_nested_exhaustive_path."
)


def main():
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2547]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2547] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2547")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2547,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:60])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())