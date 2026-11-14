"""export_R2739 - refresh docs/status-export.json for the R2739 window.

The shipped generic driver supplies everything except this round's own CEO
lines, so this driver composes the three of them from numbers THIS window read.

Numbers behind the three lines (all measured in R2739):
  qa/reconcile-all-R2737.log reads 1249289B, 671 of 675 suite rows PASS,
  671 unique names, 4 FAIL rows, criteria 5000 of the expected 5026, no BOM,
  zero CRLF, zero lone CR, zero NUL, tail RUNNER FAIL (5 failed assertions) +
  BATTERY rc=1 3963.7s - so the leg CLOSED RED and was NOT adopted green;
  its four red rows are exactly the four whose birth sites R2738 repaired
  MID-LEG (os-state-io, os-status-export-writer-dialect-wire,
  os-queue-floor-export-face, os-export-consistency-queue-face), re-run GREEN
  on the repaired tree at R2738 (8/8, 6/6, 6/6, 15/15); the registry was
  re-measured BY IMPORT at 675 suites / 5026 criteria / 675 names / 675 paths;
  the successor leg was launched at pid 64724 on the committed tree and a
  second launch was refused with E_LAUNCH_PID_EXISTS; and a read-only census
  over 474 state-writing scripts found exactly 1 canonical-writer consumer,
  8 bare json.dump callers and 464 neither.
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

CURRENT = (
    "R2739 验证窗：R2737 电池腿已闭合但读数为红（671/675 套件绿、5026 判据"
    "只走完 5000、尾部 RUNNER FAIL rc=1），四条红正是 R2738 在腿运行期修过的"
    "同一批出生地，故不采纳为绿；四条修复后已复验全绿，继任电池已在干净提交"
    "树上发射")
LATEST = (
    "src/os/launch_battery_R2739.py（发射前按 import 重测 675 套件/5026 判据，"
    "双击守卫负控 E_LAUNCH_PID_EXISTS）＋ 只读普查：474 个写盘脚本中仅 1 个用"
    "正典写入器、8 个仍裸 json.dump（单行化复发风险已量化入台账）"
    "（2026-11-14 本窗实测）")
NEXT = (
    "48h 内：按证据路径 qa/reconcile-all-R2739.log 收养继任电池（675 套件／"
    "5026 判据，绿则重刷矩阵并结清 reconcile-battery 债行）；随后首个非电池窗"
    "把已欠七窗的静默失效导出钩子 export_R2431.py 与写盘正典消费者一并修在"
    "出生地")


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
