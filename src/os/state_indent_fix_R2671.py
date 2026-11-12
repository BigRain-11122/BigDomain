"""R2671 birth-site repair: the appended log items carry the file own indent.

MEASURED: state_io.ITEM_INDENT is 16 while this file own log items are
indented by 2, so the two items this window appended landed at 16 and the
shipped fold layout reader counted 102 item lines against a log of 104. The
repair rewrites exactly those two lines at the file own prefix and proves the
document still parses with the same log length and tick.
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
MARK = 'R2671 '


def main():
    raw = state_io.read_raw(PATH)
    text = state_io.decode(raw)
    lines = text.split("\r\n")
    before = state_io.parse(text)
    fixed = 0
    for index, row in enumerate(lines):
        if row.startswith(" " * 16 + '"' + MARK):
            lines[index] = "  " + row.lstrip(" ")
            fixed += 1
    out = "\r\n".join(lines)
    after = state_io.parse(out)
    if after != before:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2671fix_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    report = state_io.report(PATH)
    print("REPAIR ok fixed=%d tick=%s log_len=%d bytes=%d"
          % (fixed, after["tick"], report["log_len"], report["bytes"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
