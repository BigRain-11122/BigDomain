# publish_relative_package_identity.py - a DECLARED package places the
# relative publish module.
# Criteria AC-PRPI1..AC-PRPI6 were pre-registered in state/queue/tech.md:482
# (the R2402 seed row) BEFORE this file existed.
#
# Why this exists: relative_import_publish_binding (R2402) added ONE notion -
# the local name a relative import binds - with the module text exactly as the
# file wrote it (".wire", ".", "..pkg.sub"). It reads a file ON ITS OWN, so it
# cannot know which package that file lives in: measured at R2402 on a fixture,
# `from closeout_export_parity_wire import publish` reads WIRE at exit 0 while
# the same file spelled `from .wire import publish` reads RELATIVE at exit 2 -
# a real in-package publisher reported as unplaceable.
#
# This module adds ONE notion and no second classifier: the caller's DECLARED
# package, joined onto the relative text the parent law already names. After
# the join the call is classified exactly like an absolute one - WIRE when the
# joined module is the wire module, FOREIGN otherwise - by the parent law's own
# classify_line, asked at CALL time, with the parent law's merged name table.
# The attribute half is still the guard's law and the prose mask is still the
# identity module's code_only.
#
# Two refusals, both naming the declaration rather than guessing a module:
#   E_PRPI_BAD_PACKAGE    the declared package is not a dotted identifier list
#   E_PRPI_CANNOT_JOIN    the relative text climbs past the declared package
#                         (e.g. `..` from a one-segment package)
# A bad package is a caller error (exit 5). A per-file join that cannot be
# placed is a reading refusal (verdict REFUSED, exit 2) and names both the
# declared package and the module text - never an invented absolute module.
#
# With NO package declared every reading is the parent's own: classify_script
# returns the parent rows unchanged and audit returns the parent's own counts,
# so today's RELATIVE reading stays byte for byte (AC-PRPI3).
#
# This module writes nothing and reads no clock (AC-PRPI6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: publish_relative_package_identity.py --check [--root PATH]
#                                            [--package MODULE]
#                                            [--export NAME] [--owner MODULE]
#                                            [--wire MODULE] [--json]
#   exit 0 = WIRE or EMPTY
#   exit 2 = FOREIGN, UNRESOLVED, RELATIVE or REFUSED, naming every script
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags or the declared package are bad

import importlib
import json
import os
import re
import sys

LABEL = "os-publish-relative-package-identity"
DEFAULT_WIRE = "closeout_export_parity_wire"
DEFAULT_EXPORT_NAME = "status-export.json"
DEFAULT_OWNER = "queue_floor_export_face"
SELF_NAME = "publish_relative_package_identity.py"
SELF_TEST_NAME = "test_publish_relative_package_identity.py"

REFUSED = "REFUSED"

REPORT_KEYS = ("label", "verdict", "root", "package", "scanned",
               "publishers", "wire", "foreign", "unresolved", "relative",
               "no_publish", "from_import", "bare", "refused", "detail")

CALL_KEYS = ("kind", "receiver", "module", "state", "line", "relative",
             "text")

# A declared package is a dotted list of Python identifiers - nothing else is
# an absolute module name this law could honestly join onto.
PACKAGE_RE = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$")

USAGE = (
    "usage: publish_relative_package_identity.py --check [--root PATH] "
    "[--package MODULE] [--export NAME] [--owner MODULE] [--wire MODULE] "
    "[--json]\n"
    "  --check         read every current publisher and place its publish\n"
    "  --root PATH     tree to read (default .)\n"
    "  --package MOD   the package the read scripts live in (default: none,\n"
    "                  which keeps the parent law's RELATIVE reading)\n"
    "  --export NAME   export document basename (default status-export.json)\n"
    "  --owner MODULE  module that owns the current export shape\n"
    "                  (default queue_floor_export_face)\n"
    "  --wire MODULE   module that proves the bytes before publishing\n"
    "                  (default closeout_export_parity_wire)\n"
    "  --json          emit one machine-readable object\n"
    "  exit 0 = WIRE or EMPTY, 2 = FOREIGN, UNRESOLVED, RELATIVE or REFUSED, "
    "3 = root missing, 5 = bad flags or bad package\n"
)


class PublishRelativePackageIdentityError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


class CannotJoinError(PublishRelativePackageIdentityError):
    """A relative text that climbs past the declared package."""

    def __init__(self, package, text):
        PublishRelativePackageIdentityError.__init__(
            self, "E_PRPI_CANNOT_JOIN", "package=%s module=%s" % (package, text))
        self.package = package
        self.text = text


