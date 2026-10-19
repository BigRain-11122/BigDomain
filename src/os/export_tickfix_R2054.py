# export_tickfix_R2054.py - drop the stray R2053 tick row from the
# export results array so the checker's exactly-one-tick-row law holds
# (the R2053 flush did the same for its own 2052 predecessor). Raw-text
# edit, json.loads validates before write-back. Pure ASCII source.
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
stray = ('    ],' + NL +
         '    [' + NL +
         '      "2053",' + NL +
         '      "' + TICK_LABEL + '"' + NL +
         '    ],' + NL +
         '    [' + NL +
         '      "R2051",')
repl = '    ],' + NL + '    [' + NL + '      "R2051",'
if text.count(stray) != 1:
    sys.exit("FATAL: stray tick anchor hit count %d"
             % text.count(stray))
text = text.replace(stray, repl, 1)

doc = json.loads(text)
ticks = [r[0] for r in doc["results"] if r[0].isdigit()]
if ticks != ["2054"]:
    sys.exit("FATAL: tick rows %r" % (ticks,))

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)

print("TICKFIX-OK rows=%d ticks=%r" % (len(doc["results"]), ticks))