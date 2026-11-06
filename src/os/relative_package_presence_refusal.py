# relative_package_presence_refusal.py - a declared package the read tree
# does not carry is refused ONCE, by name, instead of being printed as N
# broken imports.
# Criteria AC-RMPP1..AC-RMPP6 were pre-registered in state/queue/tech.md
# (the R2440 seed row, tech head after R2491) BEFORE this file existed.
#
# Why this exists: relative_module_corpus_scope (R2491) measures the module
# corpus root-wide, but MEASURED at R2440 neither it nor the existence face
# asks whether the DECLARED package itself is carried by that tree. Hand
# --package nosuchpkg a tree that carries only mypkg and every relative
# import joins onto a package that does not exist, so each one reads
# MISSING-MODULE: a typo in the declaration is published as N broken
# imports rather than one refusal naming the declaration.
#
# This module adds ONE notion and no second classifier, no second join and
# no walk of its own: the corpus is relative_module_corpus_scope.tree_corpus
# - the R2440 measured walk - asked at CALL time, the join and the one
# publish classifier stay publish_relative_package_identity's own, and the
# reading itself is relative_module_corpus_scope.check asked at CALL time.
# The only new facts are the declared package's presence (ABSENT / MARKER /
# PRESENT with its carrier count) and the single refusal E_RMPP_NO_PACKAGE.
#
# AC-RMPP2: when the tree does carry the declared package the reading is
# today's reading byte for byte - every key the R2440 face publishes keeps
# its name and its value; the presence keys are additions.
#
# This module writes nothing and reads no clock (AC-RMPP6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: relative_package_presence_refusal.py --check [--root PATH]
#                                               [--package MODULE]
#                                               [--export NAME]
#                                               [--owner MODULE]
#                                               [--wire MODULE]
#                                               [--extra NAME ...] [--json]
#   exit 0 = the parent's own WIRE or EMPTY reading
#   exit 2 = E_RMPP_NO_PACKAGE, or the parent's own missing / refusal reading
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags or the declared names are bad

import importlib
import json
import os
import sys

LABEL = "os-relative-package-presence-refusal"
NO_PACKAGE = "NO-PACKAGE"
ABSENT = "ABSENT"
MARKER = "MARKER"
PRESENT = "PRESENT"
UNDECLARED = "UNDECLARED"
REFUSAL_CODE = "E_RMPP_NO_PACKAGE"

# The presence keys this face adds. Every parent key keeps its name.
PRESENCE_KEYS = ("declaration", "presence", "presence_carriers",
                 "presence_corpus")

USAGE = (
    "usage: relative_package_presence_refusal.py --check [--root PATH] "
    "[--package MODULE] [--export NAME] [--owner MODULE] [--wire MODULE] "
    "[--extra NAME ...] [--json]\n"
    "  --check         read every current publisher and place its publish\n"
    "  --root PATH     tree to read (default .)\n"
    "  --package MOD   the package the read scripts live in; when the tree\n"
    "                  carries no module at or under it the reading is\n"
    "                  refused once as E_RMPP_NO_PACKAGE\n"
    "  --export NAME   export document basename (default: the parent's)\n"
    "  --owner MODULE  module that owns the current export shape\n"
    "  --wire MODULE   module that proves the bytes before publishing\n"
    "  --extra NAME    a dotted module name the caller declares present\n"
    "                  (repeatable; passed through to the parent reading)\n"
    "  --json          emit one machine-readable object\n"
    "  exit 0 = WIRE or EMPTY, 2 = E_RMPP_NO_PACKAGE or the parent's own\n"
    "  reading, 3 = root missing, 5 = bad flags or bad names\n"
)


class RelativePackagePresenceRefusalError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parent():
    """The module that owns the corpus walk and the one publish classifier."""
    return importlib.import_module("relative_module_corpus_scope")


def carriers_of(corpus, package):
    """Every module at or under the declared package, sorted."""
    prefix = package + "."
    return sorted(name for name in corpus
                  if name == package or name.startswith(prefix))


