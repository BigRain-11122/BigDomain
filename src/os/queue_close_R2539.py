"""R2539 board closeout for the AC-PNSB1 seed row at state/queue/tech.md:575.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: the scope reading ignores SOURCE POSITION (a binding declared
after the loop still resolves), a class body is not a scope it follows (a
class-level name reads unbound), and a loop inside a comprehension is not read
at all.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2537,"
SEED_MARK = "`src/os/probe_seam_name_binding_scope_awareness.py`"

DISCHARGED = (
    "  DISCHARGED R2539 (line 575, AC-PNSB1..AC-PNSB6 pinned in that row at "
    "R2537 BEFORE any code): src/os/probe_seam_name_binding_scope_awareness.py "
    "plus its suite shipped. A NAME step now resolves against the binding "
    "table of the SCOPE the loop is in - the module body and each function "
    "body are read as separate tables, never descending into a nested def or "
    "class - so a name bound only inside the enclosing function resolves for "
    "that function own loop, and the same name bound differently in a SIBLING "
    "function no longer makes it ambiguous. The row publishes WHICH scope the "
    "value was taken from (function:<name> or module) and announces a SHADOW "
    "when a function binding hides a module one. A name bound twice INSIDE one "
    "scope is still NAMED ambiguous at its hop and is never resolved to one of "
    "its values, and a scope with no binding does not borrow another scope own "
    "constants. The shipped nested-key face is asked FIRST, so every answer it "
    "already gave stands, the seam classifier is still the shipped registry "
    "single `quiets`, and the report keeps the base label beside this face own "
    "label and verdict word. PROOF: AC-PNSB1..AC-PNSB6 SUITE PASS 6/6 TWICE "
    "with identical output plus five adjacent probe suites green "
    "(qa/probe-seam-name-binding-scope-awareness-R2539.log, 9505B, legs=2 "
    "identical=True fails=0 adjacent=5, landed through the shipped capture "
    "callable); a live leg on the REAL tree reads SEAMS-NAME-SCOPE-COVERED over "
    "1465 probes (3 covered, 179 out-of-scope, 1283 historical, missing=0, "
    "unreadable=0) with 2762 scope loop rows, and on the SAME fixture (one name "
    "bound differently in two sibling functions) this face follows KEY='b' in "
    "function:first and KEY='zzz' in function:second while the shipped "
    "nested-key face still reads refused=ambiguous@hop2:D['a'][KEY] - the "
    "closed gap is measured on BOTH readers "
    "(qa/probe-seam-name-binding-scope-awareness-live-R2539.log, 635B, "
    "bom=False, crlf=0, lf=8). The registry moved by ONE row to 599 suites / "
    "4570 criteria, recounted by importing reconcile_all.SUITES rather than "
    "trusted, and docs/sandbox-suite-matrix.md was regenerated stamp-aligned "
    "from the eligible battery leg qa/reconcile-all-R2538-retry.log to 57846 "
    "bytes at 599/4570 with green=598/599 self-describing and --check "
    "byte-identical at rc=0, after the dry run failed first by design and wrote "
    "no byte. Three LIMITS were measured this window rather than assumed: a "
    "binding declared AFTER the loop still resolves (source position is not "
    "read), a class body is not a scope this reading follows so a class-level "
    "name reads unbound, and a loop inside a comprehension is not read at all - "
    "all three are the row seeded below. tasks.md was not touched."
)

SEED = (
    "- [ ] P2 tech seed (R2539, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_position_scope.py` - MEASURED this window "
    "on the new scope face own reader: (1) a name bound AFTER the loop still "
    "resolves, because the tables are read per scope and not per position, so "
    "a loop that runs before its key is bound reads as resolved as one that "
    "runs after; (2) a class body is not a scope it follows, so a class-level "
    "constant reads unbound for a loop in that class body while the row "
    "attributes the loop to `module`; (3) a loop inside a comprehension is not "
    "read at all because a comprehension is not an ast.For node. Product: ONE "
    "reading that resolves a NAME through the bindings that PRECEDE the loop "
    "in its scope, treats a class body as its own scope, and names a "
    "comprehension loop instead of dropping it silently. Criteria "
    "AC-PNSP1..AC-PNSP6 pre-registered HERE BEFORE any code: AC-PNSP1 a "
    "binding that precedes the loop resolves and a binding that follows it is "
    "NAMED not-yet-bound and never resolved; AC-PNSP2 a class body is its own "
    "scope, so a class-level constant resolves for a loop in that class and a "
    "module-level name of the same name is shadowed and announced; AC-PNSP3 a "
    "name bound before the loop and REBOUND after it resolves to the earlier "
    "value with the later write published on the row; AC-PNSP4 a loop spelled "
    "inside a comprehension is NAMED with its comprehension kind rather than "
    "dropped; AC-PNSP5 the reading stays read-only and every digest it touches "
    "is unchanged; AC-PNSP6 pure ASCII, stdlib only, no clock, zero network, "
    "its own reconcile label and its own suite. Five anchors to re-check "
    "zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_position_scope, AC-PNSP, E_PNSP, "
    "os-probe-seam-name-binding-position-scope, "
    "test_probe_seam_name_binding_position_scope."
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
    lines[at] = "- [x] [done 2026-11-07 R2539]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2539] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2539")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2539,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:60])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())