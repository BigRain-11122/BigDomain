"""R2705 verification window closeout: measured log lines and one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-13 R2705 VERIFICATION window on the debt the gate named "
    "(reconcile-battery-R2704, first=yes, open=45), because R2704 moved product "
    "src bytes and the R2168 mixed-tree rule puts a full battery BEFORE any "
    "further product byte. Five readings at open, all clean: git status EMPTY at "
    "HEAD ce25b72c equal to origin/main with no index.lock; ZERO @BigDomain rows "
    "in the group ledger; the content-addressed decisions face read rows=143 "
    "tokens=64 new=0 against the stored union baseline of 263; the group orders "
    "tail max timestamp is still 2026-11-12 12:45, already carried as last_order "
    "and knowledge-only for this company; benchmarks_refreshed 2026-11-13 inside "
    "the seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2704, "
    "queue_head read tech line=685 prefix=AC-PNAT1 skipped_before=7 claimable=14, "
    "queue_floor read FLOOR-MET main 5/5 tech 14/10 explore 10/10, state_fold "
    "--check read FOLD-CLEAR at 57825B against the 78500B gate with margin 20675 "
    "and 48 live log lines, state_io --check read CANON-CLEAN, ledger_lines "
    "--check read VERDICT CLEAN, and the registry was re-measured BY IMPORT at "
    "suites=664 criteria=4960 names=664 paths=664, byte for byte the target the "
    "debt row pre-registered.",

    "R2705 A DOUBLE-FIRE I CAUSED AND THEN CLEANED, disclosed rather than hidden: "
    "the launcher src/os/launch_battery_R2705.py first fired leg pid=12876 at "
    "21:11:49 and read 5 PASS / 0 FAIL at 16311B / 114 lines by 21:13:40; its "
    "liveness guard then used os.kill(pid, 0), which is NOT a liveness probe on "
    "Windows, so the guard silently answered 'no live pid' and my intended "
    "NEGATIVE CONTROL actually fired a SECOND leg pid=46476 at 21:14:03. Four "
    "python processes were then found by command line (two legs, each a "
    "battery_stream parent plus a reconcile_all child) sharing one stream file "
    "and one evidence path. All four were force-stopped and ZERO survivors were "
    "verified by command line; the polluted stream and pidfile were DELETED; "
    "qa/reconcile-all-R2705.log was verified ABSENT before any relaunch, so no "
    "killed leg ever wrote evidence and none was adopted.",

    "R2705 GUARD REPAIRED AND PROVED BY NEGATIVE CONTROL BEFORE THE ONE LEG THAT "
    "COUNTS: live_pid() now asks the kernel through ctypes OpenProcess + "
    "WaitForSingleObject (SYNCHRONIZE, no console child, no signal, no cloud), "
    "reading pid alive only on WAIT_TIMEOUT; the single relaunch read "
    "TARGET-MEASURED suites=664 criteria=4960 names=664 paths=664 and LAUNCHED "
    "pid=45032 with evidence qa/reconcile-all-R2705.log and stream "
    "logs/battery-R2705.stream, and the re-run negative control now answers "
    "E_LAUNCH_PID_EXISTS pid=45032 at rc=2 with exactly TWO python processes on "
    "the host (one battery_stream parent, one reconcile_all child), so a second "
    "leg can no longer fire against a live evidence path.",

    "R2705 LEG LIVE AT CLOSEOUT, SO NO VERDICT IS CLAIMED: two bounded polls of "
    "the final leg read 10 PASS / 0 FAIL at 18801B / 155 lines by 21:17:27 and "
    "the run is about an hour at this size. reconcile-battery-R2704 therefore "
    "STAYS OPEN at 664 suites / 4960 criteria, the debt register was not touched, "
    "and the matrix was not restamped because its stamp would otherwise claim a "
    "green this window does not have - docs/sandbox-suite-matrix.md stays at 664 "
    "rows with 663 evidence-green. The NEXT window ADOPTS this leg by its "
    "evidence path (no relaunch while it is live), recounts the criteria "
    "independently, and owes the R2614 write-sensitive re-run on the FINAL "
    "committed tree before any verdict, since this closeout commit lands under "
    "the leg window.",

    "R2705 honest disclosures: (a) ZERO product points - a launched leg, a "
    "repaired guard and a proved negative control are evidence, not something a "
    "CEO can newly open, and every P-47 business face still waits on CEO physical "
    "pieces (merchant id, mini-program appid/secret); (b) the double-fire was my "
    "own bug, cost about four minutes of wall clock and no evidence was ever "
    "written by the killed legs; (c) the guard repair is in a launcher, not in "
    "product src, and moves no registered suite; (d) this round touched no queue "
    "row and no debt row, tasks.md was not touched because it is the P-47 "
    "canonical board; (e) Docker is absent on this host; (f) BigDomain-OSLoop "
    "still reads InteractiveToken and needs an ELEVATED shell for its S4U "
    "re-registration (carried ceo-pending physical item loop-s4u-reconcile).",

    "R2705 tokens: local=~5k api=0 api_reason=verification window launch - one "
    "five-silence scan with the content-addressed decisions face, the group "
    "orders tail and the ledger face read, one debt gate read, one queue head "
    "plus one queue floor plus one fold gate plus one ledger gate plus one state "
    "IO read, one registry re-measure by import on four axes, one launcher "
    "written and fired, one mistaken double-fire found by process listing, one "
    "cleanup with a zero-survivor check, one guard repair and one proved negative "
    "control, one single relaunch with two bounded progress polls, and the "
    "state/export/heartbeat closeout; zero cloud calls and zero external API "
    "touches",
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2705_")
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
