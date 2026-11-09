"""state_append_R2594b - the push and export line, landing in the commit it
describes (the R2449/R2433 ordering law).

Read paths write nothing and read no clock. Layout round-trip is proved before
any byte is written.
"""

import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

LINE = (
    "R2594 push and export: git push origin main SUCCEEDED "
    "(137ad477..13300a12 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 13300a12 with an empty git status after the commit, so the "
    "whole window is delivered; this line lands in the follow-up commit it "
    "describes. The export was refreshed AFTER the state append (the R2449/"
    "R2433 ordering law) to %d bytes at tick 2594 with queue=CURRENT and "
    "queue_drifted=(none), and check_export_consistency read pass=21 fail=0 "
    "VERDICT PASS with the three CEO lines derived rather than typed (current "
    "names this round own fold, latest artifact reads the 12850B evidence file "
    "and the next milestone names product-face-R2593 inside a 48h window). "
    "state_fold --check read FOLD-CLEAR at 74960B against the 78500B gate with "
    "margin 3540 after fold 663 (items 68..75, 6 tokens, archive VERIFIED) and "
    "ledger_lines --check read VERDICT CLEAN with rounds_without_ledger and "
    "ledger_without_round both none. HONEST: the shipped export driver own "
    "console line still reads ok=False although it wrote the file and the "
    "independent checker reads PASS 21/0 - the driver self-report is disclosed "
    "rather than dressed up - and queue_row --check still reads pre-existing "
    "VIOLATIONS on rows that predate this window (tech 524, 537, 634 and an "
    "explore row), none of them touched here.")


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    doc = json.loads(text)
    if json.dumps(doc, ensure_ascii=False, indent=1) != text:
        print("REFUSED layout round-trip mismatch")
        return 3
    export_bytes = len(io.open(EXPORT, "rb").read())
    doc["log"].append(LINE % export_bytes)
    out = json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = back["log"][-1] == doc["log"][-1]
    print("APPEND log_rows=%d before=%dB after=%dB ok=%s export=%dB"
          % (len(back["log"]), len(text), len(out), ok, export_bytes))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())