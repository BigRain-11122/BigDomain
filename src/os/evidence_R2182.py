"""R2182: double-run the category-supply-months suite into qa/ logs.

Both runs are captured in-process as python bytes (LF, utf-8) so the
census dialect is not polluted by a pwsh CRLF capture.
"""

import hashlib
import os
import subprocess
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SUITE = os.path.join(BASE, "src", "sandbox", "ledger",
                     "test_apimarket_categorysupplymonths.py")


def run_once(tag):
    proc = subprocess.run([sys.executable, SUITE], cwd=BASE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    raw = proc.stdout.replace(b"\r\n", b"\n")
    path = os.path.join(BASE, "qa",
                        "apimarket-categorysupplymonths-R2182-%s.log"
                        % tag)
    with open(path, "wb") as handle:
        handle.write(raw)
    lines = [line for line in raw.decode("utf-8").split("\n")
             if line.startswith("PASS ") or line.startswith("FAIL ")
             or line.startswith("SUITE ")]
    return proc.returncode, path, "\n".join(lines), raw


def main():
    rc1, p1, c1, raw1 = run_once("a")
    rc2, p2, c2, raw2 = run_once("b")
    h1 = hashlib.sha256(c1.encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(c2.encode("utf-8")).hexdigest()
    print("run a rc=%d %s" % (rc1, os.path.basename(p1)))
    print("run b rc=%d %s" % (rc2, os.path.basename(p2)))
    print("criterion sha256 a=%s" % h1)
    print("criterion sha256 b=%s" % h2)
    print("IDENTICAL=%s" % (h1 == h2 and rc1 == 0 and rc2 == 0))
    print("bytes a=%d b=%d" % (len(raw1), len(raw2)))
    return 0 if (h1 == h2 and rc1 == 0 and rc2 == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())