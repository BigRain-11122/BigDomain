# debt_item_unique.py - does any item appear on more than one register row?
# Criteria AC-DIU1..AC-DIU6 were pre-registered in state/queue/tech.md as
# the R2274 seed row BEFORE this file existed.
#
# Why this exists: debt_register checks each row's shape and allows at most
# one open first=yes, but it never checks that an ITEM appears once. The
# live register carries reconcile-battery-and-matrix on two done rows, so
# "what does the register say about this item" depends on which duplicate a
# reader happens to take, and debt_close's own ALREADY-DONE and AMBIGUOUS
# refusals can both fire for one name.
#
# Read-only by construction: the row law is imported from debt_register
# (parse is asked, never re-implemented), nothing is written, no clock is
# read and no network module is imported. Source is pure ASCII, stdlib only.
#
# Two classes, never merged: a group carrying ANY open row reads DUP-OPEN
# (live debt tracked twice); a group whose rows are all closed reads
# DUP-DONE (history kept twice). AC-DIU3 names the open+done and the
# done+done cases; the boundary is drawn on whether any row is still open,
# so two open rows also read DUP-OPEN rather than needing a third class.

import io
import os
import sys

import debt_register as DR

REGISTER_REL = DR.REGISTER_REL

REPORT_KEYS = (
    "register",
    "present",
    "rows_scanned",
    "duplicate_count",
    "dup_open_count",
    "dup_done_count",
    "duplicates",
    "verdict",
)

VERDICTS = ("UNIQUE", "DUPLICATES", "EMPTY")

KIND_OPEN = "DUP-OPEN"
KIND_DONE = "DUP-DONE"


class DebtItemUniqueError(Exception):
    """Raised when the register cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def row_lines(text):
    """1-based line numbers of the lines debt_register would parse.

    The locators are debt_register's own regexes, so this counts exactly
    the lines parse() turns into rows; the parsing itself stays there.
    """
    numbers = []
    for index, line in enumerate(text.split("\n"), 1):
        if DR.OPEN_RE.match(line) or DR.DONE_RE.match(line):
            numbers.append(index)
    return numbers


def group(rows, numbers):
    """Group parsed rows by item, keeping every row and its line."""
    if len(numbers) != len(rows):
        raise DebtItemUniqueError(
            "E_DIU_SHAPE",
            "%d parsed rows against %d located lines"
            % (len(rows), len(numbers)))
    order = []
    by_item = {}
    for row, line in zip(rows, numbers):
        entry = {
            "state": row["state"],
            "opened": row["opened"],
            "closed": row["closed"],
            "line": line,
        }
        if row["item"] not in by_item:
            by_item[row["item"]] = []
            order.append(row["item"])
        by_item[row["item"]].append(entry)
    duplicates = []
    dup_open = 0
    dup_done = 0
    for item in order:
        entries = by_item[item]
        if len(entries) < 2:
            continue
        has_open = any(entry["state"] == "open" for entry in entries)
        kind = KIND_OPEN if has_open else KIND_DONE
        if has_open:
            dup_open += 1
        else:
            dup_done += 1
        duplicates.append({
            "item": item,
            "kind": kind,
            "row_count": len(entries),
            "rows": entries,
        })
    return duplicates, dup_open, dup_done


def audit(root):
    """Measure the register under root; return the closed report shape."""
    path = os.path.join(root, REGISTER_REL)
    if not os.path.isfile(path):
        raise DebtItemUniqueError("E_DIU_MISSING",
                                  "%s is absent" % REGISTER_REL)
    try:
        text = DR.read_text(path)
    except DR.DebtRegisterError as exc:
        raise DebtItemUniqueError("E_DIU_UNREADABLE", exc.detail)
    try:
        rows = DR.parse(text)
    except DR.DebtRegisterError as exc:
        raise DebtItemUniqueError(
            "E_DIU_BAD_REGISTER", "%s: %s" % (exc.code, exc.detail))
    duplicates, dup_open, dup_done = group(rows, row_lines(text))
    if not rows:
        verdict = "EMPTY"
    elif duplicates:
        verdict = "DUPLICATES"
    else:
        verdict = "UNIQUE"
    return {
        "register": REGISTER_REL.replace(os.sep, "/"),
        "present": True,
        "rows_scanned": len(rows),
        "duplicate_count": len(duplicates),
        "dup_open_count": dup_open,
        "dup_done_count": dup_done,
        "duplicates": duplicates,
        "verdict": verdict,
    }


def one_line(report):
    """The single line an operator reads."""
    return ("DEBT ITEM UNIQUE rows=%d duplicate_items=%d dup_open=%d "
            "dup_done=%d verdict=%s"
            % (report["rows_scanned"], report["duplicate_count"],
               report["dup_open_count"], report["dup_done_count"],
               report["verdict"]))


def render(report):
    """Full text rendering: the one line, then one line per duplicate."""
    out = [one_line(report)]
    for entry in report["duplicates"]:
        lines = ",".join(str(row["line"]) for row in entry["rows"])
        stamps = ",".join("%s:%s" % (row["state"], row["opened"])
                          for row in entry["rows"])
        out.append("  dup %-9s %-30s rows=%d lines=%s [%s]"
                   % (entry["kind"], entry["item"], entry["row_count"],
                      lines, stamps))
    if report["verdict"] == "EMPTY":
        out.append("  register=%s carries no rows" % report["register"])
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    import json
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: debt_item_unique.py --check [--root PATH] [--json]\n"
         "  exit 0 = every item appears once (or the register is empty)\n"
         "  exit 2 = at least one item is carried by more than one row\n"
         "  exit 3 = register absent, unreadable or malformed\n"
         "  exit 5 = bad flags")


def main(argv):
    check = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_DIU_BAD_ARGS: --root needs a path\n")
                sys.stdout.write(USAGE + "\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE + "\n")
            return 0
        else:
            sys.stdout.write("E_DIU_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE + "\n")
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_DIU_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE + "\n")
        return 5
    try:
        report = audit(root)
    except DebtItemUniqueError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "DUPLICATES":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))