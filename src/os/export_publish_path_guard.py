# export_publish_path_guard.py - name every CURRENT export publisher that
# writes the document itself instead of handing it to the proven wire
# Criteria AC-EPPG1..AC-EPPG6 were pre-registered in state/queue/tech.md:431
# (the R2378 seed row) BEFORE this file existed.
#
# Why this exists: R2378 made closeout_R2377.py publish docs/status-export.json
# through closeout_export_parity_wire.publish, so that one closeout proves the
# bytes it is about to publish before it publishes them. But the emission path
# has several writers and only one of them asks the wire: closeout_R2374.py,
# closeout_R2375.py and closeout_R2376.py import queue_floor_export_face, call
# QFE.apply and then write the document themselves. Nothing read that.
#
# This module turns it into a reading. The question it asks is deliberately
# narrow, because a wide one would be noise: the repository carries more than a
# hundred one-off historical scripts that wrote whatever the export shape was at
# their round. Those fossils are REPORTED as `historical` and are never called
# offenders, because they do not belong to the current publishing path. A script
# belongs to the current path when it composes the export through the module that
# OWNS the current shape - queue_floor_export_face - and the owner is a flag, not
# a hardcoded filename list. Within that path:
#
#   BYPASS  the script names the export in a write primitive and writes it itself
#   CLEAN   every publish it performs goes through a publish call that carries
#           the export document (the wire's proven path)
#
# The answer is a property of the code, not of a whitelist: no blessed filenames,
# no canned offender list, and a routed script reads CLEAN whatever it is called
# while a bypassing script reads BYPASS whatever it is called (AC-EPPG2).
#
# A tree with no current publisher reads EMPTY at exit 0, deliberately not
# CLEAN: "nothing to check" is not "everything is routed" (AC-EPPG4).
#
# Honest limits, stated rather than hidden: the law is line based, so a write
# whose target is only reachable through an alias built at runtime is not
# detected; and the guard excludes itself and its own suite, because both carry
# the write literals as fixture text.
#
# This module writes nothing and reads no clock (AC-EPPG3). Source is pure
# ASCII, stdlib only, zero network (AC-EPPG6).
#
# CLI: export_publish_path_guard.py --check [--root PATH] [--export NAME]
#                                    [--owner MODULE] [--json]
#   exit 0 = CLEAN (every current publisher routes through the wire) or EMPTY
#   exit 2 = BYPASS, naming every current publisher that writes the export
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags are bad

import io
import json
import os
import re
import sys

LABEL = "os-export-publish-path-guard"
DEFAULT_EXPORT_NAME = "status-export.json"
DEFAULT_OWNER = "queue_floor_export_face"
OWNER_ALIAS = "QFE"
SELF_NAME = "export_publish_path_guard.py"
SELF_TEST_NAME = "test_export_publish_path_guard.py"
SKIP_DIRS = (".git", "media", "logs", "__pycache__", ".codely-cli")

REPORT_KEYS = ("label", "verdict", "root", "scanned", "publishers",
               "offenders", "clean", "historical", "detail")

# A write primitive that takes the export document as its own argument.
WRITE_CALL_RE = re.compile(r"(?:write_text|write_bytes)\s*\(")
OPEN_CALL_RE = re.compile(r"\bopen\s*\(")
OPEN_MODE_RE = re.compile(r"""['"][wax]""")
# A publish that carries the export document through the proven path.
PUBLISH_CALL_RE = re.compile(r"\.\s*publish\s*\(")
ALIAS_RE = re.compile(r"\b%s\b" % OWNER_ALIAS)

USAGE = (
    "usage: export_publish_path_guard.py --check [--root PATH] "
    "[--export NAME] [--owner MODULE] [--json]\n"
    "  --check         read every script and name the current publishers\n"
    "  --root PATH     tree to read (default .)\n"
    "  --export NAME   export document basename (default status-export.json)\n"
    "  --owner MODULE  module that owns the current export shape\n"
    "                  (default queue_floor_export_face)\n"
    "  --json          emit one machine-readable object\n"
    "  exit 0 = CLEAN or EMPTY, 2 = BYPASS (offenders named), "
    "3 = root missing, 5 = bad flags\n"
)


class ExportPublishPathGuardError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def names_export(line, export_name=DEFAULT_EXPORT_NAME):
    """Does this line name the export document at all?"""
    if re.search(r"\bEXPORT\b", line):
        return True
    return export_name in line


