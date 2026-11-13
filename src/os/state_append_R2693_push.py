"""R2693 push receipt: one log line appended after the push, no tick bump."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINE = (
    "R2693 push and export: git push origin main read acbc394b..1cfa2125 "
    "main -> main and git rev-parse read HEAD equal to origin/main at 1cfa2125 "
    "with an EMPTY git status, so the five-silence readings, the by-import "
    "target re-measurement, the refusing launcher record, the two bounded polls "
    "and the honest live-at-closeout state are delivered; this receipt line "
    "lands in the follow-up commit it describes. The export was refreshed AFTER "
    "the state append and after the tick advance (the R2449/R2433 ordering law) "
    "through the shipped driver src/os/export_R2635.py to 406211B at tick 2685 "
    "with queue=CURRENT and queue_drifted=(none), and check_export_consistency "
    "read pass=21 fail=0 VERDICT PASS with the three CEO-visible lines derived "
    "rather than typed; it is re-derived again AFTER this line so the window own "
    "log count agrees with the document it is counted in. state_fold --check "
    "read FOLD-CLEAR at 72351B before this window append against the 78500B "
    "gate, and ledger_lines --check read VERDICT CLEAN with rounds_without_ledger "
    "none, ledger_without_round none, new_missing none and new_orphan none. THE "
    "LEG WAS STILL LIVE AND GROWING AT THIS CLOSEOUT AND THAT IS THE HONEST "
    "STATE OF THE ROUND: pid 113988 alive by process id, logs/battery-R2693."
    "stream at 449535B carrying 219 PASS suite rows and ZERO FAIL suite rows with "
    "no evidence file written yet and no closing line, against a full leg that "
    "has measured 1600-4100s in this repository and a 25-minute window budget, so "
    "reconcile-battery-R2692 stays OPEN at its registered 661 suites / 4942 "
    "criteria and the next window ADOPTS it by its evidence path "
    "qa/reconcile-all-R2693.log rather than relaunching, then lands the R2614 "
    "write-sensitive set on the FINAL committed tree before any verdict because "
    "this window closeout commits land UNDER the leg. NO successor battery is "
    "owed beyond it because this window moved no product src byte and the "
    "registry is unmoved at 661 / 4942 re-measured by import, and the queue head "
    "this window leaves behind is state/queue/tech.md line 682 prefix AC-PNAQ1 "
    "with claimable=14 and the queue floor FLOOR-MET 5/5, 14/10, 10/10."
)


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + [LINE]
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = [" " * state_io.ITEM_INDENT + json.dumps(LINE, ensure_ascii=False)]
    out = state_io.EOL.join(doc_lines[:end] + inserted + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2693r_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("RECEIPT ok bytes=%d log_len=%d" % (after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
