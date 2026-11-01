# gate_decl_retire.py - drop one capability blocker through machine_gate's law
# Criteria AC-GDRT1..AC-GDRT6 were pre-registered in state/queue/tech.md (the
# R2312 seed row) BEFORE this file existed. Anchor check at HEAD 2026-11-01:
# "gate_decl_retire", "AC-GDRT", "E_GDRT", "os-gate-decl-retire" and
# "test_gate_decl_retire" hit only prose and the seed/closeout helpers, with
# no product code path.
#
# Why this exists: the declaration can gain an entry through gate_decl_append
# but it can never lose one. Once the blocked row is completed or its text
# moves, the entry stays in state/machine_gates.json forever and reads INERT,
# so the declaration rots in exactly the direction gate_drift and the identity
# reader name - and retiring it means editing JSON by hand.
#
# The shape law is IMPORTED, never copied: the entry keys, the declaration
# keys and the post read-back all come out of machine_gate, and the live
# "is this entry still doing its job" reading is machine_gate.gate itself. A
# patched reader therefore flows straight through, which the suite proves.
# The array-span scanner is imported from gate_decl_append so the file keeps
# one array law rather than a second copy of the same string-aware walk.
#
# Refusals happen BEFORE any byte changes: an identity that is not declared
# cannot be retired, and an entry whose identity the live reading still
# reports as BLOCKED is still doing its job and is not a retirement candidate.
#
# The write is a TEXTUAL splice out of one entry object, so every surviving
# entry stays byte-intact. Dry run is the default: plan() reports the before
# and after byte counts and the removed index and writes nothing. execute=True
# performs one atomic os.replace, proves the read-back bytes equal the
# prediction and leaves no temp file.
#
# Pure ASCII source, stdlib only, zero network, no clock read.
#
# CLI: gate_decl_retire.py --identity ID [--queue NAME] [--decl PATH]
#      [--root PATH] [--execute] [--json]
#   exit 0 = planned (or retired with --execute)
#   exit 2 = refused (undeclared identity, still-blocked entry, bad field,
#            shape or write/read-back failure)
#   exit 3 = declaration or queue missing / unreadable / malformed
#   exit 5 = bad flags

import io
import json
import os
import sys

import gate_decl_append as GDA
import machine_gate as MG

TEMP_SUFFIX = ".gdrt-tmp"

REPORT_KEYS = ("path", "identity", "capability", "removed_at",
               "declarations_before", "declarations_after", "before_bytes",
               "predicted_bytes", "wrote", "read_back_ok", "verdict")

# Refusals the caller can act on; everything else is a bad input file.
REFUSAL_CODES = ("E_GDRT_UNDECLARED", "E_GDRT_STILL_BLOCKED",
                 "E_GDRT_BAD_FIELD", "E_GDRT_SHAPE", "E_GDRT_WRITE",
                 "E_GDRT_READBACK", "E_GDRT_RESIDUE")


class GateDeclRetireError(Exception):
    """Raised when an entry cannot be retired without guessing."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def entry_spans(body):
    """The (start, end) spans of every top-level object inside an array body."""
    spans = []
    depth = 0
    in_string = False
    escape = False
    start = None
    for index, char in enumerate(body):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start is not None:
                spans.append((start, index + 1))
                start = None
    return spans


def array_span(text, key="gates"):
    """The array span, through gate_decl_append's own string-aware walk."""
    try:
        return GDA.array_span(text, key)
    except GDA.GateDeclAppendError as exc:
        raise GateDeclRetireError("E_GDRT_BAD_DECL", exc.detail)


def _check_identity(identity):
    """Validate the caller's identity field before anything else happens."""
    if not isinstance(identity, str) or not identity.strip():
        raise GateDeclRetireError("E_GDRT_BAD_FIELD", "field identity is empty")
    if '"' in identity or "\\" in identity or "\n" in identity \
            or "\r" in identity:
        raise GateDeclRetireError(
            "E_GDRT_BAD_FIELD",
            "field identity cannot carry a quote, a backslash or a newline: %r"
            % (identity,))


def _blocked_line(report, identity):
    """The blocked row line carrying this identity, or None when inert."""
    for item in report["blocked"]:
        if item["identity"] == identity:
            return item["line"]
    return None


