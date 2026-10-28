"""R2188 evidence writer: runs the seller-supply suite twice and records
both transcripts through a single utf-8 LF writer, then runs the
adjacent apimarket regression set. Pure ASCII source.
"""

import io
import os
import subprocess
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
QA = os.path.join(BASE, "qa")
PY = sys.executable

SUITE = os.path.join(BASE, "src", "sandbox", "ledger",
                     "test_apimarket_sellersupply.py")

ADJACENT = [
    "test_apimarket_supply.py",
    "test_apimarket_restock.py",
    "test_apimarket_categorysupplymonths.py",
    "test_apimarket_sellertodo.py",
    "test_apimarket_delist.py",
    "test_apimarket_relist.py",
]


def run(path):
    proc = subprocess.run([PY, path], cwd=os.path.dirname(path),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def write_lf(path, text):
    # The child Python writes CRLF on Windows in text mode, so the
    # capture is normalised before it reaches the single writer - else
    # the census classifies the file as the shell-capture dialect.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    rc1, out1 = run(SUITE)
    rc2, out2 = run(SUITE)
    write_lf(os.path.join(QA, "apimarket-sellersupply-R2188-a.log"), out1)
    write_lf(os.path.join(QA, "apimarket-sellersupply-R2188-b.log"), out2)
    print("suite rc1=%d rc2=%d identical=%r"
          % (rc1, rc2, out1 == out2), flush=True)

    lines = []
    for name in ADJACENT:
        path = os.path.join(BASE, "src", "sandbox", "ledger", name)
        if not os.path.exists(path):
            lines.append("MISSING %s" % name)
            continue
        rc, out = run(path)
        last = [ln for ln in out.split("\n") if ln.startswith("SUITE")]
        lines.append("rc=%d %s %s" % (rc, name,
                                      last[-1] if last else "NO-VERDICT"))
    text = "\n".join(lines) + "\n"
    write_lf(os.path.join(QA, "regression-R2188.log"), text)
    print(text, flush=True)
    ok = (rc1 == 0 and rc2 == 0 and out1 == out2
          and all(ln.startswith("rc=0 ") for ln in lines))
    print("EVIDENCE OK=%r" % ok, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())