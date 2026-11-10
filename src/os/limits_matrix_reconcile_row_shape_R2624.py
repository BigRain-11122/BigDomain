"""R2624 limits for the suite-matrix row law the queue head names.

The row this window claims (state/queue/tech.md:652, AC-EDMH1..AC-EDMH6) was
seeded at R2621 from a limit measured there: ONE malformed data row inside the
matrix table collapsed doc_rows to 0. This script re-measures that limit on the
committed tree BEFORE any byte of the product face is written, and measures the
two shapes its criteria name beside it: a GENUINE second-table header (which
must still end the first table) and a SEPARATOR row reappearing inside the
table (which must neither restart nor end it).

Read-only: every fixture is the real document doctored in memory.
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
import suite_matrix as SM  # noqa: E402
import reconcile_all as RA  # noqa: E402

DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
OUT = os.path.join(REPO, "qa", "limits-matrix-reconcile-row-shape-R2624.log")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def lines_of(text):
    return text.splitlines()


def table_bounds(text):
    """(first row index, last row index) of the matrix table, by shape."""
    lines = lines_of(text)
    first = None
    last = None
    for index, line in enumerate(lines):
        if SMR.ROW_RE.match(line):
            if first is None:
                first = index
            last = index
    return first, last


def doctor_wrong_cells(text, cells):
    """Replace the first data row with a row carrying `cells` cells."""
    lines = lines_of(text)
    first, _ = table_bounds(text)
    parts = [cell.strip() for cell in lines[first].strip().strip("|").split("|")]
    if cells < len(parts):
        parts = parts[:cells]
    else:
        parts = parts + ["x"] * (cells - len(parts))
    lines[first] = "| " + " | ".join(parts) + " |"
    return "\n".join(lines) + "\n"


def doctor_second_header(text):
    """A GENUINE second table: a header row then a separator row."""
    lines = lines_of(text)
    _, last = table_bounds(text)
    block = ["| # | Suite | Path | Criteria | State | Secs |",
             "|---|---|---|---|---|---|",
             "| 999 | probe-suite | os/probe.py | 6 | green | 1.0 |"]
    return "\n".join(lines[:last + 1] + block + lines[last + 1:]) + "\n"


def doctor_separator_inside(text):
    """A separator row reappearing in the MIDDLE of the matrix table."""
    lines = lines_of(text)
    first, last = table_bounds(text)
    mid = first + max(1, (last - first) // 2)
    return "\n".join(lines[:mid] + ["|---|---|---|---|---|---|"]
                     + lines[mid:]) + "\n"


def main():
    if not os.path.exists(DOC):
        print("E_R2624_NO_DOC")
        return 3
    real_text = read(DOC)
    real = SMR.doc_rows(real_text)
    registry_rows, registry_criteria = SMR.registry_counts()
    patterns = SM.load_patterns()
    titles = SMR.matrix_title_count(real_text, patterns)

    four = doctor_wrong_cells(real_text, 4)
    seven = doctor_wrong_cells(real_text, 7)
    second = doctor_second_header(real_text)
    sep = doctor_separator_inside(real_text)

    rows = {
        "real": real,
        "wrong4": SMR.doc_rows(four),
        "wrong7": SMR.doc_rows(seven),
        "second_table": SMR.doc_rows(second),
        "separator_inside": SMR.doc_rows(sep),
    }
    out = [
        "R2624 limits for the table-aware row law (read-only)",
        "doc=%s" % SMR.rel(DOC),
        "registry_rows=%d registry_criteria=%d titles=%d"
        % (registry_rows, registry_criteria, titles),
        "real_rows=%d delta=0" % rows["real"],
        "wrong_cell_row(4 cells) rows=%d delta=%+d"
        % (rows["wrong4"], rows["wrong4"] - rows["real"]),
        "wrong_cell_row(7 cells) rows=%d delta=%+d"
        % (rows["wrong7"], rows["wrong7"] - rows["real"]),
        "genuine_second_header rows=%d delta=%+d (must stay 0)"
        % (rows["second_table"], rows["second_table"] - rows["real"]),
        "separator_inside_table rows=%d delta=%+d (must stay 0)"
        % (rows["separator_inside"],
           rows["separator_inside"] - rows["real"]),
        "verdict wrong4=%s wrong7=%s"
        % (SMR.WORD_ROWS if rows["wrong4"] != registry_rows
           else SMR.WORD_CURRENT,
           SMR.WORD_ROWS if rows["wrong7"] != registry_rows
           else SMR.WORD_CURRENT),
    ]
    text = "\n".join(out) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
