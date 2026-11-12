"""Report and (if needed) repair the indent of this file own R2673 log items.

Idempotent: it measures first, and only rewrites the prefix of rows that carry
an R2673 marker at an indent other than the file own two spaces. Parse equality
is proved before the write and the bytes are read back after it.
"""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
WANT = " " * 2 + '"'


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    before = state_io.parse(text)
    rows = state_io._lf_lines(text)
    odd = []
    fixed = 0
    for index, row in enumerate(rows):
        stripped = row.lstrip(" ")
        if stripped.startswith('"') and "R2673" in row:
            if not row.startswith(WANT):
                odd.append((index, row[:12]))
                rows[index] = WANT + stripped[1:]
                fixed += 1
    for index, head in odd:
        print("ODD line=%d head=%r" % (index + 1, head))
    if not fixed:
        print("INDENT ok already at two spaces")
        return 0
    out = state_io.EOL.join(rows)
    if state_io.parse(out) != before:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2673re_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    print("REINDENT ok fixed=%d bytes=%d" % (fixed, len(payload)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
