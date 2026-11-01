import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402
import closeout_R2337_log as L  # noqa: E402

ROUND = "R2337"
LOG = L.LOG

state_path = os.path.join(BASE, "state.json")
raw, state = SF.read_state(state_path)
probe = dict(state)
probe["tick"] = 2337
probe["log"] = list(state["log"]) + LOG
append_bytes = (len((json.dumps(probe, indent=2, ensure_ascii=False) + "\n")
                    .encode("utf-8")) - len(raw))
print("open", len(raw), "append adds", append_bytes, "log", len(state["log"]))

HEAD = "Folded R2336 closeout summary: earlier round blocks moved verbatim to the monthly archive with every round label and its ledger line together; tokens covered: "

best = None
for end in (5, 9, 14, 18, 23, 28, 33, 38, 43):
    window = state["log"][0:end]
    tokens = set()
    for line in window:
        tokens |= set(SF.PAT.findall(line))
    summary = HEAD + " ".join(sorted(tokens))
    if "\n" in summary or "\r" in summary:
        summary = summary.replace("\n", " ").replace("\r", " ")
    plan = SF.fold(ROOT, ROUND, 626, 1, end, summary, execute=False,
                   reserve=append_bytes)
    freed = plan["window_content_bytes"] - len(summary.encode("utf-8"))
    print("1..%-3d tokens=%-4d freed=%-6d predicted=%-6d margin=%-6d clean=%s"
          % (end, len(tokens), freed, plan["predicted_bytes"], plan["margin"],
             not plan["tokens_missing"]))
    if not plan["tokens_missing"] and plan["gate_ok"] and best is None:
        best = (end, summary, plan["predicted_bytes"])
        break

if best is None:
    print("ABORT: no clean net-positive window")
    sys.exit(1)

end, summary, predicted = best
result = SF.fold(ROOT, ROUND, 626, 1, end, summary, execute=True,
                 reserve=append_bytes)
print("fold 1..%d executed predicted=%d" % (end, predicted))

raw2, state2 = SF.read_state(state_path)
state2["tick"] = 2337
state2["log"].extend(LOG)
body = json.dumps(state2, indent=2, ensure_ascii=False) + "\n"
io.open(state_path, "w", encoding="utf-8", newline="\n").write(body)
size = len(body.encode("utf-8"))
print("after append", size, "margin", SF.GATE - size, "log",
      len(state2["log"]))