"""Open the whole sandbox with one call and hand the person the hub URL.

start_all.py already proves nine faces and prints the measured hub URL, but a
person has to run it in a console, read a JSON line, and paste a port. This
module closes the last step for a double-click launcher: it starts start_all.py
as a child, waits for the report file the child writes, and opens the browser
at the URL the child measured - never at a built-in guess.

Honesty law: the browser opens only after the report file says ok=true with a
hub_url. A launcher that opened a guessed port would be the same lie as a page
that paints a dead port green.

R3333: two readings were added because a proof that is copied by hand is not a
proof, and a teardown nobody measures is a hope.

  --qa-log NAME   the disposition this run prints is written through
                  tools/qa_log.py (the one shipped evidence writer) instead of
                  being pasted into qa/ by a person afterwards.
  descendants=    the process subtree this run started is read from a Toolhelp
                  snapshot BEFORE the stop file is written and again after the
                  child exits, so "nothing is left behind" is a number and, when
                  a process survives, a pid:exe line. A survivor makes the
                  verdict FAIL. "Gone" is read over a bounded settle window
                  (--settle, default 3s) because a console host outlives its
                  client for a moment - measured, not assumed. A console host
                  (conhost.exe) is Windows-owned: it is counted as
                  console_hosts= and never gated. The boundary is
                  stated in the output: a process
                  from an EARLIER run is not in this subtree and is not seen -
                  python_now=N is printed as context, never as a gate.

Usage:
  python src/sandbox/open_sandbox.py             # serve and open the browser
  python src/sandbox/open_sandbox.py --no-browser
  python src/sandbox/open_sandbox.py --check     # prove, stop, exit 0/2
  python src/sandbox/open_sandbox.py --check --qa-log sandbox-onclick-R1.log
Exit: 0 = hub came up and the subtree this run started is gone; 2 otherwise.
"""

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
import webbrowser
from ctypes import wintypes

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOGS = os.path.join(ROOT, "logs")
QA = os.path.join(ROOT, "qa")
QA_LOG = os.path.join(ROOT, "tools", "qa_log.py")
START_ALL = os.path.join(HERE, "start_all.py")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

TH32CS_SNAPPROCESS = 0x00000002


class _PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


def process_table():
    """{pid: (parent_pid, exe)} for every live process; {} when refused.

    Toolhelp32 is read directly so the proof costs no child process and opens
    no console - the same discipline the rest of this launcher follows.
    """
    if not hasattr(ctypes, "WinDLL"):
        return {}
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if not snap or snap == ctypes.c_void_p(-1).value:
            return {}
        table = {}
        try:
            entry = _PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(_PROCESSENTRY32W)
            more = kernel32.Process32FirstW(ctypes.c_void_p(snap),
                                            ctypes.byref(entry))
            while more:
                table[entry.th32ProcessID] = (entry.th32ParentProcessID,
                                              entry.szExeFile)
                more = kernel32.Process32NextW(ctypes.c_void_p(snap),
                                               ctypes.byref(entry))
        finally:
            kernel32.CloseHandle(ctypes.c_void_p(snap))
        return table
    except OSError:
        return {}


def descendants(root_pid, table=None):
    """Every pid reachable from root_pid through recorded parent links."""
    table = process_table() if table is None else table
    children = {}
    for pid, (ppid, _exe) in table.items():
        children.setdefault(ppid, []).append(pid)
    seen = []
    stack = list(children.get(root_pid, []))
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.append(pid)
        stack.extend(children.get(pid, []))
    return seen


def python_count(table):
    """Live python interpreters on this machine - context only, never a gate."""
    return sum(1 for _pid, (_ppid, exe) in table.items()
               if exe.lower().startswith("python"))


