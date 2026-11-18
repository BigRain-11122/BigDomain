"""Sandbox control panel: the one door that can actually START a face.

R2477 shipped one terminal command that brings every face up, and said plainly
what it did not do: the hub page is read-only, so a person in a browser could
never start anything. Every card it published ended in "start this yourself",
and a face started from a terminal stayed invisible to any page.

This module closes that. It serves one page with a Start and a Stop verb per
face, and the start route really spawns the shipped entry module on an
OS-assigned port, waits until that socket accepts, and hands back the URL it
measured - so a click is enough and no port is ever assumed free.

What it starts: the checkout demo, the token ledger console and the UGC console
are each their own process and their own module, so each gets one OS-assigned
port. The lobby server owns the ws, city, web, hub and gate sockets in ONE
process, so it is started with a whole set of ports assigned up front and is
proved by its hub port - the address a person actually opens. A panel that
printed a lobby URL nobody had measured would be lying, so the lobby counts as
live only when its hub socket accepts a connection at the moment of reading.

Ownership: the launcher can bring this panel up beside the faces it already
serves, so a page click here used to start a SECOND lobby next to the one the
person was looking at. The launcher now hands over the faces it serves and the
ports it measured (--owned-face), and this module publishes them as live by
measurement while refusing to start or stop them by name: a control surface
that forks the sandbox is not a control surface.

Honesty law: nothing is reported live because it was launched. A face reads
live only when its port accepts a connection at the moment of the reading, and
a refusal names its own error code rather than pretending success.
"""

import argparse
import itertools
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import birth_gate  # noqa: E402  (R2941: birth-site claim check)

PAGE_NAME = "panel.html"
ROUTES = ("/panel", "/panel/")
STATE_ROUTE = "/panel/api/state"
START_ROUTE = "/panel/api/start"
STOP_ROUTE = "/panel/api/stop"

CHECKOUT = os.path.join(HERE, "lobby", "checkout_demo.py")
LEDGER = os.path.join(HERE, "ledger", "ledger_page.py")
UGC = os.path.join(HERE, "ugc", "ugc_page.py")
LOBBY = os.path.join(HERE, "lobby", "server.py")
MEMBER = os.path.join(HERE, "member", "member_page.py")
LEDGER_CONFIG = os.path.join(HERE, "ledger", "config.json")

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# face id -> (module path, published path, command template)
FACE_MODULES = {
    "checkout": (CHECKOUT, "/checkout/",
                 "python src/sandbox/lobby/checkout_demo.py --host %s --port %d"),
    "ledger": (LEDGER, "/ledger/",
               "python src/sandbox/ledger/ledger_page.py --host %s --port %d"),
    "ugc": (UGC, "/ugc/",
            "python src/sandbox/ugc/ugc_page.py --host %s --port %d"),
    "member": (MEMBER, "/member/",
               "python src/sandbox/member/member_page.py --host %s --port %d"),
}
# The lobby is one process holding five sockets; the hub socket is the face a
# person opens, so the hub port is what this panel publishes and measures.
LOBBY_PORT_KEYS = ("ws", "city", "web", "hub", "gate")
LOBBY_FLAGS = {
    "ws": "--port",
    "city": "--city-http-port",
    "web": "--web-port",
    "hub": "--hub-port",
    "gate": "--gate-port",
}
LOBBY_PATH = "/hub/"
FACE_IDS = ("checkout", "ledger", "member", "ugc", "lobby")

MOCK_STATEMENT = (
    "MOCK / NO REAL CHARGE: every face this panel starts runs the sandbox "
    "build with mock=true and chargeable=false, so no money moves and no real "
    "account is touched.")

START_TIMEOUT_S = 25.0
STOP_TIMEOUT_S = 3.0
OWNER_LAUNCHER = "launcher"
OWNER_PANEL = "panel"

