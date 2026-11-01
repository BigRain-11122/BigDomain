# gate_decl_retire_wire.py - the retire writer asks the identity reader first
# Criteria AC-GDRTW1..AC-GDRTW6 were pre-registered in state/queue/tech.md as
# the R2317 seed row BEFORE this file existed.
#
# Why this exists: gate_decl_retire asks machine_gate's candidate reading,
# which only ever sees a CLAIMABLE row. An entry whose row exists but carries
# no criteria prefix therefore reads INERT and is offered for retirement while
# the declaration is still the truth. R2317 measured it live: the docker entry
# "-#02878cdc" read PLANNED for retirement (declarations 1->0) even though
# gate_decl_identity reports that same identity MATCHED at line 41.
#
# This module is the wire, not a second writer: it resolves the identity
# through gate_decl_identity (rows + resolve, both imported) and only an
# UNMATCHED identity - no row carries it - is handed to gate_decl_retire.retire,
# which keeps owning the splice, the still-blocked refusal and the read-back.
# MATCHED and AMBIGUOUS are refused here, before any byte changes, with the
# reader state and every carrier line in the detail - the same shape
# gate_decl_identity_wire already gives the append path.
#
# Imported law, never copied: the queue path and text come from queue_head
# through gate_decl_identity.rows, the identity address law from that reader's
# resolve, the declaration shape from machine_gate through gate_decl_retire.
# This module scans no queue and re-renders no entry.
#
# Dry run is the default: plan() returns the reader state, the before/after
# byte counts and writes nothing. execute=True performs gate_decl_retire's one
# atomic replace and proves the read-back.
#
# Pure ASCII source, stdlib only, zero network, no clock read.
#
# CLI: gate_decl_retire_wire.py --identity ID [--queue NAME] [--decl PATH]
#      [--root PATH] [--execute] [--json]
#   exit 0 = planned (or retired with --execute)
#   exit 2 = refused (identity MATCHED / AMBIGUOUS, undeclared, still
#            blocked, bad field, shape or write/read-back failure)
#   exit 3 = queue or declaration missing / unreadable / malformed
#   exit 5 = bad flags

import json
import os
import sys

import gate_decl_identity as GDI
import gate_decl_retire as GDRT

REPORT_KEYS = ("path", "queue", "identity", "capability", "state", "line",
               "prefix", "level", "claimable", "detail", "carriers",
               "removed_at", "declarations_before", "declarations_after",
               "before_bytes", "predicted_bytes", "wrote", "read_back_ok",
               "verdict")

VERDICT_PLANNED = "PLANNED"
VERDICT_RETIRED = "RETIRED"

REFUSE_CODES = ("E_GDRTW_MATCHED", "E_GDRTW_AMBIGUOUS") + GDRT.REFUSAL_CODES
INPUT_CODES = ("E_GDRTW_NO_QUEUE", "E_GDRTW_BAD_QUEUE", "E_GDRT_NO_DECL",
               "E_GDRT_BAD_DECL")


class WireError(Exception):
    """Raised when the wire cannot plan without guessing."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def carrier_lines(carriers):
    """The carrier rows as a stable, one-line address list."""
    if not carriers:
        return "none"
    return ",".join("L%d" % row["line"] for row in carriers)


def resolve_identity(root, identity, name="tech"):
    """Resolve one identity through the reader's own rows and resolve."""
    try:
        found = GDI.rows(root, name)
    except GDI.GateIdentityError as exc:
        raise WireError("E_GDRTW_" + exc.code.replace("E_GDI_", ""),
                        exc.detail)
    reading = GDI.resolve(identity, found)
    return {
        "state": reading["state"],
        "line": reading["line"],
        "prefix": reading["prefix"],
        "level": reading["level"],
        "claimable": reading["claimable"],
        "detail": reading["detail"],
        "carriers": reading["carriers"],
    }


def plan(root, identity, queue_name="tech", declaration=None, execute=False):
    """Resolve, then plan (or retire) under gate_decl_retire's own law."""
    reading = resolve_identity(root, identity, queue_name)
    if reading["state"] != "UNMATCHED":
        raise WireError(
            "E_GDRTW_" + reading["state"],
            "identity %r resolves %s (%s); carriers %s"
            % (identity, reading["state"], reading["detail"],
               carrier_lines(reading["carriers"])))
    try:
        report = GDRT.retire(root, identity, queue_name, declaration, execute)
    except GDRT.GateDeclRetireError as exc:
        raise WireError(exc.code, exc.detail)
    merged = {"queue": queue_name,
              "state": reading["state"],
              "line": reading["line"],
              "prefix": reading["prefix"],
              "level": reading["level"],
              "claimable": reading["claimable"],
              "detail": reading["detail"],
              "carriers": reading["carriers"]}
    for key in GDRT.REPORT_KEYS:
        if key in report:
            merged[key] = report[key]
    merged["verdict"] = VERDICT_RETIRED if report.get("wrote") \
        else VERDICT_PLANNED
    return merged


def to_json(report):
    """One byte-stable rendering over the pinned keys, in pinned order."""
    ordered = {}
    for key in REPORT_KEYS:
        if key in report:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, indent=2,
                      sort_keys=False) + "\n"


def one_line(report):
    """A single ASCII line for a CLI caller that reads stdout by eye."""
    return ("%s identity=%s state=%s line=%s declarations=%s->%s bytes=%s->%s"
            % (report.get("verdict"),
               report.get("identity"),
               report.get("state"),
               report.get("line"),
               report.get("declarations_before"),
               report.get("declarations_after"),
               report.get("before_bytes"),
               report.get("predicted_bytes")))


def parse_args(argv):
    """Pinned flags only; anything else is bad flags (exit 5)."""
    opts = {"identity": None, "queue": "tech", "decl": None, "root": None,
            "execute": False, "json": False}
    takes = {"--identity": "identity", "--queue": "queue", "--decl": "decl",
             "--root": "root"}
    flags = {"--execute": "execute", "--json": "json"}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in flags:
            opts[flags[arg]] = True
            index += 1
        elif arg in takes:
            if index + 1 >= len(argv) or not argv[index + 1]:
                raise WireError("E_GDRTW_BAD_ARGS", arg + " needs a value")
            opts[takes[arg]] = argv[index + 1]
            index += 2
        else:
            raise WireError("E_GDRTW_BAD_ARGS", arg)
    if not opts["identity"]:
        raise WireError("E_GDRTW_BAD_ARGS", "--identity is required")
    if opts["root"] is None:
        opts["root"] = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", ".."))
    return opts


def main(argv):
    try:
        opts = parse_args(argv)
    except WireError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5
    try:
        report = plan(opts["root"], opts["identity"], opts["queue"],
                      declaration=opts["decl"], execute=opts["execute"])
    except WireError as exc:
        code = exc.code
        if code in REFUSE_CODES:
            if opts["json"]:
                sys.stdout.write(json.dumps({"verdict": "REFUSED",
                                             "code": code,
                                             "detail": exc.detail},
                                            ensure_ascii=True, indent=2) + "\n")
            else:
                sys.stdout.write("REFUSED %s %s\n" % (code, exc.detail))
            return 2
        sys.stderr.write("%s\n" % exc)
        return 3
    if opts["json"]:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(one_line(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))