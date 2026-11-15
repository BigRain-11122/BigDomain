"""export_R2796 - refresh docs/status-export.json for the R2796 window.

The generic driver supplies the derived blocks; this file adds the three CEO lines
composed from numbers THIS window measured: the CEO entry page's own fourteen
criteria moved from self-check only to a battery row, proven load-bearing by two
negative controls, with the real preview tree untouched (same fingerprint before
and after the suite ran).
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

CURRENT = ("R2796 工程守护：CEO 入口页 preview/index.html 的十四条判据（AC-DIX1..14）"
           "第一次进电池——新 src/os/test_deliverable_index.py 在私有预览世界里独立重算每一条"
           "（不抄工具自己的 PASS），套件 SUITE PASS 14/14 连跑两次一致；两个反控真的翻红："
           "多塞一个未注册 -report 面→AC-DIX1 FAIL rc=2，篡改落盘块一个字节→AC-DIX3 FAIL rc=2；"
           "真树闸仍 VERDICT PASS 14/14 指纹 5ef05abdfe2aee6e 与套件跑前完全相同（证明没碰真 preview/）；"
           "注册表实测 687 套件 / 5118 判据（原 686 / 5104）")
LATEST = ("qa/deliverable-index-suite-R2796.log（1045B·本轮证据）+ src/os/test_deliverable_index.py（14 判据）"
          "+ docs/sandbox-suite-matrix.md（72516B·687 行）")
NEXT = ("48 小时内：把仍是「只靠自检」的六个面补进电池——tools/journey_demo.py、tools/face_sweep.py、"
        "tools/ugc_gate_report.py、tools/ceo_blockers.py、tools/payment_gate_report.py、"
        "tools/platform_live_report.py；或改跑一轮完整电池（687 套件 / 5118 判据）并按它自己的收尾行采纳")


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
