"""R2531 board closeout for the AC-PCAF1 seed row at state/queue/tech.md:567.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: a container reached through a constant subscript (a dict of
tuples) is refused by name and never followed. Reads once, writes once, reads
back, prints predicted against measured bytes.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2529,"
SEED_MARK = "`src/os/probe_seam_for_container_name.py`"

DISCHARGED = (
    "  DISCHARGED R2531 (line 567, AC-PCAF1..AC-PCAF6 pinned in that row at "
    "R2529 BEFORE any code): src/os/probe_seam_for_container_name.py plus its "
    "suite shipped. ONE shape that read empty now resolves and carries the "
    "chain it took: a for-loop whose iterable is a NAME bound to a container "
    "(module body and function body), an attribute chain into a same-root "
    "module, or a container literal - but ONLY when that container holds "
    "exactly one element. A container with two or more elements is NAMED "
    "ambiguous and never resolved to its first element; an empty container is "
    "NAMED empty; iterating a str is NAMED string because a character is not "
    "a module; a call, a format, a comprehension, an arithmetic expression, a "
    "subscript container and a broken chain hop are NAMED with the hop "
    "instead of reading silently absent. The shipped tables are asked FIRST "
    "and never overwritten, so every earlier answer stands, and the seam "
    "classifier is still the shipped registry single `quiets`. PROOF: "
    "AC-PCAF1..AC-PCAF6 SUITE PASS 6/6 TWICE with byte-identical output, exit "
    "0 on both legs, plus five adjacent probe suites green (alias expression, "
    "annotated constant, local constant, dynamic import, registry) "
    "(qa/probe-seam-for-container-name-R2531.log, 26014B, bom=False crlf=0 "
    "nul=0, legs=2 identical=True fails=0 adjacent=5); a live leg on the REAL "
    "tree reads SEAMS-CONTAINER-COVERED over 1431 probes (3 covered, 175 "
    "out-of-scope, 1253 historical, missing=0) with the module and render "
    "digests unchanged. The registry moved by ONE row to 595 suites / 4546 "
    "criteria, recounted by importing reconcile_all.SUITES rather than "
    "trusted, and docs/sandbox-suite-matrix.md was regenerated stamp-aligned "
    "from the eligible battery leg qa/reconcile-all-R2530-retry.log to 57362 "
    "bytes at 595/4546 with green=594/595 self-describing and --check "
    "byte-identical. BIRTH-SITE HONESTY: THREE defects were measured in my "
    "own first pass and fixed in the code rather than in the assertions - a "
    "bare string iterable fell through to shape instead of string, an ast.Call "
    "named format read as call, and the two shipped producers publish "
    "container elements in DIFFERENT representations (raw strings from the "
    "alias face `_tree_of`, nested (type, value) trees from the annotated face "
    "`_module_trees`), which my first reading copied through as a nested pair; "
    "the element reader now accepts both laws and refuses a nested container "
    "by name. One assertion was corrected against measurement: the world in "
    "the read-only criterion had to exclude the deliberately partial helper, "
    "because a helper that omits a seam legitimately reads MISSING-SEAM. "
    "LIMIT, measured this window: a container reached through a constant "
    "subscript (a dict of tuples, `for name in GROUPS[\"a\"]:`) reads "
    "subscript:GROUPS and is never followed, and a multi-target for-loop is "
    "not read at all - that shape is the row seeded below. tasks.md was not "
    "touched."
)

SEED = (
    "- [ ] P2 tech seed (R2531, from this window own measured limit): "
    "`src/os/probe_seam_subscript_container_scope.py` - MEASURED this window "
    "on the shipped face own readers: `GROUPS = {\"a\": (\"x\",)}` then "
    "`for name in GROUPS[\"a\"]:` reads refused=subscript:GROUPS and the row "
    "names nothing that resolves, so a container one constant subscript deep "
    "is never followed even when the dict and its tuple are BOTH in the "
    "table; the same shape on a same-root module (`pkg.GROUPS[\"a\"]`) is "
    "refused one hop out; and a multi-target loop (`for a, b in PAIRS:`) is "
    "not read at all, where the honest answer is to be NAMED rather than "
    "ignored. Product: ONE reading that follows a for-loop iterable reached "
    "through a constant subscript or key into the constant tables, resolves a "
    "single-element result with its chain, refuses a multi-element or "
    "non-constant one by name, and never evaluates anything. Criteria "
    "AC-PCSC1..AC-PCSC6 pre-registered HERE BEFORE any code: AC-PCSC1 a "
    "for-loop over a constant subscript of a NAME container resolves to its "
    "single element and the row carries the chain including the key; "
    "AC-PCSC2 the same shape through an attribute chain in a same-root module "
    "resolves, and a broken hop or a non-constant key is NAMED; AC-PCSC3 a "
    "resolved subscript result with two or more elements is NAMED ambiguous, "
    "never the first element; AC-PCSC4 a container built by a call, a format "
    "or a comprehension is NAMED and never evaluated; AC-PCSC5 the reading "
    "stays read-only and every digest it touches is unchanged; AC-PCSC6 pure "
    "ASCII, stdlib only, no clock, zero network, its own reconcile label and "
    "its own suite. Five anchors to re-check zero-occupancy at HEAD before any "
    "code: probe_seam_subscript_container_scope, AC-PCSC, E_PCSC, "
    "os-probe-seam-subscript-container-scope, "
    "test_probe_seam_subscript_container_scope."
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
    lines[at] = "- [x] [done 2026-11-07 R2531]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2531] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2531")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2531,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("delta %d" % (measured - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())