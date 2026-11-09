"""Launch src/os/capture_R2590.py detached, stream in logs/ (never in qa/).

The 5-minute shell silence limit killed an inline run of the capture, so the
capture is started as its own process with its stdout in logs/ and its pid in a
separate file. qa/ is written by the capture writer alone.
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
SCRIPT = os.path.join(BASE, "capture_R2590.py")
STREAM = os.path.join(REPO, "logs", "capture-R2590.stdout.log")
PIDFILE = os.path.join(REPO, "logs", "capture-R2590.pid")

DETACHED = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP


def main():
    if not os.path.isdir(os.path.join(REPO, "logs")):
        os.makedirs(os.path.join(REPO, "logs"))
    handle = open(STREAM, "wb")
    proc = subprocess.Popen([sys.executable, SCRIPT], cwd=REPO,
                            stdout=handle, stderr=subprocess.STDOUT,
                            creationflags=DETACHED, close_fds=True)
    with open(PIDFILE, "w", encoding="utf-8", newline="\n") as out:
        out.write("%d\n" % proc.pid)
    print("launched pid=%d stream=%s" % (proc.pid, STREAM))
    return 0


if __name__ == "__main__":
    sys.exit(main())