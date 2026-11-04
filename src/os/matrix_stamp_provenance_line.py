"""matrix_stamp_provenance_line - a borrowed stamp now says so.

R2418 shipped --stamp-from so a render can follow another document's stamp,
but MEASURED at R2418 the artifact could not say so: the generation command
line is a fixed format string naming only --evidence, so a doc rendered with
a BORROWED stamp was byte-for-byte indistinguishable from an ordinary render
and doc_evidence_face read only the evidence segment. The borrow lived in the
operator's memory and nowhere on disk.

ONE law with two directions, so writing and reading cannot disagree:
segment() renders the line an artifact must carry when a source was given,
and recorded_source() reads that same line back - which is why --check on a
stamp-aligned doc recovers the borrow instead of reporting drift by design.

The label and its prefix come from suite_matrix_patterns.json; nothing here
restates a label, a path, a stamp value or the evidence line. An ordinary
render (no source given) gets None, so its bytes stay exactly as before.

Criteria AC-MSPL1..AC-MSPL6 were pinned in state/queue/tech.md:508 at R2418
BEFORE this code existed.

Pure ASCII, stdlib only, no clock, no network, writes nothing.

CLI: --patterns JSON (--stamp-from PATH | --doc PATH) [--json]
  exit 0 = reading published
  exit 2 = the label is missing from the patterns (E_MSPL_NO_LABEL)
  exit 3 = a named document cannot be read
  exit 5 = bad arguments
"""

import argparse
import json
import sys

LABEL_KEY = "stamp_from"
FLAG = "--stamp-from"
E_NO_LABEL = "E_MSPL_NO_LABEL"
E_DOC = "E_MSPL_DOC_UNREADABLE"
LABEL = "os-matrix-stamp-provenance-line"


def _prefix(labels):
    """The line prefix this segment owns, asked of the patterns every call.

    Fail closed rather than render a segment nobody can read back: the label
    is the only thing tying segment() and recorded_source() together.
    """
    label = labels.get(LABEL_KEY)
    if not isinstance(label, str) or not label.strip():
        raise KeyError("%s: %s missing from patterns" % (E_NO_LABEL,
                                                         LABEL_KEY))
    return "- %s: " % label


def segment(labels, stamp_from_rel):
    """The line a render must carry for a borrowed stamp, or None.

    None is the honest answer for an ordinary render: AC-MSPL1 requires an
    artifact with no source to keep today's bytes byte for byte.
    """
    if stamp_from_rel is None:
        return None
    text = str(stamp_from_rel).strip()
    if not text:
        return None
    return "%s%s %s" % (_prefix(labels), FLAG, text)


def recorded_source(text, labels):
    """Read the borrow back out of an existing doc (None = none recorded)."""
    prefix = _prefix(labels)
    for line in text.splitlines():
        if line.startswith(prefix):
            rest = line[len(prefix):].strip()
            if not rest.startswith(FLAG):
                return None
            rest = rest[len(FLAG):].strip()
            return rest or None
    return None


def report(labels, stamp_from_rel=None, doc_text=None):
    return {"label": LABEL_KEY,
            "segment": segment(labels, stamp_from_rel),
            "recorded": (None if doc_text is None
                         else recorded_source(doc_text, labels))}


def render(report_row):
    return "\n".join([
        "MATRIX STAMP PROVENANCE label=%s" % report_row["label"],
        "  segment=%s" % (report_row["segment"] or "-"),
        "  recorded=%s" % (report_row["recorded"] or "-"),
    ])


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--patterns", required=True, metavar="JSON",
                        help="suite_matrix_patterns.json (the label owner)")
    parser.add_argument("--stamp-from", default=None, metavar="PATH",
                        help="render the segment this source would record")
    parser.add_argument("--doc", default=None, metavar="PATH",
                        help="read the recorded source back out of a doc")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    if args.stamp_from and args.doc:
        print("FAIL args: pass --stamp-from or --doc, not both")
        return 5
    if not args.stamp_from and not args.doc:
        print("FAIL args: pass --stamp-from or --doc")
        return 5
    try:
        with open(args.patterns, encoding="utf-8") as handle:
            patterns = json.load(handle)
        labels = patterns["labels"]
    except (OSError, ValueError, KeyError) as exc:
        print("FAIL patterns: %s" % exc)
        return 3

    doc_text = None
    if args.doc is not None:
        try:
            with open(args.doc, encoding="utf-8") as handle:
                doc_text = handle.read()
        except OSError as exc:
            print("FAIL doc: %s %s" % (E_DOC, exc))
            return 3

    try:
        row = report(labels, args.stamp_from, doc_text)
    except KeyError as exc:
        print("FAIL patterns: %s" % exc.args[0])
        return 2

    if args.json:
        print(json.dumps({"label": row["label"],
                          "segment": row["segment"],
                          "recorded": row["recorded"]},
                         sort_keys=True))
    else:
        print(render(row))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))