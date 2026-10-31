# debt_close.py - close a carried-debt row through the register's own law
# Criteria AC-DEBC1..AC-DEBC6 were pre-registered in state/queue/tech.md
# (R2251 seed row) BEFORE this file existed.
#
# Why this exists: debt_append.py gave the register a writer for OPEN rows,
# but closing a row is still hand surgery - a window edits "- [ ]" to
# "- [x]" and types "closed=R<n>" by hand, so a wrong or missing close
# stamp, or a closed row that keeps first=yes, stays invisible until
# debt_register refuses the whole file. This is the one callable that
# closes exactly one open row by item and proves the result by reading it
# back through debt_register's own parser and counter.
#
# Refusals, all before any write:
#   E_DEBC_UNKNOWN        no open row carries that item
#   E_DEBC_ALREADY_DONE   the item is on the register but already closed
#   E_DEBC_AMBIGUOUS      more than one open row carries that item
#   E_DEBC_BAD_ROUND      the close round is not an R-number, or predates
#                         the row's own opened round
#   E_DEBC_BAD_REGISTER   the register does not parse before or after
#   E_DEBC_SHAPE          the edit did not produce exactly the predicted row
#
# The row carries first= in its open form and a done row may not, so
# closing the row that leads the next window removes the flag instead of
# leaving it behind on a done row (AC-DEBC3).
#
# Dry run is the default: plan() returns the predicted post bytes and
# writes nothing. execute=True performs one atomic replace (temp file in
# the same directory), proves the read-back bytes equal the prediction and
# leaves no temp residue.
#
# Stdlib only, pure ASCII source, zero network, no clock read.

import io
import os
import sys

import debt_register as DR

REGISTER_REL = DR.REGISTER_REL
TEMP_SUFFIX = ".debc-tmp"

ROW_KEYS = (
    "path",
    "item",
    "round",
    "opened",
    "line",
    "row",
    "open_before",
    "open_after",
    "done_before",
    "done_after",
    "before_bytes",
    "predicted_bytes",
    "wrote",
    "read_back_ok",
)

REFUSAL_CODES = (
    "E_DEBC_UNKNOWN",
    "E_DEBC_ALREADY_DONE",
    "E_DEBC_AMBIGUOUS",
    "E_DEBC_BAD_ROUND",
)


