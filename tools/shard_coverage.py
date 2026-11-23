"""shard_coverage - which battery suites a shard leg has ever measured (R3345).

AC-SHC1..AC-SHC6 were pinned in src/os/backlog.md BEFORE this file existed.

Why this exists: "the full 762-row battery has never been run" is carried as a
sentence, while ninety shard legs already sit in qa/. Nothing could say WHICH
suites those legs measured, whether they were green, or how old the newest
reading is, so every window picked a family from memory and the debt stayed
structurally permanent. This tool turns that memory into a reading:

  - the suite set comes from the battery registry itself (AC-SHC1), never a
    copied list, and labels found only in evidence are reported as orphans;
  - a suite counts as measured only when a "SHARD row <label> rc=<n>" line
    exists (AC-SHC2) - a "SHARD selected" or "SHARD detail" mention is not a
    reading;
  - rc=0 is green and rc!=0 is red, both measured, and red is never folded
    into green (AC-SHC3);
  - the newest reading is chosen by the ROUND NUMBER parsed from the evidence
    file name (AC-SHC4), so mtime cannot move the answer;
  - the verdict is about coverage only: UNCOVERED or COVERED-ALL (AC-SHC5);
  - the tool writes nothing and reads no clock (AC-SHC6).

A shard is not a battery. This tool can never claim battery coverage; it only
says which registry rows have at least one measured shard reading.

Source discipline: pure ASCII, stdlib only, no clock, no network, no writes.
"""
import argparse
import glob
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_REL = os.path.join("src", "sandbox", "reconcile_all.py")
DEFAULT_EVIDENCE = os.path.join(ROOT, "qa")
SHARD_GLOB = "battery-shard-*.log"
ROW = re.compile(r"(?m)^SHARD row (\S+) rc=(-?\d+)")
ROUND = re.compile(r"R(\d+)")


class Refuse(Exception):
    """A named refusal that must reach the caller as rc=3."""


def registry_rows(registry_path=None):
    """AC-SHC1: (label, criteria) pairs read from the battery registry.

    The registry module is executed the way tools/battery_shard.py executes it,
    so the label set is the battery's own and a suite removed from the battery
    disappears from this reading as well.
    """
    path = registry_path or os.path.join(ROOT, REGISTRY_REL)
    if not os.path.exists(path):
        raise Refuse("E_REGISTRY_MISSING %s" % path)
    spec = importlib.util.spec_from_file_location("_shc_registry", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        rows = getattr(module, "SUITES")
    except Exception as exc:  # noqa: BLE001 - any failure is an unreadable registry
        raise Refuse("E_REGISTRY_UNREADABLE %s: %s" % (os.path.basename(path), exc))
    out = []
    for row in rows:
        try:
            label, rel, criteria = row[0], row[1], int(row[2])
        except (TypeError, ValueError, IndexError):
            raise Refuse("E_REGISTRY_ROW %r" % (row,))
        out.append((label, criteria))
    return out


def round_of(name):
    """AC-SHC4: the newest round number named in an evidence file name.

    A file with no R<digits> token is round 0, which is honest: the leg did not
    say when it ran, so it loses every comparison to a dated leg.
    """
    found = [int(m.group(1)) for m in ROUND.finditer(os.path.basename(str(name)))]
    return max(found) if found else 0


def scan(evidence_dir):
    """AC-SHC2/AC-SHC4: label -> newest measured reading from row lines only."""
    if not os.path.isdir(evidence_dir):
        raise Refuse("E_EVIDENCE_DIR %s" % evidence_dir)
    logs = sorted(glob.glob(os.path.join(evidence_dir, SHARD_GLOB)))
    measured = {}
    for path in logs:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            continue
        rnd = round_of(path)
        for label, rc in ROW.findall(text):
            rc = int(rc)
            current = measured.get(label)
            if current is None:
                measured[label] = {"round": rnd, "rc": rc, "readings": 1}
                continue
            current["readings"] += 1
            newer = rnd > current["round"]
            same_round_green = (rnd == current["round"] and rc == 0
                                and current["rc"] != 0)
            if newer or same_round_green:
                current["round"] = rnd
                current["rc"] = rc
    return logs, measured


def report(rows, evidence_dir, stale_before=0):
    """AC-SHC5: coverage, rc split, orphans and staleness as one reading."""
    logs, measured = scan(evidence_dir)
    labels = [label for label, _crit in rows]
    known = set(labels)
    covered, green, red, stale = [], [], [], []
    for label, criteria in rows:
        reading = measured.get(label)
        if reading is None:
            continue
        covered.append(label)
        if reading["rc"] == 0:
            green.append(label)
        else:
            red.append(label)
        if stale_before and reading["round"] < int(stale_before):
            stale.append(label)
    uncovered = [(label, criteria) for label, criteria in rows if label not in covered]
    orphans = sorted(label for label in measured if label not in known)
    return {
        "evidence_logs": len(logs),
        "registry_suites": len(rows),
        "registry_criteria": sum(criteria for _label, criteria in rows),
        "measured_labels": len(measured),
        "covered": len(covered),
        "green": len(green),
        "red": len(red),
        "uncovered": len(uncovered),
        "uncovered_criteria": sum(criteria for _label, criteria in uncovered),
        "uncovered_labels": sorted(label for label, _criteria in uncovered),
        "orphan_labels": orphans,
        "stale_before": int(stale_before),
        "stale": len(stale),
        "stale_labels": sorted(stale),
        "verdict": "COVERED-ALL" if not uncovered else "UNCOVERED",
    }


def render_text(result, rows_by_label):
    """The human reading; families are grouped so a new leg can pick one."""
    out = []
    out.append("SHARD-COVERAGE evidence=%d registry=%d suites/%d criteria "
               "measured=%d covered=%d green=%d red=%d uncovered=%d "
               "uncovered_criteria=%d orphan=%d stale=%d verdict=%s"
               % (result["evidence_logs"], result["registry_suites"],
                  result["registry_criteria"], result["measured_labels"],
                  result["covered"], result["green"], result["red"],
                  result["uncovered"], result["uncovered_criteria"],
                  len(result["orphan_labels"]), result["stale"],
                  result["verdict"]))
    if result["orphan_labels"]:
        out.append("SHARD-COVERAGE orphans %s"
                   % ",".join(result["orphan_labels"]))
    if result["stale"]:
        out.append("SHARD-COVERAGE stale_before=R%d %s"
                   % (result["stale_before"], ",".join(result["stale_labels"])))
    if result["uncovered_labels"]:
        families = {}
        for label in result["uncovered_labels"]:
            families.setdefault(label.split("-")[0], []).append(label)
        for key in sorted(families):
            out.append("SHARD-COVERAGE family %s uncovered=%d criteria=%d %s"
                       % (key, len(families[key]),
                          sum(rows_by_label.get(l, 0) for l in families[key]),
                          ",".join(families[key])))
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--evidence-dir", default=DEFAULT_EVIDENCE)
    parser.add_argument("--registry", default="")
    parser.add_argument("--stale-before", type=int, default=0,
                        help="round number; covered rows measured earlier are named stale")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        rows = registry_rows(args.registry or None)
        result = report(rows, args.evidence_dir, args.stale_before)
    except Refuse as exc:
        print(str(exc))
        return 3
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_text(result, {label: criteria for label, criteria in rows}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
