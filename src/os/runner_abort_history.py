"""Whether an aborted battery leg still matters (R2417; AC-RAH1..AC-RAH6).

runner_abort_face names the suite a body died on, but it cannot say whether
that abort is still debt. Measured at R2403 over the real pile, the bodies
reading ABORTED had no way to be told apart from live debt - and measured
again at this round, the R2393 retry leg the seed named now carries its own
RUNNER FAIL, so the question is answered per body rather than per story.

This module pairs an aborted body with its round's retry family and answers
one of:

  SUPERSEDED   a leg of the same round ended RUNNER PASS, so the abort is
               history; BOTH file names are published (exit 0);
  LIVE-ABORT   no leg of that round ended RUNNER PASS (exit 2);
  ORPHAN-ABORT the name carries no canonical round token at all, so no
               family can be formed and it is never folded into another
               round's (exit 3);
  NOT-ABORTED  the body carries the runner's own verdict line, so there is
               no abort to age (exit 0);
  UNREADABLE   the body carries neither a verdict line nor a suite line
               (exit 3).

Every law is asked at CALL time and none is restated here:

  * the abort verdict and the RUNNER PASS word are runner_abort_face's own
    reading and its own verdict expression;
  * the retry family, its leg order and the canonical naming scope are
    followup_retry_legs' own leg_names plus followup_history's own name law,
    the same pair the aggregate history already reads rounds through;
  * the canonical round token in a file name is round_evidence's file_round.

Because the family law only covers the canonical battery scope, a body whose
name lives outside it reads family_code naming the shipped refusal instead of
having a family invented for it (the family and the leg index are read only
for a body that reads ABORTED; every other body reports family=[] leg=-1).

Criteria AC-RAH1..AC-RAH6 were pre-registered in state/queue/tech.md line 484
(the R2403 seed row) BEFORE this file existed.

Pure ASCII, stdlib only, no clock, no network, read-only: the reader opens
evidence bodies for reading and writes nothing.
"""

import json
import os
import sys

SUITE_LABEL = "os-runner-abort-history"

SUPERSEDED = "SUPERSEDED"
LIVE_ABORT = "LIVE-ABORT"
ORPHAN_ABORT = "ORPHAN-ABORT"
NOT_ABORTED = "NOT-ABORTED"
UNREADABLE = "UNREADABLE"

NO_FAMILY = "-"

REPORT_KEYS = ("evidence", "verdict", "abort", "round", "leg_index",
               "green_leg", "family", "family_code", "code")


