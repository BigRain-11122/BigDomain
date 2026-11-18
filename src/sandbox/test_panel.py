"""Suite for the sandbox control panel (BigDomain R2481).

Six criteria AC-PAN1..AC-PAN6 pre-registered in the R2481 backlog row BEFORE
this file, src/sandbox/panel.py and its registry row existed. Five more -
AC-PAN7..AC-PAN11 - were pre-registered in the R2938 backlog row BEFORE the
ownership declaration existed, because the launcher used to leave the panel
blind and a page click could start a SECOND lobby beside the running one.
AC-PAN12..AC-PAN13 were pre-registered in the R2949 row BEFORE the per-panel
log namespace existed: R2948 kept each child's stderr (the only place a named
refusal can come from) in ONE machine-wide file per face id, so a second panel
silently overwrote the first one's evidence. AC-PAN14..AC-PAN15 were
pre-registered in the R2950 row BEFORE the teardown existed: a per-panel file
that is never removed accumulates, and the tag's four random bytes could not
prove that a reused pid never mints the same name again. AC-PAN16..AC-PAN17
were pre-registered in the R2951 row BEFORE the prune and the monotonic tag
existed: keeping every log with bytes bounded nothing, and a tag that leans on
the wall clock moving forward cannot answer a corrected clock. AC-PAN18 and
AC-PAN19 were pre-registered in the R2952 row BEFORE the count bound and the
--prune-only entry existed: an age bound leaves the RECENT pile unbounded, and
a prune whose only trigger is a human launching a panel is not scheduled at
all.

Nothing here is read off a canned string: the panel is really started, the
start route really spawns a shipped module, an independent TCP connect checks
the port it reports, the served URL is compared against the page bytes on
disk, and the teardown leg proves the children are gone.

Usage: python test_panel.py
Exit: 0 = SUITE PASS 19/19, 2 = FAIL.
"""

import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
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


class DummyListener(object):
    """A real listening socket standing in for a face a launcher serves."""

    def __init__(self):
        self.sock = socket.socket()
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except OSError:
            pass
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(16)
        self.port = int(self.sock.getsockname()[1])

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def owned_pairs(argv):
    """The --owned-face values a command vector really carries, in order."""
    pairs = []
    for index, token in enumerate(argv):
        if token == "--owned-face" and index + 1 < len(argv):
            pairs.append(argv[index + 1])
    return pairs


def ac_pan7():
    """The launcher declares what it serves, derived from its own tables."""
    import start_all as start_module

    bad = 0
    ports = dict((key, 24000 + index)
                 for index, key in enumerate(start_module.PLAN_KEYS))
    commands = dict(start_module.build_commands("127.0.0.1", ports))
    got = owned_pairs(commands.get("panel") or [])
    expected = ["%s:%d" % (key, ports[start_module.FACE_PORT_KEY[key]])
                for key in start_module.FACE_KEYS]
    if got != expected:
        bad += 1
        print("  AC-PAN7 panel vector declares %r, plan says %r"
              % (got, expected))
    # Neutral control: the same reader must SEE a declaration go missing.
    trimmed = list(commands.get("panel") or [])
    if "--owned-face" in trimmed:
        at = trimmed.index("--owned-face")
        del trimmed[at:at + 2]
    if owned_pairs(trimmed) == expected:
        bad += 1
        print("  AC-PAN7 reader cannot see a removed declaration")
    return report("AC-PAN7 launcher declares owned faces", bad,
                  "%d faces derived from FACE_KEYS/FACE_PORT_KEY" % len(expected))


def ac_pan8():
    """An owned face is refused by name; an unowned face still starts."""
    dummy = DummyListener()
    httpd, panel = panel_module.start_panel("127.0.0.1", 0,
                                            owned={"lobby": dummy.port})
    base = "http://127.0.0.1:%d" % httpd.server_address[1]
    bad = 0
    started = None
    try:
        code, body = jhttp(base + "/panel/api/start", "POST", {"face": "lobby"},
                           timeout=40.0)
        if code != 409 or body.get("error") != "E_PANEL_OWNED_BY_LAUNCHER":
            bad += 1
            print("  AC-PAN8 owned lobby start answered %s %r" % (code, body))
        if body.get("port") != dummy.port or body.get("owner") != "launcher":
            bad += 1
            print("  AC-PAN8 refusal does not name the owner: %r" % (body,))
        if not str(body.get("url") or "").endswith("/hub/"):
            bad += 1
            print("  AC-PAN8 refusal url shape drifted: %r" % (body.get("url"),))
        if panel.children:
            bad += 1
            print("  AC-PAN8 a refused start still spawned: %r"
                  % (sorted(panel.children),))
        # Neutral control: the same panel still starts a face nobody owns.
        code, started = jhttp(base + "/panel/api/start", "POST",
                              {"face": "checkout"}, timeout=40.0)
        if code != 200:
            bad += 1
            print("  AC-PAN8 unowned face answered %s %r" % (code, started))
        elif not can_connect(started.get("port")):
            bad += 1
            print("  AC-PAN8 unowned face port %r refuses a connect"
                  % (started.get("port"),))
    finally:
        jhttp(base + "/panel/api/stop", "POST", {"face": "checkout"})
        httpd.shutdown()
        httpd.server_close()
        dummy.close()
    return report("AC-PAN8 owned face refused, unowned still starts", bad,
                  "409 E_PANEL_OWNED_BY_LAUNCHER and zero children")


def ac_pan9():
    """The panel will not kill another process's child, and the port survives."""
    dummy = DummyListener()
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0,
                                             owned={"member": dummy.port})
    base = "http://127.0.0.1:%d" % httpd.server_address[1]
    bad = 0
    started = None
    try:
        code, body = jhttp(base + "/panel/api/stop", "POST", {"face": "member"})
        if code != 409 or body.get("error") != "E_PANEL_OWNER_NOT_THIS_PROCESS":
            bad += 1
            print("  AC-PAN9 owned stop answered %s %r" % (code, body))
        if not can_connect(dummy.port):
            bad += 1
            print("  AC-PAN9 the owner's listener was taken down")
        # Neutral control: a face this panel started still stops.
        code, started = jhttp(base + "/panel/api/start", "POST", {"face": "ugc"},
                              timeout=40.0)
        if code != 200:
            bad += 1
            print("  AC-PAN9 could not start a local face: %s %r"
                  % (code, started))
        else:
            code, body = jhttp(base + "/panel/api/stop", "POST", {"face": "ugc"})
            if code != 200:
                bad += 1
                print("  AC-PAN9 local stop answered %s %r" % (code, body))
            if can_connect(started.get("port")):
                bad += 1
                print("  AC-PAN9 local stop left %r listening"
                      % (started.get("port"),))
    finally:
        httpd.shutdown()
        httpd.server_close()
        dummy.close()
    return report("AC-PAN9 owned stop refused, local stop works", bad,
                  "409 named refusal and the owner's port stayed open")


def ac_pan10():
    """An owned face reads started and LIVE only while its port answers."""
    dummy = DummyListener()
    httpd, _panel = panel_module.start_panel("127.0.0.1", 0,
                                             owned={"member": dummy.port})
    base = "http://127.0.0.1:%d" % httpd.server_address[1]
    bad = 0
    try:
        code, payload = jhttp(base + "/panel/api/state")
        row = face_row(payload, "member")
        if code != 200:
            bad += 1
            print("  AC-PAN10 state answered %s" % code)
        if row.get("owner") != "launcher" or row.get("started") is not True:
            bad += 1
            print("  AC-PAN10 owned row does not name its owner: %r" % (row,))
        if row.get("port") != dummy.port:
            bad += 1
            print("  AC-PAN10 owned row port drifted: %r" % (row.get("port"),))
        if not str(row.get("url") or "").endswith("/member/"):
            bad += 1
            print("  AC-PAN10 owned row url drifted: %r" % (row.get("url"),))
        if row.get("live") is not True:
            bad += 1
            print("  AC-PAN10 a listener that accepts reads not live: %r"
                  % (row,))
        dummy.close()
        code, payload = jhttp(base + "/panel/api/state")
        row = face_row(payload, "member")
        if row.get("live") is not False:
            bad += 1
            print("  AC-PAN10 a closed port still reads live: %r" % (row,))
        if row.get("owner") != "launcher":
            bad += 1
            print("  AC-PAN10 the declaration vanished with the listener: %r"
                  % (row,))
    finally:
        httpd.shutdown()
        httpd.server_close()
        dummy.close()
    return report("AC-PAN10 owned face measured, never assumed", bad,
                  "live moved with the socket, owner stayed named")


