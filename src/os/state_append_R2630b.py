"""R2630b state append: ONE compact push and export receipt line.

The main block was committed and pushed as 2392f838; this line records the
receipt without pushing the state file past the 78500-byte fold gate.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINE = (
    "R2630 push and export: git push origin main SUCCEEDED (99d24dc2.."
    "2392f838) and HEAD equals origin/main with an empty status, so the whole "
    "window is delivered; this line lands in the commit it describes. The "
    "export was refreshed AFTER the state append and after fold 687 through "
    "src/os/export_R2630.py to 402513 bytes at tick 2630 with queue=CURRENT "
    "and queue_drifted=(none), and check_export_consistency read pass=21 "
    "fail=0 VERDICT PASS. The gate now names reconcile-battery-R2630 first=yes "
    "at the pre-registered 644 suites / 4840 criteria, so the next window owes "
    "that battery on this committed tree BEFORE any further product byte."
)


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + [LINE]
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
    inserted = [" " * item_indent + json.dumps(LINE, ensure_ascii=False)]
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2630b_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d layout_ok=%s"
          % (data["tick"], after["bytes"], after["log_len"],
             after["layout_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
