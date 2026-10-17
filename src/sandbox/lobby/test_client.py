"""Acceptance suite for the sandbox lobby server (BigDomain P-47-1b + P-47-1c).

Asserts the pre-registered criteria AC-S1..AC-S13 from
docs/spec/lobby-websocket-spec.md section 1 (AC-S11..S13 = city running
face: census whitelist reads, avatar intake, read-only HTTP API) plus the
client reconnect semantics face AC-S8c/S8d/S8e (spec v0.4: keepalive dead
detection, backoff reconnect with exact room-set restoration, idempotent
replay via client_msg_id) plus the room-level message read face
AC-S14/S15 (R1773: per-room chat counts + distinct active-actor
aggregation, pure-read derivation on the EventStore, zero UPDATE,
standing disclaimer envelope, fail-closed without a wired disclaimer)
plus the protocol wiring face AC-S16 (R1790: room.board request/
response frame over the store read face - spectator-queryable public
read, server-authoritative fields, live cross-check against the
server db, zero-cache fresh reflection, legacy no-disclaimer store
rejected gracefully through sec.reject) plus the event-derived idea
pool face AC-S18/S19 (R1792: idea_pool_board pure-read derivation over
type='idea.submit' rows + idea.board wire face with optional rooms
filter and restart-survival proof on a fresh server process over the
same db).
Each criterion prints PASS/FAIL with evidence; the process exits non-zero
on any FAIL.

Usage (run with the repo venv python that has websockets installed):
    python test_client.py            # AC-S1..S7, S8a..S8e, S9..S13 + startup refusal
    python test_client.py --load     # AC-S8 load: LOAD_N conns for LOAD_SECS (default 100 x 300s)
"""

import asyncio
import base64
import hashlib
import http.client
import inspect
import json
import os
import shutil
import socket
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import uuid

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
SERVER = os.path.join(BASE, "server.py")
CONFIG = os.path.join(BASE, "config.json")

try:
    from websockets.asyncio.client import connect
except ImportError:
    from websockets import connect

from websockets.exceptions import ConnectionClosed  # noqa: E402

# R1876 stdout-determinism hardening (suite fixture layer; product faces
# untouched): suite-side uuid4 digests come from a deterministic counter
# stand-in, and server-derived id shapes are canonicalized at display
# time, so a full default-suite double run is byte-identical.
_UUID_SEQ = [0]


def _det_uuid4():
    _UUID_SEQ[0] += 1
    return uuid.UUID(int=_UUID_SEQ[0])


uuid.uuid4 = _det_uuid4


def _hexshape(value):
    s = value if isinstance(value, str) else ""
    if s and all(c in "0123456789abcdef" for c in s):
        return "<hexid:%d>" % len(s)
    return value


def _actorshape(value):
    s = value if isinstance(value, str) else ""
    if "-" in s:
        head, tail = s.split("-", 1)
        if head in ("res", "anon") and tail and all(c in "0123456789abcdef" for c in tail):
            return head + "-<id%d>" % len(tail)
    return value


RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


class ServerProc:
    def __init__(self, port, config=CONFIG, db=None, extra=()):
        self.port = port
        self.config = config
        self.db = db or os.path.join(tempfile.mkdtemp(prefix="lobby-db-"), "events.db")
        self.extra = list(extra)
        self.proc = None
        self.banner = ""

    def start(self):
        cmd = [
            sys.executable, SERVER,
            "--host", "127.0.0.1", "--port", str(self.port),
            "--config", self.config, "--db", self.db,
        ] + self.extra
        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        deadline = time.time() + 20
        while time.time() < deadline:
            if self.proc.poll() is not None:
                err = self.proc.stderr.read()
                raise RuntimeError("server exited rc=%s: %s" % (self.proc.returncode, err.strip()))
            try:
                probe = socket.create_connection(("127.0.0.1", self.port), timeout=0.5)
                probe.close()
                self.banner = self.proc.stdout.readline().strip()
                return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("server did not come up on port %d" % self.port)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()


