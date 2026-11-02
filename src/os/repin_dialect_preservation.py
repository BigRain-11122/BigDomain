"""repin_dialect_preservation - the RE-RENDER writer keeps the dialect too
(R2406).

R2398 closed the transport question for the four SPLICE writers: an append, a
batch, a head renewal and a retirement keep the declaration's own line
endings. `residue_triage_repin` was deliberately left out of that window
because it is a RE-RENDER rather than a splice, so "every untouched line stays
byte-identical" is not a property it can have.

It still writes LF wholesale: measured at HEAD in its own source, `build`
composes `json.dumps(...) + "\n"` and `plan` writes the text with
`newline="\n"` and `encoding="utf-8"`. Re-pinning a CRLF declaration therefore
converts every line of it to LF - the whole document's transport chosen by
whichever writer happened to run, which is exactly the defect R2398 named.

This module owns one question and asks the shipped law for the answer:

  * `resolve(raw_bytes, composed_text)` returns the dialect name and the
    BYTES a re-render must land. It asks
    `declaration_writer_dialect_preservation.encode` at CALL time, so the
    dialect is still `repin_noop_eol_dialect.dialect_of`'s answer and a
    patched reading moves this writer too (AC-RDPL5). There is no second
    dialect table here.
  * an LF declaration gets today's bytes exactly (AC-RDPL2), a CRLF
    declaration is re-rendered as CRLF so the re-pin lands and the file still
    reads CRLF with no lone LF (AC-RDPL1), and a MIXED declaration REFUSES
    (`E_RDPL_MIXED`) rather than having one transport chosen for lines nobody
    asked about.
  * the NOOP path stays ahead of the writer and writes nothing (AC-RDPL3):
    `residue_triage_repin.plan` still asks `repin_noop_parity.is_noop` first,
    so an identical composition creates no temp file.
  * every refusal code, exit code and printed line the re-pin CLI already had
    is unchanged (AC-RDPL4): this module adds the MIXED refusal and moves no
    other line, and it is proved against the HEAD module's own captured
    refusal rather than asserted.

`residue_triage_repin` keeps its ONE atomic replace and its temp name; it now
writes the PAYLOAD this module derives, in BINARY mode, so no text handle can
translate the transport back. This module owns no writer of its own, which is
what the shipped "one writer" criterion (AC-RNP5) requires.

Read-only otherwise: no clock, no network, pure ASCII stdlib (AC-RDPL6).

Criteria AC-RDPL1..AC-RDPL6 were pre-registered inside the R2398 seed row of
state/queue/tech.md (line 478) BEFORE this code existed.
"""

import declaration_writer_dialect_preservation as DWDP

PREFIX = "E_RDPL"

SUITE_LABEL = "os-repin-dialect-preservation"

REPORT_KEYS = (
    "dialect",
    "composed_bytes",
    "payload_bytes",
    "preserved",
)


class RepinDialectError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def read_bytes(path):
    """The declaration's bytes, or b"" when there is no file there yet.

    A re-pin always runs over an existing declaration (its own build refuses
    UNPINNED), so an absent path is the EMPTY dialect and composes to the
    same UTF-8 bytes the writer produced before this module existed.
    """
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except (IOError, OSError):
        return b""


def resolve(raw_bytes, composed_text):
    """Ask the shipped law what bytes a re-render must land (AC-RDPL5).

    The answer is `declaration_writer_dialect_preservation.encode`'s, taken at
    CALL time; its own MIXED refusal is re-raised under this module's prefix
    so a caller sees which writer refused, and the detail still names the
    measured dialect.
    """
    try:
        return DWDP.encode(raw_bytes, composed_text)
    except DWDP.DialectError as exc:
        raise RepinDialectError(
            PREFIX + "_MIXED",
            "the declaration carries mixed line endings, so a re-render "
            "would have to choose a transport for lines nobody asked about "
            "(%s)" % exc.detail)


def payload_for(path, composed_text):
    """Read the declaration and answer for that file, without writing."""
    return resolve(read_bytes(path), composed_text)


def report(path, composed_text):
    """The reading behind the answer, without writing anything."""
    raw = read_bytes(path)
    try:
        return DWDP.report(raw, composed_text)
    except DWDP.DialectError as exc:
        raise RepinDialectError(PREFIX + "_MIXED", exc.detail)


def one_line(reading):
    """The single line an operator reads."""
    return ("REPIN DIALECT dialect=%s composed=%d payload=%s preserved=%s"
            % (reading["dialect"], reading["composed_bytes"],
               "-" if reading["payload_bytes"] is None
               else str(reading["payload_bytes"]),
               "yes" if reading["preserved"] else "no"))


def render(reading):
    """The one line, then the one fact it leaves out."""
    out = [one_line(reading)]
    if not reading["preserved"]:
        out.append("  REFUSED %s_MIXED: a re-render will not pick a "
                   "transport for lines it was not asked about" % PREFIX)
    elif reading["payload_bytes"] != reading["composed_bytes"]:
        out.append("  NOTE the payload is not the LF composition: the "
                   "declaration's own dialect is re-applied")
    return "\n".join(out)


def to_json(reading):
    """Serialise in the pinned key order only."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = reading[key]
    import json
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: repin_dialect_preservation.py --declaration FILE "
         "--composed FILE [--json]\n"
         "  exit 0 = the dialect can be preserved (payload bytes printed)\n"
         "  exit 2 = the dialect is MIXED, so a re-render would refuse\n"
         "  exit 3 = a file is missing or unreadable\n"
         "  exit 5 = bad flags\n")


def _read_required(path):
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except (IOError, OSError) as exc:
        raise RepinDialectError(PREFIX + "_UNREADABLE",
                                "%s: %s" % (path, exc))


def main(argv):
    import sys
    as_json = False
    declaration = None
    composed = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--json":
            as_json = True
        elif arg in ("--declaration", "--composed"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("%s_BAD_ARGS: %s needs a value\n"
                                 % (PREFIX, arg))
                sys.stdout.write(USAGE)
                return 5
            if arg == "--declaration":
                declaration = argv[index]
            else:
                composed = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("%s_BAD_ARGS: unknown flag %s\n" % (PREFIX, arg))
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if declaration is None or composed is None:
        sys.stdout.write("%s_BAD_ARGS: --declaration and --composed are "
                         "both required\n" % PREFIX)
        sys.stdout.write(USAGE)
        return 5
    try:
        composed_bytes = _read_required(composed)
        try:
            composed_text = composed_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RepinDialectError(PREFIX + "_UNREADABLE", str(exc))
        raw = _read_required(declaration)
        reading = report(declaration, composed_text)
        name, payload = resolve(raw, composed_text)
    except RepinDialectError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        return 2 if exc.code == PREFIX + "_MIXED" else 3
    if as_json:
        sys.stdout.write(to_json(reading))
    else:
        sys.stdout.write(render(reading) + "\n")
    if reading["payload_bytes"] is None:
        return 2
    return 0 if name is not None else 2


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))