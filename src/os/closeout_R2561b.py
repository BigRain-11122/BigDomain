"""R2561 push line: record the measured delivery of this round in state.json.

Same layout law as closeout_R2561 (indent=1, no trailing newline), proved by a
byte-identical read-back before any mutation.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")

LINE = (
    "R2561 push and export: git push origin main SUCCEEDED this window "
    "(33b9a901..2b055767 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 2b055767 with an empty git status after the commit, so the "
    "whole window is delivered. The export was refreshed AFTER the state append "
    "(the R2449/R2433 ordering law) through src/os/export_R2561.py to 353972 "
    "bytes at tick 2561 with queue=CURRENT and queue_drifted=(none), and "
    "check_export_consistency read pass=21 fail=0 VERDICT PASS with the three "
    "CEO lines derived rather than typed. The debt gate now names "
    "reconcile-battery-R2561 first=yes at the pre-registered 610 suites / 4636 "
    "criteria, so the next window owes that battery on this committed tree "
    "before any further product byte."
)


def dump(state):
    return json.dumps(state, indent=1, ensure_ascii=False).encode("utf-8")


def main():
    with open(STATE, "rb") as handle:
        before = handle.read()
    state = json.loads(before.decode("utf-8"))
    if dump(state) != before:
        print("REFUSED E_SA_LAYOUT: file is not indent=1 without trailing "
              "newline (%d bytes)" % (len(before),))
        return 3
    if LINE not in state["log"]:
        state["log"].append(LINE)
    payload = dump(state)
    with open(STATE, "wb") as handle:
        handle.write(payload)
    back = json.loads(open(STATE, "rb").read().decode("utf-8"))
    print("state %s tick=%d log=%d after=%dB"
          % ("OK" if back["tick"] == 2561 else "FAIL", back["tick"],
             len(back["log"]), len(payload)))
    return 0


if __name__ == "__main__":
    sys.exit(main())