LOG_STEM = "bigdomain-panel-child-"
LOG_SUFFIX = ".txt"
# R2951: R2950 kept every log that carries bytes, for ever, so a panel that
# kept failing accumulated without bound. The file exists to answer "why did
# this click do nothing", which a week-old refusal still answers for a person
# reading it and no longer answers for anyone else. The bound is an AGE and
# the prune judges by evidence (see prune_logs), not by who owns the directory.
LOG_PRUNE_AGE_S = 7 * 86400

# R2950: the per-panel tag carries pid + wall_ns + a process-local counter.
# R2949 used pid + four random bytes, which no criterion can prove unique.
# R2951: wall_ns alone still rested on the wall clock moving forward, so a
# BOOT-RELATIVE monotonic reading joined it (time.monotonic_ns is QPC on
# Windows: comparable across processes, unaffected by a clock correction).
# The tag is pid-wall-mono-seq: a wall clock stepped back still differs in the
# monotonic field, a reboot with the same pid still differs in the wall field,
# and the counter separates two panels inside ONE process (identical pid and,
# with an injected clock, identical stamps). What remains out of range is a
# reboot, a reused pid AND a wall clock stepped back to the same nanosecond.
_TAG_SEQ = itertools.count(1)


def make_tag(pid=None, when_ns=None, mono_ns=None):
    """The name fragment that makes a panel's child log its own.

    Kept a module function rather than an expression so the uniqueness claim
    is measurable: a caller can pin the pid, the wall clock and the monotonic
    clock and still get names that differ, which is exactly what pid reuse
    needs. ``mono_ns`` is injectable for the same reason - a criterion has to
    be able to drive a wall clock backwards without waiting for one.
    """
    pid_value = os.getpid() if pid is None else int(pid)
    stamp = time.time_ns() if when_ns is None else int(when_ns)
    mono = time.monotonic_ns() if mono_ns is None else int(mono_ns)
    return "%d-%x-%x-%x" % (pid_value, stamp, mono, next(_TAG_SEQ))


def parse_log_name(name):
    """(pid, wall_ns, mono_ns, seq, face) for a panel log name, else None.

    A name outside the namespace, or one whose tag does not parse, answers
    None: prune_logs never touches such a file, because "it looked like ours"
    is not evidence that it is ours.
    """
    if not name.startswith(LOG_STEM) or not name.endswith(LOG_SUFFIX):
        return None
    body = name[len(LOG_STEM):-len(LOG_SUFFIX)]
    parts = body.split("-")
    if len(parts) < 5:
        return None
    try:
        pid = int(parts[0])
        wall = int(parts[1], 16)
        mono = int(parts[2], 16)
        seq = int(parts[3], 16)
    except ValueError:
        return None
    face = "-".join(parts[4:])
    if not face:
        return None
    return pid, wall, mono, seq, face


FILETIME_EPOCH_OFFSET_NS = 116444736000000000 * 100
_K32 = None
_K32_LOADED = False


def _k32():
    """OpenProcess/GetProcessTimes entry points, or None off Windows."""
    global _K32, _K32_LOADED
    if _K32_LOADED:
        return _K32
    _K32_LOADED = True
    if sys.platform != "win32":
        return None
    import ctypes
    try:
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    except (OSError, AttributeError):
        return None
    k32.OpenProcess.restype = ctypes.c_void_p
    k32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int,
                                ctypes.c_uint32]
    k32.GetProcessTimes.restype = ctypes.c_int
    k32.GetProcessTimes.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                    ctypes.c_void_p, ctypes.c_void_p,
                                    ctypes.c_void_p]
    k32.CloseHandle.restype = ctypes.c_int
    k32.CloseHandle.argtypes = [ctypes.c_void_p]
    _K32 = k32
    return _K32