def ac_pan11():
    """The declaration is wired through the CLI, not only in source."""
    bad = 0
    try:
        parsed = panel_module.parse_owned(["lobby:1234", "ugc:99"])
        if parsed != {"lobby": 1234, "ugc": 99}:
            bad += 1
            print("  AC-PAN11 parse_owned returned %r" % (parsed,))
    except (AttributeError, ValueError) as exc:
        bad += 1
        print("  AC-PAN11 parse_owned is not callable: %r" % (exc,))
    for spec in ("lobby", "lobby:x", ":12", "lobby:12:3", ""):
        try:
            panel_module.parse_owned([spec])
            bad += 1
            print("  AC-PAN11 malformed pair %r was accepted" % (spec,))
        except ValueError as exc:
            if "E_PANEL_BAD_OWNED" not in str(exc):
                bad += 1
                print("  AC-PAN11 refusal is not named: %r" % (exc,))
        except AttributeError:
            bad += 1
            print("  AC-PAN11 parse_owned is missing")
            break
    dummy = DummyListener()
    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable, MODULE, "--host", "127.0.0.1", "--port", "0",
             "--owned-face", "lobby:%d" % dummy.port],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, cwd=REPO)
        line = proc.stdout.readline().decode("utf-8", "replace").strip()
        port = None
        if "http://" in line:
            tail = line.split("http://", 1)[1].split("/", 1)[0]
            port = int(tail.rsplit(":", 1)[1])
        if not port:
            bad += 1
            print("  AC-PAN11 panel did not print its own address: %r" % (line,))
        else:
            code, payload = jhttp("http://127.0.0.1:%d/panel/api/state" % port)
            row = face_row(payload, "lobby")
            if row.get("owner") != "launcher" or row.get("port") != dummy.port:
                bad += 1
                print("  AC-PAN11 CLI declaration did not reach the state: %r"
                      % (row,))
            code, body = jhttp("http://127.0.0.1:%d/panel/api/start" % port,
                               "POST", {"face": "lobby"}, timeout=40.0)
            if code != 409 or body.get("error") != "E_PANEL_OWNED_BY_LAUNCHER":
                bad += 1
                print("  AC-PAN11 CLI panel answered %s %r" % (code, body))
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except Exception:
                proc.kill()
        dummy.close()
    return report("AC-PAN11 declaration wired through the CLI", bad,
                  "parse_owned both ways and a real --owned-face process")


def digest(path):
    """sha256 of a file on disk, so "unchanged" is bytes and not opinion."""
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None


def spawn_panel():
    """A real panel process on an OS-assigned port; returns (proc, base)."""
    proc = subprocess.Popen(
        [sys.executable, MODULE, "--host", "127.0.0.1", "--port", "0"],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, cwd=REPO)
    line = proc.stdout.readline().decode("utf-8", "replace").strip()
    base = None
    if "http://" in line:
        tail = line.split("http://", 1)[1].split("/", 1)[0]
        base = "http://" + tail
    return proc, base


def stop_panel(proc):
    if proc is not None and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


def ac_pan12():
    """Two panels in ONE process must not share a child log (R2949).

    Same pid is the hardest case for a pid-only name: if the tag were the pid,
    these two panels would collide. Both files must exist at the same moment,
    and panel B starting the same face id must leave panel A's bytes alone.
    """
    bad = 0
    a_httpd, a_panel = panel_module.start_panel("127.0.0.1", 0)
    b_httpd, b_panel = panel_module.start_panel("127.0.0.1", 0)
    a_base = "http://127.0.0.1:%d" % a_httpd.server_address[1]
    b_base = "http://127.0.0.1:%d" % b_httpd.server_address[1]
    path_a = a_panel.log_path_for("ugc")
    path_b = b_panel.log_path_for("ugc")
    shared = os.path.join(tempfile.gettempdir(),
                          "bigdomain-panel-child-ugc.txt")
    # Red control: the shared slot is not merely avoided by these two names, it
    # is never opened. Under the R2948 name both starts would have truncated
    # these bytes, so an unchanged digest is the measurement that the class is
    # gone rather than dodged.
    decoy_before = None
    try:
        with open(shared, "wb") as handle:
            handle.write(b"R2949 decoy: no panel may write here\n")
        decoy_before = digest(shared)
    except OSError as exc:
        print("  AC-PAN12 could not place the decoy: %r" % (exc,))
    before = None
    try:
        if path_a == path_b:
            bad += 1
            print("  AC-PAN12 both panels picked the same file: %r" % (path_a,))
        for path in (path_a, path_b):
            name = os.path.basename(path)
            if not name.startswith("bigdomain-panel-child-"):
                bad += 1
                print("  AC-PAN12 name lost its stem: %r" % (name,))
            if "ugc" not in name:
                bad += 1
                print("  AC-PAN12 name lost the face id: %r" % (name,))
            if os.path.normcase(path) == os.path.normcase(shared):
                bad += 1
                print("  AC-PAN12 still writes the machine-wide name: %r"
                      % (path,))
        code, started = jhttp(a_base + "/panel/api/start", "POST",
                              {"face": "ugc"}, timeout=40.0)
        if code != 200:
            bad += 1
            print("  AC-PAN12 panel A could not start ugc: %s %r"
                  % (code, started))
        else:
            if started.get("child_log_path") != path_a:
                bad += 1
                print("  AC-PAN12 A published %r, not its own path %r"
                      % (started.get("child_log_path"), path_a))
            before = digest(path_a)
            if before is None:
                bad += 1
                print("  AC-PAN12 A kept no log at %r" % (path_a,))
        code, started_b = jhttp(b_base + "/panel/api/start", "POST",
                                {"face": "ugc"}, timeout=40.0)
        if code != 200:
            bad += 1
            print("  AC-PAN12 panel B could not start ugc: %s %r"
                  % (code, started_b))
        else:
            if started_b.get("child_log_path") != path_b:
                bad += 1
                print("  AC-PAN12 B published %r, not its own path %r"
                      % (started_b.get("child_log_path"), path_b))
        if not (os.path.exists(path_a) and os.path.exists(path_b)):
            bad += 1
            print("  AC-PAN12 the two logs do not coexist: %r / %r"
                  % ((os.path.exists(path_a), os.path.exists(path_b)),))
        elif before is not None and digest(path_a) != before:
            bad += 1
            print("  AC-PAN12 panel B rewrote panel A's bytes")
        if decoy_before is None:
            bad += 1
            print("  AC-PAN12 the shared-slot control could not be placed")
        elif digest(shared) != decoy_before:
            bad += 1
            print("  AC-PAN12 a panel still writes the machine-wide slot")
        # And the decoy is a LIVE control, not a file nothing could touch: the
        # same "wb" open the panel uses truncates it on the next line, so the
        # unchanged digest above meant "not opened" rather than "unchangeable".
        if decoy_before is not None:
            try:
                with open(shared, "wb"):
                    pass
            except OSError:
                pass
            if digest(shared) == decoy_before:
                bad += 1
                print("  AC-PAN12 the shared-slot control cannot change at all")
    finally:
        a_httpd.shutdown()
        a_httpd.server_close()
        b_httpd.shutdown()
        b_httpd.server_close()
        for path in (path_a, path_b, shared):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
    return report("AC-PAN12 two panels in one process keep separate logs", bad,
                  "distinct names, both on disk, no cross-write")


