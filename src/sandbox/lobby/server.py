"""Sandbox lobby WebSocket server (BigDomain P-47-1b, spec v0.1).

Local sandbox only: docker is absent on this host, so the native Python run
carries the same acceptance criteria (spec section 1, "compose absent =
native Python run under the same criteria"). Production wiring (wss/ICP,
msgSecCheck, real payment receipts) stays blocked on CEO physical items;
public opening is a P1 item (CEO approval only, never self-served).

Run:
    python server.py
    python server.py --host 127.0.0.1 --port 8091 --config config.json --db data/events.db

Startup refuses (E_GATE_OFFLINE, exit code 2) when the content-safety gate
config is missing or unwired: no content safety = no door (BLUEPRINT 5.3).
"""

import argparse
import asyncio
import json
import os
import sys
import time
import uuid
from collections import deque

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from city import CityFace, start_city_http  # noqa: E402
from sec_gate import ContentRejectedError, GateOfflineError, SecGate  # noqa: E402
from store import EventStore, utc_now_iso  # noqa: E402

try:  # websockets >= 13 asyncio implementation
    from websockets.asyncio.server import serve

    NEW_API = True
except ImportError:  # older releases, legacy implementation
    from websockets import serve

    NEW_API = False

from websockets.exceptions import ConnectionClosed  # noqa: E402

LOBBY = None


def conn_path(ws):
    request = getattr(ws, "request", None)
    if request is not None:
        return getattr(request, "path", None)
    return getattr(ws, "path", None)


async def send_frame(ws, frame):
    await ws.send(json.dumps(frame, ensure_ascii=False))


class Client:
    def __init__(self, ws, rooms):
        self.ws = ws
        self.actor = "anon-" + uuid.uuid4().hex[:8]
        self.resident = False
        self.rooms = set(rooms[:1])  # default subscription = first room (lobby)
        self.send_times = deque()
        self.violations = 0
        self.muted_until = 0.0
        self.muted_until_wall = 0.0  # wall-clock mirror for client-visible frames

    def make_resident(self):
        self.resident = True
        self.actor = "res-" + uuid.uuid4().hex[:8]


