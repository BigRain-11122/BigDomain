# stamp_residue.py - the whole stamp residue as one table, in one pass
# Criteria AC-SRS1..AC-SRS6 were pre-registered in state/queue/tech.md as the
# R2284 seed row BEFORE this file existed. Anchor check at HEAD 2026-10-31:
# stamp_residue / AC-SRS / E_SRS / os-stamp-residue / test_stamp_residue were
# all git grep -F zero-occupancy rc=1 (the bare word stamp_residue hit only
# prose in state/queue/tech.md, src/os/backlog.md and src/os/state.json).
#
# Why this exists: state_seq already names the residue - the rounds that
# stamped a queue row and left no log item (the live reading carries 185 of
# them) - and stamp_locator answers where ONE round's stamp sits. Triaging
# the residue was still N hand greps: run the locator per round and remember
# which hits were real closed rows.
#
# This reader joins the two, and nothing else: the residue list is imported
# from state_seq (its audit owns the "stamped but never logged" law) and each
# round is located by stamp_locator (its scan owns the "where does this stamp
# sit" law, and it reads the stamp regex off state_seq at call time). Patching
# either one moves this reading, which is how the suite proves the import.
#
# The distinction this makes visible: a stamp on a CLOSED row is delivery
# evidence; a stamp sitting on an OPEN row proves nothing - the row is not
# finished, so the stamp was either copied or left over. A round whose only
# hits are open reads STAMP-ONLY-OPEN rather than as a delivery.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import json
import os
import sys

import stamp_locator as SL
import state_seq as SQ

STATUSES = ("DELIVERED", "STAMP-ONLY-OPEN", "NO-HIT")

VERDICTS = ("CLEAN", "RESIDUE")

REPORT_KEYS = (
    "round_count",
    "delivered",
    "stamp_only_open",
    "no_hit",
    "verdict",
    "rounds",
)

ROW_KEYS = (
    "round",
    "hit_count",
    "closed_hits",
    "open_hits",
    "status",
    "hits",
)

HIT_KEYS = (
    "file",
    "line",
    "closed",
    "row_head",
)


class StampResidueError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def queue_dir(root):
    """The queue directory, refused when it is not there (AC-SRS5)."""
    directory = os.path.join(root, "state", "queue")
    if not os.path.isdir(directory):
        raise StampResidueError("E_SRS_BAD_QUEUE", directory)
    return directory


def residue_rounds(root):
    """The residue list, read through state_seq and never re-derived."""
    queue_dir(root)
    try:
        report = SQ.audit(root)
    except SQ.StateSeqError as exc:
        raise StampResidueError("E_SRS_BAD_STATE", exc.detail)
    rounds = []
    for number in report.get("queue_only") or []:
        rounds.append(int(number))
    return sorted(set(rounds))


def hits_of(root, number):
    """One round's hits, read through stamp_locator, keyed and bounded."""
    try:
        located = SL.locate(root, number)
    except SL.StampLocatorError as exc:
        raise StampResidueError("E_SRS_BAD_QUEUE", exc.detail)
    out = []
    for hit in located["hits"]:
        out.append({
            "file": hit["file"],
            "line": hit["line"],
            "closed": bool(hit["closed"]),
            "row_head": hit["row_head"],
        })
    return out


def classify(hits):
    """A round's status from its own hits (AC-SRS3, AC-SRS4)."""
    closed = len([hit for hit in hits if hit["closed"]])
    opened = len([hit for hit in hits if not hit["closed"]])
    if closed:
        status = "DELIVERED"
    elif opened:
        status = "STAMP-ONLY-OPEN"
    else:
        status = "NO-HIT"
    return closed, opened, status


def read(root):
    """The whole residue as one table; totals reconcile with the list."""
    rounds = residue_rounds(root)
    rows = []
    delivered = 0
    stamp_only_open = 0
    no_hit = 0
    for number in rounds:
        hits = hits_of(root, number)
        closed, opened, status = classify(hits)
        if status == "DELIVERED":
            delivered += 1
        elif status == "STAMP-ONLY-OPEN":
            stamp_only_open += 1
        else:
            no_hit += 1
        rows.append({
            "round": number,
            "hit_count": len(hits),
            "closed_hits": closed,
            "open_hits": opened,
            "status": status,
            "hits": hits,
        })
    if rows:
        verdict = "RESIDUE"
    else:
        verdict = "CLEAN"
    return {
        "round_count": len(rows),
        "delivered": delivered,
        "stamp_only_open": stamp_only_open,
        "no_hit": no_hit,
        "verdict": verdict,
        "rounds": rows,
    }


def one_line(report):
    """The one line an operator reads."""
    return ("STAMP RESIDUE rounds=%d delivered=%d stamp_only_open=%d "
            "no_hit=%d verdict=%s"
            % (report["round_count"], report["delivered"],
               report["stamp_only_open"], report["no_hit"],
               report["verdict"]))


def render(report):
    """Full text rendering: the one line, then every residue round."""
    out = [one_line(report)]
    for row in report["rounds"]:
        out.append("  ROUND R%d status=%s hits=%d closed=%d open=%d"
                   % (row["round"], row["status"], row["hit_count"],
                      row["closed_hits"], row["open_hits"]))
        for hit in row["hits"]:
            out.append("    HIT %s:%d closed=%s"
                       % (hit["file"], hit["line"],
                          "yes" if hit["closed"] else "no"))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        if key == "rounds":
            continue
        ordered[key] = report[key]
    pinned_rounds = []
    for row in report["rounds"]:
        pinned = {}
        for key in ROW_KEYS:
            if key == "hits":
                continue
            pinned[key] = row[key]
        pinned_hits = []
        for hit in row["hits"]:
            narrow = {}
            for key in HIT_KEYS:
                narrow[key] = hit[key]
            pinned_hits.append(narrow)
        pinned["hits"] = pinned_hits
        pinned_rounds.append(pinned)
    ordered["rounds"] = pinned_rounds
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: stamp_residue.py --check [--root PATH] [--json]\n"
         "  exit 0 = the residue is CLEAN (no stamped-but-never-logged "
         "round)\n"
         "  exit 2 = RESIDUE (any round is stamped and never logged) or bad "
         "flags\n"
         "  exit 3 = state.json or a queue file is missing or unreadable\n")


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
                sys.stdout.write("E_SRS_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_SRS_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_SRS_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = read(root)
    except StampResidueError as exc:
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