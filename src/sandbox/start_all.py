"""One command that brings every sandbox face up and names the door to open.

The sandbox grew one surface at a time - the city read API, the WebSocket
lobby, the browser client, the content gate, the token ledger console, the UGC
console and the 19.9 checkout demo - and each lives in its own module on its
own port. A person who wanted to look at the whole thing had to remember five
commands and five URLs, and the hub page could only describe them: it is a
read-only face, so every card it publishes ended in "start this yourself".

R2936 adds the last two published cards - the control panel and the membership
page - to the same door, because the hub has named all eight faces since they
shipped. Their measured ports are handed to the lobby on its own command line,
so the URL the hub publishes is a measured port rather than a built-in guess.

This launcher closes that last step. It picks OS-assigned ports so it never
assumes 8091..8098 are free, starts the shipped entry modules unchanged, waits
until every socket really accepts, and then asks the hub what it publishes -
so the URL it prints is the hub's own answer rather than a literal here.

Honesty law: readiness is measured. A face is reported ready only when its port
accepts a connection AND the hub's own probe map reads it live; a launcher that
printed ready because it launched something would be the same lie as a page
that paints a dead port green.

Usage:
  python src/sandbox/start_all.py              # start and keep serving
  python src/sandbox/start_all.py --check      # start, prove, tear down, exit
Exit: 0 = every face proved, 2 = at least one face never came up.
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

import job_object
import launcher_mutex
import launcher_registry

HERE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(HERE, "lobby")

SERVER = os.path.join(LOBBY, "server.py")
CHECKOUT = os.path.join(LOBBY, "checkout_demo.py")
LEDGER = os.path.join(HERE, "ledger", "ledger_page.py")
UGC = os.path.join(HERE, "ugc", "ugc_page.py")
PANEL = os.path.join(HERE, "panel.py")
MEMBER = os.path.join(HERE, "member", "member_page.py")

# Every face the hub publishes with a real port behind it. The panel and the
# membership page are here for the same reason as the rest: the hub named them
# from the day they shipped, so a launcher that skipped them left two cards
# reading NOT STARTED behind a door that advertised them.
FACE_KEYS = ("lobby", "city", "checkout", "gate", "ledger", "ugc",
             "panel", "member")
# Which planned socket carries each face (the lobby page and the WebSocket
# share the lobby module but not a port).
FACE_PORT_KEY = {"lobby": "web", "city": "city", "checkout": "checkout",
                 "gate": "gate", "ledger": "ledger", "ugc": "ugc",
                 "panel": "panel", "member": "member"}
# Every socket this launcher must place: ten ports for eight faces, because
# the lobby module owns the ws socket and the gate/web sockets itself.
PLAN_KEYS = ("ws", "city", "gate", "web", "hub", "checkout", "ledger", "ugc",
             "panel", "member")

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def free_port(host="127.0.0.1", used=None):
    """An OS-assigned free port, never one this run already handed out."""
    used = used if used is not None else set()
    for _ in range(64):
        sock = socket.socket()
        try:
            sock.bind((host, 0))
            port = int(sock.getsockname()[1])
        finally:
            sock.close()
        if port not in used:
            used.add(port)
            return port
    raise RuntimeError("E_NO_FREE_PORT")


def plan(host, overrides=None):
    """Decide the eight ports: explicit ones win, the rest are OS-assigned."""
    overrides = dict(overrides or {})
    used = set()
    ports = {}
    for key in PLAN_KEYS:
        given = overrides.get(key)
        if given:
            ports[key] = int(given)
            used.add(int(given))
        else:
            ports[key] = free_port(host, used)
    return ports


def build_commands(host, ports):
    """The exact argument vectors used to start the SHIPPED entry modules.

    Kept as a pure function so a suite can read the vectors this launcher
    really builds instead of trusting a paragraph about them. No shell is
    involved anywhere: every vector starts with sys.executable.
    """
    lobby = [
        sys.executable, SERVER, "--host", host,
        "--port", str(ports["ws"]),
        "--city-http-port", str(ports["city"]),
        "--gate-port", str(ports["gate"]),
        "--web-port", str(ports["web"]),
        "--hub-port", str(ports["hub"]),
        "--checkout-port", str(ports["checkout"]),
        "--ledger-port", str(ports["ledger"]),
        "--ugc-port", str(ports["ugc"]),
        # The panel and the membership page are separate processes, so the
        # lobby is TOLD their measured ports instead of its built-in guesses.
        "--panel-port", str(ports["panel"]),
        "--member-port", str(ports["member"]),
    ]
    # The panel is told every face this launcher already serves, with the port
    # it measured for each, so a click in the page refuses by name instead of
    # starting a second lobby beside the one the person is looking at. The
    # declaration is derived from FACE_KEYS/FACE_PORT_KEY rather than typed, so
    # a face added to the plan is declared without anyone remembering to.
    panel = [sys.executable, PANEL, "--host", host,
             "--port", str(ports["panel"])]
    for key in FACE_KEYS:
        panel.extend(["--owned-face", "%s:%d" % (key, ports[FACE_PORT_KEY[key]])])
    return [
        ("lobby", lobby),
        ("checkout", [sys.executable, CHECKOUT, "--host", host,
                      "--port", str(ports["checkout"])]),
        ("ledger", [sys.executable, LEDGER, "--host", host,
                    "--port", str(ports["ledger"])]),
        ("ugc", [sys.executable, UGC, "--host", host,
                 "--port", str(ports["ugc"])]),
        ("panel", panel),
        ("member", [sys.executable, MEMBER, "--host", host,
                    "--port", str(ports["member"])]),
    ]


def can_connect(host, port, timeout=0.35):
    """True when something is really listening on that port right now."""
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def wait_port(host, port, timeout):
    deadline = time.time() + float(timeout)
    while time.time() < deadline:
        if can_connect(host, port):
            return True
        time.sleep(0.15)
    return False


def fetch_json(url, timeout=10.0):
    with urllib.request.urlopen(url, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


class ChildGroup(list):
    """The live children plus the job they were placed in, if any.

    A list subclass so ``teardown`` keeps taking the same argument it always
    took, while the report can say truthfully whether the kill-on-close
    guarantee is actually armed - and name every child it could not place.
    """

    def __init__(self, items=(), job=None, job_enabled=False):
        list.__init__(self, items)
        self.job = job
        self.job_enabled = job_enabled
        self.assigned = 0
        self.job_errors = []
        # R2948: assign() returning without raising only says the CALL worked.
        # Whether the child is really a member is a question for the kernel,
        # asked again below, so the report can stop implying it from a count.
        self.members = {}
        self.escaped = []
        self.verified = False


def verify_members(group, pids=None):
    """Ask the kernel which of these pids are inside the group's job.

    R2948: this is the shipped consumer of ``job_object.is_in_job``. A pid the
    kernel reports outside the job is named in ``escaped`` rather than folded
    into a boolean, because "one child is outside the kill-on-close guarantee"
    is the only part of this that matters after a crash.

    ``pids`` lets a suite ask the same question about a process this launcher
    did not start (the red control: a pid that was never assigned must read
    False, or this verification would be measuring nothing).
    """
    if not group.job:
        return {"checked": False, "members": {}, "escaped": []}
    members = {}
    for name, proc in group:
        members[name] = job_object.is_in_job(group.job, proc.pid)
    for name, pid in (pids or {}).items():
        members[name] = job_object.is_in_job(group.job, int(pid))
    escaped = [name for name, inside in members.items() if not inside]
    return {"checked": True, "members": members, "escaped": escaped}


def start(commands, use_job=True):
    """Start every vector quietly, inside a kill-on-close job when possible.

    Order matters: the job is created FIRST so a child can be placed in it the
    moment it exists, and a child that cannot be placed is named in
    ``job_errors`` rather than silently left outside the guarantee.
    """
    group = ChildGroup()
    if use_job and job_object.available():
        try:
            # R2948: an ANONYMOUS job per launcher. A named job is machine-wide,
            # so two launchers (or a launcher and a suite) that both created
            # the default name shared one object: children of one run were
            # members of the other's job, and "this launcher owns these
            # children" stopped being true. Anonymous keeps kill-on-close
            # exactly as strong and local to the process that armed it.
            group.job = job_object.create(None)
            group.job_enabled = True
        except job_object.JobError as exc:
            group.job_errors.append(str(exc))
    for name, argv in commands:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=NO_WINDOW,
        )
        group.append((name, proc))
        if group.job:
            try:
                job_object.assign(group.job, proc.pid)
                group.assigned += 1
            except job_object.JobError as exc:
                group.job_errors.append("%s %s" % (name, exc))
    # R2948: a second, kernel-side read. assign() said the call succeeded; this
    # says the child IS a member, and a child that is not is named and refused
    # instead of being counted as protected.
    if group.job:
        check = verify_members(group)
        group.verified = bool(check["checked"])
        group.members = check["members"]
        group.escaped = list(check["escaped"])
        if group.escaped:
            group.job_errors.append("E_JOB_MEMBER_ESCAPED: "
                                    + ",".join(group.escaped))
    return group


def teardown(children):
    """Stop every child this process started; no orphan keeps a sandbox port.

    The polite terminate runs first and stays the normal path; the job is
    closed afterwards as the backstop, so whatever ignored the terminate dies
    with it. Closing the job is also what makes a HARD-killed launcher safe,
    because the kernel closes that handle for us.
    """
    for _name, proc in children:
        if proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
    deadline = time.time() + 3.0
    for _name, proc in children:
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.05)
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
    job = getattr(children, "job", None)
    if job:
        job_object.close(job)
        children.job = None


def verify(host, ports, timeout):
    """Wait for every socket, then read the hub's own opinion of each face."""
    missing = [key for key in PLAN_KEYS
               if not wait_port(host, ports[key], timeout)]
    hub_url = "http://%s:%d/hub/" % (host, ports["hub"])
    faces = {}
    live = {}
    if "hub" not in missing:
        try:
            payload = fetch_json(hub_url + "api/faces?probe=1")
        except (OSError, ValueError, urllib.error.URLError):
            payload = {}
        faces = dict((key, payload[key]) for key in FACE_KEYS
                     if key in payload)
        live = dict((key, bool((payload.get("live") or {}).get(key)))
                    for key in FACE_KEYS)
    ready = (not missing and len(faces) == len(FACE_KEYS)
             and all(live.get(key) for key in FACE_KEYS))
    errors = []
    if missing:
        errors.append("E_NOT_UP: " + ",".join(missing))
    if not missing and len(faces) != len(FACE_KEYS):
        errors.append("E_FACE_MISSING: published only " + ",".join(sorted(faces)))
    for key in FACE_KEYS:
        if not missing and len(faces) == len(FACE_KEYS) and not live.get(key):
            errors.append("E_NOT_LIVE: " + key)
    return ready, hub_url, faces, live, errors


