"""R2680 verification window closeout: honest log lines plus one tick.

Every number below was measured in this window (the five-silence scan, the debt
gate, the registry by import on four axes, the live leg stream bytes and its
closed suite rows, the pid chain, the state bytes and both gates) rather than
copied from the register.

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
        "2026-11-13 R2680 VERIFICATION window opened on the battery the debt gate "
        "names first (reconcile-battery-R2679, registered at 657 suites / 4918 "
        "criteria) because the R2679 product window moved product src bytes and "
        "one registry row, so the R2168 mixed-tree rule puts the full battery on "
        "the committed tree BEFORE any further product byte. Five readings at "
        "open, all clean: git status EMPTY at HEAD 271402b4 with no index.lock; "
        "ZERO unreplied @BigDomain rows (atbd_lines=0 unreplied_groups=0); the "
        "content-addressed decisions scan read rows=120 tokens=64 new=0; the "
        "group orders tail max_ts still the 2026-11-12 12:45 bm-a station "
        "ONBOARD row already carried as last_order and judged knowledge-only for "
        "this company; benchmarks_refreshed 2026-11-10 sitting three days inside "
        "the seven-day gate. debt_gate read CLAIM-FIRST "
        "item=reconcile-battery-R2679 opened=R2679 carried=1 stale=no open=45 "
        "first=1 and the target was RE-MEASURED BY IMPORT before the launch at "
        "657 suites / 4918 criteria / 657 unique names / 657 unique paths, byte "
        "for byte the registered number.",
        "2026-11-13 R2680 THE LEG WAS LAUNCHED DETACHED AND IS STILL RUNNING AT "
        "CLOSEOUT, DISCLOSED RATHER THAN DRESSED UP AS GREEN: a one-off launcher "
        "src/os/launch_battery_R2680.py refused on a moved target, a non-unique "
        "name or path, or an existing evidence/stream/pid file, then Popen-ed "
        "src/os/battery_stream.py with CREATE_NO_WINDOW|DETACHED_PROCESS|"
        "CREATE_NEW_PROCESS_GROUP and put the stream and the pid in SEPARATE "
        "files under logs/ (battery-R2680.stream, battery-R2680.pid, pid 101316 "
        "with its reconcile_all child 99092 confirmed live by command line) so "
        "qa/reconcile-all-R2680.log is written by the single utf-8 LF writer on "
        "completion and never by a shell redirection. The child environment pins "
        "PYTHONIOENCODING=utf-8:replace so a detached stream can never die on an "
        "unmappable character. MEASURED at elapsed 1179s the stream read 585191B "
        "carrying 335 closed PASS suite rows and ZERO FAIL suite rows, and the "
        "rolling pace named the reason this window cannot close the row: the "
        "apimarket block entered after row 322 carries legitimately slow suites "
        "(refundregister 256.1s, buyerhistory 100.0s, minors-wiring 71.7s, lobby "
        "46.4s, lobby-hub-panel 43.3s, named rather than called a hang). A full "
        "leg has measured roughly 1600-3300s in this repository against this "
        "window 25-minute budget, so reconcile-battery-R2679 STAYS OPEN at its "
        "registered 657 suites / 4918 criteria and the next window ADOPTS this "
        "leg by its evidence path and closes the row (the R2673/R2676/R2678 "
        "precedent) instead of a green claim this window cannot make.",
        "2026-11-13 R2680 TWO CLOSEOUT COMMITS LAND UNDER THIS LEG BY "
        "CONSTRUCTION, SO THE R2614 DISCIPLINE IS OWED AND IS NAMED HERE RATHER "
        "THAN DISCOVERED NEXT WINDOW: this window own state/export/backlog/"
        "heartbeat commits land while the leg runs, so a green verdict is "
        "admissible only beside an individual re-run of the write-sensitive set "
        "(export trio, ledger round coverage, the six readability suites, both "
        "export health suites) on the FINAL committed tree, and the follow-up "
        "four sections (matrix designed FAIL first with NO byte written, then a "
        "stamp-aligned regeneration from THIS round own green leg, then the "
        "verdict append) run next window in the designed order. The matrix doc "
        "is deliberately NOT regenerated now: it records the R2678 leg, and "
        "restamping it from a leg that has not closed would be a green claim.",
        "R2680 tokens: local=~9k api=0 api_reason=verification window - one "
        "five-silence scan with the content-addressed decisions face, the group "
        "orders tail and the ledger face read, one debt gate read, one registry "
        "target re-measured by import on four axes, one one-off refusing launcher "
        "written and executed and DELETED before the commit, one detached leg "
        "launched with its stream and pid in separate files and four bounded "
        "progress polls with a slow-row measurement, two gate reads (state_fold "
        "FOLD-CLEAR, ledger_lines CLEAN), and the state/export/heartbeat "
        "closeout; zero cloud calls and zero external API touches",
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2680_")
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
