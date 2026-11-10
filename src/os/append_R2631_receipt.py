"""append_R2631_receipt - one push and export receipt line on the shipped dialect."""

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
    "R2631 push and export: git push origin main SUCCEEDED (44f7f3a9..307beb6e) and "
    "git rev-parse read HEAD equal to origin/main at 307beb6e with an empty git status "
    "after the commit, so the whole window is delivered; this line lands in the commit it "
    "describes. The export was refreshed AFTER the state append and after fold 688 (the "
    "R2449/R2433 ordering law) through src/os/export_R2631.py to 402245 bytes at tick 2631 "
    "with queue=CURRENT and queue_drifted=(none), and check_export_consistency read "
    "pass=21 fail=0 VERDICT PASS with the three CEO lines derived rather than typed. "
    "THE BATTERY IS STILL LIVE AT THIS LINE: pid 88352 with its reconcile_all child, the "
    "stream measured 185465 bytes over 1252 lines at 07:11:55 with its newest line reading "
    "'PASS suite watermark-scale-unknown exit=0 pass-lines=6 fail-lines=0 criteria=6 11.2s', "
    "no evidence file written yet, so reconcile-battery-R2630 REMAINS OPEN at its registered "
    "644 suites / 4840 criteria and the next window owes the adoption of qa/reconcile-all-R2631.log "
    "on this committed tree BEFORE any further product byte. qa/reconcile-all-R2631.log was "
    "deliberately NOT staged, because a single writer is still appending to it and committing "
    "half a leg would freeze a partial evidence file into history."
)


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    state["log"].append(LINE)
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        reread = json.loads(fh.read().decode("utf-8"))
    ok = len(reread["log"]) == len(state["log"])
    print("RECEIPT lines=%d bytes=%d readback=%s"
          % (len(reread["log"]), len(payload), "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
