"""Per-suite timeout cap as a READING of the runner source (R2479).

Criteria AC-RSC1..AC-RSC6 were pinned inside the R2478 seed row of
state/queue/tech.md BEFORE this module existed. The defect they answer: the
battery carried a flat 300s per-suite cap and the headroom reader carried a
SECOND 300 literal, so the instrument and the run could disagree, and three
ledger suites measured 232.2s / 268.1s / 300.1s against a cap with no load
headroom left (R2393 leg 3, R2466 leg 2 and R2478 leg 1 each lost a suite to
it).

This module owns exactly one reading: given a runner source path, what cap
does that runner actually apply, and where did that number come from. Two
answers are possible and both are stated rather than implied:

  * declared - the runner carries ``SUITE_TIMEOUT_S = <number>`` and that
    number is returned;
  * fallback - no such line exists (a fixture world, or a runner that lost
    the constant), so FALLBACK_CAP is returned and the caller can tell the
    difference instead of trusting a number nobody declared.

Pure ASCII, stdlib only, zero network, no clock, read-only.
"""

import json
import os
import re
import sys

FALLBACK_CAP = 300.0

DECLARED = "declared"
FALLBACK = "fallback"

CAP_RE = re.compile(r"(?m)^SUITE_TIMEOUT_S\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*$")
OVERRIDE_RE = re.compile(r"(?m)^SUITE_TIMEOUT_OVERRIDES\s*=\s*\{([^}]*)\}")

USAGE = ("usage: runner_suite_timeout_cap.py --check [--runner PATH] "
         "[--json]")


class CapError(Exception):
    def __init__(self, code, detail):
        Exception.__init__(self, detail)
        self.code = code
        self.detail = detail


def read_source(runner_path):
    with open(runner_path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def read_cap(runner_path):
    """Return (cap, source_kind, occurrences) for one runner source.

    AC-RSC1: the number comes from the source, never from a second literal
    here, and occurrences is reported so a duplicate declaration is visible
    rather than silently last-wins.
    """
    text = read_source(runner_path)
    found = CAP_RE.findall(text)
    if not found:
        return FALLBACK_CAP, FALLBACK, 0
    return float(found[0]), DECLARED, len(found)


def read_overrides(runner_path):
    """Return the declared override labels without executing the runner.

    A declaration is a JSON-shaped dict literal on one line, which is how the
    runner writes it; anything unparseable is reported as an empty mapping so
    the caller never guesses.
    """
    text = read_source(runner_path)
    match = OVERRIDE_RE.search(text)
    if not match:
        return {}
    body = "{" + match.group(1) + "}"
    try:
        loaded = json.loads(body)
    except ValueError:
        return {}
    return dict(loaded) if isinstance(loaded, dict) else {}


def default_cap(runner_path):
    """The reader's default: the runner's own declaration, else the fallback.

    This is the single seam the headroom reader calls, so a runner change
    moves the instrument with no second edit anywhere.
    """
    return read_cap(runner_path)[0]


def assess(runner_path):
    cap, kind, occurrences = read_cap(runner_path)
    overrides = read_overrides(runner_path)
    ok = kind == DECLARED and occurrences == 1 and cap > 0
    return {"cap": "%.1f" % cap,
            "source": kind,
            "occurrences": occurrences,
            "overrides": sorted(overrides),
            "verdict": "CAP-DECLARED" if ok else "CAP-UNDECLARED",
            "ok": ok}


def render(report):
    lines = ["CAP %ss source=%s declarations=%d overrides=%d"
             % (report["cap"], report["source"], report["occurrences"],
                len(report["overrides"]))]
    for label in report["overrides"]:
        lines.append("OVERRIDE %s" % label)
    lines.append("VERDICT %s" % report["verdict"])
    return "\n".join(lines)


def parse_args(argv):
    options = {"check": False, "runner": None, "json": False, "help": False}
    index = 0
    while index < len(argv):
        token = argv[index]
        if token in ("--check",):
            options["check"] = True
            index += 1
        elif token in ("--json",):
            options["json"] = True
            index += 1
        elif token in ("--help", "-h"):
            options["help"] = True
            index += 1
        elif token == "--runner":
            if index + 1 >= len(argv) or not argv[index + 1]:
                raise CapError("E_RSC_BAD_ARGS", "--runner needs a value")
            options["runner"] = argv[index + 1]
            index += 2
        else:
            raise CapError("E_RSC_BAD_ARGS", token)
    return options


def main(argv):
    try:
        options = parse_args(argv)
    except CapError as exc:
        print("%s\n%s" % (exc.code, USAGE), flush=True)
        return 5
    if options["help"]:
        print(USAGE, flush=True)
        return 0
    if not options["check"]:
        print("E_RSC_BAD_ARGS: --check is required\n%s" % USAGE, flush=True)
        return 5
    runner = options["runner"]
    if not runner:
        root = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        runner = os.path.join(root, "src", "sandbox", "reconcile_all.py")
    if not os.path.isfile(runner):
        print("E_RSC_NO_RUNNER: %s" % runner, flush=True)
        return 3
    report = assess(runner)
    if options["json"]:
        print(json.dumps(report, sort_keys=True), flush=True)
    else:
        print(render(report), flush=True)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
