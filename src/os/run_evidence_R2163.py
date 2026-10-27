"""Double-run evidence generator for the R2163 category refund-months
suite.

Runs the suite twice through the single evidence writer (utf-8 LF, post
write dialect assertion) and reports whether the two runs are
byte-identical. ASCII source, zero network.
"""

import hashlib
import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import evidence_writer as EVID  # noqa: E402

SUITE = os.path.join(SRC, "sandbox", "ledger",
                     "test_apimarket_categoryrefundmonths.py")
ROUND = "R2163"


def one_run():
    proc = subprocess.Popen([sys.executable, SUITE],
                            cwd=REPO,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    out, _ = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace")


def main():
    first = one_run()
    second = one_run()
    qa = os.path.join(REPO, "qa")
    names = []
    for suffix, run in (("a", first), ("b", second)):
        path = os.path.join(
            qa, "apimarket-categoryrefundmonths-%s-%s.log"
            % (ROUND, suffix))
        EVID.write_evidence(path, run[1])
        names.append(path)
    with io.open(names[0], "r", encoding="utf-8") as handle:
        left = handle.read()
    with io.open(names[1], "r", encoding="utf-8") as handle:
        right = handle.read()
    same = left == right
    digest = hashlib.sha256(left.encode("utf-8")).hexdigest()[:16]
    print("rc=%d/%d identical=%r sha16=%s bytes=%d"
          % (first[0], second[0], same, digest, len(left.encode())))
    print("verdict=%s" % left.strip().splitlines()[-1])
    return 0 if (same and first[0] == 0 and second[0] == 0) else 1


if __name__ == "__main__":
    sys.exit(main())