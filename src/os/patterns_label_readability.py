"""patterns_label_readability - a label must be readable before it is published.

MEASURED at R2494 while shipping the stamp liveness face: a reader that
decodes suite_matrix_patterns.json through the platform default code page
prints labels.stamp_from as a run of Cyrillic and replacement characters
while its sibling labels read as proper Chinese, and suite_matrix renders
every label VERBATIM into docs/sandbox-suite-matrix.md - the CEO-visible
artifact - and into every evidence log that prints the segment. Nothing in
the tree asked whether a label is readable text, so a mis-decoded label was
published as if it were a label.

This face answers that question at CALL time and never rewrites the file:

  reading(labels)  classifies every label CLEAN or SUSPECT. A codepoint is
                   suspect when it is broken (replacement character,
                   unassigned, control, surrogate) or when it belongs to a
                   script the OTHER labels in this same file never carry.
                   Scripts and categories are asked of unicodedata for the
                   codepoint itself; nothing here holds a list of label keys
                   or a table of blessed scripts.
  gate(labels)     turns that reading into a publication verdict: the first
                   suspect label is NAMED with its key and its exact
                   codepoints, so a caller can refuse instead of rendering.
  publish(labels, render)
                   calls the caller's render only when the file is
                   publishable and raises LabelRefused otherwise. A clean
                   file reaches render untouched, so the artifact keeps
                   today's bytes byte for byte.

Criteria AC-PLR1..AC-PLR6 were pinned in state/queue/tech.md:538 at R2494
BEFORE this code existed.

Pure ASCII, stdlib only, no clock, no network, writes nothing.

CLI: --patterns JSON [--json] [--label KEY]
  exit 0 = every label publishable (verdict CLEAN)
  exit 2 = a label is SUSPECT, publication refused (E_PLR_SUSPECT)
  exit 3 = the patterns file is missing, unreadable or malformed
  exit 5 = bad arguments
"""

import argparse
import json
import sys
import unicodedata

LABEL = "os-patterns-label-readability"
E_ARGS = "E_PLR_ARGS"
E_PATTERNS = "E_PLR_PATTERNS"
E_SUSPECT = "E_PLR_SUSPECT"
CLEAN = "CLEAN"
SUSPECT = "SUSPECT"


class LabelRefused(Exception):
    """A suspect label stopped a publication; the key and codepoints travel."""

    def __init__(self, key, codepoints):
        Exception.__init__(self, "%s: %s" % (E_SUSPECT, key))
        self.code = E_SUSPECT
        self.label = key
        self.codepoints = codepoints


def _codepoint_rows(text):
    """Every non-ASCII codepoint of one label with the class it derives to.

    Derived per codepoint from unicodedata: no blessed-script table and no
    key list lives here, so a new label in the patterns file is read with
    the same law as the old ones.
    """
    rows = []
    for index, char in enumerate(text):
        point = ord(char)
        if point < 128:
            continue
        name = unicodedata.name(char, "")
        category = unicodedata.category(char)
        if not name or name.startswith("<"):
            kind, bucket = "broken", "UNNAMED"
        elif name == "REPLACEMENT CHARACTER":
            kind, bucket = "broken", "REPLACEMENT"
        elif category[0] in ("C",):
            kind, bucket = "broken", category
        elif category[0] in ("P", "S", "Z", "N", "M"):
            kind, bucket = "shared", category
        else:
            kind, bucket = "script", name.split()[0]
        rows.append({"index": index, "codepoint": "U+%04X" % point,
                     "name": name or "UNNAMED", "kind": kind,
                     "bucket": bucket})
    return rows


def reading(labels):
    """Classify every string label against the scripts its siblings carry."""
    if not isinstance(labels, dict):
        raise ValueError("%s: labels must be an object" % E_PATTERNS)
    carried = {}
    per_label = {}
    for key in sorted(labels):
        value = labels[key]
        if not isinstance(value, str):
            continue
        rows = _codepoint_rows(value)
        per_label[key] = rows
        for row in rows:
            if row["kind"] == "script":
                carried.setdefault(row["bucket"], set()).add(key)

    out = []
    for key in sorted(per_label):
        rows = per_label[key]
        suspects = []
        sibling_scripts = set()
        for bucket, holders in carried.items():
            if holders - set([key]):
                sibling_scripts.add(bucket)
        for row in rows:
            if row["kind"] == "broken":
                suspects.append(dict(row, reason="BROKEN-CODEPOINT"))
            elif row["kind"] == "script" and sibling_scripts:
                if row["bucket"] not in sibling_scripts:
                    suspects.append(dict(row, reason="SCRIPT-NOT-IN-SIBLINGS"))
        out.append({"label": key, "verdict": SUSPECT if suspects else CLEAN,
                    "suspects": suspects,
                    "codepoints": [row["codepoint"] for row in rows]})
    return out


def gate(labels):
    """The publication verdict: publishable, or the first refusal named."""
    rows = reading(labels)
    for row in rows:
        if row["verdict"] == SUSPECT:
            return {"publishable": False,
                    "code": E_SUSPECT,
                    "label": row["label"],
                    "codepoints": [cp["codepoint"]
                                   for cp in row["suspects"]],
                    "refusal": row,
                    "labels": rows}
    return {"publishable": True, "code": None, "label": None,
            "codepoints": [], "refusal": None, "labels": rows}


def publish(labels, render):
    """Run render() only for a publishable file, keeping its bytes untouched."""
    verdict = gate(labels)
    if not verdict["publishable"]:
        raise LabelRefused(verdict["label"], verdict["codepoints"])
    return render()


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def report(verdict):
    return {"tool": LABEL, "publishable": verdict["publishable"],
            "code": verdict["code"], "refused_label": verdict["label"],
            "refused_codepoints": verdict["codepoints"],
            "labels": [{"label": row["label"], "verdict": row["verdict"],
                        "suspects": [{"index": cp["index"],
                                      "codepoint": cp["codepoint"],
                                      "name": cp["name"],
                                      "reason": cp["reason"]}
                                     for cp in row["suspects"]]}
                       for row in verdict["labels"]]}


def render(report_row):
    lines = ["PATTERNS LABEL READABILITY %s publishable=%s"
             % (report_row["tool"], str(report_row["publishable"]).lower())]
    if report_row["code"]:
        lines.append("  refused=%s label=%s codepoints=%s"
                     % (report_row["code"], report_row["refused_label"],
                        ",".join(report_row["refused_codepoints"])))
    for row in report_row["labels"]:
        lines.append("  %-14s %s" % (row["label"], row["verdict"]))
        for cp in row["suspects"]:
            lines.append("    %s at %d %s (%s)"
                         % (cp["codepoint"], cp["index"], cp["name"],
                            cp["reason"]))
    return "\n".join(lines)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--patterns", required=True, metavar="JSON",
                        help="suite_matrix_patterns.json (the label owner)")
    parser.add_argument("--label", default=None, metavar="KEY",
                        help="read one label instead of the whole file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    try:
        document = load(args.patterns)
        labels = document["labels"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("FAIL patterns: %s %s" % (E_PATTERNS, exc))
        return 3

    if args.label is not None:
        if args.label not in labels or not isinstance(labels[args.label], str):
            print("FAIL args: %s unknown label %r" % (E_ARGS, args.label))
            return 5
        labels = {args.label: labels[args.label]}

    verdict = gate(labels)
    row = report(verdict)
    print(json.dumps(row, sort_keys=True, indent=2)
          if args.json else render(row))
    return 0 if verdict["publishable"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))