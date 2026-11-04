# status_export_writer_transport_scope.py - every writer that lands the
# CEO-visible export is asked to prove BOTH transports, each in its own
# publishable world, and a writer that refuses is published as UNPROVABLE with
# its refusal code instead of being dropped.
# Criteria AC-SEWS1..AC-SEWS6 were pre-registered in state/queue/tech.md:518
# (the R2450 seed row) BEFORE this file existed.
#
# Why this exists: the R2450 dialect wire proved the export writes ask the
# dialect law and proved both transports - but MEASURED that its transport leg
# runs the QUEUE-FLOOR writer only. Three writers land docs/status-export.json;
# a CRLF regression in the other two would not have been caught there. The row
# also measured that closeout_export_parity_wire REFUSES on a bare fixture, so
# its CRLF path cannot be exercised by a copy at all.
#
# This module is the scope. The proved set is the same derived set - read off
# the shipped audit at CALL time through the dialect wire, so no writer name is
# written down here (AC-SEWS1). Each writer is asked in its OWN publishable
# world: two copies of the export, one LF and one CRLF, and the writer's own
# entry point is called for real on each copy. The entry point is DISCOVERED
# from the module surface (write, else publish), not from a table of names.
#
# A leg that comes back refused is not an exception to be swallowed: the row
# carries the writer's own refusal code and the measured fact that the document
# was left byte-identical (AC-SEWS4). A writer that lands the file in both
# transports keeps the target's own dialect and both legs must agree on the
# same document (AC-SEWS2/AC-SEWS3).
#
# The base reading of the dialect wire is carried through UNCHANGED - every
# key it publishes keeps its value here - and the scope adds its own keys, so
# a consumer of the old reading is unaffected (AC-SEWS5).
#
# CLI: status_export_writer_transport_scope.py --check [--root PATH]
#                                                 [--sample PATH] [--json]
#   exit 0 = SCOPED (every derived writer proved both transports)
#   exit 2 = SCOPE-PARTIAL / UNROUTED / TRANSPORT-SPLIT / UNSCOPED
#   exit 3 = EMPTY (the audit derives no writer for this document)
#   exit 5 = the flags are bad
#
# Pure ASCII source, stdlib only, zero network, no clock. The only bytes it
# writes are the fixture copies inside the directory its caller supplies.

import importlib
import io
import json
import os
import shutil
import sys
import tempfile

import status_export_writer_dialect_wire as SEWD

LABEL = "os-status-export-writer-transport-scope"
TARGET = SEWD.TARGET

PROVED = "PROVED"
UNPROVABLE = "UNPROVABLE"

SCOPED = "SCOPED"
PARTIAL = "SCOPE-PARTIAL"
UNSCOPED = "UNSCOPED"

ENTRY_POINTS = ("write", "publish")
SCOPE_KEYS = ("scope_verdict", "scope", "scope_proved", "scope_unprovable",
              "scope_target")

USAGE = (
    "usage: status_export_writer_transport_scope.py --check [--root PATH] "
    "[--sample PATH] [--json]\n"
    "  --check        ask every derived writer to prove both transports\n"
    "  --root PATH    repository root the audit and every writer read (default .)\n"
    "  --sample PATH  export document to copy for the proofs "
    "(default <root>/docs/status-export.json)\n"
    "  --json         emit one machine-readable object\n"
    "  exit 0 = SCOPED, 2 = SCOPE-PARTIAL/UNROUTED/TRANSPORT-SPLIT/UNSCOPED, "
    "3 = EMPTY, 5 = bad flags\n"
)


