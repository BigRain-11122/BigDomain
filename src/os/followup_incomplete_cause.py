"""followup_incomplete_cause (R2343; criteria AC-FIC1..AC-FIC6 were pinned
inside the R2325 seed row of state/queue/tech.md BEFORE this code existed).

followup_history names which rounds are unfixed (live at R2343: 413 of 438
read INCOMPLETE) and every one of them reads the same word. The measured
truth is that at least three different debts hide behind INCOMPLETE:

  - a LEGACY-DIALECT log that predates the SECTION ritual, so it can never
    carry sections at all and no rerun in the world would change it;
  - a NO-VERDICT log whose sections ran but whose VERDICT line was never
    written;
  - a MISSING-SECTION log whose VERDICT line exists while one or more of the
    named sections are ABSENT, which is the only one of the three a rerun
    would genuinely fix.

This module is a READ-ONLY classifier. For every round it:

  - asks the section vocabulary and the SECTION/VERDICT reading of
    followup_history rather than restating either (AC-FIC1), so a patched
    parser flows straight through this reader;
  - lands every round in exactly one of four disjoint causes (AC-FIC2);
  - derives the cause from the log body alone - no clock, no round-number
    threshold, no calendar (AC-FIC3);
  - refuses with its own code at exit 3 when the evidence directory or a log
    is unreadable, and never reads COMPLETE off a failed read (AC-FIC4);
  - writes nothing: the tree digest is identical before and after the run,
    the CLI is 0 only when every round is COMPLETE, 2 when any round is not,
    5 on bad flags, and --json is byte-stable over pinned keys (AC-FIC5);
  - is pure-ASCII source, stdlib only, zero network, and carries its own
    reconcile label os-followup-incomplete-cause (AC-FIC6).
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import followup_history as FH

E_FIC_BAD_ARGS = "E_FIC_BAD_ARGS"
E_FIC_NO_EVIDENCE = "E_FIC_NO_EVIDENCE"
E_FIC_UNREADABLE = "E_FIC_UNREADABLE"

CAUSES = ("LEGACY-DIALECT", "NO-VERDICT", "MISSING-SECTION", "COMPLETE")
REPORT_KEYS = ("dir", "rounds", "counts", "legacy_range", "verdict")
ROW_KEYS = ("round", "evidence", "cause", "absent", "has_verdict")


class FollowupCauseError(Exception):
    """A refused reading; never a fabricated COMPLETE."""

    def __init__(self, code, detail):
        Exception.__init__(self, code + ": " + str(detail))
        self.code = code
        self.detail = detail


def _round_number(label):
    """AC-FIC3: order by the round digits, never by the label text."""
    digits = "".join(ch for ch in label if ch.isdigit())
    return int(digits) if digits else 0


def classify(runs, verdict, names):
    """AC-FIC2: one cause per round, disjoint by construction.

    `runs` is the mapping followup_history.parse hands back (section name ->
    status list), `verdict` its raw VERDICT status (or None) and `names` the
    vocabulary it reports. The four causes partition the space: sections and
    verdict both absent, sections present but verdict absent, verdict present
    with sections absent, and nothing absent.
    """
    has_sections = bool(runs)
    has_verdict = verdict is not None
    absent = [name for name in names if name not in runs]
    if not has_sections and not has_verdict:
        cause = "LEGACY-DIALECT"
    elif has_sections and not has_verdict:
        cause = "NO-VERDICT"
    elif has_verdict and absent:
        cause = "MISSING-SECTION"
    else:
        cause = "COMPLETE"
    return {"cause": cause, "absent": absent, "has_verdict": has_verdict,
            "has_sections": has_sections}


def audit(root, directory="qa"):
    """Read every round's incompleteness cause. Writes nothing, no clock."""
    names = FH.vocabulary()
    try:
        path = FH.evidence_dir(root, directory)
    except FH.FollowupHistoryError:
        raise FollowupCauseError(E_FIC_NO_EVIDENCE, directory)
    try:
        found, ignored = FH.collect(path)
    except FH.FollowupHistoryError as exc:
        raise FollowupCauseError(E_FIC_UNREADABLE, exc.code)
    rounds = []
    for _number, label, target in found:
        try:
            text, _encoding = FH.read_log(target)
        except FH.FollowupHistoryError:
            raise FollowupCauseError(E_FIC_UNREADABLE, os.path.basename(target))
        runs, verdict, _runner = FH.parse(text)
        judged = classify(runs, verdict, names)
        rounds.append({
            "round": label,
            "evidence": os.path.relpath(target, root).replace(os.sep, "/"),
            "cause": judged["cause"],
            "absent": judged["absent"],
            "has_verdict": judged["has_verdict"],
        })
    counts = {}
    for cause in CAUSES:
        counts[cause] = 0
    for item in rounds:
        counts[item["cause"]] += 1
    legacy = sorted((item["round"] for item in rounds
                     if item["cause"] == "LEGACY-DIALECT"),
                    key=_round_number)
    legacy_range = None
    if legacy:
        legacy_range = "%s..%s" % (legacy[0], legacy[-1])
    verdict = "ALL-COMPLETE" if counts["COMPLETE"] == len(rounds) else "SPLIT"
    return {"dir": directory.replace(os.sep, "/"), "rounds": rounds,
            "counts": counts, "legacy_range": legacy_range,
            "verdict": verdict}


def render(report):
    """One header line plus one line per round, in the house voice."""
    counts = report["counts"]
    head = ("FOLLOWUP INCOMPLETE CAUSE rounds=%d complete=%d legacy=%d "
            "no_verdict=%d missing_section=%d legacy_range=%s verdict=%s"
            % (len(report["rounds"]), counts["COMPLETE"],
               counts["LEGACY-DIALECT"], counts["NO-VERDICT"],
               counts["MISSING-SECTION"], report["legacy_range"] or "-",
               report["verdict"]))
    lines = [head]
    for item in report["rounds"]:
        lines.append("  %s %s absent=%s%s" % (
            item["round"], item["cause"],
            ",".join(item["absent"]) if item["absent"] else "-",
            "" if item["has_verdict"] else " (no-verdict)"))
    return "\n".join(lines)


def to_json(report):
    """AC-FIC5: byte-stable JSON over pinned keys, rows kept in scan order."""
    ordered = {}
    for key in REPORT_KEYS:
        if key == "rounds":
            rows = []
            for item in report["rounds"]:
                row = {}
                for row_key in ROW_KEYS:
                    row[row_key] = item[row_key]
                rows.append(row)
            ordered[key] = rows
        else:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: followup_incomplete_cause.py --audit [--root PATH] [--json]\n"
         "  exit 0 = every round reads COMPLETE\n"
         "  exit 2 = at least one round is not COMPLETE\n"
         "  exit 3 = evidence directory or a log unreadable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    operation = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--audit":
            operation = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write(E_FIC_BAD_ARGS + ": --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write(E_FIC_BAD_ARGS + ": unknown flag " + arg + "\n")
            sys.stdout.write(USAGE)
            return 5
        else:
            sys.stdout.write(E_FIC_BAD_ARGS + ": unexpected argument "
                             + arg + "\n")
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not operation:
        sys.stdout.write(E_FIC_BAD_ARGS + ": --audit is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = audit(root, "qa")
    except FollowupCauseError as exc:
        sys.stdout.write(str(exc) + "\n")
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "ALL-COMPLETE":
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))