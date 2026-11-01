"""review_window_history - the declarations list read as a HISTORY (R2345).

review_window_decl validates every row on its own, then compares only the
LAST row against the top-level window. A list that rewinds in time still
resolves AGREES: rows [R2400 w10, R2300 w20] with declared_by R2400 and a
top-level window of 20 read window=20 verdict=AGREES. The history is
therefore not a history - a later row can be OLDER than the one before it,
and a window can move twice inside one list with no reader naming either
move.

This reader adds the missing axis and nothing else:

  * the parsed rows come from review_window_decl.shape, never from a second
    validator in this file, and the resolver's own reading is asked of
    review_window_decl.resolve, so DRIFT and UNPINNED are the SAME words the
    resolver already uses about the same file - the two readers cannot
    disagree about it;
  * a declarations list whose declared_by rewinds refuses with E_RWH_REWIND
    naming BOTH rows and BOTH rounds, because a row that claims to have been
    declared by an earlier round than its predecessor is not a history;
  * every window move is named with its from/to numbers and both declaring
    rounds in FILE order, and a list with no move reads EMPTY-HISTORY rather
    than CLEAN: "the window never moved" and "nothing is pinned" must not
    read the same.

Exit 0 is the ordinary honest reading: the list is monotonic (no rewind) and
the resolver agrees with its own last row, so a NAMED move is history being
reported, not a defect - a reader whose whole purpose is to name moves may
not fail on the thing it names. EMPTY-HISTORY is likewise 0, and it is a
distinct word from CLEAN. Exit 2 is a rewind or a DRIFT, 3 is an unreadable
or badly shaped declaration, 5 is bad flags.

Criteria AC-RWH1..AC-RWH6 were pinned inside the R2327 tech seed row of
state/queue/tech.md BEFORE this code existed. This module writes nothing and
reads no clock. Pure ASCII source, stdlib only, zero network.
"""

import json
import os
import sys

import review_window_decl as RWD

VERDICTS = ("MOVED", "EMPTY-HISTORY", "DRIFT", "UNPINNED")

REFUSAL_CODES = (
    "E_RWH_UNREADABLE",
    "E_RWH_BAD_SHAPE",
    "E_RWH_REWIND",
    "E_RWH_BAD_ARGS",
)

REPORT_KEYS = (
    "verdict",
    "declarations",
    "rows",
    "moves",
    "rewind",
    "window",
    "declared_by",
    "resolver",
)


