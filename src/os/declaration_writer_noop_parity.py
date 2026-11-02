"""declaration_writer_noop_parity - the ONE NOOP question every declaration writer asks (R2389).

R2372 gave the re-pin a NOOP and R2388 taught that comparison the EOL dialect,
but the law reached the re-pin path only. Measured at R2388 by source count, not
assumed: `residue_triage_append.py`, `residue_triage_head_renew.py` and
`residue_triage_entry_retire.py` each hold `is_noop` ZERO times, so each
composes a fresh declaration and writes it through its own atomic replace with
no comparison against the bytes already on disk. Each writes LF, so a second
append that changed one entry silently rewrites a CRLF declaration; a renewal
whose render equals the head it already carries rewrites the same bytes; a
retire by construction shortens, yet the write path never asked.

This module owns that one question and nothing else:

  * the comparison is IMPORTED, never copied - `_law()` asks
    `repin_noop_eol_dialect` at CALL time, so `normalise_bytes` and
    `dialect_of` have exactly one owner and patching it moves every face;
  * `is_noop(path, payload)` answers the question the writers actually ask:
    is the document I am about to write already what is on disk, line endings
    aside? An unreadable file is NOT a NOOP, so the caller walks its own
    shipped refusals exactly as before;
  * `compare(path, payload)` is the same question with its measurements, for
    an operator who wants the reading rather than the verdict;
  * read-only in every path: it writes no byte, reads no clock, imports no
    network, and it is pure ASCII stdlib.

Criteria AC-DWNP1..AC-DWNP6 were pinned inside the R2388 seed row of
state/queue/tech.md BEFORE this code existed.
"""

import json
import os
import sys

PREFIX = "E_DWNP"

SUITE_LABEL = "os-declaration-writer-noop-parity"

VERDICTS = ("NOOP", "PLANNED")

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

EXIT_NOOP = 0
EXIT_PLANNED = 2
EXIT_UNREADABLE = 3
EXIT_BAD_ARGS = 5


class NoopParityError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _law():
    """The shared comparison, imported AT CALL time so it has one owner."""
    import repin_noop_eol_dialect as RNED
    return RNED


def as_bytes(payload):
    """A composition may arrive as str or bytes; the law compares bytes."""
    if isinstance(payload, bytes):
        return payload
    return payload.encode("utf-8")


def normalise(data):
    """The shared normalisation, reached through the shared law."""
    return _law().normalise_bytes(data)


def dialect_of(data):
    """The shared dialect reading."""
    return _law().dialect_of(data)


def is_noop(path, payload):
    """Does the file already carry this composition, line endings aside?

    This is the single seam every declaration writer asks before its atomic
    replace. An unreadable file is not a NOOP: the caller's own refusals then
    decide, which is exactly what happened before this module existed.
    """
    law = _law()
    current = law.read_bytes(path)
    if current is None:
        return False
    return law.normalise_bytes(current) == law.normalise_bytes(as_bytes(payload))


def compare(path, payload):
    """The same question with its measurements; writes nothing."""
    law = _law()
    current = law.read_bytes(path)
    if current is None:
        raise NoopParityError(
            PREFIX + "_UNREADABLE",
            "no readable declaration at %s" % path)
    composed = as_bytes(payload)
    same = law.normalise_bytes(current) == law.normalise_bytes(composed)
    return {
        "verdict": "NOOP" if same else "PLANNED",
        "raw_equal": current == composed,
        "dialect": law.dialect_of(current),
        "composed_dialect": law.dialect_of(composed),
        "declaration_bytes": len(current),
        "composed_bytes": len(composed),
        "normalised_bytes": len(law.normalise_bytes(current)),
    }


def one_line(report):
    """The single line an operator reads."""
    return ("DECLARATION WRITER NOOP verdict=%s dialect=%s composed=%s "
            "raw_equal=%s bytes=%d->%d normalised=%d"
            % (report["verdict"], report["dialect"],
               report["composed_dialect"],
               "yes" if report["raw_equal"] else "no",
               report["declaration_bytes"], report["composed_bytes"],
               report["normalised_bytes"]))


def render(report):
    """The one line, then the one fact it leaves out."""
    out = [one_line(report)]
    if report["verdict"] == "NOOP" and not report["raw_equal"]:
        out.append("  REASON the content matches; only the line endings "
                   "differ (%s vs %s), so nothing is written and the file "
                   "keeps its dialect"
                   % (report["dialect"], report["composed_dialect"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (byte-stable)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: declaration_writer_noop_parity.py --compare DECLARATION "
         "--composed FILE [--json]\n"
         "  exit 0 = NOOP (the file already carries the composition, line "
         "endings aside)\n"
         "  exit 2 = PLANNED (the content differs, so a writer would write)\n"
         "  exit 3 = a file is missing or unreadable\n"
         "  exit 5 = bad flags\n")


def _read(path):
    data = _law().read_bytes(path)
    if data is None:
        raise NoopParityError(PREFIX + "_UNREADABLE",
                              "no readable file at %s" % path)
    return data


def main(argv):
    as_json = False
    declaration = None
    composed = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--json":
            as_json = True
        elif arg in ("--compare", "--composed"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("%s_BAD_ARGS: %s needs a value\n"
                                 % (PREFIX, arg))
                sys.stdout.write(USAGE)
                return EXIT_BAD_ARGS
            if arg == "--compare":
                declaration = argv[index]
            else:
                composed = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return EXIT_NOOP
        else:
            sys.stdout.write("%s_BAD_ARGS: unknown flag %s\n"
                             % (PREFIX, arg))
            sys.stdout.write(USAGE)
            return EXIT_BAD_ARGS
        index += 1
    if declaration is None or composed is None:
        sys.stdout.write("%s_BAD_ARGS: --compare and --composed are both "
                         "required\n" % PREFIX)
        sys.stdout.write(USAGE)
        return EXIT_BAD_ARGS
    try:
        report = compare(declaration, _read(composed))
    except NoopParityError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        return EXIT_UNREADABLE
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return EXIT_NOOP if report["verdict"] == "NOOP" else EXIT_PLANNED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))