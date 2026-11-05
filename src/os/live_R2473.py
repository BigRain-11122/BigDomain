"""R2473 live capture: start the UGC console the way a person would start it.

Writes qa/ugc-console-live-R2473.log itself as ONE utf-8 LF single writer
(never a shell redirect), so the evidence dialect is provable.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
LOG = os.path.join(ROOT, "qa", "ugc-console-live-R2473.log")
SCRIPT = os.path.join(ROOT, "src", "sandbox", "ugc", "ugc_page.py")
CONFIG = os.path.join(ROOT, "src", "sandbox", "ugc", "config.json")

LINES = []


def say(text):
    LINES.append(text)
    print(text)


def http(port, path, method="GET", body=None):
    url = "http://127.0.0.1:%d%s" % (port, path)
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.getcode(), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def free_port():
    import socket
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def main():
    tmp = tempfile.mkdtemp(prefix="ugc-live-")
    db = os.path.join(tmp, "ugc.db")
    port = free_port()
    proc = subprocess.Popen(
        [sys.executable, SCRIPT, "--config", CONFIG, "--db", db,
         "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=ROOT)
    try:
        banner = ""
        deadline = time.time() + 30
        while time.time() < deadline:
            code, body = http(port, "/ugc/api/state")
            if code == 200:
                break
            time.sleep(0.2)
        else:
            say("FAIL server never answered")
            return 2
        code_state, body_state = http(port, "/ugc/api/state")
        state = json.loads(body_state.decode("utf-8"))
        say("state code=%d review=%d pool=%d max_len=%s"
            % (code_state, len(state["review"]), len(state["pool"]["items"]),
               state["notices"]["max_len"]))

        code_page, body_page = http(port, "/ugc/")
        say("page code=%d bytes=%d" % (code_page, len(body_page)))

        code_sub, body_sub = http(port, "/ugc/api/submit", "POST",
                                  {"actor": "live-visitor",
                                   "content": "live check: a story kiosk at the old bus stop"})
        receipt = json.loads(body_sub.decode("utf-8"))
        say("submit code=%d gate=%s received=%s evt=%s"
            % (code_sub, receipt.get("gate"), receipt.get("received"),
               receipt.get("evt_id")))

        cfg = json.load(open(CONFIG, encoding="utf-8"))
        gray = cfg["gate"]["gray_words"][0]
        code_g, body_g = http(port, "/ugc/api/submit", "POST",
                              {"actor": "live-gray", "content": "live gray: %s note" % gray})
        gray_receipt = json.loads(body_g.decode("utf-8"))
        say("gray code=%d gate=%s suspended=%s"
            % (code_g, gray_receipt.get("gate"), gray_receipt.get("suspended")))

        code_v, body_v = http(port, "/ugc/api/verdict", "POST",
                              {"evt_id": gray_receipt.get("evt_id"), "verdict": "pass"})
        say("verdict code=%d" % code_v)

        code_after, body_after = http(port, "/ugc/api/state")
        state_after = json.loads(body_after.decode("utf-8"))
        say("after code=%d review=%d pool=%d"
            % (code_after, len(state_after["review"]), len(state_after["pool"]["items"])))
        say("VERDICT %s" % ("PASS" if (code_state == 200 and code_page == 200 and
                                       code_sub == 200 and code_g == 200 and
                                       code_v == 200 and len(state_after["review"]) == 0 and
                                       len(state_after["pool"]["items"]) == 2) else "FAIL"))
        return 0
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
        child_alive = proc.poll() is None
        say("terminated=True child_pid=%d child_alive=%s" % (proc.pid, child_alive))
        payload = "\n".join(LINES) + "\n"
        with open(LOG, "wb") as handle:
            handle.write(payload.encode("utf-8"))
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())