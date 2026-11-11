"""state_append_R2633b - the R2633 push and export receipt.

Every number was read off the tree after the delivery commit.
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
    "R2633 push and export: git push origin main SUCCEEDED (d394be93..0f55d444"
    " main -> main) and git rev-parse read HEAD equal to origin/main at"
    " 0f55d444 with an empty git status after the commit, so the product"
    " window is delivered; this receipt line lands in the closeout commit it"
    " describes. The export was refreshed AFTER the state append and after"
    " fold 690 (the R2449/R2433 ordering law) through this round own driver"
    " src/os/export_R2633.py to 402838 bytes at tick 2634 with queue=CURRENT"
    " and queue_drifted=(none), the queue block was then landed through"
    " queue_export_gate_wire --execute (401790 bytes, gate=CURRENT), and"
    " check_export_consistency read pass=21 fail=0 VERDICT PASS with the"
    " three CEO lines derived rather than typed. state_fold --check read"
    " FOLD-CLEAR at 76205B against the 78500B gate with margin 2295 and 101"
    " live lines, and ledger_lines --check read VERDICT CLEAN with"
    " new_missing none and new_orphan none. The debt gate now names"
    " reconcile-battery-R2633 first=yes: this window moved one registry row"
    " and one product src file, so the R2168 mixed-tree rule puts the FULL"
    " battery at the pre-registered 645 suites / 4846 criteria on the"
    " committed tree BEFORE any further product byte, and the queue head the"
    " window leaves behind is state/queue/tech.md:658 prefix AC-EDWT1.",
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
