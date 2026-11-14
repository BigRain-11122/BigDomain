"""export_R2735 - refresh docs/status-export.json for the R2735 window.

The shipped generic driver supplies everything except this round's own CEO
lines, so this driver composes the three of them from numbers THIS window read.

Numbers behind the three lines (all measured in R2735):
  the leg pid 65136 answered a SYNCHRONIZE kernel probe with child 61448 and
  zero FAIL rows; the stream read 580029 bytes / 3963 lines / 331 PASS suite
  rows at 20:40:36; 140 ledger-apimarket suites exist with 121 done and 19 to
  run at a measured 89-272s each, which projects 80-110 minutes to completion;
  git was EMPTY at HEAD 7501e872 with no index.lock; zero @BigDomain ledger
  rows, zero new decision tokens, no new group order, benchmarks refreshed
  today; the queue floor read FLOOR-MET with the tech head at AC-DFOB1.
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
    "R2735 监控等待窗：675 套件／5026 判据的全量电池仍在跑（pid 65136·331/675"
    "·零 FAIL），按本腿实测时长投影还需约 80-110 分钟（19 条重型 apimarket "
    "套件实测 89-272s/条），本窗验收不了；产品字节继续按 R2168 混合树律冻结")
LATEST = (
    "src/os/backlog.md 顶行修正（已发射的电池行改标 launched 并写明 pid，堵掉"
    "下窗重复发射的口子）＋ logs/battery-R2733.stream 实时流（331/675·零 FAIL"
    "·2026-11-14 20:40 实测）")
NEXT = (
    "下一窗 48h 内：先按证据路径 qa/reconcile-all-R2733.log 验收本电池（绿则跑"
    "写敏感集、四段 followup、重压矩阵、关债），随即修那处已欠四窗的静默失效"
    "导出钩子 src/os/export_R2431.py（驱动方按文档打补丁会被无声忽略），再取 "
    "tech 队头 state/queue/tech.md:703 AC-DFOB1")


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
