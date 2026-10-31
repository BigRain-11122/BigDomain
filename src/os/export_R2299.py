"""R2299 closeout: verification window on the debt register first item.

ASCII-only source (the encoding law); the CEO-visible Chinese text lives in
the data file state/export_face_R2299.json and is only read here.

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
FACE = os.path.join(ROOT, "state", "export_face_R2299.json")

ROUND = "R2299"
TICK = 2299

HEARTBEAT_2299 = (
    "tick 2299 2026-11-01 verification window: zero product edits - the full "
    "reconcile battery ran twice on the committed R2298 tree. The FIRST run "
    "was RED 451/455 with 5 failed assertions and criteria total 3706: one "
    "root cause, the R2298 closeout had stamped a five-silence observation "
    "with the next round label and no ledger line, so the coverage gate read "
    "rounds_without_ledger=2299 and the four ledger suites (AC-LGR8, "
    "AC-LGA7/AC-LGA8, AC-LGB8, AC-LGN8) went red. The repair relabeled that "
    "item to the round that wrote it (one predicted-delta edit, 77510B to "
    "77528B, committed alone as 05d759b6), the four suites re-read 8/8 and "
    "the live gate read VERDICT CLEAN; the canon pass (four-space items to "
    "the canonical sixteen, CRLF) ran first and is disclosed. The RETRY read "
    "RUNNER PASS 455/455 suites plus controls 7/7 in 777.0s, criteria total "
    "3706 - exactly the pre-registered +1 suite / +6 criteria against R2297 "
    "from the R2298 os-stamp-residue suite - and the four follow-up sections "
    "read PASS after the matrix section refused the stale doc and "
    "suite_matrix regenerated it to 455 suites / 3706 criteria at 43861B; "
    "fold 604 then 605 brought state.json to 76192B at margin 2308B"
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
    ledger = [row for row in data["log"] if str(row).startswith("R2299 tokens:")]
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
    if "2299" in have:
        print("HEARTBEAT already carries tick 2299")
        return 0
    if not text.endswith("\n"):
        text += "\n"
    text += HEARTBEAT_2299 + "\n"
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