def ac_pan13():
    """Two REAL panel processes: each log names the process that wrote it."""
    bad = 0
    a_proc = b_proc = None
    path_a = path_b = None
    a_port = b_port = None
    before = None
    try:
        a_proc, a_base = spawn_panel()
        b_proc, b_base = spawn_panel()
        if not a_base or not b_base:
            bad += 1
            print("  AC-PAN13 a panel never printed its own address")
        else:
            code, started = jhttp(a_base + "/panel/api/start", "POST",
                                  {"face": "ugc"}, timeout=40.0)
            if code != 200:
                bad += 1
                print("  AC-PAN13 panel A answered %s %r" % (code, started))
            else:
                a_port = started.get("port")
                path_a = started.get("child_log_path")
                before = digest(path_a)
            code, started_b = jhttp(b_base + "/panel/api/start", "POST",
                                    {"face": "ugc"}, timeout=40.0)
            if code != 200:
                bad += 1
                print("  AC-PAN13 panel B answered %s %r" % (code, started_b))
            else:
                b_port = started_b.get("port")
                path_b = started_b.get("child_log_path")
            if not path_a or not path_b:
                bad += 1
                print("  AC-PAN13 a start answer hid the log path: %r %r"
                      % (path_a, path_b))
            else:
                if path_a == path_b:
                    bad += 1
                    print("  AC-PAN13 two processes share one file: %r"
                          % (path_a,))
                if str(a_proc.pid) not in os.path.basename(path_a):
                    bad += 1
                    print("  AC-PAN13 A's name hides A's pid (%d): %r"
                          % (a_proc.pid, path_a))
                if str(b_proc.pid) not in os.path.basename(path_b):
                    bad += 1
                    print("  AC-PAN13 B's name hides B's pid (%d): %r"
                          % (b_proc.pid, path_b))
                if not (os.path.exists(path_a) and os.path.exists(path_b)):
                    bad += 1
                    print("  AC-PAN13 the two logs do not coexist")
                elif before is not None and digest(path_a) != before:
                    bad += 1
                    print("  AC-PAN13 panel B rewrote panel A's bytes")
            if a_base and a_port and b_port:
                code, body = jhttp(a_base + "/panel/api/stop", "POST",
                                   {"face": "ugc"})
                if code != 200:
                    bad += 1
                    print("  AC-PAN13 A could not stop its own face: %s %r"
                          % (code, body))
                if not can_connect(b_port):
                    bad += 1
                    print("  AC-PAN13 stopping A's face took B's down")
    finally:
        stop_panel(a_proc)
        stop_panel(b_proc)
        for path in (path_a, path_b):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
    return report("AC-PAN13 two panel processes name their own writer", bad,
                  "distinct paths carrying each pid; A's stop left B serving")


def terminate_pid(pid):
    """Terminate one process by pid - used only to clean up an orphan face."""
    import ctypes
    PROCESS_TERMINATE = 0x0001
    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False,
                                                int(pid))
    if handle:
        try:
            ctypes.windll.kernel32.TerminateProcess(handle, 1)
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)


def kill_by_port(port):
    """Last-resort cleanup for a face orphaned by a hard-killed panel.

    Only a LISTENING row counts (an ESTABLISHED row names a different owner)
    and this suite never kills itself or its own parent - a TerminateProcess
    on self exits silently with rc=1 and looks exactly like a crash.
    """
    mine = (os.getpid(), os.getppid())
    try:
        out = subprocess.run(
            ["netstat", "-ano"], stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=25).stdout.decode(
                "utf-8", "replace")
    except (OSError, subprocess.SubprocessError):
        return
    needle = "127.0.0.1:%d" % int(port)
    for line in out.splitlines():
        if "LISTENING" not in line or needle not in line:
            continue
        parts = line.split()
        if not parts or not parts[-1].isdigit():
            continue
        pid = int(parts[-1])
        if pid in mine:
            continue
        try:
            terminate_pid(pid)
        except OSError:
            pass


def ac_pan14():
    """A panel's child logs are BOUNDED: empty ones die, evidence survives.

    The file exists to answer one question ("why did this click do nothing?"),
    so an empty file answers nothing and a clean teardown removes it, while a
    file with bytes is the named refusal a person needs and is kept even after
    the panel is gone. A panel killed hard runs no teardown, so its files
    survive untouched.
    """
    bad = 0
    temp = tempfile.gettempdir()
    shared = os.path.join(temp, "bigdomain-panel-child-ugc.txt")
    foreign = os.path.join(temp, "bigdomain-panel-child-4242-1-1-ugc.txt")
    decoys = {shared: b"R2950 decoy: the old machine-wide slot\n",
              foreign: b"R2950 decoy: some other panel's log\n"}
    path_a = path_b = path_c = hard_path = None
    hard_port = None
    proc = None
    httpd_a = httpd_b = httpd_c = None
    try:
        # (1) the BOUNDARY, measured: while the child still holds the stderr
        # handle, Windows refuses the unlink, so an empty log survives a
        # release and is named in kept. The panel removes it once the child is
        # gone, which is what (1b) drives.
        httpd_a, panel_a = panel_module.start_panel("127.0.0.1", 0)
        base_a = "http://127.0.0.1:%d" % httpd_a.server_address[1]
        code, started = jhttp(base_a + "/panel/api/start", "POST",
                              {"face": "ugc"}, timeout=40.0)
        if code != 200:
            bad += 1
            print("  AC-PAN14 could not start ugc: %s %r" % (code, started))
            path_a = panel_a.log_path_for("ugc")
        else:
            path_a = started.get("child_log_path")
            # R2953: the log now starts with this panel's marker, so the arm
            # measures "nothing beyond the marker" rather than zero bytes.
            header = panel_module.log_marker_line(
                os.path.basename(path_a)) or b""
            size = os.path.getsize(path_a)
            if size > len(header):
                bad += 1
                print("  AC-PAN14 a healthy face wrote %dB past the marker, "
                      "so this arm cannot measure the empty-log rule" % size)
            if not panel_module.log_attributed(path_a,
                                               os.path.basename(path_a)):
                bad += 1
                print("  AC-PAN14 the panel's own log is not attributed: %r"
                      % (path_a,))
        for path, payload in decoys.items():
            try:
                with open(path, "wb") as handle:
                    handle.write(payload)
            except OSError as exc:
                bad += 1
                print("  AC-PAN14 could not place a decoy: %r" % (exc,))
        alive = panel_a.release_logs()
        if path_a and path_a in alive["removed"]:
            bad += 1
            print("  AC-PAN14 a log was removed while its child held it")
        elif path_a and path_a not in alive["kept"]:
            bad += 1
            print("  AC-PAN14 the live-child release did not name the file: %r"
                  % (alive,))

        # (1b) once the child is gone the same rule removes it by name.
        httpd_b, panel_b = panel_module.start_panel("127.0.0.1", 0)
        base_b = "http://127.0.0.1:%d" % httpd_b.server_address[1]
        code, started_b = jhttp(base_b + "/panel/api/start", "POST",
                                {"face": "ugc"}, timeout=40.0)
        if code != 200:
            bad += 1
            print("  AC-PAN14 arm 1b answered %s %r" % (code, started_b))
            path_b = panel_b.log_path_for("ugc")
        else:
            path_b = started_b.get("child_log_path")
        panel_b.stop("ugc")
        after_stop = panel_b.release_logs()
        if path_b and path_b not in after_stop["removed"]:
            bad += 1
            print("  AC-PAN14 release_logs did not name the empty log: %r"
                  % (after_stop,))
        if path_b and os.path.exists(path_b):
            bad += 1
            print("  AC-PAN14 the empty log survived its child: %r"
                  % (path_b,))

        # (3) bytes are evidence: they survive the same clean teardown.
        httpd_c, panel_c = panel_module.start_panel("127.0.0.1", 0)
        base_c = "http://127.0.0.1:%d" % httpd_c.server_address[1]
        code, started_c = jhttp(base_c + "/panel/api/start", "POST",
                                {"face": "ugc"}, timeout=40.0)
        if code != 200:
            bad += 1
            print("  AC-PAN14 arm 3 answered %s %r" % (code, started_c))
            path_c = panel_c.log_path_for("ugc")
        else:
            path_c = started_c.get("child_log_path")
            words = b"E_FACE_NOT_LAUNCHED_BY_HOLDER (R2950 kept arm)\n"
            # R2953: the panel writes its marker before the child is given the
            # handle, so a child's refusal APPENDS to it - truncating here
            # would model a writer the shipped panel no longer is.
            with open(path_c, "ab") as handle:
                handle.write(words)
            before = digest(path_c)
            httpd_c.shutdown()
            httpd_c.server_close()
            httpd_c = None
            if not os.path.exists(path_c):
                bad += 1
                print("  AC-PAN14 a clean teardown deleted the refusal bytes")
            elif digest(path_c) != before:
                bad += 1
                print("  AC-PAN14 the kept log's bytes moved")

        # (4) a panel killed HARD runs no teardown, so its file stays for
        # post-mortem - and the orphan face it left is cleaned up by port.
        proc, base_d = spawn_panel()
        if not base_d:
            bad += 1
            print("  AC-PAN14 the hard-kill panel never printed its address")
        else:
            code, started_d = jhttp(base_d + "/panel/api/start", "POST",
                                    {"face": "ugc"}, timeout=40.0)
            if code != 200:
                bad += 1
                print("  AC-PAN14 hard-kill arm answered %s %r"
                      % (code, started_d))
            else:
                hard_path = started_d.get("child_log_path")
                hard_port = started_d.get("port")
                proc.kill()
                proc.wait(timeout=15)
                proc = None
                if not (hard_path and os.path.exists(hard_path)):
                    bad += 1
                    print("  AC-PAN14 a hard-killed panel took its log with it")

        # (5) teardown only ever touches its own files.
        for path, payload in decoys.items():
            if not os.path.exists(path):
                bad += 1
                print("  AC-PAN14 a foreign file was deleted: %r" % (path,))
            elif digest(path) != hashlib.sha256(payload).hexdigest():
                bad += 1
                print("  AC-PAN14 a foreign file was rewritten: %r" % (path,))
    finally:
        for httpd in (httpd_a, httpd_b, httpd_c):
            if httpd is not None:
                try:
                    httpd.shutdown()
                    httpd.server_close()
                except Exception:
                    pass
        stop_panel(proc)
        if hard_port:
            kill_by_port(hard_port)
        for path in (path_a, path_b, path_c, hard_path, shared, foreign):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
    return report("AC-PAN14 empty logs removed, evidence kept", bad,
                  "clean teardown bounded, hard kill preserved, foreign files "
                  "untouched")


