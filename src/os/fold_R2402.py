# fold_R2402.py - one fold at a TRUE round-block boundary (log items 1..22 =
# the fold header plus the complete R2389, R2390, R2391 and R2392 blocks, the
# cut landing on R2392's own ledger line so no block is split).
import io
import json
import sys

BASE = "src/os"
sys.path.insert(0, BASE)

import state_fold as SF

START = 1
END = 22
FOLD_NO = 649

raw, state = SF.read_state(BASE + "/state.json")
window = state["log"][START - 1:END]
tokens = set()
for line in window:
    tokens |= set(SF.PAT.findall(line))
summary = ("Fold R2402: 22 early log items moved verbatim into the monthly "
           "archive at a true round-block boundary (the cut lands on R2392's "
           "own ledger line, so no round block is split); tokens covered "
           + ",".join(sorted(tokens)) + ".")

print("WINDOW items=%d content_bytes=%d tokens=%d"
      % (END - START + 1, sum(len(x.encode("utf-8")) for x in window),
         len(tokens)))

plan, _ = SF.plan_fold(raw, state, START, END, summary)
print("PLAN predicted=%d margin=%d gate_ok=%s tokens_missing=%d newline=%s "
      "new_log_len=%d preop=%s"
      % (plan["predicted_bytes"], plan["margin"], plan["gate_ok"],
         len(plan["tokens_missing"]), plan["newline"],
         plan["folded_log_len"], plan["preop_sha16"]))
if plan["tokens_missing"] or not plan["gate_ok"]:
    sys.exit(2)

if "--execute" in sys.argv:
    result = SF.fold(".", "R2402", FOLD_NO, START, END, summary, execute=True)
    print("FOLD executed=%s bytes %d -> %d archive %d -> %d"
          % (result.get("executed"), result.get("before_bytes", -1),
             result.get("after_bytes", -1), result.get("archive_before", -1),
             result.get("archive_after", -1)))
    back = json.load(io.open(BASE + "/state.json", encoding="utf-8"))
    print("READBACK tick=%d log_items=%d" % (back["tick"], len(back["log"])))
else:
    print("DRY RUN, nothing written")