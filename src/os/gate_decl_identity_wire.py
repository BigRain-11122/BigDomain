# gate_decl_identity_wire.py - the gate declaration writer asks the identity
# reader before it plans a single byte.
# Criteria AC-GDIW1..AC-GDIW6 were pre-registered in state/queue/tech.md as the
# R2314 seed row BEFORE this file existed.
#
# Why this exists: R2314 shipped gate_decl_identity, a reader that resolves a
# declared identity against the live queue rows, and measured the gap at once:
# gate_decl_append planned "--identity -" as a brand-new declaration (427B ->
# 547B) while the reader resolved the same text as AMBIGUOUS over four
# carriers. The writer owned its own permissive address rule, so a
# misaddressed blocker could land silently and read INERT against every row
# forever.
#
# This module is the wire, not a second writer: it resolves the planned
# identity through gate_decl_identity (rows + resolve, both imported) and only
# a MATCHED identity - one row carries it - is handed to gate_decl_append.plan,
# which keeps owning the splice, the duplicate refusal and the read-back.
# UNMATCHED and AMBIGUOUS are refused here, before any byte changes, with the
# reader state and its carrier lines in the detail.
#
# Imported law, never copied: the queue path and text come from queue_head
# through gate_decl_identity.rows, the identity address law from that reader's
# resolve, the declaration shape and capability vocabulary from machine_gate
# through gate_decl_append. This module scans no queue and re-renders no entry.
#
# Dry run is the default: plan() returns the reader state, the before/after
# byte counts and writes nothing. execute=True performs gate_decl_append's one
# atomic replace and proves the read-back.
#
# Pure ASCII source, stdlib only, zero network, no clock read.
#
# CLI: gate_decl_identity_wire.py --identity ID --capability CAP --reason TEXT
#      --declared-by R<nnnn> [--queue tech] [--decl PATH] [--root PATH]
#      [--execute] [--json]
#   exit 0 = planned (or appended with --execute)
#   exit 2 = refused (identity UNMATCHED / AMBIGUOUS, duplicate, unknown
#            capability, bad field, shape or write/read-back failure)
#   exit 3 = queue or declaration missing / unreadable / malformed
#   exit 5 = bad flags

import io
import json
import os
import sys

import gate_decl_append as GDA
import gate_decl_identity as GDI

REPORT_KEYS = ("path", "queue", "identity", "capability", "reason",
               "declared_by", "state", "line", "prefix", "level",
               "claimable", "detail", "carriers", "declarations_before",
               "declarations_after", "before_bytes", "predicted_bytes",
               "wrote", "read_back_ok", "verdict")

VERDICT_PLANNED = "PLANNED"
VERDICT_APPENDED = "APPENDED"

REFUSE_CODES = ("E_GDIW_UNMATCHED", "E_GDIW_AMBIGUOUS") + GDA.REFUSAL_CODES
INPUT_CODES = ("E_GDIW_NO_QUEUE", "E_GDIW_BAD_QUEUE", "E_GDA_NO_DECL",
               "E_GDA_BAD_DECL")


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
        raise WireError("E_GDIW_" + exc.code.replace("E_GDI_", ""), exc.detail)
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


def plan(root, identity, capability, reason, declared_by, declaration=None,
         name="tech", execute=False):
    """Resolve, then plan (or append) under gate_decl_append's own law."""
    reading = resolve_identity(root, identity, name)
    if reading["state"] != "MATCHED":
        raise WireError(
            "E_GDIW_" + reading["state"],
            "identity %r resolves %s (%s); carriers %s"
            % (identity, reading["state"], reading["detail"],
               carrier_lines(reading["carriers"])))
    try:
        report = GDA.append_gate(root, identity, capability, reason,
                                 declared_by, declaration=declaration,
                                 execute=execute)
    except GDA.GateDeclAppendError as exc:
        raise WireError(exc.code, exc.detail)
    merged = {"queue": name,
              "state": reading["state"],
              "line": reading["line"],
              "prefix": reading["prefix"],
              "level": reading["level"],
              "claimable": reading["claimable"],
              "detail": reading["detail"],
              "carriers": reading["carriers"]}
    for key in GDA.REPORT_KEYS:
        if key in report:
            merged[key] = report[key]
    merged["verdict"] = VERDICT_APPENDED if report.get("wrote") \
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
    opts = {"identity": None, "capability": None, "reason": None,
            "declared_by": None, "queue": "tech", "decl": None, "root": None,
            "execute": False, "json": False}
    takes = {"--identity": "identity", "--capability": "capability",
             "--reason": "reason", "--declared-by": "declared_by",
             "--queue": "queue", "--decl": "decl", "--root": "root"}
    flags = {"--execute": "execute", "--json": "json"}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in flags:
            opts[flags[arg]] = True
            index += 1
        elif arg in takes:
            if index + 1 >= len(argv) or not argv[index + 1]:
                raise WireError("E_GDIW_BAD_ARGS", arg + " needs a value")
            opts[takes[arg]] = argv[index + 1]
            index += 2
        else:
            raise WireError("E_GDIW_BAD_ARGS", arg)
    for key in ("identity", "capability", "reason", "declared_by"):
        if not opts[key]:
            raise WireError("E_GDIW_BAD_ARGS", "--%s is required"
                            % key.replace("_", "-"))
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
        report = plan(opts["root"], opts["identity"], opts["capability"],
                      opts["reason"], opts["declared_by"],
                      declaration=opts["decl"], name=opts["queue"],
                      execute=opts["execute"])
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
        if code in INPUT_CODES:
            sys.stderr.write("%s\n" % exc)
            return 3
        sys.stderr.write("%s\n" % exc)
        return 3
    if opts["json"]:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(one_line(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))