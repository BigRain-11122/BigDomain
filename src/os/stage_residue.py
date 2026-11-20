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

ASCII only, stdlib only, no network, no clock.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The four stage suffixes the tree actually writes today. The suite proves this
# tuple still covers every `.<word>-stage` literal in shipped .py (AC-SR1 arm e),
# so a fifth stage writer reddens the arm instead of slipping past the sweep.
SUFFIXES = (".sxf-stage", ".edqf-stage", ".gate-stage", ".parity-stage")

# Only the two directories the four writers use. Named rather than walked: a
# sweep that ranges over the whole tree deletes things it was never asked about.
DIRS = ("docs", "logs")


def scan(root=None, dirs=None):
    """Relative paths (forward slashes) of residue under `dirs`, sorted.

    A name qualifies only when it ENDS with one of SUFFIXES, so the live face
    and every other document are out of reach by construction.
    """
    base = os.path.abspath(root) if root else ROOT
    found = []
    for name in (DIRS if dirs is None else dirs):
        folder = os.path.join(base, name)
        if not os.path.isdir(folder):
            continue
        try:
            names = sorted(os.listdir(folder))
        except (IOError, OSError):
            continue
        for entry in names:
            if entry.endswith(SUFFIXES):
                found.append(os.path.relpath(os.path.join(folder, entry), base)
                             .replace("\\", "/"))
    return sorted(found)


def sweep(root=None, dirs=None):
    """Remove every scanned residue. Returns (removed, skipped) relative paths.

    `skipped` holds names that carry a suffix but are not regular files (a
    directory or a link is named instead of followed, so a refusal can never
    delete something the sweep did not measure).
    """
    base = os.path.abspath(root) if root else ROOT
    removed = []
    skipped = []
    for rel in scan(base, dirs):
        path = os.path.join(base, rel.replace("/", os.sep))
        if not os.path.isfile(path) or os.path.islink(path):
            skipped.append(rel)
            continue
        try:
            os.remove(path)
        except (IOError, OSError):
            skipped.append(rel)
            continue
        removed.append(rel)
    return removed, skipped


def main(argv):
    args = list(argv[1:])
    unknown = [a for a in args if a not in ("--check", "--sweep")]
    if unknown:
        print("STAGE-RESIDUE FAIL E_SR_BAD_FLAGS %r" % (unknown,))
        return 3
    if "--sweep" in args:
        removed, skipped = sweep()
        print("STAGE-SWEPT removed=%d skipped=%d names=%s"
              % (len(removed), len(skipped),
                 ",".join(removed) if removed else "none"))
        if skipped:
            print("STAGE-SWEPT-SKIPPED names=%s" % ",".join(skipped))
        return 0
    found = scan()
    print("STAGE-RESIDUE count=%d names=%s"
          % (len(found), ",".join(found) if found else "none"))
    if "--check" in args and found:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
