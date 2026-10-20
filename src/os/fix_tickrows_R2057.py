# fix_tickrows_R2057.py - remove the stale R2056 tick row from the export
# results array so exactly one tick row (the current 2057) remains, per
# check_export_consistency's single-tick-row rule. Byte-surgical (no full
# json.dumps rewrite). Pure ASCII source.
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normcase(os.path.normpath(
    os.path.join(HERE, "..", "..")))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

with io.open(os.path.join(HERE, "export_consistency_patterns.json"),
             "r", encoding="utf-8") as f:
    TICK_LABEL = json.load(f)["tick_row_label"]

with io.open(EXPORT, "r", encoding="utf-8", newline="") as f:
    text = f.read()
NL = "\r\n" if "\r\n" in text else "\n"

block = (NL + '    [' + NL + '      "2056",' + NL +
         '      "' + TICK_LABEL + '"' + NL + '    ],')
if text.count(block) != 1:
    sys.exit("FATAL: stale tick block hit count %d"
             % text.count(block))
text = text.replace(block, "", 1)

doc = json.loads(text)
rows = [r for r in doc["results"]
        if isinstance(r, list) and len(r) >= 2 and r[1] == TICK_LABEL]
if len(rows) != 1 or str(rows[0][0]) != "2057":
    sys.exit("FATAL: tick rows after fix %r" % ([r[0] for r in rows],))

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("TICKROW-FIX-OK rows=%d tick=%s bytes=%d"
      % (len(doc["results"]), rows[0][0],
         len(text.encode("utf-8"))))