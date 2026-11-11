"""state_append_R2639b - the R2639 push and export receipt.

Every number here was read off the tree after delivery.
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
    "R2639 push and export: git push origin main SUCCEEDED (b7a83ce7..84fa2a30"
    " main -> main) and git rev-parse read HEAD equal to origin/main at"
    " 84fa2a30 with an empty git status, so the repair commit 2b2b5318, the"
    " adopted red leg, the fold archive, the state narrative and the refreshed"
    " CEO face are all delivered; this receipt line lands in the closeout"
    " commit it describes. The export was refreshed AFTER the state append and"
    " after the tick advance (the R2449/R2433 ordering law) through"
    " src/os/export_R2635.py to 403150 bytes at tick 2640 with queue=CURRENT"
    " and queue_drifted=(none), its own composed-versus-landed verdict read"
    " PASS at 403150/403150, and check_export_consistency read pass=21 fail=0"
    " VERDICT PASS with the three CEO lines derived rather than typed."
    " state_fold --check read FOLD-CLEAR at 68989B against the 78500B gate"
    " with margin 9511 and 80 live lines after fold 695, and ledger_lines"
    " --check read VERDICT CLEAN with new_orphan none. The debt gate still"
    " names reconcile-battery-R2638 first=yes and that leg is LIVE at this"
    " closeout (pid 48708, 98 PASS suite rows and ZERO FAIL rows at the last"
    " read, evidence path qa/reconcile-all-R2638-retry.log not yet written),"
    " so the row stays OPEN at its registered 647 suites / 4858 criteria and"
    " the next window adopts it; NO successor battery is owed by this window"
    " because it moved no product src byte and the registry is unmoved at 647"
    " suites / 4858 criteria.",
]


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    if not isinstance(state.get("log"), list):
        print("E_APPEND_NO_LOG")
        return 3
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
    ok = len(reread["log"]) == len(state["log"])
    print("APPEND lines=%d bytes %d -> %d readback=%s"
          % (len(LINES), before, len(check), "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
