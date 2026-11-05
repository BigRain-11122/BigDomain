"""R2472 second fold: the closeout append pushed the file back over the gate.

Window 1..17 covers the previous fold summary plus the WHOLE R2462 block (the
push line at item 8) and the WHOLE R2463 block (the self-heal line at item 17);
item 18 opens R2464, so the boundary is a true round-block boundary.
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
END = 17
kept_head = log[END] if len(log) > END else ""
tokens = set()
for line in log[0:END]:
    tokens |= set(SF.PAT.findall(line))
summary = ("Fold R2472b: log items 1..%d moved verbatim into the monthly "
           "archive at a true round-block boundary after the R2472 closeout append "
           "(the whole R2462 and R2463 blocks plus the R2472a fold summary); tokens "
           "covered %s, none missing." % (END, ",".join(sorted(tokens))))

print("kept_head=%r" % kept_head[:60])
if "--execute" in sys.argv[1:]:
    result = SF.fold(ROOT, "R2472b", 656, 1, END, summary, execute=True)
else:
    plan, _text = SF.plan_fold(raw, state, 1, END, summary)
    result = dict(plan)
    result["mode"] = "dry-run"
for key in ("window_lines", "tokens_total", "tokens_missing", "gate_ok",
            "predicted_bytes", "margin", "round_split", "mode", "post_bytes",
            "predicted_eq_actual", "would_fail"):
    if key in result:
        print("%s=%s" % (key, result[key]))