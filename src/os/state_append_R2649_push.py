"""state_append_R2649_push - the R2649 push and export receipt line."""

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
    "R2649 push and export: git push origin main SUCCEEDED"
    " (fbb28bc1..c87dd8b3 main -> main) and git rev-parse read HEAD equal to"
    " origin/main at c87dd8b3 with an empty git status, so the shipped words,"
    " the suite, the regenerated matrix, the closed board row and the opened"
    " successor are all delivered; this receipt line lands in the follow-up"
    " commit it describes. The export was refreshed AFTER the state append and"
    " after the tick advance through src/os/export_R2635.py to 404164 bytes at"
    " tick 2647 with queue=CURRENT and queue_drifted=(none), and"
    " check_export_consistency read pass=21 fail=0 VERDICT PASS with the three"
    " CEO lines derived rather than typed; the refreshed export and the matrix"
    " were committed in c87dd8b3, so this follow-up carries only this line."
    " state_fold --check read FOLD-CLEAR at 70351B against the 78500B gate with"
    " margin 8149 and 84 log lines after fold 698 (archive VERIFIED), and the"
    " ledger fold summary carried all 18 window tokens verbatim. The debt gate"
    " now names reconcile-battery-R2649 first=yes at the pre-registered 650"
    " suites / 4876 criteria, so the next window owes that full battery on the"
    " committed tree BEFORE any further product byte, and the queue head it"
    " leaves behind is state/queue/tech.md:663 prefix AC-EDWZ1.")


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    state["log"].append(LINE)
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    before = len(raw.encode("utf-8"))
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        check = fh.read()
    reread = json.loads(check.decode("utf-8"))
    ok = reread["log"][-1] == LINE
    print("APPEND receipt bytes %d -> %d readback=%s"
          % (before, len(check), "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
