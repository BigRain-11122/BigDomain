"""state_append_R2651_push - the push and export receipt line for R2651."""

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
    "R2651 push and export: git push origin main SUCCEEDED"
    " (c6d79c12..f61b1c54 main -> main) and git rev-parse read HEAD equal to"
    " origin/main at f61b1c54 with an empty git status, so the green battery"
    " evidence, the regenerated matrix, the closed debt row, the seeded"
    " successor and this round state fold are all delivered; this receipt line"
    " lands in the follow-up commit it describes. The export was refreshed"
    " AFTER the state append and after the tick advance through"
    " src/os/export_R2635.py to 403737 bytes at tick 2648 with queue=CURRENT"
    " and queue_drifted=(none), and check_export_consistency read pass=21"
    " fail=0 VERDICT PASS with the three CEO-visible lines derived rather than"
    " typed. state_fold --check read FOLD-CLEAR at 68137B against the 78500B"
    " gate with margin 10363 and 85 log lines after fold 699 (archive"
    " VERIFIED, 13 tokens carried verbatim), and ledger_lines --check read"
    " VERDICT CLEAN with rounds_without_ledger none and ledger_without_round"
    " none. The debt gate now names product-face-R2651 first=yes, so the next"
    " window is a PRODUCT face on the queue head state/queue/tech.md:663"
    " prefix AC-EDWZ1 and owes NO successor battery because this window moved"
    " no product src byte and no registry row.",
]


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
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
