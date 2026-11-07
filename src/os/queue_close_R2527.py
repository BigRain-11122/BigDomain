"""R2527 board closeout for the AC-PCAS1 seed row at state/queue/tech.md:563.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: an alias whose value is a for-loop over a NAMED constant, a
subscript or attribute chain, or a container element still reads empty and is
not named at all. Reads once, writes once, reads back, prints predicted
against measured bytes.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2525,"
SEED_MARK = "`src/os/probe_seam_constant_alias_scope.py`"

DISCHARGED = (
    "  DISCHARGED R2527 (line 563, AC-PCAS1..AC-PCAS6 pinned in that row at "
    "R2525 BEFORE any code): src/os/probe_seam_constant_alias_scope.py plus "
    "its suite shipped. An ALIAS of an existing constant now resolves to the "
    "SAME value (a plain assignment, an annotated assignment and a walrus "
    "binding, to a fixpoint so an alias of an alias follows the whole chain) "
    "and the row publishes the chain it took; a name bound twice with "
    "different values is dropped as ambiguous instead of keeping one of them. "
    "The shapes that are genuinely not constants are NAMED per name instead "
    "of reading empty - a with-as binding, a for target over two or more "
    "literals, and a value built by a call, a format, an arithmetic "
    "expression or a comprehension - and the row prints them, so an "
    "OUT-OF-SCOPE module no longer hides them. A deep dict chain resolves "
    "with its FULL label, and a chain whose hop is not a dict or whose key is "
    "missing is REFUSED with the label and the hop, never silently None. "
    "BIRTH-SITE REPAIR in the shipped annotated face: its chain label appended "
    "the hops in reverse for any chain deeper than one hop, so a three-hop "
    "reading published pkg.DEEP.NAMES.B.A; the label now reads the hops in the "
    "order they were followed (one-hop labels are unchanged, which is why no "
    "earlier criterion saw it). PROOF: AC-PCAS1..AC-PCAS6 SUITE PASS 6/6 TWICE "
    "with an identical digest plus three adjacent probe faces green "
    "(qa/probe-seam-constant-alias-scope-R2527.log, 7503B, legs=2 "
    "identical=True fails=0 adjacent=3) through the shipped evidence callable "
    "with a read-back; a live leg on the REAL tree reads SEAMS-ALIAS-COVERED "
    "over 1418 probes (3 covered, 173 out-of-scope, 1242 historical, "
    "missing=0) with the module and render digests unchanged, and the SAME "
    "fixture reads COVERED quieted=5 "
    "dynamic=importlib.import_module:pcas_live_helper@ALIAS<-BASE_NAME here "
    "while the shipped annotated face still reads OUT-OF-SCOPE quieted=0 on "
    "it, with a broken chain refused by name "
    "(qa/probe-seam-constant-alias-scope-live-R2527.log, 564B, crlf=0 "
    "lone_cr=0). The registry moved by ONE row to 593 suites / 4534 criteria, "
    "recounted by importing reconcile_all.SUITES rather than trusted, so a "
    "battery on this committed tree is owed BEFORE any further product byte "
    "(opened as reconcile-battery-R2527). tasks.md was not touched."
)

SEED = (
    "- [ ] P2 tech seed (R2527, from this window own measured limit): "
    "`src/os/probe_seam_alias_expression_scope.py` - MEASURED this window on "
    "the face own readers after shipping: `BASE_NAME = \"x\"` then "
    "`for name in (BASE_NAME,):` reads {} from local_bindings and the row "
    "names NO shape at all, so a resolvable loop over a named constant is "
    "still silently empty; `ALIAS: str = pkg.NAMES[0]` reads {} from "
    "module_bindings with no shape named either, so an alias whose value is an "
    "attribute or subscript chain is invisible; and `ALIASES = (BASE,)` keeps "
    "BASE but publishes no alias entry for the container element. Product: ONE "
    "reading that follows those three expressions through the constant tables "
    "and names the ones it refuses, so a loop over a named constant, a "
    "subscript alias and a container element are either resolved with their "
    "chain or published as a refused shape rather than reading empty. "
    "Criteria AC-PCAE1..AC-PCAE6 pre-registered HERE BEFORE any code: "
    "AC-PCAE1 a for-loop over a single constant NAMED item resolves to that "
    "constant and the row carries the chain; AC-PCAE2 an alias whose value is "
    "a subscript or attribute chain into a constant module resolves with the "
    "full chain label, and one that cannot be resolved is NAMED; AC-PCAE3 a "
    "constant element of a container alias is followed or explicitly refused, "
    "never silently absent; AC-PCAE4 a value built by a call, a format or a "
    "run-time expression is still named and never evaluated; AC-PCAE5 the "
    "reading stays read-only and every digest it touches is unchanged; "
    "AC-PCAE6 pure ASCII, stdlib only, no clock, zero network, its own "
    "reconcile label and its own suite. Five anchors to re-check zero-occupancy "
    "at HEAD before any code: probe_seam_alias_expression_scope, AC-PCAE, "
    "E_PCAE, os-probe-seam-alias-expression-scope, "
    "test_probe_seam_alias_expression_scope."
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
    lines[at] = "- [x] [done 2026-11-07 R2527]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2527] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2527")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2527,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("delta %d" % (measured - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())