def db_query(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


async def recv_json(ws, timeout=5.0):
    raw = await asyncio.wait_for(ws.recv(), timeout)
    return json.loads(raw)


async def recv_until(ws, pred, timeout=3.0):
    end = time.perf_counter() + timeout
    while True:
        remain = end - time.perf_counter()
        if remain <= 0:
            raise TimeoutError("no matching frame within %.1fs" % timeout)
        frame = await recv_json(ws, remain)
        if pred(frame):
            return frame


async def expect_silence(ws, timeout=0.5):
    """True when no frame arrives within the window (nothing was broadcast)."""
    try:
        await recv_json(ws, timeout)
        return False
    except TimeoutError:
        return True


async def open_client(port=8091):
    ws = await connect("ws://127.0.0.1:%d/ws" % port)
    hello = await recv_json(ws)
    risk = await recv_json(ws)
    return ws, hello, risk


def frame(kind, **kw):
    msg = {"v": 1, "type": kind}
    msg.update(kw)
    return json.dumps(msg, ensure_ascii=False)


async def make_resident(ws):
    await ws.send(frame("pay.grant_sandbox", payload={}))
    return await recv_until(ws, lambda f: f.get("type") == "pay.grant_sandbox")


def _free_port():
    """Reserve-and-release an ephemeral port for refusal probes.

    Why: frontdoor.py (R728 XL-16 live face) holds 8093 as a standing
    service, so probing that fixed port reports 'bound' regardless of the
    lobby server (R875 collision). An ephemeral port keeps the criterion
    semantics: the refusing server must leave ITS assigned port closed.
    """
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def startup_refusal_cases():
    """AC-S4 half: a missing/unwired gate config must refuse startup."""
    tmp = tempfile.mkdtemp(prefix="lobby-refusal-")
    probe_port = _free_port()
    with open(CONFIG, encoding="utf-8") as handle:
        cfg = json.load(handle)
    broken = os.path.join(tmp, "broken.json")
    cfg2 = json.loads(json.dumps(cfg))
    del cfg2["gate"]["forbidden_words"]
    with open(broken, "w", encoding="utf-8") as handle:
        json.dump(cfg2, handle, ensure_ascii=False)
    missing = os.path.join(tmp, "missing.json")
    ok_broken = ok_missing = bound_ok = False
    ev = []
    for cfg_path, label in ((broken, "empty-wordlist-config"), (missing, "missing-config")):
        proc = subprocess.Popen(
            [sys.executable, SERVER, "--host", "127.0.0.1", "--port", str(probe_port),
             "--config", cfg_path, "--db", os.path.join(tmp, "refusal.db")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        try:
            _, err = proc.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            _, err = proc.communicate()
            err = err or "timeout"
        ok = proc.returncode == 2 and "E_GATE_OFFLINE" in (err or "")
        if label == "empty-wordlist-config":
            ok_broken = ok
        else:
            ok_missing = ok
        ev.append("%s rc=%s offline=%s" % (label, proc.returncode, "E_GATE_OFFLINE" in (err or "")))
    try:
        socket.create_connection(("127.0.0.1", probe_port), timeout=1).close()
        bound_ok = False
    except OSError:
        bound_ok = True  # nothing ever bound = door stayed shut
    # R1876 hardening: fixed display slot (no varying port digits); the
    # probe itself stays ephemeral (R875 collision-safe).
    ev.append("port-probe(ephemeral)-never-bound=%s" % bound_ok)
    return ok_broken and ok_missing and bound_ok, "; ".join(ev)


def raw_no_pong_client(port, deadline=10):
    """Raw RFC6455 handshake, then never answer pings: server must disconnect."""
    sock = socket.create_connection(("127.0.0.1", port), timeout=5)
    try:
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            "GET /ws HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nUpgrade: websocket\r\n"
            "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n"
        ) % (port, key)
        sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = sock.recv(1024)
            if not chunk:
                return False
            buf += chunk
        if not buf.split(b"\r\n")[0].startswith(b"HTTP/1.1 101"):
            return False
        sock.settimeout(2)
        end = time.time() + deadline
        while time.time() < end:
            try:
                chunk = sock.recv(1024)
            except socket.timeout:
                continue
            if not chunk:
                return True  # server closed: no pong within timeout
        return False
    finally:
        sock.close()


def heartbeat_mechanism_case():
    """AC-S8 half: no-pong client gets disconnected by the keepalive loop."""
    srv = ServerProc(8094, extra=["--ping-interval", "1", "--ping-timeout", "2",
                                   "--city-http-port", "8097"])
    srv.start()
    try:
        t0 = time.perf_counter()
        closed = raw_no_pong_client(8094, deadline=10)
        elapsed = time.perf_counter() - t0
        # R2012 double-run caught a raw wall-clock drift on this readout
        # (3.1s vs 3.0s) - the R1876/R1993 determinism hardening missed
        # it. Classed display per the same family (sub-5s/sub-10s); the
        # real gate (elapsed < 10) stays in the returned verdict.
        klass = "sub-5s" if elapsed < 5 else "sub-10s"
        return closed and elapsed < 10, (
            "server disconnected the no-pong client after %s (test instance interval=1s timeout=2s)"
            % klass)
    finally:
        srv.stop()


# ---------------------------------------------------------------------------
# Client reconnect semantics face (spec v0.4, AC-S8c/S8d/S8e)
# ---------------------------------------------------------------------------

RC_PORT = 8098
RC_CITY_PORT = 8099
RC_PROXY_A = 8100
RC_PROXY_B = 8101
RC_PORT2 = 8102
RC_CITY_PORT2 = 8103


class CutProxy:
    """Byte-pump TCP relay with a freeze switch: a frozen proxy reads and
    drops both directions but keeps both sockets open, so the client never
    sees FIN/RST (dead-network simulation).

    Armed mode (marker set): the c2s side runs a minimal RFC6455 frame
    parser and raises the freeze while forwarding the masked TEXT frame
    whose unmasked payload carries the marker - the server processes the
    send while its reply is deterministically lost (send-arrived-ack-
    lost). Byte matching would never see the marker: client->server
    frames are always masked, and with permessage-deflate also
    compressed; the reconnecting client therefore connects with
    compression=None so unmasked text payloads are plain UTF-8. A pump
    blocked inside read() bypasses any loop-top flag, so frozen-ness is
    re-checked after every read returns.
    """

    def __init__(self, listen_port, target_port, marker=None):
        self.listen_port = listen_port
        self.target_port = target_port
        self.marker = marker
        self.armed = marker is not None
        self.frozen = False
        self.server = None
        self.sessions = 0
        self._sockets = []  # live session writer pairs (force-close set)

    async def start(self):
        self.server = await asyncio.start_server(
            self._handle, "127.0.0.1", self.listen_port)

    async def close(self):
        # Close the listener, then force both ends of every live session
        # so the handlers finish: on Python >= 3.12 wait_closed() waits
        # for ALL handlers, and a still-healthy leaked client would
        # otherwise hang the teardown forever.
        if self.server is not None:
            self.server.close()
        for pair in list(self._sockets):
            for sock in pair:
                try:
                    sock.close()
                except Exception:
                    pass
        self._sockets = []
        if self.server is not None:
            await self.server.wait_closed()
            self.server = None

    def _parse_frame(self, buf):
        """Return (end_offset, is_marker_text_frame) for the first whole
        frame in buf, or (None, False) when more bytes are needed."""
        if len(buf) < 2:
            return None, False
        opcode = buf[0] & 0x0F
        masked = buf[1] & 0x80
        length = buf[1] & 0x7F
        offset = 2
        if length == 126:
            if len(buf) < offset + 2:
                return None, False
            length = int.from_bytes(buf[offset:offset + 2], "big")
            offset += 2
        elif length == 127:
            if len(buf) < offset + 8:
                return None, False
            length = int.from_bytes(buf[offset:offset + 8], "big")
            offset += 8
        mask_key = b""
        if masked:
            if len(buf) < offset + 4:
                return None, False
            mask_key = buf[offset:offset + 4]
            offset += 4
        if len(buf) < offset + length:
            return None, False
        payload = buf[offset:offset + length]
        trigger = False
        if self.armed and opcode == 0x1 and masked and mask_key:
            plain = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
            trigger = self.marker.encode("utf-8") in plain
        return offset + length, trigger

    async def _pump_c2s_frames(self, src, dst):
        """Frame-aware c2s pump (armed mode). Phase 1 forwards the RFC6455
        opening handshake byte-transparent up to its \r\n\r\n end - frame
        parsing must not start mid-handshake, or a misaligned parse can
        synthesize a huge bogus length and stall the stream (first-run
        root cause). Phase 2 parses frames from the clean boundary,
        forwards byte-exact, raises the freeze on the marker text frame
        before forwarding it, and drops everything after the freeze
        (client pings die in the void)."""
        buf = b""
        seen_handshake = False
        while True:
            if not seen_handshake:
                idx = buf.find(b"\r\n\r\n")
                if idx < 0:
                    forward = buf[:-3] if len(buf) > 3 else b""
                    if forward:
                        dst.write(forward)
                        await dst.drain()
                        buf = buf[len(forward):]
                    data = await src.read(4096)
                    if not data:
                        break
                    buf += data
                    continue
                head, buf = buf[:idx + 4], buf[idx + 4:]
                dst.write(head)
                await dst.drain()
                seen_handshake = True
            while True:
                frame_end, trigger = self._parse_frame(buf)
                if frame_end is None:
                    break
                raw, buf = buf[:frame_end], buf[frame_end:]
                if trigger:
                    self.frozen = True  # before the forward: reply is lost
                if self.frozen and not trigger:
                    continue  # dead network: parsed and dropped
                dst.write(raw)
                await dst.drain()
            data = await src.read(4096)
            if not data:
                break
            buf += data

    async def _handle(self, reader, writer):
        self.sessions += 1
        try:
            upstream_reader, upstream_writer = await asyncio.open_connection(
                "127.0.0.1", self.target_port)
        except OSError:
            writer.close()
            return
        self._sockets.append((writer, upstream_writer))

        async def pump(src, dst):
            try:
                while True:
                    data = await src.read(4096)
                    if not data:
                        break
                    if self.frozen:
                        continue  # dead network: read and drop
                    dst.write(data)
                    await dst.drain()
            except (ConnectionError, asyncio.CancelledError):
                pass

        if self.armed:
            t_c2s = asyncio.create_task(self._pump_c2s_frames(reader, upstream_writer))
        else:
            t_c2s = asyncio.create_task(pump(reader, upstream_writer))
        t_s2c = asyncio.create_task(pump(upstream_reader, writer))
        try:
            await asyncio.gather(t_c2s, t_s2c)
        finally:
            for task in (t_c2s, t_s2c):
                task.cancel()
            for sock in (writer, upstream_writer):
                sock.close()
            if (writer, upstream_writer) in self._sockets:
                self._sockets.remove((writer, upstream_writer))


class ReconnectingClient:
    """Reference client with reconnect semantics (AC-S8c/S8d/S8e):
    keepalive-based dead detection, bounded-backoff reconnect, exact
    room-set restoration, idempotent replay of unacked sends."""

    def __init__(self, url, rooms=("lobby",), ping_interval=1.0, ping_timeout=1.0,
                 backoff_base=0.2, backoff_cap=2.0):
        self.url = url
        self.rooms = set(rooms)
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self.ws = None
        self.actor = None
        self.server_rooms = []
        self.attempts = 0
        self.dead_events = []
        self.pending = {}  # client_msg_id -> text (sent, not yet acked)

    def _note_dead(self, reason):
        self.dead_events.append((time.perf_counter(), reason))

    async def connect_once(self):
        # A reference client never leaks the previous socket, and never
        # serializes the reconnect behind its teardown: close() on a
        # connection whose closing handshake can't complete (peer gone)
        # ignores cancellation and blocks past any wait_for cap
        # (measured ~2s on websockets 17, which swallowed the whole
        # restart-downtime window in first runs). Close it in the
        # background and dial immediately.
        if self.ws is not None:
            old_ws = self.ws
            self.ws = None

            async def _close_old():
                try:
                    await old_ws.close()
                except Exception:
                    pass

            asyncio.get_running_loop().create_task(_close_old())
        self.attempts += 1
        # compression=None: keeps client->server text payloads plain when
        # unmasked (the armed proxy matches the marker on the wire);
        # close_timeout=0.5: after a keepalive ping timeout the library
        # tears the dead connection down promptly instead of waiting out
        # a 10s close handshake that a dead network can never finish.
        ws = await connect(self.url, open_timeout=5, compression=None,
                           ping_interval=self.ping_interval,
                           ping_timeout=self.ping_timeout,
                           close_timeout=0.5)
        hello = await recv_json(ws)
        risk = await recv_json(ws)
        self.ws = ws
        self.server_rooms = list(hello.get("payload", {}).get("rooms") or [])
        return hello, risk

    async def recover_state(self):
        """Re-acquire the resident grant and restore the exact room set:
        rooms in self.rooms -> subscribe, everything else -> unsubscribe
        (a fresh connection defaults to the first room, so the default
        must be explicitly undone for exact restoration)."""
        await self.ws.send(frame("pay.grant_sandbox", payload={}))
        grant = await recv_until(self.ws, lambda f: f.get("type") == "pay.grant_sandbox")
        self.actor = grant.get("payload", {}).get("actor", "")
        for room in self.server_rooms:
            if room in self.rooms:
                await self.ws.send(frame("room.subscribe", payload={"room": room}))
            else:
                await self.ws.send(frame("room.unsubscribe", payload={"room": room}))
        for _ in self.server_rooms:
            await recv_until(self.ws, lambda f: f.get("type") == "sys.notice")
        return grant

    async def connect_recovered(self):
        await self.connect_once()
        await self.recover_state()

    async def reconnect_until(self, budget_s=15.0):
        """Backoff reconnect loop: any failure (refused, timeout, protocol
        error) retries with exponential backoff capped at backoff_cap.
        Returns True on recovery, False when the budget runs out."""
        end = time.perf_counter() + budget_s
        delay = self.backoff_base
        while time.perf_counter() < end:
            try:
                await self.connect_recovered()
                return True
            except Exception as exc:  # reference-loop semantics: retry anything
                self._note_dead("reconnect attempt: %s" % type(exc).__name__)
                remain = end - time.perf_counter()
                if remain <= 0:
                    return False
                await asyncio.sleep(min(delay, remain))
                delay = min(delay * 2, self.backoff_cap)
        return False

    async def send_tracked(self, room, text):
        """Chat send carrying an idempotency key; the pair stays in
        pending until its own broadcast (matched by actor+text) or a
        chat.duplicate re-ack clears it."""
        mid = uuid.uuid4().hex
        self.pending[mid] = text
        await self.ws.send(frame("chat.send", room=room,
                                 payload={"text": text}, client_msg_id=mid))
        return mid

    def reconcile(self, f):
        kind = f.get("type")
        if kind == "chat.broadcast" and f.get("actor") == self.actor:
            text = f.get("payload", {}).get("text")
            for mid, pending_text in list(self.pending.items()):
                if pending_text == text:
                    del self.pending[mid]
                    break
        elif kind == "chat.duplicate":
            mid = f.get("payload", {}).get("client_msg_id")
            if mid in self.pending:
                del self.pending[mid]

    async def recv_until_rc(self, pred, timeout=5.0):
        end = time.perf_counter() + timeout
        while True:
            remain = end - time.perf_counter()
            if remain <= 0:
                raise TimeoutError("no matching frame within %.1fs" % timeout)
            f = await recv_json(self.ws, remain)
            self.reconcile(f)
            if pred(f):
                return f

    async def replay_pending(self):
        """Idempotent recovery: resend every unacked send with the SAME
        client_msg_id (server-side dedup makes the outcome exactly-once)."""
        room = sorted(self.rooms)[0] if self.rooms else "lobby"
        for mid, text in list(self.pending.items()):
            await self.ws.send(frame("chat.send", room=room,
                                     payload={"text": text}, client_msg_id=mid))

    async def wait_dead(self, bound_s=6.0):
        """Dead-detection probe: with the client keepalive armed (its own
        ping/pong timers), a frozen peer is aborted by the library within
        ping_interval + ping_timeout and recv raises ConnectionClosed.
        A frame arriving, or this bound timing out instead, means the
        keepalive did NOT fire (criterion failure)."""
        t0 = time.perf_counter()
        try:
            f = await asyncio.wait_for(self.ws.recv(), bound_s)
            self._note_dead("unexpected frame while probing: %r" % (f,))
            return False, time.perf_counter() - t0, "frame-arrived"
        except ConnectionClosed as exc:
            elapsed = time.perf_counter() - t0
            self._note_dead(type(exc).__name__)
            return True, elapsed, type(exc).__name__
        except asyncio.TimeoutError:
            return False, time.perf_counter() - t0, "bound-timeout"


async def reconnect_cases():
    """AC-S8c/S8d/S8e: client reconnect semantics face (R1675)."""
    srv = ServerProc(RC_PORT, extra=["--ping-interval", "0.5", "--ping-timeout", "1.0",
                                      "--city-http-port", str(RC_CITY_PORT)])
    srv.start()
    proxy_a = proxy_b = None
    cli = cli2 = cli3 = observer = probe = None
    srv2 = srv3 = None
    try:
        # ---- AC-S8c: keepalive heartbeat timeout behind a dead network ----
        proxy_a = CutProxy(RC_PROXY_A, RC_PORT)
        await proxy_a.start()
        cli = ReconnectingClient("ws://127.0.0.1:%d/ws" % RC_PROXY_A, rooms=("quant",),
                                 ping_interval=1.0, ping_timeout=1.0)
        await cli.connect_recovered()
        await cli.send_tracked("quant", "s8c baseline ping")
        await cli.recv_until_rc(lambda f: f.get("type") == "chat.broadcast"
                                and f.get("payload", {}).get("text") == "s8c baseline ping")
        baseline_ok = len(cli.pending) == 0
        proxy_a.frozen = True
        dead, elapsed, how = await cli.wait_dead(6.0)
        no_fin_premise = proxy_a.frozen and proxy_a.sessions >= 1
        cli.url = "ws://127.0.0.1:%d/ws" % RC_PORT
        rec_ok = await cli.reconnect_until(10.0)
        await cli.send_tracked("quant", "s8c after recovery")
        after = await cli.recv_until_rc(
            lambda f: f.get("type") == "chat.broadcast"
            and f.get("payload", {}).get("text") == "s8c after recovery")
        ok_c = (baseline_ok and dead and how != "bound-timeout" and elapsed <= 6.0
                and no_fin_premise and rec_ok and after is not None
                and len(cli.pending) == 0)
        record("AC-S8c", ok_c,
               "baseline-acked=%s; dead=%s via=%s in %s (keepalive 1s+1s, bound 6s); "
               "proxy-frozen=%s sessions=%d (no-FIN premise); reconnect-direct=%s; "
               "post-recovery-roundtrip=%s pending=%d"
               % (baseline_ok, dead, how,
                  "within-bound" if elapsed <= 6.0 else "OVER",
                  proxy_a.frozen, proxy_a.sessions,
                  rec_ok, after is not None, len(cli.pending)))
        try:
            await cli.ws.close()
        except Exception:
            pass
        cli = None
        await proxy_a.close()
        proxy_a = None

        # ---- AC-S8e: idempotent recovery (send arrived, ack lost) ----
        marker = "s8e race " + uuid.uuid4().hex[:8]
        proxy_b = CutProxy(RC_PROXY_B, RC_PORT, marker=marker)
        await proxy_b.start()
        observer, _, _ = await open_client(RC_PORT)
        await make_resident(observer)
        cli2 = ReconnectingClient("ws://127.0.0.1:%d/ws" % RC_PROXY_B, rooms=("lobby",),
                                  ping_interval=1.0, ping_timeout=1.0)
        await cli2.connect_recovered()
        mid = await cli2.send_tracked("lobby", marker)
        bcast = await recv_until(observer, lambda f: f.get("type") == "chat.broadcast"
                                 and f.get("payload", {}).get("text") == marker)
        orig_evt = bcast.get("evt_id")
        armed_ok = proxy_b.frozen and len(cli2.pending) == 1
        dead2, elapsed2, how2 = await cli2.wait_dead(6.0)
        cli2.url = "ws://127.0.0.1:%d/ws" % RC_PORT
        rec2 = await cli2.reconnect_until(10.0)
        await cli2.replay_pending()
        dup = await cli2.recv_until_rc(lambda f: f.get("type") == "chat.duplicate")
        n_rows = db_query(srv.db, "SELECT COUNT(*) FROM events WHERE type='chat.broadcast' "
                          "AND summary = ?", (marker,))[0][0]
        silent_obs = await expect_silence(observer, 0.5)  # no second broadcast ever
        await cli2.send_tracked("lobby", "s8e post-recovery ping")
        post = await cli2.recv_until_rc(
            lambda f: f.get("type") == "chat.broadcast"
            and f.get("payload", {}).get("text") == "s8e post-recovery ping")
        ok_e = (armed_ok and dead2 and how2 != "bound-timeout" and rec2
                and dup is not None
                and dup.get("payload", {}).get("evt_id") == orig_evt
                and dup.get("payload", {}).get("client_msg_id") == mid
                and dup.get("payload", {}).get("code") == "E_DUPLICATE_MSG"
                and n_rows == 1 and silent_obs and len(cli2.pending) == 0
                and post is not None)
        record("AC-S8e", ok_e,
               "armed=%s frozen=%s pending-after-cut=%d; observer-once evt=%s; dead=%s "
               "via=%s in %s; reconnect=%s; duplicate-ack evt-match=%s id-match=%s "
               "code=%s; store-rows=%d; no-rebroadcast=%s; pending=%d; post-roundtrip=%s"
               % (armed_ok, proxy_b.frozen, 1, _hexshape(orig_evt), dead2, how2,
                  "sub-6s" if elapsed2 <= 6.0 else "OVER", rec2,
                  dup.get("payload", {}).get("evt_id") == orig_evt,
                  dup.get("payload", {}).get("client_msg_id") == mid,
                  dup.get("payload", {}).get("code"), n_rows, silent_obs,
                  len(cli2.pending), post is not None))
        try:
            await cli2.ws.close()
        except Exception:
            pass
        cli2 = None
        try:
            await observer.close()
        except Exception:
            pass
        observer = None
        await proxy_b.close()
        proxy_b = None
    finally:
        for client_obj in (cli, cli2):
            if client_obj is not None and client_obj.ws is not None:
                try:
                    await client_obj.ws.close()
                except Exception:
                    pass
        if observer is not None:
            try:
                await observer.close()
            except Exception:
                pass
        for proxy in (proxy_a, proxy_b):
            if proxy is not None:
                await proxy.close()
        srv.stop()

    # ---- AC-S8d: server restart -> backoff reconnect -> exact state ----
    srv2 = ServerProc(RC_PORT2,
                      db=os.path.join(tempfile.mkdtemp(prefix="lobby-rc2-"), "events.db"),
                      extra=["--city-http-port", str(RC_CITY_PORT2)])
    srv2.start()
    loop_task = None
    srv3 = None
    probe = cli3 = None
    try:
        cli3 = ReconnectingClient("ws://127.0.0.1:%d/ws" % RC_PORT2, rooms=("quant",),
                                  ping_interval=1.0, ping_timeout=1.0)
        await cli3.connect_recovered()
        await cli3.send_tracked("quant", "s8d baseline")
        await cli3.recv_until_rc(lambda f: f.get("type") == "chat.broadcast"
                                 and f.get("payload", {}).get("text") == "s8d baseline")
        attempts_before = cli3.attempts
        srv2.stop()  # hard kill: FIN face, no proxy
        dead3, elapsed3, how3 = await cli3.wait_dead(6.0)
        # Refusal drill (deterministic retry-path evidence): dialing a
        # bound-but-not-listening port refuses every time on this host
        # (measured 2.03s per refusal, 3/3). The restart phase below
        # cannot rely on refusals: a freshly-terminated listener's kernel
        # backlog still accepts dials (measured: TCP connect succeeds in
        # 0.00s against a corpse), so the first dial can bridge the
        # whole restart - genuine loopback semantics, recorded honestly.
        drill_sock = socket.socket()
        drill_sock.bind(("127.0.0.1", 0))
        drill_port = drill_sock.getsockname()[1]
        cli3.url = "ws://127.0.0.1:%d/ws" % drill_port
        drill_rec = await cli3.reconnect_until(3.0)
        drill_refusals = sum(1 for _t, reason in cli3.dead_events
                             if reason.startswith("reconnect attempt"))
        drill_sock.close()
        cli3.url = "ws://127.0.0.1:%d/ws" % RC_PORT2
        attempts_before = cli3.attempts  # restart-phase count starts here
        loop_task = asyncio.create_task(cli3.reconnect_until(15.0))
        # 1.5s downtime window: the client retries while the server is
        # provably down (whether those dials refuse or bridge via the
        # corpse backlog is the loopback behavior under measurement).
        await asyncio.sleep(1.5)
        srv3 = ServerProc(RC_PORT2, db=srv2.db,
                          extra=["--city-http-port", str(RC_CITY_PORT2)])
        srv3.start()
        rec3 = await asyncio.wait_for(loop_task, 20.0)
        retries = cli3.attempts - attempts_before
        probe, _, _ = await open_client(RC_PORT2)
        await make_resident(probe)
        await probe.send(frame("chat.send", room="lobby", payload={"text": "s8d lobby probe"}))
        await recv_until(probe, lambda f: f.get("type") == "chat.broadcast"
                         and f.get("payload", {}).get("text") == "s8d lobby probe")
        silent_lobby = await expect_silence(cli3.ws, 0.5)
        # the probe needs a quant subscription of its own or the server
        # rejects its send with E_ROOM_UNKNOWN (spectators default to lobby)
        await probe.send(frame("room.subscribe", payload={"room": "quant"}))
        await recv_until(probe, lambda f: f.get("type") == "sys.notice")
        await probe.send(frame("chat.send", room="quant", payload={"text": "s8d quant probe"}))
        quant_recv = await cli3.recv_until_rc(
            lambda f: f.get("type") == "chat.broadcast"
            and f.get("payload", {}).get("text") == "s8d quant probe")
        ok_d = (dead3 and how3 != "bound-timeout" and rec3
                and drill_rec is False and drill_refusals >= 1
                and 1 <= retries <= 10
                and silent_lobby and quant_recv is not None)
        record("AC-S8d", ok_d,
               "dead=%s via=%s in %s; refusal-drill budget-out=%s "
               "drill-refusals=%s (retry loop caught+backed off real "
               "refusals); restart: reconnect=%s retries=%s (>=1, <=10: "
               "not busy-spinning; a corpse-backlog dial may bridge the "
               "restart on Windows loopback - R1876: counts display "
               "range-class for double-run byte-identity); room-set "
               "restored exactly: lobby-isolated=%s quant-received=%s"
               % (dead3, how3, "sub-6s" if elapsed3 <= 6.0 else "OVER",
                  drill_rec,
                  "caught(>=1)" if drill_refusals >= 1 else "none",
                  rec3, "in-1..10" if 1 <= retries <= 10 else "OUT",
                  silent_lobby, quant_recv is not None))
        try:
            await probe.close()
        except Exception:
            pass
        try:
            await cli3.ws.close()
        except Exception:
            pass
    finally:
        if loop_task is not None and not loop_task.done():
            loop_task.cancel()
        if probe is not None:
            try:
                await probe.close()
            except Exception:
                pass
        if cli3 is not None and cli3.ws is not None:
            try:
                await cli3.ws.close()
            except Exception:
                pass
        srv2.stop()
        if srv3 is not None:
            srv3.stop()


CITY_HTTP_PORT = 8096
DEEP_WATER = ("recent_ring", "recent_ring_date", "hook")
# Windows: os.chmod honors FILE_ATTRIBUTE_*; POSIX fallback to plain mode bits
READONLY_FLAG = getattr(stat, "FILE_ATTRIBUTE_READONLY", stat.S_IRUSR)
WRITABLE_FLAG = getattr(stat, "FILE_ATTRIBUTE_NORMAL", stat.S_IRUSR | stat.S_IWUSR)


def city_readonly_copy():
    """Copy committed city fixtures to a temp dir and set the read-only
    attribute: a native stand-in for the production :ro mount (AC-S13)."""
    src = os.path.join(BASE, "city_data")
    dst_root = tempfile.mkdtemp(prefix="lobby-city-ro-")
    dst = os.path.join(dst_root, "city")
    shutil.copytree(src, dst)
    return dst, city_hashes(dst, readonly=True)


def city_hashes(city_dir, readonly=False):
    out = {}
    for root, _dirs, files in os.walk(city_dir):
        for name in files:
            path = os.path.join(root, name)
            with open(path, "rb") as handle:
                out[path] = hashlib.sha256(handle.read()).hexdigest()
            if readonly:
                os.chmod(path, READONLY_FLAG)
    return out


def city_write_refused(city_dir):
    """Direct write attempt into the read-only city dir must fail."""
    probe = os.path.join(city_dir, "world-public.json")
    try:
        with open(probe, "w", encoding="utf-8") as handle:
            handle.write("tamper")
    except OSError:
        return True
    return False


def city_restore_writable(city_dir):
    for root, _dirs, files in os.walk(city_dir):
        for name in files:
            try:
                os.chmod(os.path.join(root, name), WRITABLE_FLAG)
            except OSError:
                pass


def http_json(port, method, path):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(method, path)
        resp = conn.getresponse()
        raw = resp.read()
        try:
            obj = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            obj = {}
        return resp.status, obj
    finally:
        conn.close()


def fixture_census_rows():
    rows = []
    with open(os.path.join(BASE, "city_data", "citizens-light.jsonl"), encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def fixture_snapshot():
    with open(os.path.join(BASE, "city_data", "world-public.json"), encoding="utf-8") as handle:
        return json.load(handle)


async def city_cases():
    """AC-S11/S12/S13: city running face against a read-only city dir."""
    with open(CONFIG, encoding="utf-8") as handle:
        cfg = json.load(handle)
    whitelist = set(cfg["city"]["census_whitelist"])
    rows = fixture_census_rows()
    snap_pkg = fixture_snapshot()
    row0 = rows[0]
    cid = row0["id"]
    ro_dir, hashes_before = city_readonly_copy()
    srv = ServerProc(
        8095,
        db=os.path.join(tempfile.mkdtemp(prefix="lobby-city-db-"), "events.db"),
        extra=["--city-dir", ro_dir, "--city-http-port", str(CITY_HTTP_PORT)])
    srv.start()
    ws = None
    try:
        # spectator connection: census read + intake are public faces (no entrance)
        ws, _, _ = await open_client(8095)

        # AC-S11: whitelist-only snapshot; deep-water fields never leave
        await ws.send(frame("census.query", payload={"id": cid}))
        snap = await recv_json(ws)
        fields = snap.get("payload", {}).get("fields", {})
        subset = set(fields) <= whitelist
        name_match = fields.get("name") == row0["name"]
        leaks = [k for k in DEEP_WATER if k in fields]
        ok_full = (snap.get("type") == "census.snapshot"
                   and snap.get("payload", {}).get("rendered") is True
                   and subset and name_match and not leaks)

        # AC-S11: explicit field subset
        await ws.send(frame("census.query", payload={"id": cid, "fields": ["name", "age"]}))
        sub = await recv_json(ws)
        ok_sub = (sub.get("type") == "census.snapshot"
                  and set(sub.get("payload", {}).get("fields", {})) == {"name", "age"})

        # AC-S11: off-whitelist field request -> E_FORBIDDEN_FIELD
        await ws.send(frame("census.query",
                           payload={"id": cid, "fields": ["name", "recent_ring"]}))
        rej = await recv_json(ws)
        ok_forbidden = (rej.get("type") == "sec.reject"
                        and rej.get("payload", {}).get("code") == "E_FORBIDDEN_FIELD")

        # AC-S11: honorary seat C-00001..09 renders nothing
        await ws.send(frame("census.query", payload={"id": "C-00001"}))
        hon = await recv_json(ws)
        ok_honorary = (hon.get("type") == "census.snapshot"
                       and hon.get("payload", {}).get("fields") == {}
                       and hon.get("payload", {}).get("rendered") is False)

        # AC-S11: unknown id -> found=false, zero fields
        await ws.send(frame("census.query", payload={"id": "B-99999"}))
        unk = await recv_json(ws)
        ok_unknown = (unk.get("type") == "census.snapshot"
                      and unk.get("payload", {}).get("found") is False
                      and unk.get("payload", {}).get("fields") == {})
        record("AC-S11", ok_full and ok_sub and ok_forbidden and ok_honorary and ok_unknown,
               "full: keys=%d subset=%s name-match=%s deep-water-leak=%s; subset=%s "
               "forbidden=%s honorary-zero-render=%s unknown=%s"
               % (len(fields), subset, name_match, leaks, ok_sub, ok_forbidden,
                  ok_honorary, ok_unknown))

        # AC-S12: spectator intake -> public event row + receipt with evt_id
        await ws.send(frame("avatar.register",
                           payload={"name": "沙箱访客化身", "intro": "想参与东区灯语谱共创"}))
        receipt = await recv_json(ws)
        evt_id = receipt.get("payload", {}).get("evt_id")
        ok_receipt = (receipt.get("type") == "avatar.intake_receipt"
                      and bool(evt_id) and receipt.get("evt_id") == evt_id
                      and receipt.get("ai_generated") is False)
        intake_rows = db_query(
            srv.db,
            "SELECT evt_id, zone FROM events WHERE type='avatar.intake' AND summary LIKE ?",
            ("%沙箱访客化身%",))
        ok_queued = (len(intake_rows) == 1 and intake_rows[0][0] == evt_id
                     and intake_rows[0][1] == "intake")

        # AC-S12: ungated content never lands and never receipts
        fw = cfg["gate"]["forbidden_words"][0]
        ab = cfg["gate"]["advisory_ban_words"][0]
        await ws.send(frame("avatar.register",
                            payload={"name": "坏样本甲", "intro": "内容含禁词 " + fw}))
        rej1 = await recv_json(ws)
        await ws.send(frame("avatar.register",
                            payload={"name": "坏样本乙", "intro": "内容含投顾词 " + ab}))
        rej2 = await recv_json(ws)
        ok_gate_rej = (rej1.get("payload", {}).get("code") == "E_CONTENT_REJECTED"
                       and rej2.get("payload", {}).get("code") == "E_CONTENT_REJECTED")
        n_bad = db_query(srv.db, "SELECT COUNT(*) FROM events WHERE type='avatar.intake' "
                         "AND (summary LIKE ? OR summary LIKE ?)",
                         ("%坏样本甲%", "%坏样本乙%"))[0][0]
        record("AC-S12", ok_receipt and ok_queued and ok_gate_rej and n_bad == 0,
               "receipt-evt_id=%s queued-row=%s gate-rejects=%s ungated-rows=%d"
               % (ok_receipt, ok_queued, ok_gate_rej, n_bad))

        # AC-S13: HTTP read API on the read-only city dir
        code_snap, body = http_json(CITY_HTTP_PORT, "GET", "/city/snapshot")
        ok_snap = (code_snap == 200 and body.get("as_of") == snap_pkg.get("as_of")
                   and body.get("city", {}).get("population") == snap_pkg["city"]["population"])
        code_cen, cen = http_json(CITY_HTTP_PORT, "GET", "/census/" + cid)
        cen_fields = cen.get("fields", {})
        ok_cen = (code_cen == 200 and set(cen_fields) <= whitelist
                  and cen_fields.get("name") == row0["name"]
                  and not any(k in cen_fields for k in DEEP_WATER))
        code_miss, _ = http_json(CITY_HTTP_PORT, "GET", "/census/B-99999")
        code_path, _ = http_json(CITY_HTTP_PORT, "GET", "/nope")
        ok_404 = code_miss == 404 and code_path == 404
        w_post, _ = http_json(CITY_HTTP_PORT, "POST", "/city/snapshot")
        w_put, _ = http_json(CITY_HTTP_PORT, "PUT", "/census/" + cid)
        w_del, _ = http_json(CITY_HTTP_PORT, "DELETE", "/city/snapshot")
        ok_405 = w_post == 405 and w_put == 405 and w_del == 405
        ro_refused = city_write_refused(ro_dir)
        unchanged = city_hashes(ro_dir) == hashes_before
        record("AC-S13", ok_snap and ok_cen and ok_404 and ok_405 and ro_refused and unchanged,
               "snapshot-200-as_of=%s census-subset=%s 404=%d/%d 405=%d/%d/%d "
               "ro-write-refused=%s files-unchanged=%s"
               % (ok_snap, ok_cen, code_miss, code_path, w_post, w_put, w_del,
                  ro_refused, unchanged))
    finally:
        if ws is not None:
            try:
                await ws.close()
            except Exception:
                pass
        srv.stop()
        city_restore_writable(ro_dir)


def room_board_cases(srv_db):
    """AC-S14/S15: room-level message read face (R1773): per-room chat
    message counts + distinct active-actor aggregation, pure-read
    derivation on the EventStore (zero UPDATE, standing disclaimer
    envelope, fail-closed without a wired disclaimer)."""
    from store import EventStore
    tmp = tempfile.mkdtemp(prefix="lobby-board-")
    notice = ("sandbox non-advisory notice: room board rows are "
              "operational read-only derivations, not advice")

    # ---- AC-S15 half: explicit bad disclaimer rejected at construction ----
    bad_refusals = []
    for value, label in (("", "empty"), ("   ", "whitespace"), (123, "non-str")):
        refused = False
        try:
            EventStore(os.path.join(tmp, "bad-%s.db" % label), disclaimer=value)
        except ValueError as exc:
            refused = "E_STORE_NO_DISCLAIMER" in str(exc)
        bad_refusals.append("%s=%s" % (label, refused))

    # ---- AC-S14: semantics, scoping, ordering, cross-validation ----
    st = EventStore(os.path.join(tmp, "board.db"), disclaimer=notice)
    empty_env = st.room_message_board()
    ok_empty = (set(empty_env.keys()) == {"room_message_board", "disclaimer"}
                and empty_env["disclaimer"] == notice
                and empty_env["room_message_board"] == [])

    # deterministic world: five chat broadcasts across two rooms by two
    # actors + two non-chat rows (scope isolation: never counted)
    world = [
        ("2026-10-11T00:00:01.000000Z", "chat.broadcast", "res-alpha", "lobby",
         "alpha lobby line", {"text": "alpha lobby line"}),
        ("2026-10-11T00:00:02.000000Z", "chat.broadcast", "res-beta", "quant",
         "beta quant line 1", {"text": "beta quant line 1"}),
        ("2026-10-11T00:00:03.000000Z", "chat.broadcast", "res-beta", "quant",
         "beta quant line 2", {"text": "beta quant line 2"}),
        ("2026-10-11T00:00:04.000000Z", "chat.broadcast", "res-alpha", "quant",
         "alpha quant line", {"text": "alpha quant line"}),
        ("2026-10-11T00:00:05.000000Z", "chat.broadcast", "res-beta", "lobby",
         "beta lobby line", {"text": "beta lobby line"}),
        ("2026-10-11T00:00:06.000000Z", "idea.submit", "res-alpha", "cocreate",
         "idea line not chat", {"text": "idea line not chat"}),
        ("2026-10-11T00:00:07.000000Z", "avatar.intake", "res-gamma", "intake",
         "intake line not chat", {"text": "intake line not chat"}),
    ]
    for evt in world:
        st.append(*evt)
    env = st.room_message_board()
    board = env["room_message_board"]
    expected = [
        {"room": "lobby", "messages": 2, "actors": 2},
        {"room": "quant", "messages": 3, "actors": 2},
    ]
    ok_rows = (board == expected
               and all(set(r.keys()) == {"room", "messages", "actors"} for r in board))

    manual = [
        {"room": r, "messages": int(n), "actors": int(k)}
        for r, n, k in db_query(
            os.path.join(tmp, "board.db"),
            "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
            " WHERE type='chat.broadcast' GROUP BY zone ORDER BY zone")
    ]
    ok_manual = manual == board
    n_all = db_query(os.path.join(tmp, "board.db"),
                     "SELECT COUNT(*) FROM events")[0][0]
    n_board_msgs = sum(r["messages"] for r in board)
    ok_scope = n_all == 7 and n_board_msgs == 5  # non-chat rows never counted

    # insertion-order independence: same world, reversed append order
    st2 = EventStore(os.path.join(tmp, "board2.db"), disclaimer=notice)
    for evt in reversed(world):
        st2.append(*evt)
    ok_order = (json.dumps(st2.room_message_board(), sort_keys=True)
                == json.dumps(env, sort_keys=True))

    # live derivation, zero cache: a new broadcast changes the next read
    st.append("2026-10-11T00:00:08.000000Z", "chat.broadcast", "res-gamma",
              "lobby", "gamma lobby line", {"text": "gamma lobby line"})
    env_after = st.room_message_board()
    lobby_row = [r for r in env_after["room_message_board"] if r["room"] == "lobby"][0]
    ok_alive = lobby_row == {"room": "lobby", "messages": 3, "actors": 3}

    record("AC-S14", ok_empty and ok_rows and ok_manual and ok_scope
           and ok_order and ok_alive,
           "empty-board=%s envelope-keys=%s; rows=%s row-keys-exact=%s; "
           "manual-sql-cross=%s scope(events=%d board-msgs=%d non-chat-excluded)=%s; "
           "insertion-order-independent=%s; live-rederive=%s"
           % (ok_empty, sorted(empty_env.keys()), board,
              all(set(r.keys()) == {"room", "messages", "actors"} for r in board),
              ok_manual, n_all, n_board_msgs, ok_scope, ok_order, ok_alive))

    # ---- AC-S15: pure-read law, fail-closed, determinism, live db ----
    unit_db = os.path.join(tmp, "board.db")
    before = [db_query(unit_db, "SELECT COUNT(*) FROM " + t)[0][0]
              for t in ("events", "census_cache")]
    st.room_message_board()
    st2.room_message_board()
    after = [db_query(unit_db, "SELECT COUNT(*) FROM " + t)[0][0]
             for t in ("events", "census_cache")]
    ok_pure = before == after and before[0] == 8

    src = inspect.getsource(EventStore.room_message_board)
    ok_src = not any(word in src for word in ("INSERT", "UPDATE", "DELETE"))
    ok_det = (json.dumps(env_after, sort_keys=True)
              == json.dumps(st.room_message_board(), sort_keys=True))

    # legacy construction (no disclaimer): the face refuses fail-closed
    st3 = EventStore(os.path.join(tmp, "legacy.db"))
    face_refused = False
    try:
        st3.room_message_board()
    except ValueError as exc:
        face_refused = "E_STORE_NO_DISCLAIMER" in str(exc)
    st3.close()

    # live cross-check: this suite's real server db (server stopped; WAL
    # read recovery) - rooms lobby+quant hold real broadcasts from the
    # AC-S1..S10 flow; the face must equal the manual re-derivation.
    st_srv = EventStore(srv_db, disclaimer=notice)
    env_srv = st_srv.room_message_board()
    manual_srv = [
        {"room": r, "messages": int(n), "actors": int(k)}
        for r, n, k in db_query(
            srv_db,
            "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
            " WHERE type='chat.broadcast' GROUP BY zone ORDER BY zone")
    ]
    rooms_srv = sorted(r["room"] for r in env_srv["room_message_board"])
    ok_srv = (env_srv["room_message_board"] == manual_srv
              and rooms_srv == ["lobby", "quant"]
              and all(r["messages"] > 0 for r in env_srv["room_message_board"]))
    st_srv.close()
    st.close()
    st2.close()

    record("AC-S15", ok_pure and ok_src and ok_det and face_refused and ok_srv
           and all("True" in r for r in bad_refusals),
           "row-counts-stable=%s (%s); zero-write-method-src=%s; "
           "deterministic=%s; bad-disclaimer-construction-refused %s; "
           "legacy-no-disclaimer-face-refused=%s; live-db cross=%s rooms=%s"
           % (ok_pure, before, ok_src, ok_det, bad_refusals, face_refused,
              ok_srv, rooms_srv))


async def idea_board_cases(srv_db):
    """AC-S18/S19 (R1792): event-derived idea pool read face +
    idea.board protocol wiring. The store face re-derives the pool
    from persistent type='idea.submit' rows (the server in-memory
    proposal_pool stub resets on restart); the wire half starts a
    FRESH server process on this suite's real db and reads the full
    board back over the socket - the restart-survival proof (a fresh
    process's stub is empty by construction; the event-derived board
    carries every prior idea)."""
    from store import EventStore
    import server as lobby_server
    from sec_gate import SecGate as _SecGate
    tmp = tempfile.mkdtemp(prefix="lobby-ideaboard-")
    with open(CONFIG, encoding="utf-8") as handle:
        cfg = json.load(handle)
    notice = ("sandbox non-advisory notice: idea pool board rows are "
              "operational read-only derivations, not advice")

    # ---- AC-S18: semantics, scoping, ordering, cross-validation ----
    bad_refusals = []
    for value, label in (("", "empty"), ("   ", "whitespace"), (123, "non-str")):
        refused = False
        try:
            EventStore(os.path.join(tmp, "bad-%s.db" % label), disclaimer=value)
        except ValueError as exc:
            refused = "E_STORE_NO_DISCLAIMER" in str(exc)
        bad_refusals.append("%s=%s" % (label, refused))

    st = EventStore(os.path.join(tmp, "pool.db"), disclaimer=notice)
    empty_env = st.idea_pool_board()
    ok_empty = (set(empty_env.keys()) == {"idea_pool_board", "disclaimer"}
                and empty_env["disclaimer"] == notice
                and empty_env["idea_pool_board"] == [])

    # deterministic world: four ideas across two pools by three actors
    # + two non-idea rows (scope isolation: never counted)
    world = [
        ("2026-10-11T01:00:01.000000Z", "idea.submit", "res-alpha", "cocreate",
         "alpha idea one", {"text": "alpha idea one", "pool": "proposal-queue-stub"}),
        ("2026-10-11T01:00:02.000000Z", "idea.submit", "res-beta", "cocreate",
         "beta idea", {"text": "beta idea", "pool": "proposal-queue-stub"}),
        ("2026-10-11T01:00:03.000000Z", "idea.submit", "res-alpha", "cocreate",
         "alpha idea two", {"text": "alpha idea two", "pool": "proposal-queue-stub"}),
        ("2026-10-11T01:00:04.000000Z", "idea.submit", "res-gamma", "lab",
         "gamma lab idea", {"text": "gamma lab idea", "pool": "proposal-queue-stub"}),
        ("2026-10-11T01:00:05.000000Z", "chat.broadcast", "res-alpha", "lobby",
         "chat line never counted", {"text": "chat line never counted"}),
        ("2026-10-11T01:00:06.000000Z", "avatar.intake", "res-delta", "intake",
         "intake line never counted", {"text": "intake line never counted"}),
    ]
    for evt in world:
        st.append(*evt)
    env = st.idea_pool_board()
    board = env["idea_pool_board"]
    expected = [
        {"room": "cocreate", "ideas": 3, "actors": 2},
        {"room": "lab", "ideas": 1, "actors": 1},
    ]
    ok_rows = (board == expected
               and all(set(r.keys()) == {"room", "ideas", "actors"} for r in board))

    manual = [
        {"room": r, "ideas": int(n), "actors": int(k)}
        for r, n, k in db_query(
            os.path.join(tmp, "pool.db"),
            "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
            " WHERE type='idea.submit' GROUP BY zone ORDER BY zone")
    ]
    ok_manual = manual == board
    n_all = db_query(os.path.join(tmp, "pool.db"),
                     "SELECT COUNT(*) FROM events")[0][0]
    n_board_ideas = sum(r["ideas"] for r in board)
    ok_scope = n_all == 6 and n_board_ideas == 4  # non-idea rows never counted

    # insertion-order independence: same world, reversed append order
    st2 = EventStore(os.path.join(tmp, "pool2.db"), disclaimer=notice)
    for evt in reversed(world):
        st2.append(*evt)
    ok_order = (json.dumps(st2.idea_pool_board(), sort_keys=True)
                == json.dumps(env, sort_keys=True))

    # live derivation, zero cache: a new idea moves the next read
    st.append("2026-10-11T01:00:08.000000Z", "idea.submit", "res-delta",
              "lab", "delta lab idea", {"text": "delta lab idea"})
    env_after = st.idea_pool_board()
    lab_row = [r for r in env_after["idea_pool_board"] if r["room"] == "lab"][0]
    ok_alive = lab_row == {"room": "lab", "ideas": 2, "actors": 2}

    # ---- AC-S18: pure-read law, determinism, legacy refusal, live db ----
    unit_db = os.path.join(tmp, "pool.db")
    before = [db_query(unit_db, "SELECT COUNT(*) FROM " + t)[0][0]
              for t in ("events", "census_cache")]
    st.idea_pool_board()
    st2.idea_pool_board()
    after = [db_query(unit_db, "SELECT COUNT(*) FROM " + t)[0][0]
             for t in ("events", "census_cache")]
    ok_pure = before == after and before[0] == 7

    src = inspect.getsource(EventStore.idea_pool_board)
    ok_src = not any(word in src for word in ("INSERT", "UPDATE", "DELETE"))
    ok_det = (json.dumps(env_after, sort_keys=True)
              == json.dumps(st.idea_pool_board(), sort_keys=True))

    st3 = EventStore(os.path.join(tmp, "legacy.db"))
    face_refused = False
    try:
        st3.idea_pool_board()
    except ValueError as exc:
        face_refused = "E_STORE_NO_DISCLAIMER" in str(exc)
    st3.close()

    # live cross-check: this suite's real db - cocreate holds the real
    # idea submitted through the wire in the AC-S10 flow
    st_srv = EventStore(srv_db, disclaimer=notice)
    env_srv = st_srv.idea_pool_board()
    manual_srv = [
        {"room": r, "ideas": int(n), "actors": int(k)}
        for r, n, k in db_query(
            srv_db,
            "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
            " WHERE type='idea.submit' GROUP BY zone ORDER BY zone")
    ]
    pools_srv = sorted(r["room"] for r in env_srv["idea_pool_board"])
    ok_srv = (env_srv["idea_pool_board"] == manual_srv
              and pools_srv == ["cocreate"]
              and all(r["ideas"] > 0 for r in env_srv["idea_pool_board"]))
    st_srv.close()
    st.close()
    st2.close()

    record("AC-S18",
           ok_empty and ok_rows and ok_manual and ok_scope and ok_order
           and ok_alive and ok_pure and ok_src and ok_det and face_refused
           and ok_srv and all("True" in r for r in bad_refusals),
           "empty-board=%s rows=%s manual-sql-cross=%s "
           "scope(events=%d board-ideas=%d)=%s insertion-order-independent=%s "
           "live-rederive=%s; row-counts-stable=%s zero-write-src=%s "
           "deterministic=%s bad-disclaimer %s legacy-refused=%s "
           "live-db-cross=%s pools=%s"
           % (ok_empty, board, ok_manual, n_all, n_board_ideas, ok_scope,
              ok_order, ok_alive, ok_pure, ok_src, ok_det, bad_refusals,
              face_refused, ok_srv, pools_srv))

    # ---- AC-S19: wire face + restart survival + rooms filter + legacy ----
    async def recv_or_none(ws_, pred_, timeout_=3.0):
        try:
            return await recv_until(ws_, pred_, timeout_)
        except (TimeoutError, ConnectionClosed):
            return None

    port2 = _free_port()
    srv2 = ServerProc(port2, db=srv_db)
    srv2.start()
    wire_clients = []
    try:
        # restart-survival: srv2 is a FRESH process on the existing db -
        # its in-memory proposal_pool stub starts empty by construction;
        # the event-derived board must still return every prior idea.
        fb, _, _ = await open_client(port2)
        wire_clients.append(fb)
        await fb.send(frame("idea.board"))
        ib_frame = await recv_until(fb, lambda x: x.get("type") == "idea.board")
        p19 = ib_frame.get("payload", {})
        board19 = p19.get("board", [])
        manual19 = [
            {"room": r, "ideas": int(n), "actors": int(k)}
            for r, n, k in db_query(
                srv_db,
                "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
                " WHERE type='idea.submit' GROUP BY zone ORDER BY zone")
        ]
        ok_restart = (board19 == manual19
                      and sum(r["ideas"] for r in board19) > 0
                      and sorted(p19.keys()) == ["board", "disclaimer"]
                      and p19.get("disclaimer") == cfg["risk_warning"]["text"]
                      and ib_frame.get("ai_generated") is False
                      and ib_frame.get("actor") == "system")

        # fresh reflection: a new idea moves the next board query
        e2, _, _ = await open_client(port2)
        wire_clients.append(e2)
        await make_resident(e2)
        await e2.send(frame("idea.submit",
                            payload={"text": "idea board refresh probe"}))
        await recv_until(e2, lambda f: f.get("type") == "sys.notice"
                         and f.get("ai_generated") is True)
        await fb.send(frame("idea.board"))
        board19b = (await recv_until(
            fb, lambda x: x.get("type") == "idea.board")) \
            .get("payload", {}).get("board", [])
        coc1 = [r for r in board19 if r["room"] == "cocreate"][0]["ideas"]
        coc2 = [r for r in board19b if r["room"] == "cocreate"][0]["ideas"]
        ok_fresh = coc2 == coc1 + 1

        # rooms filter (AC-S17 law): default full / order-preserving
        # Python-side filter / honest empty / unknown names / bad forms
        full19 = board19b
        await fb.send(frame("idea.board", payload={"rooms": ["cocreate"]}))
        b19f = (await recv_until(
            fb, lambda x: x.get("type") == "idea.board")) \
            .get("payload", {}).get("board", [])
        ok_filter = (b19f == [row for row in full19 if row["room"] == "cocreate"]
                     and [row["room"] for row in b19f] == ["cocreate"])
        await fb.send(frame("idea.board", payload={"rooms": []}))
        b19e = (await recv_until(
            fb, lambda x: x.get("type") == "idea.board")) \
            .get("payload", {}).get("board", [])
        ok_empty19 = b19e == []
        await fb.send(frame("idea.board", payload={"rooms": ["nether"]}))
        b19u = (await recv_until(
            fb, lambda x: x.get("type") == "idea.board")) \
            .get("payload", {}).get("board", [])
        ok_unknown = b19u == []
        bad19 = []
        for bad in ("cocreate", ["cocreate", 3], [""], ["   "],
                    {"cocreate": 1}, True):
            await fb.send(frame("idea.board", payload={"rooms": bad}))
            rej19 = await recv_or_none(
                fb, lambda f: f.get("type") == "sec.reject"
                and f.get("payload", {}).get("code") == "E_BAD_FRAME")
            bad19.append(rej19 is not None)
        ok_bad19 = all(bad19)
        # default sentinel None + connection survival after the burst
        await fb.send(frame("idea.board", payload={"rooms": None}))
        b19d = await recv_or_none(fb, lambda x: x.get("type") == "idea.board")
        ok_default19 = (b19d is not None
                       and b19d.get("payload", {}).get("board", []) == full19)

        # legacy no-disclaimer store: graceful sec.reject, no crash
        legacy_dir = tempfile.mkdtemp(prefix="lobby-idealegacy-")
        legacy_store = EventStore(os.path.join(legacy_dir, "legacy.db"))
        legacy_gate = _SecGate.from_config(cfg)
        legacy_lobby = lobby_server.Lobby(cfg, legacy_gate, legacy_store)

        class _FakeWS:
            def __init__(self):
                self.frames = []

            async def send(self, data):
                self.frames.append(json.loads(data))

        legacy_client = lobby_server.Client(_FakeWS(), legacy_lobby.rooms)
        await legacy_lobby.handle_idea_board(legacy_client, None)
        rej_frame = legacy_client.ws.frames[-1]
        ok_legacy19 = (rej_frame.get("type") == "sec.reject"
                       and rej_frame.get("payload", {}).get("code")
                       == "E_STORE_NO_DISCLAIMER")
        legacy_store.close()

        record("AC-S19",
               ok_restart and ok_fresh and ok_filter and ok_empty19
               and ok_unknown and ok_bad19 and ok_default19 and ok_legacy19,
               "restart-survival(board==manual=%s ideas>0=%s keys=%s "
               "disclaimer-match=%s ai_generated=%s actor=%s); "
               "fresh-reflection=%s (%d->%d); filter=%s empty=%s "
               "unknown=%s bad-rejects=%s default-full=%s legacy-reject=%s"
               % (board19 == manual19,
                  sum(r["ideas"] for r in board19) > 0,
                  sorted(p19.keys()),
                  p19.get("disclaimer") == cfg["risk_warning"]["text"],
                  ib_frame.get("ai_generated") is False,
                  ib_frame.get("actor"),
                  ok_fresh, coc1, coc2, ok_filter, ok_empty19, ok_unknown,
                  bad19, ok_default19, ok_legacy19))
    finally:
        for ws in wire_clients:
            try:
                await ws.close()
            except Exception:
                pass
        srv2.stop()


def board_window_cases(srv_db):
    """AC-S20/S21/S22 (R1869): month-window parameter on the two
    lobby board read faces (room_message_board / idea_pool_board).
    window=None keeps the full-history read byte-stable (the live
    regression anchor: the existing AC-S14..S19 cases run unchanged
    in this same suite); an explicit "YYYY-MM" window slices the row
    set by each event's own record-time month before the per-zone
    aggregation -- zone order, scope isolation and the envelope
    shape untouched."""
    from store import EventStore
    tmp = tempfile.mkdtemp(prefix="lobby-boardwin-")
    notice = ("sandbox non-advisory notice: board rows are "
              "operational read-only derivations, not advice")
    st = EventStore(os.path.join(tmp, "win.db"), disclaimer=notice)

    # deterministic two-month world: October chat rows in two zones
    # + October ideas in two pools, November rows in one of each,
    # each month carrying only its own board's rows (cross-board
    # scope isolation is asserted per month below)
    world = [
        ("2026-10-01T01:00:01.000000Z", "chat.broadcast", "res-a", "lobby",
         "oct chat one", {"text": "oct chat one"}),
        ("2026-10-01T01:00:02.000000Z", "chat.broadcast", "res-b", "quant",
         "oct chat two", {"text": "oct chat two"}),
        ("2026-10-01T01:00:03.000000Z", "chat.broadcast", "res-a", "lobby",
         "oct chat three", {"text": "oct chat three"}),
        ("2026-10-02T01:00:04.000000Z", "idea.submit", "res-a", "cocreate",
         "oct idea one", {"text": "oct idea one", "pool": "proposal-queue-stub"}),
        ("2026-10-02T01:00:05.000000Z", "idea.submit", "res-c", "lab",
         "oct idea two", {"text": "oct idea two", "pool": "proposal-queue-stub"}),
        ("2026-11-05T01:00:06.000000Z", "chat.broadcast", "res-b", "quant",
         "nov chat one", {"text": "nov chat one"}),
        ("2026-11-05T01:00:07.000000Z", "idea.submit", "res-d", "cocreate",
         "nov idea one", {"text": "nov idea one", "pool": "proposal-queue-stub"}),
    ]
    for evt in world:
        st.append(*evt)

    # ---- AC-S20: semantics, order, honest empty, cross-validation ----
    full_room = st.room_message_board()
    full_idea = st.idea_pool_board()
    ok_default_shape = (
        full_room["room_message_board"] == [
            {"room": "lobby", "messages": 2, "actors": 1},
            {"room": "quant", "messages": 2, "actors": 1},
        ]
        and full_idea["idea_pool_board"] == [
            {"room": "cocreate", "ideas": 2, "actors": 2},
            {"room": "lab", "ideas": 1, "actors": 1},
        ])

    oct_room = st.room_message_board(window="2026-10")
    oct_idea = st.idea_pool_board(window="2026-10")
    nov_room = st.room_message_board(window="2026-11")
    nov_idea = st.idea_pool_board(window="2026-11")
    ok_window_rows = (
        oct_room["room_message_board"] == [
            {"room": "lobby", "messages": 2, "actors": 1},
            {"room": "quant", "messages": 1, "actors": 1},
        ]
        and oct_idea["idea_pool_board"] == [
            {"room": "cocreate", "ideas": 1, "actors": 1},
            {"room": "lab", "ideas": 1, "actors": 1},
        ]
        and nov_room["room_message_board"] == [
            {"room": "quant", "messages": 1, "actors": 1},
        ]
        and nov_idea["idea_pool_board"] == [
            {"room": "cocreate", "ideas": 1, "actors": 1},
        ])

    # order preservation: zone-ascending inside every window read
    ok_order = all(
        [r["room"] for r in b] == sorted(r["room"] for r in b)
        for b in (oct_room["room_message_board"],
                  oct_idea["idea_pool_board"],
                  nov_room["room_message_board"],
                  nov_idea["idea_pool_board"]))

    # honest empty: a month with no rows is an empty board, same keys
    empty_room = st.room_message_board(window="2025-01")
    empty_idea = st.idea_pool_board(window="2025-01")
    ok_empty = (empty_room["room_message_board"] == []
                and empty_idea["idea_pool_board"] == []
                and set(empty_room.keys())
                == {"room_message_board", "disclaimer"}
                and set(empty_idea.keys())
                == {"idea_pool_board", "disclaimer"}
                and empty_room["disclaimer"] == notice)

    # manual SQL mirror cross (record-time substr law) + the two
    # windowed months partition the full default board
    manual_oct_room = [
        {"room": z, "messages": int(n), "actors": int(k)}
        for z, n, k in db_query(
            os.path.join(tmp, "win.db"),
            "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
            " WHERE type='chat.broadcast' AND substr(ts_utc,1,7)='2026-10'"
            " GROUP BY zone ORDER BY zone")
    ]
    ok_manual = (manual_oct_room == oct_room["room_message_board"]
                 and sum(r["messages"]
                         for r in full_room["room_message_board"])
                 == sum(r["messages"]
                        for r in oct_room["room_message_board"])
                 + sum(r["messages"]
                       for r in nov_room["room_message_board"]))

    # record-time law: insertion-order independence for windowed reads
    st2 = EventStore(os.path.join(tmp, "win2.db"), disclaimer=notice)
    for evt in reversed(world):
        st2.append(*evt)
    ok_reorder = (
        json.dumps(st2.room_message_board(window="2026-10"), sort_keys=True)
        == json.dumps(oct_room, sort_keys=True)
        and json.dumps(st2.idea_pool_board(window="2026-11"), sort_keys=True)
        == json.dumps(nov_idea, sort_keys=True))
    st2.close()

    # cross-board in-window scope isolation: October's chat rows (3)
    # never feed the idea board (2 ideas only), and vice versa
    ok_scope = (oct_room["room_message_board"][0]["messages"] == 2
                and oct_idea["idea_pool_board"][0]["ideas"] == 1
                and sum(r["ideas"] for r in oct_idea["idea_pool_board"]) == 2
                and sum(r["messages"]
                        for r in oct_room["room_message_board"]) == 3)

    record("AC-S20", ok_default_shape and ok_window_rows and ok_order
           and ok_empty and ok_manual and ok_reorder and ok_scope,
           "default-shape=%s window-rows=%s order=%s empty=%s "
           "manual-sql=%s reorder-independent=%s scope=%s"
           % (ok_default_shape, ok_window_rows, ok_order, ok_empty,
              ok_manual, ok_reorder, ok_scope))

    # ---- AC-S21: 14 bad-window forms fail-closed on both boards ----
    bads14 = ("2026-13", "2026-00", "2026-1", "2026/10", "2026",
              "202610", "abcd", "", 2026, True, 2.5,
              "2026-10\n", "2026-10 ", "2026-10\r")
    n_before = db_query(os.path.join(tmp, "win.db"),
                        "SELECT COUNT(*) FROM events")[0][0]
    rejects = []
    for bad in bads14:
        for face, label in ((st.room_message_board, "room"),
                            (st.idea_pool_board, "idea")):
            refused = False
            try:
                face(window=bad)
            except ValueError as exc:
                refused = "E_LS_BAD_WINDOW" in str(exc)
            rejects.append((label, repr(bad), refused))
    ok_bads = all(r[2] for r in rejects) and len(rejects) == 28
    n_after = db_query(os.path.join(tmp, "win.db"),
                       "SELECT COUNT(*) FROM events")[0][0]
    ok_no_side = n_before == n_after

    # gate order: the disclaimer gate stays outermost -- a legacy
    # store without a disclaimer refuses E_STORE_NO_DISCLAIMER first
    # even for a bad window
    st3 = EventStore(os.path.join(tmp, "legacy.db"))
    legacy_first = False
    try:
        st3.room_message_board(window="2026-13")
    except ValueError as exc:
        legacy_first = "E_STORE_NO_DISCLAIMER" in str(exc)
    st3.close()

    record("AC-S21", ok_bads and ok_no_side and legacy_first,
           "bads14 x 2 boards all E_LS_BAD_WINDOW=%s (%d rejects); "
           "zero-side-effects events %d==%d; "
           "disclaimer-gate-outermost=%s"
           % (ok_bads, len(rejects), n_before, n_after, legacy_first))

    # ---- AC-S22: pure-read law, determinism, live-db cross ----
    unit_db = os.path.join(tmp, "win.db")
    before = [db_query(unit_db, "SELECT COUNT(*) FROM " + t)[0][0]
              for t in ("events", "census_cache")]
    st.room_message_board(window="2026-10")
    st.idea_pool_board(window="2026-11")
    st.room_message_board(window="2025-01")
    st.idea_pool_board(window="2025-01")
    after = [db_query(unit_db, "SELECT COUNT(*) FROM " + t)[0][0]
             for t in ("events", "census_cache")]
    ok_pure = before == after and before[0] == 7
    src_both = (inspect.getsource(st.room_message_board)
                + inspect.getsource(st.idea_pool_board))
    ok_src = not any(word in src_both
                     for word in ("INSERT", "UPDATE", "DELETE"))

    # determinism: same windowed read twice byte-identical; the
    # windowed reads above never mutated the default read
    det_room = (json.dumps(st.room_message_board(window="2026-10"),
                           sort_keys=True)
                == json.dumps(st.room_message_board(window="2026-10"),
                              sort_keys=True))
    det_idea = (json.dumps(st.idea_pool_board(window="2026-11"),
                           sort_keys=True)
                == json.dumps(st.idea_pool_board(window="2026-11"),
                              sort_keys=True))
    ok_default_unchanged = (
        json.dumps(st.room_message_board(), sort_keys=True)
        == json.dumps(full_room, sort_keys=True)
        and json.dumps(st.idea_pool_board(), sort_keys=True)
        == json.dumps(full_idea, sort_keys=True))
    st.close()

    # live cross: this suite's real db -- the current UTC month board
    # equals the manual SQL mirror; a far month is an honest empty
    now_month = time.strftime("%Y-%m", time.gmtime())
    st_srv = EventStore(srv_db, disclaimer=notice)
    srv_room = st_srv.room_message_board(window=now_month)
    manual_srv = [
        {"room": z, "messages": int(n), "actors": int(k)}
        for z, n, k in db_query(
            srv_db,
            "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
            " WHERE type='chat.broadcast' AND substr(ts_utc,1,7)=?"
            " GROUP BY zone ORDER BY zone", (now_month,))
    ]
    srv_far = st_srv.room_message_board(window="2000-01")
    ok_live = (srv_room["room_message_board"] == manual_srv
               and srv_far["room_message_board"] == [])
    st_srv.close()

    record("AC-S22", ok_pure and ok_src and det_room and det_idea
           and ok_default_unchanged and ok_live,
           "row-counts-stable=%s zero-write-src=%s det-room=%s "
           "det-idea=%s default-unchanged=%s live-db-cross=%s "
           "(month=%s rows=%d)"
           % (ok_pure, ok_src, det_room, det_idea, ok_default_unchanged,
              ok_live, now_month, len(manual_srv)))


def board_monthroll_cases():
    """AC-S23/S24/S25 (R1876): cross-month roll preservation on the
    two lobby board read faces. The roll is data-driven: rows are
    appended with explicit ts_utc stamps through store.append (no
    frozen clock needed -- the lobby boards slice windows on each
    event's own record time, unlike the apidev/freetrial frozen-clock
    families). October is snapshotted first, November rows then
    arrive (the roll), and every windowed read keeps its own month's
    truth."""
    from store import EventStore
    tmp = tempfile.mkdtemp(prefix="lobby-monthroll-")
    notice = ("sandbox non-advisory notice: board rows are "
              "operational read-only derivations, not advice")
    db = os.path.join(tmp, "roll.db")
    st = EventStore(db, disclaimer=notice)

    # October world: 3 chat rows over 2 zones, 2 idea rows over 2
    # pools, plus 1 cross-board non-counted row (avatar.update feeds
    # neither board and lands inside zone "lobby" on purpose).
    oct_world = [
        ("2026-10-01T01:00:01.000000Z", "chat.broadcast", "res-a", "lobby",
         "oct chat one", {"text": "oct chat one"}),
        ("2026-10-01T01:00:02.000000Z", "chat.broadcast", "res-b", "quant",
         "oct chat two", {"text": "oct chat two"}),
        ("2026-10-01T01:00:03.000000Z", "chat.broadcast", "res-a", "lobby",
         "oct chat three", {"text": "oct chat three"}),
        ("2026-10-02T01:00:04.000000Z", "idea.submit", "res-a", "cocreate",
         "oct idea one", {"text": "oct idea one", "pool": "proposal-queue-stub"}),
        ("2026-10-02T01:00:05.000000Z", "idea.submit", "res-c", "lab",
         "oct idea two", {"text": "oct idea two", "pool": "proposal-queue-stub"}),
        ("2026-10-03T01:00:06.000000Z", "avatar.update", "res-a", "lobby",
         "oct avatar row", {"name": "resident a"}),
    ]
    for evt in oct_world:
        st.append(*evt)

    # pre-roll snapshots: explicit October window reads on both
    # boards; with October the only month on file the default reads
    # equal the windowed reads (the full-window semantics anchor).
    oct_room_snap = st.room_message_board(window="2026-10")
    oct_idea_snap = st.idea_pool_board(window="2026-10")
    pre_default_room = st.room_message_board()
    pre_default_idea = st.idea_pool_board()

    # the roll: November rows arrive with new record times. zone
    # "arena" carries zero October rows -- its grid cell is born
    # inside November only (the new-month grid proof).
    nov_world = [
        ("2026-11-05T01:00:07.000000Z", "chat.broadcast", "res-b", "lobby",
         "nov chat one", {"text": "nov chat one"}),
        ("2026-11-05T01:00:08.000000Z", "chat.broadcast", "res-d", "arena",
         "nov chat two", {"text": "nov chat two"}),
        ("2026-11-06T01:00:09.000000Z", "chat.broadcast", "res-d", "arena",
         "nov chat three", {"text": "nov chat three"}),
        ("2026-11-06T01:00:10.000000Z", "idea.submit", "res-d", "cocreate",
         "nov idea one", {"text": "nov idea one", "pool": "proposal-queue-stub"}),
        ("2026-11-07T01:00:11.000000Z", "idea.submit", "res-e", "arena",
         "nov idea two", {"text": "nov idea two", "pool": "proposal-queue-stub"}),
        ("2026-11-07T01:00:12.000000Z", "avatar.update", "res-c", "lab",
         "nov avatar row", {"name": "resident c"}),
    ]
    for evt in nov_world:
        st.append(*evt)

    nov_room = st.room_message_board(window="2026-11")
    nov_idea = st.idea_pool_board(window="2026-11")
    post_oct_room = st.room_message_board(window="2026-10")
    post_oct_idea = st.idea_pool_board(window="2026-10")

    # ---- AC-S23: roll preservation core ----
    # (1) new-month rows land in the new-month grid: the November
    # window reads carry the new rows and the arena cell is born
    # inside November; manual SQL mirror cross (record-time law).
    ok_nov_grid = (
        nov_room["room_message_board"] == [
            {"room": "arena", "messages": 2, "actors": 1},
            {"room": "lobby", "messages": 1, "actors": 1},
        ]
        and nov_idea["idea_pool_board"] == [
            {"room": "arena", "ideas": 1, "actors": 1},
            {"room": "cocreate", "ideas": 1, "actors": 1},
        ])
    manual_nov_room = [
        {"room": z, "messages": int(n), "actors": int(k)}
        for z, n, k in db_query(
            db,
            "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
            " WHERE type='chat.broadcast' AND substr(ts_utc,1,7)='2026-11'"
            " GROUP BY zone ORDER BY zone")
    ]
    manual_nov_idea = [
        {"room": z, "ideas": int(n), "actors": int(k)}
        for z, n, k in db_query(
            db,
            "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
            " WHERE type='idea.submit' AND substr(ts_utc,1,7)='2026-11'"
            " GROUP BY zone ORDER BY zone")
    ]
    ok_nov_manual = (manual_nov_room == nov_room["room_message_board"]
                     and manual_nov_idea == nov_idea["idea_pool_board"])

    # (2) the old-month window reads keep the pre-roll snapshots
    # byte-identical on both boards, and the two windows never leak
    # either way (each window sums only its own month's rows).
    ok_oct_snap = (
        json.dumps(post_oct_room, sort_keys=True)
        == json.dumps(oct_room_snap, sort_keys=True)
        and json.dumps(post_oct_idea, sort_keys=True)
        == json.dumps(oct_idea_snap, sort_keys=True))
    ok_no_leak = (
        sum(r["messages"] for r in post_oct_room["room_message_board"]) == 3
        and sum(r["messages"] for r in nov_room["room_message_board"]) == 3
        and sum(r["ideas"] for r in post_oct_idea["idea_pool_board"]) == 2
        and sum(r["ideas"] for r in nov_idea["idea_pool_board"]) == 2)

    record("AC-S23", ok_nov_grid and ok_nov_manual and ok_oct_snap
           and ok_no_leak,
           "nov-grid-born=%s nov-manual-sql=%s oct-snapshot-kept=%s "
           "no-leak-either-way=%s (oct msgs 3+3 / ideas 2+2)"
           % (ok_nov_grid, ok_nov_manual, ok_oct_snap, ok_no_leak))

    # ---- AC-S24: default full-window semantics across the roll ----
    # lobby default = the full-history read (eventtickets full-window
    # family, NOT the apidev current-month family): the default board
    # carries BOTH months -- a cross-month zone merges its October +
    # November counts, and the two explicit windows partition the
    # default board per zone exactly.
    full_room = st.room_message_board()
    full_idea = st.idea_pool_board()
    ok_default_shape = (
        full_room["room_message_board"] == [
            {"room": "arena", "messages": 2, "actors": 1},
            {"room": "lobby", "messages": 3, "actors": 2},
            {"room": "quant", "messages": 1, "actors": 1},
        ]
        and full_idea["idea_pool_board"] == [
            {"room": "arena", "ideas": 1, "actors": 1},
            {"room": "cocreate", "ideas": 2, "actors": 2},
            {"room": "lab", "ideas": 1, "actors": 1},
        ])
    oct_msgs = {r["room"]: r["messages"]
               for r in post_oct_room["room_message_board"]}
    nov_msgs = {r["room"]: r["messages"]
                for r in nov_room["room_message_board"]}
    oct_ideas = {r["room"]: r["ideas"]
                 for r in post_oct_idea["idea_pool_board"]}
    nov_ideas = {r["room"]: r["ideas"]
                 for r in nov_idea["idea_pool_board"]}
    ok_partition = (
        all(r["messages"] == oct_msgs.get(r["room"], 0)
            + nov_msgs.get(r["room"], 0)
            for r in full_room["room_message_board"])
        and all(r["ideas"] == oct_ideas.get(r["room"], 0)
                + nov_ideas.get(r["room"], 0)
                for r in full_idea["idea_pool_board"]))
    ok_pre_default = (
        json.dumps(pre_default_room, sort_keys=True)
        == json.dumps(oct_room_snap, sort_keys=True)
        and json.dumps(pre_default_idea, sort_keys=True)
        == json.dumps(oct_idea_snap, sort_keys=True))

    record("AC-S24", ok_default_shape and ok_partition and ok_pre_default,
           "default-both-months=%s windows-partition-default=%s "
           "pre-roll-default==oct-window=%s"
           % (ok_default_shape, ok_partition, ok_pre_default))

    # ---- AC-S25: immutable rows never lost + non-counted rows ----
    # events total == October rows + November rows (per-month SELECT
    # cross); the two avatar.update rows (cross-board non-counted,
    # sitting inside board zones on purpose) never surface in any
    # board read; re-counting after every read proves the pure-read
    # law; a second October window read stays byte-identical.
    total = db_query(db, "SELECT COUNT(*) FROM events")[0][0]
    oct_n = db_query(db, "SELECT COUNT(*) FROM events WHERE"
                     " substr(ts_utc,1,7)='2026-10'")[0][0]
    nov_n = db_query(db, "SELECT COUNT(*) FROM events WHERE"
                     " substr(ts_utc,1,7)='2026-11'")[0][0]
    noncounted = db_query(
        db, "SELECT COUNT(*) FROM events WHERE type NOT IN"
        " ('chat.broadcast','idea.submit')")[0][0]
    ok_total = (total == oct_n + nov_n and total == 12
                and oct_n == 6 and nov_n == 6 and noncounted == 2)
    all_chat = db_query(db, "SELECT COUNT(*) FROM events WHERE"
                        " type='chat.broadcast'")[0][0]
    all_ideas = db_query(db, "SELECT COUNT(*) FROM events WHERE"
                         " type='idea.submit'")[0][0]
    ok_type_iso = (
        sum(r["messages"] for r in full_room["room_message_board"])
        == all_chat
        and sum(r["ideas"] for r in full_idea["idea_pool_board"])
        == all_ideas
        and all_chat == 6 and all_ideas == 4)
    total_after = db_query(db, "SELECT COUNT(*) FROM events")[0][0]
    ok_pure = total_after == total
    ok_det = (json.dumps(st.room_message_board(window="2026-10"),
                         sort_keys=True)
              == json.dumps(oct_room_snap, sort_keys=True))
    st.close()

    record("AC-S25", ok_total and ok_type_iso and ok_pure and ok_det,
           "events-total=%d (oct %d + nov %d, non-counted %d)=%s "
           "type-isolation=%s pure-read=%s oct-reread-stable=%s"
           % (total, oct_n, nov_n, noncounted, ok_total,
              ok_type_iso, ok_pure, ok_det))


def board_readcap_cases(srv_db):
    """AC-S26..S31 (R1882): read-cap limit parameter on the two
    lobby board read faces (the R1729/R1880 read-hat family law;
    the seed = the boards' own R1869 window family). limit=0 is
    the sole default sentinel (full read, byte-identical
    envelope); a positive int caps the board to the tail window -
    the same rows the mirror clause (ORDER BY zone DESC LIMIT N,
    reversed back to ascending) yields - with a four-key overflow
    block whose total is the full (window-filtered) board count,
    never the post-truncation one. Zone is the GROUP BY key, so
    board rows are structurally tie-free: no rowid tie-break."""
    from store import EventStore
    tmp = tempfile.mkdtemp(prefix="lobby-boardcap-")
    notice = ("sandbox non-advisory notice: board rows are "
              "operational read-only derivations, not advice")
    db = os.path.join(tmp, "cap.db")
    st = EventStore(db, disclaimer=notice)

    # six-zone world per board family, ascending-unique zones:
    # October carries all six zones on both board types; November
    # carries only two zones (delta, zeta) -- the window x cap
    # orthogonality probe (in-window total 2 vs global 6).
    zones = ["alpha", "beta", "delta", "epsilon", "gamma", "zeta"]
    for i, z in enumerate(zones):
        st.append("2026-10-01T01:00:%02d.000000Z" % (i + 1),
                  "chat.broadcast", "res-%d" % i, z,
                  "oct chat %d" % i, {"text": "x"})
        st.append("2026-10-01T02:00:%02d.000000Z" % (i + 1),
                  "idea.submit", "res-%d" % i, z,
                  "oct idea %d" % i, {"text": "y"})
    for z, actor in (("delta", "res-d2"), ("zeta", "res-z2")):
        st.append("2026-11-05T01:00:%02d.000000Z" % (3 if z == "delta"
                                                     else 4),
                  "chat.broadcast", actor, z, "nov chat", {"text": "x"})
        st.append("2026-11-05T02:00:%02d.000000Z" % (3 if z == "delta"
                                                     else 4),
                  "idea.submit", actor, z, "nov idea", {"text": "y"})

    # ---- AC-S26: default sentinel + overflow block law ----
    full_room = st.room_message_board()
    full_idea = st.idea_pool_board()
    ok_default = (
        set(full_room.keys()) == {"room_message_board", "disclaimer"}
        and set(full_idea.keys()) == {"idea_pool_board", "disclaimer"}
        and [r["room"] for r in full_room["room_message_board"]]
        == sorted(zones)
        and len(full_room["room_message_board"]) == 6
        and len(full_idea["idea_pool_board"]) == 6
        and json.dumps(st.room_message_board(window="2026-11"),
                       sort_keys=True)
        == json.dumps(st.room_message_board(window="2026-11", limit=0),
                      sort_keys=True))
    cap_room = st.room_message_board(limit=2)
    cap_idea = st.idea_pool_board(limit=2)
    ok_cap_keys = (
        set(cap_room.keys())
        == {"room_message_board", "disclaimer", "limit", "total",
            "returned", "truncated"}
        and set(cap_idea.keys())
        == {"idea_pool_board", "disclaimer", "limit", "total",
            "returned", "truncated"}
        and cap_room["limit"] == 2 and cap_idea["limit"] == 2
        and cap_room["total"] == 6 and cap_idea["total"] == 6
        and cap_room["returned"] == 2 and cap_idea["returned"] == 2
        and cap_room["truncated"] is True
        and cap_idea["truncated"] is True
        and cap_room["room_message_board"]
        == full_room["room_message_board"][-2:]
        and cap_idea["idea_pool_board"]
        == full_idea["idea_pool_board"][-2:])
    record("AC-S26", ok_default and ok_cap_keys,
           "default-2keys-full-6zones=%s cap-6keys-total6-returned2-"
           "truncated=%s tail==full[-2:]=%s"
           % (ok_default, ok_cap_keys,
              cap_room["room_message_board"]
              == full_room["room_message_board"][-2:]))

    # ---- AC-S27: five bad limit forms + gate order ----
    bads = [-1, True, "2", 2.5, None]
    n_before = db_query(db, "SELECT COUNT(*) FROM events")[0][0]
    rejects = 0
    for bad in bads:
        for face in (st.room_message_board, st.idea_pool_board):
            refused = False
            try:
                face(limit=bad)
            except ValueError as exc:
                refused = "E_LS_BAD_LIMIT" in str(exc)
            rejects += 1 if refused else 0
    n_after = db_query(db, "SELECT COUNT(*) FROM events")[0][0]
    gate_code = win_code = ""
    try:
        st.room_message_board(limit=-1, window="2026-13")
    except ValueError as exc:
        gate_code = str(exc)
    try:
        st.idea_pool_board(window="2026-13")
    except ValueError as exc:
        win_code = str(exc)
    st_leg = EventStore(os.path.join(tmp, "legacy.db"))
    legacy_first = False
    try:
        st_leg.room_message_board(limit=-1)
    except ValueError as exc:
        legacy_first = "E_STORE_NO_DISCLAIMER" in str(exc)
    st_leg.close()
    ok27 = (rejects == 10 and n_before == n_after
            and "E_LS_BAD_LIMIT" in gate_code
            and "E_LS_BAD_WINDOW" in win_code and legacy_first)
    record("AC-S27", ok27,
           "%d/10 bad-limit x 2 boards rejected E_LS_BAD_LIMIT; "
           "events flat %d==%d; double-bad->limit gate wins=%s; "
           "bad-window-only=%s; disclaimer-outermost=%s"
           % (rejects, n_before, n_after,
              "E_LS_BAD_LIMIT" in gate_code,
              "E_LS_BAD_WINDOW" in win_code, legacy_first))

    # ---- AC-S28: tail-window three-path cross (slice/mirror) ----
    ok28 = True
    for n in (1, 3, 4):
        for face, board_key, etype in (
                (st.room_message_board, "room_message_board",
                 "chat.broadcast"),
                (st.idea_pool_board, "idea_pool_board", "idea.submit")):
            full = face()
            capped = face(limit=n)
            mirror = [
                {"room": z,
                 ("messages" if etype == "chat.broadcast" else "ideas"):
                 int(cnt), "actors": int(k)}
                for z, cnt, k in db_query(
                    db,
                    "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM"
                    " events WHERE type = ? GROUP BY zone"
                    " ORDER BY zone DESC LIMIT ?", (etype, n))
            ][::-1]
            rows = capped[board_key]
            ok28 = ok28 and rows == full[board_key][-n:] == mirror
            ok28 = ok28 and [r["room"] for r in rows] \
                == sorted(r["room"] for r in rows)
            ok28 = ok28 and capped["total"] == 6 \
                and capped["returned"] == len(rows) \
                and capped["truncated"] == (len(rows) < 6)
    record("AC-S28", ok28,
           "tail slice == mirror SQL (zone DESC LIMIT N reversed) on "
           "n=1/3/4 x both boards, zone-ascending kept=%s" % ok28)

    # ---- AC-S29: window x cap orthogonality ----
    nov_full_room = st.room_message_board(window="2026-11")
    nov_full_idea = st.idea_pool_board(window="2026-11")
    nov_cap_room = st.room_message_board(window="2026-11", limit=1)
    nov_cap_idea = st.idea_pool_board(window="2026-11", limit=1)
    oct_cap_room = st.room_message_board(window="2026-10", limit=4)
    ok29 = (
        nov_cap_room["total"] == 2 and nov_cap_room["returned"] == 1
        and nov_cap_room["truncated"] is True
        and nov_cap_room["room_message_board"]
        == nov_full_room["room_message_board"][-1:]
        and nov_cap_idea["total"] == 2 and nov_cap_idea["returned"] == 1
        and nov_cap_idea["idea_pool_board"]
        == nov_full_idea["idea_pool_board"][-1:]
        and oct_cap_room["total"] == 6 and oct_cap_room["returned"] == 4
        and oct_cap_room["room_message_board"]
        == st.room_message_board(window="2026-10")
        ["room_message_board"][-4:]
        and [r["room"] for r in nov_cap_room["room_message_board"]]
        == sorted(r["room"] for r in nov_cap_room["room_message_board"])
        and set(nov_cap_room.keys())
        == {"room_message_board", "disclaimer", "limit", "total",
            "returned", "truncated"})
    record("AC-S29", ok29,
           "window-before-cap: nov total=2 (in-window, not global 6); "
           "windowed cap rows == windowed full tail; no re-order; "
           "windowed-cap envelope exactly 6 keys (no window echo)=%s"
           % ok29)

    # ---- AC-S30: honest empty + boundary states ----
    st_e = EventStore(os.path.join(tmp, "empty.db"), disclaimer=notice)
    empty_room = st_e.room_message_board(limit=3)
    empty_idea = st_e.idea_pool_board(limit=3)
    zero_month = st.room_message_board(window="2000-01", limit=2)
    zero_month_idea = st.idea_pool_board(window="2000-01", limit=2)
    boundary = st.room_message_board(limit=6)
    one_row = st.room_message_board(limit=1)
    st_e.close()
    ok30 = (
        empty_room["room_message_board"] == []
        and empty_room["total"] == 0 and empty_room["returned"] == 0
        and empty_room["truncated"] is False and empty_room["limit"] == 3
        and empty_idea["idea_pool_board"] == []
        and empty_idea["total"] == 0 and empty_idea["truncated"] is False
        and zero_month["room_message_board"] == []
        and zero_month["total"] == 0 and zero_month["truncated"] is False
        and zero_month_idea["idea_pool_board"] == []
        and boundary["total"] == 6 and boundary["returned"] == 6
        and boundary["truncated"] is False
        and boundary["room_message_board"]
        == full_room["room_message_board"]
        and one_row["returned"] == 1 and one_row["truncated"] is True
        and one_row["room_message_board"]
        == full_room["room_message_board"][-1:])
    record("AC-S30", ok30,
           "empty board + zero-row month keep the 4-key block honest "
           "(total=0 truncated=False); limit==total full return; "
           "limit=1 tail-1=%s" % ok30)

    # ---- AC-S31: pure-read + determinism + live-db cross ----
    before31 = [db_query(db, "SELECT COUNT(*) FROM " + t)[0][0]
                for t in ("events", "census_cache")]
    st.room_message_board(limit=2)
    st.idea_pool_board(limit=2)
    st.room_message_board(window="2026-10", limit=5)
    st.idea_pool_board(window="2026-11", limit=1)
    after31 = [db_query(db, "SELECT COUNT(*) FROM " + t)[0][0]
               for t in ("events", "census_cache")]
    ok_pure = before31 == after31 and before31[0] == 16
    src_both = (inspect.getsource(st.room_message_board)
                + inspect.getsource(st.idea_pool_board))
    ok_src = not any(word in src_both
                     for word in ("INSERT", "UPDATE", "DELETE"))
    det = (json.dumps(st.room_message_board(limit=2), sort_keys=True)
           == json.dumps(cap_room, sort_keys=True)
           and json.dumps(st.idea_pool_board(limit=2), sort_keys=True)
           == json.dumps(cap_idea, sort_keys=True))
    st.close()
    now_month = time.strftime("%Y-%m", time.gmtime())
    st_srv = EventStore(srv_db, disclaimer=notice)
    srv_cap = st_srv.room_message_board(window=now_month, limit=2)
    manual_srv = [
        {"room": z, "messages": int(n), "actors": int(k)}
        for z, n, k in db_query(
            srv_db,
            "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
            " WHERE type='chat.broadcast' AND substr(ts_utc,1,7)=?"
            " GROUP BY zone ORDER BY zone DESC LIMIT 2", (now_month,))
    ][::-1]
    st_srv.close()
    ok_live = (srv_cap["room_message_board"] == manual_srv
               and srv_cap["returned"] == len(manual_srv)
               and srv_cap["total"]
               >= srv_cap["returned"])
    record("AC-S31", ok_pure and ok_src and det and ok_live,
           "row-counts-stable=%s zero-write-src=%s det-byte-identical=%s "
           "live-db-cross=%s (month=%s returned=%d total=%d)"
           % (ok_pure, ok_src, det, ok_live, now_month,
              srv_cap["returned"], srv_cap["total"]))


def board_persist_cases():
    """AC-S32..S38 (R1891): the two lobby board read faces across
    an instance restart (the R1882 read-cap family; the
    R1879/R1880/R1882 persist-family law). Both boards are pure
    read-only derivations over the immutable events table - no
    cache counters, no in-memory board state - so a close +
    same-db reopen must reproduce every read face (default /
    cap / window x cap) byte-for-byte; old explicit windows stay
    frozen across restarts while new data lands in new months;
    a second restart keeps the guarantee. Suite-only round:
    zero product-code change, the example window pins the
    existing guarantee into the suite in-book."""
    from store import EventStore
    cfg_sha_in = hashlib.sha256(
        open(CONFIG, "rb").read()).hexdigest()
    store_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "store.py"), "rb").read()).hexdigest()
    tmp = tempfile.mkdtemp(prefix="lobby-boardpersist-")
    notice = ("sandbox non-advisory notice: board rows are "
              "operational read-only derivations, not advice")
    db = os.path.join(tmp, "persist.db")
    st = EventStore(db, disclaimer=notice)

    # October anchor: six zones on both board types (the R1882
    # readcap world shape).
    zones = ["alpha", "beta", "delta", "epsilon", "gamma", "zeta"]
    for i, z in enumerate(zones):
        st.append("2026-10-01T01:00:%02d.000000Z" % (i + 1),
                  "chat.broadcast", "res-%d" % i, z,
                  "oct chat %d" % i, {"text": "x"})
        st.append("2026-10-01T02:00:%02d.000000Z" % (i + 1),
                  "idea.submit", "res-%d" % i, z,
                  "oct idea %d" % i, {"text": "y"})

    def faces(store):
        return {
            "def_room": json.dumps(store.room_message_board(),
                                   sort_keys=True),
            "def_idea": json.dumps(store.idea_pool_board(),
                                  sort_keys=True),
            "cap_room": json.dumps(store.room_message_board(limit=2),
                                   sort_keys=True),
            "cap_idea": json.dumps(store.idea_pool_board(limit=2),
                                   sort_keys=True),
            "wcap_room": json.dumps(
                store.room_message_board(window="2026-10", limit=2),
                sort_keys=True),
            "wfull_room": json.dumps(
                store.room_message_board(window="2026-10"),
                sort_keys=True),
        }

    snap = faces(st)
    d_room = json.loads(snap["def_room"])["room_message_board"]
    c_room = json.loads(snap["cap_room"])
    wcap = json.loads(snap["wcap_room"])

    # ---- AC-S32: oct anchor world + pre-close six-face snapshot ----
    ok32 = (
        [r["room"] for r in d_room] == sorted(zones)
        and len(d_room) == 6
        and c_room["total"] == 6 and c_room["returned"] == 2
        and c_room["truncated"] is True
        and c_room["room_message_board"] == d_room[-2:]
        and set(c_room.keys())
        == {"room_message_board", "disclaimer", "limit", "total",
            "returned", "truncated"}
        and wcap["total"] == 6 and wcap["returned"] == 2
        and wcap["room_message_board"] == d_room[-2:]
        and set(wcap.keys())
        == {"room_message_board", "disclaimer", "limit", "total",
            "returned", "truncated"}
        and json.loads(snap["wfull_room"])["room_message_board"]
        == d_room)
    record("AC-S32", ok32,
           "6 zones ascending=%s; cap total=6 returned=2 tail-2=%s; "
           "windowed-cap 6 keys (no window echo)=%s"
           % ([r["room"] for r in d_room] == sorted(zones),
              c_room["room_message_board"] == d_room[-2:],
              set(wcap.keys())
              == {"room_message_board", "disclaimer", "limit", "total",
                  "returned", "truncated"}))

    # ---- AC-S33: cross-restart byte identity ----
    st.close()
    st2 = EventStore(db, disclaimer=notice)
    faces2 = faces(st2)
    ok33 = faces2 == snap
    record("AC-S33", ok33,
           "close -> reopen same db: six read faces byte-identical=%s"
           % ok33)

    # ---- AC-S34: post-restart new data = default drifts, window frozen ----
    st2.append("2026-11-05T01:00:01.000000Z", "chat.broadcast",
               "res-eta", "eta", "nov chat eta", {"text": "x"})
    st2.append("2026-11-05T01:00:02.000000Z", "chat.broadcast",
               "res-d2", "delta", "nov chat delta", {"text": "x"})
    st2.append("2026-11-05T02:00:02.000000Z", "idea.submit",
               "res-d2", "delta", "nov idea delta", {"text": "y"})
    now_room = st2.room_message_board()
    now_idea = st2.idea_pool_board()
    rooms_now = [r["room"] for r in now_room["room_message_board"]]
    delta_idea = [r for r in now_idea["idea_pool_board"]
                  if r["room"] == "delta"][0]
    oct_frozen = (
        json.dumps(st2.room_message_board(window="2026-10"),
                  sort_keys=True) == snap["wfull_room"]
        and json.dumps(st2.room_message_board(window="2026-10",
                                              limit=2),
                       sort_keys=True) == snap["wcap_room"])
    nov_carries = any(
        r["room"] == "eta"
        for r in st2.room_message_board(window="2026-11")
        ["room_message_board"])
    ok34 = (rooms_now == sorted(zones + ["eta"])
            and delta_idea["ideas"] == 2 and oct_frozen and nov_carries)
    record("AC-S34", ok34,
           "default recomputed (eta 7th zone=%s, delta ideas=2)=%s; "
           "oct window reads frozen byte-identical=%s; nov window "
           "carries new rows=%s"
           % ("eta" in rooms_now, delta_idea["ideas"] == 2,
              oct_frozen, nov_carries))

    # ---- AC-S35: window total semantics + honest empty (restarted inst) ----
    oct_cap = st2.room_message_board(window="2026-10", limit=2)
    nov_cap = st2.room_message_board(window="2026-11", limit=1)
    empty = st2.room_message_board(window="2026-12", limit=2)
    empty_idea = st2.idea_pool_board(window="2026-12", limit=3)
    ok35 = (oct_cap["total"] == 6
            and nov_cap["total"] == 2 and nov_cap["returned"] == 1
            and nov_cap["truncated"] is True
            and empty["room_message_board"] == []
            and empty["total"] == 0 and empty["returned"] == 0
            and empty["truncated"] is False
            and empty_idea["idea_pool_board"] == []
            and empty_idea["total"] == 0)
    record("AC-S35", ok35,
           "oct cap total stays 6 (zero nov penetration)=%s; nov cap "
           "total=2 own-window=%s; empty month 2026-12 honest empty "
           "4-key block=%s"
           % (oct_cap["total"] == 6, nov_cap["total"] == 2,
              empty["room_message_board"] == []
              and empty["truncated"] is False))

    # ---- AC-S36: pure-read law across restarts ----
    before = [db_query(db, "SELECT COUNT(*) FROM " + t)[0][0]
              for t in ("events", "census_cache")]
    faces(st2)
    st2.room_message_board(window="2026-11", limit=1)
    st2.idea_pool_board(window="2026-12", limit=3)
    after = [db_query(db, "SELECT COUNT(*) FROM " + t)[0][0]
             for t in ("events", "census_cache")]
    ok36 = before == after and before[0] == 15
    record("AC-S36", ok36,
           "events/census_cache counts flat across the read batch "
           "(%d==%d)=%s" % (before[0], after[0], ok36))

    # ---- AC-S37: dual-restart stability ----
    late = faces(st2)
    st2.close()
    st3 = EventStore(db, disclaimer=notice)
    faces3 = faces(st3)
    st3.close()
    ok37 = (faces3 == late
            and late["wfull_room"] == snap["wfull_room"]
            and late["wcap_room"] == snap["wcap_room"])
    record("AC-S37", ok37,
           "third instance == second-instance state=%s; oct window "
           "reads still == original pre-close snapshots=%s"
           % (faces3 == late, late["wfull_room"] == snap["wfull_room"]
              and late["wcap_room"] == snap["wcap_room"]))

    # ---- AC-S38: hygiene ----
    cfg_sha_out = hashlib.sha256(
        open(CONFIG, "rb").read()).hexdigest()
    store_sha_out = hashlib.sha256(
        open(os.path.join(BASE, "store.py"), "rb").read()).hexdigest()
    own_src = inspect.getsource(board_persist_cases)
    ascii_ok = True
    try:
        own_src.encode("ascii")
    except UnicodeEncodeError:
        ascii_ok = False
    import_lines = [ln.strip() for ln in own_src.splitlines()
                    if ln.strip().startswith("import ")]
    net_hits = [ln for ln in import_lines
                for lib in ("urllib", "requests", "socket", "http")
                if lib in ln]
    world_outside = not os.path.abspath(db).startswith(
        os.path.abspath(BASE) + os.sep)
    ok38 = (ascii_ok and not net_hits
            and cfg_sha_in == cfg_sha_out
            and store_sha_in == store_sha_out and world_outside)
    record("AC-S38", ok38,
           "ascii=%s net_imports=%s cfg_unchanged=%s "
           "store_unchanged=%s world_outside_repo=%s"
           % (ascii_ok, net_hits, cfg_sha_in == cfg_sha_out,
              store_sha_in == store_sha_out, world_outside))


