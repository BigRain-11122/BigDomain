"""Read one battery leg and print a single adoption verdict, writing nothing.

Three windows in a row (R2726, R2727, R2728) measured the same live leg by hand
with the same three readings typed into a shell: a kernel liveness probe on the
pid file, a byte and line count on the stream, and a count of the PASS and FAIL
suite rows. The same probe is copy-pasted into eight per-round launchers. This
tool is the ONE read face for that, so a handover window answers "is the leg
alive, how far is it, may I adopt it yet" with one command and no shell coding.

It is deliberately a READ face: nothing is written, no pid is signalled, no
evidence path is created, and the stream is never appended to. The verdict is
printed on one line so a board line or a log line can quote it verbatim.

Verdicts and exit codes:
  LEG-ALIVE-NO-EVIDENCE   10  the pid answers the kernel probe and no evidence
  LEG-DEAD-NO-EVIDENCE    11  the pid is gone and no evidence was written
  EVIDENCE-READY          20  the evidence exists and every row measures green
  EVIDENCE-RED            21  the evidence exists but a measured row is not green
  E_NO_TARGET             30  --target was not given, so remaining is unknown

The suite row count is matched on "PASS suite " WITH the trailing space. R2724
disclosed that a bare "PASS suite" prefix also matches the closing summary row
("PASS suites 672/672 green") and so reports one suite too many; the self check
pins that trap so this face cannot repeat it.
"""

import argparse
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
LOGS = os.path.join(REPO, "logs")
QA = os.path.join(REPO, "qa")

ALIVE = 10
DEAD = 11
READY = 20
RED = 21
NO_TARGET = 30


def paths_for(leg):
    return (os.path.join(LOGS, "battery-%s.stream" % leg),
            os.path.join(LOGS, "battery-%s.pid" % leg),
            os.path.join(QA, "reconcile-all-%s.log" % leg))


def live_pid(pidfile):
    """Return the pid when that process is still alive, else 0.

    os.kill(pid, 0) does NOT raise for a live pid on Windows, which is why the
    shipped launchers ask the kernel instead through OpenProcess plus
    WaitForSingleObject. A WMI CommandLine scan is never used here: it read an
    EMPTY list for two demonstrably live legs on this host.
    """
    if not os.path.exists(pidfile):
        return 0
    try:
        with open(pidfile, "r", encoding="ascii") as fh:
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
        return pid if kernel32.WaitForSingleObject(handle, 0) == WAIT_TIMEOUT else 0
    finally:
        kernel32.CloseHandle(handle)


