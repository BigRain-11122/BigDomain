"""R2633 measurement of the AC-EDMJ fix - the SAME four shapes the R2630
successor script measured, re-read AFTER the change, plus the two named
answers the fix publishes.

Read-only against private copies; docs/ is never touched.
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
                   "limits-matrix-reconcile-second-table-separator-R2633.log")

ROW = "| 999 | probe-suite | os/probe.py | 6 | green | 1.0 |"
HEAD = "| # | Suite | Path | Criteria | State | Secs |"


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def rows_of(lines):
    return [i for i, line in enumerate(lines) if SMR.ROW_RE.match(line)]


def doctor(text, which):
    lines = text.splitlines()
    at = rows_of(lines)[-1] + 1
    if which == "header_narrow_separator":
        block = [HEAD, "|---|---|", ROW]
    elif which == "header_no_separator":
        block = [HEAD, ROW]
    elif which == "two_nonnumeric":
        for row in rows_of(lines)[:2]:
            parts = [c.strip()
                     for c in lines[row].strip().strip("|").split("|")]
            parts[0] = "n/a"
            lines[row] = "| " + " | ".join(parts) + " |"
        return "\n".join(lines) + "\n"
    elif which == "numeric_footer":
        block = ["| 4834 | total |  |"]
    else:
        raise AssertionError("E_R2633_UNKNOWN")
    return "\n".join(lines[:at] + block + lines[at:]) + "\n"


def main():
    if not os.path.exists(DOC):
        print("E_R2633_NO_DOC")
        return 3
    text = read(DOC)
    real = SMR.doc_rows(text)
    registry_rows, registry_criteria = SMR.registry_counts()
    measured = {}
    problems = {}
    for which in ("header_narrow_separator", "header_no_separator",
                  "two_nonnumeric", "numeric_footer"):
        doctored = doctor(text, which)
        measured[which], problems[which] = SMR.doc_rows_scan(doctored)
    out = [
        "R2633 measurement of the AC-EDMJ fix (read-only, private copies)",
        "registry_rows=%d registry_criteria=%d real_rows=%d"
        % (registry_rows, registry_criteria, real),
        "second_header_narrow_separator rows=%d delta=%+d problem=%s"
        % (measured["header_narrow_separator"],
           measured["header_narrow_separator"] - real,
           problems["header_narrow_separator"]),
        "second_header_no_separator rows=%d delta=%+d problem=%s"
        % (measured["header_no_separator"],
           measured["header_no_separator"] - real,
           problems["header_no_separator"]),
        "two_adjacent_nonnumeric_rows rows=%d delta=%+d problem=%s"
        % (measured["two_nonnumeric"], measured["two_nonnumeric"] - real,
           problems["two_nonnumeric"]),
        "numeric_footer_row rows=%d delta=%+d problem=%s"
        % (measured["numeric_footer"], measured["numeric_footer"] - real,
           problems["numeric_footer"]),
    ]
    body = "\n".join(out) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print(body, end="")
    ok = (measured["header_narrow_separator"] == real
          and problems["header_narrow_separator"] == (6, 2)
          and measured["header_no_separator"] == real
          and problems["header_no_separator"] == (6, None)
          and measured["two_nonnumeric"] == real - 2
          and problems["two_nonnumeric"] is None
          and measured["numeric_footer"] == real
          and problems["numeric_footer"] is None)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
