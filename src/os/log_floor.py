"""log_floor - the queue-only floor as a dated declaration (R2265).

`queue_only_reconcile` splits a queue residue only against a floor the caller
supplies, and its own live reading derived that floor from the log's smallest
label. That derivation is blind at the window bottom edge: if the oldest round
still in the log is itself the dropped one, nothing above it registers as debt
and the verdict reads RECONCILED while a ledger line is missing.

A floor must therefore be declared and dated, not derived from the thing it
judges. This reader answers three questions over a pinned
`state/log_floor.json` and refuses to guess:

  * is the declaration present and shaped as pinned (a missing file reads
    UNPINNED, never a fabricated pass);
  * is the declared floor older than the newest live log label's window (a
    floor newer than the smallest live log label would relabel real debt as
    age, so it is refused before any verdict);
  * has the effective floor moved since its last recorded declaration (a
    silent bump is exactly the failure this exists to stop - it is DRIFT with
    both rounds named, never a quiet accept).

Three deliberate narrowings:
  * The label law is `state_seq`'s, imported rather than re-implemented, so
    the floor and the log window cannot drift apart.
  * The declaration shape is one pinned form and nothing else - no partial
    file, no inferred defaults.
  * A report is a reading only: nothing is written, no clock is read, and
    unreadable input fails closed instead of producing a verdict.

Criteria AC-LFL1..AC-LFL6 were pinned in state/queue/tech.md as the R2263 seed
row BEFORE this code existed. Pure ASCII source, stdlib only, zero network.
"""

import json
import os
import sys

import state_seq

VERDICTS = ("PINNED", "UNPINNED", "DRIFT")

CONSISTENCY_CODES = ("E_LFL_FLOOR_AHEAD", "E_LFL_DECL_ORDER")

DECLARATION_KEYS = ("floor", "declared_by", "reason")

REPORT_KEYS = (
    "floor",
    "declared",
    "declared_by",
    "reason",
    "oldest_label",
    "declarations",
    "verdict",
)

DECLARATION_PATH = os.path.join("state", "log_floor.json")


