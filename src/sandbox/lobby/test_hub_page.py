"""Suite for the sandbox entry face (hub_page.py + hub.html).

Nine criteria plus AC-HUB10, each read off a REAL server process and the ports
it actually bound (AC-HUB1..AC-HUB6 were pre-registered in src/os/backlog.md at
R2462 BEFORE this module, the page and this suite existed; AC-HUB7 was
pre-registered in the R3332 backlog row, AC-HUB8 in the R3336 row, AC-HUB9 in
the R3337 row, AC-HUB10 in the R3338 row and AC-HUB12 in the R3343 row, each
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
           entry per published face. R3349 re-pinned the boot-trigger reading
           from a count of the literal to the LIST of statement-level calls,
           proven on a page copy with a second call appended.
  AC-HUB10 the dead-face cost is the connect budget, not the HTTP budget
           (R3338 measured a closed loopback port hanging to its timeout
           instead of refusing - 363ms at 0.35s, 155ms at 0.15s, stable over
           repeats): the SAME closed port is read twice, once with the connect
           budget restored to the whole 1.5s (the old shape, must cost more
           than 1.4s) and once as shipped (must cost less than 0.4s), both
           answering dead; a face that accepts and stays silent still reads
           dead AND still costs its read budget, so the split shortens the
           dead path without trading away sensitivity; the four verdicts
           (200 / 503 / closed / non-root) are unchanged and a live face
           answers inside 100ms; the connect-only path is held to the same law
           (dead port 155ms shipped against 1507ms with the shared budget), and
           eight dead faces through the shipped live_map cost under 400ms.
  AC-HUB11 the body can never overturn the verdict (R3341 measured the answer
           phase from four loopback worlds: splitting it into a short header
           budget read a silent face in 152/307/511ms but also read a face that
           needs 700ms to say anything at all as dead, while the shipped shape
           read it live in 701ms - that trade is refused because a dead face
           and a slow-but-legitimate face cost the same currency): a face that
           answers 200 text/html and streams (or stalls) its body is LIVE, the
           stalled body is bounded, a face that never answers is still dead and
           still costs its read budget, and a face that needs 350ms to answer
           is still live so the header phase keeps the whole budget.
  AC-HUB12 every face the hub can publish is reachable from the page (R3343
           counted the payload's eight face ids against the page's seven cards:
           the missing one was the entrance gate, which the R3332 click chain
           made the FIRST step of the 19.9 flow - 403 E_ENTRANCE_REQUIRED):
           build_faces with all eight ports reads a card, a link anchor and a
           wire() consumer for each id, the gate card is wiring-real, and the
           SAME parser over a copy with the gate card/anchor/read removed reads
           covered=7/8 naming gate - so the reading decides, not a constant.
           The standing page laws are re-read in the same arm (no autotimer,
           exactly two fetch calls) so this card cannot cost AC-HUB9.
  AC-HUB13 the page never shows a previous verdict as current (R3344 read the
           page's probe path: the cards start on "检测中", but probe() only
           repainted them in the success callback, so a re-check left the old
           verdicts on screen for the whole probe - a silent face costs about
           1.0-1.5s, which is long enough to read a face that just died as
           live): show_probing() puts every card back to "检测中" and must be
           called INSIDE probe() and BEFORE the probing request; the silent
           face is still dead and still costs its read budget (the refused
           short header budget is not reintroduced); and the same reading over
           a copy with the call dropped or moved after the request reddens, so
           the order law is load-bearing.
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


def boot_triggers(page):
    """Every statement-level probe() trigger in `page`, in file order.

    The law is "the boot path triggers the probing read once"; a count of the
    literal cannot say WHICH call appeared, and a bare count reddens on any
    edit without naming what changed. The list does both.
    """
    return re.findall(r"^[ \t]*(probe\(\);)[ \t]*$", page, re.M)


LIST_READ = "/hub/api/faces"
PROBE_READ = "/hub/api/faces?probe=1"
FETCH_RE = re.compile(r"fetch\(\s*'([^']*)'")


def fetch_sites(page):
    """Every endpoint the page reads, in file order.

    The law is "the page reads the face list and the probing read, and nothing
    else"; a count of the literal 'fetch(' cannot say WHICH endpoint appeared,
    so an added read would redden without naming the URL that did it.
    """
    return FETCH_RE.findall(page)


def probing_decls(page):
    """Every definition site of the probing label, by its line text."""
    return re.findall(r"^[ \t]*(function show_probing\(\) \{)[ \t]*$", page, re.M)


def probing_calls(page):
    """Every statement-level call of the probing label, in file order."""
    return re.findall(r"^[ \t]*(show_probing\(\);)[ \t]*$", page, re.M)


def page_cover(text, faces):
    """Which published faces the page really exposes: card, anchor, wire().

    AC-HUB12: the three parts are separate on purpose - a card with no anchor
    is a dead promise, an anchor with no wire() keeps a literal '#', and a
    wire() read with no card prints the URL to nobody.
    """
    covered = 0
    missing, unlinked, unwired = [], [], []
    for face in faces:
        has_card = ('data-face="%s"' % face) in text
        has_link = ('id="link-%s"' % face) in text
        has_wire = ("data.%s" % face) in text
        if has_card and has_link and has_wire:
            covered += 1
        if not has_card:
            missing.append(face)
        if not has_link:
            unlinked.append(face)
        if not has_wire:
            unwired.append(face)
    return covered, missing, unlinked, unwired


def probe_order(text, call="show_probing();",
                request="fetch('/hub/api/faces?probe=1'"):
    """(True, "") when the label call is inside probe() and before the request.

    AC-HUB13 needs the ORDER, not just the presence: a call after the request
    (or outside probe()) leaves the previous verdict on screen while a re-check
    is in flight, which is exactly the stale reading this card forbids.
    """
    fn = text.find("function probe()")
    if fn < 0:
        return False, "no probe()"
    idx = text.find(call)
    if idx < 0:
        return False, "no %s" % call.strip()
    if text.find(call, idx + 1) >= 0:
        return False, "%s appears more than once" % call.strip()
    req = text.find(request)
    if req < 0:
        return False, "no probing request"
    if idx < fn:
        return False, "%s sits before probe()" % call.strip()
    if idx > req:
        return False, "%s sits after the probing request" % call.strip()
    return True, ""


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


class _SlowBodyFace(_Face):
    """A face that answers 200 html at once and streams the body late."""

    delay = 1.0

    def do_GET(self):
        body = b"<html><body>ok</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.flush()
        time.sleep(self.delay)
        try:
            self.wfile.write(body)
        except OSError:
            # the probe closes as soon as the verdict is known, so a stalled
            # body legitimately loses its client; this is the fixture's own
            # thread, not a reading.
            pass


def serve_slow_body(delay=1.0):
    handler = type("SlowBody%s" % str(delay).replace(".", "_"),
                   (_SlowBodyFace,), {"delay": delay})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    return httpd, "http://127.0.0.1:%d/" % port, port


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
            fetches = fetch_sites(page)
            assert sorted(fetches) == sorted([LIST_READ, PROBE_READ]), (
                "page reads %r, expected the list read and the probe read"
                % (fetches,))
            plain_at = page.index("\n  fetch('/hub/api/faces'")
            triggers = boot_triggers(page)
            assert triggers == ["probe();"], (
                "the boot path triggers the probing read %d times (%r)"
                % (len(triggers), triggers))
            doubled = boot_triggers(page + "\n  probe();\n")
            assert doubled == ["probe();", "probe();"], (
                "the trigger reader missed a second boot call: %r" % (doubled,))
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
            print("PASS AC-HUB9 timers=0 fetches=2 triggers=%d plain_first=True "
                  "refresh_wired=True plain_ms=%.0f live_entries=%d"
                  % (len(triggers), plain_ms, len(ports)))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-HUB9 :: %s" % exc)

        # ---------------- AC-HUB10 ----------------
        silent_srv = ok200c = bad503c = deep_c = None
        try:
            # four verdicts, unchanged from R3332/R3336/R3337
            ok200c, url200c, port200c = serve_face(200)
            bad503c, url503c, port503c = serve_face(503)
            deep_c, deep_url_c, deep_port_c = serve_deep("/deep/")
            closed_c = free_port()
            closed_url_c = "http://127.0.0.1:%d/" % closed_c
            silent_srv, silent_url, silent_port = serve_slow(3.0)

            verdicts = {
                "ok": hub_page.face_serves(url200c),
                "bad": hub_page.face_serves(url503c),
                "closed": hub_page.face_serves(closed_url_c),
                "deep": hub_page.face_serves(deep_url_c),
            }
            assert verdicts == {"ok": True, "bad": False, "closed": False,
                                "deep": True}, "verdicts=%r" % (verdicts,)
            assert http_get("http://127.0.0.1:%d/" % deep_port_c)[0] == 404, (
                "the deep face port root is not 404")

            # the same dead port, old shape against shipped shape
            started = time.perf_counter()
            old_shape = hub_page.face_serves(closed_url_c, connect_timeout=1.5)
            old_ms = (time.perf_counter() - started) * 1000.0
            started = time.perf_counter()
            new_shape = hub_page.face_serves(closed_url_c)
            new_ms = (time.perf_counter() - started) * 1000.0
            assert old_shape is False and new_shape is False, (
                "a dead face must read dead on both shapes: old=%s new=%s"
                % (old_shape, new_shape))
            assert old_ms > 1400.0, (
                "the old shape cost %.0fms, so the split is not what saves time"
                % old_ms)
            assert new_ms < 400.0, "the shipped shape still costs %.0fms" % new_ms

            # sensitivity is not traded: accepts, never answers -> still dead,
            # still costs the read budget
            started = time.perf_counter()
            silent_read = hub_page.face_serves(silent_url, timeout=1.0)
            silent_ms = (time.perf_counter() - started) * 1000.0
            assert silent_read is False, "a silent face was read as serving"
            assert silent_ms >= 700.0, (
                "a silent face cost %.0fms, so the read budget was cut too"
                % silent_ms)

            started = time.perf_counter()
            live_ok = hub_page.face_serves(url200c)
            live_ms = (time.perf_counter() - started) * 1000.0
            assert live_ok is True and live_ms < 100.0, (
                "a live face read %s in %.0fms" % (live_ok, live_ms))

            # the connect-only path carries the same budget law
            started = time.perf_counter()
            live_new = hub_page.face_live("127.0.0.1", closed_c)
            live_new_ms = (time.perf_counter() - started) * 1000.0
            started = time.perf_counter()
            live_old = hub_page.face_live("127.0.0.1", closed_c, timeout=1.5)
            live_old_ms = (time.perf_counter() - started) * 1000.0
            assert live_new is False and live_old is False, (
                "live readings=%s/%s" % (live_new, live_old))
            assert live_new_ms < 400.0, (
                "the shipped connect budget costs %.0fms" % live_new_ms)
            assert live_old_ms > 1400.0, (
                "the shared budget costs %.0fms, so the split is not the saving"
                % live_old_ms)

            # eight dead faces through the shipped map: the hub poll itself
            dead_ports = dict(("f%d" % idx, free_port()) for idx in range(8))
            started = time.perf_counter()
            dead_map = hub_page.live_map({"face_ports": dead_ports}, "127.0.0.1")
            dead_map_ms = (time.perf_counter() - started) * 1000.0
            assert len(dead_map) == 8 and not any(dead_map.values()), (
                "dead map=%r" % (dead_map,))
            assert dead_map_ms < 400.0, (
                "eight dead faces cost %.0fms through the shipped map" % dead_map_ms)

            print("PASS AC-HUB10 verdicts=ok:True bad:False closed:False deep:True "
                  "dead_old_ms=%.0f dead_new_ms=%.0f silent=%s/%.0fms live=%.0fms "
                  "connect_old_ms=%.0f connect_new_ms=%.0f map8_dead_ms=%.0f"
                  % (old_ms, new_ms, silent_read, silent_ms, live_ms,
                     live_old_ms, live_new_ms, dead_map_ms))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-HUB10 :: %s" % exc)
        finally:
            for srv in (ok200c, bad503c, deep_c, silent_srv):
                if srv is not None:
                    srv.shutdown()
                    srv.server_close()

        # ---------------- AC-HUB11 ----------------
        body_srv = staller_srv = silent2_srv = slowhead_srv = None
        try:
            # (a) the body cannot overturn the verdict: a face that answered
            # 200 html at once and streams late is LIVE, not dead.
            body_srv, body_url, body_port = serve_slow_body(1.0)
            started = time.perf_counter()
            body_read = hub_page.face_serves(body_url, timeout=0.6)
            body_ms = (time.perf_counter() - started) * 1000.0
            assert body_read is True, (
                "a face that answered 200 html read live=%s - the body "
                "overturned the verdict" % body_read)

            # (b) the strongest form of the same defect: headers arrive, the
            # body never does. Its status line and type are the whole law.
            staller_srv, staller_url, staller_port = serve_slow_body(5.0)
            started = time.perf_counter()
            staller_read = hub_page.face_serves(staller_url, timeout=0.6)
            staller_ms = (time.perf_counter() - started) * 1000.0
            assert staller_read is True, (
                "a face that answered 200 html and stalled its body read "
                "live=%s" % staller_read)
            assert staller_ms < 1400.0, (
                "the stalled body cost %.0fms, so it was not bounded" % staller_ms)

            # (c) sensitivity is NOT traded: accepts and never answers -> dead
            # and still costs its read budget (same currency as AC-HUB10).
            silent2_srv, silent2_url, silent2_port = serve_slow(3.0)
            started = time.perf_counter()
            silent2_read = hub_page.face_serves(silent2_url, timeout=1.0)
            silent2_ms = (time.perf_counter() - started) * 1000.0
            assert silent2_read is False, "a silent face was read as serving"
            assert silent2_ms >= 700.0, (
                "a silent face cost %.0fms, so a header budget was introduced"
                % silent2_ms)

            # (d) the header phase keeps the WHOLE budget: a face needs 350ms
            # before it says anything and is still live (a short header budget
            # would kill it - measured in the R3341 probe, refused).
            slowhead_srv, slowhead_url, slowhead_port = serve_slow(0.35)
            started = time.perf_counter()
            slowhead_read = hub_page.face_serves(slowhead_url, timeout=1.5)
            slowhead_ms = (time.perf_counter() - started) * 1000.0
            assert slowhead_read is True, (
                "a face that needed %.0fms to answer read dead - the header "
                "budget was cut" % slowhead_ms)

            print("PASS AC-HUB11 body=live/%.0fms stalled_body=live/%.0fms "
                  "silent=%s/%.0fms slowhead=live/%.0fms"
                  % (body_ms, staller_ms, silent2_read, silent2_ms,
                     slowhead_ms))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-HUB11 :: %s" % exc)
        finally:
            for srv in (body_srv, staller_srv, silent2_srv, slowhead_srv):
                if srv is not None:
                    srv.shutdown()
                    srv.server_close()

    finally:
        if leg is not None:
            leg.close()

    # ---------------- AC-HUB12 ----------------
    try:
        # (a) coverage: every face the hub CAN publish is on the page
        all_faces = hub_page.build_faces(
            "127.0.0.1", free_port(), web_port=free_port(),
            city_port=free_port(), checkout_port=free_port(),
            gate_port=free_port(), ledger_port=free_port(),
            ugc_port=free_port(), panel_port=free_port(),
            member_port=free_port())
        published = sorted(all_faces["face_ports"])
        page_text = disk_bytes.decode("utf-8")
        covered, missing, unlinked, unwired = page_cover(page_text, published)
        # The law is coverage of whatever the hub publishes, not a count of
        # eight: a ninth face is growth, so dropping one port must remove
        # exactly that face from the published set and the page must still
        # cover the rest - a count could never say which face moved.
        assert published, "the hub published no faces, so coverage is vacuous"
        shrunk_faces = hub_page.build_faces(
            "127.0.0.1", free_port(), web_port=free_port(),
            city_port=free_port(), checkout_port=free_port(),
            gate_port=free_port(), ledger_port=free_port(),
            ugc_port=free_port(), panel_port=free_port(), member_port=None)
        shrunk = sorted(shrunk_faces["face_ports"])
        assert set(shrunk) == set(published) - {"member"}, (
            "dropping member_port reads published=%r, expected %r"
            % (shrunk, sorted(set(published) - {"member"})))
        s_covered, s_missing, s_unlinked, s_unwired = page_cover(
            page_text, shrunk)
        assert not (s_missing or s_unlinked or s_unwired), (
            "the shrunk face set is not covered: missing=%s unlinked=%s "
            "unwired=%s" % (s_missing, s_unlinked, s_unwired))
        assert not missing, "no card for published face(s): %s" % (missing,)
        assert not unlinked, "no link anchor for: %s" % (unlinked,)
        assert not unwired, "wire() never reads data.<face> for: %s" % (unwired,)

        # (b) the gate card is wiring-real and its fallback is honest
        assert 'id="link-gate"' in page_text, "gate anchor id missing"
        assert 'id="link-gate" href="#"' in page_text, (
            "the gate anchor does not start on a literal #")
        assert "data.gate" in page_text, "wire() does not consume data.gate"

        # (c) negative control: the same parser over a page with gate removed
        hole = page_text.replace('data-face="gate"', 'data-face="gate-x"')
        hole = hole.replace('id="link-gate"', 'id="link-gate-x"')
        hole = hole.replace("data.gate", "data.GATE_OFF")
        h_covered, h_missing, _, _ = page_cover(hole, published)
        assert h_missing == ["gate"], (
            "the hole read missing=%r, so the reading is not load-bearing"
            % (h_missing,))
        assert h_covered == len(published) - 1, (
            "hole covered=%d of %d" % (h_covered, len(published)))

        # (d) this card must not cost the standing page laws
        assert not re.search(r"setInterval|setTimeout|requestAnimationFrame",
                             page_text), "an autotimer appeared on the page"
        sites = fetch_sites(page_text)
        assert sorted(sites) == sorted([LIST_READ, PROBE_READ]), (
            "page reads %r, expected exactly the list read and the probe "
            "read" % (sites,))
        # load-bearing: an unknown endpoint is named, not merely counted
        extra = page_text.replace(
            "fetch('/hub/api/faces', { cache: 'no-store' })",
            "fetch('/hub/api/faces', { cache: 'no-store' });"
            " fetch('/hub/api/other');", 1)
        strangers = [u for u in fetch_sites(extra)
                     if u not in (LIST_READ, PROBE_READ)]
        assert strangers == ["/hub/api/other"], (
            "an added read reads strangers=%r" % (strangers,))

        print("PASS AC-HUB12 covered=%d/%d shrunk=%d/%d gate_card=True "
              "hole=%d/%d hole_missing=%s timers=0 reads=%s"
              % (covered, len(published), s_covered, len(shrunk), h_covered,
                 len(published), ",".join(h_missing), ",".join(sites)))
    except AssertionError as exc:
        failed += 1
        print("FAIL AC-HUB12 :: %s" % exc)

    # ---------------- AC-HUB13 ----------------
    try:
        # (a) the label call is inside probe() and BEFORE the probing fetch, so
        # no stale verdict can stay on screen while a re-check is in flight.
        labelled, why = probe_order(disk_bytes.decode("utf-8"))
        assert labelled, "the probing label is not ordered before the request: %s" % why

        # (b) the cost is not traded away: a silent face is still dead and
        # still costs its read budget, printed next to the stale windows.
        silent3_srv, silent3_url, silent3_port = serve_slow(3.0)
        try:
            faces = {"silent": silent3_url, "face_ports": {"silent": silent3_port}}
            started = time.perf_counter()
            live = hub_page.live_map(faces, "127.0.0.1")
            silent3_ms = (time.perf_counter() - started) * 1000.0
            assert live.get("silent") is False, (
                "a silent face was read as live by live_map: %r" % (live,))
            assert silent3_ms >= 1000.0, (
                "a silent face cost %.0fms, so a header budget was introduced"
                % silent3_ms)
        finally:
            silent3_srv.shutdown()
            silent3_srv.server_close()

        # (c) load-bearing: removing the call, or moving it after the request,
        # must redden the same reading - the order law is not a constant.
        page_text13 = disk_bytes.decode("utf-8")
        dropped = page_text13.replace("    show_probing();\n", "", 1)
        # moved: the same call put back as a statement AFTER the request, at the
        # end of probe() - an inline splice would not be a page that runs, so
        # the mutant is the real placement the order law is about.
        moved = dropped.replace(
            "      .catch(function () {\n"
            "        offline();\n"
            "        refresh.disabled = false;\n"
            "      });\n"
            "  }\n",
            "      .catch(function () {\n"
            "        offline();\n"
            "        refresh.disabled = false;\n"
            "      });\n"
            "    show_probing();\n"
            "  }\n", 1)
        dropped_ok, dropped_why = probe_order(dropped)
        moved_ok, moved_why = probe_order(moved)
        assert dropped_ok is False, "a page with no label call still read ordered"
        assert moved_ok is False, "a page with the label after the request still read ordered"
        defs = probing_decls(moved)
        calls = probing_calls(moved)
        assert defs == probing_decls(page_text13), (
            "the moved copy changed the label definition: %r" % (defs,))
        assert calls == probing_calls(page_text13) == ["show_probing();"], (
            "label call sites shipped=%r moved=%r" % (
                probing_calls(page_text13), calls))
        # load-bearing: a second statement-level call is named, not counted
        twice = page_text13.replace(
            "    show_probing();\n",
            "    show_probing();\n    show_probing();\n", 1)
        assert probing_calls(twice) == ["show_probing();", "show_probing();"], (
            "a page with two label calls reads %r"
            % (probing_calls(twice),))

        # (d) the standing page laws stay intact
        assert not re.search(r"setInterval|setTimeout|requestAnimationFrame",
                             page_text13), "an autotimer appeared on the page"
        reads13 = fetch_sites(page_text13)
        assert sorted(reads13) == sorted([LIST_READ, PROBE_READ]), (
            "page reads %r, expected the list read and the probe read"
            % (reads13,))
        assert "marks[i].textContent = '检测中'" in page_text13, (
            "show_probing() does not put the cards back to their probing label")

        print("PASS AC-HUB13 ordered=True calls=%d silent=dead/%.0fms "
              "stale_before=%.0fms stale_after=0ms dropped=%s moved=%s "
              "timers=0 reads=%s"
              % (len(calls), silent3_ms, silent3_ms, dropped_why or "red",
                 moved_why or "red", ",".join(reads13)))
    except AssertionError as exc:
        failed += 1
        print("FAIL AC-HUB13 :: %s" % exc)

    total = 13
    if failed:
        print("SUITE FAIL %d/%d" % (total - failed, total))
        return 1
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())