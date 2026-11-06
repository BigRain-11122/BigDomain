"""R2502 closeout for the AC-PLR1 seed row at state/queue/tech.md:538.

Marks the row done with this window's stamp and inserts a DISCHARGED note
directly beneath it, in the same shape the earlier closed rows use. Reads the
file once, writes once, and reads the row back to prove both edits landed.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

DISCHARGED = (
    "  DISCHARGED R2502 (line 538, AC-PLR1..AC-PLR6 pinned at R2494 BEFORE "
    "any code): src/os/patterns_label_readability.py plus its suite shipped. "
    "reading() asks unicodedata for every non-ASCII codepoint of every string "
    "label: a broken codepoint (replacement character, unassigned name, "
    "C*/C category) or a script bucket that no OTHER label in the same file "
    "carries is SUSPECT, named with its position, its U+XXXX and its Unicode "
    "name; punctuation, symbols, separators, digits and marks are shared and "
    "never suspect. gate() turns the first suspect into E_PLR_SUSPECT naming "
    "the label key, and publish(labels, render) refuses to call the renderer "
    "at all on a suspect file while a clean file reaches it untouched. "
    "HONEST MEASUREMENT: on the shipped tree every label reads CLEAN - the "
    "R2494 note's mojibake was a console decoding artifact, not a damaged "
    "byte - so SUSPECT detection is proved on fixtures built from the real "
    "file and is NOT claimed as a live catch. PROOF: AC-PLR1..AC-PLR6 SUITE "
    "PASS 6/6 TWICE with an identical digest plus three adjacent suites green "
    "(qa/patterns-label-readability-R2502.log, 4773B, legs=2 identical=True "
    "fails=0 adjacent=3), and a live reading of the real patterns file "
    "(qa/patterns-label-readability-live-R2502.log) whose digest is unchanged "
    "before and after. The clean-file parity leg drives the REAL "
    "suite_matrix.render through publish() and gets docs/sandbox-suite-matrix.md "
    "back byte for byte. REGISTRY 579/4450 -> 580/4456 by exactly one row "
    "os-patterns-label-readability(6); matrix restamped stamp-aligned from "
    "qa/reconcile-all-R2500.log to 55718B at 580/4456 with --check "
    "byte-identical, its green line honestly reading 578/580 because that "
    "evidence predates two rows.")


def main():
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    hits = [i for i, row in enumerate(lines)
            if row.startswith("- [ ] P2 tech seed (R2494,")
            and "patterns_label_readability.py`" in row]
    if len(hits) != 1:
        print("FAIL claim: %d matching open rows" % len(hits))
        return 2
    at = hits[0]
    lines[at] = "- [x] [done 2026-11-07 R2502]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, DISCHARGED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-07 R2502] P2 tech seed")
          and back[at + 1].startswith("  DISCHARGED R2502 (line 538,")
          and "patterns_label_readability.py`" in back[at])
    print("close row=%d discharged_at=%d read_back=%s bytes=%d"
          % (at + 1, at + 2, ok, len(payload.encode("utf-8"))))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())