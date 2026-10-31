"""followup_history (R2288; criteria AC-FHY1..AC-FHY6 were pinned inside the
R2272 seed row of state/queue/tech.md BEFORE this code existed).

The four post-battery sections now run as one callable (battery_followup), but
their HISTORY stayed prose. Every round's evidence log carries SECTION and
VERDICT lines and the operator re-read them by eye, so:

  - a section that FAILED at R2271 and PASSED at R2272 with no code change in
    between read exactly like a section that never failed;
  - a round whose follow-up never ran at all read exactly like a green round.

This module is a READ-ONLY reader over qa/reconcile-all-<Rxxxx>.log. It parses
the SECTION/VERDICT lines and reports, per round in R-number order:

  - each section's PASS/FAIL runs in the order they appear in the log (so a
    FAIL then PASS leg is visible, and the runs count is honest);
  - ABSENT for every section the round never reported, never silently skipped
    (AC-FHY1 - the vocabulary is imported from battery_followup.SECTIONS, so a
    second list can never drift);
  - INCOMPLETE for a log carrying no VERDICT line at all, never "green"
    (AC-FHY3).

It writes nothing, reads no clock, opens no network connection (AC-FHY4).
Unreadable or
missing evidence fails closed with its own code and zero fabricated rounds;
a duplicate round is refused rather than deduplicated (AC-FHY2).

Pure stdlib, pure-ASCII source, zero network.
"""

import io
import json
import os
import re
import sys

import battery_followup as BF

REPORT_KEYS = ("dir", "rounds", "counts", "ignored", "verdict")
ROUND_KEYS = ("round", "evidence", "encoding", "runner", "sections",
              "verdict")
SECTION_KEYS = ("name", "runs", "status")
COUNT_KEYS = ("rounds", "green", "red", "incomplete", "ignored")

NAME_RE = re.compile(r"^reconcile-all-(R(\d+))\.log$")

E_FHY_BAD_ARGS = "E_FHY_BAD_ARGS"
E_FHY_NO_EVIDENCE = "E_FHY_NO_EVIDENCE"
E_FHY_UNREADABLE = "E_FHY_UNREADABLE"
E_FHY_DUP_ROUND = "E_FHY_DUP_ROUND"


class FollowupHistoryError(Exception):
    """A reading that must not guess, carrying its own token."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code + (" " + detail if detail else ""))
        self.code = code
        self.detail = detail


def vocabulary():
    """AC-FHY1: the section names have exactly one owner."""
    return tuple(BF.SECTIONS)


def evidence_dir(root, directory):
    """Resolve the evidence directory; absent is an error, never empty."""
    path = directory
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    if not os.path.isdir(path):
        raise FollowupHistoryError(E_FHY_NO_EVIDENCE, directory)
    return path


def collect(path):
    """AC-FHY2: name-derived rounds, ordered by R number, duplicates refused."""
    found = []
    ignored = []
    for name in sorted(os.listdir(path)):
        if not name.startswith("reconcile-all"):
            continue
        match = NAME_RE.match(name)
        if match is None:
            ignored.append(name)
            continue
        found.append((int(match.group(2)), match.group(1),
                      os.path.join(path, name)))
    if not found:
        raise FollowupHistoryError(E_FHY_NO_EVIDENCE, path)
    found.sort(key=lambda item: item[0])
    seen = {}
    for number, label, target in found:
        if number in seen:
            raise FollowupHistoryError(E_FHY_DUP_ROUND,
                                       "%s and %s" % (seen[number], label))
        seen[number] = label
    return found, ignored


def decode(raw):
    """Declared encoding ladder for a legacy pile; unknown bytes fail closed.

    34 of the shipped logs predate the single-writer utf-8 rule (10-31 R2288
    measured: UTF-16LE tees and cp936 captures). A BOM is trusted over a
    guess, plain utf-8 is tried before the locale code page, and anything
    that survives none of them is UNREADABLE rather than mojibake parsed as
    green.
    """
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        try:
            return raw.decode("utf-16"), "utf-16"
        except UnicodeDecodeError:
            raise FollowupHistoryError(E_FHY_UNREADABLE, "utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        try:
            return raw.decode("utf-8-sig"), "utf-8-sig"
        except UnicodeDecodeError:
            raise FollowupHistoryError(E_FHY_UNREADABLE, "utf-8-sig")
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp936"), "cp936"
    except (UnicodeDecodeError, LookupError):
        raise FollowupHistoryError(E_FHY_UNREADABLE, "unknown")


def read_log(path):
    """AC-FHY4: an unreadable log fails closed, never read as green."""
    try:
        with io.open(path, "rb") as handle:
            raw = handle.read()
    except (OSError, ValueError):
        raise FollowupHistoryError(E_FHY_UNREADABLE, os.path.basename(path))
    try:
        return decode(raw)
    except FollowupHistoryError as exc:
        raise FollowupHistoryError(exc.code, os.path.basename(path))


def parse(text):
    """Pull the SECTION and VERDICT lines; prose lines are inert."""
    runs = {}
    verdict = None
    runner = None
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if parts[0] == "SECTION" and len(parts) >= 3:
            status = parts[2]
            if status in ("PASS", "FAIL"):
                runs.setdefault(parts[1], []).append(status)
        elif parts[0] == "VERDICT" and len(parts) >= 3:
            if parts[2] in ("PASS", "FAIL"):
                verdict = parts[2]
        elif parts[0] == "RUNNER" and len(parts) >= 2:
            runner = parts[1]
    return runs, verdict, runner


def round_of(label, evidence, encoding, runs, verdict, runner, names):
    """One round's honest reading, ABSENT sections never skipped."""
    sections = []
    absent = False
    for name in names:
        recorded = list(runs.get(name, []))
        if recorded:
            status = recorded[-1]
        else:
            status = "ABSENT"
            absent = True
        sections.append({"name": name, "runs": recorded, "status": status})
    if verdict is None or absent:
        reading = "INCOMPLETE"
    elif verdict == "FAIL":
        reading = "FAIL"
    else:
        reading = "PASS"
    return {"round": label, "evidence": evidence, "encoding": encoding,
            "runner": runner, "sections": sections, "verdict": reading}


