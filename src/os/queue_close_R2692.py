"""Close the AC-PNAP1 queue row at R2692 and seed ONE successor row.

Reads state/queue/tech.md, finds the single row carrying the AC-PNAP1 seed,
marks it done with a DISCHARGED note that keeps the original text, and inserts
ONE new seed row carrying AC-PNAQ1..AC-PNAQ6 measured in this window.
Writes atomically with a read-back and refuses on any ambiguity.

Dry run by default; --execute writes. Pure ASCII source, utf-8 data.
"""

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

MARK = "- [ ] P2 tech seed (R2689, from this window own measured limit):"
DONE_HEAD = "- [x] [done 2026-11-13 R2692] "

DISCHARGED = (
    " DISCHARGED R2692: shipped src/os/probe_seam_unnameable_dialect_marker_"
    "scope.py plus its six-criteria suite. Every word this face publishes now "
    "carries the dialect marker `dialect:1` as its FIRST part, and the marker "
    "is READ BACK from the bytes rather than assumed: measured before any byte "
    "here, R2685 published the SAME string "
    "`strict-prefix-of:ab+duplicate:2` for the one-label shape "
    "['a','ab+duplicate:2'] and for the genuine sibling-plus-copy shape "
    "['a','ab','a'], and R2689 read that one legacy string as siblings ['ab'] "
    "plus duplicate 2 with the tail lost. This face publishes "
    "`dialect:1+strict-prefix-of:ab\\+duplicate:2` for the one-label shape and "
    "`dialect:1+strict-prefix-of:ab+duplicate:2` for the genuine shape, so the "
    "two words are now distinct AND each names its publisher; "
    "`read_word('strict-prefix-of:ab+duplicate:2')` reports dialect None and "
    "the same readings R2689 gave, so every word already published is re-read "
    "exactly as before. PROOF: AC-PNAP1..AC-PNAP6 SUITE PASS 6/6 twice "
    "byte-identical through the shipped capture callable "
    "(qa/prefix-dialect-marker-R2692.log, 17649B, digest 21708D12384D9072, "
    "adjacent 2 both 6/6, fails=0) with one bounded live leg reading 5 real "
    "modules / 68 loops read-only and measuring the SAME fixture on BOTH "
    "readers. Registry 660 suites / 4936 criteria -> 661 / 4942 by exactly "
    "one row recounted by import; docs/sandbox-suite-matrix.md read FAIL stale "
    "before any byte with the evidence face agreeing (drift in content, not "
    "the face) and was regenerated stamp-aligned to 69834 bytes at 661 / 4942 "
    "with its green line honestly reading 660/661, after which --check read "
    "byte-identical."
)

SEED = (
    "- [ ] P2 tech seed (R2692, from this window own measured limit): "
    "`src/os/probe_seam_unnameable_dialect_marker_scope.py` - MEASURED this "
    "window on the face it ships: the marker names the DIALECT but nothing "
    "validates the tag it names, so `read_word('dialect:2+strict-prefix-of:"
    "ab')` reports dialect None and the whole body verbatim - a word "
    "published by a FUTURE dialect is silently mis-typed as a LEGACY word "
    "and parsed by the legacy law instead of being REFUSED with its own "
    "word. A second measured shape is named but not claimed as the product: "
    "`read_word('dialect:1+dialect:1+strict-prefix-of:ab')` reports dialect "
    "`1` with markers=2, so a string this face would never publish is "
    "accepted as its own output. Product: ONE reading in which a first part "
    "naming a dialect tag this face does not know is REFUSED naming that tag "
    "(and a word carrying more than one dialect part is refused naming the "
    "count), while every marker-less legacy word and every word R2692 "
    "published stays byte for byte. Criteria AC-PNAQ1..AC-PNAQ6 pinned HERE "
    "BEFORE any code: AC-PNAQ1 a first part naming an unknown dialect tag is "
    "refused with its own word naming the tag, never reported as a legacy "
    "word; AC-PNAQ2 a marker-less legacy word is still parsed exactly as "
    "R2692 parses it today (`strict-prefix-of:ab+duplicate:2` -> siblings "
    "['ab'] plus duplicate 2, dialect None), proved on the same fixtures; "
    "AC-PNAQ3 the word this face publishes keeps its exact bytes and reads "
    "back tag `1`; AC-PNAQ4 a word carrying MORE than one dialect part is "
    "refused naming the count instead of being read as this face own word; "
    "AC-PNAQ5 every answer R2685, R2689 and R2692 pinned rides unchanged, "
    "proved on the same fixtures plus one bounded live leg measuring the "
    "SAME fixture on BOTH readers; AC-PNAQ6 pure ASCII, stdlib only, no "
    "clock, zero network, own reconcile label and own suite."
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
        sys.stdout.write("E_QC2692_HITS %d rows carry the AC-PNAP1 seed\n"
                         % len(hits))
        return 2
    index = hits[0]
    original = lines[index]
    if "AC-PNAP1" not in original or "part_joiner_escaped_scope.py" not in original:
        sys.stdout.write("E_QC2692_SHAPE the row is not the AC-PNAP1 seed\n")
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
    tmp = TECH + ".tmp-R2692"
    with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(payload)
    os.replace(tmp, TECH)
    back = read_text(TECH)
    if back != payload:
        sys.stdout.write("E_QC2692_READBACK the file does not read back\n")
        return 3
    check = back.split("\n")
    ok = (check[index] == new_line and check[index + 1] == SEED
          and len(check) == len(new_lines))
    sys.stdout.write("readback=%s\n" % ("ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
