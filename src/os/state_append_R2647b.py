"""state_append_R2647b - the R2647 push and export receipt.

The numbers below were read off the commands this window ran: the push range,
the commit hashes on both sides, the export byte count and the consistency
summary.
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

LINES = [
    "R2647 push and export: git push origin main SUCCEEDED (12b73533..c56b8608"
    " main -> main), which delivered BOTH the adopted birth-site repair"
    " fd21c734 that had been local-only at open and this window own closeout"
    " c56b8608; git rev-parse then read HEAD equal to origin/main at c56b8608"
    " with an empty git status, so the green leg, the kept red leg, the"
    " regenerated matrix, the closed battery row and the opened successor are"
    " all delivered. The export was refreshed AFTER the state append and after"
    " the tick advance (the R2449/R2433 ordering law) through"
    " src/os/export_R2635.py to 403545 bytes at tick 2645 with queue=CURRENT"
    " and queue_drifted=(none), and check_export_consistency read pass=21"
    " fail=0 VERDICT PASS with the three CEO lines derived rather than typed."
    " state_fold --check read FOLD-CLEAR at 72953B against the 78500B gate with"
    " margin 5547 and 87 log lines after fold 697, and ledger_lines --check"
    " read rounds_without_ledger none. The debt gate now names"
    " product-face-R2647 first=yes on the queue head state/queue/tech.md:662"
    " prefix AC-EDWY1 and NO battery is owed because the registry is unmoved at"
    " 649 suites / 4870 criteria and no product src byte moved.",
]


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    if not isinstance(state.get("log"), list):
        print("E_APPEND_NO_LOG")
        return 3
    state["tick"] = int(state.get("tick", 0)) + 1
    for line in LINES:
        state["log"].append(line)
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    before = len(raw.encode("utf-8"))
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        check = fh.read()
    reread = json.loads(check.decode("utf-8"))
    ok = (len(reread["log"]) == len(state["log"])
          and reread["tick"] == state["tick"])
    print("APPEND tick=%d lines=%d bytes %d -> %d readback=%s"
          % (state["tick"], len(LINES), before, len(check),
             "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
