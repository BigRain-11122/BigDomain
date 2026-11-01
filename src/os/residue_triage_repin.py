"""residue_triage_repin - the general re-pin writer (R2363).

The triage declaration has a writer for NEW entries (`residue_triage_append`),
for the head (`residue_triage_head_renew`) and for entries whose round left
the live residue (`residue_triage_entry_retire`), but nothing rewrites the
whole entry set when the declaration expires. That act was done by a ROUND
SCRIPT (`src/os/repin_R2353.py`) with the round and the until window as
constants: a hand-shaped write with no dry run, no refusal surface and no
proof, which the next expiry would simply repeat.

This is that writer made general, and it may only claim what it measured:

  * the entry set and the status vocabulary come from `residue_triage` (its
    loader, its status tuple and its `judge`), and the live residue from its
    own live reading, so nothing is re-derived here and no second declaration
    reader exists;
  * the dry run is the default and writes no byte; the plan names the round,
    the until window, the entry count before and after, every measured status
    with its count, the rounds it would DROP, and the predicted byte count;
  * a live entry whose declared status DISAGREES refuses the re-pin naming
    both statuses and both rounds, so a re-pin can never launder a moved
    status into a fresh declaration;
  * declared entries whose round is no longer live are dropped only when the
    caller says `--drop-unmatched`; without it the re-pin refuses and names
    them, because silently retiring a round is `residue_triage_entry_retire`'s
    job and not this writer's;
  * an until earlier than the round itself refuses, and the executed write is
    ONE atomic replace that proves its predicted size, re-reads TRIAGED at the
    given round, and leaves no temp residue.

Pure stdlib, pure ASCII source, zero network, no clock of its own (the round
is an argument). Criteria AC-RTRP1..AC-RTRP6 were pinned inside the R2353 seed
row of state/queue/tech.md BEFORE this code existed.
"""

import json
import os
import sys

import residue_triage as RT

TEMP_SUFFIX = ".tmp-rtrep"

PLAN_KEYS = (
    "verdict",
    "executed",
    "round",
    "until",
    "reason",
    "entries_before",
    "entries_after",
    "statuses",
    "dropped",
    "predicted_bytes",
    "declaration_bytes",
    "residue",
    "disagrees",
)

STATUS_KEYS = ("status", "count")


class RepinError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def default_reason(number, status):
    """The reason a NEW entry gets: the measured fact and nothing more."""
    return "re-pinned at R%d at its measured status %s" % (number, status)


def build(root, round_text, until_text, reason, allow_drop=False):
    """Plan the re-pin without writing: every refusal happens here."""
    current = RT.parse_round(round_text, "caller")
    until = RT.parse_round(until_text, "--until")
    if until < current:
        raise RepinError(
            "E_RTRP_UNTIL_PREDATES",
            "--until R%d is earlier than the round being pinned R%d"
            % (until, current))
    if not isinstance(reason, str) or not reason.strip():
        raise RepinError("E_RTRP_BAD_REASON", "the head reason is empty")
    declaration = RT.load_declaration(root)
    if declaration is None:
        raise RepinError(
            "E_RTRP_UNPINNED",
            "there is no declaration to re-pin; the append channel seeds one")
    if declaration["declared_by"] > current:
        raise RepinError(
            "E_RTRP_DECL_FUTURE",
            "declared_by R%d is later than the round being pinned R%d"
            % (declaration["declared_by"], current))
    live = RT.live_residue(root)

    # a moved status is refused here, BEFORE judge: judge reports EXPIRED
    # ahead of DISAGREES, so an expired entry whose live status also moved
    # would otherwise be re-pinned at the new status without ever being
    # named - exactly the laundering AC-RTRP3 forbids.
    live_by_round = {}
    for row in live:
        live_by_round[row["round"]] = row["status"]
    moved = []
    for row in declaration["entries"]:
        live_status = live_by_round.get(row["round"])
        if live_status is not None and live_status != row["status"]:
            moved.append("R%d declared=%s live=%s"
                         % (row["round"], row["status"], live_status))
    if moved:
        raise RepinError(
            "E_RTRP_DISAGREES",
            "the live reading moved under the declaration at the re-pin "
            "round R%d: %s" % (current, ", ".join(moved)))

    judged = RT.judge(declaration["entries"], live, current)

    disagreeing = [row for row in judged["rows"]
                   if row["state"] == "DISAGREES"]
    if disagreeing:
        detail = ", ".join(
            "R%d declared=%s live=%s" % (row["round"], row["declared_status"],
                                         row["live_status"])
            for row in disagreeing)
        raise RepinError(
            "E_RTRP_DISAGREES",
            "the live reading moved under the declaration: %s" % detail)

    unmatched = [row["round"] for row in judged["rows"]
                 if row["state"] == "UNMATCHED"]
    if unmatched and not allow_drop:
        raise RepinError(
            "E_RTRP_UNMATCHED",
            "rounds declared but no longer live: %s (pass --drop-unmatched "
            "to drop them, or retire them one by one first)"
            % ", ".join("R%d" % number for number in unmatched))

    reason_by_round = {}
    for row in declaration["entries"]:
        reason_by_round[row["round"]] = row["reason"]
    entries = []
    counts = {}
    for row in sorted(live, key=lambda item: item["round"]):
        number = row["round"]
        status = row["status"]
        counts[status] = counts.get(status, 0) + 1
        entries.append({
            "round": number,
            "status": status,
            "declared_by": current,
            "reason": reason_by_round.get(number)
            or default_reason(number, status),
            "until": until,
        })

    # the composed set must read TRIAGED BEFORE any byte is written
    probe = RT.judge(entries, live, current)
    if probe["residue"] or probe["disagrees"] or probe["expired"]:
        raise RepinError(
            "E_RTRP_NOT_TRIAGED",
            "the composed set would leave residue=%r disagrees=%d expired=%d"
            % (probe["residue"], probe["disagrees"], probe["expired"]))

    document = {
        "declared_by": current,
        "reason": reason.strip(),
        "entries": entries,
    }
    text = json.dumps(document, ensure_ascii=True, indent=2) + "\n"
    path = os.path.join(root, RT.DECLARATION_PATH)
    before = os.path.getsize(path) if os.path.exists(path) else 0
    return {
        "verdict": "PLANNED",
        "executed": False,
        "round": "R%d" % current,
        "until": "R%d" % until,
        "reason": reason.strip(),
        "entries_before": len(declaration["entries"]),
        "entries_after": len(entries),
        "statuses": [{"status": name, "count": counts[name]}
                     for name in sorted(counts)],
        "dropped": unmatched if allow_drop else [],
        "predicted_bytes": len(text.encode("utf-8")),
        "declaration_bytes": before,
        "residue": [],
        "disagrees": 0,
        "_path": path,
        "_text": text,
        "_round": current,
    }


