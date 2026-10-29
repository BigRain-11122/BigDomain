# debt_register.py - machine-readable debt register plus its checker
# Criteria AC-DEBT1..AC-DEBT6 were pre-registered in state/queue/tech.md
# (R2240 c) BEFORE this file existed. AC-DEBT7 and AC-DEBT8 were added in
# the same window as the code (R2248) and are disclosed as such.
#
# Why this exists: every window that ships a product face defers the
# reconcile battery, and the deferral lived only in log prose. "owed since
# R2244, third window running" had to be re-derived by reading the tail of
# state.json, which is exactly the kind of memory that rots. This module
# turns the debt into rows a checker can read.
#
# Row law (narrow on purpose): a row starts at column 0 with "- [ ]"
# (open) or "- [x]"/"- [X]" (done), followed by pipe-separated
# key=value segments. Known keys only; unknown, duplicate, missing
# required or malformed values are refused rather than guessed, so a typo
# cannot silently drop a debt off the register.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import io
import os
import re
import sys

# Debt carried this many windows or more is an alarm, not a note.
STALE_WINDOWS = 3

REGISTER_REL = os.path.join("state", "debt.md")

OPEN_RE = re.compile(r"^- \[ \](?:[ \t]+(.*))?$")
DONE_RE = re.compile(r"^- \[[xX]\](?:[ \t]+(.*))?$")
ROUND_RE = re.compile(r"^R(\d{4,6})$")

ALLOWED_KEYS = ("opened", "item", "note", "first", "closed")
OPEN_REQUIRED = ("opened", "item", "first")
DONE_REQUIRED = ("opened", "item", "closed")

ROW_KEYS = (
    "state",
    "opened",
    "closed",
    "item",
    "note",
    "first",
    "carried",
    "stale",
)

REPORT_KEYS = (
    "register",
    "present",
    "rows",
    "open_count",
    "done_count",
    "first_count",
    "stale_count",
    "current_round",
    "stale_known",
    "oldest_carried",
    "verdict",
)

VERDICTS = ("DEBT-CLEAN", "DEBT-OPEN", "DEBT-STALE")

FIRST_VALUES = ("yes", "no")


