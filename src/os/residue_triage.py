"""residue_triage - a dated triage declaration over the stamp residue (R2310).

`stamp_residue` reports the whole stamped-but-never-logged residue in one pass
(live 185 rounds: 165 delivered on closed rows, 20 sitting on open rows), but
the review of those rounds is prose in a log item and therefore evaporates:
a round never gains a log item retroactively, so the same 185 rows are
re-triaged by hand every window.

This joins a pinned `state/residue_triage.json` to the LIVE residue:

  * the residue list and every status are imported from `stamp_residue`
    (`read` is called at call time and `STATUSES` is that module's tuple),
    so patching that reader moves this reading - nothing is re-derived here;
  * an entry is judged against the live list: a round the live reader no
    longer lists reads UNMATCHED and is inert, never applied;
  * an entry whose status disagrees with the live reading reads DISAGREES
    naming BOTH statuses, and the round stays in the debt;
  * an entry past its `until` round reads EXPIRED and hands its round back to
    the residue, naming the until round; a missing declaration reads UNPINNED
    with the full debt rather than a fabricated pass;
  * one pinned shape only, every refusal carries its own code.

Pure read: nothing is written, no clock is read, no network import.
Criteria AC-RTR1..AC-RTR6 were pinned inside the R2298 seed row of
state/queue/tech.md BEFORE this code existed.
Pure ASCII source, stdlib only.
"""

import json
import os
import sys

import stamp_residue as SR

DECLARATION_PATH = os.path.join("state", "residue_triage.json")

ENTRY_KEYS = ("round", "status", "declared_by", "reason", "until")

DECLARATION_KEYS = ("declared_by", "reason", "entries")

REPORT_KEYS = (
    "declaration",
    "declared_by",
    "reason",
    "round",
    "residue_count",
    "triaged",
    "untriaged",
    "unmatched",
    "disagrees",
    "expired",
    "verdict",
    "residue",
    "entries",
)

ROW_KEYS = (
    "round",
    "declared_status",
    "live_status",
    "state",
    "until",
)

VERDICTS = ("TRIAGED", "RESIDUE")

ENTRY_STATES = ("TRIAGED", "DISAGREES", "EXPIRED", "UNMATCHED")


class ResidueTriageError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parse_round(value, origin):
    """A round reference: "R<n>" or "<n>", nothing else (no bools)."""
    if isinstance(value, bool):
        raise ResidueTriageError(
            "E_RTR_BAD_SHAPE", "%s round must be an int, got %r"
            % (origin, value))
    if isinstance(value, int):
        number = value
    elif isinstance(value, str):
        text = value.strip()
        if text[:1] in ("R", "r"):
            text = text[1:]
        if not text or not text.isdigit():
            raise ResidueTriageError(
                "E_RTR_BAD_SHAPE", "%s round is not a round: %r"
                % (origin, value))
        number = int(text)
    else:
        raise ResidueTriageError(
            "E_RTR_BAD_SHAPE", "%s round is not a round: %r"
            % (origin, value))
    if number < 1:
        raise ResidueTriageError(
            "E_RTR_BAD_SHAPE", "%s round must be at least 1, got %d"
            % (origin, number))
    return number


