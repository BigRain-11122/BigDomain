"""R2674 push receipt: one log line recording the delivered closeout.

Lands in the follow-up commit it describes, the R2449/R2433 ordering law.
"""

import io
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
        "R2674 push and export: git push origin main read 80a0e9d1..778749ae "
        "main -> main and git rev-parse read HEAD equal to origin/main at "
        "778749ae with an EMPTY git status, so the verification closeout is "
        "delivered; this receipt line lands in the follow-up commit it "
        "describes. The export was refreshed AFTER the state append (the "
        "R2449/R2433 ordering law) through the shipped driver "
        "src/os/export_R2635.py to 405005B at tick 2663 with queue=CURRENT and "
        "queue_drifted=(none), and check_export_consistency read pass=21 "
        "fail=0 VERDICT PASS with the three CEO-visible lines derived rather "
        "than typed. state_fold --check read FOLD-CLEAR at 75331B against the "
        "78500B gate with 92 log lines and the archive present. The board top "
        "line now carries the R2674 done row plus the seeded R2675 carried item, "
        "and no product src byte moved.",
    ]
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(lines)
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = [" " * INDENT + json.dumps(item, ensure_ascii=False) +
                ("," if index < len(lines) - 1 else "")
                for index, item in enumerate(lines)]
    out = state_io.EOL.join(doc_lines[:end] + inserted + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2674b_")
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
