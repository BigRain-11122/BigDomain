"""Launch the R2705 reconcile battery detached, after re-measuring the target.

The debt gate names reconcile-battery-R2704 first=yes at the pre-registered
664 suites / 4960 criteria on the committed tree, because R2704 moved product
src bytes (the new canonical guard face plus its six-criteria suite), repaired
two int() birth sites, and added one registry row, one matrix row and one
queue row, so the R2168 mixed-tree rule puts the FULL battery BEFORE any
further product byte.

The battery at this size runs about an hour, which is longer than one window
can hold inside a single shell call, so this launcher starts the leg detached
and the NEXT window adopts it by its evidence path. It refuses to fire when
the registry has moved from the target, when any name or path is not unique,
or when the evidence file already exists, so a leg can never be claimed
against a tree it did not run on. The stream and the pid go to SEPARATE files
under logs/, and the evidence file is written by the shipped single writer
alone - never by a shell redirection into qa/.
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
LOGS = os.path.join(REPO, "logs")
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2705.log")
STREAM = os.path.join(LOGS, "battery-R2705.stream")
PIDFILE = os.path.join(LOGS, "battery-R2705.pid")

TARGET_SUITES = 664
TARGET_CRITERIA = 4960


def measure():
    sys.path.insert(0, os.path.join(REPO, "src", "sandbox"))
    import reconcile_all
    suites = reconcile_all.SUITES
    return (len(suites),
            sum(row[2] for row in suites),
            len({row[0] for row in suites}),
            len({row[1] for row in suites}))


def live_pid():
    """Return the pid recorded in the pidfile when that process is still alive.

    os.kill(pid, 0) is NOT a liveness probe on Windows - it does not raise for
    a live pid, so an earlier version of this guard silently failed and let a
    second leg fire against the same evidence path. The probe now asks the
    kernel through OpenProcess + WaitForSingleObject, which needs no console
    child and no signal.
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
