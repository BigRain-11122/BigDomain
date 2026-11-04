# relative_module_existence_face.py - a joined relative module is checked
# against the modules the read tree actually carries.
# Criteria AC-RMEF1..AC-RMEF6 were pre-registered in state/queue/tech.md:504
# (the R2415 seed row) BEFORE this file existed.
#
# Why this exists: publish_relative_package_identity (R2415) joins a relative
# module text onto a caller-DECLARED package, so `from .nosuchmodule import
# publish` with --package mypkg joins to `mypkg.nosuchmodule` and reads FOREIGN
# at exit 2 even though no such module exists in the tree - measured at R2415
# on a fixture. A typo and a genuinely foreign wire read identically, so the
# reading cannot tell a broken import from a foreign one.
#
# This module adds ONE notion and no second classifier and no second join: the
# reading is publish_relative_package_identity's own audit, asked at CALL time,
# and the join is that module's own join_package. The only new fact is the
# MODULE CORPUS - the dotted names measured off the read tree's own .py files -
# and the only new word is MISSING-MODULE, printed when a joined module has no
# file behind it.
#
# With NO package declared every reading is the parent's own byte for byte and
# no corpus is measured at all (AC-RMEF4), so the parent's RELATIVE reading is
# untouched.
#
# This module writes nothing and reads no clock (AC-RMEF6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: relative_module_existence_face.py --check [--root PATH]
#                                           [--package MODULE]
#                                           [--export NAME] [--owner MODULE]
#                                           [--wire MODULE] [--json]
#   exit 0 = the parent's own WIRE or EMPTY reading
#   exit 2 = MISSING-MODULE, or the parent's own FOREIGN / UNRESOLVED /
#            RELATIVE / REFUSED reading
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags or the declared package are bad

import importlib
import json
import os
import sys

LABEL = "os-relative-module-existence-face"
MISSING_MODULE = "MISSING-MODULE"
NO_CORPUS = "(none)"

REPORT_KEYS = ("label", "verdict", "root", "package", "corpus", "scanned",
               "publishers", "wire", "foreign", "unresolved", "relative",
               "no_publish", "from_import", "bare", "refused",
               "missing", "missing_modules", "detail")

MISSING_KEYS = ("path", "line", "module", "package")

USAGE = (
    "usage: relative_module_existence_face.py --check [--root PATH] "
    "[--package MODULE] [--export NAME] [--owner MODULE] [--wire MODULE] "
    "[--json]\n"
    "  --check         read every current publisher and place its publish\n"
    "  --root PATH     tree to read (default .)\n"
    "  --package MOD   the package the read scripts live in (default: none,\n"
    "                  which keeps the parent law's own reading)\n"
    "  --export NAME   export document basename (default: the parent's)\n"
    "  --owner MODULE  module that owns the current export shape\n"
    "                  (default: the parent's)\n"
    "  --wire MODULE   module that proves the bytes before publishing\n"
    "                  (default: the parent's)\n"
    "  --json          emit one machine-readable object\n"
    "  exit 0 = WIRE or EMPTY, 2 = MISSING-MODULE or the parent's own\n"
    "  reading, 3 = root missing, 5 = bad flags or bad package\n"
)


class RelativeModuleExistenceError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parent():
    """The module that owns the join and the one publish classifier."""
    return importlib.import_module("publish_relative_package_identity")


def corpus(root):
    """Every dotted module name the read tree carries, measured not assumed.

    A file `pkg/sub/mod.py` contributes `pkg.sub.mod`; a package marker
    `pkg/sub/__init__.py` contributes `pkg.sub`. Nothing is hard-coded, so a
    module added to or removed from the tree moves the reading (AC-RMEF1).
    """
    modules = set()
    for base, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(base, name), root)
            parts = rel.replace(os.sep, "/")[:-3].split("/")
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]
            if parts and all(part.isidentifier() for part in parts):
                modules.add(".".join(parts))
    return modules


def check(root, package=None, export_name=None, owner=None, wire_module=None):
    """The parent's own audit, plus one existence reading per joined module."""
    law = parent()
    if not os.path.isdir(root):
        raise RelativeModuleExistenceError("E_RMEF_NO_ROOT", root)
    if package is not None:
        law.check_package(package)
        modules = corpus(root)
    else:
        modules = None
    if export_name is None:
        export_name = law.DEFAULT_EXPORT_NAME
    if owner is None:
        owner = law.DEFAULT_OWNER
    if wire_module is None:
        wire_module = law.DEFAULT_WIRE
    report, code = law.audit(root, package, export_name, owner, wire_module)
    corpus_size = NO_CORPUS if modules is None else len(modules)
    missing = []
    if modules is not None:
        for row in report["detail"]:
            if not row.get("relative"):
                continue
            if row.get("state") == law.REFUSED:
                continue
            module = row.get("module") or ""
            if module and module not in modules:
                missing.append({"path": row["path"], "line": row["line"],
                                "module": module, "package": package})
    out = {
        "label": LABEL,
        "verdict": report["verdict"],
        "root": report["root"],
        "package": report["package"],
        "corpus": corpus_size,
        "scanned": report["scanned"],
        "publishers": report["publishers"],
        "wire": report["wire"],
        "foreign": report["foreign"],
        "unresolved": report["unresolved"],
        "relative": report["relative"],
        "no_publish": report["no_publish"],
        "from_import": report["from_import"],
        "bare": report["bare"],
        "refused": report["refused"],
        "missing": missing,
        "missing_modules": sorted(set(item["module"] for item in missing)),
        "detail": report["detail"],
    }
    if missing:
        out["verdict"] = MISSING_MODULE
        code = 2
    return out, code


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0

    root = "."
    package = None
    export_name = None
    owner = None
    wire_module = None
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
                sys.stderr.write("E_RMEF_BAD_FLAGS missing value for %s\n" % arg)
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
            sys.stderr.write("E_RMEF_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_RMEF_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = check(root, package, export_name, owner, wire_module)
    except parent().CannotJoinError as exc:
        sys.stderr.write("%s\n" % exc)
        return 2
    except parent().PublishRelativePackageIdentityError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5 if exc.code in ("E_PRPI_BAD_PACKAGE",
                                 "E_PRPI_NOT_RELATIVE") else 3
    except RelativeModuleExistenceError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "RELATIVE MODULE EXISTENCE %s verdict=%s package=%s corpus=%s "
            "scanned=%d publishers=%d wire=%d foreign=%s unresolved=%s "
            "relative=%d no_publish=%d from_import=%d bare=%d refused=%d "
            "missing=%d\n" % (
                report["label"], report["verdict"], report["package"],
                report["corpus"], report["scanned"],
                len(report["publishers"]), len(report["wire"]),
                ",".join(report["foreign"]) or "(none)",
                ",".join(report["unresolved"]) or "(none)",
                report["relative"], len(report["no_publish"]),
                report["from_import"], report["bare"],
                len(report["refused"]), len(report["missing"])))
        for item in report["missing"]:
            sys.stdout.write(
                "  MISSING-MODULE %s:%d module=%s package=%s\n" % (
                    item["path"], item["line"], item["module"],
                    item["package"]))
        wire_word = parent().identity().WIRE
        for row in report["detail"]:
            if row.get("relative") or row["state"] == wire_word:
                continue
            sys.stdout.write("  %s %s:%d kind=%s module=%s\n" % (
                row["state"], row["path"], row["line"], row["kind"],
                row["module"] or "(unbound)"))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))