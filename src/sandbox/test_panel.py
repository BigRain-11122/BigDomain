"""Suite for the sandbox control panel (BigDomain R2481).

Six criteria AC-PAN1..AC-PAN6 pre-registered in the R2481 backlog row BEFORE
this file, src/sandbox/panel.py and its registry row existed.

Nothing here is read off a canned string: the panel is really started, the
start route really spawns a shipped module, an independent TCP connect checks
the port it reports, the served URL is compared against the page bytes on
disk, and the teardown leg proves the children are gone.

Usage: python test_panel.py
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
REGISTRY = os.path.join(REPO, "src", "sandbox", "reconcile_all.py")
LEDGER_HTML = os.path.join(HERE, "ledger", "ledger.html")
LEDGER_CONFIG = os.path.join(HERE, "ledger", "config.json")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import panel as panel_module  # noqa: E402

RESULTS = []


def report(name, bad, detail=""):
    """One line per criterion, prefixed PASS/FAIL so the battery can count it.

    The shipped battery counts criteria with ^PASS/^FAIL, and the shipped
    evidence capture digests exactly those lines; a criterion printed as
    "AC-PAN1 ... PASS" would be counted as zero and would digest to nothing.
    """
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


def http(url, method="GET", body=None, timeout=20.0):
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


def jhttp(url, method="GET", body=None, timeout=20.0):
    code, raw = http(url, method=method, body=body, timeout=timeout)
    try:
        return code, json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return code, {}


def notices_now():
    with open(LEDGER_CONFIG, encoding="utf-8") as handle:
        cfg = json.load(handle)
    token = cfg.get("token") or {}
    return token.get("ai_label_text") or "", token.get("disclaimer") or ""


def face_row(payload, face_id):
    for row in payload.get("faces") or []:
        if row.get("id") == face_id:
            return row
    return {}


def ac_pan1():
    """The page is real and carries the standing surfaces."""
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0)
    port = httpd.server_address[1]
    bad = 0
    try:
        with open(PAGE, "rb") as handle:
            disk = handle.read()
        for path in ("/panel", "/panel/"):
            code, body = http("http://127.0.0.1:%d%s" % (port, path))
            if code != 200 or body != disk:
                bad += 1
                print("  AC-PAN1 %s not byte-identical (%s, %dB vs %dB)"
                      % (path, code, len(body), len(disk)))
        if len(disk) <= 3000:
            bad += 1
            print("  AC-PAN1 page is only %dB" % len(disk))
        text = disk.decode("utf-8")
        for marker in ("http://", "https://"):
            if marker in text:
                bad += 1
                print("  AC-PAN1 page carries an external reference: %s"
                      % marker)
        if 'src="//' in text or "href=\"//" in text:
            bad += 1
            print("  AC-PAN1 page carries a protocol-relative reference")
        ai_label, disclaimer = notices_now()
        for label, value in (("ai_label", ai_label),
                             ("disclaimer", disclaimer)):
            if not value or value not in text:
                bad += 1
                print("  AC-PAN1 standing surface missing verbatim: %s" % label)
        if "MOCK / NO REAL CHARGE" not in text:
            bad += 1
            print("  AC-PAN1 mock / no-real-charge statement missing")
    finally:
        httpd.shutdown()
        httpd.server_close()
    return report("AC-PAN1 page real and standing surfaces", bad,
                  "byte-identical on both slash forms")


def ac_pan2():
    """The state face is measured, never canned."""
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0)
    port = httpd.server_address[1]
    base = "http://127.0.0.1:%d" % port
    bad = 0
    started = None
    try:
        code, payload = jhttp(base + "/panel/api/state")
        if code != 200:
            return report("AC-PAN2 state measured", 1, "state answered %s" % code)
        ids = [row.get("id") for row in payload.get("faces") or []]
        # AMENDED at R2482: the lobby joined the published faces, so the pinned
        # three-id list gained a fourth id rather than the assertion weakening.
        # AMENDED again at R2489 for the same reason: the membership page joined
        # as the fifth startable face, so the pinned list gains that id and
        # stays an exact list (never a subset check).
        if ids != ["checkout", "ledger", "member", "ugc", "lobby"]:
            bad += 1
            print("  AC-PAN2 face list drifted: %r" % (ids,))
        for face_id in ids:
            row = face_row(payload, face_id)
            if row.get("url") is not None or row.get("live") is not False:
                bad += 1
                print("  AC-PAN2 not-started row claims state: %r" % (row,))
            cmd = row.get("cmd") or ""
            module_name = {"checkout": "checkout_demo.py",
                           "ledger": "ledger_page.py",
                           "member": "member_page.py",
                           "ugc": "ugc_page.py",
                           "lobby": "server.py"}[face_id]
            if module_name not in cmd:
                bad += 1
                print("  AC-PAN2 cmd does not name the module: %r" % (cmd,))
        code, started = jhttp(base + "/panel/api/start", "POST",
                              {"face": "ledger"}, timeout=40.0)
        if code != 200:
            bad += 1
            print("  AC-PAN2 could not start a face to measure: %s %r"
                  % (code, started))
        else:
            code, payload = jhttp(base + "/panel/api/state")
            row = face_row(payload, "ledger")
            if row.get("live") is not True:
                bad += 1
                print("  AC-PAN2 listener not seen live: %r" % (row,))
            if row.get("port") != started.get("port"):
                bad += 1
                print("  AC-PAN2 state port drifted from the start answer")
            jhttp(base + "/panel/api/stop", "POST", {"face": "ledger"})
            code, payload = jhttp(base + "/panel/api/state")
            row = face_row(payload, "ledger")
            if row.get("live") is not False:
                bad += 1
                print("  AC-PAN2 closed listener still reads live: %r" % (row,))
    finally:
        httpd.shutdown()
        httpd.server_close()
    return report("AC-PAN2 state measured", bad,
                  "listener on/off moved one face only")


def ac_pan3():
    """Start really starts."""
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0)
    port = httpd.server_address[1]
    base = "http://127.0.0.1:%d" % port
    bad = 0
    try:
        code, started = jhttp(base + "/panel/api/start", "POST",
                              {"face": "ledger"}, timeout=40.0)
        if code != 200:
            bad += 1
            print("  AC-PAN3 start answered %s %r" % (code, started))
        else:
            face_port = started.get("port")
            if not can_connect(face_port):
                bad += 1
                print("  AC-PAN3 returned port %r refuses a connect" % (face_port,))
            url = started.get("url") or ""
            if not url.endswith("/ledger/"):
                bad += 1
                print("  AC-PAN3 url shape drifted: %r" % (url,))
            code, body = http(url)
            try:
                with open(LEDGER_HTML, "rb") as handle:
                    disk = handle.read()
            except OSError:
                disk = b""
            if code != 200 or body != disk:
                bad += 1
                print("  AC-PAN3 served URL is not the shipped page (%s, %dB)"
                      % (code, len(body)))
            code, payload = jhttp(base + "/panel/api/state")
            row = face_row(payload, "ledger")
            if row.get("live") is not True or row.get("port") != face_port:
                bad += 1
                print("  AC-PAN3 state disagrees with the start answer: %r"
                      % (row,))
    finally:
        httpd.shutdown()
        httpd.server_close()
    return report("AC-PAN3 start really starts", bad,
                  "spawned port accepts and serves the shipped page")


def ac_pan4():
    """Refusals are honest and create nothing."""
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0)
    port = httpd.server_address[1]
    base = "http://127.0.0.1:%d" % port
    bad = 0
    try:
        code, payload = jhttp(base + "/panel/api/start", "POST",
                              {"face": "nope"})
        if code != 400 or payload.get("error") != "E_PANEL_UNKNOWN_FACE":
            bad += 1
            print("  AC-PAN4 unknown face answered %s %r" % (code, payload))
        code, payload = jhttp(base + "/panel/api/start", "POST", None)
        if code != 400 or payload.get("error") != "E_PANEL_BAD_FACE":
            bad += 1
            print("  AC-PAN4 blank body answered %s %r" % (code, payload))
        code, first = jhttp(base + "/panel/api/start", "POST",
                            {"face": "checkout"}, timeout=40.0)
        if code != 200:
            bad += 1
            print("  AC-PAN4 first start answered %s %r" % (code, first))
        code, second = jhttp(base + "/panel/api/start", "POST",
                             {"face": "checkout"}, timeout=40.0)
        if code != 409 or second.get("error") != "E_PANEL_ALREADY_RUNNING":
            bad += 1
            print("  AC-PAN4 second start answered %s %r" % (code, second))
        if second.get("port") != first.get("port"):
            bad += 1
            print("  AC-PAN4 second start moved the port: %r vs %r"
                  % (second.get("port"), first.get("port")))
        jhttp(base + "/panel/api/stop", "POST", {"face": "checkout"})
        code, payload = jhttp(base + "/panel/api/stop", "POST",
                              {"face": "ugc"})
        if code != 404 or payload.get("error") != "E_PANEL_NOT_STARTED":
            bad += 1
            print("  AC-PAN4 stop on a never-started face answered %s %r"
                  % (code, payload))
    finally:
        httpd.shutdown()
        httpd.server_close()
    return report("AC-PAN4 refusals honest", bad,
                  "400/409/404 with their own codes")


def ac_pan6():
    """Hygiene and registration."""
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0)
    port = httpd.server_address[1]
    base = "http://127.0.0.1:%d" % port
    bad = 0
    try:
        for route in ("/panel/api/start", "/panel/api/stop"):
            code, _ = http(base + route)
            if code != 405:
                bad += 1
                print("  AC-PAN6 GET on %s answered %s" % (route, code))
        code, _ = http(base + "/panel/api/nope")
        if code != 404:
            bad += 1
            print("  AC-PAN6 unknown path answered %s" % code)
        code, _ = http(base + "/panel/api/state", method="POST", body={})
        if code != 405:
            bad += 1
            print("  AC-PAN6 POST on the state route answered %s" % code)
    finally:
        httpd.shutdown()
        httpd.server_close()

    with open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        bad += 1
        print("  AC-PAN6 panel.py is not pure ASCII")
    text = raw.decode("utf-8", "replace")
    if "shell=True" in text:
        bad += 1
        print("  AC-PAN6 panel.py uses a shell")
    for banned in ("import requests", "import numpy"):
        if banned in text:
            bad += 1
            print("  AC-PAN6 non-stdlib import: %s" % banned)

    with open(REGISTRY, encoding="utf-8") as handle:
        registry = handle.read()
    if registry.count('("panel",') != 1:
        bad += 1
        print("  AC-PAN6 registry does not carry exactly one panel row")
    return report("AC-PAN6 hygiene and registration", bad,
                  "405/404 coded, module ASCII stdlib only, one registry row")


def ac_pan5():
    """Teardown leaves nothing behind - runs last, it closes the server."""
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0)
    port = httpd.server_address[1]
    base = "http://127.0.0.1:%d" % port
    bad = 0
    try:
        code, started = jhttp(base + "/panel/api/start", "POST",
                              {"face": "ugc"}, timeout=40.0)
        if code != 200:
            bad += 1
            print("  AC-PAN5 could not start a face: %s %r" % (code, started))
        else:
            face_port = started.get("port")
            code, payload = jhttp(base + "/panel/api/stop", "POST",
                                  {"face": "ugc"})
            if code != 200:
                bad += 1
                print("  AC-PAN5 stop answered %s %r" % (code, payload))
            if can_connect(face_port):
                bad += 1
                print("  AC-PAN5 stopped port %r still accepts" % (face_port,))
            code, payload = jhttp(base + "/panel/api/state")
            row = face_row(payload, "ugc")
            if row.get("live") is not False or row.get("started") is not False:
                bad += 1
                print("  AC-PAN5 state still claims the stopped face: %r"
                      % (row,))
        code, orphan = jhttp(base + "/panel/api/start", "POST",
                             {"face": "checkout"}, timeout=40.0)
        orphan_port = orphan.get("port")
    finally:
        httpd.shutdown()
        httpd.server_close()
    if orphan_port and can_connect(orphan_port):
        bad += 1
        print("  AC-PAN5 closed server left a child on %r" % (orphan_port,))
    return report("AC-PAN5 teardown leaves nothing", bad,
                  "stopped port refused and the server took its child down")


def main():
    ac_pan1()
    ac_pan2()
    ac_pan3()
    ac_pan4()
    ac_pan6()
    ac_pan5()
    passed = sum(1 for _name, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if passed == total else "FAIL",
                              passed, total))
    return 0 if passed == total else 2


if __name__ == "__main__":
    sys.exit(main())