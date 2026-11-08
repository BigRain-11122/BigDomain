"""R2567 closeout: queue row discharge, backlog row, heartbeat."""
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))

QUEUE = os.path.join(ROOT, "state", "queue", "tech.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

SEED = "- [ ] P2 tech seed (R2548, from this window own measured limit): `src/os/state_fold_run.py`"
ROW = ("- [x] [done 2026-11-08 R2567] " + SEED[6:] + "\n"
       " DISCHARGED R2567 (AC-SFOLD1..AC-SFOLD6 pinned in that row at R2548 "
       "BEFORE any code): src/os/state_fold_run.py + src/os/test_state_fold_run.py "
       "shipped. The fold is now a runnable face over the shipped predicate, "
       "append and waterline read (imported, not copied): it refuses a "
       "token-missing window, a round-split cut, a live block under 30 lines, "
       "a fold that would leave the file over the gate, and a file whose items "
       "disagree about their own indent; it proves the archive copy is "
       "byte-equal line by line, proves the ledger coverage reader still sees "
       "every round it saw before THROUGH the archive, proves the layout "
       "writer and the fold reader agree about the same file, and reports "
       "ALREADY-FOLDED with zero bytes on a re-run. AC-SFOLD4 closed the "
       "R2522 layout defect at its birth site: state_fold.split_layout now "
       "derives the item indent from the file instead of insisting on 16 "
       "spaces, so the REAL state.json is foldable. PROOF: SUITE PASS 6/6 "
       "TWICE with an identical body and five adjacent suites green through "
       "the shipped evidence capture (qa/state-fold-run-R2567.log, 2353B, "
       "legs=2 identical=True adjacent=5 fails=0); state_fold suite re-ran "
       "6/6 after the repair. LIVE: real state.json 327622B -> 71125B, gate "
       "78500, margin 7375, 247 -> 56 live log lines, 192 lines appended "
       "verbatim to logs/state-log-archive-2026-11.md (257082B, every line "
       "byte-equal, 124 tokens preserved), ledger coverage 1368 -> 1369 "
       "rounds, FOLD-CLEAR, pre-op bytes at logs/state-preop-R2567.bak "
       "(qa/state-fold-live-R2567.log). Wired os-state-fold-run(6) -> registry "
       "613 suites / 4654 criteria; the next window owes a full battery "
       "(reconcile-battery-R2567 first=yes).\n")

BACKLOG_ROW = (
    "- [x] [done 2026-11-08 R2567] product face: the fold face "
    "(src/os/state_fold_run.py, AC-SFOLD1..AC-SFOLD6) plus the birth-site "
    "repair of the R2522 layout defect in state_fold.split_layout; the live "
    "fold took state.json 327622B -> 71125B (FOLD-CLEAR, margin 7375) with a "
    "verbatim 257082B archive block. Registry 613/4654; next window = full "
    "battery.\n")


def main():
    text = io.open(QUEUE, encoding="utf-8").read()
    assert text.count(SEED) == 1, text.count(SEED)
    io.open(QUEUE, "w", encoding="utf-8", newline="\n").write(
        text.replace(SEED, ROW))
    backlog = io.open(BACKLOG, encoding="utf-8").read()
    io.open(BACKLOG, "w", encoding="utf-8", newline="\n").write(
        BACKLOG_ROW + backlog)
    io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n").write(
        "2026-11-08T15:52+08:00 R2567 product: fold face shipped, live fold "
        "327622B -> 71125B FOLD-CLEAR, registry 613/4654, next = battery "
        "reconcile-battery-R2567\n")
    print("closeout rows written")
    return 0


if __name__ == "__main__":
    sys.exit(main())