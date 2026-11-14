"""state_append_R2734 - record the R2734 verification window in state.json.

Every number below was read in this window: the battery target by import at
675 suites / 5026 criteria / 675 unique names / 675 unique paths, the launch
pid 65136, the stream growing to 15735 bytes with PASS rows and zero FAIL
rows, the five-silence readings, and the queue floor at tech SHORT 1.
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
    "2026-11-14 R2734 VERIFICATION window on the debt gate first item (reconcile-battery-R2733, pre-registered 675 suites / 5026 criteria at R2733), ZERO product bytes by the R2168 mixed-tree rule. Five readings at open: git status EMPTY at HEAD 92516273 with no index.lock; ZERO @BigDomain rows in the group ledger (atbd_lines=0 unreplied=0); the content-addressed decisions face read new=0 (rows 131, tokens 67 against the carried baseline) so no row was executed; the group orders tail is the 2026-11-14 00:30 master-control row already carried as knowledge-only; benchmarks_refreshed 2026-11-14 inside the seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2733 first=1 open=36 and leg_status read LEG-DEAD-NO-EVIDENCE pid=0 with no stream and no evidence file, so the leg had not been launched by an earlier window.",
    "R2734 THE TARGET WAS RE-MEASURED BY IMPORT BEFORE THE LAUNCH and matched the pre-registration byte for byte: reconcile_all.SUITES reads 675 suites / 5026 criteria with 675 unique names and 675 unique paths, so no larger delta had to be named. The launcher src/os/launch_battery_R2733.py refuses on a moved target, a duplicate name or path, an existing evidence path and a live pid, and its liveness probe is the kernel OpenProcess + WaitForSingleObject form because os.kill(pid, 0) does not raise on Windows for a live pid. LAUNCHED detached pid=65136 writing logs/battery-R2733.stream and the single-writer evidence qa/reconcile-all-R2733.log, never a shell redirection into qa/.",
    "R2734 THE LEG IS MEASURED, NOT ASSUMED: twenty seconds after the launch the stream held 75 bytes, and a second sample later in the window read 15735 bytes with PASS suite rows landing (the first row read PASS suite lobby-hub-ledger exit=0 criteria=6 13.1s) and ZERO FAIL rows. The runner own line 'no evidence path: shell-capture mode' is its startup notice about dialect, not a missing --evidence argument; the evidence file is still written by the shipped single writer at completion and is not claimed here.",
    "R2734 WHAT THIS WINDOW DID NOT DO, by law and by choice: (a) no product src byte, no registry row, no queue row and no matrix stamp moved while the leg runs, because the write-sensitive set would otherwise be measured on a tree the battery never saw; (b) the tech queue floor is SHORT by one (claimable 9 against a floor of 10) and was NOT filled, because state/queue/tech.md is read by queue suites that are running inside this very leg - it is carried as the first item of the next non-battery window; (c) the R2731 dead per-round export hook in src/os/export_R2431.py is STILL OWED and now overdue by three windows; it is product src and therefore also waits for a non-battery window; (d) no verdict is issued: a killed leg is not a red one and an unfinished leg is not a green one.",
    "R2734 honest score by the Executive Protocol scale: ZERO product points. The CEO can newly open exactly one thing - the live stream logs/battery-R2733.stream - which is progress evidence rather than a product. Every P-47 business face still waits on CEO physical pieces (merchant id, mini-program appid/secret), and the AC-* tech queue this window feeds is internal test-fixture work, which is named in the window proposal BD-PROP-009 as a treadmill rather than passed off as product.",
    "R2734 tokens: local=~9k api=0 api_reason=verification window - one five-silence scan with the debt gate, queue head, queue floor and content-addressed decisions face, one leg_status and pid-chain reading, one registry measurement by import on four axes, one detached launch plus two stream samples, one export driver and one state append through the shipped writers, and the closeout commit; zero cloud calls and zero external API touches",
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
