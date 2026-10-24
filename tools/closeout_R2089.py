"""R2089 closeout: board rows, state bookkeeping, export refresh.

Pure ASCII source (coding law). All user-facing text comes from the
UTF-8 data file passed on argv. Deterministic and idempotent: each
write is guarded by a marker check so a re-run cannot duplicate rows.
"""

import datetime
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def prepend(path, row, marker):
    text = read(path)
    if marker in text:
        print("skip (already present):", os.path.basename(path))
        return
    write(path, row + "\n" + text)
    print("prepended:", os.path.basename(path))


def queue_open(path):
    return len(re.findall(r"(?m)^- \[ \]", read(path)))


def main(argv):
    data = json.loads(read(argv[1]))

    prepend(os.path.join(ROOT, "state", "queue", "explore.md"),
            data["explore_row"], "R2089")
    prepend(os.path.join(ROOT, "src", "os", "backlog.md"),
            data["backlog_row"], "R2089")

    state_path = os.path.join(ROOT, "src", "os", "state.json")
    state = json.loads(read(state_path))
    state["tick"] = int(state.get("tick", 0)) + 1
    log = state["log"]
    for line in data["state_log"]:
        if line in log:
            continue
        log.append(line)
    write(state_path, json.dumps(state, indent=2, ensure_ascii=False) + "\n")
    print("tick:", state["tick"], "log lines:", len(log))

    export_path = os.path.join(ROOT, "docs", "status-export.json")
    export = json.loads(read(export_path))
    export["export_ts"] = datetime.datetime.now().astimezone().replace(
        microsecond=0).isoformat()
    export["ceo_face"] = data["ceo_face"]
    results = export["results"]
    if not any(str(r[0]) == "R2089" for r in results):
        results.append(data["results_row"])
    self_drive = export["self_drive"]
    self_drive["queue_tech_open"] = queue_open(
        os.path.join(ROOT, "state", "queue", "tech.md"))
    self_drive["queue_explore_open"] = queue_open(
        os.path.join(ROOT, "state", "queue", "explore.md"))
    self_drive["queue_main_open"] = 0
    window_start = datetime.date(2026, 10, 18)
    window_lines = 0
    substantive = 0
    for line in log:
        match = re.match(r"(\d{4}-\d\d-\d\d)", line)
        if match is None:
            continue
        day = datetime.date(int(match.group(1)[0:4]),
                            int(match.group(1)[5:7]),
                            int(match.group(1)[8:10]))
        if day >= window_start and not line.startswith("R"):
            window_lines += 1
            substantive += 1
    self_drive["log_lines_in_window"] = window_lines
    self_drive["substantive_non_idle_mention_lines"] = substantive
    write(export_path, json.dumps(export, indent=2, ensure_ascii=False)
          + "\n")
    print("export refreshed:", export["export_ts"],
          "results:", len(results))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))