class Lobby:
    def __init__(self, cfg, gate, store, city=None):
        self.cfg = cfg
        self.gate = gate
        self.store = store
        self.city = city  # P-47-1c read-only city face (may be None)
        self.rooms = [str(r) for r in cfg["rooms"]]
        self.clients = set()
        self.proposal_pool = []  # idea queue stub (3-layer co-creation entry)
        rate = cfg["rate_limit"]
        self.max_msgs = int(rate["max_messages"])
        self.window_s = float(rate["window_seconds"])
        self.mute_s = float(rate["mute_seconds"])
        self.mute_trigger = int(rate["mute_trigger_violations"])
        self.max_text = int(cfg.get("max_text_len", 2000))
        self.ai_label = str(cfg["ai_label_text"])
        self.risk = cfg["risk_warning"]
        heartbeat = cfg["heartbeat"]
        self.ping_interval = float(heartbeat["ping_interval"])
        self.ping_timeout = float(heartbeat["ping_timeout"])

    # ---- server frames ----

    def hello_frame(self):
        return {
            "v": 1,
            "type": "sys.hello",
            "ts_utc": utc_now_iso(),
            "actor": "system",
            "payload": {
                "v": int(self.cfg["protocol_version"]),
                "rooms": self.rooms,
                "risk_doc": self.risk["doc_pointer"],
            },
        }

    def risk_frame(self):
        return {
            "v": 1,
            "type": "sys.risk_warning",
            "ts_utc": utc_now_iso(),
            "room": self.rooms[0],
            "actor": "system",
            "payload": {
                "text": self.risk["text"],
                "persistent": bool(self.risk["persistent"]),
                "doc": self.risk["doc_pointer"],
            },
        }

    async def send_notice(self, client, text, room=None):
        await send_frame(
            client.ws,
            {
                "v": 1,
                "type": "sys.notice",
                "ts_utc": utc_now_iso(),
                "room": room or (sorted(client.rooms)[0] if client.rooms else self.rooms[0]),
                "actor": "system",
                "payload": {"notice": text},
                "ai_generated": False,
            },
        )

    async def send_reject(self, client, code, reason, extra=None):
        payload = {"code": code, "reason": reason}
        if extra:
            payload.update(extra)
        await send_frame(
            client.ws,
            {
                "v": 1,
                "type": "sec.reject",
                "ts_utc": utc_now_iso(),
                "actor": "system",
                "payload": payload,
                "ai_generated": False,
            },
        )

    async def send_rate_limit(self, client):
        await send_frame(
            client.ws,
            {
                "v": 1,
                "type": "err.rate_limit",
                "ts_utc": utc_now_iso(),
                "actor": "system",
                "payload": {
                    "code": "E_RATE_LIMIT",
                    "reason": "rate limit: %d messages per %d seconds"
                    % (self.max_msgs, int(self.window_s)),
                },
                "ai_generated": False,
            },
        )

    # ---- pipeline ----

    def _text_of(self, msg):
        payload = msg.get("payload")
        text = str(payload.get("text", "")) if isinstance(payload, dict) else ""
        return text.strip()[: self.max_text]

    async def handle_chat(self, client, msg):
        # identity: spectator = read-only (section 4 C0)
        if not client.resident:
            await self.send_reject(client, "E_ENTRANCE_REQUIRED", "paid entrance required to speak (C0)")
            return
        room = msg.get("room") or self.rooms[0]
        if room not in self.rooms or room not in client.rooms:
            await self.send_reject(client, "E_ROOM_UNKNOWN", "unknown or unsubscribed room: " + str(room))
            return
        text = self._text_of(msg)
        if not text:
            await self.send_reject(client, "E_BAD_FRAME", "chat text empty")
            return
        # gate 1 (content safety) + gate 2 (non-advisory): rejected content is
        # never broadcast and never lands in the public event stream
        try:
            self.gate.check_text(text)
        except ContentRejectedError as exc:
            await self.send_reject(client, exc.code, "gate %d wordlist hit" % exc.gate)
            return
        # gate 3 (rate limit): 5 msgs / 10s; 3 consecutive violations = 60s mute
        now = time.monotonic()
        if now < client.muted_until:
            await self.send_reject(
                client, "E_RATE_LIMIT", "temporarily muted",
                {"muted_until": client.muted_until_wall},
            )
            return
        while client.send_times and now - client.send_times[0] > self.window_s:
            client.send_times.popleft()
        if len(client.send_times) >= self.max_msgs:
            client.violations += 1
            if client.violations >= self.mute_trigger:
                client.muted_until = now + self.mute_s
                client.muted_until_wall = time.time() + self.mute_s
                client.violations = 0
                await self.send_reject(
                    client,
                    "E_RATE_LIMIT",
                    "muted for %d seconds (3 consecutive violations)" % int(self.mute_s),
                    {"muted_until": client.muted_until_wall},
                )
            else:
                await self.send_rate_limit(client)
            return
        client.send_times.append(now)
        client.violations = 0
        # server-authoritative fields: actor/ts/ai_generated from the server,
        # client-supplied values are ignored (unforgeable AIGC flag)
        ts_utc = utc_now_iso()
        evt_id = self.store.append(
            ts_utc, "chat.broadcast", client.actor, room, text, payload={"text": text}
        )
        await self.broadcast(
            room,
            {
                "v": 1,
                "type": "chat.broadcast",
                "ts_utc": ts_utc,
                "room": room,
                "actor": client.actor,
                "payload": {"text": text},
                "ai_generated": False,
                "evt_id": evt_id,
            },
        )

    async def handle_idea(self, client, msg):
        if not client.resident:
            await self.send_reject(client, "E_ENTRANCE_REQUIRED", "paid entrance required to co-create (C0)")
            return
        text = self._text_of(msg)
        if not text:
            await self.send_reject(client, "E_BAD_FRAME", "idea text empty")
            return
        try:
            self.gate.check_text(text)
        except ContentRejectedError as exc:
            await self.send_reject(client, exc.code, "gate %d wordlist hit" % exc.gate)
            return
        ts_utc = utc_now_iso()
        evt_id = self.store.append(
            ts_utc,
            "idea.submit",
            client.actor,
            "cocreate",
            text,
            payload={"text": text, "pool": "proposal-queue-stub"},
        )
        self.proposal_pool.append(
            {"idea_id": evt_id, "ts_utc": ts_utc, "actor": client.actor, "text": text}
        )
        # AI-processed triage receipt: server-side AI product, flagged at source
        await send_frame(
            client.ws,
            {
                "v": 1,
                "type": "sys.notice",
                "ts_utc": ts_utc,
                "room": "cocreate",
                "actor": "system-ai",
                "payload": {"notice": "idea queued into proposal pool (sandbox stub)", "idea_id": evt_id},
                "ai_generated": True,
                "ai_label": self.ai_label,
                "evt_id": evt_id,
            },
        )

    async def handle_grant(self, client, msg):
        # sandbox mock entrance (production = real 19.9 payment receipt,
        # blocked on WeChat merchant id = CEO physical item)
        ttl = int(self.cfg["sandbox_entrance"]["token_ttl_seconds"])
        client.make_resident()
        token = "sbx-" + uuid.uuid4().hex
        ts_utc = utc_now_iso()
        evt_id = self.store.append(
            ts_utc,
            "pay.grant_sandbox",
            client.actor,
            "lobby",
            "sandbox entrance granted (mock payment)",
            payload={"mock": True, "ttl_seconds": ttl},
        )
        await send_frame(
            client.ws,
            {
                "v": 1,
                "type": "pay.grant_sandbox",
                "ts_utc": ts_utc,
                "room": "lobby",
                "actor": "system",
                "payload": {
                    "granted": True,
                    "token": token,
                    "actor": client.actor,
                    "expires_at": time.time() + ttl,
                    "mock": True,
                },
                "ai_generated": False,
                "evt_id": evt_id,
            },
        )

    async def handle_census_query(self, client, msg):
        # AC-S11: public read face - spectators may query, whitelist enforced
        if self.city is None:
            await self.send_reject(client, "E_BAD_FRAME", "city face not enabled")
            return
        await send_frame(client.ws, self.city.census_snapshot_frame(msg))

    async def handle_avatar_register(self, client, msg):
        # AC-S12: intake face - gates 1+2, queue = one public event row,
        # receipt carries evt_id; household registration is BigLife T-04
        if self.city is None:
            await self.send_reject(client, "E_BAD_FRAME", "city face not enabled")
            return
        await send_frame(client.ws, self.city.avatar_register_frame(client.actor, msg))

    async def handle_room(self, client, msg, action):
        payload = msg.get("payload")
        room = payload.get("room") if isinstance(payload, dict) else None
        if room not in self.rooms:
            await self.send_reject(client, "E_ROOM_UNKNOWN", "unknown room: " + str(room))
            return
        if action == "subscribe":
            client.rooms.add(room)
        else:
            client.rooms.discard(room)
        await self.send_notice(client, "room " + action + ": " + room, room=room)

    async def handle_frame(self, client, raw):
        try:
            msg = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            await self.send_reject(client, "E_BAD_FRAME", "frame is not valid JSON")
            return
        if not isinstance(msg, dict):
            await self.send_reject(client, "E_BAD_FRAME", "frame is not an object")
            return
        mtype = msg.get("type")
        if mtype == "chat.send":
            await self.handle_chat(client, msg)
        elif mtype == "idea.submit":
            await self.handle_idea(client, msg)
        elif mtype == "room.subscribe":
            await self.handle_room(client, msg, "subscribe")
        elif mtype == "room.unsubscribe":
            await self.handle_room(client, msg, "unsubscribe")
        elif mtype == "pay.grant_sandbox":
            await self.handle_grant(client, msg)
        elif mtype == "census.query":
            await self.handle_census_query(client, msg)
        elif mtype == "avatar.register":
            await self.handle_avatar_register(client, msg)
        else:
            await self.send_reject(client, "E_BAD_FRAME", "unknown type: " + str(mtype))

    async def broadcast(self, room, frame):
        data = json.dumps(frame, ensure_ascii=False)
        targets = [c for c in self.clients if room in c.rooms]
        await asyncio.gather(*(c.ws.send(data) for c in targets), return_exceptions=True)

    async def handle_connection(self, ws):
        client = Client(ws, self.rooms)
        self.clients.add(client)
        try:
            path = conn_path(ws)
            if path is not None and path != "/ws":
                await ws.close(code=4004, reason="bad path")
                return
            await send_frame(ws, self.hello_frame())  # first frame (AC-S1)
            await send_frame(ws, self.risk_frame())  # risk warning at connect (AC-S6)
            async for raw in ws:
                await self.handle_frame(client, raw)
        except ConnectionClosed:
            pass
        finally:
            self.clients.discard(client)


