"""export_R2734 - refresh docs/status-export.json for the R2734 window.

The shipped generic driver supplies everything except this round's own CEO
lines, so this driver composes the three of them from numbers THIS window read
and lets the same machinery publish.

Numbers behind the three lines (all measured in R2734):
  the battery target re-measured BY IMPORT at 675 suites / 5026 criteria with
  675 unique names and 675 unique paths, matching the R2733 pre-registration
  byte for byte; the leg LAUNCHED detached at pid=65136 writing
  logs/battery-R2733.stream and qa/reconcile-all-R2733.log; the stream was
  read growing at 15735 bytes with PASS suite rows already landing and ZERO
  FAIL rows; the five-silence scan read zero @BigDomain ledger rows, zero new
  decision tokens, no new group order and benchmarks refreshed today; git was
  EMPTY at HEAD 92516273 with no index.lock; zero product src bytes moved.
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
    "R2734 验证窗：675 套件／5026 判据的全量电池已发射在跑（发射前按 import "
    "实测 675/5026/675/675，与预注册逐字一致），流在长、PASS 行在落、零 FAIL"
    "行；本窗零产品字节——按 R2168 混合树律，电池绿之前不许再落产品改动")
LATEST = (
    "src/os/launch_battery_R2733.py 发射器 ＋ logs/battery-R2733.stream 实时流"
    "（pid 65136·2026-11-14 20:1x 起·目标 675 套件／5026 判据按 import 实测）")
NEXT = (
    "下一窗 48h 内：先按证据路径 qa/reconcile-all-R2733.log 验收本电池（绿则跑"
    "写敏感集、四段 followup、重压矩阵、关债），随即修那处已欠三窗的静默失效导出"
    "钩子 src/os/export_R2431.py（驱动方按文档打补丁会被无声忽略），同期把 tech "
    "队列补回 10 条（现 9 条·SHORT 1）")


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
