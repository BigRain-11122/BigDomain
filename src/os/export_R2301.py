"""R2301 closeout: verification window on the debt register first item.

ASCII-only source (the encoding law); the CEO-visible Chinese text lives in the
data file state/export_face_R2301.json and is only read here.

Every derived block is recomputed from the real files; nothing is invented. The
state log rows for this window were written by the closeout append, so this
script only refreshes the CEO face, the export and the heartbeat row.
"""

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
FACE = os.path.join(ROOT, "state", "export_face_R2301.json")

ROUND = "R2301"
TICK = 2301

HEARTBEAT_2301 = (
    "tick 2301 2026-11-01 verification window: the whole reconcile battery was "
    "re-run on the committed R2300 tree with zero product edits until green "
    "(the R2168 mixed-tree rule). RUNNER PASS 456/456 suites plus controls 7/7 "
    "in 737.6s, birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy zero "
    "failed zero, criteria total 3712 - exactly the pre-registered +1 suite / "
    "+6 criteria against R2299 (455/3706) from the R2300 os-gate-drift suite. "
    "Four follow-up sections then ran through src/os/battery_followup.py: the "
    "matrix section FAILED first on the stale doc (43861B vs 43904B) and did "
    "not rewrite it, src/sandbox/suite_matrix.py regenerated the doc to 456 "
    "suites / 3712 criteria and the re-run read all four PASS, closing on "
    "VERDICT R2301 PASS. Register closed through its own writer (line 72, open "
    "2->1, done 49->50) and product-face-R2301 opened first=yes naming the tech "
    "head at line 366 prefix AC-EVR1. The closeout fold took three attempts and "
    "all three are disclosed: window 1..4 was refused by the fold gate, window "
    "1..8 split the R2288 block and the live ledger gate caught it, both undone "
    "byte-exactly, and window 1..9 landed with predicted 70165B equal to "
    "measured and 592 tokens covered; the four ledger suites then read 8/8 and "
    "the live gate reads VERDICT CLEAN over 54 lines. Honest score 0 product "
    "points - this window bought certainty, not a face"
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
    ledger = [row for row in data["log"] if str(row).startswith("R2301 tokens:")]
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
    if "2301" in have:
        print("HEARTBEAT already carries tick 2301")
        return 0
    if not text.endswith("\n"):
        text += "\n"
    text += HEARTBEAT_2301 + "\n"
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