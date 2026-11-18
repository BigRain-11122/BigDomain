"""Suite for the one-command sandbox launcher (BigDomain R2477).

Nine criteria AC-STL1..AC-STL9. AC-STL1..AC-STL6 were pre-registered in the
R2477 backlog row BEFORE this file, src/sandbox/start_all.py and its registry
row existed; AC-STL7..AC-STL9 were pinned in the R2936 backlog row BEFORE the
launcher grew its last two faces (in-window pre-registration, disclosed).

Nothing here is read off a canned string: the launcher is really started in
serve mode, the report it writes is compared against the hub's own probe
answer at call time, an independent TCP connect checks every published port,
the last two faces are fetched over HTTP and graded against the title their
page file carries, a blocked port is proved to make the launcher REFUSE, and
the teardown leg proves the ports are gone after the stop file appears.

Usage: python test_start_all.py
Exit: 0 = SUITE PASS 9/9, 2 = FAIL.
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
LOBBY = os.path.join(HERE, "lobby")

FACE_KEYS = ("lobby", "city", "checkout", "gate", "ledger", "ugc",
             "panel", "member")
SHIPPED = {
    "lobby": os.path.join(HERE, "lobby", "server.py"),
    "checkout": os.path.join(HERE, "lobby", "checkout_demo.py"),
    "ledger": os.path.join(HERE, "ledger", "ledger_page.py"),
    "ugc": os.path.join(HERE, "ugc", "ugc_page.py"),
    "panel": os.path.join(HERE, "panel.py"),
    "member": os.path.join(HERE, "member", "member_page.py"),
}
# The page each of the two last faces serves, so AC-STL8 can ask the running
# socket for the title the DISK says it should carry.
FACE_PAGE = {
    "panel": os.path.join(HERE, "panel.html"),
    "member": os.path.join(HERE, "member", "member.html"),
}

RESULTS = []


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


def fetch_text(url, timeout=15.0):
    """(status, body) for one page, so a face is proved by what it SERVES."""
    with urllib.request.urlopen(url, timeout=timeout) as res:
        return res.status, res.read().decode("utf-8", "replace")


def page_title(path):
    """The <title> of a page ON DISK - the expected text, never typed here."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    head = text.split("<title>", 1)
    if len(head) < 2:
        return ""
    return head[1].split("</title>", 1)[0].strip()


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

    def __init__(self, tmpdir, ws_port=None, hub_port=None, extra=None,
                 name="report.json"):
        self.dir = tmpdir
        self.report_path = os.path.join(tmpdir, name)
        self.stop_path = os.path.join(tmpdir, name + ".stop")
        argv = [sys.executable, MODULE, "--timeout", "40",
                "--report-json", self.report_path,
                "--stop-file", self.stop_path]
        if ws_port:
            argv += ["--ws-port", str(ws_port)]
        if hub_port:
            argv += ["--hub-port", str(hub_port)]
        argv += list(extra or [])
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
        report("AC-STL7", True, "no report")
        report("AC-STL8", True, "no report")
        report("AC-STL9", True, "no report")
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

    # AC-STL7: the last two published cards are started by THIS door and their
    # URLs carry the ports this run measured - not the 8099/8096 that the
    # lobby falls back to when nobody hands it real ports (which is exactly how
    # those two cards read NOT STARTED for as long as they did).
    sys.path.insert(0, HERE)
    import start_all  # noqa: E402  (path wired above)
    lobby_argv = (dict(start_all.build_commands("127.0.0.1", ports))
                  .get("lobby") or [])
    bad = []
    for key in ("panel", "member"):
        port = ports.get(key)
        url = faces.get(key) or ""
        if not port:
            bad.append("not-planned-" + key)
            continue
        if (":%d/" % int(port)) not in url:
            bad.append("url-not-measured-" + key)
        flag = "--%s-port" % key
        if flag not in lobby_argv:
            bad.append("lobby-not-told-" + key)
        elif lobby_argv[lobby_argv.index(flag) + 1] != str(int(port)):
            bad.append("lobby-told-wrong-port-" + key)
    report("AC-STL7", bool(bad), ",".join(bad))

    # AC-STL8: those two faces are served by the SHIPPED modules, and what
    # comes back is the page that is on disk (title read from the file).
    bad = []
    for key, page_path in FACE_PAGE.items():
        want = page_title(page_path)
        if not want:
            bad.append("no-title-on-disk-" + key)
            continue
        try:
            status, body = fetch_text(faces.get(key) or "")
        except (OSError, ValueError, urllib.error.URLError) as exc:
            bad.append("%s-unreadable-%s" % (key, type(exc).__name__))
            continue
        if status != 200:
            bad.append("%s-http-%s" % (key, status))
        if want not in body:
            bad.append("%s-title-mismatch" % key)
    report("AC-STL8", bool(bad), ",".join(bad))

    # AC-STL3: the vectors name the shipped modules; the module is stdlib-only
    # ASCII with no shell.
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

    # AC-STL6: the hub still publishes every face this launcher plans, one
    # registry row, hygiene.
    #
    # AMENDED OPENLY at R2489, disclosed rather than dressed up: the criterion
    # as pinned at R2477 asserted `git diff --quiet HEAD` over the hub bytes,
    # which can only hold on the round that wrote it - any later round that
    # legitimately extends the hub (R2484 added the panel card, R2489 adds the
    # member card) turns the launcher suite red for a change the launcher did
    # not make. It is replaced by what the launcher actually depends on: the
    # hub must still publish a URL for every face the launcher plans. The check
    # is measured against the shipped build_faces, and the registry assertion
    # is unchanged.
    bad = []
    sys.path.insert(0, LOBBY)
    import hub_page  # noqa: E402  (path wired just above)
    published = hub_page.build_faces("127.0.0.1", 8091, web_port=8094,
                                    city_port=8092, checkout_port=8093,
                                    gate_port=8096, ledger_port=8097,
                                    ugc_port=8098, panel_port=8099,
                                    member_port=8095)
    for key in FACE_KEYS:
        if not published.get(key):
            bad.append("hub-does-not-publish-" + key)
    # The hub publishes a face only when it is HANDED a port ("simply not
    # published rather than published with a guess"), so the two cards this
    # round starts must vanish when their port is None - otherwise the hub
    # would still be advertising a socket nobody placed.
    bare = hub_page.build_faces("127.0.0.1", 8091, panel_port=None,
                                member_port=None)
    for key in ("panel", "member"):
        if bare.get(key):
            bad.append("hub-guesses-" + key)
    with open(REGISTRY, encoding="utf-8") as handle:
        registry_text = handle.read()
    if registry_text.count('"start-all"') != 1:
        bad.append("registry-rows-%d" % registry_text.count('"start-all"'))
    if "start-all" not in registry_text:
        bad.append("registry-row-missing")
    report("AC-STL6", bool(bad), ",".join(bad))

    # AC-STL9 (red control): the two new faces are GRADED, not decorated. Hold
    # the panel socket with our own listener: the launcher must hand that port
    # to a child that cannot bind, and must then REFUSE rather than report a
    # door that advertises a face nobody can open.
    blocker = socket.socket()
    blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    blocker.bind(("127.0.0.1", 0))
    blocker.listen(1)
    held = int(blocker.getsockname()[1])
    bad = []
    try:
        red = Sandbox(tmpdir, name="red-report.json",
                      extra=["--panel-port", str(held), "--timeout", "6"])
        red.start()
        got = red.report or {}
        red.stop()
        if not got:
            bad.append("no-report-from-red-run")
        else:
            if got.get("ok") is not False:
                bad.append("reported-ok-with-panel-unbindable")
            joined = " ".join(got.get("errors") or [])
            if "panel" not in joined:
                bad.append("errors-do-not-name-panel")
            if (got.get("live") or {}).get("panel") is not False:
                bad.append("panel-read-live-while-blocked")
    finally:
        blocker.close()
    report("AC-STL9", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())