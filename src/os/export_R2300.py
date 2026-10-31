"""R2300 closeout: product window on the debt register first item.

ASCII-only source (the encoding law); the CEO-visible Chinese text lives in
the data file state/export_face_R2300.json and is only read here.

Every derived block is recomputed from the real files; nothing is invented.
The state log rows for this window were written by the closeout append, so
this script only refreshes the CEO face, the export and the heartbeat row.
"""

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
FACE = os.path.join(ROOT, "state", "export_face_R2300.json")

ROUND = "R2300"
TICK = 2300

HEARTBEAT_2300 = (
    "tick 2300 2026-11-01 product window: an inert machine gate became a "
    "decision instead of a shrug. machine_gate reports a declaration that "
    "matches no claimable candidate as inert with no line, so a row whose "
    "text was edited and a row that was deleted read identically - src/os/"
    "gate_drift.py takes the prefix of every inert identity, looks for rows "
    "still carrying it, and names DRIFT (old identity, new identity, both "
    "lines, shared prefix, moved yes/no) or GONE (prefix, no line). The gate "
    "reading and the declaration are imported from machine_gate and the "
    "suite proves it by patching that call; the row and prefix laws come from "
    "queue_floor and queue_row. SUITE PASS 6/6 double-run identical with five "
    "adjacent suites green (qa/gate-drift-R2300.log, 1309B, one utf-8 LF "
    "writer), wired os-gate-drift(6). LIVE: declarations=1 inert=1 drift=1 "
    "gone=0 moved=0 verdict=STILL-PRESENT - the docker declaration still "
    "matches row 41 verbatim, it just cannot fire because that row declares "
    "no criteria prefix. Honest defects: the first suite run was red 2/6 and "
    "both reds were this-window test expectations (a claimable row is "
    "BLOCKED, never inert); the live reading then caught a real module "
    "defect, treating the dash placeholder as a shared prefix and blaming "
    "row 7 (matches=281), fixed before the captured evidence. One real gap "
    "row seeded (gate_decl_append, AC-GDA1..AC-GDA6) to hold the tech floor "
    "at 10/10; fold 606 ran first (76192B -> 70964B, 588 tokens covered, "
    "predicted equal to measured) and the four ledger suites re-read 8/8"
)


def load(path, mode="rb"):
    with open(path, mode) as handle:
        return handle.read()


def write_json(path, data):
    text = json.dumps(data, ensure_ascii=False, indent=2)
    blob = text.encode("utf-8")
    if not blob.endswith(b"\n"):
        blob += b"\n"
    temp = path + ".tmp"
    with open(temp, "wb") as sink:
        sink.write(blob)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, path)
    return len(blob)


def check_state(execute):
    data = json.loads(load(STATE).decode("utf-8"))
    if data["tick"] != TICK:
        print("E_STATE_TICK expected %d, found %s" % (TICK, data["tick"]))
        return 3
    ledger = [row for row in data["log"] if str(row).startswith("R2300 tokens:")]
    print("STATE tick=%d log=%d ledger_rows=%d"
          % (data["tick"], len(data["log"]), len(ledger)))
    if len(ledger) != 1:
        return 3
    return 0


def update_export(execute):
    face = json.loads(load(FACE).decode("utf-8"))
    data = json.loads(load(EXPORT).decode("utf-8"))
    now = datetime.datetime.now().astimezone().replace(microsecond=0)
    data["export_ts"] = now.isoformat()
    data["do"] = face["do"]
    block = data.setdefault("ceo_face", {})
    block["current"] = face["current"]
    block["latest_artifact"] = face["latest"]
    block["next_milestone"] = face["next"]
    block["next_milestone_due"] = (
        now + datetime.timedelta(hours=24)).replace(microsecond=0).isoformat()
    block["last_artifact"] = face["last"]
    data["results"] = [[ROUND, face["result"]]] + data["results"]
    data["outs"] = [[face["out"], "on", face["result"]]] + data["outs"]
    import check_export_consistency as consistency
    derived, _, _, pattern = consistency.recompute()
    data["self_drive"] = derived
    label = pattern["tick_row_label"]
    rows = [row for row in data["results"]
            if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(rows) != 1:
        print("E_TICK_ROW expected exactly one tick row, found %d" % len(rows))
        return 3
    rows[0][0] = str(TICK)
    if not execute:
        print("DRY RUN export_ts=%s results=%d outs=%d"
              % (data["export_ts"], len(data["results"]), len(data["outs"])))
        return 0
    size = write_json(EXPORT, data)
    back = json.loads(load(EXPORT).decode("utf-8"))
    if back["export_ts"] != data["export_ts"]:
        print("E_EXPORT_READBACK")
        return 3
    print("EXPORT %dB readback ok results=%d outs=%d"
          % (size, len(back["results"]), len(back["outs"])))
    return 0


def append_heartbeat(execute):
    path = os.path.join(ROOT, "heartbeat.txt")
    raw = load(path)
    text = raw.decode("utf-8")
    have = set()
    for line in text.splitlines():
        if line.startswith("tick "):
            have.add(line.split()[1])
    if "2300" in have:
        print("HEARTBEAT already carries tick 2300")
        return 0
    if not text.endswith("\n"):
        text += "\n"
    text += HEARTBEAT_2300 + "\n"
    if not execute:
        print("DRY RUN heartbeat +1 row")
        return 0
    with open(path, "wb") as sink:
        sink.write(text.encode("utf-8"))
    print("HEARTBEAT +1 row")
    return 0


def main(argv):
    execute = "--execute" in argv
    for step in (check_state, update_export, append_heartbeat):
        code = step(execute)
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))