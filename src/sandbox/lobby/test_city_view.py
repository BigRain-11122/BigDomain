"""Acceptance suite: the city view page (BigDomain R2457, product window).

Pins AC-CV1..AC-CV6 (pre-registered in src/os/backlog.md at R2457 BEFORE
this suite and the page existed).

The read-only city HTTP face used to answer JSON only, so nothing about
the silicon city was openable in a browser. This suite proves the shipped
page is served by the SAME handler, reads ONLY the two existing endpoints,
keeps the wire contract unchanged, and fails honestly when the snapshot
package is absent.

Two real-server legs, both on a private port and a temp database:
  leg A - shipped city_data: page + wire contract + one source of truth
  leg B - an empty city dir: /city/ still served, /city/snapshot 503

Usage: python test_city_view.py
"""

import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(BASE, "server.py")
VIEW = os.path.join(BASE, "city_view.html")
RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

AI_LABEL = "AI 生成内容"
RISK_NOTE = "非投资建议"
NOT_READY = "城市快照暂未就绪"


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


def wait_ready(city_port, deadline=25.0):
    end = time.monotonic() + deadline
    last = None
    while time.monotonic() < end:
        try:
            status, _, body = http_get("http://127.0.0.1:%d/city/" % city_port,
                                       timeout=1.0)
            if status == 200 and body:
                return
            last = "status=%s" % status
        except Exception as exc:  # server still booting
            last = "%s: %s" % (type(exc).__name__, exc)
        time.sleep(0.2)
    raise AssertionError("city http face not ready: %s" % last)


class Leg(object):
    def __init__(self, city_dir=None):
        self.ws_port = free_port()
        self.city_port = free_port()
        self.tmp = tempfile.mkdtemp(prefix="lobby-cityview-")
        self.db = os.path.join(self.tmp, "events.db")
        argv = [sys.executable, SERVER,
                "--host", "127.0.0.1",
                "--port", str(self.ws_port),
                "--db", self.db,
                "--city-http-port", str(self.city_port),
                "--ping-interval", "30",
                "--ping-timeout", "60"]
        if city_dir:
            argv += ["--city-dir", city_dir]
        self.proc = subprocess.Popen(argv, cwd=BASE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     text=True)

    def base(self):
        return "http://127.0.0.1:%d" % self.city_port

    def close(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def main():
    if not os.path.exists(VIEW):
        print("FAIL AC-CV1 page missing on disk: %s" % VIEW)
        print("SUITE FAIL 0/6")
        return 1

    with open(VIEW, "rb") as fh:
        disk_bytes = fh.read()

    failed = 0
    legs = []
    try:
        # ---------------- leg A: shipped city data ----------------
        leg = Leg()
        legs.append(leg)
        wait_ready(leg.city_port)
        base = leg.base()

        # AC-CV1: page is served, self-contained
        try:
            status, ctype, body = http_get(base + "/city/")
            assert status == 200, "GET /city/ status=%s" % status
            assert "text/html" in ctype.lower(), "content-type=%s" % ctype
            assert len(body) > 1000, "page too small: %dB" % len(body)
            assert b"http://" not in body, "page reaches the network over http"
            assert b"https://" not in body, "page reaches the network over https"
            assert b'src="//' not in body, "protocol-relative reference present"
            print("PASS AC-CV1 status=200 type=text/html bytes=%d offline=True"
                  % len(body))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-CV1 :: %s" % exc)

        # AC-CV2: both standing compliance surfaces ride in the served page
        try:
            status, _, body = http_get(base + "/city/")
            text = body.decode("utf-8")
            assert AI_LABEL in text, "AIGC label missing from the served page"
            assert RISK_NOTE in text, "non-advice note missing from the served page"
            print("PASS AC-CV2 aigc_label=True risk_note=True")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-CV2 :: %s" % exc)

        # AC-CV3: the wire contract is unchanged - JSON in, no write verb
        try:
            status, ctype, body = http_get(base + "/city/snapshot")
            assert status == 200, "snapshot status=%s" % status
            assert "application/json" in ctype.lower(), "snapshot type=%s" % ctype
            snap = json.loads(body.decode("utf-8"))
            assert snap.get("as_of"), "snapshot lost its as_of key"
            assert isinstance(snap.get("city"), dict), "snapshot lost its city block"
            code, _ = http_post(base + "/city/")
            assert code == 405, "POST /city/ answered %s, expected 405" % code
            code2, _, _ = http_get(base + "/city/nope")
            assert code2 == 404, "unknown GET answered %s, expected 404" % code2
            cs, _, cbody = http_get(base + "/census/B-00231")
            assert cs == 200, "census read answered %s" % cs
            assert json.loads(cbody.decode("utf-8")).get("found") is True
            print("PASS AC-CV3 snapshot=json post=405 unknown=404 census=200")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-CV3 :: %s" % exc)

        # AC-CV4: /city and /city/ are the same bytes, and they are the file
        try:
            a_status, _, a = http_get(base + "/city")
            b_status, _, b = http_get(base + "/city/")
            assert a_status == 200 and b_status == 200, (a_status, b_status)
            assert a == b, "slash and non-slash forms differ"
            assert a == disk_bytes, "served bytes differ from disk bytes"
            print("PASS AC-CV4 identical=True bytes=%d sha16=%s"
                  % (len(a), hashlib.sha256(a).hexdigest()[:16].upper()))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-CV4 :: %s" % exc)

        # AC-CV6 (a): page hygiene + wiring, measured on the real files
        try:
            assert not disk_bytes.startswith(b"\xef\xbb\xbf"), "page has a BOM"
            assert b"\r" not in disk_bytes, "page is not LF-only"
            text = disk_bytes.decode("utf-8")
            assert NOT_READY in text, "page lost its not-ready line"
            assert "/city/snapshot" in text and "/census/" in text, \
                "page does not read through the two existing paths"
            with open(os.path.join(BASE, "city.py"), "rb") as fh:
                src = fh.read()
            assert b"city_view.html" in src, "handler does not name the page"
            assert src.isascii(), "city.py is not ASCII source"
            with open(RECONCILE, encoding="utf-8") as fh:
                registry = fh.read()
            assert '"os-lobby-city-view"' in registry, "suite not wired"
            print("PASS AC-CV6 bom=False crlf=0 ascii_src=True wired=True")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-CV6 :: %s" % exc)

        leg.close()
        legs.remove(leg)

        # ---------------- leg B: empty city dir, honest failure ----------------
        empty = tempfile.mkdtemp(prefix="lobby-cityview-empty-")
        leg2 = Leg(city_dir=empty)
        legs.append(leg2)
        try:
            wait_ready(leg2.city_port)
            base2 = leg2.base()
            s_page, _, page = http_get(base2 + "/city/")
            s_snap, _, snap_body = http_get(base2 + "/city/snapshot")
            assert s_page == 200, "page not served without a snapshot: %s" % s_page
            assert page == disk_bytes, "page bytes differ without a snapshot"
            assert s_snap == 503, "missing snapshot answered %s, expected 503" % s_snap
            err = json.loads(snap_body.decode("utf-8"))
            assert "error" in err, "503 body carries no error key"
            assert NOT_READY in page.decode("utf-8"), "page has no not-ready line"
            print("PASS AC-CV5 page=200 snapshot=503 not_ready_line=True")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-CV5 :: %s" % exc)
    finally:
        for leg in legs:
            try:
                leg.close()
            except Exception:
                pass

    total = 6
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())