"""Read-only city face for the sandbox lobby (BigDomain P-47-1c).

City running face absorbed per spec v0.2 (ledger P-2026-09-24-52(1),
server-city research referenced, not copied):
  census.query    (AC-S11): whitelist-only read; deep-water fields never
                  leave; honorary seats C-00001..09 render nothing;
                  off-whitelist field requests get E_FORBIDDEN_FIELD
  avatar.register (AC-S12): gate 1 + gate 2 -> intake queue (one public
                  event row) -> avatar.intake_receipt with evt_id; household
                  registration itself is BigLife T-04 (reference only -
                  this service just intakes and receipts); ungated content
                  never lands and never receipts
  HTTP GET read API (AC-S13): /city/snapshot and /census/<id> served from
                  the git read-only city dir; responses carry as_of; zero
                  write endpoints (405/404)

The city dir stands in for the production git read-only channel
(/opt/fluxcity mounted :ro). This module opens city files read-only only;
census rows are imported into the server's own SQLite for queries (import
SQLite + query API). Zero new collection, zero LLM (server-city section 3).
"""

import json
import os
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from sec_gate import ContentRejectedError
from store import utc_now_iso

E_FORBIDDEN_FIELD = "E_FORBIDDEN_FIELD"

MAX_NAME_LEN = 64
MAX_INTRO_LEN = 512
MAX_SUMMARY_LEN = 200


def _frame(kind, payload, evt_id=None):
    frame = {
        "v": 1,
        "type": kind,
        "ts_utc": utc_now_iso(),
        "actor": "system",
        "payload": payload,
        "ai_generated": False,
    }
    if evt_id:
        frame["evt_id"] = evt_id
    return frame


def _reject(code, reason):
    return _frame("sec.reject", {"code": code, "reason": reason})


def _load_census_rows(path):
    """Read the citizens-light jsonl import (git read-only channel)."""
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and str(obj.get("id", "")).strip():
                rows.append(obj)
    return rows