def parent():
    """The module that owns relative binding and the one publish classifier."""
    return importlib.import_module("relative_import_publish_binding")


def identity():
    """The module that owns the import patterns and the prose mask."""
    return importlib.import_module("export_publish_wire_identity")


def check_package(package):
    """Refuse a declared package that is not a dotted identifier list."""
    if package is None:
        return None
    if not PACKAGE_RE.match(package):
        raise PublishRelativePackageIdentityError("E_PRPI_BAD_PACKAGE", package)
    return package


def split_relative(text):
    """(leading dot count, dotted tail) for a relative module text."""
    dots = len(text) - len(text.lstrip("."))
    return dots, text[dots:]


def join_package(package, text):
    """Join one relative module text onto the declared package.

    `.` -> the package itself; `.M` -> package.M; `..M` drops one trailing
    package segment first. A text that would climb past the package refuses
    (AC-PRPI4) instead of inventing a module.
    """
    dots, tail = split_relative(text)
    if dots == 0:
        raise PublishRelativePackageIdentityError(
            "E_PRPI_NOT_RELATIVE", "package=%s module=%s" % (package, text))
    parts = package.split(".")
    climb = dots - 1
    if climb >= len(parts):
        raise CannotJoinError(package, text)
    base = parts[:len(parts) - climb] if climb else parts
    if tail:
        base = base + tail.split(".")
    return ".".join(base)


def classify_line(line, receivers, publish_names, package,
                  export_name=DEFAULT_EXPORT_NAME, wire_module=DEFAULT_WIRE):
    """One publish call on this line, or None - the parent law's decision.

    The parent law owns the spelling test, the two-sided import/call agreement
    and the merged name table. This file only replaces a relative module text
    with the joined absolute one before the parent's state law is re-applied:
    WIRE when the joined module is the wire module, FOREIGN otherwise.
    """
    row = parent().classify_line(line, receivers, publish_names,
                                export_name, wire_module)
    if row is None:
        return None
    if row["kind"] == "from_import" and row["module"].startswith("."):
        joined = join_package(package, row["module"])
        row["module"] = joined
        row["state"] = identity().WIRE if joined == wire_module \
            else identity().FOREIGN
        row["relative"] = True
    else:
        row["relative"] = False
    return row


def verdict_of(states):
    """UNRESOLVED outranks FOREIGN, which outranks a REFUSED join, which
    outranks RELATIVE, which outranks WIRE; nothing at all is the identity
    module's NO-PUBLISH word."""
    if not states:
        return identity().NO_PUBLISH
    for state in (identity().UNRESOLVED, identity().FOREIGN, REFUSED,
                  parent().RELATIVE):
        if state in states:
            return state
    return identity().WIRE


def classify_script(lines, package=None, export_name=DEFAULT_EXPORT_NAME,
                    wire_module=DEFAULT_WIRE, refusals=None):
    """Every publish call in one file, in file order, with its spelling.

    With no package the parent's own reader answers unchanged (AC-PRPI3). A
    join that cannot be placed appends one refusal row (when a list is given)
    and the call is reported as REFUSED rather than guessed.
    """
    lead = identity()
    if package is None:
        return parent().classify_script(lines, export_name, wire_module)
    code = lead.code_only(lines)
    receivers = lead.import_bindings(code)
    publish_names = parent().imported_publish_names(code)
    calls = []
    for number, line in enumerate(code, 1):
        try:
            call = classify_line(line, receivers, publish_names, package,
                                 export_name, wire_module)
        except CannotJoinError as exc:
            if refusals is None:
                raise
            refusals.append({"code": exc.code, "package": exc.package,
                             "module": exc.text, "line": number,
                             "text": line.strip()[:120]})
            calls.append({"kind": "from_import", "receiver": "",
                          "module": exc.text, "state": REFUSED,
                          "line": number, "relative": True,
                          "text": line.strip()[:120]})
            continue
        if call is None:
            continue
        calls.append({
            "kind": call["kind"],
            "receiver": call["receiver"],
            "module": call["module"],
            "state": call["state"],
            "line": number,
            "relative": call["relative"],
            "text": line.strip()[:120],
        })
    return calls