def load_qa_log():
    """Import the shipped evidence writer by path, so there is one writer."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("bd_qa_log", QA_LOG)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_report(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="start the sandbox and open the measured hub URL")
    parser.add_argument("--check", action="store_true",
                        help="start, wait for the hub, tear down, print a "
                             "verdict and exit 0 on proof / 2 otherwise")
    parser.add_argument("--no-browser", action="store_true",
                        help="do not open a browser (used by --check)")
    parser.add_argument("--timeout", type=float, default=90.0,
                        help="seconds to wait for the hub report")
    parser.add_argument("--qa-log", default=None, metavar="NAME",
                        help="write this run's disposition through "
                             "tools/qa_log.py into qa/NAME (suffix .log)")
    parser.add_argument("--qa-dir", default=None, metavar="DIR",
                        help="evidence directory (default qa/; suites point "
                             "this at a private tree)")
    parser.add_argument("--hold-secs", type=float, default=0.0,
                        help="TEST SEAM: also start a child that sleeps this "
                             "long instead of honouring the stop file, so the "
                             "leftover reading can be proved to bite")
    parser.add_argument("--settle", type=float, default=3.0,
                        help="seconds to let the subtree exit before a survivor "
                             "is called a leftover")
    args = parser.parse_args(argv)

    lines = []

    def say(text):
        lines.append(text)
        print(text)

    os.makedirs(LOGS, exist_ok=True)
    report_path = os.path.join(LOGS, "sandbox-start.json")
    stop_path = os.path.join(LOGS, "sandbox-stop.txt")
    child_log = os.path.join(LOGS, "sandbox-start.log")
    for path in (report_path, stop_path):
        try:
            os.remove(path)
        except OSError:
            pass

    hold = None
    if args.hold_secs > 0:
        hold = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(%r)" % args.hold_secs],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
        say("hold seam: pid=%d sleeps %.1fs instead of honouring the stop file"
            % (hold.pid, args.hold_secs))

    cmd = [sys.executable, START_ALL, "--report-json", report_path,
           "--stop-file", stop_path]
    with open(child_log, "wb") as sink:
        child = subprocess.Popen(cmd, cwd=ROOT, stdin=subprocess.DEVNULL,
                                 stdout=sink, stderr=subprocess.STDOUT,
                                 creationflags=NO_WINDOW)

    deadline = time.time() + args.timeout
    report = None
    while time.time() < deadline:
        if child.poll() is not None:
            break
        report = read_report(report_path)
        if report and report.get("hub_url") and report.get("ok"):
            break
        time.sleep(0.4)

    ok = bool(report and report.get("hub_url") and report.get("ok"))
    hub_url = (report or {}).get("hub_url") or ""
    faces = (report or {}).get("live") or {}
    live = sum(1 for v in faces.values() if v)

    if ok:
        say("sandbox up: hub=%s faces=%d/%d" % (hub_url, live, len(faces) or 8))
        if not args.no_browser and not args.check:
            webbrowser.open(hub_url)
    else:
        errors = (report or {}).get("errors") or []
        say("sandbox did not come up: %s" % ("; ".join(errors) or "no report"))

    # Read the subtree this run started while it is still alive: a pid that was
    # never observed cannot be proved gone. Taken before the stop file is
    # written, so faces still running are part of the reading. A console host
    # (conhost.exe) is owned by Windows, not by this sandbox, so it is counted
    # separately and never gated - measured at R3333: a clean run flagged one
    # conhost.exe as a leftover, and the same run without it read 14/14.
    now = process_table()
    started = [(pid, now[pid][1]) for pid in descendants(os.getpid(), now)
               if not now[pid][1].lower().startswith("conhost")]
    hosts_seen = sum(1 for pid in descendants(os.getpid(), now)
                     if now[pid][1].lower().startswith("conhost"))

    try:
        if args.check:
            time.sleep(2.0)
            with open(stop_path, "w", encoding="ascii") as fh:
                fh.write("stop\n")
        else:
            child.wait()
    except KeyboardInterrupt:
        with open(stop_path, "w", encoding="ascii") as fh:
            fh.write("stop\n")
    finally:
        if args.check or child.poll() is not None:
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                child.kill()

    # A console host outlives its client for a moment, so "gone" is read over a
    # bounded settle window instead of one snapshot: a face that really leaked
    # stays for the whole window, a console host does not. Measured at R3333 -
    # the first version flagged one conhost.exe as a leftover on a clean run.
    settle_end = time.time() + args.settle
    table = process_table()
    left = [pid for pid, _exe in started if pid in table] if table else []
    while left and time.time() < settle_end:
        time.sleep(0.25)
        table = process_table()
        left = [pid for pid, _exe in started if pid in table] if table else []
    settled = round(args.settle - max(0.0, settle_end - time.time()), 2)
    if table:
        named = ", ".join("%d:%s" % (pid, table[pid][1]) for pid in left) or "none"
        say("descendants=%d gone=%d/%d leftovers=%s console_hosts=%d"
            " python_now=%d settled=%.2fs"
            % (len(started), len(started) - len(left), len(started), named,
               hosts_seen, python_count(table), settled))
        clean = not left
        reaped = []
        for pid in left:
            try:
                os.kill(pid, 9)
                reaped.append(pid)
            except OSError:
                pass
        if reaped:
            after = process_table()
            still = [pid for pid in reaped if pid in after]
            say("reaped=%d still=%s"
                % (len(reaped), ", ".join(str(p) for p in still) or "none"))
            clean = clean and not still
    else:
        # A refused snapshot is named rather than read as a clean teardown.
        say("descendants=unread gone=unread leftovers=unread"
            " python_now=unread tree=snapshot-refused")
        clean = False

    verdict = ok and clean
    say("VERDICT %s hub=%s faces=%d/%d clean=%s"
        % ("PASS" if verdict else "FAIL", hub_url or "-", live,
           len(faces) or 8, clean))
    if hold is not None and hold.poll() is None:
        hold.kill()

    if args.qa_log:
        target = args.qa_dir or QA
        try:
            os.makedirs(target, exist_ok=True)
            load_qa_log().do_write(args.qa_log, ("\n".join(lines) + "\n").encode("utf-8"),
                                  directory=target)
        except (OSError, ValueError, ImportError, AttributeError) as exc:
            say("QA-LOG REFUSED name=%s reason=%s" % (args.qa_log, exc))
            verdict = False

    return 0 if verdict else 2


if __name__ == "__main__":
    sys.exit(main())
