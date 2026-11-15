"""
R2779 note: this copy carries the R2778 launcher body unchanged apart
from its own three paths (evidence / stream / pidfile), so the R2778
evidence file stays untouched and that leg remains its own closed row.
Launch the R2778 reconcile battery detached on the committed tree.

Why this leg exists: R2778 shipped a new read-only verification tool
(tools/face_sweep.py), repaired tools/ugc_gate_report.py so a --check run can
no longer author the document it verifies, re-encoded three qa evidence files
to the canonical dialect and re-rendered two preview artifacts. Those are
product bytes outside src/, but the R2168 mixed-tree rule is about the tree
that will carry the next product byte, so a full battery is owed on it.

The R2767 leg is still RUNNING (pid 76936 at R2778 open, stream growing, no
closing BATTERY rc= row, no evidence file). This launcher therefore refuses to
touch that evidence path and writes its own three paths.

Contract, same as launch_battery_R2767.py:
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
inside the leg's reading window. The one unavoidable exception is this file
itself, which is a new src/os byte landed by the closeout of the same round;
it is declared in the state log so the adopting window attributes rather than
discovers it.
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
LOGS = os.path.join(REPO, "logs")
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2779.log")
STREAM = os.path.join(LOGS, "battery-R2779.stream")
PIDFILE = os.path.join(LOGS, "battery-R2779.pid")

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


def live_pid():
    """Return the pid in the pidfile when that process is still alive.

    os.kill(pid, 0) is NOT a liveness probe on Windows, so the probe asks
    the kernel through OpenProcess + WaitForSingleObject and needs no
    console child.
    """
    if not os.path.exists(PIDFILE):
        return 0
    try:
        with open(PIDFILE, "r", encoding="ascii") as fh:
            pid = int(fh.read().strip())
    except (ValueError, OSError):
        return 0
    if pid <= 0:
        return 0
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except OSError:
            return 0
        return pid
    import ctypes
    from ctypes import wintypes
    SYNCHRONIZE = 0x00100000
    WAIT_TIMEOUT = 0x00000102
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    handle = kernel32.OpenProcess(SYNCHRONIZE, False, wintypes.DWORD(pid))
    if not handle:
        return 0
    try:
        state = kernel32.WaitForSingleObject(handle, 0)
        return pid if state == WAIT_TIMEOUT else 0
    finally:
        kernel32.CloseHandle(handle)


def main():
    if not os.path.isdir(LOGS):
        os.makedirs(LOGS)
    if os.path.exists(EVIDENCE):
        print("E_LAUNCH_EVIDENCE_EXISTS %s" % EVIDENCE)
        return 2
    running = live_pid()
    if running:
        print("E_LAUNCH_PID_EXISTS pid=%d" % running)
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
