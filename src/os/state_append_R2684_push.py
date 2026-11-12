"""R2684 push receipt: one honest log line, no tick move.

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
        "R2684 push and export: git push origin main read 6d66183e..3658b8a7 "
        "main -> main and git rev-parse read HEAD equal to origin/main at "
        "3658b8a7 with an EMPTY git status, so the adopted green verdict, the "
        "measured evidence, the restamped matrix, the write-sensitive evidence, "
        "the closed debt row, the opened successor, the closed board row and the "
        "carried row are all delivered; this receipt line lands in the "
        "follow-up commit it describes. The export was refreshed AFTER the state "
        "append and after the tick advance (the R2449/R2433 ordering law) "
        "through the shipped driver src/os/export_R2635.py to 405727B at tick "
        "2676 with queue=CURRENT and queue_drifted=(none), and "
        "check_export_consistency read pass=21 fail=0 VERDICT PASS with the "
        "three CEO-visible lines derived rather than typed. state_fold --check "
        "read FOLD-CLEAR at 72304B against the 78500B gate with margin 6196, 71 "
        "live log lines and the archive present, after fold 707 took the file "
        "74852B -> 66265B at a true round-block boundary (items 2..9, the "
        "complete R2673 and R2674 blocks ending on the R2674 push line) with 7 "
        "tokens carried verbatim and the archive VERIFIED; ledger_lines --check "
        "read VERDICT CLEAN with new_missing none and new_orphan none. The debt "
        "gate now names product-face-R2684 first=yes on queue head "
        "state/queue/tech.md line 680 prefix AC-PNAL1 with claimable 14 and the "
        "queue floor FLOOR-MET 5/5, 14/10, 10/10, and NO battery, because this "
        "window moved no product src byte and the registry is unmoved at 658 "
        "suites / 4924 criteria re-measured by import, so the next window owes a "
        "PRODUCT face rather than a battery.",
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2684p_")
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
