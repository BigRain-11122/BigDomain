# queue_head_delivered.py - an offer that asks the occupancy reading first
# Criteria AC-QHO1..AC-QHO6 were pre-registered in state/queue/tech.md as the
# R2337 seed row BEFORE this file existed. Anchor check at HEAD 2026-11-01:
# queue_head_delivered / AC-QHO / E_QHO / os-queue-head-delivered /
# test_queue_head_delivered were git grep -F zero-occupancy outside prose
# (the seed row, the backlog, the export and the R2337/R2351/R2353 closeout
# scripts), disclosed.
#
# Why this exists: queue_occupancy answers whether a row is already shipped,
# but queue_head never asks it - the offer still names the first prefixed
# open row, which is exactly how the R2315 row kept pointing a fresh window
# at finished work. This module is the offer wired to that reading: a row
# whose occupancy reads DELIVERED is walked over and NAMED with the module
# that shipped it, the offer continues to the next claimable row, and a
# queue whose every prefixed row is delivered reads ALL-DELIVERED instead
# of the NO-HEAD that would mistake a full queue for an empty one.
#
# The occupancy reading and the row laws are IMPORTED, never re-implemented:
#   - occupancy (which row has shipped) comes from queue_occupancy,
#   - the queue file, its path and the prefix belong to queue_floor and
#     queue_row, reached through that reader.
# This module carries no second module-path scan and no row parser.
#
# Pure read: nothing is written, no suite is run, no clock is read, no
# network import. Source is pure ASCII, stdlib only.
#
# CLI: queue_head_delivered.py --head [QUEUE] [--root PATH] [--json]
#   exit 0 = a row was offered
#   exit 2 = ALL-DELIVERED or NO-HEAD (nothing left to claim)
#   exit 3 = the queue file is missing / unreadable
#   exit 5 = bad flags

import json
import os
import sys

import queue_occupancy as QO

VERDICT_OFFERED = "OFFERED"
VERDICT_ALL_DELIVERED = "ALL-DELIVERED"
VERDICT_NO_HEAD = "NO-HEAD"

VERDICTS = (VERDICT_OFFERED, VERDICT_ALL_DELIVERED, VERDICT_NO_HEAD)

HEAD_KEYS = ("line", "prefix", "modules", "status")
WALK_KEYS = ("line", "prefix", "modules", "status")

REPORT_KEYS = (
    "queue",
    "path",
    "present",
    "head",
    "walked_over",
    "claimable_rows",
    "prefixed_rows",
    "delivered_rows",
    "verdict",
)

USAGE = ("usage: queue_head_delivered.py --head [QUEUE] [--root PATH] [--json]\n"
         "  QUEUE defaults to tech (state/queue/<QUEUE>.md)\n"
         "  exit 0 = a row was offered\n"
         "  exit 2 = ALL-DELIVERED or NO-HEAD (nothing left to claim)\n"
         "  exit 3 = the queue file is missing or unreadable\n"
         "  exit 5 = bad flags\n")


def offered(row):
    """The pinned shape of a row the offer hands out."""
    return {"line": row["line"], "prefix": row["prefix"],
            "modules": list(row["modules"]), "status": row["status"]}


def offer(report):
    """Walk the occupancy reading in FILE order and offer the first row
    that is not DELIVERED (AC-QHO4)."""
    head = None
    walked = []
    for row in report["rows"]:
        if head is not None:
            # Behind the head: not walked over, not part of the offer.
            continue
        if row["status"] == QO.STATUS_DELIVERED:
            walked.append(offered(row))
            continue
        head = offered(row)
    if head is not None:
        verdict = VERDICT_OFFERED
    elif report["prefixed_rows"] > 0:
        # Every prefixed row has shipped: a full queue is not an empty one.
        verdict = VERDICT_ALL_DELIVERED
    else:
        verdict = VERDICT_NO_HEAD
    return {
        "queue": report["queue"],
        "path": report["path"],
        "present": report["present"],
        "head": head,
        "walked_over": walked,
        "claimable_rows": report["claimable_rows"],
        "prefixed_rows": report["prefixed_rows"],
        "delivered_rows": report["delivered_rows"],
        "verdict": verdict,
    }


def read(root, name="tech"):
    """One offer from one queue, on top of the occupancy reader (AC-QHO1)."""
    return offer(QO.audit_root(root, name))


def one_line(report):
    """The single line an operator reads."""
    if report["head"] is None:
        return ("QUEUE OFFER %s %s prefixed=%d delivered=%d"
                % (report["queue"], report["verdict"],
                   report["prefixed_rows"], report["delivered_rows"]))
    return ("QUEUE OFFER %s line=%d prefix=%s walked_over=%d claimable=%d "
            "verdict=%s" % (report["queue"], report["head"]["line"],
                            report["head"]["prefix"],
                            len(report["walked_over"]),
                            report["claimable_rows"], report["verdict"]))


def render(report):
    """The one line, the offered row, then each row walked over."""
    out = [one_line(report)]
    if not report["present"]:
        out.append("  MISSING %s" % report["path"])
    if report["head"] is not None:
        out.append("  OFFER %s:%d %s modules=%s"
                   % (report["path"], report["head"]["line"],
                      report["head"]["prefix"],
                      ",".join(report["head"]["modules"]) or "-"))
    for item in report["walked_over"]:
        out.append("  WALKED %s:%d %s DELIVERED modules=%s"
                   % (report["path"], item["line"], item["prefix"],
                      ",".join(item["modules"]) or "-"))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    if report["head"] is not None:
        head_out = {}
        for key in HEAD_KEYS:
            head_out[key] = report["head"][key]
        ordered["head"] = head_out
    walked_out = []
    for item in report["walked_over"]:
        pinned = {}
        for key in WALK_KEYS:
            pinned[key] = item[key]
        walked_out.append(pinned)
    ordered["walked_over"] = walked_out
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


class _BadFlags(Exception):
    """A bad flag, kept local so the CLI code stays fixed."""


def parse_args(argv):
    """Read the flags by hand so exit 5 stays ours and no clock is touched."""
    opts = {"head": False, "json": False,
            "root": os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))),
            "queue": "tech"}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--head":
            opts["head"] = True
        elif arg == "--json":
            opts["json"] = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                raise _BadFlags("--root needs a path")
            opts["root"] = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return None
        elif arg.startswith("-"):
            raise _BadFlags("unknown flag %s" % arg)
        else:
            opts["queue"] = arg
        index += 1
    if not opts["head"]:
        raise _BadFlags("--head is required")
    return opts


def main(argv):
    try:
        opts = parse_args(argv)
    except _BadFlags as exc:
        sys.stdout.write("E_QHO_BAD_ARGS: %s\n" % exc)
        sys.stdout.write(USAGE)
        return 5
    if opts is None:
        return 0
    if QO.queue_path(opts["queue"]) is None:
        sys.stdout.write("E_QHO_BAD_ARGS: unknown queue %s\n" % opts["queue"])
        sys.stdout.write(USAGE)
        return 5
    try:
        report = read(opts["root"], opts["queue"])
    except QO.QueueOccupancyError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if opts["json"]:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] != VERDICT_OFFERED:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))