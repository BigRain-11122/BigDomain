"""R2704 push receipt: one measured line, no tick change."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINE = (
    "R2704 push and export: the product commit ba2abf4d landed after "
    "ec2a65f8..ba2abf4d main -> main and git rev-parse read HEAD equal to "
    "origin/main at ba2abf4d with an EMPTY git status, so the new canonical guard "
    "face, its six-criteria suite, both birth-site repairs, the registry row, the "
    "restamped matrix, the closed debt row, the opened reconcile-battery-R2704 and "
    "the closed-then-seeded queue rows are all delivered; this receipt line lands in "
    "the follow-up commit it describes. The export was refreshed AFTER the state "
    "append and after the tick advance (the R2449/R2433 ordering law) through the "
    "shipped driver src/os/export_R2635.py to 406753B at tick 2696 with queue=CURRENT "
    "and queue_drifted=(none), and check_export_consistency read pass=21 fail=0 "
    "VERDICT PASS with the three CEO-visible lines derived rather than typed; it is "
    "re-derived again AFTER this line so the window own log count agrees with the "
    "document it is counted in. state_fold --check read FOLD-CLEAR at 56326B against "
    "the 78500B gate with margin 22174 and 47 live log lines, state_io --check read "
    "CANON-CLEAN, ledger_lines --check read VERDICT CLEAN, and the debt gate now "
    "names reconcile-battery-R2704 first=yes at the re-measured 664 suites / 4960 "
    "criteria, so the next window owes a VERIFICATION face on the committed tree "
    "BEFORE any further product byte; the queue head this window leaves behind is "
    "state/queue/tech.md line 685 prefix AC-PNAT1 with claimable 14 and the queue "
    "floor reads FLOOR-MET 5/5, 14/10, 10/10."
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
    inserted = [" " * state_io.ITEM_INDENT +
                json.dumps(LINE, ensure_ascii=False)]
    out = state_io.EOL.join(doc_lines[:end] + inserted + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2704p_")
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
          (int(data.get("tick", 0)), after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
