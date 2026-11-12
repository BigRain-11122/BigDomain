"""state_append_R2661_push - the one receipt line for this window own push.

Kept deliberately short because the state fold margin after the product block
is small; the numbers here were read off the commands that produced them.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import general_writer_dialect_audit as GWDA  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")

LINE = (
    "R2661 push and export: git push origin main SUCCEEDED (492f0435..33d04c21"
    " main -> main) and git rev-parse read HEAD equal to origin/main at"
    " 33d04c21 with an EMPTY git status, so the shipped landing reader, its"
    " sixth-wave suite, the regenerated matrix, the closed board row and the"
    " seeded AC-EDXC1 successor are all delivered; this receipt lands in the"
    " follow-up commit it describes. The export was refreshed AFTER the state"
    " append and after the tick advance (the R2449/R2433 ordering law) through"
    " src/os/export_R2635.py to 404908 bytes at tick 2654 with queue=CURRENT"
    " and queue_drifted=(none), and check_export_consistency read pass=21"
    " fail=0 VERDICT PASS with the three CEO lines derived rather than typed."
    " The debt gate names reconcile-battery-R2661 first=yes at the"
    " pre-registered 653 suites / 4894 criteria, so the next window owes that"
    " FULL battery on the committed tree BEFORE any further product byte, and"
    " the queue head this window leaves behind is state/queue/tech.md:666"
    " prefix AC-EDXC1."
)


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    if not isinstance(state.get("log"), list):
        print("E_APPEND_NO_LOG")
        return 3
    state["log"].append(LINE)
    state["tick"] = int(state.get("tick", 0)) + 1
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    before = len(raw.encode("utf-8"))
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        check = fh.read()
    reread = json.loads(check.decode("utf-8"))
    ok = reread["log"][-1] == LINE and reread["tick"] == state["tick"]
    print("APPEND tick=%d line_bytes=%d bytes %d -> %d readback=%s"
          % (state["tick"], len(LINE.encode("utf-8")), before, len(check),
             "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
