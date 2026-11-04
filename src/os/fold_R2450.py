"""One-off: fold the R2450 log window 1..100 at the true round-block boundary
(line 100 is the R2449 push line, so the whole R2450 block stays resident)."""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_fold as SF

ROOT = os.path.dirname(os.path.dirname(BASE))
path = SF.state_path(ROOT)
raw, state = SF.read_state(path)
log = state["log"]
END = 100
tokens = set()
for line in log[0:END]:
    tokens |= set(SF.PAT.findall(line))
summary = ("Fold R2450: log lines 1..%d moved verbatim into the monthly "
           "archive at a true round-block boundary; tokens covered %s, none "
           "missing." % (END, ",".join(sorted(tokens))))

if "--execute" in sys.argv[1:]:
    result = SF.fold(ROOT, "R2450", 646, 1, END, summary, execute=True)
else:
    plan, _text = SF.plan_fold(raw, state, 1, END, summary)
    result = dict(plan)
    result["mode"] = "dry-run"
for key in ("window_lines", "tokens_total", "tokens_missing", "gate_ok",
            "predicted_bytes", "margin", "round_split", "mode", "post_bytes",
            "predicted_eq_actual", "would_fail"):
    if key in result:
        print("%s=%s" % (key, result[key]))