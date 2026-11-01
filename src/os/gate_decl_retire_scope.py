# gate_decl_retire_scope.py - a retired blocker needs its row to be DONE
# Criteria AC-GDRTS1..AC-GDRTS6 were pre-registered in state/queue/tech.md (the
# R2319 seed row) BEFORE this file existed.
#
# Why this exists: R2319's wire refuses every MATCHED identity, because a
# matched row still carries the address. That is right for an OPEN or GATED
# row and wrong for a COMPLETED one: AC-GDRTW3 measured that the gated fixture
# and the done fixture refuse identically, so a declared blocker whose row was
# finished can never be retired and the declaration rots in the opposite
# direction from the one R2317 named.
#
# This module is the scope reading, not a second writer: it takes the identity
# reading from gate_decl_identity (rows + resolve, both imported) and hands
# gate_decl_retire.plan the only case it should ever have owned - an identity
# whose carrier row is level DONE, plus an UNMATCHED identity that no row
# carries at all. A matched OPEN or GATED row refuses here with its level in
# the detail, and AMBIGUOUS keeps refusing with every carrier named.
#
# Imported law, never copied: the row level comes from gate_decl_identity.rows
# (queue path, row law and gate marker all arrive through it), the address
# resolution from that reader's resolve, and the splice, still-blocked
# refusal and read-back from gate_decl_retire. This module scans no queue and
# re-renders no entry.
#
# Dry run is the default: plan() returns the scope verdict, the reader state
# and the before/after byte counts and writes nothing. execute=True performs
# gate_decl_retire's one atomic replace and proves the read-back.
#
# Pure ASCII source, stdlib only, zero network, no clock read.
#
# CLI: gate_decl_retire_scope.py --identity ID [--queue NAME] [--decl PATH]
#      [--root PATH] [--execute] [--json]
#   exit 0 = planned (or retired with --execute)
#   exit 2 = refused (matched open / matched gated / ambiguous / undeclared /
#            still blocked / bad field / shape or write-readback failure)
#   exit 3 = queue or declaration missing / unreadable / malformed
#   exit 5 = bad flags

import json
import os
import sys

import gate_decl_identity as GDI
import gate_decl_retire as GDRT

SCOPE_ALLOWED = "RETIRE-ALLOWED"
SCOPE_REFUSED = "RETIRE-REFUSED"

VERDICT_PLANNED = "PLANNED"
VERDICT_RETIRED = "RETIRED"

REPORT_KEYS = ("path", "queue", "identity", "capability", "state", "line",
               "prefix", "level", "claimable", "detail", "carriers", "scope",
               "removed_at", "declarations_before", "declarations_after",
               "before_bytes", "predicted_bytes", "wrote", "read_back_ok",
               "verdict")

SCOPE_REFUSALS = ("E_GDRTS_MATCHED", "E_GDRTS_AMBIGUOUS")
REFUSE_CODES = SCOPE_REFUSALS + GDRT.REFUSAL_CODES


class ScopeError(Exception):
    """Raised when the scope reading cannot hand the plan an honest case."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def carrier_lines(carriers):
    """The carrier rows as a stable, one-line address list."""
    if not carriers:
        return "none"
    return ",".join("L%d" % row["line"] for row in carriers)


def scope_of(reading):
    """Map one identity reading to the scope verdict (AC-GDRTS2/3).

    A matched DONE row is the one matched case a retirement may act on; a
    matched OPEN or GATED row still carries a live blocker, and an AMBIGUOUS
    reading names no single row at all. An UNMATCHED identity is allowed: no
    row carries the address, so the declaration is the only holder.
    """
    if reading["state"] == "UNMATCHED":
        return SCOPE_ALLOWED, None
    if reading["state"] == "AMBIGUOUS":
        return SCOPE_REFUSED, "E_GDRTS_AMBIGUOUS"
    if reading["level"] == "done":
        return SCOPE_ALLOWED, None
    return SCOPE_REFUSED, "E_GDRTS_MATCHED"


def read_scope(root, identity, name="tech"):
    """The reader: identity reading plus the scope verdict, nothing written."""
    try:
        found = GDI.rows(root, name)
    except GDI.GateIdentityError as exc:
        raise ScopeError("E_GDRTS_" + exc.code.replace("E_GDI_", ""),
                         exc.detail)
    reading = GDI.resolve(identity, found)
    scope, refusal = scope_of(reading)
    return {"state": reading["state"],
            "line": reading["line"],
            "prefix": reading["prefix"],
            "level": reading["level"],
            "claimable": reading["claimable"],
            "detail": reading["detail"],
            "carriers": reading["carriers"],
            "scope": scope,
            "refusal": refusal}


def plan(root, identity, queue_name="tech", declaration=None, execute=False):
    """Scope first, then plan (or retire) under gate_decl_retire's own law."""
    reading = read_scope(root, identity, queue_name)
    if reading["scope"] != SCOPE_ALLOWED:
        if reading["refusal"] == "E_GDRTS_AMBIGUOUS":
            raise ScopeError(
                "E_GDRTS_AMBIGUOUS",
                "identity %r resolves AMBIGUOUS (%s); carriers %s"
                % (identity, reading["detail"],
                   carrier_lines(reading["carriers"])))
        raise ScopeError(
            "E_GDRTS_MATCHED",
            "identity %r resolves MATCHED at level %s (line %s); only a done "
            "row may be retired, so the declaration is still doing its job"
            % (identity, reading["level"], reading["line"]))
    try:
        report = GDRT.retire(root, identity, queue_name, declaration, execute)
    except GDRT.GateDeclRetireError as exc:
        raise ScopeError(exc.code, exc.detail)
    merged = {"queue": queue_name,
              "state": reading["state"],
              "line": reading["line"],
              "prefix": reading["prefix"],
              "level": reading["level"],
              "claimable": reading["claimable"],
              "detail": reading["detail"],
              "carriers": reading["carriers"],
              "scope": reading["scope"]}
    for key in GDRT.REPORT_KEYS:
        if key in report:
            merged[key] = report[key]
    merged["verdict"] = VERDICT_RETIRED if report.get("wrote") \
        else VERDICT_PLANNED
    return merged


def one_line(report):
    """A single ASCII line for a CLI caller that reads stdout by eye."""
    return ("%s identity=%s state=%s level=%s scope=%s declarations=%s->%s "
            "bytes=%s->%s"
            % (report.get("verdict"),
               report.get("identity"),
               report.get("state"),
               report.get("level"),
               report.get("scope"),
               report.get("declarations_before"),
               report.get("declarations_after"),
               report.get("before_bytes"),
               report.get("predicted_bytes")))


def to_json(report):
    """One byte-stable rendering over the pinned keys, in pinned order."""
    ordered = {}
    for key in REPORT_KEYS:
        if key in report:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, indent=2,
                      sort_keys=False) + "\n"


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
                raise ScopeError("E_GDRTS_BAD_ARGS", arg + " needs a value")
            opts[takes[arg]] = argv[index + 1]
            index += 2
        else:
            raise ScopeError("E_GDRTS_BAD_ARGS", arg)
    if not opts["identity"]:
        raise ScopeError("E_GDRTS_BAD_ARGS", "--identity is required")
    if opts["root"] is None:
        opts["root"] = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", ".."))
    return opts


def main(argv):
    try:
        opts = parse_args(argv)
    except ScopeError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5
    try:
        report = plan(opts["root"], opts["identity"], opts["queue"],
                      declaration=opts["decl"], execute=opts["execute"])
    except ScopeError as exc:
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