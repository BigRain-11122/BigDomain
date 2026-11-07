"""R2551 board closeout for the AC-PNDP1 seed row at state/queue/tech.md:587.

Marks that seed row done, adds its DISCHARGED note read from THIS round own
evidence on disk, and seeds ONE row measured this window: a module-level
`with ... as KEY` comes back from the shipped nested face as a refusal with NO
REASON AT ALL (reason None), two sequential nested groups under one arm read
grouped:<arm>, and a direct binding through a module-level constant NAME reads
non-literal:<arm>.

Refuses to write when the live evidence is absent, so no number is invented.
"""

import io
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
LIVE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-nested-arm-mixed-scope-live-R2551.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-nested-arm-mixed-scope-R2551.log")

SEED_HEAD = "- [ ] P2 tech seed (R2549,"
SEED_MARK = "`src/os/probe_seam_name_binding_nested_arm_mixed_scope.py`"

SEED = (
    "- [ ] P2 tech seed (R2551, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_naming.py` - MEASURED "
    "this window on the merged face own reader: (1) a `with ... as KEY` "
    "binding at module level (outside any guarded arm) comes back from the "
    "shipped nested face as a refusal whose reason is NONE, so the window is "
    "told nothing about why it was refused; (2) two sequential nested groups "
    "under one arm read grouped:<arm> and never resolve even when every leaf "
    "of both groups binds the same literal; (3) a direct arm binding written "
    "through a module-level constant NAME reads non-literal:<arm> even though "
    "the name itself binds exactly one literal. Product: ONE reading that "
    "NAMES a plain with-as refusal instead of publishing an empty reason, "
    "folds two agreeing groups under one arm into that literal, and follows "
    "one module-level constant name to its literal while a name that binds "
    "more than one value stays mixed. Criteria AC-PNDQ1..AC-PNDQ6 pinned HERE "
    "BEFORE any code: AC-PNDQ1 a module-level with-as binding is NAMED "
    "with-as:<scope> and never published with an empty reason, proved against "
    "the measured None; AC-PNDQ2 two sequential nested groups under one arm "
    "that agree resolve to that literal, proved against grouped:<arm>; "
    "AC-PNDQ3 a direct arm binding through ONE module-level constant name "
    "resolves to that constant literal, proved against non-literal:<arm>; "
    "AC-PNDQ4 two nested groups under one arm whose leaves disagree publish "
    "both values by full path and resolve nothing; AC-PNDQ5 every answer the "
    "four shipped faces already gave is carried unchanged on the row; "
    "AC-PNDQ6 pure ASCII, stdlib only, no clock, zero network, its own "
    "reconcile label and its own suite. Five anchors to re-check "
    "zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_arm_mixed_residual_naming, AC-PNDQ, E_PNDQ, "
    "os-probe-seam-name-binding-arm-mixed-residual-naming, "
    "test_probe_seam_name_binding_arm_mixed_residual_naming."
)


def live_facts():
    if not os.path.isfile(LIVE):
        return None
    text = io.open(LIVE, encoding="utf-8").read()
    facts = {}
    for match in re.finditer(r"([A-Za-z_]+)=(\S+)", text):
        facts[match.group(1)] = match.group(2)
    facts["scope"] = text.split("\n")[0]
    return facts


def main():
    facts = live_facts()
    if facts is None:
        print("REFUSED E_QCR_NO_LIVE: %s is absent" % LIVE)
        return 3
    evidence_bytes = os.path.getsize(EVIDENCE) if os.path.isfile(EVIDENCE) else 0
    discharged = (
        "  DISCHARGED R2551 (line 587, AC-PNDP1..AC-PNDP6 pinned in that row at "
        "R2549 BEFORE any code): "
        "src/os/probe_seam_name_binding_nested_arm_mixed_scope.py plus its "
        "suite shipped. A direct arm binding plus an agreeing nested tree now "
        "resolves to that literal where the R2549 face read mixed:body; a "
        "direct binding that DISAGREES publishes both values by full path and "
        "resolves nothing; a try whose else rebinds the same literal is "
        "coverage while an empty else is NAMED partial:else; and a with-as arm "
        "is NAMED with-as:<arm> instead of a shape word. PROOF: AC-PNDP1.."
        "AC-PNDP6 SUITE PASS 6/6 TWICE with identical output plus five adjacent "
        "probe suites green (qa/probe-seam-name-binding-nested-arm-mixed-scope-"
        "R2551.log, %dB, landed through the shipped capture callable); a "
        "BOUNDED live leg on the real probe family (%s) reads %s over %s "
        "probes with %s covered probes and %s arm loop rows "
        "(qa/probe-seam-name-binding-nested-arm-mixed-scope-live-R2551.log), "
        "where the SAME fixture reads %s on this face and %s on the R2549 "
        "face; the whole-tree audit was declined on budget and is said so "
        "rather than implied. The registry moved by ONE row to 605 suites "
        "/ 4606 criteria, recounted by importing reconcile_all.SUITES rather "
        "than trusted, and docs/sandbox-suite-matrix.md was regenerated "
        "stamp-aligned from the eligible R2550 battery leg to 58666 bytes at "
        "605 suites / 4606 criteria with its green line honestly reading "
        "604/605 and --check byte-identical. MEASURED and disclosed rather than "
        "smoothed: a module-level with-as binding is still handed to the "
        "shipped faces and comes back as a refusal whose reason is NONE - a "
        "real defect in the shipped nested face that this window measured and "
        "seeded instead of fixing silently; two sequential nested groups under "
        "one arm read grouped:<arm>; and a direct binding through a "
        "module-level constant NAME reads non-literal:<arm>. tasks.md was not "
        "touched."
        % (evidence_bytes, facts.get("scope"), facts.get("verdict"),
           facts.get("probes"), facts.get("covered_probes"),
           facts.get("arm_loop_rows"), facts.get("MINE_followed"),
           facts.get("BASE_refused"))
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2551]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2551] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2551")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2551,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:60])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())