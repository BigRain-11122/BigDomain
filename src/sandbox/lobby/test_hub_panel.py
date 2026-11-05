"""Suite for the hub control-panel face and its measured live map (R2484).

Six criteria AC-HPN1..AC-HPN6 were pre-registered in the R2484 backlog row
BEFORE this file, the hub_page change, the hub.html card and the server.py
flag existed. Everything here is read off the SHIPPED modules: build_faces,
the real hub HTTP face started on an OS-assigned port, and the real server.py
argument parser. A listener is opened and closed to prove the live map
measures rather than guesses.

Usage: python test_hub_panel.py
Exit: 0 = SUITE PASS 6/6, 2 = FAIL.
"""

import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

import hub_page  # noqa: E402  (path wired above)

PAGE = os.path.join(HERE, "hub.html")
MODULE = os.path.join(HERE, "hub_page.py")
SERVER = os.path.join(HERE, "server.py")
REGISTRY = os.path.join(REPO, "src", "sandbox", "reconcile_all.py")

RESULTS = []


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % (name, "FAIL" if bad else "PASS",
                       ("  " + detail) if detail else ""))
    return bad


def http(url, method="GET"):
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def listener(port):
    """A real listening socket that accepts nothing: enough for a TCP probe."""
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", port))
    sock.listen(8)
    return sock


def ac_hpn1():
    """Additive contract: every old key byte-identical, panel published."""
    host = "127.0.0.1"
    old = hub_page.build_faces(host, 8091, web_port=8094, city_port=8092,
                               checkout_port=8093, gate_port=8096)
    expected = {
        "mock": True,
        "chargeable": False,
        "read_only": True,
        "ws": "ws://127.0.0.1:8091/ws",
        "ws_port": 8091,
        "ws_path": "/ws",
        "lobby": "http://127.0.0.1:8094/lobby/",
        "lobby_note": "started by this process (--web-port)",
        "city": "http://127.0.0.1:8092/city/",
        "city_note": "started by this process (--city-http-port)",
        "checkout": "http://127.0.0.1:8093/checkout/",
        "gate": "http://127.0.0.1:8096/gate/",
        "gate_note": "started by this process (--gate-port)",
        "ledger": "http://127.0.0.1:8097/ledger/",
        "ledger_cmd": "python src/sandbox/ledger/ledger_page.py --port 8097",
        "ugc": "http://127.0.0.1:8098/ugc/",
        "ugc_cmd": "python src/sandbox/ugc/ugc_page.py --port 8098",
    }
    bad = 0
    for key, value in expected.items():
        if old.get(key) != value:
            bad += 1
            print("  AC-HPN1 old key drifted: %s=%r want %r"
                  % (key, old.get(key), value))
    for key in ("checkout_note", "ledger_note", "ugc_note"):
        if key not in old:
            bad += 1
            print("  AC-HPN1 old note missing: %s" % key)
    if old.get("panel") != "http://127.0.0.1:8099/panel/":
        bad += 1
        print("  AC-HPN1 panel url wrong by default: %r" % (old.get("panel"),))
    if old.get("panel_cmd") != "python src/sandbox/panel.py --port 8099":
        bad += 1
        print("  AC-HPN1 panel_cmd wrong: %r" % (old.get("panel_cmd"),))
    if "8099" not in str(old.get("panel_note", "")):
        bad += 1
        print("  AC-HPN1 panel_note does not name the port: %r"
              % (old.get("panel_note"),))
    want_ports = {"lobby": 8094, "city": 8092, "checkout": 8093,
                  "gate": 8096, "ledger": 8097, "ugc": 8098, "panel": 8099}
    if old.get("face_ports") != want_ports:
        bad += 1
        print("  AC-HPN1 face_ports=%r want %r"
              % (old.get("face_ports"), want_ports))
    moved = hub_page.build_faces(host, 8091, web_port=8094, city_port=8092,
                                 checkout_port=8093, gate_port=8096,
                                 panel_port=9103)
    if moved.get("panel") != "http://127.0.0.1:9103/panel/":
        bad += 1
        print("  AC-HPN1 panel ignores caller port: %r" % (moved.get("panel"),))
    if (moved.get("face_ports") or {}).get("panel") != 9103:
        bad += 1
        print("  AC-HPN1 face_ports ignores caller port: %r"
              % (moved.get("face_ports"),))
    absent = hub_page.build_faces(host, 8091, web_port=None, city_port=None,
                                 checkout_port=free_port(), gate_port=None,
                                 ledger_port=free_port(), ugc_port=free_port(),
                                 panel_port=None)
    for key in ("panel", "panel_note", "panel_cmd"):
        if key in absent:
            bad += 1
            print("  AC-HPN1 %s published although panel_port=None" % key)
    if "panel" in (absent.get("face_ports") or {}):
        bad += 1
        print("  AC-HPN1 face_ports carries panel although panel_port=None")
    return report("AC-HPN1 additive face contract", bad,
                  "old keys checked, panel published at 8099")


