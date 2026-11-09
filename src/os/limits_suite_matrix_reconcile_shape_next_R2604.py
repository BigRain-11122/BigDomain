"""R2604 limits probe for the NEXT queue row (read-only, temp dirs only).

Measures four candidate limits of src/os/suite_matrix_reconcile.py as it
stands after this window, so the successor seed names measured facts rather
than guesses. Prints one line per case; writes nothing outside %TEMP%.
"""

import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(SRC, "sandbox"))

import suite_matrix_reconcile as SMR  # noqa: E402
import suite_matrix as SM  # noqa: E402

DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
LEG = os.path.join(REPO, "qa", "reconcile-all-R2603.log")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def put(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main():
    if "--log" in sys.argv:
        path = sys.argv[sys.argv.index("--log") + 1]
        handle = io.open(path, "w", encoding="utf-8", newline="\n")
        sys.stdout = handle
    work = tempfile.mkdtemp(prefix="edmc-next-")
    try:
        base = read(DOC)
        patterns = SM.load_patterns()
        title = patterns["labels"]["matrix_title"].strip()

        # (a) a separator drawn with '=' instead of '-': still a separator?
        lines = base.splitlines(True)
        inside = False
        for index, line in enumerate(lines):
            if line.strip() == title:
                inside = True
                continue
            if inside and line.startswith("|---"):
                lines[index] = "|" + "|".join(["===="] * 4) + "|\n"
                break
        path_a = os.path.join(work, "eq-sep.md")
        put(path_a, "".join(lines))
        shape_a = SMR.matrix_shape(read(path_a), patterns)
        rep_a = SMR.report(path_a, LEG)
        print("A eq-separator shape=%s verdict=%s exit=%s"
              % (shape_a, rep_a["verdict"], rep_a["exit"]))

        # (b) a header with NO separator row at all: read or tolerated?
        lines = base.splitlines(True)
        inside = False
        kept = []
        for line in lines:
            if line.strip() == title:
                inside = True
                kept.append(line)
                continue
            if inside and line.startswith("|---"):
                continue
            kept.append(line)
        path_b = os.path.join(work, "no-sep.md")
        put(path_b, "".join(kept))
        shape_b = SMR.matrix_shape(read(path_b), patterns)
        rep_b = SMR.report(path_b, LEG)
        print("B no-separator shape=%s verdict=%s rows=%s"
              % (shape_b, rep_b["verdict"], rep_b.get("doc_rows")))

        # (c) ceiling=0: bounded before any candidate is read, or crash?
        try:
            path_c, run_c, walk_c = SMR.newest_pass_leg_scanned(None, 0)
            print("C ceiling-0 path=%s decoded=%s bounded=%s"
                  % (path_c, walk_c["decoded"], walk_c.get("bounded")))
        except Exception as exc:  # noqa: BLE001  measured, not raised
            print("C ceiling-0 RAISED %s: %s" % (type(exc).__name__, exc))

        # (d) the matrix title appearing TWICE: which table is read?
        twice = base.replace("## " + "billable", "## " + "billable")
        body = base.splitlines(True)
        doubled = "".join(body) + "\n" + title + "\n\n| a | b |\n|---|---|\n"
        path_d = os.path.join(work, "twice.md")
        put(path_d, doubled)
        shape_d = SMR.matrix_shape(read(path_d), patterns)
        rep_d = SMR.report(path_d, LEG)
        print("D title-twice shape=%s verdict=%s rows=%s"
              % (shape_d, rep_d["verdict"], rep_d.get("doc_rows")))
        _ = twice
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()