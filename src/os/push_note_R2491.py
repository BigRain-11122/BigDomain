"""R2491 one-off: record the delivered commit in the state log."""

import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
sys.path.insert(0, SRC)

import state_io  # noqa: E402

LINE = (
    "2026-11-06 R2491 push: git push origin main SUCCEEDED this window "
    "(874aba06..fb9c8659 main -> main) and git rev-parse read HEAD at "
    "fb9c8659 with an empty git status afterwards, so all three R2491 commits "
    "- the product face fb9bff6c, the birth-site repair 50a7d360 and the "
    "closeout fb9c8659 - are delivered and nothing is left staged. The export "
    "was re-derived through the shipped driver AFTER the state append (the "
    "R2449/R2433 ordering law) and its queue block was then landed through the "
    "shipped gate wire, so check_export_consistency reads pass=21 fail=0 at "
    "state_tick=2491 with the queue face CURRENT at claimable 5/10/10."
)

state = json.load(io.open(PATH, encoding="utf-8", newline=""))
if state["log"] and state["log"][-1] == LINE:
    print("already appended")
    sys.exit(0)
state["log"].append(LINE)
text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
tmp = PATH + ".tmp"
io.open(tmp, "wb").write(state_io.canon(text).encode("utf-8"))
os.replace(tmp, PATH)
back = json.load(io.open(PATH, encoding="utf-8", newline=""))
print("APPEND log_items=%d tick=%d bytes=%d"
      % (len(back["log"]), back["tick"], os.path.getsize(PATH)))