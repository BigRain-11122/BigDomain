"""R2588 export consistency repair: refresh the derived blocks from disk.

The check_export_consistency checker recomputes self_drive from the live state
log and expects exactly one tick row carrying the current tick. This face asks
that shipped module for its own derivation rather than reimplementing it, so the
export and the checker can never drift apart about the same tree.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import check_export_consistency as C  # noqa: E402

TICK_LABEL = "OSLoop 执行 tick"


def main(argv):
    derived, state, doc, _pat = C.recompute()
    path = C.P_EXPORT
    tick = str(state.get("tick"))

    doc["self_drive"] = dict(derived)
    for key in ("queue_main_open", "queue_tech_open", "queue_explore_open"):
        doc.setdefault("queue", {})[key] = derived[key]

    label = None
    for row in doc.get("results") or []:
        if isinstance(row, list) and len(row) >= 2 and row[1] == TICK_LABEL:
            label = row[1]
            row[0] = tick
    if label is None:
        doc.setdefault("results", []).append([tick, TICK_LABEL])

    out = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    execute = "--execute" in argv
    print("EXPORT derived_window=%s lines=%d sub=%d tick=%s bytes=%d "
          "execute=%s" % (derived["window"],
                          derived["log_lines_in_window"],
                          derived["substantive_non_idle_mention_lines"],
                          tick, len(out), execute))
    if not execute:
        return 0
    io.open(path, "wb").write(out)
    back = json.loads(io.open(path, "rb").read().decode("utf-8"))
    rows = [r for r in back["results"]
            if isinstance(r, list) and len(r) >= 2 and r[1] == TICK_LABEL]
    ok = (len(rows) == 1 and str(rows[0][0]) == tick
          and back["self_drive"] == derived)
    print("READBACK ok=%s tick_row=%s" % (ok, rows[0][0] if rows else None))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))