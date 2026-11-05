"""One-off live leg for R2481: drive the real panel module over HTTP.

Starts src/sandbox/panel.py the way an operator would, asks its page and its
state over HTTP, starts one face through the panel, fetches the URL it
published, stops it, and proves the port is gone. Writes one utf-8 LF evidence
file - the dialect law this week already paid for once.
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PANEL = os.path.join(ROOT, "src", "sandbox", "panel.py")
LEDGER_HTML = os.path.join(ROOT, "src", "sandbox", "ledger", "ledger.html")
EVIDENCE = os.path.join(ROOT, "qa", "panel-live-R2481.log")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

LINES = []


def say(text):
    LINES.append(text)
    print(text, flush=True)


def free_port():
    sock = socket.socket()
    try:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


def can_connect(port, timeout=0.35):
    if not port:
        return False
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def wait_port(port, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if can_connect(port):
            return True
        time.sleep(0.15)
    return False


def http(url, method="GET", body=None, timeout=30.0):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.getcode(), res.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()


def write_once(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(tmp, path)
    with open(path, "rb") as handle:
        raw = handle.read()
    return len(raw), raw.count(b"\r\n"), raw.startswith(b"\xef\xbb\xbf")


def main():
    port = free_port()
    proc = subprocess.Popen(
        [sys.executable, PANEL, "--host", "127.0.0.1", "--port", str(port)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=NO_WINDOW,
    )
    base = "http://127.0.0.1:%d" % port
    fails = []
    stopped_port = None
    try:
        if not wait_port(port):
            fails.append("E_PANEL_DOES_NOT_LISTEN")
            return fails
        code, body = http(base + "/panel")
        say("PANEL page status=%s bytes=%d" % (code, len(body)))
        if code != 200:
            fails.append("E_PANEL_PAGE")
        code, raw = http(base + "/panel/api/state")
        state = json.loads(raw.decode("utf-8"))
        ids = [row.get("id") for row in state.get("faces") or []]
        say("PANEL state status=%s faces=%s" % (code, ",".join(ids)))
        if ids != ["checkout", "ledger", "ugc"]:
            fails.append("E_PANEL_FACES")
        code, raw = http(base + "/panel/api/start", "POST", {"face": "ledger"})
        started = json.loads(raw.decode("utf-8"))
        say("PANEL start status=%s face=%s port=%s live=%s"
            % (code, started.get("face"), started.get("port"),
               started.get("live")))
        if code != 200 or not can_connect(started.get("port")):
            fails.append("E_PANEL_START")
        code, body = http(started.get("url") or "")
        with open(LEDGER_HTML, "rb") as handle:
            disk = handle.read()
        say("PANEL face url=%s status=%s bytes=%d byte_identical=%s"
            % (started.get("url"), code, len(body), body == disk))
        if code != 200 or body != disk:
            fails.append("E_PANEL_FACE_BYTES")
        stopped_port = started.get("port")
        code, raw = http(base + "/panel/api/stop", "POST", {"face": "ledger"})
        stopped = json.loads(raw.decode("utf-8"))
        say("PANEL stop status=%s stopped=%s live=%s"
            % (code, stopped.get("stopped"), stopped.get("live")))
        if code != 200:
            fails.append("E_PANEL_STOP")
        if can_connect(stopped_port):
            fails.append("E_PANEL_ORPHAN")
        say("PANEL orphan check port=%s still_open=%s"
            % (stopped_port, can_connect(stopped_port)))
    finally:
        if proc.poll() is None:
            proc.terminate()
            deadline = time.time() + 5.0
            while proc.poll() is None and time.time() < deadline:
                time.sleep(0.05)
            if proc.poll() is None:
                proc.kill()
        say("PANEL module exit=%s" % proc.poll())
        if stopped_port and can_connect(stopped_port):
            fails.append("E_PANEL_ORPHAN_AFTER_EXIT")

    say("LIVE %s fails=%d %s" % ("PASS" if not fails else "FAIL", len(fails),
                                 ",".join(fails) if fails else "none"))
    size, crlf, bom = write_once(EVIDENCE, "\n".join(LINES) + "\n")
    print("EVIDENCE %s bytes=%d crlf=%d bom=%s"
          % (os.path.relpath(EVIDENCE, ROOT), size, crlf, bom))
    return fails


if __name__ == "__main__":
    problems = main()
    sys.exit(0 if not problems else 2)