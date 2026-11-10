"""R2616 seed: ONE tech row measuring the THREE limits this window left open.

MEASURED this window with src/os/limits_matrix_reconcile_fence_rows_R2616.py
against private copies of the REAL document (qa/limits-matrix-reconcile-fence
-rows-R2616.log): (a) a data row inside a SECOND table that is not fenced is
still counted (doc_rows 641 -> 642, delta 1); (b) a fence OPENED and never
closed quotes nothing and is never named, so a broken document reads
STALE-CONTENT instead of a fence-shape answer (delta 0); (c) a four-backtick
fence carrying a three-backtick line toggles TWICE, so the row after the
block is counted and inside stays counted (delta 1 -> ROWS-MISMATCH).

Every number printed here is read from the files on disk.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
ANCHOR = "- [ ] P2 tech seed (R2596,"

SEED = (
    "- [ ] P2 tech seed (R2616, from this window own measured limit): "
    "`src/os/suite_matrix_reconcile.py` fence and table-rowed law - limits "
    "MEASURED this window with "
    "src/os/limits_matrix_reconcile_fence_rows_R2616.py against private "
    "copies of the real document (qa/limits-matrix-reconcile-fence-rows-"
    "R2616.log): (a) a data-shaped row inside a SECOND table that is NOT "
    "fenced is still counted (measured doc_rows 641 -> 642, delta 1), so the "
    "row law is fence-aware but not table-aware; (b) a fence that is OPENED "
    "and never closed quotes nothing and is never named as a shape problem, "
    "so a broken document keeps its content word (measured delta 0, verdict "
    "STALE-CONTENT); (c) a four-backtick fence carrying a three-backtick "
    "line toggles TWICE, so a row inside the block is counted AND the row "
    "after it is counted (measured doc_rows 641 -> 642, delta 1, verdict "
    "ROWS-MISMATCH). Product: ONE reading that counts a matrix row only "
    "inside the FIRST table under the shipped title, and that names an "
    "unclosed fence and a nested fence dialect instead of staying silent. "
    "Criteria AC-EDMG1..AC-EDMG6 pinned HERE BEFORE any code: AC-EDMG1 a "
    "data row in a SECOND table under the same title is not counted as a "
    "matrix row, and a document whose only row difference is in that second "
    "table stops reading ROWS-MISMATCH; AC-EDMG2 a fence opened and never "
    "closed is REFUSED by name with the line it was opened on, instead of "
    "silently quoting the rest of the document; AC-EDMG3 a fence whose "
    "opening marker is LONGER than the closing marker it carries inside is "
    "reported as a nested dialect naming both markers, instead of toggling "
    "twice and counting a quoted row; AC-EDMG4 the shipped check face is "
    "still asked exactly once per reading so a content difference keeps its "
    "content word; AC-EDMG5 every R2616 answer survives beside the new ones "
    "(fenced quoted row not counted, same-header-no-separator one table, "
    "other-header repeat TITLE-REPEATED with the count, all four shape "
    "words, both counts, the named evidence source, one CLI word and the "
    "exit codes) proved on the same fixtures; AC-EDMG6 pure ASCII, stdlib "
    "only, no clock, zero network, its own reconcile label and its own "
    "suite.\n"
)


def main():
    text = io.open(QUEUE, "r", encoding="utf-8").read()
    if "AC-EDMG1" in text:
        raise SystemExit("already seeded")
    lines = text.splitlines(True)
    at = None
    for index, line in enumerate(lines):
        if line.startswith(ANCHOR):
            at = index
            break
    if at is None:
        raise SystemExit("anchor row not found: %s" % ANCHOR[:40])
    before = len(text.encode("utf-8"))
    lines.insert(at, SEED)
    out = "".join(lines)
    after = len(out.encode("utf-8"))
    io.open(QUEUE, "w", encoding="utf-8", newline="").write(out)
    back = io.open(QUEUE, "r", encoding="utf-8").read()
    print("inserted at line %d, bytes %d -> %d, readback_ok=%s"
          % (at + 1, before, after, "AC-EDMG1" in back))
    return 0


if __name__ == "__main__":
    sys.exit(main())
