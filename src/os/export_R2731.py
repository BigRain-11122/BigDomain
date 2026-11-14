"""export_R2731 - refresh docs/status-export.json for the R2731 window.

The R2731 window is a VERIFICATION window: it moved no product src byte, so
its only landed artifact is the detached launcher plus the live evidence
stream, and its battery evidence file does not exist until the leg completes.
The shipped deriver (export_R2431.derive_latest) enumerates qa/ names for the
current round only, so on a window whose evidence lands after closeout it would
publish "none landed yet" - which is exactly what the CEO three-line law
forbids. This driver therefore stamps the three CEO lines from measured facts
of THIS window (a real path with its timestamp, never a placeholder) and leaves
every other face - the tick row, the queue face, the self-drive block - to the
same shipped machinery the generic driver uses, including the queue-face gate
and the single publish call.

The three lines are composed from numbers this window actually read:
  target 674 suites / 5020 criteria re-measured by import on 5a70e601,
  launch at 17:51:39 with pid 59208 and the negative control at rc=2,
  progress 18002B / 139 lines / 7 PASS / 0 FAIL at open+4min.
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
STAMP = datetime.datetime.now(
    datetime.timezone(datetime.timedelta(hours=8))).replace(
        microsecond=0).isoformat()

CURRENT = (
    "R2731 验证窗（零产品字节）：按 R2168 混合树律先跑债务闸点名的全量电池"
    "（reconcile-battery-R2730）——目标按导入实测 674 套件/5020 判据/674 唯一名"
    "/674 唯一路径，已在干净提交树 5a70e601 上分离启动 pid=59208，开窗 +4 分钟"
    "证据流读 7 套件全绿零 FAIL；本窗不宣称电池结果，结果由下一窗按证据路径验收")
LATEST = (
    "src/os/launch_battery_R2731.py 分离启动器（2026-11-14 17:51:39 落地·目标"
    "674/5020 常量钉死·二次启动负控读 E_LAUNCH_PID_EXISTS rc=2）＋在飞证据流 "
    "logs/battery-R2731.stream（开窗 +4 分钟 18002B/139 行/7 PASS/0 FAIL）")
NEXT = (
    "下一窗按证据路径 qa/reconcile-all-R2731.log 验收该腿：逐字节测得 674 套件、"
    "独立重算判据恰为 5020、零 FAIL、BATTERY rc= 收尾行；随后跑写敏感集与四段 "
    "followup、重压矩阵并关闭债务行，之后才开队头 state/queue/tech.md:702 AC-CEPB1")


def due():
    return (datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8)))
        + datetime.timedelta(hours=48)).replace(microsecond=0).isoformat()


def main():
    state = json.load(io.open(STATE, encoding="utf-8"))
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    tick = str(state["tick"])
    rows = data.get("results") or []
    label = tick_label()
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
          and back["ceo_face"]["next_milestone_due"] == ceo["next_milestone_due"]
          and back["ceo_face"]["updated_at"] == STAMP
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
