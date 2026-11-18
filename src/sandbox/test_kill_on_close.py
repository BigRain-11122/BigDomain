"""Suite for the kill-on-close job object that keeps children off dead ports.

Six criteria AC-KOC1..AC-KOC6, pre-registered in the R2937 backlog row BEFORE
this file and the job wiring existed (in-window pre-registration, disclosed);
AC-KOC6 was pre-registered in the R2947 board row before it existed, and it
answers the question R2937 disclosed rather than decided - whether the
guarantee reaches a GRANDCHILD, not only the layer the launcher assigns.

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

# AC-KOC6 scaffolding: two tiny processes, so the job is asked about a
# GRANDCHILD. Only the middle layer is ever assigned; the layer below it is
# inside the job because the kernel inherits job membership, which is the claim
# under test. The middle layer waits for a go file before spawning, so the
# grandchild can never win a race and be born outside the job.
KOC6_PARENT = '''import os
import subprocess
import sys
import time

grand_src, port, pidfile, go = sys.argv[1:5]
while not os.path.exists(go):
    time.sleep(0.02)
child = subprocess.Popen([sys.executable, grand_src, port],
                         stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
with open(pidfile, "w", encoding="utf-8") as handle:
    handle.write("%d\\n" % child.pid)
while True:
    time.sleep(0.2)
'''

KOC6_GRAND = '''import socket
import sys
import time

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", int(sys.argv[1])))
server.listen(8)
while True:
    time.sleep(0.2)
'''


def _write_temp(name, text):
    if not os.path.isdir(TMP):
        os.makedirs(TMP)
    path = os.path.join(TMP, name)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


def _kill_by_port(port):
    """Last-resort cleanup: kill whatever still LISTENS on that port.

    Two guards, both learned the hard way in this window: only a LISTENING row
    counts (an ESTABLISHED reshape-time row names a different owner), and this
    suite never kills itself or its own parent, because a TerminateProcess on
    self exits silently with rc=1 and looks exactly like a crash.
    """
    mine = (os.getpid(), os.getppid())
    try:
        out = subprocess.run(
            ["netstat", "-ano"], stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=25).stdout.decode("utf-8",
                                                                "replace")
    except (OSError, subprocess.SubprocessError):
        return
    for line in out.splitlines():
        if "LISTENING" not in line or ("127.0.0.1:%d" % int(port)) not in line:
            continue
        parts = line.split()
        if not parts or not parts[-1].isdigit():
            continue
        pid = int(parts[-1])
        if pid in mine:
            continue
        try:
            terminate_pid(pid)
        except OSError:
            pass


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

    # AC-KOC6: the guarantee reaches a GRANDCHILD (R2947 board item (1)).
    # AC-KOC2 kills the launcher's direct children. Here only the FIRST layer
    # is ever assigned and the kernel is asked whether the LAYER BELOW it is
    # inside the same job - membership, not "the port went quiet afterwards",
    # because a port can also go quiet for reasons that have nothing to do
    # with this job (measured: the ambient shell reaped an unassigned tree in
    # 1.6s, so a death-correlation control could not discriminate here).
    bad = []
    ports = []
    for _ in (0, 1):
        holder_probe = socket.socket()
        holder_probe.bind(("127.0.0.1", 0))
        ports.append(holder_probe.getsockname()[1])
        holder_probe.close()
    gc_port, out_port = ports
    parent_src = _write_temp("koc6_parent.py", KOC6_PARENT)
    grand_src = _write_temp("koc6_grand.py", KOC6_GRAND)
    pidfile = os.path.join(TMP, "koc6.grand.pid")
    go = os.path.join(TMP, "koc6.go")
    for path in (pidfile, go):
        if os.path.exists(path):
            os.remove(path)
    import job_object  # noqa: E402  (path wired above)
    job = None
    parent = None
    outsider = None
    grand_pid = None
    try:
        job = job_object.create()
        parent = subprocess.Popen(
            [sys.executable, parent_src, grand_src, str(gc_port), pidfile, go],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        job_object.assign(job, parent.pid)
        # the middle layer only spawns the grandchild once it is already in
        # the job, so inheritance - not a race - decides membership.
        with open(go, "w", encoding="utf-8") as handle:
            handle.write("go\n")
        deadline = time.time() + 40.0
        while time.time() < deadline:
            if os.path.exists(pidfile) and can_connect(gc_port):
                break
            time.sleep(0.05)
        if os.path.exists(pidfile):
            with open(pidfile, encoding="utf-8") as handle:
                grand_pid = int(handle.read().strip() or 0)
        if not grand_pid:
            bad.append("grandchild-never-reported")
        if not can_connect(gc_port):
            bad.append("grandchild-never-listened")
        if not job_object.is_in_job(job, parent.pid):
            bad.append("assigned-parent-not-in-job")
        if grand_pid and not job_object.is_in_job(job, grand_pid):
            bad.append("grandchild-not-in-job")
        # control: same program, never assigned, must read OUTSIDE the job and
        # must survive the job being closed - so the probe can say "no".
        outsider = subprocess.Popen(
            [sys.executable, grand_src, str(out_port)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        deadline = time.time() + 30.0
        while time.time() < deadline and not can_connect(out_port):
            time.sleep(0.05)
        if job_object.is_in_job(job, outsider.pid):
            bad.append("unassigned-process-read-as-inside")
        # closing the handle kills every member: the grandchild's port must go
        # silent while the outsider keeps serving.
        job_object.close(job)
        job = None
        silent = wait_all_silent([gc_port], 20)
        if silent < 0:
            bad.append("grandchild-outlived-the-job")
        else:
            print("PASS AC-KOC6 the grandchild's port went silent in %ss"
                  % (silent,))
        if not can_connect(out_port):
            bad.append("outsider-was-killed-by-another-jobs-close")
    finally:
        if job is not None:
            job_object.close(job)
        for victim in (parent, outsider):
            if victim is not None and victim.poll() is None:
                victim.kill()
                try:
                    victim.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    pass
        if grand_pid:
            try:
                terminate_pid(grand_pid)
            except OSError:
                pass
        for port in (gc_port, out_port):
            _kill_by_port(port)
    ok("AC-KOC6 a grandchild joins the job the kernel inherits", not bad,
       ",".join(bad))

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
