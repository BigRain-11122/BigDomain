# debt_stale_open_scan.py - is an OPEN debt row's own work already shipped?
# Criteria AC-DSRC1..AC-DSRC6 were pinned in state/queue/tech.md as the R2524
# seed row BEFORE this file existed, and re-pinned on the board at R3162
# (AC-DSRC2 JUDGED-CHANGED, narrower: see the module docstring note below).
#
# Why this exists: the register can carry an OPEN row whose named work already
# shipped, and no shipped reader ever says so. debt_gate names only the single
# `first=yes` row; debt_register ages rows by windows carried. So "a row whose
# own window landed long ago" and "a row that still owes work" read the same.
#
# Three deliberate narrowings:
#   * The register is read through the SHIPPED row law (debt_register), never
#     a second parser, so a typo cannot be read differently in two places.
#   * The DECIDING round is the row's own ITEM round. Round tokens in the note
#     are published as an evidence reading only. Measured at R3162: the one
#     genuinely outstanding carried row (loop-s4u-reconcile, 34th disclosure)
#     names only a DISCLOSURE round in its note, so letting note tokens decide
#     would push a real debt to CLOSE-BY-HAND. Narrowed, never widened.
#   * A round reads DISCHARGED only when TWO shipped faces agree - it is a
#     labelled round (live log via round_evidence, or a fold archive via
#     state_seq.archived_labels, same item_round law) AND qa/ carries at least
#     one file bearing its token (round_evidence.map_files). A missing
#     measurement is never promoted to STALE.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import json
import os
import re
import sys

import debt_register
import round_evidence
import state_seq

# A round token standing alone: not a fragment of a longer number or label
# (so "R2742b" in an item is honestly NOT a round number).
ITEM_ROUND_RE = re.compile(r"(?<![0-9A-Za-z])R(\d{3,6})(?![0-9A-Za-z])")

STATES = ("STALE-OPEN", "OPEN-UNNAMED", "OPEN-UNDISCHARGED")

VERDICTS = ("UNPINNED", "STALE-FOUND", "NO-STALE")

ACTION = "CLOSE-BY-HAND"

ROW_KEYS = ("item", "opened", "deciding", "state", "note_rounds")

REPORT_KEYS = (
    "register",
    "present",
    "open_count",
    "stale_count",
    "unnamed_count",
    "undischarged_count",
    "rows",
    "action",
    "verdict",
)

USAGE = ("usage: debt_stale_open_scan.py --check [--root PATH] "
         "[--qa-dir PATH] [--gate] [--json]\n"
         "  exit 0 = reading produced (stale rows reported when found)\n"
         "  exit 2 = --gate was asked and at least one row reads STALE-OPEN\n"
         "  exit 3 = the register is missing or malformed\n"
         "  exit 5 = bad flags\n")


class DebtStaleOpenError(Exception):
    """Raised when the reading cannot be produced honestly."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def item_round(item):
    """The row's own round from its item, or None (never a guess)."""
    found = None
    for match in ITEM_ROUND_RE.finditer(item or ""):
        found = int(match.group(1))
    return found


def note_rounds(note):
    """Round tokens in the note, in the order they appear."""
    return [int(match.group(1))
            for match in ITEM_ROUND_RE.finditer(note or "")]


def evidence_context(root, qa_dir=None):
    """The two shipped faces a round is judged by, read once."""
    try:
        live = round_evidence.audit(root)
        archived = state_seq.archived_labels(root)
        files = round_evidence.map_files(
            qa_dir if qa_dir is not None else os.path.join(root, "qa"))
    except round_evidence.RoundEvidenceError as exc:
        raise DebtStaleOpenError("E_DSRC_EVIDENCE", exc.detail)
    except state_seq.StateSeqError as exc:
        raise DebtStaleOpenError("E_DSRC_EVIDENCE", exc.detail)
    labelled = set()
    for row in live["rounds"]:
        labelled.add(row["round"])
    labelled.update(archived)
    return {"labelled": labelled, "files": files}


def round_reading(number, context):
    """DISCHARGED only when both shipped faces agree on this round."""
    return {
        "round": number,
        "labelled": number in context["labelled"],
        "files": len(context["files"].get(number) or []),
        "discharged": (number in context["labelled"]
                       and bool(context["files"].get(number))),
    }


def judge_row(row, context):
    """One open row, judged by its own item round and nothing else."""
    deciding = item_round(row["item"])
    tokens = note_rounds(row["note"])
    if deciding is None:
        state = "OPEN-UNNAMED"
        deciding_out = None
    elif round_reading(deciding, context)["discharged"]:
        state = "STALE-OPEN"
        deciding_out = deciding
    else:
        state = "OPEN-UNDISCHARGED"
        deciding_out = deciding
    return {
        "item": row["item"],
        "opened": row["opened"],
        "deciding": deciding_out,
        "state": state,
        "note_rounds": tokens,
    }


def scan(root, qa_dir=None):
    """Read the register, judge every open row, return the closed shape."""
    try:
        register = debt_register.register(root)
    except debt_register.DebtRegisterError as exc:
        raise DebtStaleOpenError("E_DSRC_REGISTER", exc.detail)
    if not register["present"]:
        raise DebtStaleOpenError(
            "E_DSRC_NO_REGISTER",
            "register file is missing: %s" % register["register"])
    context = evidence_context(root, qa_dir)
    rows = []
    stale = 0
    unnamed = 0
    undischarged = 0
    for row in register["rows"]:
        if row["state"] != "open":
            continue
        judged = judge_row(row, context)
        if judged["state"] == "STALE-OPEN":
            stale += 1
        elif judged["state"] == "OPEN-UNNAMED":
            unnamed += 1
        else:
            undischarged += 1
        rows.append(judged)
    if stale:
        verdict = "STALE-FOUND"
    else:
        verdict = "NO-STALE"
    return {
        "register": register["register"],
        "present": register["present"],
        "open_count": len(rows),
        "stale_count": stale,
        "unnamed_count": unnamed,
        "undischarged_count": undischarged,
        "rows": rows,
        "action": ACTION,
        "verdict": verdict,
    }


def one_line(report):
    """The single line an operator reads."""
    return ("DEBT STALE OPEN open=%d stale=%d unnamed=%d undischarged=%d "
            "action=%s verdict=%s"
            % (report["open_count"], report["stale_count"],
               report["unnamed_count"], report["undischarged_count"],
               report["action"], report["verdict"]))


def render(report):
    """Full rendering: the one line, then every open row with its state."""
    out = [one_line(report)]
    for row in report["rows"]:
        out.append("  %s item=%s opened=%s deciding=%s note_rounds=%s"
                   % (row["state"], row["item"], row["opened"],
                      "R%d" % row["deciding"] if row["deciding"] else "none",
                      ",".join("R%d" % tok for tok in row["note_rounds"])
                      or "none"))
    out.append("  %s: this reading closes nothing; an operator decides."
               % ACTION)
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    ordered = {}
    pinned = []
    for row in report["rows"]:
        item = {}
        for key in ROW_KEYS:
            item[key] = row[key]
        pinned.append(item)
    for key in REPORT_KEYS:
        ordered[key] = pinned if key == "rows" else report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def main(argv):
    check = False
    as_json = False
    gate = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    qa_dir = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--gate":
            gate = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_DSRC_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg == "--qa-dir":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_DSRC_BAD_ARGS: --qa-dir needs a path\n")
                return 5
            qa_dir = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_DSRC_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_DSRC_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = scan(root, qa_dir)
    except DebtStaleOpenError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if gate and report["verdict"] == "STALE-FOUND":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