def plan(text, identity, live_report):
    """Compute the post text without writing; return the planned report."""
    _check_identity(identity)
    if text.count('"version"') > 1:
        raise GateDeclRetireError(
            "E_GDRT_BAD_DECL",
            "the text carries %d declaration headers" % text.count('"version"'))
    try:
        before = MG.read_declaration_text(text)
    except MG.MachineGateError as exc:
        raise GateDeclRetireError("E_GDRT_BAD_DECL",
                                  "declaration does not parse: %s" % exc.code)
    identities = [entry["identity"] for entry in before["gates"]]
    if identity not in identities:
        raise GateDeclRetireError(
            "E_GDRT_UNDECLARED",
            "field identity %r is not declared, so it cannot be retired"
            % identity)
    line = _blocked_line(live_report, identity)
    if line is not None:
        raise GateDeclRetireError(
            "E_GDRT_STILL_BLOCKED",
            "field identity %r still blocks a live row at line %d, so it is "
            "still doing its job" % (identity, line))
    index = identities.index(identity)
    entry = before["gates"][index]
    open_at, close_at = array_span(text, "gates")
    body = text[open_at + 1:close_at]
    spans = entry_spans(body)
    if len(spans) != len(before["gates"]):
        raise GateDeclRetireError(
            "E_GDRT_SHAPE",
            "the array body carries %d objects against %d declared entries"
            % (len(spans), len(before["gates"])))
    if len(spans) == 1:
        seg_start, seg_end = spans[0]
    elif index < len(spans) - 1:
        seg_start, seg_end = spans[index][0], spans[index + 1][0]
    else:
        seg_start, seg_end = spans[index - 1][1], spans[index][1]
    body_post = body[:seg_start] + body[seg_end:]
    post = text[:open_at + 1] + body_post + text[close_at:]
    try:
        after = MG.read_declaration_text(post)
    except MG.MachineGateError as exc:
        raise GateDeclRetireError("E_GDRT_SHAPE",
                                  "post text does not parse: %s" % exc.code)
    if len(after["gates"]) != len(before["gates"]) - 1:
        raise GateDeclRetireError(
            "E_GDRT_SHAPE",
            "post text carries %d entries, expected %d"
            % (len(after["gates"]), len(before["gates"]) - 1))
    if any(row["identity"] == identity for row in after["gates"]):
        raise GateDeclRetireError(
            "E_GDRT_SHAPE", "post text still carries %r" % identity)
    for other in range(len(spans)):
        if other == index:
            continue
        survivor = body[spans[other][0]:spans[other][1]]
        if survivor not in body_post:
            raise GateDeclRetireError(
                "E_GDRT_SHAPE",
                "surviving entry %d is no longer byte-intact" % other)
    return {
        "identity": identity,
        "capability": entry["capability"],
        "removed_at": index,
        "declarations_before": len(before["gates"]),
        "declarations_after": len(after["gates"]),
        "before_bytes": len(text.encode("utf-8")),
        "predicted_bytes": len(post.encode("utf-8")),
        "post": post,
    }


def retire(root, identity, queue_name="tech", declaration=None, execute=False):
    """Plan (and optionally perform) one entry retirement under root."""
    rel = declaration or MG.DEFAULT_DECLARATION
    path = os.path.join(root, rel)
    if not os.path.isfile(path):
        raise GateDeclRetireError("E_GDRT_NO_DECL", path)
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise GateDeclRetireError("E_GDRT_NO_DECL", "%s (%s)" % (path, exc))
    try:
        live = MG.gate(root, queue_name, rel)
    except MG.MachineGateError as exc:
        raise GateDeclRetireError("E_GDRT_NO_QUEUE",
                                  "%s (%s)" % (exc.code, exc.detail))
    report = plan(text, identity, live)
    post = report.pop("post")
    report["path"] = rel.replace(os.sep, "/")
    report["wrote"] = False
    report["read_back_ok"] = None
    if not execute:
        report["verdict"] = "PLANNED"
        return report
    data = post.encode("utf-8")
    temp = path + TEMP_SUFFIX
    try:
        with io.open(temp, "wb") as handle:
            handle.write(data)
        os.replace(temp, path)
    except (IOError, OSError) as exc:
        if os.path.exists(temp):
            os.remove(temp)
        raise GateDeclRetireError("E_GDRT_WRITE", "%s (%s)" % (path, exc))
    with io.open(path, "rb") as handle:
        back = handle.read()
    report["wrote"] = True
    report["read_back_ok"] = back == data
    if not report["read_back_ok"]:
        raise GateDeclRetireError(
            "E_GDRT_READBACK",
            "read-back carries %d bytes, predicted %d"
            % (len(back), len(data)))
    if os.path.exists(temp):
        raise GateDeclRetireError("E_GDRT_RESIDUE",
                                  "temp file survived: %s" % temp)
    report["verdict"] = "RETIRED"
    return report


def one_line(report):
    """The single line an operator reads."""
    return ("GATE DECL RETIRE %s identity=%s capability=%s removed_at=%s "
            "declarations=%d->%d bytes=%d->%d verdict=%s"
            % (report["path"], report["identity"], report["capability"],
               report["removed_at"], report["declarations_before"],
               report["declarations_after"], report["before_bytes"],
               report["predicted_bytes"], report["verdict"]))


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: gate_decl_retire.py --identity ID [--queue NAME] "
         "[--decl PATH] [--root PATH]\n"
         "         [--execute] [--json]\n"
         "  --queue defaults to tech (state/queue/<QUEUE>.md)\n"
         "  --decl defaults to %s\n"
         "  --execute is required to write; the default is a dry run\n"
         "  exit 0 = planned or retired, 2 = refused, 3 = declaration or\n"
         "  queue missing or malformed, 5 = bad flags\n"
         % MG.DEFAULT_DECLARATION.replace(os.sep, "/"))


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    identity = None
    queue_name = "tech"
    declaration = None
    execute = False
    as_json = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--identity", "--queue", "--decl", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_GDRT_BAD_ARGS: %s needs a value\n" % arg)
                return 5
            value = argv[index]
            if arg == "--identity":
                identity = value
            elif arg == "--queue":
                queue_name = value
            elif arg == "--decl":
                declaration = value
            else:
                root = value
        elif arg == "--execute":
            execute = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_GDRT_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if identity is None:
        sys.stdout.write("E_GDRT_BAD_ARGS: missing --identity\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = retire(root, identity, queue_name, declaration, execute)
    except GateDeclRetireError as exc:
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