def plan(root, round_text, until_text, reason, allow_drop=False,
         execute=False):
    """Plan, and execute only when asked: one atomic replace, then a read."""
    report = build(root, round_text, until_text, reason, allow_drop)
    if not execute:
        return report
    path = report["_path"]
    text = report["_text"]
    temp = path + TEMP_SUFFIX
    with open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(temp, path)
    sized = os.path.getsize(path)
    if sized != report["predicted_bytes"]:
        raise RepinError(
            "E_RTRP_SIZE",
            "predicted %d bytes, the file reads %d"
            % (report["predicted_bytes"], sized))
    reread = RT.read(root, "R%d" % report["_round"])
    if reread["verdict"] != "TRIAGED" or reread["untriaged"]:
        raise RepinError(
            "E_RTRP_NOT_TRIAGED",
            "after the write the declaration reads %s with untriaged=%d"
            % (reread["verdict"], reread["untriaged"]))
    report["verdict"] = "PINNED"
    report["executed"] = True
    report["entries_after"] = len(reread["entries"])
    report["residue"] = reread["residue"]
    report["disagrees"] = reread["disagrees"]
    return report


def one_line(report):
    """The single line an operator reads."""
    return ("RESIDUE REPIN %s round=%s until=%s entries=%d->%d "
            "dropped=%d bytes=%d->%d"
            % (report["verdict"], report["round"], report["until"],
               report["entries_before"], report["entries_after"],
               len(report["dropped"]), report["declaration_bytes"],
               report["predicted_bytes"]))


def render(report):
    """Full text: the one line, then every status with its count."""
    out = [one_line(report)]
    for row in report["statuses"]:
        out.append("  STATUS %s count=%d" % (row["status"], row["count"]))
    for number in report["dropped"]:
        out.append("  DROP R%d no longer live" % number)
    out.append("  REASON %s" % report["reason"])
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (no private keys leak)."""
    ordered = {}
    for key in PLAN_KEYS:
        if key == "statuses":
            rows = []
            for row in report["statuses"]:
                narrow = {}
                for name in STATUS_KEYS:
                    narrow[name] = row[name]
                rows.append(narrow)
            ordered[key] = rows
        else:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: residue_triage_repin.py --round R<n> --until R<n> "
         "--reason TEXT [--drop-unmatched] [--execute] [--root PATH] "
         "[--json]\n"
         "  dry run is the default and writes no byte\n"
         "  exit 0 = PLANNED (dry run) or PINNED (--execute)\n"
         "  exit 2 = refused over live state (DISAGREES, UNMATCHED, "
         "NOT-TRIAGED)\n"
         "  exit 3 = the declaration is missing (UNPINNED) or unreadable\n"
         "  exit 5 = bad flags (including an --until before the round)\n")


def main(argv):
    as_json = False
    execute = False
    allow_drop = False
    round_text = None
    until_text = None
    reason = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--json":
            as_json = True
        elif arg == "--execute":
            execute = True
        elif arg == "--drop-unmatched":
            allow_drop = True
        elif arg in ("--round", "--until", "--reason", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RTRP_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            if arg == "--round":
                round_text = argv[index]
            elif arg == "--until":
                until_text = argv[index]
            elif arg == "--reason":
                reason = argv[index]
            else:
                root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RTRP_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if round_text is None or until_text is None or reason is None:
        sys.stdout.write("E_RTRP_BAD_ARGS: --round, --until and --reason are "
                         "required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = plan(root, round_text, until_text, reason, allow_drop,
                      execute)
    except RT.ResidueTriageError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code in ("E_RTR_UNREADABLE", "E_RTR_BAD_SHAPE",
                        "E_RTR_BAD_STATE", "E_RTR_BAD_STATUS",
                        "E_RTR_DUPLICATE"):
            return 3
        return 2
    except RepinError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code in ("E_RTRP_UNPINNED", "E_RTRP_SIZE"):
            return 3
        if exc.code in ("E_RTRP_BAD_REASON", "E_RTRP_UNTIL_PREDATES"):
            return 5
        return 2
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))