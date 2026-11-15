"""Launch the R2723 reconcile battery detached, after re-measuring the target.

The debt gate names reconcile-battery-R2723 first=yes at the pre-registered
672 suites / 5008 criteria on the committed tree, because R2723 moved product
src bytes (src/os/evidence_capture_precedence_derived.py plus its six-criteria
suite) and one registry row from 671 suites / 5002 criteria, so the R2168
mixed-tree rule puts the FULL battery BEFORE the next product byte.

The battery at this size runs about an hour, which is longer than one window
can hold inside a single shell call, so this launcher starts the leg detached
and the NEXT window adopts it by its evidence path. It refuses to fire when the
registry has moved from the target, when any name or path is not unique, when
the evidence file already exists, or when a live leg is already running, so a
leg can never be claimed against a tree it did not run on. The stream and the
pid go to SEPARATE files under logs/, and the evidence file is written by the
shipped single writer alone - never by a shell redirection into qa/.
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
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2723.log")
STREAM = os.path.join(LOGS, "battery-R2723.stream")
PIDFILE = os.path.join(LOGS, "battery-R2723.pid")

TARGET_SUITES = 672
TARGET_CRITERIA = 5008


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

