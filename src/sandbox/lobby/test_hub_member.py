"""Suite for the hub membership face and the panel startable member (R2489).

Six criteria AC-HMB1..AC-HMB6 were pre-registered in the R2489 backlog row
BEFORE this file, the hub_page change, the hub.html card, the server.py flag,
the panel row and the member_page default-port change existed. Everything here
is read off the SHIPPED modules: build_faces, the real hub HTTP face on an
OS-assigned port, the real server.py argument parser, the real panel.py face
table, and the real member_page.py process the panel spawns.

The panel leg starts a REAL member page on an OS port and reads the served
bytes back against member.html on disk, so "the panel can start it" is measured
rather than asserted.

Usage: python test_hub_member.py
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
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

import hub_page  # noqa: E402  (path wired above)

PAGE = os.path.join(HERE, "hub.html")
MODULE = os.path.join(HERE, "hub_page.py")
SERVER = os.path.join(HERE, "server.py")
REGISTRY = os.path.join(REPO, "src", "sandbox", "reconcile_all.py")
PANEL = os.path.join(REPO, "src", "sandbox", "panel.py")
MEMBER_PAGE = os.path.join(REPO, "src", "sandbox", "member", "member_page.py")
MEMBER_HTML = os.path.join(REPO, "src", "sandbox", "member", "member.html")

RESULTS = []


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % (name, "FAIL" if bad else "PASS",
                       ("  " + detail) if detail else ""))
    return bad


def http(url, method="GET"):
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
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


def ac_hmb1():
    """Additive contract: every old key byte-identical, member published."""
    host = "127.0.0.1"
    old = hub_page.build_faces(host, 8091, web_port=8094, city_port=8092,
                               checkout_port=8093, gate_port=8095)
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
        "gate": "http://127.0.0.1:8095/gate/",
        "gate_note": "started by this process (--gate-port)",
        "ledger": "http://127.0.0.1:8097/ledger/",
        "ledger_cmd": "python src/sandbox/ledger/ledger_page.py --port 8097",
        "ugc": "http://127.0.0.1:8098/ugc/",
        "ugc_cmd": "python src/sandbox/ugc/ugc_page.py --port 8098",
        "panel": "http://127.0.0.1:8099/panel/",
        "panel_cmd": "python src/sandbox/panel.py --port 8099",
    }
    bad = 0
    for key, value in expected.items():
        if old.get(key) != value:
            bad += 1
            print("  AC-HMB1 old key drifted: %s=%r want %r"
                  % (key, old.get(key), value))
    for key in ("checkout_note", "ledger_note", "ugc_note", "panel_note"):
        if key not in old:
            bad += 1
            print("  AC-HMB1 old note missing: %s" % key)
    if old.get("member") != "http://127.0.0.1:8096/member/":
        bad += 1
        print("  AC-HMB1 member url wrong by default: %r" % (old.get("member"),))
    if old.get("member_cmd") != (
            "python src/sandbox/member/member_page.py --host 127.0.0.1"
            " --port 8096"):
        bad += 1
        print("  AC-HMB1 member_cmd wrong: %r" % (old.get("member_cmd"),))
    if "8096" not in str(old.get("member_note", "")):
        bad += 1
        print("  AC-HMB1 member_note does not name the port: %r"
              % (old.get("member_note"),))
    want_ports = {"lobby": 8094, "city": 8092, "checkout": 8093,
                  "gate": 8095, "ledger": 8097, "ugc": 8098,
                  "panel": 8099, "member": 8096}
    if old.get("face_ports") != want_ports:
        bad += 1
        print("  AC-HMB1 face_ports=%r want %r"
              % (old.get("face_ports"), want_ports))
    moved = hub_page.build_faces(host, 8091, web_port=None, city_port=None,
                                 checkout_port=free_port(), gate_port=None,
                                 ledger_port=free_port(), ugc_port=free_port(),
                                 panel_port=free_port(), member_port=9104)
    if moved.get("member") != "http://127.0.0.1:9104/member/":
        bad += 1
        print("  AC-HMB1 member ignores caller port: %r" % (moved.get("member"),))
    if (moved.get("face_ports") or {}).get("member") != 9104:
        bad += 1
        print("  AC-HMB1 face_ports ignores caller port: %r"
              % (moved.get("face_ports"),))
    absent = hub_page.build_faces(host, 8091, web_port=None, city_port=None,
                                 checkout_port=free_port(), gate_port=None,
                                 ledger_port=free_port(), ugc_port=free_port(),
                                 panel_port=None, member_port=None)
    for key in ("member", "member_note", "member_cmd"):
        if key in absent:
            bad += 1
            print("  AC-HMB1 %s published although member_port=None" % key)
    if "member" in (absent.get("face_ports") or {}):
        bad += 1
        print("  AC-HMB1 face_ports carries member although member_port=None")
    return report("AC-HMB1 additive face contract", bad,
                  "old keys checked, member published at 8096")


def ac_hmb2():
    """The live map is measured: a listener flips member, closing it flips back."""
    faces = hub_page.build_faces("127.0.0.1", 8091, web_port=None,
                                 city_port=None, checkout_port=free_port(),
                                 gate_port=None, ledger_port=free_port(),
                                 ugc_port=free_port(), panel_port=free_port(),
                                 member_port=free_port())
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
            print("  AC-HMB2 live keys=%r want %r"
                  % (sorted(live), sorted(faces["face_ports"])))
        if live.get("member") is not False:
            bad += 1
            print("  AC-HMB2 dead member face read alive: %r" % (live,))
        held = listener(faces["face_ports"]["member"])
        try:
            code, raw = http(url)
            live = json.loads(raw.decode("utf-8")).get("live") or {}
            if live.get("member") is not True:
                bad += 1
                print("  AC-HMB2 listener not seen: %r" % (live,))
            if live.get("ugc") is not False or live.get("panel") is not False:
                bad += 1
                print("  AC-HMB2 unrelated face flipped: %r" % (live,))
        finally:
            held.close()
        code, raw = http(url)
        live = json.loads(raw.decode("utf-8")).get("live") or {}
        if live.get("member") is not False:
            bad += 1
            print("  AC-HMB2 closed listener still reads alive: %r" % (live,))
    finally:
        httpd.shutdown()
        httpd.server_close()
    return report("AC-HMB2 live map measured", bad,
                  "listener on/off moved member only")


def ac_hmb3():
    """The page carries the member card and all seven live markers."""
    with open(PAGE, "rb") as handle:
        page = handle.read().decode("utf-8")
    bad = 0
    if 'id="link-member"' not in page:
        bad += 1
        print("  AC-HMB3 member card link missing")
    if 'data-face="member"' not in page:
        bad += 1
        print("  AC-HMB3 member live marker missing")
    markers = 0
    for face_id in ("lobby", "city", "checkout", "ledger", "ugc", "panel",
                    "member"):
        if 'data-face="%s"' % face_id in page:
            markers += 1
    if markers != 7:
        bad += 1
        print("  AC-HMB3 markers=%d want 7" % markers)
    if "data.member" not in page or "probe=1" not in page:
        bad += 1
        print("  AC-HMB3 page does not read the published member/probe payload")
    lowered = page.lower()
    if "http://" in lowered or "https://" in lowered or "//cdn" in lowered:
        bad += 1
        print("  AC-HMB3 page carries an external reference")
    return report("AC-HMB3 page carries the face", bad,
                  "7 markers, zero external references")


def ac_hmb4():
    """The operator flag is advertised and passed through."""
    bad = 0
    proc = subprocess.run([sys.executable, SERVER, "--help"],
                          capture_output=True, text=True, timeout=180)
    if proc.returncode != 0:
        bad += 1
        print("  AC-HMB4 --help exit=%d" % proc.returncode)
    out = proc.stdout + proc.stderr
    if "--member-port" not in out:
        bad += 1
        print("  AC-HMB4 --member-port not advertised")
    if "8096" not in out:
        bad += 1
        print("  AC-HMB4 default 8096 not advertised")
    if "not started" not in out:
        bad += 1
        print("  AC-HMB4 the flag does not say the face is not started")
    with open(SERVER, "rb") as handle:
        source = handle.read().decode("utf-8", "replace")
    if "member_port=args.member_port" not in source:
        bad += 1
        print("  AC-HMB4 server does not pass the flag to build_faces")
    return report("AC-HMB4 operator wiring honest", bad,
                  "flag advertised and passed through")


def ac_hmb5():
    """The panel starts a REAL member page and the port dies on stop."""
    sys.path.insert(0, os.path.join(REPO, "src", "sandbox"))
    import panel as panel_mod  # noqa: E402  (path wired above)
    bad = 0
    if tuple(panel_mod.FACE_IDS) != ("checkout", "ledger", "member", "ugc",
                                     "lobby"):
        bad += 1
        print("  AC-HMB5 startable=%r want the five with member"
              % (tuple(panel_mod.FACE_IDS),))
    with open(MEMBER_PAGE, "rb") as handle:
        src = handle.read().decode("utf-8", "replace")
    if 'parser.add_argument("--port", type=int, default=8096)' not in src:
        bad += 1
        print("  AC-HMB5 member_page --port default is not 8096")
    if 'default=8095' in src:
        bad += 1
        print("  AC-HMB5 member_page still defaults to the hub's 8095")
    face = panel_mod.Panel(host="127.0.0.1")
    port = None
    try:
        code, payload = face.start("member")
        if code != 200:
            bad += 1
            print("  AC-HMB5 start member answered %s %r" % (code, payload))
        else:
            port = int(payload["port"])
            if not panel_mod.can_connect("127.0.0.1", port):
                bad += 1
                print("  AC-HMB5 published port %r refuses a connect" % port)
            code, body = http(payload["url"])
            with open(MEMBER_HTML, "rb") as handle:
                disk = handle.read()
            if code != 200 or body != disk:
                bad += 1
                print("  AC-HMB5 %s answered %s with %dB (disk %dB)"
                      % (payload["url"], code, len(body), len(disk)))
            state = face.state_payload()
            rows = dict((row["id"], row) for row in state["faces"])
            if state.get("startable") != list(panel_mod.FACE_IDS):
                bad += 1
                print("  AC-HMB5 state startable=%r" % (state.get("startable"),))
            if rows.get("member", {}).get("live") is not True:
                bad += 1
                print("  AC-HMB5 state does not read member live: %r"
                      % (rows.get("member"),))
            if rows.get("member", {}).get("port") != port:
                bad += 1
                print("  AC-HMB5 state port drifted: %r" % (rows.get("member"),))
            code, _ = face.stop("member")
            if code != 200:
                bad += 1
                print("  AC-HMB5 stop answered %s" % code)
            if port and panel_mod.can_connect("127.0.0.1", port):
                bad += 1
                print("  AC-HMB5 port %d still accepts after stop" % port)
    finally:
        face.stop_all()
    return report("AC-HMB5 the panel can start it", bad,
                  "real member page served and torn down")


def ac_hmb6():
    """Hygiene, one new registry row plus the member-page row."""
    bad = 0
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        bad += 1
        print("  AC-HMB6 hub_page.py is not pure ASCII")
    source = raw.decode("ascii", "replace")
    for banned in ("subprocess", "shell=True"):
        if banned in source:
            bad += 1
            print("  AC-HMB6 hub_page.py carries %r" % banned)
    with open(REGISTRY, "rb") as handle:
        registry = handle.read().decode("utf-8", "replace")
    if registry.count('"lobby-hub-member"') != 1:
        bad += 1
        print("  AC-HMB6 lobby-hub-member rows=%d want 1"
              % registry.count('"lobby-hub-member"'))
    if registry.count('"member-face"') != 1:
        bad += 1
        print("  AC-HMB6 member-face rows=%d want 1"
              % registry.count('"member-face"'))
    if '"test_member_page.py"' not in registry:
        bad += 1
        print("  AC-HMB6 the member page suite is not wired into the registry")
    return report("AC-HMB6 hygiene and registration", bad,
                  "ascii module, two registry rows wired")


def main():
    ac_hmb1()
    ac_hmb2()
    ac_hmb3()
    ac_hmb4()
    ac_hmb5()
    ac_hmb6()
    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    if passed == total:
        print("SUITE PASS %d/%d" % (passed, total))
        return 0
    print("SUITE FAIL %d/%d" % (passed, total))
    return 2


if __name__ == "__main__":
    sys.exit(main())