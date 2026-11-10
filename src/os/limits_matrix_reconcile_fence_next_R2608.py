"""R2608 limit meter for the NEXT row on src/os/suite_matrix_reconcile.py.

Measures, on private copies, what the SHIPPED face still answers after
AC-EDME1..AC-EDME6, so the successor seed row is written from measurement
rather than opinion. Read-only with respect to docs/ and qa/; it writes only
its own log.
"""

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
OUT = os.path.join(REPO, "qa", "limits-matrix-reconcile-fence-next-R2608.log")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def copy(work, name, text):
    path = os.path.join(work, name)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


def main():
    patterns = SM.load_patterns()
    title = patterns["labels"]["matrix_title"].strip()
    green = SMR.newest_pass_leg()[0]
    work = tempfile.mkdtemp(prefix="edme-lim-")
    out = []
    try:
        text = read(DOC)
        rows_before = SMR.doc_rows(text)

        # (a) a data row INSIDE a fence: the row law is not fence-aware.
        fenced = text + "\n```\n| 1 | quoted | q/x.py | 6 | green | 0.1 |\n```\n"
        path = copy(work, "fenced-row.md", fenced)
        rep = SMR.report(path, green)
        out.append("A fenced-data-row doc_rows=%d before=%d verdict=%s"
                   % (SMR.doc_rows(fenced), rows_before, rep["verdict"]))

        # (b) two titles, same header text, one WITH and one WITHOUT a
        # separator row: counted as distinct tables or as one?
        second = ("\n" + title + "\n"
                  "| i | suite | path | criteria | state | secs |\n"
                  "| 1 | q | q/x.py | 6 | green | 0.1 |\n")
        path = copy(work, "two-titles.md", text + second)
        out.append("B same-header-one-no-separator titles=%d verdict=%s"
                   % (SMR.matrix_title_count(read(path), patterns),
                      SMR.report(path, green)["verdict"]))

        # (c) two titles back to back, neither introducing a table.
        bare = "\n" + title + "\n" + title + "\n"
        path = copy(work, "bare-titles.md", text + bare)
        out.append("C two-bare-titles titles=%d verdict=%s"
                   % (SMR.matrix_title_count(read(path), patterns),
                      SMR.report(path, green)["verdict"]))

        # (d) the write path with a STARVED walk: does it create or touch a
        # byte, and which word does it give?
        starved = os.path.join(work, "qa")
        os.makedirs(starved, exist_ok=True)
        for name in ("one.log", "two.log"):
            with open(os.path.join(starved, name), "w", encoding="utf-8",
                      newline="\n") as handle:
                handle.write("RUNNER FAIL (1 failed assertions)\n")
        probe = copy(work, "write-probe.md", text)
        before = read(probe)
        wrote = SMR.write(probe, None, starved, None, 1)
        out.append("D write-starved verdict=%s written=%s bytes_changed=%s"
                   % (wrote["verdict"], wrote.get("written"),
                      read(probe) != before))

        body = "\n".join(out) + "\n"
        with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
        print(body, end="")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())