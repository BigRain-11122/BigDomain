"""One-off live leg for R2484: the hub really leads to the running panel.

Starts the SHIPPED lobby server and the SHIPPED panel on OS-assigned ports,
then reads the hub payload the way a browser would. Writes exactly one utf-8 LF
evidence file through a single writer, so the writer census never sees a
PowerShell capture dialect.

Usage: python src/os/live_R2484.py
Exit: 0 = LIVE PASS, 2 = LIVE FAIL.
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", ".."))
LOBBY = os.path.join(REPO, "src", "sandbox", "lobby", "server.py")
PANEL = os.path.join(REPO, "src", "sandbox", "panel.py")
PAGE = os.path.join(REPO, "src", "sandbox", "panel.html")
EVIDENCE = os.path.join(REPO, "qa", "hub-panel-live-R2484.log")
NO_WINDOW = 0x08000000

LINES = []


def say(text):
    LINES.append(text)
    print(text)


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def can_connect(port, timeout=0.35):
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def wait_port(port, timeout=40.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if can_connect(port):
            return True
        time.sleep(0.15)
    return False


def http(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()


def main():
    bad = 0
    ws_port = free_port()
    hub_port = free_port()
    panel_port = free_port()
    lobby = subprocess.Popen(
        [sys.executable, LOBBY, "--port", str(ws_port),
         "--hub-port", str(hub_port), "--panel-port", str(panel_port),
         "--db", os.path.join(REPO, "logs", "live-R2484-events.db")],
        cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=NO_WINDOW)
    panel = None
    try:
        if not wait_port(hub_port):
            say("FAIL hub port %d never accepted" % hub_port)
            return 2
        say("PASS lobby hub listening on %d (panel published on %d)"
            % (hub_port, panel_port))
        panel = subprocess.Popen(
            [sys.executable, PANEL, "--port", str(panel_port)],
            cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=NO_WINDOW)
        if not wait_port(panel_port):
            say("FAIL panel port %d never accepted" % panel_port)
            return 2

        code, body = http("http://127.0.0.1:%d/hub/" % hub_port)
        with open(os.path.join(REPO, "src", "sandbox", "lobby", "hub.html"),
                  "rb") as handle:
            disk_hub = handle.read()
        if code != 200 or body != disk_hub:
            bad += 1
            say("FAIL hub page %s bytes=%d disk=%d"
                % (code, len(body), len(disk_hub)))
        else:
            say("PASS hub page 200 at %dB byte-identical to disk" % len(body))

        code, raw = http("http://127.0.0.1:%d/hub/api/faces?probe=1" % hub_port)
        payload = json.loads(raw.decode("utf-8"))
        want = "http://127.0.0.1:%d/panel/" % panel_port
        if payload.get("panel") != want:
            bad += 1
            say("FAIL published panel url=%r want %r"
                % (payload.get("panel"), want))
        else:
            say("PASS published panel url=%s" % want)
        if (payload.get("live") or {}).get("panel") is not True:
            bad += 1
            say("FAIL live map reads panel=%r"
                % ((payload.get("live") or {}).get("panel"),))
        else:
            say("PASS live map reads panel=True")

        code, body = http(payload["panel"])
        with open(PAGE, "rb") as handle:
            disk_panel = handle.read()
        if code != 200 or body != disk_panel:
            bad += 1
            say("FAIL published panel url answered %s at %dB (disk %dB)"
                % (code, len(body), len(disk_panel)))
        else:
            say("PASS published panel url 200 at %dB byte-identical to disk"
                % len(body))

        code, raw = http("http://127.0.0.1:%d/panel/api/state" % panel_port)
        state = json.loads(raw.decode("utf-8"))
        if code != 200 or "lobby" not in (state.get("startable") or []):
            bad += 1
            say("FAIL panel state %s startable=%r"
                % (code, state.get("startable")))
        else:
            say("PASS panel state 200 startable=%s"
                % ",".join(state.get("startable") or []))
    finally:
        for proc in (panel, lobby):
            if proc is None:
                continue
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()

    closed = not can_connect(panel_port)
    if not closed:
        bad += 1
        say("FAIL panel port %d still open after teardown" % panel_port)
    else:
        say("PASS panel port %d refused after teardown" % panel_port)

    say("LIVE %s rc=%d" % ("FAIL" if bad else "PASS", 2 if bad else 0))
    with open(EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(LINES) + "\n")
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())