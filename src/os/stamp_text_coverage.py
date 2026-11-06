"""stamp_text_coverage - the STAMP text the artifact prints is covered too.

MEASURED at R2509 while wiring the evidence-name seam: src/sandbox/suite_matrix.py
::render interpolates two CALLER-SUPPLIED strings into the CEO-visible suite
matrix document - the generation stamp and, when one is given, the
--stamp-from provenance source - and no shipped reading covers either.
Composing the real render with a stamp and a stamp_from carrying U+FFFD printed
both codepoints into the artifact while artifact_disk_text_readability and
evidence_name_text_coverage both still returned publishable=True.

The render takes those two strings at these positions:

  * the stamp line: "- <labels.stamp>: <labels.stamp_prefix><stamp>",
  * the provenance line, only when a source was given:
    "- <labels.stamp_from>: --stamp-from <stamp_from>".

This face closes that gap without growing a second classifier:

  printed_strings(patterns, stamp, stamp_from=None)
      the caller-supplied strings the render ACTUALLY prints, derived by
      composing the real render ONCE with the values in hand and reading the
      result back through the shipped reading laws - suite_matrix.doc_stamp
      for the stamp line and matrix_stamp_provenance_line.recorded_source for
      the borrow. Nothing here holds a canned value: whatever stamp is handed
      in is what gets classified. A render given no stamp_from prints no
      provenance line, so that piece is simply not claimed rather than
      reported as empty.
  guard(patterns, stamp, stamp_from=None)
      asks src/os/patterns_label_readability.gate - the SHIPPED per-codepoint
      law - at CALL time over that derived set, and raises StampTextRefused
      naming the PIECE and the offending VALUE when the first suspect is
      found. The verdict is never re-derived here: patching PLR.gate moves
      this reading, which is how AC-STPT1 is proved.
  publish(patterns, stamp, stamp_from, render)
      runs the caller's render only when the stamp text is publishable.

No source file, no stamp source document and no evidence file is rewritten:
their digests are unchanged across a full reading (AC-STPT5).

Criteria AC-STPT1..AC-STPT6 were pinned in state/queue/tech.md:549 as the R2509
seed row BEFORE this code existed.

LIMIT, stated rather than buried: deriving the set means composing the real
render once, so five suite_matrix module attributes are replaced for the
duration of that single probe - the four guard seams the render asks before it
reads anything (each a quiet stand-in) plus this face own seam, which answers
CLEAN while depth is held - and all five are restored in a finally block.
Every other attribute is the real module object. A concurrent in-process caller
could observe the window, which the single-process CLI and the shipped render
path never do.

SECOND LIMIT, stated as measured rather than assumed: the derivation uses the
render own doc_stamp law, which reads the stamp back out of the FIRST line
carrying the stamp prefix, so a patterns document whose stamp line is missing
is refused as a probe failure rather than silently covered.

Pure ASCII, stdlib only, no clock, no network, writes nothing but stdout.

CLI: --patterns JSON --stamp TEXT [--stamp-from TEXT] [--json]
  exit 0 = every printed stamp string is publishable (verdict CLEAN)
  exit 2 = a printed stamp string is SUSPECT, publication refused
  exit 3 = the patterns file is missing, unreadable or malformed
  exit 5 = bad arguments
"""

import argparse
import hashlib
import json
import os
import sys

import patterns_label_readability as PLR

LABEL = "os-stamp-text-coverage"
E_ARGS = "E_STPT_ARGS"
E_PATTERNS = "E_STPT_PATTERNS"
E_PROBE = "E_STPT_PROBE"
CLEAN = "CLEAN"
SUSPECT = "SUSPECT"
PROBE_EVIDENCE = "stpt-probe-evidence.log"
PIECE_STAMP = "artifact.stamp"
PIECE_STAMP_FROM = "artifact.stamp_from"

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")

_PROBE_DEPTH = 0


class StampTextRefused(Exception):
    """A printed stamp string stopped a publication; piece and value travel."""

    def __init__(self, code, piece, value, codepoints):
        Exception.__init__(self, "%s: %s" % (code, piece))
        self.code = code
        self.piece = piece
        self.value = value
        self.codepoints = codepoints


class _Quiet(object):
    """Stand-in for a guard the probe must read PAST; restored in finally."""

    def guard(self, *args, **kwargs):
        return None


def suite_matrix_module():
    """The shipped render, imported from src/sandbox (one reader, no copy)."""
    if SANDBOX not in sys.path:
        sys.path.insert(0, SANDBOX)
    import suite_matrix
    return suite_matrix


def _quiet_seams(module):
    """The guard seams this profile answers quietly, asked of the module."""
    names = ["PLRC", "PNLT", "ADTR", "EVNM", "STPT"]
    return [(name, getattr(module, name, None)) for name in names
            if getattr(module, name, None) is not None]


