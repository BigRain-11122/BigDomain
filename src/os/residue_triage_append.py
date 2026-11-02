# residue_triage_append.py - one dated triage entry as its own operation
# Criteria AC-RTA1..AC-RTA6 were pre-registered inside the R2310 seed row of
# state/queue/tech.md BEFORE this file existed.
#
# Why this exists: residue_triage can now PIN a declaration, but accepting one
# more round meant re-running closeout_R2310.py, which regenerates all entries
# from the live reading and therefore silently absorbs a DISAGREES into a
# TRIAGED entry. The regeneration shortcut is the defect: it rewrites rows it
# was never asked about, so a row whose live status moved is laundered rather
# than reported.
#
# This module is the single-entry operation, and nothing else:
#   * the loader and every status come from residue_triage (imported, never
#     re-derived - AC-RTA1): the declaration is read by RT.load_declaration,
#     the live residue by RT.live_residue, and a candidate is validated by
#     RT.shape, so a patched reader flows straight through;
#   * an append whose round is ALREADY declared refuses by code naming the
#     existing entry, never a quiet overwrite (AC-RTA2);
#   * an append against a round whose live status DISAGREES refuses naming
#     BOTH statuses, so the regeneration shortcut cannot launder one
#     (AC-RTA3);
#   * an `until` earlier than its own `declared_by` refuses, and the write is
#     a raw-text splice so every other entry stays byte-identical (AC-RTA4);
#   * exit 0 only when the file was rewritten and re-read as TRIAGED, 2 on a
#     refusal over live state, 3 on unreadable input, 5 on bad flags, with a
#     byte-stable --json over the pinned keys (AC-RTA5);
#   * pure ASCII source, stdlib only, zero network, no clock (AC-RTA6).
#
# Retirement needs no second operation: an entry's `until` already expresses
# it, and residue_triage reads an expired entry as EXPIRED and hands its round
# back to the residue. This module therefore has exactly one write path.
#
# Pure apart from one atomic replace under --append; no clock, no network.

import json
import os
import sys

import residue_triage as RT

DECLARATION_PATH = RT.DECLARATION_PATH

ENTRY_KEYS = RT.ENTRY_KEYS

CLOSER = "\n  ]\n}\n"

INDENT = "    "

SUITE_LABEL = "os-residue-triage-append"

# The label single_append_status_face reports for a round the live residue does
# not carry. The READING is that module's; this constant is only the word this
# renderer compares against, and the suite pins the two equal so they cannot
# drift apart.
NOT_RESIDUE = "NOT-RESIDUE"

REPORT_KEYS = (
    "action",
    "round",
    "status",
    "declared_by",
    "until",
    "before_bytes",
    "after_bytes",
    "delta",
    "entries_before",
    "entries_after",
    "residue",
    "declaration",
    "verdict",
    "wrote",
)

UNREADABLE_CODES = (
    "E_RTA_UNREADABLE",
    "E_RTA_UNPINNED",
    "E_RTA_BAD_SHAPE",
    "E_RTA_BAD_STATUS",
    "E_RTA_BAD_STATE",
    "E_RTA_READBACK",
)


class ResidueTriageAppendError(Exception):
    """A refusal carrying its own code.

    A refused --check may also carry the live status of the asked round
    (AC-ACSP2); every other refusal leaves it None so its printed lines stay
    byte-identical (AC-ACSP4).
    """

    def __init__(self, code, detail="", status=None, round_label=None,
                 declared_by=None):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail
        self.status = status
        self.round = round_label
        # The boundary the check tripped on, read from the declaration's own
        # head (AC-RCDF1). Never set on the --append path.
        self.declared_by = "-" if declared_by is None else declared_by


def _round(value, origin):
    """One round reference, parsed by the reader's own law (AC-RTA1)."""
    try:
        return RT.parse_round(value, origin)
    except RT.ResidueTriageError as exc:
        raise ResidueTriageAppendError(
            "E_RTA_BAD_ARGS", "%s: %s" % (origin, exc.detail or exc.code))


