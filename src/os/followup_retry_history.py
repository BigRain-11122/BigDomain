"""followup_retry_history (R2325; criteria AC-FRH1..AC-FRH6 were pinned inside
the R2303 seed row of state/queue/tech.md:380 BEFORE this code existed).

followup_retry_legs reads ONE round through its retry family. The aggregate
the house actually prints (`followup_history --history`) still judged every
round from its canonical leg alone, so a round recovered by a green retry was
counted red and the aggregate could never read ALL-GREEN while any recovered
round existed (live at R2303: rounds=427 red=412 with four retried rounds).

This module is a READ-ONLY aggregate over the whole evidence directory. Per
round it takes the LAST leg's verdict and the canonical leg's verdict from
followup_retry_legs (asked, never re-implemented - AC-FRH1), and splits every
round into one of four disjoint classes:

  - green     canonical PASS and last PASS (nothing was ever wrong);
  - recovered canonical not PASS and last PASS (a retry repaired the round);
  - unfixed   canonical not PASS and last not PASS (still broken);
  - regressed canonical PASS and last not PASS (a later leg went red after a
              green canonical - reported, never silently folded into green).

recovered and unfixed therefore PARTITION the rounds whose canonical leg is
not PASS (AC-FRH2); regressed is reported separately so no round is lost and
no class overlaps. A round with no retry leg keeps exactly the reading
followup_history gives it (AC-FRH3, inherited from followup_retry_legs). A
retry leg with no canonical leg is refused with its own code rather than
dropped from the counts (AC-FRH4).

It writes nothing, reads no clock, opens no network connection (AC-FRH5/6).
Pure stdlib, pure-ASCII source, zero network.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import followup_retry_legs as FR
import retry_naming as RN

REPORT_KEYS = ("dir", "rounds", "counts", "verdict")
ROUND_KEYS = ("round", "evidence", "canonical_verdict", "verdict", "leg_count",
              "klass")
COUNT_KEYS = ("rounds", "green", "retried", "recovered", "unfixed",
              "regressed")

CLASSES = ("green", "recovered", "unfixed", "regressed")

E_FRH_COUNT = "E_FRH_COUNT"
E_FRH_BAD_ARGS = "E_FRH_BAD_ARGS"


class FollowupRetryHistoryError(Exception):
    """A reading that must not guess, carrying its own token."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code + (" " + detail if detail else ""))
        self.code = code
        self.detail = detail


def canonical_verdict(item):
    """The canonical leg's own verdict; a silent leg reads INCOMPLETE."""
    verdict = item["legs"][0]["verdict"]
    return verdict if verdict in ("PASS", "FAIL") else "INCOMPLETE"


def classify(item):
    """One of the four disjoint classes (AC-FRH2)."""
    canonical = canonical_verdict(item)
    last = item["verdict"]
    if canonical == "PASS":
        return "green" if last == "PASS" else "regressed"
    return "recovered" if last == "PASS" else "unfixed"


def _evidence_path(root, directory):
    """The evidence directory, resolved exactly as followup_retry_legs does."""
    path = directory
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    return path


def _orphan_stems(path):
    """Stems named only by a retry leg, found by asking the naming law.

    followup_history.collect enumerates CANONICAL names only, so a retry leg
    whose canonical leg is gone is invisible to the aggregate and would be
    dropped from the counts. The predicate and the base-stem law are asked of
    retry_naming, never re-derived here.
    """
    stems = []
    try:
        listing = sorted(os.listdir(path))
    except OSError:
        return stems
    for name in listing:
        if not name.endswith(".log") or FR.FH.NAME_RE.match(name) is not None:
            continue
        if not RN.is_retry(name):
            continue
        try:
            base = RN.base_stem(name)
        except RN.RetryNamingError:
            continue
        try:
            stem = FR.canonical_stem(base)
        except FR.FollowupRetryError:
            continue
        if stem not in stems:
            stems.append(stem)
    return stems


def history(root, directory="qa"):
    """Every round read through its whole retry family, then classified.

    The per-round reading and the retry order come from followup_retry_legs;
    a patched reader moves this aggregate with it (AC-FRH1).
    """
    try:
        legs_report = FR.history(root, directory)
        path = _evidence_path(root, directory)
        if os.path.isdir(path):
            for stem in _orphan_stems(path):
                FR.leg_names(path, stem)
    except FR.FollowupRetryError as exc:
        raise FollowupRetryHistoryError(exc.code, exc.detail)
    rounds = []
    counts = {"rounds": 0, "green": 0, "retried": 0, "recovered": 0,
              "unfixed": 0, "regressed": 0}
    for item in legs_report["rounds"]:
        klass = classify(item)
        counts["rounds"] += 1
        counts[klass] += 1
        if item["leg_count"] > 1:
            counts["retried"] += 1
        rounds.append({"round": item["round"], "evidence": item["evidence"],
                       "canonical_verdict": canonical_verdict(item),
                       "verdict": item["verdict"],
                       "leg_count": item["leg_count"], "klass": klass})
    canonical_bad = sum(1 for item in rounds
                        if item["canonical_verdict"] != "PASS")
    if counts["recovered"] + counts["unfixed"] != canonical_bad:
        raise FollowupRetryHistoryError(
            E_FRH_COUNT,
            "recovered=%d unfixed=%d canonical_bad=%d"
            % (counts["recovered"], counts["unfixed"], canonical_bad))
    verdict = ("HISTORY-DEBT"
               if counts["unfixed"] or counts["regressed"] else "ALL-CLEAN")
    return {"dir": legs_report["dir"], "rounds": rounds, "counts": counts,
            "verdict": verdict}


def render(report):
    """One header line, one line per non-green round, then the verdict."""
    counts = report["counts"]
    out = ["FOLLOWUP RETRY HISTORY dir=%s rounds=%d green=%d retried=%d "
           "recovered=%d unfixed=%d regressed=%d"
           % (report["dir"], counts["rounds"], counts["green"],
              counts["retried"], counts["recovered"], counts["unfixed"],
              counts["regressed"])]
    for item in report["rounds"]:
        if item["klass"] == "green":
            continue
        out.append("  %s %s canonical=%s legs=%d evidence=%s"
                   % (item["round"], item["klass"], item["canonical_verdict"],
                      item["leg_count"], item["evidence"]))
    out.append("verdict=%s" % report["verdict"])
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        if key == "counts":
            counts = {}
            for name in COUNT_KEYS:
                counts[name] = report["counts"][name]
            ordered["counts"] = counts
        elif key == "rounds":
            pinned = []
            for item in report["rounds"]:
                row = {}
                for name in ROUND_KEYS:
                    row[name] = item[name]
                pinned.append(row)
            ordered["rounds"] = pinned
        else:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: followup_retry_history.py --history [DIR] [--root PATH] "
         "[--json]\n"
         "  DIR defaults to qa\n"
         "  exit 0 = no round is unfixed and none regressed\n"
         "  exit 2 = some round is unfixed or regressed\n"
         "  exit 3 = evidence absent / unreadable / retry without canonical\n"
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
                sys.stdout.write("E_FRH_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write("E_FRH_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        else:
            directory = arg
        index += 1
    if not operation:
        sys.stdout.write("E_FRH_BAD_ARGS: --history is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = history(root, directory)
    except FollowupRetryHistoryError as exc:
        sys.stdout.write("%s\n" % str(exc))
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "HISTORY-DEBT":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))