def idem_cfg_copy(ttl=None, cap=None):
    """Derived test config for the idem_seen semantics window (AC-S41/
    AC-S42): a copy of the shipped lobby config with only the
    idempotency block overridden - the shipped config.json file is
    never modified."""
    cfg = json.loads(open(CONFIG, encoding="utf-8").read())
    idem = cfg.setdefault("idempotency", {})
    if ttl is not None:
        idem["ttl_seconds"] = ttl
    if cap is not None:
        idem["max_keys"] = cap
    path = os.path.join(tempfile.mkdtemp(prefix="lobby-idem-cfg-"), "config.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path


async def idem_restart_cases():
    """AC-S39..S43 (R1892): chat.send idem_seen restart semantics - the
    in-memory TTL+FIFO replay cache lives and dies with the server
    process (the honest boundary already documented on the pay
    authorize face). This window pins each semantic: in-TTL replay
    absorption re-acks the original evt_id, a cross-restart replay
    re-enters the event flow, TTL expiry admits a legitimate resend,
    FIFO cap eviction is honest. Suite-only round: server.py and the
    shipped config are not modified."""
    sha_server_pre = hashlib.sha256(open(SERVER, "rb").read()).hexdigest()
    sha_config_pre = hashlib.sha256(open(CONFIG, "rb").read()).hexdigest()

    async def chat_send(ws, room, text, cid):
        await ws.send(frame("chat.send", room=room,
                            payload={"text": text}, client_msg_id=cid))

    def chat_rows(db):
        return db_query(db,
                        "SELECT COUNT(*) FROM events WHERE type='chat.broadcast'")[0][0]

    # ---- AC-S39 + AC-S40: shipped-config world, then same-db restart ----
    port_a = _free_port()
    srv_a = ServerProc(port_a, db=os.path.join(
        tempfile.mkdtemp(prefix="lobby-idem-a-"), "events.db"))
    sender = observer = sender2 = None
    srv_b = None
    try:
        srv_a.start()
        sender, _, _ = await open_client(port_a)
        await make_resident(sender)
        observer, _, _ = await open_client(port_a)  # spectator: default lobby room
        await chat_send(sender, "lobby", "s39 alpha", "idem-39-a")
        b1 = await recv_until(sender, lambda f: f.get("type") == "chat.broadcast"
                              and f.get("payload", {}).get("text") == "s39 alpha")
        obs_b1 = await recv_until(observer,
                                  lambda f: f.get("type") == "chat.broadcast"
                                  and f.get("payload", {}).get("text") == "s39 alpha")
        rows_pre = chat_rows(srv_a.db)
        await chat_send(sender, "lobby", "s39 alpha", "idem-39-a")  # in-TTL replay
        dup = await recv_until(sender,
                               lambda f: f.get("type") == "chat.duplicate"
                               and f.get("payload", {}).get("client_msg_id") == "idem-39-a")
        silent_obs = await expect_silence(observer, 0.5)
        ok39 = (obs_b1 is not None
                and dup.get("payload", {}).get("code") == "E_DUPLICATE_MSG"
                and "already processed" in dup.get("payload", {}).get("reason", "")
                and dup.get("payload", {}).get("evt_id") == b1.get("evt_id")
                and chat_rows(srv_a.db) == rows_pre and silent_obs)
        record("AC-S39", ok39,
               "replay absorbed: dup-frame-evt_id==orig=%s code-ok=%s "
               "reason-processed=%s rows-unchanged=%s observer-silent=%s"
               % (dup.get("payload", {}).get("evt_id") == b1.get("evt_id"),
                  dup.get("payload", {}).get("code") == "E_DUPLICATE_MSG",
                  "already processed" in dup.get("payload", {}).get("reason", ""),
                  chat_rows(srv_a.db) == rows_pre, silent_obs))
        # cross-restart replay: the in-memory cache dies with the process
        try:
            await sender.close()
        except Exception:
            pass
        try:
            await observer.close()
        except Exception:
            pass
        sender = observer = None
        srv_a.stop()
        srv_b = ServerProc(port_a, db=srv_a.db)  # same shipped config, same db
        srv_b.start()
        sender2, _, _ = await open_client(port_a)
        await make_resident(sender2)
        await chat_send(sender2, "lobby", "s39 alpha", "idem-39-a")
        b2 = await recv_until(sender2,
                              lambda f: f.get("type") == "chat.broadcast"
                              and f.get("payload", {}).get("text") == "s39 alpha")
        ok40 = (b2 is not None and b2.get("evt_id") != b1.get("evt_id")
                and chat_rows(srv_b.db) == rows_pre + 1)
        record("AC-S40", ok40,
               "post-restart replay re-entered the event flow: new-evt=%s "
               "rows %d -> %d (in-memory cache dies with the process - "
               "honest boundary)"
               % (b2.get("evt_id") != b1.get("evt_id"), rows_pre,
                  chat_rows(srv_b.db)))
    finally:
        for ws_ in (sender, observer, sender2):
            if ws_ is not None:
                try:
                    await ws_.close()
                except Exception:
                    pass
        srv_a.stop()
        if srv_b is not None:
            srv_b.stop()

    # ---- AC-S41: TTL expiry admits a legitimate resend ----
    cfg_ttl = idem_cfg_copy(ttl=1.5)
    port_t = _free_port()
    srv_t = ServerProc(port_t, config=cfg_ttl, db=os.path.join(
        tempfile.mkdtemp(prefix="lobby-idem-t-"), "events.db"))
    ws_t = None
    try:
        srv_t.start()
        ws_t, _, _ = await open_client(port_t)
        await make_resident(ws_t)
        await chat_send(ws_t, "lobby", "s41 alpha", "idem-41-a")
        bt1 = await recv_until(ws_t, lambda f: f.get("type") == "chat.broadcast"
                               and f.get("payload", {}).get("text") == "s41 alpha")
        await chat_send(ws_t, "lobby", "s41 alpha", "idem-41-a")  # in-TTL replay
        dup_t = await recv_until(ws_t,
                                 lambda f: f.get("type") == "chat.duplicate"
                                 and f.get("payload", {}).get("client_msg_id") == "idem-41-a")
        absorbed = (dup_t.get("payload", {}).get("evt_id") == bt1.get("evt_id"))
        rows_t1 = chat_rows(srv_t.db)
        await asyncio.sleep(2.0)  # > ttl 1.5s: the cache entry expires
        await chat_send(ws_t, "lobby", "s41 alpha", "idem-41-a")  # resend
        bt2 = await recv_until(ws_t,
                               lambda f: f.get("type") == "chat.broadcast"
                               and f.get("payload", {}).get("text") == "s41 alpha"
                               and f.get("evt_id") != bt1.get("evt_id"))
        ok41 = (absorbed and bt2 is not None
                and chat_rows(srv_t.db) == rows_t1 + 1)
        record("AC-S41", ok41,
               "in-TTL replay absorbed=%s; after ttl expiry the resend "
               "re-enters as a fresh event=%s rows %d -> %d"
               % (absorbed, bt2 is not None, rows_t1, chat_rows(srv_t.db)))
    finally:
        if ws_t is not None:
            try:
                await ws_t.close()
            except Exception:
                pass
        srv_t.stop()

    # ---- AC-S42: FIFO cap eviction honesty ----
    cfg_cap = idem_cfg_copy(cap=2)  # ttl stays at the shipped 300
    port_c = _free_port()
    srv_c = ServerProc(port_c, config=cfg_cap, db=os.path.join(
        tempfile.mkdtemp(prefix="lobby-idem-c-"), "events.db"))
    ws_c = None
    try:
        srv_c.start()
        ws_c, _, _ = await open_client(port_c)
        await make_resident(ws_c)
        texts = ("s42 one", "s42 two", "s42 three")
        cids = ("idem-42-a", "idem-42-b", "idem-42-c")
        orig = []
        for text, cid in zip(texts, cids):
            await chat_send(ws_c, "lobby", text, cid)
            b = await recv_until(ws_c,
                                 lambda f: f.get("type") == "chat.broadcast"
                                 and f.get("payload", {}).get("text") == text)
            orig.append(b.get("evt_id"))
        rows_c3 = chat_rows(srv_c.db)  # 3 rows; cap=2 FIFO evicted cids[0]
        await chat_send(ws_c, "lobby", texts[0], cids[0])  # evicted-key replay
        br1 = await recv_until(ws_c,
                               lambda f: f.get("type") == "chat.broadcast"
                               and f.get("payload", {}).get("text") == texts[0]
                               and f.get("evt_id") != orig[0])
        reentered = br1 is not None and br1.get("evt_id") != orig[0]
        # The re-entered key is re-remembered at the FIFO tail, which
        # evicts the next-oldest survivor (cids[1]) - insertion-order
        # honesty: replay the freshest key (absorbed, re-entry evt_id),
        # the survivor cids[2] (absorbed), then cids[1] (evicted by the
        # re-remember -> re-enters the event flow).
        await chat_send(ws_c, "lobby", texts[0], cids[0])  # freshest replay
        dup1b = await recv_until(ws_c,
                                 lambda f: f.get("type") == "chat.duplicate"
                                 and f.get("payload", {}).get("client_msg_id") == cids[0])
        await chat_send(ws_c, "lobby", texts[2], cids[2])  # survivor replay
        dup3 = await recv_until(ws_c,
                                lambda f: f.get("type") == "chat.duplicate"
                                and f.get("payload", {}).get("client_msg_id") == cids[2])
        await chat_send(ws_c, "lobby", texts[1], cids[1])  # evicted survivor
        br2 = await recv_until(ws_c,
                               lambda f: f.get("type") == "chat.broadcast"
                               and f.get("payload", {}).get("text") == texts[1]
                               and f.get("evt_id") != orig[1])
        reentered2 = br2 is not None and br2.get("evt_id") != orig[1]
        absorbed_fresh = (dup1b.get("payload", {}).get("evt_id") == br1.get("evt_id"))
        absorbed_surv = (dup3.get("payload", {}).get("evt_id") == orig[2])
        ok42 = (reentered and absorbed_fresh and absorbed_surv and reentered2
                and chat_rows(srv_c.db) == rows_c3 + 2)
        record("AC-S42", ok42,
               "cap=2: evicted-key replay re-entered=%s; re-remembered key "
               "absorbed=%s survivor c3 absorbed=%s; next-oldest survivor "
               "c2 evicted by the re-remember -> re-entered=%s; rows 3 + 1 "
               "+ 0 + 0 + 1 = %d"
               % (reentered, absorbed_fresh, absorbed_surv, reentered2,
                  chat_rows(srv_c.db)))
    finally:
        if ws_c is not None:
            try:
                await ws_c.close()
            except Exception:
                pass
        srv_c.stop()

    # ---- AC-S43: hygiene (suite-only round) ----
    sha_server_post = hashlib.sha256(open(SERVER, "rb").read()).hexdigest()
    sha_config_post = hashlib.sha256(open(CONFIG, "rb").read()).hexdigest()
    own_src = inspect.getsource(idem_restart_cases)
    ascii_ok = True
    try:
        own_src.encode("ascii")
    except UnicodeEncodeError:
        ascii_ok = False
    ok43 = (sha_server_post == sha_server_pre
            and sha_config_post == sha_config_pre and ascii_ok)
    record("AC-S43", ok43,
           "server.py-unchanged=%s config.json-unchanged=%s section-ascii=%s"
           % (sha_server_post == sha_server_pre,
              sha_config_post == sha_config_pre, ascii_ok))


async def idem_boundary_cases():
    """AC-IDT1..IDT8 (R2012): chat.send idem_seen TTL/FIFO boundary
    window - four boundary laws the R1892 restart-semantics and R1899
    key-binding windows left unpinned: (1) the TTL window is FIXED at
    first processing - an absorbed replay never slides or extends it;
    (2) a post-expiry resend re-arms the cache with the NEW evt_id, so
    an immediate replay re-acks the fresh entry, never the original;
    (3) windows are per-key and stagger independently (a key
    remembered later is still in-window when an earlier key already
    expired); (4) len==cap is the no-eviction boundary (both live
    keys absorb at exactly cap) while the cap+1-th distinct key
    evicts the oldest in FIFO order (an evicted-while-still-live key
    re-enters the event flow). Honest boundary note: the
    exact-instant expiry predicate (expires_at <= now, inclusive)
    cannot be pinned deterministically against the live monotonic
    clock inside the server subprocess (R1678 frozen-clock
    rationale), so this window pins order boundaries with wide
    margins on both sides instead. Suite-only round: server.py and
    the shipped config are not modified (R1892/R1899 precedent)."""
    sha_server_pre = hashlib.sha256(open(SERVER, "rb").read()).hexdigest()
    sha_config_pre = hashlib.sha256(open(CONFIG, "rb").read()).hexdigest()

    async def chat_send(ws, room, text, cid):
        await ws.send(frame("chat.send", room=room,
                            payload={"text": text}, client_msg_id=cid))

    def chat_rows(db):
        return db_query(db,
                        "SELECT COUNT(*) FROM events WHERE type='chat.broadcast'")[0][0]

    async def dup_of(ws, evt_id, cid):
        return await recv_until(ws, lambda f: f.get("type") == "chat.duplicate"
                                and f.get("payload", {}).get("client_msg_id") == cid
                                and f.get("payload", {}).get("evt_id") == evt_id)

    # ---- world 1: fixed-window non-refresh + re-arm + staggered keys
    # (ttl 1.5s via derived config copy; cap stays at the shipped value) ----
    cfg_w1 = idem_cfg_copy(ttl=1.5)
    port_1 = _free_port()
    srv_1 = ServerProc(port_1, config=cfg_w1, db=os.path.join(
        tempfile.mkdtemp(prefix="lobby-idem-b1-"), "events.db"))
    ws_1 = None
    try:
        srv_1.start()
        ws_1, _, _ = await open_client(port_1)
        await make_resident(ws_1)
        await chat_send(ws_1, "lobby", "idt one", "idt-1-a")
        e_one = await recv_until(ws_1, lambda f: f.get("type") == "chat.broadcast"
                                 and f.get("payload", {}).get("text") == "idt one")
        rows_a = chat_rows(srv_1.db)
        await asyncio.sleep(0.7)   # t+0.7: inside the fixed 1.5s window
        await chat_send(ws_1, "lobby", "idt one", "idt-1-a")
        d_one = await dup_of(ws_1, e_one.get("evt_id"), "idt-1-a")
        ok_idt1 = (d_one is not None
                   and d_one.get("payload", {}).get("code") == "E_DUPLICATE_MSG"
                   and chat_rows(srv_1.db) == rows_a)
        record("AC-IDT1", ok_idt1,
               "in-window replay at t+0.7 absorbed: dup-evt==orig=%s code-ok=%s "
               "rows-unchanged=%s"
               % (d_one is not None,
                  d_one.get("payload", {}).get("code") == "E_DUPLICATE_MSG",
                  chat_rows(srv_1.db) == rows_a))
        await asyncio.sleep(0.2)   # t+0.9: stagger key two's window start
        await chat_send(ws_1, "lobby", "idt two", "idt-1-b")
        e_two = await recv_until(ws_1, lambda f: f.get("type") == "chat.broadcast"
                                 and f.get("payload", {}).get("text") == "idt two")
        rows_b = chat_rows(srv_1.db)
        await asyncio.sleep(0.9)   # t+1.8: key one past its 1.5s expiry
        await chat_send(ws_1, "lobby", "idt one", "idt-1-a")
        e_one2 = await recv_until(ws_1,
                                  lambda f: f.get("type") == "chat.broadcast"
                                  and f.get("payload", {}).get("text") == "idt one"
                                  and f.get("evt_id") != e_one.get("evt_id"))
        ok_idt2 = e_one2 is not None and chat_rows(srv_1.db) == rows_b + 1
        record("AC-IDT2", ok_idt2,
               "fixed-window non-refresh: resend at t+1.8 re-entered=%s rows %d "
               "-> %d (the t+0.7 absorption did not slide the 1.5s window)"
               % (e_one2 is not None, rows_b, chat_rows(srv_1.db)))
        await chat_send(ws_1, "lobby", "idt one", "idt-1-a")   # immediate replay
        d_rearm = await dup_of(ws_1, e_one2.get("evt_id"), "idt-1-a")
        rows_c = chat_rows(srv_1.db)
        ok_idt3 = (d_rearm is not None
                   and d_rearm.get("payload", {}).get("evt_id") != e_one.get("evt_id")
                   and rows_c == rows_b + 1)
        record("AC-IDT3", ok_idt3,
               "post-expiry re-arm: immediate replay re-acked the NEW evt=%s "
               "(orig never re-acked) rows-stable=%s"
               % (d_rearm is not None
                  and d_rearm.get("payload", {}).get("evt_id") != e_one.get("evt_id"),
                  rows_c == rows_b + 1))
        await chat_send(ws_1, "lobby", "idt two", "idt-1-b")   # key two still live
        d_two = await dup_of(ws_1, e_two.get("evt_id"), "idt-1-b")
        ok_idt4 = d_two is not None and chat_rows(srv_1.db) == rows_c
        record("AC-IDT4", ok_idt4,
               "per-key staggered windows: key two (remembered t+0.9) still "
               "absorbed at t+1.8 while key one had already expired=%s "
               "rows-stable=%s"
               % (d_two is not None, chat_rows(srv_1.db) == rows_c))
        rows_final = chat_rows(srv_1.db)
        ok_idt5 = rows_final == rows_a + 2
        record("AC-IDT5", ok_idt5,
               "world-1 store accounting: rows %d -> %d (exactly the three "
               "fresh entries idt-one/idt-two/idt-one-reentry; every absorbed "
               "replay added none)"
               % (rows_a, rows_final))
    finally:
        if ws_1 is not None:
            try:
                await ws_1.close()
            except Exception:
                pass
        srv_1.stop()

    # ---- world 2: len==cap no-eviction boundary + over-cap FIFO order
    # (cap=2 via derived config copy; ttl stays at the shipped 300s, so
    # the probes exercise eviction, not expiry) ----
    cfg_w2 = idem_cfg_copy(cap=2)
    port_2 = _free_port()
    srv_2 = ServerProc(port_2, config=cfg_w2, db=os.path.join(
        tempfile.mkdtemp(prefix="lobby-idem-b2-"), "events.db"))
    ws_2 = None
    try:
        srv_2.start()
        ws_2, _, _ = await open_client(port_2)
        await make_resident(ws_2)
        await chat_send(ws_2, "lobby", "idt k1", "idt-2-a")
        e_k1 = await recv_until(ws_2, lambda f: f.get("type") == "chat.broadcast"
                                and f.get("payload", {}).get("text") == "idt k1")
        await chat_send(ws_2, "lobby", "idt k2", "idt-2-b")
        e_k2 = await recv_until(ws_2, lambda f: f.get("type") == "chat.broadcast"
                                and f.get("payload", {}).get("text") == "idt k2")
        rows_cap = chat_rows(srv_2.db)   # len == cap == 2: no eviction yet
        await chat_send(ws_2, "lobby", "idt k1", "idt-2-a")
        d_k1 = await dup_of(ws_2, e_k1.get("evt_id"), "idt-2-a")
        await chat_send(ws_2, "lobby", "idt k2", "idt-2-b")
        d_k2 = await dup_of(ws_2, e_k2.get("evt_id"), "idt-2-b")
        ok_idt6 = (d_k1 is not None and d_k2 is not None
                   and chat_rows(srv_2.db) == rows_cap)
        record("AC-IDT6", ok_idt6,
               "len==cap no-eviction boundary: k1-absorbed=%s k2-absorbed=%s "
               "rows-stable=%s (cap=2 reached, no premature eviction)"
               % (d_k1 is not None, d_k2 is not None,
                  chat_rows(srv_2.db) == rows_cap))
        await chat_send(ws_2, "lobby", "idt k3", "idt-2-c")   # pushes over cap
        e_k3 = await recv_until(ws_2, lambda f: f.get("type") == "chat.broadcast"
                                and f.get("payload", {}).get("text") == "idt k3")
        rows_three = chat_rows(srv_2.db)   # k1 evicted (FIFO oldest)
        await chat_send(ws_2, "lobby", "idt k2", "idt-2-b")   # survivor absorbs
        d_k2b = await dup_of(ws_2, e_k2.get("evt_id"), "idt-2-b")
        await chat_send(ws_2, "lobby", "idt k1", "idt-2-a")   # evicted -> re-entry
        e_k1b = await recv_until(ws_2,
                                 lambda f: f.get("type") == "chat.broadcast"
                                 and f.get("payload", {}).get("text") == "idt k1"
                                 and f.get("evt_id") != e_k1.get("evt_id"))
        rows_four = chat_rows(srv_2.db)
        ok_idt7 = (d_k2b is not None and e_k1b is not None
                   and rows_three == rows_cap + 1 and rows_four == rows_cap + 2)
        record("AC-IDT7", ok_idt7,
               "over-cap FIFO eviction order: survivor-k2-absorbed=%s "
               "evicted-k1-reentered=%s rows %d -> %d -> %d (evicted while "
               "still TTL-live, honest re-entry)"
               % (d_k2b is not None, e_k1b is not None,
                  rows_cap, rows_three, rows_four))
    finally:
        if ws_2 is not None:
            try:
                await ws_2.close()
            except Exception:
                pass
        srv_2.stop()

    # ---- AC-IDT8: hygiene (suite-only round) ----
    sha_server_post = hashlib.sha256(open(SERVER, "rb").read()).hexdigest()
    sha_config_post = hashlib.sha256(open(CONFIG, "rb").read()).hexdigest()
    own_src = inspect.getsource(idem_boundary_cases)
    ascii_ok = True
    try:
        own_src.encode("ascii")
    except UnicodeEncodeError:
        ascii_ok = False
    record("AC-IDT8", sha_server_post == sha_server_pre
           and sha_config_post == sha_config_pre and ascii_ok,
           "server.py-unchanged=%s config.json-unchanged=%s section-ascii=%s "
           "(exact-instant expiry predicate is unpinnable against the live "
           "monotonic clock in the subprocess server; order boundaries pinned)"
               % (sha_server_post == sha_server_pre,
                  sha_config_post == sha_config_pre, ascii_ok))


async def idem_budget_gateorder_cases():
    """AC-IDB1..IDB7 (criteria pre-registered R2013 in the
    state/queue/explore.md claim row, implemented here R2014):
    chat.send gate-order budget window. The idempotency gate sits
    BEFORE the rate limit (server.py: "before the rate limit
    (replay costs no budget)"), so a replay of an already-processed
    send is absorbed as a duplicate without burning, freeing or
    extending any rate-limit budget while the 5/10s window stays
    saturated by the fresh sends. All probes run against the
    SHIPPED config values (5 msgs / 10s window, 3-violation 60s
    mute, idem ttl 300s, cap 4096): the probe batch uses 7
    distinct idem keys (far below the 4096 cap) and completes well
    inside both the 10s window and the 300s ttl, so no derived
    config copy is needed - this window certifies existing
    behavior, it legislates nothing new (R2013 claim-row note).
    Honest evidence note: client.send_times and the violations
    counter live inside the server subprocess and cannot be read
    directly; the budget claims are pinned by their behavioral
    equivalents - (a) ten consecutive replays all answer
    chat.duplicate while a budget-burning replay path would have
    tripped the 3-violation mute and the 4th+ replay would answer
    E_RATE_LIMIT muted; (b) the 6th fresh send after the replay
    storm is still rejected, so the window was neither freed nor
    extended. Suite-only round: server.py and the shipped config
    are not modified (R1892/R1999/R2012 precedent)."""
    sha_server_pre = hashlib.sha256(open(SERVER, "rb").read()).hexdigest()
    sha_config_pre = hashlib.sha256(open(CONFIG, "rb").read()).hexdigest()

    async def chat_send(ws, room, text, cid=None):
        payload = {"text": text}
        if cid is not None:
            await ws.send(frame("chat.send", room=room,
                                payload=payload, client_msg_id=cid))
        else:
            await ws.send(frame("chat.send", room=room,
                                payload=payload))

    def chat_rows(db):
        return db_query(db,
                        "SELECT COUNT(*) FROM events"
                        " WHERE type='chat.broadcast'")[0][0]

    def is_rate_reject(f):
        # both rejection shapes count: pre-mute violations answer
        # err.rate_limit (send_rate_limit) while the mute-triggered
        # and muted-window rejections answer sec.reject (AC-S9 face)
        return (f.get("payload", {}).get("code") == "E_RATE_LIMIT"
                and f.get("type") in ("err.rate_limit",
                                      "sec.reject"))

    port = _free_port()
    srv = ServerProc(port, db=os.path.join(
        tempfile.mkdtemp(prefix="lobby-idem-bg-"), "events.db"))
    ws_a = None
    ws_b = None
    try:
        srv.start()
        ws_a, _, _ = await open_client(port)
        ws_b, _, _ = await open_client(port)   # bystander, read-only
        await make_resident(ws_a)

        # saturate the 5/10s window: five fresh sends, each a unique
        # (client_msg_id, text) pair; both clients see all five
        # broadcasts (the bystander's receipts are drained here so
        # the later zero-second-broadcast probe starts clean).
        orig_evts = {}
        for i in range(5):
            cid = "idb-w%d" % i
            text = "idb fresh %d" % i
            await chat_send(ws_a, "lobby", text, cid)
            e = await recv_until(ws_a, lambda f: (
                f.get("type") == "chat.broadcast"
                and f.get("payload", {}).get("text") == text))
            await recv_until(ws_b, lambda f: (
                f.get("type") == "chat.broadcast"
                and f.get("evt_id") == e.get("evt_id")))
            orig_evts[cid] = (text, e.get("evt_id"))
        rows_sat = chat_rows(srv.db)

        # ---- AC-IDB1: saturated-window replay absorption ----
        replay_cid = "idb-w2"
        replay_text, replay_evt = orig_evts[replay_cid]
        await chat_send(ws_a, "lobby", replay_text, replay_cid)
        d1 = await recv_until(ws_a, lambda f: (
            f.get("type") == "chat.duplicate"
            and f.get("payload", {}).get("client_msg_id")
            == replay_cid))
        ok_idb1 = (d1 is not None
                   and d1.get("payload", {}).get("code")
                   == "E_DUPLICATE_MSG"
                   and d1.get("payload", {}).get("evt_id")
                   == replay_evt
                   and rows_sat == 5)
        record("AC-IDB1", ok_idb1,
               "5/10s window saturated by five fresh sends (%d rows) "
               "then a replayed (id,text) answered chat.duplicate "
               "code=%s evt==original=%s and zero E_RATE_LIMIT (a "
               "rate-path replay would have failed the duplicate wait)"
               % (rows_sat,
                  d1.get("payload", {}).get("code"),
                  d1.get("payload", {}).get("evt_id") == replay_evt))

        # ---- AC-IDB2: replay storm costs no budget (behavioral
        # equivalent of the in-process send_times/violations probe)
        # ----
        storm_ok = True
        for _ in range(9):   # plus the AC-IDB1 replay = 10 total
            await chat_send(ws_a, "lobby", replay_text, replay_cid)
            d = await recv_until(ws_a, lambda f: (
                f.get("type") == "chat.duplicate"
                and f.get("payload", {}).get("client_msg_id")
                == replay_cid))
            if (d.get("payload", {}).get("code") != "E_DUPLICATE_MSG"
                    or d.get("payload", {}).get("evt_id")
                    != replay_evt):
                storm_ok = False
        rows_storm = chat_rows(srv.db)
        ok_idb2 = storm_ok and rows_storm == rows_sat
        record("AC-IDB2", ok_idb2,
               "10 consecutive replays of one (id,text) all duplicate, "
               "store rows unchanged %d -> %d (behavioral zero-budget "
               "proof: a budget-burning replay would have tripped the "
               "3-violation mute and the 4th+ replay would answer "
               "E_RATE_LIMIT muted; send_times/violations live in the "
               "subprocess and are pinned by this behavioral equivalent)"
               % (rows_sat, rows_storm))

        # ---- AC-IDB5: store/broadcast zero side effects ----
        ws_b_silent = await expect_silence(ws_b, 0.5)
        ok_idb5 = rows_storm == rows_sat and ws_b_silent
        record("AC-IDB5", ok_idb5,
               "dup-absorb storm side effects: store rows %d == %d "
               "saturated count, bystander-second-broadcast=%s "
               "(duplicates never re-broadcast, never re-land)"
               % (rows_storm, rows_sat, not ws_b_silent))

        # ---- AC-IDB3: replays free no budget (6th fresh still
        # rejected; the window stays saturated by the original five)
        # ----
        await chat_send(ws_a, "lobby", "idb fresh 5", "idb-w5")
        f6 = await recv_until(ws_a, is_rate_reject)
        ok_idb3 = f6 is not None
        record("AC-IDB3", ok_idb3,
               "6th fresh send (new id + new text) still rejected "
               "E_RATE_LIMIT after the 10-replay storm: the window was "
               "neither freed nor extended by the replays (violation "
               "#1, below the 3-violation mute)")

        # ---- AC-IDB4: no-idem-path control anchor (gate order
        # triangulated: the dup path returns before the rate check;
        # both the miss-id fresh path and the no-id path hit the
        # rate gate) ----
        await chat_send(ws_a, "lobby", "idb fresh 6")   # no client_msg_id
        f7 = await recv_until(ws_a, is_rate_reject)
        ok_idb4 = f7 is not None
        record("AC-IDB4", ok_idb4,
               "no-client_msg_id send at the same saturated position "
               "also rejected E_RATE_LIMIT (control anchor; violation "
               "#2 - the duplicate path returns ahead of the rate "
               "check while every non-duplicate path hits it)")

        # ---- AC-IDB6: hygiene (suite-only round) ----
        sha_server_post = hashlib.sha256(
            open(SERVER, "rb").read()).hexdigest()
        sha_config_post = hashlib.sha256(
            open(CONFIG, "rb").read()).hexdigest()
        own_src = inspect.getsource(idem_budget_gateorder_cases)
        ascii_ok = True
        try:
            own_src.encode("ascii")
        except UnicodeEncodeError:
            ascii_ok = False
        net_ok = not any(
            ln.strip().startswith(("import requests", "import urllib",
                                   "import http", "from requests",
                                   "from urllib", "from http",
                                   "import socket", "import aiohttp",
                                   "import httpx"))
            for ln in own_src.splitlines())
        record("AC-IDB6", sha_server_post == sha_server_pre
               and sha_config_post == sha_config_pre and ascii_ok
               and net_ok,
               "server.py-unchanged=%s config.json-unchanged=%s "
               "section-ascii=%s true-import-lines-zero-network=%s "
               "(shipped values throughout, no derived config copy "
               "this window; the double-run byte-identity face is "
               "carried by the evidence log qa/idem-budget-R2014.log)"
               % (sha_server_post == sha_server_pre,
                  sha_config_post == sha_config_pre, ascii_ok, net_ok))

        # ---- AC-IDB7: delivery registration ----
        idb_so_far = len([1 for ac, _ in RESULTS
                          if ac.startswith("AC-IDB")])
        reg_line = ('("lobby", os.path.join("lobby",'
                    ' "test_client.py"), 72)')
        reg_src = open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "reconcile_all.py"), encoding="utf-8").read()
        reg_ok = reg_line in reg_src
        record("AC-IDB7", reg_ok and idb_so_far == 6,
               "delivery: reconcile_all SUITES lobby row 57->65->72 "
               "registered=%s; AC-IDB criteria counted %d before this "
               "record (7 with it); the full-battery RUNNER pass and "
               "the suite-matrix --check byte-identical face are "
               "carried by the evidence log qa/idem-budget-R2014.log"
               % (reg_ok, idb_so_far))
    finally:
        for ws in (ws_a, ws_b):
            if ws is not None:
                try:
                    await ws.close()
                except Exception:
                    pass
        srv.stop()


