"""followup_section_foreign (R2357; criteria AC-FSF1..AC-FSF6 were pinned
inside the R2343 seed row of state/queue/tech.md BEFORE this code existed).

followup_history reports the sections a round DID report and marks the
ritual's own four ABSENT. Its parse, however, collects a SECTION line under
ANY name, and nothing ever looks at that name again: a log carrying an older
or a future ritual name is neither reported nor refused. Measured at R2343 on
the live log.

This module is the READ-ONLY reader for that gap. The vocabulary and the
parse are followup_history's (imported at call time, never restated), and the
verdict is derived from the logs alone, per round:

  - FOREIGN-SECTION   the round carries section names outside the vocabulary,
                      listed with the legs they ran;
  - VOCABULARY-CLEAN  every name the round reported is inside it.

The two readings are disjoint and every round lands in exactly one. A
directory-level census turns a ritual RENAME into a set difference instead of
a silent gap: the vocabulary names never seen anywhere (`missing`) and the
foreign names seen (`foreign`).

It writes nothing, reads no clock, opens no network connection, and has no
round threshold of its own. Pure stdlib, pure-ASCII source.
"""

import io
import json
import os
import sys

import followup_history as FH

REPORT_KEYS = ("dir", "vocabulary", "rounds", "counts", "census", "verdict")
ROUND_KEYS = ("round", "evidence", "reading", "foreign")
COUNT_KEYS = ("rounds", "clean", "foreign")
CENSUS_KEYS = ("vocabulary", "foreign", "missing")

READING_CLEAN = "VOCABULARY-CLEAN"
READING_FOREIGN = "FOREIGN-SECTION"
VERDICT_CLEAN = "VOCABULARY-CLEAN"
VERDICT_FOREIGN = "FOREIGN-SECTION"

E_FSF_BAD_ARGS = "E_FSF_BAD_ARGS"
E_FSF_NO_EVIDENCE = "E_FSF_NO_EVIDENCE"
E_FSF_UNREADABLE = "E_FSF_UNREADABLE"
E_FSF_DUP_ROUND = "E_FSF_DUP_ROUND"

# The refusal codes below belong to followup_history; this reader keeps its
# own code surface while carrying that module's detail verbatim.
TRANSLATE = {
    "E_FHY_NO_EVIDENCE": E_FSF_NO_EVIDENCE,
    "E_FHY_UNREADABLE": E_FSF_UNREADABLE,
    "E_FHY_DUP_ROUND": E_FSF_DUP_ROUND,
}


class FollowupSectionForeignError(Exception):
    """A reading that must not guess, carrying its own token."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code + (" " + detail if detail else ""))
        self.code = code
        self.detail = detail


def vocabulary():
    """AC-FSF1: the ritual names have exactly one owner (followup_history)."""
    return tuple(FH.vocabulary())


def foreign_of(runs, names):
    """AC-FSF2: the names a round reported that the vocabulary does not own."""
    return sorted(name for name in runs if name not in names)


def round_of(label, evidence, runs, names):
    """One round's reading; the two readings are disjoint by construction."""
    foreign = foreign_of(runs, names)
    return {"round": label, "evidence": evidence,
            "reading": READING_FOREIGN if foreign else READING_CLEAN,
            "foreign": foreign}


def census_of(rounds, names):
    """AC-FSF2: a rename is a set difference, not a silent gap."""
    seen = set()
    foreign = set()
    for item in rounds:
        seen.update(name for name in item["_runs"])
        foreign.update(item["foreign"])
    return {"vocabulary": list(names),
            "foreign": sorted(foreign),
            "missing": sorted(name for name in names if name not in seen)}


def reading(root, directory="qa"):
    """Read every round's section names. Writes nothing, reads no clock."""
    try:
        path = FH.evidence_dir(root, directory)
        names = vocabulary()
        found, ignored = FH.collect(path)
        rounds = []
        for _number, label, target in found:
            text, _encoding = FH.read_log(target)
            runs, _verdict, _runner = FH.parse(text)
            shown = os.path.relpath(target, root).replace(os.sep, "/")
            row = round_of(label, shown, runs, names)
            row["_runs"] = tuple(runs)
            rounds.append(row)
    except FH.FollowupHistoryError as exc:
        raise FollowupSectionForeignError(TRANSLATE.get(exc.code,
                                                        E_FSF_UNREADABLE),
                                          exc.detail)
    census = census_of(rounds, names)
    clean = 0
    for item in rounds:
        if item["reading"] == READING_CLEAN:
            clean += 1
    counts = {"rounds": len(rounds), "clean": clean,
              "foreign": len(rounds) - clean}
    verdict = VERDICT_FOREIGN if counts["foreign"] else VERDICT_CLEAN
    shown_rounds = []
    for item in rounds:
        shown_rounds.append({"round": item["round"],
                             "evidence": item["evidence"],
                             "reading": item["reading"],
                             "foreign": item["foreign"]})
    return {"dir": directory.replace(os.sep, "/"), "vocabulary": list(names),
            "rounds": shown_rounds, "counts": counts, "census": census,
            "verdict": verdict, "ignored": ignored}


def render(report):
    """One line per round, then the directory census, then the verdict."""
    counts = report["counts"]
    census = report["census"]
    out = ["FOLLOWUP SECTIONS dir=%s rounds=%d clean=%d foreign=%d "
           "vocabulary=%s"
           % (report["dir"], counts["rounds"], counts["clean"],
              counts["foreign"], ",".join(report["vocabulary"]) or "-")]
    for item in report["rounds"]:
        out.append("  %s %s evidence=%s foreign=%s"
                   % (item["round"], item["reading"], item["evidence"],
                      ",".join(item["foreign"]) or "none"))
    out.append("census foreign=%s missing=%s"
               % (",".join(census["foreign"]) or "none",
                  ",".join(census["missing"]) or "none"))
    out.append("verdict=%s" % report["verdict"])
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    ordered["rounds"] = []
    for item in report["rounds"]:
        row = {}
        for key in ROUND_KEYS:
            row[key] = item[key]
        ordered["rounds"].append(row)
    ordered["counts"] = {}
    for key in COUNT_KEYS:
        ordered["counts"][key] = report["counts"][key]
    ordered["census"] = {}
    for key in CENSUS_KEYS:
        ordered["census"][key] = report["census"][key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: followup_section_foreign.py --check [DIR] [--root PATH] "
         "[--json]\n"
         "  DIR defaults to qa\n"
         "  exit 0 = every round's section names are in the vocabulary\n"
         "  exit 2 = some round carries a foreign section name\n"
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
        if arg == "--check":
            operation = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_FSF_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write("E_FSF_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        else:
            directory = arg
        index += 1
    if not operation:
        sys.stdout.write("E_FSF_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = reading(root, directory)
    except FollowupSectionForeignError as exc:
        sys.stdout.write("%s\n" % str(exc))
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == VERDICT_FOREIGN:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))