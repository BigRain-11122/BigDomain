"""Measure the limits the NEXT row will be seeded from, on the FIXED law.

Private copies only. Three shapes:
  (a) a TILDE fence (~~~) is not a backtick fence, so a quoted row inside it
      is still counted as a matrix row and no shape is named;
  (b) a BARE six-cell row after the matrix table, separated only by a blank
      line and carrying no header of its own, is read as a matrix row;
  (c) a matrix data row carrying SEVEN cells matches no row of the law, so the
      row is counted as absent (the shape check only guards the header).
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
sys.path.insert(0, os.path.join(SRC, "sandbox", ".."))

import suite_matrix_reconcile as SMR  # noqa: E402
import suite_matrix as SM  # noqa: E402

DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
QA_DIR = os.path.join(REPO, "qa")
ROW = "| 999 | probe-suite | os/probe.py | 6 | green | 1.0 |"
ROW7 = "| 999 | probe-suite | os/probe.py | 6 | green | 1.0 | x |"


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
    out = ["DOC doc_rows=%d registry=%d criteria=%d" % (real, rows, criteria)]
    work = tempfile.mkdtemp(prefix="edmg-next-")
    try:
        tilde = os.path.join(work, "tilde.md")
        write(tilde, text + "\n~~~\n" + ROW + "\n~~~\n")
        got = SMR.doc_rows(SMR.read_text(tilde))
        rep = SMR.report(tilde, leg)
        out.append("(a) tilde fence: doc_rows=%d delta=%d verdict=%s"
                   " shape_named=%s"
                   % (got, got - real, rep["verdict"],
                      rep["verdict"] in ("FENCE-UNCLOSED", "FENCE-NESTED")))

        bare = os.path.join(work, "bare.md")
        write(bare, text + "\n" + ROW + "\n")
        got_b = SMR.doc_rows(SMR.read_text(bare))
        rep_b = SMR.report(bare, leg)
        out.append("(b) bare row after the table: doc_rows=%d delta=%d"
                   " verdict=%s"
                   % (got_b, got_b - real, rep_b["verdict"]))

        seven = os.path.join(work, "seven.md")
        write(seven, text.replace(ROW, ROW7, 1) if ROW in text else
              text + "\n" + ROW7 + "\n")
        source = SMR.read_text(seven)
        match = SMR.ROW_RE.search(source)
        if match is not None:
            source = source[:match.start()] + ROW7 + source[match.end():]
            write(seven, source)
        got_c = SMR.doc_rows(SMR.read_text(seven))
        rep_c = SMR.report(seven, leg)
        out.append("(c) seven-cell row: doc_rows=%d delta=%d verdict=%s"
                   % (got_c, got_c - real, rep_c["verdict"]))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("\n".join(out))


if __name__ == "__main__":
    main()
