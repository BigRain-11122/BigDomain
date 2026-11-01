"""One-off fold for R2328: the R2314 and R2315 whole round blocks.

state.json measured 78496B against the 78500B gate (margin 4B), so the
closeout of this window MUST fold before it appends. The window starts at
line 5 on purpose: lines 1..4 are existing fold markers, and folding one
would re-name a token list that belongs to an earlier window. Whole round
blocks only, so the ledger gate cannot read a split, and the rounds chosen
carry CLOSED stamps so the fold creates no residue (the law measured at
R2311 and repaired by hand four times).

usage: python fold_R2328.py [--execute]
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402

WINDOW_START = 2
WINDOW_END = 12
FOLD_NO = 620
RESERVE = 11000

state = json.load(io.open(os.path.join(ROOT, "src", "os", "state.json"),
                          encoding="utf-8"))
items = state["log"][WINDOW_START - 1:WINDOW_END]
body = "\n".join(items)
tokens = sorted(set(SF.PAT.findall(body)))
summary = ("Fold R2328: log lines %d..%d (three older fold markers plus the "
           "R2314 and R2315 whole round blocks) moved verbatim to the "
           "archive; window tokens: %s"
           % (WINDOW_START, WINDOW_END, " ".join(tokens)))
print("tokens=%d summary=%dB" % (len(tokens), len(summary)))
report = SF.fold(ROOT, "R2328", FOLD_NO, WINDOW_START, WINDOW_END, summary,
                 reserve=RESERVE, execute=("--execute" in sys.argv))
for key in sorted(report):
    if key in ("post_text",):
        continue
    print("%s=%r" % (key, report[key]))