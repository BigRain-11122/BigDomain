"""R2679 push receipt line append (follow-up commit)."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")

LINE = (
    "R2679 push and export: git push origin main read 2e4f5f83..63415af5 "
    "main -> main and git rev-parse read HEAD equal to origin/main at "
    "63415af5 with an EMPTY git status, so the shipped unnameable-label face, "
    "its six-criteria suite, the limits probe, the two byte-identical evidence "
    "legs, the regenerated matrix, the closed board row, the seeded "
    "AC-PNAK1..AC-PNAK6 row and the two debt rows are all delivered; this "
    "receipt line lands in the follow-up commit it describes. The export was "
    "refreshed AFTER the state append and after the tick advance (the "
    "R2449/R2433 ordering law) through the shipped driver "
    "src/os/export_R2635.py to 405697B at tick 2671 with queue=CURRENT and "
    "queue_drifted=(none), and check_export_consistency read pass=21 fail=0 "
    "VERDICT PASS with the three CEO-visible lines derived rather than typed. "
    "state_fold --check read FOLD-CLEAR at 60961B against the 78500B gate "
    "with margin 17539 and 54 live log lines. The debt gate now names "
    "reconcile-battery-R2679 first=yes at the pre-registered 657 suites / "
    "4918 criteria, so the next window owes that FULL battery on the "
    "committed tree BEFORE any further product byte, and the queue head this "
    "window leaves behind is state/queue/tech.md line 679 prefix AC-PNAK1.")


def main():
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "R2679 push and export" in text:
        raise SystemExit("already present")
    payload = json.loads(text)
    payload["log"].append(LINE)
    text = json.dumps(payload, indent=1, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("RECEIPT appended log=%d tick=%d bytes=%d crlf=%d" % (
        len(payload["log"]), payload["tick"],
        len(text.encode("utf-8")), text.count("\r")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