if NEW_API:

    async def _handler(ws):
        await LOBBY.handle_connection(ws)

else:  # pragma: no cover

    async def _handler(ws, path):
        await LOBBY.handle_connection(ws)


def build_parser():
    parser = argparse.ArgumentParser(description="BigDomain sandbox lobby WebSocket server (P-47-1b)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--config", default=os.path.join(BASE, "config.json"))
    parser.add_argument("--db", default=os.path.join(BASE, "data", "events.db"))
    parser.add_argument("--ping-interval", type=float, default=None, help="test override")
    parser.add_argument("--ping-timeout", type=float, default=None, help="test override")
    parser.add_argument("--city-dir", default=None, help="read-only city data dir override")
    parser.add_argument("--city-http-port", type=int, default=None, help="city read API port override")
    return parser


async def run_server(host, port, ping_interval, ping_timeout):
    try:
        async with serve(
            _handler,
            host,
            port,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
        ):
            await asyncio.get_running_loop().create_future()
    finally:
        LOBBY.store.close()


def main():
    args = build_parser().parse_args()
    try:
        with open(args.config, encoding="utf-8") as handle:
            cfg = json.load(handle)
    except OSError as exc:
        print("E_GATE_OFFLINE: config unreadable: %s" % exc, file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as exc:
        print("E_GATE_OFFLINE: config not valid JSON: %s" % exc, file=sys.stderr)
        sys.exit(2)
    try:
        gate = SecGate.from_config(cfg)
    except GateOfflineError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
    port = args.port if args.port is not None else int(cfg.get("default_port", 8091))
    ping_interval = args.ping_interval if args.ping_interval is not None else float(
        cfg["heartbeat"]["ping_interval"]
    )
    ping_timeout = args.ping_timeout if args.ping_timeout is not None else float(
        cfg["heartbeat"]["ping_timeout"]
    )
    global LOBBY
    store = EventStore(args.db)
    city = None
    city_cfg = cfg.get("city")
    if isinstance(city_cfg, dict) and city_cfg.get("enabled", True):
        city_dir = args.city_dir or os.path.join(BASE, str(city_cfg.get("data_dir", "city_data")))
        city = CityFace(city_cfg, gate, store, city_dir)
    LOBBY = Lobby(cfg, gate, store, city=city)
    banner = "serving ws://%s:%d/ws rooms=%s ping_interval=%g ping_timeout=%g gate=ok db=%s" % (
        args.host, port, ",".join(LOBBY.rooms), ping_interval, ping_timeout, args.db)
    if city is not None:
        city_port = (
            args.city_http_port if args.city_http_port is not None
            else int(city_cfg.get("http_port", 8092))
        )
        httpd = start_city_http(args.host, city_port, city)
        banner += " city_api=http://%s:%d/city/snapshot census_rows=%d city_dir=%s" % (
            args.host, httpd.server_address[1], city.imported, city.city_dir)
    print(banner, flush=True)
    try:
        asyncio.run(run_server(args.host, port, ping_interval, ping_timeout))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
