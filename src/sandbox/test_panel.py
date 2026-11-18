"""Suite for the sandbox control panel (BigDomain R2481).

Six criteria AC-PAN1..AC-PAN6 pre-registered in the R2481 backlog row BEFORE
this file, src/sandbox/panel.py and its registry row existed. Five more -
AC-PAN7..AC-PAN11 - were pre-registered in the R2938 backlog row BEFORE the
ownership declaration existed, because the launcher used to leave the panel
blind and a page click could start a SECOND lobby beside the running one.
AC-PAN12..AC-PAN13 were pre-registered in the R2949 row BEFORE the per-panel
log namespace existed: R2948 kept each child's stderr (the only place a named
refusal can come from) in ONE machine-wide file per face id, so a second panel
silently overwrote the first one's evidence.

Nothing here is read off a canned string: the panel is really started, the
start route really spawns a shipped module, an independent TCP connect checks
the port it reports, the served URL is compared against the page bytes on
disk, and the teardown leg proves the children are gone.

Usage: python test_panel.py
Exit: 0 = SUITE PASS 13/13, 2 = FAIL.
"""

import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
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
    passed = sum(1 for _name, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if passed == total else "FAIL",
                              passed, total))
    return 0 if passed == total else 2


if __name__ == "__main__":
    sys.exit(main())