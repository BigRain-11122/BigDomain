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
# R2952: an age bound alone leaves the RECENT pile unbounded - seven days of
# failures is still seven days of files. A COUNT bound per face joins it: the
# newest LOG_PRUNE_KEEP_N refusals of a face survive, the older ones past that
# cap are removed even when they are young. Both bounds remove; the newest cap
# entries are protected from the COUNT bound only, never from the age bound, so
# the two rules cannot mask each other. What neither bound may delete is a file
# whose writer may still be alive (the kernel is asked), the caller's own path,
# and any kernel refusal to answer - those keep, exactly as in R2951.
LOG_PRUNE_KEEP_N = 40
# R2953: every rule above judges a NAME, and a name is something any
# same-user process can type. The prune therefore collected a hand-written
# lookalike in the namespace as readily as a real refusal. Attribution now
# comes from the file's own FIRST LINE: the panel writes a marker when it
# creates the log, and the prune removes a file only when that line names the
# same tag and face the file name does. What this is NOT: a content test for
# "does it look like a refusal" (a child's stderr may be a traceback or a bare
# warning, so judging by content would delete real evidence), and not a gate
# (a same-user process can copy the marker verbatim). It answers one question
# only - was this file written through our path - and a file that cannot answer
# it is KEPT, not deleted.
LOG_MARKER = "# bigdomain-panel-child"
# R2954: R2953's marker rule has a price, and the price now has a NUMBER.
# Every log written before that rule - and any file without a marker - is
# never collected again. That residue is a CLOSED set rather than an
# unbounded one: our writer lays the marker before anything else, so no new
# markerless file can come from us, and the set can only shrink or stand
# still. What remains legal to say about it is a measurement, so the prune
# reports legacy=N legacy_bytes=B for the subset that is inside the
# namespace, parses, carries no marker, is past the age bound AND whose pid
# cannot be its writer. Deleting that subset is an OPERATOR decision
# (--prune-only --purge-legacy) and never automatic, because a markerless
# file and a stranger's hand-written lookalike are the same bytes here.

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


def log_marker_line(name):
    """The exact first line a log with this name must start with, else None.

    R2953: the marker repeats the tag and the face the FILE NAME already
    carries, so attribution is judged by agreement between two things rather
    than by one of them alone - a lookalike that copies another log's marker
    names a different tag and is not attributed.
    """
    parsed = parse_log_name(name)
    if parsed is None:
        return None
    pid, wall, mono, seq, face = parsed
    return ("%s tag=%d-%x-%x-%x face=%s\n"
            % (LOG_MARKER, pid, wall, mono, seq, face)).encode("ascii")


def log_attributed(path, name):
    """True only when the file's FIRST line is the marker its name implies.

    A leading blank line, a truncated marker, a marker copied from another
    name and a file with no marker at all are all False: the prune keeps every
    file it cannot attribute, because deleting on "it was in our directory"
    is how a cleanup becomes someone else's data loss.
    """
    expected = log_marker_line(name)
    if not expected:
        return False
    try:
        with open(path, "rb") as handle:
            head = handle.read(len(expected))
    except OSError:
        return False
    return head == expected


def marker_for_name(name):
    """The canonical marker line rebuilt from the NAME alone (R2955).

    Deliberately separate from log_marker_line: birth compares what landed on
    disk against THIS, so a writer that produced different bytes is caught by
    two descriptions disagreeing rather than by a value checking itself.
    """
    parsed = parse_log_name(name)
    if parsed is None:
        return None
    pid, wall, mono, seq, face = parsed
    return ("%s tag=%d-%x-%x-%x face=%s\n"
            % (LOG_MARKER, pid, wall, mono, seq, face)).encode("ascii")


class PanelLogBirthError(Exception):
    """A child log that could not be created WITH its marker, by name.

    R2955: the marker used to be a step the one call site happened to take,
    so the invariant "our writer never creates a markerless file" rested on
    the call site rather than on creation. This error means the birth was
    refused: no attributed log exists at that path.
    """

    def __init__(self, code, name, detail):
        Exception.__init__(self, "%s name=%s %s" % (code, name, detail))
        self.code = code
        self.name = name
        self.detail = detail


def _forget_new_log(path):
    """Best-effort removal of a file this process just created and rejected."""
    try:
        os.remove(path)
    except OSError:
        pass


