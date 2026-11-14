"""state_append_R2735 - record the R2735 monitored-wait window in state.json.

Every number below was read in this window: the leg pid 65136 through a
SYNCHRONIZE kernel probe with child 61448, the stream at 580029 bytes with
331 PASS suite rows and zero FAIL rows, the duration accounting over those 331
rows, the apimarket remainder counted against the registry by import, and the
five-silence readings plus the debt gate, queue head and queue floor.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")
sys.path.insert(0, BASE)

import state_io  # noqa: E402

ITEMS = [
    "2026-11-14 R2735 MONITORED-WAIT window on the live reconcile-battery-R2733 leg, ZERO product bytes by the R2168 mixed-tree rule. Five readings at open: git status EMPTY at HEAD 7501e872 equal to origin/main with no index.lock; ZERO @BigDomain rows in the group evolution ledger (atbd_rows=0); the content-addressed decisions face read tokens_total 67 against the carried 266-token baseline with new=0, so no decision row was executed; no new group order against the carried 2026-11-14 01:3x baseline and the local orders.md tail is still the 2026-09-28 rows; benchmarks_refreshed 2026-11-14 inside the seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2733 first=1 open=36, queue_head read tech line=703 prefix AC-DFOB1 claimable=11, and queue_floor read FLOOR-MET main 5/5 tech 11/10 explore 10/10 shortfall=0 - so the tech SHORT 1 R2734 carried is no longer short and no floor fill was owed here.",
    "R2735 THE LEG WAS READ AS ALIVE BY KERNEL PROBE AND NOT BY REPUTATION: OpenProcess SYNCHRONIZE on pid 65136 succeeded and WaitForSingleObject returned 258 (WAIT_TIMEOUT, i.e. still running), with child 61448 python.exe holding the current suite, and the stream read 580029 bytes / 3963 lines / 331 PASS suite rows / ZERO FAIL rows at 20:40:36. Nothing was relaunched, no evidence path was touched and no verdict was issued, because a killed leg is not a red one and an unfinished leg is not a green one.",
    "R2735 WHY THIS WINDOW DID NOT ADOPT, stated as measurement rather than patience: the 331 completed rows carry 1864.2s of suite time in total (mean 5.6s, tail-20 mean 31.0s), and the heavy block still to come was counted against the registry BY IMPORT - 140 ledger-apimarket suites exist, 121 are done and 19 remain, each measured at 89-272s in this very stream (activity 89.5s, reportdossier 156.2s, buyerhistory 272.3s). Nineteen heavy rows plus 325 light ones put the honest ETA at roughly 80-110 minutes, i.e. about 22:00-22:30, which is OUTSIDE this 25 minute window. The projection is arithmetic on this leg own bytes, not a promise, and the stream was also observed holding at 331 rows for over four minutes while one heavy suite ran - the same tail behaviour R2732 measured at 150-300s per suite.",
    "R2735 ONE REAL HAZARD WAS REPAIRED IN THE INSTRUCTION CHAIN, which is the only thing this window changed on disk besides its own accounting: src/os/backlog.md line 1 still read 'next window: THE BATTERY ... owed BEFORE any product byte' although R2734 had ALREADY launched that battery at pid 65136, so a next window trusting the board would have re-measured the target and could have double-fired a leg - the exact failure the launcher own pid guard exists to refuse. That line is now stamped launched with its pid and KEPT for the launch discipline it prescribes, and a new top line names the ADOPTION step with the measured projection, the closing-line precondition, the seven-axis byte measurement, the R2614 write-sensitive receipt on the final committed tree, the designed follow-up order and the queue head AC-DFOB1 that follows it.",
    "R2735 WHAT THIS WINDOW DID NOT DO, by law and by choice: (a) no product src byte, no registry row, no queue row and no matrix stamp moved while the leg runs, because the write-sensitive set would then be measured on a tree the battery never saw; (b) the R2731 dead per-round export hook in src/os/export_R2431.py is STILL OWED and now overdue by FOUR windows, and it is product src so it waits for a non-battery window - it is carried on the new board line rather than dropped; (c) no debt row was closed and none was opened, because nothing landed that a discharge note could honestly cite; (d) the 36 open debt rows were not re-swept, since R2732 already swept them by a three-part verification rule and a second blind sweep would be the fourth idle form.",
    "R2735 honest score by the Executive Protocol scale: ZERO product points. The CEO can newly open the live stream logs/battery-R2733.stream and the corrected board line, which are progress evidence and an instruction repair rather than a product. Every P-47 business face still waits on CEO physical pieces (merchant id, mini-program appid/secret), and the AC-* tech queue this company keeps feeding is named as a treadmill in the open proposal BD-PROP-009 rather than passed off as product.",
    "R2735 tokens: local=~7k api=0 api_reason=monitored-wait window - one five-silence scan with the debt gate, queue head and queue floor, one kernel liveness probe with a child read, three stream samples with a duration accounting over 331 rows, one apimarket remainder count against the registry by import, one board-line repair for a real double-fire hazard, one export driver and one state append through the shipped writers, and the closeout commit; zero cloud calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(STATE))
    data = json.loads(text)
    data["tick"] = int(data.get("tick", 0)) + 1
    log = data.get("log") or []
    log.extend(ITEMS)
    data["log"] = log
    new_text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    new_text = state_io.canon(new_text)
    temp = STATE + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as sink:
        sink.write(new_text)
    os.replace(temp, STATE)
    back = json.loads(state_io.decode(state_io.read_raw(STATE)))
    ok = back["tick"] == data["tick"] and back["log"] == data["log"]
    print("TICK %s LINES %d OK %s LAST %s"
          % (back["tick"], len(back["log"]), ok, back["log"][-1][:60]))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
