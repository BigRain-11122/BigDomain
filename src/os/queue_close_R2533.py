"""R2533 board closeout for the AC-PCSC1 seed row at state/queue/tech.md:569.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: a SECOND constant key (a dict of dicts) is not followed and the
row names only "nested", so the hop that broke is invisible. Reads once,
writes once, reads back, prints predicted against measured bytes.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2531,"
SEED_MARK = "`src/os/probe_seam_subscript_container_scope.py`"

DISCHARGED = (
    "  DISCHARGED R2533 (line 569, AC-PCSC1..AC-PCSC6 pinned in that row at "
    "R2531 BEFORE any code): src/os/probe_seam_subscript_container_scope.py "
    "plus its suite shipped. ONE shape that read refused now resolves and "
    "carries the chain WITH its key: a for-loop whose iterable is a constant "
    "subscript of a container NAME or of a same-root module chain, but ONLY "
    "when the resolved container holds exactly one element. A result with two "
    "or more elements is NAMED ambiguous; a missing key is NAMED with the key "
    "and the container; a key that is not a literal constant is NAMED key and "
    "never guessed; a broken chain hop is NAMED with the hop; a call base and "
    "a comprehension are NAMED and never evaluated; and a MULTI-TARGET loop "
    "(the shape that used to be ignored) is now NAMED "
    "multi-target:a,b on the row. The shipped container-name tables and law "
    "are asked FIRST and never overwritten, so every earlier answer stands, "
    "and the seam classifier is still the shipped registry single `quiets`. "
    "PROOF: AC-PCSC1..AC-PCSC6 SUITE PASS 6/6 TWICE with byte-identical "
    "output, exit 0 on both legs, plus five adjacent probe suites green "
    "(container name, alias expression, annotated constant, dynamic import, "
    "registry) (qa/probe-seam-subscript-container-scope-R2533.log, 28328B, "
    "bom=False crlf=0, legs=2 identical=True fails=0 adjacent=5); a live leg "
    "on the REAL tree reads SEAMS-SUBSCRIPT-COVERED over 1437 probes (3 "
    "covered, 176 out-of-scope, 1258 historical, missing=0) with the module, "
    "the base face and the render digests unchanged. The registry moved by ONE "
    "row to 596 suites / 4552 criteria, recounted by importing "
    "reconcile_all.SUITES rather than trusted, and docs/sandbox-suite-matrix.md "
    "was regenerated stamp-aligned from the eligible battery leg "
    "qa/reconcile-all-R2532.log to 57386 bytes at 596/4552 with green=595/596 "
    "self-describing and --check byte-identical. BIRTH-SITE HONESTY: TWO "
    "defects were measured in my own first pass and fixed in the CODE - a dict "
    "of tuples is NOT in the shipped tables at all (those tables refuse a "
    "nested container), so the subscript base had to be read off the LITERAL "
    "the source declares, and my first key label printed \"...\" for a bare "
    "name instead of the name, which hid which key broke. ONE assertion was "
    "corrected against measurement rather than loosened: a format call "
    "iterable is NAMED format by the shipped law, not string. LIMIT, measured "
    "this window: a SECOND constant key (a dict of dicts, D[\"a\"][\"b\"], and "
    "a key followed by an index, D[\"a\"][0]) is refused as nested and names "
    "NO hop, so a two-deep container reads silent about which step broke - "
    "that shape is the row seeded below. tasks.md was not touched."
)

SEED = (
    "- [ ] P2 tech seed (R2533, from this window own measured limit): "
    "`src/os/probe_seam_nested_subscript_scope.py` - MEASURED this window on "
    "the shipped subscript face own readers: `D = {\"a\": {\"b\": (\"x\",)}}` "
    "then `for n in D[\"a\"][\"b\"]:` reads refused=nested for the target and "
    "names NO key at all, and `for n in D[\"a\"][0]:` (a key followed by an "
    "index into the tuple) reads the same, so a container TWO constant keys "
    "deep tells the operator nothing about which step broke even though both "
    "the outer and the inner dict are literal constants. Product: ONE reading "
    "that follows a CHAIN of constant subscripts on a literal container, "
    "resolves a single-element result with the full chain and every key on it, "
    "refuses a multi-element or non-constant step by NAME with the hop, and "
    "never evaluates anything. Criteria AC-PCNS1..AC-PCNS6 pre-registered HERE "
    "BEFORE any code: AC-PCNS1 a for-loop over a two-key chain of a literal "
    "container resolves to its single element and the row carries the chain "
    "with BOTH keys; AC-PCNS2 a chain whose second key is missing, or whose "
    "second step is an index into a tuple, is NAMED with the hop that broke "
    "rather than a bare shape word; AC-PCNS3 a resolved two-deep result with "
    "two or more elements is NAMED ambiguous, never the first element; "
    "AC-PCNS4 a step built by a call, a format or a comprehension is NAMED and "
    "never evaluated; AC-PCNS5 the reading stays read-only and every digest it "
    "touches is unchanged; AC-PCNS6 pure ASCII, stdlib only, no clock, zero "
    "network, its own reconcile label and its own suite. Five anchors to "
    "re-check zero-occupancy at HEAD before any code: "
    "probe_seam_nested_subscript_scope, AC-PCNS, E_PCNS, "
    "os-probe-seam-nested-subscript-scope, "
    "test_probe_seam_nested_subscript_scope."
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
    lines[at] = "- [x] [done 2026-11-07 R2533]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2533] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2533")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2533,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("delta %d" % (measured - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())