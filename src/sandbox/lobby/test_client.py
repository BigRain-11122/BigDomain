"""Acceptance suite for the sandbox lobby server (BigDomain P-47-1b + P-47-1c).

Asserts the pre-registered criteria AC-S1..AC-S13 from
docs/spec/lobby-websocket-spec.md section 1 (AC-S11..S13 = city running
face: census whitelist reads, avatar intake, read-only HTTP API) plus the
client reconnect semantics face AC-S8c/S8d/S8e (spec v0.4: keepalive dead
detection, backoff reconnect with exact room-set restoration, idempotent
replay via client_msg_id) plus the room-level message read face
AC-S14/S15 (R1773: per-room chat counts + distinct active-actor
aggregation, pure-read derivation on the EventStore, zero UPDATE,
standing disclaimer envelope, fail-closed without a wired disclaimer).
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
    ev.append("port-%d-never-bound=%s" % (probe_port, bound_ok))
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
        return closed and elapsed < 10, (
            "server disconnected the no-pong client after %.1fs (test instance interval=1s timeout=2s)"
            % elapsed)
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
               "baseline-acked=%s; dead=%s via=%s in %.1fs (keepalive 1s+1s, bound 6s); "
               "proxy-frozen=%s sessions=%d (no-FIN premise); reconnect-direct=%s; "
               "post-recovery-roundtrip=%s pending=%d"
               % (baseline_ok, dead, how, elapsed, proxy_a.frozen, proxy_a.sessions,
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
               "via=%s in %.1fs; reconnect=%s; duplicate-ack evt-match=%s id-match=%s "
               "code=%s; store-rows=%d; no-rebroadcast=%s; pending=%d; post-roundtrip=%s"
               % (armed_ok, proxy_b.frozen, 1, orig_evt, dead2, how2, elapsed2, rec2,
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
               "dead=%s via=%s in %.1fs; refusal-drill budget-out=%s "
               "drill-refusals=%d (retry loop caught+backed off real "
               "refusals); restart: reconnect=%s retries=%d (>=1, <=10: "
               "not busy-spinning; a corpse-backlog dial may bridge the "
               "restart on Windows loopback - honest count); room-set "
               "restored exactly: lobby-isolated=%s quant-received=%s"
               % (dead3, how3, elapsed3, drill_rec, drill_refusals,
                  rec3, retries, silent_lobby, quant_recv is not None))
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
        record("AC-S3", ok3, "rtt self=%.1fms other=%.1fms lobby-isolation=%s quant-recv-room=%s"
               % (rtt_self, rtt_other, iso_silent, got_c.get("room")))

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
               % (spoof.get("ai_generated"), spoof.get("actor"),
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
