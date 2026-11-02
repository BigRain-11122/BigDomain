# residue_triage_entry_retire.py - remove an entry only when the live reading
# proves its round is gone.
# Criteria AC-RTER1..AC-RTER6 were pre-registered inside the R2351 seed row of
# state/queue/tech.md BEFORE this file existed.
#
# Why this exists: the declaration has a writer for NEW entries
# (residue_triage_append) and a writer for the HEAD
# (residue_triage_head_renew), but nothing can RETIRE one. R2342 was declared
# at its live status and its round then left the live residue table, so the
# entry reads UNMATCHED forever and only a hand edit could remove it - the
# head keeps speaking for a round that no longer exists, and the triage
# reading keeps carrying the same single unmatched entry.
#
# This module is the missing operation, and nothing else:
#   * the entry set is read by residue_triage own loader and the live residue
#     by its own live reading (AC-RTER1): a patched loader or a patched live
#     reading moves the plan, and there is no second declaration reader here;
#   * the dry run is the default - the plan names EVERY unmatched round, the
#     entry count before and after and the predicted byte count, and no byte
#     is written without --execute (AC-RTER2);
#   * an entry whose round the live reading still carries is REFUSED with its
#     round named, so this writer can never retire a live round (AC-RTER3);
#   * the executed retire is ONE atomic text splice that removes exactly the
#     retired entry object and one adjacent separator, leaving every surviving
#     entry and the head byte-identical, proving the predicted post size
#     against the write and leaving no temp residue (AC-RTER4);
#   * exits 0 planned or retired, 2 refused over live state, 3 unreadable or
#     missing declaration, 5 bad flags, with a byte-stable --json over the
#     pinned keys in the pinned order (AC-RTER5);
#   * pure ASCII source, stdlib only, zero network, no clock of its own (the
#     round is an argument), and the only delete call is the removal of this
#     module's own temp file on a failed replace (AC-RTER6).
#
# The splice is SPAN based, not render based, on purpose: the live declaration
# carries two entry layouts (compact one-line objects written by an earlier
# dumper and the expanded multi-line blocks written by the append writer), so
# re-rendering an entry to find it would silently miss half the file.
#
# Pure apart from one atomic replace under --execute; no clock, no network.

import json
import os
import sys

import residue_triage as RT

DECLARATION_PATH = RT.DECLARATION_PATH

SUITE_LABEL = "os-residue-triage-entry-retire"

REPORT_KEYS = (
    "action",
    "round",
    "status",
    "entries_before",
    "entries_after",
    "unmatched",
    "before_bytes",
    "after_bytes",
    "delta",
    "declaration",
    "verdict",
    "wrote",
)

UNREADABLE_CODES = (
    "E_RTER_UNPINNED",
    "E_RTER_UNREADABLE",
    "E_RTER_BAD_SPAN",
    "E_RTER_READBACK",
)


class EntryRetireError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _round(value, origin):
    """One round reference, parsed by the reader's own law (AC-RTER1)."""
    try:
        return RT.parse_round(value, origin)
    except RT.ResidueTriageError as exc:
        raise EntryRetireError(
            "E_RTER_BAD_ARGS", "%s: %s" % (origin, exc.detail or exc.code))


def _declaration(root):
    """The pinned declaration, read by residue_triage (AC-RTER1)."""
    try:
        declaration = RT.load_declaration(root)
    except RT.ResidueTriageError as exc:
        raise EntryRetireError(
            "E_RTER_UNREADABLE", "%s: %s" % (exc.code, exc.detail))
    if declaration is None:
        raise EntryRetireError(
            "E_RTER_UNPINNED",
            "no %s to retire from" % DECLARATION_PATH.replace(os.sep, "/"))
    return declaration


def _live(root):
    """The live residue rounds, read by stamp_residue through residue_triage."""
    try:
        rows = RT.live_residue(root)
    except RT.ResidueTriageError as exc:
        raise EntryRetireError(
            "E_RTER_UNREADABLE", "%s: %s" % (exc.code, exc.detail))
    return set(int(row["round"]) for row in rows)