class LogFloorError(Exception):
    """Raised when the reader cannot issue an honest verdict."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parse_round(value):
    """A round reference: "R<n>" or "<n>", nothing else."""
    if not isinstance(value, str):
        raise LogFloorError("E_LFL_BAD_SHAPE", repr(value))
    text = value.strip()
    if text[:1] in ("R", "r"):
        text = text[1:]
    if not text or not text.isdigit():
        raise LogFloorError("E_LFL_BAD_SHAPE", repr(value))
    return int(text)


def shape(raw, origin):
    """Validate the pinned declaration form and return its parsed fields.

    One pinned shape only: a mapping with `floor`, `declared_by`, `reason`
    and a non-empty `declarations` list whose rows carry the same three keys.
    Anything else is unreadable rather than silently defaulted (AC-LFL1).
    """
    if not isinstance(raw, dict):
        raise LogFloorError("E_LFL_BAD_SHAPE", "%s is not an object" % origin)
    for key in DECLARATION_KEYS:
        if key not in raw:
            raise LogFloorError("E_LFL_BAD_SHAPE",
                                "%s is missing %r" % (origin, key))
    reason = raw["reason"]
    if not isinstance(reason, str) or not reason.strip():
        raise LogFloorError("E_LFL_BAD_SHAPE",
                            "%s reason is empty" % origin)
    rows = raw.get("declarations")
    if not isinstance(rows, list) or not rows:
        raise LogFloorError("E_LFL_BAD_SHAPE",
                            "%s has no declarations rows" % origin)
    parsed_rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise LogFloorError("E_LFL_BAD_SHAPE",
                                "%s declaration %d is not an object"
                                % (origin, index))
        for key in DECLARATION_KEYS:
            if key not in row:
                raise LogFloorError(
                    "E_LFL_BAD_SHAPE",
                    "%s declaration %d is missing %r" % (origin, index, key))
        row_reason = row["reason"]
        if not isinstance(row_reason, str) or not row_reason.strip():
            raise LogFloorError(
                "E_LFL_BAD_SHAPE",
                "%s declaration %d reason is empty" % (origin, index))
        parsed_rows.append({
            "floor": parse_round(row["floor"]),
            "declared_by": parse_round(row["declared_by"]),
            "reason": row_reason,
        })
    return {
        "floor": parse_round(raw["floor"]),
        "declared_by": parse_round(raw["declared_by"]),
        "reason": reason,
        "declarations": parsed_rows,
    }


def load_declaration(root):
    """Read state/log_floor.json; a missing file is UNPINNED, not a pass."""
    path = os.path.join(root, DECLARATION_PATH)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (IOError, OSError) as exc:
        raise LogFloorError("E_LFL_UNREADABLE", str(exc))
    except ValueError as exc:
        raise LogFloorError("E_LFL_UNREADABLE", "not JSON (%s)" % exc)
    return shape(raw, DECLARATION_PATH)


def oldest_label(root):
    """The smallest round the live log still carries, or None (AC-LFL2)."""
    try:
        state = state_seq.load_state(root)
        labels = state_seq.extract_labels(state)
    except state_seq.StateSeqError as exc:
        raise LogFloorError("E_LFL_UNREADABLE",
                            "%s (%s)" % (exc.code, exc.detail))
    return min(labels) if labels else None


def audit(root):
    """Read the declaration and the log window and return the closed report."""
    declaration = load_declaration(root)
    if declaration is None:
        return {
            "floor": None,
            "declared": None,
            "declared_by": None,
            "reason": "no state/log_floor.json",
            "oldest_label": None,
            "declarations": 0,
            "verdict": "UNPINNED",
        }

    floor = declaration["floor"]
    last = declaration["declarations"][-1]
    declared_by = declaration["declared_by"]
    oldest = oldest_label(root)

    # AC-LFL3: a floor cannot predate the round that declared it. The
    # declaration's own consistency is judged before it is compared with the
    # log, so a self-inconsistent file is never used to measure anything.
    if declared_by < floor:
        raise LogFloorError(
            "E_LFL_DECL_ORDER",
            "declared_by=R%d floor=R%d" % (declared_by, floor))

    # AC-LFL2: a floor newer than the smallest live log label would relabel
    # real debt as age, so it is refused before any verdict is issued.
    if oldest is not None and floor > oldest:
        raise LogFloorError(
            "E_LFL_FLOOR_AHEAD",
            "floor=R%d oldest_label=R%d" % (floor, oldest))

    # AC-LFL4: the effective floor must equal its last recorded declaration.
    # A forward bump with no new declaration row is the quiet-acccept failure.
    if floor != last["floor"]:
        direction = "forward" if floor > last["floor"] else "backward"
        return {
            "floor": floor,
            "declared": last["floor"],
            "declared_by": declared_by,
            "reason": declaration["reason"],
            "oldest_label": oldest,
            "declarations": len(declaration["declarations"]),
            "verdict": "DRIFT",
            "direction": direction,
        }

    return {
        "floor": floor,
        "declared": last["floor"],
        "declared_by": declared_by,
        "reason": declaration["reason"],
        "oldest_label": oldest,
        "declarations": len(declaration["declarations"]),
        "verdict": "PINNED",
    }


def one_line(report):
    """The single line an operator reads."""
    floor = "none" if report["floor"] is None else "R%d" % report["floor"]
    declared = ("none" if report["declared"] is None
                else "R%d" % report["declared"])
    oldest = ("none" if report["oldest_label"] is None
              else "R%d" % report["oldest_label"])
    return ("LOG FLOOR floor=%s declared=%s oldest_label=%s "
            "declarations=%d verdict=%s"
            % (floor, declared, oldest, report["declarations"],
               report["verdict"]))


def render(report):
    """Full text: the one line, then a DRIFT line naming both rounds."""
    out = [one_line(report)]
    if report["verdict"] == "DRIFT":
        out.append("  DRIFT %s floor=R%d declared=R%d"
                   % (report.get("direction", "moved"),
                      report["floor"], report["declared"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (no extra keys leak)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: log_floor.py --check [--root PATH] [--json]\n"
         "  exit 0 = the floor is PINNED and consistent with the live log\n"
         "  exit 2 = UNPINNED, DRIFT, a consistency refusal, or bad flags\n"
         "  exit 3 = state.json or state/log_floor.json is unreadable\n")


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
                sys.stdout.write("E_LFL_BAD_ARGS: --root needs a value\n")
                sys.stdout.write(USAGE)
                return 2
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_LFL_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 2
        index += 1
    if not check:
        sys.stdout.write("E_LFL_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    try:
        report = audit(root)
    except LogFloorError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code in CONSISTENCY_CODES:
            return 2
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "PINNED":
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))