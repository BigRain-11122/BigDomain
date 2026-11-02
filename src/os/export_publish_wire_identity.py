# export_publish_wire_identity.py - routed means routed BY THE WIRE
# Criteria AC-EPWI1..AC-EPWI6 were pre-registered in state/queue/tech.md:447
# (the R2384 seed row) BEFORE this file existed.
#
# Why this exists: R2384 shipped export_publish_path_guard, which names every
# script on the CURRENT export publishing path that writes the document itself
# and reads every `.publish(..., EXPORT, ...)` as the proven route. But it never
# asked WHICH module that publish call resolves to, so a script that hands the
# export to some other module's publish call satisfied the guard while never
# touching closeout_export_parity_wire - the only publisher that proves the
# bytes it writes. Measured at R2384 STEP7 on a fixture, and still true at HEAD.
#
# This module turns the callee into a reading. For every script on the CURRENT
# path (the `uses_owner` law is imported from the guard, never restated), each
# publish call that carries the export is resolved through THAT FILE's own
# import lines:
#
#   WIRE        the callee resolves to the module that proves the bytes
#   FOREIGN     the callee resolves to any other module (both named)
#   UNRESOLVED  the receiver is not bound by any import line, so naming a
#               module would be a guess - a call renamed without its import,
#               or an import renamed without its call, lands here
#   NO-PUBLISH  the script is on the path but publishes nothing at all
#
# Verdict precedence is UNRESOLVED then FOREIGN then WIRE, because a callee
# that cannot be resolved is a weaker claim than a callee that was read and is
# wrong, and both are worse than a callee proven to be the wire.
#
# The reading is derived from the import lines and the call line TOGETHER
# (AC-EPWI4): an import that stops matching its call reads UNRESOLVED rather
# than borrowing the name it used to have. The routed-publish test itself is
# export_publish_path_guard.routed_publish, asked at CALL time, so patching
# that law moves this reading and there is no second definition of "is this a
# publish of the export" (AC-EPWI1).
#
# A tree with no current publisher reads EMPTY at exit 0, deliberately not
# WIRE: nothing on the path is not the same as everything routed.
#
# Honest limits, stated rather than hidden: the law is line based, so a callee
# reached through a dict lookup, a getattr or a call chain is not resolved and
# reads UNRESOLVED rather than being called clean. String and comment spans are
# blanked before the reading (code_only), because a publish spelling inside a
# docstring or a fixture literal is not a call - measured live this window: a
# round script's own prose and its embedded fixture script both read as
# UNRESOLVED until the token mask went in. A `from M import publish` followed
# by a BARE `publish(...)` call is outside the guard's attribute-call law, so
# it did not count as a routed publish at all and the script read NO-PUBLISH;
# the spelling law now lives in export_publish_from_import_law (R2400), which
# this module asks at CALL time, and the row shape below is unchanged - the
# attribute spelling still resolves to the same receiver, module and state.
#
# This module writes nothing and reads no clock (AC-EPWI6). Source is pure
# ASCII, stdlib only, zero network.
#
# CLI: export_publish_wire_identity.py --check [--root PATH] [--export NAME]
#                                      [--owner MODULE] [--wire MODULE] [--json]
#   exit 0 = WIRE (every routed publish resolves to the wire) or EMPTY
#   exit 2 = FOREIGN or UNRESOLVED, naming every script and line
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags are bad

import importlib
import io
import json
import os
import re
import sys
import tokenize

LABEL = "os-export-publish-wire-identity"
DEFAULT_WIRE = "closeout_export_parity_wire"
DEFAULT_EXPORT_NAME = "status-export.json"
DEFAULT_OWNER = "queue_floor_export_face"
SELF_NAME = "export_publish_wire_identity.py"
SELF_TEST_NAME = "test_export_publish_wire_identity.py"
SKIP_DIRS = (".git", "media", "logs", "__pycache__", ".codely-cli")

REPORT_KEYS = ("label", "verdict", "root", "scanned", "publishers",
               "wire", "foreign", "unresolved", "no_publish", "detail")

WIRE = "WIRE"
FOREIGN = "FOREIGN"
UNRESOLVED = "UNRESOLVED"
NO_PUBLISH = "NO-PUBLISH"
EMPTY = "EMPTY"

