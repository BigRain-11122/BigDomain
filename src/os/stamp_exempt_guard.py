"""stamp_exempt_guard.py - the pinned-text guard both declaration writers ask.

Criteria AC-SEG1..AC-SEG6 were pre-registered in state/queue/tech.md as the
R2329 seed row BEFORE this file existed. Anchor check at HEAD 2026-11-01: the
five names (stamp_exempt_guard, AC-SEG, E_SEG, os-stamp-exempt-guard,
test_stamp_exempt_guard) were git grep -F hits ONLY in prose and state
(src/os/backlog.md, src/os/export_lines_R2329.json, src/os/state_close_R2329.py,
src/os/state.json, state/queue/tech.md) with zero executable occupancy.

Why this exists: stamp_exempt_append grows state/queue/stamp_exempt.json and
stamp_exempt_prune shrinks it, and each carried its own copy of the same write
mechanics - read the text, build the post, write a temp file, os.replace, read
the bytes back. Neither compared the text its plan was built from with the text
on disk at write time, so a plan read at T0 and executed at T1 silently
reverted a concurrent append, and nothing named it.

The guard is that comparison, in ONE place:

  * pin(text) is the digest a plan records next to its prediction;
  * commit(path, pinned, payload) re-reads the file, refuses E_SEG_STALE when
    the digest moved (before a single byte is written), and only then performs
    the one atomic replace with its read-back and residue proof.

Disclosed boundary: the guard owns the write mechanics and the staleness law,
not the declaration shape and not the entry rules. Those stay with
queue_done_stamp_exempt and with each writer, which import this module rather
than restating it. It reads no clock, imports nothing outside the stdlib,
opens no network connection, and writes nothing except the path it was handed.

Pure stdlib, pure-ASCII source, zero network.
"""

import hashlib
import io
import os

VERDICTS = ("PLANNED", "WROTE")

DIGEST_LEN = 16

# The stale refusal is deliberately the guard's OWN code: that fact belongs to
# the guard, so a writer may translate its write/readback/residue failures into
# its own family but not this one.
STALE_CODE = "E_SEG_STALE"

CODES = {
    "unreadable": "E_SEG_UNREADABLE",
    "write": "E_SEG_WRITE",
    "readback": "E_SEG_READBACK",
    "residue": "E_SEG_RESIDUE",
}

REPORT_KEYS = (
    "wrote",
    "read_back_ok",
    "before_bytes",
    "after_bytes",
    "digest_before",
    "digest_after",
)

USAGE = ("usage: stamped by stamp_exempt_append and stamp_exempt_prune; "
         "there is no CLI of its own\n")


class StampGuardError(Exception):
    """One refusal with its own code and detail."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s %s" % (code, detail))
        self.code = code
        self.detail = detail


def digest(data):
    """The sha16 the plan and the file comparison share (bytes in, hex out)."""
    return hashlib.sha256(data).hexdigest()[:DIGEST_LEN].upper()


def pin(text):
    """The reading a plan records: what it saw and how big that was."""
    if not isinstance(text, str):
        raise StampGuardError(CODES["unreadable"],
                              "pin expects text, got %s" % type(text).__name__)
    data = text.encode("utf-8")
    return {"digest": digest(data), "bytes": len(data)}


def read_pin(path, codes=None):
    """The same reading taken from disk right now (never a cached one)."""
    table = dict(CODES)
    table.update(codes or {})
    try:
        with io.open(path, "rb") as handle:
            data = handle.read()
    except (IOError, OSError) as exc:
        raise StampGuardError(table["unreadable"], "%s (%s)" % (path, exc))
    return {"digest": digest(data), "bytes": len(data)}


def _cleanup(temp):
    try:
        if os.path.exists(temp):
            os.remove(temp)
    except (IOError, OSError):
        pass


def commit(path, pinned, payload, temp_suffix, codes=None):
    """Replace path with payload, but only if the text on disk is still pinned.

    Refuses E_SEG_STALE when the digest moved between the plan and this call,
    and refuses it BEFORE creating the temp file, so a concurrent writer's
    bytes are untouched and no residue is left. On success the payload is one
    atomic replace, proved by reading the bytes back.
    """
    table = dict(CODES)
    table.update(codes or {})
    if not isinstance(payload, bytes):
        try:
            payload = payload.encode("utf-8")
        except (AttributeError, UnicodeEncodeError) as exc:
            raise StampGuardError(table["write"],
                                  "payload is not bytes or text (%s)" % exc)
    if not isinstance(pinned, dict) or not pinned.get("digest"):
        raise StampGuardError(
            STALE_CODE,
            "no pinned digest: a plan must pin the text it read before it "
            "can be committed")
    now = read_pin(path, table)
    if now["digest"] != pinned["digest"]:
        raise StampGuardError(
            STALE_CODE,
            "digest moved: planned %s (%s bytes) but the file now reads %s "
            "(%s bytes) - another writer touched %s between the plan and the "
            "commit" % (pinned["digest"], pinned.get("bytes"),
                        now["digest"], now["bytes"], path))
    temp = path + temp_suffix
    try:
        with io.open(temp, "wb") as handle:
            handle.write(payload)
        os.replace(temp, path)
    except (IOError, OSError) as exc:
        _cleanup(temp)
        raise StampGuardError(table["write"], "%s (%s)" % (path, exc))
    try:
        with io.open(path, "rb") as handle:
            back = handle.read()
    except (IOError, OSError) as exc:
        raise StampGuardError(table["readback"], "%s (%s)" % (path, exc))
    report = {
        "wrote": True,
        "read_back_ok": back == payload,
        "before_bytes": now["bytes"],
        "after_bytes": len(payload),
        "digest_before": now["digest"],
        "digest_after": digest(payload),
    }
    if not report["read_back_ok"]:
        raise StampGuardError(
            table["readback"],
            "read-back carries %d bytes, predicted %d"
            % (len(back), len(payload)))
    if os.path.exists(temp):
        raise StampGuardError(table["residue"],
                              "temp file survived: %s" % temp)
    return report


def one_line(report):
    """The one line a writer prints for itself (its own reconcile label)."""
    return ("STAMP EXEMPT GUARD wrote=%s read_back=%s before=%dB after=%dB "
            "digest=%s->%s"
            % ("yes" if report.get("wrote") else "no",
               "n/a" if report.get("read_back_ok") is None
               else ("ok" if report.get("read_back_ok") else "BAD"),
               report.get("before_bytes"), report.get("after_bytes"),
               report.get("digest_before"), report.get("digest_after")))