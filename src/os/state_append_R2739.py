"""state_append_R2739 - append this window's log lines through the canonical writer.

R2738 added state_io.write_document() precisely because rounds reached for a
bare json.dump and produced the one-line minified state that made the R2737
leg red. This closeout therefore WRITES THROUGH THAT WRITER rather than
around it, so the fix has at least one real consumer.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-14 R2739 SETTLEMENT window on the R2737 leg: it CLOSED RED and "
    "was NOT adopted green. Five readings at open: git status EMPTY at HEAD "
    "ddc3d6ea equal to origin/main with no index.lock; ZERO @BigDomain rows in "
    "the group ledger; the content-addressed decisions face read cur=67 "
    "base=267 new=0; the group orders tail is the carried 2026-11-14 01:3x row "
    "already knowledge-only; benchmarks_refreshed 2026-11-14 inside the "
    "seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2733 "
    "open=36, queue_head read tech line=703 prefix AC-DFOB1 claimable=11, "
    "queue_floor read FLOOR-MET main 5/5 tech 11/10 explore 10/10 shortfall=0.",

    "R2739 THE LEG WAS MEASURED ON ITS OWN BYTES AND THE READING IS RED, not "
    "adopted: qa/reconcile-all-R2737.log reads 1249289B, utf-8, bom=False, "
    "crlf=0, lone_cr=0, nul=0, 671 PASS suite rows with 671 unique names, FOUR "
    "FAIL rows, an independent criteria recount of 5000 against the expected "
    "5026, and the tail reads RUNNER FAIL (5 failed assertions) plus BATTERY "
    "rc=1 3963.7s. The four red rows are os-state-io, "
    "os-status-export-writer-dialect-wire, os-queue-floor-export-face and "
    "os-export-consistency-queue-face - EXACTLY the four whose birth sites "
    "R2738 repaired MID-LEG and then re-ran green on the repaired live tree "
    "(8/8, 6/6, 6/6, 15/15). A red row repaired mid-leg is not evidence about "
    "the repaired tree, so the settlement is: the leg is RED, its four reds "
    "are explained and re-proven elsewhere, and R2738 moved product src "
    "(src/os/state_io.py), so the R2168 mixed-tree rule owes a FULL battery on "
    "the committed tree.",

    "R2739 THE SUCCESSOR LEG WAS LAUNCHED ON THE CLEAN COMMITTED TREE at HEAD "
    "ddc3d6ea: the target was re-measured BY IMPORT at 675 suites / 5026 "
    "criteria / 675 names / 675 paths, byte for byte the pre-registration, no "
    "battery_stream or reconcile_all process was alive, the evidence path "
    "qa/reconcile-all-R2739.log was absent, and src/os/launch_battery_R2739.py "
    "was committed BEFORE the fire so the leg runs on a committed tree. "
    "LAUNCHED pid=64724 writing logs/battery-R2739.stream with the "
    "single-writer evidence landing only at completion; the negative control "
    "fired the launcher a second time and read E_LAUNCH_PID_EXISTS pid=64724 "
    "at rc=2, so a leg cannot be double-fired over the file it is already "
    "writing. At open+45s the stream read 15735B with 4 PASS suite rows and "
    "ZERO FAIL rows.",

    "R2739 ONE REAL DEFECT WAS MEASURED READ-ONLY WHILE THE LEG RAN, and it is "
    "the recurrence risk behind those four red rows: of 474 state-writing "
    "scripts in src/os, exactly ONE consumes the canonical writer R2738 added "
    "(write_document or write_canon), EIGHT still write with a bare "
    "json.dump, and 464 use neither - so the one-line minification that made "
    "the R2737 leg red is still reachable from eight live call sites. Nothing "
    "was repaired here because product src is frozen by the mixed-tree rule "
    "until this battery is green; the finding and its criteria are pinned on "
    "the board line for the first non-battery product window.",

    "R2739 honest score by the Executive Protocol scale: ZERO product points "
    "- a red leg settled, a successor launched, a defect quantified and a "
    "board line written are evidence and instruction, not something a CEO can "
    "newly open. Every P-47 business face still waits on CEO physical pieces "
    "(merchant id, mini-program appid/secret); the AC-* tech queue this "
    "company keeps feeding is named a treadmill in BD-PROP-009 rather than "
    "passed off as product; tasks.md was not touched, it is the P-47 canonical "
    "board; Docker is absent on this host; and BigDomain-OSLoop still reads "
    "InteractiveToken with the ELEVATED-shell repair carried as ceo-pending "
    "physical item loop-s4u-reconcile.",

    "R2739 tokens: local=~11k api=0 api_reason=settlement and launch window - "
    "one five-silence scan with the debt gate, the queue head and the queue "
    "floor, one legacy status read plus a byte-level settlement measurement "
    "with an independent criteria recount, one registry count by import on "
    "four axes, one launcher committed then fired with its negative control, "
    "one stream sample, one read-only 474-file writer census, one export "
    "driver through the shipped canonical caliber, and the state/export "
    "closeout; zero cloud calls and zero external API touches",
]


def main():
    raw = state_io.read_raw(STATE)
    data = state_io.parse(state_io.decode(raw))
    before = len(data["log"])
    data["log"].extend(LINES)
    data["tick"] = 2739
    state_io.write_document(STATE, data)
    back = json.load(io.open(STATE, encoding="utf-8"))
    ok = (back.get("tick") == 2739
          and len(back.get("log") or []) == before + len(LINES)
          and back["log"][-len(LINES):] == LINES)
    sys.stdout.write("APPENDED tick=%s log %d->%d ok=%s\n"
                     % (back.get("tick"), before, len(back.get("log") or []),
                        ok))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
