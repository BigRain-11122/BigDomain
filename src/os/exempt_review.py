# exempt_review.py - an accepted exemption gets AGED instead of forgotten
# Criteria AC-EXR1..AC-EXR6 were pre-registered in state/queue/tech.md as the
# R2276 seed row BEFORE this file existed. Anchor check at HEAD 2026-10-31:
# exempt_review / AC-EXR / E_EXR / os-exempt-review / test_exempt_review were
# all git grep -F zero-occupancy rc=1.
#
# Why this exists: queue_row_exempt records an acceptance once, with the round
# that granted it and a reason. Nothing ever looks at it again, so a waiver
# granted while the world looked one way quietly becomes permanent. This
# module ages every declared entry against the round being checked and names
# each one that has gone unreviewed for too long - both rounds included, so a
# reviewer can see exactly how old the waiver is.
#
# The declaration is NOT re-parsed here: entries come from
# queue_row_exempt.read_declaration, so the shape law (required keys, accepted
# queues, round syntax, an until that never predates its declared round) stays
# in the one place that owns it. A patched reader flows straight through.
#
# Age law (AC-EXR2): age = current round - declared round. An entry whose age
# is at or beyond the window is STALE and is reported with BOTH rounds. An
# entry whose `until` round has been reached is STALE as well even when its
# age is still short, because the acceptance declared its own end. A `declared`
# round LATER than the round being checked is refused (E_EXR_FUTURE) rather
# than aged to a negative number - a future acceptance cannot be aged.
#
# The window is a caller argument, never a built-in default baked into the
# verdict: no window means no staleness claim. The CLI carries 100 rounds as
# its own declared default and prints it, so a reading always says which
# window produced it.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import json
import os
import sys

import queue_row_exempt as QRE

WINDOW_DEFAULT = 100

ROW_KEYS = ("queue", "identity", "declared", "until", "age", "status")

REPORT_KEYS = (
    "round",
    "window",
    "declaration",
    "path",
    "entries",
    "stale_count",
    "stale",
    "verdict",
)

VERDICTS = ("REVIEW-CLEAN", "REVIEW-STALE")


