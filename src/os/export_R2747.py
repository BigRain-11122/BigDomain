"""export_R2747 - refresh docs/status-export.json for the R2747 window.

The shipped generic driver supplies everything except this round own CEO lines,
so this driver composes the three of them from numbers THIS window read: the
R2742 battery leg had ENDED before open (pid gone, closing BATTERY rc=1 line)
and was adopted by its evidence path at 671/676 with a criteria recount of
exactly 5032, its five red rows being the ledger family that was re-run green
on the final committed tree; the fold-caliber defect was repaired at three
sites and used to fold the log on round boundaries, taking state.json from
96461B to 47708B and clearing the 78500B waterline.
"""

import datetime
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import export_driver_queue_face as EDQF  # noqa: E402
import check_export_consistency as cec  # noqa: E402
from export_R2431 import tick_label  # noqa: E402

EXPORT = os.path.join(REPO, "docs", "status-export.json")
STATE = os.path.join(BASE, "state.json")
TZ = datetime.timezone(datetime.timedelta(hours=8))
STAMP = datetime.datetime.now(TZ).replace(microsecond=0).isoformat()

CURRENT = ("R2747 \u91c7\u7eb3\uff0b\u51fa\u751f\u7ad9\u4fee\u590d\u7a97\uff1a"
           "R2742 \u7535\u6c60\u817f\u5df2\u7ec8\u7ed3\u5e76\u6309\u8bc1\u636e"
           "\u8def\u5f84\u91c7\u7eb3\uff08671/676\uff1b5 \u7ea2\u5168\u4e3a "
           "ledger \u5bb6\u65cf\uff0c\u5df2\u5728\u6700\u7ec8\u6811\u72ec\u7acb"
           "\u91cd\u8dd1\u5168\u7eff 8/8\u00b78/8\u00b78/8\u00b76/6\u00b76/6"
           "\uff09\uff1b\u6298\u53e0\u53e3\u5f84\u7f3a\u9677\u4e09\u5904\u4fee"
           "\u597d\uff0c\u6309\u8f6e\u5bf9\u9f50\u6298\u53e0\u540e state.json "
           "96461B\u219247708B\uff0c\u6c34\u4f4d\u7ebf\u8f6c\u7eff")
LATEST = ("src/os/logs_toolkit.py \u6298\u53e0\u53e3\u5f84\u4e09\u5904\u4fee"
          "\u590d\uff08\u6587\u6863\u81ea\u6d3e\u751f 2/16 \u7a7a\u683c\uff0c"
          "\u4ecd\u62d2 8 \u7a7a\u683c\u4e0e\u6df7\u5408\uff09\uff0b\u6309"
          "\u8f6e\u5bf9\u9f50\u6298\u53e0\uff0bqa/reconcile-all-R2742.log"
          "\uff081252699 \u5b57\u8282\u00b7671/676\u00b7criteria \u6070 "
          "5032\uff09")
NEXT = ("48 \u5c0f\u65f6\u5185\uff1a\u5728\u63d0\u4ea4\u6811\u4e0a\u8d77"
        "\u5168\u91cf\u7535\u6c60\u5e76\u6309\u8bc1\u636e\u8def\u5f84\u91c7"
        "\u7eb3\uff08676 \u5957\u4ef6/5032 \u5224\u636e\uff09\uff0c\u7eff"
        "\u540e\u5173\u95ed reconcile-battery-R2742 \u5e76\u53d6\u961f\u5217"
        "\u5934 state/queue/tech.md:713 AC-LKNF1\uff08claimable 10\uff09")


def due():
    return (datetime.datetime.now(TZ)
            + datetime.timedelta(hours=48)).replace(microsecond=0).isoformat()


def main():
    state = json.load(io.open(STATE, encoding="utf-8"))
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    tick = str(state["tick"])
    label = tick_label()
    rows = data.get("results") or []
    stamped = [r for r in rows if isinstance(r, list) and len(r) >= 2
               and r[1] == label]
    if len(stamped) != 1:
        sys.stdout.write("E_EXP expected exactly 1 tick row, found %d\n"
                         % len(stamped))
        return 2
    stamped[0][0] = tick
    data["results"] = rows
    outs = data.get("outs") or []
    if not outs or outs[0] != LATEST:
        outs.insert(0, LATEST)
    data["outs"] = outs
    data["export_ts"] = STAMP
    data["do"] = CURRENT
    ceo = data.get("ceo_face") or {}
    ceo["current"] = CURRENT
    ceo["latest_artifact"] = LATEST
    ceo["last_artifact"] = LATEST
    ceo["next_milestone"] = NEXT
    ceo["next_milestone_due"] = due()
    ceo["updated_at"] = STAMP
    data["ceo_face"] = ceo
    at_write = cec.recompute()[0]
    data["self_drive"] = {
        "window": at_write["window"],
        "window_days": at_write["window_days"],
        "log_lines_in_window": at_write["log_lines_in_window"],
        "idle_fast_mention_lines": at_write["idle_fast_mention_lines"],
        "no_pullable_mention_lines": at_write["no_pullable_mention_lines"],
        "substantive_non_idle_mention_lines":
            at_write["substantive_non_idle_mention_lines"],
        "proposals_total": at_write["proposals_total"],
        "proposals_open": at_write["proposals_open"],
        "queue_main_open": at_write["queue_main_open"],
        "queue_tech_open": at_write["queue_tech_open"],
        "queue_explore_open": at_write["queue_explore_open"],
    }
    try:
        EDQF.refresh(data, REPO)
    except EDQF.ExportDriverQueueFaceError as exc:
        sys.stdout.write("E_EXP queue face unreadable %s\n" % exc)
        return 2
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    try:
        proof = EDQF.publish(REPO, EXPORT, text)
    except EDQF.ExportDriverQueueFaceError as exc:
        sys.stdout.write("QUEUE FACE REFUSED %s\n" % exc)
        return 2
    back = json.load(io.open(EXPORT, encoding="utf-8"))
    ok = (back["ceo_face"]["latest_artifact"] == LATEST
          and back["ceo_face"]["current"] == CURRENT
          and back["ceo_face"]["next_milestone"] == NEXT
          and back["export_ts"] == STAMP
          and back["outs"][0] == LATEST
          and any(isinstance(r, list) and len(r) >= 2 and r[1] == label
                  and str(r[0]) == tick for r in back["results"])
          and back["self_drive"] == data["self_drive"])
    sys.stdout.write("WROTE rows=%d outs=%d tick=%s queue=%s queue_bytes=%s "
                     "ok=%s\n"
                     % (len(back["results"]), len(back["outs"]), tick,
                        proof.get("gate"), proof.get("bytes"), ok))
    return 0 if ok and proof.get("gate") == "CURRENT" else 2


if __name__ == "__main__":
    sys.exit(main())
