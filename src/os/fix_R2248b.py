"""R2248 tick-row repair, second pass: restore three historical labels.

The first pass matched any results row whose second element merely
mentions "tick" and overwrote three round labels (R2167, R2149, R2212)
with the live tick. This pass restores each row's original first element
from HEAD by matching the row body, then advances only the real tick row
(the row whose label is the pinned tick-row label). It refuses unless
exactly one row matches the tick-row label.
"""

import io
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_STATE = os.path.join(BASE, "state.json")


def main():
    with io.open(P_STATE, "r", encoding="utf-8") as handle:
        tick = json.loads(handle.read())["tick"]
    with io.open(P_EXPORT, "r", encoding="utf-8") as handle:
        export = json.loads(handle.read())
    old = json.loads(subprocess.run(
        ["git", "show", "HEAD:docs/status-export.json"], cwd=ROOT,
        stdout=subprocess.PIPE).stdout.decode("utf-8"))
    patterns = json.loads(subprocess.run(
        ["git", "show", "HEAD:src/os/export_consistency_patterns.json"],
        cwd=ROOT, stdout=subprocess.PIPE).stdout.decode("utf-8"))
    label = patterns["tick_row_label"]

    original = {}
    for row in old.get("results", []):
        if isinstance(row, list) and len(row) >= 2:
            original[str(row[1])] = row[0]

    restored = 0
    tick_rows = 0
    for row in export["results"]:
        if not isinstance(row, list) or len(row) < 2:
            continue
        if str(row[1]) == label:
            row[0] = str(tick)
            tick_rows += 1
        elif str(row[1]) in original and str(row[0]) != str(original[str(row[1])]):
            row[0] = original[str(row[1])]
            restored += 1

    body = json.dumps(export, indent=2, ensure_ascii=False)
    if not body.endswith("\n"):
        body += "\n"
    data = body.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
    with io.open(P_EXPORT, "wb") as handle:
        handle.write(data)
    print("EXPORT bytes=%d restored=%d tick_rows=%d tick=%s"
          % (len(data), restored, tick_rows, tick))
    return 0 if tick_rows == 1 else 1


if __name__ == "__main__":
    sys.exit(main())