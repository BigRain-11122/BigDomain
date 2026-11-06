# export_consistency_queue_face.py - the 21-check face learns to see the queue
# Criteria AC-ECQF1..AC-ECQF6 were pre-registered in state/queue/tech.md:533
# (the R2497 seed row) BEFORE this file existed.
#
# Why this exists: check_export_consistency is the face every window trusts, and
# it validates the eleven self_drive fields, the tick row, the CEO face, the
# containers and its own ASCII hygiene - twenty-one checks that never open the
# queue block. MEASURED at R2497: a copy of the real export whose queue block was
# doctored (verdict FLOOR-DEBT, tech claimable 0) still read pass=21 fail=0 while
# queue_export_freshness_gate on the same document read STALE with
# drifted=section:shortfall_total, section:delivered_total, queue:tech.
#
# This face gives the trusted reading a queue eye. It asks the shipped gate at
# CALL time (AC-ECQF1) and publishes the gate's verdict beside the twenty-one
# checks instead of inside them (AC-ECQF3), so a document edited after the driver
# published it reads DRIFT rather than PASS. On a CURRENT document the base
# lines, their order and the exit code are exactly today's, plus one queue line
# (AC-ECQF4). It writes nothing and reads no clock of its own (AC-ECQF5).
#
# Pure derivation, no second row parser and no canned number.
# Source is pure ASCII, stdlib only, no network.
#
# CLI: export_consistency_queue_face.py --check [--root PATH] [--export PATH]
#                                       [--json]
#   exit 0 = the base checks pass and the queue block is CURRENT
#   exit 2 = base drift, or a STALE queue block (drifted named on its own line)
#   exit 3 = the export file is missing or unreadable
#   exit 5 = the flags are bad

import json
import os
import sys

import check_export_consistency as CEC
import queue_export_freshness_gate as QEF

NAME = "export-consistency-queue-face"
LABEL = "os-export-consistency-queue-face"
BASE_CHECKS = 21
DEFAULT_EXPORT = QEF.DEFAULT_EXPORT

USAGE = (
    "usage: export_consistency_queue_face.py --check [--root PATH] "
    "[--export PATH] [--json]\n"
    "  --check        run the twenty-one base checks plus the queue reading\n"
    "  --root PATH    repository root to read the queues from (default .)\n"
    "  --export PATH  export document to check "
    "(default docs/status-export.json)\n"
    "  --json         emit one machine-readable object\n"
    "  exit 0 = base PASS and queue CURRENT, 2 = DRIFT, "
    "3 = export missing, 5 = bad flags\n"
)


class ExportConsistencyQueueFaceError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def queue_line(queue_verdict, drifted):
    """The one additional line the face appends after the twenty-one checks."""
    return "QUEUE %s verdict=%s drifted=%s" % (
        QEF.LABEL, queue_verdict, ",".join(drifted) if drifted else "(none)")


def read(root=".", export_path=None):
    """The twenty-one shipped checks plus the live queue reading, at CALL time."""
    base_lines, base_pass, base_fail = CEC.check()
    path = export_path or os.path.join(root, DEFAULT_EXPORT)
    try:
        result, queue_code = QEF.check(root, path)
        queue_verdict = result["verdict"]
        drifted = list(result.get("drifted") or [])
    except QEF.QueueExportFreshnessGateError as exc:
        queue_verdict = "UNAVAILABLE"
        drifted = ["export:%s" % exc.code]
        queue_code = 3
    verdict = "AGREE" if queue_code == 0 and not base_fail else "DRIFT"
    exit_code = 3 if queue_code == 3 else (
        2 if (queue_code == 2 or base_fail) else 0)
    return {
        "label": LABEL,
        "verdict": verdict,
        "base_checks": base_pass + base_fail,
        "base_pass": base_pass,
        "base_fail": base_fail,
        "base_lines": list(base_lines),
        "queue_label": QEF.LABEL,
        "queue_verdict": queue_verdict,
        "queue_drifted": drifted,
        "queue_line": queue_line(queue_verdict, drifted),
        "exit_code": exit_code,
    }


def _emit(text):
    """Write LF-only bytes: a text-mode stdout would translate to CRLF."""
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is not None:
        buffer.write(text.encode("utf-8"))
        buffer.flush()
    else:
        sys.stdout.write(text)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0

    root = "."
    export = DEFAULT_EXPORT
    as_json = False
    saw_check = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            saw_check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--export"):
            index += 1
            if index >= len(argv):
                sys.stderr.write("E_ECQF_BAD_FLAGS missing value for %s\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            else:
                export = argv[index]
        else:
            sys.stderr.write("E_ECQF_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_ECQF_BAD_FLAGS --check is required\n")
        return 5

    try:
        result = read(root, export)
    except Exception as exc:  # fail-closed on any unreadable/malformed input
        sys.stderr.write("E_ECQF_FATAL %s: %s\n" % (type(exc).__name__, exc))
        return 3

    if as_json:
        _emit(json.dumps(result, ensure_ascii=False) + "\n")
    else:
        report = "".join(line + "\n" for line in result["base_lines"])
        report += result["queue_line"] + "\n"
        report += "VERDICT %s base=%d/%d queue=%s\n" % (
            result["verdict"], result["base_pass"],
            result["base_checks"], result["queue_verdict"])
        _emit(report)
    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))