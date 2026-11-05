"""Content-gate console: the shipped msgSecCheck stub as a face a person can use.

BLUEPRINT section five makes the content gate a life-or-death surface: no
generated content reaches a reader before it has been through the gate. Until
this face existed that gate could only be driven from a terminal
(``python src/sandbox/lobby/msgsec_stub.py --check TEXT``), so a reader could
not see what the gate actually decides or why.

This module serves three things and nothing else:

  GET  /gate and /gate/           the page bytes, read from disk
  GET  /gate/api/contract        the endpoint contract the REAL WeChat
                                 msgSecCheck v2 must satisfy, taken from
                                 msgsec_stub.contract() at CALL time
  POST /gate/api/check           run the SHIPPED stub over the submitted text
                                 and return its own response object unchanged,
                                 plus one DERIVED key http_decision

The check is a pure function call on the shipped stub: nothing is written,
nothing is stored, and no second wordlist or classifier lives here. The
decision key is derived through the stub own is_risky / needs_review helpers, so
the mapping from suggest to transport action has exactly one owner.

Fail-closed stays where it already was: a stub built without wordlists raises
GateOfflineError at construction, so this face cannot exist without a working
gate. The stub answers from the live config wordlists with mock=true and
billable=false on every response, and the page says on screen that the real
msgSecCheck waits on a CEO physical item (mini-program appid/secret).
"""

import json
import os
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import msgsec_stub

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_NAME = "gate.html"
ROUTES = ("/gate", "/gate/")
CONTRACT_ROUTE = "/gate/api/contract"
CHECK_ROUTE = "/gate/api/check"

E_GC_METHOD = "E_GC_METHOD"
E_GC_BAD_JSON = "E_GC_BAD_JSON"
E_GC_BAD_CONTENT = "E_GC_BAD_CONTENT"
E_GC_TOO_LONG = "E_GC_TOO_LONG"

# A console call carries one sentence, not a document. The cap bounds memory
# before any gate work happens and is reported as its own refusal.
MAX_BODY = 65536

ACTION_SERVE = "SERVE"
ACTION_REVIEW = "REVIEW"
ACTION_REFUSE = "REFUSE"


def decision_for(stub, resp):
    """Map a gate response to the transport decision, using the stub own helpers."""
    if stub.is_risky(resp):
        return ACTION_REFUSE
    if stub.needs_review(resp):
        return ACTION_REVIEW
    return ACTION_SERVE


class GatePageHandler(BaseHTTPRequestHandler):
    """HTTP face for the content-gate console."""

    stub = None  # wired at startup
    max_len = 2000
    page_path = os.path.join(HERE, PAGE_NAME)

    def _send_page(self):
        try:
            with open(self.page_path, "rb") as handle:
                body = handle.read()
        except OSError:
            self._send(503, {"error": "gate page missing on disk", "code": "E_GC_NO_PAGE"})
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
        if path == CONTRACT_ROUTE:
            self._send(200, msgsec_stub.contract())
            return
        if path == CHECK_ROUTE:
            self._send(405, {"error": "method not allowed: POST only",
                             "code": E_GC_METHOD})
            return
        self._send(404, {"error": "not found: GET /gate/, GET /gate, "
                                  "GET /gate/api/contract only"})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path != CHECK_ROUTE:
            self._send(404, {"error": "not found: POST /gate/api/check only"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            length = 0
        if length <= 0 or length > MAX_BODY:
            self._send(400, {"error": "no usable body", "code": E_GC_BAD_CONTENT})
            return
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            self._send(400, {"error": "body is not utf-8 json", "code": E_GC_BAD_JSON})
            return
        if not isinstance(payload, dict):
            self._send(400, {"error": "body is not an object", "code": E_GC_BAD_JSON})
            return
        content = payload.get("content")
        if content is None or not str(content).strip():
            self._send(400, {"error": "content is required and non-blank",
                             "code": E_GC_BAD_CONTENT})
            return
        text = str(content)
        if len(text) > int(self.max_len):
            self._send(413, {"error": "content longer than the configured limit",
                             "code": E_GC_TOO_LONG, "max_len": int(self.max_len)})
            return
        resp = dict(self.stub.check(text))
        resp["http_decision"] = decision_for(self.stub, resp)
        self._send(200, resp)

    def _not_allowed(self):
        self._send(405, {"error": "method not allowed on the gate console",
                         "code": E_GC_METHOD})

    def do_PUT(self):
        self._not_allowed()

    def do_DELETE(self):
        self._not_allowed()

    def do_PATCH(self):
        self._not_allowed()

    def log_message(self, fmt, *args):
        pass


def start_gate_http(host, port, stub, max_len=2000):
    """Start the console on its own thread; returns the server object.

    The caller may pass port 0 (the suites do) and read the real bound port back
    from server.server_address[1], so nothing here ever guesses a port.
    """
    handler = type("BoundGatePageHandler", (GatePageHandler,),
                   {"stub": stub, "max_len": int(max_len)})
    httpd = ThreadingHTTPServer((host, port), handler)
    threading.Thread(target=httpd.serve_forever, name="sandbox-gate-console",
                     daemon=True).start()
    return httpd