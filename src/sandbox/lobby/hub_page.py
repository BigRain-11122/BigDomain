"""Sandbox entry face: one page that lists every face a person can open.

The sandbox grew one surface at a time - the city page, the lobby client, the
19.9 checkout demo - and each lives on its own port, so a reader had to
remember three commands and three URLs. This face ties them together and, more
importantly, publishes the REAL bound ports as JSON from the same server that
owns the socket, so the page never guesses a port and never hardcodes one.

Read-only over HTTP: GET /hub and GET /hub/ serve the page bytes from disk,
GET /hub/api/faces answers the face list, everything else is 404 and every
non-GET method is 405. The page is the single source of truth on disk - no
template rendering and no build step.

Honesty law: the face list states what each URL is, not that it is alive. The
lobby and the city are started by this same process and their ports are the
bound ones; the checkout demo is a separate process and its URL carries a note
saying so, because claiming liveness for a port nobody is listening on would be
a lie a reader can disprove in one click.
"""

import json
import os
import socket
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_NAME = "hub.html"
ROUTES = ("/hub", "/hub/")
FACES_ROUTE = "/hub/api/faces"

CHECKOUT_NOTE = ("the 19.9 checkout demo is a separate process - start "
                 "python src/sandbox/lobby/checkout_demo.py --port %d to make "
                 "this link live")

LEDGER_CMD = "python src/sandbox/ledger/ledger_page.py --port %d"
LEDGER_NOTE = ("the token ledger console is a separate process - start "
               + LEDGER_CMD + " to make this link live")

UGC_CMD = "python src/sandbox/ugc/ugc_page.py --port %d"
UGC_NOTE = ("the UGC console is a separate process - start "
            + UGC_CMD + " to make this link live")

PROBE_PARAMS = ("1", "true", "yes", "on")


def face_live(host, port, timeout=0.35):
    """True when something is really listening on that port right now.

    A TCP connect is the cheapest honest liveness test: it needs no HTTP
    contract from the other process and it cannot be satisfied by a page that
    merely names a port. A refused or timed-out connect is a dead face, never
    an unknown one.
    """
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


class HubPageHandler(BaseHTTPRequestHandler):
    """Read-only HTTP face for the sandbox entry page."""

    faces = {}  # wired at startup
    probe_host = "127.0.0.1"
    page_path = os.path.join(HERE, PAGE_NAME)

    def _faces_payload(self, probe):
        """The published faces, plus a measured live map when asked to probe.

        The map is recomputed on every probing request and never stored, so a
        face that died since the last call cannot keep reading alive.
        """
        payload = dict(self.faces)
        if probe:
            ports = payload.get("face_ports") or {}
            payload["live"] = dict(
                (face_id, face_live(self.probe_host, port))
                for face_id, port in sorted(ports.items())
            )
        return payload

    def _send_page(self):
        try:
            with open(self.page_path, "rb") as handle:
                body = handle.read()
        except OSError:
            self._send(503, {"error": "hub page missing on disk"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path in ROUTES:
            self._send_page()
            return
        if path == FACES_ROUTE:
            query = urllib.parse.parse_qs(parsed.query)
            probe = any(value.strip().lower() in PROBE_PARAMS
                        for value in query.get("probe", []))
            self._send(200, self._faces_payload(probe))
            return
        self._send(404, {"error": "not found: GET /hub/, GET /hub and "
                                  "GET /hub/api/faces only"})

    def _read_only(self):
        self._send(405, {"error": "method not allowed: the hub face is read-only"})

    def do_POST(self):
        self._read_only()

    def do_PUT(self):
        self._read_only()

    def do_DELETE(self):
        self._read_only()

    def do_PATCH(self):
        self._read_only()

    def log_message(self, fmt, *args):
        pass


def build_faces(host, ws_port, web_port=None, city_port=None, checkout_port=8093,
                gate_port=None, ledger_port=8097, ugc_port=8098):
    """Compose the face list from the ports this process really bound.

    Every URL is derived here from a port handed in by the caller, so a suite
    can compare the published URL against the port it configured instead of a
    literal. A face whose port is None is simply not published rather than
    published with a guess.
    """
    faces = {
        "mock": True,
        "chargeable": False,
        "read_only": True,
        "ws": "ws://%s:%d/ws" % (host, int(ws_port)),
        "ws_port": int(ws_port),
        "ws_path": "/ws",
    }
    if web_port is not None:
        faces["lobby"] = "http://%s:%d/lobby/" % (host, int(web_port))
        faces["lobby_note"] = "started by this process (--web-port)"
    if city_port is not None:
        faces["city"] = "http://%s:%d/city/" % (host, int(city_port))
        faces["city_note"] = "started by this process (--city-http-port)"
    if checkout_port is not None:
        faces["checkout"] = "http://%s:%d/checkout/" % (host, int(checkout_port))
        faces["checkout_note"] = CHECKOUT_NOTE % int(checkout_port)
    if gate_port is not None:
        faces["gate"] = "http://%s:%d/gate/" % (host, int(gate_port))
        faces["gate_note"] = "started by this process (--gate-port)"
    if ledger_port is not None:
        faces["ledger"] = "http://%s:%d/ledger/" % (host, int(ledger_port))
        faces["ledger_note"] = LEDGER_NOTE % int(ledger_port)
        faces["ledger_cmd"] = LEDGER_CMD % int(ledger_port)
    if ugc_port is not None:
        faces["ugc"] = "http://%s:%d/ugc/" % (host, int(ugc_port))
        faces["ugc_note"] = UGC_NOTE % int(ugc_port)
        faces["ugc_cmd"] = UGC_CMD % int(ugc_port)
    ports = {}
    for face_id, port in (("lobby", web_port), ("city", city_port),
                          ("checkout", checkout_port), ("gate", gate_port),
                          ("ledger", ledger_port), ("ugc", ugc_port)):
        if port is not None:
            ports[face_id] = int(port)
    faces["face_ports"] = ports
    return faces


def start_hub_http(host, port, faces):
    """Start the entry face on its own thread; returns the server object.

    The real bound port is at server.server_address[1], so a caller may pass
    port 0 (tests do) and read back what the OS assigned.
    """
    handler = type("BoundHubPageHandler", (HubPageHandler,),
                   {"faces": dict(faces), "probe_host": host})
    httpd = ThreadingHTTPServer((host, port), handler)
    threading.Thread(target=httpd.serve_forever, name="sandbox-hub", daemon=True).start()
    return httpd