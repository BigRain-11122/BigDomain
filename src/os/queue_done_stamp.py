# queue_done_stamp.py - the window stamp on a closed queue row, as a reading
# Criteria AC-QDS1..AC-QDS6 were pre-registered in state/queue/tech.md as the
# R2255 seed row BEFORE this file existed. Anchor check at HEAD 2026-10-31:
# E_QDS / test_queue_done_stamp were git grep -F zero-occupancy rc=1, while
# queue_done_stamp / AC-QDS / os-queue-done-stamp / queue-done-stamp hit
# ONLY prose (the seed row itself, src/os/backlog.md, src/os/state.json and
# docs/status-export.json) - disclosed, with zero code occupancy.
#
# Why this exists: queue_row gates every CLAIMABLE OPEN row on naming its
# criteria prefix, and says nothing at all about a row that is already
# closed. A done row can therefore land with no window stamp, with a stamp
# that names no window, or with a round earlier than the round the row was
# opened in - and the trace from a delivered item back to the window that
# closed it is prose again. This module makes that trace a check.
#
# The row law is imported from queue_floor (is_done_row, QUEUE_PATHS) rather
# than re-implemented, so a row is still decided in exactly one place.
#
# Stamp forms, and only these (AC-QDS1). The marker word may be any of the
# ones this house actually writes on a closed row - done, claimed+done,
# claimed, negative, closed - because each of them names the window:
#   FORM-1  [<marker> YYYY-MM-DD R<n>]   date plus window  -> RESOLVED
#   FORM-2  [<marker> R<n>]              window only       -> RESOLVED
#   FORM-3  [<marker> YYYY-MM-DD]        date only         -> DATE-ONLY (debt)
# A date alone cannot name a window: several rounds share a day, so a
# date-only stamp is reported as debt with its own status instead of being
# quietly accepted as a trace. An empty bracket, a marker with neither token,
# or any other text inside the brackets is BAD-STAMP.
#
# Seed round law (AC-QDS3): the row own seed round is the first R<n> token in
# the row text AFTER the [done ...] stamp is removed - in this house a row
# opens by naming the round that opened it. A stamp whose round is EARLIER
# than that seed round is a violation with both rounds named, because the
# item cannot have been closed before it was opened. A row that names no
# round at all has no seed round to compare against: it is reported as such
# and never accused of a violation it cannot have committed.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import io
import json
import os
import re
import sys

import queue_floor as QF

# The marker words this house actually uses on a closed row. Every one of
# them names the window the row was closed in, so every one is a stamp; a
# row that carries none of them carries no stamp at all.
MARKERS = ("done", "claimed+done", "claimed", "negative", "closed")
STAMP_RE = re.compile(r"\[((?:claimed\+done|done|claimed|negative|closed))"
                      r"(?: ([^\]\n]{0,60}))?\]")
DATE_RE = re.compile(r"(?<![0-9])(\d{4}-\d{2}-\d{2})(?![0-9])")
ROUND_RE = re.compile(r"(?<![A-Za-z0-9_])R(\d{1,5})(?![0-9])")

VERDICTS = ("DONE-STAMP-CLEAN", "DONE-STAMP-DEBT")

STATUS_OK = "OK"
STATUS_UNSTAMPED = "UNSTAMPED"
STATUS_BAD_STAMP = "BAD-STAMP"
STATUS_DATE_ONLY = "DATE-ONLY"
STATUS_BEFORE_SEED = "STAMP-BEFORE-SEED"

QUEUE_KEYS = (
    "queue",
    "path",
    "present",
    "done_rows",
    "stamped_rows",
    "ok_rows",
    "unstamped_rows",
    "bad_stamp_rows",
    "date_only_rows",
    "before_seed_rows",
    "violation_count",
    "violations",
    "status",
)

VIOLATION_KEYS = (
    "file",
    "line",
    "status",
    "stamp",
    "round",
    "seed_round",
    "excerpt",
)

REPORT_KEYS = (
    "queues",
    "done_rows",
    "stamped_rows",
    "ok_rows",
    "unstamped_rows",
    "bad_stamp_rows",
    "date_only_rows",
    "before_seed_rows",
    "violation_count",
    "violations",
    "verdict",
    "missing",
)

EXCERPT_MAX = 100

DEBT_STATUSES = (
    STATUS_UNSTAMPED,
    STATUS_BAD_STAMP,
    STATUS_DATE_ONLY,
    STATUS_BEFORE_SEED,
)


