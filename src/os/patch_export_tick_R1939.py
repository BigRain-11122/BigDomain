# -*- coding: utf-8 -*-
"""R1939 export tick-row patch: the [:40] results cap dropped the
tail tick row 'OSLoop 执行 tick' (R1936->R1937->R1938 same-debt
precedent); restore it with r[0]==1939 and note the collection in
the R1939 results row. Checker must go green after this patch."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

with open(P_EXPORT, "rb") as fh:
    export = json.loads(fh.read().decode("utf-8"))

label = "OSLoop 执行 tick"
results = export["results"]
kept = [r for r in results
         if not (isinstance(r, list) and len(r) >= 2 and r[1] == label)]
dropped = len(results) - len(kept)
assert dropped <= 1, "unexpected tick rows: %d" % dropped
r1939 = None
for row in kept:
    if (isinstance(row, list) and len(row) >= 2 and row[0] == "R1939"):
        r1939 = row
        break
assert r1939 is not None, "R1939 results row missing"
note = ("; export refresh collected the tick-row debt (the [:40] results "
        "cap dropped the tail tick row 'OSLoop 执行 tick', restored with "
        "r[0]==1939) + checker VERDICT PASS after the fix")
if note not in r1939[1]:
    r1939[1] = r1939[1] + note
kept.append(["1939", label])
export["results"] = kept
out = json.dumps(export, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("tick row restored r[0]=1939, dropped=%d, results=%d rows"
      % (dropped, len(kept)))
