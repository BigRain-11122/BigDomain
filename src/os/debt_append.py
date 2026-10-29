# debt_append.py - write a carried-debt row through the register's own law
# Criteria AC-DEBTA1..AC-DEBTA6 were pre-registered in state/queue/tech.md
# (R2248 a seed) BEFORE this file existed.
#
# Why this exists: the register (debt_register.py) only has rows if a
# window writes them by hand, so a deferral still starts life as log
# prose and the register drifts behind what the window actually owes.
# This is the one callable that appends a row in the register format and
# then proves it by reading the row back through debt_register's own
# parser, so the writer cannot invent a shape the reader refuses.
#
# Three refusals, all before any write:
#   E_DEBTA_DUP     the item is already on the register (open or done)
#   E_DEBTA_FIRST   a second open row would claim first=yes
#   E_DEBTA_BAD_*   the row cannot be rendered in the register format
#
# Dry run is the default: plan() returns the predicted post bytes and
# writes nothing. execute=True performs one atomic replace (temp file in
# the same directory) and proves the read-back bytes equal the prediction.
#
# Stdlib only, pure ASCII source, zero network, no clock read.

import io
import os
import sys

import debt_register as DR

REGISTER_REL = DR.REGISTER_REL
OPEN_HEADING = "## Open"
CLOSED_HEADING = "## Closed"
TEMP_SUFFIX = ".debta-tmp"

ROW_KEYS = (
    "path",
    "item",
    "first",
    "opened",
    "row",
    "insert_at",
    "before_bytes",
    "predicted_bytes",
    "wrote",
    "read_back_ok",
)


