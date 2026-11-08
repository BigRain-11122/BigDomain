"""R2583 fold driver #2: fold the ORPHANED 'R2574 tokens:' line that the
previous fold left live, at the 1-BASED window the shipped predicate uses.

The first attempt of this window passed 8..14 with 0-BASED indices, so the
tool folded items 8..13 (1-based) and left the R2574 tokens line in the live
log - disclosed in the round log and repaired here rather than hidden.
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402

START = 9
END = 9
FOLD_NO = 658

state = json.load(open(os.path.join(REPO, "src", "os", "state.json"),
                       encoding="utf-8"))
items = state["log"][START - 1:END]
tokens = sorted(set(SF.PAT.findall("\n".join(items))))
summary = ("R2583 fold of log item %d (the R2574 tokens line left live by this "
           "window first fold attempt) into the archive; all %d tokens "
           "preserved verbatim in this line: %s"
           % (START, len(tokens), " ".join(tokens)))
raw, payload = SF.read_state(SF.state_path(REPO))
plan, _folded = SF.plan_fold(raw, payload, START, END, summary)
for _ in range(4):
    if not plan["tokens_missing"]:
        break
    tokens = sorted(set(tokens) | set(plan["tokens_missing"]))
    summary = ("R2583 fold of log item %d (the R2574 tokens line left live by "
               "this window first fold attempt) into the archive; all %d "
               "tokens preserved verbatim in this line: %s"
               % (START, len(tokens), " ".join(tokens)))
    plan, _folded = SF.plan_fold(raw, payload, START, END, summary)
print("PLAN tokens=%d missing=%d round_split=%s gate_ok=%s predicted=%d "
      "margin=%d" % (plan["tokens_total"], len(plan["tokens_missing"]),
                     plan["round_split"], plan["gate_ok"],
                     plan["predicted_bytes"], plan["margin"]))
if "--execute" in sys.argv and not plan["tokens_missing"]:
    result = SF.fold(REPO, "R2583", FOLD_NO, START, END, summary, execute=True)
    print("FOLD bytes=%d->%d tokens=%d ok=%s"
          % (result.get("before_bytes", 0), result.get("after_bytes", 0),
             result.get("tokens_total", 0), result.get("token_ok")))