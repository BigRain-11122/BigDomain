"""Launch the R2739 reconcile battery detached, after re-measuring the target.

Why a successor leg instead of adopting the R2737 one: the R2737 leg CLOSED
RED on its own bytes (qa/reconcile-all-R2737.log, 1249289B, 671 of 675 suite
rows PASS, criteria 5000 of the expected 5026, tail RUNNER FAIL + BATTERY
rc=1 3963.7s) and its four red rows are exactly the four whose birth sites
R2738 repaired MID-LEG (os-state-io, os-status-export-writer-dialect-wire,
os-queue-floor-export-face, os-export-consistency-queue-face). R2738 re-ran
those four GREEN on the repaired live tree (8/8, 6/6, 6/6, 15/15), but a red
row repaired mid-leg is not evidence about the repaired tree, and R2737's own
precedent is that a red leg is NOT adopted green. R2738 also moved a product
src byte (src/os/state_io.py), so the R2168 mixed-tree rule puts a FULL
battery on the committed tree BEFORE the next product byte.

Same contract as launch_battery_R2733.py: the target is re-measured BY IMPORT
on this committed tree before the launch, the leg is refused when the registry
moved, when any name or path is not unique, when the evidence file already
exists, or when a live leg is still running, so a leg can never be claimed
against a tree it did not run on. The stream and the pid live in SEPARATE
files under logs/, and the evidence file is written by the shipped single
writer alone - never by a shell redirection into qa/.
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))

_TOOLS = os.path.join(REPO, "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
import leg_interlock  # noqa: E402
LOGS = os.path.join(REPO, "logs")
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2739.log")
STREAM = os.path.join(LOGS, "battery-R2739.stream")
PIDFILE = os.path.join(LOGS, "battery-R2739.pid")

TARGET_SUITES = 675
TARGET_CRITERIA = 5026


def measure():
    sys.path.insert(0, os.path.join(REPO, "src", "sandbox"))
    import reconcile_all
    suites = reconcile_all.SUITES
    return (len(suites),
            sum(row[2] for row in suites),
            len({row[0] for row in suites}),
            len({row[1] for row in suites}))


def main():
    rc, interlock_line = leg_interlock.guard(REPO)
    print(interlock_line)
    if rc != 0:
        return 2
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
