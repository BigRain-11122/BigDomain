"""state_close_R2361 - the closeout of the R2361 product window.

Appends this window's own honest lines to src/os/state.json, bumps the tick and
records the decisions baseline this window measured. Dry run by default; on
--execute the file is written once and read back.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")

TICK = 2361
DEC_ROWS = 149

LINES = [
    "R2361 five-still gate: the evolution ledger carries no @BigDomain row, the "
    "content-addressed decisions diff read 0 new tokens over 149 rows, git "
    "status was empty and no index.lock existed, so the window pulled live "
    "work instead of declaring idle - queue_head read tech "
    "state/queue/tech.md:403 prefix AC-SGS1 (claimable=11) and explore line 3 "
    "prefix AC-SRFM1 (claimable=10).",

    "R2361 product face shipped: src/os/stamp_exempt_seed_guard_wire.py plus "
    "src/os/test_stamp_exempt_seed_guard_wire.py, AC-SGS1..AC-SGS6 pinned in "
    "that tech row at R2346 BEFORE the code and re-anchored this window (git "
    "grep -F at HEAD found the six names only in prose, zero executable "
    "occupancy). The seed generator stamp_exempt_seed_R2280.py now routes "
    "through the wire instead of one io.open(path, 'w'), so all three writers "
    "of state/queue/stamp_exempt.json ask the same pinned-text guard.",

    "R2361 evidence: SUITE RESULT passes=6 fails=0 criteria=6 on two runs that "
    "are byte-identical (qa/stamp-exempt-seed-guard-wire-R2361-a.log / -b.log, "
    "sha16 423471e4cfba0153), five adjacent stamp-exempt suites green "
    "(guard/append/prune/review/queue_done_stamp_exempt), wired "
    "os-stamp-exempt-seed-guard-wire(6) in src/sandbox/reconcile_all.py, and "
    "the live dry run on this repo planned entries=381->381 before=79026B "
    "after=78976B pin=397D3C1C71E149DB with nothing written "
    "(qa/stamp-exempt-seed-guard-wire-live-R2361.log).",

    "R2361 honest disclosures: (a) NO reconcile battery ran this window - the "
    "tree was about to change by design, so the battery belongs to the "
    "committed head and the register row reconcile-battery-R2361 was closed "
    "with reconcile-battery-R2362 opened first=yes, expecting +1 suite / +6 "
    "criteria (490 / 3916) against the R2360 reading of 489 / 3910 measured at "
    "that head rather than predicted. (b) The done-stamp gate still reads "
    "381 violations (DONE-STAMP-DEBT), the same count the live plan reported "
    "BEFORE the tech row was stamped, so this window added no new debt and "
    "cleared none. (c) tasks.md was left untouched: its on-disk encoding is not "
    "plain UTF-8 and a blind rewrite could corrupt the canonical board "
    "(disclosed, not silently skipped). (d) The live plan discloses a 50-byte "
    "shrink it would apply (79026B -> 78976B) because the on-disk note differs "
    "from the rendered one; no --execute was run this window, so the "
    "declaration is unchanged. (e) BigDomain-OSLoop still reads "
    "LogonType=InteractiveToken and needs an elevated shell (carried as "
    "loop-s4u-reconcile in state/debt.md).",

    "R2361 tokens: local=~14k api=0 api_reason=product window - one product "
    "module and its six-criteria suite written to criteria pinned two rounds "
    "earlier, one anchor check at HEAD, two suite runs plus five adjacent "
    "suites, one live dry-run plan, one runner wiring line, one queue row "
    "stamped, two register writes through their own writers, and the "
    "state/export/heartbeat/board closeout; zero cloud calls.",
]


def main(argv):
    execute = "--execute" in argv
    with io.open(STATE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    before = len(json.dumps(data, ensure_ascii=False))
    data["tick"] = TICK
    data["last_decision_rows"] = DEC_ROWS
    data["log"].extend(LINES)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(text)
    print("STATE tick=%d log=%d decisions_rows=%d"
          % (data["tick"], len(data["log"]), data["last_decision_rows"]))
    print("STATE bytes=%d (was ~%d)" % (len(text.encode("utf-8")), before))
    if not execute:
        print("DRY RUN: pass --execute to write")
        return 0
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(STATE, "r", encoding="utf-8") as handle:
        back = json.load(handle)
    ok = back["tick"] == TICK and back["log"][-1] == LINES[-1]
    print("READBACK ok=%s" % ok)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))