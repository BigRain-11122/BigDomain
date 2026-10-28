#!/usr/bin/env python3
"""retry_naming.py - one suffix for correction reruns (AC-RTN1..AC-RTN6).

A rerun of an evidence stem whose earlier RUNNER verdict differed is a
correction RETRY, not the second leg of a double-run identity pair. The
two used to share "-run2", so the identity auditor read the body
sentences of 420 suites as a file-pair byte claim (R2233, E_FALSE_BYTE_
CLAIM disclosed by hand into the baseline). This module owns the naming
seam; run_identity owns the pairing rule and owns the retry predicate,
so there is exactly one definition of what a retry name is.

ASCII only, stdlib only, zero network, no wall clock.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import run_identity as RI

RETRY_SUFFIX = RI.RETRY_SUFFIX
LEGACY_RERUN_SUFFIXES = ("-run2", "-2")
CLASSES = ("first", "retry", "legacy-rerun", "identity-leg")


class RetryNamingError(ValueError):
    """Raised with a machine-readable .code."""

    def __init__(self, code, message):
        ValueError.__init__(self, "%s: %s" % (code, message))
        self.code = code
        self.message = message


def _names(directory):
    try:
        return set(os.listdir(directory))
    except OSError as exc:
        raise RetryNamingError("E_RETRY_NO_DIR",
                               "cannot list %r: %s" % (directory, exc))


def base_stem(name):
    """The stem a name belongs to, with any retry suffix removed."""
    if not name.endswith(".log"):
        raise RetryNamingError("E_RETRY_BAD_NAME",
                               "not an evidence name: %r" % (name,))
    stem = name[:-4]
    match = RI.RETRY_RE.match(stem)
    if match:
        stem = match.group(1)
    if not stem:
        raise RetryNamingError("E_RETRY_BAD_NAME",
                               "empty stem: %r" % (name,))
    return stem


def is_retry(name):
    """Delegates to the single predicate owned by run_identity."""
    return RI.is_retry_name(name)


def check_name(name):
    """Refuse the legacy rerun suffixes for a new evidence name."""
    base_stem(name)
    stem = name[:-4]
    lowered = stem.lower()
    for suffix in LEGACY_RERUN_SUFFIXES:
        if lowered.endswith(suffix):
            raise RetryNamingError(
                "E_RETRY_BAD_SUFFIX",
                "a correction rerun uses %s, never %s: %r"
                % (RETRY_SUFFIX, suffix, name))
    if RI.is_retry_name(name):
        raise RetryNamingError(
            "E_RETRY_BAD_NAME",
            "pass the base name, not a retry leg: %r" % (name,))
    return stem


def retry_name(name, directory):
    """The next free retry leg for a stem: -retry, then -retry2, -retry3."""
    stem = base_stem(name)
    taken = _names(directory)
    candidate = stem + RETRY_SUFFIX + ".log"
    index = 1
    while candidate in taken:
        index += 1
        candidate = stem + RETRY_SUFFIX + str(index) + ".log"
    return candidate


def _counterpart(stem):
    """The identity-pair counterpart of a stem, or None."""
    for left, right in RI.PAIR_SUFFIXES:
        if right and stem.endswith(right):
            return stem[:-len(right)] + left
        if stem.endswith(left):
            return stem[:-len(left)] + right
    return None


def _suite_verdict(text):
    try:
        _criteria, suite = RI.parse_verdicts(text)
    except RI.IdentityError as exc:
        raise RetryNamingError("E_RETRY_BAD_EVIDENCE",
                               "unreadable evidence: %s" % (exc.code,))
    return suite["verdict"] if suite else None


def resolve_rerun(name, directory, new_text=None):
    """Name a rerun: first run keeps its stem, a rerun becomes a retry.

    Refuses a stem that is already an identity-pair leg (AC-RTN3 keeps
    the two classes apart) and reports whether the RUNNER verdict moved.
    """
    check_name(name)
    stem = base_stem(name)
    taken = _names(directory)
    existing = stem + ".log"
    if existing not in taken:
        return {"name": existing, "class": "first", "base": stem,
                "verdict_before": None, "verdict_after": None,
                "verdict_changed": False}
    other = _counterpart(stem)
    if other and (other + ".log") in taken:
        raise RetryNamingError(
            "E_RETRY_IDENTITY_SUFFIX",
            "a rerun of %r is a retry, not an identity leg" % (existing,))
    before = _suite_verdict(RI.read_text(os.path.join(directory, existing)))
    after = None if new_text is None else _suite_verdict(new_text)
    return {"name": retry_name(existing, directory), "class": "retry",
            "base": stem, "verdict_before": before,
            "verdict_after": after,
            "verdict_changed": after is None or after != before}


def _class_of(name, taken):
    stem = name[:-4]
    if RI.is_retry_name(name):
        return "retry"
    lowered = stem.lower()
    for suffix in LEGACY_RERUN_SUFFIXES:
        if lowered.endswith(suffix):
            return "legacy-rerun"
    other = _counterpart(stem)
    if other and (other + ".log") in taken:
        return "identity-leg"
    return "first"


def audit_dir(directory):
    """Read-only census of one evidence directory (never writes)."""
    try:
        names = sorted(os.listdir(directory))
    except OSError as exc:
        raise RetryNamingError("E_RETRY_NO_DIR",
                               "cannot list %r: %s" % (directory, exc))
    taken = set(names)
    rows = []
    for name in names:
        if not name.endswith(".log"):
            continue
        rows.append({"name": name, "class": _class_of(name, taken),
                     "base": base_stem(name)})
    envelope = {
        "dir": directory,
        "file_count": len(rows),
        "retry_count": sum(1 for row in rows if row["class"] == "retry"),
        "legacy_rerun_count": sum(1 for row in rows
                                  if row["class"] == "legacy-rerun"),
        "pair_count": len(RI.find_pairs(directory)),
        "rows": rows,
    }
    return envelope


def _stderr(message):
    sys.stderr.write(message + "\n")


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        _stderr("usage: retry_naming.py --check-dir DIR | "
                "--next NAME --dir DIR")
        return 2
    try:
        if args[0] == "--check-dir":
            if len(args) != 2:
                _stderr("usage: retry_naming.py --check-dir DIR")
                return 2
            if not os.path.isdir(args[1]):
                _stderr("E_RETRY_NO_DIR: %s" % (args[1],))
                return 3
            envelope = audit_dir(args[1])
            for row in envelope["rows"]:
                print("check-dir name=%s class=%s base=%s"
                      % (row["name"], row["class"], row["base"]))
            print("dir files=%d retry=%d legacy=%d pairs=%d"
                  % (envelope["file_count"], envelope["retry_count"],
                     envelope["legacy_rerun_count"],
                     envelope["pair_count"]))
            return 2 if envelope["legacy_rerun_count"] else 0
        if args[0] == "--next":
            if len(args) != 4 or args[2] != "--dir":
                _stderr("usage: retry_naming.py --next NAME --dir DIR")
                return 2
            print("next name=%s" % (retry_name(args[1], args[3]),))
            return 0
        _stderr("unknown command: %r" % (args[0],))
        return 2
    except RetryNamingError as exc:
        _stderr("%s: %s" % (exc.code, exc.message))
        return 2


if __name__ == "__main__":
    sys.exit(main())