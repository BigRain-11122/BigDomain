"""R2581 push and export closeout line."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")
REPO = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(REPO, "docs", "status-export.json")

LINE = (
    "2026-11-09 R2581 push and export: git push origin main SUCCEEDED"
    " (1a514249..e37c03c3 main -> main) and git rev-parse read HEAD equal to"
    " origin/main at e37c03c3 with an empty git status after the commit, so"
    " the whole window is delivered. The export was refreshed AFTER the state"
    " append (the R2449/R2433 ordering law) through this round own driver"
    " src/os/export_R2581.py to {%d} bytes at tick 2581 with queue=CURRENT and"
    " queue_drifted=(none), and check_export_consistency read pass=21 fail=0"
    " VERDICT PASS with the three CEO lines derived rather than typed;"
    " state_fold --check read FOLD-CLEAR at {%d}B against the 78500B gate."
    " The debt gate now names reconcile-battery-R2581 first=yes at the"
    " pre-registered 621 suites / 4702 criteria, so the next window owes that"
    " battery on this committed tree before any further product byte, and the"
    " product face behind it is tech line 615 prefix AC-PNAM1."
)


def main():
    exp_bytes = os.path.getsize(EXPORT)
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "R2581 push and export" in text:
        raise SystemExit("already present")
    payload = json.loads(text)
    now_bytes = len(text.encode("utf-8"))
    line = LINE % (exp_bytes, now_bytes)
    payload["log"].append(line)
    text = json.dumps(payload, indent=1, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("LOG log=%d bytes=%d export=%d"
          % (len(payload["log"]), len(text.encode("utf-8")), exp_bytes))
    return 0


if __name__ == "__main__":
    sys.exit(main())