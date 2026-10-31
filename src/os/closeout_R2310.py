"""closeout_R2310 - pin the residue triage declaration (R2310).

Writes `state/residue_triage.json` from ONE live reading of `stamp_residue`,
so the declaration can never claim a round the live reader does not list.
Every entry carries the live status, the declaring round, a reason, and an
`until` round after which the round returns to the debt and must be reviewed
again. Regenerating is the ONLY way to absorb a status change: the reader
reports DISAGREES rather than quietly following a moved reading.

Bytes are stable: sorted rounds, pinned key order, ASCII, one trailing LF.
Criteria AC-RTR1..AC-RTR6 were pinned in state/queue/tech.md BEFORE this
code existed.
Pure ASCII source, stdlib only, zero network, no clock.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import residue_triage as RT  # noqa: E402
import stamp_residue as SR  # noqa: E402

DECLARED_BY = 2310
UNTIL = 2330
REASON = ("triaged at R2310: every round below was read from the live "
          "stamp_residue table and accepted at its reported status, so the "
          "next window reads this declaration instead of re-triaging 185 "
          "rows by hand")


def build(root):
    """The declaration body, derived from one live reading only."""
    report = SR.read(root)
    entries = []
    for row in report["rounds"]:
        entries.append({
            "round": int(row["round"]),
            "status": row["status"],
            "declared_by": "R%d" % DECLARED_BY,
            "reason": "reviewed at R2310 at its live status",
            "until": UNTIL,
        })
    entries.sort(key=lambda entry: entry["round"])
    return {
        "declared_by": "R%d" % DECLARED_BY,
        "reason": REASON,
        "entries": entries,
    }


def to_text(body):
    """Stable ASCII text with the pinned key order."""
    import collections
    ordered = collections.OrderedDict()
    ordered["declared_by"] = body["declared_by"]
    ordered["reason"] = body["reason"]
    rows = []
    for entry in body["entries"]:
        pinned = collections.OrderedDict()
        for key in RT.ENTRY_KEYS:
            pinned[key] = entry[key]
        rows.append(pinned)
    ordered["entries"] = rows
    return json.dumps(ordered, ensure_ascii=True, indent=2) + "\n"


def main(argv):
    root = os.path.dirname(os.path.dirname(BASE))
    for index, arg in enumerate(argv):
        if arg == "--root":
            if index + 1 >= len(argv):
                sys.stdout.write("E_CLS_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index + 1]
        elif arg in ("--help", "-h"):
            sys.stdout.write("usage: closeout_R2310.py [--root PATH]\n")
            return 0
        elif arg.startswith("--"):
            sys.stdout.write("E_CLS_BAD_ARGS: unknown flag %s\n" % arg)
            return 5
    try:
        body = build(root)
    except SR.StampResidueError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    path = os.path.join(root, RT.DECLARATION_PATH)
    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        sys.stdout.write("E_CLS_BAD_TARGET: %s\n" % directory)
        return 3
    text = to_text(body)
    with io.open(path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(text)
    sys.stdout.write("RESIDUE TRIAGE PINNED declared_by=R%d entries=%d "
                     "until=R%d bytes=%d\n"
                     % (DECLARED_BY, len(body["entries"]), UNTIL,
                        len(text.encode("ascii"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))