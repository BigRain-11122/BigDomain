"""Detached battery launcher for R2560: evidence and stream in separate files."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVIDENCE = os.path.join(ROOT, "qa", "reconcile-all-R2560.log")
STREAM = os.path.join(ROOT, "logs", "battery-R2560.stream.log")
PID = os.path.join(ROOT, "logs", "battery-R2560.pid")


def main():
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