def process_started(pid):
    """("live", created_ns) | ("gone", None) | ("unknown", None).

    The single question the prune asks about a name: is the process that wrote
    this file still able to be the one that wrote it? ``gone`` is a kernel
    answer (ERROR_INVALID_PARAMETER = no such process), ``unknown`` is a
    refusal to guess - an access-denied read keeps the file, because deleting
    evidence on a question we could not ask is the wrong side to be wrong on.
    Windows-only, like the rest of this box's process law.
    """
    k32 = _k32()
    if k32 is None:
        return "unknown", None
    import ctypes
    handle = k32.OpenProcess(0x1000, 0, int(pid))
    if not handle:
        return ("gone" if ctypes.get_last_error() == 87 else "unknown"), None
    try:
        created = ctypes.c_uint64()
        exited = ctypes.c_uint64()
        kernel = ctypes.c_uint64()
        user = ctypes.c_uint64()
        if not k32.GetProcessTimes(handle, ctypes.byref(created),
                                   ctypes.byref(exited), ctypes.byref(kernel),
                                   ctypes.byref(user)):
            return "unknown", None
        return "live", int(created.value) * 100 - FILETIME_EPOCH_OFFSET_NS
    finally:
        k32.CloseHandle(handle)


def prune_logs(root=None, age_s=None, now=None, own=()):
    """Remove panel logs past the age bound, never a live writer's own.

    R2951: a log with bytes is evidence and is never deleted by teardown, so
    the only honest way to bound the pile is to delete evidence that has aged
    out - and to delete ONLY that. Four rules, each of which a criterion
    drives: (1) a name outside this namespace, or one whose tag does not
    parse, is never touched; (2) a file younger than the bound stays; (3) a
    file whose pid still names a process that started no later than the file
    was written may be that writer's own log and stays; (4) a path the caller
    declares as its OWN stays even then. Everything else is removed. A failed
    unlink keeps the file and names it, because Windows refuses to delete a
    file a live process still holds.
    """
    folder = tempfile.gettempdir() if root is None else root
    bound_ns = int((LOG_PRUNE_AGE_S if age_s is None else float(age_s))
                   * 1000000000)
    clock_ns = int((time.time() if now is None else float(now)) * 1000000000)
    own_paths = {os.path.abspath(path) for path in own or ()}
    report = {"removed": [], "kept": [], "fresh": [], "unknown": []}
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return report
    for name in names:
        parsed = parse_log_name(name)
        if parsed is None:
            continue
        path = os.path.join(folder, name)
        if os.path.abspath(path) in own_paths:
            report["kept"].append(path)
            continue
        try:
            mtime_ns = int(os.stat(path).st_mtime_ns)
        except OSError:
            continue
        if clock_ns - mtime_ns < bound_ns:
            report["fresh"].append(path)
            continue
        state, created = process_started(parsed[0])
        if state == "unknown":
            report["unknown"].append(path)
            continue
        if state == "live" and created is not None and created <= mtime_ns:
            report["kept"].append(path)
            continue
        try:
            os.remove(path)
        except OSError:
            report["kept"].append(path)
            continue
        report["removed"].append(path)
    return report


def parse_owned(specs):
    """face:port pairs the launcher declared it already serves.

    Raises ValueError with a named code so the CLI can refuse loudly instead
    of silently publishing a face it does not understand.
    """
    owned = {}
    for spec in specs or ():
        face_id, sep, port = str(spec).partition(":")
        face_id = face_id.strip()
        port = port.strip()
        if not sep or not face_id or not port.isdigit():
            raise ValueError("E_PANEL_BAD_OWNED: expected face:port, got %r"
                             % (spec,))
        owned[face_id] = int(port)
    return owned


def free_port(host="127.0.0.1"):
    """An OS-assigned free port, never a guess that 8097 is free."""
    sock = socket.socket()
    try:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


def can_connect(host, port, timeout=0.35):
    """True when something is really listening on that port right now."""
    if not port:
        return False
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def wait_port(host, port, timeout, proc=None):
    """Wait for a socket; stop early if the child we are waiting for has died.

    R2948: a face refused at birth exits in well under a second, and waiting
    the full timeout for a process that is already gone both wastes the click
    and hides the reason. ``proc`` is optional so existing callers are
    unchanged.
    """
    deadline = time.time() + float(timeout)
    while time.time() < deadline:
        if can_connect(host, port):
            return True
        if proc is not None and proc.poll() is not None:
            return can_connect(host, port)
        time.sleep(0.15)
    return False