async def idem_keybind_cases():
    """AC-S44..S48 (R1899): chat.send idem key binding semantics - the
    dedup key binds the client-supplied id to the exact normalized
    text, so a foreign client guessing the id cannot suppress the
    original (same id + different text = a fresh event with both keys
    coexisting), the cache is server-instance scoped (a replay from a
    different connection absorbs), the id and text domains are
    independent, and the strip/truncate normalization happens before
    the key digest. Suite-only round: server.py and the shipped
    config are not modified (R1892 precedent)."""
    sha_server_pre = hashlib.sha256(open(SERVER, "rb").read()).hexdigest()
    sha_config_pre = hashlib.sha256(open(CONFIG, "rb").read()).hexdigest()

    async def chat_send(ws, room, text, cid):
        await ws.send(frame("chat.send", room=room,
                            payload={"text": text}, client_msg_id=cid))

    def chat_rows(db):
        return db_query(db,
                        "SELECT COUNT(*) FROM events WHERE type='chat.broadcast'")[0][0]

    async def dup_of(ws, evt_id):
        return await recv_until(ws, lambda f: f.get("type") == "chat.duplicate"
                                and f.get("payload", {}).get("evt_id") == evt_id)

    # ---- AC-S44: same id + different text = fresh event, keys coexist
    port_44 = _free_port()
    srv_44 = ServerProc(port_44, db=os.path.join(
        tempfile.mkdtemp(prefix="lobby-keybind-44-"), "events.db"))
    ws_44 = None
    try:
        srv_44.start()
        ws_44, _, _ = await open_client(port_44)
        await make_resident(ws_44)
        await chat_send(ws_44, "lobby", "s44 alpha", "kb-44-a")
        e1 = await recv_until(ws_44, lambda f: f.get("type") == "chat.broadcast"
                              and f.get("payload", {}).get("text") == "s44 alpha")
        await chat_send(ws_44, "lobby", "s44 beta", "kb-44-a")  # same id, new text
        e2 = await recv_until(ws_44, lambda f: f.get("type") == "chat.broadcast"
                              and f.get("payload", {}).get("text") == "s44 beta")
        fresh44 = e2 is not None and e2.get("evt_id") != e1.get("evt_id")
        rows44 = chat_rows(srv_44.db)
        await chat_send(ws_44, "lobby", "s44 alpha", "kb-44-a")
        d1 = await dup_of(ws_44, e1.get("evt_id"))
        await chat_send(ws_44, "lobby", "s44 beta", "kb-44-a")
        d2 = await dup_of(ws_44, e2.get("evt_id"))
        coexist = (d1 is not None and d2 is not None
                  and d1.get("payload", {}).get("code") == "E_DUPLICATE_MSG"
                  and d2.get("payload", {}).get("code") == "E_DUPLICATE_MSG")
        ok44 = (fresh44 and coexist and rows44 == 2
                and chat_rows(srv_44.db) == rows44)
        record("AC-S44", ok44,
               "same-id different-text fresh-evt=%s; both keys coexist "
               "(alpha->E1, beta->E2)=%s; rows 2 stable=%s"
               % (fresh44, coexist, chat_rows(srv_44.db) == rows44))
    finally:
        if ws_44 is not None:
            try:
                await ws_44.close()
            except Exception:
                pass
        srv_44.stop()

    # ---- AC-S45: same (id, text) from another connection absorbs
    # (the cache is server-instance scoped, not per-connection)
    port_45 = _free_port()
    srv_45 = ServerProc(port_45, db=os.path.join(
        tempfile.mkdtemp(prefix="lobby-keybind-45-"), "events.db"))
    ws_a = ws_b = obs_45 = None
    try:
        srv_45.start()
        ws_a, _, _ = await open_client(port_45)
        await make_resident(ws_a)
        ws_b, _, _ = await open_client(port_45)
        await make_resident(ws_b)
        obs_45, _, _ = await open_client(port_45)  # spectator on lobby
        await chat_send(ws_a, "lobby", "s45 alpha", "kb-45-a")
        e3 = await recv_until(ws_a, lambda f: f.get("type") == "chat.broadcast"
                              and f.get("payload", {}).get("text") == "s45 alpha")
        await recv_until(obs_45, lambda f: f.get("type") == "chat.broadcast"
                         and f.get("payload", {}).get("text") == "s45 alpha")
        rows45 = chat_rows(srv_45.db)
        await chat_send(ws_b, "lobby", "s45 alpha", "kb-45-a")  # other conn
        d3 = await recv_until(ws_b, lambda f: f.get("type") == "chat.duplicate"
                              and f.get("payload", {}).get("client_msg_id") == "kb-45-a")
        silent45 = await expect_silence(obs_45, 0.5)
        ok45 = (d3 is not None
                and d3.get("payload", {}).get("code") == "E_DUPLICATE_MSG"
                and d3.get("payload", {}).get("evt_id") == e3.get("evt_id")
                and chat_rows(srv_45.db) == rows45 and silent45)
        record("AC-S45", ok45,
               "cross-connection replay absorbed=%s rows-unchanged=%s "
               "observer-silent=%s (cache is server-instance scoped)"
               % (d3 is not None
                  and d3.get("payload", {}).get("evt_id") == e3.get("evt_id"),
                  chat_rows(srv_45.db) == rows45, silent45))
    finally:
        for ws_ in (ws_a, ws_b, obs_45):
            if ws_ is not None:
                try:
                    await ws_.close()
                except Exception:
                    pass
        srv_45.stop()

    # ---- AC-S46: different id + same text = fresh event (id domain
    # independent; the text alone never dedups)
    port_46 = _free_port()
    srv_46 = ServerProc(port_46, db=os.path.join(
        tempfile.mkdtemp(prefix="lobby-keybind-46-"), "events.db"))
    ws_46 = None
    try:
        srv_46.start()
        ws_46, _, _ = await open_client(port_46)
        await make_resident(ws_46)
        await chat_send(ws_46, "lobby", "s46 shared", "kb-46-a")
        e4 = await recv_until(ws_46, lambda f: f.get("type") == "chat.broadcast"
                              and f.get("payload", {}).get("text") == "s46 shared")
        await chat_send(ws_46, "lobby", "s46 shared", "kb-46-b")  # other id
        e5 = await recv_until(ws_46, lambda f: f.get("type") == "chat.broadcast"
                              and f.get("payload", {}).get("text") == "s46 shared"
                              and f.get("evt_id") != e4.get("evt_id"))
        fresh46 = e5 is not None
        rows46 = chat_rows(srv_46.db)
        await chat_send(ws_46, "lobby", "s46 shared", "kb-46-a")
        d4 = await dup_of(ws_46, e4.get("evt_id"))
        await chat_send(ws_46, "lobby", "s46 shared", "kb-46-b")
        d5 = await dup_of(ws_46, e5.get("evt_id"))
        coexist46 = (d4 is not None and d5 is not None
                     and d4.get("payload", {}).get("code") == "E_DUPLICATE_MSG"
                     and d5.get("payload", {}).get("code") == "E_DUPLICATE_MSG")
        ok46 = (fresh46 and coexist46 and rows46 == 2
                and chat_rows(srv_46.db) == rows46)
        record("AC-S46", ok46,
               "different-id same-text fresh-evt=%s; per-id keys coexist "
               "(a->E4, b->E5)=%s; rows 2 stable=%s"
               % (fresh46, coexist46, chat_rows(srv_46.db) == rows46))
    finally:
        if ws_46 is not None:
            try:
                await ws_46.close()
            except Exception:
                pass
        srv_46.stop()

    # ---- AC-S47: normalization happens before the key digest
    # (strip / id-strip / truncation all feed the same normalized key)
    port_47 = _free_port()
    srv_47 = ServerProc(port_47, db=os.path.join(
        tempfile.mkdtemp(prefix="lobby-keybind-47-"), "events.db"))
    ws_47 = None
    try:
        srv_47.start()
        ws_47, _, _ = await open_client(port_47)
        await make_resident(ws_47)
        # strip face: padded text stores stripped, bare replay absorbs
        await chat_send(ws_47, "lobby", "  s47 padded  ", "kb-47-a")
        bp = await recv_until(ws_47, lambda f: f.get("type") == "chat.broadcast"
                              and f.get("payload", {}).get("text") == "s47 padded")
        strip_stored = bp is not None
        await chat_send(ws_47, "lobby", "s47 padded", "kb-47-a")
        dp = await dup_of(ws_47, bp.get("evt_id"))
        strip_absorb = strip_stored and dp is not None
        # id-normalization face: padded id then bare id -> same key
        await chat_send(ws_47, "lobby", "s47 idnorm", "  kb-47-b  ")
        bi = await recv_until(ws_47, lambda f: f.get("type") == "chat.broadcast"
                              and f.get("payload", {}).get("text") == "s47 idnorm")
        await chat_send(ws_47, "lobby", "s47 idnorm", "kb-47-b")
        di = await dup_of(ws_47, bi.get("evt_id"))
        idnorm_absorb = bi is not None and di is not None
        # truncation face: 2001-char texts identical to char 2000 share
        # the normalized key (digest is computed after the slice)
        base47 = "s47 tr" + "a" * 1994  # exactly 2000 chars
        await chat_send(ws_47, "lobby", base47 + "X", "kb-47-c")
        bt = await recv_until(ws_47, lambda f: f.get("type") == "chat.broadcast"
                              and f.get("payload", {}).get("text") == base47)
        trunc_stored = (bt is not None
                        and len(bt.get("payload", {}).get("text", "")) == 2000)
        await chat_send(ws_47, "lobby", base47 + "Y", "kb-47-c")
        dt = await dup_of(ws_47, bt.get("evt_id"))
        trunc_absorb = trunc_stored and dt is not None
        rows47 = chat_rows(srv_47.db)
        ok47 = (strip_stored and strip_absorb and idnorm_absorb
                and trunc_stored and trunc_absorb and rows47 == 3)
        record("AC-S47", ok47,
               "strip-face stored+absorbed=%s/%s; id-normalized "
               "absorbed=%s; truncation stored(2000)+absorbed=%s/%s; "
               "rows 3 stable=%s"
               % (strip_stored, strip_absorb, idnorm_absorb, trunc_stored,
                  trunc_absorb, rows47 == 3))
    finally:
        if ws_47 is not None:
            try:
                await ws_47.close()
            except Exception:
                pass
        srv_47.stop()

    # ---- AC-S48: hygiene (suite-only round) ----
    sha_server_post = hashlib.sha256(open(SERVER, "rb").read()).hexdigest()
    sha_config_post = hashlib.sha256(open(CONFIG, "rb").read()).hexdigest()
    own_src = inspect.getsource(idem_keybind_cases)
    ascii_ok = True
    try:
        own_src.encode("ascii")
    except UnicodeEncodeError:
        ascii_ok = False
    ok48 = (sha_server_post == sha_server_pre
            and sha_config_post == sha_config_pre and ascii_ok)
    record("AC-S48", ok48,
           "server.py-unchanged=%s config.json-unchanged=%s section-ascii=%s"
           % (sha_server_post == sha_server_pre,
              sha_config_post == sha_config_pre, ascii_ok))


