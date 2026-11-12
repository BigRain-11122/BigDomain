"""R2683 push receipt: one honest log line, no tick move.

Indent hard-coded at two spaces: state_io.ITEM_INDENT is 16 against this file's 2.
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
    lines = [
        "R2683 push and export: git push origin main read f270d1cb..eb2bbb9d "
        "main -> main and git rev-parse read HEAD equal to origin/main at "
        "eb2bbb9d with an EMPTY git status, so the launched leg, the fold, the "
        "state append, the board row and the re-derived export are delivered; "
        "this receipt line lands in the follow-up commit it describes. The "
        "export was refreshed AFTER the state append (the R2449/R2433 ordering "
        "law) through the shipped driver src/os/export_R2635.py to 405674B at "
        "tick 2675 with queue=CURRENT and queue_drifted=(none), and "
        "check_export_consistency read pass=21 fail=0 VERDICT PASS with the "
        "three CEO-visible lines derived rather than typed. THE LEG WAS STILL "
        "LIVE AND GROWING AT THIS CLOSEOUT AND THAT IS THE HONEST STATE OF THE "
        "ROUND: pid 99984 alive by its stream, logs/battery-R2683.stream at "
        "466162B carrying 230 PASS suite rows and ZERO FAIL suite rows, against "
        "a full leg that has measured 1600-4100s here, so reconcile-battery-R2682 "
        "stays OPEN at its registered 658 suites / 4924 criteria and the next "
        "window adopts it by its evidence path qa/reconcile-all-R2683.log rather "
        "than relaunching. NO successor battery is owed beyond it because this "
        "window moved no product src byte and the registry is unmoved at 658 / "
        "4924 re-measured by import.",
    ]
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(lines)
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(lines):
        suffix = "," if index < len(lines) - 1 else ""
        inserted.append(" " * INDENT + json.dumps(item, ensure_ascii=False) +
                        suffix)
    out = state_io.EOL.join(doc_lines[:end] + inserted + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    print("PREDICTED bytes=%d (gate 78500, margin %d)"
          % (len(payload), 78500 - len(payload)))
    if "--dry" in sys.argv:
        print("DRY run, nothing written")
        return 0
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2683p_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok bytes=%d log_len=%d" % (after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
