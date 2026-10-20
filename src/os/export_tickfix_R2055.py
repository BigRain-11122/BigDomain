# export_tickfix_R2055.py - keep exactly one tick row in the export
# results array: the R2055 flush prepended its own tick row while the
# previous round's "2054" tick row was still in place. Remove the stale
# one by raw-text surgery (no full rewrite), then validate with the
# consistency checker. Pure ASCII source.
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

with io.open(os.path.join(HERE, "export_consistency_patterns.json"),
             "r", encoding="utf-8") as f:
    LABEL = json.load(f)["tick_row_label"]

with io.open(EXPORT, "r", encoding="utf-8", newline="") as f:
    text = f.read()

NL = "\r\n" if "\r\n" in text else "\n"
block = (NL + '    [' + NL +
         '      "2054",' + NL +
         '      "' + LABEL + '"' + NL +
         '    ],')
if text.count(block) != 1:
    raise SystemExit("FATAL: stale tick block hit count %d"
                     % text.count(block))
text = text.replace(block, "", 1)

doc = json.loads(text)
rows = [r for r in doc["results"] if r[1] == LABEL]
if len(rows) != 1 or rows[0][0] != "2055":
    raise SystemExit("FATAL: tick rows after fix %r" % (rows,))

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("TICKFIX-OK results_rows=%d tick_rows=%d"
      % (len(doc["results"]), len(rows)))