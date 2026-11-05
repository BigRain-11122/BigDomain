# relative_module_corpus_scope.py - a MISSING-MODULE row now carries the
# search scope it was judged against, and a caller may widen that scope.
# Criteria AC-RMSC1..AC-RMSC6 were pre-registered in state/queue/tech.md:525
# (the R2440 seed row) BEFORE this file existed.
#
# Why this exists: relative_module_existence_face (R2440) measures its module
# corpus by walking the ROOT it is handed, so a join whose module is importable
# but lives OUTSIDE that root - an installed package, or a script read from a
# subdirectory while the package sits at the repository top - reads
# MISSING-MODULE exactly like a broken import. A scope limit and a typo looked
# identical, which is the defect this window measured.
#
# This module adds ONE notion and no second classifier and no second join: the
# reading is publish_relative_package_identity's own audit asked at CALL time
# (the same seam the R2440 face asks), the corpus is measured ONCE here, and
# the only new facts are (a) the scope a MISSING-MODULE row was judged against
# - the root as given plus the corpus size - and (b) caller-declared extra
# module names merged on top of the measured tree, which never REPLACE it.
#
# Every key the R2440 face publishes keeps its name and its meaning, so this
# reading is a strict extension of that contract (AC-RMSC5).
#
# This module writes nothing and reads no clock (AC-RMSC6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: relative_module_corpus_scope.py --check [--root PATH]
#                                           [--package MODULE]
#                                           [--export NAME] [--owner MODULE]
#                                           [--wire MODULE] [--extra NAME ...]
#                                           [--json]
#   exit 0 = the parent's own WIRE or EMPTY reading
#   exit 2 = MISSING-MODULE, or the parent's own FOREIGN / UNRESOLVED /
#            RELATIVE / REFUSED reading
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags, the declared package or a declared extra name are bad

import importlib
import json
import os
import sys

LABEL = "os-relative-module-corpus-scope"
MISSING_MODULE = "MISSING-MODULE"
NO_CORPUS = "(none)"
SCOPE_TREE = "TREE"
SCOPE_TREE_EXTRA = "TREE+EXTRA"
SCOPE_NONE = "NONE"

# The R2440 face's own published keys, kept first and unchanged in meaning.
REPORT_KEYS = ("label", "verdict", "root", "package", "corpus", "scanned",
               "publishers", "wire", "foreign", "unresolved", "relative",
               "no_publish", "from_import", "bare", "refused",
               "missing", "missing_modules", "detail",
               "scope", "scope_root", "scope_corpus", "extra")

# Every MISSING-MODULE row additionally carries the scope it was judged in.
MISSING_KEYS = ("path", "line", "module", "package",
                "scope_root", "scope_corpus")

USAGE = (
    "usage: relative_module_corpus_scope.py --check [--root PATH] "
    "[--package MODULE] [--export NAME] [--owner MODULE] [--wire MODULE] "
    "[--extra NAME ...] [--json]\n"
    "  --check         read every current publisher and place its publish\n"
    "  --root PATH     tree to read (default .)\n"
    "  --package MOD   the package the read scripts live in (default: none,\n"
    "                  which keeps the parent law's own reading)\n"
    "  --export NAME   export document basename (default: the parent's)\n"
    "  --owner MODULE  module that owns the current export shape\n"
    "  --wire MODULE   module that proves the bytes before publishing\n"
    "  --extra NAME    a dotted module name the caller declares present\n"
    "                  (repeatable; merged on top of the measured tree)\n"
    "  --json          emit one machine-readable object\n"
    "  exit 0 = WIRE or EMPTY, 2 = MISSING-MODULE or the parent's own\n"
    "  reading, 3 = root missing, 5 = bad flags or bad names\n"
)


class RelativeModuleCorpusScopeError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parent():
    """The module that owns the join and the one publish classifier."""
    return importlib.import_module("publish_relative_package_identity")


def valid_name(name):
    """A dotted name is declared only if every part is an identifier."""
    parts = (name or "").split(".")
    return bool(parts) and all(part.isidentifier() for part in parts)


