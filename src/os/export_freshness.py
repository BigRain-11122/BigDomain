# export_freshness.py - read-only time gate for the CEO-visible face
# Criteria AC-EXP1..AC-EXP6 were pre-registered in state/queue/tech.md
# (R2240 d seed) BEFORE this file existed.
#
# Why this exists: docs/status-export.json is the only surface the CEO
# reads, and the round book requires it to carry three lines - what is
# alive now, the most recent artifact, the next milestone within 48h.
# Shape and derivation are already policed by src/os/check_export_consistency.py
# (non-empty three lines, ISO8601 export_ts, self_drive caliber, tick row).
# What nothing measured was TIME: a face that is perfectly shaped but
# two days old passed every existing check, and a milestone announced
# three weeks out also passed. This module judges only that axis, so the
# two checkers are complements and not a second wheel.
#
# Verdicts are four and exhaustive:
#   FRESH              the face is inside the age gate and the milestone
#                      window is inside 48h
#   STALE-FACE         the face is older than the age gate
#   STALE-WINDOW       the announced milestone sits further out than 48h
#   UNVERIFIABLE-WINDOW no due stamp is published, so the window cannot be
#                      judged - reported as unknown rather than as green
#
# The clock is never read here: the caller passes `now`, so a reading is
# reproducible and testable. Pure read, no writes, no network import,
# stdlib only, source pure ASCII.

import datetime
import json
import os
import sys

AGE_GATE_HOURS = 24.0
MILESTONE_WINDOW_HOURS = 48.0

FACE_KEYS = ("current", "latest_artifact", "next_milestone")
DUE_KEY = "next_milestone_due"

VERDICTS = ("FRESH", "STALE-FACE", "STALE-WINDOW",
            "UNVERIFIABLE-WINDOW")

REPORT_KEYS = (
    "path",
    "present",
    "export_ts",
    "age_hours",
    "age_gate_hours",
    "three_lines",
    "milestone_due",
    "milestone_window_hours",
    "window_gate_hours",
    "verdict",
    "errors",
)


class ExportFreshnessError(Exception):
    """Raised when the face cannot be read or its stamps cannot be trusted."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parse_ts(text, field):
    """Parse an ISO8601 stamp that carries an explicit UTC offset.

    A naive stamp is refused rather than assumed to be local time: the
    export is written by different writers across the day and an assumed
    offset would silently shift the age by hours.
    """
    if not isinstance(text, str) or not text.strip():
        raise ExportFreshnessError("E_EXP_BAD_TS",
                                   "%s is empty" % field)
    raw = text.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        stamp = datetime.datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ExportFreshnessError("E_EXP_BAD_TS",
                                   "%s=%r (%s)" % (field, text, exc))
    if stamp.tzinfo is None:
        raise ExportFreshnessError("E_EXP_BAD_TS",
                                   "%s=%r has no UTC offset" % (field, text))
    return stamp


def read_face(path):
    """Read the export as JSON; fail closed on unreadable or non-object."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError) as exc:
        raise ExportFreshnessError("E_EXP_BAD_FILE", "%s (%s)" % (path, exc))
    try:
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ExportFreshnessError("E_EXP_BAD_FILE",
                                   "%s (%s)" % (path, exc))
    if not isinstance(data, dict):
        raise ExportFreshnessError("E_EXP_BAD_FILE",
                                   "%s is not an object" % path)
    return data


def three_line_contract(data):
    """AC-EXP1: ceo_face carries the three lines as non-empty strings."""
    face = data.get("ceo_face")
    if not isinstance(face, dict):
        raise ExportFreshnessError("E_EXP_BAD_FACE", "ceo_face is not an object")
    reading = {}
    blank = []
    for key in FACE_KEYS:
        value = face.get(key)
        ok = isinstance(value, str) and bool(value.strip())
        reading[key] = ok
        if not ok:
            blank.append(key)
    if blank:
        raise ExportFreshnessError("E_EXP_BAD_FACE",
                                   "blank or missing line(s): %s"
                                   % ",".join(blank))
    return reading


def assess_due(face, export_ts):
    """AC-EXP3: the announced milestone window, judged or declared unknown.

    Returns (due_text, due_stamp, window_hours). A missing due stamp is an
    honest unknown (due_stamp None) and never a fabricated in-window pass.
    A due stamp at or before export_ts, or further out than the window, is
    a real defect and raises.
    """
    raw = face.get(DUE_KEY)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None, None, None
    due = parse_ts(raw, DUE_KEY)
    hours = (due - export_ts).total_seconds() / 3600.0
    return raw.strip(), due, hours


