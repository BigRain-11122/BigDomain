"""R2111 evidence writer: run the new suite twice, land both stdout
captures as UTF-8/LF evidence logs and a stable double-run judgement.

The temp-dir names inside the raw stdout differ per run (mkdtemp), so
the byte-identity judgement is taken over the PASS/FAIL/child lines,
which carry every verdict and the deterministic html sha16.
"""

import hashlib
import io
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SANDBOX = os.path.join(BASE, "src", "sandbox")
SUITE = os.path.join("ledger", "test_apimarket_report_refundregister.py")
QA = os.path.join(BASE, "qa")
KEEP = re.compile(r"^(PASS|FAIL|SUITE|  child) ")


def run(tag):
    proc = subprocess.run([sys.executable, SUITE], cwd=SANDBOX,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        text = proc.stdout.decode("utf-8", "replace")
    except AttributeError:
        text = proc.stdout
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"
    path = os.path.join(QA, "apimarket-refundregister-R2111.log"
                        + ("" if tag == 1 else "-2"))
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    kept = [line for line in text.split("\n") if KEEP.match(line)]
    rescued = [line for line in kept if KEEP.match(line)]
    digest = hashlib.sha256(
        "\n".join(rescued).encode("utf-8")).hexdigest()[:16]
    return proc.returncode, path, text, digest, rescued


def main():
    rc1, p1, t1, d1, k1 = run(1)
    rc2, p2, t2, d2, k2 = run(2)
    same = d1 == d2 and k1 == k2
    judge = ("JUDGE double-run rc=%d/%d verdict_lines_sha16=%s/%s "
             "identical=%s criteria=%d\n"
             % (rc1, rc2, d1, d2, same, len(k1)))
    with io.open(p1, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(judge)
    print("PASS evidence %s (%d bytes) + %s"
          % (os.path.relpath(p1, BASE), len(t1.encode("utf-8")),
             os.path.relpath(p2, BASE)))
    print(judge.strip())
    return 0 if (rc1 == 0 and rc2 == 0 and same) else 1


if __name__ == "__main__":
    raise SystemExit(main())