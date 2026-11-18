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
REASONS_ALLOW = ("claim-unavailable", "no-holder", "parent-holds-claim")


def judge(record_path=None, mutex_name=None, ppid=None):
    """May this process become a sandbox face?

    Returns ``{allow, reason, code, ppid, holder_pid, mutex, record_path}``.
    ``code`` is None when allowed and the refusal code otherwise.
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
    }
    if not launcher_mutex.available():
        verdict["reason"] = "claim-unavailable"
        return verdict
    if not launcher_mutex.exists(mutex_name):
        return verdict
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
        "%s ppid=%d holder=%s mutex=%s record=%s reason=%s\n"
        % (verdict["code"], verdict["ppid"],
           verdict["holder_pid"] if verdict["holder_pid"] is not None else "-",
           verdict["mutex"], verdict["record_path"], verdict["reason"]))
    out.flush()
    raise SystemExit(EXIT_CODE)
