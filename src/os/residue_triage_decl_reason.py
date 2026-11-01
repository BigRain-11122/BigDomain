"""residue_triage_decl_reason - is the triage head still speaking for its set? (R2350)

`state/residue_triage.json` carries a HEAD claim - one `declared_by` and one
`reason` sentence that speak for the WHOLE entry set ("every round was read
from the live stamp_residue table once more and accepted at its reported
status until R2350"). Entries may be appended later, through the shipped
writer, carrying their OWN `declared_by` and `until`, and nothing compares the
two. Measured at R2335 and still true at R2350: the head reads `declared_by
R2331 ... until R2350` while entries appended at R2333/R2334/R2336/R2338/
R2341/R2342/R2343/R2345/R2346/R2348 carry their own rounds and three of them
carry `until 2360`. The head can therefore describe a set that no longer
exists, and a reader of the head alone believes a window that has already been
outgrown.

This is one READ-ONLY reading that compares the head claim to the entries:

  * every entry and every status come from `residue_triage` - the declaration
    is loaded through `residue_triage.load_declaration` and the status
    vocabulary is read from `residue_triage` own stamp reader at call time, so
    patching either moves this reading and nothing is re-derived here;
  * an entry whose `declared_by` is later than the head's reads HEAD-STALE
    naming both rounds and the entry round;
  * an entry whose `until` differs from the head's reads HEAD-STALE naming both
    windows, so an append that outlives the head is never silent;
  * a head that matches every entry reads HEAD-CURRENT with zero breaks;
  * a missing declaration reads UNPINNED rather than a fabricated pass.

Pure read: nothing is written, no clock is read, no network import.
Criteria AC-RTD1..AC-RTD6 were pinned inside the R2335 seed row of
state/queue/tech.md BEFORE this code existed.
Pure ASCII source, stdlib only.
"""

import json
import os
import sys

import residue_triage as RT

DECLARATION_PATH = RT.DECLARATION_PATH

REPORT_KEYS = (
    "declaration",
    "declared_by",
    "head_until",
    "head_reason",
    "entries",
    "breaks",
    "first_break",
    "verdict",
)

BREAK_KEYS = (
    "round",
    "kind",
    "entry_declared_by",
    "head_declared_by",
    "entry_until",
    "head_until",
)

VERDICTS = ("HEAD-CURRENT", "HEAD-STALE", "UNPINNED")

BREAK_KINDS = ("DECLARED_BY", "UNTIL")


class DeclReasonError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def statuses():
    """The status vocabulary, read from residue_triage at call time (AC-RTD1).

    `residue_triage` asks its own stamp reader for the tuple, so patching that
    reader moves both the declaration loader and this reading.
    """
    return tuple(RT.SR.STATUSES)


def load(root):
    """The declaration through residue_triage own loader (AC-RTD1)."""
    try:
        declaration = RT.load_declaration(root)
    except RT.ResidueTriageError as exc:
        raise DeclReasonError(exc.code, exc.detail)
    if declaration is None:
        return None
    vocabulary = statuses()
    for entry in declaration["entries"]:
        if entry["status"] not in vocabulary:
            raise DeclReasonError(
                "E_RTD_BAD_STATUS",
                "entry R%d carries %r, not one of the live statuses %s"
                % (entry["round"], entry["status"], ", ".join(vocabulary)))
    return declaration


def compare(declaration, head_until):
    """Every entry judged against the head claim, in entry order (AC-RTD2/3)."""
    head_declared_by = declaration["declared_by"]
    breaks = []
    for entry in declaration["entries"]:
        if entry["declared_by"] > head_declared_by:
            breaks.append({
                "round": "R%d" % entry["round"],
                "kind": "DECLARED_BY",
                "entry_declared_by": "R%d" % entry["declared_by"],
                "head_declared_by": "R%d" % head_declared_by,
                "entry_until": "R%d" % entry["until"],
                "head_until": "-" if head_until is None
                              else "R%d" % head_until,
            })
        elif head_until is not None and entry["until"] != head_until:
            breaks.append({
                "round": "R%d" % entry["round"],
                "kind": "UNTIL",
                "entry_declared_by": "R%d" % entry["declared_by"],
                "head_declared_by": "R%d" % head_declared_by,
                "entry_until": "R%d" % entry["until"],
                "head_until": "R%d" % head_until,
            })
    return breaks


def head_window(declaration):
    """The window the head claims: the mode of the entries' own `until`.

    A head sentence does not name a round, so the reading measures the claim
    the only way the file can be measured: the window most entries carry is
    the head's, and any entry outside it is a break. This is stated plainly
    because the head text is prose and prose cannot be compared to a number.
    """
    counts = {}
    for entry in declaration["entries"]:
        counts[entry["until"]] = counts.get(entry["until"], 0) + 1
    if not counts:
        return None
    # most common window; ties go to the LARGEST so a later append can never
    # be the one that defines the head (the conservative reading).
    ranked = sorted(counts.items(), key=lambda item: (-item[1], -item[0]))
    return ranked[0][0]


def read(root):
    """The whole reading: head claim versus entries, one verdict."""
    declaration = load(root)
    if declaration is None:
        return {
            "declaration": "UNPINNED",
            "declared_by": "-",
            "head_until": "-",
            "head_reason": "-",
            "entries": 0,
            "breaks": [],
            "first_break": "-",
            "verdict": "UNPINNED",
        }
    window = head_window(declaration)
    breaks = compare(declaration, window)
    first = breaks[0]["round"] if breaks else "-"
    return {
        "declaration": "PINNED",
        "declared_by": "R%d" % declaration["declared_by"],
        "head_until": "-" if window is None else "R%d" % window,
        "head_reason": declaration["reason"],
        "entries": len(declaration["entries"]),
        "breaks": breaks,
        "first_break": first,
        "verdict": "HEAD-STALE" if breaks else "HEAD-CURRENT",
    }


def one_line(report):
    """The single line an operator reads."""
    return ("RESIDUE TRIAGE DECL declared_by=%s head_until=%s entries=%d "
            "breaks=%d first_break=%s verdict=%s"
            % (report["declared_by"], report["head_until"],
               report["entries"], len(report["breaks"]),
               report["first_break"], report["verdict"]))


def render(report):
    """Full text: the one line, then every break in entry order."""
    out = [one_line(report)]
    for row in report["breaks"]:
        out.append("  BREAK %s kind=%s entry_declared_by=%s "
                   "head_declared_by=%s entry_until=%s head_until=%s"
                   % (row["round"], row["kind"], row["entry_declared_by"],
                      row["head_declared_by"], row["entry_until"],
                      row["head_until"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (no extra keys leak)."""
    pinned = []
    for row in report["breaks"]:
        narrow = {}
        for key in BREAK_KEYS:
            narrow[key] = row[key]
        pinned.append(narrow)
    ordered = {}
    for key in REPORT_KEYS:
        if key == "breaks":
            ordered["breaks"] = pinned
        else:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: residue_triage_decl_reason.py --check [--root PATH] [--json]\n"
         "  exit 0 = HEAD-CURRENT (the head still speaks for every entry)\n"
         "  exit 2 = HEAD-STALE (an entry outgrew the head) or UNPINNED\n"
         "  exit 3 = the declaration is unreadable or badly shaped\n"
         "  exit 5 = bad flags\n")


def main(argv):
    check = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RTD_BAD_ARGS: --root needs a value\n")
                sys.stdout.write(USAGE)
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RTD_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_RTD_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = read(root)
    except DeclReasonError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code == "E_RTD_BAD_ARGS":
            return 5
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "HEAD-CURRENT":
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))