def _unmatched(declaration, live):
    """Every declared round the live reading no longer carries, in file order."""
    return [entry["round"] for entry in declaration["entries"]
            if entry["round"] not in live]


def _spans(text):
    """Character spans of every object inside the top-level entries array.

    Brace counting that ignores braces inside strings, so a reason sentence
    carrying a brace cannot move a boundary.
    """
    marker = text.find('"entries"')
    if marker < 0:
        raise EntryRetireError(
            "E_RTER_BAD_SPAN", "the declaration has no entries key in text")
    bracket = text.find("[", marker)
    if bracket < 0:
        raise EntryRetireError(
            "E_RTER_BAD_SPAN", "the entries key opens no array")
    spans = []
    depth = 0
    in_string = False
    escaped = False
    opened = None
    index = bracket + 1
    while index < len(text):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                opened = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                raise EntryRetireError(
                    "E_RTER_BAD_SPAN", "unbalanced braces in the entries")
            if depth == 0:
                spans.append((opened, index + 1))
        elif char == "]" and depth == 0:
            return spans
        index += 1
    raise EntryRetireError(
        "E_RTER_BAD_SPAN", "the entries array never closes")


def _cut(text, spans, position):
    """Remove one object span plus exactly one adjacent separator."""
    start, end = spans[position]
    if position > 0:
        return text[:spans[position - 1][1]] + text[end:]
    if len(spans) > 1:
        return text[:start] + text[spans[1][0]:]
    head = text[:start].rstrip()
    tail = text[end:].lstrip()
    return head + "\n    " + tail if tail else head


def plan(root, round_text, execute=False):
    """Everything except the write: refusals, splice, predicted bytes."""
    number = _round(round_text, "retire round")
    declaration = _declaration(root)
    live = _live(root)
    unmatched = _unmatched(declaration, live)

    found = None
    position = None
    for index, entry in enumerate(declaration["entries"]):
        if entry["round"] == number:
            found = entry
            position = index
    if found is None:
        raise EntryRetireError(
            "E_RTER_NOT_DECLARED",
            "R%d carries no entry (%d entries are declared)"
            % (number, len(declaration["entries"])))
    if number in live:
        raise EntryRetireError(
            "E_RTER_LIVE",
            "R%d is still in the live residue, so it cannot be retired"
            % number)

    path = os.path.join(root, DECLARATION_PATH)
    try:
        with open(path, "rb") as handle:
            raw_bytes = handle.read()
    except (IOError, OSError) as exc:
        raise EntryRetireError("E_RTER_UNREADABLE", str(exc))
    try:
        before_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EntryRetireError("E_RTER_UNREADABLE", str(exc))

    spans = _spans(before_text)
    if len(spans) != len(declaration["entries"]):
        raise EntryRetireError(
            "E_RTER_BAD_SPAN",
            "the text carries %d entry objects against %d declared entries"
            % (len(spans), len(declaration["entries"])))
    after_text = _cut(before_text, spans, position)
    after_bytes = after_text.encode("utf-8")

    survivors = [entry for entry in declaration["entries"]
                 if entry["round"] != number]
    kept = [before_text[start:end] for start, end in spans]
    kept = kept[:position] + kept[position + 1:]
    if not all(block in after_text for block in kept):
        raise EntryRetireError(
            "E_RTER_BAD_SPAN",
            "a surviving entry block is not byte-identical after the splice")

    prepared = {
        "path": path,
        "round": number,
        "status": found["status"],
        "before_text": before_text,
        "before_bytes": len(raw_bytes),
        "after_text": after_text,
        "after_bytes": after_bytes,
        "delta": len(after_bytes) - len(raw_bytes),
        "entries_before": len(declaration["entries"]),
        "entries_after": len(declaration["entries"]) - 1,
        "survivors": survivors,
        "unmatched": unmatched,
        "declared_by": declaration["declared_by"],
        "reason": declaration["reason"],
        "executed": False,
    }
    if not execute:
        return prepared

    temp = path + ".tmp-rter"
    import declaration_writer_noop_parity as DWNP
    if DWNP.is_noop(path, after_bytes):
        prepared["noop"] = True
        return prepared
    try:
        with open(temp, "wb") as handle:
            handle.write(after_bytes)
        os.replace(temp, path)
    except (IOError, OSError) as exc:
        try:
            os.remove(temp)
        except (IOError, OSError):
            pass
        raise EntryRetireError("E_RTER_READBACK", str(exc))
    try:
        size = os.path.getsize(path)
    except (IOError, OSError) as exc:
        raise EntryRetireError("E_RTER_READBACK", str(exc))
    if size != len(after_bytes):
        raise EntryRetireError(
            "E_RTER_READBACK",
            "predicted %d bytes, the file measures %d"
            % (len(after_bytes), size))

    reread = _declaration(root)
    if reread["entries"] != survivors:
        raise EntryRetireError(
            "E_RTER_READBACK",
            "the surviving entries do not re-read as declared")
    if (reread["declared_by"] != declaration["declared_by"]
            or reread["reason"] != declaration["reason"]):
        raise EntryRetireError(
            "E_RTER_READBACK", "the head moved during the splice")
    prepared["executed"] = True
    return prepared


