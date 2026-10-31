"""evidence_parity - is a legacy per-round script doing exactly the ritual?

R2261 turned the per-round evidence ritual into one callable
(src/os/evidence_capture.py) and measured the pile it replaces: ninety-odd
`evidence_R*.py` scripts, 326455 bytes, against a 9509 byte callable. The pile
cannot be retired on a hunch. Each legacy copy has to be shown to do exactly
the five ritual legs the callable does - two legs of the same suite, a digest
over its criterion lines, a single-writer utf-8 LF body, an ordered adjacent
batch carrying its own SUITE lines, and a live gate line - and nothing else it
silently relied on.

This reader answers that one question per script, by static analysis only, in
the pinned leg order:

    two-legs / criteria-digest / single-writer / adjacent-batch / live-gate

Each leg reads PRESENT, MISSING or DIFFERENT. PRESENT needs a positive marker
AND the shape that marker is supposed to carry; markers with the wrong shape
read DIFFERENT rather than being rounded up to PRESENT. The reader never runs
the script it is judging, never writes anything, and reads no clock, so the
same bytes always produce the same reading.

Criteria AC-EVP1..AC-EVP6 were pinned in state/queue/tech.md as the R2261 seed
row BEFORE this code existed. Stdlib only, ASCII source, zero network.
"""

import hashlib
import json
import os
import re
import sys

LEGS = ("two-legs", "criteria-digest", "single-writer",
        "adjacent-batch", "live-gate")
VERDICTS = ("PRESENT", "MISSING", "DIFFERENT")

RUN_CALL = r"(_run\(|run_suite\(|subprocess\.run\()"

LEG_RULES = (
    {
        "name": "two-legs",
        "markers": (
            r"LEGS\s*=\s*2",
            r"for\s+[A-Za-z_]\w*\s+in\s*\(\s*['\"]a['\"]\s*,\s*['\"]b['\"]\s*\)",
            r"for\s+[A-Za-z_]\w*\s+in\s+range\(\s*2\s*\)",
        ),
        "required": (
            r"['\"]a['\"]\s*,\s*['\"]b['\"]|range\(\s*2\s*\)",
        ),
        "min_runs": 2,
    },
    {
        "name": "criteria-digest",
        "markers": (r"hashlib", r"hexdigest", r"sha256"),
        "required": (r"hashlib", r"hexdigest",
                     r"startswith\(\s*['\"]PASS|CRITERIA|MARKERS"),
        "min_runs": 0,
    },
    {
        "name": "single-writer",
        "markers": (r"open\(", r"['\"][xw]b['\"]", r"utf-8"),
        "required": (r"['\"][xw]b['\"]|\.encode\(\s*['\"]utf-8['\"]",
                     r"utf-8",
                     r"\\r\\n|newline\s*=\s*['\"]"),
        "min_runs": 0,
    },
    {
        "name": "adjacent-batch",
        "markers": (r"ADJACENT", r"adjacent", r"[Bb]atch"),
        "required": (r"startswith\(\s*['\"]SUITE|['\"]SUITE|== %s rc=",
                     r"ADJACENT|adjacent"),
        "min_runs": 0,
    },
    {
        "name": "live-gate",
        "markers": (r"LIVE", r"_live\(", r"live_"),
        "required": (r"print\(\s*['\"]LIVE|['\"]LIVE\s",
                     r"--check|_live\("),
        "min_runs": 0,
    },
)

REPORT_KEYS = ("script", "bytes", "sha16", "legs", "counts", "verdict")
LEG_KEYS = ("name", "verdict", "hits", "missing")

USAGE = ("usage: evidence_parity.py --script PATH [--json]\n"
         "       evidence_parity.py --dir PATH [--pattern GLOB] [--json]\n"
         "exit 0 = every leg PRESENT, 2 = any MISSING or DIFFERENT,\n"
         "3 = unreadable or absent input, 5 = bad flags\n")


