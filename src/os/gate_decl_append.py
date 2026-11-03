# gate_decl_append.py - add one capability blocker through machine_gate's law
# Criteria AC-GDA1..AC-GDA6 were pre-registered in state/queue/tech.md (the
# R2300 seed row) BEFORE this file existed.
#
# Why this exists: state/machine_gates.json has a reader (machine_gate
# .read_declaration) and a drift reader (gate_drift), but no writer, so adding
# or repairing a blocker means editing JSON by hand - and a hand edit is
# exactly how an identity gets a stale digest or a capability typo that only
# fails when the batch runs.
#
# The shape law is IMPORTED from machine_gate, never copied: the entry keys,
# the declaration keys, the capability vocabulary and the post read-back all
# come out of that module, so a patched vocabulary flows straight through
# (the suite proves it by widening the vocabulary and watching the same call
# accept the new capability).
#
# The write is a TEXTUAL splice, not a re-render: the pre-existing array body
# is proved byte-intact by requiring it to still be a substring of the post
# text, so a hand-formatted file is never silently reformatted.
#
# Dry run is the default: plan() returns the before/after byte counts and
# writes nothing. execute=True performs one atomic os.replace, proves the
# read-back bytes equal the prediction and leaves no temp file.
#
# Pure ASCII source, stdlib only, zero network, no clock read.
#
# CLI: gate_decl_append.py --identity ID --capability CAP --reason TEXT
#      --declared-by R<nnnn> [--decl PATH] [--root PATH] [--execute] [--json]
#   exit 0 = planned (or appended with --execute)
#   exit 2 = refused (duplicate identity, unknown capability, bad field,
#            second declaration header, shape or write/read-back failure)
#   exit 3 = declaration missing / unreadable / malformed
#   exit 5 = bad flags

import io
import json
import os
import sys

import declaration_writer_dialect_preservation as DWD
import machine_gate as MG

TEMP_SUFFIX = ".gda-tmp"

REPORT_KEYS = ("path", "identity", "capability", "reason", "declared_by",
               "insert_at", "declarations_before", "declarations_after",
               "before_bytes", "predicted_bytes", "wrote", "read_back_ok",
               "verdict")

# Refusals the caller can act on; everything else is a bad input file.
REFUSAL_CODES = ("E_GDA_DUP", "E_GDA_BAD_CAPABILITY", "E_GDA_BAD_IDENTITY",
                 "E_GDA_BAD_FIELD", "E_GDA_SECOND_HEADER", "E_GDA_SHAPE",
                 "E_GDA_WRITE", "E_GDA_READBACK", "E_GDA_RESIDUE")


class GateDeclAppendError(Exception):
    """Raised when an entry cannot be appended without guessing."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def array_span(text, key):
    """The (open, close) indexes of the array value of KEY, string-aware."""
    marker = '"%s"' % key
    at = text.find(marker)
    if at < 0:
        raise GateDeclAppendError("E_GDA_BAD_DECL",
                                  "declaration carries no %s key" % key)
    open_at = text.find("[", at)
    if open_at < 0:
        raise GateDeclAppendError("E_GDA_BAD_DECL",
                                  "%s is not an array" % key)
    depth = 0
    in_string = False
    escape = False
    index = open_at
    while index < len(text):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
            elif char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    return open_at, index
        index += 1
    raise GateDeclAppendError("E_GDA_BAD_DECL",
                              "the %s array is never closed" % key)


def render_entry(entry, indent=4):
    """One gates entry rendered at the file's own nesting depth."""
    body = json.dumps(entry, ensure_ascii=True, indent=2)
    pad = " " * indent
    return "\n".join(pad + line for line in body.split("\n"))


def _check_fields(identity, capability, reason, declared_by):
    """Validate the caller's fields against machine_gate's own vocabulary."""
    for label, value in (("identity", identity), ("capability", capability),
                         ("reason", reason), ("declared_by", declared_by)):
        if not isinstance(value, str) or not value.strip():
            raise GateDeclAppendError("E_GDA_BAD_FIELD",
                                      "%s is empty" % label)
        if '"' in value or "\\" in value or "\n" in value or "\r" in value:
            raise GateDeclAppendError(
                "E_GDA_BAD_FIELD",
                "%s cannot carry a quote, a backslash or a newline: %r"
                % (label, value))
    if capability not in MG.CAPABILITIES:
        raise GateDeclAppendError(
            "E_GDA_BAD_CAPABILITY",
            "field capability names %r, the vocabulary is %s"
            % (capability, "/".join(MG.CAPABILITIES)))


def payload_bytes(raw, post):
    """The bytes to land: the shared dialect law, asked at CALL time.

    `raw` is the declaration as it sits on disk; `post` is this writer's own
    LF composition. An LF declaration therefore gets exactly today's bytes,
    and a CRLF declaration keeps its transport instead of being converted.
    """
    return DWD.encode(raw, post)[1]