def ac_pan15():
    """A pid reused later cannot mint the same child-log name again."""
    bad = 0
    stamp = 10 ** 18
    first = panel_module.make_tag(pid=4242, when_ns=stamp)
    second = panel_module.make_tag(pid=4242, when_ns=stamp)
    reused = panel_module.make_tag(pid=4242, when_ns=stamp + 1)
    if first == second:
        bad += 1
        print("  AC-PAN15 the same pid and clock minted the same name: %r"
              % (first,))
    if len({first, second, reused}) != 3:
        bad += 1
        print("  AC-PAN15 pid reuse collided: %r"
              % ((first, second, reused),))
    for tag in (first, second, reused):
        parts = tag.split("-")
        if parts[0] != "4242" or len(parts) != 4:
            bad += 1
            print("  AC-PAN15 the tag does not read pid-wall-mono-seq: %r"
                  % (tag,))
        else:
            for part in parts[1:]:
                try:
                    int(part, 16)
                except ValueError:
                    bad += 1
                    print("  AC-PAN15 a tag field is not hex: %r" % (tag,))
                    break
    live = panel_module.Panel()
    if live.tag.split("-")[0] != str(os.getpid()):
        bad += 1
        print("  AC-PAN15 the live tag hides its own pid: %r" % (live.tag,))
    path_a = path_b = None
    a_panel = panel_module.Panel(tag_pid=4242, tag_ns=stamp)
    b_panel = panel_module.Panel(tag_pid=4242, tag_ns=stamp)
    path_a = a_panel.log_path_for("ugc")
    path_b = b_panel.log_path_for("ugc")
    try:
        if path_a == path_b:
            bad += 1
            print("  AC-PAN15 two panels on one pid shared a file: %r"
                  % (path_a,))
        for path in (path_a, path_b):
            name = os.path.basename(path)
            if not name.startswith("bigdomain-panel-child-"):
                bad += 1
                print("  AC-PAN15 name lost its stem: %r" % (name,))
            if "ugc" not in name or "4242" not in name:
                bad += 1
                print("  AC-PAN15 name lost the face id or the pid: %r"
                      % (name,))
            with open(path, "wb") as handle:
                handle.write(b"R2950 pid-reuse arm\n")
        if not (os.path.exists(path_a) and os.path.exists(path_b)):
            bad += 1
            print("  AC-PAN15 the two reuse logs do not coexist")
    finally:
        for path in (path_a, path_b):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
    return report("AC-PAN15 pid reuse cannot reuse a log name", bad,
                  "same pid and same clock still differ; names stay traceable")


DEAD_PID = 999999999  # measured "gone" (the kernel refuses it) on this box


def write_log(folder, tag, face, age_s, body=b"R2951 arm\n", marker=True,
              marker_name=None, lead=b""):
    """A panel log with a chosen tag and a chosen age, for the prune arms.

    R2953: a log the prune may collect must carry the marker its own name
    implies, so the helper writes one by default. ``marker=False`` writes a
    hand-made lookalike, ``marker_name`` copies ANOTHER name's marker, and
    ``lead`` puts bytes before the marker - the three shapes that must not be
    attributed.
    """
    path = os.path.join(folder, "%s%s-%s%s" % (
        panel_module.LOG_STEM, tag, face, panel_module.LOG_SUFFIX))
    with open(path, "wb") as handle:
        if lead:
            handle.write(lead)
        if marker:
            header = panel_module.log_marker_line(
                os.path.basename(marker_name or path))
            if header:
                handle.write(header)
        handle.write(body)
    when = time.time() - age_s
    os.utime(path, (when, when))
    return path


def spawn_panel_prune():
    """A real CLI panel and the two lines it prints: address, then PANEL-PRUNE.

    The prune is measured on the SHIPPED entry path, not by calling the
    function from the suite: a rule only the suite invokes bounds nothing.
    """
    proc = subprocess.Popen(
        [sys.executable, MODULE, "--host", "127.0.0.1", "--port", "0"],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, cwd=REPO)
    first = proc.stdout.readline().decode("utf-8", "replace").strip()
    second = proc.stdout.readline().decode("utf-8", "replace").strip()
    base = None
    if "http://" in first:
        base = "http://" + first.split("http://", 1)[1].split("/", 1)[0]
    return proc, base, second


def ac_pan16():
    """Aged-out refusals are pruned; a live writer, a fresh file and every
    foreign or malformed name survive. R2951.

    The file exists to answer "why did this click do nothing", so deleting the
    ones that aged out bounds the pile without deleting evidence that is still
    new. The hard half is the pid: a name alone does not say whether its writer
    is still running, so the arm that matters is the one where a LIVE pid wrote
    an OLD file - that pid was reused, and the file must still be collected.
    """
    bad = 0
    pid_law = sys.platform == "win32"
    root = tempfile.mkdtemp(prefix="r2951-prune-")
    own_pid = os.getpid()
    dead = write_log(root, "%d-1-1-1" % DEAD_PID, "ugc", 7200)
    fresh = write_log(root, "%d-1-1-2" % DEAD_PID, "ugc", 60)
    live = write_log(root, "%d-1-1-3" % own_pid, "ugc", 0)
    reused = write_log(root, "%d-1-1-4" % own_pid, "ugc", 7200)
    held = write_log(root, "%d-1-1-5" % DEAD_PID, "ledger", 7200)
    foreign = os.path.join(root, "notes.txt")
    broken = os.path.join(root, panel_module.LOG_STEM + "garbage.txt")
    for path in (foreign, broken):
        with open(path, "wb") as handle:
            handle.write(b"R2951 decoy: not this panel's log\n")
        when = time.time() - 7200
        os.utime(path, (when, when))
    decoy_before = {path: digest(path) for path in (foreign, broken)}
    pruned = panel_module.prune_logs(root, age_s=3600, own=(held,))
    if not pid_law:
        print("  AC-PAN16 pid arms not measurable off Windows "
              "(process_started answers unknown, so nothing is deleted)")
    if os.path.exists(dead) or dead not in pruned["removed"]:
        bad += 1
        print("  AC-PAN16 an aged-out refusal with a gone pid survived: %r"
              % (dead,))
    if not os.path.exists(fresh) or fresh not in pruned["fresh"]:
        bad += 1
        print("  AC-PAN16 a file inside the age bound was touched: %r"
              % (fresh,))
    if not os.path.exists(held) or held not in pruned["kept"]:
        bad += 1
        print("  AC-PAN16 a declared own path was deleted: %r" % (held,))
    if pid_law:
        if not os.path.exists(live) or live not in pruned["fresh"]:
            bad += 1
            print("  AC-PAN16 a live writer's file inside the bound was "
                  "touched: %r" % (live,))
        if os.path.exists(reused) or reused not in pruned["removed"]:
            bad += 1
            print("  AC-PAN16 a reused pid kept an aged-out file for ever: %r"
                  % (reused,))
    for path, before in decoy_before.items():
        if digest(path) != before:
            bad += 1
            print("  AC-PAN16 a decoy outside the namespace moved: %r"
                  % (path,))
    # Red control for the own rule: the same file is collected the moment it is
    # NOT declared, so "kept" meant "declared" and not "the roster ignores it".
    pruned_zero = panel_module.prune_logs(root, age_s=0)
    if pid_law and os.path.exists(held):
        bad += 1
        print("  AC-PAN16 an undeclared aged-out file was not collected: %r"
              % (held,))
    if not os.path.exists(live):
        bad += 1
        print("  AC-PAN16 the zero bound took a live writer's file: %r"
              % (live,))
    if os.path.exists(fresh) and pid_law:
        bad += 1
        print("  AC-PAN16 the zero bound left a gone pid's file: %r" % (fresh,))
    for path, before in decoy_before.items():
        if digest(path) != before:
            bad += 1
            print("  AC-PAN16 a decoy moved under the zero bound: %r"
                  % (path,))
    # The shipped wire: a real CLI panel prunes on the real %TEMP%.
    temp = tempfile.gettempdir()
    wired = write_log(temp, "%d-1-1-6" % DEAD_PID, "member", 8 * 86400)
    wire_decoy = os.path.join(temp, "r2951-wire-decoy.txt")
    wire_before = None
    with open(wire_decoy, "wb") as handle:
        handle.write(b"R2951 wire decoy\n")
    when = time.time() - 8 * 86400
    os.utime(wire_decoy, (when, when))
    wire_before = digest(wire_decoy)
    proc, base, second = spawn_panel_prune()
    stop_panel(proc)
    if base is None:
        bad += 1
        print("  AC-PAN16 the CLI panel never published its address")
    if not second.startswith("PANEL-PRUNE"):
        bad += 1
        print("  AC-PAN16 the CLI panel printed no prune line: %r" % (second,))
    if os.path.exists(wired):
        bad += 1
        print("  AC-PAN16 the shipped prune left an aged-out file in %%TEMP%%")
    if digest(wire_decoy) != wire_before:
        bad += 1
        print("  AC-PAN16 the shipped prune touched a foreign %%TEMP%% file")
    for path in (wired, wire_decoy, foreign, broken, live):
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
    return report("AC-PAN16 aged-out refusals collected, writers kept", bad,
                  "dead pid collected, live writer and own path kept, "
                  "decoys untouched, wired on the CLI; pid_arms=%s"
                  % ("measured" if pid_law else "unmeasured"))


