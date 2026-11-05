"""Suite for the one-command sandbox launcher (BigDomain R2477).

Six criteria AC-STL1..AC-STL6 pre-registered in the R2477 backlog row BEFORE
this file, src/sandbox/start_all.py and its registry row existed.

Nothing here is read off a canned string: the launcher is really started in
serve mode, the report it writes is compared against the hub's own probe
answer at call time, an independent TCP connect checks every published port,
and the teardown leg proves the ports are gone after the stop file appears.

Usage: python test_start_all.py
Exit: 0 = SUITE PASS 6/6, 2 = FAIL.
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
REGISTRY = os.path.join(REPO, "src", "sandbox", "reconcile_all.py")
HUB_HTML = os.path.join(HERE, "lobby", "hub.html")
HUB_MODULE = os.path.join(HERE, "lobby", "hub_page.py")

FACE_KEYS = ("lobby", "city", "checkout", "gate", "ledger", "ugc")
SHIPPED = {
    "lobby": os.path.join(HERE, "lobby", "server.py"),
    "checkout": os.path.join(HERE, "lobby", "checkout_demo.py"),
    "ledger": os.path.join(HERE, "ledger", "ledger_page.py"),
    "ugc": os.path.join(HERE, "ugc", "ugc_page.py"),
}

RESULTS = []


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % (name, "FAIL" if bad else "PASS",
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
        time.sleep(0.15)
    return None


class Sandbox(object):
    """One live launcher run held open by a stop file, torn down on exit."""

    def __init__(self, tmpdir, ws_port=None, hub_port=None):
        self.dir = tmpdir
        self.report_path = os.path.join(tmpdir, "report.json")
        self.stop_path = os.path.join(tmpdir, "stop.flag")
        argv = [sys.executable, MODULE, "--timeout", "40",
                "--report-json", self.report_path,
                "--stop-file", self.stop_path]
        if ws_port:
            argv += ["--ws-port", str(ws_port)]
        if hub_port:
            argv += ["--hub-port", str(hub_port)]
        self.argv = argv
        self.proc = None
        self.report = None

    def start(self):
        # A report left by an earlier run would be read before this run's own
        # launcher writes one, so both control files are cleared first.
        for path in (self.report_path, self.stop_path):
            if os.path.exists(path):
                os.remove(path)
        self.proc = subprocess.Popen(
            self.argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.report = wait_file(self.report_path)
        return self.report

    def stop(self, timeout=20.0):
        with open(self.stop_path, "w", encoding="utf-8") as handle:
            handle.write("stop\n")
        deadline = time.time() + timeout
        while self.proc.poll() is None and time.time() < deadline:
            time.sleep(0.1)
        if self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=5)
        return self.proc.returncode


def main():
    tmpdir = os.path.join(REPO, "logs", "start-all-suite")
    os.makedirs(tmpdir, exist_ok=True)
    ws_port = free_port()
    hub_port = free_port()

    box = Sandbox(tmpdir, ws_port=ws_port, hub_port=hub_port)
    rep = box.start()
    if rep is None:
        report("AC-STL1", True, "launcher never wrote a report")
        report("AC-STL2", True, "no report")
        report("AC-STL3", True, "no report")
        report("AC-STL4", True, "no report")
        report("AC-STL5", True, "no report")
        report("AC-STL6", True, "no report")
        box.stop()
        return 2
    ports = rep.get("ports") or {}
    face_ports = rep.get("face_ports") or {}
    faces = rep.get("faces") or {}

    # AC-STL1: six faces, and each URL equals what the hub publishes right now.
    bad = sorted(set(faces)) != sorted(FACE_KEYS)
    detail = "" if not bad else "faces " + ",".join(sorted(faces))
    if not bad:
        try:
            live_map = fetch_json(rep["hub_url"] + "api/faces?probe=1")
        except (OSError, ValueError, urllib.error.URLError) as exc:
            live_map = {}
            detail = "hub probe unreadable: %s" % exc
        if not live_map:
            bad = True
        else:
            drifted = [key for key in FACE_KEYS
                       if live_map.get(key) != faces.get(key)]
            if drifted:
                bad = True
                detail = "drifted " + ",".join(drifted)
    report("AC-STL1", bad, detail)

    # AC-STL2: the report says live AND an independent connect agrees.
    live = rep.get("live") or {}
    claimed = [key for key in FACE_KEYS if live.get(key) is not True]
    dead = [key for key in FACE_KEYS
            if not can_connect(face_ports.get(key))]
    bad = bool(claimed or dead)
    report("AC-STL2", bad,
           ("claimed-not-live " + ",".join(claimed) + " ") if claimed else ""
           + (("unreachable " + ",".join(dead)) if dead else ""))

    # AC-STL3: the vectors name the shipped modules; the module is stdlib-only
    # ASCII with no shell.
    sys.path.insert(0, HERE)
    import start_all  # noqa: E402  (path wired above)
    vectors = dict(start_all.build_commands("127.0.0.1", ports))
    bad = []
    for name, path in SHIPPED.items():
        argv = vectors.get(name) or []
        if not argv or argv[0] != sys.executable:
            bad.append("%s-not-python" % name)
            continue
        if not os.path.exists(path):
            bad.append("%s-missing" % name)
        if os.path.abspath(argv[1]) != os.path.abspath(path):
            bad.append("%s-not-shipped-module" % name)
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    text = raw.decode("utf-8")
    if raw[:3] == b"\xef\xbb\xbf":
        bad.append("module-bom")
    if b"\r\n" in raw:
        bad.append("module-crlf")
    try:
        text.encode("ascii")
    except UnicodeEncodeError:
        bad.append("module-not-ascii")
    if "shell=True" in text:
        bad.append("module-shells")
    allowed = {"argparse", "json", "os", "socket", "subprocess", "sys",
               "time", "urllib"}
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("import ") or
                stripped.startswith("from ")):
            continue
        root = stripped.split()[1].split(".")[0]
        if root not in allowed:
            bad.append("module-imports-" + root)
    report("AC-STL3", bool(bad), ",".join(bad))

    # AC-STL4: explicit overrides honoured, published ports pairwise distinct.
    bad = []
    if ports.get("ws") != ws_port:
        bad.append("ws-override-ignored")
    if ports.get("hub") != hub_port:
        bad.append("hub-override-ignored")
    if not can_connect(hub_port):
        bad.append("hub-not-on-override")
    published = [int(face_ports[key]) for key in FACE_KEYS if face_ports.get(key)]
    if len(published) != len(FACE_KEYS):
        bad.append("faces-without-port")
    if len(set(published)) != len(published):
        bad.append("ports-collide")
    report("AC-STL4", bool(bad), ",".join(bad))

    # AC-STL5: after the stop file the launcher exits and the ports go quiet.
    code = box.stop()
    bad = []
    if code != 0:
        bad.append("launcher-exit-%s" % code)
    deadline = time.time() + 3.0
    silent = list(FACE_KEYS)
    while silent and time.time() < deadline:
        silent = [key for key in silent if can_connect(face_ports.get(key))]
        if silent:
            time.sleep(0.1)
    still_up = [key for key in FACE_KEYS if can_connect(face_ports.get(key))]
    if still_up:
        bad.append("still-listening " + ",".join(still_up))
    report("AC-STL5", bool(bad), ",".join(bad))

    # AC-STL6: existing product bytes untouched, one registry row, hygiene.
    bad = []
    diff = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--",
         os.path.relpath(HUB_HTML, REPO), os.path.relpath(HUB_MODULE, REPO)],
        cwd=REPO)
    if diff.returncode != 0:
        bad.append("hub-bytes-changed")
    with open(REGISTRY, encoding="utf-8") as handle:
        registry_text = handle.read()
    if registry_text.count('"start-all"') != 1:
        bad.append("registry-rows-%d" % registry_text.count('"start-all"'))
    if "start-all" not in registry_text:
        bad.append("registry-row-missing")
    report("AC-STL6", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())