"""review_window_guard_parity - do the two review-window faces still agree?

Criteria AC-RWGP1..AC-RWGP6 were pinned inside the R2371 seed row of
state/queue/tech.md BEFORE this file existed. Anchor check at HEAD
2026-11-02: review_window_guard_parity, AC-RWGP, E_RWGP,
os-review-window-guard-parity and test_review_window_guard_parity hit only
prose and state files (this row, the R2371 board/closeout/export helpers,
src/os/backlog.md, docs/status-export.json, heartbeat.txt, state.json,
state/debt.md) with zero executable occupancy.

Why this exists: the SAME declarations list is now read by two faces and
nothing measured that they agree. review_window_wire.window_report is the
DECLARED path and refuses a rewinding list with E_RWHW_DECL_HISTORY;
review_window_wire_argument_guard.reading is the ARGUMENT path and refuses
the same file with the same code. Each was proved on its own fixtures, so a
future edit to either law could split the two paths in silence.

The parity asks exactly ONE question of both faces, because that is the only
law they share: does this declarations list rewind?

  * each side is IMPORTED and asked at call time (AC-RWGP1), so patching
    window_report or reading moves this report - no third reading of the
    declarations list, no second row parser and no rewind comparison is
    written here;
  * both refusing with the carried E_RWHW_DECL_HISTORY reads PARITY-AGREES
    and both codes are reported (AC-RWGP2);
  * a monotonic list reads PARITY-AGREES with the declared window carried
    from the wire and the argument guard's own history word beside it - the
    two faces ask different questions and that is not a disagreement
    (AC-RWGP3), and a declaration the argument path deliberately ignores
    (UNPINNED, DRIFT) is likewise reported rather than called a split;
  * the moment the two sides disagree about the rewind, or either side
    answers with a code the other cannot explain, this reads
    PARITY-DISAGREES naming both codes (AC-RWGP4).

Read-only: it writes nothing, reads no clock, imports no network. Pure ASCII
source, stdlib only.
"""

import json
import os
import sys

import review_window_wire as RWW
import review_window_wire_argument_guard as RWAG

PARITY_PREFIX = "E_RWGP"
REWIND_CODE = "E_RWHW_DECL_HISTORY"

# AC-RWGP5: the report carries these keys in this order and nothing else.
PARITY_KEYS = (
    "verdict",
    "rewind",
    "declared",
    "declared_code",
    "declared_window",
    "argument",
    "argument_history",
    "argument_code",
    "agrees",
)

VERDICTS = ("PARITY-AGREES", "PARITY-DISAGREES")

DECLARED_WINDOW = "WINDOW"
DECLARED_REFUSED = "REFUSED"


class ReviewWindowGuardParityError(Exception):
    """Raised only when the parity cannot be measured at all."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def declared_side(root, round_text):
    """The DECLARED path's answer, reduced to the rewind question (AC-RWGP1).

    Asked as an attribute of the module at call time so a patched
    window_report moves this reading. Any refusal carrying the carried rewind
    code means that face detected a rewind; a refusal with any other code is
    reported as-is and simply is not a rewind.
    """
    try:
        report = RWW.window_report(root, round_text)
    except RWW.ReviewWindowWireError as exc:
        return {
            "state": DECLARED_REFUSED,
            "code": exc.code,
            "window": None,
            "rewind": exc.code == REWIND_CODE,
        }
    except Exception as exc:  # noqa: BLE001 - a broken face is not an agreement
        return {
            "state": DECLARED_REFUSED,
            "code": PARITY_PREFIX + "_DECLARED_BROKEN",
            "window": None,
            "rewind": False,
            "broken": "%s (%s)" % (type(exc).__name__, exc),
        }
    if not isinstance(report, dict):
        return {
            "state": DECLARED_REFUSED,
            "code": PARITY_PREFIX + "_DECLARED_BROKEN",
            "window": None,
            "rewind": False,
            "broken": "window_report returned %r" % (type(report).__name__,),
        }
    return {
        "state": DECLARED_WINDOW,
        "code": None,
        "window": report.get("window"),
        "rewind": False,
    }


def argument_side(root):
    """The ARGUMENT path's answer, reduced to the same question (AC-RWGP1)."""
    try:
        found = RWAG.reading(root)
    except Exception as exc:  # noqa: BLE001 - a broken face is not an agreement
        return {
            "verdict": PARITY_PREFIX + "_ARGUMENT_BROKEN",
            "code": PARITY_PREFIX + "_ARGUMENT_BROKEN",
            "rewind": False,
            "broken": "%s (%s)" % (type(exc).__name__, exc),
        }
    if not isinstance(found, dict):
        return {
            "verdict": PARITY_PREFIX + "_ARGUMENT_BROKEN",
            "code": PARITY_PREFIX + "_ARGUMENT_BROKEN",
            "rewind": False,
            "broken": "reading returned %r" % (type(found).__name__,),
        }
    verdict = found.get("verdict")
    return {
        "verdict": verdict,
        "history": found.get("history"),
        "code": found.get("code"),
        "rewind": verdict == "ARGUMENT-REFUSED",
    }


def check(root, round_text=None):
    """Run both faces over ONE declaration and say whether they agree."""
    if not os.path.isdir(root):
        raise ReviewWindowGuardParityError(
            PARITY_PREFIX + "_ROOT", "no such root: %s" % root)

    declared = declared_side(root, round_text)
    argument = argument_side(root)

    agrees = bool(declared["rewind"]) == bool(argument["rewind"])
    if agrees and declared["rewind"]:
        agrees = declared["code"] == argument["code"]

    return {
        "verdict": "PARITY-AGREES" if agrees else "PARITY-DISAGREES",
        "rewind": bool(declared["rewind"]),
        "declared": declared["state"],
        "declared_code": declared["code"],
        "declared_window": declared["window"],
        "argument": argument["verdict"],
        "argument_history": argument.get("history"),
        "argument_code": argument["code"],
        "agrees": agrees,
    }


def one_line(report):
    """The single line an operator reads."""
    window = "-" if report["declared_window"] is None else \
        "%d" % report["declared_window"]
    return ("REVIEW WINDOW GUARD PARITY verdict=%s rewind=%s window=%s "
            "declared=%s argument=%s agrees=%s"
            % (report["verdict"],
               "yes" if report["rewind"] else "no",
               window,
               report["declared_code"] or report["declared"],
               report["argument_code"] or report["argument"],
               "yes" if report["agrees"] else "no"))


def render(report):
    """The one line, then the two codes side by side."""
    out = [one_line(report)]
    out.append("  DECLARED %s%s"
               % (report["declared"],
                  "" if not report["declared_code"]
                  else " " + report["declared_code"]))
    out.append("  ARGUMENT %s%s"
               % (report["argument"],
                  "" if not report["argument_code"]
                  else " " + report["argument_code"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (AC-RWGP5)."""
    ordered = {}
    for key in PARITY_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: review_window_guard_parity.py --check [--root PATH] "
         "[--round RN] [--json]\n"
         "  exit 0 = the two review-window faces agree\n"
         "  exit 2 = they disagree about the declarations list\n"
         "  exit 3 = the root is missing or unreadable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    check_flag = False
    as_json = False
    round_text = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check_flag = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--round"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RWGP_BAD_ARGS: %s needs a value\n" % arg)
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
            sys.stdout.write("E_RWGP_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check_flag:
        sys.stdout.write("E_RWGP_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = check(root, round_text)
    except ReviewWindowGuardParityError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return 0 if report["agrees"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))