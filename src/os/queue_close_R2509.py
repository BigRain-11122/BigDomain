"""R2509 board closeout for the AC-EVNM1 seed row at state/queue/tech.md:547.

Marks that seed row done, adds its DISCHARGED note, and seeds ONE row measured
this window: the render also prints the generation stamp and the --stamp-from
provenance source, and MEASURED this window a broken codepoint in either one
renders into the artifact while every shipped reading (label, non-label, disk
text, evidence name) still reads publishable=True. Reads once, writes once,
reads back, prints predicted against measured bytes.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2507,"
SEED_MARK = "`src/os/evidence_name_text_coverage.py`"

DISCHARGED = (
    "  DISCHARGED R2509 (line 547, AC-EVNM1..AC-EVNM6 pinned in that row at "
    "R2507 BEFORE any code): src/os/evidence_name_text_coverage.py plus its "
    "suite shipped, and src/sandbox/suite_matrix.py::render now asks it one "
    "statement after the disk-text seam. The reading DERIVES the strings the "
    "render really prints from the evidence path by composing the real render "
    "once against a recording os.path proxy (basename) and a recording rel() "
    "wrapper (the relative path the command line prints), each recording ONLY "
    "when the path asked about is the evidence path, plus the round tag the "
    "render own regex law produces when it differs from the basename - and "
    "hands that set to patterns_label_readability.gate, the SAME shipped "
    "per-codepoint law, asked at CALL time. A doctored evidence name refuses "
    "the shipped tool at exit 4 with FAIL evidence-name: E_PLR_SUSPECT "
    "piece=evidence.basename, the artifact keeps every byte it had, no residue "
    "is left, and --check reports that same refusal rather than the drift exit "
    "2; a clean name renders byte-identically to the committed doc and --check "
    "keeps exit 0. PROOF: AC-EVNM1..AC-EVNM6 SUITE PASS 6/6 TWICE with an "
    "identical digest plus two adjacent readability suites green "
    "(qa/evidence-name-text-coverage-R2509.log, 5505B, legs=2 identical=True "
    "fails=0 adjacent=2) and a live leg on the REAL tree reading CLEAN over the "
    "three derived pieces with a doctored copy refused and both the evidence "
    "and artifact digests unchanged "
    "(qa/evidence-name-text-coverage-live-R2509.log)."
)

SEED = (
    "- [ ] P2 tech seed (R2509, from this window own live measurement): "
    "`src/os/stamp_text_coverage.py` - MEASURED this window after wiring the "
    "evidence-name seam: render prints the generation stamp and, when one is "
    "given, the --stamp-from provenance source, and NO shipped reading covers "
    "either. Composing the real render with a stamp and a stamp_from carrying "
    "U+FFFD printed both codepoints into the artifact while "
    "artifact_disk_text_readability and evidence_name_text_coverage both still "
    "returned publishable=True (measured in this round own console leg, "
    "carried=True with both readings True). Product: ONE reading over the two "
    "caller-supplied strings the artifact prints, asked through the same "
    "shipped per-codepoint law, refusing publication with the first suspect "
    "named by piece, while a clean stamp keeps today's bytes. Criteria "
    "AC-STPT1..AC-STPT6 pre-registered HERE BEFORE any code: AC-STPT1 the "
    "classification is the SHIPPED law asked at CALL time, proved by patching "
    "it; AC-STPT2 a stamp carrying a broken codepoint refuses publication "
    "naming the piece and no artifact byte is written, and a stamp_from "
    "carrying one refuses the same way; AC-STPT3 a clean tree renders "
    "byte-identically to the committed doc and --check keeps exit 0; AC-STPT4 "
    "the covered set is derived from what the render actually prints, not a "
    "hand-written list, and a render given no stamp_from claims no such piece; "
    "AC-STPT5 no source file, stamp source document or evidence file is "
    "rewritten and every digest is unchanged; AC-STPT6 pure ASCII, stdlib "
    "only, no clock in the reading itself, zero network, own reconcile label "
    "and own suite. Five anchors to re-check zero-occupancy at HEAD before any "
    "code: stamp_text_coverage, AC-STPT, E_STPT, os-stamp-text-coverage, "
    "test_stamp_text_coverage."
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
    lines[at] = "- [x] [done 2026-11-07 R2509]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2509] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2509")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2509,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("delta %d" % (measured - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())