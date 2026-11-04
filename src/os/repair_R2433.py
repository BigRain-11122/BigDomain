"""R2433 birth-site repair: one tick row and a self_drive derived from the live state.

Measured at R2433 on the committed R2432 tree: the R2432 ad-hoc export edit
INSERTED a second results row carrying the tick-row label (tick 2432 beside the
surviving tick 2431) and stored a self_drive count taken BEFORE its own state
append (19 lines in window where the live log carries 23), so
check_export_consistency read 18/21 with results.tick_row finding two rows.

This script repairs the DOCUMENT, never the criterion: the surviving tick row is
the one with the largest tick, every other label row is removed, the value is set
to the live state tick, and the self_drive block is re-derived by the shipped
export_R2431.self_drive() callable (no second derivation is written here). The
write is one atomic replace with a read-back proof and the payload change is
printed before it lands.

Usage: python src/os/repair_R2433.py [--execute]
"""
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import check_export_consistency as cec  # noqa: E402
import export_R2431 as exp  # noqa: E402

EXPORT = os.path.join(ROOT, "docs", "status-export.json")
STATE = os.path.join(HERE, "state.json")


def main():
    label = cec._load_patterns()["tick_row_label"]
    state = json.load(io.open(STATE, encoding="utf-8"))
    tick = str(state["tick"])
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    rows = data.get("results") or []

    stamped = [i for i, r in enumerate(rows)
               if isinstance(r, list) and len(r) >= 2 and r[1] == label]
    if not stamped:
        sys.stdout.write("E_R2433 no tick row\n")
        return 3
    keep = max(stamped, key=lambda i: int(rows[i][0]))
    drop = [i for i in stamped if i != keep]
    before_tick = rows[keep][0]
    rows[keep][0] = tick
    for i in reversed(drop):
        rows.pop(i)
    data["results"] = rows

    before_sd = dict(data.get("self_drive") or {})
    sd = exp.self_drive()
    data["self_drive"] = sd
    changed_sd = {k: (before_sd.get(k), sd[k]) for k in sd
                  if before_sd.get(k) != sd[k]}

    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    sys.stdout.write("tick_rows before=%d after=1 kept=%s->%s removed=%s\n"
                     % (len(stamped), before_tick, tick, [rows and i for i in drop]))
    sys.stdout.write("self_drive changed=%s\n" % json.dumps(changed_sd))
    sys.stdout.write("bytes before=%d after=%d\n"
                     % (os.path.getsize(EXPORT), len(text.encode("utf-8"))))
    if "--execute" not in sys.argv:
        sys.stdout.write("dry run, wrote nothing\n")
        return 0

    handle, tmp = tempfile.mkstemp(dir=os.path.dirname(EXPORT),
                                   prefix=".r2433-", suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as sink:
        sink.write(text)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(tmp, EXPORT)

    back = json.load(io.open(EXPORT, encoding="utf-8"))
    left = [r for r in back["results"]
            if isinstance(r, list) and len(r) >= 2 and r[1] == label]
    ok = (len(left) == 1 and str(left[0][0]) == tick
          and back["self_drive"] == sd)
    sys.stdout.write("readback tick_rows=%d tick=%s ok=%s bytes=%d\n"
                     % (len(left), left[0][0] if left else "-", ok,
                        os.path.getsize(EXPORT)))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())