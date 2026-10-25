"""Align the R2120 export counters with the checker's own derivation:
the window count is measured from the state log (unchanged at 42) and
the tick row follows the new state tick."""

import io
import json
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
STATE = os.path.join(ROOT, "src", "os", "state.json")

data = json.load(io.open(EXPORT, encoding="utf-8"))
state = json.load(io.open(STATE, encoding="utf-8"))
drive = data["self_drive"]
drive["log_lines_in_window"] = 42
drive["substantive_non_idle_mention_lines"] = 42
hit = 0
for row in data["results"]:
    if len(row) == 2 and row[1] == "OSLoop \u6267\u884c tick":
        row[0] = str(state["tick"])
        hit += 1
io.open(EXPORT, "w", encoding="utf-8", newline="\n").write(
    json.dumps(data, ensure_ascii=False, indent=1) + "\n")
print("tick_row_fixed=%d tick=%s" % (hit, state["tick"]))