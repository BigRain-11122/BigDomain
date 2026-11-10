"""R2613 closer: mark the AC-AMCF1..6 tech row done with its DISCHARGED note.

The row was seeded by queue_seed_R2613.py at line 642 THIS window, with its
six criteria pinned BEFORE any code, and the repair shipped in the same
window. Every number printed here is measured on the files on disk.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
HEAD = "- [ ] P2 tech seed (R2613,"
DONE = "- [x] [done 2026-11-10 R2613] P2 tech seed (R2613,"

NOTE = (
    "\n\n  DISCHARGED R2613 (AC-AMCF1..AC-AMCF6 pinned in this row BEFORE "
    "any code): the nesting is bounded - test_apimarket_report_claims.py "
    "AC-AMCLM8 now spawns ONLY the two cheap children, MEASURED on the "
    "loaded tree at 11.1s and 16.4s, and never the heavyweight "
    "test_apimarket_report_refundregister.py, MEASURED at 1022.5s when run "
    "standalone on that same loaded tree (296s alone at R2598, 191.6s and "
    "409.6s in earlier battery legs) - which is why the parent row lost the "
    "600s cap at R2612 rather than failing an assertion. The heavy "
    "coverage MOVED rather than being dropped: the same check now reads the "
    "shipped runner registry by AST at call time and requires exactly one "
    "ledger-apimarket-refundregister row pointing at that file with the "
    "file on disk, and that suite is already a battery row of its own with "
    "a declared 900s override. The repaired parent reads SUITE PASS 8/8 at "
    "a measured 49.5s wall (was exit=124 at 600.2s). New suite "
    "src/sandbox/ledger/test_apimarket_report_claims_nesting.py supersedes "
    "the row: AC-AMCF1..AC-AMCF6 SUITE PASS 6/6, proved TWICE with an "
    "identical digest through the shipped capture callable "
    "(qa/claim-nesting-repair-R2613.log, 1550B, legs=2 identical=True "
    "adjacent=1 fails=0). Registry 639/4810 -> 640/4816 by exactly one row.\n"
)


def main():
    text = io.open(QUEUE, "r", encoding="utf-8").read()
    if DONE in text:
        raise SystemExit("already closed")
    if text.count(HEAD) != 1:
        raise SystemExit("head row not found exactly once: %d"
                         % text.count(HEAD))
    before = len(text.encode("utf-8"))
    out = text.replace(HEAD, DONE, 1)
    marker = out.index(DONE)
    end = out.index("\n", marker)
    out = out[:end] + NOTE + out[end:]
    after = len(out.encode("utf-8"))
    io.open(QUEUE, "w", encoding="utf-8", newline="").write(out)
    back = io.open(QUEUE, "r", encoding="utf-8").read()
    ok = DONE in back and "DISCHARGED R2613" in back
    print("bytes %d -> %d readback_ok=%s" % (before, after, ok))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())