"""R2680 push receipt: one honest log line, no tick change.

The numbers below were read from the push itself and from the live leg at the
moment of this receipt: git push read 271402b4..163efd82 main -> main, HEAD
163efd82, and the leg was still writing (stream 613016B measured just before
the push, 353 closed PASS suite rows, ZERO FAIL rows, one reconcile_all process
live by command line).
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

LINE = (
    "R2680 push and export: git push origin main read 271402b4..163efd82 main "
    "-> main and HEAD read 163efd82, so the opened verification window, its "
    "measured open readings, the pre-named R2614 discipline, the seeded "
    "adoption row and the closeout are delivered; this receipt line lands in "
    "the follow-up commit it describes. The export was refreshed AFTER the "
    "state append (the R2449/R2433 ordering law) through the shipped driver "
    "src/os/export_R2635.py to 405545B at tick 2672 with queue=CURRENT and "
    "queue_drifted=(none), and check_export_consistency read pass=21 fail=0 "
    "VERDICT PASS with the three CEO-visible lines derived rather than typed. "
    "state_fold --check read FOLD-CLEAR at 62191B against the 78500B gate with "
    "margin 16309 before the append and ledger_lines --check read VERDICT "
    "CLEAN with rounds_without_ledger none. THE LEG IS STILL LIVE AND THAT IS "
    "THE HONEST STATE OF THIS ROUND: one reconcile_all process alive by "
    "command line, logs/battery-R2680.stream measured 613016B with 353 closed "
    "PASS suite rows and ZERO FAIL suite rows just before the push, against a "
    "full leg that has measured 1600-3300s here, so reconcile-battery-R2679 "
    "stays OPEN at its registered 657 suites / 4918 criteria and the next "
    "window adopts it by its evidence path qa/reconcile-all-R2680.log rather "
    "than relaunching. NO successor battery is owed beyond it because this "
    "window moved no product src byte and the registry is unmoved at 657/4918 "
    "re-measured by import."
)


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + [LINE]
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = [" " * INDENT + json.dumps(LINE, ensure_ascii=False)]
    out = state_io.EOL.join(doc_lines[:end] + inserted + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2680_push_")
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
          (data.get("tick", 0), after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