def printed_strings(patterns, stamp, stamp_from=None):
    """The caller-supplied strings the real render prints, derived not listed."""
    global _PROBE_DEPTH
    module = suite_matrix_module()
    seams = _quiet_seams(module)
    out = {}
    _PROBE_DEPTH += 1
    try:
        for name, _ in seams:
            setattr(module, name, _Quiet())
        text = module.render(patterns, PROBE_EVIDENCE, {}, None, stamp,
                             stamp_from=stamp_from)
    finally:
        for name, real in seams:
            setattr(module, name, real)
        _PROBE_DEPTH -= 1
    printed = module.doc_stamp(text, patterns)
    if printed is None:
        raise RuntimeError("%s: the render printed no stamp line" % E_PROBE)
    out[PIECE_STAMP] = printed
    borrowed = module.MSPL.recorded_source(text, patterns["labels"])
    if borrowed is not None:
        out[PIECE_STAMP_FROM] = borrowed
    return out


def _clean_row(fields):
    return {"tool": LABEL, "source": PLR.LABEL, "verdict": CLEAN,
            "publishable": True, "code": None, "refused_piece": None,
            "refused_value": None, "refused_codepoints": [],
            "fields": fields}


def guard(patterns, stamp, stamp_from=None):
    """Ask the shipped gate at CALL time over the printed stamp strings."""
    if _PROBE_DEPTH:
        return _clean_row([])
    strings = printed_strings(patterns, stamp, stamp_from)
    verdict = PLR.gate(strings)
    if not verdict["publishable"]:
        piece = verdict["label"]
        raise StampTextRefused(verdict["code"], piece, strings.get(piece),
                               verdict["codepoints"])
    return _clean_row(sorted(strings))


def reading(patterns, stamp, stamp_from=None):
    """What the render path would publish, as a report row (never raises)."""
    try:
        return guard(patterns, stamp, stamp_from)
    except StampTextRefused as exc:
        return {"tool": LABEL, "source": PLR.LABEL, "verdict": SUSPECT,
                "publishable": False, "code": exc.code,
                "refused_piece": exc.piece, "refused_value": exc.value,
                "refused_codepoints": exc.codepoints,
                "fields": sorted(printed_strings(patterns, stamp,
                                                 stamp_from))}


def publish(patterns, stamp, stamp_from, render):
    """Run render() only for publishable stamp text, keeping its bytes."""
    guard(patterns, stamp, stamp_from)
    return render()


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def ascii_safe(text):
    """A value carrying a broken codepoint must not crash the console that
    reports it (R2503 lesson: the console re-encodes what it prints)."""
    if text is None:
        return ""
    return str(text).encode("unicode_escape").decode("ascii")


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def render(report_row):
    lines = ["STAMP TEXT COVERAGE %s verdict=%s source=%s pieces=%d"
             % (report_row["tool"], report_row["verdict"],
                report_row["source"], len(report_row["fields"]))]
    if not report_row["publishable"]:
        lines.append("  refused=%s piece=%s value=%s codepoints=%s"
                     % (report_row["code"], report_row["refused_piece"],
                        ascii_safe(report_row["refused_value"]),
                        ",".join(report_row["refused_codepoints"])))
    for field in report_row["fields"]:
        lines.append("  %s" % field)
    return "\n".join(lines)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--patterns", required=True, metavar="JSON",
                        help="suite_matrix_patterns.json (the render inputs)")
    parser.add_argument("--stamp", required=True, metavar="TEXT",
                        help="the generation stamp the render would print")
    parser.add_argument("--stamp-from", default=None, metavar="TEXT",
                        help="the borrowed-stamp source the render would print")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    try:
        document = load(args.patterns)
        before = digest(args.patterns)
    except (OSError, ValueError) as exc:
        print("FAIL patterns: %s %s" % (E_PATTERNS, exc))
        return 3
    try:
        row = reading(document, args.stamp, args.stamp_from)
    except (KeyError, TypeError, AttributeError) as exc:
        print("FAIL patterns: %s incomplete document: %s" % (E_PATTERNS, exc))
        return 3
    except RuntimeError as exc:
        print("FAIL probe: %s" % exc)
        return 3
    if digest(args.patterns) != before:
        print("FAIL patterns: %s source changed under the reading"
              % E_PATTERNS)
        return 3
    if args.json:
        print(json.dumps(row, sort_keys=True))
    else:
        print(render(row))
    return 0 if row["publishable"] else 2


def main_entry():
    argv = sys.argv
    try:
        return main(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 5


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - CLI guard
        sys.stderr.write("%s %s\n" % (E_ARGS, exc))
        sys.exit(5)