class ReviewWindowHistoryError(Exception):
    """Raised when no honest history can be handed back."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def load(repo_root):
    """The declaration with its parsed rows, or None when nothing is pinned.

    AC-RWH1: the rows are whatever review_window_decl.shape returns. This
    module carries no row law of its own, so a patched shape flows straight
    through both this loader and the resolver.
    """
    path = os.path.join(repo_root, RWD.DECLARATION_PATH)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (IOError, OSError) as exc:
        raise ReviewWindowHistoryError("E_RWH_UNREADABLE", str(exc))
    except ValueError as exc:
        raise ReviewWindowHistoryError(
            "E_RWH_UNREADABLE", "not JSON (%s)" % exc)
    try:
        return RWD.shape(raw, RWD.DECLARATION_PATH)
    except RWD.ReviewWindowError as exc:
        if exc.code == "E_RWD_BAD_SHAPE":
            raise ReviewWindowHistoryError("E_RWH_BAD_SHAPE", exc.detail)
        raise ReviewWindowHistoryError("E_RWH_UNREADABLE", exc.detail)


def moves(rows):
    """Every window move in FILE order, each naming both declaring rounds."""
    found = []
    for index in range(1, len(rows)):
        before = rows[index - 1]
        after = rows[index]
        if before["window"] == after["window"]:
            continue
        found.append({
            "index": index,
            "from": before["window"],
            "to": after["window"],
            "from_round": "R%d" % before["declared_by"],
            "to_round": "R%d" % after["declared_by"],
        })
    return found


def rewind(rows):
    """The first declared_by that goes backwards, or None (AC-RWH2)."""
    for index in range(1, len(rows)):
        before = rows[index - 1]
        after = rows[index]
        if after["declared_by"] < before["declared_by"]:
            return {
                "index": index,
                "previous_index": index - 1,
                "previous_round": "R%d" % before["declared_by"],
                "current_round": "R%d" % after["declared_by"],
                "previous_window": before["window"],
                "current_window": after["window"],
            }
    return None


def resolver_reading(repo_root):
    """Ask review_window_decl.resolve what IT reads about the same file.

    AC-RWH4: this module never invents a second agreement law. DRIFT and
    UNPINNED reach the report with the resolver's own detail text, so a
    fixture that differs by exactly one row cannot be DRIFT in one reader and
    something else in the other.
    """
    try:
        report = RWD.resolve(repo_root)
    except RWD.ReviewWindowError as exc:
        if exc.code in ("E_RWD_DRIFT", "E_RWD_UNPINNED"):
            return {"code": exc.code, "detail": exc.detail, "report": None}
        raise ReviewWindowHistoryError("E_RWH_UNREADABLE", "%s %s"
                                       % (exc.code, exc.detail))
    return {"code": None, "detail": "", "report": report}


def history(repo_root):
    """The declarations list read as history, or a named refusal."""
    declaration = load(repo_root)
    if declaration is None:
        reading = resolver_reading(repo_root)
        return {
            "verdict": "UNPINNED",
            "declarations": 0,
            "rows": [],
            "moves": [],
            "rewind": None,
            "window": None,
            "declared_by": None,
            "resolver": "UNPINNED %s" % reading["detail"],
        }

    rows = declaration["declarations"]

    broken = rewind(rows)
    if broken is not None:
        raise ReviewWindowHistoryError(
            "E_RWH_REWIND",
            "declaration %d declared_by=%s is earlier than declaration %d "
            "declared_by=%s (window %d -> %d)"
            % (broken["index"], broken["current_round"],
               broken["previous_index"], broken["previous_round"],
               broken["previous_window"], broken["current_window"]))

    reading = resolver_reading(repo_root)
    if reading["code"] == "E_RWD_UNPINNED":
        return {
            "verdict": "UNPINNED",
            "declarations": len(rows),
            "rows": rows,
            "moves": moves(rows),
            "rewind": None,
            "window": None,
            "declared_by": None,
            "resolver": "UNPINNED %s" % reading["detail"],
        }
    if reading["code"] == "E_RWD_DRIFT":
        return {
            "verdict": "DRIFT",
            "declarations": len(rows),
            "rows": rows,
            "moves": moves(rows),
            "rewind": None,
            "window": declaration["window"],
            "declared_by": "R%d" % declaration["declared_by"],
            "resolver": "DRIFT %s" % reading["detail"],
        }

    named = moves(rows)
    return {
        "verdict": "MOVED" if named else "EMPTY-HISTORY",
        "declarations": len(rows),
        "rows": rows,
        "moves": named,
        "rewind": None,
        "window": declaration["window"],
        "declared_by": "R%d" % declaration["declared_by"],
        "resolver": "AGREES",
    }


def one_line(report):
    """The single line an operator reads."""
    window = "-" if report["window"] is None else "%d" % report["window"]
    declared_by = report["declared_by"] or "-"
    return ("REVIEW WINDOW HISTORY declarations=%d moves=%d rewind=%s "
            "window=%s declared_by=%s verdict=%s"
            % (report["declarations"], len(report["moves"]),
               "none" if report["rewind"] is None else "yes",
               window, declared_by, report["verdict"]))


def render(report):
    """The one line, then one line per move, then the resolver reading."""
    out = [one_line(report)]
    for move in report["moves"]:
        out.append("  MOVE %d from=%d to=%d declared_by=%s"
                   % (move["index"], move["from"], move["to"],
                      move["to_round"]))
    out.append("  RESOLVER %s" % report["resolver"])
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (no extra keys leak)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: review_window_history.py --check [--root PATH] [--json]\n"
         "  exit 0 = monotonic history, moves named, or EMPTY-HISTORY\n"
         "  exit 2 = a rewind (E_RWH_REWIND), DRIFT or UNPINNED\n"
         "  exit 3 = the declaration is unreadable or badly shaped\n"
         "  exit 5 = bad flags\n")


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
                sys.stdout.write("E_RWH_BAD_ARGS: --root needs a value\n")
                sys.stdout.write(USAGE)
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RWH_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_RWH_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = history(root)
    except ReviewWindowHistoryError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code in ("E_RWH_UNREADABLE", "E_RWH_BAD_SHAPE"):
            return 3
        return 2
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] in ("MOVED", "EMPTY-HISTORY"):
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))