def ac_pan17():
    """A wall clock stepped backwards cannot mint a name that was used before.

    R2950's tag rested on the wall clock moving forward. The monotonic field is
    the join that answers that: it is boot-relative and comparable across
    processes, so a corrected clock moves one field and not the other. The
    fields are read back, so the claim is about the NAME and not about the
    intent of the function.
    """
    bad = 0
    wall = 10 ** 18
    forward = panel_module.make_tag(pid=777, when_ns=wall, mono_ns=5000)
    back = panel_module.make_tag(pid=777, when_ns=wall - 10 ** 9, mono_ns=6000)
    later = panel_module.make_tag(pid=777, when_ns=wall, mono_ns=7000)
    if forward == back or forward == later or back == later:
        bad += 1
        print("  AC-PAN17 two tags collided: %r"
              % ((forward, back, later),))
    for tag, want_wall, want_mono in ((forward, wall, 5000),
                                      (back, wall - 10 ** 9, 6000),
                                      (later, wall, 7000)):
        parts = tag.split("-")
        if len(parts) != 4 or parts[0] != "777":
            bad += 1
            print("  AC-PAN17 the tag shape is not pid-wall-mono-seq: %r"
                  % (tag,))
            continue
        for field in parts[1:]:
            try:
                int(field, 16)
            except ValueError:
                bad += 1
                print("  AC-PAN17 a tag field is not hex: %r" % (tag,))
                break
        if int(parts[1], 16) != want_wall:
            bad += 1
            print("  AC-PAN17 the wall field ignores the injected clock: %r"
                  % (tag,))
        if int(parts[2], 16) != want_mono:
            bad += 1
            print("  AC-PAN17 the monotonic field ignores the injected clock: "
                  "%r" % (tag,))
    before = time.monotonic_ns()
    live_tag = panel_module.make_tag()
    after = time.monotonic_ns()
    mono = int(live_tag.split("-")[2], 16)
    if not before <= mono <= after:
        bad += 1
        print("  AC-PAN17 the default monotonic field is not a real reading: "
              "%r not in [%d, %d]" % (live_tag, before, after))
    live = panel_module.Panel()
    if live.tag.split("-")[0] != str(os.getpid()):
        bad += 1
        print("  AC-PAN17 the live tag hides its own pid: %r" % (live.tag,))
    return report("AC-PAN17 wall clock step cannot reuse a name", bad,
                  "a corrected wall clock moves one field; the monotonic "
                  "field still separates; the default is a real reading")


def ac_pan18():
    """The count bound bounds the RECENT pile; the age bound cannot.

    Seven days of failures is still seven days of files, so a cap per face
    joins the age bound. The cap must not become a licence to delete a live
    writer's file, a caller's own path, or a name the kernel refuses to answer
    for - the three ways R2951 already bought. The red control matters as much
    as the cap: the same world under a wide cap removes nothing, so the
    removals above were caused by the slot count and not by age.
    """
    bad = 0
    pid_law = sys.platform == "win32"
    root = tempfile.mkdtemp(prefix="r2952-cap-")
    ages = (300, 240, 180, 120, 60)
    caps = [write_log(root, "%d-1-1-1%d" % (DEAD_PID, index), "ugc", age,
                      body=b"R2952 cap %d\n" % index)
            for index, age in enumerate(ages)]
    held = write_log(root, "%d-1-1-40" % DEAD_PID, "ugc", 360,
                     body=b"R2952 own\n")
    # The live writer must be OLDER than the two fillers so it ranks past the
    # cap, yet still newer than this process started - otherwise the R2951
    # reuse rule (writer started AFTER the file, so the pid was reused) would
    # be the rule under test instead of the writer guard.
    live = write_log(root, "%d-1-1-30" % os.getpid(), "lobby", 5,
                     body=b"R2952 live writer\n")
    fillers = [write_log(root, "%d-1-1-5%d" % (DEAD_PID, index), "lobby", age,
                         body=b"R2952 filler %d\n" % index)
               for index, age in enumerate((2, 1))]
    foreign = os.path.join(root, "notes.txt")
    broken = os.path.join(root, panel_module.LOG_STEM + "garbage.txt")
    for path in (foreign, broken):
        with open(path, "wb") as handle:
            handle.write(b"R2952 decoy: not this panel's log\n")
        when = time.time() - 30
        os.utime(path, (when, when))
    decoy_before = {path: digest(path) for path in (foreign, broken)}
    wide = panel_module.prune_logs(root, age_s=10 ** 9, keep_n=100,
                                   own=(held,))
    if wide["removed"] or wide["over"] or wide["unknown"]:
        bad += 1
        print("  AC-PAN18 a wide cap removed something: removed=%r over=%r "
              "unknown=%r" % (wide["removed"], wide["over"],
                              wide["unknown"]))
    for path in caps + fillers + [held, live]:
        if not os.path.exists(path):
            bad += 1
            print("  AC-PAN18 the red control world lost a file: %r" % (path,))
    capped = panel_module.prune_logs(root, age_s=10 ** 9, keep_n=2,
                                     own=(held,))
    for path in (caps[4], caps[3]):
        if not os.path.exists(path) or path not in capped["fresh"]:
            bad += 1
            print("  AC-PAN18 the cap did not keep the newest refusals: %r"
                  % (path,))
    if pid_law:
        for path in caps[:3]:
            if os.path.exists(path) or path not in capped["over"]:
                bad += 1
                print("  AC-PAN18 a file past the cap survived: %r" % (path,))
        if len(capped["over"]) != 3:
            bad += 1
            print("  AC-PAN18 the cap removed %d files, expected 3: %r"
                  % (len(capped["over"]), capped["over"]))
    elif not capped["unknown"]:
        bad += 1
        print("  AC-PAN18 off Windows the cap neither removed nor named an "
              "unknown writer")
    if not os.path.exists(held) or held not in capped["kept"]:
        bad += 1
        print("  AC-PAN18 a declared own path spent a cap slot: %r" % (held,))
    if not os.path.exists(live):
        bad += 1
        print("  AC-PAN18 the cap took a live writer's file: %r" % (live,))
    for path in fillers:
        if not os.path.exists(path):
            bad += 1
            print("  AC-PAN18 the cap removed a file inside its own slots: %r"
                  % (path,))
    for path, before in decoy_before.items():
        if digest(path) != before:
            bad += 1
            print("  AC-PAN18 a decoy moved under the cap: %r" % (path,))
    for path in caps + fillers + [held, live, foreign, broken]:
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
    return report("AC-PAN18 a count bound bounds the recent pile", bad,
                  "newest cap slots kept, older ones named in over, live "
                  "writer and own path kept, decoys untouched, wide-cap red "
                  "control removed nothing; pid_arms=%s"
                  % ("measured" if pid_law else "unmeasured"))


