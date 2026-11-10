"""R2619 verification window closeout."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-11 R2619 VERIFICATION window on the battery the debt gate named first (reconcile-battery-R2616, pre-registered 641 suites / 4822 criteria because the R2616 window moved product src bytes, one registry row and the matrix document). Five readings at open: git status EMPTY at HEAD 4cc513e8 equal to origin/main with no index.lock, ZERO @BigDomain rows in cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0), the content-addressed D-/C- decisions scan read rows=307 tokens=182 with new=0, the group orders tail unchanged at its 2026-11-10 03:52 row so last_order stands, and benchmarks_refreshed 2026-11-10 inside the seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2616 open=40 first=1, queue_head named tech line 650 prefix AC-EDMG1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10.",
    "R2619 TARGET RE-MEASURED BY IMPORT BEFORE THE LAUNCH: reconcile_all.SUITES read 641 suites / 4822 criteria / 641 unique names / 641 unique paths, byte for byte the registered number. MY OWN FIRST COUNT READ criteria=0 and is named rather than hidden: I summed len() over a criteria slot that is an integer because the registry tuple is (name, path, criteria_count), so the wrong slot was corrected and the count re-taken on four axes before anything was launched - the same trap R2526 and R2585 already recorded.",
    "R2619 THE LEG WAS LAUNCHED DETACHED AND IS STILL RUNNING AT CLOSEOUT, WHICH IS DISCLOSED RATHER THAN DRESSED UP AS GREEN: one one-off launcher src/os/launch_battery_R2616.py refuses when the registry target has moved from 641/4822 or when the evidence file already exists, Popen'ed src/os/battery_stream.py with CREATE_NO_WINDOW|DETACHED_PROCESS, and put the stream and the pid in SEPARATE files under logs/ (battery-R2616.stream, battery-R2616.pid) so qa/ is written by the single shipped writer and never by a shell redirection into qa/ (the ps-utf16 trap). pid 46108 with its reconcile_all child 75256 were confirmed live by command line, and the stream was measured at 105716B carrying 54 PASS suite rows against ZERO FAIL rows at closeout; a full leg has measured 3500-4100s in this repository against this window 25-minute budget, so reconcile-battery-R2616 STAYS OPEN at its registered 641/4822 and the next window adopts the leg and closes the row (the R2601/R2607/R2610/R2614 precedent).",
    "R2619 FOLD: state.json read 78436B against the 78500B waterline with a margin of only 64 bytes at open, so fold 679 ran at a true round-block boundary (items 86..95, the complete R2616 product-round block ending on its push line) after a dry run that agreed exactly, 78436B -> 67249B with margin 11251, archive VERIFIED, layout AGREE, 12 tokens preserved verbatim, and ledger_lines --check read CLEAN with rounds_without_ledger=none and ledger_without_round=none.",
    "R2619 honest disclosures: (a) ZERO product points on the Executive Protocol scale - no product byte was written, because the debt gate puts the owed battery before any further product work and that leg is still running, so nothing a CEO could newly open was built and no P-47 business surface moved; (b) the battery is neither green nor red and NOTHING is claimed about it beyond the rows actually measured; (c) this window wrote state.json, its archive and the export UNDER the running leg, so a future green verdict is admissible only beside an individual re-run of the write-sensitive suites on the FINAL committed tree (the R2614 lesson, named rather than smoothed); (d) a TOOL DEFECT WAS MEASURED AND NOT REPAIRED THIS WINDOW: src/os/scan_five_still.py dies with UnicodeEncodeError on its own [ORD-TOP] print because the group orders top line carries a U+FEFF BOM and the console codec is gbk, so the scan printed its [LEDGER], [DEC] and [ORD] lines and then exited 1 before its later sections - the facts this window used came from those three lines plus separate reads, and the repair is named for the next window instead of being performed under a live leg; (e) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed; (f) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (g) tasks.md was not touched, it is the P-47 canonical board; (h) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell (carried as the ceo-pending physical item loop-s4u-reconcile).",
    "R2619 tokens: local=~8k api=0 api_reason=verification window - one five-silence scan whose own [ORD-TOP] BOM defect is named above, one debt gate plus queue head and floor read, one registry target re-measured by import on four axes after correcting my own criteria-slot mistake, one detached battery launched through a refusing one-off launcher with its stream and pid in separate files and its liveness and progress measured, one fold executed at a true round-block boundary after a dry run that agreed, and the state/export closeout; zero cloud calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    expected["tick"] = int(data["tick"]) + 1
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    item_indent = None
    for line in lines[start:end]:
        stripped = line.lstrip(" ")
        if stripped.startswith('"') and not stripped.startswith('"log"'):
            item_indent = len(line) - len(stripped)
            break
    if item_indent is None:
        print("REFUSED no item line")
        return 6
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * item_indent +
                        json.dumps(item, ensure_ascii=False) + suffix)
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    out = out.replace('"tick": %d' % data["tick"],
                      '"tick": %d' % expected["tick"], 1)
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2619_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d"
          % (expected["tick"], after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
