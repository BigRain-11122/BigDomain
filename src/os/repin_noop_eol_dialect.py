"""repin_noop_eol_dialect - the NOOP comparison owns the EOL dialect (R2388).

`repin_noop_parity.is_noop` compares the composed document's BYTES with the
file's bytes. That is right about content and wrong about transport: a
declaration whose text is exactly the composition but whose line endings are
CRLF reads PLANNED, and `--execute` then rewrites it to LF as PINNED. The
round that seeded this row measured the shape on a throwaway world (27 CRLF
pairs): dry=PLANNED, execute=PINNED, the file rewritten with crlf 27 -> 0. A
semantically identical declaration was written where nothing needed writing,
and no reader could tell that rewrite from a real re-pin.

This module owns the EOL dialect and nothing else:

  * ONE normalisation lives here (`normalise_bytes`): CRLF and a lone CR
    become LF, and only line endings are touched, so a document that differs
    in CONTENT still differs after normalisation;
  * `is_noop(path, text)` reads the declaration and answers the one question
    the two writer faces ask - is the composed document already what is on
    disk, line endings aside - so a CRLF declaration that carries the
    composition reads NOOP and no byte is written;
  * `repin_noop_parity.is_noop` and
    `residue_triage_repin_idempotent.decide` both call this module AT CALL
    TIME, so a patched normaliser moves both faces and there is no second
    copy of the law to drift;
  * `dialect_of` names what the file actually carries (LF, CRLF, CR, MIXED,
    EMPTY) so an operator can see the reading rather than infer it.

Read-only in every path: it writes nothing, reads no clock, imports no
network, and it is pure ASCII stdlib. Criteria AC-RNED1..AC-RNED6 were pinned
inside the R2382 seed row of state/queue/tech.md BEFORE this code existed.
"""

import json
import os
import sys

PREFIX = "E_RNED"

# the comparison's report carries these keys in this order and nothing else
REPORT_KEYS = (
    "verdict",
    "raw_equal",
    "dialect",
    "composed_dialect",
    "declaration_bytes",
    "composed_bytes",
    "normalised_bytes",
)

VERDICTS = ("NOOP", "PLANNED")

DIALECTS = ("EMPTY", "LF", "CRLF", "CR", "MIXED")


class DialectError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def normalise_bytes(data):
    """The ONE normalisation law: line endings only, CRLF and CR to LF.

    Content is never touched: no strip, no decode, no re-encode. A document
    that differs in any byte other than a line ending still differs here.
    """
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def normalise_text(text):
    """The same law over text, for callers holding a str rather than bytes."""
    return normalise_bytes(text.encode("utf-8")).decode("utf-8")


def dialect_of(data):
    """Name the line-ending dialect the bytes actually carry."""
    if not data:
        return "EMPTY"
    pairs = data.count(b"\r\n")
    cr = data.count(b"\r")
    lf = data.count(b"\n")
    lone_cr = cr - pairs
    lone_lf = lf - pairs
    if pairs and not lone_cr and not lone_lf:
        return "CRLF"
    if lone_cr and not pairs and not lone_lf:
        return "CR"
    if lone_lf and not pairs and not lone_cr:
        return "LF"
    if not pairs and not cr and not lf:
        return "LF"
    return "MIXED"


def read_bytes(path):
    """The file's bytes, or None when there is no readable file there."""
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except (IOError, OSError):
        return None


def is_noop(path, text):
    """Does the declaration already carry the composition, EOL aside?

    An unreadable file is not a NOOP - the caller then walks the shipped
    writer and its own refusals decide, exactly as before.
    """
    current = read_bytes(path)
    if current is None:
        return False
    return normalise_bytes(current) == normalise_bytes(text.encode("utf-8"))