def report(prepared):
    """The pinned report shape, headed by the action that produced it."""
    if prepared.get("noop"):
        verdict = "NOOP"
    elif prepared["executed"]:
        verdict = "RETIRED"
    else:
        verdict = "PLANNED"
    return {
        "action": "retire" if prepared["executed"] else "plan",
        "round": "R%d" % prepared["round"],
        "status": prepared["status"],
        "entries_before": prepared["entries_before"],
        "entries_after": prepared["entries_after"],
        "unmatched": ["R%d" % value for value in prepared["unmatched"]],
        "before_bytes": prepared["before_bytes"],
        "after_bytes": prepared["before_bytes"] + prepared["delta"],
        "delta": prepared["delta"],
        "declaration": "PINNED",
        "verdict": verdict,
        "wrote": prepared["executed"],
    }


def one_line(item):
    """The single line an operator reads."""
    unmatched = ",".join(item["unmatched"]) or "-"
    return ("RESIDUE TRIAGE ENTRY RETIRE action=%s round=%s status=%s "
            "entries=%d->%d bytes=%d->%d delta=%d unmatched=%s "
            "declaration=%s verdict=%s wrote=%s"
            % (item["action"], item["round"], item["status"],
               item["entries_before"], item["entries_after"],
               item["before_bytes"], item["after_bytes"], item["delta"],
               unmatched, item["declaration"], item["verdict"],
               "yes" if item["wrote"] else "no"))


def render(item):
    """The one line, then every round still unmatched in this declaration."""
    out = [one_line(item)]
    for value in item["unmatched"]:
        out.append("  UNMATCHED %s has no live residue round" % value)
    return "\n".join(out)


def to_json(item):
    """Serialise in the pinned key order only (byte-stable)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = item[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: residue_triage_entry_retire.py --round R<n>\n"
         "         [--execute] [--root PATH] [--json]\n"
         "  the dry run is the default: nothing is written without --execute\n"
         "  exit 0 = PLANNED or RETIRED\n"
         "  exit 2 = refused over live state (still in the live residue, or\n"
         "           no such entry)\n"
         "  exit 3 = unreadable or missing declaration, bad span, readback\n"
         "  exit 5 = bad flags\n")


def main(argv):
    round_text = None
    execute = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--execute":
            execute = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--round", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RTER_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            if arg == "--round":
                round_text = argv[index]
            else:
                root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RTER_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1

    if round_text is None:
        sys.stdout.write("E_RTER_BAD_ARGS: --round is required\n")
        sys.stdout.write(USAGE)
        return 5

    try:
        item = report(plan(root, round_text, execute))
    except EntryRetireError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code == "E_RTER_BAD_ARGS":
            return 5
        if exc.code in UNREADABLE_CODES:
            return 3
        return 2

    if as_json:
        sys.stdout.write(to_json(item))
    else:
        sys.stdout.write(render(item) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))