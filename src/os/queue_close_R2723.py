"""Close the AC-ECORD1 queue row at R2723 and seed ONE successor row.

Reads state/queue/tech.md, finds the single row carrying the AC-ECORD1 seed,
marks it done with a DISCHARGED note that keeps the original text, and inserts
ONE new seed row carrying AC-EPDU1..AC-EPDU6 measured in this window.
Writes atomically with a read-back and refuses on any ambiguity.

Dry run by default; --execute writes. Pure ASCII source, utf-8 data.
"""

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

MARK = "- [ ] P2 tech seed (R2720, from this window own measured limit):"
DONE_HEAD = "- [x] [done 2026-11-14 R2723] "

DISCHARGED = (
    " DISCHARGED R2723: shipped src/os/evidence_capture_precedence_derived.py "
    "plus its six-criteria suite. The shape order is no longer a constant: for "
    "each of the fifteen shape pairs the face builds a payload carrying "
    "EXACTLY those two shapes, re-checks that isolation against the shipped "
    "counters, asks the shipped chain which code it publishes first on that "
    "payload, reads the winner off the answer, and then takes the unique "
    "topological reading of the fifteen answers - a relation that is not "
    "total, a seed that no longer isolates its pair and an answer naming a "
    "third shape are REFUSED by name (E_EPD_ORDER / E_EPD_SEED / E_EPD_ANSWER) "
    "rather than guessed. MEASURED at open on the shipped tree: derived "
    "(bom,nul,utf8,crlf,lone_cr,tail), byte for byte the order R2720 published, "
    "and with the shipped BOM-guard law patched to check NUL before BOM the "
    "derived order MOVED to (nul,bom,utf8,crlf,lone_cr,tail) while the "
    "published report followed it to code E_EBOM_NUL with shapes "
    "nul,bom,tail - the exact divergence R2720 could only name. PROOF: "
    "AC-ECORD1..AC-ECORD6 SUITE PASS 6/6 twice byte-identical through the "
    "shipped suite file (qa/evidence-capture-precedence-derived-R2723.log, "
    "7540B, legs=2 identical=True adjacent=True both_green=True fails=0) with "
    "one bounded live leg reading the real committed qa/reconcile-all-R2721.log "
    "as ACCEPT bytes=1213193 and two real compound fixtures as REFUSED with "
    "their derived shape lists (qa/evidence-capture-precedence-derived-live-"
    "R2723.log, 516B). Registry 671 suites / 5002 criteria -> 672 / 5008 by "
    "exactly one row recounted by import at 672 unique names and 672 unique "
    "paths; docs/sandbox-suite-matrix.md read ROWS-MISMATCH first (doc-rows 671 "
    "against registry 672) and was regenerated stamp-aligned from this company "
    "own green leg to 71107 bytes at 672 rows, after which --check read "
    "DOC-CURRENT."
)

SEED = (
    "- [ ] P2 tech seed (R2723, from this window own measured limit): "
    "`src/os/evidence_capture_precedence_unknown_shape.py` - MEASURED this "
    "window on the face it ships: the derivation covers the SIX shapes the "
    "shipped chain names today, and an earned shape whose code is NOT in that "
    "table is invisible to the detector while the first code still names it. "
    "With the shipped BOM-guard law patched to answer `E_EBOM_UTF16` for a "
    "byte-order-marked UTF-16 payload, `report_of` published code "
    "`E_EBOM_UTF16` beside shapes `nul,utf8,tail` - a list that does NOT "
    "contain the defect the chain named first - and `CODES[shapes[0]]` read "
    "`E_EBOM_NUL`, i.e. the two faces disagreed again at the boundary this "
    "window closed everywhere else. A payload earning ONLY the unknown shape "
    "would read ACCEPT while the chain refuses it. Product: ONE reading in "
    "which any first code outside the six known shapes is REFUSED by name "
    "(naming the unknown code and the counters) instead of publishing a shape "
    "list that cannot contain it, while every answer the six known shapes "
    "produce stays byte for byte. Criteria AC-EPDU1..AC-EPDU6 pinned HERE "
    "BEFORE any code: AC-EPDU1 a first code outside the six known shapes is "
    "refused naming that code, never reported as an ACCEPT and never published "
    "beside a list that omits it; AC-EPDU2 a payload earning ONLY the unknown "
    "shape is refused rather than accepted, proved by patching one shipped "
    "refusal law and re-reading; AC-EPDU3 every report the six known shapes "
    "publish today - each single-defect code, each counter, each derived shape "
    "list and each report line - stays byte for byte; AC-EPDU4 a clean "
    "payload, the zero-byte payload and the real committed evidence files "
    "still read ACCEPT with digests unchanged, and a refusal still leaves the "
    "target absent and an existing target byte-identical; AC-EPDU5 the "
    "derivation and the unknown-code answer are both read at CALL time from "
    "the shipped chain, so patching a shipped face moves each of them; "
    "AC-EPDU6 pure ASCII, stdlib only, no clock, zero network, own reconcile "
    "label and own suite."
)


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def main(argv):
    execute = "--execute" in argv
    text = read_text(TECH)
    lines = text.split("\n")
    hits = [index for index, line in enumerate(lines)
            if line.startswith(MARK)]
    if len(hits) != 1:
        sys.stdout.write("E_QC2723_HITS %d rows carry the AC-ECORD1 seed\n"
                         % len(hits))
        return 2
    index = hits[0]
    original = lines[index]
    if "AC-ECORD1" not in original or "precedence_derived.py" not in original:
        sys.stdout.write("E_QC2723_SHAPE the row is not the AC-ECORD1 seed\n")
        return 2
    body = original[len("- [ ] "):]
    new_line = DONE_HEAD + body + DISCHARGED
    new_lines = list(lines)
    new_lines[index] = new_line
    new_lines.insert(index + 1, SEED)
    payload = "\n".join(new_lines)
    sys.stdout.write("row=%d before=%d after=%d lines=%d->%d\n"
                     % (index + 1, len(text.encode("utf-8")),
                        len(payload.encode("utf-8")), len(lines),
                        len(new_lines)))
    if not execute:
        sys.stdout.write("PLANNED (dry run, nothing written)\n")
        return 0
    tmp = TECH + ".tmp-R2723"
    with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(payload)
    os.replace(tmp, TECH)
    back = read_text(TECH)
    if back != payload:
        sys.stdout.write("E_QC2723_READBACK the file does not read back\n")
        return 3
    check = back.split("\n")
    ok = (check[index] == new_line and check[index + 1] == SEED
          and len(check) == len(new_lines))
    sys.stdout.write("readback=%s\n" % ("ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