class ScopeError(Exception):
    """A refusal carrying its own code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def derived(root):
    """The proved set: the dialect wire own derived export writers."""
    try:
        _, rows = SEWD.derived(root)
    except SEWD.WireError as exc:
        raise ScopeError(exc.code, exc.detail)
    return rows


def module_for(name):
    """Import the writer by the name the audit reported for it."""
    stem = name[:-3] if name.endswith(".py") else name
    if not stem:
        raise ScopeError("E_SEWS_NO_MODULE", repr(name))
    try:
        return importlib.import_module(stem)
    except Exception:
        raise ScopeError("E_SEWS_NO_MODULE", name)


def entry_point(module):
    """The writer own callable, discovered by surface and never by name."""
    for attribute in ENTRY_POINTS:
        candidate = getattr(module, attribute, None)
        if callable(candidate):
            return attribute, candidate
    raise ScopeError("E_SEWS_NO_CALLABLE", getattr(module, "__name__", "?"))


def _bytes(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def _ask(module, root, path):
    """One real writer call. A refusal is a reading, not an exception."""
    attribute, callable_ = entry_point(module)
    try:
        if attribute == "write":
            callable_(root, path)
            return {"kind": "WRITTEN", "status": "WRITTEN", "code": 0,
                    "detail": ""}
        result, code = callable_(root, path)
    except Exception as exc:
        return {"kind": "ERROR", "status": "ERROR",
                "code": getattr(exc, "code", type(exc).__name__),
                "detail": str(exc)[:160]}
    code = int(code)
    status = str(result.get("verdict") or ("WRITTEN" if code == 0 else "REFUSED"))
    detail = str(result.get("reading") or result.get("gate") or "")
    return {"kind": "WRITTEN" if code == 0 else "REFUSED",
            "status": status, "code": code, "detail": detail}


def _measure(path, before, outcome):
    """What the call actually left on disk, in transport terms."""
    after = _bytes(path)
    text = after.decode("utf-8", "replace").replace("\r\n", "\n")
    return {
        "status": outcome["status"],
        "kind": outcome["kind"],
        "code": outcome["code"],
        "detail": outcome["detail"],
        "bytes": len(after),
        "crlf": after.count(b"\r\n"),
        "lone_lf": after.replace(b"\r\n", b"").count(b"\n"),
        "unchanged": after == before,
        "text": text,
    }


def _land(path, payload):
    with io.open(path, "wb") as handle:
        handle.write(payload)


def prove(root, name, folder, body):
    """Ask one writer over an LF copy and a CRLF copy of the same document."""
    module = module_for(name)
    stem = (name[:-3] if name.endswith(".py") else name) or "writer"
    lf_path = os.path.join(folder, "lf-%s.json" % stem)
    crlf_path = os.path.join(folder, "crlf-%s.json" % stem)
    crlf_body = body.replace(b"\n", b"\r\n")
    _land(lf_path, body)
    _land(crlf_path, crlf_body)

    lf = _measure(lf_path, body, _ask(module, root, lf_path))
    crlf = _measure(crlf_path, crlf_body, _ask(module, root, crlf_path))
    agree = lf["text"] == crlf["text"]

    proved = (lf["kind"] == "WRITTEN" and crlf["kind"] == "WRITTEN"
              and lf["crlf"] == 0 and crlf["lone_lf"] == 0
              and crlf["crlf"] > 0 and agree)
    if proved:
        refusal = ""
    elif crlf["kind"] != "WRITTEN":
        refusal = _refusal(crlf)
    elif lf["kind"] != "WRITTEN":
        refusal = _refusal(lf)
    else:
        refusal = "TRANSPORTS-DISAGREE"

    for leg in (lf, crlf):
        leg.pop("text", None)
    return {
        "name": name,
        "world": "export-copy",
        "verdict": PROVED if proved else UNPROVABLE,
        "refusal": refusal,
        "agree": agree,
        "lf": lf,
        "crlf": crlf,
    }


def _refused(row):
    """The leg that refused, so AC-SEWS4 can read its own evidence."""
    if row["crlf"]["kind"] != "WRITTEN":
        return row["crlf"]
    if row["lf"]["kind"] != "WRITTEN":
        return row["lf"]
    return None


def _refusal(leg):
    """The writer own refusal code, with its reading when it named one."""
    return str(leg["code"]) if not leg["detail"] else "%s/%s" % (
        leg["code"], leg["detail"])


def check(root, sample=None):
    """The one reading this module publishes: the base reading, plus scope."""
    if sample is None:
        sample = os.path.join(root, "docs", "status-export.json")
    if not os.path.exists(sample):
        raise ScopeError("E_SEWS_SAMPLE_MISSING", sample)
    try:
        with io.open(sample, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError):
        raise ScopeError("E_SEWS_SAMPLE_MISSING", sample)
    try:
        text = raw.decode("utf-8-sig").replace("\r\n", "\n")
    except UnicodeDecodeError:
        raise ScopeError("E_SEWS_SAMPLE_NOT_UTF8", sample)
    if not text.endswith("\n"):
        text += "\n"
    body = text.encode("utf-8")

    # the base reading is asked over the SAME sample, so every key it publishes
    # keeps the value it would publish on its own (AC-SEWS5)
    base = SEWD.check(root, sample)

    rows = derived(root)
    folder = tempfile.mkdtemp(prefix="sews-")
    scope = []
    try:
        for row in rows:
            try:
                scope.append(prove(root, row["name"], folder, body))
            except ScopeError as exc:
                scope.append({"name": row["name"], "world": "export-copy",
                              "verdict": UNPROVABLE, "refusal": exc.code,
                              "agree": False, "lf": None, "crlf": None,
                              "detail": exc.detail})
    finally:
        shutil.rmtree(folder, ignore_errors=True)

    unprovable = [row["name"] for row in scope
                  if row["verdict"] != PROVED]
    if base["verdict"] != SEWD.WIRED:
        verdict = base["verdict"]
    elif not scope:
        verdict = SEWD.EMPTY
    elif unprovable:
        verdict = PARTIAL
    else:
        verdict = SCOPED

    reading = dict(base)
    reading["scope_verdict"] = verdict
    reading["scope_target"] = TARGET
    reading["scope_proved"] = len(scope) - len(unprovable)
    reading["scope_unprovable"] = unprovable
    reading["scope"] = scope
    return reading


def one_line(reading):
    return ("%s scope=%s proved=%d unprovable=%s"
            % (SEWD.one_line(reading), reading["scope_verdict"],
               reading["scope_proved"],
               ",".join(reading["scope_unprovable"]) or "(none)"))


def render(reading):
    out = [one_line(reading)]
    for row in reading["scope"]:
        lf = row["lf"]
        crlf = row["crlf"]
        out.append(
            "  SCOPE %s verdict=%s refusal=%s agree=%s "
            "lf=%s/%dB crlf=%s/%dB lone-lf=%s"
            % (row["name"], row["verdict"], row["refusal"] or "(none)",
               "yes" if row["agree"] else "no",
               "-" if lf is None else lf["status"],
               0 if lf is None else lf["bytes"],
               "-" if crlf is None else crlf["status"],
               0 if crlf is None else crlf["bytes"],
               "-" if crlf is None else crlf["lone_lf"]))
    return "\n".join(out)


def parse(argv):
    opts = {"root": ".", "sample": None, "json": False, "check": False}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            opts["check"] = True
        elif arg == "--json":
            opts["json"] = True
        elif arg in ("--root", "--sample"):
            if index + 1 >= len(argv):
                raise ScopeError("E_SEWS_BAD_FLAGS", "%s needs a value" % arg)
            opts[arg[2:]] = argv[index + 1]
            index += 1
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            raise SystemExit(0)
        else:
            raise ScopeError("E_SEWS_BAD_FLAGS", "unknown argument %s" % arg)
        index += 1
    if not opts["check"]:
        raise ScopeError("E_SEWS_BAD_FLAGS", "--check is required")
    if not os.path.isdir(opts["root"]):
        raise ScopeError("E_SEWS_BAD_FLAGS", "--root is not a directory")
    return opts


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        opts = parse(argv)
        reading = check(opts["root"], opts["sample"])
    except ScopeError as exc:
        sys.stdout.write("%s\n" % exc)
        if exc.code == "E_SEWS_BAD_FLAGS":
            sys.stdout.write(USAGE)
            return 5
        return 3 if exc.code.endswith("SAMPLE_MISSING") else 2
    if opts["json"]:
        sys.stdout.write(json.dumps(reading, ensure_ascii=True, indent=2) + "\n")
    else:
        sys.stdout.write(render(reading) + "\n")
    if reading["scope_verdict"] == SCOPED:
        return 0
    if reading["scope_verdict"] == SEWD.EMPTY:
        return 3
    return 2


if __name__ == "__main__":
    sys.exit(main())