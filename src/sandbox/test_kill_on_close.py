"""Suite for the kill-on-close job object that keeps children off dead ports.

Five criteria AC-KOC1..AC-KOC5, pre-registered in the R2937 backlog row BEFORE
this file and the job wiring existed (in-window pre-registration, disclosed).

The claim under test is not "the launcher tears down nicely" - AC-STL5 already
covers that. It is the stronger one R2934 measured the absence of: a launcher
killed HARD, with no chance to run its `finally` and no stop file, must leave
ZERO listening sandbox ports, because its children were placed in a job armed
with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE.

Every number here is measured: the report is read from disk, the ten ports are
probed with real TCP connects, and the red control runs the same hard kill with
`--no-job` so the arm is proven able to SEE an orphan rather than merely able
to report green.

Usage: python test_kill_on_close.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import ctypes
import json
import os
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MODULE = os.path.join(HERE, "start_all.py")
JOB_LAW = os.path.join(HERE, "job_object.py")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
TMP = os.path.join(REPO, "logs", "kill-on-close-suite")

CHECKS = []


def ok(name, passed, detail=""):
    CHECKS.append((name, bool(passed)))
    print("%s %s%s" % ("PASS" if passed else "FAIL", name,
                       ("  " + detail) if detail else ""))
    return bool(passed)


def can_connect(port, timeout=0.3):
    if not port:
        return False
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def wait_file(path, timeout=120.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as handle:
                    return json.load(handle)
            except (OSError, ValueError):
                pass
        time.sleep(0.15)
    return None


def terminate_pid(pid):
    """The same hard kill the suite uses on the launcher, for cleanup."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    proc = kernel32.OpenProcess(0x0001, 0, int(pid))
    if not proc:
        return False
    try:
        kernel32.TerminateProcess(proc, 1)
    finally:
        kernel32.CloseHandle(proc)
    return True


class Box(object):
    """One launcher run. `hard` kills the parent without its finally."""

    def __init__(self, name, extra=None, stop_file=False):
        self.report_path = os.path.join(TMP, name + ".json")
        self.stop_path = os.path.join(TMP, name + ".stop")
        self.stop_file = stop_file
        # A private machine record per run: this suite hard-kills launchers on
        # purpose, so it must never leave a claim in the per-user record that a
        # real launcher would have to judge (R2939).
        self.registry_path = os.path.join(TMP, name + ".registry.json")
        argv = [sys.executable, MODULE, "--timeout", "40",
                "--registry", self.registry_path,
                "--report-json", self.report_path]
        if stop_file:
            argv += ["--stop-file", self.stop_path]
        argv += list(extra or [])
        self.argv = argv
        self.proc = None
        self.report = {}

    def start(self):
        for path in (self.report_path, self.stop_path):
            if os.path.exists(path):
                os.remove(path)
        self.proc = subprocess.Popen(
            self.argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.report = wait_file(self.report_path) or {}
        return self.report

    def ports(self):
        return [int(port) for port in (self.report.get("ports") or {}).values()]

    def hard_kill(self):
        """TerminateProcess on the launcher: no finally, no stop file."""
        self.proc.kill()
        self.proc.wait(timeout=10)
        return self.proc.returncode

    def polite_stop(self, timeout=25.0):
        with open(self.stop_path, "w", encoding="utf-8") as handle:
            handle.write("stop\n")
        deadline = time.time() + timeout
        while self.proc.poll() is None and time.time() < deadline:
            time.sleep(0.1)
        if self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=5)
        return self.proc.returncode


def wait_all_silent(ports, timeout):
    """Seconds until every port refuses a connect, or -1 if any still listens."""
    deadline = time.time() + float(timeout)
    while True:
        alive = [port for port in ports if can_connect(port)]
        if not alive:
            return round(float(timeout) - (deadline - time.time()), 2)
        if time.time() >= deadline:
            return -1
        time.sleep(0.2)


def wait_any_listening(ports, timeout):
    deadline = time.time() + float(timeout)
    while time.time() < deadline:
        alive = [port for port in ports if can_connect(port)]
        if alive:
            return alive
        time.sleep(0.2)
    return []


