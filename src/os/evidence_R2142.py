#!/usr/bin/env python3
"""evidence_R2142.py - double-run evidence for the apimarket search
availability axis (R2142). ASCII source, stdlib only, no network.

Runs src/sandbox/ledger/test_apimarket_searchstock.py twice in
separate process trees, writes both captures through the single
evidence writer (utf-8, no BOM, LF) as qa/apimarket-searchstock-
R2142-a.log / -b.log, and proves the criterion lines are byte
identical between the two runs.
"""

import hashlib
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, "src", "os"))

from evidence_writer import write_evidence  # noqa: E402

ROOT = BASE
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")
SUITE = "test_apimarket_searchstock.py"
QA = os.path.join(ROOT, "qa")


def run_once():
    env = dict(os.environ)
    # the suite echoes a few set reprs in its evidence lines, so the
    # hash seed is pinned to keep both runs byte identical
    env["PYTHONHASHSEED"] = "0"
    proc = subprocess.run([sys.executable, SUITE], cwd=LEDGER,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, env=env)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def criteria_lines(text):
    out = []
    for line in text.splitlines():
        head = line[:5]
        if (line.startswith("PASS ") or line.startswith("FAIL ")
                or line.startswith("SUITE ")):
            out.append(line)
        elif head.strip() and head.startswith("SUITE"):
            out.append(line)
    return "\n".join(out) + "\n"


def main():
    results = []
    for tag in ("a", "b"):
        rc, text = run_once()
        path = os.path.join(QA, "apimarket-searchstock-R2142-%s.log"
                            % tag)
        write_evidence(path, text)
        results.append((tag, rc, text, path))
        print("run %s rc=%d bytes=%d file=%s"
              % (tag, rc, len(text.encode("utf-8")),
                 os.path.basename(path)), flush=True)
    blobs = [criteria_lines(item[2]).encode("utf-8")
             for item in results]
    same = blobs[0] == blobs[1]
    sha = hashlib.sha256(blobs[0]).hexdigest()[:16]
    verdicts = [line for line in results[0][2].splitlines()
                if line.startswith("SUITE ")]
    print("verdict=%s identical=%r sha16=%s"
          % (verdicts[-1] if verdicts else "NONE", same, sha),
          flush=True)
    ok = (same and all(item[1] == 0 for item in results)
          and verdicts and verdicts[-1].startswith("SUITE PASS"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())