# debt_note_append.py - grow ONE note segment on an open register row
# Criteria AC-DRNA1..AC-DRNA6 were pre-registered in state/queue/tech.md
# (R2600 seed) BEFORE this file existed.
#
# Why this exists: R2598 and R2599 both appended their text at the END of
# the row they were annotating. When the row's last segment was
# `first=yes`, the appended text landed INSIDE that field, so
# `first` read "yes ; note_...: ..." and debt_register.parse refused the
# whole file - debt_gate.py answered exit 3 (E_DR_BAD_FIRST) for every
# round, i.e. the register that ranks work became unreadable and neither
# helper ever asked the shipped parser. This module grows the note field
# and re-emits every other key where it was; it refuses when the composed
# row would not parse.
#
# Refusals, all before any write:
#   E_DRNA_MISSING   register not found / unreadable
#   E_DRNA_NO_ROW    the item is not on the register
#   E_DRNA_DUP_ROW   the item is carried by more than one row
#   E_DRNA_NOT_OPEN  the row is closed
#   E_DRNA_MARKER    the marker is already present
#   E_DRNA_SHAPE     the row is not the pipe-separated shape with a
#                    trailing scalar `first=`
#   E_DRNA_BAD_FIELD the marker or text carries '|', '=' or a newline
#   E_DRNA_POST      the composed row does not parse through the shipped law
#
# Dry run by default: plan() predicts the post bytes and writes nothing.
# execute=True performs ONE atomic replace and proves the read-back bytes
# equal what was written.
#
# Stdlib only, pure ASCII source, zero network, no clock read.

import io
import os
import sys

import debt_register as DR

REGISTER_REL = DR.REGISTER_REL
SEGMENT_SEP = " | "
NOTE_KEY = "note="
TEMP_SUFFIX = ".drna-tmp"

REPORT_KEYS = (
    "path",
    "item",
    "marker",
    "row_line",
    "note_grew",
    "first_kept",
    "before_bytes",
    "predicted_bytes",
    "wrote",
    "read_back_ok",
)


