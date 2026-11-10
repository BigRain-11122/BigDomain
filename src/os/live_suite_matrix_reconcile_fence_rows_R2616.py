"""R2616 bounded LIVE leg: the fence-aware row law and the header-text table
identity measured on the REAL document, read-only, plus the SAME fixture
measured on a private copy so the closed shape is shown on both sides.

Writes one utf-8 LF evidence file. Nothing under docs/ or qa/ is mutated.
"""

import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(SRC, "sandbox"))

import suite_matrix as SM  # noqa: E402
import suite_matrix_reconcile as SMR  # noqa: E402

OUT = os.path.join(REPO, "qa", "suite-matrix-reconcile-fence-rows-live-R2616.log")
SHAPE = "| 9999 | quoted-example | src/os/quoted.py | 6 | PASS | 0.1 |"


def fence_scan(text):
    """(outside_rows, inside_rows) - what the row law sees on each side."""
    outside = inside = 0
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith(SMR.FENCE_MARK):
            in_fence = not in_fence
            continue
        if SMR.ROW_RE.match(line):
            if in_fence:
                inside += 1
            else:
                outside += 1
    return outside, inside


def main():
    lines = []
    text = SMR.read_text(SMR.DOC)
    patterns = SM.load_patterns()
    rows, criteria = SMR.registry_counts()
    outside, inside = fence_scan(text)
    verdict = SMR.report(SMR.DOC, None, None, 8)
    lines.append("LIVE doc=%s bytes=%d rows_outside_fence=%d"
                 " rows_inside_fence=%d doc_rows=%d registry_rows=%d"
                 " criteria=%d titles=%d"
                 % (SMR.rel(SMR.DOC), len(text.encode("utf-8")), outside,
                    inside, SMR.doc_rows(text), rows, criteria,
                    SMR.matrix_title_count(text, patterns)))
    lines.append("LIVE verdict=%s exit=%d walk=%s"
                 % (verdict["verdict"], verdict["exit"],
                    verdict.get("walk")))

    workdir = tempfile.mkdtemp(prefix="edmf-live-")
    try:
        # the SAME fixture on a private copy: one quoted data row, and the
        # same table repeated without its separator row.
        quoted = os.path.join(workdir, "quoted.md")
        shutil.copyfile(SMR.DOC, quoted)
        with open(quoted, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text + "\n" + SMR.FENCE_MARK + "\n" + SHAPE + "\n"
                         + SMR.FENCE_MARK + "\n")
        qoutside, qinside = fence_scan(SMR.read_text(quoted))
        found = SMR.title_tables(text, patterns)
        head = None
        if found:
            stem = "|" + "|".join(
                str(found[0][2][0]).split("|"))
            for line in text.splitlines():
                if line.startswith("|") and SMR.is_separator_row(line):
                    continue
                cells = "|".join(cell.strip() for cell in
                                 line.strip().strip("|").split("|"))
                if cells == found[0][2][0]:
                    head = line
                    break
        nosep = os.path.join(workdir, "nosep.md")
        shutil.copyfile(SMR.DOC, nosep)
        with open(nosep, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text + "\n"
                         + patterns["labels"]["matrix_title"].strip() + "\n\n"
                         + str(head) + "\n" + SHAPE + "\n")
        lines.append("FIXTURE quoted: rows_outside=%d rows_inside=%d"
                     " doc_rows=%d (registry=%d) -> %s"
                     % (qoutside, qinside, SMR.doc_rows(SMR.read_text(quoted)),
                        rows, SMR.report(quoted, None, None, 8)["verdict"]))
        lines.append("FIXTURE same-header-no-separator: titles=%d (real=%d)"
                     " -> %s"
                     % (SMR.matrix_title_count(SMR.read_text(nosep), patterns),
                        SMR.matrix_title_count(text, patterns),
                        SMR.report(nosep, None, None, 8)["verdict"]))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
