"""R2583 fold driver: fold items 8..14 (the complete R2574 block) at a true
round-block boundary. Prints the plan; --execute runs it.
"""

import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402

START = 8
END = 14
FOLD_NO = 657

state = json.load(open(os.path.join(REPO, "src", "os", "state.json"),
                       encoding="utf-8"))
items = state["log"][START:END + 1]
tokens = sorted(set(SF.PAT.findall("\n".join(items))))
summary = ("R2583 fold of log items %d..%d (the complete R2574 round block ending "
           "on its tokens line) into the archive; all %d tokens preserved "
           "verbatim in this line: %s"
           % (START, END, len(tokens), " ".join(tokens)))
print("SUMMARY %s" % summary[:200])
raw, payload = SF.read_state(SF.state_path(REPO))
plan, _folded = SF.plan_fold(raw, payload, START, END, summary)
for _ in range(4):
    if not plan["tokens_missing"]:
        break
    tokens = sorted(set(tokens) | set(plan["tokens_missing"]))
    summary = ("R2583 fold of log items %d..%d (the complete R2574 round block "
               "ending on its tokens line) into the archive; all %d tokens "
               "preserved verbatim in this line: %s"
               % (START, END, len(tokens), " ".join(tokens)))
    plan, _folded = SF.plan_fold(raw, payload, START, END, summary)
print("PLAN tokens=%d missing=%d round_split=%s gate_ok=%s predicted=%d "
      "margin=%d newline=%r"
      % (plan["tokens_total"], len(plan["tokens_missing"]),
         plan["round_split"], plan["gate_ok"], plan["predicted_bytes"],
         plan["margin"], plan["newline"]))
if "--execute" in sys.argv:
    result = SF.fold(REPO, "R2583", FOLD_NO, START, END, summary, execute=True)
    print("FOLD %s bytes=%d->%d tokens=%d ok=%s archive=%s layout=%s"
          % (result.get("verdict", "?"), result.get("before_bytes", 0),
             result.get("after_bytes", 0), result.get("tokens_total", 0),
             result.get("token_ok"), result.get("archive_verdict"),
             result.get("layout")))