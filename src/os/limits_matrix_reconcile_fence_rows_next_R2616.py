"""R2616 limits: the two shapes the R2608 seed row names, measured on
private copies of the REAL document BEFORE any product byte is written.

(a) a data row INSIDE a fenced code block is still counted by ROW_RE
(b) two titles carrying the SAME header text, one WITH a separator row and
    one WITHOUT, count as TWO distinct tables -> TITLE-REPEATED
(c) two bare titles (already correct per R2608) re-measured
(d) the write path over a starved walk (already correct per R2608)

Writes one utf-8 LF evidence file. Pure ASCII source.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(SRC, "sandbox"))

import suite_matrix as SM  # noqa: E402
import suite_matrix_reconcile as SMR  # noqa: E402

DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
OUT = os.path.join(REPO, "qa", "limits-matrix-reconcile-fence-rows-next-R2616.log")


def main():
    text = SMR.read_text(DOC)
    patterns = SM.load_patterns()
    lines = []

    lines.append("DOC %s bytes=%d doc_rows=%d"
                 % (SMR.rel(DOC), len(text.encode("utf-8")),
                    SMR.doc_rows(text)))

    # (a) insert a fenced block carrying one data-shaped row
    quoted = "| 9999 | quoted-example-suite | src/os/quoted.py | 6 | PASS | 0.1 |"
    marker = None
    for index, line in enumerate(text.splitlines()):
        if line.startswith("| ") and line.count("|") == 7 and \
                line.strip().strip("|").split("|")[0].strip().isdigit():
            marker = index
            break
    if marker is None:
        lines.append("(a) NO-TABLE-FOUND")
    else:
        parts = text.splitlines(True)
        injected = parts[:marker + 1] + [
            "```\n", quoted + "\n", "```\n"] + parts[marker + 1:]
        doctored = "".join(injected)
        real = SMR.doc_rows(text)
        grown = SMR.doc_rows(doctored)
        rows, _criteria = SMR.registry_counts()
        lines.append("(a) fenced data row: real_rows=%d doctored_rows=%d"
                     " delta=%d registry_rows=%d quoted_counted=%s"
                     % (real, grown, grown - real, rows, grown != real))

    # (b) same header text, first table WITH separator, second WITHOUT
    header = None
    sep = None
    for line in text.splitlines():
        if line.startswith("|") and line.count("|") == 7:
            if header is None:
                header = line
                continue
            if SMR.is_separator_row(line):
                sep = line
                break
    if header is None or sep is None:
        lines.append("(b) NO-HEADER-FOUND")
    else:
        base = "\n".join([SMR.SM.load_patterns()["labels"]["matrix_title"],
                          "", header, sep,
                          "| 1 | s | src/os/s.py | 6 | PASS | 1.0 |", ""])
        with_sep = SMR.matrix_title_count(base, patterns)
        without_text = "\n".join([patterns["labels"]["matrix_title"],
                                  "", header,
                                  "| 1 | s | src/os/s.py | 6 | PASS | 1.0 |", ""])
        without = SMR.matrix_title_count(without_text, patterns)
        # one WITH sep then one WITHOUT sep, same header text
        mixed = "\n".join([patterns["labels"]["matrix_title"],
                           "", header, sep,
                           "| 1 | s | src/os/s.py | 6 | PASS | 1.0 |",
                           "", patterns["labels"]["matrix_title"], "",
                           header,
                           "| 2 | t | src/os/t.py | 6 | PASS | 1.0 |", ""])
        lines.append("(b) same-header repeat: one-with-sep titles=%d"
                     " one-without-sep titles=%d mixed titles=%d"
                     " mixed_reads_TITLE-REPEATED=%s"
                     % (with_sep, without,
                        SMR.matrix_title_count(mixed, patterns),
                        SMR.matrix_title_count(mixed, patterns) > 1))

    # (c) two bare titles introduce no table
    bare = "\n".join([patterns["labels"]["matrix_title"], "",
                      patterns["labels"]["matrix_title"], "",
                      header, sep,
                      "| 1 | s | src/os/s.py | 6 | PASS | 1.0 |", ""])
    lines.append("(c) bare titles: titles=%d"
                 % SMR.matrix_title_count(bare, patterns))

    # (d) starved walk on the compose path changes no byte
    before = len(text.encode("utf-8"))
    result = SMR.write(DOC, None, None, None, 0)
    after = os.path.getsize(DOC)
    lines.append("(d) starved walk: verdict=%s written=%s bytes_changed=%s"
                 % (result["verdict"], result.get("written"),
                    before != after))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
