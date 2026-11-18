"""Suite for the kill-on-close job object that keeps children off dead ports.

Eight criteria AC-KOC1..AC-KOC8, pre-registered in the R2937 backlog row BEFORE
this file and the job wiring existed (in-window pre-registration, disclosed);
AC-KOC6 was pre-registered in the R2947 board row before it existed, and it
answers the question R2937 disclosed rather than decided - whether the
guarantee reaches a GRANDCHILD, not only the layer the launcher assigns.

R2975 adds AC-KOC7..AC-KOC8, pre-registered in the R2975 board row before this
code, because AC-KOC6 left one link unmeasured and the board carried it:
AC-KOC6 asks the KERNEL whether a child of an assigned process is a member, and
then CLOSES THE HANDLE ITSELF from this process. That is membership plus an
explicit close - not the path a crash takes, where the holder is killed hard and
the kernel closes its handles for it. AC-KOC7 measures that path: a holder built
from the SHIPPED job_object law creates the job, spawns the middle layer,
assigns it and then holds the handle until it is hard-killed; the grandchild
below the middle layer must die with it, and an unassigned twin of the same
program must keep serving so the probe is proven able to say no. AC-KOC8
measures the same question in the shipped tree: with a real launcher serving,
every face its panel could start is already owned by that launcher, so the panel
refuses by name and no grandchild process exists to be reached or missed.
Neither criterion stands in for the other, and neither re-claims the membership
AC-KOC6 already measured.

R2976 adds AC-KOC9..AC-KOC10, pre-registered in the R2976 board row before this
code. AC-KOC8's result rests on a relation between two constants that nothing
pinned: panel.FACE_IDS was a subset of start_all.FACE_KEYS, they agreed by
coincidence, and either file could be edited into disagreement with every suite
still green. AC-KOC9 asserts the relation itself through the shipped predicate
in face_coverage.py, including the second hop (every owned face has a port key,
every port key is a planned socket) and the fact that the published face_ports
are derived from the same constant. AC-KOC10 is the red control: a private
world with a panel-only face must be REFUSED, so the criterion is proven able
to say no rather than merely able to report green. This is an anti-decay
assertion and NOT a security boundary - it consults no request path and grants
nothing; the module header says so in the same words.

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
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

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

# AC-KOC7 scaffolding: a HOLDER that stands where the launcher stands. It is
# built from the shipped job_object law rather than from its own win32 calls, so
# what is measured is this repo's law and not a copy of it. It assigns the
# middle layer and then holds the handle and does nothing - which is exactly the
# launcher's relationship to its children, except that the launcher also serves.
# Killing this process hard is the crash path: the kernel closes its handles.
KOC7_HOLDER = '''import subprocess
import sys
import time

sandbox_dir, middle_src, grand_src, port, pidfile, go = sys.argv[1:7]
sys.path.insert(0, sandbox_dir)
import job_object

job = job_object.create(None)
middle = subprocess.Popen(
    [sys.executable, middle_src, grand_src, port, pidfile, go],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
job_object.assign(job, middle.pid)
with open(pidfile + ".middle", "w", encoding="utf-8") as handle:
    handle.write("%d\\n" % middle.pid)
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


def pid_alive(pid):
    """True while that pid names a process the kernel has not reaped yet.

    Asked with the synchronisation object rather than by name, so a pid whose
    process is gone reads dead even when the number itself still appears in a
    listing; a recycled pid could read alive, which is why this is sampled
    immediately after the kill and is never the only arm.
    """
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    wait_timeout = 0x102
    proc = kernel32.OpenProcess(0x00100000, 0, int(pid))
    if not proc:
        return False
    try:
        return kernel32.WaitForSingleObject(proc, 0) == wait_timeout
    finally:
        kernel32.CloseHandle(proc)


def spare_port():
    """One free loopback port, taken then released for the child to bind."""
    probe = socket.socket()
    try:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])
    finally:
        probe.close()


def http_json(port, path, payload=None, timeout=40.0):
    """(status, object) from a loopback HTTP call; 4xx is data, not an error."""
    url = "http://127.0.0.1:%d%s" % (int(port), path)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, method="POST" if body is not None else "GET",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as res:
            return res.getcode(), json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, {"raw": raw}


def file_digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


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

    # AC-KOC7: the same layer, but through the path a CRASH takes. AC-KOC6
    # closed the handle from this process; here the holder is hard-killed, so
    # the kernel closes it, and nothing this suite does can help or hinder the
    # grandchild afterwards.
    bad7 = []
    gc7_port = spare_port()
    out7_port = spare_port()
    holder_src = _write_temp("koc7_holder.py", KOC7_HOLDER)
    middle7_src = _write_temp("koc7_middle.py", KOC6_PARENT)
    grand7_src = _write_temp("koc7_grand.py", KOC6_GRAND)
    gc7_pid_file = os.path.join(TMP, "koc7.grand.pid")
    middle7_pid_file = gc7_pid_file + ".middle"
    go7 = os.path.join(TMP, "koc7.go")
    for path in (gc7_pid_file, middle7_pid_file, go7):
        if os.path.exists(path):
            os.remove(path)
    holder = None
    outsider7 = None
    middle7_pid = 0
    grand7_pid = 0
    try:
        holder = subprocess.Popen(
            [sys.executable, holder_src, HERE, middle7_src, grand7_src,
             str(gc7_port), gc7_pid_file, go7],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        deadline = time.time() + 40.0
        while time.time() < deadline and not os.path.exists(middle7_pid_file):
            time.sleep(0.05)
        if os.path.exists(middle7_pid_file):
            with open(middle7_pid_file, encoding="utf-8") as handle:
                middle7_pid = int(handle.read().strip() or 0)
        if not middle7_pid:
            bad7.append("holder-never-assigned-a-middle-layer")
        elif not pid_alive(middle7_pid):
            bad7.append("middle-layer-dead-before-the-kill")
        with open(go7, "w", encoding="utf-8") as handle:
            handle.write("go\n")
        deadline = time.time() + 40.0
        while time.time() < deadline:
            if os.path.exists(gc7_pid_file) and can_connect(gc7_port):
                break
            time.sleep(0.05)
        if os.path.exists(gc7_pid_file):
            with open(gc7_pid_file, encoding="utf-8") as handle:
                grand7_pid = int(handle.read().strip() or 0)
        if not grand7_pid:
            bad7.append("grandchild-never-reported")
        if not can_connect(gc7_port):
            bad7.append("grandchild-never-listened")
        # The control that lets this arm say NO: the same program, never
        # assigned, must still be serving after the kill.
        outsider7 = subprocess.Popen(
            [sys.executable, grand7_src, str(out7_port)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        deadline = time.time() + 30.0
        while time.time() < deadline and not can_connect(out7_port):
            time.sleep(0.05)
        if not can_connect(out7_port):
            bad7.append("outsider-never-listened")
        # THE measurement: no finally, no stop file, the only handle to the job
        # owned by a process that is about to stop existing.
        terminate_pid(holder.pid)
        holder.wait(timeout=10)
        silent = wait_all_silent([gc7_port], 20.0)
        if silent < 0:
            bad7.append("grandchild-outlived-the-hard-killed-holder")
        else:
            print("PASS AC-KOC7 the grandchild's port went silent %ss after "
                  "the holder was hard-killed" % (silent,))
        if middle7_pid and pid_alive(middle7_pid):
            bad7.append("middle-layer-outlived-the-hard-killed-holder")
        if not can_connect(out7_port):
            bad7.append("outsider-was-killed-by-a-job-it-never-joined")
    finally:
        for victim in (holder, outsider7):
            if victim is not None and victim.poll() is None:
                victim.kill()
                try:
                    victim.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    pass
        for pid in (grand7_pid, middle7_pid):
            if pid:
                try:
                    terminate_pid(pid)
                except OSError:
                    pass
        for port in (gc7_port, out7_port):
            _kill_by_port(port)
    ok("AC-KOC7 a grandchild of an assigned child dies when the HOLDER is "
       "hard-killed", not bad7, ",".join(bad7))

    # AC-KOC8: the other half of the same question, asked of the SHIPPED tree.
    # A real launcher serves; every face its panel could start is asked for by
    # name. If the panel started one, this round would have a grandchild to
    # worry about; the arm measures what really happens instead of assuming.
    # The private record is per PROCESS as well as per name: its kernel claim
    # name is derived from that path, so a launcher left behind by a crashed
    # earlier run can never make this arm red for a reason it is not asking
    # about (measured: it did exactly that once during this window).
    bad8 = []
    chain = Box("realchain-%d" % os.getpid(), stop_file=True)
    chain_rep = chain.start()
    import panel as panel_module  # noqa: E402  (path wired above)
    panel_port = (chain_rep.get("ports") or {}).get("panel")
    chain_face_ports = chain_rep.get("face_ports") or {}
    started_faces = []
    if not panel_port:
        bad8.append("launcher-published-no-panel-port")
    else:
        before = (file_digest(chain.report_path)
                  if os.path.exists(chain.report_path) else "")
        for face_id in panel_module.FACE_IDS:
            code, body = http_json(panel_port, "/panel/api/start",
                                   {"face": face_id})
            if code != 409 or body.get("error") != "E_PANEL_OWNED_BY_LAUNCHER":
                bad8.append("%s->%s/%s" % (face_id, code, body.get("error")))
                continue
            if body.get("owner") != panel_module.OWNER_LAUNCHER:
                bad8.append("%s-owner=%s" % (face_id, body.get("owner")))
            expected = int(chain_face_ports.get(face_id) or -1)
            if int(body.get("port") or 0) != expected:
                bad8.append("%s-port=%s-expected=%s"
                            % (face_id, body.get("port"), expected))
        state_code, state = http_json(panel_port, panel_module.STATE_ROUTE)
        if state_code != 200:
            bad8.append("state->%s" % (state_code,))
        else:
            # `started` in this payload means "a process serves it", and a face
            # the launcher owns reads started=True with owner=launcher - so the
            # discriminator for "a panel child was born" is the OWNER, not the
            # flag. Judged by owner here, and the pinned wording is corrected
            # in the board row rather than this criterion being loosened.
            started_faces = [row.get("id")
                             for row in state.get("faces") or []
                             if row.get("owner") == panel_module.OWNER_PANEL]
            if started_faces:
                bad8.append("panel-started=" + ",".join(started_faces))
            owners = set(row.get("owner") for row in state.get("faces") or [])
            if owners != {panel_module.OWNER_LAUNCHER}:
                bad8.append("owners=%s" % (sorted(map(str, owners)),))
            if sorted(state.get("startable") or []) != sorted(
                    panel_module.FACE_IDS):
                bad8.append("startable-moved")
        after = (file_digest(chain.report_path)
                 if os.path.exists(chain.report_path) else "")
        if before != after:
            bad8.append("launcher-report-changed")
    stop_code = chain.polite_stop()
    if stop_code != 0:
        bad8.append("launcher-stop-exit=%s" % (stop_code,))
    for path in (chain.registry_path, chain.report_path):
        if os.path.exists(path):
            os.remove(path)
    ok("AC-KOC8 under a serving launcher the panel starts nothing, so the "
       "shipped chain has no grandchild", not bad8, ",".join(bad8))

    # AC-KOC9: the relation AC-KOC8 rests on, asserted instead of assumed.
    # These arms read constants and pure functions only - no process starts,
    # no socket binds, and the single report_of call passes all-zero ports so
    # nothing is connected either.
    import face_coverage as coverage_module  # noqa: E402  (path wired above)
    verdict = coverage_module.coverage(panel_module.FACE_IDS,
                                       start_all.FACE_KEYS)
    ok("AC-KOC9 every panel-startable face is one the launcher owns",
       verdict["ok"] is True and verdict["unowned"] == (),
       "unowned=%s startable=%s owned=%s"
       % (verdict["unowned"], verdict["startable"], verdict["owned"]))
    ok("AC-KOC9 every owned face has a planned socket behind it",
       set(start_all.FACE_PORT_KEY) == set(start_all.FACE_KEYS)
       and set(start_all.FACE_PORT_KEY.values()) <= set(start_all.PLAN_KEYS),
       "faces=%d port_keys=%d plan=%d"
       % (len(start_all.FACE_KEYS), len(start_all.FACE_PORT_KEY),
          len(start_all.PLAN_KEYS)))
    zero = dict((key, 0) for key in start_all.PLAN_KEYS)
    published = start_all.report_of("127.0.0.1", zero, "", {}, {}, [])
    ok("AC-KOC9 the published face_ports are derived from FACE_KEYS",
       set(published.get("face_ports") or {}) == set(start_all.FACE_KEYS),
       "published=%s" % (sorted(published.get("face_ports") or {}),))
    launcher_only = coverage_module.unowned_startable(start_all.FACE_KEYS,
                                                      panel_module.FACE_IDS)
    ok("AC-KOC9 the relation is one-directional, never an equality",
       bool(launcher_only)
       and set(launcher_only) == set(start_all.FACE_KEYS)
       - set(panel_module.FACE_IDS),
       "launcher_only=%s" % (launcher_only,))

    # AC-KOC10: the red control. A private world holding one panel-only face
    # must be refused, so this criterion is proven able to say no; handing the
    # same world a matching owned set must turn it green, which shows the
    # refusal came from the missing face rather than from the name itself.
    bad10 = []
    red = coverage_module.coverage(("checkout", "ghost"), ("checkout",))
    if red["ok"] is not False:
        bad10.append("panel-only-face-read-as-covered")
    if red["unowned"] != ("ghost",):
        bad10.append("unowned=%s" % (red["unowned"],))
    healed = coverage_module.coverage(("checkout", "ghost"),
                                      ("checkout", "ghost"))
    if healed["ok"] is not True or healed["unowned"] != ():
        bad10.append("healed-still-red=%s" % (healed["unowned"],))
    repeated = coverage_module.unowned_startable(("b", "a", "b"), ("a",))
    if repeated != ("b",):
        bad10.append("order-or-repeat-sensitive=%s" % (repeated,))
    empty = coverage_module.coverage((), ())
    if empty["ok"] is not True or empty["unowned"] != ():
        bad10.append("empty-world=%s" % (empty,))
    # The decay this criterion exists for, spelled against the REAL launcher
    # constant: one panel-only face added to today's startable set must be
    # refused, so a future edit to either file cannot pass silently.
    drift = coverage_module.coverage(
        tuple(panel_module.FACE_IDS) + ("ghost",), start_all.FACE_KEYS)
    if drift["ok"] is not False or drift["unowned"] != ("ghost",):
        bad10.append("live-constant-drift=%s" % (drift["unowned"],))
    ok("AC-KOC10 the coverage predicate can say NO to a panel-only face",
       not bad10, ",".join(bad10))

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