def direct_write(line, export_name=DEFAULT_EXPORT_NAME):
    """Return the write kind when this line WRITES the export, else ''."""
    text = line.strip()
    if not text or text.startswith("#"):
        return ""
    if not names_export(text, export_name):
        return ""
    if WRITE_CALL_RE.search(text):
        return "write"
    if OPEN_CALL_RE.search(text) and OPEN_MODE_RE.search(text):
        return "open"
    return ""


def routed_publish(line, export_name=DEFAULT_EXPORT_NAME):
    """Does this line publish the export through a wire-style publish call?"""
    text = line.strip()
    if not text or text.startswith("#"):
        return False
    return bool(PUBLISH_CALL_RE.search(text)) and names_export(text, export_name)


def uses_owner(line, owner=DEFAULT_OWNER):
    """Does this line ask the module that owns the current export shape?"""
    text = line.strip()
    if not text or text.startswith("#"):
        return False
    if owner in text:
        return True
    return bool(ALIAS_RE.search(text))


def scan_scripts(root):
    """Every .py under root, skipping only this module, its suite and junk."""
    me = os.path.normcase(os.path.abspath(__file__))
    mine = os.path.normcase(os.path.join(os.path.dirname(me), SELF_TEST_NAME))
    found = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.normcase(os.path.abspath(os.path.join(base, name)))
            if path == me or path == mine:
                continue
            found.append(os.path.join(base, name))
    found.sort()
    return found


def read_lines(path):
    with io.open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read().splitlines()


def audit(root, export_name=DEFAULT_EXPORT_NAME, owner=DEFAULT_OWNER):
    """Read every script and report which CURRENT publishers write the export."""
    if not os.path.isdir(root):
        raise ExportPublishPathGuardError("E_EPPG_NO_ROOT", root)
    scanned = 0
    publishers = []
    current = []
    offenders = []
    historical = []
    detail = []
    for path in scan_scripts(root):
        scanned += 1
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        try:
            lines = read_lines(path)
        except (IOError, OSError):
            # An unreadable script is not silently called clean: it simply has
            # no readable publishing line, and `scanned` says it was walked.
            continue
        publishes = False
        on_path = False
        writes = []
        for number, line in enumerate(lines, 1):
            if uses_owner(line, owner):
                on_path = True
            kind = direct_write(line, export_name)
            if kind:
                publishes = True
                writes.append({"path": rel, "line": number, "kind": kind,
                               "text": line.strip()[:120]})
                continue
            if routed_publish(line, export_name):
                publishes = True
        if not publishes:
            continue
        publishers.append(rel)
        if not on_path:
            historical.append(rel)
            continue
        current.append(rel)
        if writes:
            offenders.append(rel)
            for row in writes:
                row["current"] = True
                detail.append(row)
    verdict = "BYPASS" if offenders else ("CLEAN" if current else "EMPTY")
    report = {
        "label": LABEL,
        "verdict": verdict,
        "root": root,
        "scanned": scanned,
        "publishers": sorted(publishers),
        "offenders": sorted(offenders),
        "clean": sorted(p for p in current if p not in offenders),
        "historical": sorted(historical),
        "detail": detail,
    }
    return report, (2 if offenders else 0)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0

    root = "."
    export_name = DEFAULT_EXPORT_NAME
    owner = DEFAULT_OWNER
    as_json = False
    saw_check = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            saw_check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--export", "--owner"):
            index += 1
            if index >= len(argv):
                sys.stderr.write("E_EPPG_BAD_FLAGS missing value for %s\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            elif arg == "--export":
                export_name = argv[index]
            else:
                owner = argv[index]
        else:
            sys.stderr.write("E_EPPG_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_EPPG_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root, export_name, owner)
    except ExportPublishPathGuardError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "EXPORT PUBLISH PATH %s verdict=%s scanned=%d publishers=%d "
            "current=%d offenders=%s historical=%d\n" % (
                report["label"], report["verdict"], report["scanned"],
                len(report["publishers"]), len(report["clean"]) +
                len(report["offenders"]),
                ",".join(report["offenders"]) or "(none)",
                len(report["historical"])))
        for row in report["detail"]:
            sys.stdout.write("  BYPASS %s:%d %s\n" % (
                row["path"], row["line"], row["text"]))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))