def compare(declaration_path, composed_text):
    """Measure both faces of the question without writing anything."""
    current = read_bytes(declaration_path)
    if current is None:
        raise DialectError(
            PREFIX + "_UNREADABLE",
            "no readable declaration at %s" % declaration_path)
    composed = composed_text.encode("utf-8")
    same = normalise_bytes(current) == normalise_bytes(composed)
    return {
        "verdict": "NOOP" if same else "PLANNED",
        "raw_equal": current == composed,
        "dialect": dialect_of(current),
        "composed_dialect": dialect_of(composed),
        "declaration_bytes": len(current),
        "composed_bytes": len(composed),
        "normalised_bytes": len(normalise_bytes(current)),
    }


def one_line(report):
    """The single line an operator reads."""
    return ("EOL NOOP COMPARE verdict=%s dialect=%s composed=%s "
            "raw_equal=%s bytes=%d->%d normalised=%d"
            % (report["verdict"], report["dialect"],
               report["composed_dialect"],
               "yes" if report["raw_equal"] else "no",
               report["declaration_bytes"], report["composed_bytes"],
               report["normalised_bytes"]))


def render(report):
    """The one line, then the one fact it leaves out."""
    if report.get("_dialect_only"):
        out = ["EOL DIALECT dialect=%s bytes=%d normalised=%d"
               % (report["dialect"], report["declaration_bytes"],
                  report["normalised_bytes"])]
        return "\n".join(out)
    out = [one_line(report)]
    if report["verdict"] == "NOOP" and not report["raw_equal"]:
        out.append("  REASON the content matches; only the line endings "
                   "differ (%s vs %s), so nothing is written and the file "
                   "keeps its dialect" % (report["dialect"],
                                          report["composed_dialect"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: repin_noop_eol_dialect.py --compare DECLARATION "
         "--composed FILE [--json]\n"
         "       repin_noop_eol_dialect.py --dialect FILE [--json]\n"
         "  exit 0 = NOOP (the file already carries the composition, line "
         "endings aside) or a dialect reading\n"
         "  exit 2 = PLANNED (the content differs, so a writer would write)\n"
         "  exit 3 = a file is missing or unreadable\n"
         "  exit 5 = bad flags\n")


def _dialect_report(path):
    data = read_bytes(path)
    if data is None:
        raise DialectError(PREFIX + "_UNREADABLE",
                           "no readable file at %s" % path)
    return {"verdict": dialect_of(data), "raw_equal": True,
            "dialect": dialect_of(data),
            "composed_dialect": dialect_of(data),
            "declaration_bytes": len(data), "composed_bytes": len(data),
            "normalised_bytes": len(normalise_bytes(data)),
            "_dialect_only": True}


def main(argv):
    as_json = False
    mode = None
    declaration = None
    composed = None
    dialect_file = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--json":
            as_json = True
        elif arg in ("--compare", "--composed", "--dialect"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("%s_BAD_ARGS: %s needs a value\n"
                                 % (PREFIX, arg))
                sys.stdout.write(USAGE)
                return 5
            if arg == "--compare":
                mode = "compare"
                declaration = argv[index]
            elif arg == "--composed":
                composed = argv[index]
            else:
                mode = "dialect"
                dialect_file = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("%s_BAD_ARGS: unknown flag %s\n"
                             % (PREFIX, arg))
            sys.stdout.write(USAGE)
            return 5
        index += 1
    try:
        if mode == "dialect" and dialect_file is not None:
            report = _dialect_report(dialect_file)
        elif mode == "compare" and declaration is not None:
            if composed is None:
                sys.stdout.write("%s_BAD_ARGS: --composed is required with "
                                 "--compare\n" % PREFIX)
                sys.stdout.write(USAGE)
                return 5
            text = read_bytes(composed)
            if text is None:
                raise DialectError(PREFIX + "_UNREADABLE",
                                   "no readable composition at %s" % composed)
            report = compare(declaration, text.decode("utf-8"))
        else:
            sys.stdout.write("%s_BAD_ARGS: --compare or --dialect is "
                             "required\n" % PREFIX)
            sys.stdout.write(USAGE)
            return 5
    except DialectError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if mode == "dialect":
        return 0
    return 0 if report["verdict"] == "NOOP" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))