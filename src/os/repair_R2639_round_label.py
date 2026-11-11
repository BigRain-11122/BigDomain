"""Birth-site repair for the R2638 verification window round label (R2639).

The R2637 verification window wrote its tokens ledger line labelled R2638
because it used the TICK instead of the window. The R2638 product window then
wrote its own R2638 tokens line, so state.json carried TWO ledger entries for
round 2638 and the shipped closing station refused the live log with
E_LGN_NOT_MONOTONIC ("round 2638 is not newer than the settled round 2638").

The repair relabels that one line to the shipped same-round second-window form
"R2637 second-half tokens:" - the form already present in this log for R2635 -
which is honest about the round it belongs to and deliberately does NOT parse
as a ledger entry, so the one-entry-per-round law holds.

Byte-level, one label, nothing else touched. --check reports the plan and
writes nothing; --execute writes atomically with a read-back. Idempotent.
Stdlib only, pure ASCII, zero network.
"""

import argparse
import io
import os
import sys

STATE = os.path.join("src", "os", "state.json")
OLD = b'"R2638 tokens: local=~9k api=0 api_reason=verification window'
NEW = b'"R2637 second-half tokens: local=~9k api=0 api_reason=verification window'


def plan(path=STATE):
    with io.open(path, "rb") as handle:
        raw = handle.read()
    old_count = raw.count(OLD)
    new_count = raw.count(NEW)
    if old_count == 0 and new_count == 1:
        return {"state": "ALREADY", "before": len(raw), "after": len(raw),
                "delta": 0, "old": 0, "new": new_count}
    if old_count != 1:
        raise SystemExit("E_RLBL_COUNT old=%d (expected exactly 1)" % old_count)
    after = raw.replace(OLD, NEW)
    if len(after) - len(raw) != len(NEW) - len(OLD):
        raise SystemExit("E_RLBL_DELTA")
    return {"state": "PLANNED", "before": len(raw), "after": len(after),
            "delta": len(after) - len(raw), "old": old_count, "new": new_count}


def execute(path=STATE):
    info = plan(path)
    if info["state"] == "ALREADY":
        print("REPAIR ALREADY %s bytes=%d" % (path, info["before"]))
        return 0
    with io.open(path, "rb") as handle:
        raw = handle.read()
    after = raw.replace(OLD, NEW)
    tmp = path + ".r2639.tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(after)
    with io.open(tmp, "rb") as handle:
        check = handle.read()
    if check != after:
        os.remove(tmp)
        raise SystemExit("E_RLBL_READBACK")
    os.replace(tmp, path)
    with io.open(path, "rb") as handle:
        landed = handle.read()
    if landed != after:
        raise SystemExit("E_RLBL_LANDED before=%d after=%d"
                         % (info["before"], len(landed)))
    print("REPAIR %s bytes=%d -> %d delta=%+d readback=ok"
          % (path, info["before"], len(landed), len(landed) - info["before"]))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        info = plan()
        print("PLAN %s before=%d after=%d delta=%+d"
              % (info["state"], info["before"], info["after"], info["delta"]))
        return 0 if info["state"] == "ALREADY" else 0
    if args.execute:
        return execute()
    parser.print_usage()
    return 2


if __name__ == "__main__":
    sys.exit(main())
