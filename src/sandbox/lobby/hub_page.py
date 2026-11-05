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


class HubPageHandler(BaseHTTPRequestHandler):
    """Read-only HTTP face for the sandbox entry page."""

    faces = {}  # wired at startup
    page_path = os.path.join(HERE, PAGE_NAME)

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
        path = urllib.parse.urlparse(self.path).path
        if path in ROUTES:
            self._send_page()
            return
        if path == FACES_ROUTE:
            self._send(200, dict(self.faces))
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


def build_faces(host, ws_port, web_port=None, city_port=None, checkout_port=8093):
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
    return faces


def start_hub_http(host, port, faces):
    """Start the entry face on its own thread; returns the server object.

    The real bound port is at server.server_address[1], so a caller may pass
    port 0 (tests do) and read back what the OS assigned.
    """
    handler = type("BoundHubPageHandler", (HubPageHandler,), {"faces": dict(faces)})
    httpd = ThreadingHTTPServer((host, port), handler)
    threading.Thread(target=httpd.serve_forever, name="sandbox-hub", daemon=True).start()
    return httpd