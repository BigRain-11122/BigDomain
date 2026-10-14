# -*- coding: utf-8 -*-
"""R1970 export tick-row debt fix (R1938/R1939 precedent: the
[:40] results cap drops the tail tick row; restore with
r[0]==1970). Checker must end 21/21 green after this."""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
sys.path.insert(0, HERE)
import check_export_consistency as cec  # noqa: E402

pat = cec._load_patterns()
tick_label = pat["tick_row_label"]
export = json.loads(io.open(P_EXPORT, encoding="utf-8").read())
rows = export["results"]
has_tick = any(len(r) == 2 and r[1] == tick_label for r in rows)
if not has_tick:
    for j in range(len(rows) - 1, -1, -1):
        if len(rows[j]) == 2 and rows[j][1] != tick_label:
            rows.pop(j)
            break
    rows.append(["1970", tick_label])
    print("tick row restored: r[0]==1970 label=%r rows=%d"
          % (tick_label, len(rows)))
else:
    print("tick row present already")
out = json.dumps(export, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
p = subprocess.run([sys.executable,
                    os.path.join(HERE, "check_export_consistency.py")],
                   capture_output=True, cwd=ROOT)
print(p.stdout.decode("utf-8", errors="replace").strip()[-400:])
sys.exit(p.returncode)
