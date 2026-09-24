"""Acceptance suite for the sandbox lobby server (BigDomain P-47-1b).

Asserts the pre-registered criteria AC-S1..AC-S10 from
docs/spec/lobby-websocket-spec.md section 1. Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Usage (run with the repo venv python that has websockets installed):
    python test_client.py            # AC-S1..S7, S9, S10 + startup refusal + heartbeat mechanism
    python test_client.py --load     # AC-S8 load: LOAD_N conns for LOAD_SECS (default 100 x 300s)
"""

import asyncio
import base64
import json
import os
import socket
import sqlite3
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


def startup_refusal_cases():
    """AC-S4 half: a missing/unwired gate config must refuse startup."""
    tmp = tempfile.mkdtemp(prefix="lobby-refusal-")
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
            [sys.executable, SERVER, "--host", "127.0.0.1", "--port", "8093",
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
        socket.create_connection(("127.0.0.1", 8093), timeout=1).close()
        bound_ok = False
    except OSError:
        bound_ok = True  # nothing ever bound = door stayed shut
    ev.append("port-8093-never-bound=%s" % bound_ok)
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
    srv = ServerProc(8094, extra=["--ping-interval", "1", "--ping-timeout", "2"])
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
    finally:
        for ws in clients:
            try:
                await ws.close()
            except Exception:
                pass
        srv.stop()


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