class DebtNoteError(Exception):
    """Raised when a note cannot be grown without guessing."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _clean(label, value):
    for bad in ("|", "=", "\n", "\r"):
        if bad in value:
            raise DebtNoteError(
                "E_DRNA_BAD_FIELD",
                "%s cannot carry %r: %r" % (label, bad, value))
    if not value.strip():
        raise DebtNoteError("E_DRNA_BAD_FIELD", "%s is empty" % label)


def _segments(body):
    """Pipe-split one row body, refusing a segment without a known key."""
    parts = body.split(SEGMENT_SEP)
    for part in parts:
        if "=" not in part:
            raise DebtNoteError(
                "E_DRNA_SHAPE", "segment carries no key: %r" % part[:40])
        key = part.split("=", 1)[0]
        if key not in DR.ALLOWED_KEYS:
            raise DebtNoteError(
                "E_DRNA_SHAPE", "unknown key %r in row" % key)
    return parts


def plan(text, item, marker, segment):
    """Compute the post text without writing; return the closed report."""
    _clean("marker", marker)
    _clean("segment", segment)
    if marker in text:
        raise DebtNoteError("E_DRNA_MARKER",
                            "marker %r is already on the register" % marker)
    try:
        rows = DR.parse(text)
    except DR.DebtRegisterError as exc:
        raise DebtNoteError("E_DRNA_MISSING",
                            "register does not parse: %s" % exc.code)
    found = [r for r in rows if r["item"] == item]
    if not found:
        raise DebtNoteError("E_DRNA_NO_ROW",
                            "item %r is not on the register" % item)
    if len(found) > 1:
        raise DebtNoteError("E_DRNA_DUP_ROW",
                            "item %r is carried by %d rows"
                            % (item, len(found)))
    if found[0]["state"] != "open":
        raise DebtNoteError("E_DRNA_NOT_OPEN",
                            "row %r is %s" % (item, found[0]["state"]))

    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines)
            if line.startswith("- [ ]") and
            ("item=%s" % item) in (line + SEGMENT_SEP)]
    if len(hits) != 1:
        raise DebtNoteError(
            "E_DRNA_SHAPE",
            "expected one open line carrying %r, found %d"
            % (item, len(hits)))
    at = hits[0]
    body = lines[at]
    if not (body.endswith("| first=yes") or body.endswith("| first=no")):
        raise DebtNoteError(
            "E_DRNA_SHAPE",
            "row does not end on a scalar first=: %r" % body[-40:])
    first_segment = body.rsplit(SEGMENT_SEP, 1)[1]
    head = body[:-len(first_segment) - len(SEGMENT_SEP)].lstrip()
    if head.startswith("- [ ]"):
        head = head[len("- [ ]"):].lstrip()
    parts = _segments(head)
    note_at = None
    for index, part in enumerate(parts):
        if part.startswith(NOTE_KEY):
            note_at = index
            break
    note_grew = note_at is not None
    if note_grew:
        old_note = parts[note_at][len(NOTE_KEY):]
        if not old_note.strip():
            parts[note_at] = NOTE_KEY + segment
        else:
            parts[note_at] = parts[note_at] + " ; " + segment
    else:
        parts.append(NOTE_KEY + segment)
    post_line = "- [ ] " + SEGMENT_SEP.join(parts) + SEGMENT_SEP + first_segment
    lines[at] = post_line
    post = "\n".join(lines)

    try:
        after = DR.parse(post)
    except DR.DebtRegisterError as exc:
        raise DebtNoteError(
            "E_DRNA_POST",
            "composed row does not parse (%s); nothing written" % exc.code)
    if len(after) != len(rows):
        raise DebtNoteError(
            "E_DRNA_POST",
            "post text carries %d rows, expected %d" % (len(after), len(rows)))
    added = [r for r in after if r["item"] == item]
    if len(added) != 1 or marker not in (added[0]["note"] or ""):
        raise DebtNoteError(
            "E_DRNA_POST", "post text does not carry the marker on the row")
    if added[0]["first"] != found[0]["first"]:
        raise DebtNoteError(
            "E_DRNA_POST",
            "first moved %r -> %r" % (found[0]["first"], added[0]["first"]))
    return {
        "item": item,
        "marker": marker,
        "row_line": at + 1,
        "note_grew": note_grew,
        "first_kept": added[0]["first"],
        "before_bytes": len(text.encode("utf-8")),
        "predicted_bytes": len(post.encode("utf-8")),
        "post": post,
    }


def append_note(root, item, marker, segment, execute=False):
    """Plan (and optionally perform) one note grow under root."""
    path = os.path.join(root, REGISTER_REL)
    if not os.path.isfile(path):
        raise DebtNoteError("E_DRNA_MISSING",
                            "register not found: %s" % path)
    try:
        text = DR.read_text(path)
    except DR.DebtRegisterError as exc:
        raise DebtNoteError("E_DRNA_MISSING",
                            "register unreadable: %s" % exc.code)
    report = plan(text, item, marker, segment)
    post = report.pop("post")
    report["path"] = REGISTER_REL.replace(os.sep, "/")
    report["wrote"] = False
    report["read_back_ok"] = None
    if not execute:
        return report
    import general_writer_dialect_audit as GWDA
    data = GWDA.payload_for(path, post)
    temp = path + TEMP_SUFFIX
    try:
        with io.open(temp, "wb") as handle:
            handle.write(data)
        os.replace(temp, path)
    except (IOError, OSError) as exc:
        if os.path.exists(temp):
            os.remove(temp)
        raise DebtNoteError("E_DRNA_WRITE", "%s (%s)" % (path, exc))
    with io.open(path, "rb") as handle:
        back = handle.read()
    report["wrote"] = True
    report["read_back_ok"] = back == data
    if not report["read_back_ok"]:
        raise DebtNoteError(
            "E_DRNA_READBACK",
            "read-back carries %d bytes, wrote %d" % (len(back), len(data)))
    if os.path.exists(temp):
        raise DebtNoteError("E_DRNA_RESIDUE",
                            "temp file survived: %s" % temp)
    return report


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    import json
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def one_line(report):
    return ("DEBT NOTE item=%s marker=%s line=%d note_grew=%s first=%s "
            "before=%dB after=%dB wrote=%s readback=%s"
            % (report["item"], report["marker"], report["row_line"],
               "yes" if report["note_grew"] else "no",
               report["first_kept"],
               report["before_bytes"], report["predicted_bytes"],
               "yes" if report["wrote"] else "no",
               "n/a" if report["read_back_ok"] is None
               else ("ok" if report["read_back_ok"] else "BAD")))


USAGE = ("usage: debt_note_append.py --item NAME --marker MARK --text TEXT\n"
         "                             [--root PATH] [--execute] [--json]\n"
         "  dry run by default (writes nothing, prints the prediction)\n"
         "  exit 0 = planned (dry run) or grown and read back\n"
         "  exit 2 = refused (no row, duplicate row, closed, marker, shape)\n"
         "  exit 3 = register missing, unreadable or malformed\n"
         "  exit 5 = bad flags\n")


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    item = None
    marker = None
    text = None
    execute = False
    as_json = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--item", "--marker", "--text", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_DRNA_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            value = argv[index]
            if arg == "--item":
                item = value
            elif arg == "--marker":
                marker = value
            elif arg == "--text":
                text = value
            else:
                root = value
        elif arg == "--execute":
            execute = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_DRNA_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not item or not marker or not text:
        sys.stdout.write("E_DRNA_BAD_ARGS: --item, --marker and --text are "
                         "required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = append_note(root, item, marker, text, execute)
    except DebtNoteError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.code in ("E_DRNA_NO_ROW", "E_DRNA_DUP_ROW", "E_DRNA_NOT_OPEN",
                        "E_DRNA_MARKER", "E_DRNA_SHAPE", "E_DRNA_BAD_FIELD",
                        "E_DRNA_POST", "E_DRNA_READBACK", "E_DRNA_RESIDUE"):
            return 2
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(one_line(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))