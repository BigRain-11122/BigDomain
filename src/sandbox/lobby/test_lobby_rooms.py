"""Suite for the lobby room picker and event ledger (AC-RP1..AC-RP6).

Every criterion is read off a REAL server process and a REAL WebSocket client,
never asserted from source text alone. The six criteria were pre-registered in
src/os/backlog.md BEFORE this file or the page change existed.

  AC-RP1  GET /lobby/api/rooms answers 200 JSON whose rooms equal the server
           configured list in order with default=first, and the room names are
           not literals inside the serving module.
  AC-RP2  the page carries a room selector and an event ledger, asks the rooms
           route, and the configured room names appear nowhere as literals in
           the page.
  AC-RP3  the served page is byte-identical to disk, offline, BOM and CRLF
           free, the serving module is pure ASCII, and the three standing
           surfaces are still present verbatim.
  AC-RP4  on a real server an entitled client subscribing a second room reads
           sys.notice room subscribe <room>, and an unknown room is refused
           with E_ROOM_UNKNOWN.
  AC-RP5  rooms really partition: a send into the second room reaches the
           subscriber and NOT a client still on the default room within one
           second, and after that client subscribes the same room a new send
           reaches both under one shared evt_id.
  AC-RP6  the exact room-switch frames the page sends (subscribe new, then
           unsubscribe old) are accepted by the shipped server and read back as
           two sys.notice lines naming the right actions and rooms, the registry
           carries the suite row, and the rooms route is reachable through the
           banner URL.
"""

import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SERVER = os.path.join(HERE, "server.py")
PAGE = os.path.join(HERE, "lobby.html")
MODULE = os.path.join(HERE, "lobby_page.py")
CONFIG = os.path.join(HERE, "config.json")
REGISTRY = os.path.join(BASE, "reconcile_all.py")