def presence(corpus, package):
    """ABSENT / MARKER / PRESENT for the declared package (AC-RMPP1..3).

    A package carried only by its own marker - `pkg/__init__.py` and no
    other file - is PRESENT with the marker state, never ABSENT: the tree
    does declare the package even when it carries nothing else under it.
    """
    if package is None:
        return UNDECLARED, []
    carriers = carriers_of(corpus, package)
    if not carriers:
        return ABSENT, carriers
    if carriers == [package]:
        return MARKER, carriers
    return PRESENT, carriers


def check(root, package=None, export_name=None, owner=None, wire_module=None,
          extra=None):
    """The parent's reading, preceded by ONE presence decision on its corpus."""
    law = parent()
    if not os.path.isdir(root):
        raise RelativePackagePresenceRefusalError("E_RMPP_NO_ROOT", root)
    if package is not None:
        law.parent().check_package(package)
    corpus = law.tree_corpus(root)
    state, carriers = presence(corpus, package)
    if state == ABSENT:
        return {
            "label": LABEL,
            "verdict": NO_PACKAGE,
            "root": root,
            "package": package,
            "corpus": len(corpus),
            "missing": [],
            "missing_modules": [],
            "detail": [],
            "declaration": package,
            "presence": ABSENT,
            "presence_carriers": 0,
            "presence_corpus": len(corpus),
            "refusal": REFUSAL_CODE,
        }, 2
    # AC-RMPP4: the corpus was measured ONCE above by the parent's own walk,
    # so the parent reading is handed that same measurement for this root
    # instead of walking the tree a second time. The substitution is local to
    # this call, answers only the root already measured, and is restored in
    # the finally block whatever happens.
    original_walk = law.tree_corpus
    root_key = os.path.abspath(root)

    def measured_corpus(walked_root):
        if os.path.abspath(walked_root) == root_key:
            return set(corpus)
        return original_walk(walked_root)

    law.tree_corpus = measured_corpus
    try:
        out, code = law.check(root, package, export_name, owner, wire_module,
                              list(extra or []))
    finally:
        law.tree_corpus = original_walk
    out["declaration"] = package
    out["presence"] = state
    out["presence_carriers"] = len(carriers)
    out["presence_corpus"] = len(corpus)
    out["refusal"] = None
    return out, code


def screen(report):
    """The operator line: the declaration is named even when it was refused."""
    lines = [
        "label=%s" % report["label"],
        "verdict=%s" % report["verdict"],
        "root=%s" % report["root"],
        "declaration=%s" % ("(none)" if report["declaration"] is None
                            else report["declaration"]),
        "presence=%s" % report["presence"],
        "presence_carriers=%d" % report["presence_carriers"],
        "presence_corpus=%d" % report["presence_corpus"],
    ]
    if report.get("refusal"):
        lines.append("refusal=%s" % report["refusal"])
    for row in report.get("missing") or []:
        lines.append("missing_module=%s path=%s line=%s scope_root=%s "
                     "scope_corpus=%s"
                     % (row.get("module"), row.get("path"), row.get("line"),
                        row.get("scope_root"), row.get("scope_corpus")))
    return "\n".join(lines) + "\n"


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
                sys.stderr.write("E_RMPP_BAD_FLAGS missing value for %s\n" % arg)
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
            sys.stderr.write("E_RMPP_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_RMPP_BAD_FLAGS --check is required\n")
        return 5

    law = parent()
    try:
        report, code = check(root, package, export_name, owner, wire_module,
                             extras)
    except law.parent().CannotJoinError as exc:
        sys.stderr.write("%s\n" % exc)
        return 2
    except law.parent().PublishRelativePackageIdentityError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5 if exc.code in ("E_PRPI_BAD_PACKAGE",
                                 "E_PRPI_NOT_RELATIVE") else 3
    except law.RelativeModuleCorpusScopeError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5 if exc.code == "E_RMSC_BAD_EXTRA" else 3
    except RelativePackagePresenceRefusalError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, sort_keys=True) + "\n")
    else:
        sys.stdout.write(screen(report))
    return code


if __name__ == "__main__":
    sys.exit(main())