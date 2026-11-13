"""R2703 push receipt line: the measured push and the re-derived export."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "R2703 push and export: git push origin main read 86aaeb2b..a3fcc6be main -> "
    "main and git rev-parse read HEAD equal to origin/main at a3fcc6be, so the "
    "adopted green leg, its measured bytes, the independent criteria recount of "
    "4954, the refused-then-re-derived fold 717, the restamped matrix at 663 rows, "
    "the fifteen-suite write-sensitive pass on the final committed tree, VERDICT "
    "R2703 PASS, the closed battery row and the opened product face are all "
    "delivered; this receipt line lands in the follow-up commit it describes. The "
    "export was refreshed AFTER the state append and after the tick advance (the "
    "R2449/R2433 ordering law) through the shipped driver src/os/export_R2635.py to "
    "406700B at tick 2695 with queue=CURRENT and queue_drifted=(none), and "
    "check_export_consistency read pass=21 fail=0 VERDICT PASS with the three "
    "CEO-visible lines derived rather than typed; it is re-derived again AFTER this "
    "line so the window own log count agrees with the document it is counted in. "
    "state_fold --check reads FOLD-CLEAR with 39 live log lines and "
    "ledger_lines --check read VERDICT CLEAN. The debt gate now names "
    "product-face-R2703 first=yes on queue head state/queue/tech.md line 684 prefix "
    "AC-PNAS1 with claimable 14, so the next window owes a PRODUCT face rather than "
    "a battery; the queue floor reads FLOOR-MET 5/5, 14/10, 10/10.",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))

    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + LINES

    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)

    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    out = state_io.EOL.join(doc_lines[:end] + inserted + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2703p_")
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
          (tick, after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