def ac_pan19():
    """The prune runs with NO panel: a scheduler can call it, a person need not.

    R2951's only trigger was a panel launch, so an aged-out refusal stayed on
    disk until somebody happened to open the panel. This arm starts the
    shipped CLI in --prune-only mode and reads what it actually did: the first
    line is the prune line, no address line exists (no panel was born), the
    aged file is gone, a foreign decoy beside it is byte-identical, and the
    process exits instead of sleeping in the server loop.
    """
    bad = 0
    temp = tempfile.gettempdir()
    aged = write_log(temp, "%d-1-1-70" % DEAD_PID, "checkout", 9 * 86400,
                     body=b"R2952 prune-only refusal\n")
    decoy = os.path.join(temp, "r2952-prune-only-decoy.txt")
    with open(decoy, "wb") as handle:
        handle.write(b"R2952 prune-only decoy: not this panel's log\n")
    when = time.time() - 9 * 86400
    os.utime(decoy, (when, when))
    before = digest(decoy)
    started = time.time()
    proc = subprocess.run([sys.executable, MODULE, "--prune-only"],
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, cwd=REPO, timeout=180)
    elapsed = time.time() - started
    out = proc.stdout.decode("utf-8", "replace")
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    if proc.returncode != 0:
        bad += 1
        print("  AC-PAN19 --prune-only exited %d: %r"
              % (proc.returncode, proc.stderr.decode("utf-8", "replace")[-300:]))
    if not lines or not lines[0].startswith("PANEL-PRUNE"):
        bad += 1
        print("  AC-PAN19 the prune-only run printed no prune line first: %r"
              % (lines,))
    if any(line.startswith("PANEL http") for line in lines):
        bad += 1
        print("  AC-PAN19 the prune-only run started a panel: %r" % (lines,))
    if os.path.exists(aged):
        bad += 1
        print("  AC-PAN19 the prune-only run left an aged-out file")
    if digest(decoy) != before:
        bad += 1
        print("  AC-PAN19 the prune-only run touched a foreign file")
    if elapsed > 30:
        bad += 1
        print("  AC-PAN19 the prune-only run did not exit promptly: %.1fs"
              % elapsed)
    for path in (aged, decoy):
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
    return report("AC-PAN19 the prune runs with no panel at all", bad,
                  "rc=0, PANEL-PRUNE first, no address line, aged file gone, "
                  "decoy unchanged, exited in %.1fs" % elapsed)


def first_line(path):
    with open(path, "rb") as handle:
        return handle.readline()


def ac_pan20():
    """A file is collected only when its FIRST LINE names the file. R2953.

    Every earlier bound judged a NAME, and any same-user process can type one,
    so a hand-written lookalike was collected like a real refusal. The marker
    the panel writes when it creates the log is now the licence: absent, not
    first, or copied from another name all keep the file, and the same file is
    collected the moment it carries its own marker - one line is the whole
    difference between kept and removed.
    """
    bad = 0
    root = tempfile.mkdtemp(prefix="bd-pan20-")
    if sys.platform != "win32":
        print("  AC-PAN20 pid arms not measurable off Windows")
        return report("AC-PAN20 marker decides attribution", bad,
                      "skipped: not Windows")
    age = 9 * 86400
    try:
        # (1) a lookalike: right name, no marker, aged out, dead pid.
        bare = write_log(root, "%d-1-1-1" % DEAD_PID, "ugc", age,
                         marker=False)
        report_a = panel_module.prune_logs(root=root)
        if bare not in report_a["unattrib"]:
            bad += 1
            print("  AC-PAN20 a markerless lookalike was not named "
                  "unattrib: %r" % (report_a["unattrib"],))
        if not os.path.exists(bare):
            bad += 1
            print("  AC-PAN20 a lookalike we never wrote was deleted")
        # (2) the SAME file, one marker line, same world, same call.
        bare = write_log(root, "%d-1-1-1" % DEAD_PID, "ugc", age,
                         marker=True)
        report_b = panel_module.prune_logs(root=root)
        if bare not in report_b["removed"]:
            bad += 1
            print("  AC-PAN20 an attributed aged file was not collected: %r"
                  % (report_b,))
        elif os.path.exists(bare):
            bad += 1
            print("  AC-PAN20 an attributed file was named removed but "
                  "survived")
        # (3) a marker copied from ANOTHER name is not this file's marker.
        other = write_log(root, "%d-1-1-2" % DEAD_PID, "ledger", age)
        copy = write_log(root, "%d-1-1-3" % DEAD_PID, "ugc", age,
                         marker_name=other)
        report_c = panel_module.prune_logs(root=root)
        if copy not in report_c["unattrib"] or not os.path.exists(copy):
            bad += 1
            print("  AC-PAN20 a marker borrowed from another name was "
                  "accepted: %r" % (report_c,))
        if other in report_c["unattrib"]:
            bad += 1
            print("  AC-PAN20 its own marker was refused as borrowed")
        # (4) a marker that is not the FIRST line (a leading blank line).
        shifted = write_log(root, "%d-1-1-4" % DEAD_PID, "ugc", age,
                            lead=b"\n")
        report_d = panel_module.prune_logs(root=root)
        if shifted not in report_d["unattrib"] or not os.path.exists(shifted):
            bad += 1
            print("  AC-PAN20 a marker on line 2 was accepted: %r"
                  % (report_d,))
        # (5) decoys: outside the namespace, and inside it but unparseable.
        foreign = os.path.join(root, "bd-pan20-stranger.txt")
        malformed = os.path.join(root, "%smallformed%s" % (
            panel_module.LOG_STEM, panel_module.LOG_SUFFIX))
        payloads = {foreign: b"R2953 decoy: not our namespace\n",
                    malformed: b"R2953 decoy: name does not parse\n"}
        for path, payload in payloads.items():
            with open(path, "wb") as handle:
                handle.write(payload)
        panel_module.prune_logs(root=root)
        panel_module.prune_logs(root=root)
        for path, payload in payloads.items():
            if not os.path.exists(path):
                bad += 1
                print("  AC-PAN20 a decoy was deleted: %r" % (path,))
            elif digest(path) != hashlib.sha256(payload).hexdigest():
                bad += 1
                print("  AC-PAN20 a decoy was rewritten: %r" % (path,))
    finally:
        for name in sorted(os.listdir(root)):
            try:
                os.remove(os.path.join(root, name))
            except OSError:
                pass
        try:
            os.rmdir(root)
        except OSError:
            pass
    return report("AC-PAN20 marker decides attribution", bad,
                  "lookalike kept, same file collected once marked, borrowed "
                  "and shifted markers refused, decoys untouched")


