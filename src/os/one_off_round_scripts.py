# one_off_round_scripts.py - refuse per-round one-off scripts at their birth
# site. Criteria AC-OOS1..AC-OOS6 were pinned in src/os/backlog.md (the R2838
# row) and committed BEFORE this file existed.
#
# Why this exists: R2837 retired 682 files across the export_R*.py and
# closeout_R*.py families, and 226 state_append_R*.py before that. The
# retirement was correct and the survivors were measured, but deleting a
# family does not stop it from growing again - nothing in this repository
# refused the NEXT one-off at the moment it was written. R2837 disclosed
# exactly that (its disclosure (b): "the two families will regrow unless a
# future window refuses new per-round export_/closeout_ scripts at their
# birth site - that refusal is carried, not shipped").
#
# This module turns that carry into a reading, and it deliberately uses a law
# that needs no maintenance: a one-off is any file whose name carries a round
# id (`_R<digits>[a-z]?.py`), and the law is a FREEZE ROUND - every such file
# whose round is at or above the freeze round is refused. Measured at R2838:
# 904 one-offs on disk, the largest round id 2781, zero at or above 2838, so
# the real tree reads OK while the next `foo_R2839.py` cannot be committed
# without this reading turning red.
#
# The alternative - a hand-maintained allowlist of 904 names - was rejected
# because it would have to be edited by the same person who is adding the
# one-off, which is not a refusal. The freeze round is a constant: it only
# ever gets stricter as rounds advance, and it never needs a new entry.
#
# Honest limits, stated rather than hidden:
#   - this is a NAME-SHAPE law, not an intent detector. An author who writes a
#     one-off without a round id in its name is not caught here (the 682
#     retired files and the 904 on disk all carried one, so the shape is the
#     observed regrowth pattern, not a guess);
#   - the default scope is src/os, the directory every retired family lived in;
#     a one-off placed elsewhere is out of scope unless --scope says otherwise;
#   - a round id below the freeze is treated as historical and is never called
#     an offender, including the live root export_R2431.py.
#
# This module writes nothing and reads no clock (AC-OOS1). Source is pure
# ASCII, stdlib only, zero network.
#
# CLI: one_off_round_scripts.py --check [--root PATH] [--scope REL]
#                                  [--freeze N] [--json]
#   exit 0 = OK (one-offs exist, none at or above the freeze) or NONE
#   exit 2 = REFUSE, naming every one-off at or above the freeze round
#   exit 3 = the root or scope is missing
#   exit 5 = the flags are bad

import io
import json
import os
import re
import sys

LABEL = "os-one-off-round-scripts"
FREEZE_ROUND = 2838
DEFAULT_SCOPE = os.path.join("src", "os")
SKIP_DIRS = (".git", "media", "logs", "__pycache__", ".codely-cli")

# A per-round one-off: a round id directly followed by an extension. The
# optional trailing letter covers the observed `fold_R2583b.py` dialect.
ONE_OFF_RE = re.compile(r"_R(\d+)[a-z]?\.py$", re.IGNORECASE)

USAGE = (
    "usage: one_off_round_scripts.py --check [--root PATH] [--scope REL]\n"
    "                                  [--freeze N] [--json]\n"
    "  --check      read the scope and name every per-round one-off\n"
    "  --root PATH  tree to read (default .)\n"
    "  --scope REL  directory inside the root to read (default src/os)\n"
    "  --freeze N   round id at or above which a one-off is refused\n"
    "               (default 2838)\n"
    "  --json       emit one machine-readable object\n"
    "  exit 0 = OK or NONE, 2 = REFUSE (offenders named), 3 = missing path,\n"
    "  5 = bad flags\n"
)


class OneOffRoundScriptsError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def round_of(name):
    """The round id a one-off's name carries, or None when it is not one."""
    match = ONE_OFF_RE.search(name)
    if not match:
        return None
    return int(match.group(1))


def walk_python(root, scope):
    """Every .py under root/scope, junk directories skipped."""
    found = []
    for base, dirs, files in os.walk(scope):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith(".py"):
                continue
            found.append(os.path.join(base, name))
    found.sort()
    return found


def audit(root=".", scope_rel=DEFAULT_SCOPE, freeze=FREEZE_ROUND):
    """Read the scope and report which one-off round ids are at the freeze."""
    if not os.path.isdir(root):
        raise OneOffRoundScriptsError("E_OOS_NO_ROOT", root)
    scope = os.path.join(root, scope_rel)
    if not os.path.isdir(scope):
        raise OneOffRoundScriptsError("E_OOS_NO_SCOPE", scope_rel)

    scanned = 0
    one_offs = []
    max_round = 0
    refused = []
    detail = []
    for path in walk_python(root, scope):
        scanned += 1
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        number = round_of(os.path.basename(path))
        if number is None:
            continue
        one_offs.append(rel)
        if number > max_round:
            max_round = number
        if number >= freeze:
            refused.append(rel)
            detail.append({"path": rel, "round": number, "freeze": freeze})
    one_offs.sort()
    refused.sort()

    if refused:
        verdict, code = "REFUSE", 2
    elif one_offs:
        verdict, code = "OK", 0
    else:
        # "nothing to check" is not "everything is clean" (AC-OOS5).
        verdict, code = "NONE", 0

    report = {
        "label": LABEL,
        "verdict": verdict,
        "root": root,
        "scope": scope_rel.replace(os.sep, "/"),
        "freeze": freeze,
        "scanned": scanned,
        "one_offs": len(one_offs),
        "max_round": max_round,
        "refused": refused,
        "detail": detail,
    }
    return report, code


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0

    root = "."
    scope_rel = DEFAULT_SCOPE
    freeze = FREEZE_ROUND
    as_json = False
    saw_check = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            saw_check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--scope", "--freeze"):
            index += 1
            if index >= len(argv):
                sys.stderr.write("E_OOS_BAD_FLAGS missing value for %s\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            elif arg == "--scope":
                scope_rel = argv[index]
            else:
                try:
                    freeze = int(argv[index])
                except ValueError:
                    sys.stderr.write("E_OOS_BAD_FLAGS --freeze must be an integer\n")
                    return 5
        else:
            sys.stderr.write("E_OOS_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_OOS_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root, scope_rel, freeze)
    except OneOffRoundScriptsError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "ONE-OFF ROUND SCRIPTS %s verdict=%s scanned=%d one_offs=%d "
            "max_round=%d freeze=%d refused=%d\n" % (
                report["label"], report["verdict"], report["scanned"],
                report["one_offs"], report["max_round"], report["freeze"],
                len(report["refused"])))
        for row in report["detail"]:
            sys.stdout.write("  REFUSE %s round=%d freeze=%d\n" % (
                row["path"], row["round"], row["freeze"]))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