def ac_hpn2():
    """The live map is measured: a listener flips panel, closing it flips back."""
    faces = hub_page.build_faces("127.0.0.1", 8091, web_port=None,
                                 city_port=None, checkout_port=free_port(),
                                 gate_port=None, ledger_port=free_port(),
                                 ugc_port=free_port(), panel_port=free_port())
    httpd = hub_page.start_hub_http("127.0.0.1", 0, faces)
    port = httpd.server_address[1]
    url = "http://127.0.0.1:%d/hub/api/faces?probe=1" % port
    bad = 0
    try:
        code, raw = http(url)
        data = json.loads(raw.decode("utf-8"))
        live = data.get("live") or {}
        if sorted(live) != sorted(faces["face_ports"]):
            bad += 1
            print("  AC-HPN2 live keys=%r want %r"
                  % (sorted(live), sorted(faces["face_ports"])))
        if live.get("panel") is not False:
            bad += 1
            print("  AC-HPN2 dead panel face read alive: %r" % (live,))
        held = listener(faces["face_ports"]["panel"])
        try:
            code, raw = http(url)
            live = json.loads(raw.decode("utf-8")).get("live") or {}
            if live.get("panel") is not True:
                bad += 1
                print("  AC-HPN2 listener not seen: %r" % (live,))
            if live.get("ugc") is not False:
                bad += 1
                print("  AC-HPN2 unrelated face flipped: %r" % (live,))
        finally:
            held.close()
        code, raw = http(url)
        live = json.loads(raw.decode("utf-8")).get("live") or {}
        if live.get("panel") is not False:
            bad += 1
            print("  AC-HPN2 closed listener still reads alive: %r" % (live,))
    finally:
        httpd.shutdown()
        httpd.server_close()
    return report("AC-HPN2 live map measured", bad,
                  "listener on/off moved panel only")


def ac_hpn3():
    """The page carries the panel card and all six live markers."""
    with open(PAGE, "rb") as handle:
        page = handle.read().decode("utf-8")
    bad = 0
    if 'id="link-panel"' not in page:
        bad += 1
        print("  AC-HPN3 panel card link missing")
    if 'data-face="panel"' not in page:
        bad += 1
        print("  AC-HPN3 panel live marker missing")
    markers = 0
    for face_id in ("lobby", "city", "checkout", "ledger", "ugc", "panel"):
        if 'data-face="%s"' % face_id in page:
            markers += 1
    if markers != 6:
        bad += 1
        print("  AC-HPN3 markers=%d want 6" % markers)
    if "data.panel" not in page or "probe=1" not in page:
        bad += 1
        print("  AC-HPN3 page does not read the published panel/probe payload")
    lowered = page.lower()
    if "http://" in lowered or "https://" in lowered or "//cdn" in lowered:
        bad += 1
        print("  AC-HPN3 page carries an external reference")
    return report("AC-HPN3 page carries the face", bad,
                  "6 markers, zero external references")


