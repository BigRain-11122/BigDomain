"""UGC pipeline console: the shipped P-47-3b pipeline as a face a person can use.

Until this face existed the whole UGC pipeline (pipeline.py, store.py,
wordlist.py, review.py, twenty-odd suites) could only be driven from a
terminal: a person could not submit a sentence, could not see whether it landed
as pass / review / risky, could not watch a gray-zone case wait for a human
verdict, and could not see the pool move.

This module serves four things and nothing else:

  GET  /ugc and /ugc/        the page bytes, read from disk
  GET  /ugc/api/state        suspended review rows read from the SHIPPED review
                             table, the SHIPPED pool_query items, per-line counts
                             derived from them, and the standing notices read
                             from config at CALL time
  POST /ugc/api/submit       grant the MOCK entrance through the SHIPPED
                             grant_entrance_sandbox, then hand the sentence to
                             the SHIPPED submit and return its receipt unchanged
  POST /ugc/api/verdict      drive the SHIPPED review_verdict

No second wordlist, classifier, routing rule or state machine lives here: the
gate, the routing, the gray-zone desk and the pool are the shipped modules, and
this face only calls them. A refused case is refused by the pipeline, never by
the console, so what a reader sees is what the pipeline really decided.
"""

import json
import os
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pipeline as UGC_PIPELINE
import store as UGC

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_NAME = "ugc_console.html"
ROUTES = ("/ugc", "/ugc/")
STATE_ROUTE = "/ugc/api/state"
SUBMIT_ROUTE = "/ugc/api/submit"
VERDICT_ROUTE = "/ugc/api/verdict"

E_UGW_METHOD = "E_UGW_METHOD"
E_UGW_BAD_JSON = "E_UGW_BAD_JSON"
E_UGW_BAD_CONTENT = "E_UGW_BAD_CONTENT"
E_UGW_TOO_LONG = "E_UGW_TOO_LONG"
E_UGW_BAD_VERDICT = "E_UGW_BAD_VERDICT"
E_UGW_UNKNOWN_CASE = "E_UGW_UNKNOWN_CASE"

# One console call carries one sentence, not a document. The cap bounds memory
# before any pipeline work happens and is reported as its own refusal.
MAX_BODY = 65536

VERDICTS = ("pass", "risky")

# Status per pipeline error code: the face maps a refusal, it never invents one.
STATUS_BY_CODE = {
    UGC.E_CONTENT_REJECTED: 422,
    UGC.E_ENTRANCE_REQUIRED: 403,
    UGC.E_RATE_LIMIT: 429,
    UGC.E_BAD_FRAME: 400,
    UGC.E_BAD_SOURCE: 400,
    UGC.E_SOURCE_BLOCKED: 403,
    UGC.E_BAD_VERDICT: 400,
    UGC.E_REVIEW_DONE: 409,
    UGC.E_NOT_FOUND: 404,
    UGC.E_DUPLICATE: 409,
}

PENDING_SQL = (
    "SELECT r.evt_id AS evt_id, r.ts_utc AS ts_utc,"
    " e.summary AS content FROM review_queue r"
    " LEFT JOIN ugc_events e ON e.evt_id = r.evt_id"
    " WHERE r.verdict IS NULL ORDER BY r.ts_utc"
)


def notices_from(config):
    """The standing surfaces, read from the live config on every call."""
    comp = config.get("compliance") or {}
    entrance = config.get("entrance") or {}
    return {
        "ai_label": comp.get("ai_label_text"),
        "disclaimer": comp.get("disclaimer"),
        "risk_note": comp.get("draft_risk_note"),
        "max_len": int(config.get("max_content_len") or 0),
        "entrance_mock": bool(entrance.get("mock")),
        "mock": True,
        "chargeable": False,
    }


def pending_cases(pipe):
    """Suspended review rows: the shipped review table, read through the store."""
    rows = pipe.store.read(PENDING_SQL)
    out = []
    for row in rows:
        out.append({"evt_id": row["evt_id"],
                    "ts_utc": row["ts_utc"],
                    "content": row["content"]})
    return out


def snapshot(pipe, config):
    """One derived state payload: every number comes off the shipped modules."""
    items = pipe.pool_query().get("items") or []
    counts = {}
    for item in items:
        line = item.get("line") or ""
        counts[line] = counts.get(line, 0) + 1
    return {
        "review": pending_cases(pipe),
        "pool": {"items": items},
        "pool_counts": counts,
        "notices": notices_from(config),
        "verified": True,
    }


