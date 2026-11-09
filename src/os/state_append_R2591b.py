"""state_append_R2591b - append the push and export line for this round.

The tick is NOT advanced: this line records the delivery of the same round.
Layout is indent=1 with no trailing newline, proved by round-trip.
"""

import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINE = (
    "2026-11-09 R2591 push and export: git push origin main SUCCEEDED "
    "(f41231c2..c88283f0 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at c88283f0 with an empty git status after the commit, so the whole "
    "window is delivered; this line lands in the follow-up commit it describes. The "
    "export was refreshed AFTER the state append and after the fold (the R2449/R2433 "
    "ordering law) through the shipped canonical driver src/os/export_R2431.py to "
    "398116 bytes at tick 2591 with queue=CURRENT and queue_drifted=(none), and "
    "check_export_consistency read pass=21 fail=0 VERDICT PASS with the three CEO lines "
    "derived rather than typed. state_fold --check read FOLD-CLEAR at 77107B against "
    "the 78500B gate with margin 1393 after fold 660 (windows 67..74, tokens 6, archive "
    "VERIFIED), and ledger_lines --check read VERDICT CLEAN with rounds_without_ledger "
    "and ledger_without_round both none. The debt gate now names product-face-R2591 "
    "first=yes on the queue head state/queue/tech.md:625 prefix AC-PNAE1, and no battery "
    "is owed because the registry is unmoved at 627 suites / 4738 criteria and no "
    "product src byte moved, so the next window owes that product face."
)


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    doc = json.loads(text)
    if json.dumps(doc, ensure_ascii=False, indent=1) != text:
        print("REFUSED layout round-trip mismatch")
        return 3
    doc["log"].append(LINE)
    out = json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = back["log"][-1] == LINE and back["tick"] == doc["tick"]
    print("APPEND tick=%d log_rows=%d before=%dB after=%dB ok=%s"
          % (back["tick"], len(back["log"]), len(text), len(out), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())