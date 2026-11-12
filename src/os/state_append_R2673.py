"""R2673 verification window closeout: two honest log lines plus one tick.

The numbers typed into the face line were measured at run time in this window
(five-silence readings, debt gate, registry by import, stream bytes at two
bounded polls) rather than copied from the register.
"""

import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
ROOT = os.path.dirname(os.path.dirname(HERE))
STREAM = os.path.join(ROOT, "logs", "battery-R2673.stream")


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))
    stream_bytes = len(io.open(STREAM, "rb").read())
    lines = [
        "2026-11-12 R2673 VERIFICATION window on the battery the debt gate "
        "named first (reconcile-battery-R2671, pre-registered 654 suites / 4900 "
        "criteria at R2671 because that window moved product src bytes, one "
        "suite and one registry row). Five readings at open: git status EMPTY "
        "with no index.lock, ZERO unreplied @BigDomain rows in "
        "cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0), the "
        "content-addressed decisions scan read rows=114 tokens=63 new=0, the "
        "group orders tail max_ts still the 2026-11-12 12:45 bm-a station "
        "onboard row already carried as last_order and judged knowledge-only "
        "for this company, and benchmarks_refreshed 2026-11-10 sitting two days "
        "inside the seven-day gate. debt_gate read CLAIM-FIRST "
        "item=reconcile-battery-R2671 opened=R2671 carried=2 stale=no open=45 "
        "first=1; queue_head named tech line 676 prefix AC-PNAG1 claimable=14 "
        "and queue_floor read FLOOR-MET at 5/5, 14/10, 10/10.",
        "2026-11-12 R2673 THE TARGET WAS RE-MEASURED BY IMPORT BEFORE THE LAUNCH "
        "and the leg was then launched DETACHED AND IS STILL RUNNING AT "
        "CLOSEOUT, DISCLOSED RATHER THAN DRESSED UP AS GREEN: "
        "reconcile_all.SUITES read 654 suites / 4900 criteria / 654 unique "
        "names / 654 unique paths, byte for byte the registered number. One "
        "one-off launcher src/os/launch_battery_R2673.py refused on a moved "
        "target, a non-unique name or path, or an existing evidence file, then "
        "Popen-ed src/os/battery_stream.py with "
        "CREATE_NO_WINDOW|DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP and put the "
        "stream and the pid in SEPARATE files under logs/ (battery-R2673.stream, "
        "battery-R2673.pid, pid 63200 with its reconcile_all child 38276 "
        "confirmed live by command line) so qa/ is written by the single writer "
        "and never by a shell redirection. MEASURED at open+45s the stream was "
        "75B with the runner own shell-capture notice, and at open+105s it read "
        "%dB carrying 13 closed PASS suite rows the first being lobby-hub-ugc "
        "6/6 at 22.4s. A full leg has measured roughly 1600-4100s in this "
        "repository against this window 25-minute budget, so "
        "reconcile-battery-R2671 STAYS OPEN at its registered 654/4900 and the "
        "next window ADOPTS this leg and closes the row (the "
        "R2601/R2607/R2609/R2610/R2614/R2635/R2655 precedent) instead of a "
        "green claim this window cannot make." % stream_bytes,
        "R2673 tokens: local=~7k api=0 api_reason=verification window - one "
        "five-silence scan with the content-addressed decisions scan, the group "
        "orders tail and the ledger face actually read, one debt gate read "
        "naming the battery, one queue head plus one queue floor read on all "
        "three lines, one registry target re-measured by import on four axes, "
        "one refusing one-off launcher written and one detached leg launched "
        "with its stream and pid in separate files and its first suite rows "
        "re-read at two bounded polls, one state fold --check and one "
        "ledger_lines --check read CLEAR with nothing folded, and the "
        "state/export/heartbeat closeout; zero cloud calls and zero external "
        "API touches",
    ]
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(lines)
    expected["tick"] = tick + 1
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(lines):
        suffix = "," if index < len(lines) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    bumped = []
    old_tick = '"tick": %d,' % tick
    new_tick = '"tick": %d,' % (tick + 1)
    seen = 0
    for row in doc_lines:
        if row.strip() == old_tick and not seen:
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2673_")
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
