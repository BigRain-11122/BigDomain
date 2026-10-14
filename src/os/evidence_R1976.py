# -*- coding: utf-8 -*-
"""R1976 double-run evidence writer for the curation
boards_combined boundary-world persistence suite: runs the
suite twice as subprocesss, captures raw stdout bytes,
normalizes to LF-only, asserts byte-identity, and writes the
suite section of the evidence log in pure LF (R1969 dialect
law; R1975 CRLF-contamination lesson). ASCII-only source."""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_curation_combinedboundary.py")
EVID = os.path.join(ROOT, "qa",
                    "curation-combinedboundary-R1976.log")


def run_once():
    proc = subprocess.run([sys.executable, SUITE],
                          capture_output=True)
    return proc.returncode, proc.stdout


rc1, out1 = run_once()
rc2, out2 = run_once()
b1 = out1.replace(b"\r\n", b"\n")
b2 = out2.replace(b"\r\n", b"\n")
identical = b1 == b2
sha = hashlib.sha256(b1).hexdigest()[:16]

lines = []
lines.append("== suite double-run (subprocess byte capture, "
             "LF-normalized) ==")
lines.append("run1 rc=%d run2 rc=%d" % (rc1, rc2))
lines.append("byte-identical=%s lf-sha16=%s crlf1=%d crlf2=%d"
             % (str(identical).lower(), sha,
                out1.count(b"\r\n"), out2.count(b"\r\n")))
lines.append("run1 stdout bytes=%d (LF-normalized %d)"
             % (len(out1), len(b1)))
lines.append("run2 stdout bytes=%d (LF-normalized %d)"
             % (len(out2), len(b2)))
lines.append("")
lines.append("-- run1 stdout verbatim (LF) --")
lines.append(b1.decode("utf-8", errors="replace").rstrip("\n"))
lines.append("-- end run1 stdout --")
text = "\n".join(lines) + "\n"

with open(EVID, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(text)

print("DOUBLE-RUN %s rc=%d/%d identical=%s sha16=%s"
      % ("PASS" if (identical and rc1 == 0 and rc2 == 0)
         else "FAIL", rc1, rc2, str(identical).lower(), sha))
print("WROTE %s (%d bytes)" % (EVID, len(text.encode("utf-8"))))
sys.exit(0 if (identical and rc1 == 0 and rc2 == 0) else 1)
