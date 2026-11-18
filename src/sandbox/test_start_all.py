"""Suite for the one-command sandbox launcher (BigDomain R2477).

Eleven criteria AC-STL1..AC-STL11. AC-STL1..AC-STL6 were pre-registered in the
R2477 backlog row BEFORE this file, src/sandbox/start_all.py and its registry
row existed; AC-STL7..AC-STL9 were pinned in the R2936 backlog row BEFORE the
launcher grew its last two faces (in-window pre-registration, disclosed).
AC-STL10..AC-STL11 were pinned in the R2948 row BEFORE the launcher verified
its own job members and before the grandson path was measured on the shipped
panel.

R2979 adds AC-STL12..AC-STL13 (plan_ports.py), pinned in the R2979 backlog row
BEFORE that module and these arms existed: one plan() call hands every plan key
a DISTINCT port. The live arm really calls the shipped allocator, so it binds
ten loopback ephemeral sockets for an instant and closes each - the red control
wires in allocators that ignore the used-set and must be refused by name.

R2980 adds AC-STL14..AC-STL15 (plan_ports.override_coverage), pinned in the
R2980 row BEFORE that predicate and these arms existed: two keys in ONE override
map naming one port is refused by name, and a key the plan does not carry is
named instead of dropped in silence. The arms pass fully explicit maps, so no
socket is bound; the one live call proves what plan() DOES today with a typo
key, which is measured rather than asserted as permanent.

R2981 adds AC-STL16..AC-STL17 (the report's override face), pinned in the
R2981 row BEFORE that field existed: the launcher's report now publishes the
override collision plan() already knows, on the same face that publishes
face_ports. One arm is measured on the SHIPPED path - a real launcher given one
number for two plan keys must name both keys in the report it writes and must
not read ok.

Nothing here is read off a canned string: the launcher is really started in
serve mode, the report it writes is compared against the hub's own probe
answer at call time, an independent TCP connect checks every published port,
the last two faces are fetched over HTTP and graded against the title their
page file carries, a blocked port is proved to make the launcher REFUSE, and
the teardown leg proves the ports are gone after the stop file appears.

Usage: python test_start_all.py
Exit: 0 = SUITE PASS 17/17, 2 = FAIL.
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


def panel_face_ids():
    """The faces the SHIPPED panel exposes, read from its own module."""
    import panel as panel_module
    return tuple(panel_module.FACE_IDS)


STATE_ERROR = ""


def panel_state(port):
    """The panel's own state, or None with the reason kept for the report."""
    global STATE_ERROR
    try:
        return fetch_json("http://127.0.0.1:%d/panel/api/state" % int(port))
    except (OSError, ValueError, urllib.error.URLError) as exc:
        STATE_ERROR = "%r" % (exc,)
        return None