def birth_child_log(path):
    """Create a panel child log and lay its marker before any other byte.

    R2953's prune trusts the FIRST line and R2954 measured the residue a
    missing first line leaves for ever, so the invariant has to hold where
    the file is born, not only on the call path that used to write the
    header. This is the ONE writer of child logs (AC-PAN26 asserts that
    statically): it writes the marker, then READS the first bytes back and
    refuses by name when they are not the marker the file name implies - the
    check does not trust the write it just performed. A refused birth removes
    the file it just made, so a failure cannot become tomorrow's residue.
    """
    name = os.path.basename(path)
    header = log_marker_line(name)
    canonical = marker_for_name(name)
    if not header or not canonical:
        raise PanelLogBirthError("E_PANEL_LOG_BIRTH_NOMARK", name,
                                 "this name does not resolve to a marker")
    handle = open(path, "wb")
    try:
        handle.write(header)
        handle.flush()
        with open(path, "rb") as check:
            head = check.read(len(canonical))
        if head != canonical:
            raise PanelLogBirthError("E_PANEL_LOG_BIRTH_UNMARKED", name,
                                     "first bytes %r are not the marker %r"
                                     % (head, canonical))
        handle.seek(0, os.SEEK_END)
    except BaseException:
        handle.close()
        _forget_new_log(path)
        raise
    return handle


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


def legacy_collectable(path, pid, bound_ns, clock_ns, own_paths=()):
    """Size of a markerless file a purge MAY collect, else None.

    R2954: the conditions are the prune's own - inside the namespace (the
    caller already parsed the name), past the age bound, and a pid that
    cannot be the writer - minus the one the prune insists on, which is the
    marker. The absent marker is precisely what makes the file legacy, and
    precisely why nothing automatic may delete it.
    """
    if os.path.abspath(path) in own_paths:
        return None
    try:
        info = os.stat(path)
    except OSError:
        return None
    mtime_ns = int(info.st_mtime_ns)
    if clock_ns - mtime_ns < bound_ns:
        return None
    state, created = process_started(pid)
    if state == "gone":
        return info.st_size
    if state == "live" and created is not None and created > mtime_ns:
        return info.st_size
    return None


def _legacy_keep_bucket(path, pid, bound_ns, clock_ns):
    """Which kept bucket a markerless file that is NOT collectable belongs to.

    Reporting only: ``legacy_collectable`` stays the single authority on
    whether a file may go, and this names WHY it stayed so the print line is
    three facts instead of one number.
    """
    try:
        mtime_ns = int(os.stat(path).st_mtime_ns)
    except OSError:
        return "kept"
    if clock_ns - mtime_ns < bound_ns:
        return "fresh"
    state, _created = process_started(pid)
    if state == "unknown":
        return "unknown"
    return "kept"


def purge_legacy(root=None, age_s=None, now=None, own=()):
    """Delete the markerless residue, only when a person asked for it.

    R2954: this is the one exit from R2953's price, and it is reachable only
    through an explicit CLI flag. The reason it cannot be automatic is the
    same reason it exists: a markerless file and a stranger's hand-written
    lookalike in the namespace are the same bytes, so the judgement belongs
    to an operator rather than to a clock. Everything the prune keeps keeps
    here too - a fresh file, a possible live writer, a kernel refusal, a path
    the caller declares its own, a foreign name, a malformed name - and an
    attributed file is left to the prune, which already judges it.
    """
    folder = tempfile.gettempdir() if root is None else root
    bound_ns = int((LOG_PRUNE_AGE_S if age_s is None else float(age_s))
                   * 1000000000)
    clock_ns = int((time.time() if now is None else float(now)) * 1000000000)
    own_paths = {os.path.abspath(path) for path in own or ()}
    report = {"removed": [], "kept": [], "fresh": [], "unknown": [],
              "bytes": 0}
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
        if log_attributed(path, name):
            # Ours, and the prune owns it: the purge neither deletes nor
            # counts it, so the two rules cannot double-delete one file.
            continue
        size = legacy_collectable(path, parsed[0], bound_ns, clock_ns,
                                  own_paths)
        if size is None:
            report[_legacy_keep_bucket(path, parsed[0], bound_ns,
                                       clock_ns)].append(path)
            continue
        try:
            os.remove(path)
        except OSError:
            report["kept"].append(path)
            continue
        report["removed"].append(path)
        report["bytes"] += size
    return report


