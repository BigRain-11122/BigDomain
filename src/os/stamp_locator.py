# stamp_locator.py - where a round's done stamp actually sits, as a reading
# Criteria AC-SLC1..AC-SLC6 were pre-registered in state/queue/tech.md as the
# R2269 seed row BEFORE this file existed. Anchor check at HEAD 2026-10-31:
# stamp_locator / AC-SLC / E_SLC / os-stamp-locator / test_stamp_locator were
# git grep -F zero-occupancy rc=1 (rc 1 = no hit); the only occurrences of
# the bare words were prose in src/os/backlog.md, src/os/state.json and two
# closeout/export helpers, with zero code occupancy - disclosed.
#
# Why this exists: the declared-floor reading names rounds that stamped a
# queue row and left no log item (the live gate reads NEVER-LOGGED R2250),
# and triaging one is still a hand search: the operator greps the stamp
# across state/queue/*.md and rewrites the finding in prose. This module
# answers the same question as data - file, line, row head and whether the
# row is closed.
#
# The stamp law is IMPORTED from state_seq and never re-implemented
# (AC-SLC1): the regex is read off state_seq at call time, so a patched
# regex flows straight through. The row-closed law is imported from
# queue_floor for the same reason, so "is this row closed" still has one
# owner.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import io
import json
import os
import sys

import queue_floor as QF
import state_seq as SQ

VERDICTS = ("HITS", "NO-HITS", "MISSING")

REPORT_KEYS = (
    "round",
    "hit_count",
    "hits",
    "queues_scanned",
    "missing_queues",
    "verdict",
)

HIT_KEYS = (
    "file",
    "line",
    "row_head",
    "closed",
    "stamp",
)

HEAD_CHARS = 120


class StampLocatorError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parse_round(text):
    """Read one round label ('R2250' or '2250') as an int, or refuse."""
    shown = (text or "").strip()
    if shown[:1] in ("R", "r"):
        shown = shown[1:]
    if not shown.isdigit():
        raise StampLocatorError("E_SLC_BAD_ROUND", "round=%r" % (text,))
    number = int(shown)
    if number < 1 or number > 99999:
        raise StampLocatorError("E_SLC_BAD_ROUND", "round=%r" % (text,))
    return number


def read_text(path):
    """Read one queue file as UTF-8, refusing on any read failure."""
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except (IOError, OSError, ValueError) as exc:
        raise StampLocatorError("E_SLC_BAD_QUEUE", "%s (%s)" % (path, exc))


def stamps_of(text):
    """Every stamp round on one line, read through the imported law."""
    out = []
    for match in SQ.DONE_STAMP_RE.finditer(text):
        out.append(int(match.group(1)))
    return out


def row_head(line):
    """The row's own leading text, one line, bounded."""
    shown = " ".join(line.split())
    if len(shown) <= HEAD_CHARS:
        return shown
    return shown[:HEAD_CHARS]


def locate_text(name, rel, text, number):
    """Every row in one queue file whose imported stamp law names `number`."""
    hits = []
    for index, line in enumerate(text.split("\n")):
        rounds = stamps_of(line)
        if number not in rounds:
            continue
        hits.append({
            "file": rel,
            "line": index + 1,
            "row_head": row_head(line),
            "closed": bool(QF.is_done_row(line)),
            "stamp": "[done ... R%d]" % number,
        })
    return hits


def locate(root, number):
    """Locate a round's done stamp across the three queues under root."""
    directory = os.path.join(root, "state", "queue")
    if not os.path.isdir(directory):
        raise StampLocatorError("E_SLC_BAD_QUEUE", directory)
    hits = []
    scanned = 0
    missing = []
    for name, rel in QF.QUEUE_PATHS:
        full = os.path.join(root, rel)
        shown = rel.replace(os.sep, "/")
        if not os.path.isfile(full):
            missing.append(name)
            continue
        scanned += 1
        hits.extend(locate_text(name, shown, read_text(full), number))
    hits.sort(key=lambda row: (row["file"], row["line"]))
    if hits:
        verdict = "HITS"
    elif scanned == 0:
        verdict = "MISSING"
    else:
        verdict = "NO-HITS"
    return {
        "round": number,
        "hit_count": len(hits),
        "hits": hits,
        "queues_scanned": scanned,
        "missing_queues": sorted(missing),
        "verdict": verdict,
    }


def one_line(report):
    """One-line rendering of a reading."""
    return ("STAMP LOCATOR round=R%d hits=%d scanned=%d missing=%d "
            "verdict=%s"
            % (report["round"], report["hit_count"], report["queues_scanned"],
               len(report["missing_queues"]), report["verdict"]))


def render(report):
    """Full text rendering: the one line, then every hit named."""
    out = [one_line(report)]
    for hit in report["hits"]:
        out.append("  HIT %s:%d closed=%s %s"
                   % (hit["file"], hit["line"],
                      "yes" if hit["closed"] else "no", hit["row_head"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    pinned = []
    for hit in report["hits"]:
        row = {}
        for key in HIT_KEYS:
            row[key] = hit[key]
        pinned.append(row)
    ordered["hits"] = pinned
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: stamp_locator.py --round R<n> [--root PATH] [--json]\n"
         "  exit 0 = the round carries at least one done stamp (HITS)\n"
         "  exit 2 = no queue row carries that stamp (NO-HITS) or bad "
         "flags\n"
         "  exit 3 = the queue directory or a queue file is missing or "
         "unreadable\n")


def main(argv):
    number = None
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--json":
            as_json = True
        elif arg == "--round":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_SLC_BAD_ARGS: --round needs a label\n")
                return 5
            try:
                number = parse_round(argv[index])
            except StampLocatorError as exc:
                sys.stdout.write("%s\n" % exc.code)
                return 5
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_SLC_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_SLC_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if number is None:
        sys.stdout.write("E_SLC_BAD_ARGS: --round is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = locate(root, number)
    except StampLocatorError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] != "HITS":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))