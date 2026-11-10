"""R2630 limits for the table-membership law the queue head names.

The row this window claims (state/queue/tech.md:653, AC-EDMI1..AC-EDMI6) was
seeded at R2624 from a limit measured there: a malformed row whose FIRST CELL
is not numeric still ENDS the matrix table, so the count collapses to zero.

This script re-measures that limit on the committed tree BEFORE any byte of the
product face is written, and measures three shapes its criteria name beside it:

  (a) a malformed row whose FIRST CELL is not numeric -> still ends the table
  (b) a GENUINE header of a SECOND table (header + separator) -> already correct
  (c) the FOOTER/total row carried right after the last data row -> already
      correct, i.e. it is a non-row and does not change the count
  (d) a malformed row as the LAST row of the table -> already correct (-1)

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

DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
OUT = os.path.join(REPO, "qa",
                   "limits-matrix-reconcile-row-membership-R2630.log")


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
    elif which == "second_header":
        block = ["| # | Suite | Path | Criteria | State | Secs |",
                 "|---|---|---|---|---|---|",
                 "| 999 | probe-suite | os/probe.py | 6 | green | 1.0 |"]
        at = rows[-1] + 1
        lines = lines[:at] + block + lines[at:]
    elif which == "footer_after_last":
        footer = "|  | total |  | 4834 | green / FAIL 0 |  |"
        at = rows[-1] + 1
        lines = lines[:at] + [footer] + lines[at:]
    elif which == "nonnumeric_last":
        parts = [c.strip() for c in
                 lines[rows[-1]].strip().strip("|").split("|")]
        parts[0] = "n/a"
        lines[rows[-1]] = "| " + " | ".join(parts) + " |"
    return "\n".join(lines) + "\n"


def main():
    if not os.path.exists(DOC):
        print("E_R2630_NO_DOC")
        return 3
    text = read(DOC)
    real = SMR.doc_rows(text)
    registry_rows, registry_criteria = SMR.registry_counts()
    rows = {
        "nonnumeric": SMR.doc_rows(doctor(text, "nonnumeric")),
        "second": SMR.doc_rows(doctor(text, "second_header")),
        "footer": SMR.doc_rows(doctor(text, "footer_after_last")),
        "last": SMR.doc_rows(doctor(text, "nonnumeric_last")),
    }
    out = [
        "R2630 limits for the table-membership law (read-only)",
        "doc=%s" % SMR.rel(DOC),
        "registry_rows=%d registry_criteria=%d"
        % (registry_rows, registry_criteria),
        "real_rows=%d delta=0" % real,
        "malformed_row_nonnumeric_first_cell rows=%d delta=%+d (the gap)"
        % (rows["nonnumeric"], rows["nonnumeric"] - real),
        "genuine_second_header rows=%d delta=%+d (must stay 0)"
        % (rows["second"], rows["second"] - real),
        "footer_after_last_data_row rows=%d delta=%+d (must stay 0)"
        % (rows["footer"], rows["footer"] - real),
        "malformed_row_as_last_row rows=%d delta=%+d (must stay -1)"
        % (rows["last"], rows["last"] - real),
    ]
    body = "\n".join(out) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print(body, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
