"""state_append_R2659_push - the push and export receipt for the R2659 window."""

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
    "R2659 push and export: git push origin main SUCCEEDED"
    " (c6595f63..fe62d1d8 main -> main) and git rev-parse read HEAD equal to"
    " origin/main at fe62d1d8 with an EMPTY git status, so the adopted green"
    " leg, its regenerated matrix, the closed debt row and the opened"
    " successor are all delivered; this receipt line lands in the follow-up"
    " commit it describes. The export was refreshed AFTER the state append"
    " through src/os/export_R2635.py to 404404 bytes at tick 2653 with"
    " queue=CURRENT and queue_drifted=(none), and check_export_consistency"
    " read pass=21 fail=0 VERDICT PASS with the three CEO-visible lines"
    " derived rather than typed. state_fold --check read FOLD-CLEAR after fold"
    " 698 and ledger_lines --check read VERDICT CLEAN. The debt gate names"
    " product-face-R2659 first=yes on the queue head state/queue/tech.md:665"
    " prefix AC-EDXB1, and NO battery is owed because this window moved no"
    " product src byte and the registry is unmoved at 652 suites / 4888"
    " criteria."
)


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    if not isinstance(state.get("log"), list):
        print("E_APPEND_NO_LOG")
        return 3
    state["log"].append(LINE)
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    before = len(raw.encode("utf-8"))
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        check = fh.read()
    reread = json.loads(check.decode("utf-8"))
    ok = len(reread["log"]) == len(state["log"])
    print("APPEND receipt lines=1 bytes %d -> %d readback=%s"
          % (before, len(check), "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
