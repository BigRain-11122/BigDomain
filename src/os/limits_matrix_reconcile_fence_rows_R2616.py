"""R2616 successor limits: THREE shapes the fence-row face does NOT close,
measured on private copies so the next row is seeded from measurement.

(a) a data row inside a SECOND table (not fenced) is still counted
(b) a fence that is OPENED and never closed quotes the rest of the document
(c) a four-backtick fence containing a three-backtick line toggles twice

Writes one utf-8 LF evidence file. Pure ASCII source.
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

OUT = os.path.join(REPO, "qa", "limits-matrix-reconcile-fence-rows-R2616.log")
SHAPE = "| 9999 | quoted-example | src/os/quoted.py | 6 | PASS | 0.1 |"


def main():
    text = SMR.read_text(SMR.DOC)
    patterns = SM.load_patterns()
    real = SMR.doc_rows(text)
    rows, criteria = SMR.registry_counts()
    lines = ["DOC bytes=%d doc_rows=%d registry_rows=%d criteria=%d"
             % (len(text.encode("utf-8")), real, rows, criteria)]
    workdir = tempfile.mkdtemp(prefix="edmf-next-")
    try:
        # (a) second table with its OWN header and separator, unfenced
        second = os.path.join(workdir, "second.md")
        shutil.copyfile(SMR.DOC, second)
        with open(second, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text + "\n"
                         + patterns["labels"]["matrix_title"].strip() + "\n\n"
                         "| a | b | c | d | e | f |\n"
                         "|---|---|---|---|---|---|\n" + SHAPE + "\n")
        got = SMR.doc_rows(SMR.read_text(second))
        lines.append("(a) second unfenced table: doc_rows=%d real=%d delta=%d"
                     " titles=%d -> %s"
                     % (got, real, got - real,
                        SMR.matrix_title_count(SMR.read_text(second), patterns),
                        SMR.report(second, None, None, 8)["verdict"]))

        # (b) fence opened, never closed, with a data row after it
        open_fence = os.path.join(workdir, "open.md")
        shutil.copyfile(SMR.DOC, open_fence)
        with open(open_fence, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text + "\n" + SMR.FENCE_MARK + "\n")
        got = SMR.doc_rows(SMR.read_text(open_fence))
        lines.append("(b) unclosed fence at EOF: doc_rows=%d real=%d delta=%d"
                     " -> %s"
                     % (got, real, got - real,
                        SMR.report(open_fence, None, None, 8)["verdict"]))

        # (c) a four-backtick fence carrying a three-backtick line
        nested = os.path.join(workdir, "nested.md")
        shutil.copyfile(SMR.DOC, nested)
        with open(nested, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text + "\n````\n" + SMR.FENCE_MARK + "\n" + SHAPE
                         + "\n````\n" + SHAPE + "\n")
        got = SMR.doc_rows(SMR.read_text(nested))
        lines.append("(c) four-backtick fence with an inner three-backtick"
                     " line: doc_rows=%d real=%d delta=%d -> %s"
                     % (got, real, got - real,
                        SMR.report(nested, None, None, 8)["verdict"]))
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
