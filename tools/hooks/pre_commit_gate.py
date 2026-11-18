"""Commit-side call site of the freeze-round law (R2840, criteria AC-HK1..8)
and of the evidence-dialect law (R2926, criteria AC-EVB1..5).

The criteria were pinned in src/os/backlog.md BEFORE this file existed.

What this owns: reading the STAGED set and naming any per-round one-off at or
above the freeze, and any staged qa/ evidence file whose STAGED BYTES are in a
non-tee writer dialect. What it does not own: what counts as a one-off (that
answer is asked of the law, src/os/one_off_round_scripts.py through its own
`round_of()` and `FREEZE_ROUND`) or what counts as a non-tee dialect (asked of
src/os/evidence_dialect.py, the same module the writer census delegates to) -
so the commit face, the closeout face, the battery face and the census cannot
disagree about either shape.

R2926 measured why the second face exists and why the label is not it: 45
shell-captured evidence files landed unnoticed in one window, and over the
shipped tree 410 files carrying SHELL_CAPTURE_LABEL classify `tee` (healthy)
while 579 of the 590 baselined debt files carry no label at all. The label
names one writer family; the dialect names the disease. So this gate refuses by
CLASS, at the only birth site the loop actually passes through.

A retired one-off is a DELETE and is never refused: only added, copied,
modified or renamed paths are read. The same filter means a deleted evidence
file is never refused either.

R2933 second face (criteria AC-CGH1..AC-CGH5, pinned in src/os/backlog.md
BEFORE this code): the staged face reads the INDEX, so a file that is `git
add`-ed as healthy and then rewritten on disk in a shell dialect still commits
clean, and a non-tee file that is written and never staged is invisible to it
for the whole round. This gate now also runs the shipped writer census
(src/os/qa_writer_census.py) over the WORKING TREE at root/qa and refuses on
the same `flags` face the closeout gate gates on (R2932 decision: a baselined
file no family decodes is PUBLISHED, never refused - it is history no round
created). Both faces always run and report separately, so neither can mask the
other. Chosen over wiring the closeout instead because the closeout is not a
program in this repo - it is the round's own action sequence - and the only
site that can refuse mechanically is git.

  exit 0 = HOOK OK, nothing staged at or above the freeze in a bad dialect and
           the working tree's evidence census is clean
  exit 1 = E_HOOK_REFUSE (one-off) and/or E_HOOK_EVIDENCE (staged dialect)
           and/or E_HOOK_TREE (working-tree census flags)
  exit 2 = E_HOOK_BAD_FLAGS
  exit 3 = E_HOOK_NO_GIT (the staged set could not be read)
         = E_HOOK_NO_LAW (the freeze law is not next to this gate)
         = E_HOOK_NO_EVIDENCE_LAW (the dialect law is not next to this gate)
         = E_HOOK_NO_CENSUS_LAW (the census law is not in the tree it gates)
         = E_HOOK_NO_CENSUS_BASELINE (the census baseline is missing/unreadable)
         = E_HOOK_CENSUS_EMPTY (the evidence dir holds no log to classify)
         = E_HOOK_CENSUS_ROW (a census row this gate cannot read)
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

USAGE = (
    "usage: pre_commit_gate.py [--root PATH] [--freeze N] [--help]\n"
    "  --root PATH  git work tree to read (default the tree above tools/)\n"
    "  --freeze N   round id at or above which a staged one-off is refused\n"
    "               (default comes from the law)\n"
    "  exit 0 = HOOK OK, 1 = E_HOOK_REFUSE/E_HOOK_EVIDENCE, 2 = bad flags,\n"
    "           3 = no git/law/dialect\n"
)


class GateError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def load_law(root):
    """The freeze law, imported from the tree being committed."""
    law_dir = os.path.join(root, "src", "os")
    if not os.path.isdir(law_dir):
        raise GateError("E_HOOK_NO_LAW", law_dir)
    if law_dir not in sys.path:
        sys.path.insert(0, law_dir)
    import one_off_round_scripts as law

    return law


def load_dialect(root):
    """The evidence-dialect law (AC-EVB5: missing = named refusal)."""
    law_dir = os.path.join(root, "src", "os")
    if not os.path.isdir(law_dir):
        raise GateError("E_HOOK_NO_EVIDENCE_LAW", law_dir)
    if law_dir not in sys.path:
        sys.path.insert(0, law_dir)
    try:
        import evidence_dialect as dialect
    except Exception as exc:   # a broken law must not read as a clean commit
        raise GateError("E_HOOK_NO_EVIDENCE_LAW",
                        "%s: %s" % (type(exc).__name__, exc))
    return dialect


def staged(root):
    """Every staged path that would ADD bytes (deletions are retired files)."""
    proc = subprocess.run(
        ["git", "-C", root, "diff", "--cached", "--name-only",
         "--diff-filter=ACMR", "-z"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise GateError("E_HOOK_NO_GIT",
                        proc.stderr.decode("utf-8", "replace").strip())
    return [p for p in proc.stdout.decode("utf-8", "replace").split("\0") if p]


def staged_blob(root, rel):
    """The staged BYTES of one path - the index, not the work tree."""
    proc = subprocess.run(["git", "-C", root, "show", ":" + rel],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise GateError("E_HOOK_NO_GIT",
                        "staged blob unreadable: %s (%s)"
                        % (rel, proc.stderr.decode("utf-8", "replace").strip()))
    return proc.stdout


def evidence_refusals(root, paths, dialect):
    """Staged qa/*.log paths whose staged bytes are not the healthy dialect.

    AC-EVB2: scoped to the evidence directory, not to the dialect - a
    non-tee sample filed anywhere else (logs/ archive copies) still commits.
    """
    out = []
    for rel in paths:
        norm = rel.replace("\\", "/")
        if not (norm.startswith("qa/") and norm.endswith(".log")):
            continue
        row = dialect.classify_bytes(staged_blob(root, rel))
        if row["class"] != dialect.HEALTHY:
            out.append((rel, row["class"]))
    out.sort()
    return out


def load_census(root):
    """The writer-census law, imported from the tree being committed.

    AC-CGH3: a missing or broken census module is a NAMED refusal, never a
    pass - the same law AC-EVB5 applies to the dialect module. The census
    inserts its own sibling dirs on sys.path from its own __file__, so a
    fixture world that ships src/os and src/sandbox needs nothing else.
    """
    law_dir = os.path.join(root, "src", "os")
    if not os.path.isdir(law_dir):
        raise GateError("E_HOOK_NO_CENSUS_LAW", law_dir)
    if law_dir not in sys.path:
        sys.path.insert(0, law_dir)
    try:
        import qa_writer_census as census
    except Exception as exc:   # a broken law must not read as a clean commit
        raise GateError("E_HOOK_NO_CENSUS_LAW",
                        "%s: %s" % (type(exc).__name__, exc))
    return census


def tree_face(root):
    """The census `flags` face over the WORKING TREE (R2933).

    The staged face reads the index; this one reads the disk, and the two are
    not mirrors: `git add` a healthy file and then rewrite it in a shell
    dialect and the index stays clean while the disk does not. AC-CGH4 keeps
    the R2932 decision intact - `reader_refused` is PUBLISHED on the row and
    never gates, because it counts files baselined by name at freeze time.

    Returns (kind, lines) with kind in PASS / REFUSED / SKIP, or raises
    GateError for an input it cannot read.
    """
    target = os.path.join(root, "qa")
    if not os.path.isdir(target):
        # AC-EVB2's scope law: the verdict is scoped to the evidence dir. No
        # dir means nothing is in scope, and the line says so instead of
        # passing silently.
        return "SKIP", ["HOOK TREE SKIP reason=no-evidence-dir dir=qa"]
    census = load_census(root)
    baseline = os.path.join(target, census.BASELINE_NAME)
    if not os.path.exists(baseline):
        raise GateError("E_HOOK_NO_CENSUS_BASELINE",
                        os.path.basename(baseline))
    lines, code = census.check_against_baseline(target, baseline)
    if code == 3:
        raise GateError("E_HOOK_CENSUS_EMPTY", target)
    if code not in (0, 2) or any(ln.startswith("baseline") for ln in lines):
        raise GateError("E_HOOK_NO_CENSUS_BASELINE",
                        lines[0] if lines else os.path.basename(baseline))
    try:
        files = census.published_int(lines, "files")
        flags = census.published_int(lines, "flags")
        unreadable = census.published_int(lines, "reader_refused")
    except ValueError as exc:
        raise GateError("E_HOOK_CENSUS_ROW", str(exc))
    named = [ln for ln in lines
             if ln.startswith("[flag]") or ln.startswith("[refuse-read]")]
    if flags == 0:
        return "PASS", (["HOOK TREE PASS files=%d flags=0 reader_refused=%d "
                         "gating=flags" % (files, unreadable)] + named)
    return "REFUSED", (["E_HOOK_TREE flags=%d files=%d gating=flags"
                        % (flags, files)] + named)


def refusals(paths, law, freeze):
    """Staged paths whose basename is a one-off at or above the freeze."""
    out = []
    for rel in paths:
        number = law.round_of(os.path.basename(rel))
        if number is not None and number >= freeze:
            out.append((rel, number))
    out.sort()
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0
    root = ROOT
    freeze = None
    rest = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--root", "--freeze"):
            if i + 1 >= len(argv):
                sys.stderr.write("E_HOOK_BAD_FLAGS missing value for %s\n" % arg)
                return 2
            value = argv[i + 1]
            if arg == "--root":
                root = value
            else:
                try:
                    freeze = int(value)
                except ValueError:
                    sys.stderr.write("E_HOOK_BAD_FLAGS --freeze must be an integer\n")
                    return 2
            i += 2
            continue
        rest.append(arg)
        i += 1
    if rest:
        sys.stderr.write("E_HOOK_BAD_FLAGS unknown argument %s\n" % rest[0])
        return 2

    try:
        law = load_law(root)
        if freeze is None:
            freeze = law.FREEZE_ROUND
        paths = staged(root)
        refused = refusals(paths, law, freeze)
        dialect = load_dialect(root)
        bad_evidence = evidence_refusals(root, paths, dialect)
    except GateError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3
    except Exception as exc:  # a broken law must not read as a clean commit
        sys.stderr.write("E_HOOK_LAW_BROKEN %s: %s\n"
                         % (type(exc).__name__, exc))
        return 3

    if refused:
        names = ",".join(rel for rel, _ in refused)
        sys.stderr.write(
            "E_HOOK_REFUSE refused=%d freeze=%d staged=%d files=%s\n"
            % (len(refused), freeze, len(paths), names))
        sys.stderr.write(
            "E_HOOK_REFUSE a per-round one-off is not committed: keep the "
            "behaviour in a permanent module and retire the one-off\n")
    if bad_evidence:
        names = ",".join("%s(%s)" % (rel, cls) for rel, cls in bad_evidence)
        sys.stderr.write(
            "E_HOOK_EVIDENCE refused=%d staged=%d files=%s\n"
            % (len(bad_evidence), len(paths), names))
        sys.stderr.write(
            "E_HOOK_EVIDENCE staged evidence is not in the healthy "
            "utf-8+LF dialect: rewrite it through tools/qa_log.py, or "
            "bypass deliberately with: git commit --no-verify\n")

    # AC-CGH1/AC-CGH2: evaluated on every run, independently of the staged
    # faces, so a clean index cannot be read as a clean tree and neither face
    # can hide the other's refusal in one run.
    try:
        tree_kind, tree_lines = tree_face(root)
    except GateError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3
    if tree_kind == "REFUSED":
        for line in tree_lines:
            sys.stderr.write("%s\n" % line)
        sys.stderr.write(
            "E_HOOK_TREE the working tree holds evidence a shell writer "
            "produced: rewrite it through tools/qa_log.py (utf-8 + LF), or "
            "bypass deliberately with: git commit --no-verify\n")
    else:
        for line in tree_lines:
            sys.stdout.write("%s\n" % line)

    if refused or bad_evidence or tree_kind == "REFUSED":
        return 1
    sys.stdout.write("HOOK OK staged=%d freeze=%d evidence=clean tree=%s "
                     "rc=0\n" % (len(paths), freeze, tree_kind))
    return 0


if __name__ == "__main__":
    sys.exit(main())
