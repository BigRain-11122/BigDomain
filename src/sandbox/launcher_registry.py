"""Machine-wide record of the sandbox launcher that is currently serving.

R2938 taught the control panel which faces the launcher already serves, but the
knowledge was ARGV: it travelled from the launcher to its own child and nowhere
else. Two doors opened on one machine therefore started twice, and nothing in
the tree could refuse either of them.

This module is the missing discovery face: one small record, one exclusive
claim, and one judgement that is RE-MEASURED rather than read off the file.

Record shape (all values written by the launcher that owns it):

    {"pid": 1234, "ts": "2026-11-18T15:01:02", "host": "127.0.0.1",
     "state": "starting" | "serving", "hub_url": "http://.../hub/",
     "ports": {...}, "face_ports": {...}}

The three rules that matter, each one is a criterion in the suite:

1. claim() is EXCLUSIVE (O_CREAT|O_EXCL). A live owner's record is never
   overwritten, so the refusal is a race-safe gate and not a check-then-write.
2. A record is judged by re-measuring: the pid is alive AND (the owner says it
   is still starting, or the recorded hub port accepts a connection RIGHT NOW).
   A dead pid, or a live pid that serves nothing, is a stale record and the new
   launcher takes it over - the refusal fires only while the first is really
   alive.
3. release() removes the record only when it names OUR pid, so a launcher can
   never delete another process's claim.

Stdlib only, no shell, no network beyond a loopback connect probe.
"""

import ctypes
import json
import os
import socket
import tempfile
import time
import urllib.parse

FILENAME = "sandbox-launcher.json"
SUBDIR = "BigDomain"

REFUSED = "E_LAUNCHER_ALREADY_RUNNING"
STILL_ACTIVE = 259  # GetExitCodeProcess value for a running process
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def default_path():
    """The machine-level record path (never inside the repository)."""
    root = (os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
            or tempfile.gettempdir())
    return os.path.join(root, SUBDIR, FILENAME)


def pid_alive(pid):
    """True only when that process id is a live process on this machine.

    os.kill(pid, 0) is NOT used on Windows: signal 0 is not a probe there, so
    the question is asked straight through OpenProcess/GetExitCodeProcess.
    """
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return False
        return code.value == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def can_connect(url_or_host, port=None, timeout=0.4):
    """True when something really answers there right now."""
    host = url_or_host
    if port is None:
        split = urllib.parse.urlsplit(str(url_or_host))
        host = split.hostname
        port = split.port
    if not host or not port:
        return False
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def read(path):
    """The record on disk, or None when there is no readable one."""
    try:
        with open(path, encoding="utf-8") as handle:
            record = json.load(handle)
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def judge(record, connect=None, pinned_host=None):
    """Is this record a HOLDER, and why?

    ``connect`` is injectable so a suite can prove both directions without
    needing a real listener for the negative arm. When ``pinned_host`` is
    given, the probe is made against the record's PORT on that host instead of
    the host in the recorded URL, which is how a second launcher asked to bind
    a different interface still re-measures the same socket.
    """
    record = record or {}
    pid = record.get("pid")
    alive = bool(pid) and pid_alive(pid)
    hub_url = record.get("hub_url") or ""
    hub_port = None
    if hub_url:
        split = urllib.parse.urlsplit(hub_url)
        hub_port = split.port
    if connect is not None:
        hub_live = bool(connect(record)) if alive else False
    else:
        hub_live = bool(alive and hub_port
                        and can_connect(pinned_host or hub_url, hub_port))
    starting = record.get("state") == "starting"
    holder = bool(alive and (starting or hub_live))
    if not pid:
        reason = "no-pid"
    elif not alive:
        reason = "pid-dead"
    elif hub_live:
        reason = "hub-live"
    elif starting:
        reason = "still-starting"
    else:
        reason = "pid-alive-but-nothing-serving"
    return {"holder": holder, "pid_alive": alive, "hub_live": hub_live,
            "reason": reason, "pid": pid, "hub_url": hub_url}


def _create_exclusive(path, record):
    """Write the record, failing with FileExistsError if one is already there."""
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        payload = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        os.write(fd, payload.encode("utf-8"))
    finally:
        os.close(fd)


def claim(path, record, connect=None, attempts=3):
    """Take the machine record, or refuse with the live holder it found.

    Returns ``(True, None, verdict_of_ours_free_path)`` or
    ``(False, holder, verdict)``. The loop is deliberate: between the failed
    exclusive create and the stale removal another launcher may claim, and that
    must end in a refusal rather than in two owners.
    """
    for _ in range(max(1, int(attempts))):
        try:
            _create_exclusive(path, record)
            return True, None, {"holder": False, "reason": "claimed"}
        except FileExistsError:
            holder = read(path)
            verdict = judge(holder, connect=connect,
                            pinned_host=record.get("host"))
            if verdict["holder"]:
                return False, holder, verdict
            # Stale: the owner is dead or serves nothing. Removing it is what
            # makes the retry possible, and the retry is still exclusive.
            try:
                os.remove(path)
            except OSError:
                pass
    holder = read(path)
    return False, holder, judge(holder, connect=connect)


def write_serving(path, record):
    """Publish the serving state once the launcher has proved every face."""
    directory = os.path.dirname(os.path.abspath(path))
    tmp = path + ".%d.tmp" % os.getpid()
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    os.replace(tmp, path)
    return os.path.dirname(os.path.abspath(path)) == directory


def release(path, pid=None):
    """Delete the record only when it names OUR pid (never someone else's)."""
    pid = os.getpid() if pid is None else pid
    record = read(path)
    if not record:
        return False
    if int(record.get("pid") or 0) != int(pid):
        return False
    try:
        os.remove(path)
    except OSError:
        return False
    return True


def stamp(when=None):
    """The ts string the record carries (local time, second resolution)."""
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(when))