class DebtCloseError(Exception):
    """Raised when a row cannot be closed without guessing."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _segment_key(segment):
    return segment.partition("=")[0].strip()


def render_closed(open_line, close_round):
    """Turn one open row line into its done form, dropping first=."""
    match = DR.OPEN_RE.match(open_line)
    if not match:
        raise DebtCloseError("E_DEBC_SHAPE",
                             "not an open row: %r" % open_line)
    payload = match.group(1) or ""
    segments = [seg.strip() for seg in payload.split("|")]
    kept = [seg for seg in segments if seg and _segment_key(seg) != "first"]
    if not any(_segment_key(seg) == "opened" for seg in kept):
        raise DebtCloseError("E_DEBC_SHAPE",
                             "open row carries no opened field: %r"
                             % open_line)
    if not any(_segment_key(seg) == "item" for seg in kept):
        raise DebtCloseError("E_DEBC_SHAPE",
                             "open row carries no item field: %r" % open_line)
    kept.append("closed=%s" % close_round)
    return "- [x] " + " | ".join(kept)


def _counts(rows):
    open_count = 0
    done_count = 0
    for row in rows:
        if row["state"] == "open":
            open_count += 1
        else:
            done_count += 1
    return open_count, done_count


def plan(text, item, close_round):
    """Compute the post text without writing; return the closed report."""
    if DR.round_number(close_round) is None:
        raise DebtCloseError("E_DEBC_BAD_ROUND",
                             "close round is not an R-number: %r"
                             % close_round)
    if not item or not item.strip():
        raise DebtCloseError("E_DEBC_UNKNOWN", "item is empty")
    try:
        rows = DR.parse(text)
    except DR.DebtRegisterError as exc:
        raise DebtCloseError("E_DEBC_BAD_REGISTER",
                             "register does not parse: %s" % exc.code)
    lines = text.split("\n")
    hits = []
    for index, line in enumerate(lines):
        if not DR.OPEN_RE.match(line):
            continue
        try:
            row = DR.parse_row(DR.OPEN_RE.match(line).group(1), True)
        except DR.DebtRegisterError as exc:
            raise DebtCloseError("E_DEBC_BAD_REGISTER",
                                 "row %d does not parse: %s"
                                 % (index + 1, exc.code))
        if row["item"] == item:
            hits.append((index, row))
    if not hits:
        done_items = [r["item"] for r in rows if r["state"] == "done"]
        if item in done_items:
            raise DebtCloseError(
                "E_DEBC_ALREADY_DONE",
                "item %r is already closed on the register" % item)
        raise DebtCloseError("E_DEBC_UNKNOWN",
                             "no open row carries item %r" % item)
    if len(hits) > 1:
        raise DebtCloseError(
            "E_DEBC_AMBIGUOUS",
            "%d open rows carry item %r (lines %s)"
            % (len(hits), item,
               ", ".join(str(index + 1) for index, _ in hits)))
    index, row = hits[0]
    if DR.round_number(close_round) < DR.round_number(row["opened"]):
        raise DebtCloseError(
            "E_DEBC_BAD_ROUND",
            "close %r predates opened %r" % (close_round, row["opened"]))
    closed_line = render_closed(lines[index], close_round)
    post_lines = list(lines)
    post_lines[index] = closed_line
    post = "\n".join(post_lines)
    try:
        after = DR.parse(post)
    except DR.DebtRegisterError as exc:
        raise DebtCloseError(
            "E_DEBC_BAD_REGISTER",
            "post text does not parse: %s" % exc.code)
    if len(after) != len(rows):
        raise DebtCloseError(
            "E_DEBC_SHAPE",
            "post text carries %d rows, expected %d"
            % (len(after), len(rows)))
    open_before, done_before = _counts(rows)
    open_after, done_after = _counts(after)
    if (open_after != open_before - 1) or (done_after != done_before + 1):
        raise DebtCloseError(
            "E_DEBC_SHAPE",
            "counts did not move by one (open %d->%d done %d->%d)"
            % (open_before, open_after, done_before, done_after))
    closed_rows = [r for r in after
                   if r["state"] == "done" and r["item"] == item
                   and r["closed"] == close_round]
    if len(closed_rows) != 1:
        raise DebtCloseError(
            "E_DEBC_SHAPE",
            "post text carries %d rows closed at %r"
            % (len(closed_rows), close_round))
    return {
        "item": item,
        "round": close_round,
        "opened": row["opened"],
        "line": index + 1,
        "row": closed_line,
        "open_before": open_before,
        "open_after": open_after,
        "done_before": done_before,
        "done_after": done_after,
        "before_bytes": len(text.encode("utf-8")),
        "predicted_bytes": len(post.encode("utf-8")),
        "post": post,
    }


def close_row(root, item, close_round, execute=False):
    """Plan (and optionally perform) one row close under root."""
    path = os.path.join(root, REGISTER_REL)
    if not os.path.isfile(path):
        raise DebtCloseError("E_DEBC_MISSING",
                             "register not found: %s" % path)
    try:
        text = DR.read_text(path)
    except DR.DebtRegisterError as exc:
        raise DebtCloseError("E_DEBC_BAD_REGISTER",
                             "register unreadable: %s" % exc.code)
    report = plan(text, item, close_round)
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
        raise DebtCloseError("E_DEBC_WRITE", "%s (%s)" % (path, exc))
    with io.open(path, "rb") as handle:
        back = handle.read()
    report["wrote"] = True
    report["read_back_ok"] = back == data
    if not report["read_back_ok"]:
        raise DebtCloseError(
            "E_DEBC_READBACK",
            "read-back carries %d bytes, predicted %d"
            % (len(back), len(data)))
    if os.path.exists(temp):
        raise DebtCloseError("E_DEBC_RESIDUE",
                             "temp file survived: %s" % temp)
    # The read-back goes through the register parser, so an edit that
    # leaves the file unreadable is an error rather than a silent write.
    try:
        measured = DR.register(root, close_round)
    except DR.DebtRegisterError as exc:
        raise DebtCloseError(
            "E_DEBC_BAD_REGISTER",
            "register does not parse after the edit: %s" % exc.code)
    if (measured["open_count"] != report["open_after"]
            or measured["done_count"] != report["done_after"]):
        raise DebtCloseError(
            "E_DEBC_SHAPE",
            "read-back counts %d/%d, predicted %d/%d"
            % (measured["open_count"], measured["done_count"],
               report["open_after"], report["done_after"]))
    return report


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    import json
    ordered = {}
    for key in ROW_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def one_line(report):
    return ("DEBT CLOSE item=%s round=%s opened=%s line=%d "
            "open=%d->%d done=%d->%d before=%dB after=%dB wrote=%s "
            "readback=%s"
            % (report["item"], report["round"], report["opened"],
               report["line"], report["open_before"], report["open_after"],
               report["done_before"], report["done_after"],
               report["before_bytes"], report["predicted_bytes"],
               "yes" if report["wrote"] else "no",
               "n/a" if report["read_back_ok"] is None
               else ("ok" if report["read_back_ok"] else "BAD")))


USAGE = ("usage: debt_close.py --item NAME --round R<nnnn> [--root PATH]\n"
         "                      [--execute] [--json]\n"
         "  dry run by default (writes nothing, prints the prediction)\n"
         "  exit 0 = planned (dry run) or closed and read back\n"
         "  exit 2 = refused (unknown item, already done, ambiguous,\n"
         "           bad or predating close round, bad flags)\n"
         "  exit 3 = register missing, unreadable or malformed\n"
         "  exit 5 = bad flags\n")


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    item = None
    close_round = None
    execute = False
    as_json = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--item", "--round", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_DEBC_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            value = argv[index]
            if arg == "--item":
                item = value
            elif arg == "--round":
                close_round = value
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
            sys.stdout.write("E_DEBC_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not item:
        sys.stdout.write("E_DEBC_BAD_ARGS: --item is required\n")
        sys.stdout.write(USAGE)
        return 5
    if not close_round:
        sys.stdout.write("E_DEBC_BAD_ARGS: --round is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = close_row(root, item, close_round, execute)
    except DebtCloseError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.code in REFUSAL_CODES:
            return 2
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(one_line(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))