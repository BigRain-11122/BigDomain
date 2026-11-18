"""Suite for the machine-wide launcher record (BigDomain R2939).

Five criteria AC-LND1..AC-LND5, pre-registered in the R2939 backlog row BEFORE
this file, src/sandbox/launcher_registry.py and its registry row existed.
AC-LND6 and AC-LND7 (R2974) were pre-registered in the R2974 backlog PIN row
BEFORE the pid_started wiring: a record is now judged as PID PLUS THE PROCESS
IT BELONGS TO, so a number the system recycled cannot resurrect a dead holder.

Nothing is read off a paragraph: a real launcher is held open in serve mode and
its record is compared with the report the SAME run wrote, a second door is
really started against that record and must be refused with zero children, and
two stale-record worlds are proven to START - one with a dead pid, one with a
live pid that serves nothing - while the same live pid pointed at a real
listener is proven to REFUSE. Every launcher in this file carries a private
--registry path, so the suite never competes for the machine claim.

Usage: python test_launcher_registry.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

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
LEAF = os.path.join(HERE, "launcher_registry.py")
REGISTRY = os.path.join(REPO, "src", "sandbox", "reconcile_all.py")
# The R2973 commit point: the bytes from BEFORE a record carried the creation
# stamp of the process that wrote it. Pinned as a constant because after this
# round's commit HEAD is already the new code (the R2959 lesson).
PRE_R2974_REV = "2d33f1ebc4ee30f93547db1ff0e88ddc631b7c58"

sys.path.insert(0, HERE)
import launcher_registry  # noqa: E402  (path wired above)

RESULTS = []

# The fields judge() answered BEFORE R2974. AC-LND7 compares these field by
# field on records an older launcher could have written, so "no decision this
# tree already made moved" is measured rather than claimed.
OLD_FIELDS = ("holder", "reason", "pid_alive", "hub_live", "pid", "hub_url")

# Loads one leaf by path and prints a narrow verdict per record, so the same
# driver can be pointed at the pinned bytes and at the working tree.
DRIVER = '''import importlib.util, json, sys

def load(path):
    spec = importlib.util.spec_from_file_location("leaf_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

leaf = load(sys.argv[1])
with open(sys.argv[2], encoding="utf-8") as handle:
    records = json.load(handle)
fields = %r
out = []
for rec in records:
    verdict = leaf.judge(rec)
    out.append(dict((name, verdict.get(name)) for name in fields))
sys.stdout.write(json.dumps(out, sort_keys=True))
''' % (OLD_FIELDS,)



def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


def can_connect(port, timeout=0.35):
    if not port:
        return False
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def fetch_json(url, timeout=15.0):
    with urllib.request.urlopen(url, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def wait_file(path, timeout=90.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as handle:
                    return json.load(handle)
            except (OSError, ValueError):
                pass
        time.sleep(0.1)
    return None


def dead_pid():
    """A process id that is really not alive any more."""
    proc = subprocess.Popen([sys.executable, "-c", "pass"],
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    proc.wait(timeout=20)
    return proc.pid


class Run(object):
    """One launcher invocation; serve mode is held open by a stop file."""

    def __init__(self, tmpdir, name, registry, extra=None, serve=True):
        self.dir = tmpdir
        self.report_path = os.path.join(tmpdir, name + ".json")
        self.stop_path = os.path.join(tmpdir, name + ".stop")
        argv = [sys.executable, MODULE, "--registry", registry,
                "--timeout", "40"]
        if serve:
            argv += ["--report-json", self.report_path,
                     "--stop-file", self.stop_path]
        else:
            argv += ["--check"]
        argv += list(extra or [])
        self.argv = argv
        self.proc = None
        self.report = None

    def start(self):
        for path in (self.report_path, self.stop_path):
            if os.path.exists(path):
                os.remove(path)
        self.proc = subprocess.Popen(
            self.argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        if self._serves():
            self.report = wait_file(self.report_path)
        return self.report

    def _serves(self):
        return "--stop-file" in self.argv

    def stop(self, timeout=25.0):
        if self._serves():
            with open(self.stop_path, "w", encoding="utf-8") as handle:
                handle.write("stop\n")
        deadline = time.time() + timeout
        while self.proc.poll() is None and time.time() < deadline:
            time.sleep(0.1)
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=10)
        return self.proc.returncode

    def stdout_json(self):
        raw = self.proc.stdout.read() if self.proc and self.proc.stdout else b""
        text = raw.decode("utf-8", "replace").strip()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except ValueError:
                    continue
        return {}


def main():
    tmpdir = os.path.join(REPO, "logs", "launcher-registry-suite")
    os.makedirs(tmpdir, exist_ok=True)
    registry = os.path.join(tmpdir, "machine-record.json")
    for path in (registry, registry + ".inspect"):
        if os.path.exists(path):
            os.remove(path)

    # ---- AC-LND1: the record IS this run, compared field by field ----------
    bad = []
    box = Run(tmpdir, "main", registry)
    rep = box.start() or {}
    rec = launcher_registry.read(registry) if rep else None
    if not rep:
        bad.append("launcher-never-reported")
    if not rec:
        bad.append("no-record-written")
    else:
        if int(rec.get("pid") or 0) != int(box.proc.pid):
            bad.append("pid-%s-not-%s" % (rec.get("pid"), box.proc.pid))
        if rec.get("state") != "serving":
            bad.append("state-" + str(rec.get("state")))
        if rec.get("host") != rep.get("host"):
            bad.append("host-mismatch")
        if rec.get("hub_url") != rep.get("hub_url"):
            bad.append("hub-url-mismatch")
        if rec.get("ports") != rep.get("ports"):
            bad.append("ports-mismatch")
        if rec.get("face_ports") != rep.get("face_ports"):
            bad.append("face-ports-mismatch")
        if not str(rec.get("ts") or "").startswith("20"):
            bad.append("ts-" + str(rec.get("ts")))
    if not bad and os.path.exists(registry):
        # ... and a clean exit removes exactly that record.
        code = box.stop()
        if code != 0:
            bad.append("exit-%s" % code)
        if os.path.exists(registry):
            bad.append("record-survived-clean-exit")
    else:
        box.stop()
    report("AC-LND1", bool(bad), ",".join(bad))

    # ---- AC-LND2: a second door is refused by name, with zero children -----
    bad = []
    box = Run(tmpdir, "holder", registry)
    rep = box.start() or {}
    if not rep or not os.path.exists(registry):
        bad.append("holder-never-served")
    else:
        second = Run(tmpdir, "second", registry,
                     extra=["--timeout", "6"], serve=False)
        second.start()
        code = second.stop()
        payload = second.stdout_json()
        if code != 2:
            bad.append("second-exit-%s" % code)
        errors = " ".join(payload.get("errors") or [])
        if launcher_registry.REFUSED not in errors:
            bad.append("no-named-refusal")
        if box.proc.pid and ("pid=%d" % box.proc.pid) not in errors:
            bad.append("refusal-does-not-name-holder")
        if payload.get("children") != []:
            bad.append("children-present")
        if payload.get("pids") != {}:
            bad.append("pids-present")
        if (payload.get("registry") or {}).get("claimed") is not False:
            bad.append("registry-read-claimed")
        try:
            still = fetch_json(rep["hub_url"] + "api/faces?probe=1")
        except (OSError, ValueError, urllib.error.URLError) as exc:
            still = {}
            bad.append("holder-unreadable-%s" % type(exc).__name__)
        if not still:
            bad.append("holder-hub-empty")
        if not (payload.get("registry") or {}).get("held_by"):
            bad.append("no-holder-record-in-report")
    if rep:
        box.stop()
    report("AC-LND2", bool(bad), ",".join(bad))

    # ---- AC-LND3 (red control): a DEAD pid is not a holder ------------------
    bad = []
    gone = dead_pid()
    stale = {"pid": gone, "ts": launcher_registry.stamp(),
             "host": "127.0.0.1", "state": "serving",
             "hub_url": "http://127.0.0.1:%d/hub/" % free_port(),
             "ports": {}, "face_ports": {}}
    with open(registry, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(stale, handle, sort_keys=True)
        handle.write("\n")
    box = Run(tmpdir, "after-dead", registry)
    rep = box.start() or {}
    rec = launcher_registry.read(registry) or {}
    if not rep:
        bad.append("never-started-over-dead-record")
    else:
        if rep.get("ok") is not True:
            bad.append("not-ok")
        if int(rec.get("pid") or 0) != int(box.proc.pid):
            bad.append("record-not-replaced")
        if int(rec.get("pid") or 0) == int(gone):
            bad.append("dead-pid-still-recorded")
    box.stop()
    report("AC-LND3", bool(bad), ",".join(bad))

    # ---- AC-LND4 (red control, both directions): aliveness is MEASURED ------
    bad = []
    closed = free_port()
    alive_dead_hub = {"pid": os.getpid(), "ts": launcher_registry.stamp(),
                      "host": "127.0.0.1", "state": "serving",
                      "hub_url": "http://127.0.0.1:%d/hub/" % closed,
                      "ports": {}, "face_ports": {}}
    with open(registry, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(alive_dead_hub, handle, sort_keys=True)
        handle.write("\n")
    allow = Run(tmpdir, "alive-dead-hub", registry,
                extra=["--timeout", "30"], serve=False)
    allow.start()
    if allow.stop(timeout=90) != 0:
        bad.append("refused-a-live-pid-that-serves-nothing")

    holder_sock = socket.socket()
    holder_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    holder_sock.bind(("127.0.0.1", 0))
    holder_sock.listen(4)
    try:
        live = {"pid": os.getpid(), "ts": launcher_registry.stamp(),
                "host": "127.0.0.1", "state": "serving",
                "hub_url": "http://127.0.0.1:%d/hub/"
                           % int(holder_sock.getsockname()[1]),
                "ports": {}, "face_ports": {}}
        with open(registry, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(live, handle, sort_keys=True)
            handle.write("\n")
        deny = Run(tmpdir, "alive-live-hub", registry,
                   extra=["--timeout", "6"], serve=False)
        deny.start()
        code = deny.stop()
        payload = deny.stdout_json()
        if code != 2:
            bad.append("allowed-a-live-pid-with-a-live-hub-%s" % code)
        joined = " ".join(payload.get("errors") or [])
        if launcher_registry.REFUSED not in joined:
            bad.append("live-hub-refusal-unnamed")
        if payload.get("children") != []:
            bad.append("live-hub-children-present")
    finally:
        holder_sock.close()
    report("AC-LND4", bool(bad), ",".join(bad))

    # ---- AC-LND5: exclusivity, no over-reach, module shape -----------------
    bad = []
    scratch = os.path.join(tmpdir, "claim.json")
    if os.path.exists(scratch):
        os.remove(scratch)
    mine = {"pid": os.getpid(), "ts": launcher_registry.stamp(),
            "host": "127.0.0.1", "state": "starting", "hub_url": None,
            "ports": {}, "face_ports": {}}
    first, _holder, _verdict = launcher_registry.claim(scratch, mine)
    if first is not True:
        bad.append("claim-on-empty-refused")
    second, holder, verdict = launcher_registry.claim(scratch, mine)
    if second is not False:
        bad.append("double-claim-allowed")
    if verdict.get("reason") != "still-starting":
        bad.append("double-claim-reason-" + str(verdict.get("reason")))
    if not holder or int(holder.get("pid") or 0) != os.getpid():
        bad.append("holder-not-returned")
    foreign = dict(mine, pid=os.getpid() + 1)
    launcher_registry.write_serving(scratch, foreign)
    if launcher_registry.release(scratch, os.getpid()) is not False:
        bad.append("released-a-foreign-record")
    if not os.path.exists(scratch):
        bad.append("foreign-record-deleted")
    launcher_registry.write_serving(scratch, mine)
    if launcher_registry.release(scratch) is not True:
        bad.append("own-record-not-released")
    if os.path.exists(scratch):
        bad.append("own-record-still-on-disk")

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
    if "shell=True" in text or "subprocess" in text:
        bad.append("leaf-shells")
    allowed = {"ctypes", "json", "os", "socket", "tempfile", "time",
               "urllib"}
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("import ") or
                stripped.startswith("from ")):
            continue
        root = stripped.split()[1].split(".")[0]
        if root not in allowed:
            bad.append("leaf-imports-" + root)
    default = launcher_registry.default_path()
    if not default.endswith(launcher_registry.FILENAME):
        bad.append("default-name-" + os.path.basename(default))
    if os.path.abspath(default).lower().startswith(
            os.path.abspath(REPO).lower()):
        bad.append("default-inside-repo")
    with open(MODULE, encoding="utf-8") as handle:
        launcher_text = handle.read()
    if '"--registry"' not in launcher_text:
        bad.append("launcher-has-no-registry-flag")
    with open(REGISTRY, encoding="utf-8") as handle:
        registry_text = handle.read()
    if registry_text.count('"launcher-registry"') != 1:
        bad.append("registry-rows-%d"
                   % registry_text.count('"launcher-registry"'))
    report("AC-LND5", bool(bad), ",".join(bad))

    # ---- AC-LND6 (R2974): a record is a pid PLUS the process it belongs to --
    bad = []
    mine_started = launcher_registry.process_started(os.getpid())
    if not mine_started:
        bad.append("own-stamp-unreadable")
    honest = {"pid": os.getpid(), "pid_started": mine_started,
              "ts": launcher_registry.stamp(), "host": "127.0.0.1",
              "state": "starting", "hub_url": None, "ports": {},
              "face_ports": {}}
    held = launcher_registry.judge(honest)
    if not held["holder"] or held["reason"] != "still-starting":
        bad.append("honest-record-%s/%s" % (held["holder"], held["reason"]))
    if held.get("trust") != "record-pid-start":
        bad.append("trust-" + str(held.get("trust")))
    if held.get("pid_started_ok") is not True:
        bad.append("stamp-check-" + str(held.get("pid_started_ok")))
    # THE REWRITE: pid and aliveness untouched by the third party, only the
    # stamp names a different process - exactly the shape a recycled pid leaves.
    forged = dict(honest, pid_started=int(mine_started) + 1)
    reused = launcher_registry.judge(forged)
    if reused["holder"]:
        bad.append("rewritten-record-still-held")
    if reused["reason"] != "pid-reused":
        bad.append("rewrite-reason-" + str(reused["reason"]))
    if reused["pid_alive"] is not True:
        bad.append("aliveness-not-measured")
    if reused.get("pid_started_ok") is not False:
        bad.append("rewrite-stamp-check-" + str(reused.get("pid_started_ok")))
    # an older launcher's record carries no stamp: the old judgement is kept.
    older = dict(honest)
    older.pop("pid_started")
    legacy = launcher_registry.judge(older)
    if not legacy["holder"] or legacy.get("trust") != "record-pid":
        bad.append("stampless-%s/%s" % (legacy["holder"],
                                        legacy.get("trust")))
    if legacy.get("pid_started_ok") is not None:
        bad.append("stampless-claims-a-check")
    # a stamp that cannot be measured never demotes a live pid.
    real_started = launcher_registry.process_started
    launcher_registry.process_started = lambda pid: None
    try:
        blind = launcher_registry.judge(honest)
    finally:
        launcher_registry.process_started = real_started
    if not blind["holder"]:
        bad.append("unmeasurable-stamp-demoted")
    # a dead pid still loses to the older refusal, whatever stamp it claims.
    gone = dead_pid()
    stale_stamped = launcher_registry.judge(
        {"pid": gone, "pid_started": mine_started, "state": "starting"})
    if stale_stamped["holder"] or stale_stamped["reason"] != "pid-dead":
        bad.append("dead-%s/%s" % (stale_stamped["holder"],
                                   stale_stamped["reason"]))
    report("AC-LND6", bool(bad), ",".join(bad))

    # ---- AC-LND7 (R2974): the shipped path writes it, and no decision this
    #      tree already made moves (measured against the pinned bytes) --------
    bad = []
    if os.path.exists(registry):
        os.remove(registry)
    box = Run(tmpdir, "stamped", registry)
    rep = box.start() or {}
    rec = launcher_registry.read(registry) or {}
    wrote_stamp = rec.get("pid_started")
    true_stamp = launcher_registry.process_started(box.proc.pid) if rep else None
    if not rep:
        bad.append("launcher-never-reported")
    if wrote_stamp is None:
        bad.append("record-carries-no-stamp")
    elif true_stamp is None or int(wrote_stamp) != int(true_stamp):
        bad.append("stamp-%s-not-%s" % (wrote_stamp, true_stamp))
    if rep:
        second = Run(tmpdir, "stamped-second", registry,
                     extra=["--timeout", "6"], serve=False)
        second.start()
        code = second.stop()
        payload = second.stdout_json()
        errors = " ".join(payload.get("errors") or [])
        if code != 2:
            bad.append("second-exit-%s" % code)
        if launcher_registry.REFUSED not in errors:
            bad.append("no-named-refusal-against-stamped-record")
        if box.proc.pid and ("pid=%d" % box.proc.pid) not in errors:
            bad.append("refusal-does-not-name-holder")
    box.stop()
    # the pinned bytes and the working tree, one driver, the same records.
    holder_sock = socket.socket()
    holder_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    holder_sock.bind(("127.0.0.1", 0))
    holder_sock.listen(4)
    live_port = int(holder_sock.getsockname()[1])
    own = launcher_registry.process_started(os.getpid())
    records = [
        # three shapes an older launcher could leave behind
        {"pid": dead_pid(), "ts": launcher_registry.stamp(),
         "host": "127.0.0.1", "state": "serving",
         "hub_url": "http://127.0.0.1:%d/hub/" % free_port(), "ports": {},
         "face_ports": {}},
        {"pid": os.getpid(), "ts": launcher_registry.stamp(),
         "host": "127.0.0.1", "state": "serving",
         "hub_url": "http://127.0.0.1:%d/hub/" % free_port(), "ports": {},
         "face_ports": {}},
        {"pid": os.getpid(), "ts": launcher_registry.stamp(),
         "host": "127.0.0.1", "state": "serving",
         "hub_url": "http://127.0.0.1:%d/hub/" % live_port, "ports": {},
         "face_ports": {}},
        # the honest stamped record and the same record rewritten
        {"pid": os.getpid(), "pid_started": own,
         "ts": launcher_registry.stamp(), "host": "127.0.0.1",
         "state": "starting", "hub_url": None, "ports": {}, "face_ports": {}},
        {"pid": os.getpid(), "pid_started": (own or 0) + 1,
         "ts": launcher_registry.stamp(), "host": "127.0.0.1",
         "state": "starting", "hub_url": None, "ports": {}, "face_ports": {}},
    ]
    try:
        driver = os.path.join(tmpdir, "judge-driver.py")
        payload_path = os.path.join(tmpdir, "judge-records.json")
        with open(driver, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(DRIVER)
        with open(payload_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(records, handle, sort_keys=True)
            handle.write("\n")
        old = subprocess.run(["git", "show", PRE_R2974_REV
                              + ":src/sandbox/launcher_registry.py"],
                             cwd=REPO, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        if old.returncode != 0 or not old.stdout:
            bad.append("no-old-bytes")
        else:
            old_leaf = os.path.join(tmpdir, "launcher_registry_prer2974.py")
            with open(old_leaf, "wb") as handle:
                handle.write(old.stdout)
            before = subprocess.run(
                [sys.executable, driver, old_leaf, payload_path],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=120)
            after = subprocess.run(
                [sys.executable, driver, LEAF, payload_path],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=120)
            if before.returncode != 0 or after.returncode != 0:
                bad.append("driver-rc-%d/%d" % (before.returncode,
                                                after.returncode))
            else:
                old_rows = json.loads(before.stdout.decode("utf-8"))
                new_rows = json.loads(after.stdout.decode("utf-8"))
                # the three older shapes plus the honest stamped record keep
                # every field the old judge answered, on all four.
                moved = [i for i in (0, 1, 2, 3) if old_rows[i] != new_rows[i]]
                if moved:
                    bad.append("old-decisions-moved-%s" % moved)
                # the rewritten record is the one that MOVED, and only it.
                if old_rows[4]["holder"] is not True:
                    bad.append("old-held-the-rewrite-anyway")
                if new_rows[4]["holder"] is not False:
                    bad.append("new-held-the-rewrite")
                if new_rows[4]["reason"] != "pid-reused":
                    bad.append("new-rewrite-reason-" + str(new_rows[4]["reason"]))
            os.remove(old_leaf)
    finally:
        holder_sock.close()
    report("AC-LND7", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
