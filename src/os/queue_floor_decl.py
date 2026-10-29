"""queue_floor_decl - the declared floor as the only source of a floor (R2266).

`queue_only_reconcile` splits a queue residue only against a floor the caller
supplies. R2265 pinned that floor in `state/log_floor.json` and made it a
reading, but nothing consumes it: the pinned file can read PINNED while every
actual split is run against some other number, and that divergence is
invisible. This resolver joins the two faces.

  * It loads the declaration through `log_floor.audit` (imported, never
    re-read or re-shaped here), so the floor law has exactly one owner.
  * It hands back NO floor when the declaration is UNPINNED, DRIFT or
    consistency-refused: a refusal is its own code, never a default.
  * A caller-supplied floor is reported against the declared one: equal reads
    AGREES, different reads DISAGREES with both rounds named, so a silent
    disagreement becomes a named reading instead of an assumption.
  * It writes nothing and reads no clock, so a reading is reproducible.

Criteria AC-FDL1..AC-FDL6 were pinned in state/queue/tech.md as the R2265 seed
row BEFORE this code existed. Pure ASCII source, stdlib only, zero network.
"""

import json
import os
import sys

import log_floor

VERDICTS = ("AGREES", "DISAGREES")

REFUSAL_CODES = ("E_FDL_UNPINNED", "E_FDL_DRIFT", "E_FDL_REFUSED")

REPORT_KEYS = (
    "floor",
    "declared",
    "declared_by",
    "caller",
    "oldest_label",
    "declarations",
    "verdict",
)

CONSISTENCY_CODES = ("E_LFL_FLOOR_AHEAD", "E_LFL_DECL_ORDER")


class FloorDeclError(Exception):
    """Raised when no honest floor can be handed back."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def resolve(root, caller_floor=None):
    """The declared floor, or a refusal; never a default (AC-FDL1, AC-FDL2)."""
    caller = None
    if caller_floor is not None:
        try:
            caller = log_floor.parse_round(caller_floor)
        except log_floor.LogFloorError as exc:
            raise FloorDeclError("E_FDL_BAD_SHAPE", exc.detail)

    # AC-FDL1: the verdict is log_floor's, imported. Nothing about the
    # declaration shape or its consistency is judged a second time here.
    try:
        report = log_floor.audit(root)
    except log_floor.LogFloorError as exc:
        if exc.code in CONSISTENCY_CODES:
            raise FloorDeclError("E_FDL_REFUSED",
                                 "%s (%s)" % (exc.code, exc.detail))
        raise FloorDeclError("E_FDL_UNREADABLE",
                             "%s (%s)" % (exc.code, exc.detail))

    verdict = report.get("verdict")
    # AC-FDL2: no floor is handed back for an unreadable declaration state,
    # and each refusal carries its own code instead of falling back.
    if verdict == "UNPINNED":
        raise FloorDeclError("E_FDL_UNPINNED", "state/log_floor.json")
    if verdict == "DRIFT":
        raise FloorDeclError(
            "E_FDL_DRIFT",
            "floor=R%s declared=R%s"
            % (report.get("floor"), report.get("declared")))
    if verdict != "PINNED":
        raise FloorDeclError("E_FDL_REFUSED", "verdict=%r" % (verdict,))

    floor = report["floor"]
    # AC-FDL3: a supplied floor is compared, not trusted.
    if caller is None or caller == floor:
        resolved = "AGREES"
    else:
        resolved = "DISAGREES"

    return {
        "floor": floor,
        "declared": report.get("declared"),
        "declared_by": report.get("declared_by"),
        "caller": caller,
        "oldest_label": report.get("oldest_label"),
        "declarations": report.get("declarations"),
        "verdict": resolved,
    }


def one_line(report):
    """The single line an operator reads."""
    floor = "R%d" % report["floor"]
    caller = ("-" if report["caller"] is None
              else "R%d" % report["caller"])
    oldest = ("none" if report["oldest_label"] is None
              else "R%d" % report["oldest_label"])
    return ("QUEUE FLOOR DECL floor=%s caller=%s oldest_label=%s "
            "declarations=%s verdict=%s"
            % (floor, caller, oldest, report["declarations"],
               report["verdict"]))


def render(report):
    """Full text: the one line, then a DISAGREES line naming both rounds."""
    out = [one_line(report)]
    if report["verdict"] == "DISAGREES":
        out.append("  DISAGREES caller=R%d declared=R%d"
                   % (report["caller"], report["floor"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (no extra keys leak)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: queue_floor_decl.py --check [--floor R<n>] [--root PATH]"
         " [--json]\n"
         "  exit 0 = the declaration is PINNED and any supplied floor agrees\n"
         "  exit 2 = UNPINNED, DRIFT, a refusal, a disagreement, or bad"
         " flags\n"
         "  exit 3 = state.json or the declaration is unreadable\n")


def main(argv):
    check = False
    as_json = False
    caller = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--floor", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_FDL_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 2
            if arg == "--floor":
                caller = argv[index]
            else:
                root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_FDL_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 2
        index += 1
    if not check:
        sys.stdout.write("E_FDL_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    try:
        report = resolve(root, caller)
    except FloorDeclError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code == "E_FDL_UNREADABLE":
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