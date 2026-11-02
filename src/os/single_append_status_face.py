# single_append_status_face.py - the live status of the ONE round a single
# --append is about, in the shape that composes it
# Criteria AC-SASF1..AC-SASF6 were pre-registered inside the R2379 seed row of
# state/queue/tech.md BEFORE this file existed.
#
# Why this exists: residue_batch_status_face gave the BATCH writer the live
# status of every residue round, and residue_triage_append_batch asks it at
# call time. The SINGLE writer still printed no status at all, so composing one
# --append meant running the batch face by hand and guessing - which is the
# same refused call the batch CLI no longer costs (measured at R2379: the
# single CLI answered without statuses while the batch CLI carried them).
#
# This module is that one reading and nothing else:
#   * the status of the asked round IS residue_batch_status_face's reading,
#     imported at CALL time, so patching that face moves what is printed here
#     (AC-SASF1). No second residue scan, no queue parse and no stamp regex
#     live in this file;
#   * the asked round is named WITH its live status, so one --check call is
#     enough to compose a single --append (AC-SASF2);
#   * a round the live residue does not carry reads NOT-RESIDUE with its own
#     code rather than an invented status (AC-SASF3);
#   * this file writes nothing, reads no clock, imports no network, and is
#     pure ASCII stdlib (AC-SASF6).
#
# The single writer asks this module from its --check path only; its --append
# path never reaches it, which is what keeps every append refusal code and
# printed line byte-identical (AC-SASF4).
#
# Pure read: nothing is written, no clock, no network.

import json
import os
import sys

SUITE_LABEL = "os-single-append-status-face"

NOT_RESIDUE = "NOT-RESIDUE"

REPORT_KEYS = (
    "action",
    "requested",
    "requested_status",
    "found",
    "verdict",
    "round_count",
    "source",
)


class SingleAppendStatusFaceError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _face(root, requested):
    """The batch face's own reading, asked at call time (AC-SASF1)."""
    import residue_batch_status_face as RSBF
    try:
        return RSBF.face(root, requested)
    except RSBF.ResidueBatchStatusFaceError as exc:
        code = "E_SASF_BAD_STATE"
        if exc.code == "E_RSBF_BAD_ARGS":
            code = "E_SASF_BAD_ARGS"
        raise SingleAppendStatusFaceError(
            code, "%s: %s" % (exc.code, exc.detail))


def reading(root, requested):
    """The one round, with the status the live residue reports (AC-SASF2)."""
    face = _face(root, requested)
    verdict = face["verdict"]
    return {
        "action": "check",
        "requested": face["requested"],
        "requested_status": face["requested_status"],
        "found": verdict == "FOUND",
        "verdict": NOT_RESIDUE if verdict == NOT_RESIDUE else verdict,
        "round_count": face["round_count"],
        "source": face["source"],
    }


def one_line(report):
    """The single line an operator reads (AC-SASF2)."""
    return ("SINGLE APPEND STATUS action=%s requested=%s requested_status=%s "
            "found=%s rounds=%d verdict=%s source=%s"
            % (report["action"], report["requested"],
               report["requested_status"],
               "yes" if report["found"] else "no", report["round_count"],
               report["verdict"], report["source"]))


def render(report):
    """The one line, then the honest note when the round is not residue."""
    out = [one_line(report)]
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


USAGE = ("usage: single_append_status_face.py --check --round R<n>\n"
         "         [--root PATH] [--json]\n"
         "  exit 0 = the asked round is in the live residue and its status\n"
         "           was read\n"
         "  exit 2 = --round names a round the live residue does not carry\n"
         "           (NOT-RESIDUE, E_SASF_NOT_RESIDUE)\n"
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
                sys.stdout.write("E_SASF_BAD_ARGS: %s needs a value\n" % arg)
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
            sys.stdout.write("E_SASF_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1

    if mode != "check":
        sys.stdout.write("E_SASF_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    if round_text is None:
        sys.stdout.write("E_SASF_BAD_ARGS: --round is required\n")
        sys.stdout.write(USAGE)
        return 5

    try:
        report = reading(root, round_text)
    except SingleAppendStatusFaceError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code == "E_SASF_BAD_ARGS":
            return 5
        return 3

    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == NOT_RESIDUE:
        sys.stdout.write("E_SASF_NOT_RESIDUE: %s is not in the live residue\n"
                         % report["requested"])
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))