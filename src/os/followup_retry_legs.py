"""followup_retry_legs (R2303; criteria AC-FRTL1..AC-FRTL6 were pinned inside
the R2289 seed row of state/queue/tech.md BEFORE this code existed).

A correction rerun is named `<stem>-retry.log` by law (os-retry-naming), but
followup_history only reads `reconcile-all-R<nnnn>.log`: it reports the retry
leg as IGNORED and judges the round from the canonical leg alone. A round
whose first battery went RED and whose retry went GREEN therefore reads
FAIL/INCOMPLETE forever (measured live at R2289 and R2277), even though the
green leg is on disk with its own RUNNER line.

This module is a READ-ONLY joiner. Given a round it:

  - resolves the canonical leg plus every retry leg, taking the retry family
    (suffix constant, predicate and base-stem law) from retry_naming rather
    than restating it (AC-FRTL1);
  - orders the legs canonical first, then retry, -retry2, -retry3 (AC-FRTL2),
    with the order derived from retry_naming's own naming expression so a
    changed suffix moves this reader too;
  - takes the round verdict from the LAST leg while every earlier leg is
    still reported with its own runner line (AC-FRTL3);
  - returns, for a round with no retry leg, exactly the round entry
    followup_history would return (same keys, same reading) (AC-FRTL4);
  - refuses when a retry leg exists and its canonical leg does not, instead
    of inventing a round from a suffix (AC-FRTL5).

It writes nothing, reads no clock, opens no network connection (AC-FRTL6).
Pure stdlib, pure-ASCII source, zero network.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import followup_history as FH
import retry_naming as RN

REPORT_KEYS = ("dir", "target", "rounds", "counts", "verdict")
ROUND_KEYS = ("round", "evidence", "encoding", "runner", "sections", "legs",
              "leg_count", "verdict")
LEG_KEYS = ("name", "index", "kind", "runner", "verdict", "evidence")
COUNT_KEYS = ("rounds", "canonical_only", "retried", "red")

E_FRTL_BAD_ARGS = "E_FRTL_BAD_ARGS"
E_FRTL_NO_EVIDENCE = "E_FRTL_NO_EVIDENCE"
E_FRTL_ORPHAN_RETRY = "E_FRTL_ORPHAN_RETRY"
E_FRTL_BAD_RETRY_NAME = "E_FRTL_BAD_RETRY_NAME"


class FollowupRetryError(Exception):
    """A reading that must not guess, carrying its own token."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code + (" " + detail if detail else ""))
        self.code = code
        self.detail = detail


def _canonical_prefix():
    """The canonical name scope, asked of followup_history's own pattern.

    Only the literal head before the first group is read; a patched pattern
    moves the scope with it, so no second name law exists here.
    """
    pattern = FH.NAME_RE.pattern
    head = pattern[1:] if pattern.startswith("^") else pattern
    prefix = head.split("(")[0]
    if not prefix:
        raise FollowupRetryError(E_FRTL_BAD_RETRY_NAME, "empty name law")
    return prefix


def canonical_stem(target):
    """A round name (`R2289`, `reconcile-all-R2289`, or with `.log`)."""
    if not isinstance(target, str) or not target.strip():
        raise FollowupRetryError(E_FRTL_BAD_RETRY_NAME, repr(target))
    stem = target.strip()
    if stem.endswith(".log"):
        stem = stem[:-4]
    if FH.NAME_RE.match(stem + ".log") is not None:
        return stem
    prefix = _canonical_prefix()
    if stem.startswith(prefix):
        raise FollowupRetryError(E_FRTL_BAD_RETRY_NAME, target)
    candidate = prefix + stem
    if FH.NAME_RE.match(candidate + ".log") is None:
        raise FollowupRetryError(E_FRTL_BAD_RETRY_NAME, target)
    return candidate


def retry_index(stem, name):
    """The retry index of `name` for `stem`, asked of the naming expression.

    retry_naming builds `<stem><suffix><n>.log` with an empty n for the first
    retry, so the index is the n whose own construction equals the name. A
    retry name the generator cannot rebuild reads None and is refused rather
    than ordered by guesswork.
    """
    for index in range(1, 100):
        suffix = RN.RETRY_SUFFIX + ("" if index == 1 else str(index))
        if stem + suffix + ".log" == name:
            return index
    return None


def leg_names(path, stem):
    """Canonical leg first, then every retry leg in retry order (AC-FRTL2).

    The retry family is asked of retry_naming: the predicate decides what a
    retry is, the base-stem law decides which stem it belongs to, and the
    suffix constant supplies the order. A retry leg with no canonical leg
    refuses here (AC-FRTL5) instead of becoming a fabricated round.
    """
    try:
        listing = sorted(os.listdir(path))
    except OSError as exc:
        raise FollowupRetryError(E_FRTL_NO_EVIDENCE,
                                 "cannot list %r: %s" % (path, exc))
    canonical = stem + ".log"
    retries = []
    for name in listing:
        if name == canonical or not name.endswith(".log"):
            continue
        if FH.NAME_RE.match(name) is not None:
            continue
        if not RN.is_retry(name):
            continue
        try:
            base = RN.base_stem(name)
        except RN.RetryNamingError:
            continue
        if base != stem:
            continue
        index = retry_index(stem, name)
        if index is None:
            raise FollowupRetryError(E_FRTL_BAD_RETRY_NAME, name)
        retries.append((index, name))
    retries.sort()
    present = os.path.isfile(os.path.join(path, canonical))
    if retries and not present:
        raise FollowupRetryError(
            E_FRTL_ORPHAN_RETRY,
            "%s exists without %s" % (retries[0][1], canonical))
    if not present:
        raise FollowupRetryError(E_FRTL_NO_EVIDENCE, stem)
    return [canonical] + [name for _index, name in retries]


