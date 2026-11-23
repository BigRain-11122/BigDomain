"""Suite for the sandbox entry face (hub_page.py + hub.html).

Seven criteria plus AC-HUB8, each read off a REAL server process and the ports
it actually bound (AC-HUB1..AC-HUB6 were pre-registered in src/os/backlog.md at
R2462 BEFORE this module, the page and this suite existed; AC-HUB7 was
pre-registered in the R3332 backlog row and AC-HUB8 in the R3336 row, both
before their code landed):

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
  AC-HUB7  a listening port that cannot serve its page is NOT live: three
           in-process servers (200 html, 503 html, closed port) are asked by
           face_serves and face_live, and the old connect-only reading is
           printed beside the new one so the difference is a reading, not a
           claim.
  AC-HUB8  the eight published faces are read CONCURRENTLY (R3336 measured the
           published paths answer 200 directly while each port root answers 404,
           so the URL is used as published and no route is guessed): three real
           faces that sleep 0.6s each read alive, the same world with
           workers=1 costs at least 1.5s of wall time, the shipped default
           costs under 1.2s, and 200/503/closed/non-root verdicts are
           unchanged.
  AC-HUB9  the page asks on load and on the button, never on a timer (R3337
           measured zero autotimers, a dead face costing its whole timeout -
           357ms on the connect reading, 1500ms on the HTTP reading - against
           1.1ms for a pool of eight threads, so the cost is the dead face and
           not the threads): the page carries no setInterval/setTimeout/
           requestAnimationFrame, exactly two fetch calls with the unprobed
           list issued BEFORE the probing one, and the refresh control wired to
           the same probe; measured, the unprobed list carries no live key and
           answers inside half a second, while the probing read carries one
           entry per published face.
"""

import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.append(HERE)

import hub_page  # noqa: E402  (AC-HUB7 asks the shipped probe itself)
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


class _Face(BaseHTTPRequestHandler):
    """The smallest possible face: one status, one html body, no state."""

    code = 200
    body = b"<!doctype html><title>face</title><p>face</p>"

    def do_GET(self):
        self.send_response(self.code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(self.body)))
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, *args):
        pass


def serve_face(code):
    """A loopback face answering `code`; returns (server, url, port)."""
    handler = type("Face%d" % code, (_Face,), {"code": code})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    return httpd, "http://127.0.0.1:%d/" % port, port


class _SlowFace(_Face):
    """A face that takes its time before it answers (a hanging face)."""

    delay = 0.6

    def do_GET(self):
        time.sleep(self.delay)
        _Face.do_GET(self)


def serve_slow(delay=0.6):
    handler = type("SlowFace%s" % str(delay).replace(".", "_"), (_SlowFace,),
                   {"delay": delay})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    return httpd, "http://127.0.0.1:%d/" % port, port


class _DeepFace(_Face):
    """A face whose page lives on a non-root route and whose root is 404."""

    route = "/deep/"

    def do_GET(self):
        if self.path == type(self).route:
            _Face.do_GET(self)
            return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args):
        pass


