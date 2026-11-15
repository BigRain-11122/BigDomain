"""Launch the R2715b reconcile RETRY leg detached, after re-measuring the target.

Why a second leg exists at all: the R2715 leg ran to completion and landed a
RED evidence file (qa/reconcile-all-R2715.log, 1198928B, 6 suites / 7 criteria
red) whose every failure was the same birth-site defect this window created -
the R2715 ledger line carried the narrative date prefix, so ledger_lines
parsed it as a round and reported rounds_without_ledger=[2715]. The line was
repaired at that birth site (it now reads 'R2715 tokens: local=...'), the
audit reads rounds_without_ledger=[] and the six red suites were re-run
INDIVIDUALLY and read green (8/8, 8/8, 8/8, 6/6, 6/6, 8/8).

A red leg is evidence and is never deleted or rewritten, and a mixed tree can
never be called green, so the full battery is owed once more on the committed
tree that carries the repair. This launcher therefore writes a DIFFERENT
evidence path and refuses when that path already exists, when the registry has
moved from the target, when any name or path is not unique, or when a live leg
is already running.

The battery at this size runs about half an hour, longer than one window can
hold inside a single shell call, so the leg starts detached and is adopted by
its evidence path. The stream and the pid go to SEPARATE files under logs/,
and the evidence file is written by the shipped single writer alone.
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
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2715b.log")
STREAM = os.path.join(LOGS, "battery-R2715b.stream")
PIDFILE = os.path.join(LOGS, "battery-R2715b.pid")

TARGET_SUITES = 668
TARGET_CRITERIA = 4984


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