def read_leg(path, name, stem, names):
    """One leg's own reading: runner line, section runs, suite verdict."""
    text, encoding = FH.read_log(os.path.join(path, name))
    runs, verdict, runner = FH.parse(text)
    match = FH.NAME_RE.match(stem + ".log")
    label = match.group(1) if match is not None else stem
    index = 0 if name == stem + ".log" else retry_index(stem, name)
    kind = "canonical" if index == 0 else "retry"
    return {
        "name": name,
        "index": index,
        "kind": kind,
        "runner": runner,
        "verdict": verdict,
        "evidence": os.path.relpath(os.path.join(path, name),
                                    os.path.dirname(path)).replace(os.sep,
                                                                   "/"),
        "_round": label,
        "_encoding": encoding,
        "_runs": runs,
        "_names": names,
    }


def round_reading(path, stem):
    """The round as its last leg reads it, every earlier leg still reported."""
    names = FH.vocabulary()
    legs = [read_leg(path, name, stem, names) for name in
            leg_names(path, stem)]
    last = legs[-1]
    base = FH.round_of(last["_round"], last["evidence"], last["_encoding"],
                       last["_runs"], last["verdict"], last["runner"], names)
    reading = {}
    for key in ("round", "evidence", "encoding", "runner", "sections",
                "verdict"):
        reading[key] = base[key]
    pinned = []
    for leg in legs:
        row = {}
        for key in ("name", "index", "kind", "runner", "verdict", "evidence"):
            row[key] = leg[key]
        pinned.append(row)
    ordered = {}
    for key in ROUND_KEYS:
        if key == "legs":
            ordered["legs"] = pinned
        elif key == "leg_count":
            ordered["leg_count"] = len(pinned)
        else:
            ordered[key] = reading[key]
    return ordered


def history(root, directory="qa", target=None):
    """Every round (or one round) read through its whole retry family."""
    path = directory
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    if not os.path.isdir(path):
        raise FollowupRetryError(E_FRTL_NO_EVIDENCE, directory)
    rounds = []
    if target is None:
        try:
            found, _ignored = FH.collect(path)
        except FH.FollowupHistoryError as exc:
            raise FollowupRetryError(E_FRTL_NO_EVIDENCE, str(exc))
        for _number, label, _target in found:
            rounds.append(round_reading(path, canonical_stem(label)))
    else:
        rounds.append(round_reading(path, canonical_stem(target)))
    if not rounds:
        raise FollowupRetryError(E_FRTL_NO_EVIDENCE, directory)
    counts = {"rounds": len(rounds), "canonical_only": 0, "retried": 0,
              "red": 0}
    for item in rounds:
        if item["leg_count"] > 1:
            counts["retried"] += 1
        else:
            counts["canonical_only"] += 1
        if item["verdict"] != "PASS":
            counts["red"] += 1
    verdict = "HISTORY-RED" if counts["red"] else "ALL-GREEN"
    return {"dir": directory.replace(os.sep, "/"),
            "target": "all" if target is None else canonical_stem(target),
            "rounds": rounds, "counts": counts, "verdict": verdict}


def render(report):
    """One line per round, then one line per leg with its own runner line."""
    counts = report["counts"]
    out = ["FOLLOWUP RETRY LEGS dir=%s target=%s rounds=%d canonical_only=%d "
           "retried=%d red=%d"
           % (report["dir"], report["target"], counts["rounds"],
              counts["canonical_only"], counts["retried"], counts["red"])]
    for item in report["rounds"]:
        out.append("  %s %s legs=%d evidence=%s encoding=%s runner=%s"
                   % (item["round"], item["verdict"], item["leg_count"],
                      item["evidence"], item["encoding"], item["runner"]))
        for leg in item["legs"]:
            out.append("    leg %d %s %s runner=%s evidence=%s"
                       % (leg["index"], leg["kind"],
                          leg["verdict"] or "INCOMPLETE",
                          leg["runner"] or "-", leg["evidence"]))
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


USAGE = ("usage: followup_retry_legs.py --legs [ROUND|all] [--root PATH] "
         "[--json]\n"
         "  ROUND may be R<n>, reconcile-all-R<n>, or a full stem\n"
         "  exit 0 = every round reads PASS from its last leg\n"
         "  exit 2 = some round reads FAIL or INCOMPLETE\n"
         "  exit 3 = evidence absent / unreadable / retry without canonical\n"
         "  exit 5 = bad flags\n")


def main(argv):
    operation = False
    as_json = False
    target = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--legs":
            operation = True
            if index + 1 < len(argv) and not argv[index + 1].startswith("-"):
                target = argv[index + 1]
                if target == "all":
                    target = None
                index += 1
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_FRTL_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write("E_FRTL_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        else:
            target = arg
        index += 1
    if not operation:
        sys.stdout.write("E_FRTL_BAD_ARGS: --legs is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = history(root, "qa", target)
    except FollowupRetryError as exc:
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