def serve_deep(route="/deep/"):
    handler = type("DeepFace", (_DeepFace,), {"route": route})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    return httpd, "http://127.0.0.1:%d%s" % (port, route), port


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
            print("SUITE FAIL 0/7")
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

        # ---------------- AC-HUB7 ----------------
        ok200 = bad503 = None
        try:
            ok200, url200, port200 = serve_face(200)
            bad503, url503, port503 = serve_face(503)
            closed_port = free_port()
            closed_url = "http://127.0.0.1:%d/" % closed_port

            serves200 = hub_page.face_serves(url200)
            serves503 = hub_page.face_serves(url503)
            serves_closed = hub_page.face_serves(closed_url)
            live503 = hub_page.face_live("127.0.0.1", port503)
            live_closed = hub_page.face_live("127.0.0.1", closed_port)

            assert serves200 is True, "a 200 html face read not serving"
            assert serves503 is False, "a 503 face read serving"
            assert serves_closed is False, "a closed port read serving"
            assert live503 is True, "connect-only reading cannot see the 503"
            assert live_closed is False, "connect-only reading called a dead port live"
            print("PASS AC-HUB7 serves=200:%s 503:%s closed:%s | "
                  "connect_only=503:%s closed:%s live_diff=%s"
                  % (serves200, serves503, serves_closed, live503, live_closed,
                     (serves503 != live503)))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-HUB7 :: %s" % exc)
        finally:
            for srv in (ok200, bad503):
                if srv is not None:
                    srv.shutdown()
                    srv.server_close()

        # ---------------- AC-HUB8 ----------------
        slow_servers = []
        try:
            slow_servers = [serve_slow(0.6) for _ in range(3)]
            faces = {"face_ports": {}}
            for idx, (_, url, port) in enumerate(slow_servers):
                faces["face%d" % idx] = url
                faces["face_ports"]["face%d" % idx] = port
            started = time.time()
            parallel = hub_page.live_map(faces, "127.0.0.1")
            parallel_s = round(time.time() - started, 3)
            started = time.time()
            serial = hub_page.live_map(faces, "127.0.0.1", workers=1)
            serial_s = round(time.time() - started, 3)

            assert parallel == {"face0": True, "face1": True, "face2": True}, (
                "parallel readings=%r" % (parallel,))
            assert serial == parallel, "serial readings differ: %r" % (serial,)
            assert parallel_s < 1.2, "parallel wall time %.3fs >= 1.2s" % parallel_s
            assert serial_s >= 1.5, "serial wall time %.3fs < 1.5s" % serial_s

            # verdicts are unchanged by the concurrency: 200 / 503 / closed /
            # non-root route (published path used, port root is 404).
            ok200b, url200b, port200b = serve_face(200)
            bad503b, url503b, port503b = serve_face(503)
            closed_port = free_port()
            deep, deep_url, deep_port = serve_deep("/deep/")
            wrote = {
                "ok": url200b, "bad": url503b,
                "closed": "http://127.0.0.1:%d/" % closed_port,
                "deep": deep_url,
            }
            ports = {"ok": port200b, "bad": port503b, "closed": closed_port,
                     "deep": deep_port}
            verdicts = hub_page.live_map(
                {"face_ports": ports, "ok": wrote["ok"], "bad": wrote["bad"],
                 "closed": wrote["closed"], "deep": wrote["deep"]},
                "127.0.0.1")
            root_status = http_get("http://127.0.0.1:%d/" % deep_port)[0]
            assert verdicts == {"ok": True, "bad": False, "closed": False,
                                "deep": True}, "verdicts=%r" % (verdicts,)
            assert root_status == 404, "deep face port root answered %s" % root_status
            print("PASS AC-HUB8 parallel_ms=%.0f serial_ms=%.0f slow=3x0.6s "
                  "verdicts=ok:True bad:False closed:False deep:True "
                  "deep_root=404" % (parallel_s * 1000.0, serial_s * 1000.0))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-HUB8 :: %s" % exc)
        finally:
            for srv in slow_servers:
                srv[0].shutdown()
                srv[0].server_close()
            # serve_face/serve_deep unpack to (server, url, port), so these
            # names hold the SERVERS themselves.
            for srv in (locals().get("ok200b"), locals().get("bad503b"),
                        locals().get("deep")):
                if srv is not None:
                    srv.shutdown()
                    srv.server_close()

        # ---------------- AC-HUB9 ----------------
        try:
            page = disk_bytes.decode("utf-8")
            timers = sum(page.count(name) for name in
                         ("setInterval", "setTimeout", "requestAnimationFrame"))
            assert timers == 0, "page carries %d auto-timer mentions" % timers
            fetches = page.count("fetch(")
            assert fetches == 2, "page issues %d fetch calls, expected 2" % fetches
            plain_at = page.index("\n  fetch('/hub/api/faces'")
            assert page.count("probe();") == 1, (
                "the probing read is not triggered exactly once in the boot path")
            assert plain_at < page.index("probe();"), (
                "the boot path triggers the probing read before the plain answer")
            assert 'id="refresh"' in page, "page carries no refresh control"
            assert "refresh.addEventListener('click', probe)" in page, (
                "the refresh control is not wired to the same probe")

            started = time.perf_counter()
            status, ctype, plain_body = http_get(base + "/hub/api/faces")
            plain_ms = (time.perf_counter() - started) * 1000.0
            assert status == 200 and "application/json" in ctype.lower(), (status, ctype)
            plain = json.loads(plain_body.decode("utf-8"))
            assert "live" not in plain, "the unprobed list already carries live readings"
            assert plain_ms < 500, "the unprobed list took %.0fms" % plain_ms

            _, _, probed_body = http_get(base + "/hub/api/faces?probe=1")
            probed = json.loads(probed_body.decode("utf-8"))
            ports = probed.get("face_ports") or {}
            assert set(probed.get("live") or {}) == set(ports), (
                "probing read covers %r against published %r"
                % (sorted(probed.get("live") or {}), sorted(ports)))
            print("PASS AC-HUB9 timers=0 fetches=2 plain_first=True refresh_wired=True "
                  "plain_ms=%.0f live_entries=%d" % (plain_ms, len(ports)))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-HUB9 :: %s" % exc)

    finally:
        if leg is not None:
            leg.close()

    total = 9
    if failed:
        print("SUITE FAIL %d/%d" % (total - failed, total))
        return 1
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())