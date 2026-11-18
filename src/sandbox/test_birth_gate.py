"""Suite for the birth-site gate that closes R2940's measured hand-start hole.

Five criteria AC-HSG1..AC-HSG5, pre-registered in src/os/backlog.md BEFORE this
file, src/sandbox/birth_gate.py and the six entry wires existed.

Nothing here is read off a paragraph. A real holder process takes the kernel
claim and writes the detail record naming ITSELF, and then the suite starts the
SHIPPED lobby server directly - beside that holder - and requires the named
refusal with nothing listening. The same command in the same world without the
holder must come up, so the refusal is caused by the holder. The legitimate
path is proven by the same holder starting the face as ITS OWN CHILD.

Usage: python test_birth_gate.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import json
import os
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LOBBY = os.path.join(HERE, "lobby", "server.py")
LEAF = os.path.join(HERE, "birth_gate.py")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
ROW = "birth-gate"
TEMPDIR = os.path.join(REPO, "logs", "birth-gate-suite")

ENTRIES = (
    os.path.join("lobby", "server.py"),
    os.path.join("panel.py"),
    os.path.join("member", "member_page.py"),
    os.path.join("ledger", "ledger_page.py"),
    os.path.join("ugc", "ugc_page.py"),
    os.path.join("lobby", "checkout_demo.py"),
)

sys.path.insert(0, HERE)
import birth_gate  # noqa: E402
import launcher_mutex  # noqa: E402
import launcher_registry  # noqa: E402

RESULTS = []

HOLDER_SRC = '''import json
import os
import subprocess
import sys
import time

SANDBOX = sys.argv[1]
record = sys.argv[2]
mutex = sys.argv[3]
child = sys.argv[4]
stop_path = sys.argv[5]
sys.path.insert(0, SANDBOX)
import launcher_mutex
import launcher_registry

lane = launcher_mutex.acquire(mutex)
if not lane.get("held"):
    print("E_HOLDER_CLAIM", flush=True)
    sys.exit(9)
rec = {"pid": os.getpid(), "ts": launcher_registry.stamp(),
       "host": "127.0.0.1", "state": "starting", "hub_url": None,
       "ports": {}, "face_ports": {}}
if not launcher_registry.claim(record, rec)[0]:
    print("E_HOLDER_RECORD", flush=True)
    sys.exit(9)
print("READY %d" % os.getpid(), flush=True)
proc = None
if child != "-":
    proc = subprocess.Popen(json.loads(child),
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    print("CHILD %d" % proc.pid, flush=True)
while not os.path.exists(stop_path):
    time.sleep(0.05)
if proc is not None:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
launcher_registry.release(record)
launcher_mutex.release(lane.get("handle"))
print("STOPPED", flush=True)
'''


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def free_port():
    sock = socket.socket()
    try:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


def can_connect(port, timeout=0.35):
    try:
        with socket.create_connection(("127.0.0.1", int(port)),
                                      timeout=timeout):
            return True
    except OSError:
        return False


def wait_port(port, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if can_connect(port):
            return True
        time.sleep(0.1)
    return False


def face_argv(port):
    """The shipped lobby entry, with every socket pinned to a free port."""
    argv = [sys.executable, LOBBY, "--host", "127.0.0.1", "--port", str(port)]
    for flag in ("--city-http-port", "--gate-port", "--web-port", "--hub-port"):
        argv += [flag, str(free_port())]
    return argv


def write_holder():
    if not os.path.isdir(TEMPDIR):
        os.makedirs(TEMPDIR)
    path = os.path.join(TEMPDIR, "holder.py")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(HOLDER_SRC)
    return path


class Holder(object):
    """A real process holding the claim and naming itself in the record."""

    def __init__(self, record, mutex, child_argv=None, name="holder"):
        self.record = record
        self.mutex = mutex
        self.stop_path = os.path.join(TEMPDIR, name + ".stop")
        if os.path.exists(self.stop_path):
            os.remove(self.stop_path)
        self.argv = [sys.executable, write_holder(), HERE, record, mutex,
                     json.dumps(child_argv) if child_argv else "-",
                     self.stop_path]
        self.proc = None

    def start(self):
        if os.path.exists(self.record):
            os.remove(self.record)
        self.proc = subprocess.Popen(
            self.argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        deadline = time.time() + 30.0
        while time.time() < deadline:
            if os.path.exists(self.record):
                return True
            if self.proc.poll() is not None:
                return False
            time.sleep(0.05)
        return False

    def stop(self, timeout=20.0):
        with open(self.stop_path, "w", encoding="utf-8") as handle:
            handle.write("stop\n")
        deadline = time.time() + timeout
        while self.proc.poll() is None and time.time() < deadline:
            time.sleep(0.05)
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=10)


def run_face(argv, timeout=40):
    """Run a face to completion; returns (rc, stderr_text)."""
    proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
    return proc.returncode, err.decode("utf-8", "replace")


def main():
    if not os.path.isdir(TEMPDIR):
        os.makedirs(TEMPDIR)
    record = launcher_registry.default_path()
    mutex = launcher_mutex.name_for(record)
    busy = launcher_mutex.exists(mutex)
    if busy:
        report("AC-HSG0", True, "machine-busy: a launcher holds %s" % mutex)
        print("SUITE FAIL machine-busy")
        return 2

    # ---- AC-HSG1: the refusal is caused by a live holder ----------------
    bad = []
    port = free_port()
    holder = Holder(record, mutex, name="hsg1")
    if not holder.start():
        bad.append("holder-never-claimed")
    try:
        rc, err = run_face(face_argv(port))
        if rc != 3:
            bad.append("rc-%s" % rc)
        if birth_gate.REFUSED not in err:
            bad.append("code-not-named")
        if can_connect(port):
            bad.append("face-bound-anyway")
    finally:
        holder.stop()
    if os.path.exists(record):
        bad.append("record-not-released")
    if launcher_mutex.exists(mutex):
        bad.append("claim-not-released")
    # red control: the SAME command in the SAME world without a holder starts.
    proc = subprocess.Popen(face_argv(port), stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    try:
        if not wait_port(port, 40):
            bad.append("no-holder-world-did-not-start")
    finally:
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    report("AC-HSG1", bool(bad), ",".join(bad))

    # ---- AC-HSG2: the holder's own child is allowed ----------------------
    bad = []
    port = free_port()
    holder = Holder(record, mutex, child_argv=face_argv(port), name="hsg2")
    if not holder.start():
        bad.append("holder-never-claimed")
    try:
        if not wait_port(port, 40):
            bad.append("child-of-holder-refused")
    finally:
        holder.stop()
    if can_connect(port):
        bad.append("child-survived-holder-stop")
    report("AC-HSG2", bool(bad), ",".join(bad))

    # ---- AC-HSG3: a claim without a record is a named refusal -----------
    bad = []
    port = free_port()
    holder = Holder(record, mutex, name="hsg3")
    if not holder.start():
        bad.append("holder-never-claimed")
    try:
        if os.path.exists(record):
            os.remove(record)
        rc, err = run_face(face_argv(port))
        if rc != 3:
            bad.append("rc-%s" % rc)
        if birth_gate.UNIDENTIFIED not in err:
            bad.append("unidentified-not-named")
        if can_connect(port):
            bad.append("face-bound-without-record")
    finally:
        holder.stop()
    if launcher_mutex.exists(mutex):
        bad.append("claim-not-released")
    report("AC-HSG3", bool(bad), ",".join(bad))

    # ---- AC-HSG4: shipped entry wires + leaf shape ----------------------
    bad = []
    for rel in ENTRIES:
        path = os.path.join(HERE, rel)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        if "birth_gate.guard(" not in text:
            bad.append("unwired-" + rel.replace(os.sep, "/"))
        if "birth_gate" not in text:
            bad.append("no-import-" + rel.replace(os.sep, "/"))
    with open(LEAF, "rb") as handle:
        raw = handle.read()
    if raw[:3] == b"\xef\xbb\xbf":
        bad.append("leaf-bom")
    if b"\r\n" in raw:
        bad.append("leaf-crlf")
    try:
        text = raw.decode("utf-8")
        text.encode("ascii")
    except (UnicodeDecodeError, UnicodeEncodeError):
        bad.append("leaf-not-ascii")
        text = raw.decode("utf-8", "replace")
    if "subprocess" in text or "shell=True" in text:
        bad.append("leaf-shells")
    allowed = {"os", "sys", "launcher_mutex", "launcher_registry"}
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("import ") or
                stripped.startswith("from ")):
            continue
        root = stripped.split()[1].split(".")[0]
        if root not in allowed:
            bad.append("leaf-imports-" + root)
    with open(REGISTRY, encoding="utf-8") as handle:
        rows = handle.read().count('"' + ROW + '"')
    if rows != 1:
        bad.append("registry-rows-%d" % rows)
    with open(os.path.abspath(__file__), "rb") as handle:
        own = handle.read()
    if b"\r\n" in own or own[:3] == b"\xef\xbb\xbf":
        bad.append("suite-dialect")
    report("AC-HSG4", bool(bad), ",".join(bad))

    # ---- AC-HSG5: the judge is a read ----------------------------------
    bad = []
    if launcher_mutex.exists(mutex):
        bad.append("claim-left-behind")
    if os.path.exists(record):
        bad.append("record-left-behind")
    verdict = birth_gate.judge()
    if not verdict.get("allow"):
        bad.append("no-holder-world-refused")
    if verdict.get("reason") != "no-holder":
        bad.append("reason-" + str(verdict.get("reason")))
    if verdict.get("code") is not None:
        bad.append("code-on-allowed")
    forced = birth_gate.judge(ppid=-1)
    if not forced.get("allow"):
        bad.append("judge-invented-a-holder")
    if os.path.exists(record):
        bad.append("judge-wrote-a-record")
    if launcher_mutex.exists(mutex):
        bad.append("judge-created-a-claim")
    report("AC-HSG5", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
