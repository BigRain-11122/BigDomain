"""R2728 export results fix: tick row carries the state tick, round row carries the text."""

import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    os.pardir, os.pardir))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
PATTERNS = os.path.join(ROOT, "src", "os", "export_consistency_patterns.json")

TEXT = ("R2728 MONITORED-WAIT window: the R2725 battery leg is still live at "
        "closeout (652 of 673 suite rows, zero FAIL, no evidence file) and was "
        "not relaunched, so reconcile-battery-R2725 stays open and no verdict "
        "is issued. One artifact landed: src/os/verify_writesensitive.py, a "
        "parameterised consolidation of the three per-window write-sensitive "
        "runners that imports the pinned 15-name set instead of retyping it "
        "(self-check names=15 missing=[] paths_ok=15, commit 39483020). Zero "
        "product points by the Executive Protocol scale.")

with io.open(PATTERNS, encoding="utf-8") as fh:
    label = json.load(fh)["tick_row_label"]
with io.open(EXPORT, encoding="utf-8") as fh:
    doc = json.load(fh)

rows = doc.get("results") or []
# drop the malformed row written by the previous pass (tick in slot 0, prose in slot 1)
rows = [r for r in rows
        if not (isinstance(r, list) and len(r) >= 2 and r[0] == "2724"
                and r[1] != label)]

hits = 0
for row in rows:
    if isinstance(row, list) and len(row) >= 2 and row[1] == label:
        row[0] = "2724"
        hits += 1
if hits != 1:
    print("REFUSED tick row count=%d" % hits)
    raise SystemExit(3)

if not (rows and isinstance(rows[-1], list) and rows[-1][1] == "R2728"):
    rows.append(["R2728", TEXT])
doc["results"] = rows
with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(doc, fh, ensure_ascii=False, indent=1)
    fh.write("\n")
print("RESULTS ok rows=%d tick_row=2724 bytes=%d"
      % (len(rows), os.path.getsize(EXPORT)))