class ExemptReviewError(Exception):
    """Raised when an honest reading cannot be produced."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def round_number(text):
    """R<n> -> n, or None when the token is not a round (imported law)."""
    return QRE.round_number(text)


def check_window(window):
    """The staleness window must be a positive int that is not a bool."""
    if isinstance(window, bool) or not isinstance(window, int):
        raise ExemptReviewError("E_EXR_BAD_WINDOW",
                                "window must be an int, got %r" % (window,))
    if window < 1:
        raise ExemptReviewError("E_EXR_BAD_WINDOW",
                                "window must be at least 1, got %d" % window)
    return window


def one_entry(raw, current, window):
    """Age one declared entry; refused entries raise, never read as clean."""
    if not isinstance(raw, dict):
        raise ExemptReviewError("E_EXR_BAD_DECL",
                                "declaration entry is not an object")
    declared_n = round_number(raw.get("declared"))
    if declared_n is None:
        raise ExemptReviewError("E_EXR_BAD_DECL",
                                "entry declares no round: %r"
                                % (raw.get("declared"),))
    if declared_n > current:
        raise ExemptReviewError(
            "E_EXR_FUTURE",
            "%s/%s declares %s which is LATER than the round being checked %s"
            % (raw.get("queue"), raw.get("identity"), raw.get("declared"),
               "R%d" % current))
    until = raw.get("until")
    until_n = round_number(until) if until is not None else None
    age = current - declared_n
    expired = until_n is not None and current >= until_n
    stale = age >= window or expired
    status = "STALE" if stale else "FRESH"
    return {
        "queue": raw.get("queue"),
        "identity": raw.get("identity"),
        "declared": "R%d" % declared_n,
        "until": until,
        "age": age,
        "status": status,
    }


def audit(root, round_text, window=WINDOW_DEFAULT):
    """Age every declared exemption against one round. Writes nothing."""
    current = round_number(round_text)
    if current is None:
        raise ExemptReviewError("E_EXR_BAD_ROUND",
                                "round must be R<n>, got %r" % (round_text,))
    window = check_window(window)
    try:
        declaration = QRE.read_declaration(root)
    except QRE.QueueRowExemptError as exc:
        raise ExemptReviewError("E_EXR_BAD_DECL", str(exc))
    except Exception as exc:  # noqa: BLE001 - a broken reader is not clean
        raise ExemptReviewError("E_EXR_UNREADABLE",
                                "%s (%s)" % (type(exc).__name__, exc))
    if not isinstance(declaration, dict):
        raise ExemptReviewError("E_EXR_BAD_DECL",
                                "declaration reader returned %r"
                                % (type(declaration).__name__,))
    raw_entries = declaration.get("entries")
    if not isinstance(raw_entries, list):
        raise ExemptReviewError("E_EXR_BAD_DECL",
                                "declaration carries no entries list")
    rows = []
    for raw in raw_entries:
        rows.append(one_entry(raw, current, window))
    stale = [row for row in rows if row["status"] == "STALE"]
    return {
        "round": "R%d" % current,
        "window": window,
        "declaration": declaration.get("status"),
        "path": declaration.get("path"),
        "entries": rows,
        "stale_count": len(stale),
        "stale": stale,
        "verdict": VERDICTS[1] if stale else VERDICTS[0],
    }


def one_line(report):
    """The single line a window prints for itself."""
    return ("EXEMPT REVIEW round=%s window=%d declaration=%s entries=%d "
            "stale=%d verdict=%s"
            % (report["round"], report["window"], report["declaration"],
               len(report["entries"]), report["stale_count"],
               report["verdict"]))


def detail_line(row):
    """One stale entry, naming BOTH rounds and its reason."""
    return ("  STALE %s/%s declared=%s age=%d until=%s"
            % (row["queue"], row["identity"], row["declared"], row["age"],
               row["until"]))


def render_json(report):
    """Byte-stable JSON over the pinned keys, in the pinned order."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, indent=2, sort_keys=False)


def main(argv):
    args = list(argv[1:])
    round_text = None
    window = WINDOW_DEFAULT
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    use_json = False
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--round":
            if index + 1 >= len(args):
                raise ExemptReviewError("E_EXR_BAD_FLAGS", "--round needs a value")
            round_text = args[index + 1]
            index += 2
        elif arg == "--window":
            if index + 1 >= len(args):
                raise ExemptReviewError("E_EXR_BAD_FLAGS", "--window needs a value")
            try:
                window = int(args[index + 1])
            except ValueError:
                raise ExemptReviewError("E_EXR_BAD_WINDOW",
                                        "window is not an int: %r"
                                        % (args[index + 1],))
            index += 2
        elif arg == "--root":
            if index + 1 >= len(args):
                raise ExemptReviewError("E_EXR_BAD_FLAGS", "--root needs a value")
            root = args[index + 1]
            index += 2
        elif arg == "--json":
            use_json = True
            index += 1
        else:
            raise ExemptReviewError("E_EXR_BAD_FLAGS",
                                    "unknown argument %r" % (arg,))
    if round_text is None:
        raise ExemptReviewError("E_EXR_BAD_FLAGS",
                                "--round is mandatory (a default round would "
                                "decide on its own)")
    report = audit(root, round_text, window)
    if use_json:
        print(render_json(report))
    else:
        print(one_line(report))
        for row in report["stale"]:
            print(detail_line(row))
    return 2 if report["stale_count"] else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except ExemptReviewError as exc:
        if exc.code in ("E_EXR_BAD_FLAGS", "E_EXR_BAD_ROUND",
                        "E_EXR_BAD_WINDOW"):
            print("BAD FLAGS %s" % exc.code)
            sys.exit(5)
        print("REFUSE %s: %s" % (exc.code, exc.detail))
        sys.exit(3)