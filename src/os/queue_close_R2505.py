"""R2505 board closeout for the AC-PNLT1 seed row at state/queue/tech.md:542.

Marks the row done with this window's stamp, inserts a DISCHARGED note beneath
it, and seeds ONE row measured this window (the gate now reads every string the
render takes from the patterns document, but the artifact also interpolates
registry suite labels and config.json keys that come from DISK, and a broken
codepoint in those still reaches the document). Reads once, writes once, reads
back, and prints predicted vs measured bytes.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

DISCHARGED = (
    "  DISCHARGED R2505 (line 542, AC-PNLT1..AC-PNLT6 pinned at R2503 BEFORE "
    "any code): src/os/patterns_non_label_text_readability.py plus its suite "
    "shipped, and src/sandbox/suite_matrix.py::render now asks it one "
    "statement after the label seam, so a non-label defect is refused before a "
    "byte is composed. The coverage is DERIVED, not listed: the shipped render "
    "is composed once against a recording mapping that keeps every string it "
    "asks for, addressed by the field path that asked for it (header_note, "
    "labels.summary_cols[0], domains[0].faces[1].label, and fields read "
    "through .get such as labels.stamp_from), and that set is handed to "
    "patterns_label_readability.gate - the same shipped per-codepoint law, "
    "asked at CALL time, proved by patching the gate and watching the verdict "
    "move with the gate's own code carried verbatim. A key the render never "
    "reads is honestly NOT claimed as covered. A doctored header_note refuses "
    "the shipped tool at exit 4 with FAIL non-label: E_PLR_SUSPECT "
    "field=header_note and U+FFFD, the target keeps every byte it had, no "
    "residue is left, and --check reports the same refusal rather than the "
    "drift exit 2; a clean file renders byte-identically to the committed doc. "
    "PROOF: AC-PNLT1..AC-PNLT6 SUITE PASS 6/6 TWICE with an identical digest "
    "plus three adjacent suites green (qa/patterns-non-label-text-readability-"
    "R2505.log, 7967B, legs=2 identical=True fails=0 adjacent=3). TWO OF MY "
    "OWN ASSERTIONS FAILED FIRST and were fixed as TEST defects rather than "
    "loosened: the call-time proof had to ask this face directly because the "
    "label seam refuses first on the same patched gate, and the byte-identity "
    "leg had to be measured AFTER the new registry row moved the artifact "
    "(55841B -> 55964B), not against the pre-move doc. DISCLOSED LIMIT: the "
    "coverage probe patches PLR.gate to an allow-all stub for the duration of "
    "one compose and restores it in a finally block, so a concurrent "
    "in-process caller could observe that window. REGISTRY 581/4462 -> "
    "582/4468 by exactly one row os-patterns-non-label-text-readability(6); "
    "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from "
    "qa/reconcile-all-R2504.log to 55964B at 582 suites / 4468 criteria with "
    "--check byte-identical and its green line honestly reading 581/582."
)

SEED = (
    "- [ ] P2 tech seed (R2505, from this window own live measurement): "
    "`src/os/artifact_disk_text_readability.py` - MEASURED this window after "
    "wiring the non-label gate: that gate covers every string the render takes "
    "from the PATTERNS DOCUMENT, while `suite_matrix.render` also interpolates "
    "the registry's own suite labels (imported live from reconcile_all.SUITES) "
    "and the keys of each product config.json read from disk. A registry label "
    "carrying U+FFFD rendered straight into docs/sandbox-suite-matrix.md while "
    "the shipped gate still read publishable=True "
    "(qa/patterns-non-label-live-R2505.log, 435B, utf-8 LF, crlf=0, bom=False: "
    "'published=True carried=True gate_publishable=True'), so the CEO-visible "
    "artifact can still hold unreadable text that lives outside the patterns "
    "file. Product: ONE reading over the artifact's DISK-sourced text too, "
    "asked through the same shipped per-codepoint law rather than a second "
    "classifier, refusing publication with the first suspect named by source "
    "and field, while a clean tree keeps today's bytes. Criteria "
    "AC-ADTR1..AC-ADTR6 to be pre-registered in a new row BEFORE any code "
    "(this row states the intent only): AC-ADTR1 the classification is the "
    "SHIPPED law asked at CALL time, proved by patching it; AC-ADTR2 a "
    "registry label carrying a broken codepoint refuses publication naming the "
    "SOURCE (registry) and the label, and no artifact byte is written; "
    "AC-ADTR3 a clean tree renders byte-identically to the committed doc; "
    "AC-ADTR4 coverage is derived from what the render actually reads off "
    "disk, not a hand-written source list; AC-ADTR5 no source file on disk is "
    "rewritten and every digest is unchanged; AC-ADTR6 pure ASCII, stdlib "
    "only, no clock, zero network, own reconcile label and own suite. Five "
    "anchors to re-check zero-occupancy at HEAD before any code: "
    "artifact_disk_text_readability, AC-ADTR, E_ADTR, "
    "os-artifact-disk-text-readability, "
    "test_artifact_disk_text_readability."
)


def main():
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    before = len(text.encode("utf-8"))
    hits = [i for i, row in enumerate(lines)
            if row.startswith("- [ ] P2 tech seed (R2503,")
            and "patterns_non_label_text_readability.py`" in row]
    if len(hits) != 1:
        print("FAIL claim: %d matching open rows" % len(hits))
        return 2
    at = hits[0]
    lines[at] = "- [x] [done 2026-11-07 R2505]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2505] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2505")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2505,"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at,
             len(payload.encode("utf-8")), len("\n".join(back).encode(
                 "utf-8"))))
    print("delta %d" % (len("\n".join(back).encode("utf-8")) - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())