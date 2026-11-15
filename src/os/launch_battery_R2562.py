"""Detached battery launcher for R2562: evidence and stream in separate files."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_TOOLS = os.path.join(ROOT, "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
import leg_interlock  # noqa: E402
EVIDENCE = os.path.join(ROOT, "qa", "reconcile-all-R2562.log")
STREAM = os.path.join(ROOT, "logs", "battery-R2562.stream.log")
PID = os.path.join(ROOT, "logs", "battery-R2562.pid")


def main():
    rc, interlock_line = leg_interlock.guard(ROOT)
    print(interlock_line)
    if rc != 0:
        return 2
    cmd = [sys.executable, os.path.join(ROOT, "src", "os", "battery_stream.py"),
           "--evidence", EVIDENCE]
    flags = 0
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        flags = subprocess.CREATE_NO_WINDOW
    with open(STREAM, "wb") as out:
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT,
                                creationflags=flags)
    with open(PID, "w", encoding="ascii", newline="\n") as fh:
        fh.write(str(proc.pid) + "\n")
    print("launched", proc.pid, "evidence", EVIDENCE, "stream", STREAM)


if __name__ == "__main__":
    main()