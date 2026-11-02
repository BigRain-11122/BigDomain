"""R2387 board edit: stamp the claimed tech row and seed one measured gap.

One-off round helper (the R2371/R2381 pattern): the queue file is 1.4 MB of
long lines, so the stamp and the seed are applied by EXACT line prefix match
and the byte delta is reported rather than assumed. Pure ASCII source; the
Chinese-free queue file is read and written as UTF-8 with LF endings.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BASE)
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

STAMP_OLD = ("- [ ] P2 tech seed (R2381, from this window own measured seam): "
             "`src/os/review_window_guard_parity_blind_agreement.py`")
STAMP_NEW = ("- [x] [done 2026-11-02 R2387] P2 tech seed (R2381, from this "
             "window own measured seam): "
             "`src/os/review_window_guard_parity_blind_agreement.py`")

DISCHARGE = (
    "\n  DISCHARGED R2387 (line 439, AC-RWGB1..AC-RWGB6): "
    "src/os/review_window_guard_parity_blind_agreement.py plus "
    "src/os/test_review_window_guard_parity_blind_agreement.py shipped with "
    "the criteria pinned in this row at R2381 BEFORE the code. The parity is "
    "imported and asked at call time, so patching its check moves this "
    "reading; an agreement where either side could not judge reads "
    "PARITY-UNKNOWN naming both carried codes (never AGREES), a real split "
    "still reads PARITY-DISAGREES and outranks an ignorance, and every "
    "informed reading keeps the parity own eight fields byte for byte. The "
    "argument face UNKNOWN word is taken from that face vocabulary at call "
    "time rather than restated. SUITE PASS 6/6 twice identical plus three "
    "adjacent review-window suites green "
    "(qa/review-window-guard-parity-blind-agreement-R2387.log, 3803B, "
    "legs=2 identical=True adjacent=3 fails=0). LIVE: "
    "qa/review-window-guard-parity-blind-agreement-live-R2387.log reads the "
    "real tree PARITY-AGREES ignorance=none window=100 with a byte-stable "
    "--json over the nine pinned keys, and a fixture declaration neither face "
    "can read reads PARITY-UNKNOWN both at rc 1 where the shipped parity "
    "still reads PARITY-AGREES. One REAL measured gap seeded below: no "
    "product path reads either reading.\n")

SEED = (
    "\n- [ ] P2 tech seed (R2387, from this window own measured seam): "
    "`src/os/review_window_guard_parity_consumer_wire.py` - the review-window "
    "parity can now tell an informed agreement from a blind one, but NOTHING "
    "in the product ever asks it: measured this window with git grep, `RWGP.` "
    "has ZERO non-test hits under src/ and review_window_guard_parity is "
    "referenced only by its own suite, the runner registry and round scripts, "
    "so a split - and now an ignorance - refuses no path an operator actually "
    "walks. Product: the reading is ASKED from the path that acts on the "
    "declarations list, so PARITY-DISAGREES and PARITY-UNKNOWN refuse with "
    "their own codes where the window would be used, while an informed "
    "PARITY-AGREES leaves today's behaviour byte for byte. Criteria "
    "AC-RWPC1..AC-RWPC6 pre-registered HERE BEFORE any code: AC-RWPC1 the "
    "consumer asks the shipped reading at call time, so patching it moves what "
    "the acting path does and no second rewind comparison is written; AC-RWPC2 "
    "a split refuses with its own code naming both faces; AC-RWPC3 a blind "
    "agreement refuses with its own code naming the ignorant side(s) and never "
    "the same word as a split; AC-RWPC4 an informed agreement leaves the "
    "acting path byte-identical to today, proved on the same world before and "
    "after; AC-RWPC5 the refusal codes and the pinned report keys extend "
    "without renaming any shipped word, exits 0/2/3/5 unchanged; AC-RWPC6 pure "
    "ASCII, stdlib only, zero network, no clock, plus its own reconcile label. "
    "Five anchors zero-occupancy at HEAD 2026-11-02: "
    "review_window_guard_parity_consumer_wire, AC-RWPC, E_RWPC, "
    "os-review-window-guard-parity-consumer-wire, "
    "test_review_window_guard_parity_consumer_wire.\n")


def main():
    before = io.open(QUEUE, "r", encoding="utf-8", newline="").read()
    if STAMP_OLD not in before:
        print("REFUSED: the seeded row is not present verbatim")
        return 2
    if before.count(STAMP_OLD) != 1:
        print("REFUSED: the seeded row matched %d times" % before.count(STAMP_OLD))
        return 2
    if "review_window_guard_parity_consumer_wire" in before:
        print("REFUSED: the seed row already exists")
        return 2
    after = before.replace(STAMP_OLD, STAMP_NEW + DISCHARGE, 1)
    after = after + SEED
    io.open(QUEUE, "w", encoding="utf-8", newline="\n").write(after)
    written = io.open(QUEUE, "r", encoding="utf-8", newline="").read()
    print("STAMPED row 439 [done 2026-11-02 R2387] (payload %d chars)"
          % len("[done 2026-11-02 R2387]"))
    print("SEEDED review_window_guard_parity_consumer_wire")
    print("bytes %d -> %d (delta %d)" % (len(before), len(after),
                                         len(after) - len(before)))
    print("readback ok=%s stamp=%s seed=%s"
          % (written == after, STAMP_NEW in written,
             "AC-RWPC1" in written))
    return 0


if __name__ == "__main__":
    sys.exit(main())