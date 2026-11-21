"""Names every git-tracked Python file whose first bytes are a UTF-8 BOM.

Why this exists (measured at R3170, probe in qa/probe-R3170.log):

    A UTF-8 BOM is invisible to the plain reader every source-scanning gate in
    this repo uses. `open(path, encoding="utf-8")` keeps the U+FEFF as the first
    character of the text, and `ast.parse` then refuses the WHOLE file with
    "invalid non-printable character U+FEFF". All 80 BOM-carrying .py files
    measured at R3170 read exactly that way (plain_utf8_blind=80 of 80) while
    `utf-8-sig` parsed every one of them. So a BOM does not change a program's
    meaning - it changes whether a gate can SEE the program.

    The defect bit twice before this face existed: R3164 wrote a BOM through
    `Set-Content -Encoding UTF8` and made src/sandbox/reconcile_all.py
    unparseable (E_RTH_NO_REGISTRY U+FEFF), and registry_counter_census.py had
    to learn utf-8-sig because four of its registry rows were blind for the same
    reason. A scanner that silently loses a file is worse than one that refuses
    it, so the byte that causes the blindness is now named at birth.

The law, narrow on purpose:

    * the universe is `git ls-files` for `*.py` - untracked scratch under logs/
      and .codely-cli/ is not part of the shipped tree and is not judged;
    * an offender is a file whose FIRST THREE BYTES are EF BB BF;
    * a UTF-16/UTF-32 BOM (FF FE / FE FF ...) is a different defect and is not
      this face's business, and a BOM anywhere past byte 0 is a data-file
      question, also not this face's business;
    * nothing is ever written - the scan reads bytes and returns a reading.

Read-only, ASCII source, stdlib only, zero network.

Criteria AC-SBS1..AC-SBS6 are pre-registered in src/os/backlog.md as the R3170
PIN row BEFORE the code existed.
"""

import io
import json
import os
import subprocess
import sys

BOM = b"\xef\xbb\xbf"

REPORT_KEYS = ("verdict", "tracked_python", "offenders", "unreadable")
VERDICT_CLEAN = "SOURCE-BOM-CLEAN"
VERDICT_FOUND = "SOURCE-BOM-FOUND"
EXIT_CLEAN = 0
EXIT_FOUND = 2
EXIT_ENV = 3


def tracked_python(root):
    """Tracked *.py paths, repo-relative, POSIX separators, sorted.

    Returns (paths, error). `error` is a short string when the universe could
    not be read, in which case the caller must not read "clean" out of an empty
    list - an unreadable universe is an environment failure, not a pass.
    """
    try:
        out = subprocess.run(
            ["git", "-C", root, "ls-files", "-z", "--", "*.py"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError as exc:
        return [], "git-unavailable:%s" % exc.__class__.__name__
    if out.returncode != 0:
        msg = out.stderr.decode("utf-8", "replace").strip().splitlines()
        return [], "git-failed:%s" % (msg[0] if msg else "rc=%d" % out.returncode)
    raw = out.stdout.decode("utf-8", "replace")
    paths = sorted(p for p in raw.split("\0") if p)
    return paths, None


def has_bom(path):
    """True when the file's first three bytes are the UTF-8 BOM."""
    try:
        with open(path, "rb") as handle:
            head = handle.read(3)
    except OSError:
        return None
    return head == BOM


def scan(root, tracked=None):
    """Read the tree and return the pinned report.

    `tracked` is injectable so a suite can drive the law without a git repo;
    production always takes the git universe.
    """
    if tracked is None:
        tracked, error = tracked_python(root)
    else:
        error = None
    offenders = []
    unreadable = []
    for rel in sorted(tracked):
        state = has_bom(os.path.join(root, rel.replace("/", os.sep)))
        if state is None:
            unreadable.append(rel)
        elif state:
            offenders.append(rel)
    if error:
        verdict = "SOURCE-BOM-UNREADABLE-TREE"
    elif offenders or unreadable:
        verdict = VERDICT_FOUND
    else:
        verdict = VERDICT_CLEAN
    return {
        "verdict": verdict,
        "tracked_python": len(tracked),
        "offenders": offenders,
        "unreadable": unreadable,
        "_error": error,
    }


def render(report):
    lines = ["%s tracked_python=%d offenders=%d unreadable=%d" % (
        report["verdict"], report["tracked_python"],
        len(report["offenders"]), len(report["unreadable"]))]
    for rel in report["offenders"]:
        lines.append("BOM %s" % rel)
    for rel in report["unreadable"]:
        lines.append("UNREADABLE %s" % rel)
    if report.get("_error"):
        lines.append("ENV %s" % report["_error"])
    return lines


def to_json(report):
    body = dict((key, report[key]) for key in REPORT_KEYS)
    return json.dumps(body, ensure_ascii=True, sort_keys=False)


USAGE = "usage: source_bom_scan.py [--check] [--json] [--root DIR]"


def main(argv, out=None, err=None):
    out = out or sys.stdout
    err = err or sys.stderr
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    check = False
    as_json = False
    i = 0
    bad = None
    while i < len(argv):
        arg = argv[i]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            i += 1
            if i >= len(argv):
                bad = "--root needs a value"
                break
            root = argv[i]
        elif arg in ("-h", "--help"):
            out.write(USAGE + "\n")
            return 0
        else:
            bad = "unknown flag: %s" % arg
            break
        i += 1
    if bad:
        err.write("%s\n" % bad)
        err.write(USAGE + "\n")
        return EXIT_FOUND
    report = scan(root)
    if as_json:
        out.write(to_json(report) + "\n")
    else:
        for line in render(report):
            out.write(line + "\n")
    if report.get("_error"):
        return EXIT_ENV
    if check and (report["offenders"] or report["unreadable"]):
        return EXIT_FOUND
    return EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
