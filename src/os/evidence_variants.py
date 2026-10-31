"""evidence_variants (R2302; criteria AC-EVR1..AC-EVR6 were pinned inside the
R2288 seed row of state/queue/tech.md BEFORE this code existed).

followup_history reads the canonical `reconcile-all-R<nnnn>.log` names and
reports every other name as IGNORED (61 of them on the live pile: `-2.log`,
`-fail1.log`, `.err`, `-retry.log`). An IGNORED list is honest about what was
skipped but says nothing about what it skipped, so:

  - a failure leg written under a variant name is invisible to the history
    while the canonical leg of the same round still reads green;
  - a correction retry that turned a RED battery GREEN is counted as noise;
  - a variant whose canonical round was never committed reads exactly like a
    duplicate of a round that does exist.

This module is a READ-ONLY classifier over one evidence directory. For every
non-canonical `reconcile-all*` name it reports:

  - the round it belongs to and the suffix that makes it non-canonical, both
    derived by asking followup_history.NAME_RE rather than by a second regex
    (AC-EVR1: the law has one owner, so patching that pattern changes both
    readers);
  - ORPHAN when no canonical leg of that round exists on disk - the variant is
    listed, never dropped silently (AC-EVR2);
  - DUPLICATE or DISTINCT by CONTENT digest, never by name, with both digests
    named on a DISTINCT (AC-EVR3);
  - whether the name is a correction retry, asked through
    retry_naming.is_retry so the retry law keeps its single owner.

It writes nothing, reads no clock and opens no network connection (AC-EVR4,
AC-EVR6). Unreadable or missing evidence fails closed with its own code and
zero fabricated rows.

Pure stdlib, pure-ASCII source, zero network.
"""

import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import followup_history as FH
import retry_naming as RN

REPORT_KEYS = ("dir", "counts", "variants", "verdict")
VARIANT_KEYS = ("name", "round", "suffix", "canonical", "kind", "status",
                "digest", "canonical_digest")
COUNT_KEYS = ("variants", "duplicate", "distinct", "orphan", "retry")

TERMINAL_EXTENSIONS = (".log", ".err")

E_EVR_BAD_ARGS = "E_EVR_BAD_ARGS"
E_EVR_NO_EVIDENCE = "E_EVR_NO_EVIDENCE"
E_EVR_BAD_NAME = "E_EVR_BAD_NAME"
E_EVR_UNREADABLE = "E_EVR_UNREADABLE"


class EvidenceVariantsError(Exception):
    """A reading that must not guess, carrying its own token."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code + (" " + detail if detail else ""))
        self.code = code
        self.detail = detail


def canonical_prefix():
    """AC-EVR1: the name scope is derived from followup_history's own law.

    The pattern text is split at its first group, so the literal prefix is
    never restated here - patch FH.NAME_RE and both readers move together.
    """
    pattern = FH.NAME_RE.pattern
    head = pattern[1:] if pattern.startswith("^") else pattern
    prefix = head.split("(")[0]
    if not prefix:
        raise EvidenceVariantsError(E_EVR_BAD_NAME, "empty prefix law")
    return prefix


def core_of(name):
    """The name without its terminal extension, or None when it has none."""
    for extension in TERMINAL_EXTENSIONS:
        if name.endswith(extension) and len(name) > len(extension):
            return name[:-len(extension)]
    return None


def split_core(core):
    """Ask the shared law for the longest canonical head; the rest is suffix.

    No regex of our own decides what a round is: every candidate split is
    handed to FH.NAME_RE, so a change to that law changes this reader.
    """
    for index in range(len(core), 0, -1):
        head = core[:index]
        match = FH.NAME_RE.match(head + ".log")
        if match is not None:
            return head, core[index:], int(match.group(2))
    raise EvidenceVariantsError(E_EVR_BAD_NAME, core)


def digest_of(path):
    """AC-EVR4: an unreadable file fails closed instead of reading as a twin."""
    try:
        with io.open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except (OSError, ValueError):
        raise EvidenceVariantsError(E_EVR_UNREADABLE, os.path.basename(path))


def kind_of(name, core):
    """The retry law has one owner; it only speaks about .log names."""
    probe = name if name.endswith(".log") else core + ".log"
    return "retry" if RN.is_retry(probe) else "other"


def classify(path, name):
    """One variant's honest reading: round, suffix, kind, status, digests."""
    prefix = canonical_prefix()
    core = core_of(name)
    if core is None or not core.startswith(prefix):
        raise EvidenceVariantsError(E_EVR_BAD_NAME, name)
    head, suffix, number = split_core(core)
    canonical = head + ".log"
    canonical_path = os.path.join(path, canonical)
    mine = digest_of(os.path.join(path, name))
    if not os.path.isfile(canonical_path):
        return {"name": name, "round": "R%d" % number, "suffix": suffix,
                "canonical": canonical, "kind": kind_of(name, core),
                "status": "ORPHAN", "digest": mine,
                "canonical_digest": None}
    theirs = digest_of(canonical_path)
    status = "DUPLICATE" if mine == theirs else "DISTINCT"
    return {"name": name, "round": "R%d" % number, "suffix": suffix,
            "canonical": canonical, "kind": kind_of(name, core),
            "status": status, "digest": mine, "canonical_digest": theirs}


