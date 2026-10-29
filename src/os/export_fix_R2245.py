"""R2245 export fix: the two defects check_export_consistency caught.

1. export_ts must be an ISO8601 timestamp with a zone offset; the closeout
   wrote a naive local time (the R2244 precedent carries +08:00).
2. the results tick row still carried the previous tick (2244).

Targeted surgery, every other byte kept, verified by re-parsing.
"""

import datetime
import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
STATE = os.path.join(BASE, "state.json")


def main():
    with io.open(STATE, "rb") as handle:
        state = json.loads(handle.read().decode("utf-8"))
    tick = int(state["tick"])
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        text = handle.read()
    before = json.loads(text)

    stamp = datetime.datetime.now().astimezone().replace(
        microsecond=0).isoformat()
    text = re.sub(r'"export_ts": "[^"]*"',
                  lambda match: '"export_ts": %s' % json.dumps(stamp),
                  text, count=1)

    old_head = None
    for row in before["results"]:
        if len(row) == 2 and row[0].isdigit() and row[1] == "OSLoop 执行 tick":
            old_head = row[0]
    if old_head is None:
        raise SystemExit("E_ANCHOR: tick row not found")
    pattern = r'"%s"(\s*,\s*"OSLoop 执行 tick")' % re.escape(old_head)
    if len(re.findall(pattern, text)) != 1:
        raise SystemExit("E_ANCHOR: tick row literal is not unique")
    text = re.sub(pattern, lambda match: '"%d"%s' % (tick, match.group(1)),
                  text, count=1)

    after = json.loads(text)
    tick_rows = [row for row in after["results"]
                 if len(row) == 2 and row[1] == "OSLoop 执行 tick"]
    if (after["export_ts"] != stamp or not tick_rows
            or tick_rows[0][0] != str(tick)):
        raise SystemExit("E_VERIFY: export fix did not land")
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("FIX ts=%s tick_row=%s bytes=%d"
          % (after["export_ts"], tick_rows[0][0],
             len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())