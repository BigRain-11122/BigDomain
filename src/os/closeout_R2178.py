# closeout_R2178.py - apply the R2178 closeout: explore queue reseed rows,
# the backlog head flip + next head, state.json (tick + log + token line),
# and docs/status-export.json. Pure stdlib, pure ASCII source; every
# Chinese payload string is read from state/r2178_payload.json (a data
# file, so the encoding law holds: scripts ASCII, payloads UTF-8).
import io
import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
PAYLOAD = os.path.join(ROOT, "state", "r2178_payload.json")

DEC_ROWS = 240


def dump_state(doc):
    text = json.dumps(doc, ensure_ascii=False, indent=2)
    text = text.replace("\n", "\r\n") + "\r\n"
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def main():
    payload = json.load(io.open(PAYLOAD, encoding="utf-8"))

    # 1) explore queue: claim row + ten seeds appended in order (idempotent
    #    on rerun: a partial earlier attempt must not duplicate rows)
    existing = io.open(EXPLORE, encoding="utf-8").read()
    probe = payload["explore_rows"][0][:60]
    if probe in existing:
        print("explore rows already present, skipped")
    else:
        with io.open(EXPLORE, "a", encoding="utf-8",
                     newline="\n") as handle:
            for row in payload["explore_rows"]:
                handle.write(row + "\n")
        print("explore rows appended=%d" % len(payload["explore_rows"]))

    # 2) backlog: flip the R2178 head to done, append the R2179 head
    raw = io.open(BACKLOG, encoding="utf-8").read().split("\n")
    flipped = 0
    for i, line in enumerate(raw):
        if line.startswith(payload["backlog_done_marker"]):
            raw[i] = ("- [x] " + line[len(payload["backlog_done_marker"]):]
                      + payload["backlog_done_suffix"])
            flipped += 1
            break
    if flipped != 1:
        raise SystemExit("backlog head marker not found exactly once")
    with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(raw) + "\n" + payload["backlog_new_head"] + "\n")
    print("backlog head flipped=%d next head appended" % flipped)

    # 3) state.json
    doc = json.loads(io.open(STATE, encoding="utf-8").read())
    doc["tick"] = int(doc["tick"]) + 1
    doc["last_decision_rows"] = DEC_ROWS
    doc["log"].append(payload["state_entry"])
    doc["log"].append(payload["tokens_line"])
    dump_state(doc)
    print("state tick=%d log=%d" % (doc["tick"], len(doc["log"])))

    # 4) status export
    exp = json.load(io.open(EXPORT, encoding="utf-8"))
    spec = payload["export"]
    exp["export_ts"] = spec["export_ts"]
    exp["do"] = spec["do"]
    face = exp["ceo_face"]
    face["current"] = spec["current"]
    face["latest_artifact"] = spec["latest_artifact"]
    face["next_milestone"] = spec["next_milestone"]
    face["last_artifact"] = spec["last_artifact"]
    exp["results"].insert(0, spec["result"])
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(exp, ensure_ascii=False, indent=2) + "\n")
    print("export refreshed")


if __name__ == "__main__":
    main()