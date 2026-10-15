"""Evidence driver for R1997 civic month-window suite: runs the
suite twice as subprocesses, asserts byte-identical stdout, and
writes the evidence file itself in utf-8 LF (python single-writer
dialect; the R1924 ps-utf16 trap is structurally avoided)."""

import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_civic_monthwindow.py")
OUT = os.path.join(ROOT, "qa", "civic-monthwindow-R1997.log")


def run_once():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([sys.executable, SUITE], env=env,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=300)
    return proc.returncode, proc.stdout


def main():
    rc1, out1 = run_once()
    rc2, out2 = run_once()
    identical = out1 == out2
    sha = hashlib.sha256(out1).hexdigest()
    lines = []
    lines.append("# R1997 civic behavior distribution month-window"
                 " suite evidence (double run)")
    lines.append("# criteria AC-CVM1..AC-CVM7 pre-registered in"
                 " state/queue/explore.md before the code existed")
    lines.append("# honest erratum: AC-CVM5 first draft asserted a"
                 " plain per-column sum across the month partition;"
                 " the red run exposed participants as a"
                 " COUNT(DISTINCT) union-law dimension, the"
                 " assertion was corrected to additive sum law for"
                 " events/total_points + set-union law for"
                 " participants same round (product behavior was"
                 " already right; R1996 AC-CJM6 precedent)")
    lines.append("run1 exit=%d run2 exit=%d" % (rc1, rc2))
    lines.append("stdout byte-identical=%s" % identical)
    lines.append("stdout sha256=%s bytes=%d" % (sha, len(out1)))
    lines.append("VERDICT %s" % ("PASS" if (
        rc1 == 0 and rc2 == 0 and identical) else "FAIL"))
    lines.append("----- run1 stdout -----")
    lines.extend(out1.decode("utf-8").splitlines())
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote %s identical=%s sha256=%s rc=%d/%d" % (
        OUT, identical, sha, rc1, rc2))
    return 0 if (rc1 == 0 and rc2 == 0 and identical) else 1


if __name__ == "__main__":
    sys.exit(main())
