"""Per-suite timeout headroom against the battery's own cap (R2395).

The battery runs every registered suite through `subprocess.run(...,
timeout=300)` and a single slow suite aborts the WHOLE run with no code
defect at all: R2393 leg 3 died on ledger/test_apimarket_report_claims.py
after exactly 300s while the same suite had measured 183.3s and 194.9s in
the two earlier legs of that window - a load artefact, not a bug. Nothing
in the tree read those durations, so the first sign of load was a dead
battery.

This module reads the durations the runner itself printed, derives each
suite's slowest measured leg, and reports the headroom it carries against
the cap, naming every suite inside a warning band.

Criteria AC-RTH1..AC-RTH6 were pre-registered in state/queue/tech.md line
462 (the R2393 seed row) BEFORE this file existed.

Pure ASCII, stdlib only, no clock, no network, read-only: the CLI opens
evidence and the runner source for reading and writes nothing.
"""

import ast
import io
import json
import os
import re
import sys

SUITE_LABEL = "os-runner-suite-timeout-headroom"

CAP_DEFAULT = 300.0
BAND_DEFAULT = 0.6

CLEAN = "HEADROOM-CLEAN"
BAND_HIT = "BAND-HIT"
NO_MEASURE = "NO-MEASURE"

COMFORTABLE = "COMFORTABLE"

REPORT_KEYS = ("cap", "band_fraction", "verdict", "code", "suites",
               "band", "no_measure", "measured", "total")

# The runner's own line: note() prints "%s %s" % (PASS|FAIL, body) and the
# body is "suite <label> exit=%d pass-lines=%d fail-lines=%d criteria=%d
# %.1fs". A plain "status + label + duration" reading would also match the
# summary line "PASS suites 520/520 green...", so the "suite " token and its
# field order are pinned instead of a loose word match.
SUITE_LINE_RE = re.compile(
    r"^(PASS|FAIL) suite (\S+) exit=(-?\d+) pass-lines=(\d+) "
    r"fail-lines=(\d+) criteria=(\d+) ([0-9]+(?:\.[0-9]+)?)s\s*$")


class HeadroomError(Exception):
    def __init__(self, code, detail):
        Exception.__init__(self, detail)
        self.code = code
        self.detail = detail


def parse_evidence_line(line):
    """One runner suite line -> (label, ok, seconds), else None.

    Asked as a module attribute by scan_text, so patching this reading moves
    the assessment (AC-RTH1).
    """
    match = SUITE_LINE_RE.match(line.rstrip("\r\n"))
    if match is None:
        return None
    return match.group(2), match.group(1) == "PASS", float(match.group(7))


def scan_text(text):
    """Aggregate per-suite durations from one evidence body.

    Only PASS/FAIL suite lines count. A suite that appears more than once in
    one body keeps every leg, because the caller wants the slowest one.
    """
    durations = {}
    lines = 0
    for line in text.splitlines():
        parsed = parse_evidence_line(line)
        if parsed is None:
            continue
        label, _ok, seconds = parsed
        durations.setdefault(label, []).append(seconds)
        lines += 1
    return durations, lines


def read_evidence(paths):
    durations = {}
    lines = 0
    for path in paths:
        try:
            with io.open(path, "r", encoding="utf-8", errors="replace") as handle:
                body = handle.read()
        except OSError as exc:
            raise HeadroomError("E_RTH_UNREADABLE",
                                "cannot read evidence %s: %s"
                                % (path, exc.strerror or exc))
        found, used = scan_text(body)
        lines += used
        for label, legs in found.items():
            durations.setdefault(label, []).extend(legs)
    return durations, lines


