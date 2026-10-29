"""R2248 layout + tick-row repair (idempotent, run after the closeout).

Two defects were caught by the project's own checkers at closeout:
  - state_io --check read CANON-DRIFT because json.dumps(indent=2) puts
    log items at 4 spaces while the canonical habit is 16;
  - check_export_consistency read results.tick_row stored='2247' because
    the tick row in the export was not advanced with the tick.
Both are repaired here on the current files, and the reading is printed
so the fix is proven rather than claimed.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))

P_STATE = os.path.join(BASE, "state.json")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

ITEM_INDENT = 16
BASE_INDENT = 4


def reindent_log(text):
    lines = text.split("\n")
    out = []
    inside = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('"log": ['):
            inside = True
            out.append(line)
            continue
        if inside and stripped == "]":
            inside = False
            out.append(line)
            continue
        if inside and (len(line) - len(line.lstrip(" "))) == BASE_INDENT:
            out.append(" " * ITEM_INDENT + stripped)
            continue
        out.append(line)
    return "\n".join(out)


def write_text(path, text):
    data = text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
    with io.open(path, "wb") as handle:
        handle.write(data)
    return len(data)


def main():
    with io.open(P_STATE, "r", encoding="utf-8") as handle:
        text = handle.read()
    state = json.loads(text)
    body = reindent_log(json.dumps(state, indent=2, ensure_ascii=False))
    if not body.endswith("\n"):
        body += "\n"
    size = write_text(P_STATE, body)
    print("STATE bytes=%d tick=%d" % (size, state["tick"]))

    with io.open(P_EXPORT, "r", encoding="utf-8") as handle:
        export = json.loads(handle.read())
    patched = 0
    for row in export.get("results", []):
        if isinstance(row, list) and len(row) >= 2 and "tick" in str(row[1]):
            row[0] = str(state["tick"])
            patched += 1
    body = json.dumps(export, indent=2, ensure_ascii=False)
    if not body.endswith("\n"):
        body += "\n"
    size = write_text(P_EXPORT, body)
    print("EXPORT bytes=%d tick_rows_patched=%d" % (size, patched))
    return 0 if patched == 1 else 1


if __name__ == "__main__":
    sys.exit(main())