"""review_window_wire - exempt_review reads its window from the declaration.

`review_window_decl` pins and dates the window a review is judged against, but
until R2327 nothing consumed it: `exempt_review` still took `--window` as a
per-call argument with its own CLI default, so the declaration could read
PINNED while every actual age reading used another number and the divergence
was invisible. This module is the one place that translates the declaration
into the number a reviewer ages against, and it never derives that number
itself:

  * the window comes from `review_window_decl.resolve` (caller window left
    unset) and is read off the report it hands back - no second join over the
    declarations rows, no default, no arithmetic in this file;
  * an UNPINNED, DRIFT or consistency-refused declaration is a refusal here
    too, with its own E_RWW_* code, so a caller that asked for the declared
    window never silently falls back to a literal;
  * the resolver's own codes are carried through rather than collapsed: the
    suffix after E_RWD_ becomes the suffix after E_RWW_ (UNPINNED, DRIFT,
    REFUSED, DECL_FUTURE, UNREADABLE, BAD_SHAPE), so an operator reading the
    refusal can tell which law refused.

R2345 added a second law about the same file: `review_window_history` reads
the declarations LIST as a history, because a list whose declared_by rewinds
in time still resolved AGREES. The resolver is blind to that, so a caller
could age every entry against a window taken from a list that is not a
history at all. This wire therefore asks the HISTORY first (AC-RWHW1) and
only then asks the resolver for the number:

  * a rewinding list refuses as E_RWHW_DECL_HISTORY, and the detail carries
    the history's own refusal code and both rounds - the rewind law is
    imported, never restated here (no declared_by comparison lives in this
    file);
  * a history that reads UNPINNED or DRIFT refuses with the SAME code and the
    SAME resolver detail the previous path produced, so the absent case keeps
    its old meaning byte for byte (AC-RWHW3) and a DRIFT keeps the resolver's
    own wording rather than a re-worded one (AC-RWHW2);
  * a moved-but-monotonic list is history being reported, not a defect: the
    wire hands the window out and its report names every move (AC-RWHW4).

Two authorities, kept apart on purpose: the history law answers "is this
list a history", the resolver answers "what number does it pin". Neither is
re-implemented here.

Read-only, no clock, no network. Criteria AC-RWW1..AC-RWW6 were pinned inside
the R2305 seed row of state/queue/tech.md BEFORE this file existed;
AC-RWHW1..AC-RWHW6 were pinned inside the R2345 seed row of the same board
BEFORE this guard existed.
Pure ASCII source, stdlib only.
"""

import json
import os
import sys

import review_window_decl
import review_window_history

REFUSAL_PREFIX = "E_RWW"
HISTORY_PREFIX = "E_RWH_"
HISTORY_REFUSAL_PREFIX = "E_RWHW"
RESOLVER_PREFIX = "E_RWD_"

SOURCE_DECLARATION = "declaration"
SOURCE_ARGUMENT = "argument"

# AC-RWHW1: the rewind code is CARRIED from the history law, not restated; every
# other history refusal keeps the exact code the resolver path already gave.
HISTORY_CODE_MAP = {
    "E_RWH_REWIND": HISTORY_REFUSAL_PREFIX + "_DECL_HISTORY",
    "E_RWH_UNREADABLE": REFUSAL_PREFIX + "_UNREADABLE",
    "E_RWH_BAD_SHAPE": REFUSAL_PREFIX + "_BAD_SHAPE",
}

REPORT_KEYS = (
    "verdict",
    "window",
    "source",
    "declared_by",
    "moves",
    "history",
    "resolver",
)

VERDICTS = ("MOVED", "EMPTY-HISTORY")


