"""Single-writer evidence runner for the R2231 window.

Runs the new apimarket suite twice and writes each transcript itself as
utf-8 with LF endings. A shell redirection is deliberately not used:
the R2228/R2230 rounds proved PowerShell writes UTF-16LE with a BOM,
which the qa writer census then flags as a new dialect.

Usage: python src/os/evidence_R2231.py
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_apimarket_sellerquestionmonths.py")


def run(tag):
    out = os.path.join(ROOT, "qa",
                       "apimarket-sellerquestionmonths-R2231-%s.log" % tag)
    proc = subprocess.run([sys.executable, SUITE],
                          cwd=os.path.dirname(SUITE),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    body = proc.stdout.decode("utf-8", "replace")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print("%s rc=%d bytes=%d -> %s"
          % (tag.upper(), proc.returncode, len(body.encode("utf-8")),
             os.path.relpath(out, ROOT)))
    return proc.returncode, body


def main():
    rc_a, body_a = run("a")
    rc_b, body_b = run("b")
    same = body_a == body_b
    print("CRITERION_LINES_IDENTICAL %r" % same)
    if not same:
        return 1
    return 0 if rc_a == 0 and rc_b == 0 else 1


if __name__ == "__main__":
    sys.exit(main())