def variants(root, directory="qa"):
    """Every non-canonical leg of one directory, in name order."""
    path = directory
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    if not os.path.isdir(path):
        raise EvidenceVariantsError(E_EVR_NO_EVIDENCE, directory)
    try:
        names = sorted(os.listdir(path))
    except OSError:
        raise EvidenceVariantsError(E_EVR_NO_EVIDENCE, directory)
    prefix = canonical_prefix()
    rows = []
    for name in names:
        if not name.startswith(prefix):
            continue
        core = core_of(name)
        if core is None:
            continue
        if FH.NAME_RE.match(name) is not None:
            continue
        rows.append(classify(path, name))
    rows.sort(key=lambda row: row["name"])
    counts = {"variants": len(rows), "duplicate": 0, "distinct": 0,
              "orphan": 0, "retry": 0}
    for row in rows:
        if row["status"] == "DUPLICATE":
            counts["duplicate"] += 1
        elif row["status"] == "DISTINCT":
            counts["distinct"] += 1
        else:
            counts["orphan"] += 1
        if row["kind"] == "retry":
            counts["retry"] += 1
    verdict = "RESOLVED"
    if counts["distinct"] or counts["orphan"]:
        verdict = "UNRESOLVED"
    return {"dir": directory.replace(os.sep, "/"), "variants": rows,
            "counts": counts, "verdict": verdict}


def render(report):
    """One line per variant, the two digests named on a DISTINCT."""
    counts = report["counts"]
    out = ["EVIDENCE VARIANTS dir=%s variants=%d duplicate=%d distinct=%d "
           "orphan=%d retry=%d verdict=%s"
           % (report["dir"], counts["variants"], counts["duplicate"],
              counts["distinct"], counts["orphan"], counts["retry"],
              report["verdict"])]
    for row in report["variants"]:
        out.append("  %s round=%s suffix=%s kind=%s status=%s "
                   "digest=%s canonical_digest=%s"
                   % (row["name"], row["round"], row["suffix"] or "-",
                      row["kind"], row["status"], row["digest"][:12],
                      (row["canonical_digest"] or "-")[:12]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        if key == "counts":
            counts = {}
            for name in COUNT_KEYS:
                counts[name] = report["counts"][name]
            ordered["counts"] = counts
        elif key == "variants":
            pinned = []
            for item in report["variants"]:
                row = {}
                for name in VARIANT_KEYS:
                    row[name] = item[name]
                pinned.append(row)
            ordered["variants"] = pinned
        else:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: evidence_variants.py --variants [DIR] [--root PATH] [--json]\n"
         "  DIR defaults to qa\n"
         "  exit 0 = every variant resolves to a canonical round leg\n"
         "  exit 2 = some variant is ORPHAN or DISTINCT\n"
         "  exit 3 = evidence absent or unreadable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    operation = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    directory = "qa"
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--variants":
            operation = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_EVR_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write("E_EVR_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        else:
            directory = arg
        index += 1
    if not operation:
        sys.stdout.write("E_EVR_BAD_ARGS: --variants is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = variants(root, directory)
    except EvidenceVariantsError as exc:
        sys.stdout.write("%s\n" % str(exc))
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "UNRESOLVED":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))