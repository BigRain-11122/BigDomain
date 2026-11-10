"""Launch the R2631 reconcile battery detached, after re-measuring the target.

The debt gate names reconcile-battery-R2630 first=yes at a pre-registered
644 suites / 4840 criteria on the committed tree, because R2630 moved product
src bytes (src/os/suite_matrix_reconcile.py) and one registry row, so the
R2168 mixed-tree rule puts the full battery BEFORE any further product byte.

This launcher refuses to fire when the registry has moved from that target,
or when the evidence file already exists, so a leg can never be claimed
against a tree it did not run on. The stream and the pid go to SEPARATE
files under logs/, and the evidence file is written by the shipped single
writer alone - never by a shell redirection into qa/.
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
LOGS = os.path.join(REPO, "logs")
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2631.log")
STREAM = os.path.join(LOGS, "battery-R2631.stream")
PIDFILE = os.path.join(LOGS, "battery-R2631.pid")

TARGET_SUITES = 644
TARGET_CRITERIA = 4840


def measure():
    sys.path.insert(0, os.path.join(os.path.dirname(BASE), "sandbox"))
    import reconcile_all
    suites = reconcile_all.SUITES
    return len(suites), sum(row[2] for row in suites)


def main():
    if not os.path.isdir(LOGS):
        os.makedirs(LOGS)
    if os.path.exists(EVIDENCE):
        print("E_LAUNCH_EVIDENCE_EXISTS %s" % EVIDENCE)
        return 2
    suites, criteria = measure()
    if suites != TARGET_SUITES or criteria != TARGET_CRITERIA:
        print("E_LAUNCH_TARGET_MOVED suites=%d criteria=%d expected=%d/%d"
              % (suites, criteria, TARGET_SUITES, TARGET_CRITERIA))
        return 3
    print("TARGET-MEASURED suites=%d criteria=%d" % (suites, criteria))
    stream = open(STREAM, "wb")
    flags = 0
    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        flags |= subprocess.CREATE_NEW_PROCESS_GROUP
    if hasattr(subprocess, "DETACHED_PROCESS"):
        flags |= subprocess.DETACHED_PROCESS
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        flags |= subprocess.CREATE_NO_WINDOW
    proc = subprocess.Popen(
        [sys.executable,
         os.path.join(BASE, "battery_stream.py"),
         "--evidence", EVIDENCE],
        stdin=subprocess.DEVNULL,
        stdout=stream,
        stderr=subprocess.STDOUT,
        cwd=REPO,
        creationflags=flags,
        close_fds=True,
    )
    with open(PIDFILE, "w", encoding="ascii") as fh:
        fh.write("%d\n" % proc.pid)
    print("LAUNCHED pid=%d evidence=%s stream=%s"
          % (proc.pid, EVIDENCE, STREAM))
    return 0


if __name__ == "__main__":
    sys.exit(main())
