"""R2140 closeout: append the round log lines to src/os/state.json.

Single-purpose, ASCII source. The narrative is kept in a sibling
payload file so no shell quoting is involved.
"""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")
PAYLOAD = os.path.join(BASE, "r2140_log.json")


def main():
    with io.open(PAYLOAD, "rb") as handle:
        lines = json.loads(handle.read().decode("utf-8"))
    with io.open(STATE, "rb") as handle:
        raw = handle.read().decode("utf-8")
    data = json.loads(raw)
    for line in lines:
        data["log"].append(line)
    data["tick"] = 2140
    out = json.dumps(data, ensure_ascii=False, indent=2)
    blob = (out.replace("\n", "\r\n") + "\r\n").encode("utf-8")
    with io.open(STATE, "wb") as handle:
        handle.write(blob)
    print("tick=%d log_lines=%d bytes=%d" %
          (data["tick"], len(data["log"]), len(blob)))


if __name__ == "__main__":
    main()