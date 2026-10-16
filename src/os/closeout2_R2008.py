# closeout2_R2008.py - R2008 closeout resume (steps 2-4):
# the primary closeout driver completed the state.json surgery
# (tick 2008 + two-line log append, comma repaired by
# fix_comma_R2008.py per the R2006/R2007 same-pit precedent
# family) and died at its own post-write parse gate before the
# explore/heartbeat/export steps - this resume runs exactly
# those steps, unchanged in logic.
# ASCII script logic; Chinese content lives in the payload.
import io
import json
import os
import sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_PAYLOAD = os.path.join(HERE, "closeout_payload_R2008.json")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

PAY = json.loads(io.open(P_PAYLOAD, encoding="utf-8").read())


def main():
    # -- gate: state must already be valid and complete ---------
    st = json.loads(io.open(P_STATE, encoding="utf-8").read())
    assert st["tick"] == 2008, "tick not bumped"
    assert len(st["log"]) == 19, "log append shape wrong"
    assert st["log"][-2].startswith("2026-10-17 R2008")
    assert st["log"][-1].startswith("R2008 tokens:")
    sz = os.path.getsize(P_STATE)
    assert sz < 78500, "state over budget: %d" % sz
    print("gate ok tick=2008 log-items=%d bytes=%d"
          % (len(st["log"]), sz))

    # -- (2) explore.md claim flip + done note + reseed ---------
    text = io.open(P_EXPLORE, encoding="utf-8").read()
    anchor_open = PAY["claim_row_open_anchor"]
    assert text.count(anchor_open) == 1, "claim row anchor"
    text = text.replace(anchor_open,
                        "- [x] 数据集覆盖榜双窗并读板例窗探索"
                        "（coverage_board 后续")
    done_anchor = PAY["claim_row_done_anchor"]
    assert text.count(done_anchor) == 1, "done anchor"
    text = text.replace(done_anchor,
                        done_anchor + PAY["done_note"])
    assert text.count(PAY["reseed_row"]) == 0, "reseed exists"
    if not text.endswith("\n"):
        text += "\n"
    text += PAY["reseed_row"] + "\n"
    with io.open(P_EXPLORE, "w", encoding="utf-8",
                 newline="") as fh:
        fh.write(text)
    print("explore ok: row flipped, done note, reseed appended")

    # -- (3) heartbeat line --------------------------------------
    now = datetime.now(timezone(timedelta(hours=8)))
    stamp = now.strftime("%Y-%m-%d %H:%M") + " +08:00"
    hb_line = (stamp + " | BigDomain OSLoop alive | tick 2008 | "
               + PAY["heartbeat_line"] + "\n")
    with io.open(P_HEART, "a", encoding="utf-8",
                 newline="") as fh:
        fh.write(hb_line)
    print("heartbeat ok")

    # -- (4) status-export refresh -------------------------------
    import check_export_consistency as CEC
    derived, _state, exp, _pat = CEC.recompute()
    exp["export_ts"] = now.isoformat(timespec="seconds")
    exp["ceo_face"]["current"] = PAY["ceo_current"]
    exp["ceo_face"]["latest_artifact"] = PAY["ceo_artifact"]
    exp["ceo_face"]["next_milestone"] = PAY["ceo_milestone"]
    exp["results"].append([PAY["results_row_tick"],
                           PAY["results_row_label"]])
    derived["method"] = ("machine-derived from state.json log"
                        " per BD-PROP-001 caliber"
                        " (check_export_consistency.recompute)")
    exp["self_drive"] = derived
    with io.open(P_EXPORT, "w", encoding="utf-8",
                 newline="") as fh:
        json.dump(exp, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("export ok ts=%s self_drive window=%s W=%d sub=%d"
          " explore_open=%d"
          % (exp["export_ts"], derived["window"],
             derived["log_lines_in_window"],
             derived["substantive_non_idle_mention_lines"],
             derived.get("queue_explore_open", -1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
