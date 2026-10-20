"""Drop the stale 2057 tick row from docs/status-export.json (R2058)."""

import io
import json
import re

PATH = "docs/status-export.json"
PAT = "src/os/export_consistency_patterns.json"

with io.open(PAT, encoding="utf-8") as fh:
    label = json.load(fh)["tick_row_label"]

with io.open(PATH, encoding="utf-8", newline="") as fh:
    text = fh.read()

before = json.loads(text)
rows_before = [r[0] for r in before["results"]
               if isinstance(r, list) and len(r) >= 2 and r[1] == label]
print("tick rows before:", rows_before)
assert rows_before.count("2058") == 1, rows_before
assert "2057" in rows_before, rows_before

pattern = r'    \[\r?\n      "2057",\r?\n      "[^"]*"\r?\n    \],\r?\n'
text, n = re.subn(pattern, "", text, count=1)
assert n == 1, "tick row block not found"

doc = json.loads(text)
rows = [r[0] for r in doc["results"]
        if isinstance(r, list) and len(r) >= 2 and r[1] == label]
assert rows == ["2058"], rows
assert doc["results"][0][0] == "R2058"
assert doc["results"][1][0] == "2058"

with io.open(PATH, "w", encoding="utf-8", newline="") as fh:
    fh.write(text)

print("tick row pruned; results=%d" % len(doc["results"]))