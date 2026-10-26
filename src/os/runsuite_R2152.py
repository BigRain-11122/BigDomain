"""Double-run evidence generator for the R2152 ledger-line suite.

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

SUITE = os.path.join(BASE, "test_ledger_lines.py")
ROUND = "R2152"


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
        path = os.path.join(qa, "ledger-lines-%s-%s.log" % (ROUND, suffix))
        EVID.write_evidence(path, run[1])
        names.append(path)
    with io.open(names[0], "r", encoding="utf-8") as handle:
        left = handle.read()
    with io.open(names[1], "r", encoding="utf-8") as handle:
        right = handle.read()
    same = left == right
    digest = hashlib.sha256(left.encode("utf-8")).hexdigest()[:16]
    print("rc: %d/%d" % (first[0], second[0]))
    print("byte-identical: %s" % same)
    print("sha16: %s" % digest)
    print("evidence: %s" % names[0])
    print("evidence: %s" % names[1])
    ok = (first[0] == 0 and second[0] == 0 and same)
    print("VERDICT %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())