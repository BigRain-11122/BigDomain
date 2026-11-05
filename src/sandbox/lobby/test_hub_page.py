"""Suite for the sandbox entry face (hub_page.py + hub.html).

Six criteria, each read off a REAL server process and the ports it actually
bound (AC-HUB1..AC-HUB6 were pre-registered in src/os/backlog.md at R2462
BEFORE this module, the page and this suite existed):

  AC-HUB1  GET /hub/ answers 200 text/html with bytes identical to the page on
           disk, bigger than 2000 bytes, and the page makes no external
           reference.
  AC-HUB2  the served page carries all three standing surfaces verbatim (AI
           generated label, non-advice note, mock/no-real-charge statement)
           plus the read-only statement.
  AC-HUB3  GET /hub and GET /hub/ are the same bytes; GET /hub/api/faces
           answers 200 application/json; an unknown path answers 404 and a POST
           answers 405.
  AC-HUB4  the published face URLs are ROUTE-REAL - lobby carries the REAL
           bound web port and /lobby/, city carries the REAL bound city port
           and /city/, checkout carries the declared checkout port and
           /checkout/, the ws port is published, and the payload marks every
           object mock=true chargeable=false.
  AC-HUB5  the page carries no BOM and no CRLF and the serving module is pure
           ASCII.
  AC-HUB6  server.py wires the face: --hub-port prints
           hub=http://127.0.0.1:<real bound port>/hub/ in the banner and the
           registry carries the os-sandbox-hub suite row.
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
PAGE = os.path.join(HERE, "hub.html")
MODULE = os.path.join(HERE, "hub_page.py")
REGISTRY = os.path.join(BASE, "reconcile_all.py")

AI_LABEL = "AI 生成内容标识"
RISK_NOTE = "非投顾提示"
MOCK_NOTE = "mock"
READ_ONLY = "只读入口页"


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
        self.checkout_port = free_port()
        self.tmp = tempfile.mkdtemp(prefix="sandbox-hub-")
        self.db = os.path.join(self.tmp, "events.db")
        argv = [sys.executable, SERVER,
                "--host", "127.0.0.1",
                "--port", str(self.ws_port),
                "--db", self.db,
                "--city-http-port", str(self.city_port),
                "--web-port", "0",
                "--hub-port", "0",
                "--checkout-port", str(self.checkout_port),
                "--ping-interval", "30",
                "--ping-timeout", "60"]
        self.proc = subprocess.Popen(argv, cwd=HERE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     text=True)
        self.banner = self._wait_banner()
        self.hub_port = self._hub_port()
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

    def _hub_port(self):
        match = re.search(r"hub=http://127\.0\.0\.1:(\d+)/hub/", self.banner)
        assert match, "banner carries no hub url: %s" % self.banner
        return int(match.group(1))

    def _web_port(self):
        match = re.search(r"lobby_page=http://127\.0\.0\.1:(\d+)/lobby/", self.banner)
        assert match, "banner carries no lobby_page url: %s" % self.banner
        return int(match.group(1))

    def base(self):
        return "http://127.0.0.1:%d" % self.hub_port

    def close(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def main():
    for path, what in ((PAGE, "page"), (MODULE, "module")):
        if not os.path.exists(path):
            print("FAIL AC-HUB1 %s missing on disk: %s" % (what, path))
            print("SUITE FAIL 0/6")
            return 1

    with open(PAGE, "rb") as fh:
        disk_bytes = fh.read()

    failed = 0
    leg = None
    try:
        leg = Leg()
        base = leg.base()

        # ---------------- AC-HUB1 ----------------
        try:
            status, ctype, body = http_get(base + "/hub/")
            assert status == 200, "GET /hub/ status=%s" % status
            assert "text/html" in ctype.lower(), "content-type=%s" % ctype
            assert len(body) > 2000, "page too small: %dB" % len(body)
            assert b"http://" not in body, "page reaches the network over http"
            assert b"https://" not in body, "page reaches the network over https"
            assert b'src="//' not in body, "protocol-relative reference present"
            assert body == disk_bytes, "served bytes differ from the file on disk"
            print("PASS AC-HUB1 status=200 type=text/html bytes=%d offline=True same_as_disk=True"
                  % len(body))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-HUB1 :: %s" % exc)

        # ---------------- AC-HUB2 ----------------
        try:
            status, _, body = http_get(base + "/hub/")
            text = body.decode("utf-8")
            for label in (AI_LABEL, RISK_NOTE, MOCK_NOTE, READ_ONLY):
                assert label in text, "standing surface missing: %s" % label
            print("PASS AC-HUB2 aigc_label=True risk_note=True mock_note=True read_only=True")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-HUB2 :: %s" % exc)

        # ---------------- AC-HUB3 ----------------
        try:
            a_status, _, a = http_get(base + "/hub")
            b_status, _, b = http_get(base + "/hub/")
            assert a_status == 200 and b_status == 200, (a_status, b_status)
            assert a == b == disk_bytes, "slash forms or disk bytes disagree"
            f_status, f_type, f_body = http_get(base + "/hub/api/faces")
            assert f_status == 200, "faces status=%s" % f_status
            assert "application/json" in f_type.lower(), "faces type=%s" % f_type
            faces = json.loads(f_body.decode("utf-8"))
            code, _, _ = http_get(base + "/hub/nope")
            assert code == 404, "unknown GET answered %s" % code
            pcode, _ = http_post(base + "/hub/")
            assert pcode == 405, "POST answered %s, expected 405" % pcode
            print("PASS AC-HUB3 identical=True faces_json=True unknown=404 post=405")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-HUB3 :: %s" % exc)

        # ---------------- AC-HUB4 ----------------
        try:
            _, _, body = http_get(base + "/hub/api/faces")
            faces = json.loads(body.decode("utf-8"))
            expect = {
                "lobby": "http://127.0.0.1:%d/lobby/" % leg.web_port,
                "city": "http://127.0.0.1:%d/city/" % leg.city_port,
                "checkout": "http://127.0.0.1:%d/checkout/" % leg.checkout_port,
                "ws": "ws://127.0.0.1:%d/ws" % leg.ws_port,
            }
            for key, url in expect.items():
                assert faces.get(key) == url, "%s=%r expected %r" % (key, faces.get(key), url)
            assert faces.get("ws_port") == leg.ws_port, "ws_port=%r" % faces.get("ws_port")
            assert faces.get("ws_path") == "/ws", "ws_path=%r" % faces.get("ws_path")
            assert faces.get("mock") is True, "mock flag missing"
            assert faces.get("chargeable") is False, "chargeable flag missing"
            assert faces.get("checkout_note"), "checkout note missing"
            assert "checkout_demo.py" in faces["checkout_note"], "checkout note names no process"
            print("PASS AC-HUB4 lobby_port=True city_port=True checkout_port=True "
                  "ws_port=True mock=True chargeable=False")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-HUB4 :: %s" % exc)

        # ---------------- AC-HUB5 ----------------
        try:
            assert not disk_bytes.startswith(b"\xef\xbb\xbf"), "page carries a BOM"
            assert b"\r\n" not in disk_bytes, "page carries CRLF line endings"
            with open(MODULE, "rb") as fh:
                module_bytes = fh.read()
            module_bytes.decode("ascii")
            print("PASS AC-HUB5 bom=False crlf=0 ascii_module=True page_sha16=%s"
                  % hashlib.sha256(disk_bytes).hexdigest()[:16].upper())
        except (AssertionError, UnicodeDecodeError) as exc:
            failed += 1
            print("FAIL AC-HUB5 :: %s" % exc)

        # ---------------- AC-HUB6 ----------------
        try:
            assert "hub=http://127.0.0.1:%d/hub/" % leg.hub_port in leg.banner, (
                "banner hub url does not name the bound port: %s" % leg.banner)
            assert "checkout_port=%d" % leg.checkout_port in leg.banner, (
                "banner does not publish the checkout port")
            with open(REGISTRY, encoding="utf-8") as fh:
                registry = fh.read()
            assert "os-sandbox-hub" in registry, "registry carries no suite row"
            print("PASS AC-HUB6 banner_url=True checkout_port=True wired=True")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-HUB6 :: %s" % exc)

    finally:
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