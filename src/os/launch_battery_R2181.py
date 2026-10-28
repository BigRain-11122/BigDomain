"""R2181 battery launcher: start battery_stream detached so the shell
call returns immediately and the evidence log has a single writer
(utf-8 LF). This pays the R2180 first-item debt (full battery plus suite
matrix regeneration)."""

import os
import subprocess
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STREAM = os.path.join(BASE, "src", "os", "battery_stream.py")
EVIDENCE = os.path.join(BASE, "qa", "reconcile-all-R2181.log")


def main():
    flags = 0
    if os.name == "nt":
        flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | NEW_PROCESS_GROUP
    out = os.path.join(BASE, "logs", "battery-R2181.out")
    with open(out, "wb") as so:
        proc = subprocess.Popen(
            [sys.executable, "-u", STREAM, "--evidence", EVIDENCE],
            cwd=BASE, stdout=so, stderr=subprocess.STDOUT,
            creationflags=flags)
    print("PID=%d log=%s evidence=%s" % (proc.pid, out, EVIDENCE))
    return 0


if __name__ == "__main__":
    sys.exit(main())