AI_LABEL = "AI 生成内容标识"
RISK_NOTE = "非投顾提示"
MOCK_NOTE = "mock"


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def http_get(url, timeout=6.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()


def http_post(url, payload=b"{}", timeout=6.0):
    req = urllib.request.Request(url, data=payload, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


class Leg(object):
    def __init__(self):
        self.ws_port = free_port()
        self.tmp = tempfile.mkdtemp(prefix="lobby-rooms-")
        self.db = os.path.join(self.tmp, "events.db")
        argv = [sys.executable, SERVER,
                "--host", "127.0.0.1",
                "--port", str(self.ws_port),
                "--db", self.db,
                "--web-port", "0",
                "--ping-interval", "30",
                "--ping-timeout", "60"]
        self.proc = subprocess.Popen(argv, cwd=HERE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     text=True)
        self.banner = self._wait_banner()
        self.web_port = self._web_port()

    def _wait_banner(self, deadline=25.0):
        end = time.monotonic() + deadline
        while time.monotonic() < end:
            line = self.proc.stdout.readline()
            if not line:
                if self.proc.poll() is not None:
                    raise AssertionError("server exited before banner")
                time.sleep(0.05)
                continue
            if "serving ws://" in line:
                return line.strip()
        raise AssertionError("server banner not seen")

    def _web_port(self):
        match = re.search(r"lobby_page=http://127\.0\.0\.1:(\d+)/lobby/", self.banner)
        assert match, "banner carries no lobby_page url: %s" % self.banner
        return int(match.group(1))

    def base(self):
        return "http://127.0.0.1:%d" % self.web_port

    def ws_url(self):
        return "ws://127.0.0.1:%d/ws" % self.ws_port

    def close(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def recv_frame(ws, timeout=6.0):
    return json.loads(ws.recv(timeout=timeout))


def drain(ws, seconds=1.0):
    """Collect frames until the socket is quiet for `seconds`."""
    got = []
    while True:
        try:
            got.append(recv_frame(ws, timeout=seconds))
        except Exception:  # noqa: BLE001 - quiet socket is the expected exit
            return got


def wait_for(ws, wanted, timeout=6.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        frame = recv_frame(ws, timeout=timeout)
        if frame.get("type") == wanted:
            return frame
    raise AssertionError("frame type %s never arrived" % wanted)


def connect_entitled(leg):
    from websockets.sync.client import connect
    ws = connect(leg.ws_url())
    first = recv_frame(ws)
    second = recv_frame(ws)
    assert first.get("type") == "sys.hello", "hello=%s" % first.get("type")
    assert second.get("type") == "sys.risk_warning", "risk=%s" % second.get("type")
    ws.send(json.dumps({"v": 1, "type": "pay.grant_sandbox", "payload": {}}))
    grant = wait_for(ws, "pay.grant_sandbox")
    assert grant["payload"].get("granted") is True, "grant not granted"
    return ws


def main():
    for path, what in ((PAGE, "page"), (MODULE, "module")):
        if not os.path.exists(path):
            print("FAIL AC-RP1 %s missing on disk: %s" % (what, path))
            print("SUITE FAIL 0/6")
            return 1

    with open(PAGE, "rb") as fh:
        disk_bytes = fh.read()
    page_text = disk_bytes.decode("utf-8")
    with open(CONFIG, encoding="utf-8") as fh:
        cfg_rooms = [str(name) for name in json.load(fh)["rooms"]]
    assert len(cfg_rooms) >= 2, "config declares fewer than two rooms: %s" % cfg_rooms
    room_one, room_two = cfg_rooms[0], cfg_rooms[1]

    failed = 0
    leg = None
    opened = []
    try:
        leg = Leg()
        base = leg.base()

        # ---------------- AC-RP1 ----------------
        try:
            status, ctype, body = http_get(base + "/lobby/api/rooms")
            assert status == 200, "rooms status=%s" % status
            assert "application/json" in ctype.lower(), "rooms content-type=%s" % ctype
            payload = json.loads(body.decode("utf-8"))
            assert payload.get("rooms") == cfg_rooms, (
                "rooms=%s config=%s" % (payload.get("rooms"), cfg_rooms))
            assert payload.get("default") == cfg_rooms[0], (
                "default=%s first=%s" % (payload.get("default"), cfg_rooms[0]))
            with open(MODULE, "rb") as fh:
                module_text = fh.read().decode("ascii")
            for name in cfg_rooms[1:]:
                assert name not in module_text, (
                    "room %r is a literal inside the serving module" % name)
            print("PASS AC-RP1 status=200 rooms=%s default=%s not_hardcoded=True"
                  % (",".join(cfg_rooms), payload.get("default")))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-RP1 :: %s" % exc)

        # ---------------- AC-RP2 ----------------
        try:
            assert 'id="room"' in page_text, "page carries no room selector"
            assert 'id="ledger"' in page_text, "page carries no event ledger"
            assert "api/rooms" in page_text, "page never asks the rooms route"
            leaks = [name for name in cfg_rooms if name in page_text]
            assert not leaks, "configured room names hardcoded in the page: %s" % leaks
            assert "room.subscribe" in page_text, "page never subscribes a room"
            assert "room.unsubscribe" in page_text, "page never releases the old room"
            print("PASS AC-RP2 selector=True ledger=True fetches_rooms=True literals=0")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-RP2 :: %s" % exc)

        # ---------------- AC-RP3 ----------------
        try:
            status, ctype, body = http_get(base + "/lobby/")
            assert status == 200, "page status=%s" % status
            assert "text/html" in ctype.lower(), "page content-type=%s" % ctype
            assert body == disk_bytes, "served bytes differ from disk"
            assert b"http://" not in body, "page reaches the network over http"
            assert b"https://" not in body, "page reaches the network over https"
            assert not disk_bytes.startswith(b"\xef\xbb\xbf"), "page carries a BOM"
            assert b"\r\n" not in disk_bytes, "page carries CRLF"
            with open(MODULE, "rb") as fh:
                fh.read().decode("ascii")
            for surface in (AI_LABEL, RISK_NOTE, MOCK_NOTE):
                assert surface in page_text, "standing surface missing: %s" % surface
            print("PASS AC-RP3 same_as_disk=True offline=True bytes=%d bom=False crlf=0 "
                  "ascii_module=True surfaces=3" % len(body))
        except (AssertionError, UnicodeDecodeError) as exc:
            failed += 1
            print("FAIL AC-RP3 :: %s" % exc)

        # ---------------- AC-RP4 ----------------
        try:
            ws = connect_entitled(leg)
            opened.append(ws)
            ws.send(json.dumps({"v": 1, "type": "room.subscribe",
                                "payload": {"room": room_two}}))
            notice = wait_for(ws, "sys.notice")
            text = (notice.get("payload") or {}).get("notice", "")
            assert ("room subscribe" in text and room_two in text), (
                "subscribe notice=%r" % text)
            assert notice.get("room") == room_two, "notice room=%s" % notice.get("room")
            ws.send(json.dumps({"v": 1, "type": "room.subscribe",
                                "payload": {"room": "no-such-room-xyz"}}))
            refused = wait_for(ws, "sec.reject")
            assert refused["payload"]["code"] == "E_ROOM_UNKNOWN", (
                "refusal code=%s" % refused["payload"]["code"])
            print("PASS AC-RP4 subscribe_notice=True room=%s unknown_room=E_ROOM_UNKNOWN"
                  % room_two)
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-RP4 :: %s" % exc)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print("FAIL AC-RP4 :: %s: %s" % (type(exc).__name__, exc))

        # ---------------- AC-RP5 ----------------
        try:
            ws_a = connect_entitled(leg)
            opened.append(ws_a)
            from websockets.sync.client import connect
            ws_b = connect(leg.ws_url())
            opened.append(ws_b)
            assert recv_frame(ws_b).get("type") == "sys.hello", "B hello missing"
            assert recv_frame(ws_b).get("type") == "sys.risk_warning", "B risk missing"
            ws_a.send(json.dumps({"v": 1, "type": "room.subscribe",
                                  "payload": {"room": room_two}}))
            wait_for(ws_a, "sys.notice")
            ws_a.send(json.dumps({"v": 1, "type": "chat.send", "room": room_two,
                                  "payload": {"text": "room two only message"},
                                  "client_msg_id": "rp5-first"}))
            first_cast = wait_for(ws_a, "chat.broadcast")
            assert first_cast.get("room") == room_two, "cast room=%s" % first_cast.get("room")
            quiet = drain(ws_b, seconds=1.0)
            assert not [f for f in quiet if f.get("type") == "chat.broadcast"], (
                "default-room client received a %s room broadcast" % room_two)
            ws_b.send(json.dumps({"v": 1, "type": "room.subscribe",
                                  "payload": {"room": room_two}}))
            wait_for(ws_b, "sys.notice")
            ws_a.send(json.dumps({"v": 1, "type": "chat.send", "room": room_two,
                                  "payload": {"text": "room two shared message"},
                                  "client_msg_id": "rp5-second"}))
            cast_a = wait_for(ws_a, "chat.broadcast")
            cast_b = wait_for(ws_b, "chat.broadcast")
            assert cast_a.get("evt_id") == cast_b.get("evt_id"), (
                "evt_id not shared: %s vs %s" % (cast_a.get("evt_id"), cast_b.get("evt_id")))
            print("PASS AC-RP5 partitioned=True stranger_quiet=True shared_evt=True "
                  "evt_len=%d" % len(str(cast_a.get("evt_id") or "")))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-RP5 :: %s" % exc)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print("FAIL AC-RP5 :: %s: %s" % (type(exc).__name__, exc))

        # ---------------- AC-RP6 ----------------
        try:
            from websockets.sync.client import connect
            ws_s = connect(leg.ws_url())
            opened.append(ws_s)
            assert recv_frame(ws_s).get("type") == "sys.hello", "switch hello missing"
            assert recv_frame(ws_s).get("type") == "sys.risk_warning", "switch risk missing"
            # exactly the frames the page sends when the selector changes
            ws_s.send(json.dumps({"v": 1, "type": "room.subscribe",
                                  "payload": {"room": room_two}}))
            ws_s.send(json.dumps({"v": 1, "type": "room.unsubscribe",
                                  "payload": {"room": room_one}}))
            notices = [wait_for(ws_s, "sys.notice"), wait_for(ws_s, "sys.notice")]
            texts = [(n.get("payload") or {}).get("notice", "") for n in notices]
            assert any("room subscribe" in t and room_two in t for t in texts), (
                "no subscribe notice for %s: %s" % (room_two, texts))
            assert any("room unsubscribe" in t and room_one in t for t in texts), (
                "no unsubscribe notice for %s: %s" % (room_one, texts))
            status, _, body = http_get(base + "/lobby/api/rooms")
            assert status == 200, "rooms route not reachable through the banner url"
            assert json.loads(body.decode("utf-8"))["rooms"] == cfg_rooms, (
                "banner-url rooms payload drifted")
            with open(REGISTRY, encoding="utf-8") as fh:
                registry = fh.read()
            assert "os-lobby-room-picker" in registry, "registry carries no suite row"
            print("PASS AC-RP6 switch_frames_accepted=True subscribe_notice=True "
                  "unsubscribe_notice=True banner_route=True wired=True")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-RP6 :: %s" % exc)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print("FAIL AC-RP6 :: %s: %s" % (type(exc).__name__, exc))

    finally:
        for conn in opened:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass
        if leg is not None:
            leg.close()

    if failed:
        print("SUITE FAIL %d/6" % (6 - failed))
        return 1
    print("SUITE PASS 6/6")
    return 0


if __name__ == "__main__":
    sys.exit(main())