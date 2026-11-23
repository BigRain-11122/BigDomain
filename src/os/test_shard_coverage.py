"""AC-SHC1..AC-SHC6 for tools/shard_coverage.py (R3345).

The criteria were pinned in src/os/backlog.md BEFORE this suite or the tool
existed. Every arm builds its own evidence corpus inside a private temp dir and
asks the shipped functions, so nothing here can pass on live-tree state.

Pure ASCII, stdlib only, no network, no clock, no writes outside the temp dir.
"""
import contextlib
import importlib.util
import io
import os
import shutil
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL_REL = os.path.join(ROOT, "tools", "shard_coverage.py")
REGISTRY_REL = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")

FAILS = []


def check(name, ok, detail):
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILS.append(name)


def load(path, alias):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_log(directory, name, text):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


def main():
    tool = load(TOOL_REL, "_shc_tool")
    registry = load(REGISTRY_REL, "_shc_registry")
    source = open(TOOL_REL, "r", encoding="utf-8").read()
    rows = tool.registry_rows()
    labels = [label for label, _crit in rows]
    by_label = dict(rows)
    registry_labels = [row[0] for row in registry.SUITES]

    # AC-SHC1: the suite set is the battery's own, in both directions.
    same_set = sorted(labels) == sorted(registry_labels)
    same_crit = all(by_label[label] == int(dict(
        (r[0], r[2]) for r in registry.SUITES)[label]) for label in labels)
    tmp = tempfile.mkdtemp(prefix="shc-")
    try:
        write_log(tmp, "battery-shard-orphan-R3300.log",
                  "SHARD row ghost-label-not-in-registry rc=0\n")
        orphan = tool.report(rows, tmp)
        check("AC-SHC1", same_set and same_crit
              and "reconcile_all.py" in source
              and orphan["orphan_labels"] == ["ghost-label-not-in-registry"]
              and orphan["covered"] == 0,
              "registry=%d same_set=%s same_crit=%s orphans=%s covered=%d"
              % (len(rows), same_set, same_crit,
                 ",".join(orphan["orphan_labels"]), orphan["covered"]))

        # AC-SHC2: only a SHARD row line is a measurement.
        target = labels[0]
        corpus = os.path.join(tmp, "rowlaw")
        os.makedirs(corpus)
        write_log(corpus, "battery-shard-a-R3300.log",
                  "SHARD selected %s crit=1 path=x\n"
                  "SHARD detail %s PASS something\n"
                  "SUITE PASS 3/3\n" % (target, target))
        before = tool.report(rows, corpus)
        write_log(corpus, "battery-shard-b-R3301.log",
                  "SHARD row %s rc=0\n" % target)
        after = tool.report(rows, corpus)
        check("AC-SHC2", target in before["uncovered_labels"]
              and target not in after["uncovered_labels"]
              and before["covered"] == 0 and after["covered"] == 1,
              "label=%s mentions_only_covered=%d row_covered=%d"
              % (target, before["covered"], after["covered"]))

        # AC-SHC3: rc=0 is green, rc!=0 is red, red is never green.
        split = os.path.join(tmp, "split")
        os.makedirs(split)
        green_label, red_label = labels[1], labels[2]
        write_log(split, "battery-shard-split-R3300.log",
                  "SHARD row %s rc=0\nSHARD row %s rc=2\n"
                  % (green_label, red_label))
        split_result = tool.report(rows, split)
        check("AC-SHC3", split_result["green"] == 1 and split_result["red"] == 1
              and split_result["covered"] == 2
              and split_result["uncovered"] == len(rows) - 2,
              "green=%d red=%d covered=%d uncovered=%d"
              % (split_result["green"], split_result["red"],
                 split_result["covered"], split_result["uncovered"]))

        # AC-SHC4: the newest reading follows the round in the name, not mtime.
        rounds = os.path.join(tmp, "rounds")
        os.makedirs(rounds)
        old = write_log(rounds, "battery-shard-old-R2900.log",
                        "SHARD row %s rc=2\n" % red_label)
        write_log(rounds, "battery-shard-new-R3300.log",
                  "SHARD row %s rc=0\n" % red_label)
        os.utime(old, (4102444800, 4102444800))
        measured = tool.scan(rounds)[1]
        round_result = tool.report(rows, rounds)
        check("AC-SHC4", measured[red_label]["round"] == 3300
              and measured[red_label]["rc"] == 0
              and round_result["red"] == 0 and round_result["green"] == 1
              and tool.round_of("battery-shard-x-R2799-leg2.log") == 2799
              and tool.round_of("battery-shard-nameless.log") == 0,
              "newest_round=%d rc=%d red=%d nameless_round=%d"
              % (measured[red_label]["round"], measured[red_label]["rc"],
                 round_result["red"], tool.round_of("battery-shard-nameless.log")))

        # AC-SHC5: both ends of the verdict, plus the two refusal codes.
        empty = os.path.join(tmp, "empty")
        os.makedirs(empty)
        empty_result = tool.report(rows, empty)
        full = os.path.join(tmp, "full")
        os.makedirs(full)
        write_log(full, "battery-shard-full-R3300.log", "".join(
            "SHARD row %s rc=0\n" % label for label in labels))
        full_result = tool.report(rows, full)
        missing_dir = tool.main(["--evidence-dir", os.path.join(tmp, "nope")])
        refused_registry = tool.main(
            ["--registry", os.path.join(tmp, "no-registry.py")])
        check("AC-SHC5", empty_result["covered"] == 0
              and empty_result["uncovered"] == len(rows)
              and empty_result["verdict"] == "UNCOVERED"
              and full_result["uncovered"] == 0
              and full_result["verdict"] == "COVERED-ALL"
              and missing_dir == 3 and refused_registry == 3,
              "empty=%s full=%s rc_missing=%d rc_registry=%d"
              % (empty_result["verdict"], full_result["verdict"],
                 missing_dir, refused_registry))

        # AC-SHC6: the reading writes nothing and its json is byte-stable.
        stable = os.path.join(tmp, "stable")
        os.makedirs(stable)
        write_log(stable, "battery-shard-s-R3300.log",
                  "SHARD row %s rc=0\n" % labels[3])
        listing_before = sorted(os.listdir(stable))
        runs = []
        for _ in range(2):
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                rc = tool.main(["--json", "--evidence-dir", stable])
            runs.append((rc, buffer.getvalue()))
        listing_after = sorted(os.listdir(stable))
        no_clock = "import time" not in source and "time." not in source
        no_write = ("open(" in source
                    and source.count('open(path, "r"') == source.count("open(")
                    and "makedirs" not in source and "remove(" not in source)
        check("AC-SHC6", runs[0][0] == 0 and runs[1][0] == 0
              and runs[0][1] == runs[1][1]
              and listing_before == listing_after
              and no_clock and no_write,
              "json_bytes=%d identical=%s dir_unchanged=%s no_clock=%s "
              "no_write=%s"
              % (len(runs[0][1]), runs[0][1] == runs[1][1],
                 listing_before == listing_after, no_clock, no_write))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    criteria = 6
    passed = criteria - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s" % (passed, criteria, ",".join(FAILS)))
        return 1
    print("SUITE PASS %d/%d" % (criteria, criteria))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
