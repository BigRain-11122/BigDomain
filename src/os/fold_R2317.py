"""One-off fold for R2317: whole blocks R2302 and R2303 into the archive.

The closeout would cross the 78500B waterline (75553B with a 2947B margin),
so the fold runs BEFORE the append through the shipped state_fold law. The
window starts at line 2 on purpose: line 1 is the existing fold marker, and
folding it would demand that its whole token list be re-named in a new
summary. Whole round blocks only, so the ledger gate cannot read a split.
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
WINDOW_END = 8
FOLD_NO = 616
RESERVE = 7000

state = json.load(io.open(os.path.join(ROOT, "src", "os", "state.json"),
                          encoding="utf-8"))
items = state["log"][WINDOW_START - 1:WINDOW_END]
body = "\n".join(items)
tokens = sorted(set(SF.PAT.findall(body)))
summary = ("Fold R2317: log lines %d..%d (the R2302 and R2303 whole round "
           "blocks) moved verbatim to the archive; window tokens: %s"
           % (WINDOW_START, WINDOW_END, " ".join(tokens)))
print("tokens=%d summary=%dB" % (len(tokens), len(summary)))
report = SF.fold(ROOT, "R2317", FOLD_NO, WINDOW_START, WINDOW_END, summary,
                 reserve=RESERVE, execute=True)
for key in sorted(report):
    if key in ("post_text",):
        continue
    print("%s=%r" % (key, report[key]))