def history(root, directory="qa"):
    """Read every round's follow-up ritual. Writes nothing, reads no clock."""
    path = evidence_dir(root, directory)
    names = vocabulary()
    rounds = []
    found, ignored = collect(path)
    for _number, label, target in found:
        text, encoding = read_log(target)
        runs, verdict, runner = parse(text)
        shown = os.path.relpath(target, root).replace(os.sep, "/")
        rounds.append(round_of(label, shown, encoding, runs, verdict, runner,
                               names))
    counts = {"rounds": len(rounds), "green": 0, "red": 0, "incomplete": 0,
              "ignored": len(ignored)}
    for item in rounds:
        if item["verdict"] == "PASS":
            counts["green"] += 1
        elif item["verdict"] == "INCOMPLETE":
            counts["incomplete"] += 1
        else:
            counts["red"] += 1
    if counts["red"] or counts["incomplete"]:
        verdict = "HISTORY-RED"
    else:
        verdict = "ALL-GREEN"
    return {"dir": directory.replace(os.sep, "/"), "rounds": rounds,
            "counts": counts, "ignored": ignored, "verdict": verdict}


def render(report):
    """One line per round, sections in the pinned order."""
    counts = report["counts"]
    out = ["FOLLOWUP HISTORY dir=%s rounds=%d green=%d red=%d incomplete=%d "
           "ignored=%d"
           % (report["dir"], counts["rounds"], counts["green"], counts["red"],
              counts["incomplete"], counts["ignored"])]
    for item in report["rounds"]:
        legs = []
        for section in item["sections"]:
            if section["runs"]:
                legs.append("%s:%s" % (section["name"],
                                       ">".join(section["runs"])))
            else:
                legs.append("%s:ABSENT" % section["name"])
        out.append("  %s %s evidence=%s encoding=%s runner=%s"
                   % (item["round"], item["verdict"], item["evidence"],
                      item["encoding"], item["runner"] or "-"))
        out.append("    sections=%s" % ",".join(legs))
    out.append("verdict=%s" % report["verdict"])
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    ordered["counts"] = {}
    for key in COUNT_KEYS:
        ordered["counts"][key] = report["counts"][key]
    pinned = []
    for item in report["rounds"]:
        row = {}
        for key in ROUND_KEYS:
            row[key] = item[key]
        sections = []
        for section in item["sections"]:
            leg = {}
            for key in SECTION_KEYS:
                leg[key] = section[key]
            sections.append(leg)
        row["sections"] = sections
        pinned.append(row)
    ordered["rounds"] = pinned
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: followup_history.py --history [DIR] [--root PATH] [--json]\n"
         "  DIR defaults to qa\n"
         "  exit 0 = every parsed round is complete and green\n"
         "  exit 2 = some round is INCOMPLETE or red\n"
         "  exit 3 = evidence absent / unreadable / duplicate round\n"
         "  exit 5 = bad flags\n")


def main(argv):
    operation = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    directory = "qa"
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--history":
            operation = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_FHY_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write("E_FHY_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        else:
            directory = arg
        index += 1
    if not operation:
        sys.stdout.write("E_FHY_BAD_ARGS: --history is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = history(root, directory)
    except FollowupHistoryError as exc:
        sys.stdout.write("%s\n" % str(exc))
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "HISTORY-RED":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))