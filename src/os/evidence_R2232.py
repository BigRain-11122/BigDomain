"""Single-writer evidence runner for the R2232 window.

Runs the new apimarket suite twice and writes each transcript itself as
utf-8 with LF endings. A shell redirection is deliberately not used:
the R2228/R2230 rounds proved PowerShell writes UTF-16LE with a BOM,
which the qa writer census then flags as a new dialect.

Usage: python src/os/evidence_R2232.py
"""

import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_apimarket_buyeranswerwait.py")


def criterion_lines(body):
    return "\n".join(line for line in body.splitlines()
                     if line.startswith(("PASS ", "FAIL ", "SUITE ",
                                         "PRODUCT_SHA_STABLE ")))


def run(tag):
    out = os.path.join(ROOT, "qa",
                       "apimarket-buyeranswerwait-R2232-%s.log" % tag)
    proc = subprocess.run([sys.executable, SUITE],
                          cwd=os.path.dirname(SUITE),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    body = proc.stdout.decode("utf-8", "replace")
    # The child's piped stdout translates "\n" to os.linesep, so the
    # newline axis is normalised here (R2168/R2231 evidence dialect).
    body = body.replace("\r\n", "\n")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print("%s rc=%d bytes=%d sha16=%s -> %s"
          % (tag.upper(), proc.returncode, len(body.encode("utf-8")),
             hashlib.sha256(criterion_lines(body).encode("utf-8"))
             .hexdigest()[:16],
             os.path.relpath(out, ROOT)))
    return proc.returncode, body


def main():
    rc_a, body_a = run("a")
    rc_b, body_b = run("b")
    same = criterion_lines(body_a) == criterion_lines(body_b)
    print("CRITERION_LINES_IDENTICAL %r" % same)
    if not same:
        return 1
    return 0 if rc_a == 0 and rc_b == 0 else 1


if __name__ == "__main__":
    sys.exit(main())