"""R2543 board closeout for the AC-PNCF1 seed row at state/queue/tech.md:579.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: the control-flow reading names a guard and publishes two arms of
ONE if, but MEASURED here three shapes stay unreported - two arms binding the
SAME literal refuse as guarded although both arms agree, two SEPARATE if
statements binding one name to two values read as one guard word instead of two
groups, and a NESTED binding publishes only the innermost guard while the outer
guard on the same path is dropped.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2541,"
SEED_MARK = "`src/os/probe_seam_name_binding_control_flow_scope.py`"

DISCHARGED = (
    "  DISCHARGED R2543 (line 579, AC-PNCF1..AC-PNCF6 pinned in that row at "
    "R2541 BEFORE any code): "
    "src/os/probe_seam_name_binding_control_flow_scope.py plus its suite "
    "shipped. A NAME step now resolves ONLY when its binding is proved to run "
    "before the loop: a binding behind a branch is NAMED guarded:if:<line> and "
    "never resolved while an unconditional binding still resolves even when a "
    "later branch rebinds the name; a with-as binding is NAMED with-as instead "
    "of reading unbound; two EXCLUSIVE arms of one if binding two different "
    "literals publish BOTH arms by name instead of one ambiguity word; and a "
    "binding inside a loop body, a try arm or a handler is NAMED with its own "
    "guard. The shipped position face is asked FIRST so every answer it "
    "already gave keeps its answer, the seam classifier is still the shipped "
    "registry single `quiets`, and each row carries the shipped answer beside "
    "this face own. PROOF: AC-PNCF1..AC-PNCF6 SUITE PASS 6/6 TWICE with "
    "identical output plus five adjacent probe suites green "
    "(qa/probe-seam-name-binding-control-flow-scope-R2543.log, 11053B, legs=2 "
    "identical=True fails=0 adjacent=5, landed through the shipped capture "
    "callable); a live leg on the REAL tree reads SEAMS-CONTROL-FLOW-COVERED "
    "over 1481 probes (3 covered, 181 out-of-scope, 1297 historical, "
    "missing=0, unreadable=0) with the covered probes publishing 9 own "
    "control-flow loop rows (qa/probe-seam-name-binding-control-flow-scope-"
    "live-R2543.log, utf-8, LF, single writer). The registry moved by ONE row "
    "to 601 suites / 4582 criteria, recounted by importing "
    "reconcile_all.SUITES rather than trusted. Three LIMITS were MEASURED this "
    "window rather than assumed and are the row seeded below: two arms binding "
    "the SAME literal still refuse as guarded, two separate if statements "
    "binding one name to two values read as one guard word, and a nested "
    "binding publishes only the innermost guard. tasks.md was not touched."
)

SEED = (
    "- [ ] P2 tech seed (R2543, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_control_flow_guard_scope.py` - MEASURED "
    "this window on the new control-flow face own reader: (1) `if c: KEY=\"b\" "
    "else: KEY=\"b\"` refuses as guarded:if:2 although BOTH arms agree, so a "
    "provably single value is withheld; (2) two SEPARATE if statements binding "
    "one name to two different values read as one guard word for the first "
    "statement, so the second group is invisible rather than published; (3) a "
    "binding nested `if a: if b: KEY=\"b\"` publishes only guarded:if:3 and "
    "drops the outer guard on the same path. Product: ONE reading that "
    "aggregates guards instead of naming the first - agreeing arms resolve to "
    "the value they agree on, every guard that stands on the path is "
    "published in order, and two separate guard groups are published as two "
    "groups rather than one word. Criteria AC-PNCG1..AC-PNCG6 pre-registered "
    "HERE BEFORE any code: AC-PNCG1 two arms of one if binding the SAME "
    "literal resolve to that value rather than refusing, while two arms with "
    "different values still publish both; AC-PNCG2 two separate if statements "
    "binding one name to two values publish BOTH groups with their guards, not "
    "one word; AC-PNCG3 a nested binding publishes EVERY guard on its path in "
    "order, outermost first, and never only the innermost; AC-PNCG4 an "
    "unconditional binding still wins and every answer the shipped "
    "control-flow face already gave is carried unchanged; AC-PNCG5 the reading "
    "stays read-only and every digest it touches is unchanged; AC-PNCG6 pure "
    "ASCII, stdlib only, no clock, zero network, its own reconcile label and "
    "its own suite. Five anchors to re-check zero-occupancy at HEAD before any "
    "code: probe_seam_name_binding_control_flow_guard_scope, AC-PNCG, E_PNCG, "
    "os-probe-seam-name-binding-control-flow-guard-scope, "
    "test_probe_seam_name_binding_control_flow_guard_scope."
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
    lines[at] = "- [x] [done 2026-11-08 R2543]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2543] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2543")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2543,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:60])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())