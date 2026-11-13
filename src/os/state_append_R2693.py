"""R2693 verification window closeout: measured log lines plus one tick.

Every number typed here was measured in this window rather than copied from
the register: the five-silence readings, the debt gate, the queue head and
floor, the fold and ledger gates, the registry recounted by import, the
launch tuple, the two bounded polls and the process liveness.
"""

import io  # noqa: F401
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))
    lines = [
        "2026-11-13 R2693 VERIFICATION window LAUNCHING the battery the debt "
        "gate names first (reconcile-battery-R2692, pre-registered 661 suites "
        "/ 4942 criteria at R2692). Five readings at open, all clean: git "
        "status EMPTY at HEAD acbc394b equal to origin/main with no "
        "index.lock; ZERO @BigDomain rows in the group ledger (atbd_lines=0); "
        "the content-addressed decisions scan read rows=143 file_tokens=66 "
        "against the stored union baseline with new=0; the group orders tail "
        "max timestamp is still 2026-11-12 12:45, the bm-a station ONBOARD row "
        "already carried as last_order and judged knowledge-only for this "
        "company; benchmarks_refreshed 2026-11-10 sitting three days inside "
        "the seven-day gate. debt_gate read CLAIM-FIRST "
        "item=reconcile-battery-R2692 opened=R2692 carried=1 stale=no open=45 "
        "first=1, queue_head read tech line=682 prefix AC-PNAQ1 claimable=14, "
        "queue_floor read FLOOR-MET 5/5, 14/10, 10/10, state_fold --check read "
        "FOLD-CLEAR at 72351B against the 78500B gate with margin 6149 and 63 "
        "live log lines, and ledger_lines --check read VERDICT CLEAN with "
        "new_missing none and new_orphan none.",

        "R2693 THE TARGET WAS RE-MEASURED BY IMPORT BEFORE THE LAUNCH and read "
        "661 suites / 4942 criteria / 661 unique names / 661 unique paths, "
        "byte for byte the registered number. A one-off launcher held in tmp/ "
        "refused on a moved target (any tuple other than 661/4942/661/661), an "
        "existing evidence file or an existing pid file, then Popen-ed "
        "src/os/battery_stream.py with CREATE_NO_WINDOW|DETACHED_PROCESS|"
        "CREATE_NEW_PROCESS_GROUP and put the stream and the pid in SEPARATE "
        "files under logs/ (battery-R2693.stream, battery-R2693.pid, pid "
        "113988), so qa/reconcile-all-R2693.log is written by the single utf-8 "
        "LF writer and never by a shell redirection. MEASURED at two bounded "
        "polls: open+100s the stream read 16311B carrying 5 PASS suite rows "
        "and ZERO FAIL suite rows; open+340s it read 225267B carrying 121 PASS "
        "suite rows and ZERO FAIL suite rows with the pid alive by process id.",

        "R2693 honest disclosures: (a) ZERO product points - a launched "
        "battery is evidence in flight, not something a CEO can open, and "
        "every P-47 business face still waits on CEO physical pieces (merchant "
        "id, mini-program appid/secret); (b) the leg is LIVE at closeout and "
        "this window makes NO verdict, so reconcile-battery-R2692 STAYS OPEN at "
        "its registered 661 suites / 4942 criteria and the next window ADOPTS "
        "it by its evidence path qa/reconcile-all-R2693.log (the "
        "R2683/R2686/R2687/R2690 precedent) rather than relaunching; (c) this "
        "window moved no product src byte and no registry row, the registry "
        "unmoved at 661 / 4942 re-measured by import, so NO successor battery "
        "is owed beyond the adopted one; (d) the one-off launcher in tmp/ is "
        "DELETED before the commit rather than staged; (e) Docker is absent on "
        "this host; (f) tasks.md was not touched, it is the P-47 canonical "
        "board; (g) BigDomain-OSLoop still reads InteractiveToken and needs an "
        "ELEVATED shell for its S4U re-registration (carried ceo-pending "
        "physical item loop-s4u-reconcile).",

        "R2693 tokens: local=~7k api=0 api_reason=verification launch window - "
        "one five-silence scan with the content-addressed decisions face, the "
        "group orders tail and the ledger face read, one debt gate read, one "
        "queue head plus one queue floor read, one fold gate plus one ledger "
        "gate read, one registry target re-measured by import on four axes, one "
        "refusing launcher executed once, two bounded progress polls with row "
        "counts and a process-liveness read, and the state/export/heartbeat "
        "closeout; zero cloud calls and zero external API touches",
    ]

    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + lines
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2693_")
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
