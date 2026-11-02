"""review_window_wire_argument_guard - the explicit --window path asks the history.

Criteria AC-RWAG1..AC-RWAG6 were pinned inside the R2359 seed row of
state/queue/tech.md BEFORE this file existed. Anchor check at HEAD
2026-11-02: review_window_wire_argument_guard / AC-RWAG / E_RWAG were git
grep -F hits only in prose and state files (the seed row, the R2359 closeout
script and src/os/backlog.md) and os-review-window-wire-argument-guard /
test_review_window_wire_argument_guard were zero-occupancy, so no executable
byte stood on this face.

Why this exists: R2345 shipped review_window_history, which reads the
declarations list as a HISTORY and refuses one whose declared_by rewinds, and
R2359 wired that law into the DECLARED path, so
`exempt_review --window-from-declaration` refuses a rewinding list with
E_RWHW_DECL_HISTORY before it ages anything. The ARGUMENT path never asked:
`exempt_review --window N` takes the number, ages every entry and returns, so
an operator who passes an explicit window against a list that rewinds still
gets a reading with no refusal at all. That is the seam this guard closes.

It carries no law of its own:

  * the rewind reading is review_window_history.history, imported at call
    time, so a patched history flows straight through this file and no second
    declared_by comparison lives here;
  * the refusal code is review_window_wire.carry_history_code, the very
    mapping the declared path already uses, so the argument path refuses with
    the same E_RWHW_DECL_HISTORY word rather than a look-alike of its own.

Scope is deliberately narrow (AC-RWAG2/AC-RWAG3): ONLY a provable rewind
changes the argument path's reading. A declaration that is UNPINNED or in
DRIFT, a list that merely moved, and a declarations file that cannot be read
all leave the explicit window's reading exactly as it was, because an
explicit window is the caller's and the declaration is not its authority. The
guard therefore adds a refusal and nothing else; it does not become a second
gate on a path that never asked the declaration in the first place.

This module writes nothing, reads no clock, imports no network. Pure ASCII
source, stdlib only.
"""

import json
import os
import sys

import review_window_history as RWH
import review_window_wire as RWW

GUARD_PREFIX = "E_RWAG"
REWIND_CODE = "E_RWHW_DECL_HISTORY"

# AC-RWAG5: the report carries these keys in this order and nothing else.
REPORT_KEYS = (
    "verdict",
    "code",
    "history",
    "declarations",
    "moves",
    "rewind",
    "declared_by",
    "window",
    "detail",
)

# AC-RWAG1 is the refusal; AC-RWAG2/AC-RWAG3 are the two quiet outcomes;
# ARGUMENT-UNKNOWN is the honest "the list could not be judged" reading, and
# it is NOT a refusal on this path (see the scope note above).
VERDICTS = ("ARGUMENT-CLEAN", "ARGUMENT-REFUSED", "ARGUMENT-UNKNOWN")

SOURCE_ARGUMENT = "argument"


class ReviewWindowArgumentGuardError(Exception):
    """Raised only when the declarations list provably rewinds."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _blank(verdict, code, history, detail, found=None):
    found = found or {}
    return {
        "verdict": verdict,
        "code": code,
        "history": history,
        "declarations": found.get("declarations"),
        "moves": found.get("moves"),
        "rewind": found.get("rewind"),
        "declared_by": found.get("declared_by"),
        "window": found.get("window"),
        "detail": detail,
    }


def reading(root):
    """Ask the history law what it reads, and answer in THIS face's words.

    AC-RWAG1: the rewind is carried, not re-detected - the history raises
    E_RWH_REWIND and the wire's own mapping turns it into the declared path's
    E_RWHW_DECL_HISTORY. Anything else the history can legitimately say about
    the list is not this path's business.
    """
    try:
        found = RWH.history(root)
    except RWH.ReviewWindowHistoryError as exc:
        carried = RWW.carry_history_code(exc.code)
        if carried == REWIND_CODE:
            # Same detail shape the declared path produces: the history's own
            # code, then its own words. Nothing is re-worded here.
            return _blank("ARGUMENT-REFUSED", carried, exc.code,
                          "%s %s" % (exc.code, exc.detail),
                          {"rewind": None})
        return _blank("ARGUMENT-UNKNOWN", carried, exc.code, exc.detail)
    except Exception as exc:  # noqa: BLE001 - a broken reader is not a pass
        return _blank("ARGUMENT-UNKNOWN", GUARD_PREFIX + "_UNREADABLE",
                      "E_RWAG_UNREADABLE",
                      "%s (%s)" % (type(exc).__name__, exc))
    if not isinstance(found, dict):
        return _blank("ARGUMENT-UNKNOWN", GUARD_PREFIX + "_UNREADABLE",
                      "E_RWAG_UNREADABLE",
                      "history returned %r" % (type(found).__name__,))
    verdict = found.get("verdict")
    if verdict not in RWH.VERDICTS:
        return _blank("ARGUMENT-UNKNOWN", GUARD_PREFIX + "_UNREADABLE",
                      "E_RWAG_UNREADABLE",
                      "history verdict is not a known word: %r" % (verdict,),
                      found)
    return _blank("ARGUMENT-CLEAN", None, verdict, "", found)


def guard(root):
    """Refuse a rewinding list; hand every other reading back untouched."""
    found = reading(root)
    if found["verdict"] == "ARGUMENT-REFUSED":
        raise ReviewWindowArgumentGuardError(found["code"], found["detail"])
    return found


def one_line(found):
    """The single line an operator reads."""
    declared_by = found["declared_by"] or "-"
    window = "-" if found["window"] is None else "%d" % found["window"]
    moves = found["moves"]
    return ("REVIEW WINDOW ARGUMENT GUARD verdict=%s history=%s window=%s "
            "moves=%d declared_by=%s"
            % (found["verdict"], found["history"], window,
               0 if not isinstance(moves, list) else len(moves), declared_by))


def to_json(found):
    """Serialise in the pinned key order only (AC-RWAG5)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = found.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: review_window_wire_argument_guard.py --check "
         "[--root PATH] [--json]\n"
         "  exit 0 = no rewind, the explicit window may age entries\n"
         "  exit 2 = the declarations list rewinds "
         "(E_RWHW_DECL_HISTORY) or cannot be read\n"
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
                sys.stdout.write("E_RWAG_BAD_FLAGS: --root needs a value\n")
                sys.stdout.write(USAGE)
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RWAG_BAD_FLAGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_RWAG_BAD_FLAGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    found = reading(root)
    if as_json:
        sys.stdout.write(to_json(found))
    else:
        sys.stdout.write(one_line(found) + "\n")
        if found["code"]:
            sys.stdout.write("  %s%s\n"
                             % (found["code"],
                                "" if not found["detail"]
                                else ": " + found["detail"]))
        elif found["detail"]:
            sys.stdout.write("  %s\n" % found["detail"])
    return 0 if found["verdict"] == "ARGUMENT-CLEAN" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))