# -*- coding: utf-8 -*-
"""R1971 export tick-row repair: the 41st-row cap in
closeout_R1971.py trimmed the tick row (latent bug in the
R1970 closeout pattern, first triggered at 41 rows). Restore:
drop the oldest R-row (tail), append the tick row = 1971.
Re-verify with checker + gauge + eol."""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

d = json.load(io.open(P_EXPORT, encoding="utf-8"))
rs = d["results"]
tick_label = None
# recover the tick label from the checker pattern module
sys.path.insert(0, HERE)
import check_export_consistency as cec
_, _, _, pat = cec.recompute()
tick_label = pat["tick_row_label"]
assert tick_label, "tick label unavailable"

have = [r for r in rs if isinstance(r, list) and len(r) == 2
        and r[1] == tick_label]
assert len(have) == 0, "tick row unexpectedly present"
# drop the oldest tail R-row, append the tick row
assert rs[-1][0].startswith("R"), "tail row is not an R-row"
rs = rs[:-1]
rs.append(["1971", tick_label])
assert len(rs) == 40, "row count != 40"
d["results"] = rs
out = json.dumps(d, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("tick row restored: ['1971', %r] -> 40 rows" % tick_label)

for cmd in (
    [sys.executable, os.path.join(HERE, "check_export_consistency.py")],
    [sys.executable, os.path.join(HERE, "logs_toolkit.py"), "gauge"],
    [sys.executable, os.path.join(HERE, "logs_toolkit.py"), "eol"],
):
    p = subprocess.run(cmd, capture_output=True, cwd=ROOT)
    tail = [l for l in p.stdout.decode("utf-8", errors="replace")
            .splitlines() if l.strip()][-2:]
    print("verify rc=%d :: %s" % (p.returncode, " | ".join(tail)))
    if p.returncode != 0:
        sys.exit(2)
print("REPAIR-OK R1971")
