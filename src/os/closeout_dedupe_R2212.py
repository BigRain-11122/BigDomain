"""R2212 repair: the closeout ran twice, so this script removes the
duplicate log lines and the duplicate export rows it appended and puts
the tick back to 2212 (one logical round)."""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_HEART = os.path.join(ROOT, "heartbeat.txt")


def read(path):
    with io.open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write(path, data, indent):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, indent=indent, ensure_ascii=False)
                     + "\n")


def main():
    state = read(P_STATE)
    log = state.get("log", [])
    seen = set()
    out = []
    dropped = 0
    for line in log:
        if line in seen:
            dropped += 1
            continue
        seen.add(line)
        out.append(line)
    state["log"] = out
    state["tick"] = 2212
    write(P_STATE, state, 2)

    export = read(P_EXPORT)
    for key, field in (("outs", None), ("results", 0)):
        rows = export.get(key, [])
        seen_rows = set()
        kept = []
        lost = 0
        for row in rows:
            marker = (json.dumps(row, sort_keys=True) if field is None
                      else str(row[field]))
            if marker in seen_rows:
                lost += 1
                continue
            seen_rows.add(marker)
            kept.append(row)
        export[key] = kept
        print("%s: kept=%d dropped=%d" % (key, len(kept), lost))
    write(P_EXPORT, export, 1)

    with io.open(P_HEART, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("2212\n")
    print("state: log dropped=%d kept=%d tick=%d"
          % (dropped, len(state["log"]), state["tick"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())