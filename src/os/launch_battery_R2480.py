"""R2480 battery launcher: start battery_stream detached so the shell call
returns immediately and the evidence log keeps a single utf-8 LF writer
(the R2211/R2268/R2348 filtering-pipe trap). This window owes the full
reconcile battery for reconcile-battery-R2479 (567 suites / 4378 criteria,
pre-registered at R2479) on the committed tree before any further product
byte."""

import os
import subprocess
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_TOOLS = os.path.join(BASE, "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
import leg_interlock  # noqa: E402
STREAM = os.path.join(BASE, "src", "os", "battery_stream.py")
EVIDENCE = os.path.join(BASE, "qa", "reconcile-all-R2480.log")


def main():
    rc, interlock_line = leg_interlock.guard(BASE)
    print(interlock_line)
    if rc != 0:
        return 2
    suffix = sys.argv[1] if len(sys.argv) > 1 else ""
    evidence = EVIDENCE
    if suffix:
        evidence = evidence.replace(".log", "-%s.log" % suffix)
    flags = 0
    if os.name == "nt":
        flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | NEW_PROCESS_GROUP
    out = os.path.join(BASE, "logs", "battery-R2480%s-stdout.log" % suffix)
    err = os.path.join(BASE, "logs", "battery-R2480%s-stderr.log" % suffix)
    with open(out, "wb") as so, open(err, "wb") as se:
        proc = subprocess.Popen(
            [sys.executable, "-u", STREAM, "--evidence", evidence],
            cwd=BASE, stdout=so, stderr=se,
            creationflags=flags)
    print("PID=%d stdout=%s evidence=%s" % (proc.pid, out, evidence))
    return 0


if __name__ == "__main__":
    sys.exit(main())