def _declaration(root):
    """The pinned declaration, read by residue_triage (AC-RTA1)."""
    try:
        declaration = RT.load_declaration(root)
    except RT.ResidueTriageError as exc:
        raise ResidueTriageAppendError(
            "E_RTA_UNREADABLE", "%s: %s" % (exc.code, exc.detail))
    if declaration is None:
        raise ResidueTriageAppendError(
            "E_RTA_UNPINNED",
            "no %s to append to; pin one with the triage writer first"
            % DECLARATION_PATH.replace(os.sep, "/"))
    return declaration


def _live(root):
    """The live residue, read by stamp_residue through residue_triage."""
    try:
        rows = RT.live_residue(root)
    except RT.ResidueTriageError as exc:
        raise ResidueTriageAppendError(
            "E_RTA_BAD_STATE", "%s: %s" % (exc.code, exc.detail))
    status = {}
    for row in rows:
        status[int(row["round"])] = row["status"]
    return status


def entry_text(entry):
    """One entry rendered in the declaration's own layout."""
    lines = [
        INDENT + "{",
        INDENT + '  "round": %d,' % entry["round"],
        INDENT + '  "status": "%s",' % entry["status"],
        INDENT + '  "declared_by": "R%d",' % entry["declared_by"],
        INDENT + "  \"reason\": %s,"
        % json.dumps(entry["reason"], ensure_ascii=True),
        INDENT + '  "until": %d' % entry["until"],
        INDENT + "}",
    ]
    return "\n".join(lines)


def compose(before_text, entry):
    """Splice one entry into the entries array, leaving every other byte."""
    if not before_text.endswith(CLOSER):
        raise ResidueTriageAppendError(
            "E_RTA_BAD_SHAPE",
            "the declaration does not end with the pinned layout")
    cut = len(before_text) - len(CLOSER)
    head = before_text[:cut]
    body = head.rstrip()
    if body.endswith("}"):
        prefix = body + ",\n"
    else:
        prefix = body + "\n"
    return prefix + entry_text(entry) + before_text[cut:]


def plan(root, round_value, status, declared_by, reason, until):
    """Everything except the write: refusals, candidate, predicted bytes."""
    number = _round(round_value, "append round")
    by = _round(declared_by, "declared_by")
    until_round = _round(until, "until")
    if until_round < by:
        raise ResidueTriageAppendError(
            "E_RTA_UNTIL_BEFORE_DECL",
            "until R%d is earlier than declared_by R%d" % (until_round, by))
    if not isinstance(status, str) or not status.strip():
        raise ResidueTriageAppendError(
            "E_RTA_BAD_SHAPE", "status must be a non-empty string")
    if not isinstance(reason, str) or not reason.strip():
        raise ResidueTriageAppendError(
            "E_RTA_BAD_SHAPE", "reason must be a non-empty string")

    declaration = _declaration(root)
    existing = {}
    for entry in declaration["entries"]:
        existing[entry["round"]] = entry
    if number in existing:
        old = existing[number]
        raise ResidueTriageAppendError(
            "E_RTA_DUPLICATE",
            "R%d is already declared status=%s declared_by=R%d until=R%d"
            % (number, old["status"], old["declared_by"], old["until"]))

    live = _live(root)
    if number not in live:
        raise ResidueTriageAppendError(
            "E_RTA_NOT_RESIDUE",
            "R%d is not in the live residue (%d rounds are)"
            % (number, len(live)))
    live_status = live[number]
    if live_status != status:
        raise ResidueTriageAppendError(
            "E_RTA_DISAGREES",
            "R%d declares %s while the live reader reports %s"
            % (number, status, live_status))

    entry = {
        "round": number,
        "status": status,
        "declared_by": by,
        "reason": reason,
        "until": until_round,
    }
    raw_entries = []
    for item in declaration["entries"]:
        raw_entries.append({
            "round": "R%d" % item["round"],
            "status": item["status"],
            "declared_by": "R%d" % item["declared_by"],
            "reason": item["reason"],
            "until": "R%d" % item["until"],
        })
    raw_entries.append({
        "round": "R%d" % entry["round"],
        "status": entry["status"],
        "declared_by": "R%d" % entry["declared_by"],
        "reason": entry["reason"],
        "until": "R%d" % entry["until"],
    })
    try:
        candidate = RT.shape({
            "declared_by": "R%d" % declaration["declared_by"],
            "reason": declaration["reason"],
            "entries": raw_entries,
        }, "candidate declaration")
    except RT.ResidueTriageError as exc:
        raise ResidueTriageAppendError(
            "E_RTA_BAD_STATUS" if exc.code == "E_RTR_BAD_STATUS"
            else "E_RTA_BAD_SHAPE",
            "%s: %s" % (exc.code, exc.detail))

    live_rows = [{"round": key, "status": live[key]}
                 for key in sorted(live)]
    judged = RT.judge(candidate["entries"], live_rows, by)
    if judged["residue"]:
        raise ResidueTriageAppendError(
            "E_RTA_NOT_TRIAGED",
            "after R%d the reader would still carry %d untriaged round(s): %s"
            % (number, len(judged["residue"]),
               ", ".join("R%d" % value for value in judged["residue"][:5])))

    path = os.path.join(root, DECLARATION_PATH)
    try:
        with open(path, "rb") as handle:
            raw_bytes = handle.read()
    except (IOError, OSError) as exc:
        raise ResidueTriageAppendError("E_RTA_UNREADABLE", str(exc))
    try:
        before_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ResidueTriageAppendError("E_RTA_UNREADABLE", str(exc))
    after_text = compose(before_text, entry)
    after_bytes = after_text.encode("utf-8")
    return {
        "entry": entry,
        "path": path,
        "after_bytes": after_bytes,
        "before_bytes": len(raw_bytes),
        "delta": len(after_bytes) - len(raw_bytes),
        "entries_before": len(declaration["entries"]),
        "entries_after": len(declaration["entries"]) + 1,
    }