def plan(text, identity, capability, reason, declared_by, raw=None):
    """Compute the post text without writing; return the planned report."""
    _check_fields(identity, capability, reason, declared_by)
    if text.count('"version"') > 1:
        raise GateDeclAppendError(
            "E_GDA_SECOND_HEADER",
            "the text carries %d declaration headers" % text.count('"version"'))
    try:
        before = MG.read_declaration_text(text)
    except MG.MachineGateError as exc:
        raise GateDeclAppendError("E_GDA_BAD_DECL",
                                  "declaration does not parse: %s"
                                  % exc.code)
    for entry in before["gates"]:
        if entry["identity"] == identity:
            raise GateDeclAppendError(
                "E_GDA_DUP",
                "field identity %r is already declared (capability %s, "
                "declared %s)" % (identity, entry["capability"],
                                  entry["declared_by"]))
    open_at, close_at = array_span(text, "gates")
    body = text[open_at + 1:close_at]
    entry = {"identity": identity, "capability": capability,
             "reason": reason, "declared_by": declared_by}
    block = render_entry(entry)
    stripped = body.rstrip()
    if stripped:
        splice_at = open_at + 1 + len(stripped)
        inserted = ",\n" + block
        post = text[:splice_at] + inserted + text[splice_at:]
    else:
        splice_at = open_at + 1
        inserted = "\n" + block + "\n  "
        post = text[:splice_at] + inserted + text[close_at:]
    try:
        after = MG.read_declaration_text(post)
    except MG.MachineGateError as exc:
        raise GateDeclAppendError("E_GDA_SHAPE",
                                  "post text does not parse: %s" % exc.code)
    if len(after["gates"]) != len(before["gates"]) + 1:
        raise GateDeclAppendError(
            "E_GDA_SHAPE",
            "post text carries %d entries, expected %d"
            % (len(after["gates"]), len(before["gates"]) + 1))
    added = [row for row in after["gates"] if row["identity"] == identity]
    if len(added) != 1:
        raise GateDeclAppendError(
            "E_GDA_SHAPE",
            "post text carries %d entries for %r" % (len(added), identity))
    if added[0]["capability"] != capability or added[0]["reason"] != reason \
            or added[0]["declared_by"] != declared_by:
        raise GateDeclAppendError(
            "E_GDA_SHAPE",
            "the appended entry does not read back as written")
    post_open, post_close = array_span(post, "gates")
    if stripped and stripped not in post[post_open + 1:post_close]:
        raise GateDeclAppendError(
            "E_GDA_SHAPE", "a pre-existing entry is no longer byte-intact")
    return {
        "identity": identity,
        "capability": capability,
        "reason": reason,
        "declared_by": declared_by,
        "insert_at": splice_at,
        "declarations_before": len(before["gates"]),
        "declarations_after": len(after["gates"]),
        "before_bytes": len(text.encode("utf-8")),
        "predicted_bytes": len(payload_bytes(
            post.encode("utf-8") if raw is None else raw, post)),
        "post": post,
    }


def append_gate(root, identity, capability, reason, declared_by,
                declaration=None, execute=False):
    """Plan (and optionally perform) one entry append under root."""
    rel = declaration or MG.DEFAULT_DECLARATION
    path = os.path.join(root, rel)
    if not os.path.isfile(path):
        raise GateDeclAppendError("E_GDA_NO_DECL", path)
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        with io.open(path, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise GateDeclAppendError("E_GDA_NO_DECL", "%s (%s)" % (path, exc))
    report = plan(text, identity, capability, reason, declared_by, raw=raw)
    post = report.pop("post")
    report["path"] = rel.replace(os.sep, "/")
    report["wrote"] = False
    report["read_back_ok"] = None
    if not execute:
        report["verdict"] = "PLANNED"
        return report
    data = payload_bytes(raw, post)
    temp = path + TEMP_SUFFIX
    try:
        with io.open(temp, "wb") as handle:
            handle.write(data)
        os.replace(temp, path)
    except (IOError, OSError) as exc:
        if os.path.exists(temp):
            os.remove(temp)
        raise GateDeclAppendError("E_GDA_WRITE", "%s (%s)" % (path, exc))
    with io.open(path, "rb") as handle:
        back = handle.read()
    report["wrote"] = True
    report["read_back_ok"] = back == data
    if not report["read_back_ok"]:
        raise GateDeclAppendError(
            "E_GDA_READBACK",
            "read-back carries %d bytes, predicted %d"
            % (len(back), len(data)))
    if os.path.exists(temp):
        raise GateDeclAppendError("E_GDA_RESIDUE",
                                  "temp file survived: %s" % temp)
    report["verdict"] = "APPENDED"
    return report


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def one_line(report):
    """The single line an operator reads."""
    return ("GATE DECL %s identity=%s capability=%s declarations=%d->%d "
            "bytes=%d->%d verdict=%s"
            % (report["path"], report["identity"], report["capability"],
               report["declarations_before"], report["declarations_after"],
               report["before_bytes"], report["predicted_bytes"],
               report["verdict"]))


USAGE = ("usage: gate_decl_append.py --identity ID --capability CAP "
         "--reason TEXT --declared-by R<nnnn>\n"
         "         [--decl PATH] [--root PATH] [--execute] [--json]\n"
         "  CAP is one of: %s\n"
         "  --execute is required to write; the default is a dry run\n"
         "  exit 0 = planned or appended, 2 = refused, 3 = declaration\n"
         "  missing or malformed, 5 = bad flags\n"
         % "/".join(MG.CAPABILITIES))


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    fields = {"identity": None, "capability": None, "reason": None,
              "declared_by": None}
    declaration = None
    execute = False
    as_json = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--identity", "--capability", "--reason", "--declared-by",
                   "--decl", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_GDA_BAD_ARGS: %s needs a value\n" % arg)
                return 5
            value = argv[index]
            if arg == "--decl":
                declaration = value
            elif arg == "--root":
                root = value
            else:
                fields[arg[2:].replace("-", "_")] = value
        elif arg == "--execute":
            execute = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_GDA_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    missing = [name for name in fields if fields[name] is None]
    if missing:
        sys.stdout.write("E_GDA_BAD_ARGS: missing %s\n"
                         % ", ".join("--" + name.replace("_", "-")
                                     for name in missing))
        sys.stdout.write(USAGE)
        return 5
    try:
        report = append_gate(root, fields["identity"], fields["capability"],
                             fields["reason"], fields["declared_by"],
                             declaration, execute)
    except GateDeclAppendError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 2 if exc.code in REFUSAL_CODES else 3
    except MG.MachineGateError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(one_line(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))