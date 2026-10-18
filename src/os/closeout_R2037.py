# closeout_R2037.py - R2037 closeout edits (state tick/log,
# heartbeat row, oss-harvest registry row, backlog radar note,
# explore queue line note, export refresh via recompute).
# Pure ASCII source; CJK copy lives in the closeout data file
# closeout_R2037.json (data file law).
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

DATA = json.loads(io.open(os.path.join(HERE, "closeout_R2037.json"),
                          encoding="utf-8").read())
ROUND_LINE = DATA["round_line"]
TOKENS_LINE = DATA["tokens_line"]
HEART_ROW = DATA["heart_row"]
REG_ROW = DATA["reg_row"]
RADAR_NOTE = DATA["radar_note"]
QUEUE_NOTE = DATA["queue_note"]
EXPORT_CURRENT = DATA["export_current"]
EXPORT_ARTIFACT = DATA["export_artifact"]
EXPORT_MILESTONE = DATA["export_milestone"]
EXPORT_RESULT = DATA["export_result"]


def rd(p):
    return io.open(p, encoding="utf-8", newline="").read()


def wr(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)


def main():
    # 1. state.json: tick + append round/tokens lines
    sp = os.path.join(ROOT, "src", "os", "state.json")
    st = json.loads(rd(sp))
    assert st["tick"] == 2036, "tick unexpected %s" % st["tick"]
    st["tick"] = 2037
    st["log"].append(ROUND_LINE)
    st["log"].append(TOKENS_LINE)
    body = json.dumps(st, ensure_ascii=False, indent=2)
    wr(sp, body + "\n")
    sz = os.path.getsize(sp)
    assert sz < 78500, "state over gate: %d" % sz
    print("STATE ok bytes=%d log=%d" % (sz, len(st["log"])))

    # 2. heartbeat row append
    hp = os.path.join(ROOT, "heartbeat.txt")
    hb = rd(hp)
    assert "tick 2036" in hb[-800:], "heartbeat tail lacks tick 2036"
    wr(hp, hb.rstrip("\n") + "\n" + HEART_ROW + "\n")
    print("HEARTBEAT ok")

    # 3. registry (7) row append
    rp = os.path.join(ROOT, "docs", "oss-harvest", "README.md")
    reg = rd(rp)
    assert "OH-20261015-bigdomain.md" in reg, "reg anchor missing"
    wr(rp, reg.rstrip("\n") + "\n\n" + REG_ROW + "\n")
    print("REGISTRY ok")

    # 4. backlog radar standing line note
    bp = os.path.join(ROOT, "src", "os", "backlog.md")
    bl = rd(bp)
    anchor = "P-2026-10-04-01/02"
    idx = bl.find(anchor)
    assert idx >= 0, "radar line anchor missing"
    eol = bl.find("\n", idx)
    assert eol >= 0
    bl2 = bl[:eol].rstrip() + RADAR_NOTE + bl[eol:]
    assert bl2 != bl
    wr(bp, bl2)
    print("BACKLOG ok")

    # 5. explore queue line note
    qp = os.path.join(ROOT, "state", "queue", "explore.md")
    q = rd(qp)
    qanchor = "- [ ] " + DATA["queue_anchor_head"]
    qidx = q.find(qanchor)
    assert qidx >= 0, "explore line anchor missing"
    qeol = q.find("\n", qidx)
    q2 = q[:qeol].rstrip() + QUEUE_NOTE + q[qeol:]
    assert q2 != q
    wr(qp, q2)
    print("QUEUE ok")

    # 6. export refresh
    ep = os.path.join(ROOT, "docs", "status-export.json")
    ex = json.loads(rd(ep))
    ex["export_ts"] = DATA["export_ts"]
    ex["ceo_face"]["current"] = EXPORT_CURRENT
    ex["ceo_face"]["latest_artifact"] = EXPORT_ARTIFACT
    ex["ceo_face"]["next_milestone"] = EXPORT_MILESTONE
    ex["results"].insert(0, ["R2037", EXPORT_RESULT])
    # keep history rows untouched (bounded results face: the trailing
    # tick placeholder row is never the round-history face)
    try:
        import check_export_consistency as CEC
        derived, _st, _ex, info = CEC.recompute()
        if isinstance(derived, dict) and derived:
            for k, v in derived.items():
                ex[k] = v
            print("EXPORT self_drive rederived: %s" % sorted(derived))
        else:
            print("EXPORT recompute returned no dict, info=%s" % (info,))
    except Exception as e:
        print("EXPORT recompute failed honestly noted: %s" % e)
    wr(ep, json.dumps(ex, ensure_ascii=False, indent=2) + "\n")
    print("EXPORT ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
