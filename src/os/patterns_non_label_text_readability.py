"""patterns_non_label_text_readability - the artifact's OTHER text is readable too.

MEASURED at R2503 while wiring the render-path guard: patterns_label_readability
.gate is asked with patterns["labels"] ONLY, while src/sandbox/suite_matrix.py
::render interpolates patterns["header_note"], labels["response_text"], every
table caption and every face label straight into docs/sandbox-suite-matrix.md -
the CEO-visible artifact. A doctored copy carrying U+FFFD inside header_note
still read publishable=True from the label gate while the composed document
really carried the broken codepoint (qa/patterns-render-consumer-live-R2503.log),
so the shipped and readable-label-guarded tool could still publish unreadable
text.

This face closes that gap without growing a second classifier:

  interpolated_strings(patterns)
      the set of strings the render ACTUALLY READS out of the patterns
      document, derived by composing the real render against a recording
      mapping and keeping every string it asked for, addressed by the field
      path that asked for it ("header_note", "labels.summary_cols[0]",
      "domains[0].faces[1].label"). Nothing here holds a hand-written field
      list, so a field added to the patterns file is covered the moment the
      render reads it, and a field the render never reads is honestly not
      covered.
  guard(patterns)
      asks src/os/patterns_label_readability.gate - the SHIPPED per-codepoint
      law - at CALL time over that derived set, and raises NonLabelRefused
      naming the FIELD and the codepoints when the first suspect is found.
      The verdict is never re-derived here: patching PLR.gate moves this
      reading, which is how AC-PNLT1 is proved.
  publish(patterns, render)
      runs the caller's render only for a publishable file.

The patterns file is read, never rewritten: a run leaves its bytes and digest
untouched (AC-PNLT5).

Criteria AC-PNLT1..AC-PNLT6 were pinned in state/queue/tech.md:542 at R2503
BEFORE this code existed.

LIMIT, stated rather than buried: deriving the read set means composing the
real render once, so two module attributes are patched for the duration of
that single probe (PLR.gate to an allow-all stub, and this module's own guard
flag so the probe cannot re-enter itself) and both are restored in a finally
block. A concurrent in-process caller in the same interpreter could observe
the patched gate during that window; the CLI and the shipped render path are
single-process, so the window is not reachable there.

Pure ASCII, stdlib only, no clock, no network, writes nothing but stdout.

CLI: --patterns JSON [--json]
  exit 0 = every interpolated string is publishable (verdict CLEAN)
  exit 2 = a non-label field is SUSPECT, publication refused
  exit 3 = the patterns file is missing, unreadable or malformed
  exit 5 = bad arguments
"""

import argparse
import hashlib
import json
import os
import sys

import patterns_label_readability as PLR

LABEL = "os-patterns-non-label-text-readability"
E_ARGS = "E_PNLT_ARGS"
E_PATTERNS = "E_PNLT_PATTERNS"
CLEAN = "CLEAN"
SUSPECT = "SUSPECT"
PROBE_STAMP = "PNLT-PROBE"
PROBE_STAMP_FROM = "pnlt-probe-source.md"

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")
PROBE_EVIDENCE = "pnlt-probe-evidence.log"

_PROBE_DEPTH = 0


class NonLabelRefused(Exception):
    """A non-label field stopped a publication; field and codepoints travel."""

    def __init__(self, code, field, codepoints):
        Exception.__init__(self, "%s: %s" % (code, field))
        self.code = code
        self.field = field
        self.codepoints = codepoints


class _Recorder(dict):
    """A patterns mapping that remembers the field path of every string read."""

    def __init__(self, source, sink, prefix):
        dict.__init__(self, source)
        self._sink = sink
        self._prefix = prefix

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        path = ("%s.%s" % (self._prefix, key)) if self._prefix else str(key)
        return _record(value, self._sink, path)

    def get(self, key, default=None):
        """A field read through .get is a field the render publishes too."""
        if not dict.__contains__(self, key):
            return default
        return self.__getitem__(key)


