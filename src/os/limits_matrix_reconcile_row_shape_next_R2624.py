"""R2624 successor limits for the row law - measured AFTER the AC-EDMH fix so
the next seed row names shapes that are still open rather than ones already
closed here.

Measured on private copies of the real document:
  (a) a malformed row whose FIRST CELL is not numeric  -> still ends the table
  (b) a malformed row as the LAST row of the table     -> already correct
  (c) two adjacent malformed rows                      -> already correct
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import suite_matrix_reconcile as SMR  # noqa: E402

DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
OUT = os.path.join(REPO, "qa",
                   "limits-matrix-reconcile-row-shape-next-R2624.log")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def row_indexes(lines):
    return [i for i, line in enumerate(lines) if SMR.ROW_RE.match(line)]


def doctor(text, which):
    lines = text.splitlines()
    rows = row_indexes(lines)
    if which == "nonnumeric":
        parts = [c.strip() for c in
                 lines[rows[0]].strip().strip("|").split("|")]
        parts[0] = "n/a"
        lines[rows[0]] = "| " + " | ".join(parts) + " |"
    elif which == "last":
        parts = [c.strip() for c in
                 lines[rows[-1]].strip().strip("|").split("|")]
        lines[rows[-1]] = "| " + " | ".join(parts[:4]) + " |"
    elif which == "two":
        for row in rows[:2]:
            parts = [c.strip() for c in
                     lines[row].strip().strip("|").split("|")]
            lines[row] = "| " + " | ".join(parts[:4]) + " |"
    return "\n".join(lines) + "\n"


def main():
    text = read(DOC)
    real = SMR.doc_rows(text)
    rows = {
        "nonnumeric": SMR.doc_rows(doctor(text, "nonnumeric")),
        "last": SMR.doc_rows(doctor(text, "last")),
        "two": SMR.doc_rows(doctor(text, "two")),
    }
    out = ["R2624 successor limits (read-only, measured after the AC-EDMH fix)",
           "real_rows=%d" % real,
           "malformed_row_nonnumeric_first_cell rows=%d delta=%+d"
           % (rows["nonnumeric"], rows["nonnumeric"] - real),
           "malformed_row_as_last_row rows=%d delta=%+d (expected -1)"
           % (rows["last"], rows["last"] - real),
           "two_adjacent_malformed_rows rows=%d delta=%+d (expected -2)"
           % (rows["two"], rows["two"] - real)]
    body = "\n".join(out) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print(body, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
