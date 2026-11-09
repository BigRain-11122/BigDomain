"""state_append_R2592b - append the push and export closeout line."""

import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-09 R2592 push and export: git push origin main SUCCEEDED "
    "(31eb4612..83c714f3 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 83c714f3 with an empty git status after the commit, so the "
    "whole window is delivered; this line lands in the follow-up commit it "
    "describes. The export was refreshed AFTER the state append and after the "
    "fold (the R2449/R2433 ordering law) through the shipped canonical driver "
    "src/os/export_R2431.py to 398262 bytes at tick 2592 with queue=CURRENT and "
    "queue_drifted=(none), and check_export_consistency read pass=21 fail=0 "
    "VERDICT PASS with the three CEO lines derived rather than typed. "
    "state_fold --check read FOLD-CLEAR at 75882B against the 78500B gate with "
    "margin 2618 after fold 661 (items 14..23, tokens 8, archive VERIFIED), "
    "and ledger_lines --check read VERDICT CLEAN with rounds_without_ledger and "
    "ledger_without_round both none. The debt gate now names "
    "reconcile-battery-R2592 first=yes at the pre-registered 628 suites / 4744 "
    "criteria, so the next window owes that battery on this committed tree "
    "BEFORE any further product byte, and the product face behind it is tech "
    "line 627 prefix AC-PNAF1.",
]


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    doc = json.loads(text)
    if json.dumps(doc, ensure_ascii=False, indent=1) != text:
        print("REFUSED layout round-trip mismatch")
        return 3
    doc["log"].extend(LINES)
    out = json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = back["log"][-1] == LINES[-1]
    print("APPEND log_rows=%d before=%dB after=%dB ok=%s"
          % (len(back["log"]), len(text), len(out), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())