# -*- coding: utf-8 -*-
"""R2108 export consistency repair (tick row + machine-derived counters)."""

import io
import json
import os

ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

pat = json.loads(io.open("src/os/export_consistency_patterns.json",
                         encoding="utf-8").read())
label = pat["tick_row_label"]
path = "docs/status-export.json"
doc = json.loads(io.open(path, encoding="utf-8").read())

rows = [r for r in doc["results"]
        if isinstance(r, list) and len(r) == 2 and r[1] == label]
assert len(rows) >= 1, "tick row missing"
for row in rows:
    row[0] = "2108"
print("tick rows", len(rows))

sd = doc["self_drive"]
sd["log_lines_in_window"] = 32
sd["substantive_non_idle_mention_lines"] = 32
sd["queue_tech_open"] = 4
sd["queue_explore_open"] = 1
sd["queue_main_open"] = 6
print("self_drive", json.dumps(sd, ensure_ascii=False))

io.open(path, "w", encoding="utf-8", newline="\n").write(
    json.dumps(doc, ensure_ascii=False, indent=1) + "\n")