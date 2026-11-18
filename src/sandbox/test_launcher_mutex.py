"""Suite for the kernel claim that replaced the file as the launcher gate.

Five criteria AC-LMX1..AC-LMX5, pre-registered in the R2940 backlog row BEFORE
this file, src/sandbox/launcher_mutex.py and its registry row existed.

Nothing here is read off a paragraph: a real launcher is held open in serve
mode, a real second launcher is started against it with a DIFFERENT and EMPTY
record path, the record file is deleted from the outside to prove the refusal
survived that, and the same deleted-record world with a `--no-mutex` holder is
proven to START so the hole is measured rather than assumed. The kernel's own
release-on-death is proven by killing a child that holds the claim.

Usage: python test_launcher_mutex.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MODULE = os.path.join(HERE, "start_all.py")
LEAF = os.path.join(HERE, "launcher_mutex.py")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
ROW = "launcher-mutex"

sys.path.insert(0, HERE)
import launcher_mutex  # noqa: E402  (path wired above)

RESULTS = []


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


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


class Run(object):
    """One launcher invocation; serve mode is held open by a stop file."""

    def __init__(self, tmpdir, name, registry, mutex, extra=None, serve=True):
        self.report_path = os.path.join(tmpdir, name + ".json")
        self.stop_path = os.path.join(tmpdir, name + ".stop")
        argv = [sys.executable, MODULE, "--registry", registry,
                "--timeout", "40"]
        if mutex:
            argv += ["--mutex-name", mutex]
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
        if "--stop-file" in self.argv:
            self.report = wait_file(self.report_path)
        return self.report

    def stop(self, timeout=40.0):
        if "--stop-file" in self.argv and self.proc.poll() is None:
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


def refusal_of(payload):
    return " ".join(payload.get("errors") or [])


def main():
    tmpdir = os.path.join(REPO, "logs", "launcher-mutex-suite")
    os.makedirs(tmpdir, exist_ok=True)
    held_record = os.path.join(tmpdir, "held.json")
    other_record = os.path.join(tmpdir, "other.json")
    for path in (held_record, other_record):
        if os.path.exists(path):
            os.remove(path)
    shared = launcher_mutex.NAME + "-suite-a"
    hole = launcher_mutex.NAME + "-suite-b"

    # ---- AC-LMX1: the mutex is the holder, and the FILE is not ------------
    bad = []
    box = Run(tmpdir, "lnd-holder", held_record, shared)
    held_report = box.start() or {}
    if not held_report:
        bad.append("holder-never-served")
    second = Run(tmpdir, "lnd-second", other_record, shared, serve=False)
    second.start()
    refused_code = second.stop()
    refused = second.stdout_json()
    if refused_code != 2:
        bad.append("second-exit-%s" % refused_code)
    joined = refusal_of(refused)
    if launcher_mutex.REFUSED not in joined:
        bad.append("no-named-refusal")
    if "source=mutex" not in joined:
        bad.append("refusal-does-not-name-the-mutex")
    if refused.get("children") != []:
        bad.append("children-present")
    if refused.get("pids") != {}:
        bad.append("pids-present")
    if (refused.get("mutex") or {}).get("already") is not True:
        bad.append("mutex-not-reported-held")
    if os.path.exists(other_record):
        bad.append("refused-door-wrote-a-record")
    if (held_report.get("mutex") or {}).get("held") is not True:
        bad.append("holder-report-says-mutex-not-held")
    if (held_report.get("mutex") or {}).get("name") != shared:
        bad.append("holder-report-name-"
                   + str((held_report.get("mutex") or {}).get("name")))
    box.stop()
    # ... and the SAME second invocation must start once the holder is gone.
    again = Run(tmpdir, "lnd-second-again", other_record, shared, serve=False)
    again.start()
    allowed_code = again.stop(timeout=90)
    if allowed_code != 0:
        bad.append("still-refused-after-holder-left-%s" % allowed_code)
    report("AC-LMX1", bool(bad), ",".join(bad))

    # ---- AC-LMX2: the record deleted while serving (red control both ways) -
    bad = []
    box = Run(tmpdir, "del-holder", held_record, shared)
    rep = box.start() or {}
    if not rep:
        bad.append("holder-never-served")
    if not os.path.exists(held_record):
        bad.append("no-record-to-delete")
    else:
        os.remove(held_record)
    door = Run(tmpdir, "del-second", held_record, shared, serve=False)
    door.start()
    code = door.stop()
    payload = door.stdout_json()
    if code != 2:
        bad.append("deleted-record-admitted-a-second-door-%s" % code)
    if launcher_mutex.REFUSED not in refusal_of(payload):
        bad.append("deleted-record-refusal-unnamed")
    if payload.get("children") != []:
        bad.append("deleted-record-children-present")
    if os.path.exists(held_record):
        bad.append("second-door-recreated-the-record")
    box.stop()

    # RED CONTROL: the same deleted-record world with --no-mutex must START,
    # which is what makes the arm above able to see the defect at all.
    loose = Run(tmpdir, "loose-holder", held_record, hole,
                extra=["--no-mutex"])
    loose_rep = loose.start() or {}
    if not loose_rep:
        bad.append("loose-holder-never-served")
    if os.path.exists(held_record):
        os.remove(held_record)
    open_door = Run(tmpdir, "loose-second", held_record, hole, serve=False)
    open_door.start()
    open_code = open_door.stop(timeout=90)
    if open_code != 0:
        bad.append("red-control-was-refused-too-%s" % open_code)
    loose.stop()
    report("AC-LMX2", bool(bad), ",".join(bad))

    # ---- AC-LMX3: the kernel releases the claim on a HARD death ------------
    bad = []
    name = launcher_mutex.NAME + "-suite-c"
    script = (
        "import sys; sys.path.insert(0, %r); import launcher_mutex as m; "
        "r = m.acquire(%r); print('LANE', r['held'], r['already'], "
        "flush=True); sys.stdin.read()" % (HERE, name))
    child = subprocess.Popen([sys.executable, "-c", script],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True)
    line = ""
    try:
        line = child.stdout.readline().strip()
        if line != "LANE True False":
            bad.append("child-never-took-the-claim-" + (line or "-"))
        if not launcher_mutex.exists(name):
            bad.append("exists-false-while-a-child-holds-it")
        lane = launcher_mutex.acquire(name)
        if lane.get("held") or lane.get("already") is not True:
            bad.append("parent-took-a-held-claim")
        if not launcher_mutex.exists(name):
            bad.append("exists-false-after-refusal")
        child.kill()
        child.wait(timeout=20)
        time.sleep(0.3)
        if launcher_mutex.exists(name):
            bad.append("claim-survived-a-hard-kill")
        after = launcher_mutex.acquire(name)
        if after.get("held") is not True:
            bad.append("claim-not-reclaimable-after-death")
        launcher_mutex.release(after.get("handle"))
        if launcher_mutex.exists(name):
            bad.append("claim-survived-release")
    finally:
        if child.poll() is None:
            child.kill()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
    report("AC-LMX3", bool(bad), ",".join(bad))

    # ---- AC-LMX4: no over-reach, stable names, honest report --------------
    bad = []
    a = launcher_mutex.name_for(os.path.join(tmpdir, "one.json"))
    b = launcher_mutex.name_for(os.path.join(tmpdir, "two.json"))
    a_again = launcher_mutex.name_for(os.path.join(tmpdir, "ONE.json"))
    if a == b:
        bad.append("two-paths-share-one-name")
    if a != a_again:
        bad.append("one-path-has-two-names")
    if not (a.startswith("Local\\") and launcher_mutex.NAME.startswith("Local\\")):
        bad.append("not-per-user-session")
    if "Global\\" in a:
        bad.append("global-namespace")
    name = launcher_mutex.NAME + "-suite-d"
    if launcher_mutex.exists(name):
        bad.append("exists-true-before-any-claim")
    first = launcher_mutex.acquire(name)
    if first.get("held") is not True:
        bad.append("first-claim-refused")
    if not launcher_mutex.exists(name):
        bad.append("exists-false-after-claim")
    if launcher_mutex.acquire(name).get("already") is not True:
        bad.append("second-claim-in-one-process-allowed")
    launcher_mutex.release(first.get("handle"))
    if launcher_mutex.exists(name):
        bad.append("exists-true-after-release")
    derived = launcher_mutex.name_for(os.path.join(tmpdir, "name-face.json"))
    with open(MODULE, encoding="utf-8") as handle:
        text = handle.read()
    if "launcher_mutex.name_for(registry_path)" not in text:
        bad.append("launcher-does-not-derive-the-name")
    if derived == shared:
        bad.append("derived-name-collides-with-the-suite-name")
    report("AC-LMX4", bool(bad), ",".join(bad))

    # ---- AC-LMX5: module shape + wiring ----------------------------------
    bad = []
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
    allowed = {"ctypes", "hashlib", "os", "sys"}
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("import ") or
                stripped.startswith("from ")):
            continue
        root = stripped.split()[1].split(".")[0]
        if root not in allowed:
            bad.append("leaf-imports-" + root)
    with open(MODULE, encoding="utf-8") as handle:
        launcher_text = handle.read()
    for flag in ('"--mutex-name"', '"--no-mutex"', "import launcher_mutex"):
        if flag not in launcher_text:
            bad.append("launcher-missing-" + flag)
    with open(REGISTRY, encoding="utf-8") as handle:
        rows = handle.read().count('"' + ROW + '"')
    if rows != 1:
        bad.append("registry-rows-%d" % rows)
    with open(os.path.join(HERE, "test_launcher_mutex.py"), "rb") as handle:
        own = handle.read()
    if b"\r\n" in own or own[:3] == b"\xef\xbb\xbf":
        bad.append("suite-dialect")
    report("AC-LMX5", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
