"""R2489 live leg: the real hub and the real member page, end to end.

Starts the SHIPPED lobby server (which starts the hub face), starts the SHIPPED
member page on an OS-assigned port, then reads the published hub payload back
and opens the published member URL. Writes one utf-8 LF evidence line set.

Usage: python src/os/live_R2489.py
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

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SERVER = os.path.join(REPO, "src", "sandbox", "lobby", "server.py")
MEMBER = os.path.join(REPO, "src", "sandbox", "member", "member_page.py")
MEMBER_HTML = os.path.join(REPO, "src", "sandbox", "member", "member.html")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

OUT = []


def say(text):
    print(text)
    OUT.append(text)


def http(url):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=20) as res:
        return res.status, res.read()


def can_connect(port, host="127.0.0.1"):
    try:
        with socket.create_connection((host, int(port)), timeout=0.4):
            return True
    except (OSError, ValueError):
        return False


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def wait_connect(port, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if can_connect(port):
            return True
        time.sleep(0.15)
    return False


def main():
    bad = []
    hub_port = free_port()
    member_port = free_port()
    server = subprocess.Popen(
        [sys.executable, SERVER, "--host", "127.0.0.1",
         "--port", str(free_port()), "--hub-port", str(hub_port),
         "--member-port", str(member_port)],
        cwd=REPO, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
    member = None
    try:
        if not wait_connect(hub_port, 25.0):
            bad.append("hub-never-listened")
        faces_url = "http://127.0.0.1:%d/hub/api/faces?probe=1" % hub_port
        code, raw = http(faces_url)
        payload = json.loads(raw.decode("utf-8"))
        say("hub_probe status=%d member=%s live_member=%r"
            % (code, payload.get("member"), (payload.get("live") or {}).get("member")))
        if payload.get("member") != "http://127.0.0.1:%d/member/" % member_port:
            bad.append("member-url-not-published")
        if (payload.get("live") or {}).get("member") is not False:
            bad.append("member-read-live-before-start")

        member = subprocess.Popen(
            [sys.executable, MEMBER, "--host", "127.0.0.1",
             "--port", str(member_port)],
            cwd=REPO, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
        if not wait_connect(member_port, 25.0):
            bad.append("member-page-never-listened")
        code, raw = http(faces_url)
        payload = json.loads(raw.decode("utf-8"))
        live = payload.get("live") or {}
        say("hub_probe_after_start live_member=%r live_panel=%r keys=%d"
            % (live.get("member"), live.get("panel"), len(live)))
        if live.get("member") is not True:
            bad.append("member-not-read-live-after-start")
        if live.get("panel") is not False:
            bad.append("unrelated-face-flipped")

        code, body = http(payload["member"])
        with open(MEMBER_HTML, "rb") as handle:
            disk = handle.read()
        say("member_get status=%d bytes=%d disk=%d identical=%s"
            % (code, len(body), len(disk), body == disk))
        if code != 200 or body != disk:
            bad.append("member-page-not-served-from-disk")

        code, raw = http("http://127.0.0.1:%d/hub" % hub_port)
        say("hub_page status=%d bytes=%d external_refs=%s"
            % (code, len(raw),
               ("http://" in raw.decode("utf-8").lower().replace(
                   "http://127.0.0.1", ""))))
    finally:
        for proc in (member, server):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
        time.sleep(1.0)
        say("ports_after_stop hub_open=%s member_open=%s"
            % (can_connect(hub_port), can_connect(member_port)))
        if can_connect(hub_port) or can_connect(member_port):
            bad.append("port-still-open-after-stop")

    if bad:
        say("LIVE FAIL " + ",".join(bad))
        return 2
    say("LIVE PASS member face published, measured and served")
    return 0


if __name__ == "__main__":
    code = main()
    with open(os.path.join(REPO, "qa", "hub-member-live-R2489.log"),
              "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(OUT) + "\n")
    sys.exit(code)