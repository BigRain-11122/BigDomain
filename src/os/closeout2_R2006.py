# closeout2_R2006.py - R2006 closeout continuation: steps 2-4
# (explore flip/done/reseed, heartbeat, export refresh). Step 1
# (state append) landed via closeout_R2006.py + fix_comma
# surgical repair; this driver must NOT touch state.json.
# ASCII logic; CJK lives in closeout_payload_R2006.json.
import io
import json
import os
import sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_PAYLOAD = os.path.join(HERE, "closeout_payload_R2006.json")
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

PAY = json.loads(io.open(P_PAYLOAD, encoding="utf-8").read())


def main():
    # guard: state must already carry the R2006 pair
    st = json.loads(io.open(
        os.path.join(ROOT, "src", "os", "state.json"),
        encoding="utf-8").read())
    assert st["tick"] == 2006 and len(st["log"]) == 19, \
        "state not at post-closeout shape"

    # -- explore.md claim flip + done note + reseed --------------
    text = io.open(P_EXPLORE, encoding="utf-8").read()
    anchor_open = PAY["claim_row_open_anchor"]
    assert text.count(anchor_open) == 1, "claim row anchor"
    text = text.replace(
        anchor_open,
        "- [x] API 市场开发者销量榜跨重启持久化例窗探索"
        "（apimarket dev_sales_board 后继")
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

    # -- heartbeat line -------------------------------------------
    now = datetime.now(timezone(timedelta(hours=8)))
    stamp = now.strftime("%Y-%m-%d %H:%M") + " +08:00"
    hb_line = (stamp + " | BigDomain OSLoop alive | tick 2006 | "
               + PAY["heartbeat_line"] + "\n")
    with io.open(P_HEART, "a", encoding="utf-8",
                 newline="") as fh:
        fh.write(hb_line)
    print("heartbeat ok")

    # -- export refresh --------------------------------------------
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
    print("export ok ts=%s window=%s W=%d sub=%d explore=%d"
          % (exp["export_ts"], derived["window"],
             derived["log_lines_in_window"],
             derived["substantive_non_idle_mention_lines"],
             derived.get("queue_explore_open", -1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
