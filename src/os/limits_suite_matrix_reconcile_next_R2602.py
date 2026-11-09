"""R2602 limits probe for the NEXT queue row (read-only, temp dirs only).

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
LEG = os.path.join(REPO, "qa", "reconcile-all-R2595-retry2.log")


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
    work = tempfile.mkdtemp(prefix="edmc-")
    try:
        base = read(DOC)
        patterns = SM.load_patterns()
        title = patterns["labels"]["matrix_title"]

        # (a) header six cells, separator FIVE dashes -> is the shape checked?
        lines = base.splitlines(True)
        inside = False
        for index, line in enumerate(lines):
            if line.strip() == title.strip():
                inside = True
                continue
            if inside and line.startswith("|---"):
                lines[index] = "|---|---|---|---|\n"
                break
        path_a = os.path.join(work, "sep5.md")
        put(path_a, "".join(lines))
        cells_a = SMR.matrix_header_cells(read(path_a), patterns)
        rep_a = SMR.report(path_a, LEG)
        print("A separator-5 header_cells=%s verdict=%s exit=%s"
              % (cells_a, rep_a["verdict"], rep_a["exit"]))

        # (b) a document that carries NO matrix table at all: which word?
        lines = base.splitlines(True)
        kept = []
        inside = False
        for line in lines:
            if line.strip() == title.strip():
                inside = True
                continue
            if inside and line.startswith("|"):
                continue
            kept.append(line)
        path_b = os.path.join(work, "no-table.md")
        put(path_b, "".join(kept))
        cells_b = SMR.matrix_header_cells(read(path_b), patterns)
        rep_b = SMR.report(path_b, LEG)
        print("B no-matrix-table header_cells=%s verdict=%s rows=%s"
              % (cells_b, rep_b["verdict"], rep_b.get("doc_rows")))

        # (c) --qa-dir together with --evidence: which one wins, any word?
        probe = os.path.join(work, "qa-empty")
        os.makedirs(probe)
        rep_c = SMR.report(DOC, LEG, probe)
        print("C evidence+qa-dir verdict=%s walk=%s"
              % (rep_c["verdict"], rep_c.get("walk")))

        # (d) a qa dir with NO pass leg: how much is decoded?
        dump = os.path.join(work, "qa-dump")
        os.makedirs(dump)
        for index in range(40):
            put(os.path.join(dump, "x%02d.log" % index), "STATUS unknown\n")
        path_d, run_d, walk_d = SMR.newest_pass_leg_scanned(dump)
        print("D no-pass-leg path=%s considered=%d decoded=%d"
              % (path_d, walk_d["considered"], walk_d["decoded"]))
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()