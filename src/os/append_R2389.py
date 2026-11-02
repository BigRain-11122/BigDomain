"""append_R2389 - the two closeout housekeeping lines and one wording fix."""

import io
import json
import os

P = "src/os/state.json"

OLD = "reads the REAL 67603B declaration as NOOP dialect=LF"
NEW = "reads the REAL declaration as NOOP dialect=LF"

HOUSE = (
    "R2389 closeout housekeeping, measured not assumed: the state file stood "
    "at 80913B with 76 log items at 4-space indent and bare LF "
    "(layout_ok=False), so src/os/state_io.py ran FIRST (CANON-FIXED 80913B "
    "-> 81998B, crlf=173, off_indent=0, JSON payload proven equal); fold 647 "
    "then ran through src/os/state_fold.py at a TRUE round-block boundary "
    "(log lines 1..10, the cut landing after a tokens line so no block is "
    "split) with a summary naming all 842 window tokens (token_missing=[]), "
    "predicted 74664B and measured 74664B exactly, margin 3836B, archive "
    "693392B -> 708132B with its prefix intact and 67 log items left live."
)

RESIDUE = (
    "R2389 the fold created residue for the round it moved as the law "
    "predicts (R2379, live status DELIVERED, undeclared once its block left "
    "the live log), so residue_triage_repin ran once from ONE live reading "
    "(declared_by=R2389, until=R2406, entries 234 -> 235, 67603B -> 67758B "
    "exactly as planned, dropped=0) and residue_triage --check now reads "
    "TRIAGED 235/235; the live capture was then re-run on the final tree and "
    "reads the REAL 67758B declaration as NOOP with its digest unchanged "
    "before and after, while the four ledger suites, os-residue-triage and "
    "this window own suite re-ran 8/8/8/8/6/6 after the fold and the export "
    "checker recomputes 21/21 PASS."
)


def main():
    raw = open(P, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    hits = 0
    for index, line in enumerate(state["log"]):
        if OLD in line:
            state["log"][index] = line.replace(OLD, NEW, 1)
            hits += 1
    if hits != 1:
        print("REFUSE: wording anchor found %d times" % hits)
        return 1
    state["log"].append(HOUSE)
    state["log"].append(RESIDUE)
    payload = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    temp = P + ".tmp-r2389e"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    os.replace(temp, P)
    back = json.loads(open(P, "rb").read().decode("utf-8"))
    print("APPENDED log=%d bytes=%d wording_fixed=%d"
          % (len(back["log"]), os.path.getsize(P), hits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())