"""matrix_stamp_from_liveness - a borrowed stamp now says whether it resolves.

R2442 shipped matrix_stamp_provenance_line: an artifact rendered with a
BORROWED stamp carries a line naming the document it borrowed from, and
recorded_source() reads that same line back. MEASURED at R2442 the line was
only ever copied: recorded_source() hands the recorded string back verbatim,
so a doc borrowing from a source deleted the next day reads exactly like a
live one - the operator cannot tell a resolvable provenance from a dangling
one.

This face asks the TREE, at CALL time, whether the recorded source still
exists, and publishes the answer as LIVE / MISSING / AMBIGUOUS / NONE
together with the segment the doc must carry. The recorded string is never
rewritten: it is reported byte for byte as the document wrote it, and the
resolved path travels beside it.

Resolution order (one law, two steps, no picking):
  1. the recorded string joined onto the root - if that file exists, LIVE.
  2. otherwise the root is walked once for files whose BASENAME equals the
     recorded basename: exactly one match is LIVE (the resolved path is
     published), more than one is AMBIGUOUS with every candidate named, and
     none is MISSING.

A doc that carries no provenance line reads NONE, not MISSING: the absence of
a borrow is not a dangling borrow.

The provenance reading itself is matrix_stamp_provenance_line's, asked at
CALL time, so there is still exactly one reader of that line and the labels
come from suite_matrix_patterns.json rather than from this source.

Criteria AC-MSFL1..AC-MSFL6 were pinned in state/queue/tech.md:529 at R2442
BEFORE this code existed.

Pure ASCII, stdlib only, no clock, no network, writes nothing.

CLI: --patterns JSON --doc PATH [--root PATH] [--json]
  exit 0 = reading published (LIVE or NONE)
  exit 2 = a dangling or ambiguous borrow is named (MISSING / AMBIGUOUS)
  exit 3 = the doc, the patterns or the root cannot be read
  exit 5 = bad arguments
"""

import argparse
import json
import os
import sys

LABEL = "os-matrix-stamp-from-liveness"
E_PATTERNS = "E_MSFL_PATTERNS_UNREADABLE"
E_DOC = "E_MSFL_DOC_UNREADABLE"
E_ROOT = "E_MSFL_ROOT_UNREADABLE"

LIVE = "LIVE"
MISSING = "MISSING"
AMBIGUOUS = "AMBIGUOUS"
NONE = "NONE"

SKIP_DIRS = (".git", "__pycache__", ".codely-cli")

_MPL = None


def law():
    """matrix_stamp_provenance_line, imported on first use (one reader)."""
    global _MPL
    if _MPL is None:
        here = os.path.dirname(os.path.abspath(__file__))
        if here not in sys.path:
            sys.path.insert(0, here)
        import matrix_stamp_provenance_line as module
        _MPL = module
    return _MPL


def _relative(root, path):
    return os.path.relpath(path, root).replace("\\", "/")


def candidates_for(root, basename):
    """Every file under the root whose name is exactly the basename."""
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        if basename in filenames:
            hits.append(_relative(root, os.path.join(dirpath, basename)))
    hits.sort()
    return hits


def resolve(recorded, root):
    """Answer LIVE / MISSING / AMBIGUOUS for one recorded provenance string.

    None is the honest answer for a doc that records nothing (NONE), and the
    recorded string is never rewritten - it travels verbatim in the report.
    """
    if recorded is None:
        return {"state": NONE, "recorded": None, "resolved": None,
                "candidates": []}
    text = str(recorded).strip().replace("\\", "/")
    if not text:
        return {"state": NONE, "recorded": None, "resolved": None,
                "candidates": []}
    exact = os.path.join(root, *text.split("/"))
    if os.path.isfile(exact):
        return {"state": LIVE, "recorded": recorded,
                "resolved": _relative(root, exact), "candidates": []}
    basename = text.rsplit("/", 1)[-1]
    hits = candidates_for(root, basename)
    if len(hits) == 1:
        return {"state": LIVE, "recorded": recorded,
                "resolved": hits[0], "candidates": hits}
    if len(hits) > 1:
        return {"state": AMBIGUOUS, "recorded": recorded, "resolved": None,
                "candidates": hits}
    return {"state": MISSING, "recorded": recorded, "resolved": None,
            "candidates": []}


def report(labels, doc_text, root):
    """The whole reading: the borrow the doc records, the segment it must
    carry, and where that borrow resolves to on the tree right now."""
    recorded = law().recorded_source(doc_text, labels)
    row = resolve(recorded, root)
    row["label"] = LABEL
    row["segment"] = law().segment(labels, recorded)
    return row


def render(row):
    return "\n".join([
        "MATRIX STAMP FROM LIVENESS label=%s" % row["label"],
        "  state=%s" % row["state"],
        "  recorded=%s" % (row["recorded"] or "-"),
        "  resolved=%s" % (row["resolved"] or "-"),
        "  candidates=%s" % (",".join(row["candidates"]) or "-"),
        "  segment=%s" % (row["segment"] or "-"),
    ])


def exit_code(state):
    if state in (LIVE, NONE):
        return 0
    return 2


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--patterns", required=True, metavar="JSON",
                        help="suite_matrix_patterns.json (the label owner)")
    parser.add_argument("--doc", required=True, metavar="PATH",
                        help="the document whose provenance line is read")
    parser.add_argument("--root", default=".", metavar="PATH",
                        help="the tree the recorded source is resolved against")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    try:
        with open(args.patterns, encoding="utf-8") as handle:
            labels = json.load(handle)["labels"]
    except (OSError, ValueError, KeyError) as exc:
        print("FAIL patterns: %s %s" % (E_PATTERNS, exc))
        return 3
    if not os.path.isdir(args.root):
        print("FAIL root: %s %s" % (E_ROOT, args.root))
        return 3
    try:
        with open(args.doc, encoding="utf-8") as handle:
            doc_text = handle.read()
    except OSError as exc:
        print("FAIL doc: %s %s" % (E_DOC, exc))
        return 3

    try:
        row = report(labels, doc_text, args.root)
    except KeyError as exc:
        print("FAIL patterns: %s" % exc.args[0])
        return 2

    if args.json:
        print(json.dumps({"label": row["label"], "state": row["state"],
                          "recorded": row["recorded"],
                          "resolved": row["resolved"],
                          "candidates": row["candidates"],
                          "segment": row["segment"]}, sort_keys=True))
    else:
        print(render(row))
    return exit_code(row["state"])


if __name__ == "__main__":
    sys.exit(main(sys.argv))