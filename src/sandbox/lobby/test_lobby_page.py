"""Suite for the P-47-1b browser lobby face (lobby_page.py + lobby.html).

Six criteria, each read off a REAL server process and a REAL WebSocket client:

  AC-LBP1  GET /lobby/ answers 200 text/html with bytes identical to the page on
           disk, the page makes no external reference, and it is big enough to
           be a client rather than a stub.
  AC-LBP2  the served page carries all three standing surfaces verbatim: the AI
           generated label, the non-advice note, and the mock/no-real-charge
           statement.
  AC-LBP3  GET /lobby and GET /lobby/ are the same bytes; GET /lobby/api/config
           answers the REAL WebSocket port of this server and the /ws path;
           an unknown path answers 404 and a POST answers 405.
  AC-LBP4  the frames the page actually sends are accepted by the shipped
           server: hello and risk arrive first, a spectator send is refused with
           E_ENTRANCE_REQUIRED, the sandbox grant answers mock=true, and the
           next send is broadcast to a second connection with one shared evt_id.
  AC-LBP5  page and module hygiene: the page carries no BOM and no CRLF, and the
           serving module is pure ASCII.
  AC-LBP6  the server wires the face: --web-port prints the lobby_page URL with
           the real bound port and the real ws port, and the registry carries
           the os-lobby-lobby-page suite row.
"""

