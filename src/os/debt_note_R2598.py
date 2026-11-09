"""R2598 note append: the red battery leg on the open R2596 debt row.

Appends ONE note segment to the existing `reconcile-battery-R2596` row,
quoting only numbers measured this window. It refuses when the row is
missing, already carries this segment, or the note would change any other
line.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
DEBT = os.path.join(REPO, "state", "debt.md")
MARK = "note_red_run_R2598:"
ITEM = "item=reconcile-battery-R2596"

NOTE = (
    " ; note_red_run_R2598: the battery RAN on the committed tree and came "
    "back RED and KEPT - qa/reconcile-all-R2598.log 1078987B, RUNNER FAIL "
    "(8 failed assertions) in 4095.8s at 632 suites, with "
    "ledger-apimarket-refundregister exit=124 on the 600s cap (296s when run "
    "alone minutes later) and six readability suites red because "
    "docs/sandbox-suite-matrix.md still renders the 631-row registry while "
    "the registry reads 632 rows / 4768 criteria by import. Birth-site repair "
    "committed alone: a declared per-suite override of 900s (1.5x the "
    "slowest measured leg) through the AC-RSC2 mechanism, with the two "
    "timeout guard suites re-run green; the matrix was regenerated from the "
    "red leg, judged by its own check face as an evidence-face mismatch, and "
    "therefore REVERTED so no document ships on a red leg. THIS ROW STAYS "
    "OPEN: the next window owes a full battery on the committed tree."
)


def main():
    text = io.open(DEBT, "r", encoding="utf-8").read()
    if MARK in text:
        raise SystemExit("note already present")
    lines = text.splitlines(True)
    hits = [i for i, line in enumerate(lines) if ITEM in line]
    if len(hits) != 1:
        raise SystemExit("expected one open row, found %d" % len(hits))
    at = hits[0]
    if not lines[at].startswith("- [ ]"):
        raise SystemExit("row is not open")
    before = len(text.encode("utf-8"))
    lines[at] = lines[at].rstrip("\r\n") + NOTE + lines[at][len(lines[at].rstrip("\r\n")):]
    out = "".join(lines)
    after = len(out.encode("utf-8"))
    io.open(DEBT, "w", encoding="utf-8", newline="").write(out)
    back = io.open(DEBT, "r", encoding="utf-8").read().splitlines()
    same_others = [a == b for a, b in zip(text.splitlines(), back) if a != lines[at].rstrip("\r\n")]
    print("row line %d, bytes %d -> %d, readback=%s"
          % (at + 1, before, after, MARK in io.open(DEBT, "r", encoding="utf-8").read()))
    print("other_lines_unchanged=%s" % all(same_others))
    return 0


if __name__ == "__main__":
    sys.exit(main())