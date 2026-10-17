"""R2017 evidence driver: double-run the statsmonth
zero-registry boundary persist suite with subprocess byte
capture + LF normalization (R1880 dialect-prevention family;
R1999 evidence_R1999.py pattern), writing a single-dialect
utf-8 LF evidence log. Suite-only helper for the R2017 round.
"""

import hashlib
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
SUITE = os.path.join(
    ROOT, "src", "sandbox", "ledger",
    "test_showcase_statsmonthboundarypersist.py")
OUT = os.path.join(ROOT, "qa",
                   "showcase-statsmonthboundary-R2017.log")


def run_once(label):
    proc = subprocess.run(
        [sys.executable, SUITE],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    raw = proc.stdout.replace(b"\r\n", b"\n")
    return proc.returncode, raw


def main():
    rc1, out1 = run_once("run1")
    rc2, out2 = run_once("run2")
    identical = out1 == out2
    sha1 = hashlib.sha256(out1).hexdigest()[:16]
    lines = []
    lines.append("--- run 1 (subprocess byte capture, LF"
                 " normalized) rc=%d sha16=%s bytes=%d ---"
                 % (rc1, sha1, len(out1)))
    lines.append(out1.decode("utf-8", "replace").rstrip("\n"))
    lines.append("--- run 2 (subprocess byte capture, LF"
                 " normalized) rc=%d ---" % rc2)
    lines.append(out2.decode("utf-8", "replace").rstrip("\n"))
    lines.append("--- verdict ---")
    verdict_ok = rc1 == 0 and rc2 == 0 and identical
    lines.append("DOUBLE-RUN rc=%d/%d byte-identical=%s"
                 " sha16=%s" % (rc1, rc2, identical, sha1))
    lines.append("VERDICT %s" % ("PASS" if verdict_ok else "FAIL"))
    with open(OUT, "wb") as handle:
        handle.write(("\n".join(lines) + "\n")
                     .encode("utf-8"))
    print("VERDICT %s rc=%d/%d identical=%s sha16=%s"
          % ("PASS" if verdict_ok else "FAIL", rc1, rc2,
             identical, sha1))
    return 0 if verdict_ok else 2


if __name__ == "__main__":
    sys.exit(main())
