"""live_R2464 - start the shipped server the way a person would and read the
room face over HTTP, writing one UTF-8 LF evidence file.

Not a library: one round's live proof. It never imports the product modules, so
what it measures is the process a CEO would actually start.
"""

import io
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOBBY = os.path.join(ROOT, "src", "sandbox", "lobby")
SERVER = os.path.join(LOBBY, "server.py")
EVIDENCE = os.path.join(ROOT, "qa", "lobby-room-picker-live-R2464.log")


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def main():
    ws_port = free_port()
    tmp = os.path.join(os.environ.get("TEMP", "."), "r2464-live")
    os.makedirs(tmp, exist_ok=True)
    flags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW
    proc = subprocess.Popen(
        [sys.executable, "-u", SERVER, "--host", "127.0.0.1",
         "--port", str(ws_port), "--db", os.path.join(tmp, "e.db"),
         "--web-port", "0", "--ping-interval", "30", "--ping-timeout", "60"],
        cwd=LOBBY, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, creationflags=flags)
    banner = ""
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        if "serving ws://" in line:
            banner = line.strip()
            break
    match = re.search(r"lobby_page=http://127\.0\.0\.1:(\d+)/lobby/", banner)
    if not match:
        print("FAIL no lobby_page banner: %r" % banner)
        proc.kill()
        return 1
    web_port = int(match.group(1))

    def get(path):
        url = "http://127.0.0.1:%d%s" % (web_port, path)
        with urllib.request.urlopen(url, timeout=8) as resp:
            return resp.status, resp.read()

    rooms_status, rooms_body = get("/lobby/api/rooms")
    page_status, page_body = get("/lobby/")
    payload = json.loads(rooms_body.decode("utf-8"))
    page_text = page_body.decode("utf-8")
    with open(os.path.join(LOBBY, "config.json"), encoding="utf-8") as handle:
        cfg_rooms = [str(name) for name in json.load(handle)["rooms"]]
    leaks = [name for name in cfg_rooms if name in page_text]

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)

    lines = [
        "LIVE R2464 room picker: the server was started the way a person would "
        "start it, banner=%s" % banner,
        "LIVE rooms route status=%d payload=%s"
        % (rooms_status, json.dumps(payload, sort_keys=True)),
        "LIVE page status=%d bytes=%d carries_selector=%s carries_ledger=%s"
        % (page_status, len(page_body), 'id="room"' in page_text,
           'id="ledger"' in page_text),
        "LIVE the selector reads the route, not the file: configured room names "
        "found in the page=%d" % len(leaks),
        "LIVE process terminated, returncode=%s" % proc.returncode,
    ]
    with io.open(EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    for line in lines:
        print(line)
    ok = (rooms_status == 200 and page_status == 200 and not leaks
          and payload.get("rooms") == cfg_rooms)
    print("LIVE verdict=%s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())