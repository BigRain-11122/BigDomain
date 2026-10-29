"""Repair pass for the R2246 export: the tick row survives, counts recount."""

import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")


def queue_open(name):
    path = os.path.join(ROOT, "state", "queue", "%s.md" % name)
    if not os.path.exists(path):
        return None
    count = 0
    with open(path, "rb") as handle:
        text = handle.read().decode("utf-8", "replace")
    for line in text.split("\n"):
        if line.startswith("- [ ]"):
            count += 1
    return count


def now_tick():
    path = os.path.join(ROOT, "src", "os", "state.json")
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))["tick"]


def main():
    head = subprocess.run(["git", "show", "HEAD:docs/status-export.json"],
                          cwd=ROOT, stdout=subprocess.PIPE)
    old = json.loads(head.stdout.decode("utf-8"))
    tick_rows = [row for row in old["results"]
                 if any("tick" in str(cell).lower() for cell in row)]
    now = json.load(open(EXPORT, encoding="utf-8"))
    labels = [str(row[0]) for row in now["results"]]
    restored = 0
    for row in tick_rows:
        if str(row[0]) not in labels:
            now["results"].append(row)
            restored += 1
    for row in now["results"]:
        if any(str(cell).strip().lower() == "osloop 执行 tick" for cell in row):
            row[0] = str(now_tick())
    now["self_drive"]["queue_main_open"] = queue_open("main")
    now["self_drive"]["queue_tech_open"] = queue_open("tech")
    now["self_drive"]["queue_explore_open"] = queue_open("explore")
    text = json.dumps(now, ensure_ascii=False, indent=2) + "\n"
    with open(EXPORT, "wb") as handle:
        handle.write(text.encode("utf-8"))
    print("RESTORED %d tick rows; queues main=%s tech=%s explore=%s bytes=%d"
          % (restored, now["self_drive"]["queue_main_open"],
             now["self_drive"]["queue_tech_open"],
             now["self_drive"]["queue_explore_open"],
             len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())