"""Refresh docs/status-export.json for BigDomain R2112 (ASCII source;
the Chinese strings live in the data sidecar export_payload_R2112.json).

Updates the CEO face three-line block, appends the round result row and
the outs row, refreshes the tick row and recomputes every self_drive
field with the same caliber the checker uses (so flush and check agree).

Usage: python export_refresh_R2112.py
"""

import io
import json
import os
import re
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
PAYLOAD = os.path.join(ROOT, "src", "os", "export_payload_R2112.json")
STATE = os.path.join(ROOT, "src", "os", "state.json")
PROPOSALS = os.path.join(ROOT, "docs", "proposals.md")
QUEUES = {
    "queue_main_open": os.path.join(ROOT, "state", "queue", "main.md"),
    "queue_tech_open": os.path.join(ROOT, "state", "queue", "tech.md"),
    "queue_explore_open": os.path.join(
        ROOT, "state", "queue", "explore.md"),
}
RE_QUEUE_OPEN = re.compile(r"^- \[ \]")
RE_DECL = re.compile(r"no-pullable|idle-fast")


def read_text(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    with io.open(EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    with io.open(PAYLOAD, encoding="utf-8") as handle:
        payload = json.load(handle)
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)

    export["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    face = export["ceo_face"]
    face["current"] = payload["ceo_current"]
    face["latest_artifact"] = payload["ceo_latest"]
    face["next_milestone"] = payload["ceo_next"]

    export["outs"].append(payload["out_row"])
    export["results"].append(payload["result_row"])

    tick = state["tick"]
    tick_rows = [row for row in export["results"]
                 if isinstance(row, list) and len(row) == 2
                 and row[1] == "OSLoop \u6267\u884c tick"]
    for row in tick_rows:
        row[0] = str(tick)

    derived = {}
    win = payload["window"]
    start, end = win.split("..")
    log = state.get("log", [])
    win_lines = [ln for ln in log if ln[:10] >= start and ln[:10] <= end]
    derived["window"] = win
    derived["window_days"] = int(payload["window_days"])
    derived["log_lines_in_window"] = len(win_lines)
    derived["idle_fast_mention_lines"] = sum(
        1 for ln in win_lines if "idle-fast" in ln)
    derived["no_pullable_mention_lines"] = sum(
        1 for ln in win_lines if "no-pullable" in ln)
    derived["substantive_non_idle_mention_lines"] = sum(
        1 for ln in win_lines if not RE_DECL.search(ln))
    prop_lines = [ln for ln in read_text(PROPOSALS).splitlines()
                  if ln.startswith("### BD-PROP-")]
    derived["proposals_total"] = len(prop_lines)
    derived["proposals_open"] = sum(
        1 for ln in prop_lines if payload["proposal_open_marker"] in ln)
    for key, path in QUEUES.items():
        derived[key] = sum(1 for ln in read_text(path).splitlines()
                           if RE_QUEUE_OPEN.match(ln))
    export["self_drive"] = derived

    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(export, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    print("export refreshed tick=%s log_lines=%d queues=%d/%d/%d"
          % (tick, derived["log_lines_in_window"],
             derived["queue_main_open"], derived["queue_tech_open"],
             derived["queue_explore_open"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())