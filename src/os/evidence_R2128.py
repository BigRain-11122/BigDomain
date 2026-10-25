"""R2128 evidence writer: run the buyer-ledger suite twice and capture
both runs with one ASCII/LF writer (PowerShell redirection is UTF-16 and
trips the census dialect gate)."""

import hashlib
import os
import subprocess
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SUITE = os.path.join(BASE, "src", "sandbox", "ledger",
                     "test_apimarket_buyerledger.py")
QA = os.path.join(BASE, "qa")


def run_once():
    proc = subprocess.run([sys.executable, SUITE], cwd=os.path.dirname(SUITE),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def criteria(text):
    return [line for line in text.splitlines()
            if line.startswith("PASS ") or line.startswith("FAIL ")
            or line.startswith("SUITE ")]


def write(path, text):
    data = text.replace("\r\n", "\n").replace("\r", "\n")
    if not data.endswith("\n"):
        data += "\n"
    data.encode("ascii")
    with open(path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(data)
    return hashlib.sha256(data.encode("ascii")).hexdigest()


def main():
    rc1, out1 = run_once()
    rc2, out2 = run_once()
    sha1 = hashlib.sha256("\n".join(criteria(out1)).encode(
        "ascii")).hexdigest()
    sha2 = hashlib.sha256("\n".join(criteria(out2)).encode(
        "ascii")).hexdigest()
    h1 = write(os.path.join(QA, "apimarket-buyerledger-R2128.log"), out1)
    h2 = write(os.path.join(QA, "apimarket-buyerledger-R2128-run2.log"),
               out2)
    print("rc=%s/%s" % (rc1, rc2))
    print("criteria_sha16=%s/%s identical=%r"
          % (sha1[:16].upper(), sha2[:16].upper(), sha1 == sha2))
    print("file_sha16=%s/%s" % (h1[:16], h2[:16]))
    return 0 if (rc1 == 0 and rc2 == 0 and sha1 == sha2) else 1


if __name__ == "__main__":
    sys.exit(main())