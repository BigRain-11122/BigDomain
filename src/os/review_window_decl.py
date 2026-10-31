"""review_window_decl - the review window as a dated declaration (R2305).

`exempt_review` ages every accepted entry against a window, and that window
arrives as a per-call argument whose only default lives in the CLI. Two
reviewers can therefore read the SAME declaration as FRESH and STALE on the
same day and neither reading is wrong; the live exempt declaration also
carries no `until` on any entry, so the age window is the only thing that can
ever end a waiver. The house never pins the window it reviews against - the
same seam `state/log_floor.json` closed for the queue-only floor.

This resolver joins a pinned `state/review_window.json` to the round being
checked and refuses to guess:

  * one pinned shape only - a mapping with `window` (positive int),
    `declared_by` (round), non-empty `reason`, and a non-empty `declarations`
    list whose rows carry the same three keys. A missing file reads UNPINNED,
    never a fabricated pass, and every refusal carries its own code;
  * the declaration's own consistency is judged BEFORE it is used: a
    `declared_by` round later than the round being checked is
    E_RWD_DECL_FUTURE, because a future declaration cannot be honoured;
  * a window that moved without a new declaration row is DRIFT with both
    rounds named - never a quiet adoption of the newer number;
  * UNPINNED, DRIFT and every refusal hand back NO window. There is no
    default here: a default would decide on its own, which is exactly what
    the per-call argument was already doing wrong.

A caller-supplied window is compared, not trusted: equal reads AGREES,
different reads DISAGREES with both numbers named.

Nothing is written, no clock is read. Criteria AC-RWD1..AC-RWD6 were pinned
inside the R2292 seed row of state/queue/tech.md BEFORE this code existed.
Pure ASCII source, stdlib only, zero network.
"""

import json
import os
import sys

VERDICTS = ("AGREES", "DISAGREES")

REFUSAL_CODES = (
    "E_RWD_UNPINNED",
    "E_RWD_DRIFT",
    "E_RWD_REFUSED",
    "E_RWD_DECL_FUTURE",
)

DECLARATION_KEYS = ("window", "declared_by", "reason")

REPORT_KEYS = (
    "window",
    "declared",
    "declared_by",
    "reason",
    "round",
    "declarations",
    "caller",
    "verdict",
)

DECLARATION_PATH = os.path.join("state", "review_window.json")


class ReviewWindowError(Exception):
    """Raised when no honest window can be handed back."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parse_round(value):
    """A round reference: "R<n>" or "<n>", nothing else."""
    if not isinstance(value, str):
        raise ReviewWindowError("E_RWD_BAD_SHAPE", repr(value))
    text = value.strip()
    if text[:1] in ("R", "r"):
        text = text[1:]
    if not text or not text.isdigit():
        raise ReviewWindowError("E_RWD_BAD_SHAPE", repr(value))
    return int(text)


def parse_window(value, origin):
    """The window is a positive int that is not a bool."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReviewWindowError(
            "E_RWD_BAD_SHAPE", "%s window must be an int, got %r"
            % (origin, value))
    if value < 1:
        raise ReviewWindowError(
            "E_RWD_BAD_SHAPE", "%s window must be at least 1, got %d"
            % (origin, value))
    return value


def shape(raw, origin):
    """Validate the pinned declaration form and return its parsed fields.

    One pinned shape only (AC-RWD1): a mapping with `window`, `declared_by`,
    `reason` and a non-empty `declarations` list whose rows carry the same
    three keys. Anything else is a named refusal, never a silent default.
    """
    if not isinstance(raw, dict):
        raise ReviewWindowError("E_RWD_BAD_SHAPE", "%s is not an object" % origin)
    for key in DECLARATION_KEYS:
        if key not in raw:
            raise ReviewWindowError(
                "E_RWD_BAD_SHAPE", "%s is missing %r" % (origin, key))
    reason = raw["reason"]
    if not isinstance(reason, str) or not reason.strip():
        raise ReviewWindowError(
            "E_RWD_BAD_SHAPE", "%s reason is empty" % origin)
    rows = raw.get("declarations")
    if not isinstance(rows, list) or not rows:
        raise ReviewWindowError(
            "E_RWD_BAD_SHAPE", "%s has no declarations rows" % origin)
    parsed_rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ReviewWindowError(
                "E_RWD_BAD_SHAPE",
                "%s declaration %d is not an object" % (origin, index))
        for key in DECLARATION_KEYS:
            if key not in row:
                raise ReviewWindowError(
                    "E_RWD_BAD_SHAPE",
                    "%s declaration %d is missing %r" % (origin, index, key))
        row_reason = row["reason"]
        if not isinstance(row_reason, str) or not row_reason.strip():
            raise ReviewWindowError(
                "E_RWD_BAD_SHAPE",
                "%s declaration %d reason is empty" % (origin, index))
        parsed_rows.append({
            "window": parse_window(row["window"],
                                   "%s declaration %d" % (origin, index)),
            "declared_by": parse_round(row["declared_by"]),
            "reason": row_reason,
        })
    return {
        "window": parse_window(raw["window"], origin),
        "declared_by": parse_round(raw["declared_by"]),
        "reason": reason,
        "declarations": parsed_rows,
    }