def read_lines(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        raw = fh.read()
    return raw, raw.decode("utf-8", "replace").splitlines()


def count_rows(lines):
    """Count real suite rows, then the criteria those rows declare.

    A real row ends its counts with "exit=" and starts with "PASS suite " or
    "FAIL suite ". The summary row starts with "PASS suites " and is excluded
    by the trailing space alone.
    """
    passed, failed, names, criteria = 0, 0, set(), 0
    for line in lines:
        if " exit=" not in line:
            continue
        if line.startswith("PASS suite "):
            passed += 1
        elif line.startswith("FAIL suite "):
            failed += 1
            continue
        else:
            continue
        parts = line.split()
        if len(parts) > 2:
            names.add(parts[2])
        for token in parts:
            if token.startswith("criteria="):
                try:
                    criteria += int(token.split("=", 1)[1])
                except ValueError:
                    pass
    return passed, failed, len(names), criteria


def byte_reading(raw):
    return {
        "bytes": len(raw),
        "bom": raw.startswith(b"\xef\xbb\xbf"),
        "crlf": raw.count(b"\r\n"),
        "lone_cr": raw.count(b"\r") - raw.count(b"\r\n"),
        "nul": raw.count(b"\x00"),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--leg", required=False)
    ap.add_argument("--target", type=int, default=0)
    ap.add_argument("--stream")
    ap.add_argument("--pidfile")
    ap.add_argument("--evidence")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args(argv)

    if args.self_check:
        return self_check()
    if not args.leg and not (args.stream and args.pidfile and args.evidence):
        print("E_ARGS need --leg or all three of --stream --pidfile --evidence")
        return 2

    stream, pidfile, evidence = paths_for(args.leg or "")
    stream = args.stream or stream
    pidfile = args.pidfile or pidfile
    evidence = args.evidence or evidence

    raw_ev = read_lines(evidence)
    if raw_ev:
        raw, lines = raw_ev
        b = byte_reading(raw)
        passed, failed, names, criteria = count_rows(lines)
        green = (not b["bom"] and b["crlf"] == 0 and b["lone_cr"] == 0
                 and b["nul"] == 0 and failed == 0 and passed > 0
                 and names == passed)
        if args.target:
            green = green and passed == args.target
        print("EVIDENCE-%s bytes=%d suites=%d names=%d fails=%d criteria=%d "
              "bom=%s crlf=%d lone_cr=%d nul=%d target=%d"
              % ("READY" if green else "RED", b["bytes"], passed, names,
                 failed, criteria, b["bom"], b["crlf"], b["lone_cr"], b["nul"],
                 args.target))
        return READY if green else RED

    pid = live_pid(pidfile)
    raw_st = read_lines(stream)
    if raw_st is None:
        print("%s pid=%d stream=absent evidence=absent"
              % ("LEG-ALIVE-NO-EVIDENCE" if pid else "LEG-DEAD-NO-EVIDENCE", pid))
        return ALIVE if pid else DEAD
    raw, lines = raw_st
    passed, failed, names, _ = count_rows(lines)
    remaining = (args.target - passed) if args.target else -1
    if args.target == 0:
        print("E_NO_TARGET pid=%d bytes=%d pass=%d fail=%d"
              % (pid, len(raw), passed, failed))
        return NO_TARGET
    print("%s pid=%d bytes=%d lines=%d pass=%d fail=%d remaining=%d target=%d"
          % ("LEG-ALIVE-NO-EVIDENCE" if pid else "LEG-DEAD-NO-EVIDENCE",
             pid, len(raw), len(lines), passed, failed, remaining, args.target))
    return ALIVE if pid else DEAD


def self_check():
    """Prove the counting rules on private fixtures under the system temp."""
    import tempfile
    checks = []
    with tempfile.TemporaryDirectory() as tmp:
        stream = os.path.join(tmp, "battery-X.stream")
        pidfile = os.path.join(tmp, "battery-X.pid")
        evidence = os.path.join(tmp, "reconcile-all-X.log")
        with open(stream, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("PASS suite alpha exit=0 criteria=6\n")
            fh.write("  | PASS AC-A1 a criterion\n")
            fh.write("PASS suite beta exit=0 criteria=4\n")
            fh.write("FAIL suite gamma exit=1 criteria=4\n")
            fh.write("PASS suites 2/2 green\n")
        raw = open(stream, "rb").read()
        passed, failed, names, criteria = count_rows(
            raw.decode("utf-8").splitlines())
        checks.append(("suite rows counted without the summary row",
                       (passed, failed, names, criteria) == (2, 1, 2, 10)))
        checks.append(("fail rows are never counted as pass rows", failed == 1))
        with open(pidfile, "w", encoding="ascii") as fh:
            fh.write("999999\n")
        checks.append(("a dead pid reads 0", live_pid(pidfile) == 0))
        with open(pidfile, "w", encoding="ascii") as fh:
            fh.write("%d\n" % os.getpid())
        checks.append(("the live self pid reads back", live_pid(pidfile) == os.getpid()))
        with open(evidence, "wb") as fh:
            fh.write(b"PASS suite alpha exit=0 criteria=6\n"
                     b"PASS suite beta exit=0 criteria=6\n"
                     b"PASS suites 2/2 green\n")
        b = byte_reading(open(evidence, "rb").read())
        checks.append(("a clean evidence file measures clean",
                       b["bom"] is False and b["crlf"] == 0
                       and b["lone_cr"] == 0 and b["nul"] == 0))
        with open(evidence, "wb") as fh:
            fh.write(b"\xef\xbb\xbfPASS suite alpha exit=0 criteria=6\r\n")
        b = byte_reading(open(evidence, "rb").read())
        checks.append(("a BOM and a CRLF are both measured", b["bom"] and b["crlf"] == 1))
        argv = ["--stream", stream, "--pidfile", pidfile,
                "--evidence", evidence, "--target", "2"]
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(argv)
        line = buf.getvalue().strip()
        checks.append(("a BOM evidence exits RED, not READY", code == RED))
        checks.append(("the verdict line names the byte defect",
                       "EVIDENCE-RED" in line and "bom=True" in line))
        os.remove(evidence)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(argv)
        checks.append(("no evidence plus a live pid exits ALIVE",
                       code == ALIVE and "LEG-ALIVE-NO-EVIDENCE" in buf.getvalue()))
        checks.append(("remaining is the target minus the rows landed",
                       "remaining=0" in buf.getvalue()))
    bad = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print("%s %s" % ("PASS" if ok else "FAIL", name))
    print("SELF-CHECK %s checks=%d red=%d"
          % ("PASS" if not bad else "FAIL", len(checks), len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
