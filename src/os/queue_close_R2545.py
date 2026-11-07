"""R2545 board closeout for the AC-PNCG1 seed row at state/queue/tech.md:581.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: the guard face aggregates the guards of a binding, but MEASURED
here four sibling shapes stay unreported - an if/elif/else chain that covers
every path is flattened to the outer pair so the elif own value never appears,
a `match` statement binding a name is not collected at all and reads unbound,
a conditional expression `KEY = "b" if c else "z"` reads a bare shape word, and
a try/except whose two arms bind the SAME literal is refused exactly like the
two-arm if that this window taught it to resolve.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2543,"
SEED_MARK = "`src/os/probe_seam_name_binding_control_flow_guard_scope.py`"

DISCHARGED = (
    "  DISCHARGED R2545 (line 581, AC-PNCG1..AC-PNCG6 pinned in that row at "
    "R2543 BEFORE any code): "
    "src/os/probe_seam_name_binding_control_flow_guard_scope.py plus its suite "
    "shipped. Guards are now AGGREGATED instead of the first one named: the "
    "two arms of ONE if binding the same literal resolve to that value (they "
    "cover every path), two SEPARATE guard groups are published as two groups "
    "each with its own guards rather than one word, every guard on a nested "
    "path is published in order outermost first (guarded:if:2>if:3) instead of "
    "only the innermost, an unconditional binding still wins, and the shipped "
    "control-flow answer is carried on every row beside this face own. The "
    "resolution law is SHAPE based and never evaluates a condition: a pair is "
    "exhaustive only when it is one if with both arms binding one literal "
    "each. PROOF: AC-PNCG1..AC-PNCG6 SUITE PASS 6/6 TWICE with identical "
    "output plus five adjacent probe suites green "
    "(qa/probe-seam-name-binding-control-flow-guard-scope-R2545.log, 13469B, "
    "legs=2 identical=True fails=0 adjacent=5, landed through the shipped "
    "capture callable); a live leg on the REAL tree reads SEAMS-GUARD-COVERED "
    "over 1487 probes (3 covered, 182 out-of-scope, 1302 historical, "
    "missing=0, unreadable=0) written by one UTF-8 LF writer "
    "(qa/probe-seam-name-binding-control-flow-guard-scope-live-R2545.log). The "
    "registry moved by ONE row to 602 suites / 4588 criteria, recounted by "
    "importing reconcile_all.SUITES rather than trusted. BIRTH-SITE DEFECT "
    "FOUND AND REPAIRED IN MY OWN FIRST PASS, disclosed rather than smoothed: "
    "my report took its name set only from the shipped row own followed and "
    "refused keys, so when the shipped face published its answer as ARMS the "
    "name was dropped entirely and the row lost it; the name set now includes "
    "the arms keys and the shipped arms are carried as base_arms. One "
    "ASSERTION was corrected against measurement rather than the code "
    "loosened: the shipped face names the INNERMOST guard on a nested path "
    "(guarded:if:3), not the outer one, so the criterion now states that "
    "measured fact. Four LIMITS were MEASURED this window and are the row "
    "seeded below. tasks.md was not touched."
)

SEED = (
    "- [ ] P2 tech seed (R2545, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_control_flow_guard_exhaustive.py` - "
    "MEASURED this window on the new guard face own reader: (1) "
    "`if a1: KEY=\"b\" elif a2: KEY=\"z\" else: KEY=\"b\"` covers every path "
    "and dominates to \"b\", but the reading flattens it to the outer pair and "
    "reads exclusive-arms, so the elif own value never appears and a provable "
    "single value is withheld; (2) a `match kind: case 1: KEY=\"b\" case _: "
    "KEY=\"z\"` binding is not collected at all, so a loop after it reads "
    "unbound; (3) `KEY = \"b\" if c else \"z\"` reads a bare shape word rather "
    "than either the two operands or a refusal naming them; (4) a try/except "
    "whose two arms bind the SAME literal is refused exactly like the two-arm "
    "if this window taught it to resolve, so the sibling shape is still "
    "withheld. Product: ONE reading that recognises an EXHAUSTIVE path set "
    "beyond a single two-arm if - an if/elif/else chain, a try/except/else "
    "whose arms agree, and a conditional expression - resolves only when every "
    "arm is a literal and they all agree, and otherwise publishes every arm by "
    "name; a match statement is collected as its own guarded group rather than "
    "silently absent. Criteria AC-PNCT1..AC-PNCT6 pre-registered HERE BEFORE "
    "any code: AC-PNCT1 an if/elif/else chain whose arms all bind the same "
    "literal resolves to it, while a chain with two distinct dominant values "
    "publishes every arm; AC-PNCT2 a try/except whose two arms bind the same "
    "literal resolves, while different arms stay refused with both named; "
    "AC-PNCT3 a conditional expression publishes its two operands and resolves "
    "only when they agree; AC-PNCT4 a match statement binding a name is "
    "COLLECTED as a guarded group with its case count and is never resolved; "
    "AC-PNCT5 every answer the shipped control-flow face and this guard face "
    "already gave is carried unchanged; AC-PNCT6 pure ASCII, stdlib only, no "
    "clock, zero network, its own reconcile label and its own suite. Five "
    "anchors to re-check zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_control_flow_guard_exhaustive, AC-PNCT, E_PNCT, "
    "os-probe-seam-name-binding-control-flow-guard-exhaustive, "
    "test_probe_seam_name_binding_control_flow_guard_exhaustive."
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
    lines[at] = "- [x] [done 2026-11-08 R2545]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2545] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2545")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2545,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:60])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())