"""debt_gate - does the register name an item for THIS window? (R2267).

`state/debt.md` carries a machine-readable register and one open row may be
flagged `first=yes`: that is the item the next window is supposed to lead
with. Nothing enforced reading it, so a window could open, look somewhere
else and still look diligent. This gate answers exactly one question before
any work starts:

  * does the register carry an open `first=yes` row, and if so which one.

Three honest outcomes, no fourth:

  * CLAIM-FIRST - one row is flagged; it is named with its opened round, its
    carried age when a round is supplied, and its note, so the window either
    claims that item or explicitly clears it.
  * OPEN-NONE - the register is readable and no open row is flagged. That is
    not an error: an empty register and a register whose open rows all read
    `first=no` both mean the same thing, and the window owes its own row.
  * a refusal - the register is missing, unreadable or malformed. Absence of
    a file is NOT `OPEN-NONE`: a lost register must not read as "nothing
    owed", so the gate fails closed with its own code.

The row law is imported from `debt_register` rather than re-implemented, so
the register has exactly one owner and the gate cannot drift from the
checker. It writes nothing and reads no clock, so a reading is reproducible.

Criteria AC-DGT1..AC-DGT5 were pinned in state/queue/tech.md as the R2248 f
seed row BEFORE this code existed. Pure ASCII source, stdlib only, zero
network.
"""

import json
import os
import sys

import debt_register

VERDICTS = ("CLAIM-FIRST", "OPEN-NONE")

REPORT_KEYS = (
    "register",
    "present",
    "verdict",
    "item",
    "opened",
    "carried",
    "stale",
    "note",
    "open_count",
    "first_count",
    "current_round",
)

USAGE = ("usage: debt_gate.py --check [--root PATH] [--round R<nnnn>] "
         "[--json]\n"
         "  exit 0 = CLAIM-FIRST (the register names an item for this window)\n"
         "  exit 2 = OPEN-NONE (no open first=yes row; this window owes one)\n"
         "  exit 3 = register missing, unreadable or malformed\n"
         "  exit 5 = bad flags\n")


class DebtGateError(Exception):
    """Raised when the register cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def gate(root, round_label=None):
    """Read the register and return the closed gate report shape."""
    try:
        report = debt_register.register(root, round_label)
    except debt_register.DebtRegisterError as exc:
        # The register keeps its own codes; the gate only re-labels the
        # family so a caller can tell a gate refusal from a bare read.
        suffix = exc.code[5:] if exc.code.startswith("E_DR_") else exc.code
        raise DebtGateError("E_DGT_" + suffix, exc.detail)
    if not report["present"]:
        raise DebtGateError(
            "E_DGT_NO_REGISTER",
            "register file is missing: %s" % report["register"])
    lead = None
    for row in report["rows"]:
        if row["state"] == "open" and row["first"] == "yes":
            lead = row
            break
    if lead is None:
        verdict = "OPEN-NONE"
    else:
        verdict = "CLAIM-FIRST"
    return {
        "register": report["register"],
        "present": report["present"],
        "verdict": verdict,
        "item": lead["item"] if lead else None,
        "opened": lead["opened"] if lead else None,
        "carried": lead["carried"] if lead else None,
        "stale": lead["stale"] if lead else False,
        "note": lead["note"] if lead else "",
        "open_count": report["open_count"],
        "first_count": report["first_count"],
        "current_round": report["current_round"],
    }


def one_line(report):
    """The single line an operator reads before any work starts."""
    if report["current_round"] is None:
        aged = "carried=unknown"
    elif report["carried"] is None:
        aged = "carried=n/a"
    else:
        aged = "carried=%d stale=%s" % (
            report["carried"], "yes" if report["stale"] else "no")
    return ("DEBT GATE verdict=%s item=%s opened=%s %s open=%d first=%d"
            % (report["verdict"], report["item"] or "none",
               report["opened"] or "none", aged,
               report["open_count"], report["first_count"]))


def render(report):
    """Full text rendering: the one line, then the note of the named row."""
    out = [one_line(report)]
    if report["verdict"] == "CLAIM-FIRST" and report["note"]:
        out.append("  note: %s" % report["note"])
    elif report["verdict"] == "OPEN-NONE":
        out.append("  note: no open first=yes row; this window owes one")
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def main(argv):
    check = False
    as_json = False
    round_label = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--round":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_DGT_BAD_ARGS: --round needs an R-number\n")
                sys.stdout.write(USAGE)
                return 5
            round_label = argv[index]
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_DGT_BAD_ARGS: --root needs a path\n")
                sys.stdout.write(USAGE)
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_DGT_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_DGT_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = gate(root, round_label)
    except DebtGateError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "OPEN-NONE":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))