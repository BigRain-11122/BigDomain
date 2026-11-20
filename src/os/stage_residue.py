"""Stage residue: the names a killed or refused writer leaves beside a face.

WHY THIS FILE EXISTS (measured at R3119, not assumed):
`tmp/probe_R3119.py` -> `qa/probe-R3119.log` counted 690 directory-enumeration
call sites in shipped .py, of which ZERO point at `docs/` and three point at
`logs/` - `ledger_lines.archive_files()` (filtered by an archive prefix AND an
archive suffix) plus two arms of the R3118 suite. A `docs/*.json` glob sees only
the live face, and a private world holding four truncated residues beside a
judgeable face still read `face_judgeable -> None` and `assess -> FRESH`, so no
reader mistakes a residue for a face.

What a residue DOES do is dirty the tree: `git check-ignore` says
`docs/status-export.json.sxf-stage` is NOT ignored (the `logs/` twin is), and
the next round reads an untracked file as another executor mid-write and turns
into a read-only round. This module sweeps exactly the four measured suffixes,
never names the live face, and is idempotent by construction.

WHY THE SURFACE IS A WALK AND NOT A DIRECTORY LIST (measured at R3120, not
assumed): every writer stages at `<target> + suffix` and the target is a CLI
argument - `tmp/probe_R3120.py` -> `qa/probe-R3120.log` counted 33 shipped call
sites that name an explicit `--export`. A two-name whitelist therefore saw 8 of
16 residues planted across docs/logs/state/preview/tmp and missed the other 12
without a word. The suffixes are exact and pinned by AC-SR1 arm e, so a walk
cannot reach a face; only the repository's own bookkeeping (`.git`) is left
unwalked.

WHY THE WALK NAMES ITS OWN BLIND SPOTS (measured at R3121, not assumed):
`tmp/probe_R3121.py` -> `qa/probe-R3121.log` walked the live tree in 0.787s
(3482 directories, 57329 files; `src/` is 29.5% of that, `qa/` only 1.0%, so
the guess that qa/ dominated was wrong) with zero unlistable directories TODAY
- which is why the old silent `except: continue` was invisible rather than
harmless. The same probe drove the refusals on Windows: a residue held open by
another handle refuses with winerror=32, a read-only one with 5, and a removing
directory with 5, while errno is 13 for all three - so `skipped` (not a regular
file) and `failed` (the OS refused) are now separate readings, and a directory
that cannot be listed is named as `unreadable` instead of skipped in silence.

WHY THE SWEEP ACCEPTS A REPORT (measured at R3122, not assumed):
`tmp/probe_R3122.py` -> `qa/probe-R3122.log` walked the live tree in 910.9ms
and attributed the cost: `src/` 52.0%, `.codely-cli/` 17.2%, `logs/` 15.4%,
`tmp/` 7.3%, `qa/` 5.3%, `__pycache__` only 2.3% - so pruning generated
subtrees would save 20ms and is not done. What the same probe DID find is that
the closeout walked the tree twice per round (scan_report, then sweep which
scanned again), so `sweep` now takes the report its caller already paid for.
Timing stays with the caller: this module still reads no clock.

ASCII only, stdlib only, no network, no clock.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The four stage suffixes the tree actually writes today. The suite proves this
# tuple still covers every `.<word>-stage` literal in shipped .py (AC-SR1 arm e),
# so a fifth stage writer reddens the arm instead of slipping past the sweep.
SUFFIXES = (".sxf-stage", ".edqf-stage", ".gate-stage", ".parity-stage")

# The two directories the four writers reach by default: docs/ holds the live
# face, logs/ the archive. Kept as the measurement record (the suite asserts the
# walk still covers both); the sweep no longer narrows to them, because a named
# target can put the same residue anywhere.
DIRS = ("docs", "logs")

# The only subtree a sweep refuses to enter: git's own store, where a name that
# ends with a stage suffix is not residue beside a face.
SKIP_DIRS = (".git",)


def _rel(path, base):
    return os.path.relpath(path, base).replace("\\", "/")


def _listing(folder, base, unreadable):
    """Sorted names in `folder`, or None when the OS refuses to list it.

    The refusal is RECORDED, not swallowed (R3121): a walk that silently covers
    less than the tree would make "the whole tree is covered" an assumption.
    """
    try:
        return sorted(os.listdir(folder))
    except (IOError, OSError) as exc:
        unreadable.append("%s:%s" % (_rel(folder, base), type(exc).__name__))
        return None


def _walk(base, unreadable):
    """(folder, names) for every listable directory under `base`.

    Recursion is explicit listdir-by-listdir (not os.walk) so a directory the OS
    will not list is NAMED instead of vanishing; SKIP_DIRS and symlinked
    directories are not entered.
    """
    stack = [base]
    while stack:
        folder = stack.pop()
        names = _listing(folder, base, unreadable)
        if names is None:
            continue
        yield folder, names
        for name in names:
            path = os.path.join(folder, name)
            if name in SKIP_DIRS or os.path.islink(path) or not os.path.isdir(path):
                continue
            stack.append(path)


def scan_report(root=None, dirs=None):
    """What the surface really saw: found / folders / unreadable.

    A name qualifies only when it ENDS with one of SUFFIXES, so the live face
    and every other document are out of reach by construction. `dirs` names a
    narrower surface for callers that ask about one directory (not recursive);
    the default is the whole tree minus SKIP_DIRS.
    """
    base = os.path.abspath(root) if root else ROOT
    found = []
    unreadable = []
    if dirs is None:
        folders = _walk(base, unreadable)
    else:
        pairs = []
        for name in dirs:
            folder = os.path.join(base, name)
            if not os.path.isdir(folder):
                continue
            names = _listing(folder, base, unreadable)
            if names is not None:
                pairs.append((folder, names))
        folders = pairs
    count = 0
    for folder, names in folders:
        count += 1
        for entry in names:
            if entry.endswith(SUFFIXES):
                found.append(_rel(os.path.join(folder, entry), base))
    return {"found": sorted(found), "folders": count,
            "unreadable": sorted(unreadable)}


def scan(root=None, dirs=None):
    """Relative paths (forward slashes) of residue under `dirs`, sorted."""
    return scan_report(root, dirs)["found"]


def sweep(root=None, dirs=None, report=None):
    """Remove every scanned residue. Returns (removed, skipped, failed).

    `report` is a `scan_report()` result the caller already paid for (R3122):
    the closeout needs the counts AND the sweep in the same step, and passing
    the report makes that one walk instead of two. It is the AUTHORITY on what
    gets removed - a report that names nothing removes nothing, even when a
    residue sits on disk - because re-walking there would silently disagree
    with the counts the face is about to print. Callers must pass a report
    produced for the same `root`/`dirs`; the default recomputes it.

    `skipped` holds names that carry a suffix but are NOT regular files (a
    directory or a link is named instead of followed). `failed` holds names the
    OS refused to remove, each as `<rel>:winerror=<n>` (or `errno=<n>` off
    Windows) - measured at R3121: a residue held open by another handle refuses
    with winerror=32 while a read-only one refuses with 5, and folding both into
    `skipped` would read exactly like "not a file".
    """
    base = os.path.abspath(root) if root else ROOT
    if report is None:
        report = scan_report(base, dirs)
    removed = []
    skipped = []
    failed = []
    for rel in report["found"]:
        path = os.path.join(base, rel.replace("/", os.sep))
        if not os.path.isfile(path) or os.path.islink(path):
            skipped.append(rel)
            continue
        try:
            os.remove(path)
        except (IOError, OSError) as exc:
            code = getattr(exc, "winerror", None)
            failed.append("%s:%s" % (rel, "winerror=%d" % code if code
                                     else "errno=%r" % getattr(exc, "errno", None)))
            continue
        removed.append(rel)
    return removed, skipped, failed


def main(argv):
    args = list(argv[1:])
    unknown = [a for a in args if a not in ("--check", "--sweep")]
    if unknown:
        print("STAGE-RESIDUE FAIL E_SR_BAD_FLAGS %r" % (unknown,))
        return 3
    if "--sweep" in args:
        removed, skipped, failed = sweep()
        print("STAGE-SWEPT removed=%d skipped=%d failed=%d"
              % (len(removed), len(skipped), len(failed)))
        if skipped:
            print("STAGE-SWEPT-SKIPPED names=%s" % ",".join(skipped))
        if failed:
            print("STAGE-SWEPT-FAILED names=%s" % ",".join(failed))
        return 1 if failed else 0
    report = scan_report()
    found = report["found"]
    print("STAGE-RESIDUE count=%d names=%s"
          % (len(found), ",".join(found) if found else "none"))
    if report["unreadable"]:
        print("STAGE-RESIDUE-UNREADABLE count=%d dirs=%s"
              % (len(report["unreadable"]), ",".join(report["unreadable"])))
    if "--check" in args and found:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
