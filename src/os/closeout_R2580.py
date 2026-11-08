"""R2580 closeout: bump the tick and append one heartbeat line."""

import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")
HEART = os.path.join(ROOT, "heartbeat.txt")

ROUND = 2580
BEAT = (
    "2026-11-09T00:15+08:00 R2580 verification: the owed battery went RED"
    " first (4 assertions in three ledger suites) because the R2578 fold"
    " archived the R2568 ledger line while its fold summary stayed live and"
    " NARRATIVE_RE read that summary as a round narrative; repaired in its"
    " birth site with a word-bounded FOLD_SUMMARY_RE guard, six criteria"
    " pre-registered before the code and a shipped suite (1312B, legs=2,"
    " identical=True, adjacent=3), then GREEN at the re-measured 620 suites /"
    " 4696 criteria (1530.0s, zero FAIL rows, independent recount exactly"
    " 4696); matrix 61574B green=620/620 byte-identical, VERDICT R2580 PASS;"
    " debt: battery R2579 closed and product-face-R2580 opened first=yes"
    " naming tech line 626 AC-LKND1; state folded 79225B -> 69827B"
    " (FOLD-CLEAR 8673)."
)


def main():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload["tick"] != ROUND - 1:
        raise SystemExit("unexpected tick %r" % payload["tick"])
    with io.open(HEART, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "R2580 verification" in text:
        raise SystemExit("heartbeat already present")
    if not text.endswith("\n"):
        text += "\n"
    with io.open(HEART, "w", encoding="utf-8", newline="") as handle:
        handle.write(text + BEAT + "\n")
    print("heartbeat lines=%d bytes=%d" % (text.count("\n") + 1,
                                           len((text + BEAT + "\n")
                                               .encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())