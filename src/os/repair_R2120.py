"""Roll back the R2120 closeout bookkeeping written with a bad battery
regex (the log carries an inner short RUNNER PASS line). ASCII only."""

import io
import json
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
STATE = os.path.join(ROOT, "src", "os", "state.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")

state = json.load(io.open(STATE, encoding="utf-8"))
log = state.get("log", [])
removed = []
while log and log[-1].startswith("R2120"):
    removed.append(log.pop()[:40])
    state["tick"] = int(state.get("tick", 0)) - 1
io.open(STATE, "w", encoding="utf-8", newline="\n").write(
    json.dumps(state, ensure_ascii=False, indent=1) + "\n")


def unflip(path, marker):
    lines = io.open(path, encoding="utf-8").read().splitlines(True)
    out = []
    hit = False
    for line in lines:
        if not hit and line.startswith("- [x] " + marker):
            line = "- [ ] " + line[len("- [x] "):]
            cut = line.find(" [done 2026-10-25 R2120]")
            if cut >= 0:
                line = line[:cut] + "\n"
            hit = True
        out.append(line)
    io.open(path, "w", encoding="utf-8", newline="\n").write("".join(out))
    return hit


b = unflip(BACKLOG, "P3 explore \u961f\u5934\u8ba4\u9886\uff08R2120")
e = unflip(EXPLORE, "P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97\u8ba4\u9886"
                   "\uff08R2120\uff09")
print("removed=%d tick=%d backlog=%r explore=%r"
      % (len(removed), state["tick"], b, e))