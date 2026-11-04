"""Clickable 19.9 entrance checkout for the lobby sandbox (BigDomain P-47-4).

The lobby already ships two business modules - pay_mock.py (mock 19.9 order,
receipt and month card, never chargeable) and msgsec_stub.py (WeChat
msgSecCheck v2 response shape over the shipped wordlists) - but until this
module nothing human could operate them without a terminal: the parity check
and the two-client interop demo are both command-line runs.

This module serves one self-contained page plus four same-origin JSON routes:

    GET  /checkout, /checkout/      the page on disk, served byte for byte
    GET  /checkout/api/state        entitlement for ?actor=<name>
    POST /checkout/api/order        create the mock 19.9 entrance order
    POST /checkout/api/pay          pay it and grant the mock month card
    POST /checkout/api/send         entrance gate, then content gate, then accept

Laws carried from the shipped faces, never re-implemented here:

  - the payment channel is pay_mock.PayMock; every object it returns reads
    mock=true / chargeable=false, and this module never books money;
  - the content gate is msgsec_stub.MsgSecStub, fail-closed: an unwired gate
    refuses (503) rather than passing;
  - entrance gate FIRST: an actor without an active entitlement is refused
    E_ENTRANCE_REQUIRED before the content gate is asked at all;
  - zero network egress: the page is read from disk, every fetch target in
    it is a same-origin /checkout/... path, and the server makes no outbound
    call.

Pre-registered criteria AC-CKD1..AC-CKD6 live in the R2459 backlog row and
were written before this code existed (honesty law).

Stdlib only. Source is pure ASCII; the page is the only non-ASCII file.
"""

import argparse
import json
import os
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from msgsec_stub import (
    SUGGEST_PASS,
    SUGGEST_REVIEW,
    SUGGEST_RISKY,
    MsgSecStub,
)
from pay_mock import PayMock, PayMockError, contract as pay_contract

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_NAME = "checkout.html"
DEFAULT_CONFIG = os.path.join(HERE, "config.json")

MAX_BODY_BYTES = 8192

E_ENTRANCE_REQUIRED = "E_ENTRANCE_REQUIRED"
E_CONTENT_REJECTED = "E_CONTENT_REJECTED"
E_CONTENT_REVIEW = "E_CONTENT_REVIEW"
E_BAD_BODY = "E_BAD_BODY"
E_GATE_OFFLINE = "E_GATE_OFFLINE"

# Status per shipped refusal code, so a caller can be written once.
PAY_STATUS = {
    "E_PAYMOCK_BAD_ACTOR": 400,
    "E_PAYMOCK_BAD_AMOUNT": 400,
    "E_PAYMOCK_UNKNOWN_ORDER": 404,
    "E_PAYMOCK_STUB_ONLY": 403,
}


class DemoError(Exception):
    """A refusal this face owns, carrying its own HTTP status."""

    def __init__(self, code, status, detail="", extra=None):
        super().__init__(code + (": " + detail if detail else ""))
        self.code = code
        self.status = int(status)
        self.detail = detail
        self.extra = dict(extra or {})


class CheckoutDemo:
    """The whole business flow, in memory, over the two shipped modules."""

    def __init__(self, pay=None, stub=None):
        self.pay = pay if pay is not None else PayMock()
        self.stub = stub
        self.counts = {"gate_calls": 0}

    # -- write face -------------------------------------------------

    def create_order(self, actor):
        return self.pay.create_order(actor)

    def pay_order(self, order_id):
        """Pay the mock order and grant the month card exactly once.

        A replayed pay returns the very same receipt (pay_mock own law) and
        therefore reuses the entitlement that was granted on the first call.
        """
        receipt = self.pay.pay(order_id)
        actor = receipt["actor"]
        entitlement = self.pay.entitlement_of(actor)
        if entitlement is None:
            entitlement = self.pay.grant_month_card(actor)
        return {"receipt": receipt, "entitlement": entitlement}

    def send(self, actor, text):
        """Entrance gate, then content gate, then accept."""
        actor = str(actor or "").strip()
        if not actor:
            raise DemoError(E_BAD_BODY, 400, "actor required")
        entitlement = self.pay.entitlement_of(actor)
        if not entitlement or not entitlement.get("active"):
            raise DemoError(
                E_ENTRANCE_REQUIRED,
                403,
                "no active entrance entitlement for " + actor,
            )
        if self.stub is None:
            raise DemoError(E_GATE_OFFLINE, 503, "content gate unwired")
        self.counts["gate_calls"] += 1
        resp = self.stub.check(text, actor)
        result = resp.get("result") or {}
        suggest = result.get("suggest")
        decision = {
            "suggest": suggest,
            "label": result.get("label"),
            "trace_id": resp.get("trace_id"),
            "provider": resp.get("provider"),
            "mock": resp.get("mock"),
        }
        if suggest == SUGGEST_RISKY:
            raise DemoError(
                E_CONTENT_REJECTED,
                422,
                "content gate reads risky",
                extra={"decision": decision},
            )
        if suggest == SUGGEST_REVIEW:
            raise DemoError(
                E_CONTENT_REVIEW,
                422,
                "content gate reads review (human queue)",
                extra={"decision": decision},
            )
        if suggest != SUGGEST_PASS:
            raise DemoError(
                E_GATE_OFFLINE, 503, "content gate answered an unknown suggest",
                extra={"decision": decision},
            )
        return {
            "accepted": True,
            "actor": actor,
            "text": "" if text is None else str(text),
            "ai_generated": False,
            "server_authoritative": True,
            "decision": decision,
        }

    # -- read face --------------------------------------------------

    def state(self, actor):
        actor = str(actor or "").strip()
        entitlement = self.pay.entitlement_of(actor)
        return {
            "actor": actor,
            "entrance_active": bool(entitlement and entitlement.get("active")),
            "entitlement": entitlement,
            "contract": pay_contract(),
            "counts": dict(self.counts),
        }