async def room_board_persist_cases():
    """AC-S49..S54 (R1915): the room.board PROTOCOL face across full
    server-process restarts. Adjudication (premise correction, the
    R1704 precedent): the store-level read-face persist is already
    in-book (R1891 board_persist_cases, AC-S32..S38, EventStore
    direct, zero server-process dependency); the genuine
    zero-in-book surface is the protocol face (handle_room_board
    with its payload.rooms subscription filter) across a ServerProc
    stop -> same-config same-db same-port restart (the R1892
    restart carrier). The protocol face is a pure derivation over
    the persisted events table (the server holds no in-memory board
    state), so a restarted process must reproduce every read
    byte-for-byte at the payload level (the frame ts_utc/room
    fields are server-clock envelope noise, stripped per the R1902
    banded-projection law); new data through the live protocol
    recomputes (zero cache); an explicit-ts November row (the R1876
    lobby explicit-ts product path, appended in a stopped-server
    window) proves the old month window frozen across restart x
    new data while a new zone is born in the November window; a
    second restart keeps the guarantee (sequential-instance
    identity). Product reality adjudication: chat.send only speaks
    into config rooms (server gate), so the live-protocol new data
    lands in the existing lobby room and the new zone is born by
    the November append. Suite-only round: server.py, store.py and
    the shipped config are not modified."""
    sha_server_pre = hashlib.sha256(open(SERVER, "rb").read()).hexdigest()
    sha_store_pre = hashlib.sha256(
        open(os.path.join(BASE, "store.py"), "rb").read()).hexdigest()
    sha_config_pre = hashlib.sha256(open(CONFIG, "rb").read()).hexdigest()
    with open(CONFIG, encoding="utf-8") as handle:
        cfg = json.load(handle)
    notice = cfg["risk_warning"]["text"]

    def dump_payload(fr):
        p = fr.get("payload", {})
        return json.dumps({"board": p.get("board", []),
                           "disclaimer": p.get("disclaimer", "")},
                          sort_keys=True)

    async def board_read(ws, rooms="__unset__"):
        if rooms == "__unset__":
            await ws.send(frame("room.board"))
        else:
            await ws.send(frame("room.board", payload={"rooms": rooms}))
        return await recv_until(ws, lambda f: f.get("type") == "room.board")

    def manual_board(db, window=None):
        sql = ("SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
               " WHERE type = 'chat.broadcast'")
        args = ()
        if window is not None:
            sql += " AND substr(ts_utc, 1, 7) = ?"
            args = (window,)
        sql += " GROUP BY zone ORDER BY zone"
        return [
            {"room": r, "messages": int(n), "actors": int(k)}
            for r, n, k in db_query(db, sql, args)
        ]

    def chat_rows(db):
        return db_query(
            db, "SELECT COUNT(*) FROM events"
            " WHERE type = 'chat.broadcast'")[0][0]

    tmp = tempfile.mkdtemp(prefix="lobby-rbpersist-")
    db = os.path.join(tmp, "events.db")
    port = _free_port()
    srv_a = ServerProc(port, db=db)
    sender = reader = sender2 = reader2 = reader_c = reader_d = None
    srv_b = srv_c = srv_d = None
    try:
        srv_a.start()
        # world load: live-protocol product path - one resident, three
        # broadcasts across two config rooms (lobby x2 + quant x1).
        sender, _, _ = await open_client(port)
        await make_resident(sender)
        await sender.send(frame("chat.send", room="lobby",
                                payload={"text": "s49 lobby one"}))
        await recv_until(sender, lambda f: f.get("type") == "chat.broadcast"
                         and f.get("payload", {}).get("text") == "s49 lobby one")
        await sender.send(frame("chat.send", room="lobby",
                                payload={"text": "s49 lobby two"}))
        await recv_until(sender, lambda f: f.get("type") == "chat.broadcast"
                         and f.get("payload", {}).get("text") == "s49 lobby two")
        await sender.send(frame("room.subscribe", payload={"room": "quant"}))
        await recv_until(sender, lambda f: f.get("type") == "sys.notice")
        await sender.send(frame("chat.send", room="quant",
                                payload={"text": "s49 quant one"}))
        await recv_until(sender, lambda f: f.get("type") == "chat.broadcast"
                         and f.get("payload", {}).get("text") == "s49 quant one")

        # ---- AC-S49: server-A anchor + pre-restart five-face snapshot ----
        reader, _, _ = await open_client(port)  # spectator may query
        full_a = await board_read(reader)
        quant_a = await board_read(reader, ["quant"])
        empty_a = await board_read(reader, [])
        none_a = await board_read(reader, None)
        snap_full = dump_payload(full_a)
        snap_quant = dump_payload(quant_a)
        snap_empty = dump_payload(empty_a)
        board_a = full_a.get("payload", {}).get("board", [])
        expected_a = [
            {"room": "lobby", "messages": 2, "actors": 1},
            {"room": "quant", "messages": 1, "actors": 1}]
        w = db_query(
            db, "SELECT substr(MIN(ts_utc), 1, 7) FROM events"
            " WHERE type = 'chat.broadcast'")[0][0]
        ok49 = (
            board_a == manual_board(db) and board_a == expected_a
            and all(set(r.keys()) == {"room", "messages", "actors"}
                    for r in board_a)
            and sorted(full_a.get("payload", {}).keys())
            == ["board", "disclaimer"]
            and full_a.get("payload", {}).get("disclaimer") == notice
            and full_a.get("ai_generated") is False
            and full_a.get("actor") == "system"
            and quant_a.get("payload", {}).get("board", [])
            == [r for r in board_a if r["room"] == "quant"]
            and empty_a.get("payload", {}).get("board", []) == []
            and dump_payload(none_a) == snap_full
            and manual_board(db, w) == board_a
            and chat_rows(db) == 3)
        record("AC-S49", ok49,
               "board==manual==expected=%s envelope-facts=%s "
               "filter-subseq=%s empty=%s default-none==full=%s "
               "w=%s mirror-window==full=%s chat-rows=3=%s"
               % (board_a == manual_board(db) and board_a == expected_a,
                  (sorted(full_a.get("payload", {}).keys())
                   == ["board", "disclaimer"]
                   and full_a.get("payload", {}).get("disclaimer") == notice
                   and full_a.get("ai_generated") is False
                   and full_a.get("actor") == "system"),
                  quant_a.get("payload", {}).get("board", [])
                  == [r for r in board_a if r["room"] == "quant"],
                  empty_a.get("payload", {}).get("board", []) == [],
                  dump_payload(none_a) == snap_full,
                  w, manual_board(db, w) == board_a, chat_rows(db) == 3))

        # ---- AC-S50: full-process restart, protocol face byte identity ----
        try:
            await sender.close()
        except Exception:
            pass
        try:
            await reader.close()
        except Exception:
            pass
        sender = reader = None
        srv_a.stop()
        srv_b = ServerProc(port, db=db)  # same shipped config, same db
        srv_b.start()
        reader2, _, _ = await open_client(port)
        full_b = await board_read(reader2)
        quant_b = await board_read(reader2, ["quant"])
        empty_b = await board_read(reader2, [])
        full_b2 = await board_read(reader2)
        ok50 = (dump_payload(full_b) == snap_full
                and dump_payload(quant_b) == snap_quant
                and dump_payload(empty_b) == snap_empty
                and dump_payload(full_b2) == dump_payload(full_b))
        record("AC-S50", ok50,
               "restart reproduces protocol reads byte-identical: "
               "full=%s filter=%s empty=%s double-read-self=%s"
               % (dump_payload(full_b) == snap_full,
                  dump_payload(quant_b) == snap_quant,
                  dump_payload(empty_b) == snap_empty,
                  dump_payload(full_b2) == dump_payload(full_b)))

        # ---- AC-S51: post-restart new data through the live protocol ----
        rows_pre51 = chat_rows(db)
        sender2, _, _ = await open_client(port)
        await make_resident(sender2)
        await sender2.send(frame("chat.send", room="lobby",
                                 payload={"text": "s51 lobby fresh"}))
        await recv_until(sender2, lambda f: f.get("type") == "chat.broadcast"
                         and f.get("payload", {}).get("text") == "s51 lobby fresh")
        full_b3 = await board_read(reader2)
        lobby_b = await board_read(reader2, ["lobby"])
        quant_b3 = await board_read(reader2, ["quant"])
        board_b3 = full_b3.get("payload", {}).get("board", [])
        expected_b3 = [
            {"room": "lobby", "messages": 3, "actors": 2},
            {"room": "quant", "messages": 1, "actors": 1}]
        rows_post51 = chat_rows(db)
        ok51 = (dump_payload(full_b3) != snap_full
                and board_b3 == manual_board(db)
                and board_b3 == expected_b3
                and lobby_b.get("payload", {}).get("board", [])
                == [{"room": "lobby", "messages": 3, "actors": 2}]
                and dump_payload(quant_b3) == snap_quant
                and rows_post51 == rows_pre51 + 1)
        record("AC-S51", ok51,
               "post-restart live data recomputed: full!=pre=%s "
               "==manual==expected=%s lobby-filter=%s "
               "quant-frozen==pre=%s chat-rows %d -> %d"
               % (dump_payload(full_b3) != snap_full,
                  board_b3 == manual_board(db)
                  and board_b3 == expected_b3,
                  lobby_b.get("payload", {}).get("board", [])
                  == [{"room": "lobby", "messages": 3, "actors": 2}],
                  dump_payload(quant_b3) == snap_quant,
                  rows_pre51, rows_post51))

        # pure-read battery on the live server: board reads never write
        cnt_before = [db_query(db, "SELECT COUNT(*) FROM " + t)[0][0]
                      for t in ("events", "census_cache")]
        for _ in range(3):
            await board_read(reader2)
        await board_read(reader2, ["lobby"])
        await board_read(reader2, [])
        cnt_after = [db_query(db, "SELECT COUNT(*) FROM " + t)[0][0]
                     for t in ("events", "census_cache")]

        try:
            await sender2.close()
        except Exception:
            pass
        try:
            await reader2.close()
        except Exception:
            pass
        sender2 = reader2 = None
        srv_b.stop()

        # ---- AC-S52: stopped-window explicit-ts November row + cross-face ----
        from store import EventStore
        st = EventStore(db, disclaimer=notice)
        s_oct = json.dumps(st.room_message_board(window=w), sort_keys=True)
        st.append("2026-11-05T01:00:01.000000Z", "chat.broadcast",
                  "res-nov-direct", "arena", "nov arena row",
                  {"text": "nov arena row"})
        nov_env = st.room_message_board(window="2026-11")
        store_full_rows = st.room_message_board()["room_message_board"]
        nov_expected_rows = [{"room": "arena", "messages": 1, "actors": 1}]
        full_expected_rows = [
            {"room": "arena", "messages": 1, "actors": 1},
            {"room": "lobby", "messages": 3, "actors": 2},
            {"room": "quant", "messages": 1, "actors": 1}]
        ok_nov_local = (nov_env["room_message_board"] == nov_expected_rows
                        and store_full_rows == full_expected_rows)
        st.close()

        srv_c = ServerProc(port, db=db)
        srv_c.start()
        reader_c, _, _ = await open_client(port)
        full_c = await board_read(reader_c)
        ok52 = (ok_nov_local
                and dump_payload(full_c) == json.dumps(
                    {"board": store_full_rows, "disclaimer": notice},
                    sort_keys=True)
                and full_c.get("payload", {}).get("board", [])
                == manual_board(db))
        record("AC-S52", ok52,
               "nov-window==[arena 1/1]=%s store-full==expected=%s; "
               "restarted server protocol read == store read "
               "byte-identical=%s manual-cross=%s"
               % (nov_env["room_message_board"] == nov_expected_rows,
                  store_full_rows == full_expected_rows,
                  dump_payload(full_c) == json.dumps(
                      {"board": store_full_rows, "disclaimer": notice},
                      sort_keys=True),
                  full_c.get("payload", {}).get("board", [])
                  == manual_board(db)))

        # ---- AC-S53: old-window freeze + second restart sequential reads ----
        quant_c = await board_read(reader_c, ["quant"])
        cap_full_c = dump_payload(full_c)
        cap_quant_c = dump_payload(quant_c)
        try:
            await reader_c.close()
        except Exception:
            pass
        reader_c = None
        srv_c.stop()

        st2 = EventStore(db, disclaimer=notice)
        oct_after = json.dumps(st2.room_message_board(window=w),
                               sort_keys=True)
        nov_after = json.dumps(st2.room_message_board(window="2026-11"),
                               sort_keys=True)
        st2.close()

        srv_d = ServerProc(port, db=db)  # second restart, no data change
        srv_d.start()
        reader_d, _, _ = await open_client(port)
        full_d = await board_read(reader_d)
        quant_d = await board_read(reader_d, ["quant"])
        ok53 = (oct_after == s_oct
                and json.loads(nov_after)["room_message_board"]
                == nov_expected_rows
                and dump_payload(full_d) == cap_full_c
                and dump_payload(quant_d) == cap_quant_c)
        record("AC-S53", ok53,
               "oct-window frozen across restart-x-nov-row=%s "
               "nov-window==[arena 1/1]=%s; second restart sequential "
               "reads byte-identical: full=%s quant=%s"
               % (oct_after == s_oct,
                  json.loads(nov_after)["room_message_board"]
                  == nov_expected_rows,
                  dump_payload(full_d) == cap_full_c,
                  dump_payload(quant_d) == cap_quant_c))

        # ---- AC-S54: pure-read law + hygiene (suite-only round) ----
        sha_server_post = hashlib.sha256(
            open(SERVER, "rb").read()).hexdigest()
        sha_store_post = hashlib.sha256(
            open(os.path.join(BASE, "store.py"), "rb").read()).hexdigest()
        sha_config_post = hashlib.sha256(
            open(CONFIG, "rb").read()).hexdigest()
        own_src = inspect.getsource(room_board_persist_cases)
        ascii_ok = True
        try:
            own_src.encode("ascii")
        except UnicodeEncodeError:
            ascii_ok = False
        ok54 = (cnt_before == cnt_after
                and sha_server_post == sha_server_pre
                and sha_store_post == sha_store_pre
                and sha_config_post == sha_config_pre
                and ascii_ok)
        record("AC-S54", ok54,
               "read-battery row-counts stable=%s (%s); server.py=%s "
               "store.py=%s config.json=%s unchanged; section-ascii=%s"
               % (cnt_before == cnt_after, cnt_before,
                  sha_server_post == sha_server_pre,
                  sha_store_post == sha_store_pre,
                  sha_config_post == sha_config_pre, ascii_ok))
    finally:
        for ws_ in (sender, reader, sender2, reader2, reader_c, reader_d):
            if ws_ is not None:
                try:
                    await ws_.close()
                except Exception:
                    pass
        for srv_ in (srv_a, srv_b, srv_c, srv_d):
            if srv_ is not None:
                srv_.stop()


