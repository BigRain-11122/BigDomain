"""R2523 board closeout for the AC-PLC1 seed row at state/queue/tech.md:559.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: annotated assignments, walrus and for-loop bindings, and a
container reached through a NESTED attribute still read unresolved. Reads once,
writes once, reads back, prints predicted against measured bytes.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2521,"
SEED_MARK = "`src/os/probe_seam_local_constant_scope.py`"

DISCHARGED = (
    "  DISCHARGED R2523 (line 559, AC-PLC1..AC-PLC6 pinned in that row at "
    "R2521 BEFORE any code): src/os/probe_seam_local_constant_scope.py plus "
    "its suite shipped. The string constant table is now read at CALL time "
    "off the probe own syntax tree in TWO scopes - the module body (unchanged) "
    "and the enclosing FUNCTION bodies - with a name dropped as soon as it is "
    "also bound to something that is not a constant anywhere in the tree or to "
    "two different constants, so an ambiguous name is never resolved; a "
    "constant-key lookup into a module-level container is resolved when the "
    "container is reached by a PLAIN ATTRIBUTE on a module file in the SAME "
    "root (opted in by the probe own imports). A probe that declares its "
    "module name inside a function body reads COVERED with helper, binding and "
    "dynamic shape named on the row; a container probe reads COVERED naming "
    "the attribute it was followed through; such a binding that reaches a "
    "helper omitting a seam reads MISSING-SEAM naming seam and file and "
    "neither probe nor helper is imported or run; a name built by a call, a "
    "concatenation, a comprehension or a module container reached through a "
    "call is NOT resolved and the row names the unresolved call instead, so it "
    "reads OUT-OF-SCOPE rather than being guessed at or counted clean; an "
    "unparseable source or helper reads UNREADABLE rather than being skipped; "
    "a round-token file reads HISTORICAL. PROOF: AC-PLC1..AC-PLC6 SUITE PASS "
    "6/6 TWICE with an identical digest plus three adjacent probe faces green "
    "(qa/probe-seam-local-constant-scope-R2523.log, 6833B, legs=2 "
    "identical=True fails=0 adjacent=3) captured through the shipped evidence "
    "callable, and a live leg on the REAL tree through the shipped single "
    "writer reading SEAMS-LOCAL-COVERED over 1400 probes (3 covered, 171 "
    "out-of-scope, 1226 historical) with the module and render digests "
    "unchanged across the reading, while the SAME local fixture reads COVERED "
    "here and OUT-OF-SCOPE quieted=0 under the shipped constant-binding face "
    "and a stale local fixture reads MISSING-SEAM missing=PLRC "
    "(qa/probe-seam-local-constant-scope-live-R2523.log, 1254B, crlf=0). "
    "Registry recounted by import: 590 suites and 4516 criteria became 591 and "
    "4522 by exactly one row; the matrix was regenerated stamp-aligned from "
    "the eligible battery leg qa/reconcile-all-R2522-leg3.log (56905 bytes, "
    "591 suites, 4522 criteria, green=590/591 because this tree own battery "
    "has not run yet) and --check reads byte-identical."
)

SEED = (
    "- [ ] P2 tech seed (R2523, from this window own measured limit): "
    "`src/os/probe_seam_annotated_constant_scope.py` - MEASURED this window "
    "before shipping, on the new face own readers: `NAME: str = \"x\"` is an "
    "AnnAssign and reads {} from BOTH module_bindings and local_bindings, a "
    "walrus binding `if (name := \"x\"):` reads {} from local_bindings, and a "
    "for-loop target `for name in (\"x\",):` reads {} as well, so a probe that "
    "declares its module name in any of those three forms still reads "
    "OUT-OF-SCOPE; and a container reached through a NESTED attribute "
    "(`pkg.CFG.NAMES[0]`) resolves to None because only one attribute hop on a "
    "module file in the same root is followed. Product: ONE reading that "
    "resolves a module name through ANNOTATED assignments (module and function "
    "scope), through a walrus or for-loop binding of a str literal, and "
    "through one more attribute hop on a module-level container, on the same "
    "cycle-guarded same-root walk, so such a probe reads COVERED or "
    "MISSING-SEAM on its own row while a name computed at run time still reads "
    "OUT-OF-SCOPE and the row names the unresolved call. Criteria "
    "AC-PLAC1..AC-PLAC6 pre-registered HERE BEFORE any code: AC-PLAC1 the "
    "extended table is read from the probe own syntax tree at CALL time and "
    "only literally-constant values enter it, never a call; AC-PLAC2 a probe "
    "whose dynamic import names an annotated module-level or function-level "
    "constant reads COVERED with helper, binding and shape named; AC-PLAC3 "
    "such a binding that reaches a helper omitting a seam reads MISSING-SEAM "
    "naming seam and file, and the probe is not run; AC-PLAC4 a value built by "
    "a call, a comprehension or a run-time expression still reads "
    "OUT-OF-SCOPE with the unresolved call named, and an annotated assignment "
    "whose annotation is not a plain name is NOT resolved; AC-PLAC5 the "
    "reading stays read-only and every digest it touches is unchanged; "
    "AC-PLAC6 pure ASCII, stdlib only, no clock, zero network, its own "
    "reconcile label and its own suite. Five anchors to re-check "
    "zero-occupancy at HEAD before any code: "
    "probe_seam_annotated_constant_scope, AC-PLAC, E_PLAC, "
    "os-probe-seam-annotated-constant-scope, "
    "test_probe_seam_annotated_constant_scope."
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
    lines[at] = "- [x] [done 2026-11-07 R2523]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2523] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2523")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2523,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("delta %d" % (measured - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())