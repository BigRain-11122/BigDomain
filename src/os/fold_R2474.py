"""R2474 fold: window 1..84 at a true round-block boundary.

Line 1 is the previous fold summary and travels with it; line 84 is the R2473
push line, the last item of that round, and line 85 opens R2474.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_fold as SF

ROOT = os.path.dirname(os.path.dirname(BASE))
path = SF.state_path(ROOT)
raw, state = SF.read_state(path)
log = state["log"]
END = 84
kept_head = log[END] if len(log) > END else ""
tokens = set()
for line in log[0:END]:
    tokens |= set(SF.PAT.findall(line))
summary = ("Fold R2474: log items 1..%d moved verbatim into the monthly archive "
           "at a true round-block boundary (the whole R2465..R2473 blocks plus "
           "the previous fold summary); tokens covered %s, none missing."
           % (END, ",".join(sorted(tokens))))

print("kept_head=%r" % kept_head[:60])
if "--execute" in sys.argv[1:]:
    result = SF.fold(ROOT, "R2474", 658, 1, END, summary, execute=True)
else:
    plan, _text = SF.plan_fold(raw, state, 1, END, summary)
    result = dict(plan)
    result["mode"] = "dry-run"
for key in ("window_lines", "tokens_total", "tokens_missing", "gate_ok",
            "predicted_bytes", "margin", "round_split", "mode", "post_bytes",
            "predicted_eq_actual", "would_fail"):
    if key in result:
        print("%s=%s" % (key, result[key]))