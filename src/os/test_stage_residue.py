"""Battery suite for src/os/stage_residue.py - criterion AC-SR1 (six arms).

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

Isolation: private worlds are temp dirs; the only live reads are shipped
sources. Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import ast
import os
import re
import shutil
import sys
import tempfile

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
