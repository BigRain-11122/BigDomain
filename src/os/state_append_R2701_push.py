"""R2701 push receipt line, appended after the push it describes."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINE = (
    "R2701 push and export: git push origin main read d5883aad..cb155897 main "
    "-> main and git rev-parse read HEAD equal to origin/main at cb155897 with "
    "an EMPTY git status, so the shape-guard face, its six-criteria suite, the "
    "two byte-identical evidence legs with one adjacent suite, the one registry "
    "row, the restamped matrix at 663 rows, the closed board row, the seeded "
    "AC-PNAS1..AC-PNAS6 row, the two debt rows and the corrected R2698 note are "
    "all delivered; this receipt line lands in the follow-up commit it "
    "describes. The export was refreshed AFTER the state append and after the "
    "tick advance (the R2449/R2433 ordering law) through the shipped driver "
    "src/os/export_R2635.py to 406623B at tick 2693 with queue=CURRENT and "
    "queue_drifted=(none), and check_export_consistency read pass=21 fail=0 "
    "VERDICT PASS with the three CEO-visible lines derived rather than typed; "
    "it is re-derived again AFTER this line so the window own log count agrees "
    "with the document it is counted in. state_fold --check read FOLD-CLEAR at "
    "69183B against the 78500B gate with margin 9317 and 59 live log lines - no "
    "fold was owed this window - and ledger_lines --check read VERDICT CLEAN "
    "with rounds_without_ledger none and ledger_without_round none. The debt "
    "gate names reconcile-battery-R2701 first=yes at the pre-registered 663 "
    "suites / 4954 criteria, so the next window owes that FULL battery on the "
    "committed tree BEFORE any further product byte, and the queue head this "
    "window leaves behind is state/queue/tech.md line 684 prefix AC-PNAS1 with "
    "claimable 14 and the queue floor FLOOR-MET 5/5, 14/10, 10/10."
)


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))

    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + [LINE]

    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)

    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = [" " * state_io.ITEM_INDENT +
                json.dumps(LINE, ensure_ascii=False)]
    out = state_io.EOL.join(doc_lines[:end] + inserted + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2701p_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("RECEIPT ok tick=%d bytes=%d log_len=%d" %
          (tick, after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