def tree_corpus(root):
    """Every dotted module name the read tree carries - ONE walk, measured.

    A file `pkg/sub/mod.py` contributes `pkg.sub.mod`; a package marker
    `pkg/sub/__init__.py` contributes `pkg.sub`. The walk is root-wide on
    purpose, so a module carried under ANY top-level package of the tree is
    present and a package-scoped guess cannot hide it (AC-RMSC2).
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


def check(root, package=None, export_name=None, owner=None, wire_module=None,
          extra=None):
    """The parent's own audit, plus the scope each absence was judged in."""
    law = parent()
    if not os.path.isdir(root):
        raise RelativeModuleCorpusScopeError("E_RMSC_NO_ROOT", root)
    extras = []
    for name in (extra or []):
        if not valid_name(name):
            raise RelativeModuleCorpusScopeError("E_RMSC_BAD_EXTRA", str(name))
        if name not in extras:
            extras.append(name)
    if package is not None:
        law.check_package(package)
        modules = tree_corpus(root)
    else:
        modules = None
    merged = set(modules or ()) | set(extras) if modules is not None else None
    if export_name is None:
        export_name = law.DEFAULT_EXPORT_NAME
    if owner is None:
        owner = law.DEFAULT_OWNER
    if wire_module is None:
        wire_module = law.DEFAULT_WIRE
    report, code = law.audit(root, package, export_name, owner, wire_module)
    corpus_size = NO_CORPUS if merged is None else len(merged)
    if merged is None:
        scope = SCOPE_NONE
    elif extras:
        scope = SCOPE_TREE_EXTRA
    else:
        scope = SCOPE_TREE
    missing = []
    if merged is not None:
        for row in report["detail"]:
            if not row.get("relative"):
                continue
            if row.get("state") == law.REFUSED:
                continue
            module = row.get("module") or ""
            if module and module not in merged:
                missing.append({"path": row["path"], "line": row["line"],
                                "module": module, "package": package,
                                "scope_root": root,
                                "scope_corpus": corpus_size})
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
        "scope": scope,
        "scope_root": root,
        "scope_corpus": corpus_size,
        "extra": extras,
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
    extras = []
    as_json = False
    saw_check = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            saw_check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--package", "--export", "--owner", "--wire",
                     "--extra"):
            index += 1
            if index >= len(argv):
                sys.stderr.write("E_RMSC_BAD_FLAGS missing value for %s\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            elif arg == "--package":
                package = argv[index]
            elif arg == "--export":
                export_name = argv[index]
            elif arg == "--owner":
                owner = argv[index]
            elif arg == "--wire":
                wire_module = argv[index]
            else:
                extras.append(argv[index])
        else:
            sys.stderr.write("E_RMSC_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_RMSC_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = check(root, package, export_name, owner, wire_module,
                             extras)
    except parent().CannotJoinError as exc:
        sys.stderr.write("%s\n" % exc)
        return 2
    except parent().PublishRelativePackageIdentityError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5 if exc.code in ("E_PRPI_BAD_PACKAGE",
                                 "E_PRPI_NOT_RELATIVE") else 3
    except RelativeModuleCorpusScopeError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5 if exc.code == "E_RMSC_BAD_EXTRA" else 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "RELATIVE MODULE CORPUS SCOPE %s verdict=%s package=%s corpus=%s "
            "scope=%s scope_root=%s scanned=%d publishers=%d wire=%d "
            "foreign=%s unresolved=%s relative=%d no_publish=%d "
            "from_import=%d bare=%d refused=%d missing=%d extra=%s\n" % (
                report["label"], report["verdict"], report["package"],
                report["corpus"], report["scope"], report["scope_root"],
                report["scanned"], len(report["publishers"]),
                len(report["wire"]),
                ",".join(report["foreign"]) or "(none)",
                ",".join(report["unresolved"]) or "(none)",
                report["relative"], len(report["no_publish"]),
                report["from_import"], report["bare"],
                len(report["refused"]), len(report["missing"]),
                ",".join(report["extra"]) or "(none)"))
        for item in report["missing"]:
            sys.stdout.write(
                "  MISSING-MODULE %s:%d module=%s package=%s "
                "scope_root=%s scope_corpus=%s\n" % (
                    item["path"], item["line"], item["module"],
                    item["package"], item["scope_root"],
                    item["scope_corpus"]))
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