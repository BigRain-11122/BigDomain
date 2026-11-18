"""Suite for the birth-site gate that closes R2940's measured hand-start hole.

Eleven criteria AC-HSG1..AC-HSG11. AC-HSG1..AC-HSG5 were pre-registered in
src/os/backlog.md BEFORE this file, src/sandbox/birth_gate.py and the six entry
wires existed; AC-HSG6..AC-HSG8 were pinned in the same board in the R2942
window before the gate moved into the nine shipped starters; AC-HSG9 and
AC-HSG10 were pinned there in R2947 before the trust surface was published.

AC-HSG9 and AC-HSG10 are not defences, they are measurements of the boundary
R2947 decided: the pid this gate compares against is read from a per-user
WRITABLE record, so a process that rewrites that record to name its own parent
is let through - driven here in both directions on the same shipped command.
What the file cannot do is grant on its own: with no kernel claim held, judge()
allows whatever the record says, because the gate is the mutex and the record
is detail.

Nothing here is read off a paragraph. A real holder process takes the kernel
claim and writes the detail record naming ITSELF, and then the suite starts the
SHIPPED lobby server directly - beside that holder - and requires the named
refusal with nothing listening. The same command in the same world without the
holder must come up, so the refusal is caused by the holder. The legitimate
path is proven by the same holder starting the face as ITS OWN CHILD.

Usage: python test_birth_gate.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import inspect
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LOBBY = os.path.join(HERE, "lobby", "server.py")
PANEL = os.path.join(HERE, "panel.py")
CHECKOUT = os.path.join(HERE, "lobby", "checkout_demo.py")
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
for _sub in ("lobby", "ledger", "ugc", "member"):
    _dir = os.path.join(HERE, _sub)
    if _dir not in sys.path:
        sys.path.append(_dir)
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


STARTERS = (
    (os.path.join("lobby", "city.py"), "start_city_http"),
    (os.path.join("lobby", "hub_page.py"), "start_hub_http"),
    (os.path.join("lobby", "lobby_page.py"), "start_lobby_http"),
    (os.path.join("lobby", "gate_page.py"), "start_gate_http"),
    (os.path.join("ugc", "ugc_page.py"), "start_ugc_http"),
    (os.path.join("ledger", "ledger_page.py"), "start_server"),
    (os.path.join("lobby", "checkout_demo.py"), "start_server"),
    ("panel.py", "start_panel"),
    (os.path.join("member", "member_page.py"), "make_server"),
)


def function_source(path, name):
    """The text of one top-level function, by indentation; None if absent."""
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    head = "def %s(" % name
    start = None
    for idx, line in enumerate(lines):
        if line.startswith(head):
            start = idx
            break
    if start is None:
        return None
    body = [lines[start]]
    for line in lines[start + 1:]:
        if line.strip() and not line.startswith((" ", "\t")):
            break
        body.append(line)
    return "\n".join(body)


def embedded_start(port, captured):
    """Call the shipped ledger starter IN THIS PROCESS; never a subprocess.

    Returns (exit_code_or_None, server_or_None, exception_or_None).
    """
    import contextlib
    import ledger_page

    with contextlib.redirect_stderr(captured):
        try:
            return None, ledger_page.start_server("127.0.0.1", port, None), None
        except SystemExit as exc:
            return exc.code, None, None
        except BaseException as exc:  # noqa: BLE001 - reported, not swallowed
            return None, None, exc


def close_server(server):
    try:
        server.shutdown()
    except Exception:
        pass
    try:
        server.server_close()
    except Exception:
        pass


def face_argv(port):
    """The shipped lobby entry, with every socket pinned to a free port."""
    argv = [sys.executable, LOBBY, "--host", "127.0.0.1", "--port", str(port)]
    for flag in ("--city-http-port", "--gate-port", "--web-port", "--hub-port"):
        argv += [flag, str(free_port())]
    return argv


def checkout_argv(port):
    """The shipped checkout entry - the exact shape the panel spawns."""
    return [sys.executable, CHECKOUT, "--host", "127.0.0.1",
            "--port", str(port)]


def post_json(port, path, payload, timeout=20.0):
    """(status, body) for one panel route; a refusal is a result, not a raise."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:%d%s" % (int(port), path), data=data, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, json.loads(res.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body or "{}")
        except ValueError:
            return exc.code, {"raw": body}


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

    # ---- AC-HSG6: the EMBEDDED path is refused too ----------------------
    # R2941's gate sat in main(), so a harness calling the starter directly
    # never reached it. This calls the shipped starter IN THIS PROCESS.
    bad = []
    port = free_port()
    holder = Holder(record, mutex, name="hsg6")
    if not holder.start():
        bad.append("holder-never-claimed")
    captured = io.StringIO()
    code, server, raised = embedded_start(port, captured)
    try:
        if code != 3:
            bad.append("rc-%s" % code)
        if raised:
            bad.append("raised-" + raised.__class__.__name__)
        if birth_gate.REFUSED not in captured.getvalue():
            bad.append("code-not-named")
        if can_connect(port):
            bad.append("embedded-face-bound-anyway")
        if server is not None:
            bad.append("embedded-server-returned")
    finally:
        if server is not None:
            close_server(server)
        holder.stop()
    # red control: the SAME call in the SAME world after the holder leaves.
    code, server, raised = embedded_start(port, io.StringIO())
    try:
        if code is not None or raised is not None:
            bad.append("no-holder-embedded-refused")
        if server is None:
            bad.append("no-holder-embedded-no-server")
        elif not wait_port(int(server.server_address[1]), 10):
            bad.append("no-holder-embedded-port-dead")
    finally:
        if server is not None:
            close_server(server)
    report("AC-HSG6", bool(bad), ",".join(bad))

    # ---- AC-HSG7: every shipped starter routes through the gate ---------
    bad = []
    for rel, func_name in STARTERS:
        flag = rel.replace(os.sep, "/")
        source = function_source(os.path.join(HERE, rel), func_name)
        if source is None:
            bad.append("missing-%s:%s" % (flag, func_name))
            continue
        if "birth_gate.checked_server(" not in source:
            bad.append("ungated-%s:%s" % (flag, func_name))
    report("AC-HSG7", bool(bad), ",".join(bad))

    # ---- AC-HSG8: the judge runs BEFORE the factory (both ways) ---------
    bad = []
    port = free_port()
    holder = Holder(record, mutex, name="hsg8")
    if not holder.start():
        bad.append("holder-never-claimed")
    calls = []

    def canary():
        calls.append(1)
        raise RuntimeError("FACTORY-RAN")

    captured = io.StringIO()
    try:
        birth_gate.checked_server(canary)
        bad.append("no-exit-with-holder")
    except SystemExit as exc:
        if exc.code != 3:
            bad.append("exit-%s" % exc.code)
    except RuntimeError:
        bad.append("factory-ran-before-judge")
    finally:
        if calls:
            bad.append("factory-called-with-holder")
        holder.stop()
    # red control: with no holder the factory IS called, so the arm is not
    # busy refusing everything.
    calls[:] = []
    try:
        birth_gate.checked_server(canary)
        bad.append("no-error-without-holder")
    except RuntimeError:
        pass
    except SystemExit as exc:
        bad.append("refused-without-holder-%s" % exc.code)
    finally:
        if len(calls) != 1:
            bad.append("factory-calls-%d" % len(calls))
    report("AC-HSG8", bool(bad), ",".join(bad))

    # ---- AC-HSG9: the writable record IS the identity, measured ----------
    # This arm does not defend the gate, it sizes it: the pid the gate trusts
    # lives in a per-user writable file, so a process that rewrites that file
    # to name its own parent is let through. Both directions run here, on the
    # SAME shipped command in the SAME world, with only that one field moved.
    bad = []
    port = free_port()
    holder = Holder(record, mutex, name="hsg9")
    if not holder.start():
        bad.append("holder-never-claimed")
    holder_pid = None
    try:
        original = launcher_registry.read(record) or {}
        holder_pid = original.get("pid")
        if not holder_pid:
            bad.append("holder-record-has-no-pid")
        # forgery: name THIS process, which is the face's real parent.
        forged = dict(original)
        forged["pid"] = os.getpid()
        launcher_registry.write_serving(record, forged)
        proc = subprocess.Popen(face_argv(port), stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        try:
            if not wait_port(port, 40):
                bad.append("forged-record-did-not-open-the-door")
        finally:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        # red control: put the TRUE holder back; same command, same world.
        launcher_registry.write_serving(record, original)
        rc, err = run_face(face_argv(port))
        if rc != 3:
            bad.append("true-record-rc-%s" % rc)
        if birth_gate.REFUSED not in err:
            bad.append("true-record-code-not-named")
        if can_connect(port):
            bad.append("true-record-bound-anyway")
    finally:
        holder.stop()
        if os.path.exists(record):
            try:
                os.remove(record)
            except OSError:
                pass
    report("AC-HSG9", bool(bad), ",".join(bad))

    # ---- AC-HSG10: the file alone grants nothing; trust is published -----
    bad = []
    private_mutex = "Local\\bigdomain-hsg10-%d" % os.getpid()
    nowhere = os.path.join(TEMPDIR, "hsg10-record.json")
    launcher_registry.write_serving(nowhere, {"pid": os.getpid(),
                                              "state": "starting"})
    verdict = birth_gate.judge(record_path=nowhere, mutex_name=private_mutex)
    if not verdict.get("allow"):
        bad.append("record-alone-refused")
    if verdict.get("reason") != "no-holder":
        bad.append("reason-%s" % verdict.get("reason"))
    if verdict.get("trust") != birth_gate.TRUST_NONE:
        bad.append("trust-%s" % verdict.get("trust"))
    # and when the kernel claim IS held, the trust surface says so and the
    # named refusal carries it into evidence.
    holder = Holder(record, mutex, name="hsg10")
    if not holder.start():
        bad.append("holder-never-claimed")
    try:
        held = birth_gate.judge(record_path=record, mutex_name=mutex,
                                ppid=1)
        if held.get("trust") != birth_gate.TRUST_RECORD_PID:
            bad.append("held-trust-%s" % held.get("trust"))
        if held.get("allow"):
            bad.append("held-allowed")
        captured = io.StringIO()
        try:
            birth_gate.guard(record_path=record, mutex_name=mutex, stream=captured)
            bad.append("guard-did-not-exit")
        except SystemExit as exc:
            if exc.code != 3:
                bad.append("guard-exit-%s" % exc.code)
        if "trust=" not in captured.getvalue():
            bad.append("refusal-line-hides-trust")
    finally:
        holder.stop()
        if os.path.exists(record):
            try:
                os.remove(record)
            except OSError:
                pass
        if os.path.exists(nowhere):
            try:
                os.remove(nowhere)
            except OSError:
                pass
    report("AC-HSG10", bool(bad), ",".join(bad))

    # ---- AC-HSG11: launcher -> panel -> face, on the SHIPPED panel --------
    # R2948: the grandchild path had never been driven through the shipped
    # panel. The holder starts the real panel as its OWN child (no
    # --owned-face, so the panel believes it may start faces), the panel then
    # spawns the shipped checkout module - and that child is a grandchild of
    # the claim holder, so the birth gate refuses it by name. The panel reports
    # the child's own words because R2948 made it keep the child's stderr; the
    # control runs the SAME vector one layer up, where the holder is the parent
    # and the face therefore comes up.
    bad = []
    panel_port = free_port()
    # R2949: the child log is per PANEL now, and its path is published in the
    # start answer, so this leg deletes the path it was told about instead of
    # guessing a machine-wide name (the old pre-clean existed only because the
    # name was shared, and after R2949 a guessed name would leave the real file
    # behind on every run).
    child_log = None
    holder = Holder(record, mutex, name="hsg11",
                    child_argv=[sys.executable, PANEL, "--host", "127.0.0.1",
                                "--port", str(panel_port)])
    if not holder.start():
        bad.append("holder-never-claimed")
    try:
        if not wait_port(panel_port, 40):
            bad.append("panel-never-came-up")
        else:
            code, obj = post_json(panel_port, "/panel/api/start",
                                  {"face": "checkout"})
            child_log = obj.get("child_log_path")
            if code != 500:
                bad.append("start-code-%s" % code)
            if obj.get("error") != "E_PANEL_NOT_UP":
                bad.append("start-err-%s" % obj.get("error"))
            if birth_gate.REFUSED not in (obj.get("child_log") or ""):
                bad.append("child-log-hides-code")
            if obj.get("child_exit") != 3:
                bad.append("child-exit-%s" % obj.get("child_exit"))
            if not child_log:
                bad.append("child-log-path-unpublished")
            if can_connect(int(obj.get("port") or 0)):
                bad.append("grandchild-bound-anyway")
    finally:
        holder.stop()
        if os.path.exists(record):
            try:
                os.remove(record)
            except OSError:
                pass
        if child_log and os.path.exists(child_log):
            try:
                os.remove(child_log)
            except OSError:
                pass
    # control: the same vector, started by the HOLDER itself, must come up.
    port = free_port()
    holder = Holder(record, mutex, name="hsg11c",
                    child_argv=checkout_argv(port))
    if not holder.start():
        bad.append("control-holder-never-claimed")
    try:
        if not wait_port(port, 40):
            bad.append("holder-child-never-came-up")
    finally:
        holder.stop()
        if os.path.exists(record):
            try:
                os.remove(record)
            except OSError:
                pass
    report("AC-HSG11", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
