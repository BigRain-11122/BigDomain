# -*- coding: utf-8 -*-
"""R1946 export tick-row patch: the closeout results cap (insert at
0 -> 41 rows -> [:40]) dropped the tail tick row (the R1938/R1939
patch_export_tick family - the same truncation erratum, third
occurrence). Surgical fix: drop the oldest non-tick row (R1891)
instead and keep the tick row at the tail with tick=1946, then
re-run the F3 consistency checker (must be 21/21 PASS)."""
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
TICK_LABEL = "OSLoop 执行 tick"

with open(P_EXPORT, encoding="utf-8") as fh:
    export = json.load(fh)
rows = export["results"]
has_tick = any(len(r) == 2 and r[1] == TICK_LABEL for r in rows)
assert not has_tick, "tick row already present, nothing to patch"
assert len(rows) == 40, "unexpected results cap: %d" % len(rows)
victim = None
for i in range(len(rows) - 1, -1, -1):
    if len(rows[i]) == 2 and rows[i][1] != TICK_LABEL:
        victim = i
        break
assert victim is not None, "no non-tick row to drop"
dropped = rows.pop(victim)
rows.append(["1946", TICK_LABEL])
with open(P_EXPORT, "wb") as fh:
    fh.write((json.dumps(export, indent=1, ensure_ascii=False)
              + "\n").encode("utf-8"))
print("patched: dropped oldest non-tick row %r, tick row restored"
      " at tail (len=%d)" % (dropped[0], len(rows)))

out_log = os.path.join(ROOT, ".codely-cli", "tmp",
                       "ec1946-postpatch.log")
proc = subprocess.run(
    [sys.executable, "-X", "utf8",
     os.path.join(BASE, "check_export_consistency.py"),
     "--out", out_log],
    cwd=ROOT, capture_output=True)
print(proc.stdout.decode("utf-8", "replace").strip()[-400:])
sys.exit(proc.returncode)
