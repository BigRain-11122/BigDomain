"""R2721 battery launch closeout: the leg is live, disclosed, one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2721 BATTERY LAUNCH window on reconcile-battery-R2720, the debt gate "
    "CLAIM-FIRST item at the pre-registered 671 suites / 5002 criteria on the committed "
    "tree 691f66e8: the R2168 mixed-tree rule owes a full battery BEFORE any product "
    "byte because R2720 moved product src (the compound refusal report plus its "
    "six-criteria suite) and one registry row. MEASURED BEFORE any launch: reconcile_all "
    "imported and read suites 671 criteria 5002 names 671 paths 671 with every name and "
    "path unique, qa/reconcile-all-R2721.log ABSENT, and the launcher own evidence-path "
    "and live-pid guards intact. src/os/launch_battery_R2721.py pins those numbers as "
    "its target and launched detached as pid 55868 into logs/battery-R2721.stream with "
    "qa/reconcile-all-R2721.log owned by the shipped single utf-8 LF writer.",
    "R2721 LIVENESS read rather than assumed: the guard was NEGATIVE-CONTROLLED in the "
    "same window (a second run read E_LAUNCH_PID_EXISTS pid=55868 at rc=2), and after 80 "
    "seconds the stream carried 16311 bytes with FIVE closed PASS suite rows, ZERO FAIL "
    "rows and a tail landing on lobby-hub-ugc exit=0 criteria=6 22.4s, so the leg is "
    "really running on this tree. NO product src byte and NO registry row was touched "
    "this window; the queue head AC-ECORD1 (state/queue/tech.md:694) stays untouched BY "
    "DESIGN because the battery must land green first.",
    "R2721 tokens: local=~3k api=0 api_reason=battery launch window - one debt gate and "
    "queue reading, one registry measurement by import on four axes, one launcher "
    "written and fired and negative-controlled, one bounded liveness read, and the "
    "state/export/heartbeat closeout; zero cloud calls and zero external API touches",
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2721_")
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