def source_of(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    return raw, raw.decode("utf-8", "replace")


def main():
    os.makedirs(TMP, exist_ok=True)
    if sys.platform != "win32":
        print("SKIP suite=kill-on-close reason=no-job-objects-on-this-platform")
        return 0

    # AC-KOC1: the report proves its own guarantee, derived not typed.
    box = Box("job")
    rep = box.start()
    sys.path.insert(0, HERE)
    import start_all  # noqa: E402  (path wired above)
    expected = len(start_all.build_commands("127.0.0.1", rep.get("ports") or {}))
    job = rep.get("job") or {}
    pids = rep.get("pids") or {}
    ok("AC-KOC1 report arms the job and counts every child",
       bool(rep) and job.get("enabled") is True
       and int(job.get("assigned") or 0) == expected and not job.get("errors"),
       "enabled=%s assigned=%s expected=%d errors=%s"
       % (job.get("enabled"), job.get("assigned"), expected,
          job.get("errors")))
    ok("AC-KOC1 every child pid is published by name",
       sorted(pids) == sorted(name for name, _argv in
                              start_all.build_commands("127.0.0.1",
                                                       rep.get("ports") or {})),
       "pids=%s" % (sorted(pids),))
    ports = box.ports()
    ok("AC-KOC1 the ten planned ports are all really listening before the kill",
       len(ports) == len(start_all.PLAN_KEYS)
       and len([port for port in ports if can_connect(port)]) == len(ports),
       "ports=%d listening=%d"
       % (len(ports), len([port for port in ports if can_connect(port)])))

    # AC-KOC2: the real proof. Hard-kill the PARENT and nothing survives.
    box.hard_kill()
    took = wait_all_silent(ports, 12.0)
    ok("AC-KOC2 a HARD-killed launcher leaves zero listening ports",
       took >= 0, "silent_after=%ss ports=%d" % (took, len(ports)))

    # AC-KOC3: the red control - same hard kill, no job, the orphan appears.
    red = Box("red", extra=["--no-job"])
    red_rep = red.start()
    red_ports = red.ports()
    red_job = red_rep.get("job") or {}
    ok("AC-KOC3 the control run really started WITHOUT a job",
       bool(red_rep) and red_job.get("enabled") is False
       and len([port for port in red_ports if can_connect(port)]) == len(red_ports),
       "enabled=%s ports=%d" % (red_job.get("enabled"), len(red_ports)))
    red.hard_kill()
    survivors = wait_any_listening(red_ports, 4.0)
    ok("AC-KOC3 without the job the SAME hard kill leaves orphans listening",
       bool(survivors), "survivors=%d example=%s"
       % (len(survivors), survivors[:3]))
    for pid in (red_rep.get("pids") or {}).values():
        terminate_pid(pid)
    cleaned = wait_all_silent(red_ports, 8.0)
    ok("AC-KOC3 the control's orphans are killed by published pid",
       cleaned >= 0, "silent_after=%ss" % cleaned)

    # AC-KOC4: the normal path does not regress - the stop file still exits 0.
    polite = Box("polite", stop_file=True)
    polite_rep = polite.start()
    polite_ports = polite.ports()
    code = polite.polite_stop()
    silent = wait_all_silent(polite_ports, 10.0)
    ok("AC-KOC4 the stop-file path still exits 0 and leaves no port open",
       bool(polite_rep) and code == 0 and silent >= 0,
       "exit=%s silent_after=%ss ports=%d"
       % (code, silent, len(polite_ports)))

    # AC-KOC5: one law, and honest failure off Windows.
    raw, law_src = source_of(JOB_LAW)
    imports = sorted(set(line.strip().split()[1].split(".")[0]
                         for line in law_src.splitlines()
                         if line.strip().startswith("import ")))
    ok("AC-KOC5 the job law is a leaf (ctypes and sys only, no BOM, no CRLF)",
       imports == ["ctypes", "sys"] and raw[:3] != b"\xef\xbb\xbf"
       and b"\r\n" not in raw, "imports=%s" % (imports,))
    ok("AC-KOC5 the law names the flag it arms",
       "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000" in law_src,
       "flag=0x2000")
    _raw_sa, sa_src = source_of(MODULE)
    ok("AC-KOC5 the launcher delegates instead of holding its own win32 calls",
       "import job_object" in sa_src and "CreateJobObjectW" not in sa_src
       and "AssignProcessToJobObject" not in sa_src,
       "delegates=%s" % ("job_object" in sa_src,))
    import job_object  # noqa: E402  (path wired above)
    ok("AC-KOC5 availability is a real boolean, not a promise",
       isinstance(job_object.available(), bool), "available=%s"
       % (job_object.available(),))
    with open(REGISTRY, encoding="utf-8") as handle:
        registry_text = handle.read()
    ok("AC-KOC5 exactly one registry row names this suite",
       registry_text.count('"kill-on-close"') == 1,
       "rows=%d" % registry_text.count('"kill-on-close"'))

    total = len(CHECKS)
    acs = set()
    for name in [entry[0] for entry in CHECKS]:
        token = name.split(" ", 1)[0]
        for cut in range(len(token), 0, -1):
            if token[cut - 1].isdigit():
                acs.add(token[:cut])
                break
    print("suite: %d assertions over %d criteria" % (total, len(acs)))
    failed = [name for name, passed in CHECKS if not passed]
    if failed:
        print("SUITE FAIL %d/%d failed=%s"
              % (total - len(failed), total, "; ".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
