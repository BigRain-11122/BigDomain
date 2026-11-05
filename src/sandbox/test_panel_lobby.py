"""Suite for the panel started lobby face (BigDomain R2482).

Six criteria AC-LBY1..AC-LBY6 pre-registered in the R2482 backlog row BEFORE
this file and the panel.py lobby leg existed.

Nothing is read off a canned string: the panel is really started, the start
route really spawns src/sandbox/lobby/server.py with five OS-assigned ports, an
independent TCP connect checks the hub port it publishes, the served hub page
is fetched over HTTP, and the teardown leg proves the child is gone.

Usage: python test_panel_lobby.py
Exit: 0 = SUITE PASS 6/6, 2 = FAIL.
"""

import json
import os
import socket
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MODULE = os.path.join(HERE, "panel.py")
PAGE = os.path.join(HERE, "panel.html")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
LOBBY = os.path.join(HERE, "lobby", "server.py")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import panel as panel_module  # noqa: E402

RESULTS = []
PORT_KEYS = ("ws", "city", "web", "hub", "gate")


def report(name, bad, detail=""):
    """One PASS/FAIL line per criterion so the battery can count it."""
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def can_connect(port, timeout=0.35):
    if not port:
        return False
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def http(url, method="GET", body=None, timeout=45.0):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.getcode(), res.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()


def jhttp(url, method="GET", body=None, timeout=45.0):
    code, raw = http(url, method=method, body=body, timeout=timeout)
    try:
        return code, json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return code, {"raw": raw[:200].decode("utf-8", "replace")}


def face_row(payload, face_id):
    for row in payload.get("faces") or []:
        if row.get("id") == face_id:
            return row
    return {}


def ac_lby1():
    """The published contract names the lobby and its five sockets."""
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0)
    base = "http://127.0.0.1:%d" % httpd.server_address[1]
    bad = 0
    try:
        code, payload = jhttp(base + "/panel/api/state")
        if code != 200:
            bad += 1
            print("  AC-LBY1 state answered %s" % (code,))
        startable = payload.get("startable")
        if startable != ["checkout", "ledger", "ugc", "lobby"]:
            bad += 1
            print("  AC-LBY1 startable reads %r" % (startable,))
        row = face_row(payload, "lobby")
        if not row:
            bad += 1
            print("  AC-LBY1 no lobby row in the payload")
        if row.get("module") != os.path.join("sandbox", "lobby", "server.py"):
            bad += 1
            print("  AC-LBY1 lobby module reads %r" % (row.get("module"),))
        cmd = row.get("cmd") or ""
        for flag in ("--port", "--city-http-port", "--web-port",
                     "--hub-port", "--gate-port"):
            if flag not in cmd:
                bad += 1
                print("  AC-LBY1 command is missing %s: %r" % (flag, cmd))
        if row.get("live") is not False or row.get("started") is not False:
            bad += 1
            print("  AC-LBY1 an unstarted lobby reads live: %r" % (row,))
    finally:
        httpd.shutdown()
        httpd.server_close()
    return report("AC-LBY1 lobby published in the contract", bad,
                  "startable lists four faces and the lobby command names "
                  "all five sockets")


