"""Drop the previous OSLoop tick row from the export results face
(one tick row only, the checker law). Pure ASCII source."""

import io
import json
import re
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EXPORT = os.path.normpath(os.path.join(HERE, "..", "..", "docs",
                                       "status-export.json"))

with io.open(EXPORT, "r", encoding="utf-8", newline="") as f:
    text = f.read()

pat = re.compile(r'    \[\r?\n      "2072",\r?\n      "(?:[^"\\\\]|\\.)*tick'
                 r'(?:[^"\\\\]|\\.)*"\r?\n    \],\r?\n')
text2, n = pat.subn("", text)
if n != 1:
    raise SystemExit("FATAL: stale tick row anchor hit %d" % n)

doc = json.loads(text2)
labels = [r[0] for r in doc["results"]]
if labels.count("2072") != 0 or labels.count("2073") != 1:
    raise SystemExit("FATAL: tick rows %r" % (labels[:4],))

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text2)
print("TRIM-OK head=%r" % (labels[:3],))