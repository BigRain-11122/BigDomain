"""R2535 board closeout for the AC-PCNS1 seed row at state/queue/tech.md:571.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: a step that is a NAME bound to a str constant is refused as a
key, so `D["a"][KEY]` names the hop but never resolves it.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2533,"
SEED_MARK = "`src/os/probe_seam_nested_subscript_scope.py`"

DISCHARGED = (
    "  DISCHARGED R2535 (line 571, AC-PCNS1..AC-PCNS6 pinned in that row at "
    "R2533 BEFORE any code): src/os/probe_seam_nested_subscript_scope.py plus "
    "its suite shipped. ONE shape that read a bare word now resolves and "
    "carries EVERY key: a for-loop whose iterable is a CHAIN of two or more "
    "constant string subscripts on a literal container, in the module body and "
    "in function bodies, but ONLY when the resolved container holds exactly "
    "one element. A missing key, an integer index into a tuple, a call, a "
    "format and a comprehension step are NAMED together with the HOP that "
    "broke (key@hop2, index@hop2, call@hop2, format@hop2, "
    "comprehension@hop1) rather than a bare shape word, a two-element result "
    "is NAMED ambiguous and never resolved to its first element, and an index "
    "step is never followed because a position is not a named slot. The "
    "shipped subscript tables and law are asked FIRST and never overwritten, "
    "so every earlier answer stands, and the seam classifier is still the "
    "shipped registry single `quiets`. PROOF: AC-PCNS1..AC-PCNS6 SUITE PASS "
    "6/6 TWICE with byte-identical output and exit 0 on both legs plus five "
    "adjacent probe suites green (subscript container, container name, dynamic "
    "import, registry, alias expression) "
    "(qa/probe-seam-nested-subscript-scope-R2535.log, 8446B, legs=2 "
    "identical=True fails=0 adjacent=5, landed through the shipped capture "
    "callable); a live leg on the REAL tree reads "
    "SEAMS-NESTED-SUBSCRIPT-COVERED over 1447 probes (3 covered, 177 "
    "out-of-scope, 1267 historical, missing=0) with the module, the base face "
    "and the render digests unchanged across the reading, and on the SAME "
    "fixture this face follows D['a']['b'] while the shipped subscript face "
    "still reads refused=nested "
    "(qa/probe-seam-nested-subscript-scope-live-R2535.log, 672B, crlf=0, "
    "bom=False). The registry moved by ONE row to 597 suites / 4558 criteria, "
    "recounted by importing reconcile_all.SUITES rather than trusted, and "
    "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the "
    "eligible battery leg qa/reconcile-all-R2533.log to 57572 bytes at "
    "597/4558 with green=596/597 self-describing and --check byte-identical. "
    "BIRTH-SITE HONESTY: THREE defects were measured in my own first pass and "
    "fixed in the CODE rather than in the assertions - the reading delegated "
    "the helper walk to the wrong shipped face (AttributeError on "
    "helper_scope) and was pointed at the container-name face; a function-body "
    "chain could not see a MODULE-level literal container, so the local "
    "literal table is now the module table shadowed by the function table; and "
    "a format step was named call because the label was read off the wrong "
    "shipped face, so the format word is now derived from the AST node itself. "
    "One report noise source was also removed: the inherited refusal of the "
    "container NAME itself is filtered to for-loop targets, so the row speaks "
    "only about loop bindings. LIMIT, measured this window: a step that is a "
    "NAME bound to a str constant (`KEY = \"b\"` then `D[\"a\"][KEY]`) is "
    "NAMED with its hop but is NOT resolved - that shape is the row seeded "
    "below. tasks.md was not touched."
)

SEED = (
    "- [ ] P2 tech seed (R2535, from this window own measured limit): "
    "`src/os/probe_seam_nested_key_binding_scope.py` - MEASURED this window on "
    "the shipped nested face own readers: with `KEY = \"b\"` in scope, "
    "`for n in D[\"a\"][KEY]:` reads refused=key@hop2 and names the step, but "
    "the honest answer is available - KEY is a literal string constant in the "
    "SAME scope and the container holds exactly one element, so the chain "
    "`D['a']['b']` is derivable without evaluating anything. The same silence "
    "hits an annotated binding (`KEY: str = \"b\"`) and a walrus binding, and "
    "an ambiguous name bound twice is the one case that must stay refused. "
    "Product: ONE reading that resolves a NAME step through the constant "
    "tables at CALL time, publishes the chain with the binding label it "
    "followed, refuses an ambiguous or non-constant name by NAME with the hop, "
    "and never evaluates anything. Criteria AC-PNKB1..AC-PNKB6 pre-registered "
    "HERE BEFORE any code: AC-PNKB1 a step naming a literal str constant "
    "resolves and the row carries the chain with BOTH the key value and the "
    "binding label; AC-PNKB2 an annotated or walrus binding of the same "
    "constant resolves too, and a name bound twice with different values is "
    "NAMED ambiguous at its hop; AC-PNKB3 a name bound to a call, a format or "
    "a comprehension is NAMED at its hop and never evaluated; AC-PNKB4 a chain "
    "that mixes a literal key and a named key still resolves in order and "
    "carries every step; AC-PNKB5 the reading stays read-only and every digest "
    "it touches is unchanged; AC-PNKB6 pure ASCII, stdlib only, no clock, zero "
    "network, its own reconcile label and its own suite. Five anchors to "
    "re-check zero-occupancy at HEAD before any code: "
    "probe_seam_nested_key_binding_scope, AC-PNKB, E_PNKB, "
    "os-probe-seam-nested-key-binding-scope, "
    "test_probe_seam_nested_key_binding_scope."
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
    lines[at] = "- [x] [done 2026-11-07 R2535]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2535] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2535")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2535,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("delta %d" % (measured - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())