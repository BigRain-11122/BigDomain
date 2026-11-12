"""state_append_R2657_push - the push and export receipt line for R2657."""

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
    "R2657 push and export: git push origin main SUCCEEDED"
    " (956acfb9..9f6af910 main -> main) and git rev-parse read HEAD equal to"
    " origin/main at 9f6af910 with an EMPTY git status, so the shipped landing"
    " reader, its six-criteria suite, the amended parent assertion, the"
    " regenerated matrix, the closed board row and the seeded successor are all"
    " delivered; this receipt line lands in the follow-up commit it describes."
    " The export was refreshed AFTER the state append and after the tick"
    " advance (the R2449/R2433 ordering law) through src/os/export_R2635.py to"
    " 404808 bytes at tick 2652 with queue=CURRENT and queue_drifted=(none),"
    " and check_export_consistency read pass=21 fail=0 VERDICT PASS with the"
    " three CEO-visible lines derived rather than typed; the queue block was"
    " then landed through queue_export_gate_wire --execute to 403740 bytes at"
    " gate=CURRENT with drifted=(none) and the consistency check re-read 21/21"
    " PASS. state_fold --check read FOLD-CLEAR at 76590B against the 78500B"
    " gate with margin 1910 and 98 live log lines, and ledger_lines --check"
    " read VERDICT CLEAN with rounds_without_ledger none and"
    " ledger_without_round none. The debt gate names reconcile-battery-R2657"
    " first=yes at the pre-registered 652 suites / 4888 criteria, so the next"
    " window owes that FULL battery on the committed tree BEFORE any further"
    " product byte, and the queue head this window leaves behind is"
    " state/queue/tech.md:665 prefix AC-EDXB1.",
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
    print("APPEND-RECEIPT tick=%d lines=%d bytes %d -> %d readback=%s"
          % (reread["tick"], len(LINES), before, len(check),
             "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