def prune_logs(root=None, age_s=None, now=None, own=(), keep_n=None):
    """Remove panel logs past the age bound or beyond the per-face count cap.

    R2951 deleted only evidence that had aged out, which bounded the pile by
    SEVEN DAYS of failures - still unbounded inside that window. R2952 joins a
    count bound: per face, the newest ``keep_n`` (LOG_PRUNE_KEEP_N) refusals
    survive and the older ones past the cap go, young or not. Two independent
    bounds, each of which a criterion drives, and neither can mask the other:
    the age bound removes old files even when they are inside the cap, and the
    count bound removes young files that sit past it.

    Five rules guard both: (1) a name outside this namespace, or one whose tag
    does not parse, is never touched; (2) a file whose pid still names a
    process that started no later than the file was written may be that
    writer's own log and stays; (3) a kernel refusal to answer keeps the file;
    (4) a path the caller declares as its OWN stays and does not spend a cap
    slot; (5) a failed unlink keeps the file and names it, because Windows
    refuses to delete a file a live process still holds. The cap therefore
    bounds what nobody claims, and every exception is named in the report
    rather than silently widening the bound.
    """
    folder = tempfile.gettempdir() if root is None else root
    bound_ns = int((LOG_PRUNE_AGE_S if age_s is None else float(age_s))
                   * 1000000000)
    clock_ns = int((time.time() if now is None else float(now)) * 1000000000)
    cap = LOG_PRUNE_KEEP_N if keep_n is None else max(0, int(keep_n))
    own_paths = {os.path.abspath(path) for path in own or ()}
    report = {"removed": [], "kept": [], "fresh": [], "unknown": [],
              "over": [], "unattrib": [], "legacy": [], "legacy_bytes": 0}
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return report
    within_age = {}
    for name in names:
        parsed = parse_log_name(name)
        if parsed is None:
            continue
        path = os.path.join(folder, name)
        if os.path.abspath(path) in own_paths:
            report["kept"].append(path)
            continue
        if not log_attributed(path, name):
            # R2953: a name we could have typed is not a file we wrote.
            report["unattrib"].append(path)
            # R2954: the slice a purge MAY collect is counted here and
            # removed nowhere here, so the residue is a number instead of an
            # indefinite noun.
            size = legacy_collectable(path, parsed[0], bound_ns, clock_ns,
                                      own_paths)
            if size is not None:
                report["legacy"].append(path)
                report["legacy_bytes"] += size
            continue
        try:
            mtime_ns = int(os.stat(path).st_mtime_ns)
        except OSError:
            continue
        if clock_ns - mtime_ns < bound_ns:
            # Still young: the age bound says nothing, and the count pass
            # below decides. Reported only once its fate is known.
            within_age.setdefault(parsed[4], []).append(
                (mtime_ns, name, path, parsed[0]))
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
    # The count bound. Newest first, so ``cap`` slots keep the refusals a
    # person is most likely to be reading; everything past them is offered to
    # the same kernel question before it is deleted.
    for face in sorted(within_age):
        rows = sorted(within_age[face], key=lambda row: (row[0], row[1]),
                      reverse=True)
        report["fresh"].extend(row[2] for row in rows[:cap])
        for mtime_ns, _name, path, pid in rows[cap:]:
            state, created = process_started(pid)
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
            report["over"].append(path)
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
            # R2955: the marker is no longer a step of this call site but the
            # condition of creation - birth_child_log() writes it, reads the
            # first bytes back, and refuses by name (removing what it made)
            # when the file on disk does not carry it.
            try:
                log_handle = birth_child_log(log_path)
            except PanelLogBirthError as exc:
                return 500, {"error": exc.code, "face": face_id,
                             "child_log_path": log_path,
                             "detail": str(exc)}
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
            # R2953: this panel's own marker is not evidence of anything, so a
            # log that never got past it answers no question and goes; a byte
            # past the marker is a child's own words and stays.
            header = log_marker_line(os.path.basename(path)) or b""
            if size > len(header):
                report["kept"].append(path)
                continue
            try:
                os.remove(path)
            except OSError:
                report["kept"].append(path)
                continue
            report["removed"].append(path)
        return report


