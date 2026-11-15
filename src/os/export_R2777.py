"""export_R2777 - refresh docs/status-export.json for the R2777 window.

The shipped generic driver supplies the derived blocks; this file adds only
the three CEO lines, composed from numbers THIS window measured: two shipped
faces (ceo-blockers, face-sweep) had zero links on the CEO entry page, so the
renderer now lists every preview X.html that carries a sibling X.json (27
pairs today), and deliverable_index --check reads 14/14 with the entry page
grown 28131B -> 33817B.
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

CURRENT = ("R2777 \u4ea7\u54c1\u5207\u7247\uff1aCEO \u5165\u53e3\u9875\u4ece\u300c\u53ea\u94fe\u6700\u65b0\u4e00\u5bf9\u300d"
           "\u53d8\u6210\u300c\u5217\u51fa\u5168\u90e8\u5df2\u4e0a\u7ebf\u9762\u300d\u2014\u2014\u5f00\u8f6e\u5b9e\u6d4b "
           "ceo-blockers.html \u4e0e face-sweep.html \u5728 preview/index.html "
           "\u91cc\u96f6\u94fe\u63a5\uff08\u4e13\u4e3a CEO \u5199\u7684\u963b\u585e\u9762\u5374\u4ece CEO \u7684"
           "\u7b2c\u4e00\u9875\u6253\u4e0d\u5f00\uff09\uff1b\u73b0\u7531\u76ee\u5f55\u6d3e\u751f\u51fa 27 "
           "\u4e2a\u6210\u5bf9\u9762\u5e76\u9010\u6761\u94fe\u63a5\uff0c--check PASS 14/14\uff0c"
           "\u5165\u53e3\u9875 28131B\u219233817B")
LATEST = ("preview/index.html\uff0833817B\u00b7\u5168\u90e8 27 \u9762\u53ef\u70b9\u5f00\uff09"
          "\uFF0Bqa/entry-pairs-band-R2777.log\uff08732B\u00b7UTF-8/LF\u00b7"
          "\u7ecf tools/qa_log.py \u6b63\u8f68\u5199\u51fa\uff09")
NEXT = ("48 \u5c0f\u65f6\u5185\uff1a\u6309\u81ea\u8eab\u95ed\u5408 BATTERY rc= \u884c\u91c7\u7eb3 "
        "reconcile-battery-R2775\uff08\u672c\u7a97\u5173\u95ed\u65f6\u4ecd live\uff09\uff0c"
        "\u5e76\u5728\u6700\u7ec8\u63d0\u4ea4\u6811\u4e0a\u91cd\u8dd1 census \u5bb6\u65cf\u4e0e export "
        "\u961f\u5217\uff1b\u817f\u95ed\u540e\u89e3\u51bb src/ \u5e76\u63a5\u7ebf leg_interlock\uff08AC-LINTW1..6\uff09")


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
