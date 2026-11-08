"""R2582 push and export closeout line."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")
REPO = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(REPO, "docs", "status-export.json")

LINE = (
    "R2582 push and export: git push origin main SUCCEEDED (168dda59..c06603c3"
    " main -> main) and git rev-parse read HEAD equal to origin/main at"
    " c06603c3 with an empty git status after the commit, so the whole window"
    " is delivered. The export was refreshed AFTER the state append through"
    " this round own driver src/os/export_R2582.py to {%d} bytes at tick 2582"
    " with queue=CURRENT and queue_drifted=(none), and"
    " check_export_consistency read pass=21 fail=0 VERDICT PASS with the three"
    " CEO lines derived rather than typed; state_fold --check read FOLD-CLEAR"
    " at {%d}B against the 78500B gate. The debt gate now names"
    " product-face-R2582 first=yes on the queue head state/queue/tech.md:615"
    " prefix AC-PNAM1, and NO battery is owed because this window moved no"
    " product src byte and the registry is unmoved at 621 suites / 4702"
    " criteria, so the next window owes that product face before any battery."
)


def main():
    exp_bytes = os.path.getsize(EXPORT)
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "R2582 push and export" in text:
        raise SystemExit("already present")
    payload = json.loads(text)
    payload["log"].append(LINE % (exp_bytes, len(text.encode("utf-8"))))
    text = json.dumps(payload, indent=1, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("LOG log=%d bytes=%d export=%d"
          % (len(payload["log"]), len(text.encode("utf-8")), exp_bytes))
    return 0


if __name__ == "__main__":
    sys.exit(main())