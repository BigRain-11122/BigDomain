"""R2478 battery launcher: start battery_stream detached so the shell call
returns immediately and the evidence log keeps a single utf-8 LF writer
(the R2211/R2268/R2348 filtering-pipe trap). This window owes the full
reconcile battery for reconcile-battery-R2477 (566 suites / 4372 criteria)
on the committed tree before any further product byte."""

import os
import subprocess
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STREAM = os.path.join(BASE, "src", "os", "battery_stream.py")
EVIDENCE = os.path.join(BASE, "qa", "reconcile-all-R2478.log")


def main():
    suffix = sys.argv[1] if len(sys.argv) > 1 else ""
    evidence = EVIDENCE
    if suffix:
        evidence = evidence.replace(".log", "-%s.log" % suffix)
    flags = 0
    if os.name == "nt":
        flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | NEW_PROCESS_GROUP
    out = os.path.join(BASE, "logs", "battery-R2478%s-stdout.log" % suffix)
    err = os.path.join(BASE, "logs", "battery-R2478%s-stderr.log" % suffix)
    with open(out, "wb") as so, open(err, "wb") as se:
        proc = subprocess.Popen(
            [sys.executable, "-u", STREAM, "--evidence", evidence],
            cwd=BASE, stdout=so, stderr=se,
            creationflags=flags)
    print("PID=%d stdout=%s evidence=%s" % (proc.pid, out, evidence))
    return 0


if __name__ == "__main__":
    sys.exit(main())