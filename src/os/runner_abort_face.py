"""Which suite killed the battery, named from the body it left behind (R2403).

runner_suite_timeout_headroom reads the suites some leg FINISHED, so the one
suite that actually killed a run is the one line the pile never carries:
R2393 leg 3 died on ledger/test_apimarket_report_claims.py after exactly
300s and no suite line was ever written for it, which is why the same suite
reads 246.8s today and looks merely slow.

This module reads a battery body and answers three things:

  COMPLETE   the body carries the runner's own verdict line, so nothing was
             aborted and no abort reading is written at all;
  ABORTED    the body carries suite lines but no verdict line, so the run
             died; the suite that was running is derived as the FIRST suite
             the runner registers that has no suite line in the body - never
             a hard-coded label - and the last echoed line is carried so an
             operator sees where it stopped;
  UNREADABLE the body carries neither a verdict line nor a suite line, so
             silence is not read as an abort.

The registry labels and the suite-line law are asked of
runner_suite_timeout_headroom at CALL time, so patching either one moves this
reading and the tree keeps one owner for both.

Criteria AC-RAF1..AC-RAF6 were pre-registered in state/queue/tech.md line 474
(the R2395 seed row) BEFORE this file existed.

Pure ASCII, stdlib only, no clock, no network, read-only: the CLI opens the
runner source and the evidence body for reading and writes nothing.
"""

import io
import json
import os
import re
import sys

SUITE_LABEL = "os-runner-abort-face"

COMPLETE = "COMPLETE"
ABORTED = "ABORTED"
UNREADABLE = "UNREADABLE"

REPORT_KEYS = ("verdict", "code", "suite", "missing", "registered", "seen",
               "last_line", "evidence")

# The battery runner's own closing line, as reconcile_all prints it:
#   RUNNER PASS (520/520 suites green, reconcile controls 7/7, 1007.7s)
#   RUNNER FAIL (2 failed assertions)
VERDICT_RE = re.compile(r"^RUNNER (PASS|FAIL)\b")


class AbortError(Exception):
    def __init__(self, code, detail):
        Exception.__init__(self, detail)
        self.code = code
        self.detail = detail


def _headroom():
    """The shipped suite-line and registry law, asked at call time."""
    base = os.path.dirname(os.path.abspath(__file__))
    if base not in sys.path:
        sys.path.insert(0, base)
    import runner_suite_timeout_headroom
    return runner_suite_timeout_headroom


def carried_verdict(lines):
    """The runner's own closing verdict line, or None when the body has none."""
    for line in lines:
        if VERDICT_RE.match(line):
            return line.strip()
    return None


def seen_suites(lines):
    """Suite labels the body carries, in first-seen order (the shipped law)."""
    law = _headroom()
    order = []
    for line in lines:
        parsed = law.parse_evidence_line(line)
        if parsed is None:
            continue
        label = parsed[0]
        if label not in order:
            order.append(label)
    return order


def analyse(text, labels):
    """One body plus the runner's registry -> the pinned report."""
    lines = [line.rstrip("\r\n") for line in text.splitlines()]
    nonblank = [line for line in lines if line.strip()]
    last_line = nonblank[-1].strip() if nonblank else ""
    registered = list(labels)
    verdict_line = carried_verdict(lines)
    seen = seen_suites(lines)
    if verdict_line is not None:
        return {"verdict": COMPLETE, "code": 0, "suite": "-",
                "missing": [], "registered": len(registered),
                "seen": len(seen), "last_line": last_line,
                "evidence": "-", "verdict_line": verdict_line}
    if not seen:
        return {"verdict": UNREADABLE, "code": 3, "suite": "-",
                "missing": list(registered), "registered": len(registered),
                "seen": 0, "last_line": last_line, "evidence": "-",
                "verdict_line": "-"}
    missing = [label for label in registered if label not in seen]
    for label in seen:
        if label not in registered:
            registered.append(label)
    return {"verdict": ABORTED, "code": 2,
            "suite": missing[0] if missing else "-",
            "missing": missing, "registered": len(registered),
            "seen": len(seen), "last_line": last_line, "evidence": "-",
            "verdict_line": "-"}


def read_body(path):
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError as exc:
        raise AbortError("E_RAF_UNREADABLE",
                         "cannot read evidence %s: %s"
                         % (path, exc.strerror or exc))


def registry_labels(runner_path):
    """The registered labels, through the shipped reading (never re-derived)."""
    law = _headroom()
    try:
        return law.registry_labels(runner_path)
    except law.HeadroomError as exc:
        raise AbortError(exc.code, exc.detail)


def check(evidence_path, runner_path):
    report = analyse(read_body(evidence_path),
                     registry_labels(runner_path))
    report["evidence"] = os.path.basename(evidence_path)
    return report


def render(report):
    lines = ["BATTERY ABORT VERDICT %s evidence=%s registered=%d seen=%d"
             % (report["verdict"], report["evidence"],
                report["registered"], report["seen"])]
    if report["verdict"] == COMPLETE:
        lines.append("VERDICT-LINE %s" % report["verdict_line"])
        lines.append("abort=none (the body carries the runner's own verdict)")
    elif report["verdict"] == ABORTED:
        lines.append("SUITE %s (first registered suite with no suite line)"
                     % report["suite"])
        for label in report["missing"]:
            lines.append("MISSING %s" % label)
        lines.append("LAST %s" % report["last_line"])
    else:
        lines.append("no suite line and no verdict line in this body")
        lines.append("LAST %s" % report["last_line"])
    return "\n".join(lines)


USAGE = ("usage: runner_abort_face.py --check [--root PATH] [--runner PATH] "
         "[--json] EVIDENCE\n"
         "exit 0 = COMPLETE, 2 = ABORTED, 3 = UNREADABLE input, "
         "5 = bad flags")


def parse_args(argv):
    options = {"check": False, "root": None, "runner": None, "json": False}
    paths = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--check":
            options["check"] = True
        elif token == "--json":
            options["json"] = True
        elif token in ("--root", "--runner"):
            index += 1
            if index >= len(argv):
                raise AbortError("E_RAF_BAD_ARGS", "%s needs a value" % token)
            options[token[2:]] = argv[index]
        elif token.startswith("-"):
            raise AbortError("E_RAF_BAD_ARGS", "unknown flag: %s" % token)
        else:
            paths.append(token)
        index += 1
    if len(paths) != 1:
        raise AbortError("E_RAF_BAD_ARGS",
                         "exactly one evidence path is required")
    options["evidence"] = paths[0]
    return options


def main(argv):
    try:
        options = parse_args(argv)
    except AbortError as exc:
        print("%s\n%s" % (exc.code, USAGE), flush=True)
        return 5
    if not options["check"]:
        print("E_RAF_BAD_ARGS: --check is required\n%s" % USAGE, flush=True)
        return 5
    root = os.path.abspath(options["root"] or
                           os.path.dirname(os.path.dirname(
                               os.path.dirname(os.path.abspath(__file__)))))
    runner = options["runner"] or os.path.join(root, "src", "sandbox",
                                               "reconcile_all.py")
    try:
        report = check(options["evidence"], runner)
    except AbortError as exc:
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