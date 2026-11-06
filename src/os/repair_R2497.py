"""repair_R2497 - relabel the RESULT row a failed driver run left behind.

Cause, disclosed rather than swept: the first export_R2497 run happened while
the state append was still failing (a wrong decisions.md path), so the driver
inserted this round's RESULT row stamped with the OLD tick 2496. The corrected
run then found the RESULT text already present and did not insert a new row, so
the document kept results[0] = ["2496", <R2497 RESULT>] and the driver's own
read-back self-check (which compares results[0][0] with the live tick) read
ok=False. The row's TEXT is right; only its label is stale. This repair sets the
label of every row carrying this round's RESULT text to the live tick, proves
the change by reading back, and writes nothing else.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2497 as driver  # noqa: E402

EXPORT = os.path.join(os.path.dirname(os.path.dirname(BASE)),
                      "docs", "status-export.json")
STATE = os.path.join(BASE, "state.json")


def main(argv):
    execute = "--execute" in argv
    state = json.load(io.open(STATE, encoding="utf-8"))
    tick = str(state["tick"])
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    rows = data.get("results") or []
    hits = [i for i, row in enumerate(rows)
            if isinstance(row, list) and len(row) >= 2
            and row[1] == driver.base.RESULT]
    stale = [i for i in hits if str(rows[i][0]) != tick]
    print("PLAN tick=%s result_rows=%d stale_labels=%d"
          % (tick, len(hits), len(stale)))
    if not stale:
        print("DRY RUN nothing_to_repair wrote=no")
        return 0
    for index in stale:
        rows[index][0] = tick
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if not execute:
        print("DRY RUN wrote=no")
        return 0
    tmp = EXPORT + ".r2497.tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(tmp, EXPORT)
    back = json.load(io.open(EXPORT, encoding="utf-8"))
    ok = (all(str(row[0]) == tick for row in back["results"]
              if isinstance(row, list) and len(row) >= 2
              and row[1] == driver.base.RESULT))
    print("WRITTEN bytes=%d readback=%s" % (os.path.getsize(EXPORT), ok))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))