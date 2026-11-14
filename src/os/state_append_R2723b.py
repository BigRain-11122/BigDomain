"""R2723 launch phase: battery fired on the committed tree, one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2723 BATTERY LAUNCH phase on reconcile-battery-R2723, the debt "
    "gate CLAIM-FIRST item at the pre-registered 672 suites / 5008 criteria on "
    "the committed tree c58ff81e: the R2168 mixed-tree rule owes a full battery "
    "BEFORE any further product byte because this round moved product src (the "
    "derived precedence face plus its six-criteria suite) and one registry row. "
    "MEASURED BEFORE any launch: reconcile_all imported and read suites 672 "
    "criteria 5008 names 672 paths 672 with every name and path unique, "
    "qa/reconcile-all-R2723.log ABSENT, and a process-table scan over python.exe "
    "command lines matched NOTHING for battery_stream or reconcile_all, so no "
    "duplicate leg could fire.",
    "R2723 THE LEG WAS LAUNCHED DETACHED AND NEGATIVE-CONTROLLED IN THE SAME "
    "WINDOW: src/os/launch_battery_R2723.py pins the target and refuses on a "
    "moved registry, a non-unique name or path, an existing evidence path or a "
    "live pid read through ctypes OpenProcess plus WaitForSingleObject, and it "
    "started src/os/battery_stream.py as pid 63108 into logs/battery-R2723.stream "
    "with the pid in its own file, so qa/reconcile-all-R2723.log is written by "
    "the shipped single utf-8 LF writer alone. A SECOND run read "
    "E_LAUNCH_PID_EXISTS pid=63108 at rc=2, so a leg cannot be double-fired over "
    "the file it is already writing. Liveness read rather than assumed: after 85 "
    "seconds the stream carried 15735 bytes with 4 closed PASS suite rows, ZERO "
    "FAIL rows and a tail landing on lobby-hub-ledger exit=0 criteria=6 14.4s.",
    "R2723 launch tokens: local=~2k api=0 api_reason=battery launch phase - one "
    "target measurement by import on four axes, one evidence-path and one "
    "process-table occupancy check, one launcher fired and negative-controlled, "
    "one bounded liveness read, and the state/export closeout; zero cloud calls "
    "and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))

    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + LINES
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2723l_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d" %
          (tick + 1, after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