def registry_labels(runner_path):
    """Labels the runner registers, read from its SUITES table by AST.

    The runner is never imported: it is a 5000-line battery driver and
    importing it would run whatever its module level carries. Parsing keeps
    this reading read-only and clock-free.
    """
    try:
        with io.open(runner_path, "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        raise HeadroomError("E_RTH_NO_REGISTRY",
                            "cannot read runner %s: %s"
                            % (runner_path, exc.strerror or exc))
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise HeadroomError("E_RTH_NO_REGISTRY",
                            "runner does not parse: %s" % exc)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = [target.id for target in node.targets
                 if isinstance(target, ast.Name)]
        if "SUITES" not in names:
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            break
        labels = []
        for row in node.value.elts:
            if not isinstance(row, (ast.List, ast.Tuple)) or not row.elts:
                continue
            first = row.elts[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                labels.append(first.value)
        if labels:
            return labels
        break
    raise HeadroomError("E_RTH_NO_REGISTRY",
                        "no literal SUITES table in %s" % runner_path)


OVERRIDES_NAME = "SUITE_TIMEOUT_OVERRIDES"


def read_overrides(runner_path):
    """Declared per-suite caps, read from one AST pass over the runner (R2599).

    AC-EDWU1: the AC-RSC2 override table the runner already applies is
    finally consumed here, so a declared ceiling is visible to the report
    instead of the flat global cap being printed against a suite the battery
    actually allows longer.

    AC-EDWU3: the table is parsed by AST, not by a loose regex, and a
    declaration that is not a dict literal of label -> positive number
    REFUSES with its own code rather than silently reading as "no overrides"
    (which would report a fictional 0.0s headroom for a suite the runner
    gives 900s). An ABSENT table is not a defect: fixture worlds carry none,
    and every suite then reads the flat global cap byte for byte (AC-EDWU2).
    """
    try:
        with io.open(runner_path, "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        raise HeadroomError("E_RTH_NO_REGISTRY",
                            "cannot read runner %s: %s"
                            % (runner_path, exc.strerror or exc))
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise HeadroomError("E_RTH_NO_REGISTRY",
                            "runner does not parse: %s" % exc)
    overrides = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = [target.id for target in node.targets
                 if isinstance(target, ast.Name)]
        if OVERRIDES_NAME not in names:
            continue
        if not isinstance(node.value, ast.Dict):
            raise HeadroomError(
                "E_RTH_BAD_OVERRIDES",
                "%s is not a dict literal in %s"
                % (OVERRIDES_NAME, runner_path))
        for key_node, value_node in zip(node.value.keys, node.value.values):
            if not (isinstance(key_node, ast.Constant)
                    and isinstance(key_node.value, str)):
                raise HeadroomError(
                    "E_RTH_BAD_OVERRIDES",
                    "%s carries a non-literal label in %s"
                    % (OVERRIDES_NAME, runner_path))
            value = None
            if (isinstance(value_node, ast.Constant)
                    and isinstance(value_node.value, (int, float))
                    and not isinstance(value_node.value, bool)):
                value = float(value_node.value)
            if value is None or value <= 0:
                raise HeadroomError(
                    "E_RTH_BAD_OVERRIDES",
                    "%s[%s] is not a positive literal number in %s"
                    % (OVERRIDES_NAME, key_node.value, runner_path))
            overrides[key_node.value] = value
        break
    return overrides


def assess(cap, band_fraction, labels, durations, overrides=None):
    """One report: per-suite slowest leg, cap, headroom, band, verdict, code.

    R2599: a suite with a declared override is judged against ITS OWN cap
    (AC-EDWU1) and every row names the cap it was judged against
    (AC-EDWU4), so a declared ceiling can never be read as the global one.
    With no overrides the R2395 answers stand byte for byte.
    """
    if cap <= 0:
        raise HeadroomError("E_RTH_BAD_CAP", "cap must be positive")
    if not 0 < band_fraction <= 1:
        raise HeadroomError("E_RTH_BAD_BAND",
                            "band fraction must sit inside (0, 1]")
    declared = dict(overrides or {})
    order = list(labels)
    for label in sorted(durations):
        if label not in order:
            order.append(label)
    suites = []
    band = []
    missing = []
    for label in order:
        row_cap = float(declared.get(label, cap))
        threshold = row_cap * band_fraction
        legs = durations.get(label) or []
        if not legs:
            suites.append({"suite": label, "cap": "%.1f" % row_cap,
                           "legs": 0, "slowest": "-",
                           "headroom": "-", "status": NO_MEASURE})
            missing.append(label)
            continue
        slowest = max(legs)
        headroom = row_cap - slowest
        status = BAND_HIT if slowest >= threshold else COMFORTABLE
        suites.append({"suite": label, "cap": "%.1f" % row_cap,
                       "legs": len(legs),
                       "slowest": "%.1f" % slowest,
                       "headroom": "%.1f" % headroom,
                       "status": status})
        if status == BAND_HIT:
            band.append(label)
    if band:
        verdict, code = BAND_HIT, 2
    elif missing:
        verdict, code = NO_MEASURE, 2
    else:
        verdict, code = CLEAN, 0
    return {"cap": "%.1f" % cap,
            "band_fraction": band_fraction,
            "verdict": verdict,
            "code": code,
            "suites": suites,
            "band": band,
            "no_measure": missing,
            "measured": len(suites) - len(missing),
            "total": len(suites)}


def render(report):
    cap = float(report["cap"])
    threshold = cap * report["band_fraction"]
    lines = ["CAP %ss BAND %d%% (>=%.1fs)"
             % (report["cap"], int(round(report["band_fraction"] * 100)),
                threshold)]
    for row in report["suites"]:
        if row["status"] == NO_MEASURE:
            lines.append("SUITE %s cap=%ss NO-MEASURE (no measured leg)"
                         % (row["suite"], row["cap"]))
        else:
            lines.append("SUITE %s cap=%ss legs=%d slowest=%ss "
                         "headroom=%ss %s"
                         % (row["suite"], row["cap"], row["legs"],
                            row["slowest"], row["headroom"], row["status"]))
    for label in report["band"]:
        row = [item for item in report["suites"] if item["suite"] == label][0]
        lines.append("BAND %s slowest=%ss headroom=%ss"
                     % (label, row["slowest"], row["headroom"]))
    for label in report["no_measure"]:
        row = [item for item in report["suites"] if item["suite"] == label][0]
        lines.append("NO-MEASURE %s cap=%ss" % (label, row["cap"]))
    lines.append("VERDICT %s suites=%d measured=%d band=%d no_measure=%d"
                 % (report["verdict"], report["total"], report["measured"],
                    len(report["band"]), len(report["no_measure"])))
    return "\n".join(lines)


USAGE = ("usage: runner_suite_timeout_headroom.py --check [--cap S] "
         "[--band F] [--root PATH] [--runner PATH] [--json] [EVIDENCE ...]\n"
         "exit 0 = HEADROOM-CLEAN, 2 = BAND-HIT or NO-MEASURE, "
         "3 = unreadable input, 5 = bad flags")


def parse_args(argv):
    options = {"check": False, "cap": CAP_DEFAULT, "band": BAND_DEFAULT,
               "root": None, "runner": None, "json": False,
               "cap_given": False}
    paths = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--check":
            options["check"] = True
        elif token == "--json":
            options["json"] = True
        elif token in ("--cap", "--band", "--root", "--runner"):
            index += 1
            if index >= len(argv):
                raise HeadroomError("E_RTH_BAD_ARGS",
                                    "%s needs a value" % token)
            value = argv[index]
            if token == "--cap":
                try:
                    options["cap"] = float(value)
                except ValueError:
                    raise HeadroomError("E_RTH_BAD_ARGS",
                                        "cap is not a number: %s" % value)
                options["cap_given"] = True
            elif token == "--band":
                try:
                    options["band"] = float(value)
                except ValueError:
                    raise HeadroomError("E_RTH_BAD_ARGS",
                                        "band is not a number: %s" % value)
            elif token == "--root":
                options["root"] = value
            else:
                options["runner"] = value
        elif token.startswith("-"):
            raise HeadroomError("E_RTH_BAD_ARGS", "unknown flag: %s" % token)
        else:
            paths.append(token)
        index += 1
    if options["cap"] <= 0:
        raise HeadroomError("E_RTH_BAD_ARGS", "cap must be positive")
    if not 0 < options["band"] <= 1:
        raise HeadroomError("E_RTH_BAD_ARGS",
                            "band fraction must sit inside (0, 1]")
    return options, paths


def default_inputs(root):
    qa = os.path.join(root, "qa")
    paths = []
    if os.path.isdir(qa):
        for name in sorted(os.listdir(qa)):
            if name.startswith("reconcile-all-") and name.endswith(".log"):
                paths.append(os.path.join(qa, name))
    return paths


def check(root, evidence, runner, cap, band, overrides=None):
    labels = registry_labels(runner)
    if overrides is None:
        overrides = read_overrides(runner)
    durations, lines = read_evidence(evidence)
    report = assess(cap, band, labels, durations, overrides)
    report["evidence_lines"] = lines
    return report


def main(argv):
    try:
        options, paths = parse_args(argv)
    except HeadroomError as exc:
        print("%s\n%s" % (exc.code, USAGE), flush=True)
        return 5
    if not options["check"]:
        print("E_RTH_BAD_ARGS: --check is required\n%s" % USAGE, flush=True)
        return 5
    root = os.path.abspath(options["root"] or
                           os.path.dirname(os.path.dirname(
                               os.path.dirname(os.path.abspath(__file__)))))
    runner = options["runner"] or os.path.join(root, "src", "sandbox",
                                               "reconcile_all.py")
    # R2479 AC-RSC1: the cap is a READING of the runner source, so this
    # instrument cannot disagree with the run it describes. The import is
    # the dunder form on purpose: AC-RTH6 pins this module's import set to
    # exactly ast/io/json/os/re/sys, and a top-level (or indented) import
    # statement would widen it. A fixture world carries no declaration, so
    # runner_suite_timeout_cap answers its fallback cap and the pinned
    # 300.0 fixtures keep reading exactly as they did.
    if not options["cap_given"] and os.path.isfile(runner):
        options["cap"] = __import__(
            "runner_suite_timeout_cap").default_cap(runner)
    evidence = paths or default_inputs(root)
    if not evidence:
        print("E_RTH_NO_EVIDENCE: no reconcile-all-*.log under %s"
              % os.path.join(root, "qa"), flush=True)
        return 3
    try:
        report = check(root, evidence, runner, options["cap"],
                       options["band"])
    except HeadroomError as exc:
        print("%s: %s" % (exc.code, exc.detail), flush=True)
        return 3
    if options["json"]:
        payload = dict((key, report[key]) for key in REPORT_KEYS)
        print(json.dumps(payload, sort_keys=False), flush=True)
    else:
        print(render(report), flush=True)
    return report["code"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))