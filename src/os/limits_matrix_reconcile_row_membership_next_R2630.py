"""R2630 successor limits for the table-membership law - measured AFTER the
AC-EDMI fix so the next seed row names shapes that are still open rather than
ones already closed here.

Measured on private copies of the real document (read-only):
  (a) a SECOND-table header whose separator carries a DIFFERENT cell count
  (b) a SECOND-table header carrying NO separator row at all
  (c) two adjacent malformed rows whose first cell is not numeric
  (d) a footer row whose FIRST CELL IS numeric but whose cell count is wrong
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
                   "limits-matrix-reconcile-row-membership-next-R2630.log")

ROW = "| 999 | probe-suite | os/probe.py | 6 | green | 1.0 |"
HEAD = "| # | Suite | Path | Criteria | State | Secs |"


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def rows_of(lines):
    return [i for i, line in enumerate(lines) if SMR.ROW_RE.match(line)]


def doctor(text, which):
    lines = text.splitlines()
    rows = rows_of(lines)
    at = rows[-1] + 1
    if which == "header_narrow_separator":
        block = [HEAD, "|---|---|", ROW]
    elif which == "header_no_separator":
        block = [HEAD, ROW]
    elif which == "two_nonnumeric":
        for row in rows[:2]:
            parts = [c.strip()
                     for c in lines[row].strip().strip("|").split("|")]
            parts[0] = "n/a"
            lines[row] = "| " + " | ".join(parts) + " |"
        return "\n".join(lines) + "\n"
    elif which == "numeric_footer":
        block = ["| 4834 | total |  |"] 
    else:
        raise AssertionError("E_R2630_UNKNOWN")
    return "\n".join(lines[:at] + block + lines[at:]) + "\n"


def main():
    if not os.path.exists(DOC):
        print("E_R2630_NO_DOC")
        return 3
    text = read(DOC)
    real = SMR.doc_rows(text)
    registry_rows, registry_criteria = SMR.registry_counts()
    measured = {}
    for which in ("header_narrow_separator", "header_no_separator",
                  "two_nonnumeric", "numeric_footer"):
        measured[which] = SMR.doc_rows(doctor(text, which))
    out = [
        "R2630 successor limits (read-only, measured after the AC-EDMI fix)",
        "registry_rows=%d registry_criteria=%d real_rows=%d"
        % (registry_rows, registry_criteria, real),
        "second_header_narrow_separator rows=%d delta=%+d"
        % (measured["header_narrow_separator"],
           measured["header_narrow_separator"] - real),
        "second_header_no_separator rows=%d delta=%+d"
        % (measured["header_no_separator"],
           measured["header_no_separator"] - real),
        "two_adjacent_nonnumeric_rows rows=%d delta=%+d (expected -2)"
        % (measured["two_nonnumeric"], measured["two_nonnumeric"] - real),
        "numeric_footer_row rows=%d delta=%+d (expected 0)"
        % (measured["numeric_footer"], measured["numeric_footer"] - real),
    ]
    body = "\n".join(out) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print(body, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