class CheckoutHandler(BaseHTTPRequestHandler):
    """Five routes, all same-origin; everything else 404 or 405."""

    demo = None  # wired at startup
    page_path = os.path.join(HERE, PAGE_NAME)

    # -- plumbing ---------------------------------------------------

    def _send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
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
            self._send_json(503, {"error": "checkout page missing on disk"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = self.headers.get("Content-Length")
        if not length:
            return {}
        try:
            size = int(length)
        except (TypeError, ValueError):
            raise DemoError(E_BAD_BODY, 400, "bad content-length")
        if size < 0 or size > MAX_BODY_BYTES:
            raise DemoError(E_BAD_BODY, 400, "body too large")
        raw = self.rfile.read(size)
        if not raw:
            return {}
        try:
            obj = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise DemoError(E_BAD_BODY, 400, "body must be json")
        if not isinstance(obj, dict):
            raise DemoError(E_BAD_BODY, 400, "body must be a json object")
        return obj

    def _dispatch(self, route):
        try:
            payload = self._read_body()
            if route == "/checkout/api/order":
                order = self.demo.create_order(payload.get("actor"))
                self._send_json(201, {"order": order})
                return
            if route == "/checkout/api/pay":
                out = self.demo.pay_order(payload.get("order_id"))
                self._send_json(200, out)
                return
            if route == "/checkout/api/send":
                out = self.demo.send(payload.get("actor"), payload.get("text"))
                self._send_json(200, out)
                return
        except DemoError as exc:
            body = {"error": exc.code, "detail": exc.detail}
            body.update(exc.extra)
            self._send_json(exc.status, body)
            return
        except PayMockError as exc:
            self._send_json(
                PAY_STATUS.get(exc.code, 400),
                {"error": exc.code, "detail": exc.detail},
            )
            return
        self._send_json(404, {"error": "not found: " + route})

    # -- verbs ------------------------------------------------------

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path in ("/checkout", "/checkout/"):
            self._send_page()
            return
        if path == "/checkout/api/state":
            query = urllib.parse.parse_qs(parsed.query or "")
            actor = (query.get("actor") or [""])[0]
            self._send_json(200, self.demo.state(actor))
            return
        self._send_json(404, {"error": "not found: " + path})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path.startswith("/checkout/api/"):
            self._dispatch(path)
            return
        self._send_json(404, {"error": "not found: " + path})

    def _method_reject(self):
        self._send_json(405, {"error": "method not allowed on the checkout face"})

    def do_PUT(self):
        self._method_reject()

    def do_DELETE(self):
        self._method_reject()

    def do_PATCH(self):
        self._method_reject()

    def log_message(self, fmt, *args):
        pass


def start_server(host, port, demo):
    """Start the checkout face on its own thread; returns the server object.

    The real bound port is at server.server_address[1], so a caller can pass
    port 0 and read back what the OS assigned.
    """
    handler = type("BoundCheckoutHandler", (CheckoutHandler,), {"demo": demo})
    httpd = ThreadingHTTPServer((host, port), handler)
    threading.Thread(target=httpd.serve_forever, name="checkout-demo",
                     daemon=True).start()
    return httpd


def build_demo(config_path=DEFAULT_CONFIG, with_gate=True):
    """Build the demo over the shipped modules; an unwired gate stays None."""
    stub = None
    if with_gate:
        with open(config_path, "r", encoding="utf-8") as handle:
            cfg = json.load(handle)
        stub = MsgSecStub.from_config(cfg)
    return CheckoutDemo(PayMock(), stub)


def main():
    parser = argparse.ArgumentParser(
        description="19.9 entrance checkout sandbox (mock channel, never chargeable)"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8093)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--no-gate", action="store_true",
                        help="serve the page with the content gate unwired (send reads 503)")
    args = parser.parse_args()

    demo = build_demo(args.config, with_gate=not args.no_gate)
    httpd = start_server(args.host, args.port, demo)
    port = httpd.server_address[1]
    print("CHECKOUT DEMO on http://%s:%d/checkout/" % (args.host, port))
    print("channel=mock chargeable=false gate=%s"
          % ("unwired" if demo.stub is None else "wordlist-stub"))
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())