def ac_lby2():
    """Start assigns five distinct OS ports and publishes the hub one."""
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0)
    base = "http://127.0.0.1:%d" % httpd.server_address[1]
    bad = 0
    try:
        code, started = jhttp(base + "/panel/api/start", "POST",
                              {"face": "lobby"}, timeout=60.0)
        if code != 200:
            bad += 1
            print("  AC-LBY2 start answered %s %r" % (code, started))
            started = {}
        ports = started.get("ports") or {}
        if sorted(ports) != sorted(PORT_KEYS):
            bad += 1
            print("  AC-LBY2 ports map reads %r" % (ports,))
        values = [ports.get(key) for key in PORT_KEYS]
        if len(set(values)) != len(values):
            bad += 1
            print("  AC-LBY2 ports are not pairwise distinct: %r" % (values,))
        if any(not isinstance(v, int) or v < 1024 for v in values):
            bad += 1
            print("  AC-LBY2 a published port is not an OS port: %r"
                  % (values,))
        hub = ports.get("hub")
        if started.get("port") != hub:
            bad += 1
            print("  AC-LBY2 the published port is not the hub port: %r"
                  % (started.get("port"),))
        want = "http://127.0.0.1:%s/hub/" % (hub,)
        if started.get("url") != want:
            bad += 1
            print("  AC-LBY2 url reads %r, wanted %r"
                  % (started.get("url"), want))
        if started.get("live") is not True:
            bad += 1
            print("  AC-LBY2 start did not claim a measured live face")
        jhttp(base + "/panel/api/stop", "POST", {"face": "lobby"})
    finally:
        httpd.shutdown()
        httpd.server_close()
    return report("AC-LBY2 start assigns five distinct OS ports", bad,
                  "hub port is the published address")


def ac_lby3():
    """Readiness is measured: an independent connect plus the real page."""
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0)
    base = "http://127.0.0.1:%d" % httpd.server_address[1]
    bad = 0
    try:
        code, started = jhttp(base + "/panel/api/start", "POST",
                              {"face": "lobby"}, timeout=60.0)
        hub = (started.get("ports") or {}).get("hub")
        if code != 200 or not hub:
            bad += 1
            print("  AC-LBY3 lobby did not start: %s %r" % (code, started))
        else:
            if not can_connect(hub):
                bad += 1
                print("  AC-LBY3 published hub port %r does not accept"
                      % (hub,))
            code, raw = http(started.get("url"), timeout=20.0)
            if code != 200 or not raw:
                bad += 1
                print("  AC-LBY3 hub page answered %s with %d bytes"
                      % (code, len(raw)))
            code, payload = jhttp(base + "/panel/api/state")
            row = face_row(payload, "lobby")
            if row.get("live") is not True or row.get("port") != hub:
                bad += 1
                print("  AC-LBY3 state disagrees with the start answer: %r"
                      % (row,))
        jhttp(base + "/panel/api/stop", "POST", {"face": "lobby"})
    finally:
        httpd.shutdown()
        httpd.server_close()
    return report("AC-LBY3 readiness measured, never declared", bad,
                  "the published hub port accepts and serves the hub page")


def ac_lby4():
    """Refusals stay honest and still create nothing."""
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0)
    base = "http://127.0.0.1:%d" % httpd.server_address[1]
    bad = 0
    try:
        code, payload = jhttp(base + "/panel/api/start", "POST",
                              {"face": "nope"})
        if code != 400 or payload.get("error") != "E_PANEL_UNKNOWN_FACE":
            bad += 1
            print("  AC-LBY4 unknown face answered %s %r" % (code, payload))
        code, payload = jhttp(base + "/panel/api/start", "POST", None)
        if code != 400 or payload.get("error") != "E_PANEL_BAD_FACE":
            bad += 1
            print("  AC-LBY4 blank body answered %s %r" % (code, payload))
        code, payload = jhttp(base + "/panel/api/stop", "POST",
                              {"face": "ledger"})
        if code != 404 or payload.get("error") != "E_PANEL_NOT_STARTED":
            bad += 1
            print("  AC-LBY4 stopping a never-started face answered %s %r"
                  % (code, payload))
        code, first = jhttp(base + "/panel/api/start", "POST",
                            {"face": "lobby"}, timeout=60.0)
        code, second = jhttp(base + "/panel/api/start", "POST",
                             {"face": "lobby"}, timeout=60.0)
        if second.get("error") != "E_PANEL_ALREADY_RUNNING":
            bad += 1
            print("  AC-LBY4 second lobby start answered %s %r"
                  % (code, second))
        if second.get("port") != first.get("port"):
            bad += 1
            print("  AC-LBY4 second start moved the hub port: %r vs %r"
                  % (second.get("port"), first.get("port")))
        jhttp(base + "/panel/api/stop", "POST", {"face": "lobby"})
    finally:
        httpd.shutdown()
        httpd.server_close()
    return report("AC-LBY4 refusals honest and cheap", bad,
                  "unknown face, blank body, never-started stop, double start")