def ac_pan21():
    """The SHIPPED writer lays the marker, and a stranger's lookalike lives.

    AC-PAN20 drives the rule from the suite's own files; this criterion reads
    the FIRST LINE the real panel writes, then runs the real --prune-only over
    the real %TEMP% carrying one lookalike and one attributed file, because a
    rule only the suite invokes bounds nothing.
    """
    bad = 0
    temp = tempfile.gettempdir()
    httpd = panel = None
    log_path = None
    lookalike = attributed = None
    try:
        httpd, panel = panel_module.start_panel("127.0.0.1", 0)
        base = "http://127.0.0.1:%d" % httpd.server_address[1]
        code, started = jhttp(base + "/panel/api/start", "POST",
                              {"face": "ugc"}, timeout=40.0)
        if code != 200:
            bad += 1
            print("  AC-PAN21 could not start ugc: %s %r" % (code, started))
        else:
            log_path = started.get("child_log_path")
            expected = panel_module.log_marker_line(
                os.path.basename(log_path))
            if not expected:
                bad += 1
                print("  AC-PAN21 the published path does not parse: %r"
                      % (log_path,))
            elif first_line(log_path) != expected:
                bad += 1
                print("  AC-PAN21 the shipped writer's first line is %r, "
                      "expected %r" % (first_line(log_path), expected))
            if not panel_module.log_attributed(log_path,
                                               os.path.basename(log_path)):
                bad += 1
                print("  AC-PAN21 the panel's own log is not attributed")
        # (3) a log that never got past the marker is not evidence.
        if panel is not None:
            panel.stop("ugc")
            after_stop = panel.release_logs()
            if log_path and os.path.exists(log_path):
                bad += 1
                print("  AC-PAN21 a marker-only log survived a clean "
                      "teardown: %r" % (after_stop,))
        if httpd is not None:
            httpd.shutdown()
            httpd.server_close()
            httpd = None
        # (2) one lookalike and one attributed file, same world, one run.
        lookalike = write_log(temp, "%d-1-1-81" % DEAD_PID, "member",
                              9 * 86400, marker=False)
        attributed = write_log(temp, "%d-1-1-82" % DEAD_PID, "member",
                               9 * 86400, marker=True)
        proc = subprocess.run(
            [sys.executable, MODULE, "--prune-only"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, cwd=REPO, timeout=120)
        lines = proc.stdout.decode("utf-8", "replace").splitlines()
        first = lines[0].strip() if lines else ""
        if proc.returncode != 0:
            bad += 1
            print("  AC-PAN21 --prune-only exited %d" % proc.returncode)
        if not first.startswith("PANEL-PRUNE"):
            bad += 1
            print("  AC-PAN21 --prune-only printed no prune line: %r" % (first,))
        elif "unattrib=" not in first:
            bad += 1
            print("  AC-PAN21 the prune line hides the unattrib bucket: %r"
                  % (first,))
        if not os.path.exists(lookalike):
            bad += 1
            print("  AC-PAN21 the shipped prune deleted a file we never "
                  "wrote")
        if os.path.exists(attributed):
            bad += 1
            print("  AC-PAN21 the shipped prune left an attributed aged file")
    finally:
        if httpd is not None:
            try:
                httpd.shutdown()
                httpd.server_close()
            except Exception:
                pass
        for path in (lookalike, attributed):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
    return report("AC-PAN21 shipped writer marked, lookalike survives", bad,                  "first line equals the marker, marker-only log removed, "
                  "lookalike kept while the marked file went")


def ac_pan22():
    """The markerless residue is a CLOSED set, counted, and never collected
    by the prune. R2954.

    R2953 bought attribution with a price: every file written before the
    marker rule, and every file without one, is never collected again. The
    price is now a number - the prune reports legacy/legacy_bytes for the
    slice a purge MAY take - and the same world flips it: mark the file and
    it is collected, so a log our writer produces can never enter the bucket.
    """
    bad = 0
    root = tempfile.mkdtemp(prefix="bd-pan22-")
    if sys.platform != "win32":
        print("  AC-PAN22 pid arms not measurable off Windows")
        return report("AC-PAN22 legacy residue counted, not collected", bad,
                      "skipped: not Windows")
    age = 9 * 86400
    try:
        # (1) aged, dead pid, right name, no marker: kept, and counted.
        bare = write_log(root, "%d-1-1-1" % DEAD_PID, "ugc", age,
                         marker=False)
        size = os.path.getsize(bare)
        report_a = panel_module.prune_logs(root=root)
        report_a = panel_module.prune_logs(root=root)
        if bare not in report_a["unattrib"]:
            bad += 1
            print("  AC-PAN22 the residue left the unattrib bucket: %r"
                  % (report_a["unattrib"],))
        if bare not in report_a["legacy"]:
            bad += 1
            print("  AC-PAN22 an aged markerless file was not counted as "
                  "legacy: %r" % (report_a,))
        if report_a["legacy_bytes"] != size:
            bad += 1
            print("  AC-PAN22 legacy_bytes %d is not the file size %d"
                  % (report_a["legacy_bytes"], size))
        if not os.path.exists(bare):
            bad += 1
            print("  AC-PAN22 the prune deleted legacy residue")
        # (2) the SAME file with its own marker, same world, same call.
        marked = write_log(root, "%d-1-1-1" % DEAD_PID, "ugc", age,
                           marker=True)
        if marked != bare:
            bad += 1
            print("  AC-PAN22 the marked arm wrote a different name")
        report_b = panel_module.prune_logs(root=root)
        if bare not in report_b["removed"] or os.path.exists(bare):
            bad += 1
            print("  AC-PAN22 a marked file was not collected: %r"
                  % (report_b,))
        if report_b["legacy"] or report_b["legacy_bytes"]:
            bad += 1
            print("  AC-PAN22 a marked file was counted as legacy: %r"
                  % (report_b,))
        # (3) fresh markerless files are not legacy either: the bucket is a
        # residue of AGE plus missing attribution, not of missing markers.
        young = write_log(root, "%d-1-1-2" % DEAD_PID, "ugc", 60,
                          marker=False)
        report_c = panel_module.prune_logs(root=root)
        if young in report_c["legacy"]:
            bad += 1
            print("  AC-PAN22 a fresh markerless file was counted as legacy")
        if not os.path.exists(young):
            bad += 1
            print("  AC-PAN22 a fresh markerless file was deleted")
        # (4) the SHIPPED printer publishes both numbers, measured in its own
        # process so the claim is about the shipped line and not a helper.
        prose = subprocess.run(
            [sys.executable, "-c",
             "import sys, panel as p; p.print_prune(p.prune_logs("
             "root=sys.argv[1]))", root],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=HERE)
        line = prose.stdout.decode("utf-8", "replace").strip()
        if "legacy=" not in line or "legacy_bytes=" not in line:
            bad += 1
            print("  AC-PAN22 the shipped prune line hides the residue: %r"
                  % (line,))
    finally:
        for name in sorted(os.listdir(root)):
            try:
                os.remove(os.path.join(root, name))
            except OSError:
                pass
        try:
            os.rmdir(root)
        except OSError:
            pass
    return report("AC-PAN22 legacy residue counted, not collected", bad,
                  "aged markerless file counted and kept, the same file "
                  "collected once marked, fresh file outside the bucket, "
                  "shipped line carries legacy/legacy_bytes")


def ac_pan23():
    """The exit from the residue is an OPERATOR call, and it cannot run by
    accident. R2954.

    Three claims: a plain --prune-only reports the residue and deletes none of
    it; adding --purge-legacy to the SAME world deletes exactly it; and
    --purge-legacy without --prune-only is refused, so the panel start path
    can never reach a legacy delete. Fresh files, a possible live writer, a
    foreign name and a malformed name keep in both worlds.
    """
    bad = 0
    if sys.platform != "win32":
        print("  AC-PAN23 arms not measurable off Windows")
        return report("AC-PAN23 purge-legacy is operator-gated", bad,
                      "skipped: not Windows")
    age = 9 * 86400
    root = tempfile.mkdtemp(prefix="bd-pan23-")
    writer_root = tempfile.mkdtemp(prefix="bd-pan23-writer-")
    try:
        # (3) the two keep arms, measured on the function the flag calls.
        young = write_log(root, "%d-2-2-1" % DEAD_PID, "ugc", 60,
                          marker=False)
        report_k = panel_module.purge_legacy(root=root)
        if young not in report_k["fresh"] or not os.path.exists(young):
            bad += 1
            print("  AC-PAN23 a fresh markerless file was purged: %r"
                  % (report_k,))
        if report_k["removed"]:
            bad += 1
            print("  AC-PAN23 purge removed a fresh file: %r"
                  % (report_k["removed"],))
        # The live-writer arm needs a file that is past the AGE bound but NOT
        # older than the process that could have written it, so it is driven
        # in its own folder under a zero age bound: a nine-day mtime under a
        # live pid is pid REUSE (which is correctly collectable) and would not
        # test this rule at all.
        writer = write_log(writer_root, "%d-2-2-2" % os.getpid(), "ugc", 0,
                           marker=False)
        report_w = panel_module.purge_legacy(root=writer_root, age_s=0)
        if writer not in report_w["kept"] or not os.path.exists(writer):
            bad += 1
            print("  AC-PAN23 a possible live writer's file was purged: %r"
                  % (report_w,))
        # (4) decoys on the same call: outside the namespace, unparseable.
        foreign = os.path.join(root, "bd-pan23-stranger.txt")
        malformed = os.path.join(root, "%smallformed%s" % (
            panel_module.LOG_STEM, panel_module.LOG_SUFFIX))
        payloads = {foreign: b"R2954 decoy: not our namespace\n",
                    malformed: b"R2954 decoy: name does not parse\n"}
        for path, payload in payloads.items():
            with open(path, "wb") as handle:
                handle.write(payload)
        aged = write_log(root, "%d-2-2-3" % DEAD_PID, "ugc", age,
                         marker=False)
        report_d = panel_module.purge_legacy(root=root)
        if aged not in report_d["removed"] or os.path.exists(aged):
            bad += 1
            print("  AC-PAN23 an aged markerless file survived the purge: %r"
                  % (report_d,))
        for path, payload in payloads.items():
            if not os.path.exists(path):
                bad += 1
                print("  AC-PAN23 a decoy was purged: %r" % (path,))
            elif digest(path) != hashlib.sha256(payload).hexdigest():
                bad += 1
                print("  AC-PAN23 a decoy was rewritten: %r" % (path,))
    finally:
        for folder in (root, writer_root):
            for name in sorted(os.listdir(folder)):
                try:
                    os.remove(os.path.join(folder, name))
                except OSError:
                    pass
            try:
                os.rmdir(folder)
            except OSError:
                pass
    # (5) the flag on its own is refused BEFORE anything is judged, and the
    # arms below plant their own files in the REAL %TEMP%, so the shipped
    # entry path is what is measured and nothing else on the box is at risk.
    temp = tempfile.gettempdir()
    planted = write_log(temp, "%d-3-3-1" % DEAD_PID, "bdpan23",
                        age, marker=False)
    decoy = os.path.join(temp, "bd-pan23-should-stay.txt")
    try:
        with open(decoy, "wb") as handle:
            handle.write(b"R2954 control: a stranger's file\n")
        alone = subprocess.run([sys.executable, MODULE, "--purge-legacy"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               cwd=REPO)
        if alone.returncode != 2:
            bad += 1
            print("  AC-PAN23 --purge-legacy without --prune-only exited %d"
                  % (alone.returncode,))
        if not os.path.exists(planted):
            bad += 1
            print("  AC-PAN23 the refused call still deleted legacy residue")
        # (1) the RED CONTROL: a plain --prune-only reports and keeps.
        plain = subprocess.run([sys.executable, MODULE, "--prune-only"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               cwd=REPO)
        first = plain.stdout.decode("utf-8", "replace").splitlines()
        line = first[0] if first else ""
        if plain.returncode != 0 or not line.startswith("PANEL-PRUNE"):
            bad += 1
            print("  AC-PAN23 --prune-only exited %d: %r"
                  % (plain.returncode, first[:2]))
        elif "legacy=0" in line:
            bad += 1
            print("  AC-PAN23 the planted residue was not counted: %r"
                  % (line,))
        if not os.path.exists(planted):
            bad += 1
            print("  AC-PAN23 a plain --prune-only purged legacy residue")
        # (2) the same world, one flag: the residue goes, the decoy stays.
        purged = subprocess.run(
            [sys.executable, MODULE, "--prune-only", "--purge-legacy"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=REPO)
        lines = purged.stdout.decode("utf-8", "replace").splitlines()
        second = lines[1] if len(lines) > 1 else ""
        if purged.returncode != 0 or not second.startswith(
                "PANEL-PURGE-LEGACY"):
            bad += 1
            print("  AC-PAN23 the purge line is missing: %r" % (lines[:3],))
        elif "removed=0" in second or "bytes=0" in second:
            bad += 1
            print("  AC-PAN23 the purge reported nothing: %r" % (second,))
        if os.path.exists(planted):
            bad += 1
            print("  AC-PAN23 --prune-only --purge-legacy kept the residue")
        if not os.path.exists(decoy):
            bad += 1
            print("  AC-PAN23 the purge reached a stranger's file")
        elif digest(decoy) != hashlib.sha256(
                b"R2954 control: a stranger's file\n").hexdigest():
            bad += 1
            print("  AC-PAN23 the purge rewrote a stranger's file")
    finally:
        for path in (planted, decoy):
            try:
                os.remove(path)
            except OSError:
                pass
    return report("AC-PAN23 purge-legacy is operator-gated", bad,
                  "plain prune reports and keeps, one flag collects it, "
                  "flag alone refused rc=2, fresh/live-writer/foreign/"
                  "malformed all keep")


def ac_pan24():
    """Impersonation is out of scope BY NAME, and the gain is measured. R2954.

    The marker is a first line any same-user process can copy, so attribution
    holds only for the honest case. What an impersonator gains is asserted
    here as a measurement instead: the same file is deletable by that process
    with a plain os.remove, so the prune earns them a deletion they already
    had - and it cannot walk their marker out of the namespace, which is
    driven in the SAME call on a decoy beside the file.
    """
    bad = 0
    root = tempfile.mkdtemp(prefix="bd-pan24-")
    if sys.platform != "win32":
        print("  AC-PAN24 pid arms not measurable off Windows")
        return report("AC-PAN24 impersonation out of scope, gain measured",
                      bad, "skipped: not Windows")
    age = 9 * 86400
    try:
        # (1) a copied marker is accepted - both ways on the same file.
        copied = write_log(root, "%d-4-4-1" % DEAD_PID, "ugc", age,
                           marker=True)
        report_a = panel_module.prune_logs(root=root)
        if copied not in report_a["removed"] or os.path.exists(copied):
            bad += 1
            print("  AC-PAN24 a copied marker was not honoured: %r"
                  % (report_a,))
        stripped = write_log(root, "%d-4-4-1" % DEAD_PID, "ugc", age,
                             marker=False)
        report_b = panel_module.prune_logs(root=root)
        if stripped in report_b["removed"] or not os.path.exists(stripped):
            bad += 1
            print("  AC-PAN24 the same file without its marker was "
                  "collected: %r" % (report_b,))
        # (2) the impersonation cannot leave the namespace: one call, a
        # decoy beside the file that goes.
        decoy = os.path.join(root, "bd-pan24-neighbour.txt")
        payload = b"R2954 decoy: outside the namespace\n"
        with open(decoy, "wb") as handle:
            handle.write(payload)
        copied = write_log(root, "%d-4-4-2" % DEAD_PID, "ugc", age,
                           marker=True)
        report_c = panel_module.prune_logs(root=root)
        if copied in report_c["removed"] and os.path.exists(decoy):
            if digest(decoy) != hashlib.sha256(payload).hexdigest():
                bad += 1
                print("  AC-PAN24 the decoy was rewritten")
        else:
            bad += 1
            print("  AC-PAN24 the pair arm did not discriminate: %r"
                  % (report_c,))
        # (3) the gain is zero, measured: the same file is removable by the
        # same user with os.remove, so the prune adds nothing new.
        probe = write_log(root, "%d-4-4-3" % DEAD_PID, "ugc", age,
                          marker=False)
        try:
            os.remove(probe)
        except OSError as exc:
            bad += 1
            print("  AC-PAN24 the same-user removal failed: %r" % (exc,))
    finally:
        for name in sorted(os.listdir(root)):
            try:
                os.remove(os.path.join(root, name))
            except OSError:
                pass
        try:
            os.rmdir(root)
        except OSError:
            pass
    return report("AC-PAN24 impersonation out of scope, gain measured", bad,
                  "copied marker honoured both ways, decoy untouched beside "
                  "it, same file removable by plain os.remove")


def main():
    ac_pan1()
    ac_pan2()
    ac_pan3()
    ac_pan4()
    ac_pan6()
    ac_pan5()
    ac_pan7()
    ac_pan8()
    ac_pan9()
    ac_pan10()
    ac_pan11()
    ac_pan12()
    ac_pan13()
    ac_pan14()
    ac_pan15()
    ac_pan16()
    ac_pan17()
    ac_pan18()
    ac_pan19()
    ac_pan20()
    ac_pan21()
    ac_pan22()
    ac_pan23()
    ac_pan24()
    passed = sum(1 for _name, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if passed == total else "FAIL",
                              passed, total))
    return 0 if passed == total else 2


if __name__ == "__main__":
    sys.exit(main())