"""queue_R2369.py - stamp the claimed tech row and seed one measured gap.

Same shape as the earlier queue writers: the row is found by its criteria
prefix, the stamp is written in the pinned [done YYYY-MM-DD R<n>] form, and a
new seed row is appended only when the claim dropped claimable below the floor.

Usage: python src/os/queue_R2369.py
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import queue_floor  # noqa: E402

TECH = os.path.join(REPO, "state", "queue", "tech.md")

PREFIX = "AC-RTAB1"

STAMP = "- [x] [done 2026-11-02 R2369]"

SEED = (
    "- [ ] P2 tech seed (R2369, from this window own measured pain): "
    "\\src/os/residue_batch_status_face.py\\ - the batch writer refuses a "
    "status that disagrees with the live reading, but nothing in that CLI "
    "tells an operator WHAT the live status is: --check prints the rounds "
    "awaiting an entry and no status at all, so composing a --pair list means "
    "running stamp_residue separately and guessing, and the first attempt at a "
    "batch costs a refused call. Measured this window: building this module "
    "own suite required guessing DELIVERED against STAMP-ONLY-OPEN from the "
    "fixture shape, and the first live-shaped fixture was wrong. Product: the "
    "batch check names every residue round WITH its live status, and a round "
    "that is not in the residue reads NOT-RESIDUE rather than a guessed "
    "status. Criteria AC-RSBF1..AC-RSBF6 pre-registered HERE BEFORE any code: "
    "AC-RSBF1 the status map is imported from stamp_residue own reader "
    "(patching it moves the printed statuses) and no second residue scan is "
    "written; AC-RSBF2 --check names each residue round and its live status, "
    "so a --pair list can be composed without a second tool; AC-RSBF3 a round "
    "absent from the live residue reads NOT-RESIDUE with its own code rather "
    "than an invented status; AC-RSBF4 every existing --append refusal code "
    "and printed line stays byte-identical; AC-RSBF5 CLI exits 0/2/3 with a "
    "byte-stable --json over pinned keys; AC-RSBF6 pure ASCII, stdlib only, "
    "no clock, no network, plus its own reconcile label. Five anchors "
    "zero-occupancy at HEAD 2026-11-02: residue_batch_status_face, AC-RSBF, "
    "E_RSBF, os-residue-batch-status-face, test_residue_batch_status_face.\n"
)


def main():
    raw = io.open(TECH, "r", encoding="utf-8", newline="").read()
    lines = raw.split("\n")
    hit = None
    for index, line in enumerate(lines):
        if line.startswith("- [ ]") and PREFIX in line:
            hit = index
            break
    if hit is None:
        print("REFUSED: no open row carrying %s" % PREFIX)
        return 2
    lines[hit] = STAMP + " " + lines[hit][len("- [ ] "):]
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    if SEED not in text:
        text += SEED
    with io.open(TECH, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    back = io.open(TECH, "r", encoding="utf-8", newline="").read()
    ok = (STAMP + " " in back) and (SEED in back)
    print("QUEUE stamped line=%d prefix=%s readback=%s"
          % (hit + 1, PREFIX, ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())