def load_declaration(root):
    """Read state/review_window.json; a missing file is UNPINNED, not a pass."""
    path = os.path.join(root, DECLARATION_PATH)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (IOError, OSError) as exc:
        raise ReviewWindowError("E_RWD_UNREADABLE", str(exc))
    except ValueError as exc:
        raise ReviewWindowError("E_RWD_UNREADABLE", "not JSON (%s)" % exc)
    return shape(raw, DECLARATION_PATH)


def resolve(root, caller_window=None, round_text=None):
    """The pinned window, or a refusal; never a default (AC-RWD4)."""
    caller = None
    if caller_window is not None:
        caller = parse_window(caller_window, "caller")

    current = None
    if round_text is not None:
        current = parse_round(round_text)

    declaration = load_declaration(root)
    # AC-RWD4: an absent declaration hands back NO window. The full pinned
    # shape is still required of whatever file is present, so a half-written
    # file refuses instead of reading as "nothing pinned yet".
    if declaration is None:
        raise ReviewWindowError("E_RWD_UNPINNED", DECLARATION_PATH)

    window = declaration["window"]
    declared_by = declaration["declared_by"]
    last = declaration["declarations"][-1]

    # AC-RWD1: the declaration's own consistency is judged BEFORE it is used.
    # A round that has not happened yet cannot have declared anything.
    if current is not None and declared_by > current:
        raise ReviewWindowError(
            "E_RWD_DECL_FUTURE",
            "declared_by=R%d is later than the round being checked R%d"
            % (declared_by, current))
    if declared_by < last["declared_by"]:
        raise ReviewWindowError(
            "E_RWD_REFUSED",
            "declared_by=R%d predates its own last declaration R%d"
            % (declared_by, last["declared_by"]))

    # AC-RWD3: a window that moved without a new declaration row is DRIFT,
    # and both rounds are named so the operator can see which edit to undo.
    if window != last["window"]:
        direction = "forward" if window > last["window"] else "backward"
        raise ReviewWindowError(
            "E_RWD_DRIFT",
            "%s window %d declared %d declared_by=R%d last=R%d"
            % (direction, window, last["window"], declared_by,
               last["declared_by"]))

    # AC-RWD2: a supplied window is compared, not trusted.
    if caller is None or caller == window:
        verdict = "AGREES"
    else:
        verdict = "DISAGREES"

    return {
        "window": window,
        "declared": last["window"],
        "declared_by": "R%d" % declared_by,
        "reason": declaration["reason"],
        "round": None if current is None else "R%d" % current,
        "declarations": len(declaration["declarations"]),
        "caller": caller,
        "verdict": verdict,
    }


def one_line(report):
    """The single line an operator reads."""
    caller = "-" if report["caller"] is None else "%d" % report["caller"]
    round_text = "-" if report["round"] is None else report["round"]
    return ("REVIEW WINDOW window=%d declared=%d declared_by=%s round=%s "
            "declarations=%d caller=%s verdict=%s"
            % (report["window"], report["declared"], report["declared_by"],
               round_text, report["declarations"], caller,
               report["verdict"]))


def render(report):
    """Full text: the one line, then a DISAGREES line naming both windows."""
    out = [one_line(report)]
    if report["verdict"] == "DISAGREES":
        out.append("  DISAGREES caller=%d declared=%d"
                   % (report["caller"], report["window"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (no extra keys leak)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: review_window_decl.py --check [--window N] [--round R<n>]"
         " [--root PATH] [--json]\n"
         "  exit 0 = the window is pinned and any supplied window agrees\n"
         "  exit 2 = UNPINNED, DRIFT, a refusal, a disagreement, or bad"
         " flags\n"
         "  exit 3 = the declaration is unreadable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    check = False
    as_json = False
    caller = None
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
        elif arg in ("--window", "--round", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RWD_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            if arg == "--window":
                try:
                    caller = int(argv[index])
                except ValueError:
                    sys.stdout.write(
                        "E_RWD_BAD_WINDOW: %r is not an int\n" % (argv[index],))
                    sys.stdout.write(USAGE)
                    return 5
            elif arg == "--round":
                round_text = argv[index]
            else:
                root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RWD_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_RWD_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = resolve(root, caller, round_text)
    except ReviewWindowError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code in ("E_RWD_UNREADABLE", "E_RWD_BAD_SHAPE"):
            return 3
        return 2
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "AGREES":
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))