def audit(root, package=None, export_name=DEFAULT_EXPORT_NAME,
          owner=DEFAULT_OWNER, wire_module=DEFAULT_WIRE):
    """Read every current publisher and place its publish spelling."""
    if not os.path.isdir(root):
        raise PublishRelativePackageIdentityError("E_PRPI_NO_ROOT", root)
    check_package(package)
    scanner = parent().guard()
    lead = identity()
    scanned = 0
    publishers = []
    wire = []
    foreign = []
    unresolved = []
    relative = []
    no_publish = []
    refused = []
    refused_scripts = []
    from_import = 0
    bare = 0
    relative_calls = 0
    detail = []
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
        code = lead.code_only(lines)
        if not any(scanner.uses_owner(line, owner) for line in code):
            continue
        here_refusals = []
        calls = classify_script(lines, package, export_name, wire_module,
                                here_refusals)
        verdict = verdict_of([row["state"] for row in calls])
        if verdict == lead.NO_PUBLISH:
            no_publish.append(rel)
            continue
        publishers.append(rel)
        if verdict == lead.WIRE:
            wire.append(rel)
        elif verdict == lead.FOREIGN:
            foreign.append(rel)
        elif verdict == REFUSED:
            refused_scripts.append(rel)
        elif verdict == parent().RELATIVE:
            relative.append(rel)
        else:
            unresolved.append(rel)
        for row in calls:
            if row["kind"] == "from_import":
                from_import += 1
            elif row["kind"] == "bare":
                bare += 1
            if row["relative"]:
                relative_calls += 1
            item = dict(row)
            item["path"] = rel
            detail.append(item)
        for item in here_refusals:
            item["path"] = rel
            refused.append("%s:%d" % (rel, item["line"]))
    refused = sorted(set(refused))
    refused_scripts = sorted(set(refused_scripts))
    if unresolved:
        verdict = lead.UNRESOLVED
    elif foreign:
        verdict = lead.FOREIGN
    elif refused_scripts:
        verdict = REFUSED
    elif relative:
        verdict = parent().RELATIVE
    elif wire:
        verdict = lead.WIRE
    else:
        verdict = lead.EMPTY
    report = {
        "label": LABEL,
        "verdict": verdict,
        "root": root,
        "package": package if package is not None else "(none)",
        "scanned": scanned,
        "publishers": sorted(publishers),
        "wire": sorted(wire),
        "foreign": sorted(foreign),
        "unresolved": sorted(unresolved),
        "relative": relative_calls,
        "no_publish": sorted(no_publish),
        "from_import": from_import,
        "bare": bare,
        "refused": refused,
        "detail": detail,
    }
    return report, (2 if verdict in (lead.FOREIGN, lead.UNRESOLVED,
                                     parent().RELATIVE, REFUSED) else 0)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0

    root = "."
    package = None
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
        elif arg in ("--root", "--package", "--export", "--owner", "--wire"):
            index += 1
            if index >= len(argv):
                sys.stderr.write("E_PRPI_BAD_FLAGS missing value for %s\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            elif arg == "--package":
                package = argv[index]
            elif arg == "--export":
                export_name = argv[index]
            elif arg == "--owner":
                owner = argv[index]
            else:
                wire_module = argv[index]
        else:
            sys.stderr.write("E_PRPI_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_PRPI_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root, package, export_name, owner, wire_module)
    except CannotJoinError as exc:
        sys.stderr.write("%s\n" % exc)
        return 2
    except PublishRelativePackageIdentityError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5 if exc.code in ("E_PRPI_BAD_PACKAGE",
                                 "E_PRPI_NOT_RELATIVE") else 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "PUBLISH RELATIVE PACKAGE IDENTITY %s verdict=%s package=%s "
            "scanned=%d publishers=%d wire=%d foreign=%s unresolved=%s "
            "relative=%d no_publish=%d from_import=%d bare=%d "
            "refused=%d wire_module=%s\n" % (
                report["label"], report["verdict"], report["package"],
                report["scanned"], len(report["publishers"]),
                len(report["wire"]),
                ",".join(report["foreign"]) or "(none)",
                ",".join(report["unresolved"]) or "(none)",
                report["relative"], len(report["no_publish"]),
                report["from_import"], report["bare"],
                len(report["refused"]), wire_module))
        for row in report["detail"]:
            if row["state"] == identity().WIRE:
                continue
            sys.stdout.write("  %s %s:%d kind=%s receiver=%s module=%s\n" % (
                row["state"], row["path"], row["line"], row["kind"],
                row["receiver"] or "(bare)", row["module"] or "(unbound)"))
        for item in report["refused"]:
            sys.stdout.write("  REFUSED %s E_PRPI_CANNOT_JOIN package=%s\n" % (
                item, report["package"]))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))