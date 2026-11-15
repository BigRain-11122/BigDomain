"""Launch the R2762 reconcile battery detached on the committed tree.

Why this leg exists: the R2757 leg closed RED at 675/676 and its one birth site
was repaired inside that window (src/os/export_R2431.py no longer demands
back["outs"][0] == latest, which R2751 D3 forbids on any wait round). The
residual red row was the criterion that still PINNED that retired literal -
src/os/test_export_R2431_health_verdict.py AC-EDSW5 - repaired at R2762 to
accept the successor literal back["outs"] == written_outs while still refusing
a total drop of the term. That repair moved product src, so the R2168
mixed-tree rule is owed again: no full battery has run on the tree that will
carry the next product byte.

Contract, same as launch_battery_R2757.py:
  * the target is re-measured BY IMPORT on this committed tree before the
    launch, and the leg is refused when the registry moved or when any
    name or path is not unique;
  * the evidence file must not exist and no live leg may be running, so a
    leg can never be claimed against a tree it did not run on and a red
    leg is never relaunched over;
  * the stream and the pid live in SEPARATE files under logs/, and the
    evidence file is written by the shipped single writer alone - never
    by a shell redirection into qa/.

ORDER MATTERS (R2752 lesson): the export refresh and every state and board
write were committed BEFORE this launcher runs, so no export byte moves
inside the leg's reading window.
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
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2762.log")
STREAM = os.path.join(LOGS, "battery-R2762.stream")
PIDFILE = os.path.join(LOGS, "battery-R2762.pid")

TARGET_SUITES = 676
TARGET_CRITERIA = 5032


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
