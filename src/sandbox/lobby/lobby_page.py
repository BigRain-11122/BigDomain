"""P-47-1b browser face: serve the shipped lobby client page.

The WebSocket server (server.py) speaks a JSON frame protocol that until this
module existed could only be driven from a terminal (interop_demo.py). This
face serves one self-contained HTML page so a person can open the lobby in a
browser, take the sandbox entrance and chat with a second window.

Read-only over HTTP: GET /lobby/ and GET /lobby serve the page bytes from disk,
GET /lobby/api/config answers the WebSocket port so the page never has to guess
it, everything else is 404 and every non-GET method is 405. The page itself is
the single source of truth on disk - no template rendering, no build step.
"""

import json
import os
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_NAME = "lobby.html"
ROUTES = ("/lobby", "/lobby/")
CONFIG_ROUTE = "/lobby/api/config"


class LobbyPageHandler(BaseHTTPRequestHandler):
    """Read-only HTTP face for the lobby client page."""

    ws_port = None  # wired at startup
    page_path = os.path.join(HERE, PAGE_NAME)

    def _send_page(self):
        try:
            with open(self.page_path, "rb") as handle:
                body = handle.read()
        except OSError:
            self._send(503, {"error": "lobby page missing on disk"})
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
        if path == CONFIG_ROUTE:
            self._send(200, {"ws_port": int(self.ws_port), "ws_path": "/ws"})
            return
        self._send(404, {"error": "not found: GET /lobby/ and GET /lobby/api/config only"})

    def _read_only(self):
        self._send(405, {"error": "method not allowed: the lobby page face is read-only"})

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


def start_lobby_http(host, port, ws_port):
    """Start the page face on its own thread; returns the server object.

    The real bound port is at server.server_address[1], so a caller may pass
    port 0 (tests do) and read back what the OS assigned.
    """
    handler = type("BoundLobbyPageHandler", (LobbyPageHandler,), {"ws_port": int(ws_port)})
    httpd = ThreadingHTTPServer((host, port), handler)
    threading.Thread(target=httpd.serve_forever, name="lobby-page", daemon=True).start()
    return httpd