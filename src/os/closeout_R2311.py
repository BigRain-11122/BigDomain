"""closeout_R2311 - carry the pinned residue declaration forward one round.

R2310 pinned 185 residue rounds at `until=R2330`. The R2311 waterline fold
moved nine whole log blocks into the archive, and one of those blocks held
the only log item of R2298: that round is delivered (its accepted stamp sits
on a closed queue row) but no longer has a live log line, so the live reader
now lists it as residue. This writer carries every existing entry verbatim
and adds ONLY the rounds the live reader names that the declaration does not
yet cover, each stamped `declared_by=R2311` with the fold as its reason, so
a carried decision is never relabelled as this window's work.

It fails closed in both directions: a declared round the live reader no
longer lists is refused (the declaration side would go stale), and a live
round is never absorbed without an explicit reason line.

Bytes are stable: entries sorted by round, pinned key order, ASCII, one
trailing LF.

  python src/os/closeout_R2311.py             dry run (writes nothing)
  python src/os/closeout_R2311.py --execute   write and read back
"""

import collections
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import residue_triage as RT  # noqa: E402
import stamp_residue as SR  # noqa: E402

DECLARED_BY = "R2311"
UNTIL = 2330
REASON = ("the R2311 waterline fold moved this round's only log item into "
          "the archive while its accepted stamp still sits on a closed "
          "queue row, so the delivery stands and the round stops reading "
          "as untriaged debt")


def plan(root):
    path = os.path.join(root, RT.DECLARATION_PATH)
    if not os.path.isfile(path):
        raise SR.StampResidueError("E_CLS_NO_DECLARATION", path)
    try:
        with io.open(path, encoding="ascii") as handle:
            body = json.load(handle)
    except (IOError, OSError, ValueError) as exc:
        raise SR.StampResidueError("E_CLS_BAD_DECLARATION", str(exc))
    entries = list(body.get("entries") or [])
    declared = {}
    for entry in entries:
        declared[int(entry["round"])] = entry
    live = SR.read(root)
    live_rounds = {}
    for row in live["rounds"]:
        live_rounds[int(row["round"])] = row["status"]
    stale = sorted(set(declared) - set(live_rounds))
    if stale:
        raise SR.StampResidueError(
            "E_CLS_STALE_DECLARATION",
            "declared rounds the live reader no longer lists: %s" % stale)
    added = sorted(set(live_rounds) - set(declared))
    for number in added:
        entries.append({
            "round": number,
            "status": live_rounds[number],
            "declared_by": DECLARED_BY,
            "reason": REASON,
            "until": UNTIL,
        })
    entries.sort(key=lambda entry: int(entry["round"]))
    ordered = collections.OrderedDict()
    ordered["declared_by"] = body.get("declared_by")
    ordered["reason"] = body.get("reason")
    ordered["entries"] = [
        collections.OrderedDict((key, entry[key]) for key in RT.ENTRY_KEYS)
        for entry in entries]
    text = json.dumps(ordered, ensure_ascii=True, indent=2) + "\n"
    return path, body, ordered, added, text


def main(argv):
    root = os.path.dirname(os.path.dirname(BASE))
    execute = False
    for index, arg in enumerate(argv):
        if arg == "--root":
            if index + 1 >= len(argv):
                sys.stdout.write("E_CLS_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index + 1]
        elif arg == "--execute":
            execute = True
        elif arg in ("--help", "-h"):
            sys.stdout.write("usage: closeout_R2311.py [--root PATH] "
                             "[--execute]\n")
            return 0
        elif arg.startswith("--"):
            sys.stdout.write("E_CLS_BAD_ARGS: unknown flag %s\n" % arg)
            return 5
    try:
        path, before, body, added, text = plan(os.path.abspath(root))
    except SR.StampResidueError as exc:
        sys.stdout.write("%s\n" % exc)
        return 3
    wrote = "no"
    readback = "n/a"
    if execute:
        with io.open(path, "w", encoding="ascii", newline="\n") as handle:
            handle.write(text)
        wrote = "yes"
        with io.open(path, encoding="ascii") as handle:
            again = handle.read()
        readback = "ok" if again == text else "DRIFT"
    sys.stdout.write(
        "RESIDUE TRIAGE CARRY entries=%d->%d added=%s wrote=%s "
        "readback=%s bytes=%d\n"
        % (len(before["entries"]), len(body["entries"]), added, wrote,
           readback, len(text.encode("ascii"))))
    return 0 if readback in ("n/a", "ok") else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))