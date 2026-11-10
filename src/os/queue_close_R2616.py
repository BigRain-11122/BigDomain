"""R2616 closer: mark the AC-EDMF1..6 tech row done with its DISCHARGED note.

The row was seeded at R2608 with its six criteria pinned BEFORE any code and
its four limits re-measured at the start of R2616. Every number printed here
is measured on the files on disk.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
HEAD = "- [ ] P2 tech seed (R2608,"
DONE = "- [x] [done 2026-11-10 R2616] P2 tech seed (R2608,"

NOTE = (
    "\n\n  DISCHARGED R2616 (AC-EDMF1..AC-EDMF6 pinned in this row BEFORE "
    "any code, four limits re-measured at the start of this window with "
    "src/os/limits_matrix_reconcile_fence_rows_next_R2616.py): the row law "
    "in src/os/suite_matrix_reconcile.py is now FENCE-AWARE - the scan skips "
    "``` blocks, so a quoted data row is not a matrix row (MEASURED real 641 "
    "-> doctored 641, delta 0, was 641 -> 642 before the change) and a "
    "document whose only row difference is quoted no longer reads "
    "ROWS-MISMATCH (unpatched it now reads STALE-CONTENT, the shipped check "
    "face own content word, and with the check green it reads DOC-CURRENT "
    "where the old law read ROWS-MISMATCH). A table is now identified by its "
    "HEADER TEXT and WIDTH instead of by its separator width, so the same "
    "table repeated WITHOUT its separator row is the SAME table "
    "(MEASURED titles=1, was 2 -> TITLE-REPEATED), while a table with "
    "DIFFERENT header text is still a second table and still refuses "
    "TITLE-REPEATED naming the count (MEASURED titles=2 exit=3). The shipped "
    "check face is still asked exactly once per reading (MEASURED "
    "check-asked=1 code=2 on a content-doctored copy, which keeps "
    "STALE-CONTENT), and every R2608 answer survives on the same fixtures. "
    "Suites: src/os/test_suite_matrix_reconcile_fence_rows.py "
    "AC-EDMF1..AC-EDMF6 SUITE PASS 6/6, proved TWICE with an identical "
    "digest through the shipped capture callable "
    "(qa/suite-matrix-reconcile-fence-rows-R2616.log, 1824B, legs=2 "
    "identical=True adjacent=3 fails=0, digest 8BF6A2A18FFF1898). Registry "
    "640/4816 -> 641/4822 by exactly one row, recounted by import; "
    "docs/sandbox-suite-matrix.md regenerated through the shipped write face "
    "to 65483B / 641 rows / 4822 criteria and --check reads DOC-CURRENT.\n"
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
    ok = DONE in back and "DISCHARGED R2616" in back
    print("bytes %d -> %d readback_ok=%s" % (before, after, ok))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
