"""R2549 board closeout for the AC-PNCD1 seed row at state/queue/tech.md:585.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: a nested guard tree now folds to its ROOT group when every leaf
agrees, but an arm that binds directly AND contains a nested group is refused
as mixed:<arm>, a try nested under an arm keeps its own incomplete refusal
when it carries an else or a finally, and a with-as binding is never counted
as coverage so it reads non-literal:<arm> rather than with-as.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2547,"
SEED_MARK = "`src/os/probe_seam_name_binding_nested_exhaustive_path.py`"

DISCHARGED = (
    "  DISCHARGED R2549 (line 585, AC-PNCD1..AC-PNCD6 pinned in that row at "
    "R2547 BEFORE any code): "
    "src/os/probe_seam_name_binding_nested_exhaustive_path.py plus its suite "
    "shipped. A guard tree now folds to its ROOT group and resolves ONLY when "
    "every group on it covers every path AND every LEAF binds the same single "
    "literal, so a nested if that agrees on all three leaves resolves where "
    "the shipped exhaustive face published two groups and withheld the value. "
    "An arm that binds nothing is NAMED partial:<arm> instead of being "
    "counted as an arm binding, a loop standing on the path is NAMED "
    "loop:<line> instead of being folded into coverage, and leaves that "
    "DISAGREE publish every leaf by its full path (if:2/body>if:3/else) rather "
    "than one word. MEASURED this window and disclosed rather than smoothed: "
    "on the partial fixture and on the loop-under-an-arm fixture the shipped "
    "exhaustive face RESOLVED a value the tree does not prove (part=\"b\" with "
    "the outer else binding nothing; loop=\"b\" under a for that may run zero "
    "times), and this face refuses both, with the shipped answers still "
    "carried verbatim on every row as base_* fields. PROOF: AC-PNCD1..AC-PNCD6 "
    "SUITE PASS 6/6 TWICE with identical output plus five adjacent probe "
    "suites green (qa/probe-seam-name-binding-nested-exhaustive-path-R2549.log, "
    "27885B, legs=2 identical=True fails=0 adjacent=5, landed through the "
    "shipped capture callable); a live leg on the REAL tree reads "
    "SEAMS-NESTED-COVERED over 1499 probes (3 covered, 184 out-of-scope, 1312 "
    "historical, missing=0) with every digest unchanged and the SAME fixtures "
    "measured on BOTH readers (qa/probe-seam-name-binding-nested-exhaustive-path"
    "-live-R2549.log, 557B, utf-8 LF, crlf=0). The registry moved by ONE row to "
    "604 suites / 4600 criteria, recounted by importing reconcile_all.SUITES "
    "rather than trusted, and docs/sandbox-suite-matrix.md was regenerated "
    "stamp-aligned to 58526 bytes at 604 suites / 4600 criteria with its green "
    "line honestly reading 603/604 and --check byte-identical. One assertion "
    "of mine was corrected against measurement rather than the code loosened "
    "(the fold returns its arms as a LIST of per-result rows, so the criterion "
    "states that measured shape). tasks.md was not touched."
)

SEED = (
    "- [ ] P2 tech seed (R2549, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_nested_arm_mixed_scope.py` - MEASURED "
    "this window on the nested exhaustive face own reader: (1) an arm that "
    "binds the name DIRECTLY and also contains a nested guard reading mixed:<arm> "
    "and never resolves, even when the direct value and every nested leaf "
    "agree; (2) a try nested under an arm that carries an else or a finally "
    "reads incomplete:<group> even when every handler arm agrees and the else "
    "arm rebinds the same literal; (3) a `with ... as KEY` binding inside an "
    "arm reads non-literal:<arm> and is never named with-as, so a with-bound "
    "key hides the reason it was refused. Product: ONE reading that merges a "
    "direct arm binding with its nested tree when they agree on ONE literal, "
    "treats an else that rebinds the same literal as coverage while an else "
    "that binds nothing stays partial, and names a with-as binding as "
    "with-as:<arm> rather than a shape word. Criteria AC-PNDP1..AC-PNDP6 "
    "pinned HERE BEFORE any code: AC-PNDP1 a direct arm binding plus an "
    "agreeing nested tree resolves to that literal, proved against this "
    "window face which reads mixed:<arm>; AC-PNDP2 a direct binding that "
    "DISAGREES with a nested leaf publishes both by full path and resolves "
    "nothing; AC-PNDP3 a try with an else rebinding the same literal resolves "
    "while an else binding nothing is NAMED partial:else; AC-PNDP4 a with-as "
    "binding inside an arm is NAMED with-as:<arm> and never resolved; "
    "AC-PNDP5 every answer the two shipped faces and this window face already "
    "gave is carried unchanged on the row; AC-PNDP6 pure ASCII, stdlib only, "
    "no clock, zero network, its own reconcile label and its own suite. Five "
    "anchors to re-check zero-occupancy at HEAD before any code: "
    "probe_seam_nested_arm_mixed_scope, AC-PNDP, E_PNDP, "
    "os-probe-seam-name-binding-nested-arm-mixed-scope, "
    "test_probe_seam_name_binding_nested_arm_mixed_scope."
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
    lines[at] = "- [x] [done 2026-11-08 R2549]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2549] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2549")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2549,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:60])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())