class DebtAppendError(Exception):
    """Raised when a row cannot be appended without guessing."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def build_row(opened, item, note, first):
    """Render one open row exactly in the register format."""
    if DR.round_number(opened) is None:
        raise DebtAppendError("E_DEBTA_BAD_ROUND",
                              "opened is not an R-number: %r" % opened)
    if not item or not item.strip():
        raise DebtAppendError("E_DEBTA_BAD_ITEM", "item is empty")
    for label, value in (("item", item), ("note", note)):
        if "|" in value or "=" in value or "\n" in value or "\r" in value:
            raise DebtAppendError(
                "E_DEBTA_BAD_FIELD",
                "%s cannot carry '|', '=' or a newline: %r" % (label, value))
    if first not in DR.FIRST_VALUES:
        raise DebtAppendError("E_DEBTA_BAD_FIRST",
                              "first must be yes or no, got %r" % first)
    if note:
        return "- [ ] opened=%s | item=%s | note=%s | first=%s" % (
            opened, item, note, first)
    return "- [ ] opened=%s | item=%s | first=%s" % (opened, item, first)


def _insert_at(lines):
    """Index of the line the new row goes after (end of the Open block)."""
    open_at = None
    for index, line in enumerate(lines):
        if line.strip() == OPEN_HEADING:
            open_at = index
            break
    if open_at is None:
        raise DebtAppendError("E_DEBTA_NO_OPEN",
                              "register carries no %r heading" % OPEN_HEADING)
    last_row = None
    for index in range(open_at + 1, len(lines)):
        line = lines[index]
        if line.strip() == CLOSED_HEADING:
            break
        if DR.OPEN_RE.match(line) or DR.DONE_RE.match(line):
            last_row = index
    if last_row is None:
        return open_at + 2
    return last_row + 1


def plan(text, opened, item, note, first):
    """Compute the post text without writing; return the closed report."""
    row = build_row(opened, item, note, first)
    try:
        rows = DR.parse(text)
    except DR.DebtRegisterError as exc:
        raise DebtAppendError("E_DEBTA_BAD_REGISTER",
                              "register does not parse: %s" % exc.code)
    for existing in rows:
        if existing["item"] == item:
            raise DebtAppendError(
                "E_DEBTA_DUP",
                "item %r is already on the register (%s)"
                % (item, existing["state"]))
    if first == "yes":
        for existing in rows:
            if existing["state"] == "open" and existing["first"] == "yes":
                raise DebtAppendError(
                    "E_DEBTA_FIRST",
                    "open row %r already claims first=yes" % existing["item"])
    lines = text.split("\n")
    at = _insert_at(lines)
    lines.insert(at, row)
    post = "\n".join(lines)
    try:
        after = DR.parse(post)
    except DR.DebtRegisterError as exc:
        raise DebtAppendError("E_DEBTA_BAD_REGISTER",
                              "post text does not parse: %s" % exc.code)
    if len(after) != len(rows) + 1:
        raise DebtAppendError(
            "E_DEBTA_SHAPE",
            "post text carries %d rows, expected %d"
            % (len(after), len(rows) + 1))
    appended = [r for r in after if r["item"] == item]
    if len(appended) != 1:
        raise DebtAppendError(
            "E_DEBTA_SHAPE",
            "post text carries %d rows for %r" % (len(appended), item))
    return {
        "item": item,
        "first": first,
        "opened": opened,
        "row": row,
        "insert_at": at,
        "before_bytes": len(text.encode("utf-8")),
        "predicted_bytes": len(post.encode("utf-8")),
        "post": post,
    }


def append_row(root, opened, item, note="", first="no", execute=False):
    """Plan (and optionally perform) one row append under root."""
    path = os.path.join(root, REGISTER_REL)
    if not os.path.isfile(path):
        raise DebtAppendError("E_DEBTA_MISSING",
                              "register not found: %s" % path)
    try:
        text = DR.read_text(path)
    except DR.DebtRegisterError as exc:
        raise DebtAppendError("E_DEBTA_BAD_REGISTER",
                              "register unreadable: %s" % exc.code)
    report = plan(text, opened, item, note, first)
    post = report.pop("post")
    report["path"] = REGISTER_REL.replace(os.sep, "/")
    report["wrote"] = False
    report["read_back_ok"] = None
    if not execute:
        return report
    data = post.encode("utf-8")
    temp = path + TEMP_SUFFIX
    try:
        with io.open(temp, "wb") as handle:
            handle.write(data)
        os.replace(temp, path)
    except (IOError, OSError) as exc:
        if os.path.exists(temp):
            os.remove(temp)
        raise DebtAppendError("E_DEBTA_WRITE", "%s (%s)" % (path, exc))
    with io.open(path, "rb") as handle:
        back = handle.read()
    report["wrote"] = True
    report["read_back_ok"] = back == data
    if not report["read_back_ok"]:
        raise DebtAppendError(
            "E_DEBTA_READBACK",
            "read-back carries %d bytes, predicted %d"
            % (len(back), len(data)))
    if os.path.exists(temp):
        raise DebtAppendError("E_DEBTA_RESIDUE",
                              "temp file survived: %s" % temp)
    return report


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    import json
    ordered = {}
    for key in ROW_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def one_line(report):
    return ("DEBT APPEND item=%s first=%s opened=%s before=%dB after=%dB "
            "wrote=%s readback=%s"
            % (report["item"], report["first"], report["opened"],
               report["before_bytes"], report["predicted_bytes"],
               "yes" if report["wrote"] else "no",
               "n/a" if report["read_back_ok"] is None
               else ("ok" if report["read_back_ok"] else "BAD")))


USAGE = ("usage: debt_append.py --item NAME [--opened R<nnnn>] [--note TEXT]\n"
         "                      [--first yes|no] [--execute] [--root PATH]\n"
         "                      [--json]\n"
         "  dry run by default (writes nothing, prints the prediction)\n"
         "  exit 0 = planned (dry run) or appended and read back\n"
         "  exit 2 = refused (duplicate item, second first=yes)\n"
         "  exit 3 = register missing, unreadable or malformed\n"
         "  exit 5 = bad flags\n")


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    opened = None
    item = None
    note = ""
    first = "no"
    execute = False
    as_json = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--item", "--opened", "--note", "--first", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_DEBTA_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            value = argv[index]
            if arg == "--item":
                item = value
            elif arg == "--opened":
                opened = value
            elif arg == "--note":
                note = value
            elif arg == "--first":
                first = value
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
            sys.stdout.write("E_DEBTA_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not item:
        sys.stdout.write("E_DEBTA_BAD_ARGS: --item is required\n")
        sys.stdout.write(USAGE)
        return 5
    if not opened:
        sys.stdout.write("E_DEBTA_BAD_ARGS: --opened is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = append_row(root, opened, item, note, first, execute)
    except DebtAppendError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.code in ("E_DEBTA_DUP", "E_DEBTA_FIRST"):
            return 2
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(one_line(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))