IMPORT_AS_RE = re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)\s+as\s+([A-Za-z_]\w*)")
IMPORT_PLAIN_RE = re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)")
FROM_AS_RE = re.compile(
    r"^\s*from\s+([A-Za-z_][\w.]*)\s+import\s+([A-Za-z_]\w*)\s+as\s+([A-Za-z_]\w*)")
FROM_PLAIN_RE = re.compile(
    r"^\s*from\s+([A-Za-z_][\w.]*)\s+import\s+([A-Za-z_]\w*)")
RECEIVER_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\.\s*publish\s*\(")

USAGE = (
    "usage: export_publish_wire_identity.py --check [--root PATH] "
    "[--export NAME] [--owner MODULE] [--wire MODULE] [--json]\n"
    "  --check         resolve every routed publish to its callee module\n"
    "  --root PATH     tree to read (default .)\n"
    "  --export NAME   export document basename (default status-export.json)\n"
    "  --owner MODULE  module that owns the current export shape\n"
    "                  (default queue_floor_export_face)\n"
    "  --wire MODULE   module that proves the bytes before publishing\n"
    "                  (default closeout_export_parity_wire)\n"
    "  --json          emit one machine-readable object\n"
    "  exit 0 = WIRE or EMPTY, 2 = FOREIGN or UNRESOLVED, "
    "3 = root missing, 5 = bad flags\n"
)


class ExportPublishWireIdentityError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def guard():
    """The module that owns the current-path and routed-publish laws.

    Imported at call time so a caller (and the suite) can patch it and move
    this reading, and so this file never carries a second copy of that law.
    """
    return importlib.import_module("export_publish_path_guard")


def import_bindings(lines):
    """alias -> module for every import line in this file.

    `import a.b as c` binds c to a.b; `import a.b` binds a to a.b (a bare
    import of a dotted module is asked by its leading name because that is
    what the call site can spell); `from m import n [as x]` binds x (or n)
    to m, because the callee of that call lives in m.
    """
    bindings = {}
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        found = IMPORT_AS_RE.match(line)
        if found:
            bindings[found.group(2)] = found.group(1)
            continue
        found = FROM_AS_RE.match(line)
        if found:
            bindings[found.group(3)] = found.group(1)
            continue
        found = FROM_PLAIN_RE.match(line)
        if found:
            bindings[found.group(2)] = found.group(1)
            continue
        found = IMPORT_PLAIN_RE.match(line)
        if found:
            name = found.group(1)
            bindings[name.split(".")[0]] = name
    return bindings


def callee_of(line, bindings):
    """(receiver, module) for the publish call on this line, module may be ''.

    A receiver that no import line binds is reported with module '' - the
    caller reads that as UNRESOLVED rather than as any module at all. Only
    attribute calls reach here, because the routed-publish test is the guard's
    `.publish(` law; there is no second spelling of a publish in this file.
    """
    found = RECEIVER_RE.search(line)
    if found:
        receiver = found.group(1)
        return receiver, bindings.get(receiver, "")
    return "", ""


def code_only(lines):
    """The same lines with string and comment spans blanked out.

    A publish spelling inside a docstring or a fixture literal is not a call,
    and the token stream is the only honest way to tell them apart, so the
    reading is taken over code only. Line numbers are preserved exactly, so a
    finding still names the line the operator will open.
    """
    text = "\n".join(lines)
    masked = [list(line) for line in lines]
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # Source that will not tokenise is read as it is rather than hidden.
        return list(lines)
    for token in tokens:
        if token.type not in (tokenize.STRING, tokenize.COMMENT):
            continue
        start_row, start_col = token.start
        end_row, end_col = token.end
        for row in range(start_row, end_row + 1):
            if row - 1 >= len(masked):
                continue
            chars = masked[row - 1]
            first = start_col if row == start_row else 0
            last = end_col if row == end_row else len(chars)
            for col in range(first, min(last, len(chars))):
                chars[col] = " "
    return ["".join(chars) for chars in masked]


def from_import_law():
    """The module that owns which publish SPELLINGS count as a publish.

    Imported at call time so a caller (and the suite) can patch it and move
    this reading, and so the spelling law has exactly one owner.
    """
    return importlib.import_module("export_publish_from_import_law")


def audit_script(source_lines, export_name, wire_module):
    """Every publish call in one file, resolved against its own imports.

    The spelling law is export_publish_from_import_law asked at CALL time, so
    a `from M import publish` followed by a bare `publish(...)` is read here
    too instead of reading NO-PUBLISH. The row shape is unchanged on purpose:
    the attribute spelling still yields the same receiver, module and state,
    and the four keys below are exactly what this module published before.
    """
    calls = []
    for row in from_import_law().classify_script(
            source_lines, export_name, wire_module):
        calls.append({"line": row["line"], "receiver": row["receiver"],
                      "module": row["module"], "state": row["state"],
                      "text": row["text"]})
    return calls


def verdict_of(states):
    """UNRESOLVED outranks FOREIGN outranks WIRE; nothing at all is NO-PUBLISH."""
    if not states:
        return NO_PUBLISH
    for state in (UNRESOLVED, FOREIGN):
        if state in states:
            return state
    return WIRE


def audit(root, export_name=DEFAULT_EXPORT_NAME, owner=DEFAULT_OWNER,
          wire_module=DEFAULT_WIRE):
    """Read every script and resolve each current publisher's callee."""
    if not os.path.isdir(root):
        raise ExportPublishWireIdentityError("E_EPWI_NO_ROOT", root)
    scanner = guard()
    scanned = 0
    publishers = []
    wire = []
    foreign = []
    unresolved = []
    no_publish = []
    detail = []
    # This module and its suite carry the publish spellings as fixture and
    # docstring text, the same reason the guard excludes its own pair.
    mine = (SELF_NAME, SELF_TEST_NAME)
    for path in scanner.scan_scripts(root):
        scanned += 1
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        if os.path.basename(rel) in mine:
            continue
        try:
            lines = scanner.read_lines(path)
        except (IOError, OSError):
            continue
        code = code_only(lines)
        on_path = any(scanner.uses_owner(line, owner) for line in code)
        if not on_path:
            continue
        calls = audit_script(lines, export_name, wire_module)
        verdict = verdict_of([row["state"] for row in calls])
        if verdict == NO_PUBLISH:
            # Not a publisher: reported, never counted as proven.
            no_publish.append(rel)
            continue
        publishers.append(rel)
        if verdict == WIRE:
            wire.append(rel)
        elif verdict == FOREIGN:
            foreign.append(rel)
        else:
            unresolved.append(rel)
        for row in calls:
            item = dict(row)
            item["path"] = rel
            detail.append(item)
    if foreign:
        verdict = FOREIGN
    elif unresolved:
        verdict = UNRESOLVED
    elif wire:
        verdict = WIRE
    else:
        verdict = EMPTY
    report = {
        "label": LABEL,
        "verdict": verdict,
        "root": root,
        "scanned": scanned,
        "publishers": sorted(publishers),
        "wire": sorted(wire),
        "foreign": sorted(foreign),
        "unresolved": sorted(unresolved),
        "no_publish": sorted(no_publish),
        "detail": detail,
    }
    return report, (2 if verdict in (FOREIGN, UNRESOLVED) else 0)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0

    root = "."
    export_name = DEFAULT_EXPORT_NAME
    owner = DEFAULT_OWNER
    wire_module = DEFAULT_WIRE
    as_json = False
    saw_check = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            saw_check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--export", "--owner", "--wire"):
            index += 1
            if index >= len(argv):
                sys.stderr.write("E_EPWI_BAD_FLAGS missing value for %s\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            elif arg == "--export":
                export_name = argv[index]
            elif arg == "--owner":
                owner = argv[index]
            else:
                wire_module = argv[index]
        else:
            sys.stderr.write("E_EPWI_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_EPWI_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root, export_name, owner, wire_module)
    except ExportPublishWireIdentityError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "EXPORT PUBLISH WIRE IDENTITY %s verdict=%s scanned=%d "
            "publishers=%d wire=%d foreign=%s unresolved=%s no_publish=%d "
            "wire_module=%s\n" % (
                report["label"], report["verdict"], report["scanned"],
                len(report["publishers"]), len(report["wire"]),
                ",".join(report["foreign"]) or "(none)",
                ",".join(report["unresolved"]) or "(none)",
                len(report["no_publish"]), wire_module))
        for row in report["detail"]:
            if row["state"] == WIRE:
                continue
            sys.stdout.write("  %s %s:%d receiver=%s module=%s\n" % (
                row["state"], row["path"], row["line"],
                row["receiver"] or "(bare)", row["module"] or "(unbound)"))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))