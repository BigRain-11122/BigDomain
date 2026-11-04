"""Two-client interop proof for the lobby sandbox (P-47-1b acceptance face).

Starts the real server on a private port and a private database, then runs the
CE0-visible acceptance case from D-20261105-09: one paying client and one
spectator in the same room, one message arriving, one refusal.

What it proves, in order:
  1. sys.hello then sys.risk_warning arrive first (AC-S1, AC-S6)
  2. a spectator send is refused with E_ENTRANCE_REQUIRED and is not broadcast
  3. a sandbox-granted client send is broadcast to both connections (AC-S3)
  4. the broadcast carries the server-authoritative ai_generated flag (AC-S5)
  5. a blocked word is refused and never broadcast (AC-S4)

Usage:
    python interop_demo.py --label R2456 --log qa/lobby-interop-R2456.log
Exit 0 only when every case above is proved.
"""

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
import tempfile
import time

BASE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(BASE, "server.py")

from websockets.asyncio.client import connect  # noqa: E402


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


async def recv_until(ws, wanted, timeout=6.0):
    """Read frames until one of the wanted types arrives (or time out)."""
    deadline = time.monotonic() + timeout
    seen = []
    while True:
        left = deadline - time.monotonic()
        if left <= 0:
            raise AssertionError("timeout waiting for %s; saw %s" % (wanted, seen))
        raw = await asyncio.wait_for(ws.recv(), timeout=left)
        frame = json.loads(raw)
        seen.append(frame.get("type"))
        if frame.get("type") in wanted:
            return frame


async def wait_ready(port, deadline=20.0):
    end = time.monotonic() + deadline
    while time.monotonic() < end:
        try:
            async with connect("ws://127.0.0.1:%d/ws" % port, open_timeout=1.0) as ws:
                await recv_until(ws, {"sys.hello"}, timeout=3.0)
                return
        except Exception:
            await asyncio.sleep(0.2)
    raise AssertionError("server did not become ready on port %d" % port)


async def run_case(port, out):
    url = "ws://127.0.0.1:%d/ws" % port

    async with connect(url) as payer, connect(url) as spectator:
        hello = await recv_until(payer, {"sys.hello"})
        risk = await recv_until(payer, {"sys.risk_warning"})
        out.append("AC-S1 hello rooms=%s v=%s" % (hello["payload"]["rooms"], hello["payload"]["v"]))
        out.append("AC-S6 risk persistent=%s text_len=%d" % (risk["payload"]["persistent"], len(risk["payload"]["text"])))

        await recv_until(spectator, {"sys.risk_warning"})

        await payer.send(json.dumps({"type": "room.subscribe", "payload": {"room": "lobby"}}))
        await recv_until(payer, {"sys.notice"})
        await spectator.send(json.dumps({"type": "room.subscribe", "payload": {"room": "lobby"}}))
        await recv_until(spectator, {"sys.notice"})

        # 2. spectator cannot speak
        await spectator.send(json.dumps({
            "type": "chat.send",
            "room": "lobby",
            "payload": {"text": "spectator attempt"},
        }))
        rej = await recv_until(spectator, {"sec.reject"})
        assert rej["payload"]["code"] == "E_ENTRANCE_REQUIRED", rej
        out.append("AC-S2 spectator send refused code=%s" % rej["payload"]["code"])

        # 3. paying client granted then speaks
        await payer.send(json.dumps({"type": "pay.grant_sandbox", "payload": {}}))
        grant = await recv_until(payer, {"pay.grant_sandbox"})
        assert grant["payload"]["granted"] is True and grant["payload"]["mock"] is True, grant
        out.append("AC-S3 grant mock=%s" % grant["payload"]["mock"])

        sent_at = time.monotonic()
        await payer.send(json.dumps({
            "type": "chat.send",
            "room": "lobby",
            "payload": {"text": "sandbox interop: payer to room", "client_msg_id": "interop-1"},
        }))
        cast_payer = await recv_until(payer, {"chat.broadcast"})
        cast_spec = await recv_until(spectator, {"chat.broadcast"})
        rtt_ms = (time.monotonic() - sent_at) * 1000.0
        assert cast_spec["payload"]["text"] == "sandbox interop: payer to room", cast_spec
        assert cast_payer.get("evt_id") and cast_spec.get("evt_id") == cast_payer.get("evt_id"), (cast_payer, cast_spec)
        out.append("AC-S3 broadcast delivered to 2 connections rtt_ms=%.1f evt_id=%s" % (rtt_ms, cast_payer["evt_id"]))
        assert rtt_ms <= 500.0, "round trip over 500ms: %.1f" % rtt_ms

        # 4. server-authoritative AI flag
        assert cast_spec.get("ai_generated") is False, cast_spec
        out.append("AC-S5 ai_generated=%s actor=%s" % (cast_spec.get("ai_generated"), cast_spec.get("actor")))

        # 5. content gate refuses and never broadcasts
        with open(os.path.join(BASE, "config.json"), "r", encoding="utf-8") as fh:
            forbidden = json.load(fh)["gate"]["forbidden_words"][0]
        await payer.send(json.dumps({
            "type": "chat.send",
            "room": "lobby",
            "payload": {"text": "blocked word: " + forbidden},
        }))
        rej2 = await recv_until(payer, {"sec.reject"})
        assert rej2["payload"]["code"] == "E_CONTENT_REJECTED", rej2
        out.append("AC-S4 blocked word refused code=%s and not broadcast" % rej2["payload"]["code"])
        try:
            leaked = await recv_until(spectator, {"chat.broadcast"}, timeout=1.0)
        except (AssertionError, asyncio.TimeoutError):
            # A silent room is the pass: the rejected text never broadcast.
            leaked = None
        assert leaked is None, "gate leak: %s" % leaked
        out.append("AC-S4 no broadcast leaked to spectator")


async def main_async(args):
    port = free_port()
    tmp = tempfile.mkdtemp(prefix="lobby-interop-")
    db = os.path.join(tmp, "events.db")
    proc = subprocess.Popen(
        [sys.executable, SERVER, "--host", "127.0.0.1", "--port", str(port), "--db", db,
         "--city-http-port", str(free_port()), "--ping-interval", "30", "--ping-timeout", "60"],
        cwd=BASE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    out = []
    ok = False
    try:
        await wait_ready(port)
        await run_case(port, out)
        ok = True
    except Exception as exc:  # honest failure, never a silent pass
        out.append("FAIL %s: %s" % (type(exc).__name__, exc))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    lines = [
        "LOBBY INTEROP %s round=%s port=%d db=%s" % ("PASS" if ok else "FAIL", args.label, port, db),
    ] + ["  " + line for line in out]
    body = "\n".join(lines) + "\n"
    print(body, end="")
    if args.log:
        os.makedirs(os.path.dirname(os.path.abspath(args.log)), exist_ok=True)
        with open(args.log, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
    return 0 if ok else 2


def main():
    parser = argparse.ArgumentParser(description="Lobby sandbox two-client interop proof")
    parser.add_argument("--label", default="sandbox")
    parser.add_argument("--log", default=None)
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())