"""R2541 board closeout for the AC-PNSP1 seed row at state/queue/tech.md:577.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: the position reading resolves the bindings that precede the loop
but it does not read CONTROL FLOW - a binding inside a branch that never runs
still resolves, a with-as binding is not collected at all, and a try/except
with two values reads ambiguous rather than two exclusive branches.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2539,"
SEED_MARK = "`src/os/probe_seam_name_binding_position_scope.py`"

DISCHARGED = (
    "  DISCHARGED R2541 (line 577, AC-PNSP1..AC-PNSP6 pinned in that row at "
    "R2539 BEFORE any code): src/os/probe_seam_name_binding_position_scope.py "
    "plus its suite shipped. A NAME step is now resolved against the bindings "
    "that PRECEDE the loop in its scope, so a loop that runs before its key is "
    "bound is NAMED not-yet-bound and never resolved while the later write is "
    "published on the row as a fact; a class body is its own scope, so a "
    "class-level constant resolves for a loop in that class and a module name "
    "of the same name is announced as shadowed; a name bound before the loop "
    "and REBOUND after it resolves to the earlier value with the later write "
    "published; and a loop spelled inside a comprehension is NAMED with its "
    "own kind (comprehension:list / :set / :dict / :generator) instead of "
    "being dropped. The shipped scope face is asked FIRST, the position tables "
    "add the LINE of each binding rather than replacing that law, the seam "
    "classifier is still the shipped registry single `quiets`, and the report "
    "keeps the base label beside this face own label and verdict word. PROOF: "
    "AC-PNSP1..AC-PNSP6 SUITE PASS 6/6 TWICE with identical output plus five "
    "adjacent probe suites green "
    "(qa/probe-seam-name-binding-position-scope-R2541.log, 14166B, legs=2 "
    "identical=True fails=0 adjacent=5, landed through the shipped capture "
    "callable); a live leg on the REAL tree reads SEAMS-POSITION-COVERED over "
    "1474 probes (3 covered, 180 out-of-scope, 1291 historical, missing=0, "
    "unreadable=0) with the covered probes publishing their own position loop "
    "rows (qa/probe-seam-name-binding-position-scope-live-R2541.log, 1206B, "
    "utf-8, LF). The registry moved by ONE row to 600 suites / 4576 criteria, "
    "recounted by importing reconcile_all.SUITES rather than trusted. Three "
    "LIMITS were MEASURED this window rather than assumed and are the row "
    "seeded below: control flow is not read (a binding inside `if False:` "
    "still resolves), a `with ... as NAME` binding is not collected at all and "
    "reads unbound, and a try/except binding the name twice in two exclusive "
    "branches reads ambiguous. tasks.md was not touched."
)

SEED = (
    "- [ ] P2 tech seed (R2541, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_control_flow_scope.py` - MEASURED this "
    "window on the new position face own reader: (1) a binding written inside "
    "`if False:` still resolves for a loop after it, because the bindings are "
    "collected by walking the syntax tree and no branch is ever asked whether "
    "it runs; (2) a `with open(...) as KEY` binding is not collected at all, "
    "so a loop that reads KEY after the with-block reads unbound; (3) a "
    "try/except that binds the SAME name to two different values in two "
    "exclusive branches reads ambiguous rather than two branches. Product: "
    "ONE reading that refuses to resolve a binding it cannot prove runs before "
    "the loop - a binding inside a branch, a loop or a handler is NAMED with "
    "its guard rather than resolved, a with-as binding is NAMED with that "
    "shape, and an exclusive branch pair publishes both arms instead of one "
    "ambiguity word. Criteria AC-PNCF1..AC-PNCF6 pre-registered HERE BEFORE "
    "any code: AC-PNCF1 a binding inside a branch that may not run is NAMED "
    "with its guard and never resolved, while an unconditional binding before "
    "the loop still resolves; AC-PNCF2 a with-as binding is NAMED with that "
    "shape instead of reading unbound; AC-PNCF3 two exclusive branches binding "
    "the same name publish BOTH arms rather than one ambiguous word; AC-PNCF4 "
    "a binding inside a loop body that may run zero times is NAMED with its "
    "guard; AC-PNCF5 the reading stays read-only and every digest it touches "
    "is unchanged; AC-PNCF6 pure ASCII, stdlib only, no clock, zero network, "
    "its own reconcile label and its own suite. Five anchors to re-check "
    "zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_control_flow_scope, AC-PNCF, E_PNCF, "
    "os-probe-seam-name-binding-control-flow-scope, "
    "test_probe_seam_name_binding_control_flow_scope."
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
    lines[at] = "- [x] [done 2026-11-07 R2541]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2541] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2541")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2541,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:60])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())