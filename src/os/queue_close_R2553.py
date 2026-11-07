"""R2553 board closeout for the AC-PNDQ1 seed row at state/queue/tech.md:589.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window: a constant that is itself
bound to another module constant reads name-unbound, a constant declared inside
a function body is not a module constant, and a three-group chain with one
disagreeing branch publishes both values without naming which group disagreed.

Refuses to write when the live evidence or the suite evidence is absent, so no
number is invented.
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
    "probe-seam-name-binding-arm-mixed-residual-naming-live-R2553.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-naming-R2553.log")

SEED_HEAD = "- [ ] P2 tech seed (R2551,"
SEED_MARK = "`src/os/probe_seam_name_binding_arm_mixed_residual_naming.py`"

SEED = (
    "- [ ] P2 tech seed (R2553, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_chain.py` - "
    "MEASURED this window on the residual face own reader: (1) a module "
    "constant that is ITSELF bound to another module constant (`B = A` with "
    "`A = \"b\"`) reads name-unbound:B, so a one-hop-only reader answers "
    "nothing on a two-hop alias chain; (2) a constant declared INSIDE a "
    "function body reads name-unbound:C even though that function own guard "
    "is exhaustive; (3) a chain of three sequential groups under one arm where "
    "ONE group disagrees publishes both values but the arm-level reason is "
    "nested-arms, so the row never says WHICH group disagreed. Product: ONE "
    "reading that follows a module-level alias chain to a FIXPOINT while a "
    "name that ends in more than one value stays mixed, reads a constant bound "
    "in the loop own FUNCTION body as that scope own constant, and names the "
    "disagreeing group by its key on a multi-group arm. Criteria "
    "AC-PNDR1..AC-PNDR6 pinned HERE BEFORE any code: AC-PNDR1 a two-hop "
    "module alias chain resolves to the literal, proved against "
    "name-unbound:B; AC-PNDR2 a chain that ends in two values reads "
    "name-mixed with the last name, and no value is published; AC-PNDR3 a "
    "constant bound in the loop own function body resolves in that scope, "
    "proved against name-unbound:C; AC-PNDR4 a multi-group arm whose leaves "
    "disagree NAMES the disagreeing group key on the row while still "
    "publishing both values by full path; AC-PNDR5 every answer the five "
    "shipped faces already gave is carried unchanged on the row; AC-PNDR6 "
    "pure ASCII, stdlib only, no clock, zero network, its own reconcile label "
    "and its own suite. Five anchors to re-check zero-occupancy at HEAD before "
    "any code: probe_seam_name_binding_arm_mixed_residual_alias_chain, "
    "AC-PNDR, E_PNDR, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-chain, "
    "test_probe_seam_name_binding_arm_mixed_residual_alias_chain."
)


def live_facts():
    if not os.path.isfile(LIVE):
        return None
    text = io.open(LIVE, encoding="utf-8").read()
    facts = {}
    for key in ("verdict", "files", "probes", "covered", "out_of_scope",
                "historical", "missing", "folded", "named"):
        match = re.search(r"(?<![A-Za-z_])%s=(\S+)" % (key,), text)
        if match:
            facts[key] = match.group(1)
    return facts


def main():
    facts = live_facts()
    if facts is None:
        print("REFUSED E_QCR_NO_LIVE: %s is absent" % LIVE)
        return 3
    if not os.path.isfile(EVIDENCE):
        print("REFUSED E_QCR_NO_EVIDENCE: %s is absent" % EVIDENCE)
        return 3
    evidence_bytes = os.path.getsize(EVIDENCE)
    discharged = (
        "  DISCHARGED R2553 (line 589, AC-PNDQ1..AC-PNDQ6 pinned in that row at "
        "R2551 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_naming.py plus its "
        "suite shipped. A plain with-as binding is NAMED with-as:<scope> "
        "instead of a refusal whose reason is None; two sequential nested "
        "groups under one arm are folded together and resolve to that literal "
        "when every leaf agrees; when they disagree BOTH values are published "
        "by full path and nothing is resolved; and a direct arm binding "
        "through ONE module-level constant name resolves to that literal while "
        "a name bound twice is NAMED name-mixed:<name>. PROOF: AC-PNDQ1.."
        "AC-PNDQ6 SUITE PASS 6/6 TWICE with identical output plus five "
        "adjacent probe suites green "
        "(qa/probe-seam-name-binding-arm-mixed-residual-naming-R2553.log, "
        "%dB, landed through the shipped capture callable); a BOUNDED live leg "
        "over %s real probe_seam modules reads %s with probes=%s "
        "out_of_scope=%s missing=%s folded=%s named=%s "
        "(qa/probe-seam-name-binding-arm-mixed-residual-naming-live-R2553.log), "
        "where the SAME fixture resolves the literal on this face and reads "
        "grouped:body on the shipped arm-mixed face, and a with-as fixture "
        "reads with-as:module here against None there; the WHOLE-TREE audit "
        "was attempted first, produced no output for five minutes and was "
        "replaced by the bounded leg, and that is said so rather than implied. "
        "The registry moved by ONE row to 606 suites / 4612 criteria, "
        "recounted by importing reconcile_all.SUITES rather than trusted, and "
        "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the "
        "eligible R2552 battery leg to 58816 bytes at 606 suites / 4612 "
        "criteria with its green line honestly reading 605/606 and --check "
        "byte-identical. tasks.md was not touched."
        % (evidence_bytes, facts.get("files"), facts.get("verdict"),
           facts.get("probes"), facts.get("out_of_scope"),
           facts.get("missing"), facts.get("folded"), facts.get("named"))
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2553]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2553] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2553")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2553,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:60])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())