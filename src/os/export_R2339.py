"""export_R2339 - refresh the CEO-visible face and append one heartbeat row.

Every human-facing string lives in export_lines_R2339.json (a data file), so
this source stays pure ASCII. Derived fields come from the shipped consistency
checker (F3: self_drive is never written by hand). Dry run by default;
--execute writes the export atomically and appends the heartbeat once.
"""

import datetime
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import check_export_consistency as CEC  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
LINES = os.path.join(BASE, "export_lines_R2339.json")
ROUND = "R2339"
TICK = "2339"
ARTIFACTS = ("src/os/orphan_promote.py",
             "qa/reconcile-all-R2136.log",
             "qa/orphan-promote-R2339.log",
             "src/os/state.json")


def main(argv):
    with io.open(LINES, "r", encoding="utf-8") as handle:
        lines = json.load(handle)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    derived, state, _export, pat = CEC.recompute()
    now = datetime.datetime.now().astimezone().replace(microsecond=0)
    before = len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    data["export_ts"] = now.isoformat()
    data["do"] = lines["do"]
    face = data.get("ceo_face") or {}
    face["current"] = lines["current"]
    face["latest_artifact"] = lines["latest_artifact"]
    face["next_milestone"] = lines["next_milestone"]
    face["next_milestone_due"] = (now
                                  + datetime.timedelta(hours=48)).isoformat()
    data["ceo_face"] = face
    drive = data.get("self_drive") or {}
    for key in ("window", "window_days", "log_lines_in_window",
                "idle_fast_mention_lines", "no_pullable_mention_lines",
                "substantive_non_idle_mention_lines", "proposals_total",
                "proposals_open", "queue_main_open", "queue_tech_open",
                "queue_explore_open"):
        if key in derived:
            drive[key] = derived[key]
    data["self_drive"] = drive
    outs = data.get("outs") or []
    for name in ARTIFACTS:
        if not any(row and row[0] == name for row in outs):
            outs.insert(0, [name, "on", lines["entry"]])
    data["outs"] = outs
    results = data.get("results") or []
    label = pat["tick_row_label"]
    for row in results:
        if isinstance(row, list) and len(row) >= 2 and row[1] == label:
            row[0] = TICK
    if not any(row and row[0] == ROUND for row in results):
        results.insert(0, [ROUND, lines["entry"]])
    data["results"] = results
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    after = len(body.encode("utf-8"))
    print("EXPORT %s before=%dB after=%dB export_ts=%s window=%s lines=%s"
          % (ROUND, before, after, data["export_ts"], drive.get("window"),
             drive.get("log_lines_in_window")))
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    temp = EXPORT + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    os.replace(temp, EXPORT)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != body:
        print("E_READBACK")
        return 3
    if os.path.exists(temp):
        print("E_RESIDUE")
        return 3
    with io.open(HEARTBEAT, "r", encoding="utf-8") as handle:
        beat = handle.read()
    stamp = "tick %s " % TICK
    if stamp in beat:
        print("HEARTBEAT already carries tick %s" % TICK)
    else:
        if not beat.endswith("\n"):
            beat += "\n"
        beat += lines["heartbeat"] + "\n"
        with io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(beat)
        print("HEARTBEAT appended tick %s" % TICK)
    print("WROTE readback ok temp clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))