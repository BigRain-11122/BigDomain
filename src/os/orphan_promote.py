"""orphan_promote (R2339; criteria AC-OTP1..AC-OTP6 were pre-registered inside
the R2323 seed row of state/queue/tech.md:387 BEFORE this file existed).

orphan_trace resolves which leg of an ORPHAN round stands in (live: R2136
reads TRACE-EXISTS with reconcile-all-R2136c.log RUNNER PASS and
reconcile-all-R2136b.log RUNNER FAIL), but nothing could ACT on that reading:
the green leg stayed stranded under a variant name, so followup_history could
not see the round at all and the operator had to hand-copy a 675KB log while
hoping the copy was faithful and that no canonical leg appeared meanwhile.

This module is the one writer for that operation, and it is narrow:

  * the orphan round, its legs and its standing-in leg are all asked of
    orphan_trace (imported, never re-derived - AC-OTP1), so a patched reading
    flows straight through;
  * a plan names the source leg, the canonical target, the byte count and the
    digest; a standings-only pick (no --src) prefers the FIRST RUNNER PASS leg
    in name order and names every other leg that carries PASS (AC-OTP2);
  * a round reading NO-TRACE refuses with its own code, a named source that
    does not carry RUNNER PASS refuses naming the green legs instead of
    promoting a failure, and an existing canonical target refuses before any
    byte is written (AC-OTP3);
  * a dry run is the default and writes nothing; an executed promotion COPIES
    (never moves) so the variant leg survives its own promotion, writes
    exactly one new file proved by read-back with no temp residue, and proves
    the source is still byte-identical (AC-OTP4);
  * CLI exits 0 on a plan or a performed promotion, 2 on any refusal over live
    state, 3 on unreadable input or a missing evidence directory, 5 on bad
    flags, with a byte-stable --json over pinned keys and no clock (AC-OTP5);
  * pure ASCII source, stdlib only, zero network, plus its own reconcile
    label (AC-OTP6).

No delete path exists here: the only mutation is one os.replace of a file this
module itself just wrote, and the source leg is only ever read.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import orphan_trace as OT

SUITE_LABEL = "os-orphan-promote"

REPORT_KEYS = ("action", "round", "source", "target", "source_bytes",
               "digest", "standing_in", "green_legs", "other_green", "wrote",
               "verdict")

_DECODE_MAP = {
    OT.E_OTR_NO_EVIDENCE: "E_OTP_NO_EVIDENCE",
    OT.E_OTR_UNREADABLE: "E_OTP_UNREADABLE",
    OT.E_OTR_BAD_NAME: "E_OTP_BAD_NAME",
    OT.E_OTR_UNDECODABLE: "E_OTP_UNDECODABLE",
}

PART_SUFFIX = ".part"


class OrphanPromoteError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parse_round(value):
    """One round reference: R2136, 2136 or 2136 int. Nothing else."""
    if isinstance(value, bool):
        raise OrphanPromoteError("E_OTP_BAD_ARGS", "round must be a number")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str):
        text = value.strip()
        if text[:1] in ("R", "r"):
            text = text[1:]
        if not text.isdigit():
            raise OrphanPromoteError("E_OTP_BAD_ARGS",
                                     "round %r is not a round number" % value)
        number = int(text)
    else:
        raise OrphanPromoteError("E_OTP_BAD_ARGS",
                                 "round %r is not a round number" % (value,))
    if number <= 0:
        raise OrphanPromoteError("E_OTP_BAD_ARGS", "round must be positive")
    return number


def canonical_name(number):
    """The canonical evidence name a promoted round must carry."""
    return "reconcile-all-R%d.log" % number


def traces(root, directory="qa"):
    """The whole orphan reading, asked of orphan_trace (AC-OTP1)."""
    try:
        return OT.traces(root, directory)
    except OT.OrphanTraceError as exc:
        raise OrphanPromoteError(_DECODE_MAP.get(exc.code, "E_OTP_UNREADABLE"),
                                 exc.detail or exc.code)


def _trace_of(report, number):
    for item in report["rounds"]:
        if int(item["round"][1:]) == number:
            return item
    raise OrphanPromoteError(
        "E_OTP_NO_ROUND",
        "R%d is not an orphan round of %s (%d orphan round(s) there)"
        % (number, report["dir"], report["counts"]["rounds"]))


def _green(trace):
    """Every leg carrying RUNNER PASS, in name order (AC-OTP2)."""
    return [leg["name"] for leg in trace["legs"] if leg["runner"] == "PASS"]


def _standings(trace):
    """One line per leg: name with its runner and verdict tokens."""
    parts = []
    for leg in trace["legs"]:
        parts.append("%s runner=%s verdict=%s"
                     % (leg["name"], leg["runner"] or "-",
                        leg["verdict"] or "-"))
    return "; ".join(parts)


def plan(root, round_value, directory="qa", source=None):
    """Everything except the write: refusals, source, target, bytes, digest."""
    number = parse_round(round_value)
    report = traces(root, directory)
    trace = _trace_of(report, number)
    if trace["status"] != "TRACE-EXISTS":
        raise OrphanPromoteError(
            "E_OTP_NO_TRACE",
            "R%d reads %s: no leg carries a runner line (%s)"
            % (number, trace["status"], _standings(trace)))
    greens = _green(trace)
    if source is None:
        if not greens:
            raise OrphanPromoteError(
                "E_OTP_NOT_GREEN",
                "R%d carries no RUNNER PASS leg (%s)"
                % (number, _standings(trace)))
        source = greens[0]
        other_green = greens[1:]
    else:
        names = [leg["name"] for leg in trace["legs"]]
        if source not in names:
            raise OrphanPromoteError(
                "E_OTP_BAD_SOURCE",
                "%s is not one of the legs of R%d (%s)"
                % (source, number, ", ".join(names)))
        runners = {}
        for leg in trace["legs"]:
            runners[leg["name"]] = leg["runner"]
        if runners[source] != "PASS":
            raise OrphanPromoteError(
                "E_OTP_NOT_GREEN",
                "%s carries RUNNER %s; the green legs are %s"
                % (source, runners[source] or "-",
                   ", ".join(greens) if greens else "none"))
        other_green = [name for name in greens if name != source]

    directory_path = os.path.join(root, directory)
    source_path = os.path.join(directory_path, source)
    target_name = canonical_name(number)
    target_path = os.path.join(directory_path, target_name)
    if os.path.exists(target_path):
        raise OrphanPromoteError(
            "E_OTP_TARGET_EXISTS",
            "%s already exists; nothing is overwritten"
            % target_name)
    try:
        source_bytes = os.path.getsize(source_path)
    except (IOError, OSError) as exc:
        raise OrphanPromoteError("E_OTP_UNREADABLE", "%s: %s"
                                 % (source, exc))

    digest = None
    for leg in trace["legs"]:
        if leg["name"] == source:
            digest = leg["digest"]
    return {
        "action": "PLAN",
        "round": number,
        "source": source,
        "target": target_name,
        "source_bytes": source_bytes,
        "digest": digest,
        "standing_in": trace["standing_in"],
        "green_legs": greens,
        "other_green": other_green,
        "wrote": False,
        "verdict": "PLANNED",
    }


def promote(root, round_value, directory="qa", source=None, execute=False):
    """Plan, and with execute=True copy exactly one leg into its canonical name."""
    report = plan(root, round_value, directory, source)
    if not execute:
        return report
    directory_path = os.path.join(root, directory)
    source_path = os.path.join(directory_path, report["source"])
    target_path = os.path.join(directory_path, report["target"])
    part_path = target_path + PART_SUFFIX
    if os.path.exists(part_path):
        raise OrphanPromoteError(
            "E_OTP_TEMP_RESIDUE",
            "%s is already present; nothing is overwritten" % PART_SUFFIX)
    try:
        with open(source_path, "rb") as handle:
            payload = handle.read()
    except (IOError, OSError) as exc:
        raise OrphanPromoteError("E_OTP_UNREADABLE", "%s: %s"
                                 % (report["source"], exc))
    if len(payload) != report["source_bytes"]:
        raise OrphanPromoteError(
            "E_OTP_PREDICT",
            "%s measured %d bytes then %d on re-read"
            % (report["source"], report["source_bytes"], len(payload)))
    try:
        handle = open(part_path, "wb")
        try:
            handle.write(payload)
        finally:
            handle.close()
        os.replace(part_path, target_path)
    except (IOError, OSError) as exc:
        try:
            if os.path.exists(part_path):
                os.remove(part_path)
        except (IOError, OSError):
            pass
        raise OrphanPromoteError("E_OTP_WRITE", str(exc))
    try:
        with open(target_path, "rb") as back:
            landed = back.read()
    except (IOError, OSError) as exc:
        raise OrphanPromoteError("E_OTP_READBACK", str(exc))
    if landed != payload:
        raise OrphanPromoteError(
            "E_OTP_READBACK",
            "%s landed %d bytes against %d planned"
            % (report["target"], len(landed), len(payload)))
    try:
        with open(source_path, "rb") as again:
            kept = again.read()
    except (IOError, OSError) as exc:
        raise OrphanPromoteError("E_OTP_UNREADABLE", str(exc))
    if kept != payload:
        raise OrphanPromoteError(
            "E_OTP_SOURCE_MOVED",
            "%s changed while its copy was written" % report["source"])
    if os.path.exists(part_path):
        raise OrphanPromoteError("E_OTP_TEMP_RESIDUE", part_path)
    report["action"] = "PROMOTE"
    report["wrote"] = True
    report["verdict"] = "PROMOTED"
    return report


def render(report):
    """One line for the round, one for the pick (and its alternatives)."""
    out = ["ORPHAN PROMOTE action=%s round=R%d source=%s target=%s bytes=%d "
           "digest=%s"
           % (report["action"], report["round"], report["source"],
              report["target"], report["source_bytes"],
              (report["digest"] or "-")[:12])]
    out.append("  standing_in=%s green_legs=%d other_green=%s wrote=%s "
               "verdict=%s"
               % (report["standing_in"] or "-", len(report["green_legs"]),
                  ",".join(report["other_green"]) or "-",
                  "yes" if report["wrote"] else "no", report["verdict"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: orphan_promote.py (--plan|--promote) ROUND [DIR] [--root PATH]\n"
         "                         [--src LEG] [--json]\n"
         "  DIR defaults to qa; --promote is the only writing mode\n"
         "  --src picks one leg by name; without it the first RUNNER PASS\n"
         "  leg in name order is chosen and the other green legs are named\n"
         "  exit 0 = planned, or one promotion performed\n"
         "  exit 2 = refused over live state (no trace, not green, target\n"
         "           exists) and nothing was written\n"
         "  exit 3 = evidence absent, unreadable or undecodable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    operation = None
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    directory = "qa"
    source = None
    operands = []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--plan", "--promote"):
            if operation is not None:
                sys.stdout.write("E_OTP_BAD_ARGS: one mode only\n")
                return 5
            operation = "promote" if arg == "--promote" else "plan"
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_OTP_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg == "--src":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_OTP_BAD_ARGS: --src needs a leg name\n")
                return 5
            source = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write("E_OTP_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        else:
            operands.append(arg)
        index += 1
    if operation is None:
        sys.stdout.write("E_OTP_BAD_ARGS: --plan or --promote is required\n")
        sys.stdout.write(USAGE)
        return 5
    if not operands:
        sys.stdout.write("E_OTP_BAD_ARGS: a round is required\n")
        sys.stdout.write(USAGE)
        return 5
    if len(operands) > 2:
        sys.stdout.write("E_OTP_BAD_ARGS: too many operands\n")
        sys.stdout.write(USAGE)
        return 5
    if len(operands) == 2:
        directory = operands[1]
    try:
        report = promote(root, operands[0], directory, source,
                         execute=(operation == "promote"))
    except OrphanPromoteError as exc:
        sys.stdout.write("%s\n" % str(exc))
        return 3 if exc.code in ("E_OTP_NO_EVIDENCE", "E_OTP_UNREADABLE",
                                "E_OTP_BAD_NAME", "E_OTP_UNDECODABLE") else 2
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))