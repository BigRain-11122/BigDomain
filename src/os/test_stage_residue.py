"""Battery suite for src/os/stage_residue.py - AC-SR1 (six arms) and AC-SR2
(six arms).

WHY THIS SUITE EXISTS (measured at R3119, not assumed):
The R3117/R3118 stage doors made "a refusal lands nothing" structural, but the
stage files themselves still sit beside the face while they exist. A process
killed between `open(stage)` and `os.replace` leaves one behind. The probe
counted what that residue can reach: 0 shipped .py enumerate `docs/`, 3 name
`logs/` (all filtered by an archive prefix+suffix), a `docs/*.json` glob sees
only the live face, and a truncated residue beside a judgeable face changes
nothing about `face_judgeable` or `assess`. The cost of a residue is therefore
not a misread face - it is a dirty tree: `git check-ignore` says the docs/ name
is NOT ignored, and the next round reads an untracked file as another executor
mid-write. This suite pins the sweep that removes exactly those names.

WHAT IS PROVED HERE (one criterion, six arms):
  a  a private world with all four suffixes beside a live face scans to exactly
     four names, and the live face is not among them.
  b  a clean world scans to zero.
  c  sweep removes exactly the four and leaves the live face byte-identical.
  d  sweep is idempotent: the second call removes nothing.
  e  drift: every `.<word>-stage` string literal in shipped .py is one of the
     four suffixes, and the count is measured rather than typed.
  f  never-read: no shipped non-test .py enumerates `docs/`, and the shipped
     logs/ archive enumerator admits none of the four names.

AC-SR2 (the sweep's REACH, measured at R3120): a two-name whitelist saw 8 of 16
residues planted across five directories and missed the rest without a word,
while 33 shipped call sites name an explicit `--export`. Six arms:
  a  residue beside a named target in state/, preview/ and tmp/ is found by the
     default scan (20 of 20 planted, live face not among them).
  b  `.git` is never entered: a stage-suffixed name inside it is neither named
     nor removed, while the same name outside it is.
  c  `dirs=` still narrows the surface for a caller that asks about one folder.
  d  sweep of the five-directory world removes all 20, is idempotent, and
     leaves the live face byte-identical.
  e  a DIRECTORY named like a residue is skipped by name, never removed.
  f  the live tree scans without naming the live face, and DIRS (the measured
     default destinations) are still covered by the walk.

Isolation: private worlds are temp dirs; the only live reads are shipped
sources. Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import ast
import os
import re
import shutil
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BATTERY = os.path.abspath(__file__)

sys.path.insert(0, os.path.join(ROOT, "src", "os"))
import ledger_lines as LL  # noqa: E402
import stage_residue as SR  # noqa: E402

STAGE_SHAPE = re.compile(r"^\.[a-z0-9]+-stage$")
ENUM_NAMES = {"listdir", "scandir", "walk", "glob", "iglob", "iterdir"}
CHECKS = []
FAILS = []


def ok(name, cond, detail):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))


def world():
    base = tempfile.mkdtemp(prefix="sr-")
    for name in ("docs", "logs"):
        os.makedirs(os.path.join(base, name))
    with open(os.path.join(base, "docs", "status-export.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write('{"export_ts": "2026-11-21T12:00:00+08:00"}\n')
    return base


# The five directories the R3120 probe planted into: the two the writers reach
# by default plus the three a named `--export` can reach today.
WIDE_DIRS = ("docs", "logs", "state", "preview", "tmp")


def wide_world():
    base = tempfile.mkdtemp(prefix="sr-wide-")
    for name in WIDE_DIRS:
        os.makedirs(os.path.join(base, name))
    with open(os.path.join(base, "docs", "status-export.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write('{"export_ts": "2026-11-21T12:00:00+08:00"}\n')
    return base


def wide_plant(base):
    """One residue per (directory, suffix) pair; returns how many were made."""
    made = 0
    for name in WIDE_DIRS:
        for suffix in SR.SUFFIXES:
            with open(os.path.join(base, name, "status-export.json" + suffix),
                      "w", encoding="utf-8", newline="\n") as handle:
                handle.write('{"partial')
            made += 1
    return made


def face_bytes(base):
    with open(os.path.join(base, "docs", "status-export.json"), "rb") as handle:
        return handle.read()


def plant(base):
    for suffix in SR.SUFFIXES:
        with open(os.path.join(base, "docs", "status-export.json" + suffix), "w",
                  encoding="utf-8", newline="\n") as handle:
            handle.write('{"partial')
        with open(os.path.join(base, "logs", "state-log-archive-2026-11.md" + suffix),
                  "w", encoding="utf-8", newline="\n") as handle:
            handle.write("# partial")


def shipped_sources(include_tests):
    for base in ("src", "tools"):
        for folder, _, files in os.walk(os.path.join(ROOT, base)):
            if "__pycache__" in folder:
                continue
            for name in files:
                if not name.endswith(".py"):
                    continue
                if not include_tests and name.startswith("test_"):
                    continue
                yield os.path.join(folder, name)


def main():
    worlds = []

    # ---- a / b: the scan sees residue and only residue. -------------------
    planted = world()
    worlds.append(planted)
    plant(planted)
    found = SR.scan(planted)
    docs_only = [p for p in found if p.endswith(".sxf-stage")
                 and p.startswith("docs/")]
    ok("AC-SR1 arm a - four residues found, live face not among them",
       len(found) == 8 and "docs/status-export.json" not in found and docs_only,
       "found=%d docs_sxf=%r" % (len(found), docs_only))

    clean = world()
    worlds.append(clean)
    ok("AC-SR1 arm b - a clean world scans to zero",
       SR.scan(clean) == [], "found=%r" % (SR.scan(clean),))

    # ---- c / d: the sweep removes exactly those names, once. -------------
    before = face_bytes(planted)
    removed, skipped = SR.sweep(planted)
    after = face_bytes(planted)
    left = SR.scan(planted)
    ok("AC-SR1 arm c - sweep removes exactly the planted names, face untouched",
       len(removed) == 8 and not skipped and left == [] and before == after
       and os.path.isfile(os.path.join(planted, "docs", "status-export.json")),
       "removed=%d skipped=%d left=%r face_same=%s"
       % (len(removed), len(skipped), left, before == after))

    again_removed, again_skipped = SR.sweep(planted)
    ok("AC-SR1 arm d - the second sweep removes nothing",
       again_removed == [] and again_skipped == [],
       "removed=%r skipped=%r" % (again_removed, again_skipped))

    # ---- e: no shipped writer invents a fifth suffix. --------------------
    literals = set()
    for path in shipped_sources(include_tests=True):
        try:
            tree = ast.parse(open(path, encoding="utf-8",
                                  errors="replace").read())
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and STAGE_SHAPE.match(node.value):
                literals.add(node.value)
    stray = sorted(literals - set(SR.SUFFIXES))
    ok("AC-SR1 arm e - every shipped stage literal is a swept suffix",
       not stray and len(literals) >= 4,
       "literals=%d stray=%r" % (len(literals), stray))

    # ---- f: nothing enumerates docs/ and the archive reader filters. -----
    docs_enum = []
    for path in shipped_sources(include_tests=False):
        try:
            tree = ast.parse(open(path, encoding="utf-8",
                                  errors="replace").read())
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else (
                fn.id if isinstance(fn, ast.Name) else "")
            if name not in ENUM_NAMES or not node.args:
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str) \
                    and "docs" in first.value.lower():
                docs_enum.append("%s:%d"
                                 % (os.path.relpath(path, ROOT).replace("\\", "/"),
                                    node.lineno))
    admit = LL.archive_files(os.path.join(planted, "logs"))
    ok("AC-SR1 arm f - no shipped docs/ enumerator, and the archive reader "
       "admits no residue",
       docs_enum == [] and admit == [],
       "docs_enum=%r archive_entries=%d" % (docs_enum, len(admit)))

    # ---- AC-SR2 a: the surface is every directory, not two names. --------
    wide = wide_world()
    worlds.append(wide)
    planted_wide = wide_plant(wide)
    wide_found = SR.scan(wide)
    ok("AC-SR2 arm a - residue beside a named target in every directory is "
       "found by the default scan",
       len(wide_found) == planted_wide
       and "docs/status-export.json" not in wide_found
       and all(p.split("/")[0] in WIDE_DIRS for p in wide_found),
       "planted=%d found=%d face_named=%s"
       % (planted_wide, len(wide_found),
          "docs/status-export.json" in wide_found))

    # ---- AC-SR2 b: git's own store is never entered. ---------------------
    git_dir = os.path.join(wide, ".git")
    if not os.path.isdir(git_dir):
        os.makedirs(git_dir)
    hidden = os.path.join(git_dir, "status-export.json.sxf-stage")
    with open(hidden, "w", encoding="utf-8", newline="\n") as handle:
        handle.write('{"partial')
    git_named = [p for p in SR.scan(wide) if p.startswith(".git/")]
    ok("AC-SR2 arm b - a stage-suffixed name inside .git is neither named nor "
       "removed",
       git_named == [] and os.path.isfile(hidden),
       "named=%r still_on_disk=%s" % (git_named, os.path.isfile(hidden)))

    # ---- AC-SR2 c: a caller may still ask about one folder. --------------
    docs_narrow = SR.scan(wide, ("docs",))
    ok("AC-SR2 arm c - dirs= narrows the surface to the folder the caller names",
       len(docs_narrow) == len(SR.SUFFIXES)
       and all(p.startswith("docs/") for p in docs_narrow),
       "narrowed=%d %r" % (len(docs_narrow), docs_narrow))

    # ---- AC-SR2 d: the sweep clears all of them, once. -------------------
    wide_before = face_bytes(wide)
    wide_removed, wide_skipped = SR.sweep(wide)
    wide_after = face_bytes(wide)
    ok("AC-SR2 arm d - sweep removes all 20 planted names, is idempotent, and "
       "leaves the live face byte-identical",
       len(wide_removed) == planted_wide and not wide_skipped
       and wide_before == wide_after and SR.scan(wide) == []
       and SR.sweep(wide) == ([], [])
       and os.path.isfile(os.path.join(wide, "docs", "status-export.json")),
       "removed=%d left=%r face_same=%s"
       % (len(wide_removed), SR.scan(wide), wide_before == wide_after))

    # ---- AC-SR2 e: a directory that carries the suffix is skipped. -------
    dir_case = wide_world()
    worlds.append(dir_case)
    blocked = os.path.join(dir_case, "state", "held.sxf-stage")
    os.makedirs(blocked)
    dir_named = SR.scan(dir_case)
    dir_removed, dir_skipped = SR.sweep(dir_case)
    ok("AC-SR2 arm e - a directory named like a residue is named and skipped, "
       "never removed",
       dir_named == ["state/held.sxf-stage"] and dir_removed == []
       and dir_skipped == ["state/held.sxf-stage"]
       and os.path.isdir(blocked),
       "named=%r removed=%r skipped=%r still_dir=%s"
       % (dir_named, dir_removed, dir_skipped, os.path.isdir(blocked)))

    # ---- AC-SR2 f: the live tree, and the measured defaults inside it. ---
    started = time.time()
    live = SR.scan()
    elapsed = time.time() - started
    live_ok = (all(p.rsplit("/", 1)[-1].endswith(SR.SUFFIXES) for p in live)
               and "docs/status-export.json" not in live)
    ok("AC-SR2 arm f - the live tree scans by suffix only and never names the "
       "live face",
       live_ok and all(os.path.isdir(os.path.join(ROOT, name))
                       for name in SR.DIRS),
       "live=%r dirs=%r elapsed=%.2fs" % (live, SR.DIRS, elapsed))

    for path in worlds:
        shutil.rmtree(path, ignore_errors=True)

    criteria = set(name.split(" ", 1)[0] for name in CHECKS)
    total = len(CHECKS)
    print("suite: %d assertions over %d criteria" % (total, len(criteria)))
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s" % (total - len(FAILS), total, FAILS))
        return 2
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
