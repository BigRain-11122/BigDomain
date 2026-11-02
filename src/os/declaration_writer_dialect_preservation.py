# declaration_writer_dialect_preservation.py - a changed declaration keeps its
# own line-ending dialect instead of being converted by the transport.
# Criteria AC-DWPP1..AC-DWPP6 were pre-registered inside the R2389 seed row of
# state/queue/tech.md BEFORE this file existed.
#
# Why this exists: R2388/R2389 closed the POINTLESS write (a document that
# already carried the composition was rewritten). The REAL write was left
# alone, and it is worse: measured at R2389 in the source,
# residue_triage_append.compose builds its entry with hard-coded "\n" and
# apply encodes the whole document as UTF-8, so a genuine append to a CRLF
# declaration silently converts EVERY line of the file. head renew and entry
# retire carry the same shape, and so does the batch append.
#
# This module owns exactly one question:
#
#   given the bytes the declaration carries NOW and the composed text a writer
#   wants to land, what bytes must be written so the declaration keeps its own
#   dialect and every line the writer did not touch stays byte-identical?
#
# The dialect itself is NOT re-invented here: it is asked of the shared law
# (repin_noop_eol_dialect.dialect_of) at CALL time, so a patched reading moves
# every writer that asks this seam (AC-DWPP5).
#
#   * LF (and an EMPTY file)  -> today's bytes exactly, byte for byte
#     (AC-DWPP2), so nothing already correct moves;
#   * CRLF -> the composed text re-rendered with CRLF, so an append to a CRLF
#     declaration lands and the result still reads CRLF (AC-DWPP1);
#   * CR -> the same shape over a lone-CR file;
#   * MIXED -> REFUSE (E_DWPP_MIXED) rather than silently normalising a file
#     whose dialect no writer could preserve; the writer's own refusals then
#     stand, so no refusal code, exit code or printed line of an existing
#     writer changes (AC-DWPP4).
#
# residue_triage_repin is deliberately OUT of scope: it re-renders the whole
# document from the live reading rather than splicing it, so "every untouched
# line stays byte-identical" is not a property it can have.
#
# Pure apart from nothing at all: it writes nothing, reads no clock, imports
# no network, and it is pure ASCII stdlib (AC-DWPP6).

import repin_noop_eol_dialect as RNP

PREFIX = "E_DWPP"

SUITE_LABEL = "os-declaration-writer-dialect-preservation"

# the dialects a writer can preserve; anything else refuses
PRESERVABLE = ("EMPTY", "LF", "CRLF", "CR")

REPORT_KEYS = (
    "dialect",
    "composed_bytes",
    "payload_bytes",
    "preserved",
)


class DialectError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def dialect(raw_bytes):
    """The declaration's own dialect, asked of the SHARED law (AC-DWPP5)."""
    return RNP.dialect_of(raw_bytes)


def _canonical(text):
    """The composed text with LF line endings, asked of the SHARED law.

    A writer splices into universal-newline text, but a caller that composed
    from raw bytes can still hand over CRLF beside its own LF. Normalising
    first makes the re-render below idempotent instead of turning CRLF into
    CRCRLF. This is the dialect law's own normalisation, not a second copy.
    """
    return RNP.normalise_text(text)


def encode(raw_bytes, composed_text):
    """The bytes to write, rendered in the declaration's own dialect.

    `composed_text` is the writer's composition, exactly what every writer
    produced before this module existed. An LF declaration therefore gets the
    SAME bytes as before (AC-DWPP2); a CRLF declaration gets its own transport
    back (AC-DWPP1); a dialect no writer can preserve is refused instead of
    converted (AC-DWPP4).
    """
    name = dialect(raw_bytes)
    canon = _canonical(composed_text)
    if name in ("EMPTY", "LF"):
        payload = canon.encode("utf-8")
    elif name == "CRLF":
        payload = canon.replace("\n", "\r\n").encode("utf-8")
    elif name == "CR":
        payload = canon.replace("\n", "\r").encode("utf-8")
    else:
        raise DialectError(
            PREFIX + "_MIXED",
            "the declaration carries mixed line endings (%s), so a write "
            "would have to choose a transport for lines it was not asked "
            "about" % name)
    return name, payload


def report(raw_bytes, composed_text):
    """The reading behind the answer, without writing anything."""
    name = dialect(raw_bytes)
    canon = _canonical(composed_text)
    composed = canon.encode("utf-8")
    if name in ("EMPTY", "LF"):
        payload = composed
    elif name == "CRLF":
        payload = canon.replace("\n", "\r\n").encode("utf-8")
    elif name == "CR":
        payload = canon.replace("\n", "\r").encode("utf-8")
    else:
        payload = None
    return {
        "dialect": name,
        "composed_bytes": len(composed),
        "payload_bytes": None if payload is None else len(payload),
        "preserved": payload is not None,
    }


def one_line(reading):
    """The single line an operator reads."""
    return ("DECLARATION DIALECT dialect=%s composed=%d payload=%s "
            "preserved=%s"
            % (reading["dialect"], reading["composed_bytes"],
               "-" if reading["payload_bytes"] is None
               else str(reading["payload_bytes"]),
               "yes" if reading["preserved"] else "no"))


def render(reading):
    """The one line, then the one fact it leaves out."""
    out = [one_line(reading)]
    if not reading["preserved"]:
        out.append("  REFUSED %s_MIXED: a writer will not pick a transport "
                   "for lines it was not asked about" % PREFIX)
    elif reading["payload_bytes"] != reading["composed_bytes"]:
        out.append("  NOTE the payload is not the LF composition: the "
                   "declaration's own dialect is re-applied")
    return "\n".join(out)


USAGE = ("usage: declaration_writer_dialect_preservation.py "
         "--declaration FILE --composed FILE [--json]\n"
         "  exit 0 = the dialect can be preserved (payload bytes printed)\n"
         "  exit 2 = the dialect is MIXED, so a writer would refuse\n"
         "  exit 3 = a file is missing or unreadable\n"
         "  exit 5 = bad flags\n")


def _read(path):
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except (IOError, OSError) as exc:
        raise DialectError(PREFIX + "_UNREADABLE", "%s: %s" % (path, exc))


def main(argv):
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
                import sys
                sys.stdout.write("%s_BAD_ARGS: %s needs a value\n"
                                 % (PREFIX, arg))
                sys.stdout.write(USAGE)
                return 5
            if arg == "--declaration":
                declaration = argv[index]
            else:
                composed = argv[index]
        elif arg in ("--help", "-h"):
            import sys
            sys.stdout.write(USAGE)
            return 0
        else:
            import sys
            sys.stdout.write("%s_BAD_ARGS: unknown flag %s\n" % (PREFIX, arg))
            sys.stdout.write(USAGE)
            return 5
        index += 1
    import sys
    if declaration is None or composed is None:
        sys.stdout.write("%s_BAD_ARGS: --declaration and --composed are "
                         "both required\n" % PREFIX)
        sys.stdout.write(USAGE)
        return 5
    try:
        raw = _read(declaration)
        text_bytes = _read(composed)
        try:
            composed_text = text_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DialectError(PREFIX + "_UNREADABLE", str(exc))
        reading = report(raw, composed_text)
    except DialectError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        return 3
    if as_json:
        import json
        ordered = {}
        for key in REPORT_KEYS:
            ordered[key] = reading[key]
        sys.stdout.write(json.dumps(ordered, ensure_ascii=True,
                                    sort_keys=False) + "\n")
    else:
        sys.stdout.write(render(reading) + "\n")
    return 0 if reading["preserved"] else 2


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))