def apply(root, prepared):
    """One atomic replace, then a read-back through the reader (AC-RTA4).

    The write path asks the shared NOOP comparison FIRST (AC-DWNP1), so a
    composition that already equals the declaration writes no byte and creates
    no temp. On any other reading the shipped path below runs unchanged.
    """
    path = prepared["path"]
    payload = prepared["after_bytes"]
    import declaration_writer_noop_parity as DWNP
    if DWNP.is_noop(path, payload):
        return None
    temp = path + ".tmp-rta"
    try:
        with open(temp, "wb") as handle:
            handle.write(payload)
        os.replace(temp, path)
    except (IOError, OSError) as exc:
        try:
            os.remove(temp)
        except (IOError, OSError):
            pass
        raise ResidueTriageAppendError("E_RTA_READBACK", str(exc))
    try:
        size = os.path.getsize(path)
    except (IOError, OSError) as exc:
        raise ResidueTriageAppendError("E_RTA_READBACK", str(exc))
    if size != prepared["before_bytes"] + prepared["delta"]:
        raise ResidueTriageAppendError(
            "E_RTA_READBACK",
            "predicted %d bytes, the file measures %d"
            % (prepared["before_bytes"] + prepared["delta"], size))
    reread = _declaration(root)
    entry = prepared["entry"]
    found = None
    for item in reread["entries"]:
        if item["round"] == entry["round"]:
            found = item
    if found != entry:
        raise ResidueTriageAppendError(
            "E_RTA_READBACK",
            "the appended entry does not re-read as written: %r" % (found,))
    if len(reread["entries"]) != prepared["entries_after"]:
        raise ResidueTriageAppendError(
            "E_RTA_READBACK",
            "entry count re-read as %d, predicted %d"
            % (len(reread["entries"]), prepared["entries_after"]))
    try:
        report = RT.read(root, "R%d" % entry["declared_by"])
    except RT.ResidueTriageError as exc:
        raise ResidueTriageAppendError(
            "E_RTA_READBACK", "%s: %s" % (exc.code, exc.detail))
    if report["verdict"] != "TRIAGED":
        raise ResidueTriageAppendError(
            "E_RTA_NOT_TRIAGED",
            "the file re-reads %s with %d untriaged round(s)"
            % (report["verdict"], report["untriaged"]))
    return report