def _record(value, sink, path):
    """Keep every string the render asks for, addressed by the asking path."""
    if isinstance(value, str):
        sink[path] = value
        return value
    if isinstance(value, dict):
        return _Recorder(value, sink, path)
    if isinstance(value, list):
        return [_record(item, sink, "%s[%d]" % (path, index))
                for index, item in enumerate(value)]
    return value


def suite_matrix_module():
    """The shipped render, imported from src/sandbox (one reader, no copy)."""
    if SANDBOX not in sys.path:
        sys.path.insert(0, SANDBOX)
    import suite_matrix
    return suite_matrix


def _allow_all(labels):
    """Stub used ONLY inside the coverage probe: the probe must read past the
    label gate to see every field, and a label defect is still caught by the
    shipped consumer seam one statement later in the real render."""
    return {"publishable": True, "code": None, "label": None,
            "codepoints": [], "refusal": None, "labels": []}


def interpolated_strings(patterns):
    """The strings the real render reads out of this document, derived."""
    global _PROBE_DEPTH
    module = suite_matrix_module()
    sink = {}
    recorder = _Recorder(patterns, sink, "")
    saved_gate = PLR.gate
    _PROBE_DEPTH += 1
    PLR.gate = _allow_all
    try:
        module.render(recorder, PROBE_EVIDENCE, {}, None, PROBE_STAMP,
                      stamp_from=PROBE_STAMP_FROM)
    finally:
        PLR.gate = saved_gate
        _PROBE_DEPTH -= 1
    return sink


def guard(patterns):
    """Ask the shipped gate at CALL time over what the render will publish."""
    if _PROBE_DEPTH:
        return {"tool": LABEL, "source": PLR.LABEL, "verdict": CLEAN,
                "publishable": True, "code": None, "refused_field": None,
                "refused_codepoints": [], "fields": []}
    strings = interpolated_strings(patterns)
    verdict = PLR.gate(strings)
    fields = sorted(strings)
    if not verdict["publishable"]:
        raise NonLabelRefused(verdict["code"], verdict["label"],
                              verdict["codepoints"])
    return {"tool": LABEL, "source": PLR.LABEL, "verdict": CLEAN,
            "publishable": True, "code": None, "refused_field": None,
            "refused_codepoints": [], "fields": fields}


def reading(patterns):
    """What the render path would publish, as a report row (never raises)."""
    try:
        row = guard(patterns)
    except NonLabelRefused as exc:
        return {"tool": LABEL, "source": PLR.LABEL, "verdict": SUSPECT,
                "publishable": False, "code": exc.code,
                "refused_field": exc.field,
                "refused_codepoints": exc.codepoints,
                "fields": sorted(interpolated_strings(patterns))}
    return row


def publish(patterns, render):
    """Run render() only for a publishable document, keeping its bytes."""
    guard(patterns)
    return render()


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def render(report_row):
    lines = ["PATTERNS NON-LABEL READABILITY %s verdict=%s source=%s fields=%d"
             % (report_row["tool"], report_row["verdict"],
                report_row["source"], len(report_row["fields"]))]
    if not report_row["publishable"]:
        lines.append("  refused=%s field=%s codepoints=%s"
                     % (report_row["code"], report_row["refused_field"],
                        ",".join(report_row["refused_codepoints"])))
    for field in report_row["fields"]:
        lines.append("  %s" % field)
    return "\n".join(lines)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--patterns", required=True, metavar="JSON",
                        help="suite_matrix_patterns.json (the interpolated text)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    try:
        document = load(args.patterns)
        before = digest(args.patterns)
    except (OSError, ValueError) as exc:
        print("FAIL patterns: %s %s" % (E_PATTERNS, exc))
        return 3
    try:
        row = reading(document)
    except (KeyError, TypeError, AttributeError) as exc:
        print("FAIL patterns: %s incomplete document: %s" % (E_PATTERNS, exc))
        return 3
    after = digest(args.patterns)
    if after != before:
        print("FAIL digest: %s patterns file changed under a read-only face"
              % E_ARGS)
        return 5
    print(json.dumps(row, sort_keys=True, indent=2)
          if args.json else render(row))
    return 0 if row["publishable"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))