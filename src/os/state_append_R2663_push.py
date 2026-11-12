"""state_append_R2663_push - the push and export receipt for R2663."""

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
    "R2663 push and export: git push origin main SUCCEEDED (3f78e2cb..c2c2bcd0"
    " main -> main) and git rev-parse read HEAD equal to origin/main at"
    " c2c2bcd0 with an EMPTY git status, so the birth-site repair, the red first"
    " leg facts, the fold and the opened retry row are all delivered; this"
    " receipt line lands in the follow-up commit it describes. The export was"
    " refreshed AFTER the state append (the R2449/R2433 ordering law) through"
    " src/os/export_R2635.py to 404620 bytes at tick 2656 with queue=CURRENT and"
    " queue_drifted=(none), and check_export_consistency read pass=21 fail=0"
    " VERDICT PASS - its earlier 19/2 reading was the fold moving ten live log"
    " lines and is named here rather than smoothed. The debt gate still names"
    " reconcile-battery-R2661 first=yes at 653 suites / 4894 criteria and that"
    " row STAYS OPEN because the first leg carries one FAIL row and the green"
    " retry has not run; the queue head this window leaves behind is"
    " state/queue/tech.md:666 prefix AC-EDXC1.",
]


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
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
