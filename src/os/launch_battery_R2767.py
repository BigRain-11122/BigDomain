"""Launch the R2767 reconcile battery detached on the committed tree.

Why this leg exists: the R2757 leg closed RED at 675/676 and its one birth site
was repaired inside that window (src/os/export_R2431.py no longer demands
back["outs"][0] == latest, which R2751 D3 forbids on any wait round). The
residual red row was the criterion that still PINNED that retired literal -
src/os/test_export_R2431_health_verdict.py AC-EDSW5 - repaired at R2767 to
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
LOGS = os.path.join(REPO, "logs")
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2767.log")
STREAM = os.path.join(LOGS, "battery-R2767.stream")
PIDFILE = os.path.join(LOGS, "battery-R2767.pid")

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
