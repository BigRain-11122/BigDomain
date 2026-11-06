"""R2504 fold: window 1..87 at a true round-block boundary.

Line 1 is the previous fold summary and travels with it; line 87 is the last
item of the R2502 block and line 88 opens R2503, so the fold never splits a
round. Every token in the window is carried into the one summary line.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_fold as SF

ROOT = os.path.dirname(os.path.dirname(BASE))
END = 87

raw, state = SF.read_state(SF.state_path(ROOT))
log = state["log"]
kept_head = log[END] if len(log) > END else ""
tokens = set()
for line in log[0:END]:
    tokens |= set(SF.PAT.findall(line))
summary = ("Fold R2504: log items 1..%d moved verbatim into the monthly archive "
           "at a true round-block boundary (the whole R2495..R2502 blocks plus "
           "the previous fold summary); tokens covered %s, none missing."
           % (END, ",".join(sorted(tokens))))

print("kept_head=%r" % kept_head[:70])
if "--execute" in sys.argv[1:]:
    result = SF.fold(ROOT, "R2504", 2504, 1, END, summary, execute=True)
else:
    plan, _text = SF.plan_fold(raw, state, 1, END, summary)
    result = dict(plan)
    result["mode"] = "dry-run"
for key in ("window_lines", "tokens_total", "tokens_missing", "gate_ok",
            "predicted_bytes", "margin", "round_split", "mode", "post_bytes",
            "predicted_eq_actual", "would_fail"):
    if key in result:
        print("%s=%s" % (key, result[key]))