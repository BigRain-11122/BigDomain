"""R2683 verification window closeout: honest log lines plus one tick.

Every number below was measured in this window (the five-silence scan, the debt
gate, the registry by import on four axes, the stream sizes and the PASS/FAIL
suite row counts) rather than copied from the register.

The indent is hard-coded at two spaces on purpose: state_io.ITEM_INDENT is 16
while this file own log items sit at 2.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
INDENT = 2


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))
    lines = [
        "2026-11-13 R2683 VERIFICATION window on the battery the debt gate "
        "named first (reconcile-battery-R2682, pre-registered 658 suites / 4924 "
        "criteria at R2682). Five readings at open, all clean: git status EMPTY "
        "at HEAD f270d1cb equal to origin/main with no index.lock; ZERO "
        "unreplied @BigDomain rows (atbd_lines=0 unreplied_groups=0); the "
        "content-addressed decisions scan read rows=120 tokens=64 new=0; the "
        "group orders tail max_ts still the 2026-11-12 12:45 bm-a ONBOARD row "
        "already carried as last_order and judged knowledge-only for this "
        "company; benchmarks_refreshed 2026-11-10 sitting three days inside the "
        "seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2682 "
        "opened=R2682 open=45 first=1, and queue_head read tech line=680 "
        "prefix=AC-PNAL1 claimable=14.",
        "R2683 THE TARGET WAS RE-MEASURED BY IMPORT BEFORE THE LAUNCH and read "
        "658 suites / 4924 criteria / 658 unique names / 658 unique paths, byte "
        "for byte the registered number. A one-off launcher "
        "src/os/launch_battery_R2683.py refused on a moved target, an existing "
        "evidence file or an existing pid file, then Popen-ed "
        "src/os/battery_stream.py with "
        "CREATE_NO_WINDOW|DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP and put the "
        "stream and the pid in SEPARATE files under logs/ "
        "(battery-R2683.stream, battery-R2683.pid, pid 99984) so qa/ is written "
        "by the single utf-8 LF writer and never by a shell redirection.",
        "R2683 ONE OWN LAUNCH DEFECT BORN AND REPAIRED INSIDE THIS WINDOW, "
        "DISCLOSED RATHER THAN SMOOTHED: the launcher first read BASE as the "
        "src directory and joined qa/ and logs/ onto it, so the very first "
        "attempt died with FileNotFoundError on src/logs/battery-R2683.stream "
        "BEFORE any process started, any pid file was written or any evidence "
        "path was created. The join was corrected to the repository root and the "
        "relaunch then printed LAUNCHED pid=99984 target=(658, 4924, 658, 658).",
        "R2683 MEASURED AT TWO BOUNDED POLLS AND STILL LIVE AT CLOSEOUT: at "
        "open+50s the stream read 15153B with the runner own rows already "
        "closing suites, and at open+160s it read 20701B carrying 13 PASS suite "
        "rows and ZERO FAIL suite rows. A full leg has measured roughly "
        "1600-4100s in this repository against this window 25-minute budget, so "
        "reconcile-battery-R2682 STAYS OPEN at its registered 658 suites / 4924 "
        "criteria and the next window ADOPTS this leg by its evidence path "
        "qa/reconcile-all-R2683.log and closes the row (the "
        "R2671/R2673/R2674/R2676/R2680 precedent) instead of a green claim this "
        "window cannot make. NO successor battery is owed beyond it because this "
        "window moved no product src byte and the registry is unmoved at 658 / "
        "4924 re-measured by import.",
        "R2683 tokens: local=~7k api=0 api_reason=verification window - one "
        "five-silence scan with the content-addressed decisions face, the group "
        "orders tail and the ledger face read, one debt gate read, one queue "
        "head read, one registry target re-measured by import on four axes, one "
        "refusing one-off launcher written, corrected at its own path defect and "
        "then executed, one detached leg launched with its stream and pid in "
        "separate files and two bounded progress polls with row counts, and the "
        "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
        "external API touches",
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
        inserted.append(" " * INDENT + json.dumps(item, ensure_ascii=False) +
                        suffix)
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
    print("PREDICTED bytes=%d (gate 78500, margin %d)"
          % (len(payload), 78500 - len(payload)))
    if "--dry" in sys.argv:
        print("DRY run, nothing written")
        return 0
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2683_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d items_off_indent=%d" %
          (tick + 1, after["bytes"], after["log_len"],
           after["items_off_indent"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