def assess(path, now, age_gate_hours=AGE_GATE_HOURS,
           window_hours=MILESTONE_WINDOW_HOURS):
    """Measure one export file. `now` must be an aware datetime."""
    if now.tzinfo is None:
        raise ExportFreshnessError("E_EXP_BAD_TS", "now has no UTC offset")
    present = os.path.isfile(path)
    if not present:
        return {
            "path": path,
            "present": False,
            "export_ts": None,
            "age_hours": None,
            "age_gate_hours": age_gate_hours,
            "three_lines": {key: False for key in FACE_KEYS},
            "milestone_due": None,
            "milestone_window_hours": None,
            "window_gate_hours": window_hours,
            "verdict": "UNVERIFIABLE-WINDOW",
            "errors": ["E_EXP_NO_FILE"],
        }
    data = read_face(path)
    lines = three_line_contract(data)
    export_ts = parse_ts(data.get("export_ts"), "export_ts")
    face = data["ceo_face"]
    due_text, _due, window = assess_due(face, export_ts)
    age = (now - export_ts).total_seconds() / 3600.0
    errors = []
    if age > age_gate_hours:
        verdict = "STALE-FACE"
        errors.append("E_EXP_STALE_FACE")
    elif window is None:
        verdict = "UNVERIFIABLE-WINDOW"
        errors.append("E_EXP_NO_DUE")
    elif window <= 0:
        verdict = "STALE-WINDOW"
        errors.append("E_EXP_DUE_IN_PAST")
    elif window > window_hours:
        verdict = "STALE-WINDOW"
        errors.append("E_EXP_WINDOW_TOO_FAR")
    else:
        verdict = "FRESH"
    return {
        "path": path,
        "present": True,
        "export_ts": export_ts.isoformat(),
        "age_hours": round(age, 3),
        "age_gate_hours": age_gate_hours,
        "three_lines": lines,
        "milestone_due": due_text,
        "milestone_window_hours": None if window is None else round(window, 3),
        "window_gate_hours": window_hours,
        "verdict": verdict,
        "errors": errors,
    }


def one_line(report):
    """The single operator line: age, milestone window, verdict."""
    age = "n/a" if report["age_hours"] is None else "%.1fh" % report["age_hours"]
    window = ("unknown" if report["milestone_window_hours"] is None
              else "%.1fh" % report["milestone_window_hours"])
    return ("EXPORT FRESHNESS age=%s gate=%.0fh milestone=%s gate=%.0fh "
            "verdict=%s"
            % (age, report["age_gate_hours"], window,
               report["window_gate_hours"], report["verdict"]))


def to_json(report):
    """Stable key order, ASCII, one trailing LF."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: export_freshness.py --check [--export PATH] [--now ISO8601] "
         "[--max-age-hours H] [--window-hours H] [--json]\n"
         "  exit 0 = FRESH\n"
         "  exit 2 = STALE-FACE or STALE-WINDOW\n"
         "  exit 3 = file missing or unreadable or a stamp is untrustworthy\n"
         "  exit 4 = UNVERIFIABLE-WINDOW (no due stamp published)\n"
         "  exit 5 = bad flags\n")


def _default_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))


def main(argv):
    check = False
    as_json = False
    export = os.path.join(_default_root(), "docs", "status-export.json")
    now = None
    age_gate = AGE_GATE_HOURS
    window_gate = MILESTONE_WINDOW_HOURS
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg in ("--export", "--now", "--max-age-hours", "--window-hours"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_EXP_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            value = argv[index]
            if arg == "--export":
                export = value
            elif arg == "--now":
                try:
                    now = parse_ts(value, "--now")
                except ExportFreshnessError as exc:
                    sys.stdout.write("%s\n" % exc.code)
                    return 5
            else:
                try:
                    number = float(value)
                except ValueError:
                    sys.stdout.write("E_EXP_BAD_ARGS: %s needs a number\n" % arg)
                    sys.stdout.write(USAGE)
                    return 5
                if number <= 0:
                    sys.stdout.write("E_EXP_BAD_ARGS: %s must be > 0\n" % arg)
                    return 5
                if arg == "--max-age-hours":
                    age_gate = number
                else:
                    window_gate = number
        else:
            sys.stdout.write("E_EXP_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_EXP_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    try:
        report = assess(export, now, age_gate, window_gate)
    except ExportFreshnessError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(one_line(report) + "\n")
        for err in report["errors"]:
            sys.stdout.write("  %s\n" % err)
    if not report["present"]:
        return 3
    verdict = report["verdict"]
    if verdict == "FRESH":
        return 0
    if verdict == "UNVERIFIABLE-WINDOW":
        return 4
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))