def read_tail(path, limit=1200):
    """The last bytes a child said, decoded for a refusal body.

    R2948: a face that is refused at birth names its code on stderr
    (``E_FACE_NOT_LAUNCHED_BY_HOLDER``) and exits before binding, so the panel
    can only report WHY a start failed if it kept those bytes. Missing or
    unreadable reads as empty rather than raising inside a route.
    """
    if not path:
        return ""
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError:
        return ""
    return data.decode("utf-8", "replace")[-limit:]


def read_notices(path=LEDGER_CONFIG):
    """The standing surfaces, read from disk at CALL time - never hardcoded."""
    notices = {"ai_label": "", "disclaimer": ""}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            cfg = json.load(handle)
    except (OSError, ValueError):
        return notices
    token = (cfg or {}).get("token") or {}
    notices["ai_label"] = token.get("ai_label_text") or ""
    notices["disclaimer"] = token.get("disclaimer") or ""
    return notices


class Panel(object):
    """The children this panel owns; nothing else is ever terminated."""

    def __init__(self, host="127.0.0.1", timeout=START_TIMEOUT_S, owned=None,
                 tag_pid=None, tag_ns=None):
        self.host = host
        self.timeout = float(timeout)
        self.lock = threading.Lock()
        self.children = {}  # face id -> {"port": int, "proc": Popen}
        # Faces a launcher serves beside this panel, with the ports it measured.
        self.owned = dict(owned or {})
        # R2949: the child-log name was machine-wide per face id, so a second
        # panel on the same box overwrote the first one's evidence. The tag
        # carries this panel's own pid, so a name on disk still says which
        # process wrote it.
        # R2950: the uniqueness half is a monotonic stamp + counter instead of
        # four random bytes, so pid reuse cannot mint the same name again.
        self.tag = make_tag(tag_pid, tag_ns)
        # Every log THIS panel created, so teardown can never reach a file it
        # did not write (the same-user writable temp dir is shared ground).
        self.logs = set()

    def log_path_for(self, face_id):
        """Where THIS panel keeps what a child says on stderr.

        R2948 caught those bytes because a face refused at birth names its
        code there and nowhere else; R2949 keeps each panel's copy apart, and
        the path is published in the start answer so the evidence can still be
        read after the panel is gone.
        """
        return os.path.join(
            tempfile.gettempdir(),
            "%s%s-%s%s" % (LOG_STEM, self.tag, face_id, LOG_SUFFIX))

    def url_of(self, face_id, port):
        if face_id == "lobby":
            return "http://%s:%d%s" % (self.host, int(port), LOBBY_PATH)
        return "http://%s:%d%s" % (self.host, int(port),
                                   FACE_MODULES[face_id][1])

    def cmd_of(self, face_id, ports=None):
        if face_id == "lobby":
            parts = []
            for key in LOBBY_PORT_KEYS:
                parts.append(LOBBY_FLAGS[key])
                parts.append(str(int(ports[key])) if ports else "0")
            return "python src/sandbox/lobby/server.py --host %s %s" % (
                self.host, " ".join(parts))
        template = FACE_MODULES[face_id][2]
        return template % (self.host, int(ports) if ports else 0)

    def module_of(self, face_id):
        path = LOBBY if face_id == "lobby" else FACE_MODULES[face_id][0]
        return os.path.relpath(path, os.path.dirname(HERE))

    def face_rows(self):
        rows = []
        with self.lock:
            snapshot = dict(self.children)
            owned = dict(self.owned)
        for face_id in FACE_IDS:
            entry = snapshot.get(face_id)
            if entry is None and face_id in owned:
                owned_port = int(owned[face_id])
                rows.append({
                    "id": face_id,
                    "port": owned_port,
                    "url": self.url_of(face_id, owned_port),
                    "live": can_connect(self.host, owned_port),
                    "started": True,
                    "owner": OWNER_LAUNCHER,
                    "cmd": None,
                    "module": self.module_of(face_id),
                })
                continue
            port = entry["port"] if entry else None
            ports = entry.get("ports") if entry else None
            cmd_ports = ports if face_id == "lobby" else port
            alive = bool(entry) and entry["proc"].poll() is None
            live = alive and can_connect(self.host, port) if port else False
            rows.append({
                "id": face_id,
                "port": port,
                "url": self.url_of(face_id, port) if port else None,
                "live": bool(live),
                "started": bool(entry),
                "owner": OWNER_PANEL if entry else None,
                "cmd": self.cmd_of(face_id, cmd_ports),
                "module": self.module_of(face_id),
            })
        return rows

    def state_payload(self):
        notices = read_notices()
        return {
            "host": self.host,
            "mock": True,
            "chargeable": False,
            "read_only": False,
            "faces": self.face_rows(),
            "notices": {
                "ai_label": notices["ai_label"],
                "disclaimer": notices["disclaimer"],
                "mock_statement": MOCK_STATEMENT,
            },
            "startable": list(FACE_IDS),
        }

    def start(self, face_id):
        """Spawn one shipped module and prove it before claiming success."""
        if face_id not in FACE_IDS:
            return 400, {"error": "E_PANEL_UNKNOWN_FACE",
                         "detail": "startable: " + ",".join(FACE_IDS)}
        log_path = self.log_path_for(face_id)
        with self.lock:
            entry = self.children.get(face_id)
            if entry is not None and entry["proc"].poll() is None:
                return 409, {"error": "E_PANEL_ALREADY_RUNNING",
                             "face": face_id, "port": entry["port"]}
            owned_port = self.owned.get(face_id)
        if owned_port:
            # Starting a second copy would fork the sandbox: the person would
            # be looking at one lobby and writing into another.
            return 409, {"error": "E_PANEL_OWNED_BY_LAUNCHER",
                         "face": face_id,
                         "owner": OWNER_LAUNCHER,
                         "port": int(owned_port),
                         "url": self.url_of(face_id, owned_port),
                         "detail": "the launcher already serves this face; "
                                   "open the url it reports instead of "
                                   "starting a second copy"}
        with self.lock:
            ports = None
            if face_id == "lobby":
                ports = {}
                taken = set()
                for key in LOBBY_PORT_KEYS:
                    candidate = free_port(self.host)
                    while candidate in taken:
                        candidate = free_port(self.host)
                    taken.add(candidate)
                    ports[key] = candidate
                port = ports["hub"]
                argv = [sys.executable, LOBBY, "--host", self.host]
                for key in LOBBY_PORT_KEYS:
                    argv.extend([LOBBY_FLAGS[key], str(ports[key])])
            else:
                port = free_port(self.host)
                argv = [sys.executable, FACE_MODULES[face_id][0],
                        "--host", self.host, "--port", str(port)]
            # R2948: the child's own stderr is the only place a named refusal
            # can come from (a grandchild of the launcher is refused at birth,
            # by name, before it binds), so it is captured to a file instead of
            # being thrown away - DEVNULL made every failure read the same.
            # R2949: that file is per panel, never per face id alone.
            log_handle = open(log_path, "wb")
            try:
                proc = subprocess.Popen(
                    argv,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=log_handle,
                    creationflags=NO_WINDOW,
                )
            finally:
                log_handle.close()
            self.children[face_id] = {"port": port, "proc": proc,
                                      "ports": ports, "log": log_path}
            self.logs.add(log_path)
        if not wait_port(self.host, port, self.timeout,
                         (self.children.get(face_id) or {}).get("proc")):
            child_log = read_tail(self.children.get(face_id, {}).get("log"))
            exit_code = None
            entry = self.children.get(face_id) or {}
            if entry.get("proc") is not None:
                exit_code = entry["proc"].poll()
            self._kill(face_id)
            return 500, {"error": "E_PANEL_NOT_UP", "face": face_id,
                         "port": port,
                         "child_exit": exit_code,
                         "child_log": child_log,
                         "child_log_path": log_path,
                         "detail": "the module was launched but its port never "
                                   "accepted a connection"}
        body = {
            "face": face_id,
            "port": port,
            "url": self.url_of(face_id, port),
            "live": True,
            "mock": True,
            "chargeable": False,
            "child_log_path": log_path,
            "cmd": self.cmd_of(face_id, ports if face_id == "lobby" else port),
        }
        if ports:
            body["ports"] = dict(ports)
        return 200, body

    def stop(self, face_id):
        with self.lock:
            entry = self.children.get(face_id)
            owned_port = self.owned.get(face_id)
        if entry is None:
            if owned_port:
                # The launcher's child is not this panel's to kill: it also
                # serves every other face the person is looking at.
                return 409, {"error": "E_PANEL_OWNER_NOT_THIS_PROCESS",
                             "face": face_id,
                             "owner": OWNER_LAUNCHER,
                             "port": int(owned_port),
                             "detail": "this panel did not start that face, so "
                                       "it will not kill another process's child"}
            return 404, {"error": "E_PANEL_NOT_STARTED", "face": face_id}
        port = entry["port"]
        self._kill(face_id)
        deadline = time.time() + STOP_TIMEOUT_S
        while time.time() < deadline and can_connect(self.host, port):
            time.sleep(0.05)
        return 200, {"face": face_id, "port": port, "stopped": True,
                     "live": can_connect(self.host, port)}

    def _kill(self, face_id):
        with self.lock:
            entry = self.children.pop(face_id, None)
        if not entry:
            return
        proc = entry["proc"]
        if proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
        deadline = time.time() + STOP_TIMEOUT_S
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.05)
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass

    def stop_all(self):
        with self.lock:
            face_ids = list(self.children)
        for face_id in face_ids:
            self._kill(face_id)

    def release_logs(self):
        """Drop the logs this panel wrote that carry NOTHING; keep the rest.

        R2950: R2949 made each panel's child log its own file, and the price
        was accumulation - a panel that started five faces left five files in
        %TEMP% for ever. The file exists to answer one question ("why did this
        click do nothing?"), so an EMPTY file answers nothing and is removed,
        while any file with bytes is exactly the named refusal a person needs
        and is kept even after the panel is gone. A panel killed hard runs no
        teardown, so its files survive untouched for post-mortem. Only paths
        this panel created are ever touched, and the call belongs AFTER the
        children are gone: Windows refuses to unlink a file a live child still
        holds on its stderr, so a still-running face's empty log is removed by
        that face's stop or the panel's shutdown rather than while it runs
        (measured by AC-PAN14).
        """
        with self.lock:
            paths = sorted(self.logs)
            self.logs.clear()
        report = {"removed": [], "kept": [], "missing": []}
        for path in paths:
            try:
                size = os.path.getsize(path)
            except OSError:
                report["missing"].append(path)
                continue
            if size:
                report["kept"].append(path)
                continue
            try:
                os.remove(path)
            except OSError:
                report["kept"].append(path)
                continue
            report["removed"].append(path)
        return report


