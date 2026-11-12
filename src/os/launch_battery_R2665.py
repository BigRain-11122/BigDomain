"""Launch the R2665 reconcile battery detached, after re-measuring the target.

The debt gate names reconcile-battery-R2661 first=yes at the pre-registered
653 suites / 4894 criteria on the committed tree, because R2661 moved product
src bytes (src/os/export_composed_landed_face.py), one suite and one registry
row, so the R2168 mixed-tree rule puts the full battery BEFORE any further
product byte.

R2663 launched a leg that went RED on reconcile-daily-census because two R2661
evidence logs were pwsh-capture; that birth site was repaired and committed
alone as 6542ad6c and the census re-reads DRIFT-CLEAN flags=0. R2663 then
committed the repair WHILE its leg was still running, so that leg can never be
a verdict on this tree (the one-tree law) and is adopted as the red evidence
only. This launcher starts the leg that may be judged, on the committed tree.

It refuses to fire when the registry has moved from that target, when any name
or path is not unique, or when the evidence file already exists, so a leg can
never be claimed against a tree it did not run on. The stream and the pid go
to SEPARATE files under logs/, and the evidence file is written by the shipped
single writer alone - never by a shell redirection into qa/.
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
LOGS = os.path.join(REPO, "logs")
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2665.log")
STREAM = os.path.join(LOGS, "battery-R2665.stream")
PIDFILE = os.path.join(LOGS, "battery-R2665.pid")

TARGET_SUITES = 653
TARGET_CRITERIA = 4894


def measure():
    sys.path.insert(0, os.path.join(os.path.dirname(BASE), "sandbox"))
    import reconcile_all
    suites = reconcile_all.SUITES
    return (len(suites),
            sum(row[2] for row in suites),
            len({row[0] for row in suites}),
            len({row[1] for row in suites}))


def main():
    if not os.path.isdir(LOGS):
        os.makedirs(LOGS)
    if os.path.exists(EVIDENCE):
        print("E_LAUNCH_EVIDENCE_EXISTS %s" % EVIDENCE)
        return 2
    suites, criteria, names, paths = measure()
    if suites != TARGET_SUITES or criteria != TARGET_CRITERIA:
        print("E_LAUNCH_TARGET_MOVED suites=%d criteria=%d expected=%d/%d"
              % (suites, criteria, TARGET_SUITES, TARGET_CRITERIA))
        return 3
    if names != suites or paths != suites:
        print("E_LAUNCH_NOT_UNIQUE names=%d paths=%d suites=%d"
              % (names, paths, suites))
        return 4
    print("TARGET-MEASURED suites=%d criteria=%d names=%d paths=%d"
          % (suites, criteria, names, paths))
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