async def suite():
    with open(CONFIG, encoding="utf-8") as handle:
        cfg = json.load(handle)
    fw = cfg["gate"]["forbidden_words"][0]
    ab = cfg["gate"]["advisory_ban_words"][0]

    ok_refusal, ev_refusal = startup_refusal_cases()

    srv = ServerProc(8091)
    srv.start()
    clients = []
    try:
        # AC-S1: first frame = sys.hello (protocol version / room list / risk doc pointer)
        a, first, second = await open_client(8091)
        clients.append(a)
        ok1 = (first.get("type") == "sys.hello"
               and first.get("payload", {}).get("v") == cfg["protocol_version"]
               and first.get("payload", {}).get("rooms") == cfg["rooms"]
               and bool(first.get("payload", {}).get("risk_doc")))
        record("AC-S1", ok1, "first frame type=%s payload keys=%s"
               % (first.get("type"), sorted(first.get("payload", {}).keys())))

        # AC-S6: sys.risk_warning delivered at connect, persistent flag set
        ok6 = (second.get("type") == "sys.risk_warning"
               and bool(second.get("payload", {}).get("text"))
               and second.get("payload", {}).get("persistent") is True)
        record("AC-S6", ok6, "frame2 type=%s persistent=%s text_len=%d"
               % (second.get("type"), second.get("payload", {}).get("persistent"),
                  len(second.get("payload", {}).get("text", ""))))

        # AC-S2: spectator receives broadcasts but cannot speak
        b, _, _ = await open_client(8091)
        clients.append(b)
        grant = await make_resident(b)
        b_actor = grant.get("payload", {}).get("actor", "")
        await a.send(frame("chat.send", room="lobby", payload={"text": "spectator tries to speak"}))
        rej = await recv_json(a)
        ok_rej = (rej.get("type") == "sec.reject"
                  and rej.get("payload", {}).get("code") == "E_ENTRANCE_REQUIRED")
        silent_b = await expect_silence(b, 0.5)
        await b.send(frame("chat.send", room="lobby", payload={"text": "resident hello"}))
        got = await recv_until(a, lambda f: f.get("type") == "chat.broadcast")
        ok2 = ok_rej and silent_b and got.get("payload", {}).get("text") == "resident hello"
        record("AC-S2", ok2, "spectator-rejected=%s not-broadcast=%s spectator-receives=%s"
               % (ok_rej, silent_b, got.get("payload", {}).get("text") == "resident hello"))

        # AC-S3: resident chat broadcasts to the room; round trip <= 500ms; rooms isolated
        c, _, _ = await open_client(8091)
        clients.append(c)
        await c.send(frame("room.unsubscribe", payload={"room": "lobby"}))
        await recv_until(c, lambda f: f.get("type") == "sys.notice")
        await c.send(frame("room.subscribe", payload={"room": "quant"}))
        await recv_until(c, lambda f: f.get("type") == "sys.notice")
        t0 = time.perf_counter()
        await b.send(frame("chat.send", room="lobby",
                           payload={"text": "rtt check " + uuid.uuid4().hex[:6]}))
        own = await recv_until(b, lambda f: f.get("type") == "chat.broadcast")
        rtt_self = (time.perf_counter() - t0) * 1000.0
        other = await recv_until(a, lambda f: f.get("type") == "chat.broadcast")
        rtt_other = (time.perf_counter() - t0) * 1000.0
        iso_silent = await expect_silence(c, 0.5)
        await b.send(frame("room.subscribe", payload={"room": "quant"}))
        await recv_until(b, lambda f: f.get("type") == "sys.notice")
        await b.send(frame("chat.send", room="quant", payload={"text": "quant only msg"}))
        got_c = await recv_until(c, lambda f: f.get("type") == "chat.broadcast")
        await recv_until(b, lambda f: f.get("type") == "chat.broadcast")
        ok3 = (rtt_self <= 500 and rtt_other <= 500 and iso_silent
               and got_c.get("room") == "quant"
               and got_c.get("payload", {}).get("text") == "quant only msg")
        # R1876 hardening: ms readouts display as budget-class tokens
        # (the <=500ms gate is still really measured inside ok3).
        record("AC-S3", ok3, "rtt self=%s other=%s lobby-isolation=%s quant-recv-room=%s"
               % ("ok(<=500ms)" if rtt_self <= 500.0 else "over",
                  "ok(<=500ms)" if rtt_other <= 500.0 else "over",
                  iso_silent, got_c.get("room")))

        # AC-S4: wordlist gate hits rejected (no broadcast, nothing in the
        # public event stream); clean text passes; unwired gate refuses startup
        await b.send(frame("chat.send", room="lobby", payload={"text": "gate probe " + fw}))
        rej1 = await recv_until(b, lambda f: f.get("type") == "sec.reject")
        ok_hit1 = (rej1.get("payload", {}).get("code") == "E_CONTENT_REJECTED"
                   and str(rej1.get("payload", {}).get("reason", "")).startswith("gate 1"))
        silent_a = await expect_silence(a, 0.5)
        await b.send(frame("chat.send", room="lobby", payload={"text": "advisory probe " + ab}))
        rej2 = await recv_until(b, lambda f: f.get("type") == "sec.reject")
        ok_hit2 = (rej2.get("payload", {}).get("code") == "E_CONTENT_REJECTED"
                   and str(rej2.get("payload", {}).get("reason", "")).startswith("gate 2"))
        await b.send(frame("chat.send", room="lobby",
                           payload={"text": "clean text passes the gate"}))
        clean = await recv_until(b, lambda f: f.get("type") == "chat.broadcast")
        clean_a = await recv_until(a, lambda f: f.get("type") == "chat.broadcast")
        ok_clean = (clean.get("payload", {}).get("text") == "clean text passes the gate"
                    and clean_a.get("payload", {}).get("text") == "clean text passes the gate")
        n_hit = db_query(srv.db, "SELECT COUNT(*) FROM events WHERE summary LIKE ?",
                         ("%gate probe%",))[0][0]
        n_adv = db_query(srv.db, "SELECT COUNT(*) FROM events WHERE summary LIKE ?",
                         ("%advisory probe%",))[0][0]
        ok4 = ok_refusal and ok_hit1 and ok_hit2 and silent_a and ok_clean and n_hit == 0 and n_adv == 0
        record("AC-S4", ok4,
               "refusal[%s]; gate1=%s gate2=%s no-broadcast=%s clean-passed=%s rejected-in-stream=%d/%d"
               % (ev_refusal, ok_hit1, ok_hit2, silent_a, ok_clean, n_hit, n_adv))

        # AC-S5: ai_generated is server-authoritative (spoof overwritten to
        # false; server-side AI receipt carries true + presentation label)
        await b.send(json.dumps({
            "v": 1, "type": "chat.send", "room": "lobby",
            "payload": {"text": "ai flag spoof probe"},
            "ai_generated": True, "actor": "spoofed-actor",
            "ts_utc": "1970-01-01T00:00:00Z"}, ensure_ascii=False))
        spoof = await recv_until(b, lambda f: f.get("type") == "chat.broadcast")
        ok_spoof = (spoof.get("ai_generated") is False
                    and spoof.get("actor") == b_actor
                    and spoof.get("actor") != "spoofed-actor")
        await b.send(frame("idea.submit", payload={"text": "idea probe: sandbox triage stub"}))
        notice = await recv_until(b, lambda f: f.get("type") == "sys.notice"
                                  and f.get("ai_generated") is True)
        ok_ai = bool(notice.get("ai_label")) and notice.get("actor") == "system-ai"
        record("AC-S5", ok_spoof and ok_ai,
               "spoof overwritten: ai_generated=%s actor=%s; ai-notice ai_generated=%s label-set=%s"
               % (spoof.get("ai_generated"), _actorshape(spoof.get("actor")),
                  notice.get("ai_generated"), bool(notice.get("ai_label"))))

        # AC-S7: six-field core + evt_id rows, dedup on replay, jsonl export
        row = db_query(srv.db, "SELECT evt_id, ts_utc, type, actor, repo, zone, summary "
                       "FROM events WHERE type='chat.broadcast' ORDER BY ts_utc DESC LIMIT 1")[0]
        ok_row = (row[4] == "domain/BigDomain" and row[5] in cfg["rooms"]
                  and all(bool(x) for x in row))
        from store import EventStore
        unit_dir = tempfile.mkdtemp(prefix="lobby-unit-")
        st = EventStore(os.path.join(unit_dir, "unit.db"))
        evt = ("2026-09-24T00:00:00.000000Z", "chat.broadcast", "res-test",
               "lobby", "dedup probe", {"text": "dedup probe"})
        eid = st.append(*evt)
        dedup_rejected = False
        try:
            st.append(*evt)
        except sqlite3.IntegrityError:
            dedup_rejected = True
        path, written = st.export_day("2026-09-24", os.path.join(unit_dir, "export"))
        ok_export = os.path.exists(path) and written == 1
        if ok_export:
            with open(path, encoding="utf-8") as handle:
                lines = [json.loads(line) for line in handle if line.strip()]
            ok_export = (len(lines) == 1 and lines[0].get("evt_id") == eid
                         and {"ts_utc", "type", "actor", "repo", "zone", "summary",
                              "evt_id"}.issubset(lines[0].keys()))
        st.close()
        record("AC-S7", ok_row and dedup_rejected and ok_export,
               "last row repo=%s zone=%s all-fields-set=%s; replay-rejected=%s; jsonl-export=%s evt_id=%s"
               % (row[4], row[5], all(bool(x) for x in row), dedup_rejected, ok_export, eid))

        # AC-S9: 5 msgs / 10s, then E_RATE_LIMIT; 3 consecutive violations = mute
        d, _, _ = await open_client(8091)
        clients.append(d)
        await make_resident(d)
        for i in range(5):
            await d.send(frame("chat.send", room="lobby",
                               payload={"text": "burst msg %d" % i}))
        for _ in range(5):
            await recv_until(d, lambda f: f.get("type") == "chat.broadcast")
        await d.send(frame("chat.send", room="lobby", payload={"text": "burst violation 1"}))
        f1 = await recv_json(d)
        await d.send(frame("chat.send", room="lobby", payload={"text": "burst violation 2"}))
        f2 = await recv_json(d)
        await d.send(frame("chat.send", room="lobby", payload={"text": "burst violation 3"}))
        f3 = await recv_json(d)
        ok_v = all(f.get("type") == "err.rate_limit"
                   and f.get("payload", {}).get("code") == "E_RATE_LIMIT" for f in (f1, f2))
        ok_mute = (f3.get("type") == "sec.reject"
                   and f3.get("payload", {}).get("code") == "E_RATE_LIMIT"
                   and float(f3.get("payload", {}).get("muted_until", 0)) > time.time())
        await d.send(frame("chat.send", room="lobby", payload={"text": "burst while muted"}))
        f4 = await recv_json(d)
        ok_hold = f4.get("type") == "sec.reject"
        record("AC-S9", ok_v and ok_mute and ok_hold,
               "violations-err.rate_limit=%s; 3rd-violation-mute-sec.reject=%s muted_until-in-future=%s; "
               "muted-hold=%s (60s unmute path not awaited in suite; window asserted via muted_until)"
               % (ok_v, f3.get("type"), ok_mute, ok_hold))

        # AC-S10: routing: chat -> room broadcast; idea -> proposal pool stub
        e, _, _ = await open_client(8091)
        clients.append(e)
        await make_resident(e)
        await e.send(frame("chat.send", room="lobby",
                           payload={"text": "routing probe chat line"}))
        chat_out = await recv_until(e, lambda f: f.get("type") == "chat.broadcast")
        await e.send(frame("idea.submit", payload={"text": "routing probe idea entry"}))
        idea_out = await recv_until(e, lambda f: f.get("type") == "sys.notice"
                                    and f.get("ai_generated") is True)
        types = [r[0] for r in db_query(srv.db, "SELECT DISTINCT type FROM events "
                                            "WHERE summary LIKE 'routing probe%'")]
        ok10 = (chat_out.get("type") == "chat.broadcast" and chat_out.get("room") == "lobby"
                and idea_out.get("type") == "sys.notice"
                and bool(idea_out.get("payload", {}).get("idea_id"))
                and "chat.broadcast" in types and "idea.submit" in types)
        record("AC-S10", ok10, "chat->%s(room=%s); idea->pool-stub idea_id=%s; store-types=%s"
               % (chat_out.get("type"), chat_out.get("room"),
                  bool(idea_out.get("payload", {}).get("idea_id")), types))

        # AC-S16: room.board protocol wiring (R1790) - spectator public
        # read face over the R1773 store read face; cross-checked against
        # this server's db (WAL concurrent read) and proven live-fresh.
        fb, _, _ = await open_client(8091)
        clients.append(fb)
        await fb.send(frame("room.board"))
        board_frame = await recv_until(fb, lambda x: x.get("type") == "room.board")
        board = board_frame.get("payload", {}).get("board", [])
        bdis = board_frame.get("payload", {}).get("disclaimer", "")
        manual = db_query(
            srv.db,
            "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
            " WHERE type='chat.broadcast' GROUP BY zone ORDER BY zone")
        manual_board = [{"room": r, "messages": int(n), "actors": int(k)}
                        for r, n, k in manual]
        ok_board = (board == manual_board
                    and board_frame.get("ai_generated") is False
                    and board_frame.get("actor") == "system"
                    and bdis == cfg["risk_warning"]["text"]
                    and all(row["room"] in cfg["rooms"] for row in board)
                    and any(row["messages"] > 0 for row in board))
        # fresh reflection: a new broadcast moves the next board query
        # (e is the resident with remaining rate budget; d is muted)
        await e.send(frame("chat.send", room="lobby",
                           payload={"text": "board refresh probe"}))
        await recv_until(e, lambda x: x.get("type") == "chat.broadcast")
        await fb.send(frame("room.board"))
        board2 = (await recv_until(fb, lambda x: x.get("type") == "room.board")) \
            .get("payload", {}).get("board", [])
        lob1 = [row for row in board if row["room"] == "lobby"][0]
        lob2 = [row for row in board2 if row["room"] == "lobby"][0]
        ok_fresh = lob2["messages"] == lob1["messages"] + 1
        # legacy no-disclaimer store: graceful sec.reject, no crash
        import server as lobby_server
        from sec_gate import SecGate as _SecGate
        legacy_dir = tempfile.mkdtemp(prefix="lobby-legacy-")
        legacy_store = EventStore(os.path.join(legacy_dir, "legacy.db"))
        legacy_gate = _SecGate.from_config(cfg)
        legacy_lobby = lobby_server.Lobby(cfg, legacy_gate, legacy_store)

        class _FakeWS:
            def __init__(self):
                self.frames = []

            async def send(self, data):
                self.frames.append(json.loads(data))

        legacy_client = lobby_server.Client(_FakeWS(), legacy_lobby.rooms)
        await legacy_lobby.handle_room_board(legacy_client, None)
        rej_frame = legacy_client.ws.frames[-1]
        ok_legacy = (rej_frame.get("type") == "sec.reject"
                     and rej_frame.get("payload", {}).get("code") == "E_STORE_NO_DISCLAIMER")
        legacy_store.close()
        record("AC-S16", ok_board and ok_fresh and ok_legacy,
               "board==manual-sql=%s rooms=%s ai_generated=%s actor=%s "
               "disclaimer-match=%s fresh-reflection=%s legacy-reject=%s"
               % (board == manual_board, [r["room"] for r in board],
                  board_frame.get("ai_generated") is False,
                  board_frame.get("actor"),
                  bdis == cfg["risk_warning"]["text"], ok_fresh, ok_legacy))

        # AC-S17: room.board optional subscription filter (R1791) -
        # payload.rooms absent/None keeps the full board; a list filters
        # rows Python-side AFTER the store read face (order-preserving
        # subsequence, zero second SQL engine); an explicit empty list
        # is an honest empty interest set; bad forms fail closed through
        # sec.reject E_BAD_FRAME and the connection survives.
        async def recv_or_none(ws_, pred_, timeout_=3.0):
            try:
                return await recv_until(ws_, pred_, timeout_)
            except (TimeoutError, ConnectionClosed):
                return None

        await fb.send(frame("room.board"))
        full17 = (await recv_until(fb, lambda x: x.get("type") == "room.board")) \
            .get("payload", {}).get("board", [])
        await fb.send(frame("room.board", payload={"rooms": ["lobby"]}))
        p17 = (await recv_until(fb, lambda x: x.get("type") == "room.board")) \
            .get("payload", {})
        b17 = p17.get("board", [])
        manual17 = db_query(
            srv.db,
            "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
            " WHERE type='chat.broadcast' GROUP BY zone ORDER BY zone")
        manual17_board = [{"room": r, "messages": int(n), "actors": int(k)}
                          for r, n, k in manual17]
        ok_filter = (
            b17 == [row for row in full17 if row["room"] == "lobby"]
            and b17 == [row for row in manual17_board if row["room"] == "lobby"]
            and [row["room"] for row in b17] == ["lobby"]
            and sorted(p17.keys()) == ["board", "disclaimer"]
            and p17.get("disclaimer") == cfg["risk_warning"]["text"])
        await fb.send(frame("room.board",
                            payload={"rooms": ["quant", "lobby", "nether"]}))
        b17b = (await recv_until(fb, lambda x: x.get("type") == "room.board")) \
            .get("payload", {}).get("board", [])
        ok_multi = (
            b17b == [row for row in full17
                     if row["room"] in ("quant", "lobby")]
            and "nether" not in [row["room"] for row in b17b]
            and len(b17b) >= 2)
        await fb.send(frame("room.board", payload={"rooms": []}))
        b17c = (await recv_until(fb, lambda x: x.get("type") == "room.board")) \
            .get("payload", {}).get("board", [])
        ok_empty = b17c == []
        bad17 = []
        for bad in ("lobby", ["lobby", 3], [""], ["   "], {"lobby": 1}, True):
            await fb.send(frame("room.board", payload={"rooms": bad}))
            rej17 = await recv_or_none(
                fb, lambda f: f.get("type") == "sec.reject"
                and f.get("payload", {}).get("code") == "E_BAD_FRAME")
            bad17.append(rej17 is not None)
        ok_bad = all(bad17)
        # default sentinel None + connection survival: the same socket
        # still answers a good query after the reject burst.
        await fb.send(frame("room.board", payload={"rooms": None}))
        b17d = await recv_or_none(
            fb, lambda x: x.get("type") == "room.board")
        ok_default = (b17d is not None
                     and b17d.get("payload", {}).get("board", []) == full17)
        record("AC-S17",
               ok_filter and ok_multi and ok_empty and ok_bad and ok_default,
               "single==py-slice==manual-sql=%s multi+unknown=%s empty=%s "
               "bad-forms-reject=%s default-none-full=%s"
               % (ok_filter, ok_multi, ok_empty, bad17, ok_default))

        # AC-S8a: heartbeat config 30/60 on the main server + no-pong enforcement
        ok_cfg_hb = (cfg["heartbeat"]["ping_interval"] == 30
                     and cfg["heartbeat"]["ping_timeout"] == 60)
        ok_banner = "ping_interval=30" in srv.banner and "ping_timeout=60" in srv.banner
        ok_mech, ev_mech = heartbeat_mechanism_case()
        record("AC-S8a", ok_cfg_hb and ok_banner and ok_mech,
               "config-30/60=%s banner-ok=%s; %s" % (ok_cfg_hb, ok_banner, ev_mech))

        # AC-S8c/S8d/S8e: client reconnect semantics face (spec v0.4)
        await reconnect_cases()
    finally:
        for ws in clients:
            try:
                await ws.close()
            except Exception:
                pass
        srv.stop()

    # AC-S14/S15: room-level message read face (R1773) - unit store plus
    # this server's real db (server stopped; WAL read recovery on open).
    room_board_cases(srv.db)

    # AC-S18/S19: event-derived idea pool read face + idea.board wire
    # face with restart-survival proof (fresh process on the same db).
    await idea_board_cases(srv.db)

    # AC-S20/S21/S22 (R1869): month-window parameter on the two
    # lobby board read faces (store-level; window only slices rows).
    board_window_cases(srv.db)

    # AC-S23/S24/S25 (R1876): cross-month roll preservation on the
    # two lobby board read faces (explicit-ts world; store-level).
    board_monthroll_cases()

    # AC-S26..S31 (R1882): read-cap limit parameter on the two
    # lobby board read faces (store-level; live-db cross on the
    # real server db).
    board_readcap_cases(srv.db)
    board_persist_cases()

    # AC-S39..S43 (R1892): chat.send idem_seen restart semantics window
    # (in-TTL absorption / cross-restart re-entry / TTL expiry / FIFO cap).
    await idem_restart_cases()

    # AC-S44..S48 (R1899): chat.send idem key binding semantics window
    # (same-id-different-text / cross-connection / id-domain / pre-key
    # normalization faces).
    await idem_keybind_cases()

    # AC-IDT1..IDT8 (R2012): chat.send idem_seen TTL/FIFO boundary
    # window (fixed-window non-refresh / post-expiry re-arm /
    # per-key staggered windows / len==cap no-eviction / over-cap
    # FIFO eviction order).
    await idem_boundary_cases()

    # AC-IDB1..IDB7 (R2013 criteria, R2014): chat.send gate-order
    # budget window - the idem gate sits before the rate limit, so
    # replays of processed sends absorb as duplicates without
    # burning/freeing/extending rate budget while the 5/10s window
    # stays saturated (fresh-storm + 10-replay storm + 6th-fresh
    # rejection + no-id control anchor, shipped config values).
    await idem_budget_gateorder_cases()

    # AC-S49..S54 (R1915): room.board protocol face across full
    # server-process restarts (the store-level persist is already
    # in-book R1891; the protocol face + subscription filter across
    # a ServerProc restart is the genuine zero-in-book surface).
    await room_board_persist_cases()

    await city_cases()