def ac_lby5():
    """Teardown: the stop verb and the server shutdown both leave nothing."""
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0)
    base = "http://127.0.0.1:%d" % httpd.server_address[1]
    bad = 0
    orphan_hub = None
    try:
        code, started = jhttp(base + "/panel/api/start", "POST",
                              {"face": "lobby"}, timeout=60.0)
        hub = (started.get("ports") or {}).get("hub")
        if code != 200 or not hub:
            bad += 1
            print("  AC-LBY5 lobby did not start: %s %r" % (code, started))
        else:
            code, payload = jhttp(base + "/panel/api/stop", "POST",
                                  {"face": "lobby"})
            if code != 200:
                bad += 1
                print("  AC-LBY5 stop answered %s %r" % (code, payload))
            if can_connect(hub):
                bad += 1
                print("  AC-LBY5 stopped hub port %r still accepts" % (hub,))
            code, payload = jhttp(base + "/panel/api/state")
            row = face_row(payload, "lobby")
            if row.get("live") is not False or row.get("started") is not False:
                bad += 1
                print("  AC-LBY5 state still claims the stopped lobby: %r"
                      % (row,))
        code, again = jhttp(base + "/panel/api/start", "POST",
                            {"face": "lobby"}, timeout=60.0)
        orphan_hub = (again.get("ports") or {}).get("hub")
    finally:
        httpd.shutdown()
        httpd.server_close()
    if orphan_hub and can_connect(orphan_hub):
        bad += 1
        print("  AC-LBY5 closed server left the lobby on %r" % (orphan_hub,))
    return report("AC-LBY5 teardown leaves nothing", bad,
                  "stop refuses the hub port and shutdown kills the child")


def ac_lby6():
    """Hygiene: ASCII source, no shell, one new registry row, page honest."""
    bad = 0
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        bad += 1
        print("  AC-LBY6 panel.py is not pure ASCII")
    text = raw.decode("utf-8", "replace")
    if "shell=True" in text:
        bad += 1
        print("  AC-LBY6 panel.py uses shell=True")
    if not os.path.isfile(LOBBY):
        bad += 1
        print("  AC-LBY6 the shipped lobby module is missing on disk")
    with open(REGISTRY, "r", encoding="utf-8", errors="replace") as handle:
        registry = handle.read()
    rows = registry.count('"test_panel_lobby.py"')
    if rows != 1:
        bad += 1
        print("  AC-LBY6 registry carries %d rows for this suite" % (rows,))
    if "panel-lobby" not in registry:
        bad += 1
        print("  AC-LBY6 registry does not name the panel-lobby row")
    with open(PAGE, "r", encoding="utf-8", errors="replace") as handle:
        page = handle.read()
    if "lobby" not in page:
        bad += 1
        print("  AC-LBY6 the page never mentions the lobby face")
    stale = ("\u53ea\u5217\u51fa\u53ef\u72ec\u7acb\u542f\u52a8\u7684"
             "\u4e09\u4e2a\u9762")
    if stale in page:
        bad += 1
        print("  AC-LBY6 the page still claims only three faces start here")
    return report("AC-LBY6 hygiene, registration and an honest page", bad,
                  "ASCII source, no shell, one registry row, page updated")


def main():
    ac_lby1()
    ac_lby2()
    ac_lby3()
    ac_lby4()
    ac_lby6()
    ac_lby5()
    passed = sum(1 for _name, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if passed == total else "FAIL",
                              passed, total))
    return 0 if passed == total else 2


if __name__ == "__main__":
    sys.exit(main())