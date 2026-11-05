"""R2467 evidence capture: two suite legs plus one live bring-up.

House law asks for the evidence file to have ONE writer, so this script is the
writer and it writes utf-8 with LF endings. It runs the content-gate console
suite twice (the digest of its criterion lines must be identical between legs)
and then starts a real server the way a person would, reads the console over
HTTP and records what it saw.

Run: python src/os/live_R2467.py
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
REPO = os.path.dirname(os.path.dirname(HERE))
LOBBY = os.path.join(REPO, "src", "sandbox", "lobby")
SUITE = os.path.join(LOBBY, "test_gate_console.py")
SERVER = os.path.join(LOBBY, "server.py")
EVIDENCE = os.path.join(REPO, "qa", "content-gate-console-R2467.log")
LIVE = os.path.join(REPO, "qa", "content-gate-console-live-R2467.log")


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def http_get(url, timeout=8.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def http_post(url, payload, timeout=8.0):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def run_suite():
    proc = subprocess.run([sys.executable, SUITE], cwd=LOBBY,
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def digest_of(lines):
    keep = [ln for ln in lines if ln.startswith("PASS ") or ln.startswith("FAIL ")]
    return hashlib.sha256("\n".join(keep).encode("utf-8")).hexdigest()[:16].upper()


def live_capture():
    ws_port = free_port()
    city_port = free_port()
    hub_port = free_port()
    gate_port = free_port()
    tmp = tempfile.mkdtemp(prefix="gate-live-")
    db = os.path.join(tmp, "events.db")
    argv = [sys.executable, SERVER, "--host", "127.0.0.1",
            "--port", str(ws_port), "--db", db,
            "--city-http-port", str(city_port),
            "--web-port", "0", "--hub-port", str(hub_port),
            "--gate-port", str(gate_port),
            "--ping-interval", "30", "--ping-timeout", "60"]
    proc = subprocess.Popen(argv, cwd=LOBBY, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    out = []
    try:
        banner = None
        end = time.monotonic() + 25
        while time.monotonic() < end:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            if "serving ws://" in line:
                banner = line.strip()
                break
        if not banner:
            out.append("FAIL banner not seen")
            return out
        out.append("BANNER %s" % banner)
        match = re.search(r"gate=http://127\.0\.0\.1:(\d+)/gate/", banner)
        if not match:
            out.append("FAIL banner carries no gate url")
            return out
        bound = int(match.group(1))
        out.append("GATE PORT bound=%d requested=%d" % (bound, gate_port))
        base = "http://127.0.0.1:%d" % bound

        status, body = http_get(base + "/gate/")
        text = body.decode("utf-8")
        out.append("GET /gate/ status=%d bytes=%d notices_ok=%s" % (
            status, len(body),
            all(m in text for m in ("AI 生成内容标识", "非投顾提示", "mock", "CEO 物理件"))))

        status, body = http_get(base + "/gate/api/contract")
        contract = json.loads(body.decode("utf-8"))
        out.append("GET /gate/api/contract status=%d endpoint=%s blocked_on=%s" % (
            status, contract.get("endpoint"), contract.get("blocked_on")))

        with open(os.path.join(LOBBY, "config.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        probe = [
            ("plain", "plain research note about the sandbox"),
            ("forbidden", "text with " + cfg["gate"]["forbidden_words"][0]),
            ("advisory", "text with " + cfg["gate"]["advisory_ban_words"][0]),
        ]
        for name, payload in probe:
            status, body = http_post(base + "/gate/api/check", {"content": payload})
            resp = json.loads(body.decode("utf-8"))
            out.append("POST /gate/api/check %s status=%d suggest=%s label=%s "
                       "decision=%s mock=%s billable=%s" % (
                           name, status, resp["result"]["suggest"], resp["result"]["label"],
                           resp.get("http_decision"), resp.get("mock"), resp.get("billable")))

        status, body = http_post(base + "/gate/api/check", {"content": "   "})
        out.append("POST /gate/api/check blank status=%d code=%s" % (
            status, json.loads(body.decode("utf-8")).get("code")))

        status, body = http_get("http://127.0.0.1:%d/hub/api/faces" % hub_port)
        faces = json.loads(body.decode("utf-8"))
        out.append("HUB faces gate=%s" % faces.get("gate"))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    return out


def main():
    code_a, text_a = run_suite()
    code_b, text_b = run_suite()
    dig_a = digest_of(text_a.splitlines())
    dig_b = digest_of(text_b.splitlines())
    lines = []
    lines.append("R2467 CONTENT-GATE CONSOLE EVIDENCE legs=2 adjacent=4")
    lines.append("LEG 1 exit=%d digest=%s" % (code_a, dig_a))
    for ln in text_a.splitlines():
        lines.append("  " + ln)
    lines.append("LEG 2 exit=%d digest=%s identical=%s" % (code_b, dig_b, dig_a == dig_b))
    for ln in text_b.splitlines():
        lines.append("  " + ln)
    lines.append("VERDICT legs_identical=%s suite_exit=%d/%d" % (
        dig_a == dig_b, code_a, code_b))
    with open(EVIDENCE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    live = live_capture()
    with open(LIVE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(live) + "\n")

    print("EVIDENCE %s bytes=%d identical=%s" % (
        os.path.relpath(EVIDENCE, REPO), os.path.getsize(EVIDENCE), dig_a == dig_b))
    for ln in live:
        print("LIVE " + ln)
    return 0 if dig_a == dig_b and code_a == 0 and code_b == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())