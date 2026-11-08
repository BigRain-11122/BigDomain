"""R2580: increment state.json tick 2579 -> 2580 in place."""

import io
import json
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")


def main():
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    pattern = re.compile(r'(\n\s*"tick"\s*:\s*)2579(\s*,)')
    hits = pattern.findall(text)
    if len(hits) != 1:
        raise SystemExit("tick anchor not unique (%d)" % len(hits))
    text = pattern.sub(r"\g<1>2580\g<2>", text, count=1)
    payload = json.loads(text)
    assert payload["tick"] == 2580
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("TICK 2579 -> %d bytes=%d crlf=%d" % (
        payload["tick"], len(text.encode("utf-8")), text.count("\r")))
    return 0


if __name__ == "__main__":
    sys.exit(main())