import hashlib
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
        self.city_port = free_port()
        self.tmp = tempfile.mkdtemp(prefix="lobby-page-")
        self.db = os.path.join(self.tmp, "events.db")
        argv = [sys.executable, SERVER,
                "--host", "127.0.0.1",
                "--port", str(self.ws_port),
                "--db", self.db,
                "--city-http-port", str(self.city_port),
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
    from websockets.sync.client import connect  # noqa: F401  (proves the lib)
    return json.loads(ws.recv(timeout=timeout))


def main():
    for path, what in ((PAGE, "page"), (MODULE, "module")):
        if not os.path.exists(path):
            print("FAIL AC-LBP1 %s missing on disk: %s" % (what, path))
            print("SUITE FAIL 0/6")
            return 1

    with open(PAGE, "rb") as fh:
        disk_bytes = fh.read()

    failed = 0
    leg = None
    ws_out = ws_peer = None
    try:
        leg = Leg()
        base = leg.base()

        # ---------------- AC-LBP1 ----------------
        try:
            status, ctype, body = http_get(base + "/lobby/")
            assert status == 200, "GET /lobby/ status=%s" % status
            assert "text/html" in ctype.lower(), "content-type=%s" % ctype
            assert len(body) > 3000, "page too small: %dB" % len(body)
            assert b"http://" not in body, "page reaches the network over http"
            assert b"https://" not in body, "page reaches the network over https"
            assert b'src="//' not in body, "protocol-relative reference present"
            assert body == disk_bytes, "served bytes differ from the file on disk"
            print("PASS AC-LBP1 status=200 type=text/html bytes=%d offline=True same_as_disk=True"
                  % len(body))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-LBP1 :: %s" % exc)

        # ---------------- AC-LBP2 ----------------
        try:
            status, _, body = http_get(base + "/lobby/")
            text = body.decode("utf-8")
            assert AI_LABEL in text, "AI generated label missing"
            assert RISK_NOTE in text, "non-advice note missing"
            assert MOCK_NOTE in text, "mock / no-real-charge statement missing"
            print("PASS AC-LBP2 aigc_label=True risk_note=True mock_note=True")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-LBP2 :: %s" % exc)

        # ---------------- AC-LBP3 ----------------
        try:
            a_status, _, a = http_get(base + "/lobby")
            b_status, _, b = http_get(base + "/lobby/")
            assert a_status == 200 and b_status == 200, (a_status, b_status)
            assert a == b == disk_bytes, "slash forms or disk bytes disagree"
            cfg_status, cfg_type, cfg_body = http_get(base + "/lobby/api/config")
            assert cfg_status == 200, "config status=%s" % cfg_status
            assert "application/json" in cfg_type.lower(), "config type=%s" % cfg_type
            cfg = json.loads(cfg_body.decode("utf-8"))
            assert cfg.get("ws_port") == leg.ws_port, (
                "config ws_port=%s real=%s" % (cfg.get("ws_port"), leg.ws_port))
            assert cfg.get("ws_path") == "/ws", "config ws_path=%s" % cfg.get("ws_path")
            code, _, _ = http_get(base + "/lobby/nope")
            assert code == 404, "unknown GET answered %s" % code
            pcode, _ = http_post(base + "/lobby/")
            assert pcode == 405, "POST answered %s, expected 405" % pcode
            print("PASS AC-LBP3 identical=True ws_port_matches=True unknown=404 post=405")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-LBP3 :: %s" % exc)

        # ---------------- AC-LBP4 ----------------
        try:
            from websockets.sync.client import connect
            ws_out = connect(leg.ws_url())
            ws_peer = connect(leg.ws_url())
            first = recv_frame(ws_out)
            second = recv_frame(ws_out)
            assert first.get("type") == "sys.hello", "first frame=%s" % first.get("type")
            assert second.get("type") == "sys.risk_warning", (
                "second frame=%s" % second.get("type"))
            # the peer connection carries its own hello + risk before anything else
            peer_first = recv_frame(ws_peer)
            peer_second = recv_frame(ws_peer)
            assert peer_first.get("type") == "sys.hello", (
                "peer first frame=%s" % peer_first.get("type"))
            assert peer_second.get("type") == "sys.risk_warning", (
                "peer second frame=%s" % peer_second.get("type"))
            # frames exactly as the page sends them
            ws_out.send(json.dumps({"type": "room.subscribe", "payload": {"room": "lobby"}}))
            ws_peer.send(json.dumps({"type": "room.subscribe", "payload": {"room": "lobby"}}))
            ws_out.send(json.dumps({
                "v": 1, "type": "chat.send", "room": "lobby",
                "payload": {"text": "page interop before entrance"},
                "client_msg_id": "page-1"}))
            refused = recv_frame(ws_out)
            while refused.get("type") == "sys.notice":
                refused = recv_frame(ws_out)
            assert refused.get("type") == "sec.reject", "refusal type=%s" % refused.get("type")
            assert refused["payload"]["code"] == "E_ENTRANCE_REQUIRED", (
                "refusal code=%s" % refused["payload"]["code"])
            ws_out.send(json.dumps({"v": 1, "type": "pay.grant_sandbox", "room": "lobby",
                                    "payload": {}}))
            grant = recv_frame(ws_out)
            assert grant.get("type") == "pay.grant_sandbox", "grant type=%s" % grant.get("type")
            assert grant["payload"].get("mock") is True, "grant is not marked mock"
            assert grant["payload"].get("granted") is True, "grant not granted"
            ws_out.send(json.dumps({
                "v": 1, "type": "chat.send", "room": "lobby",
                "payload": {"text": "page interop after entrance"},
                "client_msg_id": "page-2"}))
            cast_out = recv_frame(ws_out)
            assert cast_out.get("type") == "chat.broadcast", "cast type=%s" % cast_out.get("type")
            cast_peer = recv_frame(ws_peer)
            while cast_peer.get("type") == "sys.notice":
                cast_peer = recv_frame(ws_peer)
            assert cast_peer.get("type") == "chat.broadcast", "peer cast type=%s" % cast_peer.get("type")
            assert cast_out.get("evt_id") and cast_out.get("evt_id") == cast_peer.get("evt_id"), (
                "evt_id not shared: %s vs %s" % (cast_out.get("evt_id"), cast_peer.get("evt_id")))
            assert cast_out.get("ai_generated") is False, "server-authoritative flag moved"
            print("PASS AC-LBP4 hello_risk_first=True spectator_refused=E_ENTRANCE_REQUIRED "
                  "grant_mock=True broadcast_shared=True")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-LBP4 :: %s" % exc)
        except Exception as exc:  # noqa: BLE001 - a lost connection is a failed criterion
            failed += 1
            print("FAIL AC-LBP4 :: %s: %s" % (type(exc).__name__, exc))

        # ---------------- AC-LBP5 ----------------
        try:
            assert not disk_bytes.startswith(b"\xef\xbb\xbf"), "page carries a BOM"
            assert b"\r\n" not in disk_bytes, "page carries CRLF line endings"
            with open(MODULE, "rb") as fh:
                module_bytes = fh.read()
            module_bytes.decode("ascii")
            print("PASS AC-LBP5 bom=False crlf=0 ascii_module=True page_sha16=%s"
                  % hashlib.sha256(disk_bytes).hexdigest()[:16].upper())
        except (AssertionError, UnicodeDecodeError) as exc:
            failed += 1
            print("FAIL AC-LBP5 :: %s" % exc)

        # ---------------- AC-LBP6 ----------------
        try:
            assert "lobby_page=" in leg.banner, "banner carries no lobby_page line"
            assert "lobby_page=http://127.0.0.1:%d/lobby/" % leg.web_port in leg.banner, (
                "banner url does not name the bound port")
            assert "ws_port=%d" % leg.ws_port in leg.banner, "banner does not publish the ws port"
            with open(REGISTRY, encoding="utf-8") as fh:
                registry = fh.read()
            assert "os-lobby-lobby-page" in registry, "registry carries no suite row"
            print("PASS AC-LBP6 banner_url=True ws_port=True wired=True")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-LBP6 :: %s" % exc)

    finally:
        for conn in (ws_out, ws_peer):
            if conn is not None:
                try:
                    conn.close()
                except Exception:  # noqa: BLE001
                    pass
        if leg is not None:
            leg.close()

    total = 6
    if failed:
        print("SUITE FAIL %d/%d" % (total - failed, total))
        return 1
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())