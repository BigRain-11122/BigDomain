"""Re-measure the three limits the AC-EDMG row names, BEFORE any code.

Private copies only: docs/ is never touched. Each measurement prints the
row law answer (doc_rows) and the shipped report verdict on a PASS leg.

Row: P2 tech seed (R2616) - a data-shaped row inside a SECOND table that is
NOT fenced is still counted; a fence opened and never closed is never named
as a shape problem; a four-backtick fence carrying a three-backtick line
toggles twice so a quoted row AND the row after it are counted.
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
QA_DIR = os.path.join(REPO, "qa")
ROW = "| 999 | probe-suite | os/probe.py | 6 | green | 1.0 |"


def green_leg():
    paths = [os.path.join(QA_DIR, n) for n in os.listdir(QA_DIR)
             if n.endswith(".log")]
    paths.sort(key=lambda p: (-os.path.getmtime(p), os.path.basename(p)))
    for path in paths:
        try:
            _, run = SM.parse_evidence(path)
        except (OSError, UnicodeDecodeError):
            continue
        if run and run["verdict"] == "PASS":
            return path
    return None


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main():
    leg = green_leg()
    text = SMR.read_text(DOC)
    real = SMR.doc_rows(text)
    rows, criteria = SMR.registry_counts()
    out = ["DOC bytes=%d doc_rows=%d registry=%d criteria=%d"
           % (len(text.encode("utf-8")), real, rows, criteria),
           "PASS leg=%s" % (os.path.basename(leg) if leg else "NONE")]
    work = tempfile.mkdtemp(prefix="edmg-limits-")
    try:
        second = os.path.join(work, "second.md")
        write(second, text + "\n| a | b | c | d | e | f |\n"
                            "|---|---|---|---|---|---|\n" + ROW + "\n")
        got = SMR.doc_rows(SMR.read_text(second))
        rep = SMR.report(second, leg)
        out.append("(a) second unfenced table: doc_rows=%d real=%d delta=%d"
                   " verdict=%s" % (got, real, got - real, rep["verdict"]))

        open_fence = os.path.join(work, "openfence.md")
        write(open_fence, text + "\n```\n" + ROW + "\n")
        got_b = SMR.doc_rows(SMR.read_text(open_fence))
        rep_b = SMR.report(open_fence, leg)
        out.append("(b) unclosed fence at EOF: doc_rows=%d real=%d delta=%d"
                   " verdict=%s shape_named=%s"
                   % (got_b, real, got_b - real, rep_b["verdict"],
                      rep_b["verdict"] in ("FENCE-UNCLOSED", "FENCE-NESTED")))

        nested = os.path.join(work, "nested.md")
        write(nested, text + "\n````\n" + ROW + "\n```\n" + ROW + "\n````\n")
        got_c = SMR.doc_rows(SMR.read_text(nested))
        rep_c = SMR.report(nested, leg)
        out.append("(c) four-backtick fence carrying a three-backtick line:"
                   " doc_rows=%d real=%d delta=%d verdict=%s shape_named=%s"
                   % (got_c, real, got_c - real, rep_c["verdict"],
                      rep_c["verdict"] in ("FENCE-UNCLOSED", "FENCE-NESTED")))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("\n".join(out))


if __name__ == "__main__":
    main()
