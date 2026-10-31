"""R2302 closeout: product window on the debt register first item.

ASCII-only source (the encoding law); the CEO-visible Chinese text lives in the
data file state/export_face_R2302.json and is only read here.

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
FACE = os.path.join(ROOT, "state", "export_face_R2302.json")

ROUND = "R2302"
TICK = 2302

HEARTBEAT_2302 = (
    "tick 2302 2026-11-01 product window: the evidence pile the history had "
    "been rounding became a classified fact. src/os/evidence_variants.py asks "
    "followup_history.NAME_RE for the round and the suffix of every "
    "non-canonical reconcile-all leg instead of restating the law, pairs each "
    "with its canonical log, and splits DUPLICATE from DISTINCT by content "
    "digest with both digests named; a leg with no canonical round reads "
    "ORPHAN and is listed, and retry-ness is asked through retry_naming. SUITE "
    "PASS 6/6 double-run identical digest 4C1B9787CFCC43E7 with five adjacent "
    "suites green (qa/evidence-variants-R2302.log, 1307B, single utf-8 LF "
    "writer), wired os-evidence-variants(6). LIVE: variants=61 duplicate=0 "
    "distinct=59 orphan=2 retry=4 - the two orphans are the R2136 b/c legs "
    "whose canonical log was never committed and the four retries are the "
    "R2262/R2277/R2289/R2299 red-then-green corrections. Phrasing note: this "
    "row reuses no older wording. The claim dropped tech claimable to 9, so a "
    "real gap row was seeded (orphan_trace, AC-OTR1..AC-OTR6) and the floor "
    "closed FLOOR-MET 5/5 10/10 10/10. Register closed product-face-R2301 and "
    "opened product-face-R2303 at the tech head line 367 prefix AC-FRTL1; the "
    "fold was block-aligned as fold 608 over log lines 1..5 and the four "
    "ledger suites read 8/8 afterwards"
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
    ledger = [row for row in data["log"] if str(row).startswith("R2302 tokens:")]
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
    if "2302" in have:
        print("HEARTBEAT already carries tick 2302")
        return 0
    if not text.endswith("\n"):
        text += "\n"
    text += HEARTBEAT_2302 + "\n"
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