class UgcPageHandler(BaseHTTPRequestHandler):
    """HTTP face for the UGC pipeline console."""

    pipe = None  # wired at startup
    config = None
    page_path = os.path.join(HERE, PAGE_NAME)

    def _send_page(self):
        try:
            with open(self.page_path, "rb") as handle:
                body = handle.read()
        except OSError:
            self._send(503, {"error": "ugc page missing on disk",
                             "code": "E_UGW_NO_PAGE"})
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

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            length = 0
        if length <= 0 or length > MAX_BODY:
            return None, (400, {"error": "no usable body", "code": E_UGW_BAD_CONTENT})
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return None, (400, {"error": "body is not utf-8 json", "code": E_UGW_BAD_JSON})
        if not isinstance(payload, dict):
            return None, (400, {"error": "body is not an object", "code": E_UGW_BAD_JSON})
        return payload, None

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ROUTES:
            self._send_page()
            return
        if path == STATE_ROUTE:
            self._send(200, snapshot(self.pipe, self.config))
            return
        if path in (SUBMIT_ROUTE, VERDICT_ROUTE):
            self._send(405, {"error": "method not allowed: POST only",
                             "code": E_UGW_METHOD})
            return
        self._send(404, {"error": "not found: GET /ugc/, GET /ugc, "
                                  "GET /ugc/api/state only"})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == STATE_ROUTE:
            self._send(405, {"error": "method not allowed: GET only",
                             "code": E_UGW_METHOD})
            return
        if path not in (SUBMIT_ROUTE, VERDICT_ROUTE):
            self._send(404, {"error": "not found: POST /ugc/api/submit, "
                                      "POST /ugc/api/verdict only"})
            return
        payload, refusal = self._read_json()
        if refusal is not None:
            self._send(refusal[0], refusal[1])
            return
        if path == SUBMIT_ROUTE:
            self._submit(payload)
        else:
            self._verdict(payload)

    def _submit(self, payload):
        content = payload.get("content")
        if content is None or not str(content).strip():
            self._send(400, {"error": "content is required and non-blank",
                             "code": E_UGW_BAD_CONTENT})
            return
        text = str(content)
        max_len = int(self.config.get("max_content_len") or 0)
        if max_len and len(text) > max_len:
            self._send(413, {"error": "content longer than the configured limit",
                             "code": E_UGW_TOO_LONG, "max_len": max_len})
            return
        actor = str(payload.get("actor") or "").strip() or "visitor"
        try:
            self.pipe.grant_entrance_sandbox(actor)
            receipt = self.pipe.submit("direct", actor, text)
        except UGC.PipelineError as exc:
            code = getattr(exc, "code", "E_PIPELINE")
            self._send(STATUS_BY_CODE.get(code, 400),
                       {"error": str(exc), "code": code, "actor": actor})
            return
        self._send(200, receipt)

    def _verdict(self, payload):
        evt_id = str(payload.get("evt_id") or "").strip()
        verdict = str(payload.get("verdict") or "").strip()
        if verdict not in VERDICTS:
            self._send(400, {"error": "verdict must be one of %s" % (list(VERDICTS),),
                             "code": E_UGW_BAD_VERDICT})
            return
        if not evt_id or self.pipe.store.review_row(evt_id) is None:
            self._send(404, {"error": "no review case with that evt_id",
                             "code": E_UGW_UNKNOWN_CASE, "evt_id": evt_id})
            return
        try:
            receipt = self.pipe.review_verdict(evt_id, verdict)
        except UGC.PipelineError as exc:
            code = getattr(exc, "code", "E_PIPELINE")
            self._send(STATUS_BY_CODE.get(code, 400),
                       {"error": str(exc), "code": code, "evt_id": evt_id})
            return
        self._send(200, {"evt_id": evt_id, "verdict": verdict, "receipt": receipt})

    def _not_allowed(self):
        self._send(405, {"error": "method not allowed on the ugc console",
                         "code": E_UGW_METHOD})

    def do_PUT(self):
        self._not_allowed()

    def do_DELETE(self):
        self._not_allowed()

    def do_PATCH(self):
        self._not_allowed()

    def log_message(self, fmt, *args):
        pass


def start_ugc_http(host, port, pipe, config):
    """Start the console on its own thread; returns the server object.

    The caller may pass port 0 (the suites do) and read the real bound port back
    from server.server_address[1], so nothing here ever guesses a port.
    """
    handler = type("BoundUgcPageHandler", (UgcPageHandler,),
                   {"pipe": pipe, "config": config})
    httpd = ThreadingHTTPServer((host, port), handler)
    threading.Thread(target=httpd.serve_forever, name="sandbox-ugc-console",
                     daemon=True).start()
    return httpd


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        description="BigDomain sandbox UGC pipeline console (P-47-3b)")
    parser.add_argument("--config", default=os.path.join(HERE, "config.json"))
    parser.add_argument("--db", default=os.path.join(HERE, "data", "ugc.db"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8098)
    args = parser.parse_args(argv)
    try:
        with open(args.config, encoding="utf-8") as handle:
            cfg = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print("E_GATE_OFFLINE: config unreadable: %s" % exc)
        return 2
    try:
        pipe = UGC_PIPELINE.UGCPipeline(cfg, args.db)
    except UGC_PIPELINE.GateOfflineError as exc:
        print(str(exc))
        return 2
    httpd = start_ugc_http(args.host, args.port, pipe, cfg)
    port = httpd.server_address[1]
    print("UGC CONSOLE http://%s:%d/ugc/ max_len=%d db=%s"
          % (args.host, port, int(cfg.get("max_content_len") or 0), args.db),
          flush=True)
    try:
        while True:
            threading.Event().wait(3600)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
        pipe.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())