"""Remove the stale R2069 tick row so exactly one tick row remains.

The tick row is a single marker whose id must equal state.tick
(checker rule); the R2069 closeout inserted a second one. Raw-text
surgery, json validates before write-back. Pure ASCII source.
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

sys.path.insert(0, HERE)
with io.open(os.path.join(HERE, "export_consistency_patterns.json"),
             "r", encoding="utf-8") as _f:
    LABEL = json.load(_f)["tick_row_label"]

with io.open(EXPORT, "r", encoding="utf-8", newline="") as f:
    text = f.read()
NL = "\r\n" if "\r\n" in text else "\n"

block = ("    [" + NL + '      "2069",' + NL + '      "' + LABEL + '"' +
         NL + "    ]," + NL)
count = text.count(block)
if count != 1:
    sys.exit("FATAL: stale tick block count %d" % count)
text = text.replace(block, "", 1)

doc = json.loads(text)
rows = [r[0] for r in doc["results"] if len(r) > 1 and r[1] == LABEL]
if rows != ["2070"]:
    sys.exit("FATAL: tick rows %r" % (rows,))

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("TICK-ROW-FIX-OK tick_rows=%r results=%d" % (rows, len(doc["results"])))