class DebtRegisterError(Exception):
    """Raised when the register cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def round_number(value):
    """Parse an R-number label; raise on anything that is not one."""
    match = ROUND_RE.match(value)
    if not match:
        return None
    return int(match.group(1))


def parse_row(payload, is_open):
    """Parse one row payload into a closed key/value dict."""
    if payload is None or not payload.strip():
        raise DebtRegisterError("E_DR_BAD_ROW", "row carries no fields")
    fields = {}
    for segment in payload.split("|"):
        key, sep, value = segment.partition("=")
        key = key.strip()
        value = value.strip()
        if not sep:
            raise DebtRegisterError("E_DR_BAD_ROW",
                                    "segment without '=': %r" % segment)
        if key not in ALLOWED_KEYS:
            raise DebtRegisterError("E_DR_BAD_KEY", "unknown key %r" % key)
        if key in fields:
            raise DebtRegisterError("E_DR_DUP_KEY", "duplicate key %r" % key)
        fields[key] = value
    required = OPEN_REQUIRED if is_open else DONE_REQUIRED
    for key in required:
        if key not in fields:
            raise DebtRegisterError("E_DR_MISSING_KEY",
                                    "row is missing %r" % key)
    if not is_open:
        for key in ("first",):
            if key in fields:
                raise DebtRegisterError(
                    "E_DR_BAD_ROW", "a done row cannot carry %r" % key)
    opened = round_number(fields["opened"])
    if opened is None:
        raise DebtRegisterError("E_DR_BAD_ROUND",
                                "opened is not an R-number: %r"
                                % fields["opened"])
    if not fields["item"]:
        raise DebtRegisterError("E_DR_BAD_ROW", "item is empty")
    closed = None
    if is_open:
        if fields["first"] not in FIRST_VALUES:
            raise DebtRegisterError("E_DR_BAD_FIRST",
                                    "first must be yes or no, got %r"
                                    % fields["first"])
    else:
        closed = round_number(fields["closed"])
        if closed is None:
            raise DebtRegisterError("E_DR_BAD_ROUND",
                                    "closed is not an R-number: %r"
                                    % fields["closed"])
        if closed < opened:
            raise DebtRegisterError("E_DR_BAD_ROW",
                                    "closed %r predates opened %r"
                                    % (fields["closed"], fields["opened"]))
    return {
        "state": "open" if is_open else "done",
        "opened": fields["opened"],
        "closed": fields["closed"] if closed is not None else None,
        "item": fields["item"],
        "note": fields.get("note", ""),
        "first": fields.get("first", "no"),
    }


def read_text(path):
    """Read the register as utf-8; fail closed on unreadable input."""
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise DebtRegisterError("E_DR_UNREADABLE", "%s (%s)" % (path, exc))


def parse(text):
    """Parse the register body into rows; refuse the first bad row."""
    rows = []
    for line in text.split("\n"):
        is_open = bool(OPEN_RE.match(line))
        is_done = bool(DONE_RE.match(line))
        if not is_open and not is_done:
            continue
        match = OPEN_RE.match(line) if is_open else DONE_RE.match(line)
        rows.append(parse_row(match.group(1), is_open))
    return rows


def register(root, current_round=None):
    """Measure the register under root; return the closed report shape."""
    if current_round is not None and round_number(current_round) is None:
        raise DebtRegisterError("E_DR_BAD_ARGS",
                                "--round wants an R-number, got %r"
                                % current_round)
    path = os.path.join(root, REGISTER_REL)
    present = os.path.isfile(path)
    if present:
        rows = parse(read_text(path))
    else:
        rows = []
    now = round_number(current_round) if current_round else None
    open_count = 0
    done_count = 0
    first_count = 0
    stale_count = 0
    oldest = None
    for row in rows:
        # Every row carries the full key set: a done row has no age to
        # report, and saying so with None is honest rather than absent.
        row["carried"] = None
        row["stale"] = False
        if row["state"] == "done":
            done_count += 1
            continue
        open_count += 1
        if row["first"] == "yes":
            first_count += 1
        if now is None:
            row["carried"] = None
            row["stale"] = False
        else:
            carried = now - round_number(row["opened"])
            row["carried"] = carried
            row["stale"] = carried >= STALE_WINDOWS
            if oldest is None or carried > oldest:
                oldest = carried
        if row["stale"]:
            stale_count += 1
    if first_count > 1:
        raise DebtRegisterError(
            "E_DR_BAD_FIRST",
            "%d open rows claim first=yes, at most one may" % first_count)
    if stale_count:
        verdict = "DEBT-STALE"
    elif open_count:
        verdict = "DEBT-OPEN"
    else:
        verdict = "DEBT-CLEAN"
    return {
        "register": REGISTER_REL.replace(os.sep, "/"),
        "present": present,
        "rows": rows,
        "open_count": open_count,
        "done_count": done_count,
        "first_count": first_count,
        "stale_count": stale_count,
        "current_round": current_round,
        "stale_known": now is not None,
        "oldest_carried": oldest,
        "verdict": verdict,
    }


def first_item(report):
    """The item that leads the next window, or None when none is flagged."""
    for row in report["rows"]:
        if row["state"] == "open" and row["first"] == "yes":
            return row["item"]
    return None


def one_line(report):
    """The single line an operator reads."""
    lead = first_item(report) or "none"
    if report["stale_known"] and report["oldest_carried"] is not None:
        aged = "carried=%d" % report["oldest_carried"]
    else:
        aged = "carried=unknown"
    return ("DEBT REGISTER open=%d done=%d first=%s stale=%d %s verdict=%s"
            % (report["open_count"], report["done_count"], lead,
               report["stale_count"], aged, report["verdict"]))


def render(report):
    """Full text rendering: the one line, then one line per open row."""
    out = [one_line(report)]
    for row in report["rows"]:
        if row["state"] != "open":
            continue
        if row["carried"] is None:
            aged = "carried=?"
        else:
            aged = "carried=%d stale=%s" % (row["carried"],
                                            "yes" if row["stale"] else "no")
        out.append("  open %-7s %-28s first=%-3s %s"
                   % (row["opened"], row["item"], row["first"], aged))
    if not report["present"]:
        out.append("  register=%s MISSING" % report["register"])
    elif not report["stale_known"]:
        out.append("  stale=unknown (pass --round R<nnnn> to age the rows)")
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    import json
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: debt_register.py --check [--root PATH] [--round R<nnnn>]"
         " [--json]\n"
         "  exit 0 = register clean (no open debt)\n"
         "  exit 2 = debt open, none stale\n"
         "  exit 3 = register missing, unreadable or malformed\n"
         "  exit 4 = stale debt (carried %d+ windows)\n"
         "  exit 5 = bad flags\n" % STALE_WINDOWS)


def main(argv):
    check = False
    as_json = False
    current_round = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--round":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_DR_BAD_ARGS: --round needs an R-number\n")
                sys.stdout.write(USAGE)
                return 5
            current_round = argv[index]
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_DR_BAD_ARGS: --root needs a path\n")
                sys.stdout.write(USAGE)
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_DR_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_DR_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = register(root, current_round)
    except DebtRegisterError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if not report["present"]:
        return 3
    if report["verdict"] == "DEBT-STALE":
        return 4
    if report["verdict"] == "DEBT-OPEN":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))