class QueueDoneStampError(Exception):
    """Raised when an honest reading cannot be produced."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def excerpt(text):
    """A deterministic ASCII excerpt of a row, for the refusal report."""
    body = text.strip()
    if len(body) > EXCERPT_MAX:
        body = body[:EXCERPT_MAX] + "..."
    return body.encode("ascii", "replace").decode("ascii")


def read_text(path):
    """Read a queue file as utf-8; fail closed on unreadable input."""
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise QueueDoneStampError("E_QDS_BAD_QUEUE", "%s (%s)" % (path, exc))


def parse_stamp(text):
    """Resolve the window stamp of one done row.

    Returns a dict with form ("DATE+ROUND" / "ROUND" / "DATE" / "BAD" /
    None), date, round (int or None) and stamp (the raw bracket text, or
    None). form is None only when the row carries no stamp at all.
    """
    hit = STAMP_RE.search(text)
    if not hit:
        return {"form": None, "date": None, "round": None, "stamp": None,
                "marker": None}
    marker = hit.group(1)
    body = (hit.group(2) or "").strip()
    date_hit = DATE_RE.search(body)
    round_hit = ROUND_RE.search(body)
    date = date_hit.group(1) if date_hit else None
    round_no = int(round_hit.group(1)) if round_hit else None
    if date is not None and round_no is not None:
        form = "DATE+ROUND"
    elif round_no is not None:
        form = "ROUND"
    elif date is not None:
        form = "DATE"
    else:
        form = "BAD"
    return {"form": form, "date": date, "round": round_no,
            "stamp": body, "marker": marker}


def seed_round_of(text):
    """The round the row was opened in: first R<n> after the stamp."""
    hit = STAMP_RE.search(text)
    body = text[:hit.start()] + text[hit.end():] if hit else text
    found = ROUND_RE.search(body)
    return int(found.group(1)) if found else None


def classify(text):
    """Classify one done row into exactly one status."""
    stamp = parse_stamp(text)
    form = stamp["form"]
    seed = seed_round_of(text)
    if form is None:
        status = STATUS_UNSTAMPED
    elif form == "BAD":
        status = STATUS_BAD_STAMP
    elif form == "DATE":
        status = STATUS_DATE_ONLY
    elif seed is not None and stamp["round"] < seed:
        status = STATUS_BEFORE_SEED
    else:
        status = STATUS_OK
    return {
        "status": status,
        "form": form,
        "stamp": stamp["stamp"],
        "round": stamp["round"],
        "seed_round": seed,
    }


def audit_text(name, rel, text):
    """Audit the done rows of one queue file."""
    done_rows = 0
    stamped = 0
    counts = {
        STATUS_OK: 0,
        STATUS_UNSTAMPED: 0,
        STATUS_BAD_STAMP: 0,
        STATUS_DATE_ONLY: 0,
        STATUS_BEFORE_SEED: 0,
    }
    violations = []
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if not QF.is_done_row(line):
            continue
        done_rows += 1
        row = classify(line)
        if row["form"] is not None:
            stamped += 1
        counts[row["status"]] += 1
        if row["status"] in DEBT_STATUSES:
            violations.append({
                "file": rel,
                "line": index + 1,
                "status": row["status"],
                "stamp": row["stamp"],
                "round": row["round"],
                "seed_round": row["seed_round"],
                "excerpt": excerpt(line),
            })
    if violations:
        status = "DEBT"
    elif done_rows == 0:
        status = "EMPTY"
    else:
        status = "PASS"
    return {
        "queue": name,
        "path": rel,
        "present": True,
        "done_rows": done_rows,
        "stamped_rows": stamped,
        "ok_rows": counts[STATUS_OK],
        "unstamped_rows": counts[STATUS_UNSTAMPED],
        "bad_stamp_rows": counts[STATUS_BAD_STAMP],
        "date_only_rows": counts[STATUS_DATE_ONLY],
        "before_seed_rows": counts[STATUS_BEFORE_SEED],
        "violation_count": len(violations),
        "violations": violations,
        "status": status,
    }


def empty_queue(name, rel):
    """A missing queue reads MISSING with an honest zero, never a pass."""
    return {
        "queue": name,
        "path": rel,
        "present": False,
        "done_rows": 0,
        "stamped_rows": 0,
        "ok_rows": 0,
        "unstamped_rows": 0,
        "bad_stamp_rows": 0,
        "date_only_rows": 0,
        "before_seed_rows": 0,
        "violation_count": 0,
        "violations": [],
        "status": "MISSING",
    }


def audit_root(root):
    """Audit every queue under root; return the closed report shape."""
    queues = []
    missing = []
    for name, rel in QF.QUEUE_PATHS:
        full = os.path.join(root, rel)
        shown = rel.replace(os.sep, "/")
        if not os.path.isfile(full):
            queues.append(empty_queue(name, shown))
            missing.append(name)
            continue
        queues.append(audit_text(name, shown, read_text(full)))
    totals = {
        "done_rows": 0,
        "stamped_rows": 0,
        "ok_rows": 0,
        "unstamped_rows": 0,
        "bad_stamp_rows": 0,
        "date_only_rows": 0,
        "before_seed_rows": 0,
        "violation_count": 0,
    }
    violations = []
    for row in queues:
        for key in totals:
            totals[key] += row[key]
        violations.extend(row["violations"])
    verdict = ("DONE-STAMP-CLEAN" if totals["violation_count"] == 0
               else "DONE-STAMP-DEBT")
    report = {"queues": queues}
    for key in ("done_rows", "stamped_rows", "ok_rows", "unstamped_rows",
                "bad_stamp_rows", "date_only_rows", "before_seed_rows",
                "violation_count"):
        report[key] = totals[key]
    report["violations"] = violations
    report["verdict"] = verdict
    report["missing"] = missing
    return report


def one_line(report):
    """The single line an operator reads."""
    return ("QUEUE DONE STAMP done=%d stamped=%d ok=%d unstamped=%d "
            "bad_stamp=%d date_only=%d before_seed=%d violations=%d "
            "verdict=%s"
            % (report["done_rows"], report["stamped_rows"], report["ok_rows"],
               report["unstamped_rows"], report["bad_stamp_rows"],
               report["date_only_rows"], report["before_seed_rows"],
               report["violation_count"], report["verdict"]))


def render(report):
    """Full text rendering: the one line, per queue, then each violation."""
    out = [one_line(report)]
    for row in report["queues"]:
        out.append("  %-8s done=%d stamped=%d ok=%d unstamped=%d "
                   "bad_stamp=%d date_only=%d before_seed=%d "
                   "violations=%d status=%s"
                   % (row["queue"], row["done_rows"], row["stamped_rows"],
                      row["ok_rows"], row["unstamped_rows"],
                      row["bad_stamp_rows"], row["date_only_rows"],
                      row["before_seed_rows"], row["violation_count"],
                      row["status"]))
    for item in report["violations"]:
        extra = ""
        if item["round"] is not None:
            extra = " round=R%d" % item["round"]
        if item["seed_round"] is not None:
            extra += " seed=R%d" % item["seed_round"]
        out.append("  %-17s %s:%d%s %s"
                   % (item["status"], item["file"], item["line"], extra,
                      item["excerpt"]))
    if report["missing"]:
        out.append("  missing=%s" % ",".join(report["missing"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    ordered["queues"] = []
    for row in report["queues"]:
        item = {}
        for key in QUEUE_KEYS:
            item[key] = row[key]
        item["violations"] = []
        for bad in row["violations"]:
            pinned = {}
            for key in VIOLATION_KEYS:
                pinned[key] = bad[key]
            item["violations"].append(pinned)
        ordered["queues"].append(item)
    pinned_violations = []
    for bad in report["violations"]:
        pinned = {}
        for key in VIOLATION_KEYS:
            pinned[key] = bad[key]
        pinned_violations.append(pinned)
    ordered["violations"] = pinned_violations
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: queue_done_stamp.py --check [--root PATH] [--json]\n"
         "  every done row must carry a resolvable window stamp: [done\n"
         "  YYYY-MM-DD R<n>] or [done R<n>]. A date alone names no window\n"
         "  and reads as debt; a stamp older than the row own seed round is\n"
         "  a violation with both rounds named.\n"
         "  exit 0 = no done row is debt (DONE-STAMP-CLEAN)\n"
         "  exit 2 = at least one done row is debt (DONE-STAMP-DEBT)\n"
         "  exit 3 = a required queue file is missing or unreadable\n"
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
                sys.stdout.write("E_QDS_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_QDS_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_QDS_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = audit_root(root)
    except QueueDoneStampError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["missing"]:
        return 3
    if report["verdict"] == "DONE-STAMP-DEBT":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))