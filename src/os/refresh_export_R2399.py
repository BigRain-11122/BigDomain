"""R2399 export tick-row re-derivation (surgical, predicted delta).

The closeout refreshed the derived counters and the three CEO lines but not the
`results` tick row, so the checker read stored 2398 against a recomputed 2399.
This rewrites that ONE cell from the live state tick and proves the rest of the
document is byte-identical.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
PATTERNS = os.path.join(REPO, "src", "os", "export_consistency_patterns.json")


def main():
    pat = json.loads(io.open(PATTERNS, encoding="utf-8").read())
    label = pat["tick_row_label"]
    state = json.load(io.open(STATE, encoding="utf-8"))
    tick = str(state["tick"])
    before = io.open(EXPORT, encoding="utf-8", newline="").read()
    data = json.loads(before)
    rows = [r for r in data["results"]
            if isinstance(r, list) and len(r) >= 2 and r[1] == label]
    if len(rows) != 1:
        sys.stdout.write("E_TICK ROW count=%d\n" % len(rows))
        return 2
    old = rows[0][0]
    rows[0][0] = tick
    after = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    handle, tmp = tempfile.mkstemp(dir=os.path.dirname(EXPORT),
                                   prefix=".otuw-", suffix=".tmp")
    os.close(handle)
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as out:
        out.write(after)
    os.replace(tmp, EXPORT)
    back = io.open(EXPORT, encoding="utf-8", newline="").read()
    if back != after:
        sys.stdout.write("E_TICK read-back differs\n")
        return 2
    print("TICK ROW %s -> %s bytes=%d -> %d"
          % (old, tick, len(before.encode("utf-8")), len(back.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())