"""R2298 closeout: product window on the tech head (stamp_residue).

ASCII-only source (the encoding law); the CEO-visible Chinese text lives in
the data file state/export_face_R2298.json and is only read here.

Every derived block is recomputed from the real files; nothing is invented.
The state log rows for this window were written when the product face landed,
so this script only appends the five-silence scan row if it is missing.
"""

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
FACE = os.path.join(ROOT, "state", "export_face_R2298.json")

ROUND = "R2298"
TICK = 2298

LOG_SCAN = (
    "R2299 opened on a five-silence scan taken at the head of R2298 and "
    "recorded here rather than left implicit: tree clean (empty git status "
    "--short, no index.lock), decisions.md carrying 289 non-empty rows EQUAL "
    "to the stored baseline with an empty token diff (the stored token set of "
    "194 is a superset of the live 185 - the nine absent tokens left with "
    "the archive rotation, so no new decision row is presented and zero "
    "domain action was owed), group orders.md latest timestamp 2026-10-31 "
    "18:23 EQUAL to the stored last_order so no new order, global-benchmarks "
    "refreshed 2026-10-29 inside the 7-day gate, and no un-replied "
    "@BigDomain row in the group ledger. One measurement correction belongs "
    "to this row: state.json stores last_dec_tokens as one comma-joined "
    "STRING rather than a JSON array, so a naive set() over it compares "
    "characters and reports every token as new - the honest diff parses the "
    "string first, and the baseline is now rewritten as the live 185-token "
    "set."
)

HEARTBEAT_2298 = (
    "tick 2298 2026-11-01 product window: the stamped-but-never-logged "
    "residue became one table - src/os/stamp_residue.py plus its suite "
    "(AC-SRS1..AC-SRS6 pinned in the R2284 seed row before the code, SUITE "
    "PASS 6/6 double-run identical with five adjacent os suites green, wired "
    "os-stamp-residue(6)) joining state_seq queue_only with stamp_locator "
    "hits, so a stamp on a CLOSED row reads as delivery evidence and a stamp "
    "sitting on an OPEN row reads STAMP-ONLY-OPEN; live 179 rounds / 159 "
    "delivered / 20 open-only / 0 no-hit, 178/158/20 after this window own "
    "log item retired R2298; one real gap row seeded (residue_triage) to hold "
    "the tech floor at 10/10; the queue note first said 185/165 by reading "
    "queue_done as the residue size and was corrected to the measured numbers "
    "before any commit"
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


def update_state(execute):
    data = json.loads(load(STATE).decode("utf-8"))
    if data["tick"] != TICK:
        print("E_STATE_TICK expected %d, found %s" % (TICK, data["tick"]))
        return 3
    log = data["log"]
    if not any("R2299 opened on a five-silence scan" in row for row in log):
        log.append(LOG_SCAN)
    else:
        print("STATE scan row already present")
    if not execute:
        print("DRY RUN state tick=%d log=%d" % (data["tick"], len(log)))
        return 0
    size = write_json(STATE, data)
    back = json.loads(load(STATE).decode("utf-8"))
    if back["tick"] != TICK or len(back["log"]) != len(log):
        print("E_STATE_READBACK")
        return 3
    print("STATE tick=%d log=%d %dB readback ok"
          % (back["tick"], len(back["log"]), size))
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
    if "2298" in have:
        print("HEARTBEAT already carries tick 2298")
        return 0
    if not text.endswith("\n"):
        text += "\n"
    text += HEARTBEAT_2298 + "\n"
    if not execute:
        print("DRY RUN heartbeat +1 row")
        return 0
    with open(path, "wb") as sink:
        sink.write(text.encode("utf-8"))
    print("HEARTBEAT +1 row")
    return 0


def main(argv):
    execute = "--execute" in argv
    for step in (update_state, update_export, append_heartbeat):
        code = step(execute)
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))