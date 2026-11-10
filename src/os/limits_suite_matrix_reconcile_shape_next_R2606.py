"""R2606 limit meter for the NEXT row on src/os/suite_matrix_reconcile.py.

Measures, on private copies of the real document, what the SHIPPED face still
answers after AC-EDMD1..AC-EDMD6, so the successor seed row is written from
measurement rather than from opinion. Read-only with respect to docs/ and qa/;
the only file it writes is its own log.
"""

import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import suite_matrix_reconcile as SMR  # noqa: E402
import suite_matrix as SM  # noqa: E402

DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
OUT = os.path.join(REPO, "qa", "limits-matrix-reconcile-shape-next-R2606.log")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def table_lines(lines, title):
    for index, line in enumerate(lines):
        if line.strip() != title.strip():
            continue
        header = None
        for j in range(index + 1, len(lines)):
            if not lines[j].startswith("|"):
                if lines[j].strip():
                    return None
                continue
            if header is None:
                header = j
                continue
            return header, j
        return None
    return None


def main():
    patterns = SM.load_patterns()
    title = patterns["labels"]["matrix_title"]
    green = SMR.newest_pass_leg()[0]
    work = tempfile.mkdtemp(prefix="edmd-lim-")
    lines_out = []
    try:
        text = read(DOC)
        lines = text.splitlines(True)
        where = table_lines(lines, title)
        header, sep = where
        cells = lines[header].count("|") - 1

        # (a) a separator drawn with MIXED punctuation.
        mixed = list(lines)
        mixed[sep] = "|" + "-=" * 3 + "|" + "=-" * 3 + "|" * (cells - 1) \
            + "\n"
        path = os.path.join(work, "mixed.md")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("".join(mixed))
        r = SMR.report(path, green)
        lines_out.append(
            "A mixed-punct-separator shape=%s verdict=%s exit=%d"
            % (SMR.matrix_shape("".join(mixed), patterns), r["verdict"],
               r["exit"]))

        # (b) a matrix title inside a fenced code block.
        fenced = text + "\n```\n" + title + "\n```\n"
        path = os.path.join(work, "fenced.md")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(fenced)
        count = SMR.matrix_title_count(fenced, patterns)
        r = SMR.report(path, green)
        lines_out.append(
            "B fenced-title titles=%d verdict=%s exit=%d"
            % (count, r["verdict"], r["exit"]))

        # (c) a title line with trailing spaces (stripped, so it still counts).
        trailing = text + "\n" + title + "   \n"
        path = os.path.join(work, "trailing.md")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(trailing)
        count = SMR.matrix_title_count(trailing, patterns)
        r = SMR.report(path, green)
        lines_out.append(
            "C trailing-title titles=%d verdict=%s exit=%d"
            % (count, r["verdict"], r["exit"]))

        # (d) ceiling of ONE over a pile that has no PASS leg: the bound is
        # reached and named, but the walk still decoded one candidate.
        starved = os.path.join(work, "qa")
        os.makedirs(starved, exist_ok=True)
        for name in ("one.log", "two.log"):
            with open(os.path.join(starved, name), "w", encoding="utf-8",
                      newline="\n") as handle:
                handle.write("RUNNER FAIL (1 failed assertions)\n")
        r = SMR.report(DOC, None, starved, 1)
        lines_out.append(
            "D ceiling-one verdict=%s walk=%s" % (r["verdict"],
                                                 r.get("walk")))
        body = "\n".join(lines_out) + "\n"
        with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
        print(body, end="")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())