def ac_hpn4():
    """The operator flag is advertised and passed through."""
    bad = 0
    proc = subprocess.run([sys.executable, SERVER, "--help"],
                          capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        bad += 1
        print("  AC-HPN4 --help exit=%d" % proc.returncode)
    out = proc.stdout + proc.stderr
    if "--panel-port" not in out:
        bad += 1
        print("  AC-HPN4 --panel-port not advertised")
    if "8099" not in out:
        bad += 1
        print("  AC-HPN4 default 8099 not advertised")
    if "not started" not in out:
        bad += 1
        print("  AC-HPN4 the flag does not say the face is not started")
    with open(SERVER, "rb") as handle:
        source = handle.read().decode("utf-8", "replace")
    if "panel_port=args.panel_port" not in source:
        bad += 1
        print("  AC-HPN4 server does not pass the flag to build_faces")
    return report("AC-HPN4 operator wiring honest", bad,
                  "flag advertised and passed through")


def ac_hpn5():
    """Read-only surface and determinism, plus the three adjacent hub suites."""
    faces = hub_page.build_faces("127.0.0.1", 8091, web_port=None,
                                 city_port=None, checkout_port=free_port(),
                                 gate_port=None, ledger_port=free_port(),
                                 ugc_port=free_port(), panel_port=free_port())
    httpd = hub_page.start_hub_http("127.0.0.1", 0, faces)
    port = httpd.server_address[1]
    bad = 0
    try:
        with open(PAGE, "rb") as handle:
            disk = handle.read()
        for path in ("/hub", "/hub/"):
            code, body = http("http://127.0.0.1:%d%s" % (port, path))
            if code != 200 or body != disk:
                bad += 1
                print("  AC-HPN5 %s not byte-identical (%s, %dB vs %dB)"
                      % (path, code, len(body), len(disk)))
        code, _ = http("http://127.0.0.1:%d/hub/api/nope" % port)
        if code != 404:
            bad += 1
            print("  AC-HPN5 unknown path answered %s" % code)
        code, _ = http("http://127.0.0.1:%d/hub/api/faces" % port, method="POST")
        if code != 405:
            bad += 1
            print("  AC-HPN5 POST answered %s" % code)
        url = "http://127.0.0.1:%d/hub/api/faces?probe=1" % port
        first = http(url)[1]
        second = http(url)[1]
        if first != second:
            bad += 1
            print("  AC-HPN5 probe bodies differ on a still world")
        payload = json.loads(first.decode("utf-8"))
        if "panel" not in payload:
            bad += 1
            print("  AC-HPN5 probe body does not publish the panel face")
    finally:
        httpd.shutdown()
        httpd.server_close()
    for suite in ("test_hub_page.py", "test_hub_ledger_live.py",
                  "test_hub_ugc.py"):
        path = os.path.join(HERE, suite)
        proc = subprocess.run([sys.executable, path], capture_output=True,
                              text=True, timeout=1200,
                              cwd=os.path.dirname(path))
        tail = (proc.stdout or "").strip().splitlines()
        verdict = tail[-1] if tail else ""
        if proc.returncode != 0 or "SUITE PASS" not in verdict:
            bad += 1
            print("  AC-HPN5 adjacent suite %s rc=%d verdict=%r"
                  % (suite, proc.returncode, verdict))
    return report("AC-HPN5 read-only surface untouched", bad,
                  "page byte-identical, three adjacent suites green")


def ac_hpn6():
    """Hygiene, single registry row."""
    bad = 0
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        bad += 1
        print("  AC-HPN6 hub_page.py is not pure ASCII")
    source = raw.decode("ascii", "replace")
    for banned in ("subprocess", "shell=True"):
        if banned in source:
            bad += 1
            print("  AC-HPN6 hub_page.py carries %r" % banned)
    with open(REGISTRY, "rb") as handle:
        registry = handle.read().decode("utf-8", "replace")
    if registry.count('"lobby-hub-panel"') != 1:
        bad += 1
        print("  AC-HPN6 registry rows=%d want 1"
              % registry.count('"lobby-hub-panel"'))
    return report("AC-HPN6 hygiene and registration", bad,
                  "ascii module, one registry row")


def main():
    ac_hpn1()
    ac_hpn2()
    ac_hpn3()
    ac_hpn4()
    ac_hpn5()
    ac_hpn6()
    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    if passed == total:
        print("SUITE PASS %d/%d" % (passed, total))
        return 0
    print("SUITE FAIL %d/%d" % (passed, total))
    return 2


if __name__ == "__main__":
    sys.exit(main())