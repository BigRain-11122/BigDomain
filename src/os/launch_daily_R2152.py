"""R2152 daily launcher: start reconcile_daily detached so the shell call
returns immediately (the runner buffers child output, so an in-line call
trips the five-minute no-output rule). ASCII source, zero network.
"""

import os
import subprocess
import sys

BASE = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", ".."))
RUNNER = os.path.join(BASE, "src", "sandbox", "reconcile_daily.py")
OUT = os.path.join(BASE, "logs", "daily-R2152.out")


def main():
    flags = 0
    if os.name == "nt":
        flags = 0x00000008 | 0x00000200  # DETACHED | NEW_PROCESS_GROUP
    with open(OUT, "wb") as sink:
        proc = subprocess.Popen([sys.executable, RUNNER],
                                cwd=os.path.join(BASE, "src", "sandbox"),
                                stdout=sink, stderr=subprocess.STDOUT,
                                creationflags=flags)
    print("PID=%d sink=%s" % (proc.pid, OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())