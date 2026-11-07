"""R2517 board closeout for the AC-PSL1 seed row at state/queue/tech.md:553.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: a probe that builds its import at RUN time (importlib or
__import__ with a computed name) reads OUT-OF-SCOPE with zero quieted seams
because only import STATEMENTS are read. Reads once, writes once, reads back,
prints predicted against measured bytes.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2515,"
SEED_MARK = "`src/os/probe_seam_lazy_scope.py`"

DISCHARGED = (
    "  DISCHARGED R2517 (line 553, AC-PSL1..AC-PSL6 pinned in that row at "
    "R2515 BEFORE any code): src/os/probe_seam_lazy_scope.py plus its suite "
    "shipped. Import resolution is DERIVED at CALL time from the probe own "
    "syntax tree at ANY nesting level (module body, function body, method "
    "body), so the same cycle-guarded same-root walk that the forwarding face "
    "runs now also reaches a helper named only inside a function; each row "
    "names the helpers it was followed through AND the lazy imports it took, "
    "so the shape is visible rather than inferred. A probe that quiets nothing "
    "itself but lazily imports a helper that does reads COVERED; the same "
    "fixture reads OUT-OF-SCOPE under the module-level forwarding face, which "
    "is the closed gap measured on one fixture in both readers; a lazy helper "
    "that omits a seam makes the probe MISSING-SEAM naming seam and file and "
    "the probe is never imported or run; a module whose lazy imports quiet "
    "nothing stays OUT-OF-SCOPE; a lazily chained helper is followed so a "
    "partial middle helper cannot invent a missing seam; a lazy import cycle "
    "terminates; an unparseable source or helper reads UNREADABLE rather than "
    "being skipped; a round-token file reads HISTORICAL. PROOF: "
    "AC-PSL1..AC-PSL6 SUITE PASS 6/6 TWICE with an identical digest plus two "
    "adjacent probe faces green (qa/probe-seam-lazy-scope-R2517.log, 6504B, "
    "legs=2 identical=True fails=0 adjacent=2) captured through the shipped "
    "single evidence writer, and a live leg on the REAL tree through the same "
    "writer reading SEAMS-LAZY-COVERED over 3 covered probes, 168 "
    "out-of-scope modules and 1208 historical one-shot scripts, with a lazy "
    "fixture COVERED helpers=quiet_helper quieted=5 beside the same fixture "
    "OUT-OF-SCOPE quieted=0 on the module-level face and a stale lazy fixture "
    "MISSING-SEAM missing=STPT, while render and artifact digests were "
    "unchanged across the reading "
    "(qa/probe-seam-lazy-scope-live-R2517.log, 625B). Registry recounted by "
    "import: 587 suites and 4498 criteria became 588 and 4504 by exactly one "
    "row; the matrix was regenerated stamp-aligned from the last green "
    "battery leg (56544 bytes, 588 suites, 4504 criteria, green=587/588 "
    "because this tree own battery has not run yet) and --check reads "
    "byte-identical."
)

SEED = (
    "- [ ] P2 tech seed (R2517, from this window own live measurement): "
    "`src/os/probe_seam_dynamic_import_scope.py` - MEASURED this window while "
    "closing the lazy face: a probe that builds its import at RUN time reads "
    "OUT-OF-SCOPE with zero quieted seams, because this reading and every "
    "reading below it resolve import STATEMENTS off a syntax tree. Measured "
    "fixtures in a private temp root: "
    "`def run(): return importlib.import_module(\"quiet_helper\").QUIETED` "
    "reads OUT-OF-SCOPE quieted=0 and "
    "`def run(): return __import__(\"quiet_helper\").QUIETED` reads "
    "OUT-OF-SCOPE quieted=0, while the same helper reads COVERED quieted=5, "
    "so a probe whose quieting is resolved at run time is invisible again and "
    "a stale one is never named. Product: ONE reading that follows a "
    "COMPUTED import whose module name is a string constant visible in the "
    "probe own tree (importlib.import_module and __import__ with a literal, "
    "resolve_name style forms, and a module-level binding of the callable), "
    "on the same cycle-guarded same-root walk, so such a probe reads COVERED "
    "or MISSING-SEAM on its own row while a probe whose module name is NOT a "
    "constant still reads OUT-OF-SCOPE and the row names the unresolved call "
    "rather than guessing it. Criteria AC-PDI1..AC-PDI6 pre-registered HERE "
    "BEFORE any code: AC-PDI1 the dynamic call and its literal module name "
    "are derived from the probe own syntax tree at CALL time, never a "
    "hand-written list, and a name that is not a literal constants is NOT "
    "resolved; AC-PDI2 a probe whose literal dynamic import reaches a helper "
    "that quiets every seam reads COVERED with the helper named and the "
    "dynamic shape named on the row; AC-PDI3 a literal dynamic import of a "
    "helper that omits a seam reads MISSING-SEAM naming seam and file, and "
    "the probe is not run; AC-PDI4 a computed name that is not a constant "
    "reads OUT-OF-SCOPE with the unresolved call named, rather than being "
    "guessed at or counted as clean; AC-PDI5 the reading stays read-only and "
    "every digest it touches is unchanged; AC-PDI6 pure ASCII, stdlib only, "
    "no clock, zero network, its own reconcile label and its own suite. Five "
    "anchors to re-check zero-occupancy at HEAD before any code: "
    "probe_seam_dynamic_import_scope, AC-PDI, E_PDI, "
    "os-probe-seam-dynamic-import-scope, "
    "test_probe_seam_dynamic_import_scope."
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
    lines[at] = "- [x] [done 2026-11-07 R2517]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2517] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2517")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2517,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("delta %d" % (measured - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())