def ws_open(ws):
    state = getattr(ws, "state", None)
    if state is not None:
        return getattr(state, "name", "") == "OPEN"
    return not getattr(ws, "closed", True)


async def load_test():
    """AC-S8b: N concurrent connections, sustained broadcast, p95 latency."""
    n = int(os.environ.get("LOAD_N", "100"))
    secs = float(os.environ.get("LOAD_SECS", "300"))
    senders = max(1, n // 10)
    srv = ServerProc(8091, db=os.path.join(tempfile.mkdtemp(prefix="lobby-load-"), "events.db"))
    srv.start()
    t0_map = {}
    deltas = []
    frames_seen = [0] * n
    closed_during_run = []
    conns = []
    try:
        for _ in range(n):
            ws, _, _ = await open_client(8091)
            conns.append(ws)
        for i in range(senders):
            await make_resident(conns[i])

        async def reader(idx, ws):
            try:
                while True:
                    data = await recv_json(ws, 10.0)
                    if data.get("type") == "chat.broadcast":
                        frames_seen[idx] += 1
                        text = data.get("payload", {}).get("text", "")
                        if text.startswith("L:") and text[2:] in t0_map:
                            deltas.append((time.perf_counter() - t0_map[text[2:]]) * 1000.0)
            except Exception:
                closed_during_run.append(idx)

        readers = [asyncio.create_task(reader(i, ws)) for i, ws in enumerate(conns)]
        stop_at = time.perf_counter() + secs

        async def sender(ws):
            sent = 0
            while time.perf_counter() < stop_at:
                token = uuid.uuid4().hex[:8]
                t0_map[token] = time.perf_counter()
                await ws.send(frame("chat.send", room="lobby", payload={"text": "L:" + token}))
                sent += 1
                await asyncio.sleep(2.2)  # stay under the 5 msgs / 10s limit
            return sent

        async def monitor():
            while time.perf_counter() < stop_at:
                await asyncio.sleep(30)
                left = max(0.0, stop_at - time.perf_counter())
                print("load progress: %.0fs left, frames=%d" % (left, sum(frames_seen)), flush=True)

        outcomes = await asyncio.gather(
            *(sender(conns[i]) for i in range(senders)), monitor())
        await asyncio.sleep(0.5)
        for task in readers:
            task.cancel()
        alive = sum(1 for ws in conns if ws_open(ws))
        await asyncio.gather(*(ws.close() for ws in conns), return_exceptions=True)
        deltas.sort()
        p50 = deltas[int(len(deltas) * 0.50)] if deltas else -1
        p95 = deltas[min(len(deltas) - 1, int(len(deltas) * 0.95))] if deltas else -1
        mx = deltas[-1] if deltas else -1
        ok = alive == n and not closed_during_run and len(deltas) > 0 and p95 <= 200
        record("AC-S8b", ok,
               "load n=%d secs=%.0f senders=%d msgs=%d deltas=%d p50=%.1fms p95=%.1fms "
               "max=%.1fms alive=%d closed=%d"
               % (n, secs, senders, sum(outcomes[:-1]), len(deltas), p50, p95, mx,
                  alive, len(closed_during_run)))
    finally:
        srv.stop()


def main():
    if "--load" in sys.argv:
        asyncio.run(load_test())
    else:
        asyncio.run(suite())
    fails = [ac for ac, ok in RESULTS if not ok]
    total = len(RESULTS)
    print("SUITE %s (%d/%d criteria pass)" % ("PASS" if not fails else "FAIL",
                                              total - len(fails), total), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