class PanelHandler(BaseHTTPRequestHandler):
    """One page plus three JSON routes: state, start, stop."""

    panel = None  # wired at startup
    page_path = os.path.join(HERE, PAGE_NAME)

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False,
                          sort_keys=True).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_page(self):
        try:
            with open(self.page_path, "rb") as handle:
                body = handle.read()
        except OSError:
            self._send(503, {"error": "panel page missing on disk"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            length = 0
        if length <= 0:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ROUTES:
            self._send_page()
            return
        if path == STATE_ROUTE:
            self._send(200, self.panel.state_payload())
            return
        if path in (START_ROUTE, STOP_ROUTE):
            self._send(405, {"error": "method not allowed: POST only"})
            return
        self._send(404, {"error": "not found: GET /panel/ and "
                                  "GET /panel/api/state only"})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path not in (START_ROUTE, STOP_ROUTE):
            if path in ROUTES or path == STATE_ROUTE:
                self._send(405, {"error": "method not allowed: GET only"})
            else:
                self._send(404, {"error": "not found: POST " + path})
            return
        payload = self._body()
        if not isinstance(payload, dict):
            self._send(400, {"error": "E_PANEL_BAD_FACE",
                             "detail": "expected a JSON object with a face key"})
            return
        face_id = payload.get("face")
        if not isinstance(face_id, str) or not face_id.strip():
            self._send(400, {"error": "E_PANEL_BAD_FACE",
                             "detail": "the face key is required"})
            return
        face_id = face_id.strip()
        if path == START_ROUTE:
            code, obj = self.panel.start(face_id)
        else:
            code, obj = self.panel.stop(face_id)
        self._send(code, obj)

    def _method_not_allowed(self):
        self._send(405, {"error": "method not allowed: GET and POST only"})

    def do_PUT(self):
        self._method_not_allowed()

    def do_DELETE(self):
        self._method_not_allowed()

    def do_PATCH(self):
        self._method_not_allowed()

    def log_message(self, fmt, *args):
        pass


class PanelServer(ThreadingHTTPServer):
    """Threading server that takes its children down with it."""

    def __init__(self, address, handler, panel):
        self.panel = panel
        ThreadingHTTPServer.__init__(self, address, handler)

    def shutdown(self):
        try:
            self.panel.stop_all()
            # R2950: the clean path is the only one that may delete anything -
            # empty logs only, and only files this panel wrote.
            report = self.panel.release_logs()
            print("PANEL-CLEANUP removed=%d kept=%d missing=%d"
                  % (len(report["removed"]), len(report["kept"]),
                     len(report["missing"])), flush=True)
        finally:
            ThreadingHTTPServer.shutdown(self)


def start_panel(host, port, timeout=START_TIMEOUT_S, owned=None):
    """Start the panel on its own thread; returns (server, panel).

    Pass port 0 and read server.server_address[1] for the real bound port.
    ``owned`` maps a face id to the port a launcher beside this panel serves.
    """
    panel = Panel(host=host, timeout=timeout, owned=owned)
    handler = type("BoundPanelHandler", (PanelHandler,), {"panel": panel})
    httpd = birth_gate.checked_server(
        lambda: PanelServer((host, port), handler, panel))
    threading.Thread(target=httpd.serve_forever, name="sandbox-panel",
                     daemon=True).start()
    return httpd, panel


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="control panel: start and stop the sandbox faces from a page")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8099)
    parser.add_argument("--timeout", type=float, default=START_TIMEOUT_S)
    parser.add_argument("--owned-face", action="append", default=None,
                        dest="owned_face", metavar="FACE:PORT",
                        help="a face a launcher beside this panel already "
                             "serves, with the port it measured; this panel "
                             "publishes it as live and refuses to start or "
                             "stop it (repeat for each face)")
    args = parser.parse_args(argv)
    # R2941: a face may only be born under the door that holds the sandbox
    # claim. With no launcher serving there is no claim and this passes.
    birth_gate.guard()
    try:
        owned = parse_owned(args.owned_face)
    except ValueError as exc:
        parser.error(str(exc))
    httpd, panel = start_panel(args.host, args.port, args.timeout, owned)

    print("PANEL http://%s:%d/panel/" % (args.host,
                                        httpd.server_address[1]), flush=True)
    # R2951: every panel launch is one prune window, so the pile of aged-out
    # refusals is bounded without a scheduler. Printed after the address line
    # because the launcher and the suites read that line first.
    pruned = prune_logs()
    print("PANEL-PRUNE removed=%d kept=%d fresh=%d unknown=%d"
          % (len(pruned["removed"]), len(pruned["kept"]),
             len(pruned["fresh"]), len(pruned["unknown"])), flush=True)
    try:
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
        httpd.server_close()
        panel.stop_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())