def check(root, round_value):
    """The read-only face: what would an append have to accept?"""
    current = _round(round_value, "round")
    # The status face is asked FIRST, so a refused triage read still names the
    # live status of the round the operator asked about (AC-ACSP1, AC-ACSP2).
    # The precedence itself is append_check_status_precedence's; the E_RTA_*
    # code mapping below stays this module's one law.
    import append_check_status_precedence as ACSP
    try:
        outcome = ACSP.asked(root, "R%d" % current)
    except ACSP.AppendCheckStatusPrecedenceError as exc:
        raise ResidueTriageAppendError(
            "E_RTA_BAD_STATE", "%s: %s" % (exc.code, exc.detail))
    if outcome["refusal"] is not None:
        code = "E_RTA_UNREADABLE"
        if outcome["refusal"]["code"] in ("E_RTR_BAD_ARGS",):
            code = "E_RTA_BAD_ARGS"
        elif outcome["refusal"]["code"] in ("E_RTR_BAD_STATE",):
            code = "E_RTA_BAD_STATE"
        # The declared boundary travels with the refusal so the payload and the
        # prose name one round (AC-RCDF1). The head is derived without aging
        # anything, so the refusal code above is unchanged (AC-RCDF3).
        import refused_check_declaration_face as RCDF
        raise ResidueTriageAppendError(
            code,
            "%s: %s" % (outcome["refusal"]["code"],
                        outcome["refusal"]["detail"]),
            status=outcome["status"],
            round_label=outcome["requested"],
            declared_by=RCDF.head(root))
    report = outcome["report"]
    out = {
        "action": "check",
        "round": "R%d" % current,
        "status": outcome["status"],
        "declared_by": "-" if report["declared_by"] is None
        else report["declared_by"],
        "until": "-",
        "before_bytes": 0,
        "after_bytes": 0,
        "delta": 0,
        "entries_before": len(report["entries"]),
        "entries_after": len(report["entries"]),
        "residue": list(report["residue"]),
        "declaration": report["declaration"],
        "verdict": report["verdict"],
        "wrote": False,
    }
    return out


def one_line(report):
    """The single line an operator reads."""
    residue = ",".join("R%d" % value for value in report["residue"]) or "-"
    return ("RESIDUE TRIAGE APPEND action=%s round=%s status=%s declared_by=%s "
            "until=%s entries=%d->%d bytes=%d->%d delta=%d residue=%s "
            "declaration=%s verdict=%s wrote=%s"
            % (report["action"], report["round"], report["status"],
               report["declared_by"], report["until"],
               report["entries_before"], report["entries_after"],
               report["before_bytes"], report["after_bytes"],
               report["delta"], residue, report["declaration"],
               report["verdict"], "yes" if report["wrote"] else "no"))


def render(report):
    """The one line, then every round still awaiting an append."""
    out = [one_line(report)]
    for value in report["residue"]:
        out.append("  RESIDUE R%d has no dated entry yet" % value)
    if report["status"] == NOT_RESIDUE:
        out.append("  NOTE E_SASF_NOT_RESIDUE: %s is not in the live residue"
                   % report["round"])
    if report["verdict"] == "NOOP":
        out.append("  NOTE the composition already equals the declaration, "
                   "so no byte was written")
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (byte-stable)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: residue_triage_append.py --check --round R<n> [--root PATH]\n"
         "       residue_triage_append.py --append --round R<n> --status S\n"
         "         --by R<n> --reason TEXT --until R<n> [--dry-run]\n"
         "  [--root PATH] [--json]\n"
         "  exit 0 = the file was rewritten and re-reads TRIAGED (or, for\n"
         "           --check, every live residue round already has an entry)\n"
         "  exit 2 = refused over live state (duplicate, disagrees, not in\n"
         "           the residue, until before declared_by, still untriaged)\n"
         "  exit 3 = unreadable or unpinned declaration, bad shape\n"
         "  exit 5 = bad flags\n")


def refused_report(exc):
    """The pinned keys for a refused --check, with its status carried
    (AC-ACSP5) and the declared boundary named (AC-RCDF1). Never used by the
    --append path (AC-ACSP4)."""
    return {
        "action": "check",
        "round": exc.round or "-",
        "status": exc.status,
        "declared_by": exc.declared_by,
        "until": "-",
        "before_bytes": 0,
        "after_bytes": 0,
        "delta": 0,
        "entries_before": 0,
        "entries_after": 0,
        "residue": [],
        "declaration": "-",
        "verdict": exc.code,
        "wrote": False,
    }