class ReviewWindowWireError(Exception):
    """Raised when the declaration cannot hand back an honest window."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def carry_code(code):
    """E_RWD_X -> E_RWW_X; anything unexpected is an unreadable refusal."""
    if isinstance(code, str) and code.startswith(RESOLVER_PREFIX):
        return REFUSAL_PREFIX + "_" + code[len(RESOLVER_PREFIX):]
    return REFUSAL_PREFIX + "_UNREADABLE"


def carry_history_code(code):
    """E_RWH_X -> its wire code; an unknown history code is a broken reader."""
    mapped = HISTORY_CODE_MAP.get(code)
    if mapped is not None:
        return mapped
    return REFUSAL_PREFIX + "_UNREADABLE"


def resolver_detail(carried, verdict):
    """The resolver's own words, taken from the history record.

    AC-RWHW2/AC-RWHW3: the history stores the resolver reading verbatim as
    '<VERDICT> <detail>', so stripping the verdict word hands back exactly the
    detail the old direct path produced - the wire words nothing itself.
    """
    text = carried.get("resolver")
    prefix = verdict + " "
    if isinstance(text, str) and text.startswith(prefix):
        return text[len(prefix):]
    return ""


def history_reading(root):
    """Ask review_window_history what IT reads about the declarations list.

    AC-RWHW1/AC-RWHW6: the law is imported at call time, so a patched history
    flows straight through this wire and no second rewind rule is written.
    """
    try:
        found = review_window_history.history(root)
    except review_window_history.ReviewWindowHistoryError as exc:
        raise ReviewWindowWireError(carry_history_code(exc.code),
                                    "%s %s" % (exc.code, exc.detail))
    except Exception as exc:  # noqa: BLE001 - a broken reader is not a pass
        raise ReviewWindowWireError(
            REFUSAL_PREFIX + "_UNREADABLE",
            "%s (%s)" % (type(exc).__name__, exc))
    if not isinstance(found, dict):
        raise ReviewWindowWireError(
            REFUSAL_PREFIX + "_UNREADABLE",
            "history returned %r" % (type(found).__name__,))
    verdict = found.get("verdict")
    if verdict not in ("MOVED", "EMPTY-HISTORY", "DRIFT", "UNPINNED"):
        raise ReviewWindowWireError(
            REFUSAL_PREFIX + "_UNREADABLE",
            "history verdict is not a known word: %r" % (verdict,))
    return found


def resolver_window(root, round_text):
    """The pinned window through the resolver, or a named refusal (AC-RWW1)."""
    try:
        report = review_window_decl.resolve(root, None, round_text)
    except review_window_decl.ReviewWindowError as exc:
        raise ReviewWindowWireError(carry_code(exc.code), exc.detail)
    except Exception as exc:  # noqa: BLE001 - a broken resolver is not a pass
        raise ReviewWindowWireError(
            REFUSAL_PREFIX + "_UNREADABLE",
            "%s (%s)" % (type(exc).__name__, exc))
    if not isinstance(report, dict):
        raise ReviewWindowWireError(
            REFUSAL_PREFIX + "_UNREADABLE",
            "resolver returned %r" % (type(report).__name__,))
    return report.get("window")


def window_report(root, round_text):
    """The window plus the history it was read through, or a named refusal.

    AC-RWHW1 runs the guard BEFORE any number is handed back; AC-RWHW4 keeps a
    legal move a report rather than a refusal.
    """
    found = history_reading(root)
    verdict = found["verdict"]

    if verdict == "UNPINNED":
        raise ReviewWindowWireError(REFUSAL_PREFIX + "_UNPINNED",
                                    resolver_detail(found, verdict))
    if verdict == "DRIFT":
        raise ReviewWindowWireError(REFUSAL_PREFIX + "_DRIFT",
                                    resolver_detail(found, verdict))

    window = resolver_window(root, round_text)
    if isinstance(window, bool) or not isinstance(window, int) or window < 1:
        raise ReviewWindowWireError(
            REFUSAL_PREFIX + "_BAD_WINDOW",
            "resolver window is not a positive int: %r" % (window,))

    moves = found.get("moves")
    if not isinstance(moves, list):
        moves = []
    return {
        "verdict": verdict,
        "window": window,
        "source": SOURCE_DECLARATION,
        "declared_by": found.get("declared_by"),
        "moves": moves,
        "history": verdict,
        "resolver": found.get("resolver", ""),
    }


def declared_window(root, round_text):
    """The pinned window, guarded by the history, or a named refusal.

    The signature is unchanged so the exempt_review call site keeps reading a
    plain int; the guard and the report live in window_report.
    """
    return window_report(root, round_text)["window"]


def one_line(report):
    """The single line an operator reads."""
    declared_by = report["declared_by"] or "-"
    return ("REVIEW WINDOW WIRE window=%d source=%s moves=%d declared_by=%s "
            "verdict=%s"
            % (report["window"], report["source"], len(report["moves"]),
               declared_by, report["verdict"]))


def render(report):
    """The one line, then one line per move, then the resolver reading."""
    out = [one_line(report)]
    for move in report["moves"]:
        out.append("  MOVE %d from=%d to=%d declared_by=%s"
                   % (move.get("index", 0), move.get("from", 0),
                      move.get("to", 0), move.get("to_round", "-")))
    out.append("  RESOLVER %s" % report["resolver"])
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (no extra keys leak)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: review_window_wire.py --check [--root PATH] [--round RN] "
         "[--json]\n"
         "  exit 0 = the declaration pins a window (moves reported)\n"
         "  exit 2 = refused (UNPINNED / DRIFT / a rewinding declarations "
         "history / other)\n"
         "  exit 3 = the declaration is unreadable or badly shaped\n"
         "  exit 5 = bad flags\n")


def main(argv):
    check = False
    as_json = False
    round_text = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--round"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RWW_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            if arg == "--root":
                root = argv[index]
            else:
                round_text = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RWW_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_RWW_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = window_report(root, round_text)
    except ReviewWindowWireError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code in (REFUSAL_PREFIX + "_UNREADABLE",
                        REFUSAL_PREFIX + "_BAD_SHAPE"):
            return 3
        return 2
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))