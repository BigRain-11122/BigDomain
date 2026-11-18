"""A face refuses to be born outside the door that holds the sandbox claim.

R2940 made the SECOND DOOR impossible: start_all takes a kernel named mutex
before it starts anything, so two launchers cannot both serve. It then measured
the hole beside that door - `qa/handstart-hole-R2940.log` shows a bare
`python lobby/server.py` coming up while a launcher was serving and accepting a
connection. A gate that only guards the launcher's own entry cannot see a face
that was never started through it.

This module is the birth-site check: a shipped face server asks, BEFORE it
binds, whether somebody holds the sandbox claim and whether that somebody is
this process's own parent. Two answers are refused:

* a claim is held by a pid that is not our parent - the face would live beside
  a sandbox it does not belong to (``E_FACE_NOT_LAUNCHED_BY_HOLDER``);
* a claim is held but the detail record does not name a pid - we cannot tell
  whose sandbox this is, and "the record file is missing" must never mean
  "allow" (``E_FACE_CLAIM_UNIDENTIFIED``).

Everything else is allowed: no claim at all means there is no launcher to
belong to, which is exactly the world a person gets when they run one face by
hand on a machine with no sandbox up.

``judge`` is a read: it stops at the first refusal and never writes a record,
never creates the claim. Only the thin ``guard`` shim exits the process.

Known and named rather than hidden: the check is per user session (the claim is
`Local\\`), it is absent on platforms without kernel named objects, and a
GRANDCHILD (a face started by a launcher-owned panel) is refused - which agrees
with R2938, where a launcher-owned panel already refuses to start a face it
does not own.

THE RECORD IS TRUSTED INPUT (official, R2947). Asked four rounds running
(R2941, R2943, R2944, R2946), decided here rather than carried again: the pid
this gate compares against is read out of a per-user writable file, so a
same-user process that rewrites that file to name its own parent is allowed
through. That is measured, not feared - AC-HSG9 drives both directions.

Why a secret in the record cannot fix it: a face has exactly two channels, the
record and its own environment, and both are readable and writable by any
process running as the same user (a plain file, and another process's
environment block via PROCESS_VM_READ). Any token the launcher writes into the
record can therefore be copied by the attacker, so a token would turn "edit one
JSON field" into "read one JSON field and set one environment variable" at
cryptographic gain of zero. The only identity a face can get from the kernel
is its own parent pid - and the only statement of WHO holds the sandbox is the
record. That is the shape of this seam, and it is written here instead of being
implied closed.

What IS proven, and matters: the record alone grants nothing. With no kernel
claim held, judge() allows whatever the record says (AC-HSG10), because the
gate is the mutex and the record is only detail. What the file can do is make
the gate refuse - never make it allow on its own.

Stdlib only, no shell, no network, no writes.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import launcher_mutex  # noqa: E402
import launcher_registry  # noqa: E402

REFUSED = "E_FACE_NOT_LAUNCHED_BY_HOLDER"
UNIDENTIFIED = "E_FACE_CLAIM_UNIDENTIFIED"
EXIT_CODE = 3
# Where the answer came from, published in every verdict so the reliance on a
# writable record is visible in evidence instead of living in a comment.
TRUST_NONE = "no-claim"
TRUST_UNAVAILABLE = "claim-unavailable"
TRUST_RECORD_PID = "record-pid"
REASONS_ALLOW = ("claim-unavailable", "no-holder", "parent-holds-claim")


def judge(record_path=None, mutex_name=None, ppid=None):
    """May this process become a sandbox face?

    Returns ``{allow, reason, code, ppid, holder_pid, mutex, record_path,
    trust}``. ``code`` is None when allowed and the refusal code otherwise;
    ``trust`` names what the verdict rests on (see TRUST_* above).
    """
    record_path = record_path or launcher_registry.default_path()
    mutex_name = mutex_name or launcher_mutex.name_for(record_path)
    ppid = os.getppid() if ppid is None else int(ppid)
    verdict = {
        "allow": True,
        "reason": "no-holder",
        "code": None,
        "ppid": ppid,
        "holder_pid": None,
        "mutex": mutex_name,
        "record_path": record_path,
        "trust": TRUST_NONE,
    }
    if not launcher_mutex.available():
        verdict["reason"] = "claim-unavailable"
        verdict["trust"] = TRUST_UNAVAILABLE
        return verdict
    if not launcher_mutex.exists(mutex_name):
        return verdict
    verdict["trust"] = TRUST_RECORD_PID
    record = launcher_registry.read(record_path) or {}
    holder = record.get("pid")
    verdict["holder_pid"] = holder
    if not holder:
        verdict.update({"allow": False, "reason": "claim-without-record",
                        "code": UNIDENTIFIED})
        return verdict
    if int(holder) == ppid:
        verdict["reason"] = "parent-holds-claim"
        return verdict
    verdict.update({"allow": False, "reason": "claim-held-by-another-pid",
                    "code": REFUSED})
    return verdict


def guard(record_path=None, mutex_name=None, stream=None):
    """Judge, and stop the process with a named line when refused.

    Returns the verdict dict when the face may bind; raises SystemExit(3) with
    the refusal code printed to stderr otherwise. Callers put this immediately
    before they bind their first socket.
    """
    verdict = judge(record_path=record_path, mutex_name=mutex_name)
    if verdict["allow"]:
        return verdict
    out = stream or sys.stderr
    out.write(
        "%s ppid=%d holder=%s mutex=%s record=%s reason=%s trust=%s\n"
        % (verdict["code"], verdict["ppid"],
           verdict["holder_pid"] if verdict["holder_pid"] is not None else "-",
           verdict["mutex"], verdict["record_path"], verdict["reason"],
           verdict["trust"]))
    out.flush()
    raise SystemExit(EXIT_CODE)


def checked_server(factory, record_path=None, mutex_name=None):
    """Judge, then let ``factory`` build (and bind) a shipped face server.

    ``factory`` is a zero-argument callable that constructs the server, which
    is the step that binds the socket. Every shipped starter routes through
    here, so a face imported and embedded by a harness is refused exactly like
    one started from the command line - the refusal happens BEFORE the factory
    runs, which is why a refused start leaves no listener behind.
    """
    guard(record_path=record_path, mutex_name=mutex_name)
    return factory()