class HistoryError(Exception):
    """Raised with a machine-readable .code."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _base_module(name):
    base = os.path.dirname(os.path.abspath(__file__))
    if base not in sys.path:
        sys.path.insert(0, base)
    return __import__(name)


def _abort_face():
    """The shipped abort reading, asked at call time."""
    return _base_module("runner_abort_face")


def _retry_naming():
    """The shipped retry-naming law, asked at call time."""
    return _base_module("retry_naming")


def _round_evidence():
    """The shipped canonical-round-in-a-name law, asked at call time."""
    return _base_module("round_evidence")


def _leg_reader():
    """The shipped retry-family reader, asked at call time."""
    return _base_module("followup_retry_legs")


def _family_law():
    """The shipped canonical-name scope, asked at call time."""
    return _base_module("followup_history")


def scope_stem(name):
    """The canonical stem this name belongs to, or None.

    The retry base-stem law is retry_naming's, so a retry leg collapses onto
    its own stem; the canonical scope is followup_history's own name law, so
    a name outside the battery naming reads None instead of being forced into
    a round.
    """
    stem = _retry_naming().base_stem(name)
    if _family_law().NAME_RE.match(stem + ".log") is None:
        return None
    return stem


def family(where, name):
    """(ordered family without this name, this name's index, refusal code).

    The order, the membership test and the retry spelling are
    followup_retry_legs' own leg_names; a refusal there is carried as the
    code rather than being turned into an empty family that reads like a
    body with no siblings.
    """
    reader = _leg_reader()
    stem = scope_stem(name)
    if stem is None:
        return [], -1, "OUT-OF-SCOPE"
    try:
        names = reader.leg_names(where, stem)
    except reader.FollowupRetryError as exc:
        return [], -1, exc.code
    if name not in names:
        return names, -1, "NOT-IN-FAMILY"
    return ([other for other in names if other != name],
            names.index(name), NO_FAMILY)


def _verdict_word(face, report):
    """The PASS/FAIL word of the body's own verdict line, or None."""
    line = report.get("verdict_line") or ""
    match = face.VERDICT_RE.match(line)
    if not match:
        return None
    return match.group(1)


def history(evidence_path, runner_path, directory=None):
    """One evidence body -> the pinned report (read-only)."""
    face = _abort_face()
    rounds = _round_evidence()
    name = os.path.basename(evidence_path)
    where = directory or os.path.dirname(os.path.abspath(evidence_path))
    try:
        report = face.check(evidence_path, runner_path)
    except face.AbortError as exc:
        raise HistoryError("E_RAH_UNREADABLE",
                           "%s: %s" % (exc.code, exc.detail))
    abort = report["verdict"]
    round_no = rounds.file_round(name)
    row = {"evidence": name, "verdict": abort, "abort": abort,
           "round": round_no, "leg_index": -1, "green_leg": "-",
           "family": [], "family_code": NO_FAMILY, "code": 0}
    if abort == face.COMPLETE:
        row["verdict"] = NOT_ABORTED
        return row
    if abort != face.ABORTED:
        row["verdict"] = UNREADABLE
        row["code"] = 3
        return row
    if round_no is None:
        row["verdict"] = ORPHAN_ABORT
        row["code"] = 3
        return row
    members, index, refusal = family(where, name)
    row["family"] = members
    row["leg_index"] = index
    row["family_code"] = refusal
    green = []
    for member in members:
        try:
            other = face.check(os.path.join(where, member), runner_path)
        except (face.AbortError, OSError):
            continue
        if other["verdict"] == face.COMPLETE and \
                _verdict_word(face, other) == "PASS":
            green.append(member)
    if green:
        row["green_leg"] = green[-1]
        row["verdict"] = SUPERSEDED
        return row
    row["verdict"] = LIVE_ABORT
    row["code"] = 2
    return row


def render(row):
    lines = ["BATTERY ABORT HISTORY %s evidence=%s round=%s leg=%s family=%d"
             % (row["verdict"], row["evidence"],
                "-" if row["round"] is None else "R%d" % (row["round"],),
                "-" if row["leg_index"] < 0 else row["leg_index"],
                len(row["family"]))]
    if row["verdict"] == SUPERSEDED:
        lines.append("GREEN %s (a leg of the same round ended RUNNER PASS)"
                     % row["green_leg"])
        lines.append("SUPERSEDED-BY %s" % row["green_leg"])
    elif row["verdict"] == LIVE_ABORT:
        lines.append("no leg of round R%d ended RUNNER PASS"
                     % (row["round"],))
        if row["family_code"] != NO_FAMILY:
            lines.append("FAMILY-UNRESOLVED %s" % row["family_code"])
    elif row["verdict"] == ORPHAN_ABORT:
        lines.append("no canonical round token in this name, so no family")
    elif row["verdict"] == NOT_ABORTED:
        lines.append("abort=none (the body carries the runner's own verdict)")
    else:
        lines.append("no suite line and no verdict line in this body")
    return "\n".join(lines)


USAGE = ("usage: runner_abort_history.py --check [--root PATH] "
         "[--runner PATH] [--json] EVIDENCE\n"
         "exit 0 = SUPERSEDED or NOT-ABORTED, 2 = LIVE-ABORT, "
         "3 = ORPHAN-ABORT or unreadable, 5 = bad flags")


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
                raise HistoryError("E_RAH_BAD_ARGS",
                                   "%s needs a value" % token)
            options[token[2:]] = argv[index]
        elif token.startswith("-"):
            raise HistoryError("E_RAH_BAD_ARGS", "unknown flag: %s" % token)
        else:
            paths.append(token)
        index += 1
    if len(paths) != 1:
        raise HistoryError("E_RAH_BAD_ARGS",
                           "exactly one evidence path is required")
    options["evidence"] = paths[0]
    return options


def main(argv):
    try:
        options = parse_args(argv)
    except HistoryError as exc:
        print("%s\n%s" % (exc.code, USAGE), flush=True)
        return 5
    if not options["check"]:
        print("E_RAH_BAD_ARGS: --check is required\n%s" % USAGE, flush=True)
        return 5
    root = os.path.abspath(options["root"] or
                           os.path.dirname(os.path.dirname(
                               os.path.dirname(os.path.abspath(__file__)))))
    runner = options["runner"] or os.path.join(root, "src", "sandbox",
                                               "reconcile_all.py")
    try:
        row = history(options["evidence"], runner)
    except HistoryError as exc:
        print("%s: %s" % (exc.code, exc.detail), flush=True)
        return 3
    if options["json"]:
        payload = dict((key, row[key]) for key in REPORT_KEYS)
        print(json.dumps(payload, sort_keys=False), flush=True)
        return row["code"]
    print(render(row), flush=True)
    return row["code"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))