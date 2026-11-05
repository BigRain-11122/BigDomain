"""One command that brings every sandbox face up and names the door to open.

The sandbox grew one surface at a time - the city read API, the WebSocket
lobby, the browser client, the content gate, the token ledger console, the UGC
console and the 19.9 checkout demo - and each lives in its own module on its
own port. A person who wanted to look at the whole thing had to remember five
commands and five URLs, and the hub page could only describe them: it is a
read-only face, so every card it publishes ended in "start this yourself".

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

HERE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(HERE, "lobby")

SERVER = os.path.join(LOBBY, "server.py")
CHECKOUT = os.path.join(LOBBY, "checkout_demo.py")
LEDGER = os.path.join(HERE, "ledger", "ledger_page.py")
UGC = os.path.join(HERE, "ugc", "ugc_page.py")

# The six faces the hub publishes with a real port behind them.
FACE_KEYS = ("lobby", "city", "checkout", "gate", "ledger", "ugc")
# Which planned socket carries each face (the lobby page and the WebSocket
# share the lobby module but not a port).
FACE_PORT_KEY = {"lobby": "web", "city": "city", "checkout": "checkout",
                 "gate": "gate", "ledger": "ledger", "ugc": "ugc"}
# Every socket this launcher must place: eight ports for six faces, because
# the lobby module owns the ws socket and the gate/web sockets itself.
PLAN_KEYS = ("ws", "city", "gate", "web", "hub", "checkout", "ledger", "ugc")

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
    ]
    return [
        ("lobby", lobby),
        ("checkout", [sys.executable, CHECKOUT, "--host", host,
                      "--port", str(ports["checkout"])]),
        ("ledger", [sys.executable, LEDGER, "--host", host,
                    "--port", str(ports["ledger"])]),
        ("ugc", [sys.executable, UGC, "--host", host,
                 "--port", str(ports["ugc"])]),
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


def start(commands):
    """Start every vector quietly and return the live children."""
    children = []
    for name, argv in commands:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=NO_WINDOW,
        )
        children.append((name, proc))
    return children


def teardown(children):
    """Stop every child this process started; no orphan keeps a sandbox port."""
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


def report_of(host, ports, hub_url, faces, live, errors):
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
    args = parser.parse_args(argv)

    overrides = dict((key, getattr(args, "%s_port" % key)) for key in PLAN_KEYS)
    ports = plan(args.host, overrides)
    children = start(build_commands(args.host, ports))
    code = 2
    try:
        ready, hub_url, faces, live, errors = verify(
            args.host, ports, args.timeout)
        report = report_of(args.host, ports, hub_url, faces, live, errors)
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
        teardown(children)
    return code


if __name__ == "__main__":
    sys.exit(main())