def report_of(host, ports, hub_url, faces, live, errors, group=None,
              mutex=None):
    group = group if group is not None else ChildGroup()
    return {
        "ok": not errors,
        "host": host,
        "hub_url": hub_url,
        "ports": dict(ports),
        "face_ports": dict((key, ports[FACE_PORT_KEY[key]])
                           for key in FACE_KEYS),
        "faces": faces,
        "live": live,
        "children": [[name, os.path.relpath(argv[1], os.path.dirname(HERE))]
                     for name, argv in build_commands(host, ports)],
        "pids": dict((name, proc.pid) for name, proc in group),
        "job": {"available": job_object.available(),
                "enabled": bool(group.job_enabled),
                "assigned": group.assigned,
                "verified": bool(group.verified),
                "members": dict(group.members),
                "escaped": list(group.escaped),
                "errors": list(group.job_errors)},
        "mutex": dict(mutex or {}),
        "errors": errors,
        "mock": True,
        "chargeable": False,
    }


def write_report(path, report):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, path)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="start every sandbox face and print the one door to open")
    parser.add_argument("--host", default="127.0.0.1")
    for key in PLAN_KEYS:
        parser.add_argument("--%s-port" % key, type=int, default=None,
                            dest="%s_port" % key)
    parser.add_argument("--timeout", type=float, default=45.0,
                        help="seconds to wait for each socket")
    parser.add_argument("--check", action="store_true",
                        help="start, prove every face, tear down, print the "
                             "report, exit 0 on proof and 2 otherwise")
    parser.add_argument("--report-json", default=None,
                        help="write the report to this path as soon as the "
                             "sandbox is up (serve mode)")
    parser.add_argument("--stop-file", default=None,
                        help="serve mode watches this path and tears down "
                             "when it appears")
    parser.add_argument("--no-job", action="store_true",
                        help="start WITHOUT a kill-on-close job object (red "
                             "control: a hard-killed launcher then leaves its "
                             "children holding ports)")
    parser.add_argument("--registry", default=None,
                        help="path of the machine-wide launcher record "
                             "(default: the per-user record, never in this "
                             "repo). Suites pass a private path so two test "
                             "runs never compete for the machine claim.")
    parser.add_argument("--mutex-name", default=None,
                        help="kernel claim name; default is derived from the "
                             "record path, so private registries stay private")
    parser.add_argument("--no-mutex", action="store_true",
                        help="start WITHOUT the kernel claim (red control: a "
                             "deleted record then admits a second door)")
    args = parser.parse_args(argv)

    overrides = dict((key, getattr(args, "%s_port" % key)) for key in PLAN_KEYS)
    ports = plan(args.host, overrides)
    registry_path = args.registry or launcher_registry.default_path()
    # R2940: the kernel claim comes FIRST, before the record and before any
    # child. A record is a file and a file can be deleted; the named mutex
    # cannot be, and the kernel drops it when the holder dies.
    mutex_name = args.mutex_name or launcher_mutex.name_for(registry_path)
    claim_mutex = {"available": launcher_mutex.available(),
                   "name": mutex_name, "held": False, "already": False,
                   "enabled": not args.no_mutex}
    mutex_handle = None
    if not args.no_mutex:
        lane = launcher_mutex.acquire(mutex_name)
        claim_mutex.update({"held": bool(lane.get("held")),
                            "already": bool(lane.get("already")),
                            "source": lane.get("source")})
        mutex_handle = lane.get("handle")
        if not lane.get("held"):
            holder = launcher_registry.read(registry_path) or {}
            refused = {
                "ok": False, "host": args.host, "hub_url": "",
                "ports": {}, "face_ports": {}, "faces": {}, "live": {},
                "children": [], "pids": {},
                "job": {"available": job_object.available(), "enabled": False,
                        "assigned": 0, "verified": False, "members": {},
                        "escaped": [], "errors": []},
                "mutex": claim_mutex,
                "registry": {"path": registry_path, "claimed": False,
                             "held_by": holder or None},
                "errors": ["%s source=mutex pid=%s name=%s"
                           % (launcher_mutex.REFUSED,
                              holder.get("pid") or "-", mutex_name)],
                "mock": True, "chargeable": False,
            }
            if args.report_json:
                write_report(args.report_json, refused)
            print(json.dumps(refused, ensure_ascii=False, sort_keys=True),
                  flush=True)
            return 2
    # R2939: the machine record is claimed BEFORE the first child exists, so a
    # second door is refused with zero processes started rather than after it
    # has already forked a sandbox beside the one it cannot see.
    claim = {
        "pid": os.getpid(),
        "ts": launcher_registry.stamp(),
        "host": args.host,
        "state": "starting",
        "hub_url": None,
        "ports": dict(ports),
        "face_ports": dict((key, ports[FACE_PORT_KEY[key]])
                           for key in FACE_KEYS),
    }
    claimed, holder, verdict = launcher_registry.claim(registry_path, claim)
    if not claimed:
        refused = {
            "ok": False, "host": args.host, "hub_url": "",
            "ports": {}, "face_ports": {}, "faces": {}, "live": {},
            "children": [], "pids": {},
            "job": {"available": job_object.available(), "enabled": False,
                    "assigned": 0, "verified": False, "members": {},
                    "escaped": [], "errors": []},
            "mutex": claim_mutex,
            "registry": {"path": registry_path, "claimed": False,
                         "held_by": holder, "verdict": verdict},
            "errors": ["%s pid=%s hub_url=%s reason=%s"
                       % (launcher_registry.REFUSED, verdict.get("pid"),
                          verdict.get("hub_url") or "-",
                          verdict.get("reason"))],
            "mock": True, "chargeable": False,
        }
        if args.report_json:
            write_report(args.report_json, refused)
        print(json.dumps(refused, ensure_ascii=False, sort_keys=True),
              flush=True)
        launcher_mutex.release(mutex_handle)
        return 2
    commands = build_commands(args.host, ports)
    group = start(commands, use_job=not args.no_job)
    code = 2
    try:
        ready, hub_url, faces, live, errors = verify(
            args.host, ports, args.timeout)
        # A child that could not be placed in the job is not a cosmetic
        # warning: the kill-on-close guarantee simply does not cover it, so
        # the round refuses instead of advertising a safety it does not have.
        for item in group.job_errors:
            errors.append("E_JOB_UNASSIGNED: " + item)
        ready = ready and not group.job_errors
        report = report_of(args.host, ports, hub_url, faces, live, errors,
                           group, claim_mutex)
        report["registry"] = {"path": registry_path, "claimed": True,
                              "pid": os.getpid(),
                              "state": "serving" if ready else "starting"}
        if ready:
            serving = dict(claim)
            serving["state"] = "serving"
            serving["hub_url"] = hub_url
            launcher_registry.write_serving(registry_path, serving)
            report["registry"]["published"] = True
        if args.report_json:
            write_report(args.report_json, report)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True), flush=True)
        code = 0 if ready else 2
        if not args.check and ready:
            while True:
                if args.stop_file and os.path.exists(args.stop_file):
                    break
                time.sleep(0.2)
    except KeyboardInterrupt:
        code = 0
    finally:
        launcher_registry.release(registry_path)
        launcher_mutex.release(mutex_handle)
        teardown(group)
    return code


if __name__ == "__main__":
    sys.exit(main())