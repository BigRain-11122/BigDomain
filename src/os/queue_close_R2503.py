"""R2503 board closeout for the AC-PLRC1 seed row at state/queue/tech.md:540.

Marks the row done with this window's stamp, inserts a DISCHARGED note beneath
it, and seeds ONE row measured this window (the readability gate is asked with
patterns[labels] only while render() interpolates header_note, response_text
and every caption into the artifact). Reads once, writes once, reads back.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

DISCHARGED = (
    "  DISCHARGED R2503 (line 540, AC-PLRC1..AC-PLRC6 pinned at R2502 BEFORE "
    "any code): src/os/patterns_label_readability_render_consumer.py plus its "
    "suite shipped, and src/sandbox/suite_matrix.py now asks that seam at the "
    "top of render() so the refusal lands before a byte is composed. The "
    "consumer holds NO classifier: guard() asks "
    "patterns_label_readability.gate at CALL time and carries its verdict and "
    "its code verbatim, proved by patching the gate and watching the real "
    "render refuse with the gate's own code and label key. A suspect patterns "
    "file refuses the shipped tool at exit 4 (a distinct word and exit, never "
    "the drift exit 2) with FAIL readability naming E_PLR_SUSPECT and the "
    "label key, the target keeps every byte it had and no residue is left; a "
    "clean file renders byte-identically to the committed doc at 55846 bytes. "
    "PROOF: AC-PLRC1..AC-PLRC6 SUITE PASS 6/6 TWICE with an identical digest "
    "plus three adjacent suites green (qa/patterns-render-consumer-R2503.log, "
    "5855B, utf-8 LF, legs=2 identical=True fails=0 adjacent=3), and a live "
    "reading of the real patterns file through the seam "
    "(qa/patterns-render-consumer-live-R2503.log, 405B) reading CLEAN with "
    "the file digest unchanged (%s). TWO OF MY OWN ASSERTIONS FAILED FIRST "
    "and were fixed as TEST defects, not loosened: the wired-row string had "
    "to match the registry's real two-line shape, and the label check had to "
    "compare the shipped labels to their own earlier reading instead of "
    "assuming every value is a string (the patterns file carries list "
    "captions). The registry row moved the artifact, so the doc was "
    "regenerated stamp-aligned from qa/reconcile-all-R2502.log to 55846B at "
    "581 suites / 4462 criteria with --check byte-identical and its green "
    "line honestly reading 580/581. REGISTRY 580/4456 -> 581/4462 by exactly "
    "one row os-patterns-label-readability-render-consumer(6)."
)

SEED = (
    "- [ ] P2 tech seed (R2503, from this window own measured limit): "
    "`src/os/patterns_non_label_text_readability.py` - MEASURED this window "
    "while wiring the render-path guard: `patterns_label_readability.gate` is "
    "asked with `patterns[\"labels\"]` ONLY, while `suite_matrix.render` "
    "interpolates `header_note`, `labels[\"response_text\"]` and every table "
    "caption straight into docs/sandbox-suite-matrix.md. A doctored copy with "
    "U+FFFD in header_note still read publishable=True from the gate and the "
    "composed document really carried the broken codepoint "
    "(qa/patterns-render-consumer-live-R2503.log), so the CEO-visible "
    "artifact can hold unreadable text the guard never sees. Product: ONE "
    "reading over every string the artifact interpolates - labels AND the "
    "non-label text - asked through the shipped law rather than a second "
    "classifier, refusing publication with the first suspect named by field "
    "and codepoint, while a clean patterns file keeps today's bytes. Criteria "
    "AC-PNLT1..AC-PNLT6 pre-registered HERE BEFORE any code: AC-PNLT1 the "
    "classification is the SHIPPED per-codepoint law asked at CALL time, "
    "proved by patching it and watching the verdict move, never a second "
    "classifier; AC-PNLT2 a patterns file whose header_note carries a broken "
    "codepoint refuses publication naming the FIELD (not a label key) and its "
    "codepoints, and no artifact byte is written; AC-PNLT3 a clean file "
    "renders byte-identically to today, proved against the committed doc at "
    "its recorded evidence; AC-PNLT4 every string the render interpolates is "
    "covered, derived from what the render actually reads rather than a "
    "hand-written field list; AC-PNLT5 the patterns file is never rewritten "
    "and its digest is unchanged after any run; AC-PNLT6 pure ASCII, stdlib "
    "only, no clock, zero network, own reconcile label and own suite. Five "
    "anchors to re-check zero-occupancy at HEAD before any code: "
    "patterns_non_label_text_readability, AC-PNLT, E_PNLT, "
    "os-patterns-non-label-text-readability, "
    "test_patterns_non_label_text_readability."
)


def main():
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    hits = [i for i, row in enumerate(lines)
            if row.startswith("- [ ] P2 tech seed (R2502,")
            and "patterns_label_readability_render_consumer.py`" in row]
    if len(hits) != 1:
        print("FAIL claim: %d matching open rows" % len(hits))
        return 2
    at = hits[0]
    lines[at] = "- [x] [done 2026-11-07 R2503]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2503] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2503")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2503,"))
    print("board %s at=%d bytes=%d" % ("OK" if ok else "FAIL", at,
                                       len(payload.encode("utf-8"))))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())