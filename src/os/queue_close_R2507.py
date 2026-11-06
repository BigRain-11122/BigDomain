"""R2507 board closeout for the AC-ADTR1 seed row at state/queue/tech.md:544.

Marks the seed row done, adds its DISCHARGED note, marks this window's claim row
done, and seeds ONE row measured this window (the artifact also interpolates the
EVIDENCE FILE NAME, and the coverage probe hands a constant there, so a broken
codepoint in that name still reaches the document while the disk reading reads
publishable=True). Reads once, writes once, reads back, prints predicted
against measured bytes.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2505,"
SEED_MARK = "`src/os/artifact_disk_text_readability.py`"
CLAIM_HEAD = "- [ ] P2 tech claim (R2507,"

DISCHARGED = (
    "  DISCHARGED R2507 (line 544, AC-ADTR1..AC-ADTR6 pre-registered in the "
    "R2507 claim row BEFORE any code): src/os/artifact_disk_text_readability.py "
    "plus its suite shipped, and src/sandbox/suite_matrix.py::render now asks "
    "it one statement after the non-label seam. The reading DERIVES the "
    "artifact's disk-sourced text by composing the real render once against "
    "recording wrappers - the registry labels and suite paths read live from "
    "reconcile_all.SUITES, and every string billable_faces pulls out of each "
    "product config.json, addressed by the path that asked for it - and hands "
    "that set to patterns_label_readability.gate, the SAME shipped per-codepoint "
    "law, asked at CALL time. A registry label carrying U+FFFD refuses the "
    "shipped tool at exit 4 with FAIL disk-text: E_PLR_SUSPECT "
    "source=registry field=registry[0].label, the artifact keeps every byte it "
    "had, no residue is left, and --check reports the same refusal rather than "
    "the drift exit 2; a clean tree renders byte-identically to the committed "
    "doc and --check keeps exit 0. PROOF: AC-ADTR1..AC-ADTR6 SUITE PASS 6/6 "
    "TWICE with an identical digest plus three adjacent suites green "
    "(qa/artifact-disk-text-readability-R2507.log, 4935B, legs=2 "
    "identical=True fails=0 adjacent=3) and a live leg reading the REAL tree "
    "CLEAN over 1226 disk-sourced strings (registry 1166, config 60) with a "
    "doctored registry refused and the doc digest unchanged "
    "(qa/artifact-disk-text-readability-live-R2507.log, 373B, utf-8 LF). "
    "REGISTRY 582/4468 -> 583/4474 by exactly one row "
    "os-artifact-disk-text-readability(6), recounted by importing "
    "reconcile_all.SUITES; docs/sandbox-suite-matrix.md was regenerated "
    "stamp-aligned from qa/reconcile-all-R2506-retry.log to 56095B at 583 "
    "suites / 4474 criteria with --check byte-identical and its green line "
    "honestly reading 582/583."
)

SEED = (
    "- [ ] P2 tech seed (R2507, from this window own live measurement): "
    "`src/os/evidence_name_text_coverage.py` - MEASURED this window after "
    "wiring the disk-text gate: that gate derives everything the render reads "
    "off DISK through recording wrappers, but the coverage probe hands the "
    "render a CONSTANT evidence path, so the evidence file NAME the artifact "
    "prints is outside the derived set. A copy of the real evidence named "
    "`reconcile-all-R2506-retr<U+FFFD>y.log` rendered into the document with "
    "the broken codepoint carried while the shipped reading still returned "
    "publishable=True (qa/adtr-evidence-name-live-R2507.log). Product: ONE "
    "reading that covers the evidence-name text as well - the name is handed "
    "through the same shipped per-codepoint law with the piece named (basename, "
    "round tag or relative path), refusing publication with the first suspect "
    "named, while a clean name keeps today's bytes. Criteria AC-EVNM1..AC-EVNM6 "
    "pre-registered HERE BEFORE any code: AC-EVNM1 the classification is the "
    "SHIPPED law asked at CALL time, proved by patching it; AC-EVNM2 an "
    "evidence file name carrying a broken codepoint refuses publication naming "
    "the name and the piece, and no artifact byte is written; AC-EVNM3 a clean "
    "tree renders byte-identically to the committed doc and --check keeps exit "
    "0; AC-EVNM4 coverage is derived from what the render actually prints from "
    "the evidence path, not a hand-written list; AC-EVNM5 no source file or "
    "evidence file on disk is rewritten and every digest is unchanged; "
    "AC-EVNM6 pure ASCII, stdlib only, no clock, zero network, own reconcile "
    "label and own suite. Five anchors to re-check zero-occupancy at HEAD "
    "before any code: evidence_name_text_coverage, AC-EVNM, E_EVNM, "
    "os-evidence-name-text-coverage, test_evidence_name_text_coverage."
)


def main():
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    before = len(text.encode("utf-8"))
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    claims = [i for i, row in enumerate(lines) if row.startswith(CLAIM_HEAD)]
    if len(seeds) != 1 or len(claims) != 1:
        print("FAIL claim: seeds=%d claims=%d" % (len(seeds), len(claims)))
        return 2
    at = seeds[0]
    if claims[0] != at + 1:
        print("FAIL layout: claim row is not directly under the seed row")
        return 2
    lines[at] = "- [x] [done 2026-11-07 R2507]" + lines[at][len("- [ ]"):]
    lines[at + 1] = ("- [x] [done 2026-11-07 R2507]" +
                     lines[at + 1][len("- [ ]"):])
    lines.insert(at + 2, DISCHARGED)
    lines.insert(at + 3, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2507] P2 tech seed")
          and back[at + 1].startswith("- [x] [done 2026-11-07 R2507] P2 tech")
          and back[at + 2].strip().startswith("DISCHARGED R2507")
          and back[at + 3].startswith("- [ ] P2 tech seed (R2507,"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at,
             len(payload.encode("utf-8")),
             len("\n".join(back).encode("utf-8"))))
    print("delta %d" % (len("\n".join(back).encode("utf-8")) - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())