#!/usr/bin/env python3
"""evidence_R2238.py - double-run evidence for the retry-naming suite.

Runs src/os/test_os_retry_naming.py twice and writes both legs through
ONE python writer (run_identity.normalize, utf-8, LF, no BOM, one
trailing newline) - never a shell redirection, which is exactly the
dialect defect the R2230/R2233 windows had to repair afterwards.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
QA = os.path.join(REPO, "qa")
SUITE = os.path.join(HERE, "test_os_retry_naming.py")

sys.path.insert(0, HERE)
import run_identity as RI


def run_suite():
    proc = subprocess.run([sys.executable, SUITE], capture_output=True)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def write_leg(path, text):
    payload = RI.normalize(text)
    with open(path, "wb") as handle:
        handle.write(payload.encode("utf-8"))
    with open(path, "rb") as handle:
        raw = handle.read()
    assert b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf")
    return raw


def main():
    os.makedirs(QA, exist_ok=True)
    legs = []
    for label in ("a", "b"):
        rc, out = run_suite()
        print("SUITE-%s rc=%d" % (label.upper(), rc))
        legs.append((rc, out))
    if legs[0][0] != 0 or legs[1][0] != 0:
        sys.stderr.write("a leg failed, no evidence written\n")
        return 1
    if legs[0][1] != legs[1][1]:
        sys.stderr.write("legs differ, no evidence written\n")
        return 1
    bodies = []
    for label, (_rc, out) in zip(("a", "b"), legs):
        path = os.path.join(QA, "os-retry-naming-R2238-%s.log" % (label,))
        bodies.append(write_leg(path, out))
        print("WROTE %s bytes=%d" % (os.path.basename(path), len(bodies[-1])))
    if bodies[0] != bodies[1]:
        sys.stderr.write("legs not byte identical\n")
        return 1
    print("IDENTICAL sha16=%s" % (RI.digest16(bodies[0].decode("utf-8")),))
    return 0


if __name__ == "__main__":
    sys.exit(main())