"""queue_only_reconcile - which queue done stamps never reached the log (R2263).

`state_seq` reports a residue it does not classify: done-stamped rounds in
state/queue/ that carry no log item. At the R2257 reading that number was 156,
and nobody could say which of them were folded out of the log window
legitimately and which were never logged at all. The two are indistinguishable
from the outside - a window whose ledger line was silently dropped looks
exactly like one that aged out - so an unreconciled residue is a place where
real debt can hide behind an honest-looking number.

This reader splits the residue in two against a declared log-window floor:
a stamp BELOW the floor that is absent from the log is FOLDED (it aged out, as
the fold intends), and a stamp AT OR ABOVE the floor that is absent is
NEVER-LOGGED (a round that claimed a queue row and left no log item - real
debt). The floor is mandatory and explicit, because a default floor would
silently relabel real debt as age.

Three deliberate narrowings:
  * The stamp law and the label law are `state_seq`'s, imported rather than
    re-implemented, so the two faces cannot drift apart.
  * The three classes are exhaustive by construction - a stamp is LOGGED,
    FOLDED or NEVER-LOGGED and there is no fourth answer - and their counts are
    required to sum to the stamp count before a verdict is issued.
  * A report is a reading only. Nothing is written, no clock is read, and
    unreadable input fails closed instead of producing a classification.

Criteria AC-QOC1..AC-QOC6 were pinned in state/queue/tech.md as the R2257 seed
row BEFORE this code existed. The declared-floor wiring (AC-QFW1..AC-QFW6) was
pinned as the R2266 seed row BEFORE it existed: `--floor-from-declaration`
takes the floor from `queue_floor_decl.resolve` so the pinned declaration has a
real consumer and the two faces cannot disagree by hand, while `--floor` stays
for an explicit reading and the two are refused together.
Pure ASCII source, stdlib only, zero network.
"""

import json
import os
import sys

import queue_floor_decl
import state_seq

VERDICTS = ("EMPTY", "RECONCILED", "RESIDUE")

REPORT_KEYS = (
    "floor",
    "stamps",
    "logged",
    "folded",
    "never_logged",
    "folded_rounds",
    "never_logged_rounds",
    "max_stamp",
    "verdict",
)


class QueueOnlyError(Exception):
    """Raised when the reader cannot produce an honest classification."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parse_floor(value):
    """An explicit round floor: "R<n>" or "<n>", nothing else (AC-QOC3)."""
    if value is None:
        raise QueueOnlyError("E_QOC_BAD_FLOOR", "a floor is required")
    if not isinstance(value, str):
        raise QueueOnlyError("E_QOC_BAD_FLOOR", repr(value))
    text = value.strip()
    if text[:1] in ("R", "r"):
        text = text[1:]
    if not text or not text.isdigit():
        raise QueueOnlyError("E_QOC_BAD_FLOOR", repr(value))
    return int(text)


def declared_floor(root):
    """The declared floor through the resolver, or a refusal (AC-QFW1/QFW2).

    The floor is taken from `queue_floor_decl.resolve` and never derived from
    the log: a derived floor is the exact blindness `log_floor` exists to stop,
    so a declaration that is not PINNED refuses the split instead of falling
    back to one.
    """
    try:
        report = queue_floor_decl.resolve(root)
    except queue_floor_decl.FloorDeclError as exc:
        if exc.code == "E_FDL_UNREADABLE":
            raise QueueOnlyError("E_QFW_UNREADABLE",
                                 "%s (%s)" % (exc.code, exc.detail))
        raise QueueOnlyError("E_QFW_NOT_PINNED",
                             "%s (%s)" % (exc.code, exc.detail))
    return report["floor"]


def classify(stamps, labels, floor):
    """Split the stamps into LOGGED / FOLDED / NEVER-LOGGED (AC-QOC2)."""
    logged_set = set(labels)
    logged = []
    folded = []
    never = []
    for number in stamps:
        if number in logged_set:
            logged.append(number)
        elif number < floor:
            folded.append(number)
        else:
            never.append(number)
    return logged, folded, never


def audit(root, floor):
    """Read the queues and the log, classify, and return the closed report."""
    try:
        state = state_seq.load_state(root)
        labels = state_seq.extract_labels(state)
        stamps = state_seq.queue_done_rounds(root)
    except state_seq.StateSeqError as exc:
        raise QueueOnlyError("E_QOC_UNREADABLE",
                             "%s (%s)" % (exc.code, exc.detail))

    logged, folded, never = classify(stamps, labels, floor)
    if len(logged) + len(folded) + len(never) != len(stamps):
        raise QueueOnlyError("E_QOC_BAD_CLASS",
                             "%d != %d" % (len(logged) + len(folded)
                                           + len(never), len(stamps)))

    if not stamps:
        verdict = "EMPTY"
    elif never:
        verdict = "RESIDUE"
    else:
        verdict = "RECONCILED"

    return {
        "floor": floor,
        "stamps": len(stamps),
        "logged": len(logged),
        "folded": len(folded),
        "never_logged": len(never),
        "folded_rounds": folded,
        "never_logged_rounds": never,
        "max_stamp": stamps[-1] if stamps else None,
        "verdict": verdict,
    }


def one_line(report):
    """The single line an operator reads."""
    return ("QUEUE ONLY floor=R%d stamps=%d logged=%d folded=%d "
            "never_logged=%d max_stamp=%s verdict=%s"
            % (report["floor"], report["stamps"], report["logged"],
               report["folded"], report["never_logged"],
               report["max_stamp"], report["verdict"]))


def render(report):
    """Full text rendering: the one line, then every never-logged round."""
    out = [one_line(report)]
    for number in report["never_logged_rounds"]:
        out.append("  NEVER-LOGGED R%d" % number)
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order (no indent, ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: queue_only_reconcile.py --check "
         "(--floor R<n> | --floor-from-declaration) "
         "[--root PATH] [--json]\n"
         "  exit 0 = every stamp is LOGGED or FOLDED (or the queues are "
         "honestly empty)\n"
         "  exit 2 = at least one stamp is NEVER-LOGGED, the declared floor "
         "is not PINNED, or the flags are bad\n"
         "  exit 3 = state.json, a queue file or the declaration is missing "
         "or unparseable\n")


def main(argv):
    check = False
    as_json = False
    from_decl = False
    floor_text = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--floor-from-declaration":
            from_decl = True
        elif arg in ("--floor", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_QOC_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 2
            if arg == "--floor":
                floor_text = argv[index]
            else:
                root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_QOC_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 2
        index += 1
    if not check:
        sys.stdout.write("E_QOC_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    # AC-QFW3: two sources of truth are the ambiguity this closes, and zero
    # sources would let a derived floor back in silently.
    if from_decl and floor_text is not None:
        sys.stdout.write("E_QFW_BOTH: --floor and --floor-from-declaration "
                         "are two sources of truth\n")
        sys.stdout.write(USAGE)
        return 2
    if from_decl:
        try:
            floor = declared_floor(root)
        except QueueOnlyError as exc:
            sys.stdout.write("%s: %s\n" % (exc.code, exc.detail))
            if exc.code == "E_QFW_UNREADABLE":
                return 3
            return 2
    else:
        try:
            floor = parse_floor(floor_text)
        except QueueOnlyError as exc:
            sys.stdout.write("%s\n" % exc.code)
            sys.stdout.write(USAGE)
            return 2
    try:
        report = audit(root, floor)
    except QueueOnlyError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "RESIDUE":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))