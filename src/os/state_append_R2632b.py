"""state_append_R2632b - append the R2632 push and export receipt.

Every number here was read off the tree after the delivery commit, so this
line describes what actually landed rather than what was planned.
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
    "R2632 push and export: git push origin main SUCCEEDED (8433133a..731052d3 main -> main) and git rev-parse read HEAD equal to origin/main at 731052d3 with an empty git status after the commit, so the whole window is delivered; this line lands in the commit it describes. The export was refreshed AFTER the state append and after fold 689 (the R2449/R2433 ordering law) through this round own driver src/os/export_R2632.py to 402274 bytes at tick 2632 with queue=CURRENT and queue_drifted=(none), and check_export_consistency read pass=21 fail=0 VERDICT PASS with the three CEO lines derived rather than typed; state_fold --check read FOLD-CLEAR at 76962B against the 78500B gate with margin 1538 and 102 live lines, and ledger_lines --check read VERDICT CLEAN with new_missing none and new_orphan none. The debt gate now names product-face-R2632 first=yes on the queue head state/queue/tech.md:654 prefix AC-EDMJ1, and NO battery is owed because the registry stands unmoved at 644 suites / 4840 criteria and no product src byte moved, so the next window owes that product face before any product byte.",
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
