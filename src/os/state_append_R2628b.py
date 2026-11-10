"""R2628 follow-up append: the push and export receipt line.

The round commit and its delivery are recorded after they happened, with the
numbers read back rather than predicted.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "R2628 push and export: git push origin main SUCCEEDED (fa5d4a7f..6631572f "
    "main -> main) and git rev-parse read HEAD equal to origin/main at "
    "6631572f with an empty git status after the commit, so the whole window "
    "is delivered; this line lands in the follow-up commit it describes. The "
    "export was refreshed AFTER the state append and after the fold (the "
    "R2449/R2433 ordering law) through the shipped driver to 402021 bytes at "
    "tick 2629 with queue=CURRENT and queue_drifted=(none), and "
    "check_export_consistency read pass=21 fail=0 VERDICT PASS with "
    "export_ts 2026-11-11T06:43:19+08:00. state_fold --check read FOLD-CLEAR "
    "at 76703B against the 78500B gate with margin 1797 and 99 log lines "
    "after fold 686 archived the complete R2627 block (items 93..96) at a "
    "true round-block boundary with the archive VERIFIED and ledger_lines "
    "--check reading CLEAN. The debt gate now names product-face-R2628 "
    "first=yes at open=42 with no battery owed, so the next window owes that "
    "product face on queue head state/queue/tech.md:653 prefix AC-EDMI1 "
    "before any battery.",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    item_indent = None
    for line in lines[start + 1:end]:
        if line.strip().startswith('"'):
            item_indent = len(line) - len(line.lstrip(" "))
            break
    if item_indent is None:
        print("REFUSED no item line to measure the indent")
        return 6
    inserted = [" " * item_indent + json.dumps(item, ensure_ascii=False)
                for item in LINES]
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2628b_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok bytes=%d log_len=%d layout_ok=%s"
          % (after["bytes"], after["log_len"], after["layout_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
