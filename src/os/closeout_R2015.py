# closeout_R2015.py - R2015 takeover closeout: append the round
# line + tokens line after fold R545, bump tick to 2015, mark the
# explore claim row done + reseed the successor row, refresh the
# status export ceo_face, append the heartbeat row.
# Pure ASCII source; CJK content lives in
# closeout_R2015.json (data file law).
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))

STATE = os.path.join(ROOT, "src", "os", "state.json")
QUEUE = os.path.join(ROOT, "state", "queue", "explore.md")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HB = os.path.join(ROOT, "heartbeat.txt")
DATA = os.path.join(HERE, "closeout_R2015.json")
MAX_STATE = 78500


def read_bytes(path):
    with io.open(path, "rb") as fh:
        return fh.read()


def write_bytes(path, raw):
    with io.open(path, "wb") as fh:
        fh.write(raw)


def main():
    d = json.loads(io.open(DATA, encoding="utf-8").read())

    # 1) state.json: append round + tokens after fold R545, tick
    st = json.loads(read_bytes(STATE).decode("utf-8"))
    assert st["tick"] == 2014, "unexpected tick %s" % st["tick"]
    tail = st["log"][-1]
    assert "fold R545" in tail, "tail is not the fold R545 line"
    assert "\n" not in d["round_line"]
    assert "\n" not in d["tokens_line"]
    st["log"].append(d["round_line"])
    st["log"].append(d["tokens_line"])
    st["tick"] = 2015
    out = json.dumps(st, ensure_ascii=False, indent=2) + "\n"
    assert len(out.encode("utf-8")) < MAX_STATE, "state over line"
    write_bytes(STATE, out.encode("utf-8"))
    sz = os.path.getsize(STATE)
    print("STATE tick=2015 bytes=%d log-items=%d"
          % (sz, len(st["log"])))
    assert sz < MAX_STATE

    # 2) explore queue: flip checkbox + done note + reseed row
    qraw = read_bytes(QUEUE).decode("utf-8")
    old_p, new_p = (d["queue_claim_prefix_old"],
                    d["queue_claim_prefix_new"])
    assert qraw.count(old_p) == 1, "claim prefix count != 1"
    qraw = qraw.replace(old_p, new_p, 1)
    lines = qraw.split("\n")
    idx = [i for i, ln in enumerate(lines)
           if new_p in ln and "R2015" in ln]
    assert len(idx) == 1, "claim line not unique: %s" % idx
    i = idx[0]
    assert lines[i].endswith("qa/showcase-statsmonth-R2015.log"), \
        "claim line tail mismatch"
    lines[i] = lines[i] + d["queue_done_note"]
    lines.insert(i + 1, d["queue_reseed_row"])
    write_bytes(QUEUE, "\n".join(lines).encode("utf-8"))
    print("QUEUE done-marked + reseed inserted at line %d" % i)

    # 3) status export: refresh export_ts + ceo_face three rows
    eraw = read_bytes(EXPORT)
    ex = json.loads(eraw.decode("utf-8"))
    probe = json.dumps(ex, ensure_ascii=False, indent=2) + "\n"
    assert probe.encode("utf-8") == eraw, \
        "export convention mismatch (indent/newline)"
    ts = None
    for k in ("export_ts",):
        pass
    from datetime import datetime, timezone, timedelta
    ts = datetime.now(timezone(timedelta(hours=8))).strftime(
        "%Y-%m-%dT%H:%M:%S+08:00")
    ex["export_ts"] = ts
    ex["ceo_face"]["current"] = d["export_current"]
    ex["ceo_face"]["latest_artifact"] = d["export_artifact"]
    ex["ceo_face"]["next_milestone"] = d["export_milestone"]
    eout = json.dumps(ex, ensure_ascii=False, indent=2) + "\n"
    write_bytes(EXPORT, eout.encode("utf-8"))
    print("EXPORT refreshed ts=%s bytes=%d"
          % (ts, len(eout.encode("utf-8"))))

    # 4) heartbeat: append canonical row
    hraw = read_bytes(HB)
    if not hraw.endswith(b"\n"):
        hraw += b"\n"
    stamp = datetime.now(timezone(timedelta(hours=8))).strftime(
        "%Y-%m-%d %H:%M")
    row = "%s +08:00 | BigDomain OSLoop alive | tick 2015 | %s\n" \
        % (stamp, d["hb_row"])
    write_bytes(HB, hraw + row.encode("utf-8"))
    print("HB row appended: %s" % stamp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