class ParityError(Exception):
    """A refused reading: the code names why, detail names the input."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def _resolve(root, name):
    if os.path.isabs(name):
        return name
    return os.path.join(root, name)


def read_script(path):
    """Read a script as bytes, then decode. Absent and unreadable differ."""
    if not os.path.isfile(path):
        raise ParityError("E_EVP_NO_SCRIPT", path)
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError):
        raise ParityError("E_EVP_UNREADABLE", path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ParityError("E_EVP_UNREADABLE", path)
    return raw, text


def _leg_verdict(text, rule):
    """PRESENT / MISSING / DIFFERENT for one leg against one text."""
    hits = [pattern for pattern in rule["markers"]
            if re.search(pattern, text)]
    if not hits:
        return {"name": rule["name"], "verdict": "MISSING", "hits": 0,
                "missing": ["positive-marker"]}
    absent = [pattern for pattern in rule["required"]
              if not re.search(pattern, text)]
    short_runs = 0
    if rule["min_runs"]:
        short_runs = len(re.findall(RUN_CALL, text))
        if short_runs < rule["min_runs"]:
            absent = list(absent) + ["run-call-count=%d<"
                                    "%d" % (short_runs, rule["min_runs"])]
    verdict = "PRESENT" if not absent else "DIFFERENT"
    return {"name": rule["name"], "verdict": verdict, "hits": len(hits),
            "missing": absent}


def analyse(text, script):
    """The pinned report for one decoded body. Pure: no I/O, no clock."""
    legs = [_leg_verdict(text, rule) for rule in LEG_RULES]
    counts = dict((name, 0) for name in VERDICTS)
    for leg in legs:
        counts[leg["verdict"]] += 1
    if counts["MISSING"] or counts["DIFFERENT"]:
        verdict = "PARITY-DEBT"
    else:
        verdict = "ALL-PRESENT"
    return {"script": script,
            "bytes": len(text.encode("utf-8")),
            "sha16": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
            "legs": legs,
            "counts": counts,
            "verdict": verdict}


def check(root, script):
    """One script, read once, judged in place. Writes nothing."""
    path = _resolve(root, script)
    raw, text = read_script(path)
    report = analyse(text, script)
    report["sha16"] = hashlib.sha256(raw).hexdigest()[:16]
    report["bytes"] = len(raw)
    return report


def scan(root, directory, pattern="evidence_R*.py"):
    """The live pile: one reading per script, plus a per-leg count.

    A script that cannot be read is reported with its own code and counted as
    unreadable; it never aborts the pile and never contributes fabricated legs.
    """
    path = _resolve(root, directory)
    if not os.path.isdir(path):
        raise ParityError("E_EVP_NO_SCRIPT", path)
    names = sorted(name for name in os.listdir(path)
                   if re.match(pattern.replace("*", ".*") + "$", name))
    rows = []
    unreadable = []
    for name in names:
        if os.path.isabs(directory):
            rel = os.path.join(path, name)
        else:
            rel = os.path.join(directory, name)
        try:
            rows.append(check(root, rel))
        except ParityError as exc:
            unreadable.append({"script": rel, "code": exc.code})
    counts = dict((leg, dict((verdict, 0) for verdict in VERDICTS))
                  for leg in LEGS)
    for row in rows:
        for leg in row["legs"]:
            counts[leg["name"]][leg["verdict"]] += 1
    clean = [row["script"] for row in rows
             if row["verdict"] == "ALL-PRESENT"]
    ok = bool(rows) and not unreadable and len(clean) == len(rows)
    return {"dir": directory, "pattern": pattern, "scripts": len(names),
            "unreadable": unreadable, "leg_counts": counts,
            "all_present": clean, "rows": rows,
            "verdict": "ALL-PRESENT" if ok else "PARITY-DEBT"}


def render(report):
    counts = report["counts"]
    return ("EVIDENCE PARITY script=%s bytes=%d sha16=%s legs=%d "
            "present=%d missing=%d different=%d verdict=%s"
            % (report["script"], report["bytes"], report["sha16"],
               len(report["legs"]), counts["PRESENT"], counts["MISSING"],
               counts["DIFFERENT"], report["verdict"]))


def render_scan(report):
    parts = ["EVIDENCE PARITY PILE dir=%s pattern=%s scripts=%d "
             "unreadable=%d all_present=%d verdict=%s"
             % (report["dir"], report["pattern"], report["scripts"],
                len(report["unreadable"]), len(report["all_present"]),
                report["verdict"])]
    for leg in LEGS:
        row = report["leg_counts"][leg]
        parts.append("LEG %s present=%d missing=%d different=%d"
                     % (leg, row["PRESENT"], row["MISSING"],
                        row["DIFFERENT"]))
    for row in report["unreadable"]:
        parts.append("UNREADABLE %s %s" % (row["script"], row["code"]))
    return "\n".join(parts)


def to_json(report):
    ordered = {}
    for key in REPORT_KEYS:
        value = report[key]
        if key == "legs":
            value = [dict((name, leg[name]) for name in LEG_KEYS)
                     for leg in value]
        ordered[key] = value
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def to_json_scan(report):
    ordered = {"dir": report["dir"], "pattern": report["pattern"],
               "scripts": report["scripts"],
               "unreadable": list(report["unreadable"]),
               "leg_counts": dict((leg, report["leg_counts"][leg])
                                  for leg in LEGS),
               "all_present": list(report["all_present"]),
               "verdict": report["verdict"]}
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


EXIT_BY_CODE = {"E_EVP_NO_SCRIPT": 3, "E_EVP_UNREADABLE": 3,
                "E_EVP_BAD_ARGS": 5}


def main(argv):
    script = None
    directory = None
    pattern = "evidence_R*.py"
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--json":
            as_json = True
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg in ("--script", "--dir", "--pattern", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_EVP_BAD_ARGS: %s needs a value\n" % arg)
                return 5
            value = argv[index]
            if arg == "--script":
                script = value
            elif arg == "--dir":
                directory = value
            elif arg == "--pattern":
                pattern = value
            else:
                root = value
        else:
            sys.stdout.write("E_EVP_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if (script is None) == (directory is None):
        sys.stdout.write("E_EVP_BAD_ARGS: exactly one of --script or --dir "
                         "is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        if directory is not None:
            report = scan(root, directory, pattern)
            sys.stdout.write(to_json_scan(report) if as_json
                             else render_scan(report) + "\n")
            return 0 if report["verdict"] == "ALL-PRESENT" else 2
        report = check(root, script)
        sys.stdout.write(to_json(report) if as_json
                         else render(report) + "\n")
        return 0 if report["verdict"] == "ALL-PRESENT" else 2
    except ParityError as exc:
        sys.stdout.write("%s %s\n" % (exc.code, exc.detail))
        sys.stdout.write("REFUSE TO READ\n")
        return EXIT_BY_CODE.get(exc.code, 3)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))