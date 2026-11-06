"""R2507 pre-registration writer: pin the AC-ADTR1..AC-ADTR6 claim on the board.

The tech row at state/queue/tech.md:544 stated the intent only and demanded the
criteria land in a new row BEFORE any code exists. This writer inserts exactly
one claim row directly beneath that seed row, at a true line boundary, reading
once and writing once with a read-back.

ASCII source, stdlib only, no network, no clock.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2505,"
SEED_MARK = "`src/os/artifact_disk_text_readability.py`"

CLAIM = (
    "- [ ] P2 tech claim (R2507, AC-ADTR1..AC-ADTR6 PRE-REGISTERED in this "
    "row BEFORE any code): `src/os/artifact_disk_text_readability.py` plus "
    "`src/os/test_artifact_disk_text_readability.py`, and "
    "src/sandbox/suite_matrix.py::render asks it one statement after the "
    "non-label seam. The reading DERIVES the artifact's disk-sourced text by "
    "composing the real render once against recording wrappers - the registry "
    "labels and suite paths read live from reconcile_all.SUITES, and every "
    "string billable_faces pulls out of each product config.json - and hands "
    "that set to patterns_label_readability.gate, the SAME shipped "
    "per-codepoint law, asked at CALL time. No second classifier, no "
    "hand-written source list. Criteria: AC-ADTR1 the classification is the "
    "SHIPPED law asked at CALL time, proved by patching patterns_label_"
    "readability.gate and watching this face carry the gate own code and its "
    "refused field verbatim; AC-ADTR2 a registry label carrying a broken "
    "codepoint (U+FFFD) refuses publication naming the SOURCE (registry) and "
    "the label path, and the shipped tool writes NO artifact byte while the "
    "target keeps every byte it had and no .tmp/.part residue appears; "
    "AC-ADTR3 a clean tree renders byte-identically to the committed "
    "docs/sandbox-suite-matrix.md and --check keeps today reading; AC-ADTR4 "
    "coverage is DERIVED from what the render actually reads off disk, never a "
    "hand-written source list - proved by the recorded set carrying the live "
    "registry labels and config keys, by a key the render never reads being "
    "honestly not claimed, and by no literal registry label or config key "
    "appearing in the module source; AC-ADTR5 no source file on disk is "
    "rewritten - the registry module, every product config.json and the "
    "patterns file keep their digests across a full reading, and the module "
    "holds no write primitive; AC-ADTR6 pure ASCII, stdlib only, no clock, "
    "zero network, its own reconcile label and its own registered suite."
)


def main():
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    before = len(text.encode("utf-8"))
    hits = [i for i, row in enumerate(lines)
            if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(hits) != 1:
        print("FAIL claim: %d matching seed rows" % len(hits))
        return 2
    if any("AC-ADTR1..AC-ADTR6 PRE-REGISTERED" in row for row in lines):
        print("NOOP already pre-registered")
        return 0
    at = hits[0]
    lines.insert(at + 1, CLAIM)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at + 1].startswith("- [ ] P2 tech claim (R2507,")
          and "AC-ADTR1..AC-ADTR6 PRE-REGISTERED" in back[at + 1])
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at,
             len(payload.encode("utf-8")),
             len("\n".join(back).encode("utf-8"))))
    print("delta %d" % (len("\n".join(back).encode("utf-8")) - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())