"""R2821 closeout: append the round log lines and bump the tick through state_io.

ASCII source only; the narrative strings live in tmp/log-R2821.json (data file).
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io

STATE = os.path.join(REPO, "src", "os", "state.json")
LINES = os.path.join(REPO, "tmp", "log-R2821.json")


def main():
    payload = json.loads(io.open(STATE, encoding="utf-8").read())
    lines = json.loads(io.open(LINES, encoding="utf-8").read())
    payload["tick"] = int(payload.get("tick") or 0) + 1
    payload.setdefault("log", []).extend(lines)
    state_io.write_document(STATE, payload)
    after = json.loads(io.open(STATE, encoding="utf-8").read())
    print("TICK %d LOG %d SIZE %d" % (after["tick"], len(after["log"]),
                                      os.path.getsize(STATE)))
    print("TAIL %s" % after["log"][-1][:60])
    return 0


if __name__ == "__main__":
    sys.exit(main())