def print_prune(report, scope=None):
    """The one line both prune windows print, so the bound is visible.

    R2954: ``legacy``/``legacy_bytes`` publish the residue R2953 created, so a
    reader sees the size of what no automatic rule will ever collect instead
    of reading that it exists somewhere.

    R2957: ``scope`` is appended ONLY when an operator aimed the window, so a
    call that names no folder prints the exact line every earlier round
    printed - the new field cannot move an old reader.
    """
    line = ("PANEL-PRUNE removed=%d kept=%d fresh=%d unknown=%d over=%d "
            "unattrib=%d legacy=%d legacy_bytes=%d"
            % (len(report["removed"]), len(report["kept"]),
               len(report["fresh"]), len(report["unknown"]),
               len(report["over"]), len(report["unattrib"]),
               len(report["legacy"]), int(report["legacy_bytes"])))
    if scope is not None:
        line += " root=%s" % scope
    print(line, flush=True)


def print_purge_legacy(report, scope=None):
    """The one line a legacy purge prints, so the exit is visible too.

    R2957: same rule as ``print_prune`` - the aimed folder is named, and an
    unaimed call is byte-identical to what R2954 shipped.
    """
    line = ("PANEL-PURGE-LEGACY removed=%d kept=%d fresh=%d unknown=%d bytes=%d"
            % (len(report["removed"]), len(report["kept"]),
               len(report["fresh"]), len(report["unknown"]),
               int(report["bytes"])))
    if scope is not None:
        line += " root=%s" % scope
    print(line, flush=True)


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
    parser.add_argument("--prune-only", action="store_true",
                        dest="prune_only",
                        help="run one prune window and exit: no panel is "
                             "started and no port is bound, so any scheduler "
                             "can call this instead of waiting for a person "
                             "to open the panel")
    parser.add_argument("--purge-legacy", action="store_true",
                        dest="purge_legacy",
                        help="with --prune-only: also delete the markerless "
                             "residue (inside the namespace, past the age "
                             "bound, writer impossible); refused on its own, "
                             "so no panel start can ever reach it")
    parser.add_argument("--root", default=None, metavar="DIR",
                        help="with --prune-only: aim the whole window at one "
                             "folder instead of the temp dir; omitted means "
                             "the shipped behaviour is unchanged, and a "
                             "folder that is not there is refused rather "
                             "than reported as an empty window")
    args = parser.parse_args(argv)
    # R2957: the prune and the purge may now be AIMED. Both halves of one
    # window take the same scope, because a purge that cleans A while the
    # prune still judges B would be a half-aimed window nobody could reason
    # about. The scope is refused where it cannot apply, for the same reason
    # --purge-legacy is: a flag silently ignored reads as if it acted.
    scope = None
    if args.root is not None:
        if not args.prune_only:
            parser.error("E_PANEL_ROOT_NEEDS_PRUNE: --root only scopes the "
                         "--prune-only window; a panel start always prunes "
                         "the temp dir")
        scope = os.path.abspath(args.root)
        # A folder that is not there would list as nothing and print
        # removed=0 - a successful-looking answer to a mistyped path. The
        # window is refused instead.
        if not os.path.isdir(scope):
            parser.error("E_PANEL_ROOT_NOT_DIR: --root %s is not an existing "
                         "folder; refusing to report an empty window as clean"
                         % args.root)
    # R2952: the prune used to be coupled to a human launching a panel, so
    # "seven days" meant "seven days plus however long until the next launch".
    # This entry point decouples the judgement from the launch: it binds no
    # socket, takes no sandbox claim, prints the same PANEL-PRUNE line and
    # exits. Nothing on this box schedules it yet - that is written down in
    # the round, not implied by the flag existing.
    if args.prune_only:
        print_prune(prune_logs(root=scope), scope=scope)
        # R2954: collecting the markerless residue is an OPERATOR decision,
        # taken on the same call that would otherwise only report it. The
        # flag is refused without --prune-only (below), which is what keeps
        # a panel start from ever reaching this line.
        if args.purge_legacy:
            print_purge_legacy(purge_legacy(root=scope), scope=scope)
        return 0
    if args.purge_legacy:
        parser.error("E_PANEL_PURGE_NEEDS_PRUNE: --purge-legacy is only "
                     "meaningful with --prune-only; a panel start never "
                     "collects legacy residue")
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
    print_prune(prune_logs())
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