def panel_post(port, path, payload):
    """(status, body) even when the status is a refusal, never an exception."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:%d%s" % (int(port), path), data=data, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.status, json.loads(res.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body or "{}")
        except ValueError:
            return exc.code, {"raw": body}


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
        # A private machine record per run, so this suite neither competes for
        # the per-user claim nor leaves one behind (R2939).
        self.registry_path = os.path.join(tmpdir, name + ".registry.json")
        argv = [sys.executable, MODULE, "--timeout", "40",
                "--registry", self.registry_path,
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
        report("AC-STL10", True, "no report")
        report("AC-STL11", True, "no report")
        report("AC-STL16", True, "no report")
        report("AC-STL17", True, "no report")
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
    # AMENDED OPENLY at R2937, same discipline as AC-STL6 below: the intent of
    # this leg is stdlib-only with no third-party dependency and no shell, and
    # the launcher now imports a SIBLING leaf module (job_object) that lives
    # in this directory. A sibling file is not a package requirement and not a
    # install step, so the leg accepts a root that resolves to a .py file next
    # to the launcher while still refusing anything else by name.
    siblings = set(os.path.splitext(name)[0] for name in os.listdir(HERE)
                   if name.endswith(".py"))
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("import ") or
                stripped.startswith("from ")):
            continue
        root = stripped.split()[1].split(".")[0]
        if root not in allowed and root not in siblings:
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

    # AC-STL10 (R2948): the launcher verifies its OWN members against the
    # kernel. A report that says "assigned=6" only says the call returned; the
    # question that survives a crash is whether each child is really inside
    # the job. Both directions run here: the live run must read every member
    # True, and a pid that was never placed must read False and be named.
    bad = []
    job = rep.get("job") or {}
    children = [name for name, _rel in (rep.get("children") or [])]
    if job.get("available"):
        if not job.get("enabled"):
            bad.append("job-not-enabled")
        if not job.get("verified"):
            bad.append("members-never-verified")
        members = job.get("members") or {}
        for name in children:
            if members.get(name) is not True:
                bad.append("member-%s-%s" % (name, members.get(name)))
        if job.get("escaped"):
            bad.append("escaped-" + ",".join(job["escaped"]))
    elif job.get("verified"):
        bad.append("claimed-verification-without-kernel")
    # red control, in-process: the same helper, asked about a process that was
    # never placed, must name it instead of folding it into a count.
    import job_object
    import start_all

    outsider = subprocess.Popen([sys.executable, "-c",
                                 "import time; time.sleep(20)"],
                                stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
    probe = subprocess.Popen([sys.executable, "-c",
                              "import time; time.sleep(20)"],
                             stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
    group = start_all.ChildGroup()
    try:
        if job_object.available():
            group.job = job_object.create("bigdomain-stl10")
            group.job_enabled = True
            group.append(("probe", probe))
            job_object.assign(group.job, probe.pid)
            check = start_all.verify_members(group, {"outsider": outsider.pid})
            if check.get("checked") is not True:
                bad.append("in-process-not-checked")
            if check["members"].get("outsider") is not False:
                bad.append("outsider-read-%s" % check["members"].get("outsider"))
            if "outsider" not in check.get("escaped", []):
                bad.append("outsider-not-named-escaped")
            # and a placed pid reads True, so the arm is not refusing all
            placed = start_all.verify_members(group)
            if placed["members"].get("probe") is not True:
                bad.append("placed-read-%s" % placed["members"].get("probe"))
            if placed.get("escaped"):
                bad.append("placed-named-escaped")
        # --no-job must not pretend to have verified anything
        nojob = start_all.start([("probe", [sys.executable, "-c",
                                            "import time; time.sleep(5)"])],
                                use_job=False)
        try:
            if nojob.verified:
                bad.append("nojob-claims-verified")
            if nojob.escaped:
                bad.append("nojob-claims-escaped")
        finally:
            start_all.teardown(nojob)
    finally:
        if group.job:
            job_object.close(group.job)
            group.job = None
        for proc in (probe, outsider):
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
    report("AC-STL10", bool(bad), ",".join(bad))

    # AC-STL11 (R2948): the launcher -> panel -> face path is not merely
    # refused at the face, it is not OFFERED by the shipped door. The panel the
    # real launcher started owns every face it serves, so each startable verb
    # must answer 409 by name and spawn nothing. A launcher is started HERE
    # because AC-STL5 already proved the first one tears down on its stop file.
    bad = []
    box = Sandbox(tmpdir, name="owner-report.json")
    rep = box.start()
    try:
        if not rep:
            bad.append("no-report")
        else:
            panel_port = (rep.get("face_ports") or {}).get("panel")
            ports = rep.get("face_ports") or {}
            if not panel_port:
                bad.append("no-panel-port")
            else:
                face_ids = panel_face_ids()
                before = panel_state(panel_port)
                if not before:
                    bad.append("panel-state-unreadable:" + STATE_ERROR)
                else:
                    rows = dict((row.get("id"), row)
                                for row in before.get("faces") or [])
                    for face_id in face_ids:
                        row = rows.get(face_id) or {}
                        if row.get("owner") != "launcher":
                            bad.append("row-%s-owner-%s"
                                       % (face_id, row.get("owner")))
                    for face_id in face_ids:
                        code, obj = panel_post(panel_port, "/panel/api/start",
                                               {"face": face_id})
                        if code != 409:
                            bad.append("start-%s-code-%s" % (face_id, code))
                            continue
                        if obj.get("error") != "E_PANEL_OWNED_BY_LAUNCHER":
                            bad.append("start-%s-err-%s"
                                       % (face_id, obj.get("error")))
                        if obj.get("owner") != "launcher":
                            bad.append("start-%s-owner-%s"
                                       % (face_id, obj.get("owner")))
                        want = ports.get(face_id)
                        if want is not None and int(obj.get("port") or 0) != int(want):
                            bad.append("start-%s-port-%s"
                                       % (face_id, obj.get("port")))
                    after = panel_state(panel_port)
                    if after:
                        if (after.get("faces") or []) != (before.get("faces") or []):
                            bad.append("panel-rows-moved-after-refusals")
                        for row in after.get("faces") or []:
                            if row.get("owner") != "launcher":
                                bad.append("after-%s-owner-%s"
                                           % (row.get("id"), row.get("owner")))
                    else:
                        bad.append("panel-state-unreadable-after")
    finally:
        box.stop()
    report("AC-STL11", bool(bad), ",".join(bad))

    # AC-STL12 (R2979): one plan() call hands every plan key a DISTINCT port.
    # Pinned in the R2979 backlog row BEFORE this block and plan_ports.py
    # existed. Unlike AC-KOC11, which passes a fully explicit override map so
    # the allocator never runs, this arm really calls the shipped plan(), so it
    # binds ten loopback ephemeral sockets and closes each immediately.
    import plan_ports
    import start_all

    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    bad = []
    lived = start_all.plan("127.0.0.1")
    verdict = plan_ports.port_plan_coverage(lived, start_all.PLAN_KEYS)
    if not verdict["ok"]:
        bad.append("not-ok")
    if verdict["duplicates"]:
        bad.append("dups-%r" % (verdict["duplicates"],))
    if verdict["missing"]:
        bad.append("missing-" + ",".join(verdict["missing"]))
    if verdict["keys"] != tuple(sorted(start_all.PLAN_KEYS)):
        bad.append("keys-not-plan")
    if verdict["count"] != len(start_all.PLAN_KEYS):
        bad.append("count-%d" % verdict["count"])
    if verdict["distinct"] != len(start_all.PLAN_KEYS):
        bad.append("distinct-%d" % verdict["distinct"])
    # and the numbers themselves are usable ports, not placeholders
    for key in start_all.PLAN_KEYS:
        value = lived.get(key)
        if not isinstance(value, int):
            bad.append("%s-not-int" % key)
        elif not 1 <= value <= 65535:
            bad.append("%s-out-of-range" % key)
    # an explicit override is fed into the used-set, so the nine auto keys must
    # avoid the number the override took - the other direction of the same law
    pinned = start_all.free_port("127.0.0.1")
    seeded = start_all.plan("127.0.0.1", {"ws": pinned})
    if seeded.get("ws") != pinned:
        bad.append("override-not-honoured")
    avoided = [k for k in start_all.PLAN_KEYS if k != "ws"]
    if any(seeded.get(k) == pinned for k in avoided):
        bad.append("override-not-fed-into-used-set")
    # two calls in a row are each internally unique; comparing them to EACH
    # OTHER would be wrong, because the OS may reuse a number after close()
    for attempt in range(2):
        again = plan_ports.port_plan_coverage(
            start_all.plan("127.0.0.1"), start_all.PLAN_KEYS)
        if not again["ok"]:
            bad.append("call-%d-not-ok" % attempt)
    report("AC-STL12", bool(bad), ",".join(bad))

    # AC-STL13 (R2979): the control that proves the criterion above can say No.
    # An allocator that ignores its used-set is wired in on purpose; the verdict
    # must go red and NAME the colliding port with every key that took it.
    class StuckSocket(object):
        """A socket stand-in that always reports the same port."""

        def __init__(self, port):
            self.port = port

        def bind(self, addr):
            return None

        def getsockname(self):
            return ("127.0.0.1", self.port)

        def close(self):
            return None

    bad = []
    real_free_port = start_all.free_port
    real_socket = start_all.socket
    try:
        start_all.free_port = lambda host="127.0.0.1", used=None: 7000
        blind = plan_ports.port_plan_coverage(
            start_all.plan("127.0.0.1"), start_all.PLAN_KEYS)
        if blind["ok"]:
            bad.append("blind-allocator-read-ok")
        if blind["duplicates"] != ((7000, tuple(sorted(start_all.PLAN_KEYS))),):
            bad.append("blind-dups-%r" % (blind["duplicates"],))

        # a cycler that ignores used-set but still changes numbers - the same
        # defect in another shape, so the red is about repetition and not about
        # a constant return
        cycle = [7000, 7001, 7000]
        state = {"i": 0}

        def cycling(host="127.0.0.1", used=None):
            port = cycle[state["i"] % len(cycle)]
            state["i"] += 1
            return port

        start_all.free_port = cycling
        cycled = plan_ports.port_plan_coverage(
            start_all.plan("127.0.0.1"), start_all.PLAN_KEYS)
        if cycled["ok"]:
            bad.append("cycling-read-ok")
        if not any(port == 7000 for port, _keys in cycled["duplicates"]):
            bad.append("cycling-dups-%r" % (cycled["duplicates"],))
    finally:
        start_all.free_port = real_free_port

    # the mechanism itself: free_port refuses a number the run already holds,
    # and the same stand-in is accepted when the set does not hold it - so the
    # refusal is the used-set, not "that port is unavailable"
    try:
        start_all.socket = type("StubSocketModule", (), {
            "socket": staticmethod(lambda: StuckSocket(7000))})()
        try:
            held = start_all.free_port("127.0.0.1", {7000})
        except RuntimeError as exc:
            if "E_NO_FREE_PORT" not in str(exc):
                bad.append("stuck-wrong-error-%s" % exc)
        else:
            bad.append("stuck-returned-%r" % (held,))
        try:
            free = start_all.free_port("127.0.0.1", set())
        except RuntimeError as exc:
            bad.append("stuck-refused-when-free-%s" % exc)
        else:
            if free != 7000:
                bad.append("stuck-free-read-%r" % (free,))
    finally:
        start_all.socket = real_socket

    # healthy worlds stay green, and a plan that dropped a key is refused
    if not plan_ports.port_plan_coverage({"a": 7000})["ok"]:
        bad.append("single-key-not-ok")
    if not plan_ports.port_plan_coverage({})["ok"]:
        bad.append("empty-not-ok")
    dropped = plan_ports.port_plan_coverage({"a": 7000}, ("a", "b"))
    if dropped["ok"]:
        bad.append("missing-key-read-ok")
    if dropped["missing"] != ("b",):
        bad.append("missing-named-%r" % (dropped["missing"],))
    report("AC-STL13", bool(bad), ",".join(bad))

    # AC-STL14 (R2980): the OVERRIDE face of the same question. plan() adds an
    # override to the used-set but never compares overrides with each other, so
    # two keys naming one port is refused nowhere at run time. This arm judges
    # the healthy shapes (single-key --ws-port style, empty, two distinct keys)
    # and names the typo face: a key the plan does not carry is dropped by
    # plan() without a word, measured here rather than asserted for all time.
    bad = []
    single = plan_ports.override_coverage({"ws": 7000}, start_all.PLAN_KEYS)
    if not single["ok"]:
        bad.append("single-not-ok")
    if single["duplicates"]:
        bad.append("single-dups-%r" % (single["duplicates"],))
    if single["unknown"] or single["bad"]:
        bad.append("single-named-%r/%r" % (single["unknown"], single["bad"]))
    if single["keys"] != ("ws",):
        bad.append("single-keys-%r" % (single["keys"],))
    empty = plan_ports.override_coverage({}, start_all.PLAN_KEYS)
    if not empty["ok"] or empty["count"]:
        bad.append("empty-%r/%d" % (empty["ok"], empty["count"]))
    pair = plan_ports.override_coverage({"ws": 7000, "hub": 7001},
                                        start_all.PLAN_KEYS)
    if not pair["ok"] or pair["distinct"] != 2:
        bad.append("pair-%r/%d" % (pair["ok"], pair["distinct"]))
    typo = plan_ports.override_coverage({"wss": 7000}, start_all.PLAN_KEYS)
    if typo["ok"]:
        bad.append("typo-read-ok")
    if typo["unknown"] != ("wss",):
        bad.append("typo-unknown-%r" % (typo["unknown"],))
    # and the launcher really drops it: the plan's key set is exactly PLAN_KEYS
    with_typo = start_all.plan("127.0.0.1", {"wss": 7000})
    if tuple(sorted(with_typo)) != tuple(sorted(start_all.PLAN_KEYS)):
        bad.append("typo-reached-plan-%r" % (tuple(sorted(with_typo)),))
    report("AC-STL14", bool(bad), ",".join(bad))

    # AC-STL15 (R2980): the control that proves AC-STL14's predicate says No.
    # Everything here is a fully explicit map, so no socket is bound and no
    # process starts. The reds must NAME both keys, not fold into a boolean.
    bad = []
    clash = plan_ports.override_coverage({"ws": 7000, "city": 7000},
                                         start_all.PLAN_KEYS)
    if clash["ok"]:
        bad.append("clash-read-ok")
    if clash["duplicates"] != ((7000, ("city", "ws")),):
        bad.append("clash-dups-%r" % (clash["duplicates"],))
    moved = plan_ports.override_coverage({"ws": 7000, "city": 7001},
                                         start_all.PLAN_KEYS)
    if not moved["ok"] or moved["duplicates"]:
        bad.append("moved-%r/%r" % (moved["ok"], moved["duplicates"]))
    three = plan_ports.override_coverage(
        {"ws": 7000, "city": 7000, "hub": 7000}, start_all.PLAN_KEYS)
    if three["duplicates"] != ((7000, ("city", "hub", "ws")),):
        bad.append("three-dups-%r" % (three["duplicates"],))
    # plan() stores int(given), so the predicate must compare numbers and not
    # spellings; a value that is not a number is named instead of crashing
    spelled = plan_ports.override_coverage({"ws": "7000", "city": 7000},
                                           start_all.PLAN_KEYS)
    if spelled["duplicates"] != ((7000, ("city", "ws")),):
        bad.append("spelled-dups-%r" % (spelled["duplicates"],))
    garbage = plan_ports.override_coverage({"ws": "nope"},
                                           start_all.PLAN_KEYS)
    if garbage["ok"] or garbage["bad"] != ("ws",):
        bad.append("garbage-%r/%r" % (garbage["ok"], garbage["bad"]))
    report("AC-STL15", bool(bad), ",".join(bad))

    # AC-STL16 (R2981): the report PUBLISHES the override collision plan()
    # already knows. Every arm here is in-process: one report_of call each, all
    # zero ports, no socket bound and no process started.
    bad = []
    zero = dict((key, 0) for key in start_all.PLAN_KEYS)
    healthy = start_all.report_of("127.0.0.1", zero, "", {}, {}, [])
    if "override_duplicates" not in healthy:
        bad.append("field-missing")
    elif healthy["override_duplicates"] != ():
        bad.append("healthy-%r" % (healthy["override_duplicates"],))
    # the additive claim MEASURED rather than asserted in prose: every key the
    # report carried before R2981 is still there, so an old reader is not
    # broken by the new one
    before = ("ok", "host", "hub_url", "ports", "face_ports", "faces", "live",
              "children", "pids", "job", "mutex", "errors", "mock",
              "chargeable")
    gone = [key for key in before if key not in healthy]
    if gone:
        bad.append("dropped-" + ",".join(gone))
    named = start_all.report_of(
        "127.0.0.1", zero, "", {}, {}, [],
        override_duplicates=plan_ports.override_collisions(
            {"ws": 7000, "city": 7000}))
    if named["override_duplicates"] != ((7000, ("city", "ws")),):
        bad.append("collision-%r" % (named["override_duplicates"],))
    single = start_all.report_of(
        "127.0.0.1", zero, "", {}, {}, [],
        override_duplicates=plan_ports.override_collisions({"ws": 7000}))
    if single["override_duplicates"] != ():
        bad.append("single-%r" % (single["override_duplicates"],))
    empty_map = start_all.report_of(
        "127.0.0.1", zero, "", {}, {}, [],
        override_duplicates=plan_ports.override_collisions({}))
    if empty_map["override_duplicates"] != ():
        bad.append("empty-%r" % (empty_map["override_duplicates"],))
    report("AC-STL16", bool(bad), ",".join(bad))

    # AC-STL17 (R2981): the control, and the shipped half of it. Arm 1 reads the
    # report the real launcher above wrote (no overrides, so the field must be
    # empty). Arm 2 starts ONE more real launcher and gives ws and city the SAME
    # number - the report it writes must name both keys and must not read ok.
    # Arm 3 keeps the three-way shape in-process.
    bad = []
    shipped = rep.get("override_duplicates")
    if shipped is None:
        bad.append("live-report-field-missing")
    elif list(shipped) != []:
        bad.append("live-report-%r" % (shipped,))
    clash_port = free_port()
    red = Sandbox(tmpdir, ws_port=clash_port,
                  extra=["--timeout", "6", "--city-port", str(clash_port)],
                  name="clash-report.json")
    red_report = red.start()
    red_code = red.stop()
    if not red_report:
        bad.append("clash-no-report")
    else:
        got = [(int(port), tuple(keys))
               for port, keys in (red_report.get("override_duplicates") or [])]
        if got != [(clash_port, ("city", "ws"))]:
            bad.append("clash-%r" % (got,))
        if red_report.get("ok"):
            bad.append("clash-read-ok")
    if red_code == 0:
        bad.append("clash-exit-0")
    three = plan_ports.override_collisions(
        {"ws": 7000, "city": 7000, "hub": 7000})
    if three != ((7000, ("city", "hub", "ws")),):
        bad.append("three-%r" % (three,))
    report("AC-STL17", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())