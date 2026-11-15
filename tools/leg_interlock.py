"""Cross-leg interlock for reconcile batteries: refuse a launch while ANY leg is live.

WHY THIS EXISTS (measured at R2771, not hypothesised):
src/os/launch_battery_R2767.py and src/os/launch_battery_R2768.py both carry a
live_pid() that reads ONLY its own logs/battery-R<round>.pid. A second launcher
therefore sees its own pidfile absent, concludes the machine is clear, and
starts a SECOND full sweep of the same 676 suites / 5032 criteria. At R2771 open
that had actually happened: pid 76936 (R2767) and pid 53980 (R2768) were BOTH
alive, each replaying the identical registry, roughly doubling the wall time and
handing the adopting window two divergent FAIL sets for one tree. The guard
belongs above the per-round pidfile, so it lives here and is callable by any
future launcher: guard() answers "may I start a leg on this machine right now".

WHAT IT DOES NOT DO: no write path, no clock, no network, no shell, no state
surgery. It reads pidfiles, asks the kernel whether those pids are alive, and
answers. Evidence lives in qa/leg-interlock-R2771.log.

Criteria are pre-registered as AC-LINT1..AC-LINT6 and are proved in a PRIVATE
world by --check, so the live machine state can never be mistaken for a pass.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

PREFIX = "battery-"
SUFFIX = ".pid"

NETWORK_IMPORTS = ("socket", "requests", "http.client", "urllib.request", "urllib3")


def probe_pid(pid: int) -> tuple[bool, float]:
    """Return (alive, creation_epoch).

    os.kill(pid, 0) is NOT a liveness probe on Windows, so the Windows path asks
    the kernel through OpenProcess + WaitForSingleObject and needs no console
    child (the R2746/R2767 contract, reused rather than re-invented). The second
    element is the kernel's process creation time, because a live pid is NOT
    proof that MY leg is alive: Windows reuses pids, and this census measured
    exactly that on battery-R2520-retry.pid, whose pid answered alive hours after
    that leg had ended.
    """
    if pid <= 0:
        return False, 0.0
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except OSError:
            return False, 0.0
        try:
            with open("/proc/%d/stat" % pid, "rb") as fh:
                fields = fh.read().split()
            start_ticks = float(fields[21])
            btime = float(open("/proc/stat").read().split("btime")[1].split()[0])
            return True, btime + start_ticks / 100.0
        except (OSError, IndexError, ValueError):
            return True, 0.0
    import ctypes
    from ctypes import wintypes

    SYNCHRONIZE = 0x00100000
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    WAIT_TIMEOUT = 0x00000102
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    handle = kernel32.OpenProcess(
        SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, False, wintypes.DWORD(pid))
    if not handle:
        return False, 0.0
    try:
        if kernel32.WaitForSingleObject(handle, 0) != WAIT_TIMEOUT:
            return False, 0.0
        times = [wintypes.FILETIME() for _ in range(4)]
        ok = kernel32.GetProcessTimes(handle, ctypes.byref(times[0]), ctypes.byref(times[1]),
                                      ctypes.byref(times[2]), ctypes.byref(times[3]))
        if not ok:
            return True, 0.0
        created = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        return True, (created - 116444736000000000) / 10000000.0
    finally:
        kernel32.CloseHandle(handle)


def _boot_plus(btime: float, start_ticks: float, uptime: float) -> float:
    # stat field 22 is clock ticks since boot; 100 ticks/s is the Linux default.
    return btime + start_ticks / 100.0


# How far a leg's process creation may sit from its pidfile's write time. The
# launcher writes the pidfile within a second of Popen, so a small forward window
# covers a slow write; anything older or newer means the pid now names a
# different process.
CREATION_SLACK_EARLY = 120.0
CREATION_SLACK_LATE = 600.0


def classify(pid: int, pidfile_mtime: float) -> tuple[str, float]:
    alive, created = probe_pid(pid)
    if not alive:
        return "GONE", created
    if created <= 0.0 or pidfile_mtime <= 0.0:
        # The kernel would not date the process, so the identity cannot be
        # confirmed. Treated as LIVE: an unconfirmed leg is the safe answer,
        # because refusing a launch costs a wait while double-running costs the
        # whole machine (the defect this tool exists to stop).
        return "LIVE", created
    if created < pidfile_mtime - CREATION_SLACK_EARLY:
        return "REUSED", created
    if created > pidfile_mtime + CREATION_SLACK_LATE:
        return "REUSED", created
    return "LIVE", created


def leg_from_path(path: str) -> str:
    name = os.path.basename(path)
    if name.startswith(PREFIX) and name.endswith(SUFFIX):
        return name[len(PREFIX):-len(SUFFIX)]
    return name


def pidfile_rows(root: str) -> list[dict]:
    """Census every battery pidfile under <root>/logs.

    status is one of LIVE, GONE, REUSED, UNPARSED.
      LIVE     the pid is alive AND was created when this pidfile was written.
      GONE     nothing answers on that pid; the leg has ended.
      REUSED   the pid is alive but names a different process (Windows reuses
               pids), so it must not block a launch.
      UNPARSED the file does not carry a pid; reported by name so a truncated
               write is visible instead of silent, but it never blocks.
    """
    rows: list[dict] = []
    pattern = os.path.join(root, "logs", PREFIX + "*" + SUFFIX)
    for path in sorted(glob.glob(pattern)):
        leg = leg_from_path(path)
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0.0
        try:
            with open(path, "r", encoding="ascii", errors="strict") as fh:
                raw = fh.read().strip()
            pid = int(raw)
        except (OSError, ValueError, UnicodeDecodeError):
            rows.append({"leg": leg, "path": path, "pid": 0, "status": "UNPARSED",
                         "created": 0.0})
            continue
        status, created = classify(pid, mtime)
        rows.append({"leg": leg, "path": path, "pid": pid, "status": status,
                     "created": created})
    return rows


def census(root: str) -> dict:
    rows = pidfile_rows(root)
    live = [r for r in rows if r["status"] == "LIVE"]
    return {
        "rows": rows,
        "live": live,
        "gone": [r for r in rows if r["status"] == "GONE"],
        "reused": [r for r in rows if r["status"] == "REUSED"],
        "unparsed": [r for r in rows if r["status"] == "UNPARSED"],
        "duplicate": len(live) > 1,
    }


def guard(root: str) -> tuple[int, str]:
    """Answer whether a new leg may start. 0 = clear, 2 = refused."""
    report = census(root)
    if not report["live"]:
        return 0, "INTERLOCK CLEAR live=0 gone=%d unparsed=%d" % (
            len(report["gone"]), len(report["unparsed"]))
    named = " ".join("%s(pid=%d)" % (r["leg"], r["pid"]) for r in report["live"])
    if report["duplicate"]:
        return 2, "E_INTERLOCK_DUPLICATE_LEG live=%d refused %s" % (
            len(report["live"]), named)
    return 2, "E_INTERLOCK_LIVE_LEG live=1 refused %s" % named

def static_criteria(tool_path: str) -> list[tuple[str, bool, str]]:
    """The two non-behavioural criteria: no network use, no shell use.

    Scored against the AST rather than the source text, because a substring
    scan matches the sentence that NAMES the banned token and can therefore
    never pass on its own file (the R2760/R2761 self-matching defect class,
    hit again here on the first run of this very check).
    """
    import ast

    tree = ast.parse(open(tool_path, "r", encoding="utf-8").read())
    modules: set[str] = set()
    shell_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
        elif isinstance(node, ast.Call):
            target = node.func
            name = ""
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                name = "%s.%s" % (target.value.id, target.attr)
            elif isinstance(target, ast.Name):
                name = target.id
            if name in ("os.system", "os.popen", "subprocess.call",
                        "subprocess.run", "subprocess.Popen", "system", "popen"):
                shell_calls.append(name)
    network = sorted(m for m in modules
                     if any(m == p or m.startswith(p + ".") for p in NETWORK_IMPORTS))
    shell = sorted(set(modules & {"subprocess"})) + shell_calls
    return [
        ("AC-LINT5", network == [], "no network import measured=%s" % (network or "none")),
        ("AC-LINT6", shell == [], "no shell or subprocess use measured=%s" % (shell or "none")),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cross-leg reconcile battery interlock (read-only).")
    parser.add_argument("--census", action="store_true",
                        help="print every leg pidfile with LIVE/GONE/UNPARSED")
    parser.add_argument("--guard", action="store_true",
                        help="exit 0 when a new leg may start, 2 when refused")
    parser.add_argument("--check", action="store_true",
                        help="prove AC-LINT1..6 in a private world")
    parser.add_argument("--root", default=os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), help="repo root (default: parent of tools/)")
    args = parser.parse_args(argv)
    if not any((args.census, args.guard, args.check)):
        parser.print_help()
        return 5
    if args.census:
        report = census(args.root)
        print("LEG-CENSUS live=%d reused=%d gone=%d unparsed=%d duplicate=%s" % (
            len(report["live"]), len(report["reused"]), len(report["gone"]),
            len(report["unparsed"]), report["duplicate"]))
        for row in report["rows"]:
            if row["status"] == "GONE":
                continue
            print("  %-8s leg=%s pid=%d %s" % (
                row["status"], row["leg"], row["pid"], row["path"]))
        return 0
    if args.guard:
        rc, line = guard(args.root)
        print(line)
        return rc
    # --check delegates to the private-world driver so the live machine state
    # can never be scored as a pass.
    driver = os.path.join(args.root, "tmp", "check_leg_interlock.py")
    if not os.path.exists(driver):
        print("E_CHECK_DRIVER_MISSING %s" % driver)
        return 3
    import runpy
    namespace = runpy.run_path(driver)
    return namespace["main"]()


if __name__ == "__main__":
    sys.exit(main())
