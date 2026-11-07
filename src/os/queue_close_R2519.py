"""R2519 board closeout for the AC-PDI1 seed row at state/queue/tech.md:555.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: a dynamic import whose module name is a module-level string
constant binding still reads OUT-OF-SCOPE with the call named unresolved.
Reads once, writes once, reads back, prints predicted against measured bytes.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2517,"
SEED_MARK = "`src/os/probe_seam_dynamic_import_scope.py`"

DISCHARGED = (
    "  DISCHARGED R2519 (line 555, AC-PDI1..AC-PDI6 pinned in that row at "
    "R2517 BEFORE any code): src/os/probe_seam_dynamic_import_scope.py plus "
    "its suite shipped. The dynamic call and its module name are DERIVED at "
    "CALL time from the probe own syntax tree: the importlib attribute form, "
    "__import__, a from-import of import_module and a module-level binding of "
    "any of those callables are all recognised, and the helper set is still "
    "read by the same cycle-guarded same-root walk, so a probe that only "
    "builds its import at run time is answered on its own row. A literal "
    "dynamic import of a helper that quiets every seam reads COVERED with the "
    "helper AND the dynamic shape named on the row; a helper that omits a "
    "seam makes the probe MISSING-SEAM naming seam and file and the probe is "
    "never imported or run; a computed name that is not a string constant is "
    "NOT resolved and the row names the unresolved call instead, so it reads "
    "OUT-OF-SCOPE rather than being guessed at or counted as clean; a "
    "dynamically chained helper is followed so a partial middle helper cannot "
    "invent a missing seam; a dynamic import cycle terminates; a bare string "
    "that merely names a helper is not an import; an unparseable source or "
    "helper reads UNREADABLE rather than being skipped; a round-token file "
    "reads HISTORICAL. PROOF: AC-PDI1..AC-PDI6 SUITE PASS 6/6 TWICE with an "
    "identical digest plus three adjacent probe faces green "
    "(qa/probe-seam-dynamic-import-scope-R2519.log, 4172B, legs=2 "
    "identical=True fails=0 adjacent=3) captured through the shipped single "
    "evidence writer, and a live leg on the REAL tree through the same writer "
    "reading SEAMS-DYNAMIC-COVERED over 3 covered probes, 169 out-of-scope "
    "modules and 1214 historical one-shot scripts, with the same fixture "
    "reading OUT-OF-SCOPE under the lazy face so the closed gap is measured "
    "in both readers (qa/probe-seam-dynamic-import-scope-live-R2519.log, "
    "1352B). Registry recounted by import: 588 suites and 4504 criteria "
    "became 589 and 4510 by exactly one row; the matrix was regenerated "
    "stamp-aligned from this round own evidence (59011 bytes, 589 suites, "
    "4510 criteria, green=0/589 because this tree own battery has not run "
    "yet) and --check reads byte-identical."
)

SEED = (
    "- [ ] P2 tech seed (R2519, from this window own measured limit): "
    "`src/os/probe_seam_constant_binding_scope.py` - MEASURED this window in "
    "AC-PDI1 and AC-PDI4 fixtures: a probe that binds the module name to a "
    "string constant at module level and then imports it reads "
    "OUT-OF-SCOPE with the call named unresolved - "
    "`import importlib` / `name = \"quiet_helper\"` / "
    "`def run(): return importlib.import_module(name)` reads "
    "unresolved=['importlib.import_module:name'] quieted=0, while "
    "`importlib.import_module(\"quiet_helper\")` in the same position reads "
    "COVERED, so the one shape between a literal and a computation is still "
    "invisible and a stale probe written that way is never named. Product: "
    "ONE reading that resolves a dynamic module name through the STRING "
    "CONSTANT bindings visible in the probe own tree (a module-level "
    "assignment of a str literal, and a module-level constant tuple or dict "
    "lookup by a constant key), on the same cycle-guarded same-root walk, so "
    "such a probe reads COVERED or MISSING-SEAM on its own row while a name "
    "bound to a real computation still reads OUT-OF-SCOPE and the row names "
    "the unresolved call rather than evaluating it. Criteria AC-PCB1..AC-PCB6 "
    "pre-registered HERE BEFORE any code: AC-PCB1 the binding table is read "
    "from the probe own syntax tree at CALL time, never a hand-written list, "
    "and only str-literal bindings and constant-key lookups are resolved; "
    "AC-PCB2 a probe whose dynamic import names a str-literal binding reads "
    "COVERED with the helper, the binding name and the dynamic shape named on "
    "the row; AC-PCB3 a binding that reaches a helper omitting a seam makes "
    "the probe MISSING-SEAM naming seam and file, and the probe is not run; "
    "AC-PCB4 a name bound to a computation (a call, a join, a format, an "
    "f-string, an imported constant) is NOT resolved and still reads "
    "OUT-OF-SCOPE with the unresolved call named; AC-PCB5 the reading stays "
    "read-only and every digest it touches is unchanged; AC-PCB6 pure ASCII, "
    "stdlib only, no clock, zero network, its own reconcile label and its own "
    "suite. Five anchors to re-check zero-occupancy at HEAD before any code: "
    "probe_seam_constant_binding_scope, AC-PCB, E_PCB, "
    "os-probe-seam-constant-binding-scope, "
    "test_probe_seam_constant_binding_scope."
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
    lines[at] = "- [x] [done 2026-11-07 R2519]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2519] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2519")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2519,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("delta %d" % (measured - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())