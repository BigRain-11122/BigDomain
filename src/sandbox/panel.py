"""Sandbox control panel: the one door that can actually START a face.

R2477 shipped one terminal command that brings every face up, and said plainly
what it did not do: the hub page is read-only, so a person in a browser could
never start anything. Every card it published ended in "start this yourself",
and a face started from a terminal stayed invisible to any page.

This module closes that. It serves one page with a Start and a Stop verb per
face, and the start route really spawns the shipped entry module on an
OS-assigned port, waits until that socket accepts, and hands back the URL it
measured - so a click is enough and no port is ever assumed free.

What it starts: the checkout demo, the token ledger console and the UGC console
are each their own process and their own module, so each gets one OS-assigned
port. The lobby server owns the ws, city, web, hub and gate sockets in ONE
process, so it is started with a whole set of ports assigned up front and is
proved by its hub port - the address a person actually opens. A panel that
printed a lobby URL nobody had measured would be lying, so the lobby counts as
live only when its hub socket accepts a connection at the moment of reading.

Honesty law: nothing is reported live because it was launched. A face reads
live only when its port accepts a connection at the moment of the reading, and
a refusal names its own error code rather than pretending success.
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_NAME = "panel.html"
ROUTES = ("/panel", "/panel/")
STATE_ROUTE = "/panel/api/state"
START_ROUTE = "/panel/api/start"
STOP_ROUTE = "/panel/api/stop"

CHECKOUT = os.path.join(HERE, "lobby", "checkout_demo.py")
LEDGER = os.path.join(HERE, "ledger", "ledger_page.py")
UGC = os.path.join(HERE, "ugc", "ugc_page.py")
LOBBY = os.path.join(HERE, "lobby", "server.py")
MEMBER = os.path.join(HERE, "member", "member_page.py")
LEDGER_CONFIG = os.path.join(HERE, "ledger", "config.json")

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# face id -> (module path, published path, command template)
FACE_MODULES = {
    "checkout": (CHECKOUT, "/checkout/",
                 "python src/sandbox/lobby/checkout_demo.py --host %s --port %d"),
    "ledger": (LEDGER, "/ledger/",
               "python src/sandbox/ledger/ledger_page.py --host %s --port %d"),
    "ugc": (UGC, "/ugc/",
            "python src/sandbox/ugc/ugc_page.py --host %s --port %d"),
    "member": (MEMBER, "/member/",
               "python src/sandbox/member/member_page.py --host %s --port %d"),
}
# The lobby is one process holding five sockets; the hub socket is the face a
# person opens, so the hub port is what this panel publishes and measures.
LOBBY_PORT_KEYS = ("ws", "city", "web", "hub", "gate")
LOBBY_FLAGS = {
    "ws": "--port",
    "city": "--city-http-port",
    "web": "--web-port",
    "hub": "--hub-port",
    "gate": "--gate-port",
}
LOBBY_PATH = "/hub/"
FACE_IDS = ("checkout", "ledger", "member", "ugc", "lobby")

MOCK_STATEMENT = (
    "MOCK / NO REAL CHARGE: every face this panel starts runs the sandbox "
    "build with mock=true and chargeable=false, so no money moves and no real "
    "account is touched.")

START_TIMEOUT_S = 25.0
STOP_TIMEOUT_S = 3.0


def free_port(host="127.0.0.1"):
    """An OS-assigned free port, never a guess that 8097 is free."""
    sock = socket.socket()
    try:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


def can_connect(host, port, timeout=0.35):
    """True when something is really listening on that port right now."""
    if not port:
        return False
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


def read_notices(path=LEDGER_CONFIG):
    """The standing surfaces, read from disk at CALL time - never hardcoded."""
    notices = {"ai_label": "", "disclaimer": ""}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            cfg = json.load(handle)
    except (OSError, ValueError):
        return notices
    token = (cfg or {}).get("token") or {}
    notices["ai_label"] = token.get("ai_label_text") or ""
    notices["disclaimer"] = token.get("disclaimer") or ""
    return notices


class Panel(object):
    """The children this panel owns; nothing else is ever terminated."""

    def __init__(self, host="127.0.0.1", timeout=START_TIMEOUT_S):
        self.host = host
        self.timeout = float(timeout)
        self.lock = threading.Lock()
        self.children = {}  # face id -> {"port": int, "proc": Popen}

    def url_of(self, face_id, port):
        if face_id == "lobby":
            return "http://%s:%d%s" % (self.host, int(port), LOBBY_PATH)
        return "http://%s:%d%s" % (self.host, int(port),
                                   FACE_MODULES[face_id][1])

    def cmd_of(self, face_id, ports=None):
        if face_id == "lobby":
            parts = []
            for key in LOBBY_PORT_KEYS:
                parts.append(LOBBY_FLAGS[key])
                parts.append(str(int(ports[key])) if ports else "0")
            return "python src/sandbox/lobby/server.py --host %s %s" % (
                self.host, " ".join(parts))
        template = FACE_MODULES[face_id][2]
        return template % (self.host, int(ports) if ports else 0)

    def module_of(self, face_id):
        path = LOBBY if face_id == "lobby" else FACE_MODULES[face_id][0]
        return os.path.relpath(path, os.path.dirname(HERE))

    def face_rows(self):
        rows = []
        with self.lock:
            snapshot = dict(self.children)
        for face_id in FACE_IDS:
            entry = snapshot.get(face_id)
            port = entry["port"] if entry else None
            ports = entry.get("ports") if entry else None
            cmd_ports = ports if face_id == "lobby" else port
            alive = bool(entry) and entry["proc"].poll() is None
            live = alive and can_connect(self.host, port) if port else False
            rows.append({
                "id": face_id,
                "port": port,
                "url": self.url_of(face_id, port) if port else None,
                "live": bool(live),
                "started": bool(entry),
                "cmd": self.cmd_of(face_id, cmd_ports),
                "module": self.module_of(face_id),
            })
        return rows

    def state_payload(self):
        notices = read_notices()
        return {
            "host": self.host,
            "mock": True,
            "chargeable": False,
            "read_only": False,
            "faces": self.face_rows(),
            "notices": {
                "ai_label": notices["ai_label"],
                "disclaimer": notices["disclaimer"],
                "mock_statement": MOCK_STATEMENT,
            },
            "startable": list(FACE_IDS),
        }

    def start(self, face_id):
        """Spawn one shipped module and prove it before claiming success."""
        if face_id not in FACE_IDS:
            return 400, {"error": "E_PANEL_UNKNOWN_FACE",
                         "detail": "startable: " + ",".join(FACE_IDS)}
        with self.lock:
            entry = self.children.get(face_id)
            if entry is not None and entry["proc"].poll() is None:
                return 409, {"error": "E_PANEL_ALREADY_RUNNING",
                             "face": face_id, "port": entry["port"]}
            ports = None
            if face_id == "lobby":
                ports = {}
                taken = set()
                for key in LOBBY_PORT_KEYS:
                    candidate = free_port(self.host)
                    while candidate in taken:
                        candidate = free_port(self.host)
                    taken.add(candidate)
                    ports[key] = candidate
                port = ports["hub"]
                argv = [sys.executable, LOBBY, "--host", self.host]
                for key in LOBBY_PORT_KEYS:
                    argv.extend([LOBBY_FLAGS[key], str(ports[key])])
            else:
                port = free_port(self.host)
                argv = [sys.executable, FACE_MODULES[face_id][0],
                        "--host", self.host, "--port", str(port)]
            proc = subprocess.Popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=NO_WINDOW,
            )
            self.children[face_id] = {"port": port, "proc": proc,
                                      "ports": ports}
        if not wait_port(self.host, port, self.timeout):
            self._kill(face_id)
            return 500, {"error": "E_PANEL_NOT_UP", "face": face_id,
                         "port": port,
                         "detail": "the module was launched but its port never "
                                   "accepted a connection"}
        body = {
            "face": face_id,
            "port": port,
            "url": self.url_of(face_id, port),
            "live": True,
            "mock": True,
            "chargeable": False,
            "cmd": self.cmd_of(face_id, ports if face_id == "lobby" else port),
        }
        if ports:
            body["ports"] = dict(ports)
        return 200, body

    def stop(self, face_id):
        with self.lock:
            entry = self.children.get(face_id)
        if entry is None:
            return 404, {"error": "E_PANEL_NOT_STARTED", "face": face_id}
        port = entry["port"]
        self._kill(face_id)
        deadline = time.time() + STOP_TIMEOUT_S
        while time.time() < deadline and can_connect(self.host, port):
            time.sleep(0.05)
        return 200, {"face": face_id, "port": port, "stopped": True,
                     "live": can_connect(self.host, port)}

    def _kill(self, face_id):
        with self.lock:
            entry = self.children.pop(face_id, None)
        if not entry:
            return
        proc = entry["proc"]
        if proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
        deadline = time.time() + STOP_TIMEOUT_S
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.05)
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass

    def stop_all(self):
        with self.lock:
            face_ids = list(self.children)
        for face_id in face_ids:
            self._kill(face_id)


class PanelHandler(BaseHTTPRequestHandler):
    """One page plus three JSON routes: state, start, stop."""

    panel = None  # wired at startup
    page_path = os.path.join(HERE, PAGE_NAME)

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False,
                          sort_keys=True).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_page(self):
        try:
            with open(self.page_path, "rb") as handle:
                body = handle.read()
        except OSError:
            self._send(503, {"error": "panel page missing on disk"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            length = 0
        if length <= 0:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ROUTES:
            self._send_page()
            return
        if path == STATE_ROUTE:
            self._send(200, self.panel.state_payload())
            return
        if path in (START_ROUTE, STOP_ROUTE):
            self._send(405, {"error": "method not allowed: POST only"})
            return
        self._send(404, {"error": "not found: GET /panel/ and "
                                  "GET /panel/api/state only"})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path not in (START_ROUTE, STOP_ROUTE):
            if path in ROUTES or path == STATE_ROUTE:
                self._send(405, {"error": "method not allowed: GET only"})
            else:
                self._send(404, {"error": "not found: POST " + path})
            return
        payload = self._body()
        if not isinstance(payload, dict):
            self._send(400, {"error": "E_PANEL_BAD_FACE",
                             "detail": "expected a JSON object with a face key"})
            return
        face_id = payload.get("face")
        if not isinstance(face_id, str) or not face_id.strip():
            self._send(400, {"error": "E_PANEL_BAD_FACE",
                             "detail": "the face key is required"})
            return
        face_id = face_id.strip()
        if path == START_ROUTE:
            code, obj = self.panel.start(face_id)
        else:
            code, obj = self.panel.stop(face_id)
        self._send(code, obj)

    def _method_not_allowed(self):
        self._send(405, {"error": "method not allowed: GET and POST only"})

    def do_PUT(self):
        self._method_not_allowed()

    def do_DELETE(self):
        self._method_not_allowed()

    def do_PATCH(self):
        self._method_not_allowed()

    def log_message(self, fmt, *args):
        pass


class PanelServer(ThreadingHTTPServer):
    """Threading server that takes its children down with it."""

    def __init__(self, address, handler, panel):
        self.panel = panel
        ThreadingHTTPServer.__init__(self, address, handler)

    def shutdown(self):
        try:
            self.panel.stop_all()
        finally:
            ThreadingHTTPServer.shutdown(self)


def start_panel(host, port, timeout=START_TIMEOUT_S):
    """Start the panel on its own thread; returns (server, panel).

    Pass port 0 and read server.server_address[1] for the real bound port.
    """
    panel = Panel(host=host, timeout=timeout)
    handler = type("BoundPanelHandler", (PanelHandler,), {"panel": panel})
    httpd = PanelServer((host, port), handler, panel)
    threading.Thread(target=httpd.serve_forever, name="sandbox-panel",
                     daemon=True).start()
    return httpd, panel


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="control panel: start and stop the sandbox faces from a page")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8099)
    parser.add_argument("--timeout", type=float, default=START_TIMEOUT_S)
    args = parser.parse_args(argv)
    httpd, panel = start_panel(args.host, args.port, args.timeout)
    print("PANEL http://%s:%d/panel/" % (args.host,
                                        httpd.server_address[1]), flush=True)
    try:
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
        httpd.server_close()
        panel.stop_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())