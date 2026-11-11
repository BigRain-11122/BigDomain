"""R2633 successor limits, measured AFTER the AC-EDMJ fix so the next seed
names shapes that are still open.

Read-only against private copies of the real document.
  (a) a second-table header whose FIRST CELL is numeric but whose cells are
      otherwise text - the row law already counts it as a data row
  (b) a table-shaped run whose separator AGREES in width with its header -
      already ends the table (named as correct, not claimed)
  (c) a trailing table-shaped header with nothing after it
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
OUT = os.path.join(
    REPO, "qa", "limits-matrix-reconcile-second-table-separator-next-R2633.log")

ROW = "| 999 | probe-suite | os/probe.py | 6 | green | 1.0 |"
NUMBERED_HEAD = "| 1 | Suite | Path | Criteria | State | Secs |"
TEXT_HEAD = "| 2026 | Event | Count |"


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def rows_of(lines):
    return [i for i, line in enumerate(lines) if SMR.ROW_RE.match(line)]


def doctor(text, which):
    lines = text.splitlines()
    at = rows_of(lines)[-1] + 1
    if which == "numeric_first_cell_header":
        block = [NUMBERED_HEAD, "|---|---|", ROW]
    elif which == "agreeing_separator":
        block = [NUMBERED_HEAD, "|---|---|---|---|---|---|", ROW]
    elif which == "trailing_header":
        block = [TEXT_HEAD]
    else:
        raise AssertionError("E_R2633N_UNKNOWN")
    return "\n".join(lines[:at] + block + lines[at:]) + "\n"


def main():
    text = read(DOC)
    real = SMR.doc_rows(text)
    out = ["R2633 successor limits (read-only, measured after the AC-EDMJ fix)",
           "real_rows=%d" % real]
    for which in ("numeric_first_cell_header", "agreeing_separator",
                  "trailing_header"):
        count, problem = SMR.doc_rows_scan(doctor(text, which))
        out.append("%s rows=%d delta=%+d problem=%s"
                   % (which, count, count - real, problem))
    body = "\n".join(out) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print(body, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