def shape(raw, origin):
    """Validate the pinned declaration form (unknown keys refuse)."""
    if not isinstance(raw, dict):
        raise ResidueTriageError(
            "E_RTR_BAD_SHAPE", "%s is not an object" % origin)
    for key in raw.keys():
        if key not in DECLARATION_KEYS:
            raise ResidueTriageError(
                "E_RTR_BAD_SHAPE", "%s carries unknown key %r" % (origin, key))
    for key in DECLARATION_KEYS:
        if key not in raw:
            raise ResidueTriageError(
                "E_RTR_BAD_SHAPE", "%s is missing %r" % (origin, key))
    reason = raw["reason"]
    if not isinstance(reason, str) or not reason.strip():
        raise ResidueTriageError(
            "E_RTR_BAD_SHAPE", "%s reason is empty" % origin)
    entries = raw["entries"]
    if not isinstance(entries, list):
        raise ResidueTriageError(
            "E_RTR_BAD_SHAPE", "%s entries is not a list" % origin)
    parsed = []
    seen = set()
    for index, entry in enumerate(entries):
        where = "%s entry %d" % (origin, index)
        if not isinstance(entry, dict):
            raise ResidueTriageError(
                "E_RTR_BAD_SHAPE", "%s is not an object" % where)
        for key in entry.keys():
            if key not in ENTRY_KEYS:
                raise ResidueTriageError(
                    "E_RTR_BAD_SHAPE", "%s carries unknown key %r"
                    % (where, key))
        for key in ENTRY_KEYS:
            if key not in entry:
                raise ResidueTriageError(
                    "E_RTR_BAD_SHAPE", "%s is missing %r" % (where, key))
        number = parse_round(entry["round"], where)
        if number in seen:
            raise ResidueTriageError(
                "E_RTR_DUPLICATE", "%s repeats round %d" % (where, number))
        seen.add(number)
        status = entry["status"]
        if not isinstance(status, str) or status not in SR.STATUSES:
            raise ResidueTriageError(
                "E_RTR_BAD_STATUS",
                "%s status %r is not one of stamp_residue own statuses"
                % (where, status))
        row_reason = entry["reason"]
        if not isinstance(row_reason, str) or not row_reason.strip():
            raise ResidueTriageError(
                "E_RTR_BAD_SHAPE", "%s reason is empty" % where)
        until = parse_round(entry["until"], where)
        parsed.append({
            "round": number,
            "status": status,
            "declared_by": parse_round(entry["declared_by"], where),
            "reason": row_reason,
            "until": until,
        })
    return {
        "declared_by": parse_round(raw["declared_by"], origin),
        "reason": reason,
        "entries": parsed,
    }


def load_declaration(root):
    """Read the declaration; a missing file is UNPINNED, not a pass."""
    path = os.path.join(root, DECLARATION_PATH)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (IOError, OSError) as exc:
        raise ResidueTriageError("E_RTR_UNREADABLE", str(exc))
    except ValueError as exc:
        raise ResidueTriageError(
            "E_RTR_UNREADABLE", "not JSON (%s)" % exc)
    return shape(raw, DECLARATION_PATH)


def live_residue(root):
    """The live residue list, read through stamp_residue (AC-RTR1)."""
    try:
        report = SR.read(root)
    except SR.StampResidueError as exc:
        raise ResidueTriageError("E_RTR_BAD_STATE", exc.detail)
    out = []
    for row in report.get("rounds") or []:
        status = row.get("status")
        if status not in SR.STATUSES:
            raise ResidueTriageError(
                "E_RTR_BAD_STATUS",
                "stamp_residue returned %r for R%s, not one of its statuses"
                % (status, row.get("round")))
        out.append({"round": int(row["round"]), "status": status})
    return out


def judge(entries, live, current):
    """Resolve every declared entry against the live residue (AC-RTR2..4)."""
    live_by_round = {}
    for row in live:
        live_by_round[row["round"]] = row["status"]
    rows = []
    covered = set()
    unmatched = 0
    disagrees = 0
    expired = 0
    for entry in entries:
        number = entry["round"]
        if entry["declared_by"] > current:
            raise ResidueTriageError(
                "E_RTR_DECL_FUTURE",
                "entry for R%d is declared_by R%d, later than the round "
                "being checked R%d"
                % (number, entry["declared_by"], current))
        live_status = live_by_round.get(number)
        if live_status is None:
            state = "UNMATCHED"
            unmatched += 1
        elif current > entry["until"]:
            state = "EXPIRED"
            expired += 1
        elif entry["status"] != live_status:
            state = "DISAGREES"
            disagrees += 1
        else:
            state = "TRIAGED"
            covered.add(number)
        rows.append({
            "round": number,
            "declared_status": entry["status"],
            "live_status": "-" if live_status is None else live_status,
            "state": state,
            "until": entry["until"],
        })
    residue = sorted(number for number in live_by_round
                     if number not in covered)
    return {
        "rows": rows,
        "residue": residue,
        "unmatched": unmatched,
        "disagrees": disagrees,
        "expired": expired,
    }


