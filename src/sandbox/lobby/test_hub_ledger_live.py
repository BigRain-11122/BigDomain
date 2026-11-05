"""Suite for the hub ledger face and its measured live map (BigDomain R2471).

Six criteria AC-HLL1..AC-HLL6 pre-registered in the R2471 backlog row BEFORE
this file, the hub_page change and the hub.html card existed. Everything here
is read off the SHIPPED modules: build_faces, the real hub HTTP face started on
an OS-assigned port, and the real server.py argument parser. A listener is
opened and closed to prove the live map measures rather than guesses.

Usage: python test_hub_ledger_live.py
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


def ac_hll1():
    """Additive contract: old keys byte-identical, ledger face published."""
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
    }
    bad = 0
    for key, value in expected.items():
        if old.get(key) != value:
            bad += 1
            print("  AC-HLL1 old key drifted: %s=%r want %r"
                  % (key, old.get(key), value))
    if "checkout_note" not in old or "8093" not in old["checkout_note"]:
        bad += 1
        print("  AC-HLL1 checkout_note missing or wrong: %r"
              % (old.get("checkout_note"),))
    if old.get("ledger") != "http://127.0.0.1:8097/ledger/":
        bad += 1
        print("  AC-HLL1 ledger url wrong by default: %r" % (old.get("ledger"),))
    if "8097" not in str(old.get("ledger_cmd", "")):
        bad += 1
        print("  AC-HLL1 ledger_cmd does not name the port: %r"
              % (old.get("ledger_cmd"),))
    if "8097" not in str(old.get("ledger_note", "")):
        bad += 1
        print("  AC-HLL1 ledger_note does not name the port: %r"
              % (old.get("ledger_note"),))
    want_ports = {"lobby": 8094, "city": 8092, "checkout": 8093,
                  "gate": 8096, "ledger": 8097}
    if old.get("face_ports") != want_ports:
        bad += 1
        print("  AC-HLL1 face_ports=%r want %r"
              % (old.get("face_ports"), want_ports))
    moved = hub_page.build_faces(host, 8091, web_port=8094, city_port=8092,
                                 checkout_port=8093, gate_port=8096,
                                 ledger_port=9101)
    if moved.get("ledger") != "http://127.0.0.1:9101/ledger/":
        bad += 1
        print("  AC-HLL1 ledger ignores caller port: %r" % (moved.get("ledger"),))
    if (moved.get("face_ports") or {}).get("ledger") != 9101:
        bad += 1
        print("  AC-HLL1 face_ports ignores caller port: %r"
              % (moved.get("face_ports"),))
    return report("AC-HLL1 additive face contract", bad,
                  "old keys 14 checked, ledger published")


def ac_hll2():
    """The live map is measured: a listener flips one face, closing it flips back."""
    base_faces = lambda: hub_page.build_faces(  # noqa: E731
        "127.0.0.1", 8091, web_port=None, city_port=None,
        checkout_port=free_port(), gate_port=None, ledger_port=free_port())
    faces = base_faces()
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
            print("  AC-HLL2 live keys=%r want %r"
                  % (sorted(live), sorted(faces["face_ports"])))
        if live.get("checkout") is not False or live.get("ledger") is not False:
            bad += 1
            print("  AC-HLL2 dead faces read alive: %r" % (live,))
        held = listener(faces["face_ports"]["checkout"])
        try:
            code, raw = http(url)
            live = json.loads(raw.decode("utf-8")).get("live") or {}
            if live.get("checkout") is not True:
                bad += 1
                print("  AC-HLL2 listener not seen: %r" % (live,))
            if live.get("ledger") is not False:
                bad += 1
                print("  AC-HLL2 unrelated face flipped: %r" % (live,))
        finally:
            held.close()
        code, raw = http(url)
        live = json.loads(raw.decode("utf-8")).get("live") or {}
        if live.get("checkout") is not False:
            bad += 1
            print("  AC-HLL2 closed listener still reads alive: %r" % (live,))
    finally:
        httpd.shutdown()
        httpd.server_close()
    return report("AC-HLL2 live map measured", bad,
                  "listener on/off moved one face only")


def ac_hll3():
    """Read-only surface and determinism."""
    faces = hub_page.build_faces("127.0.0.1", 8091, web_port=None,
                                 city_port=None, checkout_port=free_port(),
                                 gate_port=None, ledger_port=free_port())
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
                print("  AC-HLL3 %s not byte-identical (%s, %dB vs %dB)"
                      % (path, code, len(body), len(disk)))
        code, _ = http("http://127.0.0.1:%d/hub/api/nope" % port)
        if code != 404:
            bad += 1
            print("  AC-HLL3 unknown path answered %s" % code)
        code, _ = http("http://127.0.0.1:%d/hub/api/faces" % port, method="POST")
        if code != 405:
            bad += 1
            print("  AC-HLL3 POST answered %s" % code)
        url = "http://127.0.0.1:%d/hub/api/faces?probe=1" % port
        first = http(url)[1]
        second = http(url)[1]
        if first != second:
            bad += 1
            print("  AC-HLL3 probe bodies differ on a still world")
    finally:
        httpd.shutdown()
        httpd.server_close()
    return report("AC-HLL3 read-only surface untouched", bad,
                  "page byte-identical on both slash forms")


def ac_hll4():
    """The page carries the ledger card and per-face live markers, no externals."""
    with open(PAGE, "rb") as handle:
        raw = handle.read()
    page = raw.decode("utf-8")
    bad = 0
    if 'id="link-ledger"' not in page:
        bad += 1
        print("  AC-HLL4 ledger card link missing")
    if 'data-face="ledger"' not in page:
        bad += 1
        print("  AC-HLL4 ledger live marker missing")
    markers = 0
    for face_id in ("lobby", "city", "checkout", "ledger"):
        if 'data-face="%s"' % face_id in page:
            markers += 1
    if markers != 4:
        bad += 1
        print("  AC-HLL4 markers=%d want 4" % markers)
    if "data.ledger" not in page or "probe=1" not in page:
        bad += 1
        print("  AC-HLL4 page does not read the published ledger/probe payload")
    lowered = page.lower()
    if "http://" in lowered or "https://" in lowered or "//cdn" in lowered:
        bad += 1
        print("  AC-HLL4 page carries an external reference")
    return report("AC-HLL4 page carries the face", bad,
                  "4 markers, zero external references")


def ac_hll5():
    """The operator flag is advertised and passed through."""
    bad = 0
    proc = subprocess.run([sys.executable, SERVER, "--help"],
                          capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        bad += 1
        print("  AC-HLL5 --help exit=%d" % proc.returncode)
    out = proc.stdout + proc.stderr
    if "--ledger-port" not in out:
        bad += 1
        print("  AC-HLL5 --ledger-port not advertised")
    if "8097" not in out:
        bad += 1
        print("  AC-HLL5 default 8097 not advertised")
    with open(SERVER, "rb") as handle:
        source = handle.read().decode("utf-8", "replace")
    if "ledger_port=args.ledger_port" not in source:
        bad += 1
        print("  AC-HLL5 server does not pass the flag to build_faces")
    return report("AC-HLL5 operator wiring honest", bad,
                  "flag advertised and passed through")


def ac_hll6():
    """Hygiene, single registry row, adjacent suites still green."""
    bad = 0
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        bad += 1
        print("  AC-HLL6 hub_page.py is not pure ASCII")
    with open(REGISTRY, "rb") as handle:
        registry = handle.read().decode("utf-8", "replace")
    if registry.count('"lobby-hub-ledger"') != 1:
        bad += 1
        print("  AC-HLL6 registry rows=%d want 1"
              % registry.count('"lobby-hub-ledger"'))
    for suite in ("test_hub_page.py",
                  os.path.join("..", "ledger", "test_ledger_page.py")):
        path = os.path.join(HERE, suite)
        proc = subprocess.run([sys.executable, path], capture_output=True,
                              text=True, timeout=900, cwd=os.path.dirname(path))
        tail = (proc.stdout or "").strip().splitlines()
        verdict = tail[-1] if tail else ""
        if proc.returncode != 0 or "SUITE PASS" not in verdict:
            bad += 1
            print("  AC-HLL6 adjacent suite %s rc=%d verdict=%r"
                  % (suite, proc.returncode, verdict))
    return report("AC-HLL6 hygiene and registration", bad,
                  "ascii module, one row, adjacent suites green")


def main():
    ac_hll1()
    ac_hll2()
    ac_hll3()
    ac_hll4()
    ac_hll5()
    ac_hll6()
    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    if passed == total:
        print("SUITE PASS %d/%d" % (passed, total))
        return 0
    print("SUITE FAIL %d/%d" % (passed, total))
    return 2


if __name__ == "__main__":
    sys.exit(main())