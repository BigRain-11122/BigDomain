"""Suite for the content-gate console (gate_page.py + gate.html).

Six criteria, each read off a REAL server process (AC-GC1..AC-GC6 were
pre-registered in src/os/backlog.md at R2467 BEFORE this module, the page and
this suite existed):

  AC-GC1  GET /gate/ answers 200 text/html with bytes identical to the page on
           disk, bigger than 2000 bytes, and the page makes no external
           reference (no http://, https:// or protocol-relative src).
  AC-GC2  the served page carries the three standing surfaces verbatim (AI
           generated label, non-advice note, mock/no-real-charge statement)
           plus the honest statement that the real msgSecCheck waits on the CEO
           physical item.
  AC-GC3  GET /gate/api/contract answers 200 application/json equal to
           msgsec_stub.contract() asked at CALL time, with blocked_on naming
           the physical item.
  AC-GC4  POST /gate/api/check drives the SHIPPED stub - plain text reads
           pass/100/SERVE, a word from the LIVE config forbidden list reads
           risky/20001/REFUSE, a word from the LIVE advisory list reads
           review/20002/REVIEW, every response carries a 32-char trace_id with
           mock=true and billable=false, and no configured word appears as a
           literal in the serving module.
  AC-GC5  GET /gate and /gate/ are the same bytes; unknown path 404 for GET and
           POST; a non-POST method on the check route 405; blank content 400
           with its own code and an over-length body answered 413 without
           reaching the gate.
  AC-GC6  the page carries no BOM and no CRLF, the serving module is pure ASCII
           with no clock import, the banner publishes
           gate=http://127.0.0.1:<real bound port>/gate/, the hub payload lists
           the gate face, and the registry carries the suite row.
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
PAGE = os.path.join(HERE, "gate.html")
MODULE = os.path.join(HERE, "gate_page.py")
STUB = os.path.join(HERE, "msgsec_stub.py")
CONFIG = os.path.join(HERE, "config.json")
REGISTRY = os.path.join(BASE, "reconcile_all.py")

sys.path.insert(0, HERE)
import msgsec_stub  # noqa: E402

AI_LABEL = "AI 生成内容标识"
RISK_NOTE = "非投顾提示"
MOCK_NOTE = "mock"
PHYSICAL = "CEO 物理件"


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


def http_call(url, method, payload=None, raw=None, timeout=6.0):
    data = raw if raw is not None else (
        json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else b"")
    req = urllib.request.Request(url, data=data, method=method,
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
        self.tmp = tempfile.mkdtemp(prefix="sandbox-gate-")
        self.db = os.path.join(self.tmp, "events.db")
        argv = [sys.executable, SERVER,
                "--host", "127.0.0.1",
                "--port", str(self.ws_port),
                "--db", self.db,
                "--city-http-port", str(self.city_port),
                "--web-port", "0",
                "--hub-port", "0",
                "--gate-port", "0",
                "--ping-interval", "30",
                "--ping-timeout", "60"]
        self.proc = subprocess.Popen(argv, cwd=HERE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     text=True)
        self.banner = self._wait_banner()
        self.gate_port = self._match_port(r"gate=http://127\.0\.0\.1:(\d+)/gate/", "gate")
        self.hub_port = self._match_port(r"hub=http://127\.0\.0\.1:(\d+)/hub/", "hub")

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

    def _match_port(self, pattern, what):
        match = re.search(pattern, self.banner)
        assert match, "banner carries no %s url: %s" % (what, self.banner)
        return int(match.group(1))

    def base(self):
        return "http://127.0.0.1:%d" % self.gate_port

    def close(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def main():
    for path, what in ((PAGE, "page"), (MODULE, "module")):
        if not os.path.exists(path):
            print("FAIL AC-GC1 %s missing on disk: %s" % (what, path))
            print("SUITE FAIL 0/6")
            return 1

    with open(PAGE, "rb") as fh:
        disk_bytes = fh.read()
    with open(CONFIG, encoding="utf-8") as fh:
        cfg = json.load(fh)
    forbidden = list(cfg["gate"]["forbidden_words"])
    advisory = list(cfg["gate"]["advisory_ban_words"])
    max_len = int(cfg.get("max_text_len", 2000))

    failed = 0
    leg = None
    try:
        leg = Leg()
        base = leg.base()

        # ---------------- AC-GC1 ----------------
        try:
            status, ctype, body = http_get(base + "/gate/")
            assert status == 200, "GET /gate/ status=%s" % status
            assert "text/html" in ctype.lower(), "content-type=%s" % ctype
            assert len(body) > 2000, "page too small: %dB" % len(body)
            assert b"http://" not in body, "page reaches the network over http"
            assert b"https://" not in body, "page reaches the network over https"
            assert b'src="//' not in body, "protocol-relative reference present"
            assert body == disk_bytes, "served bytes differ from the file on disk"
            print("PASS AC-GC1 status=200 type=text/html bytes=%d offline=True same_as_disk=True"
                  % len(body))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-GC1 :: %s" % exc)

        # ---------------- AC-GC2 ----------------
        try:
            _, _, body = http_get(base + "/gate/")
            text = body.decode("utf-8")
            for label in (AI_LABEL, RISK_NOTE, MOCK_NOTE):
                assert label in text, "standing surface missing: %s" % label
            assert PHYSICAL in text, "page does not name the CEO physical item"
            print("PASS AC-GC2 aigc_label=True risk_note=True mock_note=True physical_item=True")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-GC2 :: %s" % exc)

        # ---------------- AC-GC3 ----------------
        try:
            status, ctype, body = http_get(base + "/gate/api/contract")
            assert status == 200, "contract status=%s" % status
            assert "application/json" in ctype.lower(), "contract type=%s" % ctype
            served = json.loads(body.decode("utf-8"))
            live = msgsec_stub.contract()
            for key in ("provider_prod", "endpoint", "suggest_values",
                        "request_keys", "response_keys", "result_keys"):
                assert served.get(key) == live.get(key), (
                    "contract %s served=%r live=%r" % (key, served.get(key), live.get(key)))
            assert served.get("blocked_on"), "contract names no blocking item"
            assert "appid" in served["blocked_on"], (
                "contract blocked_on does not name the appid: %r" % served["blocked_on"])
            print("PASS AC-GC3 provider=%s endpoint=%s suggests=%d blocked_on=True"
                  % (served["provider_prod"], served["endpoint"],
                     len(served["suggest_values"])))
        except (AssertionError, ValueError) as exc:
            failed += 1
            print("FAIL AC-GC3 :: %s" % exc)

        # ---------------- AC-GC4 ----------------
        try:
            status, body = http_call(base + "/gate/api/check", "POST",
                                     {"content": "plain research note about the sandbox"})
            assert status == 200, "plain status=%s body=%r" % (status, body[:200])
            plain = json.loads(body.decode("utf-8"))
            assert plain["result"]["suggest"] == "pass", plain["result"]
            assert plain["result"]["label"] == 100, plain["result"]
            assert plain["http_decision"] == "SERVE", plain["http_decision"]

            status, body = http_call(base + "/gate/api/check", "POST",
                                     {"content": "这句里含 " + forbidden[0]})
            risky = json.loads(body.decode("utf-8"))
            assert status == 200, "risky status=%s" % status
            assert risky["result"]["suggest"] == "risky", risky["result"]
            assert risky["result"]["label"] == 20001, risky["result"]
            assert risky["http_decision"] == "REFUSE", risky["http_decision"]

            status, body = http_call(base + "/gate/api/check", "POST",
                                     {"content": "这句里含 " + advisory[0]})
            review = json.loads(body.decode("utf-8"))
            assert status == 200, "review status=%s" % status
            assert review["result"]["suggest"] == "review", review["result"]
            assert review["result"]["label"] == 20002, review["result"]
            assert review["http_decision"] == "REVIEW", review["http_decision"]

            for resp in (plain, risky, review):
                assert len(resp.get("trace_id") or "") == 32, resp.get("trace_id")
                assert resp.get("mock") is True, resp.get("mock")
                assert resp.get("billable") is False, resp.get("billable")
                assert resp.get("provider") == "stub", resp.get("provider")

            with open(MODULE, encoding="utf-8") as fh:
                module_src = fh.read()
            for word in forbidden + advisory:
                assert word not in module_src, "wordlist literal in the module: %s" % word
            print("PASS AC-GC4 plain=SERVE forbidden=REFUSE advisory=REVIEW "
                  "trace32=True mock=True billable=False config_driven=True")
        except (AssertionError, ValueError, KeyError) as exc:
            failed += 1
            print("FAIL AC-GC4 :: %s" % exc)

        # ---------------- AC-GC5 ----------------
        try:
            a_status, _, a = http_get(base + "/gate")
            b_status, _, b = http_get(base + "/gate/")
            assert a_status == 200 and b_status == 200, (a_status, b_status)
            assert a == b == disk_bytes, "slash forms or disk bytes disagree"

            code, _, _ = http_get(base + "/gate/nope")
            assert code == 404, "unknown GET answered %s" % code
            pcode, _ = http_call(base + "/gate/nope", "POST", {"content": "x"})
            assert pcode == 404, "unknown POST answered %s" % pcode
            gcode, _ = http_call(base + "/gate/api/check", "GET")
            assert gcode == 405, "GET on the check route answered %s" % gcode
            ucode, _ = http_call(base + "/gate/api/check", "PUT", {"content": "x"})
            assert ucode == 405, "PUT answered %s" % ucode

            bcode, bbody = http_call(base + "/gate/api/check", "POST", {"content": "   "})
            assert bcode == 400, "blank content answered %s" % bcode
            assert json.loads(bbody.decode("utf-8")).get("code") == "E_GC_BAD_CONTENT", bbody

            long_text = "a" * (max_len + 1)
            lcode, lbody = http_call(base + "/gate/api/check", "POST", {"content": long_text})
            assert lcode == 413, "over-length content answered %s" % lcode
            assert json.loads(lbody.decode("utf-8")).get("code") == "E_GC_TOO_LONG", lbody
            print("PASS AC-GC5 identical=True unknown404=True method405=True "
                  "blank400=True overlong413=True")
        except (AssertionError, ValueError) as exc:
            failed += 1
            print("FAIL AC-GC5 :: %s" % exc)

        # ---------------- AC-GC6 ----------------
        try:
            assert not disk_bytes.startswith(b"\xef\xbb\xbf"), "page carries a BOM"
            assert b"\r\n" not in disk_bytes, "page carries CRLF line endings"
            with open(MODULE, "rb") as fh:
                module_bytes = fh.read()
            module_bytes.decode("ascii")
            module_src = module_bytes.decode("ascii")
            assert "import time" not in module_src, "serving module imports a clock"
            assert "gate=http://127.0.0.1:%d/gate/" % leg.gate_port in leg.banner, (
                "banner gate url does not name the bound port: %s" % leg.banner)
            _, _, faces_body = http_get("http://127.0.0.1:%d/hub/api/faces" % leg.hub_port)
            faces = json.loads(faces_body.decode("utf-8"))
            assert faces.get("gate") == "http://127.0.0.1:%d/gate/" % leg.gate_port, (
                "hub does not publish the real gate port: %r" % faces.get("gate"))
            with open(REGISTRY, encoding="utf-8") as fh:
                registry = fh.read()
            assert "os-content-gate-console" in registry, "registry carries no suite row"
            print("PASS AC-GC6 bom=False crlf=0 ascii_module=True clock=0 banner=True "
                  "hub_face=True wired=True page_sha16=%s"
                  % hashlib.sha256(disk_bytes).hexdigest()[:16].upper())
        except (AssertionError, UnicodeDecodeError, ValueError) as exc:
            failed += 1
            print("FAIL AC-GC6 :: %s" % exc)

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