def read(root, round_text=None):
    """The whole reading: live residue, declaration, one verdict."""
    current = None if round_text is None else parse_round(round_text, "caller")
    live = live_residue(root)
    live_rounds = sorted(row["round"] for row in live)
    declaration = load_declaration(root)

    if declaration is None:
        entries = []
        rows = []
        residue = live_rounds
        counts = {"unmatched": 0, "disagrees": 0, "expired": 0}
        label = "UNPINNED"
        declared_by = None
        reason = "-"
    else:
        if current is None:
            raise ResidueTriageError(
                "E_RTR_BAD_ARGS", "--round is required to age a declaration")
        if declaration["declared_by"] > current:
            raise ResidueTriageError(
                "E_RTR_DECL_FUTURE",
                "declared_by R%d is later than the round being checked R%d"
                % (declaration["declared_by"], current))
        judged = judge(declaration["entries"], live, current)
        entries = judged["rows"]
        residue = judged["residue"]
        counts = {"unmatched": judged["unmatched"],
                  "disagrees": judged["disagrees"],
                  "expired": judged["expired"]}
        label = "PINNED"
        declared_by = declaration["declared_by"]
        reason = declaration["reason"]

    residue_set = set(residue)
    triaged = len([row for row in (live_rounds) if row not in residue_set])
    verdict = "TRIAGED" if not residue else "RESIDUE"
    return {
        "declaration": label,
        "declared_by": None if declared_by is None else "R%d" % declared_by,
        "reason": reason,
        "round": None if current is None else "R%d" % current,
        "residue_count": len(live_rounds),
        "triaged": triaged,
        "untriaged": len(residue),
        "unmatched": counts["unmatched"],
        "disagrees": counts["disagrees"],
        "expired": counts["expired"],
        "verdict": verdict,
        "residue": residue,
        "entries": entries,
    }


def one_line(report):
    """The single line an operator reads."""
    return ("RESIDUE TRIAGE declaration=%s declared_by=%s round=%s "
            "residue=%d triaged=%d untriaged=%d unmatched=%d disagrees=%d "
            "expired=%d verdict=%s"
            % (report["declaration"],
               "-" if report["declared_by"] is None else report["declared_by"],
               "-" if report["round"] is None else report["round"],
               report["residue_count"], report["triaged"],
               report["untriaged"], report["unmatched"], report["disagrees"],
               report["expired"], report["verdict"]))


def render(report):
    """Full text: the one line, then the untriaged rounds and every entry."""
    out = [one_line(report)]
    for row in report["entries"]:
        out.append("  ENTRY R%d state=%s declared=%s live=%s until=R%d"
                   % (row["round"], row["state"], row["declared_status"],
                      row["live_status"], row["until"]))
    for number in report["residue"]:
        out.append("  RESIDUE R%d still untriaged" % number)
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (no extra keys leak)."""
    ordered = {}
    for key in REPORT_KEYS:
        if key == "entries":
            continue
        ordered[key] = report[key]
    pinned_rows = []
    for row in report["entries"]:
        narrow = {}
        for key in ROW_KEYS:
            narrow[key] = row[key]
        pinned_rows.append(narrow)
    ordered["entries"] = pinned_rows
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: residue_triage.py --check --round R<n> [--root PATH] "
         "[--json]\n"
         "  exit 0 = every live residue round is triaged\n"
         "  exit 2 = UNPINNED or RESIDUE (some round is untriaged, "
         "disagrees, or expired)\n"
         "  exit 3 = the residue reader, or the declaration, is unreadable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    check = False
    as_json = False
    round_text = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--round", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RTR_BAD_ARGS: %s needs a value\n" % arg)
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
            sys.stdout.write("E_RTR_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_RTR_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    if round_text is None:
        sys.stdout.write("E_RTR_BAD_ARGS: --round is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = read(root, round_text)
    except ResidueTriageError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code in ("E_RTR_UNREADABLE", "E_RTR_BAD_SHAPE",
                        "E_RTR_BAD_STATE", "E_RTR_BAD_STATUS",
                        "E_RTR_DUPLICATE"):
            return 3
        if exc.code == "E_RTR_BAD_ARGS":
            return 5
        return 2
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "TRIAGED":
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))