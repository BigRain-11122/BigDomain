"""R2554 battery launcher: detached, unfiltered, single-writer evidence.

The stream and the pid are written to DIFFERENT paths (the R2532 collision), and
no shell redirection ever touches qa/ (the ps-utf16 trap).
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))

ROUND = sys.argv[1] if len(sys.argv) > 1 else "R2554"
STREAM = os.path.join(REPO, "logs", "battery-%s.stream.log" % (ROUND,))
PIDFILE = os.path.join(REPO, "logs", "battery-%s.pid" % (ROUND,))
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-%s.log" % (ROUND,))


def main():
    handle = open(STREAM, "wb")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "battery_stream.py"),
         "--evidence", EVIDENCE],
        cwd=REPO, stdin=subprocess.DEVNULL, stdout=handle,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW)
    with open(PIDFILE, "w", encoding="ascii") as pid:
        pid.write(str(proc.pid))
    print("LAUNCHED pid=%d evidence=%s" % (proc.pid, EVIDENCE))
    return 0


if __name__ == "__main__":
    sys.exit(main())