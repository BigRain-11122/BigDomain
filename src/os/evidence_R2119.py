"""Evidence writer for R2119 (single python writer, utf-8 LF, ASCII).

Runs the new suite twice and writes both logs, then prints the sha16 of
the criterion lines so a double run can be compared byte for byte.
"""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_apimarket_buyerquestions.py")
QA = os.path.join(ROOT, "qa")


def run(path):
    proc = subprocess.run([sys.executable, SUITE], cwd=ROOT,
                          capture_output=True)
    out = proc.stdout + proc.stderr
    text = out.decode("utf-8", "replace")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return proc.returncode, text


def criterion_lines(text):
    lines = [line for line in text.splitlines()
             if line.startswith(("PASS ", "FAIL ", "SUITE "))]
    return "\n".join(lines) + "\n"


def main():
    logs = []
    for suffix in ("", "-run2"):
        path = os.path.join(QA, "apimarket-buyerquestions-R2119.log"
                            + suffix)
        rc, text = run(path)
        logs.append((path, rc, text))
        print("run%s rc=%d bytes=%d %s"
              % (suffix or "1", rc, len(text.encode("utf-8")), path))
    a = criterion_lines(logs[0][2]).encode("utf-8")
    b = criterion_lines(logs[1][2]).encode("utf-8")
    print("criteria identical=%r sha16=%s"
          % (a == b, hashlib.sha256(a).hexdigest()[:16]))
    same = all(l.encode("utf-8") == a for l in
               [criterion_lines(logs[0][2]),
                criterion_lines(logs[1][2])])
    return 0 if (all(rc == 0 for _p, rc, _t in logs) and same) else 1


if __name__ == "__main__":
    sys.exit(main())