def main(argv):
    mode = None
    as_json = False
    dry_run = False
    round_text = None
    status = None
    by = None
    reason = None
    until = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--check", "--append"):
            if mode is not None and mode != arg[2:]:
                sys.stdout.write("E_RTA_BAD_ARGS: --check and --append are "
                                 "mutually exclusive\n")
                sys.stdout.write(USAGE)
                return 5
            mode = arg[2:]
        elif arg == "--json":
            as_json = True
        elif arg == "--dry-run":
            dry_run = True
        elif arg in ("--round", "--status", "--by", "--reason", "--until",
                     "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RTA_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            value = argv[index]
            if arg == "--round":
                round_text = value
            elif arg == "--status":
                status = value
            elif arg == "--by":
                by = value
            elif arg == "--reason":
                reason = value
            elif arg == "--until":
                until = value
            else:
                root = value
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RTA_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1

    if mode is None:
        sys.stdout.write("E_RTA_BAD_ARGS: --check or --append is required\n")
        sys.stdout.write(USAGE)
        return 5
    if round_text is None:
        sys.stdout.write("E_RTA_BAD_ARGS: --round is required\n")
        sys.stdout.write(USAGE)
        return 5
    if mode == "append":
        missing = [flag for flag, value in (("--status", status),
                                            ("--by", by),
                                            ("--reason", reason),
                                            ("--until", until))
                   if value is None]
        if missing:
            sys.stdout.write("E_RTA_BAD_ARGS: --append needs %s\n"
                             % ", ".join(missing))
            sys.stdout.write(USAGE)
            return 5

    try:
        if mode == "check":
            report = check(root, round_text)
            if dry_run:
                report["action"] = "check"
        else:
            prepared = plan(root, round_text, status, by, reason, until)
            entry = prepared["entry"]
            if dry_run:
                report = {
                    "action": "dry-run",
                    "round": "R%d" % entry["round"],
                    "status": entry["status"],
                    "declared_by": "R%d" % entry["declared_by"],
                    "until": "R%d" % entry["until"],
                    "before_bytes": prepared["before_bytes"],
                    "after_bytes": prepared["before_bytes"]
                    + prepared["delta"],
                    "delta": prepared["delta"],
                    "entries_before": prepared["entries_before"],
                    "entries_after": prepared["entries_after"],
                    "residue": [],
                    "declaration": "PINNED",
                    "verdict": "DRY-RUN",
                    "wrote": False,
                }
            else:
                reread = apply(root, prepared)
                if reread is None:
                    report = {
                        "action": "append",
                        "round": "R%d" % entry["round"],
                        "status": entry["status"],
                        "declared_by": "R%d" % entry["declared_by"],
                        "until": "R%d" % entry["until"],
                        "before_bytes": prepared["before_bytes"],
                        "after_bytes": prepared["before_bytes"],
                        "delta": 0,
                        "entries_before": prepared["entries_before"],
                        "entries_after": prepared["entries_before"],
                        "residue": [],
                        "declaration": "PINNED",
                        "verdict": "NOOP",
                        "wrote": False,
                    }
                else:
                    report = {
                        "action": "append",
                        "round": "R%d" % entry["round"],
                        "status": entry["status"],
                        "declared_by": "R%d" % entry["declared_by"],
                        "until": "R%d" % entry["until"],
                        "before_bytes": prepared["before_bytes"],
                        "after_bytes": prepared["before_bytes"]
                        + prepared["delta"],
                        "delta": prepared["delta"],
                        "entries_before": prepared["entries_before"],
                        "entries_after": prepared["entries_after"],
                        "residue": list(reread["residue"]),
                        "declaration": reread["declaration"],
                        "verdict": reread["verdict"],
                        "wrote": True,
                    }
    except ResidueTriageAppendError as exc:
        if as_json and exc.status is not None:
            sys.stdout.write(to_json(refused_report(exc)))
        else:
            sys.stdout.write("%s\n" % exc.code)
            if exc.detail:
                sys.stdout.write("  %s\n" % exc.detail)
            if exc.status is not None:
                import append_check_status_precedence as ACSP
                for line in ACSP.refusal_lines(
                        {"requested": exc.round, "status": exc.status}):
                    sys.stdout.write("  %s\n" % line)
        if exc.code == "E_RTA_BAD_ARGS":
            return 5
        if exc.code in UNREADABLE_CODES:
            return 3
        return 2

    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["action"] == "dry-run":
        return 0
    if report["verdict"] in ("TRIAGED", "NOOP"):
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))