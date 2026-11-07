"""R2529 board closeout for the AC-PCAE1 seed row at state/queue/tech.md:565.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: a for-loop over a NAME bound to a constant CONTAINER still reads
empty and names nothing at all. Reads once, writes once, reads back, prints
predicted against measured bytes.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2527,"
SEED_MARK = "`src/os/probe_seam_alias_expression_scope.py`"

DISCHARGED = (
    "  DISCHARGED R2529 (line 565, AC-PCAE1..AC-PCAE6 pinned in that row at "
    "R2527 BEFORE any code): src/os/probe_seam_alias_expression_scope.py plus "
    "its suite shipped. THREE shapes that read empty now resolve through the "
    "SHIPPED tables and carry the chain they took: a for-loop over a single "
    "NAMED constant (module body and function body), an annotated alias whose "
    "value is a subscript or an attribute chain into a same-root module, and a "
    "container alias whose elements are names (element values are substituted "
    "through a fixpoint, so an alias of an alias follows). Every shape the "
    "reading cannot follow is NAMED on the row instead of reading silently "
    "absent - a call, a format, an arithmetic expression, a comprehension, a "
    "nested container and an unresolvable chain each publish their own short "
    "reason, and a name bound twice with different trees is dropped as "
    "ambiguous. PROOF: AC-PCAE1..AC-PCAE6 SUITE PASS 6/6 TWICE, exit 0 on both "
    "legs, plus five adjacent probe suites green (annotated constant, local "
    "constant, constant alias, dynamic import, registry) "
    "(qa/probe-seam-alias-expression-scope-R2529.log, legs=2 identical=True "
    "fails=0 adjacent=5); a live leg on the REAL tree reads SEAMS-ALIAS-COVERED "
    "over 1424 probes (3 covered, 174 out-of-scope, 1247 historical, "
    "missing=0) with the module and render digests unchanged "
    "(qa/probe-seam-alias-expression-scope-live-R2529.log, exit 0). The "
    "registry moved by ONE row to 594 suites / 4540 criteria, recounted by "
    "importing reconcile_all.SUITES rather than trusted, and "
    "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the "
    "eligible battery leg to 57227 bytes at 594/4540 with green=593/594 "
    "self-describing and --check byte-identical. BIRTH-SITE HONESTY: my first "
    "container reading published nested TREES into the shipped table, and the "
    "shipped element reader raised TypeError on a tuple; the entries were "
    "flattened to the SHIPPED format and a nested container is now refused as "
    "nested by name rather than published unreadable. Two assertions in my own "
    "suite were corrected against measurement, not loosened to fit a claim: "
    "the shipped dynamic face names the CALL-SITE expression (so the binding "
    "reads @name while the chain to the constant is carried separately in "
    "aliases), and the eval/compile guard now allows re.compile while still "
    "forbidding eval, exec and __import__. LIMIT, measured this window: a "
    "for-loop over a NAME bound to a constant CONTAINER still reads empty and "
    "names nothing at all, which is the row seeded below. tasks.md was not "
    "touched."
)

SEED = (
    "- [ ] P2 tech seed (R2529, from this window own measured limit): "
    "`src/os/probe_seam_for_container_name.py` - MEASURED this window on the "
    "face own readers after shipping: `NAMES = (\"x\",)` then "
    "`for name in NAMES:` reads {} for name and the row names NO shape at "
    "all, so a loop over a container NAME is still silently empty even though "
    "the container itself is in the table; a loop over a container reached "
    "through a chain in another module is the same shape one hop out; and a "
    "loop over a container with two or more elements currently reads nothing "
    "and says nothing, where the honest answer is to be NAMED as ambiguous "
    "rather than resolved to one element. Product: ONE reading that follows a "
    "for-loop iterable that is a NAME or a chain into the constant tables, "
    "resolves a single-element container with its chain, refuses a "
    "multi-element one by name, and never evaluates anything. Criteria "
    "AC-PCAF1..AC-PCAF6 pre-registered HERE BEFORE any code: AC-PCAF1 a "
    "for-loop over a NAME bound to a single-element constant container "
    "resolves to that element and the row carries the chain; AC-PCAF2 a "
    "for-loop over a container with two or more elements is NAMED as "
    "ambiguous, never resolved to the first element; AC-PCAF3 a container "
    "reached through an attribute chain in a same-root module resolves, and "
    "one whose chain breaks is NAMED with the hop; AC-PCAF4 a container built "
    "by a call, a format or a comprehension is NAMED and never evaluated; "
    "AC-PCAF5 the reading stays read-only and every digest it touches is "
    "unchanged; AC-PCAF6 pure ASCII, stdlib only, no clock, zero network, its "
    "own reconcile label and its own suite. Five anchors to re-check "
    "zero-occupancy at HEAD before any code: probe_seam_for_container_name, "
    "AC-PCAF, E_PCAF, os-probe-seam-for-container-name, "
    "test_probe_seam_for_container_name."
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
    lines[at] = "- [x] [done 2026-11-07 R2529]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2529] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2529")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2529,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("delta %d" % (measured - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())