class CityFace:
    """Census whitelist reads + avatar intake + snapshot reads. Built from
    config (whitelist/honorary seats are data, per the encoding discipline)."""

    def __init__(self, cfg, gate, store, city_dir):
        self.cfg = cfg
        self.gate = gate
        self.store = store
        self.city_dir = city_dir
        self.whitelist = [str(f) for f in cfg.get("census_whitelist", []) if str(f)]
        self.honorary = set(str(s) for s in cfg.get("honorary_seats", []))
        self.census_file = str(cfg.get("census_file", "citizens-light.jsonl"))
        self.snapshot_file = str(cfg.get("snapshot_file", "world-public.json"))
        if not self.whitelist:
            raise ValueError("city.census_whitelist missing or empty")
        self.imported = self.store.import_census(_load_census_rows(self.census_path))

    @property
    def census_path(self):
        return os.path.join(self.city_dir, self.census_file)

    @property
    def snapshot_path(self):
        return os.path.join(self.city_dir, self.snapshot_file)

    # ---- AC-S11: census query (whitelist-only read) ----

    def census_fields(self, row, requested=None):
        keys = self.whitelist if requested is None else requested
        return {k: row[k] for k in keys if k in row}

    def census_snapshot_frame(self, msg):
        payload = msg.get("payload")
        payload = payload if isinstance(payload, dict) else {}
        cid = str(payload.get("id", "")).strip()
        if not cid:
            return _reject("E_BAD_FRAME", "census.query needs payload.id")
        requested = payload.get("fields")
        if requested is not None:
            if not isinstance(requested, list) or not all(isinstance(f, str) for f in requested):
                return _reject("E_BAD_FRAME", "payload.fields must be a list of strings")
            bad = [f for f in requested if f not in self.whitelist]
            if bad:
                return _reject(E_FORBIDDEN_FIELD, "field not in census whitelist: " + ",".join(bad))
        if cid in self.honorary:
            return _frame(
                "census.snapshot",
                {"id": cid, "found": True, "rendered": False, "fields": {},
                 "note": "reserved seat: zero render"},
            )
        row = self.store.census_lookup(cid)
        if row is None:
            return _frame("census.snapshot", {"id": cid, "found": False, "rendered": False, "fields": {}})
        return _frame(
            "census.snapshot",
            {"id": cid, "found": True, "rendered": True, "fields": self.census_fields(row, requested)},
        )

    # ---- AC-S12: avatar registration intake (queue = one public event row) ----

    def avatar_register_frame(self, actor, msg):
        payload = msg.get("payload")
        payload = payload if isinstance(payload, dict) else {}
        name = str(payload.get("name", "")).strip()[:MAX_NAME_LEN]
        intro = str(payload.get("intro", "")).strip()[:MAX_INTRO_LEN]
        text = (name + " " + intro).strip()
        if not text:
            return _reject("E_BAD_FRAME", "avatar.register needs payload.name / payload.intro")
        try:
            self.gate.check_text(text)
        except ContentRejectedError as exc:
            return _reject(exc.code, "gate %d wordlist hit" % exc.gate)
        summary = ("avatar intake: name=" + name + " intro=" + intro)[:MAX_SUMMARY_LEN]
        evt_id = self.store.append(
            utc_now_iso(),
            "avatar.intake",
            actor,
            "intake",
            summary,
            payload={"name": name, "intro": intro, "queue": "biglife-t04-reference"},
        )
        return _frame(
            "avatar.intake_receipt",
            {
                "received": True,
                "evt_id": evt_id,
                "note": "intake queued; household registration is BigLife T-04 (this service only intakes)",
            },
            evt_id=evt_id,
        )

    # ---- AC-S13: HTTP read API bodies ----

    def snapshot_body(self):
        """Read the world-public snapshot package (git read-only channel).
        Returns (http_status, body_obj); as_of comes from the package itself
        (tick-round-end export -> visitor-facing delay <= 20min upstream)."""
        if not os.path.exists(self.snapshot_path):
            return 503, {"error": "city snapshot not imported yet"}
        with open(self.snapshot_path, encoding="utf-8") as handle:
            try:
                obj = json.load(handle)
            except json.JSONDecodeError:
                return 503, {"error": "city snapshot is not valid JSON"}
        if not isinstance(obj, dict) or not obj.get("as_of"):
            return 503, {"error": "city snapshot malformed: as_of missing"}
        return 200, obj

    def census_http_body(self, cid):
        if cid in self.honorary:
            return 200, {"id": cid, "found": True, "rendered": False, "fields": {}}
        row = self.store.census_lookup(cid)
        if row is None:
            return 404, {"id": cid, "found": False}
        return 200, {"id": cid, "found": True, "rendered": True, "fields": self.census_fields(row)}


class CityReadHandler(BaseHTTPRequestHandler):
    """Read-only HTTP face: GET /city/snapshot, GET /census/<id>. Everything
    else is 404; every non-GET method is 405 (no write endpoints at all -
    the intake face is the WebSocket avatar.register, not HTTP)."""

    city = None  # wired at startup

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/city/snapshot":
            code, obj = self.city.snapshot_body()
            self._send(code, obj)
            return
        if path.startswith("/census/"):
            cid = urllib.parse.unquote(path[len("/census/"):])
            if cid and "/" not in cid:
                code, obj = self.city.census_http_body(cid)
                self._send(code, obj)
                return
        self._send(404, {"error": "not found: read API is GET /city/snapshot and GET /census/<id> only"})

    def _write_reject(self):
        self._send(405, {"error": "method not allowed: city API is read-only"})

    def do_POST(self):
        self._write_reject()

    def do_PUT(self):
        self._write_reject()

    def do_DELETE(self):
        self._write_reject()

    def do_PATCH(self):
        self._write_reject()

    def log_message(self, fmt, *args):
        pass


def start_city_http(host, port, city):
    """Start the read-only HTTP face on its own thread; returns the server
    object (actual bound port at .server_address[1]). Daemon threads die
    with the process."""
    handler = type("BoundCityReadHandler", (CityReadHandler,), {"city": city})
    httpd = ThreadingHTTPServer((host, port), handler)
    threading.Thread(target=httpd.serve_forever, name="city-read-api", daemon=True).start()
    return httpd
