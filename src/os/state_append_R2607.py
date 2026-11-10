"""R2607 closeout append: log lines plus tick advance.

Reads the live state file as bytes, inserts the new log items at the measured
log-block end with the canonical CRLF and 16-space item indent, proves the JSON
payload moved by exactly those strings, then writes through state_io.write_canon.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-10 R2607 VERIFICATION window on the battery the debt gate named first (reconcile-battery-R2606, pre-registered 638 suites / 4804 criteria at R2606 because that window moved product src bytes and one registry row). Five readings at open: git status EMPTY at HEAD 486cacfb equal to origin/main with no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the content-addressed D-/C- decisions scan read tokens=67 new=0 over 109 rows, the group orders tail unchanged at the 2026-11-09 00:59 BigStream row, benchmarks 2026-11-03 exactly seven days old and therefore INSIDE the gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2606 first=1 open=39, queue_head named tech line 640 prefix AC-EDME1 claimable=15 and queue_floor read FLOOR-MET 5/5 15/10 10/10.",
    "2026-11-10 R2607 TARGET RE-MEASURED BY IMPORT BEFORE THE LAUNCH: reconcile_all.SUITES read 638 suites / 4804 criteria / 638 unique names / 638 unique paths, byte for byte the registered number.",
    "2026-11-10 R2607 THE LEG WAS LAUNCHED DETACHED AND IS STILL RUNNING AT CLOSEOUT, WHICH IS DISCLOSED RATHER THAN DRESSED UP AS GREEN: this window wrote one one-off launcher src/os/launch_battery_R2607.py that refuses when the registry target has moved from 638/4804 or when the evidence file already exists, Popen'ed src/os/battery_stream.py with CREATE_NO_WINDOW|DETACHED_PROCESS, and put the stream and the pid in SEPARATE files under logs/ (battery-R2607.stream, battery-R2607.pid) so qa/ is written by the single writer and never by a shell redirection. pid 43948 with its reconcile_all child were confirmed live by command line at open+65s reading 106 stream lines and again at +5min reading 312 lines; a full leg has measured 3500-4100s in this repository against this window 25-minute budget, so the debt row reconcile-battery-R2606 STAYS OPEN at its registered 638/4804 and the next window adopts the leg and closes the row (the R2601 precedent) instead of a green claim this window cannot make.",
    "R2607 FOLD AND LEDGER, disclosed: the first fold over window 77..82 archived the complete R2605 block ending on its push line but left ONE R2605 narrative line (item 76) live, so ledger_lines --check read rounds_without_ledger=[2605]; a second fold over item 76 healed it and the checks then read FOLD-CLEAR at 68725 bytes against the 78500B gate with margin 9775 and 83 log lines, and ledger_lines CLEAN with ledger=8 round=44 other=31, baseline missing=0 orphan=0, archive VERIFIED (folds 670 and 671).",
    "R2607 honest disclosures: (a) ZERO product points on the Executive Protocol scale - no product byte was written, because the debt gate puts the owed battery before any further product work and that leg is still running; (b) the battery is NOT green and is NOT claimed green - it is live at closeout with its evidence file not yet written, so the debt row stays open and the matrix document keeps whatever honest reading it already carried; (c) the fold took two passes because my first window started at item 77 and left item 76 live, which is named above rather than hidden; (d) benchmarks at 2026-11-03 are exactly seven days old, inside the gate by the letter of it with no margin, so a refresh is DUE and is named rather than performed; (e) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed; (f) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (g) tasks.md was not touched, it is the P-47 canonical board; (h) BigDomain-OSLoop still needs an ELEVATED shell for its S4U re-registration (carried as the ceo-pending physical item loop-s4u-reconcile).",
    "R2607 tokens: local=~9k api=0 api_reason=verification window - one five-silence scan with the content-addressed decisions scan, the group orders tail and the ledger face actually read, one debt gate plus queue head and floor read, one registry target re-measured by import on both axes, one detached battery launched through a refusing one-off launcher with its stream and pid in separate files and its liveness re-read twice, two folds with the first one name-checked and healed, and the state/export/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    raw = state_io.read_raw(PATH)
    text = state_io.decode(raw)
    data = state_io.parse(text)
    before = state_io.layout(text)
    if not before["layout_ok"]:
        print("REFUSED layout not canonical")
        return 2
    expected = json.loads(json.dumps(data))
    expected["tick"] = int(data["tick"]) + 1
    expected["log"] = list(data["log"]) + list(LINES)

    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    for index in range(start):
        if lines[index].strip().startswith('"tick":'):
            lines[index] = ' "tick": %d,' % expected["tick"]
            break
    else:
        print("REFUSED no tick line")
        return 6
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    new_lines = lines[:end] + inserted + lines[end:]
    # the item before the inserted block still ends with a comma, and the last
    # inserted item needs one before the closing bracket
    last_live = end - 1
    if not new_lines[last_live].rstrip().endswith(","):
        new_lines[last_live] = new_lines[last_live].rstrip() + ","
    out = state_io.EOL.join(new_lines)
    got = state_io.parse(out)
    if got != expected:
        print("REFUSED payload moved beyond the append")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".append_R2607_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(payload)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, PATH)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    if not after["layout_ok"] or after["log_len"] != len(expected["log"]):
        print("REFUSED post-write layout %r" % (after,))
        return 5
    print("APPEND ok tick=%d written=%d bytes=%d log_len=%d layout_ok=%s"
          % (expected["tick"], len(payload), after["bytes"],
             after["log_len"], after["layout_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())