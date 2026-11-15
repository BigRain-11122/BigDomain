"""R2163 battery launcher: start reconcile_all detached with its own
Tee evidence path so the shell call returns immediately."""

import os
import subprocess
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_TOOLS = os.path.join(BASE, "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
import leg_interlock  # noqa: E402
RUNNER = os.path.join(BASE, "src", "sandbox", "reconcile_all.py")
OUT = os.path.join(BASE, "qa", "reconcile-all-R2163.log")


def main():
    rc, interlock_line = leg_interlock.guard(BASE)
    print(interlock_line)
    if rc != 0:
        return 2
    flags = 0
    if os.name == "nt":
        flags = 0x00000008 | 0x00000200  # DETACHED | NEW_PROCESS_GROUP
    with open(os.path.join(BASE, "logs", "battery-R2163.out"),
              "wb") as so:
        proc = subprocess.Popen(
            [sys.executable, RUNNER, OUT],
            cwd=os.path.join(BASE, "src", "sandbox"),
            stdout=so, stderr=subprocess.STDOUT, creationflags=flags)
    print("PID=%d log=%s" % (proc.pid, OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())