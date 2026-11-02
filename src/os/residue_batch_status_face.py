# residue_batch_status_face.py - the live status of every residue round, in
# the shape an operator needs to compose a --pair list
# Criteria AC-RSBF1..AC-RSBF6 were pre-registered inside the R2369 seed row of
# state/queue/tech.md BEFORE this file existed.
#
# Why this exists: residue_triage_append_batch refuses a status that disagrees
# with the live reading, but nothing in that CLI said WHAT the live status is.
# Its --check printed the rounds awaiting an entry and no status at all, so
# composing a --pair list meant running stamp_residue separately and guessing,
# and the first attempt at a batch cost a refused call (measured at R2369,
# where the module own suite guessed DELIVERED against STAMP-ONLY-OPEN and was
# wrong).
#
# This module is the missing reading and nothing else:
#   * the status map IS residue_triage.live_residue, which is stamp_residue's
#     own read validated against stamp_residue's own vocabulary - imported at
#     call time, so patching either reader moves this reading (AC-RSBF1). No
#     second residue scan, no queue parse and no stamp regex live here;
#   * the reported vocabulary is stamp_residue's STATUSES read at call time,
#     so a status this module has never heard of travels rather than being
#     dropped (AC-RSBF1);
#   * every residue round is named WITH its live status, so a --pair list can
#     be composed from this one call (AC-RSBF2);
#   * a round the live reading does not carry reads NOT-RESIDUE with its own
#     code rather than an invented status (AC-RSBF3);
#   * this file writes nothing, reads no clock, imports no network, and is
#     pure ASCII stdlib (AC-RSBF6).
#
# The batch CLI asks this face from its --check path; its --append path is
# untouched and never calls it, which is what keeps every append refusal code
# and printed line byte-identical (AC-RSBF4).
#
# Pure read: nothing is written, no clock, no network.

import json
import os
import sys

import residue_triage as RT

SUITE_LABEL = "os-residue-batch-status-face"

NOT_RESIDUE = "NOT-RESIDUE"

REPORT_KEYS = (
    "action",
    "requested",
    "requested_status",
    "round_count",
    "counts",
    "verdict",
    "rounds",
    "statuses",
    "source",
)

UNREADABLE_CODES = (
    "E_RSBF_BAD_STATE",
    "E_RSBF_BAD_VOCABULARY",
)


class ResidueBatchStatusFaceError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _vocabulary():
    """The status vocabulary, read off stamp_residue at call time (AC-RSBF1)."""
    import stamp_residue as SR
    statuses = getattr(SR, "STATUSES", None)
    if not statuses:
        raise ResidueBatchStatusFaceError(
            "E_RSBF_BAD_VOCABULARY",
            "stamp_residue exposes no STATUSES to report")
    return tuple(statuses)


def status_map(root):
    """Every residue round with its live status (AC-RSBF1, AC-RSBF2)."""
    try:
        rows = RT.live_residue(root)
    except RT.ResidueTriageError as exc:
        raise ResidueBatchStatusFaceError(
            "E_RSBF_BAD_STATE", "%s: %s" % (exc.code, exc.detail))
    out = []
    for row in rows:
        out.append({"round": int(row["round"]), "status": row["status"]})
    out.sort(key=lambda item: item["round"])
    return out


def counts_of(rows):
    """One '<STATUS>=<n>' entry per stamp_residue status, in its own order."""
    statuses = _vocabulary()
    seen = {}
    for row in rows:
        seen[row["status"]] = seen.get(row["status"], 0) + 1
    out = []
    for status in statuses:
        out.append("%s=%d" % (status, seen.get(status, 0)))
    for status in sorted(seen):
        if status not in statuses:
            out.append("%s=%d" % (status, seen[status]))
    return out


def face(root, requested=None):
    """The reading, optionally asked about one round (AC-RSBF2, AC-RSBF3)."""
    rows = status_map(root)
    requested_label = "-"
    requested_status = "-"
    verdict = "MAP"
    if requested is not None:
        try:
            number = RT.parse_round(requested, "requested round")
        except RT.ResidueTriageError as exc:
            raise ResidueBatchStatusFaceError(
                "E_RSBF_BAD_ARGS", "%s: %s" % (exc.code, exc.detail))
        requested_label = "R%d" % number
        for row in rows:
            if row["round"] == number:
                requested_status = row["status"]
                verdict = "FOUND"
        if verdict != "FOUND":
            requested_status = NOT_RESIDUE
            verdict = NOT_RESIDUE
    return {
        "action": "check",
        "requested": requested_label,
        "requested_status": requested_status,
        "round_count": len(rows),
        "counts": counts_of(rows),
        "verdict": verdict,
        "rounds": ["R%d" % row["round"] for row in rows],
        "statuses": [row["status"] for row in rows],
        "source": "stamp_residue via residue_triage",
    }


def one_line(report):
    """The single line an operator reads."""
    counts = ",".join(report["counts"]) or "-"
    return ("RESIDUE BATCH STATUS action=%s rounds=%d requested=%s "
            "requested_status=%s counts=%s verdict=%s source=%s"
            % (report["action"], report["round_count"], report["requested"],
               report["requested_status"], counts, report["verdict"],
               report["source"]))


def render(report):
    """The one line, then every residue round WITH its live status."""
    out = [one_line(report)]
    for index, label in enumerate(report["rounds"]):
        status = report["statuses"][index]
        out.append("  ROUND %s status=%s" % (label, status))
    if report["verdict"] == NOT_RESIDUE:
        out.append("  %s %s is not in the live residue"
                   % (NOT_RESIDUE, report["requested"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (byte-stable)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: residue_batch_status_face.py --check [--round R<n>]\n"
         "         [--root PATH] [--json]\n"
         "  exit 0 = the live status of every residue round was read\n"
         "  exit 2 = --round names a round the live residue does not carry\n"
         "           (NOT-RESIDUE, E_RSBF_NOT_RESIDUE)\n"
         "  exit 3 = the residue cannot be read in this root\n"
         "  exit 5 = bad flags\n")


def main(argv):
    mode = None
    as_json = False
    round_text = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            mode = "check"
        elif arg == "--json":
            as_json = True
        elif arg in ("--round", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RSBF_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            if arg == "--round":
                round_text = argv[index]
            else:
                root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RSBF_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1

    if mode != "check":
        sys.stdout.write("E_RSBF_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5

    try:
        report = face(root, round_text)
    except ResidueBatchStatusFaceError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code == "E_RSBF_BAD_ARGS":
            return 5
        if exc.code == "E_RSBF_NOT_RESIDUE":
            return 2
        return 3

    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == NOT_RESIDUE:
        sys.stdout.write("E_RSBF_NOT_RESIDUE: %s is not in the live residue\n"
                         % report["requested"])
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))