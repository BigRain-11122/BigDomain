"""R2726 battery-launch closeout: log lines, one tick, canonical read-back."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2726 BATTERY LAUNCH window on reconcile-battery-R2725, the debt "
    "gate CLAIM-FIRST item at the pre-registered 673 suites / 5014 criteria on "
    "the committed tree d5334aea: the R2168 mixed-tree rule owes a full battery "
    "BEFORE any further product byte because R2725 moved product src (the "
    "unknown-shape refusal face plus its six-criteria suite) and one registry "
    "row. MEASURED BEFORE any launch: reconcile_all imported and read suites 673 "
    "criteria 5014 names 673 paths 673 with every name and path unique, "
    "qa/reconcile-all-R2725.log ABSENT, and a process-table scan over python.exe "
    "command lines matched NOTHING for battery_stream or reconcile_all, so no "
    "duplicate leg could fire. Five-silence readings at open: git status carried "
    "ONE untracked entry only (the empty tmp/ scratch directory) at HEAD "
    "b01074fe equal to origin/main with no index.lock; the group ledger read "
    "atbd_rows=0 with three carried P rows (P-2026-11-08-01, P-2026-10-25-08, "
    "P-2026-11-01-04) and the decisions face read rows=134 new=0; the group "
    "orders tail is the carried 10-16 row already knowledge-only; "
    "benchmarks_refreshed 2026-11-14 inside the seven-day gate; "
    "heartbeat.txt carried a bare timestamp with no tick token, which is the "
    "own heartbeat debt repaired below rather than reported as a pass.",
    "R2726 THE LEG WAS LAUNCHED DETACHED AND NEGATIVE-CONTROLLED IN THE SAME "
    "WINDOW: src/os/launch_battery_R2725.py pins the target and refuses on a "
    "moved registry, a non-unique name or path, an existing evidence path or a "
    "live pid read through ctypes OpenProcess plus WaitForSingleObject, and it "
    "started src/os/battery_stream.py as pid 56016 into logs/battery-R2725.stream "
    "with the pid in its own file, so qa/reconcile-all-R2725.log is written by "
    "the shipped single utf-8 LF writer alone. A SECOND run read "
    "E_LAUNCH_PID_EXISTS pid=56016 at rc=2, so a leg cannot be double-fired over "
    "the file it is already writing. Liveness read rather than assumed: at "
    "15:38:39 the pid answered ALIVE through the same kernel probe and the "
    "stream carried 16888 bytes with 6 closed PASS suite rows and ZERO FAIL "
    "rows. The launcher was committed BEFORE the fire (d5334aea) so the leg "
    "runs on a committed tree.",
    "R2726 LEDGER face receipt by number, knowledge-only and zero BigDomain "
    "action: P-2026-11-08-01 (BigMoney iteration loop dead face) is the quant "
    "host own loop, reached by that repository own watchdog, not a BigDomain "
    "execution face; P-2026-10-25-08 (veto-window semantics still conflicting "
    "between evolution.md and the round prompts) is a T1 text decision awaiting "
    "one CEO sentence and this company neither writes cph4 nor owns that "
    "prompt set; P-2026-11-01-04 (lane scheduled tasks back on InteractiveToken "
    "against the S4U law) is the same physical-piece domain this company already "
    "carries as ceo-pending loop-s4u-reconcile for its own BigDomain-OSLoop, and "
    "it needs an ELEVATED shell that an unattended round cannot obtain. None of "
    "the three is claimable work here, so each is recorded rather than re-scanned.",
    "R2726 tokens: local=~4k api=0 api_reason=battery launch phase - one "
    "five-silence scan with the debt gate, the queue head and the ledger face, "
    "one target measurement by import on four axes, one evidence-path and one "
    "process-table occupancy check, one launcher committed then fired and "
    "negative-controlled, one kernel liveness read with six suite rows counted, "
    "one heartbeat repair, and the state/export closeout; zero cloud calls and "
    "zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))
    expected = json.loads(text)
    for item in LINES:
        expected["log"].append(item)
    expected["tick"] = tick + 1

    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)

    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    bumped = []
    old_tick = '"tick": %d' % tick
    new_tick = '"tick": %d' % (tick + 1)
    seen = 0
    for row in doc_lines:
        if row.strip().rstrip(",") == old_tick and not seen:
            bumped.append(row.replace(old_tick, new_tick))
            seen += 1
        else:
            bumped.append(row)
    if seen != 1:
        print("REFUSED tick line not found exactly once")
        return 3
    out = state_io.EOL.join(bumped[:end] + inserted + bumped[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2726_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d layout_ok=%d"
          % (tick + 1, after["bytes"], after["log_len"],
             int(after["layout_ok"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
