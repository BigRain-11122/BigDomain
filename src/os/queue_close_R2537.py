"""R2537 board closeout for the AC-PNKB1 seed row at state/queue/tech.md:573.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: the name-binding reader merges every function body into ONE table,
so the same name bound in two different functions reads ambiguous even though
each scope is unambiguous.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2535,"
SEED_MARK = "`src/os/probe_seam_nested_key_binding_scope.py`"

DISCHARGED = (
    "  DISCHARGED R2537 (line 573, AC-PNKB1..AC-PNKB6 pinned in that row at "
    "R2535 BEFORE any code): src/os/probe_seam_nested_key_binding_scope.py "
    "plus its suite shipped. A for-loop step that is a NAME bound to a string "
    "constant now RESOLVES at CALL time through the constant tables, in the "
    "module body and in function bodies, and the chain it carries keeps BOTH "
    "the key value and the binding label (D['a'][KEY='b']), so an operator can "
    "see which binding produced which key. An annotated binding, a walrus "
    "step and a walrus-bound name resolve too. A name bound twice with "
    "different values is NAMED ambiguous@hopN and never resolved to either "
    "value, a name bound to a call, a format or a comprehension is NAMED at "
    "its hop and never evaluated (a marker file proved nothing ran), and a "
    "two-element result stays ambiguous. The shipped nested-subscript tables "
    "and law are asked FIRST and never overwritten, so every earlier answer "
    "stands, and the seam classifier is still the shipped registry single "
    "`quiets`. PROOF: AC-PNKB1..AC-PNKB6 SUITE PASS 6/6 TWICE with a "
    "byte-identical criterion digest plus five adjacent probe suites green "
    "(qa/probe-seam-nested-key-binding-scope-R2537.log, 9107B, legs=2 "
    "identical=True fails=0 adjacent=5, landed through the shipped capture "
    "callable); a live leg on the REAL tree reads SEAMS-NESTED-KEY-COVERED "
    "over 1457 probes (3 covered, 179 out-of-scope, 1275 historical, "
    "missing=0, unreadable=0) with the module, the base face and the render "
    "digests unchanged across the reading, and on the SAME fixture this face "
    "follows D['a'][KEY='b'] while the shipped nested face still reads "
    "refused=key@hop2 (qa/probe-seam-nested-key-binding-scope-live-R2537.log, "
    "452B then 730B after the two-reader section, class=tee). The registry "
    "moved by ONE row to 598 suites / 4564 criteria, recounted by importing "
    "reconcile_all.SUITES rather than trusted, and docs/sandbox-suite-matrix.md "
    "was regenerated stamp-aligned from the eligible battery leg "
    "qa/reconcile-all-R2536.log to 57696 bytes at 598/4564 with green=597/598 "
    "self-describing and --check byte-identical at rc=0, after the dry run "
    "failed first by design and wrote no byte. Three defects were measured in "
    "my own first pass and fixed in the CODE rather than in the assertions: a "
    "refusal returned a 2-tuple where the caller unpacked three; the shipped "
    "tables answered a twice-bound name with its LAST value, so the source "
    "bindings are now read first and an ambiguous name is refused rather than "
    "quietly resolved to one; and a walrus STEP (D['a'][(KEY := 'b')]) is a "
    "NamedExpr node that was not a constant, so a str-valued walrus step now "
    "resolves. One FIXTURE was corrected against measurement rather than the "
    "code loosened: a name assigned None and later reassigned is genuinely "
    "two values, so that fixture was replaced by a real walrus binding. LIMIT, "
    "measured this window: the binding reader walks the WHOLE source, so a "
    "name bound in two different function bodies merges into ONE table and "
    "reads ambiguous even though each scope is unambiguous - that shape is the "
    "row seeded below. tasks.md was not touched."
)

SEED = (
    "- [ ] P2 tech seed (R2537, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_scope_awareness.py` - MEASURED this "
    "window on the shipped nested-key face own readers: `_bindings_of` walks "
    "the whole module, so with `def a(): KEY = \"b\"` and `def b(): KEY = "
    "\"c\"`, a loop inside either function reads refused=ambiguous even though "
    "each scope holds exactly one constant; the same over-broad read makes a "
    "function-local name visible to a module-level loop it cannot reach. "
    "Product: ONE reading that resolves a NAME step against the binding table "
    "of the SCOPE the loop is in (module body vs the enclosing function), "
    "publishes which scope it followed, refuses a name that is genuinely "
    "ambiguous INSIDE one scope, and never evaluates anything. Criteria "
    "AC-PNSB1..AC-PNSB6 pre-registered HERE BEFORE any code: AC-PNSB1 a name "
    "bound only inside the enclosing function resolves for a loop in that "
    "function; AC-PNSB2 the SAME name bound differently in a sibling function "
    "does not make it ambiguous; AC-PNSB3 a module-level name stays visible to "
    "a function loop only when the function does not shadow it, and a shadowed "
    "name resolves to the inner binding with the shadow announced; AC-PNSB4 a "
    "name bound twice INSIDE one scope is still NAMED ambiguous at its hop; "
    "AC-PNSB5 the reading stays read-only and every digest it touches is "
    "unchanged; AC-PNSB6 pure ASCII, stdlib only, no clock, zero network, its "
    "own reconcile label and its own suite. Five anchors to re-check "
    "zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_scope_awareness, AC-PNSB, E_PNSB, "
    "os-probe-seam-name-binding-scope-awareness, "
    "test_probe_seam_name_binding_scope_awareness."
)


def main():
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    before = len(text.encode("utf-8"))
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-07 R2537]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2537] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2537")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2537,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("delta %d" % (measured - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())