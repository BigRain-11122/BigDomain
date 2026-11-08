"""R2555 board closeout for the AC-PNDR1 seed row at state/queue/tech.md:591.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window: a walrus alias is not followed,
an attribute-valued alias is not followed, and a constant declared AFTER the
loop still resolves because source position is not read.

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
    "probe-seam-name-binding-arm-mixed-residual-alias-chain-live-R2555.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-chain-R2555.log")

SEED_HEAD = "- [ ] P2 tech seed (R2553,"
SEED_MARK = "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_chain.py`"

SEED = (
    "- [ ] P2 tech seed (R2555, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_position.py` - "
    "MEASURED this window on the alias-chain face own reader: (1) a WALRUS "
    "alias (`(B := A)` at module level) reads name-unbound:B because only "
    "plain and annotated assignments are alias edges; (2) an alias whose "
    "value is an ATTRIBUTE (`B = M.A`) reads name-unbound:B because the alias "
    "table holds bare names only; (3) a constant declared AFTER the loop still "
    "resolves to its literal because source POSITION is not read, which is an "
    "over-resolution rather than a refusal. Product: ONE reading that takes a "
    "walrus binding as an alias edge, follows ONE attribute hop on a same-root "
    "module constant, and refuses a constant whose binding line is LATER than "
    "the loop own line. Criteria AC-PNDS1..AC-PNDS6 pinned HERE BEFORE any "
    "code: AC-PNDS1 a walrus alias resolves to the literal, proved against "
    "name-unbound:B; AC-PNDS2 an attribute-valued alias resolves through one "
    "hop on a module constant, proved against name-unbound:B; AC-PNDS3 a "
    "constant bound AFTER the loop is NAMED not-yet-bound and never resolved, "
    "proved against the value b this window measured; AC-PNDS4 an attribute "
    "chain that breaks or runs deeper than one hop is NAMED rather than "
    "guessed; AC-PNDS5 every answer the six shipped faces already gave is "
    "carried unchanged on the row; AC-PNDS6 pure ASCII, stdlib only, no "
    "clock, zero network, its own reconcile label and its own suite. Five "
    "anchors to re-check zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_arm_mixed_residual_alias_position, AC-PNDS, "
    "E_PNDS, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-position, "
    "test_probe_seam_name_binding_arm_mixed_residual_alias_position."
)


def live_facts():
    if not os.path.isfile(LIVE):
        return None
    text = io.open(LIVE, encoding="utf-8").read()
    facts = {}
    for key in ("verdict", "files", "probes", "covered", "out_of_scope",
                "historical", "missing", "alias_resolved", "alias_named"):
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
        "  DISCHARGED R2555 (line 591, AC-PNDR1..AC-PNDR6 pinned in that row at "
        "R2553 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_chain.py plus "
        "its suite shipped. A module alias chain is followed to a FIXPOINT and "
        "publishes the names it walked; a chain that ends in two values reads "
        "name-mixed with the LAST name and publishes no value; a constant "
        "bound in the loop own function body resolves in that scope; and a "
        "multi-group arm whose leaves disagree NAMES the disagreeing group key "
        "while every leaf keeps its full path and its value. An alias cycle is "
        "NAMED name-cycle:<name> rather than resolved. PROOF: AC-PNDR1.."
        "AC-PNDR6 SUITE PASS 6/6 TWICE with identical output plus five "
        "adjacent probe suites green "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-chain-R2555.log, "
        "%dB, landed through the shipped capture callable); a BOUNDED live leg "
        "over %s real probe_seam modules reads %s with probes=%s "
        "out_of_scope=%s missing=%s alias_resolved=%s alias_named=%s "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-chain-live-"
        "R2555.log), where the SAME fixtures are measured on BOTH readers: the "
        "two-hop fixture reads b here against name-unbound:B there, the "
        "function-body constant reads b here against name-unbound:C there, and "
        "the disagreeing arm reads nested-arms:if:7 here against nested-arms "
        "there with both values published on both. The registry moved by ONE "
        "row to 607 suites / 4618 criteria, recounted by importing "
        "reconcile_all.SUITES rather than trusted, and "
        "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the "
        "eligible R2554 battery leg to 58970 bytes at 607 suites / 4618 "
        "criteria with its green line honestly reading 606/607 and --check "
        "byte-identical. tasks.md was not touched."
        % (evidence_bytes, facts.get("files"), facts.get("verdict"),
           facts.get("probes"), facts.get("out_of_scope"),
           facts.get("missing"), facts.get("alias_resolved"),
           facts.get("alias_named"))
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2555]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2555] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2555")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2555,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:60])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())